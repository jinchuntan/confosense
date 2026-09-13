"""Predeclared robustness / contamination / recovery extension (amendment 003).

Evaluates, for every core-run unit (dataset × outer fold × model seed) and that
unit's own frozen pipeline (read from the immutable core run's provenance):

* **Closed-loop faults** — the observed test stream is corrupted inside the
  predeclared [25%, 55%) window of each group's test span and the supervised
  features are **rebuilt from the corrupted series**, so corrupted readings feed
  the lagged/rolling inputs of every subsequent prediction. Coverage is always
  measured against the clean ground truth (the fault corrupts the sensor, not
  reality); alerts fire on what the operator would see (the corrupted stream).
  A zero-severity control runs the identical machinery with magnitude 0 and must
  reproduce the clean cell exactly.
* **Calibration contamination** — a predeclared fraction of calibration targets
  is biased by +2σ before the conformity scores are formed; the evaluated test
  stream stays clean. The contamination family (clean-reference + contaminated)
  uses the split-conformal residual-offset construction uniformly so the paired
  contrast isolates the contamination (documented deviation from per-method
  intervals).
* **Recalibration recovery** — a level-shift fault with recalibration policies
  {static, periodic, rolling}, consuming only causally available (delayed,
  corrupted) residuals via :class:`~src.residuals.DelayedResidualPool`; recovery
  is the predeclared rolling-coverage criterion, censored if never reached.

The extension also persists what the Phase-1 audit flagged as missing: interval
widths and Winkler scores per cell, and clean-test point MAE/RMSE for
persistence vs the tuned XGBoost model (RQ1 evidence), with wall-clock timing.

Everything writes to a new timestamped run directory; the core run
``full_20260831_220811`` is never touched.
"""

from __future__ import annotations

import json
import hashlib
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from . import (alerts_corrected as AC, conformal_cqr, conformal_quantile,
               metrics as M, recalibration, windowing, xgboost_model)
from .conformal_enbpi import _updated_intervals_causal
from .corrected_study import make_outer_folds
from .datasets.base import ChronologicalPartitioner
from .residuals import DelayedResidualPool
from . import split_integrity as SI
from .interval_stream import IntervalEstimator, recalibrated_bounds, group_mask
from .unit_checkpoint import UnitCheckpoint, source_digest, digest, require_cells

FAULT_TYPES = ("random_missing", "dropout", "stuck", "level_shift", "drift")
MAGNITUDE_FAULTS = {"level_shift", "drift"}          # others have no magnitude dim
WINDOW_FRAC = (0.25, 0.55)
SEGMENTS = {"pre": (0.0, 0.25), "during": (0.25, 0.55), "post": (0.55, 1.0)}
RANDOM_MISSING_FRACTION = 0.2


# --------------------------------------------------------------------------- #
# Fault application on a series frame (test-window only, per group)
# --------------------------------------------------------------------------- #
def apply_fault_to_frame(frame: pd.DataFrame, window: pd.DatetimeIndex,
                         kind: str, magnitude: float, seed: int) -> pd.DataFrame:
    """Corrupt ``target`` inside ``window`` on a copy of ``frame``.

    ``magnitude`` is already in target units (severity_sd x per-group train-only
    robust sigma). ``magnitude == 0`` must be the identity for every kind — the
    zero-severity control depends on it.
    """
    out = frame.copy()
    idx = out.index.intersection(window)
    if len(idx) == 0:
        return out
    tgt = out["target"]
    if kind == "level_shift":
        out.loc[idx, "target"] = tgt.loc[idx] + magnitude
    elif kind == "drift":
        ramp = np.linspace(0.0, magnitude, len(idx))
        out.loc[idx, "target"] = tgt.loc[idx] + ramp
    elif kind == "stuck":
        if magnitude != 0.0:
            out.loc[idx, "target"] = float(tgt.loc[idx[0]])
    elif kind == "dropout":
        if magnitude != 0.0:
            pos = out.index.get_indexer([idx[0]])[0]
            hold = float(tgt.iloc[pos - 1]) if pos > 0 else float(tgt.loc[idx[0]])
            out.loc[idx, "target"] = hold
    elif kind == "random_missing":
        if magnitude != 0.0:
            rng = np.random.default_rng(seed)
            pick = rng.random(len(idx)) < RANDOM_MISSING_FRACTION
            hit = idx[pick]
            # gap-filled telemetry: each missing step shows the last clean value
            vals = tgt.copy()
            vals.loc[hit] = np.nan
            out["target"] = vals.ffill()
    else:
        raise ValueError(f"unknown fault kind {kind!r}")
    return out


