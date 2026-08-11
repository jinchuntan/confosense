"""Auxiliary UCI Occupancy run: a pipeline-portability check, not a benchmark.

Answers one question — does the generic ConfoSense pipeline operate on an
independent public building-sensor dataset with only a small adapter? — by
exercising the whole chain end to end:

    load -> preprocess -> chronologically partition -> generate features
         -> point forecast -> conformally calibrate -> evaluate -> report

Every stage below calls the same generic module the four primary experiments
call. Nothing is reimplemented here, and no method is added or altered for UCI.

Deliberately *not* run: DSCP, EnbPI, the alert-rule search, the robustness
matrix and the recalibration comparison. Those answer research questions this
auxiliary check is not making claims about, and running them would invite the
results to be read as a fifth primary dataset.

Outputs go only to ``outputs/auxiliary_uci/``. The frozen study under
``outputs/full_study/`` is never opened.

Usage
-----
    python -m src.run_uci_auxiliary --config configs/uci_auxiliary.yaml
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import conformal_cqr, conformal_quantile
from . import metrics as M
from . import statistics as S
from . import windowing, xgboost_model
from .datasets import get_adapter
from .manifest import RunManifest

SUBDIRS = ("data_profiles", "metrics", "predictions", "figures", "report",
           "manifests")


def _write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _ctx(prepared, h: int, **extra) -> dict:
    return {
        "dataset": prepared.dataset_id,
        "target": prepared.metadata.get("target_column", ""),
        "units": prepared.series[0].units,
        "sampling_freq": str(prepared.freq),
        "horizon_steps": h,
        "horizon_minutes": prepared.horizon_minutes(h),
        **extra,
    }


# --------------------------------------------------------------------------- #
def stage_prepare(cfg: dict, out: Path, manifest: RunManifest):
    adapter = get_adapter(cfg.get("adapter", cfg["dataset"]))
    prepared = adapter.prepare(cfg)

    prof = out / "data_profiles"
    adapter.profile(prepared).to_csv(prof / "dataset_profile.csv", index=False)
    prepared.split_summary().to_csv(prof / "partition_summary.csv", index=False)
    with open(prof / "partitioning.json", "w", encoding="utf-8") as f:
        json.dump({**prepared.partitioner.describe(),
                   "segment_gaps": prepared.metadata.get("segment_gaps", []),
                   "segment_order": prepared.metadata.get("segment_order", [])},
                  f, indent=2, default=str)

    prov = prepared.provenance.to_dict()
    prov["target_description"] = prepared.target_description
    prov["target_rationale"] = prepared.metadata.get("target_rationale", "")
    manifest.add_provenance(prepared.dataset_id, prov)

    fcfg = windowing.feature_config(cfg, prepared.series[0].covariates)
    windows, summaries = {}, []
    for h in cfg["horizons"]:
        w = windowing.build_dataset_windows(prepared, h, fcfg)
        windows[h] = w
        summaries.append(windowing.window_summary(w))
    pd.concat(summaries, ignore_index=True).to_csv(
        prof / "window_summary.csv", index=False)
    return prepared, windows


# --------------------------------------------------------------------------- #
def stage_point(cfg, prepared, windows, out: Path):
    """Persistence and XGBoost only — enough to prove the path executes."""
    seed = int(cfg.get("seed", 42))
    xcfg = cfg["models"]["xgboost"]
    rows, frames, store = [], [], {}

    for h in cfg["horizons"]:
        w = windows[h]
        idx, X, y, meta = w["idx"], w["X"], w["y"], w["meta"]
        tr, te = idx["train"], idx["test"]
        X_tr, y_tr = windowing.subset(X, tr), y[tr]
        X_te, y_te = windowing.subset(X, te), y[te]

        preds = {"persistence": meta.loc[te, "persistence_pred"].to_numpy()}
        tuned = xgboost_model.tune(
            X_tr, pd.Series(y_tr), n_iter=int(xcfg["search_iter"]),
            n_splits=int(xcfg["cv_splits"]), seed=seed,
            n_jobs=int(xcfg.get("search_n_jobs", -1)))
        seed_preds = {}
        for s in range(seed, seed + int(xcfg["seeds"])):
            model = xgboost_model.fit_with_params(
                X_tr, pd.Series(y_tr), tuned["best_params"], s,
                n_jobs=int(xcfg.get("refit_n_jobs", 1)))
            seed_preds[s] = xgboost_model.predict(model, X_te)
        preds["xgboost"] = seed_preds[seed]

        with open(out / "metrics" / f"xgboost_best_params_h{h}.json", "w") as f:
            json.dump({"best_params": tuned["best_params"],
                       "best_cv_mae": tuned["best_cv_mae"],
                       "seeds": sorted(seed_preds),
                       "refit_n_jobs": int(xcfg.get("refit_n_jobs", 1)),
                       "xgboost_version": __import__("xgboost").__version__},
                      f, indent=2)

        base_mae = M.mae(y_te, preds["persistence"])
        base_rmse = M.rmse(y_te, preds["persistence"])
        for name, p in preds.items():
            row = {**_ctx(prepared, h), "point_model": name,
                   "mae": M.mae(y_te, p), "rmse": M.rmse(y_te, p),
                   "pct_mae_improvement": M.pct_improvement(base_mae, M.mae(y_te, p)),
                   "pct_rmse_improvement": M.pct_improvement(base_rmse, M.rmse(y_te, p)),
                   "n_test": M.n_valid(y_te, p),
                   "n_seeds": len(seed_preds) if name == "xgboost" else 1}
            if name == "xgboost":
                maes = [M.mae(y_te, v) for v in seed_preds.values()]
                row["mae_std"] = float(np.std(maes))
                row["seeds_used"] = ",".join(str(k) for k in seed_preds)
            rows.append(row)

        frames.append(pd.DataFrame({
            "dataset": prepared.dataset_id, "horizon": h,
            "group_id": meta.loc[te, "group_id"].to_numpy(),
            "target_time": meta.loc[te, "target_time"].to_numpy(),
            "y_true": y_te, **preds}))
        store[h] = {"preds": preds, "y_test": y_te}

    _write(pd.DataFrame(rows), out / "metrics" / "point_metrics.csv")
    pd.concat(frames, ignore_index=True).to_csv(
        out / "predictions" / "point_predictions.csv", index=False)
    return store


# --------------------------------------------------------------------------- #
def stage_intervals(cfg, prepared, windows, out: Path):
    """Uncalibrated quantile band and CQR, from the audited implementations."""
    seed = int(cfg.get("seed", 42))
    levels = list(cfg.get("coverage_levels", [0.95]))
    rows, frames, store = [], [], {}

    for h in cfg["horizons"]:
        w = windows[h]
        idx, X, y, meta = w["idx"], w["X"], w["y"], w["meta"]
        tr, ca, te = idx["train"], idx["calibration"], idx["test"]
        X_tr, y_tr = windowing.subset(X, tr), pd.Series(y[tr])
        X_ca, y_ca = windowing.subset(X, ca), pd.Series(y[ca])
        X_te, y_te = windowing.subset(X, te), y[te]
        scale = float(np.nanstd(y[tr])) or 1.0

        for level in levels:
            model = conformal_cqr.fit_cqr(X_tr, y_tr, X_ca, y_ca, level, seed)
            results = {
                "cqr": conformal_cqr.cqr_interval(model, X_te),
                conformal_quantile.METHOD_NAME:
                    conformal_quantile.quantile_interval(model, X_te),
            }
            for name, res in results.items():
                im = M.interval_metrics(y_te, res["lower"], res["upper"], level)
                crossed = int(res.get("n_crossed_repaired", res.get("n_crossed", 0)))
                rows.append({
                    **_ctx(prepared, h, conformal_method=name,
                           nominal_coverage=level),
                    **im,
                    "normalised_mean_width": im["mean_interval_width"] / scale,
                    "n_crossed_repaired": crossed,
                    "pct_crossed": 100.0 * crossed / max(1, len(res["lower"])),
                    "point_model": "HistGBR-quantile",
                })
                frames.append(pd.DataFrame({
                    "dataset": prepared.dataset_id, "horizon": h,
                    "conformal_method": name, "nominal_coverage": level,
                    "group_id": meta.loc[te, "group_id"].to_numpy(),
                    "target_time": meta.loc[te, "target_time"].to_numpy(),
                    "y_true": y_te, "point": res["point"],
                    "lower": res["lower"], "upper": res["upper"]}))
            store.setdefault(h, {})[level] = {
                **results["cqr"], "y_true": y_te,
                "target_time": meta.loc[te, "target_time"].to_numpy(),
                "group_id": meta.loc[te, "group_id"].to_numpy()}

    _write(pd.DataFrame(rows), out / "metrics" / "interval_metrics.csv")
    pd.concat(frames, ignore_index=True).to_csv(
        out / "predictions" / "interval_predictions.csv", index=False)
    return store


# --------------------------------------------------------------------------- #
def stage_diagnostic(cfg, prepared, intervals, out: Path):
    """Raw interval-violation rate. A descriptive diagnostic, NOT alerting.

    The UCI dataset carries no labelled sensor-fault events of the kind the
    dissertation's alert protocol scores against, so no rule is tuned, no event
    catalogue is injected and no precision, recall or F1 is computed. What is
    reported is the bare proportion of test observations falling outside the
    interval — which is simply one minus empirical coverage, restated in the
    monitoring vocabulary.
    """
    level = max(cfg.get("coverage_levels", [0.95]))
    rows = []
    for h, by_level in intervals.items():
        res = by_level[level]
        y, lo, hi = res["y_true"], res["lower"], res["upper"]
        outside = (y < lo) | (y > hi)
        rows.append({
            **_ctx(prepared, h, conformal_method="cqr", nominal_coverage=level),
            "metric": "interval_violation_diagnostic",
            "n_test": int(len(y)),
            "n_outside_interval": int(np.sum(outside)),
            "violation_rate": float(np.mean(outside)),
            "expected_violation_rate": 1.0 - level,
            "note": ("descriptive interval-violation diagnostic; NOT alert "
                     "reliability. No fault labels exist for this dataset, so "
                     "no k-of-m rule, event catalogue, precision, recall or F1 "
                     "is computed."),
        })
    _write(pd.DataFrame(rows), out / "metrics" / "interval_violation_diagnostic.csv")
    return rows


# --------------------------------------------------------------------------- #
def stage_bootstrap(cfg, prepared, point_store, out: Path):
    """Bootstrap CIs, reusing the generic routine the primary study uses."""
    n_boot = int(cfg.get("bootstrap", {}).get("n_boot", 1000))
    seed = int(cfg.get("seed", 42))
    frames = [
        S.bootstrap_all_point_models(
            art["y_test"], art["preds"], context=_ctx(prepared, h),
            n_boot=n_boot, seed=seed)
        for h, art in point_store.items()
    ]
    if frames:
        _write(pd.concat(frames, ignore_index=True),
               out / "metrics" / "bootstrap_metrics.csv")


# --------------------------------------------------------------------------- #
def stage_figures(cfg, prepared, out: Path):
    """Exactly two figures: one point-forecast, one interval."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    made = []
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    span = int(cfg.get("plotting", {}).get("window_steps", 240))

    pm = pd.read_csv(out / "metrics" / "point_metrics.csv")
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    piv = pm.pivot_table(index="horizon_minutes", columns="point_model", values="mae")
    piv.plot(kind="bar", ax=ax, width=0.75)
    ax.set_ylabel(f"MAE ({pm['units'].iloc[0]})")
    ax.set_xlabel("horizon (minutes)")
    ax.set_title("UCI Occupancy (auxiliary): point-forecast MAE", fontsize=10)
    ax.tick_params(axis="x", rotation=0)
    ax.legend(fontsize=8)
    fig.tight_layout()
    p = fig_dir / "fig_uci_01_point_mae.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    made.append(str(p))

    iv = pd.read_csv(out / "predictions" / "interval_predictions.csv")
    level = max(cfg.get("coverage_levels", [0.95]))
    h0 = min(cfg["horizons"])
    sub = iv[(iv.conformal_method == "cqr") & (iv.horizon == h0)
             & (np.isclose(iv.nominal_coverage, level))].copy()
    sub["t"] = pd.to_datetime(sub["target_time"])
    sub = sub.sort_values("t").head(span)
    fig, ax = plt.subplots(figsize=(8.5, 3.4))
    ax.fill_between(sub["t"], sub["lower"], sub["upper"], alpha=0.3,
                    label=f"CQR {level:.0%} interval")
    ax.plot(sub["t"], sub["y_true"], lw=1.1, label="observed")
    ax.plot(sub["t"], sub["point"], lw=1.0, ls="--", label="forecast")
    ax.set_ylabel("temperature (degC)")
    ax.set_title(f"UCI Occupancy (auxiliary): CQR intervals, h={h0} min",
                 fontsize=10)
    ax.legend(fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    p = fig_dir / "fig_uci_02_cqr_interval.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    made.append(str(p))
    return made


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="configs/uci_auxiliary.yaml")
    ap.add_argument("--outputs", default="")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    out = Path(args.outputs or cfg["paths"].get("output_dir", "outputs/auxiliary_uci"))
    for sub in SUBDIRS:
        (out / sub).mkdir(parents=True, exist_ok=True)

    manifest = RunManifest(args.config, cfg, out, fast=False,
                           datasets=[cfg["dataset"]])
    manifest.note_limitation(
        "UCI Occupancy is an auxiliary pipeline-portability check, not a "
        "primary benchmark. It is excluded from the cross-dataset statistical "
        "comparison and from every dissertation conclusion."
    )
    t0 = time.time()

    print("[uci] prepare ...")
    prepared, windows = stage_prepare(cfg, out, manifest)
    manifest.record("uci:prepare", "completed", time.time() - t0)

    t = time.time()
    print("[uci] point ...")
    point_store = stage_point(cfg, prepared, windows, out)
    manifest.record("uci:point", "completed", time.time() - t)

    t = time.time()
    print("[uci] intervals ...")
    intervals = stage_intervals(cfg, prepared, windows, out)
    manifest.record("uci:intervals", "completed", time.time() - t)

    t = time.time()
    print("[uci] violation diagnostic ...")
    stage_diagnostic(cfg, prepared, intervals, out)
    manifest.record("uci:violation_diagnostic", "completed", time.time() - t)

    t = time.time()
    print("[uci] bootstrap ...")
    stage_bootstrap(cfg, prepared, point_store, out)
    manifest.record("uci:bootstrap", "completed", time.time() - t)

    t = time.time()
    print("[uci] figures ...")
    made = stage_figures(cfg, prepared, out)
    manifest.record("uci:figures", "completed", time.time() - t, n_figures=len(made))

    payload = manifest.write()
    prov_src = out / "manifests" / "dataset_sources.json"
    if prov_src.exists():
        (out / "manifests" / "dataset_source.json").write_text(
            prov_src.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"[done] {payload['runtime_seconds']}s | "
          f"completed {payload['n_completed']}, failed {payload['n_failed']}")
    print(f"[done] outputs under {out}")


if __name__ == "__main__":
    main()
