"""Adapter selection and segmentation logic, on synthetic frames only.

No test here downloads RICO or BDG2; the pure functions that decide *which* data
is used are exercised directly, which is the part that has to be reproducible.
"""

import numpy as np
import pandas as pd
import pytest

from src.datasets import bdg2, rico


# --------------------------------------------------------------------------- #
# BDG2 subset selection
# --------------------------------------------------------------------------- #
def _profile(n=20):
    """Candidate buildings with deliberately varied quality."""
    rows = []
    for i in range(n):
        rows.append({
            "building_id": f"Site{i % 4}_office_B{i:02d}",
            "site_id": f"Site{i % 4}",
            "primary_use": "Office",
            "sqm": 1000 + i,
            "meter_type": "electricity",
            "start": pd.Timestamp("2016-01-01"),
            "end": pd.Timestamp("2017-12-31"),
            "span_days": 730.0,
            "n_valid": 17000 - i,
            "coverage": 0.99 - i * 0.001,
            "missing_fraction": 0.01 + i * 0.001,
            "mean": 100.0, "std": 20.0, "min": 1.0, "max": 500.0,
            "n_negative": 0, "n_zero": 0, "constant_fraction": 0.05,
        })
    return pd.DataFrame(rows)


SEL = {"n_buildings": 6, "min_span_days": 300, "min_coverage": 0.95,
       "max_constant_fraction": 0.5, "max_per_site": 2,
       "require_documented_use": True}


def test_subset_selection_is_deterministic_and_needs_no_seed():
    prof = _profile()
    a = bdg2.select_subset(prof, SEL)
    b = bdg2.select_subset(prof.sample(frac=1, random_state=99), SEL)
    assert set(a[a.selected].building_id) == set(b[b.selected].building_id)
    assert a.selected.sum() == SEL["n_buildings"]


def test_selection_respects_the_per_site_cap_for_diversity():
    out = bdg2.select_subset(_profile(), SEL)
    chosen = out[out.selected]
    assert (chosen.groupby("site_id").size() <= SEL["max_per_site"]).all()
    assert chosen["site_id"].nunique() > 1, "the subset should span several sites"


def test_every_candidate_is_accounted_for_with_a_reason():
    prof = _profile()
    out = bdg2.select_subset(prof, SEL)
    assert len(out) == len(prof)
    assert (out["selection_reason"].astype(str).str.len() > 0).all()
    for col in ("building_id", "site_id", "primary_use", "meter_type", "start",
                "end", "coverage", "missing_fraction", "selected"):
        assert col in out.columns


def test_quality_filters_exclude_and_explain():
    prof = _profile(8)
    prof.loc[0, "span_days"] = 10                  # too short
    prof.loc[1, "coverage"] = 0.10                 # too incomplete
    prof.loc[2, "std"] = 0.0                       # constant
    prof.loc[3, "n_negative"] = 5                  # impossible readings
    prof.loc[4, "primary_use"] = ""                # undocumented
    out = bdg2.select_subset(prof, {**SEL, "n_buildings": 8}).set_index("building_id")

    reasons = out["reason_excluded"]
    assert "span" in reasons.iloc[0] or "span" in reasons.loc[prof.loc[0, "building_id"]]
    for i, fragment in [(0, "span"), (1, "coverage"), (2, "constant"),
                        (3, "negative"), (4, "primary use")]:
        bid = prof.loc[i, "building_id"]
        assert fragment in out.loc[bid, "reason_excluded"], (
            f"{bid} should be excluded for {fragment}")
        assert not out.loc[bid, "selected"]


def test_selection_never_consults_a_forecast_metric():
    """Adding a performance column must not change the outcome."""
    prof = _profile()
    base = bdg2.select_subset(prof, SEL)
    noisy = prof.copy()
    noisy["mae"] = np.random.default_rng(0).normal(size=len(noisy))
    after = bdg2.select_subset(noisy, SEL)
    assert set(base[base.selected].building_id) == set(after[after.selected].building_id)


