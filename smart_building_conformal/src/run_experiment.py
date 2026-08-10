"""End-to-end driver for the preliminary conformal-forecasting experiment.

Run with:
    python -m src.run_experiment --config configs/pleia_preliminary.yaml

The ``--fast`` flag shrinks the search, seed counts and horizons for a quick
smoke test of the whole pipeline; it does not change any methodology.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import yaml

from . import prepare_data, features, xgboost_model, attention_lstm
from . import conformal_cqr, conformal_enbpi, alerts as alert_mod, robustness
from . import metrics as M
from . import plotting


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def covariate_columns(cfg: dict) -> list[str]:
    cov = cfg["covariates"]
    return [cov["outdoor_temp"], cov["humidity"], cov["radiation"],
            cov["hvac_state"], cov["setpoint"], *cov["hvac_mode_onehot"]]


def feature_cfg(cfg: dict) -> dict:
    return {
        "target_lags": cfg["features"]["target_lags"],
        "rolling_windows": cfg["features"]["rolling_windows"],
        "include_weekly": cfg["features"]["include_weekly"],
        "covariates": covariate_columns(cfg),
    }


def build_horizon_data(processed: pd.DataFrame, horizon: int, cfg: dict, boundaries) -> dict:
    """Aligned flat-feature and LSTM-sequence datasets for one horizon."""
    freq = pd.Timedelta(cfg["resample"]["freq"])
    season = cfg["resample"]["season_steps"]
    fcfg = feature_cfg(cfg)

    sup = features.build_supervised(processed, horizon, freq, season, fcfg)
    sup_times = pd.DatetimeIndex(sup["meta"]["origin_time"])

    lcfg = {"covariates": covariate_columns(cfg)}
    chan, chan_names = attention_lstm.build_channel_matrix(processed, lcfg)
    seq_len = cfg["models"]["lstm"]["seq_len"]
    Xseq, yseq, pos = attention_lstm.build_sequences(
        chan, processed["target"].to_numpy(), seq_len, horizon
    )
    lstm_times = processed.index[pos]

    common = sup_times.intersection(lstm_times)
    sup_mask = sup_times.isin(common)
    lstm_mask = lstm_times.isin(common)

    Xf = sup["X"].loc[sup_mask].reset_index(drop=True)
    meta = sup["meta"].loc[sup_mask].reset_index(drop=True)
    yf = meta["y_true"].to_numpy()
    Xseq, yseq = Xseq[lstm_mask], yseq[lstm_mask]

    origin = pd.DatetimeIndex(meta["origin_time"])
    labels = prepare_data.assign_split(origin, *boundaries)
    idx = {name: labels == name for name in ["train", "calibration", "test"]}

    return {
        "Xf": Xf, "yf": yf, "meta": meta,
        "Xseq": Xseq, "yseq": yseq,
        "idx": idx, "feature_names": sup["feature_names"],
        "channel_names": chan_names, "seq_len": seq_len,
    }


def _sub(df_or_arr, mask):
    if isinstance(df_or_arr, pd.DataFrame):
        return df_or_arr.loc[mask].reset_index(drop=True)
    return df_or_arr[mask]


# --------------------------------------------------------------------------- #
# Point forecasting (step 6)
# --------------------------------------------------------------------------- #
def run_point_models(data: dict, horizon: int, cfg: dict, out: Path) -> dict:
    idx = data["idx"]
    Xf, yf, meta = data["Xf"], data["yf"], data["meta"]
    tr, ca, te = idx["train"], idx["calibration"], idx["test"]

    X_train, y_train = _sub(Xf, tr), yf[tr]
    X_test = _sub(Xf, te)
    y_test = yf[te]

    # Baselines (leak-free predictions carried in meta).
    persistence = meta.loc[te, "persistence_pred"].to_numpy()
    seasonal = meta.loc[te, "seasonal_naive_pred"].to_numpy()

    # XGBoost: tune once (seed 42, training only), then refit across seeds.
    tuned = xgboost_model.tune(
        X_train, pd.Series(y_train),
        n_iter=cfg["models"]["xgboost"]["search_iter"],
        n_splits=cfg["models"]["xgboost"]["cv_splits"],
        seed=cfg["seed"],
    )
    xgb_seed_preds = {}
    xgb_model_primary = None
    for seed in range(cfg["seed"], cfg["seed"] + cfg["models"]["xgboost"]["seeds"]):
        model = xgboost_model.fit_with_params(X_train, pd.Series(y_train), tuned["best_params"], seed)
        xgb_seed_preds[seed] = xgboost_model.predict(model, X_test)
        if seed == cfg["seed"]:
            xgb_model_primary = model
    xgb_primary = xgb_seed_preds[cfg["seed"]]

    # Attention-LSTM across seeds.
    lcfg = cfg["models"]["lstm"]
    Xseq, yseq = data["Xseq"], data["yseq"]
    lstm_seed_preds, lstm_history = {}, None
    for seed in range(cfg["seed"], cfg["seed"] + lcfg["seeds"]):
        res = attention_lstm.train_predict(Xseq[tr], yseq[tr], Xseq[te], lcfg, seed)
        lstm_seed_preds[seed] = res["predictions"]
        if seed == cfg["seed"]:
            lstm_history = res["history"]
    lstm_primary = lstm_seed_preds[cfg["seed"]]

    preds = {
        "persistence": persistence,
        "seasonal_naive": seasonal,
        "xgboost": xgb_primary,
        "attention_lstm": lstm_primary,
    }

    # Metrics table.
    base_mae = M.mae(y_test, persistence)
    base_rmse = M.rmse(y_test, persistence)
    rows = []

    def add_row(model_name, pred, seed_preds=None):
        mae = M.mae(y_test, pred)
        rmse = M.rmse(y_test, pred)
        mae_std = rmse_std = np.nan
        n_seeds = 1
        if seed_preds:
            maes = [M.mae(y_test, p) for p in seed_preds.values()]
            rmses = [M.rmse(y_test, p) for p in seed_preds.values()]
            mae_std, rmse_std = float(np.std(maes)), float(np.std(rmses))
            n_seeds = len(seed_preds)
        rows.append({
            "horizon": horizon, "model": model_name,
            "mae": mae, "rmse": rmse,
            "mae_std": mae_std, "rmse_std": rmse_std,
            "pct_mae_improvement": M.pct_improvement(base_mae, mae),
            "pct_rmse_improvement": M.pct_improvement(base_rmse, rmse),
            "n_seeds": n_seeds, "n_test": M.n_valid(y_test, pred),
        })

    add_row("persistence", persistence)
    add_row("seasonal_naive", seasonal)
    add_row("xgboost", xgb_primary, xgb_seed_preds)
    add_row("attention_lstm", lstm_primary, lstm_seed_preds)

    # Persist models, params, history and predictions.
    models_dir = out / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(xgb_model_primary, models_dir / f"xgboost_h{horizon}_seed{cfg['seed']}.joblib")
    with open(models_dir / f"xgboost_best_params_h{horizon}.json", "w") as f:
        json.dump({"best_params": tuned["best_params"], "best_cv_mae": tuned["best_cv_mae"]}, f, indent=2)
    with open(models_dir / f"lstm_history_h{horizon}_seed{cfg['seed']}.json", "w") as f:
        json.dump(lstm_history, f, indent=2)

    pred_df = pd.DataFrame({
        "target_time": meta.loc[te, "target_time"].to_numpy(),
        "y_true": y_test,
        **preds,
    })
    (out / "predictions").mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(out / "predictions" / f"point_predictions_h{horizon}.csv", index=False)

    return {"metrics": rows, "pred_df": pred_df, "xgb_best_params": tuned["best_params"]}


# --------------------------------------------------------------------------- #
# Conformal intervals (steps 7-9)
# --------------------------------------------------------------------------- #
def run_conformal(data: dict, horizon: int, cfg: dict, target_name: str):
    idx = data["idx"]
    Xf, yf, meta = data["Xf"], data["yf"], data["meta"]
    tr, ca, te = idx["train"], idx["calibration"], idx["test"]
    X_train, y_train = _sub(Xf, tr), pd.Series(yf[tr])
    X_calib, y_calib = _sub(Xf, ca), pd.Series(yf[ca])
    X_test, y_test = _sub(Xf, te), yf[te]
    tt = meta.loc[te, "target_time"].to_numpy()
    levels = cfg["coverage_levels"]

    cqr_rows, enbpi_rows, combined, cqr_pred, enbpi_pred = [], [], [], [], []
    cqr_primary_models = {}

    # ---- CQR ----
    for level in levels:
        seed_intervals = []
        for seed in range(cfg["seed"], cfg["seed"] + cfg["conformal"]["cqr"]["seeds"]):
            model = conformal_cqr.fit_cqr(X_train, y_train, X_calib, y_calib, level, seed)
            res = conformal_cqr.cqr_interval(model, X_test)
            seed_intervals.append(res)
            if seed == cfg["seed"]:
                cqr_primary_models[level] = model
        primary = seed_intervals[0]
        im = M.interval_metrics(y_test, primary["lower"], primary["upper"], level)
        covs = [M.empirical_coverage(y_test, r["lower"], r["upper"]) for r in seed_intervals]
        wids = [M.mean_interval_width(r["lower"], r["upper"]) for r in seed_intervals]
        row = {"horizon": horizon, "nominal_coverage": level, **im,
               "coverage_std": float(np.std(covs)), "width_std": float(np.std(wids)),
               "n_seeds": len(seed_intervals)}
        cqr_rows.append(row)
        combined.append({
            "dataset": "PLEIAData", "target_sensor": target_name, "horizon": horizon,
            "point_model": "HistGBR-quantile", "conformal_method": "CQR",
            "nominal_coverage": level, "empirical_coverage": im["empirical_coverage"],
            "coverage_deviation": im["coverage_deviation"],
            "mean_interval_width": im["mean_interval_width"],
            "median_interval_width": im["median_interval_width"],
            "winkler_score": im["winkler_score"],
        })
        cqr_pred.append(pd.DataFrame({
            "horizon": horizon, "nominal_coverage": level, "target_time": tt,
            "y_true": y_test, "point": primary["point"],
            "lower": primary["lower"], "upper": primary["upper"],
        }))

    # ---- EnbPI (static + updated) ----
    seed_results = []
    for seed in range(cfg["seed"], cfg["seed"] + cfg["conformal"]["enbpi"]["seeds"]):
        res = conformal_enbpi.run_enbpi(
            X_train, y_train, X_calib, y_calib, X_test, pd.Series(y_test),
            levels, cfg["conformal"]["enbpi"], seed,
        )
        seed_results.append(res)
    base_name = seed_results[0]["base_estimator"]

    for variant in ["static", "updated"]:
        for level in levels:
            primary = seed_results[0][variant][level]
            im = M.interval_metrics(y_test, primary["lower"], primary["upper"], level)
            covs = [M.empirical_coverage(y_test, r[variant][level]["lower"], r[variant][level]["upper"])
                    for r in seed_results]
            wids = [M.mean_interval_width(r[variant][level]["lower"], r[variant][level]["upper"])
                    for r in seed_results]
            enbpi_rows.append({"horizon": horizon, "variant": variant, "nominal_coverage": level,
                               **im, "coverage_std": float(np.std(covs)),
                               "width_std": float(np.std(wids)), "n_seeds": len(seed_results),
                               "base_estimator": base_name})
            combined.append({
                "dataset": "PLEIAData", "target_sensor": target_name, "horizon": horizon,
                "point_model": base_name, "conformal_method": f"EnbPI-{variant}",
                "nominal_coverage": level, "empirical_coverage": im["empirical_coverage"],
                "coverage_deviation": im["coverage_deviation"],
                "mean_interval_width": im["mean_interval_width"],
                "median_interval_width": im["median_interval_width"],
                "winkler_score": im["winkler_score"],
            })
            enbpi_pred.append(pd.DataFrame({
                "horizon": horizon, "variant": variant, "nominal_coverage": level,
                "target_time": tt, "y_true": y_test, "point": primary["point"],
                "lower": primary["lower"], "upper": primary["upper"],
            }))

    return {
        "cqr_rows": cqr_rows, "enbpi_rows": enbpi_rows, "combined": combined,
        "cqr_pred": pd.concat(cqr_pred, ignore_index=True),
        "enbpi_pred": pd.concat(enbpi_pred, ignore_index=True),
        "cqr_models": cqr_primary_models,
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def apply_fast_overrides(cfg: dict) -> dict:
    cfg["horizons"] = [1]
    cfg["models"]["xgboost"].update({"search_iter": 4, "cv_splits": 2, "seeds": 2})
    cfg["models"]["lstm"].update({"max_epochs": 3, "seeds": 1})
    cfg["conformal"]["cqr"]["seeds"] = 2
    cfg["conformal"]["enbpi"].update({"n_resamplings": 5, "seeds": 1, "update_step": 50})
    cfg["conformal"]["enbpi"]["base_n_estimators"] = 80
    cfg["bootstrap"]["n_boot"] = 100
    cfg["alerts"]["events"]["instances_per_type"] = 2
    return cfg


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the preliminary experiment.")
    parser.add_argument("--config", default="configs/pleia_preliminary.yaml")
    parser.add_argument("--fast", action="store_true", help="Reduced settings for a smoke test.")
    args = parser.parse_args()

    # MAPIE emits an INFO log for every re-sorted prediction; silence that noise
    # so the progress output stays readable.
    logging.disable(logging.INFO)

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.fast:
        cfg = apply_fast_overrides(cfg)

    seed = cfg["seed"]
    np.random.seed(seed)
    torch.manual_seed(seed)

    out = Path(cfg["paths"]["outputs_dir"])
    for sub in ["metrics", "predictions", "figures", "models", "report", "data_profiles"]:
        (out / sub).mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print("[1/9] Preparing data ...")
    prep = prepare_data.run(cfg)
    processed, boundaries = prep["processed"], prep["boundaries"]
    target_name = f"{prep['choice']['block']}-room{prep['choice']['room']}-{prep['choice']['sensor_variable']}"
    freq = pd.Timedelta(cfg["resample"]["freq"])

    train_std = float(processed.loc[processed.index < boundaries[0], "target"].std())

    horizon_data = {}
    point_metrics, cqr_metrics, enbpi_metrics, combined_metrics = [], [], [], []
    boot_rows = []
    pred_frames = {}
    cqr_pred_all, enbpi_pred_all = [], []

    for h in cfg["horizons"]:
        print(f"[2/9] Horizon {h}: building datasets ...")
        data = build_horizon_data(processed, h, cfg, boundaries)
        horizon_data[h] = data

        print(f"[3/9] Horizon {h}: point models ...")
        pr = run_point_models(data, h, cfg, out)
        point_metrics.extend(pr["metrics"])
        pred_frames[h] = pr["pred_df"]

        print(f"[4/9] Horizon {h}: conformal intervals ...")
        cf = run_conformal(data, h, cfg, target_name)
        cqr_metrics.extend(cf["cqr_rows"])
        enbpi_metrics.extend(cf["enbpi_rows"])
        combined_metrics.extend(cf["combined"])
        cqr_pred_all.append(cf["cqr_pred"])
        enbpi_pred_all.append(cf["enbpi_pred"])
        horizon_data[h]["cqr_models"] = cf["cqr_models"]

        # Bootstrap CIs (step 13) from the primary-seed predictions.
        te = data["idx"]["test"]
        y_test = data["yf"][te]
        best_point = min(["xgboost", "attention_lstm"],
                         key=lambda m: M.mae(y_test, pr["pred_df"][m].to_numpy()))
        bp = M.bootstrap_point_metrics(y_test, pr["pred_df"][best_point].to_numpy(),
                                       n_boot=cfg["bootstrap"]["n_boot"], seed=seed)
        boot_rows.append({"horizon": h, "quantity": f"point:{best_point}", **bp})
        for level in cfg["coverage_levels"]:
            sub = cf["cqr_pred"][cf["cqr_pred"]["nominal_coverage"] == level]
            bi = M.bootstrap_interval_metrics(sub["y_true"].to_numpy(), sub["lower"].to_numpy(),
                                              sub["upper"].to_numpy(),
                                              n_boot=cfg["bootstrap"]["n_boot"], seed=seed)
            boot_rows.append({"horizon": h, "quantity": f"CQR@{level}", **bi})

    # Persist metric tables.
    pd.DataFrame(point_metrics).to_csv(out / "metrics" / "point_forecast_metrics.csv", index=False)
    pd.DataFrame(cqr_metrics).to_csv(out / "metrics" / "cqr_interval_metrics.csv", index=False)
    pd.DataFrame(enbpi_metrics).to_csv(out / "metrics" / "enbpi_interval_metrics.csv", index=False)
    pd.DataFrame(combined_metrics).to_csv(out / "metrics" / "interval_metrics.csv", index=False)
    pd.concat(cqr_pred_all, ignore_index=True).to_csv(out / "predictions" / "cqr_predictions.csv", index=False)
    pd.concat(enbpi_pred_all, ignore_index=True).to_csv(out / "predictions" / "enbpi_predictions.csv", index=False)
    pd.DataFrame(boot_rows).to_csv(out / "metrics" / "bootstrap_metrics.csv", index=False)

    # ---- Figures 5 and metric comparison ----
    print("[5/9] Figures for point forecasts ...")
    make_point_figures(pred_frames, point_metrics, cfg, out)

    # ---- Alerts (steps 10-11) ----
    print("[6/9] Alerts ...")
    alert_ctx = run_alerts(horizon_data, processed, boundaries, train_std, target_name, cfg, out)

    # ---- Figure 6 ----
    make_interval_figure(horizon_data, cfg, out)

    # ---- Robustness (step 12) ----
    print("[7/9] Robustness ...")
    run_robustness(processed, boundaries, train_std, alert_ctx, cfg, out)

    # ---- Reproducibility artefacts + report ----
    print("[8/9] Writing report and reproducibility artefacts ...")
    write_repro_artifacts(cfg, prep, args.config, out)
    write_reports(cfg, prep, out)

    print(f"[9/9] Done in {time.time() - t0:.1f}s")


# --------------------------------------------------------------------------- #
# Figures
# --------------------------------------------------------------------------- #
def make_point_figures(pred_frames, point_metrics, cfg, out: Path):
    h = cfg["horizons"][0]
    df = pred_frames[h].copy().sort_values("target_time").reset_index(drop=True)
    w = cfg["plotting"]["window_steps"]
    window = df.iloc[:w].set_index("target_time")
    plotting.plot_point_forecasts(
        window, "y_true", ["persistence", "seasonal_naive", "xgboost", "attention_lstm"],
        out / "figures" / "figure_5_point_forecasts.png",
    )
    mdf = pd.DataFrame(point_metrics)
    plotting.plot_metric_comparison(mdf, out / "figures" / "point_metric_comparison.png")


def make_interval_figure(horizon_data, cfg, out: Path):
    h = cfg["alerts"]["primary_horizon"]
    level = cfg["alerts"]["primary_level"]
    data = horizon_data[h]
    model = data["cqr_models"][level]
    te = data["idx"]["test"]
    X_test = _sub(data["Xf"], te)
    meta = data["meta"].loc[te].reset_index(drop=True)
    res = conformal_cqr.cqr_interval(model, X_test)
    df = pd.DataFrame({
        "target_time": meta["target_time"].to_numpy(),
        "y_true": data["yf"][te], "point": res["point"],
        "lower": res["lower"], "upper": res["upper"],
    }).sort_values("target_time").reset_index(drop=True)
    w = cfg["plotting"]["window_steps"]
    plotting.plot_conformal_intervals(
        df.iloc[:w], f"CQR {int(level*100)}% intervals on the first test window (horizon {h})",
        out / "figures" / "figure_6_conformal_intervals.png",
    )


# --------------------------------------------------------------------------- #
# Alerts and robustness
# --------------------------------------------------------------------------- #
def run_alerts(horizon_data, processed, boundaries, train_std, target_name, cfg, out: Path):
    acfg = cfg["alerts"]
    h, level = acfg["primary_horizon"], acfg["primary_level"]
    freq = pd.Timedelta(cfg["resample"]["freq"])
    data = horizon_data[h]
    model = data["cqr_models"][level]

    ca, te = data["idx"]["calibration"], data["idx"]["test"]
    X_calib, X_test = _sub(data["Xf"], ca), _sub(data["Xf"], te)
    meta = data["meta"]
    y_calib = data["yf"][ca]
    y_test = data["yf"][te]
    times_calib = pd.DatetimeIndex(meta.loc[ca, "target_time"])
    times_test = pd.DatetimeIndex(meta.loc[te, "target_time"])

    ci = conformal_cqr.cqr_interval(model, X_calib)
    ti = conformal_cqr.cqr_interval(model, X_test)

    # Rule selection on calibration only.
    rule_name, sel_table = alert_mod.select_rule(
        y_calib, ci["lower"], ci["upper"], train_std, freq, times_calib, acfg, seed=cfg["seed"],
    )
    sel_table.to_csv(out / "metrics" / "alert_rule_selection.csv", index=False)
    k, m = alert_mod.RULES[rule_name]

    # Clean test -> natural false alerts.
    viol_clean = alert_mod.point_violations(y_test, ti["lower"], ti["upper"])
    alerts_clean = alert_mod.apply_rule(viol_clean, k, m)
    nat = alert_mod.natural_false_alerts(alerts_clean, len(y_test), freq)

    # Injected test events (fresh, distinct seed).
    perturbed, catalog = alert_mod.inject_events(
        y_test, train_std, freq, times_test, acfg["events"],
        seed=cfg["seed"] + 100, dataset_label="test",
    )
    catalog.to_csv(out / "data_profiles" / "injected_event_catalog.csv", index=False)
    viol = alert_mod.point_violations(perturbed, ti["lower"], ti["upper"])
    alerts = alert_mod.apply_rule(viol, k, m)
    ev = alert_mod.evaluate_alerts(alerts, catalog, len(y_test), freq,
                                   acfg["detection_tolerance_steps"])

    rows = [
        {"scenario": "clean_test", "rule": rule_name, "conformal_method": "CQR",
         "nominal_coverage": level, "horizon": h,
         "true_positives": np.nan, "false_positives": nat["false_positives"],
         "false_negatives": np.nan, "precision": np.nan, "recall": np.nan, "f1": np.nan,
         "false_alert_events_per_day": nat["false_alert_events_per_day"],
         "mean_detection_delay_min": np.nan, "median_detection_delay_min": np.nan,
         "n_events": 0},
        {"scenario": "injected_test", "rule": rule_name, "conformal_method": "CQR",
         "nominal_coverage": level, "horizon": h, **ev},
    ]
    pd.DataFrame(rows).to_csv(out / "metrics" / "alert_metrics.csv", index=False)

    # Figure 7 centred on the first injected event.
    plot_alert_figure(times_test, perturbed, ti, viol, alerts, catalog, cfg, out)

    return {
        "rule": (k, m), "rule_name": rule_name, "level": level, "horizon": h,
        "cqr_model": model, "test_start_time": times_test.min(),
    }


def plot_alert_figure(times_test, perturbed, ti, viol, alerts, catalog, cfg, out: Path):
    df = pd.DataFrame({
        "target_time": times_test, "observed": perturbed,
        "lower": ti["lower"], "upper": ti["upper"],
        "violation": viol, "alert": alerts,
    }).sort_values("target_time").reset_index(drop=True)
    w = cfg["plotting"]["window_steps"]
    if len(catalog):
        first = catalog.sort_values("start_index").iloc[0]
        centre = int(first["start_index"])
        lo = max(0, centre - w // 3)
        sub = df.iloc[lo: lo + w]
        cat = catalog[(catalog["start_index"] >= lo) & (catalog["start_index"] < lo + w)]
    else:
        sub, cat = df.iloc[:w], catalog
    plotting.plot_alert_timeline(
        sub, cat, "Alert timeline around the first injected test event",
        out / "figures" / "figure_7_alert_timeline.png",
    )


def run_robustness(processed, boundaries, train_std, alert_ctx, cfg, out: Path):
    freq = pd.Timedelta(cfg["resample"]["freq"])
    season = cfg["resample"]["season_steps"]
    fcfg = feature_cfg(cfg)
    model = alert_ctx["cqr_model"]

    def predict_fn(X_df):
        res = conformal_cqr.cqr_interval(model, X_df)
        return res["point"], res["lower"], res["upper"]

    table = robustness.run(
        processed, alert_ctx["test_start_time"], freq, season, fcfg,
        predict_fn, alert_ctx["rule"], train_std, alert_ctx["level"],
        cfg["robustness"], seed=cfg["seed"],
    )
    table.to_csv(out / "metrics" / "preliminary_robustness_metrics.csv", index=False)


# --------------------------------------------------------------------------- #
# Reproducibility + reporting
# --------------------------------------------------------------------------- #
def write_repro_artifacts(cfg, prep, config_path, out: Path):
    import sklearn, xgboost, mapie, scipy, matplotlib
    versions = {
        "python": __import__("sys").version.split()[0],
        "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__, "xgboost": xgboost.__version__,
        "torch": torch.__version__, "mapie": mapie.__version__,
        "matplotlib": matplotlib.__version__,
    }
    with open(out / "report" / "environment_versions.json", "w") as f:
        json.dump(versions, f, indent=2)

    seeds = {
        "global_seed": cfg["seed"],
        "xgboost_seeds": list(range(cfg["seed"], cfg["seed"] + cfg["models"]["xgboost"]["seeds"])),
        "lstm_seeds": list(range(cfg["seed"], cfg["seed"] + cfg["models"]["lstm"]["seeds"])),
        "cqr_seeds": list(range(cfg["seed"], cfg["seed"] + cfg["conformal"]["cqr"]["seeds"])),
        "enbpi_seeds": list(range(cfg["seed"], cfg["seed"] + cfg["conformal"]["enbpi"]["seeds"])),
        "alert_test_injection_seed": cfg["seed"] + 100,
    }
    with open(out / "report" / "random_seed_log.json", "w") as f:
        json.dump(seeds, f, indent=2)

    with open(out / "models" / "lstm_config.json", "w") as f:
        json.dump(cfg["models"]["lstm"], f, indent=2)


def write_reports(cfg, prep, out: Path):
    """Compose the report files strictly from the persisted CSVs."""
    from . import reporting
    reporting.build(cfg, prep, out)


if __name__ == "__main__":
    main()
