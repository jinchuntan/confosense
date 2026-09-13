"""Nested, end-to-end corrected study engine (audit C3/E, D1, D4 + integration).

This is the single traceable pipeline the audit requires. For each dataset it

1. builds group-safe supervised windows (horizon embargo + ``target_lag_0``
   already enforced in :mod:`src.windowing`);
2. cuts **outer** folds (rolling-origin for chronological datasets, whole-run
   blocks for RICO) and, inside each, an **inner** train / calibration /
   selection split that never touches the outer test;
3. on the inner data only, selects the interval-owned predictor and interval
   method and nominal coverage (D1: among uncalibrated quantiles, CQR, static &
   updated recentred EnbPI, DSCP), recalibration strategy and a physical-time
   k-of-m alert rule — under the frozen feasibility policy, abstaining with
   ``no_feasible_configuration`` when nothing qualifies (D7);
4. freezes that configuration (hash) and evaluates *exactly it* on the outer
   test: the selected, recalibrated interval stream is the one physical-time
   alerting consumes (C3/E), events are injected by exposure (D4), matching is
   one-to-one and onset-aware (D6), metrics are macro recall + background
   workload per asset-day (D8);
5. records full provenance and asserts selected-config-hash == evaluated-config
   -hash and alert-consumed-bounds == selected-recalibrated-bounds.

The engine **fails closed** (raises :class:`FailClosed`) on cross-group state,
target-time leakage, unavailable residual updates, an infeasible physical rule it
was told to use, incomplete folds/seeds, or a silent fall-back to a hard-coded
interval method.

It also runs the four-level ablation (baseline / conformal-only / temporal /
full) on the *same* outer folds and event catalogues.

Everything writes under a run directory; nothing here touches
``outputs/full_study``. No number is a "result" until the full (non-fast) run and
its programmatic reports exist.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import (alerts_corrected as AC, alert_study, baselines, conformal_cqr,
               conformal_enbpi, conformal_quantile, metrics as M, recalibration,
               windowing, xgboost_model)
from .datasets.base import ChronologicalPartitioner
from .residuals import DelayedResidualPool
from . import split_integrity as SI
from .interval_stream import IntervalEstimator, recalibrated_bounds
from .unit_checkpoint import UnitCheckpoint, source_digest

INTERVAL_METHODS = ("quantile_uncalibrated", "cqr", "recentred_enbpi_static",
                    "recentred_enbpi_updated", "dscp")
ABLATION_LEVELS = ("baseline", "conformal_only", "temporal", "full")


class FailClosed(RuntimeError):
    """Raised when the engine detects a condition that invalidates a result."""


# --------------------------------------------------------------------------- #
@dataclass
class Pipeline:
    """The frozen, selected end-to-end configuration for one outer fold."""
    dataset: str
    horizon: int
    seed: int
    outer_fold: int
    point_model: str
    interval_method: str
    operating_level: float
    recalibration: str
    rule_name: str
    rule_k: int
    rule_m: int
    rule_window_minutes: float
    selection_reason: str
    config_hash: str = ""
    estimator_class: str = ""
    event_seed: int | None = None
    fallback: dict | None = None
    predictor_role: str = "interval_owned"

    def freeze(self) -> "Pipeline":
        payload = {k: v for k, v in asdict(self).items() if k != "config_hash"}
        self.config_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        return self


# --------------------------------------------------------------------------- #
# Fold construction
# --------------------------------------------------------------------------- #
def make_outer_folds(meta, scheme, n_outer, horizon, freq):
    """Common-time outer tests and purged refit blocks, or whole-run tests."""
    meta.attrs["split_scheme"] = scheme
    pos = np.arange(len(meta))
    folds = []
    if scheme == SI.GROUPED:
        groups = sorted(pd.unique(meta.group_id), key=lambda g: (
            meta.loc[meta.group_id == g, "origin_time"].min(), str(g)))
        if len(groups) < n_outer + 2:
            raise FailClosed("not enough whole runs for the requested outer folds")
        for fi in range(n_outer):
            test_group = groups[-(fi + 1)]
            te = pos[meta.group_id.eq(test_group).to_numpy()]
            pool = pos[meta.group_id.isin(groups[:-(fi + 1)]).to_numpy()]
            tr, ca = SI.refit_split(meta, pool, scheme)
            SI.assert_boundary(meta, np.concatenate([tr, ca]), te, scheme)
            folds.append(dict(train=tr, calibration=ca, test=te, scheme=scheme))
    else:
        times = np.sort(meta.origin_time.unique())
        seg = len(times) // (n_outer + 2)
        if seg < 20:
            raise FailClosed("too few distinct origins for the requested outer folds")
        for fi in range(n_outer):
            start = seg * (n_outer + 1 - fi)
            end = len(times) if fi == 0 else start + seg
            te = pos[meta.origin_time.isin(times[start:end]).to_numpy()]
            pool = pos[((meta.origin_time < times[start]) &
                        (meta.target_time < times[start])).to_numpy()]
            tr, ca = SI.refit_split(meta, pool, scheme)
            SI.assert_boundary(meta, np.concatenate([tr, ca]), te, scheme)
            folds.append(dict(train=tr, calibration=ca, test=te, scheme=scheme))
    return folds


def inner_split(meta, trc_idx, scheme, horizon, freq):
    """The existing 50/25/25 inner holdout, purged at BOTH boundaries."""
    try:
        tr, ca, se = SI.ordered_blocks(meta, trc_idx, [.5, .25, .25], scheme)
    except ValueError as exc:
        raise FailClosed(str(exc)) from exc
    if min(map(len, (tr, ca, se))) < 10:
        raise FailClosed("inner split produced a block below 10 windows")
    return dict(inner_train=tr, inner_calib=ca, inner_select=se)


# --------------------------------------------------------------------------- #
# Fitting
# --------------------------------------------------------------------------- #
def _fit_point(method: str, X_tr, y_tr, X_eval, meta_tr, meta_eval, freq, horizon, seed=42):
    """Return point predictions on ``X_eval`` for the requested point model."""
    if method == "persistence":
        # y_t (target_lag_0) is a feature; persistence == that column.
        col = next((c for c in X_eval.columns if c.endswith("target_lag_0")), None)
        if col is not None:
            return X_eval[col].to_numpy(dtype=float)
        return np.full(len(X_eval), float(np.nanmean(y_tr)))
    if method == "xgboost":
        res = xgboost_model.tune(X_tr, pd.Series(y_tr), n_iter=4, n_splits=2,
                                 seed=seed, n_jobs=1, meta_train=meta_tr)
        return xgboost_model.predict(res["estimator"], X_eval)
    raise FailClosed(f"unknown point model {method!r}")


def _interval(method, X_tr, y_tr, X_ca, y_ca, X_ev, y_ev, level, *,
              groups_ev, o_ev, t_ev, groups_ca, t_ca, horizon, seed=42):
    if method == "dscp":
        raise NotApplicable("dscp requires >= 2 horizons; single-horizon operation")
    m_ca = pd.DataFrame({"group_id": groups_ca, "target_time": t_ca})
    model = IntervalEstimator(method, level, X_tr, y_tr, X_ca, y_ca, m_ca, horizon, seed)
    return model.stream(X_ev, y_obs=y_ev, groups=groups_ev, o_te=o_ev, t_te=t_ev)


class NotApplicable(Exception):
    """A candidate that does not apply here — recorded with a reason, not fatal."""


# --------------------------------------------------------------------------- #
# Exposure-based event catalogue (D4)
# --------------------------------------------------------------------------- #
def exposure_event_catalogue(y, meta_block, freq, scale_map, incidence_per_day,
                             seed, dataset, *, warmup=6, guard=6, min_events=8):
    """Inject a group-safe, exposure-proportional synthetic-event catalogue (D4).

    The **block** event budget follows monitored asset-time,
    ``round(incidence x total_asset_days)``, with a viability floor
    (``min_events``) so a block of short runs — RICO's 2-4 h experiments would
    otherwise round to zero events per run and starve selection — still carries a
    balanced catalogue. The budget is distributed across the groups that are long
    enough to host an event, proportional to their asset-time (largest remainder).
    Events stay inside a group; attempted / placed / rejected and the requested vs
    realised incidence are recorded. A copy of ``y`` is perturbed; the clean array
    is returned untouched for the paired background-workload measurement.
    """
    y = np.asarray(y, dtype=float)
    groups = meta_block["group_id"].to_numpy()
    freq_min = pd.Timedelta(freq) / pd.Timedelta(minutes=1)
    perturbed = y.copy()
    dur = max(1, int(round(60.0 / freq_min)))
    min_len = warmup + guard + dur + 1

    uniq = list(pd.unique(groups))
    gpos = {g: np.nonzero(groups == g)[0] for g in uniq}
    asset_days = {g: (len(gpos[g]) * freq_min) / (60.0 * 24.0) for g in uniq}
    total_days = sum(asset_days.values())
    hostable = [g for g in uniq if len(gpos[g]) >= min_len]
    if not hostable:
        return perturbed, pd.DataFrame(), {
            "attempted": 0, "placed": 0, "rejected": 0,
            "requested_incidence_per_asset_day": incidence_per_day,
            "realised_incidence_per_asset_day": 0.0,
            "reason": "no group long enough to host an event"}

    budget = max(int(np.floor(incidence_per_day * total_days + 0.5)), int(min_events))
    floor_applied = budget > int(np.floor(incidence_per_day * total_days + 0.5))
    # Largest-remainder allocation across hostable groups by asset-time.
    host_days = np.array([asset_days[g] for g in hostable], float)
    share = host_days / host_days.sum() * budget
    alloc = np.floor(share).astype(int)
    rem = budget - int(alloc.sum())
    for j in np.argsort(-(share - np.floor(share)))[:max(0, rem)]:
        alloc[j] += 1

    rows, attempted, placed, rejected, eid = [], 0, 0, 0, 0
    for g, n_g in zip(hostable, alloc):
        if n_g < 1:
            continue
        specs = _balanced_specs(int(n_g), freq)
        attempted += len(specs)
        scale = float(scale_map.get(g, scale_map.get("__pooled__", 1.0)))
        rng = np.random.default_rng(seed + int(hashlib.sha256(str(g).encode()).hexdigest()[:8], 16) % 10_000)
        local = base_place(specs, len(gpos[g]), warmup, guard, seed + eid + 1)
        placed_here = {e["start_index"] for e in local}
        rejected += len(specs) - len(local)
        for e in local:
            s, en = e["start_index"], e["end_index"]
            gs, ge = gpos[g][s], gpos[g][en]
            if groups[gs] != groups[ge]:
                rejected += 1
                continue
            _apply_event(perturbed, gs, ge, e, scale, rng)
            rows.append({"event_id": eid, "event_type": e["type"],
                         "severity": e["severity"], "group_id": g,
                         "start_index": int(gs), "end_index": int(ge),
                         "duration_steps": int(ge - gs + 1)})
            placed += 1
            eid += 1
    catalog = pd.DataFrame(rows)
    return perturbed, catalog, {
        "attempted": attempted, "placed": placed, "rejected": rejected,
        "requested_incidence_per_asset_day": incidence_per_day,
        "realised_incidence_per_asset_day":
            (placed / total_days) if total_days else 0.0,
        "viability_floor_applied": bool(floor_applied)}


def _balanced_specs(n_events, freq):
    """Round-robin over type x severity so the catalogue is balanced."""
    freq_min = pd.Timedelta(freq) / pd.Timedelta(minutes=1)
    dur = max(1, int(round(60.0 / freq_min)))       # ~1h events, >= 1 step
    combos = [(t, s) for t in ("bias", "level_shift", "drift", "stuck")
              for s in (0.5, 1.0, 2.0)]
    specs = []
    for i in range(n_events):
        t, s = combos[i % len(combos)]
        specs.append({"type": t, "severity": f"{s}sd", "magnitude_sd": s,
                      "duration": 1 if t == "spike" else dur,
                      "sign": +1 if i % 2 == 0 else -1})
    return specs


def base_place(specs, n, warmup, guard, seed):
    from .alerts import _place_events
    return _place_events(specs, n, warmup=warmup, guard=guard, seed=seed)


def _apply_event(arr, s, e, spec, scale, rng):
    mag = spec["magnitude_sd"] * scale
    sign = spec.get("sign", 1)
    if spec["type"] in ("bias", "level_shift"):
        arr[s:e + 1] += sign * mag
    elif spec["type"] == "drift":
        arr[s:e + 1] += np.linspace(0.0, sign * mag, e - s + 1)
    elif spec["type"] == "stuck":
        arr[s:e + 1] = arr[s]
    elif spec["type"] == "spike":
        arr[s] += sign * mag


# --------------------------------------------------------------------------- #
# Alerting on a chosen interval stream (C3/E, D2/D3/D6/D8)
# --------------------------------------------------------------------------- #
def _rule_dict(pipe) -> dict:
    """Reconstruct the alert-rule dict a frozen pipeline should run."""
    if pipe.rule_name == "single" or pipe.rule_m == 1:
        return {"name": "single", "immediate": True, "required": 1}
    return {"name": pipe.rule_name, "window_minutes": pipe.rule_window_minutes,
            "required": pipe.rule_k}


def alert_on_stream(observed, lower, upper, groups, meta_block, catalog, rule,
                    freq, tolerance_steps):
    """Run physical-time k-of-m alerting on exactly the given interval stream."""
    freq_min = pd.Timedelta(freq) / pd.Timedelta(minutes=1)
    if rule.get("immediate"):
        # Single-violation alert: 1-of-1 step, applicable at any sampling rate.
        k, m, rule_name = 1, 1, rule["name"]
    else:
        conv = AC.convert_physical_rule(rule["window_minutes"], rule["required"],
                                        freq_min, name=rule["name"])
        if not conv.applicable:
            raise NotApplicable(conv.reason)
        k, m, rule_name = conv.k, conv.m_steps, conv.name
    viol = AC.point_violations(observed, lower, upper)
    alerts = AC.apply_rule_grouped(viol, k, m, groups)
    episodes = AC.alert_episodes(alerts, groups)
    match = AC.match_events(episodes, catalog, tolerance_steps=tolerance_steps,
                            freq_minutes=freq_min)
    recall = AC.macro_event_recall(match["per_event"])
    workload = AC.background_workload_per_asset_day(
        match["n_background_episodes"], groups, freq_min)
    return {"rule": rule_name, "k": k, "m": m,
            **recall, **workload, "n_detected": match["n_detected"],
            "n_events": match["n_events"], "lower": lower, "upper": upper,
            "per_event": match["per_event"]}


SINGLE_RULE = {"name": "single", "immediate": True, "required": 1}
PHYSICAL_RULES = [
    SINGLE_RULE,
    {"name": "k2_w5", "window_minutes": 5, "required": 2},
    {"name": "k3_w15", "window_minutes": 15, "required": 3},
    {"name": "k3_w30", "window_minutes": 30, "required": 3},
    {"name": "k4_w60", "window_minutes": 60, "required": 4},
    {"name": "k3_w180", "window_minutes": 180, "required": 3},
    {"name": "k4_w360", "window_minutes": 360, "required": 4},
]


# --------------------------------------------------------------------------- #
# Interval cache and recalibration streams
# --------------------------------------------------------------------------- #
def _all_intervals(X_tr, y_tr, X_ca, y_ca, X_ev, y_ev, levels, *,
                   groups_ev, o_ev, t_ev, groups_ca, t_ca, horizon, seed=42):
    """Shared fits, but method-specific calibration predictions and identity."""
    import copy
    out, notes, calib_pts = {}, {}, {}
    m_ca = pd.DataFrame({"group_id": groups_ca, "target_time": t_ca})
    enb = None
    for level in levels:
        cqr = IntervalEstimator("cqr", level, X_tr, y_tr, X_ca, y_ca, m_ca, horizon, seed)
        if enb is None:
            enb = IntervalEstimator("recentred_enbpi_static", level, X_tr, y_tr,
                                    X_ca, y_ca, m_ca, horizon, seed)
        for method in INTERVAL_METHODS:
            if method == "dscp":
                notes[(method, level)] = "requires multi-horizon quality evaluation; not run by alert core"
                continue
            model = copy.copy(cqr if method in ("cqr", "quantile_uncalibrated") else enb)
            model.method, model.level = method, level
            out[(method, level)] = model.stream(X_ev, y_obs=y_ev, groups=groups_ev,
                                                o_te=o_ev, t_te=t_ev)
            calib_pts[(method, level)] = model.point_ca
    return out, notes, calib_pts


def _recalibrated_stream(strategy, point, y_ca, point_ca, groups_ev, o_ev, t_ev,
                         groups_ca, t_ca, level, horizon, *, y_observed,
                         update_every=48, window=250, min_samples=30):
    return recalibrated_bounds(strategy, point, y_observed, y_ca, point_ca,
        groups_ev, o_ev, t_ev, groups_ca, t_ca, level, horizon,
        update_every=update_every, window=window, min_samples=min_samples)


def physical_rules(policy):
    declared = policy.get("alert_rules_physical")
    if not declared:
        return PHYSICAL_RULES
    return [SINGLE_RULE if r["required_violations"] == 1 and r["window_minutes"] == 1
            else {"name": r["name"], "window_minutes": r["window_minutes"],
                  "required": r["required_violations"]} for r in declared]


def catalogue_seed(policy, model_seed):
    models = policy.get("model_seeds", [model_seed])
    events = policy.get("event_seeds", [model_seed])
    if len(models) != len(events) or model_seed not in models:
        raise FailClosed("event/model seed pairing is not declared")
    return int(events[models.index(model_seed)])


# --------------------------------------------------------------------------- #
# Inner selection (D1: method+level; recal; rule; D7 abstention)
# --------------------------------------------------------------------------- #
def select_on_inner(dataset, horizon, seed, fold_i, meta, X, y, inner, cfg,
                    freq, scale_map, policy):
    """Choose the whole pipeline on inner data only; return a frozen Pipeline."""
    itr, ica, ise = inner["inner_train"], inner["inner_calib"], inner["inner_select"]
    scheme = meta.attrs.get("split_scheme", "chronological")
    SI.assert_boundary(meta, itr, ica, scheme)
    SI.assert_boundary(meta, ica, ise, scheme)
    for block, name in ((itr, "train"), (ica, "calibration"), (ise, "selection")):
        if len(block) < policy.get(f"min_{name}_windows", 10):
            raise FailClosed(f"inner {name} below declared minimum window count")
    if len(ica) < policy.get("min_calibration_for_level", 10):
        raise FailClosed("inner calibration below declared interval-level minimum")
    Xtr, ytr = X.iloc[itr], y[itr]
    Xca, yca = X.iloc[ica], y[ica]
    Xse, yse = X.iloc[ise], y[ise]
    m_se = meta.iloc[ise]; m_ca = meta.iloc[ica]
    g_se = m_se["group_id"].to_numpy(); g_ca = m_ca["group_id"].to_numpy()
    o_se = pd.DatetimeIndex(m_se["origin_time"]); t_se = pd.DatetimeIndex(m_se["target_time"])
    t_ca = pd.DatetimeIndex(m_ca["target_time"])
    levels = [lv for lv in policy["operating_levels"]]
    tol = int(cfg.get("alerts", {}).get("detection_tolerance_steps", 6))

    # Interval methods own their predictor. Separate point benchmarking is not
    # an operational model-selection input and must not label these intervals.
    # ---- interval streams on inner-selection ----
    intervals, notes, calib_pts = _all_intervals(
        Xtr, ytr, Xca, yca, Xse, yse, levels, groups_ev=g_se, o_ev=o_se,
        t_ev=t_se, groups_ca=g_ca, t_ca=t_ca, horizon=horizon, seed=seed)

    # ---- exposure events on inner-selection (deterministic) ----
    perturbed, catalog, alloc = exposure_event_catalogue(
        yse, m_se, freq, scale_map, policy["incidence"], catalogue_seed(policy, seed) + 100, dataset)
    if catalog.empty:
        raise FailClosed("inner-selection produced no injectable events")

    rows = []
    for (method, level), iv in intervals.items():
        point = np.asarray(iv["point"], float)
        point_ca = calib_pts[(method, level)]
        for recal in policy.get("recalibration_strategies", ("static", "periodic", "rolling")):
            if recal == "static":
                lo, hi = iv["lower"], iv["upper"]
            else:
                lo, hi = _recalibrated_stream(
                    recal, point, yca, point_ca, g_se, o_se, t_se, g_ca, t_ca,
                    level, horizon, y_observed=yse)
            for rule in physical_rules(policy):
                try:
                    sc = alert_on_stream(perturbed, lo, hi, g_se, m_se, catalog,
                                         rule, freq, tol)
                except NotApplicable:
                    continue
                rows.append({"interval_method": method, "operating_level": level,
                             "estimator_class": iv["identity"]["estimator_class"],
                             "model_seed": seed, "event_seed": catalogue_seed(policy, seed),
                             "fallback": json.dumps(iv["identity"]["fallback"]),
                             "recalibration": recal, "rule": sc["rule"],
                             "rule_immediate": bool(rule.get("immediate", False)),
                             "rule_window_minutes": rule.get("window_minutes", 0),
                             "rule_required": rule["required"],
                             "macro_recall": sc["macro_recall"],
                             "background_episodes_per_asset_day":
                                 sc["background_episodes_per_asset_day"],
                             "median_detection_delay_min": np.nan})
    surface = pd.DataFrame(rows)
    freq_min = pd.Timedelta(freq) / pd.Timedelta(minutes=1)

    def _pipe_from_row(r, reason):
        if r.get("rule_immediate"):
            k, m, wm = 1, 1, 0.0
        else:
            conv = AC.convert_physical_rule(r["rule_window_minutes"],
                                            int(r["rule_required"]), freq_min,
                                            name=r["rule"])
            k, m, wm = conv.k, conv.m_steps, float(r["rule_window_minutes"])
        return Pipeline(
            dataset=dataset, horizon=horizon, seed=seed, outer_fold=fold_i,
            point_model=intervals[(r["interval_method"], float(r["operating_level"]))]["identity"]["estimator_class"].split(".")[-1],
            estimator_class=intervals[(r["interval_method"], float(r["operating_level"]))]["identity"]["estimator_class"],
            fallback=intervals[(r["interval_method"], float(r["operating_level"]))]["identity"]["fallback"],
            event_seed=catalogue_seed(policy, seed), interval_method=r["interval_method"],
            operating_level=float(r["operating_level"]),
            recalibration=r["recalibration"], rule_name=str(r["rule"]), rule_k=k,
            rule_m=m, rule_window_minutes=wm, selection_reason=reason).freeze()

    decision = AC.select_pipeline(surface, min_recall=policy["min_recall"],
                                  workload_max=policy["workload_max"],
                                  use_confidence_bounds=False)
    # Best-effort row (numerically best recall, then lowest workload) — used only
    # for the diagnostic ablation/outer evaluation when the operational policy
    # abstains, never presented as an operational choice.
    be = surface.sort_values(["macro_recall", "background_episodes_per_asset_day"],
                             ascending=[False, True]).iloc[0]
    best_effort = _pipe_from_row(be, "best_effort_diagnostic_only")
    common = {"surface": surface, "point_model": best_effort.point_model,
              "notes": {str(k): v for k, v in notes.items()},
              "event_allocation": alloc, "best_effort": best_effort}
    if decision["decision"] == AC.NO_FEASIBLE:
        return {"decision": AC.NO_FEASIBLE, "reason": decision["reason"], **common}
    ch = decision["chosen"]
    pipe = _pipe_from_row(ch, decision["reason"])
    return {"decision": "selected", "pipeline": pipe, **common}


# --------------------------------------------------------------------------- #
# Outer evaluation of the frozen pipeline (C3/E) + ablation
# --------------------------------------------------------------------------- #
def _fit_interval_on(method, level, X, y, tr_ca, te, meta, horizon, seed=42):
    """Fit on purged train/calibration blocks; retain this model's calibration points."""
    itr, ica = SI.refit_split(meta, tr_ca)
    SI.assert_boundary(meta, np.concatenate([itr, ica]), te,
                       meta.attrs.get("split_scheme", "chronological"))
    m_ca = meta.iloc[ica]; m_te = meta.iloc[te]
    iv = _interval(
        method, X.iloc[itr], y[itr], X.iloc[ica], y[ica], X.iloc[te], y[te],
        level, groups_ev=m_te["group_id"].to_numpy(),
        o_ev=pd.DatetimeIndex(m_te["origin_time"]),
        t_ev=pd.DatetimeIndex(m_te["target_time"]),
        groups_ca=m_ca["group_id"].to_numpy(),
        t_ca=pd.DatetimeIndex(m_ca["target_time"]), horizon=horizon, seed=seed)
    return iv, (ica, m_ca), iv["calibration_point"]


