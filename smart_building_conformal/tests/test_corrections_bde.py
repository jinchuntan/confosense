"""Regression tests for B2 (feature-schema persistence), A2 (run-aware nested
subsplit) and D5 (per-group train-only robust event scaling).
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src import alert_study, alerts_corrected as AC, windowing
from src.datasets.base import (GroupPartitioner, PreparedDataset,
                               PreparedSeries, Provenance)


def _grouped_dataset(n=240, freq="1min"):
    series = []
    for gi, g in enumerate(["run1", "run2", "run3", "run4", "run5"]):
        idx = pd.date_range("2021-01-01", periods=n, freq=freq)
        frame = pd.DataFrame(
            {"target": np.linspace(20, 22, n) + gi, "tmed": np.zeros(n)}, index=idx)
        series.append(PreparedSeries(
            dataset_id="rico_like", target_id="t", frame=frame,
            freq=pd.Timedelta(freq), group_id=g, season_steps=None,
            covariates=["tmed"], units="degC"))
    part = GroupPartitioner(fractions=(0.6, 0.2, 0.2)).fit(series)
    return PreparedDataset(
        dataset_id="rico_like", series=series, partitioner=part,
        provenance=Provenance(dataset_id="rico_like", official_source="synthetic"))


# ---- B2: feature-schema persistence ------------------------------------- #
def test_feature_schema_persisted(tmp_path):
    ds = _grouped_dataset()
    fcfg = windowing.feature_config({"features": {"target_lags": [1, 2]}},
                                    ds.series[0].covariates)
    w = windowing.build_dataset_windows(ds, 5, fcfg)
    path = windowing.persist_feature_schema(w, "rico_like", tmp_path)
    assert path.exists()
    schema = json.loads(path.read_text())
    assert schema["feature_names_in_order"] == list(w["feature_names"])
    assert schema["n_features"] == len(w["feature_names"])
    assert len(schema["schema_hash"]) == 64
    # lag 0 (y_t) must be present in the persisted schema.
    assert any("lag_0" in c for c in schema["feature_names_in_order"])


# ---- A2: run-aware nested subsplit -------------------------------------- #
def test_group_blocked_subsplit_keeps_runs_whole():
    # Five runs, each 100 rows, interleaved-free chronological groups.
    groups, origins, targets = [], [], []
    base = pd.Timestamp("2021-01-01")
    for gi, g in enumerate(["r1", "r2", "r3", "r4", "r5"]):
        start = base + pd.Timedelta(days=gi)
        idx = pd.date_range(start, periods=100, freq="1min")
        groups += [g] * 100
        origins += list(idx)
        targets += list(idx + pd.Timedelta(minutes=5))
    out = alert_study.group_blocked_subsplit(
        groups, pd.DatetimeIndex(origins), pd.DatetimeIndex(targets),
        fraction=0.6, min_samples=50)
    g = np.asarray(groups)
    conf_g = set(g[out["conformal_mask"]])
    rule_g = set(g[out["rule_mask"]])
    # No run appears in both blocks.
    assert conf_g.isdisjoint(rule_g)
    assert out["usable"]


def test_group_blocked_subsplit_no_run_split_across_blocks():
    groups = np.array(["a"] * 60 + ["b"] * 60)
    idx = pd.date_range("2021-01-01", periods=120, freq="1min")
    out = alert_study.group_blocked_subsplit(
        groups, idx, idx + pd.Timedelta(minutes=5), fraction=0.5, min_samples=10)
    g = groups
    for grp in ["a", "b"]:
        in_conf = out["conformal_mask"][g == grp].any()
        in_rule = out["rule_mask"][g == grp].any()
        assert not (in_conf and in_rule), f"run {grp} split across blocks"


# ---- D5: per-group train-only robust scaling ---------------------------- #
def test_per_group_scale_is_group_specific_and_train_only():
    rng = np.random.default_rng(0)
    y = np.concatenate([rng.normal(0, 1, 500), rng.normal(0, 5, 500)])
    groups = np.array(["a"] * 500 + ["b"] * 500)
    res = AC.per_group_robust_scale(y, groups)
    assert res["source"] == "train_only"
    # Group b is ~5x more variable than group a.
    assert res["scale"]["b"] > 3 * res["scale"]["a"]


def test_per_group_scale_falls_back_for_degenerate_group():
    y = np.concatenate([np.random.default_rng(1).normal(0, 1, 500),
                        np.zeros(500)])         # group b degenerate (zero MAD)
    groups = np.array(["a"] * 500 + ["b"] * 500)
    res = AC.per_group_robust_scale(y, groups)
    assert "b" in res["groups_using_fallback"]
    assert res["scale"]["b"] == res["pooled_fallback"]
