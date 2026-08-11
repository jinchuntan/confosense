"""UCI Occupancy adapter — the auxiliary pipeline-portability check.

These tests never download anything: they write small synthetic files with the
real archive's column names and its real *structure* (three disjoint segments
separated by genuine recording gaps, one-minute sampling with sub-minute
timestamp jitter), and assert the properties that make the auxiliary run
scientifically usable — chronological order, no partition leakage, no window
spanning a recording gap, correct direct-horizon targets, and no future
information in the features.
"""

import numpy as np
import pandas as pd
import pytest

from src import windowing
from src.datasets import get_adapter
from src.datasets.uci_occupancy import (
    MEMBERS,
    PooledChronologicalPartitioner,
    UciOccupancyAdapter,
    read_segment,
)

# Segment lengths and the gaps between them mirror the real archive's shape.
SEGMENTS = {
    "datatest.txt": ("2015-02-02 14:19:00", 300),
    "datatraining.txt": ("2015-02-04 17:51:00", 800),
    "datatest2.txt": ("2015-02-11 14:48:00", 900),
}


def _write_archive(raw_dir, jitter=True):
    """Write synthetic members with the real column names and 1 s jitter."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    for name, (start, n) in SEGMENTS.items():
        idx = pd.date_range(start, periods=n, freq="1min")
        if jitter:
            offs = rng.choice([-1, 0, 1], size=n)
            stamps = idx + pd.to_timedelta(offs, unit="s")
        else:
            stamps = idx
        t = np.linspace(0, 4 * np.pi, n)
        frame = pd.DataFrame({
            "date": stamps.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperature": 21.0 + np.sin(t),
            "Humidity": 27.0 + np.cos(t),
            "Light": 400.0 + 50 * np.sin(2 * t),
            "CO2": 700.0 + 100 * np.cos(2 * t),
            "HumidityRatio": 0.0047 + 0.0001 * np.sin(t),
            "Occupancy": (np.sin(t) > 0).astype(int),
        })
        frame.to_csv(raw_dir / name, index=False)
    return raw_dir


def _cfg(tmp_path, **over):
    cfg = {
        "paths": {"raw_dir": str(tmp_path)},
        "split": {"train_frac": 0.6, "calib_frac": 0.2},
        "uci_occupancy": {"subdir": "uci_occupancy", "auto_download": False,
                          "freq": "1min"},
        "features": {"target_lags": [1, 2, 3], "rolling_windows": [5],
                     "include_weekly": False},
        "horizons": [5, 15],
        "seed": 42,
    }
    cfg.update(over)
    return cfg


@pytest.fixture
def prepared(tmp_path):
    _write_archive(tmp_path / "uci_occupancy")
    return UciOccupancyAdapter().prepare(_cfg(tmp_path))


# --------------------------------------------------------------------------- #
# Loader
# --------------------------------------------------------------------------- #
def test_adapter_is_registered_and_declares_its_official_source():
    adapter = get_adapter("uci_occupancy")
    prov = adapter.provenance()
    assert prov.doi == "10.24432/C5X01N"
    assert "archive.ics.uci.edu" in prov.download_url
    assert "CC BY 4.0" in prov.license
    assert "Candanedo" in prov.citation


def test_reader_rounds_jittered_timestamps_onto_a_one_minute_grid(tmp_path):
    raw = _write_archive(tmp_path / "uci_occupancy")
    frame = read_segment(raw / "datatraining.txt")
    assert isinstance(frame.index, pd.DatetimeIndex)
    assert frame.index.is_monotonic_increasing
    assert (frame.index.second == 0).all(), "sub-minute jitter survived rounding"
    assert frame.index.to_series().diff().dropna().eq(pd.Timedelta("1min")).all()


def test_reader_refuses_a_file_with_a_hidden_gap(tmp_path):
    """A silent interpolation here would let a window span a recording break."""
    raw = _write_archive(tmp_path / "uci_occupancy")
    df = pd.read_csv(raw / "datatest.txt")
    df = pd.concat([df.iloc[:100], df.iloc[150:]], ignore_index=True)
    df.to_csv(raw / "datatest.txt", index=False)
    with pytest.raises(ValueError, match="gap-free"):
        read_segment(raw / "datatest.txt")


def test_preparation_keeps_one_series_per_archive_member(prepared):
    assert len(prepared.series) == len(MEMBERS)
    assert {s.group_id for s in prepared.series} == {
        m.replace(".txt", "") for m in MEMBERS}
    assert all(s.units == "degC" for s in prepared.series)
    assert all(s.season_steps is None for s in prepared.series)


def test_segments_are_ordered_by_time_not_by_filename(prepared):
    """The file named 'datatraining' is the middle segment in the real archive."""
    order = [s.group_id for s in prepared.series]
    assert order == ["datatest", "datatraining", "datatest2"]
    starts = [s.start for s in prepared.series]
    assert starts == sorted(starts)


def test_target_is_temperature_and_occupancy_is_not_used(prepared):
    for s in prepared.series:
        assert "target" in s.frame.columns
        assert "Occupancy" not in s.frame.columns
    assert prepared.metadata["target_column"] == "Temperature"
    assert "performance" in prepared.metadata["target_rationale"] or \
           "no performance criterion" in prepared.metadata["target_rationale"]


def test_preparation_is_reproducible(tmp_path):
    _write_archive(tmp_path / "uci_occupancy")
    a = UciOccupancyAdapter().prepare(_cfg(tmp_path))
    b = UciOccupancyAdapter().prepare(_cfg(tmp_path))
    for sa, sb in zip(a.series, b.series):
        pd.testing.assert_frame_equal(sa.frame, sb.frame)
    assert a.partitioner.describe() == b.partitioner.describe()


# --------------------------------------------------------------------------- #
# Partitioning
# --------------------------------------------------------------------------- #
def test_partitions_are_chronological_and_do_not_interleave(prepared):
    """train < calibration < test in wall-clock time, across segments.

    A per-series chronological split would put segment 1's test rows before
    segment 2's training rows, so a model would be fitted on observations
    recorded after forecasts it is scored on.
    """
    fcfg = windowing.feature_config({"features": {"target_lags": [1, 2],
                                                  "rolling_windows": [5]}},
                                    prepared.series[0].covariates)
    w = windowing.build_dataset_windows(prepared, 5, fcfg)
    meta = w["meta"]
    spans = {p: (meta.loc[meta.partition == p, "origin_time"].min(),
                 meta.loc[meta.partition == p, "origin_time"].max())
             for p in ("train", "calibration", "test")}
    assert spans["train"][1] < spans["calibration"][0]
    assert spans["calibration"][1] < spans["test"][0]


def test_no_observation_appears_in_two_partitions(prepared):
    fcfg = windowing.feature_config({"features": {"target_lags": [1, 2],
                                                  "rolling_windows": [5]}},
                                    prepared.series[0].covariates)
    w = windowing.build_dataset_windows(prepared, 5, fcfg)
    meta = w["meta"]
    keys = {}
    for part in ("train", "calibration", "test"):
        sub = meta[meta.partition == part]
        keys[part] = set(zip(sub["group_id"], sub["origin_time"]))
    assert not keys["train"] & keys["calibration"]
    assert not keys["train"] & keys["test"]
    assert not keys["calibration"] & keys["test"]


def test_pooled_partitioner_needs_its_boundaries(prepared):
    bare = PooledChronologicalPartitioner()
    with pytest.raises(ValueError, match="boundaries"):
        bare.labels(prepared.series[0], prepared.series[0].frame.index)


# --------------------------------------------------------------------------- #
# Windowing
# --------------------------------------------------------------------------- #
def test_no_window_spans_a_recording_gap(prepared):
    """Every window's origin and target must lie inside one segment."""
    fcfg = windowing.feature_config({"features": {"target_lags": [1, 2],
                                                  "rolling_windows": [5]}},
                                    prepared.series[0].covariates)
    bounds = {s.group_id: (s.frame.index[0], s.frame.index[-1])
              for s in prepared.series}
    for h in (5, 15):
        meta = windowing.build_dataset_windows(prepared, h, fcfg)["meta"]
        for gid, sub in meta.groupby("group_id"):
            lo, hi = bounds[gid]
            assert sub["origin_time"].min() >= lo
            assert sub["target_time"].max() <= hi