def evaluate_outer(pipe, meta, X, y, tr_ca, te, cfg, freq, scale_map, policy):
    """Evaluate exactly the frozen pipeline on the outer-test fold (C3/E)."""
    m_te = meta.iloc[te]
    g_te = m_te["group_id"].to_numpy()
    o_te = pd.DatetimeIndex(m_te["origin_time"]); t_te = pd.DatetimeIndex(m_te["target_time"])
    tol = int(cfg.get("alerts", {}).get("detection_tolerance_steps", 6))

    iv, (ica, m_ca), point_ca = _fit_interval_on(
        pipe.interval_method, pipe.operating_level, X, y, tr_ca, te, meta,
        pipe.horizon, seed=pipe.seed)
    if (pipe.estimator_class != iv["identity"]["estimator_class"] or
        pipe.point_model != iv["identity"]["estimator_class"].split(".")[-1] or
        pipe.fallback != iv["identity"]["fallback"]):
        raise FailClosed("recorded predictor identity differs from evaluated estimator")
    point = np.asarray(iv["point"], float)
    if pipe.recalibration == "static":
        lo, hi = iv["lower"], iv["upper"]
    else:
        lo, hi = _recalibrated_stream(
            pipe.recalibration, point, y[ica], point_ca, g_te, o_te, t_te,
            m_ca["group_id"].to_numpy(), pd.DatetimeIndex(m_ca["target_time"]),
            pipe.operating_level, pipe.horizon, y_observed=y[te])

    perturbed, catalog, alloc = exposure_event_catalogue(
        y[te], m_te, freq, scale_map, policy["incidence"], (pipe.event_seed if pipe.event_seed is not None else pipe.seed) + 100,
        pipe.dataset)
    sc = alert_on_stream(perturbed, lo, hi, g_te, m_te, catalog,
                         _rule_dict(pipe), freq, tol)

    # ---- fail-closed integrity gates ----
    reeval_hash = Pipeline(**{**asdict(pipe), "config_hash": ""}).freeze().config_hash
    if reeval_hash != pipe.config_hash:
        raise FailClosed("selected config hash != evaluated config hash")
    if not (np.array_equal(sc["lower"], lo) and np.array_equal(sc["upper"], hi)):
        raise FailClosed("alert-consumed bounds != selected recalibrated bounds")
    cov = M.empirical_coverage(y[te], lo, hi)
    row = {"dataset": pipe.dataset, "horizon": pipe.horizon, "seed": pipe.seed,
           "outer_fold": pipe.outer_fold, "config_hash": pipe.config_hash,
           "point_model": pipe.point_model, "estimator_class": iv["identity"]["estimator_class"],
           "model_seed": pipe.seed, "event_seed": pipe.event_seed,
           "fallback": json.dumps(iv["identity"]["fallback"]), "interval_method": pipe.interval_method,
           "operating_level": pipe.operating_level, "recalibration": pipe.recalibration,
           "rule": pipe.rule_name, "empirical_coverage": cov,
           "macro_recall": sc["macro_recall"],
           "background_episodes_per_asset_day": sc["background_episodes_per_asset_day"],
           "n_detected": sc["n_detected"], "n_events": sc["n_events"],
           "events_placed": alloc["placed"]}
    # Per-group and per-event detail so a downstream CI stage can resample the
    # correct units (runs for RICO, buildings for BDG2, blocks for series).
    ge = np.asarray(g_te)
    per_group = []
    tag = dict(dataset=pipe.dataset, seed=pipe.seed, outer_fold=pipe.outer_fold)
    for g in pd.unique(ge):
        gm = ge == g
        per_group.append({**tag, "group_id": g,
                          "empirical_coverage": M.empirical_coverage(
                              y[te][gm], np.asarray(lo)[gm], np.asarray(hi)[gm]),
                          "n": int(gm.sum())})
    per_event = sc["per_event"].copy()
    for k_, v_ in tag.items():
        per_event[k_] = v_
    row.update(mae=M.mae(y[te], point), rmse=M.rmse(y[te], point),
               mean_interval_width=M.mean_interval_width(lo, hi),
               winkler=M.winkler_score(y[te], lo, hi, 1 - pipe.operating_level))
    calibration = m_ca[["group_id", "origin_time", "target_time"]].copy()
    calibration["y_true"], calibration["point"] = y[ica], point_ca
    return row, {"point": point, "lower": lo, "upper": hi,
                 "event_observed": perturbed, "calibration": calibration}, pd.DataFrame(per_group), per_event