def group_test_windows(meta: pd.DataFrame, te: np.ndarray,
                       frac: tuple[float, float]) -> dict:
    """Per-group fault window (DatetimeIndex of target times) inside the test span."""
    m_te = meta.iloc[te]
    out = {}
    for g, sub in m_te.groupby("group_id", dropna=False, sort=False):
        tt = pd.DatetimeIndex(sub["target_time"]).sort_values()
        n = len(tt)
        lo, hi = int(np.floor(frac[0] * n)), int(np.floor(frac[1] * n))
        out[g] = tt[lo:hi]
    return out


def segment_masks(meta: pd.DataFrame, te: np.ndarray) -> dict[str, np.ndarray]:
    """Boolean masks over the test rows for pre/during/post, per group position."""
    m_te = meta.iloc[te].reset_index(drop=True)
    masks = {k: np.zeros(len(te), dtype=bool) for k in SEGMENTS}
    for _, sub in m_te.groupby("group_id", dropna=False, sort=False):
        pos_in_te = sub.index.to_numpy()
        order = np.argsort(pd.DatetimeIndex(sub["target_time"]).values,
                           kind="stable")
        n = len(pos_in_te)
        ranks = np.empty(n, dtype=float)
        ranks[order] = np.arange(n) / max(1, n)
        for k, (lo, hi) in SEGMENTS.items():
            seg = (ranks >= lo) & ((ranks < hi) if hi < 1.0 else (ranks <= hi))
            masks[k][pos_in_te[seg]] = True
    return masks


def _window_for_series(windows: dict, group_id):
    """The fault window for one series (single-series datasets key by NaN)."""
    if group_id in windows:
        return windows[group_id]
    if len(windows) == 1:
        return next(iter(windows.values()))
    for k, v in windows.items():
        if str(k) == str(group_id):
            return v
    return pd.DatetimeIndex([])


# --------------------------------------------------------------------------- #
# One-time model fit per unit; per-cell prediction
# --------------------------------------------------------------------------- #
# Public compatibility name; core and extension now use one implementation.
UnitModel = IntervalEstimator


# --------------------------------------------------------------------------- #
# Cell scoring
# --------------------------------------------------------------------------- #
def score_cell(y_clean, y_obs, lower, upper, groups, meta_te, masks, freq_min,
               rule_k, rule_m, level, tolerance_steps):
    """Segmented coverage, alert behaviour and interval quality for one cell."""
    cover = (y_clean >= lower) & (y_clean <= upper)
    widths = upper - lower
    viol = AC.point_violations(y_obs, lower, upper)
    alerts = AC.apply_rule_grouped(viol, rule_k, rule_m, groups)
    episodes = AC.alert_episodes(alerts, groups)
    onsets = np.array([e["onset"] for e in episodes], dtype=int)

    during = masks["during"]; pre = masks["pre"]; post = masks["post"]
    tol = int(tolerance_steps)
    detections, delays = [], []
    for group in pd.unique(groups):
        positions = np.flatnonzero(group_mask(groups, group))
        local_during = np.flatnonzero(during[positions])
        local_onsets = np.flatnonzero(np.isin(positions, onsets))
        hits = local_onsets[(local_onsets >= local_during.min()) &
            (local_onsets <= local_during.max() + tol)] if len(local_during) else []
        detections.append(bool(len(hits)))
        delays.append(int(hits[0] - local_during.min()) if len(hits) else np.nan)
    # Single-group endpoints retain their meaning. Multi-group detection rate
    # is explicit; a pooled boolean/delay would hide which assets were hit.
    fault_detected = detections[0] if len(detections) == 1 else np.nan
    delay_steps = delays[0] if len(delays) == 1 else np.nan
    bg_onsets = onsets[(pre[onsets] | post[onsets])] if len(onsets) else onsets
    cascade = int(np.sum(post[onsets])) if len(onsets) else 0
    bg_days = (int(pre.sum() + post.sum()) * freq_min) / (60.0 * 24.0)

    def seg_cov(mask):
        return float(np.mean(cover[mask])) if mask.any() else np.nan

    wink = M.winkler_score(y_clean, lower, upper, 1.0 - level)
    row = {
        "coverage_pre": seg_cov(pre), "coverage_during": seg_cov(during),
        "coverage_post": seg_cov(post), "coverage_all": float(np.mean(cover)),
        "delta_coverage_during_vs_pre": seg_cov(during) - seg_cov(pre),
        "fault_detected": fault_detected,
        "fault_detection_rate": float(np.mean(detections)),
        "n_fault_groups": len(detections), "n_detected_groups": sum(detections),
        "detection_delay_steps": delay_steps,
        "background_episodes": int(len(bg_onsets)),
        "background_per_asset_day": (len(bg_onsets) / bg_days) if bg_days else np.nan,
        "post_fault_cascade_episodes": cascade,
        "n_episodes_total": len(episodes),
        "mean_width": float(np.mean(widths)),
        "median_width": float(np.median(widths)),
        "winkler": float(wink) if np.isscalar(wink) else float(np.nanmean(wink)),
    }
    return row