def test_direct_horizon_target_is_the_value_h_steps_ahead(prepared):
    fcfg = windowing.feature_config({"features": {"target_lags": [1, 2],
                                                  "rolling_windows": [5]}},
                                    prepared.series[0].covariates)
    for h in (5, 15):
        w = windowing.build_dataset_windows(prepared, h, fcfg)
        meta, y = w["meta"], w["y"]
        step = prepared.series[0].freq
        assert (pd.DatetimeIndex(meta["target_time"])
                - pd.DatetimeIndex(meta["origin_time"]) == h * step).all()
        lookup = {(s.group_id, t): v
                  for s in prepared.series
                  for t, v in s.frame["target"].items()}
        sample = meta.sample(min(50, len(meta)), random_state=0)
        for pos, row in zip(sample.index, sample.itertuples()):
            assert np.isclose(y[pos], lookup[(row.group_id, row.target_time)])


def test_features_never_use_information_after_the_forecast_origin(prepared):
    """Perturb the target strictly after an origin; its features must not move."""
    fcfg = windowing.feature_config({"features": {"target_lags": [1, 2, 3],
                                                  "rolling_windows": [5]}},
                                    prepared.series[0].covariates)
    base = windowing.build_dataset_windows(prepared, 5, fcfg)

    import copy
    tampered = copy.deepcopy(prepared)
    s = tampered.series[1]
    cut = s.frame.index[len(s.frame) // 2]
    s.frame.loc[s.frame.index > cut, "target"] += 100.0
    s.frame.loc[s.frame.index > cut, "Humidity"] += 100.0
    after = windowing.build_dataset_windows(tampered, 5, fcfg)

    meta = base["meta"]
    keep = ((meta["group_id"] == s.group_id)
            & (pd.DatetimeIndex(meta["origin_time"]) <= cut)).to_numpy()
    assert keep.sum() > 0
    pd.testing.assert_frame_equal(
        base["X"].loc[keep].reset_index(drop=True),
        after["X"].loc[keep].reset_index(drop=True),
        check_exact=False,
    )


# --------------------------------------------------------------------------- #
# Conformal output shape
# --------------------------------------------------------------------------- #
def test_cqr_bounds_are_ordered_on_the_uci_adapter(prepared):
    from src import conformal_cqr

    fcfg = windowing.feature_config({"features": {"target_lags": [1, 2],
                                                  "rolling_windows": [5]}},
                                    prepared.series[0].covariates)
    w = windowing.build_dataset_windows(prepared, 5, fcfg)
    idx, X, y = w["idx"], w["X"], w["y"]
    tr, ca, te = idx["train"], idx["calibration"], idx["test"]
    if min(tr.sum(), ca.sum(), te.sum()) < 30:
        pytest.skip("synthetic fixture too small for a conformal fit")
    model = conformal_cqr.fit_cqr(
        windowing.subset(X, tr), pd.Series(y[tr]),
        windowing.subset(X, ca), pd.Series(y[ca]), 0.9, 42)
    res = conformal_cqr.cqr_interval(model, windowing.subset(X, te))
    assert (res["lower"] <= res["upper"]).all()
    assert res["n_crossed_repaired"] >= 0