def evaluate_ablation(pipe, meta, X, y, tr_ca, te, cfg, freq, scale_map, policy):
    """Four levels on the same outer fold and event catalogue."""
    m_te = meta.iloc[te]; g_te = m_te["group_id"].to_numpy()
    tol = int(cfg.get("alerts", {}).get("detection_tolerance_steps", 6))
    perturbed, catalog, _ = exposure_event_catalogue(
        y[te], m_te, freq, scale_map, policy["incidence"], (pipe.event_seed if pipe.event_seed is not None else pipe.seed) + 100,
        pipe.dataset)
    lvl = pipe.operating_level
    full_rule = _rule_dict(pipe)
    specs = {
        "baseline": ("quantile_uncalibrated", SINGLE_RULE, "static"),
        "conformal_only": ("cqr", SINGLE_RULE, "static"),
        "temporal": ("cqr", full_rule, "static"),
        "full": (pipe.interval_method, full_rule, pipe.recalibration),
    }
    rows = []
    for level_name, (method, rule, recal) in specs.items():
        try:
            iv, (ica, m_ca), point_ca = _fit_interval_on(method, lvl, X, y, tr_ca,
                                                          te, meta, pipe.horizon, seed=pipe.seed)
        except NotApplicable as na:
            rows.append({"ablation": level_name, "applicable": False, "reason": str(na)})
            continue
        lo, hi = iv["lower"], iv["upper"]
        if recal != "static":
            lo, hi = _recalibrated_stream(
                recal, np.asarray(iv["point"], float), y[ica], point_ca, g_te,
                pd.DatetimeIndex(m_te["origin_time"]),
                pd.DatetimeIndex(m_te["target_time"]), m_ca["group_id"].to_numpy(),
                pd.DatetimeIndex(m_ca["target_time"]), lvl, pipe.horizon,
                y_observed=y[te])
        try:
            sc = alert_on_stream(perturbed, lo, hi, g_te, m_te, catalog, rule, freq, tol)
        except NotApplicable as na:
            rows.append({"ablation": level_name, "applicable": False, "reason": str(na)})
            continue
        rows.append({"ablation": level_name, "applicable": True,
                     "dataset": pipe.dataset, "seed": pipe.seed,
                     "outer_fold": pipe.outer_fold, "interval_method": method,
                     "estimator_class": iv["identity"]["estimator_class"],
                     "model_seed": pipe.seed, "event_seed": pipe.event_seed,
                     "fallback": json.dumps(iv["identity"]["fallback"]),
                     "recalibration": recal, "rule": sc["rule"],
                     "macro_recall": sc["macro_recall"],
                     "background_episodes_per_asset_day":
                         sc["background_episodes_per_asset_day"]})
    return rows


