"""Compose the report-ready markdown files from the persisted CSV outputs.

Nothing here computes a metric; every number is read back from a file written
earlier in the run, so the reports cannot contain values that are not also in
the machine-readable outputs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _load(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def _f(x, nd=3) -> str:
    if x is None:
        return "n/a"
    try:
        if pd.isna(x):
            return "n/a"
    except (TypeError, ValueError):
        pass
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if isinstance(x, (float, np.floating)):
        return f"{x:.{nd}f}"
    return str(x)


def _md_table(df: pd.DataFrame, cols: list[str], headers: list[str], nd=3) -> str:
    lines = ["| " + " | ".join(headers) + " |",
             "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(_f(row[c], nd) for c in cols) + " |")
    return "\n".join(lines)


def build(cfg: dict, prep: dict, out: Path) -> None:
    metrics = out / "metrics"
    profiles = out / "data_profiles"

    pre = _load(profiles / "preprocessing_summary.csv")
    splits = _load(profiles / "split_summary.csv")
    point = _load(metrics / "point_forecast_metrics.csv")
    interval = _load(metrics / "interval_metrics.csv")
    cqr = _load(metrics / "cqr_interval_metrics.csv")
    enbpi = _load(metrics / "enbpi_interval_metrics.csv")
    alerts = _load(metrics / "alert_metrics.csv")
    robust = _load(metrics / "preliminary_robustness_metrics.csv")
    boot = _load(metrics / "bootstrap_metrics.csv")

    _write_narrative(cfg, out, pre, splits, point, interval, cqr, enbpi, alerts, robust, boot)
    _write_tables(cfg, out, pre, splits, point, interval, alerts)


def _best_by(point: pd.DataFrame, horizon: int, metric: str) -> pd.Series:
    sub = point[point["horizon"] == horizon]
    return sub.loc[sub[metric].idxmin()]


def _write_narrative(cfg, out, pre, splits, point, interval, cqr, enbpi, alerts, robust, boot):
    L = []
    L.append("# Preliminary Experiment: Report-Ready Results\n")
    L.append("_All values below are read directly from the CSV files in "
             "`outputs/metrics` and `outputs/data_profiles`._\n")

    # 1. Dataset and preprocessing
    L.append("## 1. Dataset and Preprocessing\n")
    if pre is not None and splits is not None:
        r = pre.iloc[0]
        tr = splits[splits["split"] == "train"].iloc[0]
        ca = splits[splits["split"] == "calibration"].iloc[0]
        te = splits[splits["split"] == "test"].iloc[0]
        L.append(
            f"The preliminary target is the indoor-temperature series (variable "
            f"`{r['sensor_variable']}`) of room {r['room']} in block {r['block']} of the "
            f"PLEIAData dataset, resampled to a regular {r['resample_freq']} grid over "
            f"{r['start']} to {r['end']} ({int(r['n_processed_steps'])} steps). "
            f"Physically implausible readings outside "
            f"[{_f(r['target_min_bound'],1)}, {_f(r['target_max_bound'],1)}] °C were removed "
            f"({int(r['n_outliers_removed'])} values); short gaps up to "
            f"{cfg['missing']['max_short_gap_steps']} steps were interpolated. "
            f"The series was partitioned chronologically into "
            f"{int(tr['n_steps'])} training, {int(ca['n_steps'])} calibration and "
            f"{int(te['n_steps'])} test steps (60/20/20), with "
            f"train ending {tr['end']}, calibration {ca['start']}–{ca['end']}, and test "
            f"beginning {te['start']}.\n"
        )

    # 2. Point forecasting
    L.append("## 2. Preliminary Point-Forecasting Results\n")
    if point is not None:
        for h in sorted(point["horizon"].unique()):
            bmae = _best_by(point, h, "mae")
            brmse = _best_by(point, h, "rmse")
            L.append(
                f"At horizon {int(h)} the lowest test MAE was achieved by "
                f"**{bmae['model']}** (MAE {_f(bmae['mae'])} °C, "
                f"{_f(bmae['pct_mae_improvement'],1)}% better than persistence); the lowest "
                f"RMSE by **{brmse['model']}** (RMSE {_f(brmse['rmse'])} °C, "
                f"{_f(brmse['pct_rmse_improvement'],1)}% better than persistence)."
            )
        L.append("")
    if boot is not None and len(boot):
        pt = boot[boot["quantity"].str.startswith("point")]
        for _, r in pt.iterrows():
            L.append(
                f"- Horizon {int(r['horizon'])} {r['quantity']}: MAE {_f(r['mae'])} "
                f"(95% CI {_f(r['mae_ci_low'])}–{_f(r['mae_ci_high'])}), "
                f"RMSE {_f(r['rmse'])} (95% CI {_f(r['rmse_ci_low'])}–{_f(r['rmse_ci_high'])})."
            )
        L.append("")

    # 3. Interval results
    L.append("## 3. Preliminary Prediction-Interval Results\n")
    if interval is not None:
        for method in interval["conformal_method"].unique():
            sub = interval[interval["conformal_method"] == method]
            L.append(f"**{method}**")
            for _, r in sub.iterrows():
                L.append(
                    f"- h{int(r['horizon'])}, nominal {int(r['nominal_coverage']*100)}%: "
                    f"empirical coverage {_f(r['empirical_coverage'])} "
                    f"(deviation {_f(r['coverage_deviation'])}), mean width "
                    f"{_f(r['mean_interval_width'])} °C, Winkler {_f(r['winkler_score'])}."
                )
            L.append("")

    # 4. Alerts
    L.append("## 4. Preliminary Alert Results\n")
    if alerts is not None and len(alerts):
        clean = alerts[alerts["scenario"] == "clean_test"]
        inj = alerts[alerts["scenario"] == "injected_test"]
        rule = alerts.iloc[0]["rule"]
        L.append(
            f"The aggregation rule selected on the calibration set (with its own injected "
            f"events) was **{rule}**, using {alerts.iloc[0]['conformal_method']} "
            f"{int(float(alerts.iloc[0]['nominal_coverage'])*100)}% intervals at horizon "
            f"{int(alerts.iloc[0]['horizon'])}."
        )
        if len(clean):
            c = clean.iloc[0]
            L.append(
                f"On unmodified test data the rule produced "
                f"{int(c['false_positives'])} false-alert clusters "
                f"({_f(c['false_alert_events_per_day'])} per day)."
            )
        if len(inj):
            i = inj.iloc[0]
            L.append(
                f"On test data with {int(i['n_events'])} injected events it detected "
                f"{int(i['true_positives'])} (recall {_f(i['recall'])}, precision "
                f"{_f(i['precision'])}, F1 {_f(i['f1'])}), with "
                f"{int(i['false_positives'])} false-alert clusters "
                f"({_f(i['false_alert_events_per_day'])}/day) and mean/median detection "
                f"delay {_f(i['mean_detection_delay_min'],1)}/"
                f"{_f(i['median_detection_delay_min'],1)} min."
            )
        L.append("")

    # 5. Robustness
    L.append("## 5. Preliminary Robustness Results\n")
    L.append("_Preliminary probe only; not the full dissertation robustness study._\n")
    if robust is not None and len(robust):
        L.append(_md_table(
            robust,
            ["scenario", "mae", "rmse", "empirical_coverage", "mean_interval_width",
             "alert_recall", "false_alert_events_per_day"],
            ["Scenario", "MAE", "RMSE", "Coverage", "Width", "Alert recall", "False/day"],
        ))
        L.append("")

    # 6. Limitations
    L.append("## 6. Limitations of the Preliminary Experiment\n")
    L.append(
        "- A single room from one dataset is used; results are not yet generalised across "
        "sensors or buildings.\n"
        "- The authors' processed file is already gap-filled, so the series shows no "
        "residual missingness; missing-data handling is exercised mainly through the "
        "synthetic robustness scenarios.\n"
        "- Prediction intervals are held fixed when synthetic events are injected, so "
        "feedback of a perturbation into the model features is not modelled.\n"
        "- EnbPI residual updating is applied per direct-horizon step and, for horizons "
        "greater than one, anticipates ground-truth availability; this is an "
        "approximation.\n"
        "- Alert-rule selection optimises a simple recall / false-alert trade-off on one "
        "calibration injection; a broader operating-point study is future work.\n"
        "- Seed counts for the LSTM and EnbPI are reduced relative to the ideal five "
        "because of CPU runtime (see `random_seed_log.json`).\n"
    )

    (out / "report" / "report_ready_results.md").write_text("\n".join(L), encoding="utf-8")


def _write_tables(cfg, out, pre, splits, point, interval, alerts):
    L = ["# Filled Result Placeholders\n",
         "_Populated from the generated CSV outputs._\n"]

    # Table 15
    L.append("## Table 15 — Preliminary Dataset and Preprocessing Summary\n")
    if pre is not None and splits is not None:
        r = pre.iloc[0]
        rows = [
            ("Dataset", r["dataset"]),
            ("Target sensor", f"block {r['block']}, room {r['room']}, variable {r['sensor_variable']}"),
            ("Date range", f"{r['start']} – {r['end']}"),
            ("Resample interval", r["resample_freq"]),
            ("Processed steps", int(r["n_processed_steps"])),
            ("Outliers removed", int(r["n_outliers_removed"])),
            ("Raw missing fraction", _f(r["missing_fraction"], 4)),
        ]
        for name in ["train", "calibration", "test"]:
            s = splits[splits["split"] == name].iloc[0]
            rows.append((f"{name.capitalize()} steps", int(s["n_steps"])))
        L.append("| Item | Value |\n| --- | --- |")
        L += [f"| {k} | {_f(v)} |" for k, v in rows]
        L.append("")

    # Table 16
    L.append("## Table 16 — Preliminary Point-Forecasting Performance\n")
    if point is not None:
        L.append(_md_table(
            point,
            ["horizon", "model", "mae", "rmse", "mae_std", "rmse_std",
             "pct_mae_improvement", "pct_rmse_improvement", "n_seeds"],
            ["Horizon", "Model", "MAE", "RMSE", "MAE std", "RMSE std",
             "MAE impr %", "RMSE impr %", "Seeds"],
        ))
        L.append("")

    # Table 17
    L.append("## Table 17 — Preliminary Prediction-Interval Performance\n")
    if interval is not None:
        L.append(_md_table(
            interval,
            ["horizon", "conformal_method", "nominal_coverage", "empirical_coverage",
             "coverage_deviation", "mean_interval_width", "median_interval_width", "winkler_score"],
            ["Horizon", "Method", "Nominal", "Empirical", "Cov. dev.",
             "Mean width", "Median width", "Winkler"],
        ))
        L.append("")

    # Table 18
    L.append("## Table 18 — Preliminary Interval-Based Alert Performance\n")
    if alerts is not None:
        L.append(_md_table(
            alerts,
            ["scenario", "rule", "true_positives", "false_positives", "false_negatives",
             "precision", "recall", "f1", "false_alert_events_per_day",
             "mean_detection_delay_min", "median_detection_delay_min"],
            ["Scenario", "Rule", "TP", "FP", "FN", "Precision", "Recall", "F1",
             "False/day", "Mean delay", "Median delay"],
        ))
        L.append("")

    (out / "report" / "result_placeholders_filled.md").write_text("\n".join(L), encoding="utf-8")
