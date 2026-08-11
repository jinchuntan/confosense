"""Group-safe windowing: no window may cross a group, no partition may overlap.

These are the leakage guarantees the whole multi-dataset design rests on, so they
are checked directly against the concatenated design matrix rather than trusted
to the construction.
"""

import numpy as np
import pandas as pd
import pytest

from src import windowing
from src.datasets.base import (
    ChronologicalPartitioner,
    GroupPartitioner,
    PreparedDataset,
    PreparedSeries,
    Provenance,
)

FCFG = {"target_lags": [1, 2, 3], "rolling_windows": [6],
        "include_weekly": False, "covariates": ["tmed"]}


def _series(n, group, start, season=144, freq="10min", offset=0.0):
    idx = pd.date_range(start, periods=n, freq=freq)
    rng = np.random.default_rng(abs(hash(group)) % 2**32)
    frame = pd.DataFrame({
        "target": offset + 20 + np.sin(np.arange(n) / 20) + rng.normal(0, .05, n),
        "target_was_missing": np.zeros(n, dtype=int),
        "tmed": rng.normal(size=n),
    }, index=idx)
    return PreparedSeries("synthetic", "t", frame, pd.Timedelta(freq),
                          group_id=group, season_steps=season, covariates=["tmed"])


def grouped_dataset(n_groups=6, n=300, season=None):
    # Runs one day apart so their timestamps cannot be confused for one series.
    series = [_series(n, f"run{i}", f"2021-03-{i+1:02d}", season=season,
                      freq="1min", offset=10.0 * i)
              for i in range(n_groups)]
    part = GroupPartitioner(fractions=(0.6, 0.2, 0.2)).fit(series)
    return PreparedDataset("synthetic", series, part, Provenance("synthetic", "s"))


def test_windows_never_cross_a_group_boundary():
    """A lag feature must equal the same group's own past, never a neighbour's."""
    ds = grouped_dataset()
    w = windowing.build_dataset_windows(ds, horizon=5, fcfg=FCFG)
    meta, X = w["meta"], w["X"]

    frames = {s.group_id: s.frame for s in ds.series}
    for _, row in meta.sample(40, random_state=0).iterrows():
        frame = frames[row["group_id"]]
        origin = row["origin_time"]
        # lag_1 is this group's value one step before the origin.
        expected = frame["target"].shift(1).loc[origin]
        assert np.isclose(X.loc[row.name, "target_lag_1"], expected)
        # The target is this group's value h steps after the origin.
        assert np.isclose(row["y_true"], frame["target"].loc[row["target_time"]])
        # Both endpoints lie inside the group's own span.
        assert frame.index[0] <= origin <= frame.index[-1]
        assert row["target_time"] <= frame.index[-1]


def test_no_target_extends_past_the_end_of_its_group():
    ds = grouped_dataset()
    w = windowing.build_dataset_windows(ds, horizon=10, fcfg=FCFG)
    ends = {s.group_id: s.frame.index[-1] for s in ds.series}
    assert (w["meta"]["target_time"] <= w["meta"]["group_id"].map(ends)).all()


def test_group_partitions_are_disjoint_in_time_and_membership():
    """No run contributes rows to two partitions, and no timestamp is shared."""
    ds = grouped_dataset()
    w = windowing.build_dataset_windows(ds, horizon=5, fcfg=FCFG)
    meta = w["meta"]

    per_group = meta.groupby("group_id")["partition"].nunique()
    assert (per_group == 1).all(), "a run appeared in more than one partition"

    seen = {}
    for part in ("train", "calibration", "test"):
        sub = meta[meta["partition"] == part]
        seen[part] = set(zip(sub["group_id"], sub["origin_time"]))
    assert not (seen["train"] & seen["calibration"])
    assert not (seen["calibration"] & seen["test"])
    assert not (seen["train"] & seen["test"])


def test_chronological_partitions_do_not_overlap_within_a_building():
    series = [_series(600, f"b{i}", "2021-01-01", season=24, freq="1h")
              for i in range(3)]
    ds = PreparedDataset("synthetic", series,
                         ChronologicalPartitioner(fractions=(0.6, 0.2, 0.2)),
                         Provenance("synthetic", "s"))
    w = windowing.build_dataset_windows(ds, horizon=3, fcfg=FCFG)
    meta = w["meta"]
    for gid, sub in meta.groupby("group_id"):
        tr = sub[sub["partition"] == "train"]["origin_time"]
        ca = sub[sub["partition"] == "calibration"]["origin_time"]
        te = sub[sub["partition"] == "test"]["origin_time"]
        assert tr.max() < ca.min(), f"{gid}: train overlaps calibration"
        assert ca.max() < te.min(), f"{gid}: calibration overlaps test"


def test_direct_horizon_targets_differ_between_horizons():
    """Each horizon predicts its own step, not a recursively rolled-forward one."""
    ds = grouped_dataset()
    w1 = windowing.build_dataset_windows(ds, horizon=1, fcfg=FCFG)
    w5 = windowing.build_dataset_windows(ds, horizon=5, fcfg=FCFG)
    m1 = w1["meta"].set_index(["group_id", "origin_time"])
    m5 = w5["meta"].set_index(["group_id", "origin_time"])
    common = m1.index.intersection(m5.index)[:50]
    assert len(common) > 0
    step = ds.freq
    assert ((m5.loc[common, "target_time"] - m1.loc[common, "target_time"])
            == 4 * step).all()


def test_seasonal_features_absent_when_no_seasonal_cycle_exists():
    """A RICO-like run gets no daily lag and a NaN seasonal-naive baseline."""
    ds = grouped_dataset(season=None)
    w = windowing.build_dataset_windows(ds, horizon=5, fcfg=FCFG)
    assert "target_daily_lag" not in w["X"].columns
    assert w["meta"]["seasonal_naive_pred"].isna().all()
    assert not ds.seasonal_naive_supported


def test_series_too_short_are_reported_not_silently_dropped():
    short = [_series(20, "tiny", "2021-04-01", season=None, freq="1min")]
    long = [_series(300, f"ok{i}", f"2021-04-{i+2:02d}", season=None, freq="1min")
            for i in range(4)]
    series = short + long
    ds = PreparedDataset("synthetic", series,
                         GroupPartitioner().fit(series), Provenance("s", "s"))
    w = windowing.build_dataset_windows(ds, horizon=30, fcfg=FCFG)
    assert "tiny" in w["skipped_groups"]
    assert "tiny" not in set(w["meta"]["group_id"])