# --------------------------------------------------------------------------- #
# Per-dataset driver and engine
# --------------------------------------------------------------------------- #
def _policy_from_cfg(cfg, fast):
    pr = cfg.get("protocol", {})
    if fast:
        # Two levels keep the integration smoke quick; not a results run.
        levels = (cfg.get("defaults", {}).get("coverage_levels")
                  or cfg.get("coverage_levels", [0.9, 0.95]))[:2]
    else:
        # The full run selects the operating alert level among the protocol's
        # operating levels (all > 0.95 supported), per D1/D10.
        levels = list(pr.get("operating_levels", [0.95, 0.975, 0.99, 0.995]))
    return {"operating_levels": list(levels),
            "incidence": float(pr.get("event_incidence_per_asset_day", 0.5)),
            "min_recall": float(pr.get("min_recall", 0.6)),
            "workload_max": float(pr.get("workload_max", 1.0)),
            "model_seeds": pr.get("seeds_model", [42, 43, 44, 45, 46]),
            "event_seeds": pr.get("seeds_event_catalogue", [42, 43, 44, 45, 46]),
            "alert_rules_physical": pr.get("alert_rules_physical"),
            **{k: pr.get(k, 10) for k in ("min_train_windows", "min_calibration_windows",
                "min_selection_windows", "min_calibration_for_level")},
            "recalibration_strategies": pr.get("recalibration_strategies", ["static", "periodic", "rolling"])}