# --------------------------------------------------------------------------- #
# RICO run segmentation
# --------------------------------------------------------------------------- #
def _acquisition(n_groups=3, group_len=600, flagged=(30, 270), freq="1min"):
    """One acquisition frame: each scheduler group holds one flagged block."""
    frames = []
    start = pd.Timestamp("2024-01-01")
    for g in range(n_groups):
        idx = pd.date_range(start + pd.Timedelta(minutes=g * group_len),
                            periods=group_len, freq=freq)
        flag = np.zeros(group_len, dtype=int)
        flag[flagged[0]:flagged[1]] = 1
        frames.append(pd.DataFrame({
            "Acquisition Phase": 1, "Scheduler Step": g, "Flag": flag,
            "B.RTD3": 20 + np.sin(np.arange(group_len) / 30),
        }, index=idx))
    return pd.concat(frames)


def test_runs_are_the_flagged_contiguous_blocks():
    df = _acquisition()
    runs = rico.segment_runs(df, pd.Timedelta("1min"), min_length=120)
    assert len(runs) == 3
    for r in runs:
        assert r["accepted"]
        assert r["n"] == 240                        # 270 - 30
        assert (r["frame"]["Flag"] == 1).all()      # unflagged samples excluded
        gaps = r["frame"].index.to_series().diff().dropna().unique()
        assert list(gaps) == [pd.Timedelta("1min")]


def test_run_ids_are_unique_and_runs_do_not_overlap_in_time():
    df = _acquisition(n_groups=5)
    runs = rico.segment_runs(df, pd.Timedelta("1min"), min_length=120)
    ids = [r["run_id"] for r in runs]
    assert len(ids) == len(set(ids))
    spans = sorted((r["start"], r["end"]) for r in runs)
    for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
        assert e1 < s2, "two runs overlap in time"


def test_short_runs_are_rejected_with_a_reason_not_silently_dropped():
    df = _acquisition(group_len=200, flagged=(10, 40))   # only 30 flagged samples
    runs = rico.segment_runs(df, pd.Timedelta("1min"), min_length=120)
    assert len(runs) == 3
    assert all(not r["accepted"] for r in runs)
    assert all("only 30 flagged samples" in r["reason_excluded"] for r in runs)


def test_irregularly_sampled_runs_are_rejected():
    df = _acquisition(n_groups=1)
    df = df.drop(df.index[100])                     # punch a hole in the run
    runs = rico.segment_runs(df, pd.Timedelta("1min"), min_length=120)
    assert not runs[0]["accepted"]
    assert "irregular sampling" in runs[0]["reason_excluded"]


def test_multiple_flagged_blocks_in_one_group_become_separate_runs():
    idx = pd.date_range("2024-02-01", periods=600, freq="1min")
    flag = np.zeros(600, dtype=int)
    flag[50:200] = 1
    flag[300:500] = 1                               # a second usable block
    df = pd.DataFrame({"Acquisition Phase": 2, "Scheduler Step": 0, "Flag": flag,
                       "B.RTD3": np.arange(600, dtype=float)}, index=idx)
    runs = rico.segment_runs(df, pd.Timedelta("1min"), min_length=100)
    assert len(runs) == 2
    assert len({r["run_id"] for r in runs}) == 2
    assert [r["n"] for r in runs] == [150, 200]


def test_documented_temperature_sensors_are_the_only_target_candidates():
    assert set(rico.TEMPERATURE_SENSORS) == {"B.RTD1", "B.RTD2", "B.RTD3", "B.RTD6"}
    # The default target is the 110 cm Pt100 air sensor, and its description says so.
    assert "110 cm" in rico.TEMPERATURE_SENSORS["B.RTD3"]
    assert "Globe" in rico.TEMPERATURE_SENSORS["B.RTD6"]      # operative, not air
    assert "Cell A" in rico.TEMPERATURE_SENSORS["B.RTD1"]     # uncontrolled cell
