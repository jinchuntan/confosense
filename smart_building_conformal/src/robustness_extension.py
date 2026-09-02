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
            out["target"] = vals.ffill().bfill()
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
class UnitModel:
    """The unit's interval model fitted once on clean train/calib."""

    def __init__(self, method: str, level: float, X_tr, y_tr, X_ca, y_ca,
                 meta_ca, horizon: int):
        self.method, self.level, self.horizon = method, float(level), int(horizon)
        self.meta_ca = meta_ca
        t0 = time.perf_counter()
        if method in ("cqr", "quantile_uncalibrated"):
            self.m = conformal_cqr.fit_cqr(X_tr, pd.Series(y_tr), X_ca,
                                           pd.Series(y_ca), self.level, seed=0)
        elif method in ("recentred_enbpi_static", "recentred_enbpi_updated"):
            from mapie.regression import TimeSeriesRegressor
            from mapie.subsample import BlockBootstrap
            from .conformal_enbpi import _build_base
            base, _ = _build_base(0, {"base_n_estimators": 60})
            self.m = TimeSeriesRegressor(
                estimator=base, method="enbpi",
                cv=BlockBootstrap(n_resamplings=5, length=24, overlapping=True,
                                  random_state=0),
                agg_function="mean", random_state=0, n_jobs=1)
            self.m.fit(X_tr.to_numpy(), np.asarray(y_tr))
            self.m.conformalize(X_ca.to_numpy(), np.asarray(y_ca))
        else:
            raise ValueError(f"unsupported unit interval method {method!r}")
        self.fit_seconds = time.perf_counter() - t0
        # calibration point + residuals for recalibration / contamination cells
        if method in ("cqr", "quantile_uncalibrated"):
            self.point_ca = conformal_cqr.cqr_interval(self.m, X_ca)["point"]
        else:
            self.point_ca = np.asarray(self.m.predict(X_ca.to_numpy(),
                                                      ensemble=False)).ravel()
        self.y_ca = np.asarray(y_ca, float)
        self.resid_ca = self.y_ca - self.point_ca

    def predict(self, X_te, *, y_obs=None, groups=None, o_te=None, t_te=None):
        """(point, lower, upper) on ``X_te`` under the unit's method."""
        if self.method == "cqr":
            r = conformal_cqr.cqr_interval(self.m, X_te)
        elif self.method == "quantile_uncalibrated":
            r = conformal_quantile.quantile_interval(self.m, X_te)
        elif self.method == "recentred_enbpi_static":
            from .conformal_enbpi import _recentered_intervals
            rr = _recentered_intervals(self.m, X_te.to_numpy(), [self.level])
            r = rr[self.level]
        else:   # recentred_enbpi_updated: causal online updating on observed stream
            point = np.asarray(self.m.predict(X_te.to_numpy(),
                                              ensemble=False)).ravel()
            res_te = (np.asarray(y_obs, float) - point if y_obs is not None
                      else np.zeros(len(point)))
            out = _updated_intervals_causal(
                point_test=point, calib_residuals=self.resid_ca,
                calib_groups=self.meta_ca["group_id"].to_numpy(),
                calib_target_times=pd.DatetimeIndex(self.meta_ca["target_time"]),
                test_residuals=res_te, test_groups=np.asarray(groups),
                test_origin_times=pd.DatetimeIndex(o_te),
                test_target_times=pd.DatetimeIndex(t_te),
                horizon=self.horizon, confidence_levels=[self.level], window=None)
            r = out[self.level]
        return (np.asarray(r["point"], float), np.asarray(r["lower"], float),
                np.asarray(r["upper"], float))


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
    during_pos = np.nonzero(during)[0]
    d_lo = during_pos.min() if len(during_pos) else -1
    d_hi = during_pos.max() if len(during_pos) else -1
    fault_detected = bool(len(onsets) and
                          np.any((onsets >= d_lo) & (onsets <= d_hi + tol)))
    delay_steps = (int(onsets[(onsets >= d_lo)].min() - d_lo)
                   if fault_detected and np.any(onsets >= d_lo) else np.nan)
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
    order = np.argsort(meta.iloc[trc]["origin_time"].to_numpy(), kind="stable")
    cut = int(0.75 * len(trc))
    itr, ica = trc[order[:cut]], trc[order[cut:]]
    m_te, m_ca = meta.iloc[te], meta.iloc[ica]
    g_te = m_te["group_id"].to_numpy()
    o_te = pd.DatetimeIndex(m_te["origin_time"]); t_te = pd.DatetimeIndex(m_te["target_time"])

    method = pipe_row["interval_method"]
    level = float(pipe_row["operating_level"])
    rule_k, rule_m = int(pipe_row["rule_k"]), int(pipe_row["rule_m"])
    recal = pipe_row["recalibration"]
    seed = int(pipe_row["seed"])
    tol = int(cfg.get("alerts", {}).get("detection_tolerance_steps", 6))

    um = UnitModel(method, level, X.iloc[itr], y[itr], X.iloc[ica], y[ica],
                   m_ca, horizon)
    masks = segment_masks(meta, te)
    windows = group_test_windows(meta, te, WINDOW_FRAC)
    y_clean = y[te]

    def recal_bounds(point, res_obs, strategy):
        lo = np.empty(len(point)); hi = np.empty(len(point))
        gca = m_ca["group_id"].to_numpy(); tca = pd.DatetimeIndex(m_ca["target_time"])
        for g in pd.unique(g_te):
            evi = np.nonzero(g_te == g)[0]
            srt = np.argsort(t_te.values[evi], kind="stable"); evo = evi[srt]
            cm = gca == g
            pool = DelayedResidualPool.build(
                um.resid_ca[cm], tca[cm], res_obs[evo], o_te[evo], t_te[evo],
                horizon)
            rr = recalibration.apply_strategy(point[evo], pool, level, strategy,
                                              update_every=48, window=250,
                                              min_samples=30)
            lo[evo] = rr.lower; hi[evo] = rr.upper
        return lo, hi

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
        rec_steps, censored = time_to_recovery(cover, masks, freq_min,
                                               row["coverage_pre"])
        row.update({
            "dataset": ds, "outer_fold": fold_i, "seed": seed,
            "family": family, "cell": cell_name or (kind or "clean"),
            "fault_type": kind, "severity_sd": magnitude_sd,
            "contamination_rate": contam_rate, "recal_policy": strategy or recal,
            "interval_method": method, "nominal_level": level,
            "rule_k": rule_k, "rule_m": rule_m,
            "time_to_recovery_steps": rec_steps, "recovery_censored": censored,
            "operational_feasible": bool(pipe_row.get("operational_feasible", False)),
            "eval_seconds": round(time.perf_counter() - t0, 2),
        })
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
    pa.append({"dataset": ds, "outer_fold": fold_i, "seed": seed,
               "model": "persistence", "mae": M.mae(y_clean, pers),
               "rmse": M.rmse(y_clean, pers), "fit_seconds": 0.0})
    t0 = time.perf_counter()
    try:
        tuned = xgboost_model.tune(X.iloc[itr], pd.Series(y[itr]), n_iter=4,
                                   n_splits=2, seed=seed, n_jobs=1)
        xp = xgboost_model.predict(tuned["estimator"], X.iloc[te])
        pa.append({"dataset": ds, "outer_fold": fold_i, "seed": seed,
                   "model": "xgboost", "mae": M.mae(y_clean, xp),
                   "rmse": M.rmse(y_clean, xp),
                   "fit_seconds": round(time.perf_counter() - t0, 2)})
    except Exception as exc:                                 # noqa: BLE001
        pa.append({"dataset": ds, "outer_fold": fold_i, "seed": seed,
                   "model": "xgboost", "mae": np.nan, "rmse": np.nan,
                   "fit_seconds": np.nan, "error": str(exc)[:120]})
    return rows, pa, {"unit_fit_seconds": round(um.fit_seconds, 2)}


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def run_extension(config_path, datasets, out_root, *, fast=False,
                  core_artifacts="outputs/final_dissertation_v2/metrics/run_artifacts"):
    from .run_study import load_config, resolve_dataset_config
    from .datasets import get_adapter
    from . import protocol as P
    from .corrected_study import _policy_from_cfg
    from . import alerts_corrected

    study = load_config(config_path)
    proto = P.load_protocol(study["protocol_ref"]["path"])
    out_root = Path(out_root); out_root.mkdir(parents=True, exist_ok=True)
    summary = {}
    for ds in datasets:
        cfg = resolve_dataset_config(study, ds)
        prepared = get_adapter(cfg.get("adapter", ds)).prepare(cfg)
        horizon = int(cfg.get("alerts", {}).get("primary_horizon",
                      cfg.get("horizons", [1])[0]))
        fcfg = windowing.feature_config(cfg, prepared.series[0].covariates)
        w = windowing.build_dataset_windows(prepared, horizon, fcfg)
        meta, X, y = w["meta"], w["X"], w["y"]
        scheme = ("chronological" if isinstance(prepared.partitioner,
                                                ChronologicalPartitioner)
                  else "whole_run_group_blocked")
        tr_mask = (meta["partition"] == "train").to_numpy()
        sc = alerts_corrected.per_group_robust_scale(
            y[tr_mask], meta["group_id"].to_numpy()[tr_mask])
        scale_map = dict(sc["scale"]); scale_map["__pooled__"] = sc["pooled_fallback"]
        folds = make_outer_folds(meta, scheme, 3, horizon, prepared.freq)

        prov = json.loads(Path(core_artifacts, ds, "provenance.json")
                          .read_text(encoding="utf-8"))
        pipes = {(int(p["seed"]), int(p["outer_fold"])): p for p in prov}
        seeds = sorted({s for s, _ in pipes}) if not fast else [42]
        use_folds = range(len(folds)) if not fast else [0]

        cell_rows, point_rows, timing = [], [], []
        for fi in use_folds:
            for seed in seeds:
                p = pipes.get((seed, fi))
                if p is None:
                    cell_rows.append({"dataset": ds, "outer_fold": fi,
                                      "seed": seed, "family": "abstention_row",
                                      "cell": "missing_pipeline",
                                      "reason": "no provenance entry"})
                    continue
                rows, pa, tm = evaluate_unit(
                    ds, prepared, meta, X, y, fi, folds[fi], p, cfg,
                    prepared.freq, scale_map, fcfg, horizon, fast=fast)
                cell_rows.extend(rows); point_rows.extend(pa)
                timing.append({"dataset": ds, "outer_fold": fi, "seed": seed, **tm})
                print(f"[{ds}] fold {fi} seed {seed}: {len(rows)} cells done",
                      flush=True)
        d = out_root / ds; d.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(cell_rows).to_csv(d / "robustness_cells.csv", index=False)
        pd.DataFrame(point_rows).to_csv(d / "point_accuracy.csv", index=False)
        pd.DataFrame(timing).to_csv(d / "unit_timing.csv", index=False)
        summary[ds] = {"n_cell_rows": len(cell_rows),
                       "n_units": len(timing),
                       "families": sorted({r.get("family") for r in cell_rows})}
    (out_root / "extension_summary.json").write_text(json.dumps({
        "fast": fast, "datasets": summary,
        "protocol_hash": __import__("src.protocol", fromlist=["protocol_hash"])
            .protocol_hash(study["protocol_ref"]["path"]),
        "core_run": "full_20260831_220811 (immutable, untouched)"},
        indent=2, default=str), encoding="utf-8")
    return summary


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Robustness extension (amendment 003).")
    ap.add_argument("--config", default="configs/study_final_dissertation_v2.yaml")
    ap.add_argument("--dataset", action="append", default=None)
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    datasets = args.dataset or ["pleia", "pleia_energy", "rico", "bdg2"]
    summary = run_extension(args.config, datasets, args.out, fast=args.fast)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