def run_dataset(dataset_id, cfg, prepared, out_dir, seeds, n_outer, freq, fast,
                *, resume=False):
    """Checkpoint each complete selection/evaluation unit, including bounds."""
    out = Path(out_dir)
    horizon = int(cfg.get("alerts", {}).get("primary_horizon", cfg.get("horizons", [1])[0]))
    fcfg = windowing.feature_config(cfg, prepared.series[0].covariates)
    w = windowing.build_dataset_windows(prepared, horizon, fcfg)
    meta, X, y = w["meta"], w["X"], w["y"]
    scheme = "chronological" if isinstance(prepared.partitioner, ChronologicalPartitioner) else SI.GROUPED
    folds = make_outer_folds(meta, scheme, n_outer, horizon, freq)
    policy = _policy_from_cfg(cfg, fast)
    data_hash = hashlib.sha256(pd.util.hash_pandas_object(X, index=False).values.tobytes()
        + pd.util.hash_pandas_object(meta, index=False).values.tobytes()).hexdigest()
    spec = dict(dataset=dataset_id, horizon=horizon, seeds=list(seeds), n_outer=n_outer,
                fast=fast, config=cfg, source_hash=source_digest(), data_hash=data_hash,
                execution_scope="interval_owned_alert_core", integration_version=1)
    store = UnitCheckpoint(out, spec, resume=resume)
    windowing.persist_feature_schema(w, dataset_id, out / "data_profiles")
    expected = [f"h{horizon}_f{fi}_s{seed}_e{catalogue_seed(policy, seed)}"
                for seed in seeds for fi in range(len(folds))]
    if len(expected) != len(set(expected)):
        raise FailClosed("duplicate requested core units")
    selections, outers, ablations, allocations, provenance, pgs, pes = [], [], [], [], [], [], []
    for seed in seeds:
        for fi, fold in enumerate(folds):
            key = f"h{horizon}_f{fi}_s{seed}_e{catalogue_seed(policy, seed)}"
            loaded = store.load(key) if resume else None
            if loaded is None:
                trc = np.concatenate([fold["train"], fold["calibration"]])
                inner = inner_split(meta, trc, scheme, horizon, freq)
                inner_scale = SI.training_scale(y, meta, inner["inner_train"])
                refit_train, refit_calib = SI.refit_split(meta, trc, scheme)
                if (len(refit_train) < policy["min_train_windows"] or
                    len(refit_calib) < max(policy["min_calibration_windows"],
                                           policy["min_calibration_for_level"])):
                    raise FailClosed("outer refit below declared train/calibration minimum")
                outer_scale = SI.training_scale(y, meta, refit_train)
                sel = select_on_inner(dataset_id, horizon, seed, fi, meta, X, y,
                                      inner, cfg, freq, inner_scale, policy)
                feasible = sel["decision"] == "selected"
                pipe = sel["pipeline"] if feasible else sel["best_effort"]
                selection = dict(decision=sel["decision"], reason=sel.get("reason", ""), **asdict(pipe))
                row, bounds, pg, pe = evaluate_outer(pipe, meta, X, y, trc,
                    fold["test"], cfg, freq, outer_scale, policy)
                row["operational_feasible"] = feasible
                abl = evaluate_ablation(pipe, meta, X, y, trc, fold["test"], cfg,
                                       freq, outer_scale, policy)
                for r in abl:
                    r["operational_feasible"] = feasible
                allocation = dict(dataset=dataset_id, seed=seed, outer_fold=fi,
                                  **sel["event_allocation"])
                prov = {**asdict(pipe), "operational_feasible": feasible,
                    "integration_version": 1, "notes": sel["notes"],
                    "inner_train_membership": SI.membership_hash(meta, inner["inner_train"]),
                    "outer_train_membership": SI.membership_hash(meta, refit_train),
                    "inner_scale": {str(k): v for k, v in inner_scale.items()},
                    "outer_scale": {str(k): v for k, v in outer_scale.items()}}
                predictions = meta.iloc[fold["test"]][["group_id", "origin_time", "target_time"]].copy()
                predictions["y_true"] = y[fold["test"]]
                for name in ("point", "lower", "upper", "event_observed"):
                    predictions[name] = bounds[name]
                payload = dict(selection=selection, outer=row, ablation=abl,
                               allocation=allocation, provenance=prov)
                frames = dict(predictions=predictions, calibration=bounds["calibration"],
                              per_group=pg, per_event=pe, selection_surface=sel["surface"])
                store.save(key, payload, frames)
            else:
                payload, frames = loaded
            selections.append(payload["selection"]); outers.append(payload["outer"])
            ablations.extend(payload["ablation"]); allocations.append(payload["allocation"])
            provenance.append(payload["provenance"])
            pgs.append(frames["per_group"]); pes.append(frames["per_event"])
            print(f"[{dataset_id}] {key}: {'resumed' if loaded else 'checkpointed'}", flush=True)
    store.require_complete(expected)
    for name, rows in [("selection", selections), ("outer_metrics", outers),
                       ("ablation", ablations), ("event_allocation", allocations)]:
        pd.DataFrame(rows).to_csv(out / (name + ".csv"), index=False)
    pd.concat(pgs, ignore_index=True).to_csv(out / "outer_per_group_coverage.csv", index=False)
    pd.concat(pes, ignore_index=True).to_csv(out / "outer_per_event.csv", index=False)
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2, default=str), encoding="utf-8")
    return dict(n_folds=len(folds), n_outer_rows=len(outers), n_ablation_rows=len(ablations),
                ablation_levels=sorted({r["ablation"] for r in ablations}),
                complete_units=len(expected), execution_scope="interval_owned_alert_core")


