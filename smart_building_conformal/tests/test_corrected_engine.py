"""Nested end-to-end engine: the contracts the audit requires (C3/E, D4, folds,
fail-closed), tested at the primitive level so they are fast and exact.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import corrected_study as E


# ---- Pipeline config-hash determinism / equality (C3/E) ----------------- #
def _pipe(**kw):
    base = dict(dataset="d", horizon=1, seed=42, outer_fold=0,
                point_model="persistence", interval_method="cqr",
                operating_level=0.95, recalibration="static", rule_name="single",
                rule_k=1, rule_m=1, rule_window_minutes=0.0, selection_reason="x")
    base.update(kw)
    return E.Pipeline(**base).freeze()


def test_pipeline_hash_is_deterministic_and_sensitive():
    a = _pipe()
    b = _pipe()
    assert a.config_hash == b.config_hash and len(a.config_hash) == 64
    c = _pipe(recalibration="rolling")
    assert c.config_hash != a.config_hash


def test_reeval_hash_matches_selected_hash():
    from dataclasses import asdict
    p = _pipe()
    re = E.Pipeline(**{**asdict(p), "config_hash": ""}).freeze().config_hash
    assert re == p.config_hash          # the guard evaluate_outer enforces


# ---- C3/E: alerting consumes exactly the given interval stream ---------- #
def test_alert_on_stream_consumes_the_passed_bounds():
    n = 50
    meta = pd.DataFrame({"group_id": ["g"] * n,
                         "origin_time": pd.date_range("2021", periods=n, freq="h")})
    groups = meta["group_id"].to_numpy()
    observed = np.zeros(n)
    lower = np.full(n, -1.0); upper = np.full(n, 1.0)
    observed[10] = 5.0                    # one clear violation
    cat = pd.DataFrame([{"event_id": 0, "event_type": "bias", "severity": "1.0sd",
                         "group_id": "g", "start_index": 10, "end_index": 11}])
    out = E.alert_on_stream(observed, lower, upper, groups, meta, cat,
                            {"name": "single", "immediate": True, "required": 1},
                            pd.Timedelta("1h"), tolerance_steps=1)
    # The returned bounds ARE the passed arrays (no silent revert to CQR@95%).
    assert np.array_equal(out["lower"], lower) and np.array_equal(out["upper"], upper)
    assert out["n_detected"] == 1


def test_immediate_rule_applies_at_any_sampling():
    r = E._rule_dict(_pipe(rule_name="single", rule_m=1))
    assert r.get("immediate") is True


# ---- D4: exposure-based, group-safe, no silent drops -------------------- #
def _block(groups, freq="1min"):
    n = len(groups)
    # each group gets its own local time so runs do not overlap in index space
    times = pd.date_range("2021", periods=n, freq=freq)
    return pd.DataFrame({"group_id": groups, "origin_time": times,
                         "target_time": times})


def test_exposure_allocation_scales_with_asset_time():
    # long group gets proportionally more events than a short one.
    groups = np.array(["long"] * 4000 + ["short"] * 400)
    y = np.zeros(len(groups))
    meta = _block(groups)
    scale = {"long": 1.0, "short": 1.0, "__pooled__": 1.0}
    _, cat, alloc = E.exposure_event_catalogue(
        y, meta, pd.Timedelta("1min"), scale, incidence_per_day=5.0, seed=1,
        dataset="d")
    n_long = (cat["group_id"] == "long").sum()
    n_short = (cat["group_id"] == "short").sum()
    assert n_long > n_short
    # nothing dropped silently: attempted == placed + rejected
    assert alloc["attempted"] == alloc["placed"] + alloc["rejected"]


def test_exposure_events_never_cross_group_boundary():
    groups = np.array(["a"] * 500 + ["b"] * 500)
    y = np.zeros(len(groups))
    meta = _block(groups)
    scale = {"a": 1.0, "b": 1.0, "__pooled__": 1.0}
    _, cat, _ = E.exposure_event_catalogue(
        y, meta, pd.Timedelta("1min"), scale, incidence_per_day=10.0, seed=2,
        dataset="d")
    g = groups
    for _, e in cat.iterrows():
        s, en = int(e["start_index"]), int(e["end_index"])
        assert g[s] == g[en], "an event spanned two groups"


def test_exposure_allocation_is_deterministic():
    groups = np.array(["a"] * 1000)
    y = np.zeros(len(groups)); meta = _block(groups)
    scale = {"a": 1.0, "__pooled__": 1.0}
    args = (y, meta, pd.Timedelta("1min"), scale)
    _, c1, a1 = E.exposure_event_catalogue(*args, incidence_per_day=5.0, seed=7, dataset="d")
    _, c2, a2 = E.exposure_event_catalogue(*args, incidence_per_day=5.0, seed=7, dataset="d")
    assert a1 == a2 and len(c1) == len(c2)


# ---- Folds: group-safe and embargoed ------------------------------------ #
def _meta_chrono(n=600):
    t = pd.date_range("2021-01-01", periods=n, freq="10min")
    return pd.DataFrame({"group_id": ["s"] * n, "origin_time": t,
                         "target_time": t + pd.Timedelta("30min")})


def test_chronological_folds_embargo_no_train_target_after_test_origin():
    meta = _meta_chrono()
    folds = E.make_outer_folds(meta, "chronological", 2, horizon=3,
                               freq=pd.Timedelta("10min"))
    o = pd.DatetimeIndex(meta["origin_time"]); t = pd.DatetimeIndex(meta["target_time"])
    for f in folds:
        trc = np.concatenate([f["train"], f["calibration"]])
        assert t[trc].max() < o[f["test"]].min(), "target-time leak across fold"


def test_whole_run_folds_keep_runs_intact():
    rows = []
    base = pd.Timestamp("2021-01-01")
    for gi, g in enumerate(["r1", "r2", "r3", "r4", "r5"]):
        t = pd.date_range(base + pd.Timedelta(days=gi), periods=120, freq="1min")
        for ts in t:
            rows.append({"group_id": g, "origin_time": ts,
                         "target_time": ts + pd.Timedelta("5min")})
    meta = pd.DataFrame(rows)
    folds = E.make_outer_folds(meta, "whole_run_group_blocked", 2, horizon=5,
                               freq=pd.Timedelta("1min"))
    for f in folds:
        gtr = set(meta.iloc[f["train"]]["group_id"])
        gca = set(meta.iloc[f["calibration"]]["group_id"])
        gte = set(meta.iloc[f["test"]]["group_id"])
        assert gtr.isdisjoint(gte) and gca.isdisjoint(gte) and gtr.isdisjoint(gca)


def test_too_few_runs_fails_closed():
    rows = []
    for g in ["r1", "r2"]:
        t = pd.date_range("2021", periods=50, freq="1min")
        for ts in t:
            rows.append({"group_id": g, "origin_time": ts, "target_time": ts})
    meta = pd.DataFrame(rows)
    with pytest.raises(E.FailClosed):
        E.make_outer_folds(meta, "whole_run_group_blocked", 2, 1,
                           pd.Timedelta("1min"))