def time_to_recovery(cover, masks, freq_min, pre_cov):
    """Predeclared recovery criterion on the post segment; censored if never."""
    post = np.nonzero(masks["post"])[0]
    if len(post) < 10 or not np.isfinite(pre_cov):
        return np.nan, True
    day_steps = max(1, int(round(24 * 60 / freq_min)))
    w = max(10, min(day_steps, len(post) // 4))
    series = pd.Series(cover[post]).rolling(w, min_periods=w).mean()
    ok = series >= (pre_cov - 0.05)
    hit = np.nonzero(ok.to_numpy())[0]
    if len(hit) == 0:
        return np.nan, True
    return int(hit[0]), False


# --------------------------------------------------------------------------- #
# Unit evaluation
# --------------------------------------------------------------------------- #
def evaluate_unit(ds, prepared, meta, X, y, fold_i, fold, pipe_row, cfg, freq,
                  scale_map, fcfg, horizon, *, fast=False):
    """All predeclared cells for one (dataset, fold, seed) unit."""
    freq_min = freq / pd.Timedelta(minutes=1)
    te = fold["test"]
    trc = np.concatenate([fold["train"], fold["calibration"]])
    itr, ica = SI.refit_split(meta, trc)
    SI.assert_boundary(meta, np.concatenate([itr, ica]), te,
                       meta.attrs.get("split_scheme", "chronological"))
    m_te, m_ca = meta.iloc[te], meta.iloc[ica]
    g_te = m_te["group_id"].to_numpy()
    o_te = pd.DatetimeIndex(m_te["origin_time"]); t_te = pd.DatetimeIndex(m_te["target_time"])

    method = pipe_row["interval_method"]
    level = float(pipe_row["operating_level"])
    rule_k, rule_m = int(pipe_row["rule_k"]), int(pipe_row["rule_m"])
    recal = pipe_row["recalibration"]
    model_seed = int(pipe_row["seed"])
    seed = int(pipe_row.get("event_seed") if pipe_row.get("event_seed") is not None else model_seed)
    tol = int(cfg.get("alerts", {}).get("detection_tolerance_steps", 6))

    um = UnitModel(method, level, X.iloc[itr], y[itr], X.iloc[ica], y[ica],
                   m_ca, horizon, seed=model_seed)
    if (pipe_row.get("estimator_class") != um.estimator_class or
        pipe_row.get("fallback") != um.fallback):
        raise ValueError("extension requires repaired core predictor provenance")
    masks = segment_masks(meta, te)
    windows = group_test_windows(meta, te, WINDOW_FRAC)
    y_clean = y[te]
    streams = []
    group_recovery = []

    def recal_bounds(point, res_obs, strategy):
        return recalibrated_bounds(strategy, point, point + res_obs, um.y_ca,
            um.point_ca, g_te, o_te, t_te, m_ca.group_id.to_numpy(),
            m_ca.target_time, level, horizon)

    def cell(kind, magnitude_sd, family, strategy=None, contam_rate=None,
             cell_name=None):
        t0 = time.perf_counter()
        if family in ("clean", "fault"):
            if kind is None:                      # pristine clean cell
                w2 = None
                X_te2, y_obs = X.iloc[te], y[te].copy()
            else:
                series2 = []
                for s in prepared.series:
                    win = _window_for_series(windows, s.group_id)
                    mag = magnitude_sd * float(
                        scale_map.get(s.group_id, scale_map.get("__pooled__", 1.0)))
                    f2 = apply_fault_to_frame(s.frame, win, kind, mag,
                                              seed=seed + 7)
                    series2.append(replace(s, frame=f2))
                prepared2 = replace(prepared, series=series2)
                w2 = windowing.build_dataset_windows(prepared2, horizon, fcfg)
                key = ["group_id", "origin_time"]
                lut = w2["meta"][key].copy(); lut["row"] = np.arange(len(lut))
                sel = m_te[key].merge(lut, on=key, how="left", validate="one_to_one")
                rows = sel["row"].to_numpy()
                if np.isnan(rows).any():
                    raise RuntimeError("corrupted rebuild lost test rows")
                rows = rows.astype(int)
                X_te2 = w2["X"].iloc[rows]
                y_obs = w2["y"][rows]
            point, lo, hi = um.predict(X_te2, y_obs=y_obs, groups=g_te,
                                       o_te=o_te, t_te=t_te)
            if recal in ("periodic", "rolling"):
                lo, hi = recal_bounds(point, y_obs - point, recal)
        elif family == "contamination":
            # split-conformal residual-offset construction, uniform in-family
            res = um.resid_ca.copy()
            if contam_rate:
                rng = np.random.default_rng(seed + 11)
                k = int(round(contam_rate * len(res)))
                pick = rng.choice(len(res), size=k, replace=False)
                sigma = float(scale_map.get("__pooled__", 1.0))
                res[pick] += 2.0 * sigma
            a = (1 - level) / 2
            qlo, qhi = np.quantile(res, a), np.quantile(res, 1 - a)
            point, _, _ = um.predict(X.iloc[te], y_obs=y[te], groups=g_te,
                                     o_te=o_te, t_te=t_te)
            lo, hi = point + qlo, point + qhi
            y_obs = y[te].copy()
        elif family == "recovery":
            series2 = []
            for s in prepared.series:
                win = _window_for_series(windows, s.group_id)
                mag = 2.0 * float(scale_map.get(s.group_id,
                                                scale_map.get("__pooled__", 1.0)))
                f2 = apply_fault_to_frame(s.frame, win, "level_shift", mag,
                                          seed=seed + 7)
                series2.append(replace(s, frame=f2))
            prepared2 = replace(prepared, series=series2)
            w2 = windowing.build_dataset_windows(prepared2, horizon, fcfg)
            key = ["group_id", "origin_time"]
            lut = w2["meta"][key].copy(); lut["row"] = np.arange(len(lut))
            sel = m_te[key].merge(lut, on=key, how="left", validate="one_to_one")
            rows = sel["row"].to_numpy().astype(int)
            X_te2 = w2["X"].iloc[rows]; y_obs = w2["y"][rows]
            point, lo0, hi0 = um.predict(X_te2, y_obs=y_obs, groups=g_te,
                                         o_te=o_te, t_te=t_te)
            if strategy == "static":
                lo, hi = lo0, hi0
            else:
                lo, hi = recal_bounds(point, y_obs - point, strategy)
        else:
            raise ValueError(family)

        row = score_cell(y_clean, y_obs, lo, hi, g_te, m_te, masks, freq_min,
                         rule_k, rule_m, level, tol)
        cover = (y_clean >= lo) & (y_clean <= hi)
        recoveries = []
        for group in pd.unique(g_te):
            positions = np.flatnonzero(group_mask(g_te, group))
            local_masks = {k: v[positions] for k, v in masks.items()}
            pre = local_masks["pre"]
            pre_cov = np.mean(cover[positions][pre]) if pre.any() else np.nan
            steps, is_censored = time_to_recovery(cover[positions], local_masks, freq_min, pre_cov)
            recoveries.append((steps, is_censored))
            group_recovery.append(dict(dataset=ds, outer_fold=fold_i, seed=model_seed,
                cell=cell_name, group_id=group, time_to_recovery_steps=steps,
                recovery_censored=is_censored, n_post=int(local_masks["post"].sum())))
        rec_steps, censored = recoveries[0] if len(recoveries) == 1 else (np.nan, np.nan)
        row.update({
            "dataset": ds, "outer_fold": fold_i, "seed": model_seed,
            "event_seed": seed,
            "family": family, "cell": cell_name or (kind or "clean"),
            "fault_type": kind, "severity_sd": magnitude_sd,
            "contamination_rate": contam_rate, "recal_policy": strategy or recal,
            "interval_method": method, "nominal_level": level,
            "estimator_class": um.estimator_class, "model_seed": model_seed,
            "fallback": json.dumps(um.fallback),
            "rule_k": rule_k, "rule_m": rule_m,
            "time_to_recovery_steps": rec_steps, "recovery_censored": censored,
            "n_recovery_groups": len(recoveries),
            "n_recovery_censored": sum(c for _, c in recoveries),
            "operational_feasible": bool(pipe_row.get("operational_feasible", False)),
            "eval_seconds": round(time.perf_counter() - t0, 2),
        })
        stream = m_te[["group_id", "origin_time", "target_time"]].copy()
        stream["cell"] = row["cell"]
        stream["y_clean"], stream["y_observed"] = y_clean, y_obs
        stream["point"], stream["lower"], stream["upper"] = point, lo, hi
        streams.append(stream)
        return row

    rows = []
    rows.append(cell(None, 0.0, "clean", cell_name="clean"))
    rows.append(cell("level_shift", 0.0, "fault", cell_name="zero_control"))
    sevs = [2.0] if fast else [1.0, 2.0]
    for kind in FAULT_TYPES:
        mags = sevs if kind in MAGNITUDE_FAULTS else [1.0]
        for mag in mags:
            rows.append(cell(kind, mag, "fault",
                             cell_name=f"{kind}@{mag if kind in MAGNITUDE_FAULTS else 'na'}"))
    rows.append(cell(None, 0.0, "contamination", contam_rate=0.0,
                     cell_name="contam_clean_ref"))
    for cr in ([0.10] if fast else [0.05, 0.10]):
        rows.append(cell(None, 0.0, "contamination", contam_rate=cr,
                         cell_name=f"contam@{cr}"))
    for pol in (["periodic"] if fast else ["static", "periodic", "rolling"]):
        rows.append(cell(None, 2.0, "recovery", strategy=pol,
                         cell_name=f"recovery_{pol}"))

    # ---- point accuracy on clean test (RQ1 evidence) ----
    pa = []
    col = next((c for c in X.columns if c.endswith("target_lag_0")), None)
    pers = X.iloc[te][col].to_numpy(float) if col else np.full(len(te), np.nan)
    pa.append({"dataset": ds, "outer_fold": fold_i, "seed": model_seed,
            "event_seed": seed,
               "model": "persistence", "mae": M.mae(y_clean, pers),
               "rmse": M.rmse(y_clean, pers), "fit_seconds": 0.0})
    t0 = time.perf_counter()
    try:
        tuned = xgboost_model.tune(X.iloc[itr], pd.Series(y[itr]), n_iter=4,
                                   n_splits=2, seed=model_seed, n_jobs=1, meta_train=meta.iloc[itr])
        xp = xgboost_model.predict(tuned["estimator"], X.iloc[te])
        pa.append({"dataset": ds, "outer_fold": fold_i, "seed": model_seed,
            "event_seed": seed,
                   "model": "xgboost", "mae": M.mae(y_clean, xp),
                   "rmse": M.rmse(y_clean, xp),
                   "fit_seconds": round(time.perf_counter() - t0, 2)})
    except Exception as exc:                                 # noqa: BLE001
        pa.append({"dataset": ds, "outer_fold": fold_i, "seed": model_seed,
            "event_seed": seed,
                   "model": "xgboost", "mae": np.nan, "rmse": np.nan,
                   "fit_seconds": np.nan, "error": str(exc)[:120]})
    calibration = m_ca[["group_id", "origin_time", "target_time"]].copy()
    calibration["y_true"], calibration["point"] = y[ica], um.point_ca
    return rows, pa, {"unit_fit_seconds": round(um.fit_seconds, 2),
                     "_streams": pd.concat(streams, ignore_index=True),
                     "_recovery_by_group": pd.DataFrame(group_recovery),
                     "_calibration": calibration}


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def expected_cell_names(fast=False):
    names = ["clean", "zero_control"]
    for kind in FAULT_TYPES:
        for mag in ([2.0] if fast else [1.0, 2.0]) if kind in MAGNITUDE_FAULTS else ["na"]:
            names.append(f"{kind}@{mag}")
    return names + ["contam_clean_ref"] + [f"contam@{r}" for r in
        ([.10] if fast else [.05, .10])] + [f"recovery_{p}" for p in
        (["periodic"] if fast else ["static", "periodic", "rolling"])]


def run_extension(config_path, datasets, out_root, *, fast=False,
                  core_artifacts, resume=False):
    from .run_study import load_config, resolve_dataset_config
    from .datasets import get_adapter
    from . import protocol as P
    from .corrected_study import _policy_from_cfg
    from . import alerts_corrected

    study = load_config(config_path)
    proto = P.load_protocol(study["protocol_ref"]["path"])
    core_summary_path = Path(core_artifacts) / "engine_summary.json"
    core_summary = json.loads(core_summary_path.read_text(encoding="utf-8"))
    if core_summary.get("integration_version") != 1:
        raise ValueError("extension requires a repaired core run, not historical selections")
    if not fast and core_summary.get("fast", True):
        raise ValueError("full extension cannot use smoke core selections")
    out_root = Path(out_root); out_root.mkdir(parents=True, exist_ok=True)
    summary = {}
    for ds in datasets:
        cfg = resolve_dataset_config(study, ds)
        prepared = SI.causal_prepared(get_adapter(cfg.get("adapter", ds)).prepare(cfg),
            cfg.get("missing", {}).get("max_short_gap_steps", 3))
        horizon = int(cfg.get("alerts", {}).get("primary_horizon",
                      cfg.get("horizons", [1])[0]))
        fcfg = windowing.feature_config(cfg, prepared.series[0].covariates)
        w = windowing.build_dataset_windows(prepared, horizon, fcfg)
        meta, X, y = w["meta"], w["X"], w["y"]
        scheme = ("chronological" if isinstance(prepared.partitioner,
                                                ChronologicalPartitioner)
                  else "whole_run_group_blocked")
        core_manifest = json.loads(Path(core_artifacts, ds, "checkpoint_manifest.json")
                                   .read_text(encoding="utf-8"))
        core_spec = core_manifest["spec"]
        if not fast and core_spec.get("fast", True):
            raise ValueError("full extension cannot use smoke core checkpoints")
        folds = make_outer_folds(meta, scheme, int(core_spec["n_outer"]), horizon, prepared.freq)

        prov = json.loads(Path(core_artifacts, ds, "provenance.json")
                          .read_text(encoding="utf-8"))
        pipes = {(int(p["seed"]), int(p["outer_fold"])): p for p in prov}
        if len(pipes) != len(prov) or any(p.get("integration_version") != 1 or
                not p.get("estimator_class") for p in prov):
            raise ValueError("duplicate or unrepaired core pipeline provenance")
        seeds = list(proto.seeds.model) if not fast else [proto.seeds.model[0]]
        use_folds = range(len(folds)) if not fast else [0]
        wanted = {(seed, fi) for fi in use_folds for seed in seeds}
        if not wanted <= pipes.keys():
            raise ValueError("missing core pipeline cells; complete core before extension")
        data_hash = hashlib.sha256(pd.util.hash_pandas_object(X, index=False).values.tobytes()
            + pd.util.hash_pandas_object(meta, index=False).values.tobytes()).hexdigest()
        if (core_spec.get("data_hash") != data_hash or
            core_spec.get("source_hash") != source_digest()):
            raise ValueError("core code/data identity differs from extension; rerun core")
        spec = dict(dataset=ds, horizon=horizon, fast=fast, seeds=seeds, config=cfg,
            protocol_hash=P.protocol_hash(study["protocol_ref"]["path"]),
            source_hash=source_digest(), data_hash=data_hash,
            core_provenance_hash=digest(Path(core_artifacts, ds, "provenance.json")),
            core_summary_hash=digest(core_summary_path), integration_version=1)
        d = out_root / ds
        store = UnitCheckpoint(d, spec, resume=resume)
        expected = [f"h{horizon}_f{fi}_s{s}" for fi in use_folds for s in seeds]

        cell_rows, point_rows, timing = [], [], []
        for fi in use_folds:
            for seed in seeds:
                p = pipes[(seed, fi)]
                key = f"h{horizon}_f{fi}_s{seed}"
                loaded = store.load(key) if resume else None
                if loaded is not None:
                    payload, _ = loaded
                    cell_rows.extend(payload["cells"]); point_rows.extend(payload["points"])
                    timing.append(payload["timing"])
                    print(f"[{ds}] {key}: resumed", flush=True)
                    continue
                refit_train, _ = SI.refit_split(meta, np.concatenate([
                    folds[fi]["train"], folds[fi]["calibration"]]), scheme)
                scale_map = SI.training_scale(y, meta, refit_train)
                if p.get("outer_train_membership") != SI.membership_hash(meta, refit_train):
                    raise ValueError("core/extension training membership differs")
                rows, pa, tm = evaluate_unit(
                    ds, prepared, meta, X, y, fi, folds[fi], p, cfg,
                    prepared.freq, scale_map, fcfg, horizon, fast=fast)
                require_cells(pd.DataFrame(rows), ["cell"], [(c,) for c in expected_cell_names(fast)])
                if any(r.get("error") for r in pa):
                    raise ValueError("point baseline fit failed; unit is incomplete")
                frames = dict(predictions=tm.pop("_streams"), calibration=tm.pop("_calibration"),
                              recovery_by_group=tm.pop("_recovery_by_group"))
                record = {"dataset": ds, "outer_fold": fi, "seed": seed, **tm}
                payload = dict(cells=rows, points=pa, timing=record,
                    core_pipeline=p, train_membership=SI.membership_hash(meta, refit_train),
                    scale={str(k): v for k, v in scale_map.items()})
                store.save(key, payload, frames)
                cell_rows.extend(rows); point_rows.extend(pa)
                timing.append(record)
                print(f"[{ds}] fold {fi} seed {seed}: {len(rows)} cells done",
                      flush=True)
        store.require_complete(expected)
        require_cells(pd.DataFrame(cell_rows), ["outer_fold", "seed", "cell"],
            [(fi, s, c) for fi in use_folds for s in seeds for c in expected_cell_names(fast)])
        pd.DataFrame(cell_rows).to_csv(d / "robustness_cells.csv", index=False)
        pd.DataFrame(point_rows).to_csv(d / "point_accuracy.csv", index=False)
        pd.DataFrame(timing).to_csv(d / "unit_timing.csv", index=False)
        summary[ds] = {"n_cell_rows": len(cell_rows),
                       "n_units": len(timing),
                       "families": sorted({r.get("family") for r in cell_rows})}
    (out_root / "extension_summary.json").write_text(json.dumps({
        "fast": fast, "datasets": summary, "integration_version": 1,
        "protocol_hash": __import__("src.protocol", fromlist=["protocol_hash"])
            .protocol_hash(study["protocol_ref"]["path"]),
        "core_run": str(Path(core_artifacts).resolve()),
        "core_summary_hash": digest(core_summary_path)},
        indent=2, default=str), encoding="utf-8")
    return summary


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Robustness extension (amendment 003).")
    ap.add_argument("--config", default="configs/study_final_dissertation_v2.yaml")
    ap.add_argument("--dataset", action="append", default=None)
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--core-artifacts", required=True, help="repaired core run directory")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    datasets = args.dataset or ["pleia", "pleia_energy", "rico", "bdg2"]
    summary = run_extension(args.config, datasets, args.out, fast=args.fast,
                            core_artifacts=args.core_artifacts, resume=args.resume)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