def run_engine(config_path, datasets, out_root, *, fast, seeds=None, resume=False):
    """Run the nested corrected engine across datasets into ``out_root``."""
    from .run_study import load_config, resolve_dataset_config
    from .datasets import get_adapter
    from . import protocol as P

    study = load_config(config_path)
    proto_path = study.get("protocol_ref", {}).get(
        "path", "outputs/final_dissertation_v2/protocol/frozen_protocol.yaml")
    proto = P.load_protocol(proto_path)
    resolved = P.compile_to_config(proto, study)
    seeds = seeds or ([proto.seeds.model[0]] if fast else list(proto.seeds.model))
    n_outer = 2 if fast else proto.partitioning.outer_folds
    out_root = Path(out_root); out_root.mkdir(parents=True, exist_ok=True)
    summary = {}
    for ds in datasets:
        cfg = resolve_dataset_config(study, ds)
        cfg["protocol"] = resolved["protocol"]
        cfg.setdefault("defaults", {})["coverage_levels"] = \
            resolved["defaults"]["coverage_levels"]
        adapter = get_adapter(cfg.get("adapter", ds))
        prepared = SI.causal_prepared(adapter.prepare(cfg),
            cfg.get("missing", {}).get("max_short_gap_steps", 3))
        if hasattr(prepared.partitioner, "fit"):
            try:
                prepared.partitioner.fit(prepared.series)
            except Exception:                               # noqa: BLE001
                pass
        summary[ds] = run_dataset(ds, cfg, prepared, out_root / ds, seeds,
                                  n_outer, prepared.freq, fast, resume=resume)
    (out_root / "engine_summary.json").write_text(
        json.dumps({"fast": fast, "datasets": summary, "integration_version": 1,
                    "execution_scope": "interval_owned_alert_core",
                    "full_declared_methodology_complete": False,
                    "protocol_hash": P.protocol_hash(proto_path)},
                   indent=2, default=str), encoding="utf-8")
    return summary


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Run the nested corrected study engine.")
    ap.add_argument("--config", default="configs/study_final_dissertation_v2.yaml")
    ap.add_argument("--dataset", action="append", default=None)
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--out", default="outputs/final_dissertation_v2/runs/engine_smoke")
    args = ap.parse_args()
    datasets = args.dataset or ["pleia", "pleia_energy", "rico", "bdg2"]
    summary = run_engine(args.config, datasets, args.out, fast=args.fast, resume=args.resume)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
