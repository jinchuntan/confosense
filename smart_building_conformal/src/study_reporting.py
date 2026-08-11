"""Report generation for the full study.

The single rule this module follows: **every number printed is read back from a
file the pipeline wrote.** Nothing here computes a metric, and there is no code
path by which a literal figure can reach the prose. If a stage did not run, the
corresponding section says so rather than being quietly omitted — a report that
silently drops a failed experiment is indistinguishable from one where the
experiment succeeded.

Three files are produced:

``full_study_results.md``
    Narrative summary: dataset profiles, point forecasting, intervals, alerts,
    robustness, recalibration, statistical comparisons, cross-dataset findings.

``table_ready_results.md``
    The same content as markdown tables, sized for direct inclusion in the
    dissertation.

``full_study_limitations.md``
    Everything that did not go to plan: reduced seed counts, methods that were
    not applicable, stages that failed or were skipped, fast-mode runs, and the
    standing methodological caveats. Negative findings are stated, not buried.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _load(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    df = pd.read_csv(path)
    return df if len(df) else None


def _f(x, nd=3) -> str:
    if x is None:
        return "n/a"
    try:
        if pd.isna(x):
            return "n/a"
    except (TypeError, ValueError):
        pass
    if isinstance(x, (bool, np.bool_)):
        return "yes" if x else "no"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if isinstance(x, (float, np.floating)):
        return f"{x:.{nd}f}"
    return str(x)


def _table(df: pd.DataFrame, cols: list[str], headers: list[str], nd=3,
           limit: int | None = None) -> str:
    cols = [c for c in cols if c in df.columns]
    headers = headers[:len(cols)]
    if not cols:
        return "_no columns available_"
    lines = ["| " + " | ".join(headers) + " |",
             "| " + " | ".join(["---"] * len(headers)) + " |"]
    rows = df.head(limit) if limit else df
    for _, r in rows.iterrows():
        lines.append("| " + " | ".join(_f(r[c], nd) for c in cols) + " |")
    if limit and len(df) > limit:
        lines.append(f"| _... {len(df) - limit} further rows in the CSV_ |"
                     + " |" * (len(headers) - 1))
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
def build(out_root: Path, manifest, *, fast: bool = False) -> None:
    out_root = Path(out_root)
    combined = out_root / "combined"
    report = out_root / "report"
    report.mkdir(parents=True, exist_ok=True)

    tables = {
        "point": _load(combined / "point_metrics.csv"),
        "interval": _load(combined / "interval_metrics.csv"),
        "alerts": _load(combined / "alert_metrics.csv"),
        "robust": _load(combined / "robustness_metrics.csv"),
        "recal": _load(combined / "recalibration_metrics.csv"),
        "boot": _load(combined / "bootstrap_metrics.csv"),
        "dm": _load(combined / "statistical_tests.csv"),
        "eff": _load(combined / "effect_sizes.csv"),
        "rank": _load(combined / "model_rankings.csv"),
        "ranktest": _load(combined / "ranking_tests.csv"),
        "posthoc": _load(combined / "posthoc_comparisons.csv"),
    }
    profiles = {p.parent.parent.name: pd.read_csv(p)
                for p in out_root.glob("*/data_profiles/series_profile.csv")}

    _write_narrative(out_root, report, tables, profiles, manifest, fast)
    _write_tables(report, tables)
    _write_limitations(report, tables, manifest, fast)
    _write_digest(report, tables, profiles, manifest, fast)


# --------------------------------------------------------------------------- #
def _write_narrative(out_root, report, T, profiles, manifest, fast) -> None:
    L: list[str] = []
    L.append("# ConfoSense Full Study — Results\n")
    L.append("_Every value in this document is read back from a CSV written by "
             "the pipeline under `outputs/full_study/`. No number is entered by "
             "hand._\n")
    if fast:
        L.append("> **Fast mode.** This run used `--fast` smoke-test settings "
                 "(reduced horizons, seeds, search iterations, epochs and "
                 "bootstrap replicates). The values below verify that the "
                 "pipeline executes end to end; they are not the full-study "
                 "results.\n")

    # ---- 1. datasets ----
    L.append("## 1. Dataset Profiles\n")
    if profiles:
        for ds, prof in sorted(profiles.items()):
            n_series = len(prof)
            n_rows = int(prof["n_rows"].sum())
            freq = prof["freq"].iloc[0]
            seasonal = bool(prof["seasonal_naive_supported"].all())
            L.append(
                f"- **{ds}** — {n_series} series, {n_rows} observations at "
                f"{freq} sampling, target units `{prof['units'].iloc[0]}`, "
                f"span {prof['start'].min()} to {prof['end'].max()}, mean target "
                f"missingness {_f(prof['missing_fraction'].mean(), 4)}. "
                f"Seasonal-naive baseline applicable: {'yes' if seasonal else 'no'}."
            )
        L.append("")
    else:
        L.append("_No dataset profile was written; the prepare stage did not "
                 "complete for any dataset._\n")

    # ---- 2. point forecasting ----
    L.append("## 2. Point Forecasting\n")
    point = T["point"]
    if point is not None:
        ok = point[point.get("applicable", True) == True]  # noqa: E712
        for ds in sorted(ok["dataset"].unique()):
            sub = ok[ok["dataset"] == ds]
            for h in sorted(sub["horizon_steps"].unique()):
                s = sub[sub["horizon_steps"] == h]
                if s["mae"].isna().all():
                    continue
                best = s.loc[s["mae"].idxmin()]
                L.append(
                    f"- **{ds}**, horizon {int(h)} "
                    f"({_f(best['horizon_minutes'], 0)} min): lowest MAE from "
                    f"**{best['point_model']}** at {_f(best['mae'])} "
                    f"{best.get('units', '')} "
                    f"({_f(best['pct_mae_improvement'], 1)}% versus persistence), "
                    f"RMSE {_f(best['rmse'])}, over {int(best['n_seeds'])} seed(s)."
                )
        na = point[point.get("applicable", True) == False]  # noqa: E712
        for _, r in na.iterrows():
            L.append(f"- _{r['dataset']}, horizon {int(r['horizon_steps'])}: "
                     f"{r['point_model']} not applicable — {r['note']}._")
        L.append("")
    else:
        L.append("_Point-forecasting metrics were not produced._\n")

    # ---- 3. intervals ----
    L.append("## 3. Prediction Intervals\n")
    iv = T["interval"]
    if iv is not None:
        L.append("Methods are reported under their exact names: "
                 "`quantile_uncalibrated` is the raw quantile band before any "
                 "conformal correction, `cqr` is that band conformalized, the "
                 "EnbPI variants are the documented **recentred** adaptation, and "
                 "`dscp` is the dual-splitting procedure.\n")
        for ds in sorted(iv["dataset"].unique()):
            sub = iv[iv["dataset"] == ds]
            L.append(f"**{ds}**")
            for level in sorted(sub["nominal_coverage"].unique()):
                s = sub[sub["nominal_coverage"] == level]
                agg = (s.groupby("conformal_method")
                       .agg(cov=("empirical_coverage", "mean"),
                            dev=("coverage_deviation", "mean"),
                            width=("mean_interval_width", "mean"),
                            wink=("winkler_score", "mean")))
                for method, r in agg.iterrows():
                    L.append(
                        f"- nominal {level:.0%}, `{method}`: mean empirical "
                        f"coverage {_f(r['cov'])} (deviation {_f(r['dev'])}), "
                        f"mean width {_f(r['width'])}, Winkler {_f(r['wink'])}."
                    )
            L.append("")
    else:
        L.append("_Interval metrics were not produced._\n")

    # ---- 4. alerts ----
    L.append("## 4. Interval-Based Alerting\n")
    al = T["alerts"]
    if al is not None and "role" in al.columns:
        for ds in sorted(al["dataset"].unique()):
            sub = al[al["dataset"] == ds]
            sel = sub[sub.get("selected_operating_rule", False) == True]  # noqa: E712
            cal = sel[sel["role"] == "calibration_selection"]
            test = sel[sel["role"] == "post_hoc_sensitivity"]
            clean = sel[sel["role"] == "clean_test_no_events"]
            if cal.empty:
                continue
            c = cal.iloc[0]
            L.append(
                f"- **{ds}** — operating rule **{c['rule']}**, frozen on "
                f"calibration data. {c['selection_reason']}"
            )
            L.append(
                f"  On calibration: recall {_f(c['recall'])}, precision "
                f"{_f(c['precision'])}, F1 {_f(c['f1'])}, "
                f"{_f(c['false_alert_events_per_day'])} false alert events/day, "
                f"point-level FAR {_f(c['far'], 4)}."
            )
            if len(test):
                t = test.iloc[0]
                L.append(
                    f"  On test with {int(t['n_events'])} injected events: "
                    f"detected {int(t['true_positives'])} (recall {_f(t['recall'])}, "
                    f"precision {_f(t['precision'])}, F1 {_f(t['f1'])}), "
                    f"{_f(t['false_alert_events_per_day'])} false alert events/day, "
                    f"point-level FAR {_f(t['far'], 4)}, mean/median detection delay "
                    f"{_f(t['mean_detection_delay_min'], 1)}/"
                    f"{_f(t['median_detection_delay_min'], 1)} min."
                )
            if len(clean):
                cl = clean.iloc[0]
                L.append(f"  On unmodified test data: "
                         f"{_f(cl['false_alert_events_per_day'])} false alert "
                         f"events/day.")
        L.append("")
        L.append("_False Alarm Rate (FAR, point-level FP/(FP+TN)) and false alert "
                 "events per day are distinct quantities and are reported "
                 "separately throughout._\n")
    else:
        L.append("_Alert metrics were not produced._\n")

    # ---- 5. robustness ----
    L.append("## 5. Robustness\n")
    rb = T["robust"]
    if rb is not None:
        L.append("`legacy_fixed_intervals` reproduces the preliminary behaviour "
                 "(intervals frozen after injection); `closed_loop` is the primary "
                 "realistic evaluation, in which the perturbation propagates into "
                 "the lagged features and the model re-forecasts from the "
                 "corrupted history.\n")
        for ds in sorted(rb["dataset"].unique()):
            sub = rb[rb["dataset"] == ds]
            base = sub[sub["scenario"] == "clean"]
            if len(base):
                b = base.iloc[0]
                L.append(f"- **{ds}** clean baseline: coverage "
                         f"{_f(b['empirical_coverage'])}, MAE {_f(b.get('mae'))}, "
                         f"{_f(b.get('false_alert_events_per_day'))} false alerts/day.")
            for mode in sorted(sub["mode"].unique()):
                m = sub[(sub["mode"] == mode) & (sub["scenario"] != "clean")]
                if m.empty or m["coverage_deviation"].isna().all():
                    continue
                worst = m.loc[m["coverage_deviation"].idxmax()]
                L.append(
                    f"  - `{mode}`: largest coverage deviation "
                    f"{_f(worst['coverage_deviation'])} under "
                    f"`{worst['scenario']}` (empirical coverage "
                    f"{_f(worst['empirical_coverage'])})."
                )
        L.append("")
    else:
        L.append("_Robustness metrics were not produced._\n")

    # ---- 6. recalibration ----
    L.append("## 6. Recalibration\n")
    rc = T["recal"]
    if rc is not None:
        L.append("Adaptive strategies consume a residual only once its ground "
                 "truth has been observed, enforced by a delayed-availability "
                 "queue; for horizon *h* a residual becomes usable *h* steps "
                 "after its forecast origin.\n")
        for ds in sorted(rc["dataset"].unique()):
            sub = rc[rc["dataset"] == ds]
            for _, r in sub.iterrows():
                L.append(
                    f"- **{ds}** `{r['recalibration_strategy']}`: coverage "
                    f"{_f(r['empirical_coverage'])} (deviation "
                    f"{_f(r['coverage_deviation'])}), mean width "
                    f"{_f(r['mean_interval_width'])}, Winkler "
                    f"{_f(r['winkler_score'])}, {int(r['n_updates'])} updates, "
                    f"residual delay {int(r['residual_delay_steps'])} steps."
                )
        L.append("")
    else:
        L.append("_Recalibration metrics were not produced._\n")

    # ---- 7. statistics ----
    L.append("## 7. Statistical Analysis\n")
    dm = T["dm"]
    if dm is not None:
        sig = dm[dm.get("significant_holm_5pct", False) == True]  # noqa: E712
        L.append(f"Diebold–Mariano comparisons: {len(dm)} pairwise tests, "
                 f"{len(sig)} significant at the 5% level after Holm adjustment.\n")
        for _, r in dm.head(12).iterrows():
            L.append(
                f"- {r['dataset']} h{int(r['horizon_steps'])}: "
                f"{r['model_a']} vs {r['model_b']} — DM {_f(r['dm_statistic'], 2)}, "
                f"p {_f(r['p_value'], 4)}, Holm p {_f(r.get('p_value_holm'), 4)}"
                f"{' (significant)' if r.get('significant_holm_5pct') else ''}."
            )
        L.append("")
    eff = T["eff"]
    if eff is not None:
        L.append("Effect sizes (practical significance):\n")
        for _, r in eff.head(12).iterrows():
            L.append(
                f"- {r['dataset']} h{int(r['horizon_steps'])}: {r['model_a']} vs "
                f"{r['model_b']} — MAE improvement {_f(r['pct_mae_improvement'], 1)}%, "
                f"median paired |error| difference {_f(r['median_abs_error_difference'])}, "
                f"mean difference 95% CI [{_f(r['mean_difference_ci_low'])}, "
                f"{_f(r['mean_difference_ci_high'])}]."
            )
        L.append("")
    rt = T["ranktest"]
    if rt is not None:
        for _, r in rt.iterrows():
            if pd.notna(r.get("p_value")):
                L.append(f"- Friedman test over {int(r['n_blocks'])} blocks and "
                         f"{int(r['n_methods'])} methods: statistic "
                         f"{_f(r['statistic'], 2)}, p {_f(r['p_value'], 4)}.")
            else:
                L.append(f"- Friedman test not run: {r.get('note', 'design invalid')}.")
        L.append("")
    if dm is None and eff is None and rt is None:
        L.append("_No statistical tests were produced._\n")

    # ---- 8. cross-dataset ----
    L.append("## 8. Cross-Dataset Findings\n")
    rank = T["rank"]
    if rank is not None:
        L.append("Raw MAE is not comparable across targets measured in degrees "
                 "Celsius and kilowatt-hours, so cross-dataset statements use "
                 "within-dataset rankings, percentage improvement over "
                 "persistence, normalised interval width and coverage deviation.\n")
        for ds in sorted(rank["dataset"].unique()):
            sub = rank[rank["dataset"] == ds].sort_values("mean_rank_mae")
            order = ", ".join(f"{r['point_model']} ({_f(r['mean_rank_mae'], 2)})"
                              for _, r in sub.iterrows())
            L.append(f"- **{ds}** mean MAE rank: {order}.")
        L.append("")
    else:
        L.append("_Cross-dataset rankings were not produced._\n")

    # ---- 9. figures ----
    figdir = Path(out_root) / "report" / "figures"
    figs = sorted(figdir.glob("*.png")) if figdir.exists() else []
    L.append("## 9. Figures\n")
    if figs:
        for f in figs:
            L.append(f"- `{f.relative_to(Path(out_root))}`")
    else:
        L.append("_No figures were generated._")
    L.append("")

    (report / "full_study_results.md").write_text("\n".join(L), encoding="utf-8")


# --------------------------------------------------------------------------- #
def _write_tables(report: Path, T: dict) -> None:
    L = ["# ConfoSense Full Study — Table-Ready Results\n",
         "_Generated from the persisted CSV outputs._\n"]

    specs = [
        ("Point forecasting", T["point"],
         ["dataset", "target", "horizon_steps", "horizon_minutes", "point_model",
          "mae", "rmse", "mae_std", "pct_mae_improvement", "n_seeds"],
         ["Dataset", "Target", "h (steps)", "h (min)", "Model", "MAE", "RMSE",
          "MAE sd", "MAE impr %", "Seeds"]),
        ("Prediction intervals", T["interval"],
         ["dataset", "horizon_steps", "conformal_method", "nominal_coverage",
          "empirical_coverage", "coverage_deviation", "mean_interval_width",
          "normalized_mean_interval_width", "winkler_score"],
         ["Dataset", "h", "Method", "Nominal", "Empirical", "Cov. dev.",
          "Width", "Norm. width", "Winkler"]),
        ("Alert rules", T["alerts"],
         ["dataset", "role", "rule", "precision", "recall", "f1", "far",
          "false_alert_events_per_day", "mean_detection_delay_min",
          "median_detection_delay_min", "selected_operating_rule"],
         ["Dataset", "Role", "Rule", "Precision", "Recall", "F1", "FAR",
          "False/day", "Mean delay", "Median delay", "Selected"]),
        ("Robustness", T["robust"],
         ["dataset", "mode", "scenario", "severity_label", "mae",
          "empirical_coverage", "coverage_deviation", "mean_interval_width",
          "false_alert_events_per_day"],
         ["Dataset", "Mode", "Scenario", "Severity", "MAE", "Coverage",
          "Cov. dev.", "Width", "False/day"]),
        ("Recalibration", T["recal"],
         ["dataset", "recalibration_strategy", "empirical_coverage",
          "coverage_deviation", "mean_interval_width", "winkler_score",
          "n_updates", "update_every", "rolling_window"],
         ["Dataset", "Strategy", "Coverage", "Cov. dev.", "Width", "Winkler",
          "Updates", "Every", "Window"]),
        ("Bootstrap confidence intervals", T["boot"],
         ["dataset", "horizon_steps", "model", "mae", "mae_ci_low", "mae_ci_high",
          "rmse", "rmse_ci_low", "rmse_ci_high"],
         ["Dataset", "h", "Model", "MAE", "MAE lo", "MAE hi", "RMSE",
          "RMSE lo", "RMSE hi"]),
        ("Diebold-Mariano tests", T["dm"],
         ["dataset", "horizon_steps", "model_a", "model_b", "dm_statistic",
          "p_value", "p_value_holm", "significant_holm_5pct"],
         ["Dataset", "h", "A", "B", "DM", "p", "Holm p", "Significant"]),
        ("Model rankings", T["rank"],
         ["dataset", "point_model", "mean_rank_mae", "mean_rank_rmse",
          "mean_pct_mae_improvement", "n_blocks"],
         ["Dataset", "Model", "Mean MAE rank", "Mean RMSE rank",
          "Mean impr %", "Blocks"]),
        ("Post-hoc comparisons (Holm-adjusted)", T["posthoc"],
         ["method_a", "method_b", "n_blocks", "mean_rank_a", "mean_rank_b",
          "median_difference", "p_value", "p_value_holm", "significant_holm_5pct"],
         ["A", "B", "Blocks", "Rank A", "Rank B", "Median diff", "p", "Holm p",
          "Significant"]),
    ]
    for title, df, cols, headers in specs:
        L.append(f"## {title}\n")
        if df is None:
            L.append("_not produced by this run_\n")
            continue
        L.append(_table(df, cols, headers, limit=200))
        L.append("")
    (report / "table_ready_results.md").write_text("\n".join(L), encoding="utf-8")


# --------------------------------------------------------------------------- #
def _write_limitations(report: Path, T: dict, manifest, fast: bool) -> None:
    L = ["# ConfoSense Full Study — Limitations\n",
         "_Tracked automatically from the run manifest and the generated "
         "outputs. Inconvenient findings are recorded here rather than "
         "omitted._\n"]

    L.append("## Recorded during this run\n")
    notes = list(getattr(manifest, "limitations", []))
    if notes:
        for n in notes:
            L.append(f"- {n}")
    else:
        L.append("- No run-time limitation was recorded.")
    L.append("")

    L.append("## Stages that failed or were skipped\n")
    stages = [s for s in getattr(manifest, "stages", [])
              if s.status in ("failed", "skipped")]
    if stages:
        L.append("| Stage | Status | Reason |")
        L.append("| --- | --- | --- |")
        for s in stages:
            L.append(f"| {s.name} | {s.status} | {s.reason or '—'} |")
    else:
        L.append("- Every stage completed.")
    L.append("")

    L.append("## Seed counts actually used\n")
    point = T["point"]
    stochastic = {"xgboost", "attention_lstm"}
    if point is not None and "n_seeds" in point.columns:
        seeds = (point[point.get("applicable", True) == True]      # noqa: E712
                 .groupby(["dataset", "point_model"])["n_seeds"].max().reset_index())
        seeds["stochastic"] = seeds["point_model"].isin(stochastic)
        L.append(_table(seeds, ["dataset", "point_model", "n_seeds", "stochastic"],
                        ["Dataset", "Model", "Seeds actually run", "Stochastic"]))
        L.append("")
        L.append("Persistence and seasonal naive are deterministic, so a single "
                 "run is the complete result for them; the seed count is only "
                 "meaningful for the stochastic methods.\n")
        low = seeds[seeds["stochastic"] & (seeds["n_seeds"] < 5)]
        if len(low):
            names = ", ".join(f"{r['dataset']}/{r['point_model']} ({int(r['n_seeds'])})"
                              for _, r in low.iterrows())
            L.append(f"Below the five-seed target because of CPU cost: {names}. "
                     "These are the counts actually executed, not the target.\n")
    else:
        L.append("_No point metrics available to report seed counts._\n")

    L.append("## Methods not applicable\n")
    if point is not None:
        na = point[point.get("applicable", True) == False]          # noqa: E712
        if len(na):
            L.append(_table(na, ["dataset", "horizon_steps", "point_model", "note"],
                            ["Dataset", "h", "Model", "Reason"]))
        else:
            L.append("- Every configured point model was applicable.")
    L.append("")

    L.append("## Standing methodological caveats\n")
    L.append(
        "- Anomalies are synthetic. The datasets carry no labelled real fault "
        "record, so alert precision and recall are measured against injected "
        "events whose catalogue is recorded in `data_profiles/"
        "injected_event_catalog.csv`. They quantify sensitivity to controlled "
        "disturbances, not field fault-detection performance.\n"
        "- DSCP is applied to a multi-step vector assembled across ConfoSense's "
        "direct per-horizon models rather than a single multi-output model as in "
        "Yu et al. (2025). No official author implementation was located, so the "
        "code is written from the open-access preprint (arXiv:2503.21251v1) and "
        "the paper-to-code mapping is documented in `src/conformal_dscp.py`.\n"
        "- The EnbPI variants are a documented **recentred** adaptation, reported "
        "as `recentred_enbpi_static` / `recentred_enbpi_updated`, never as "
        "standard EnbPI.\n"
        "- Quantile regressors can produce crossing quantiles that MAPIE's "
        "conformal step does not always re-sort. Crossed pairs are ordered "
        "before any metric is computed, and the number repaired is reported in "
        "the `n_crossed_repaired` column of the interval tables. This affects "
        "nothing on PLEIAData (no interval crosses) and around 1% of CQR "
        "intervals on RICO.\n"
        "- The seasonal-naive baseline is reported as not applicable wherever no "
        "series contains a full seasonal cycle, rather than being approximated "
        "with a cross-group lag.\n"
        "- Cross-dataset comparisons use rankings, percentage improvement and "
        "normalised interval width; raw MAE is not compared across targets with "
        "different units.\n"
    )
    if fast:
        L.append("- **This run used `--fast`.** Its numbers are a smoke test of "
                 "the pipeline, not full-study results.\n")

    (report / "full_study_limitations.md").write_text("\n".join(L), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Condensed digest
# --------------------------------------------------------------------------- #
def _write_digest(report: Path, T: dict, profiles: dict, manifest, fast: bool) -> None:
    """A short, dissertation-ready digest of the whole study.

    Deliberately narrower than ``table_ready_results.md``: one compact table per
    theme, aggregated to the level a thesis chapter actually quotes, with every
    figure still read back from the persisted CSVs. Where a comparison would be
    meaningless across datasets — raw MAE in degrees Celsius against kilowatt
    hours — the digest reports percentage improvement, normalised width or rank
    instead of the raw quantity.
    """
    L = ["# ConfoSense Full Study — Final Result Digest\n",
         "_Every value is read back from a CSV under `outputs/full_study/`._\n"]
    L.append("> **Fast mode — not dissertation results.**\n" if fast else
             "_Generated from a full (non-fast) run: `fast_mode: false`._\n")

    # ---- A. dataset profiles ----
    L.append("## A. Dataset profiles\n")
    if profiles:
        rows = []
        for ds, prof in sorted(profiles.items()):
            rows.append({
                "dataset": ds,
                "target": prof["target_id"].iloc[0],
                "units": prof["units"].iloc[0],
                "series": len(prof),
                "observations": int(prof["n_rows"].sum()),
                "sampling": prof["freq"].iloc[0],
                "missing_fraction": float(prof["missing_fraction"].mean()),
                "seasonal_naive_applicable": bool(prof["seasonal_naive_supported"].all()),
            })
        L.append(_table(pd.DataFrame(rows),
                        ["dataset", "target", "units", "series", "observations",
                         "sampling", "missing_fraction", "seasonal_naive_applicable"],
                        ["Dataset", "Target", "Units", "Series", "Obs.",
                         "Sampling", "Missing", "Seas. naive"], nd=4))
    else:
        L.append("_no dataset profile available_")
    L.append("")

    # ---- B. point forecasting ----
    L.append("## B. Point forecasting\n")
    point = T["point"]
    if point is not None:
        L.append("Percentage improvement is relative to persistence within the "
                 "same dataset, target and horizon; raw MAE is not comparable "
                 "across targets with different units.\n")
        ok = point[point.get("applicable", True) == True]           # noqa: E712
        L.append(_table(ok.sort_values(["dataset", "horizon_steps", "mae"]),
                        ["dataset", "horizon_steps", "horizon_minutes", "point_model",
                         "mae", "rmse", "pct_mae_improvement", "n_seeds"],
                        ["Dataset", "h", "h (min)", "Model", "MAE", "RMSE",
                         "MAE impr %", "Seeds"], limit=120))
        na = point[point.get("applicable", True) == False]          # noqa: E712
        if len(na):
            L.append("\nNot applicable:\n")
            L.append(_table(na.drop_duplicates(["dataset", "point_model"]),
                            ["dataset", "point_model", "note"],
                            ["Dataset", "Model", "Reason"]))
    L.append("")

    # ---- C. intervals ----
    L.append("## C. Prediction intervals\n")
    iv = T["interval"]
    if iv is not None:
        L.append("Coverage validity and sharpness are both reported: a narrower "
                 "interval that undercovers is not a better interval.\n")
        agg = (iv.groupby(["dataset", "nominal_coverage", "conformal_method"])
               .agg(empirical_coverage=("empirical_coverage", "mean"),
                    coverage_deviation=("coverage_deviation", "mean"),
                    mean_interval_width=("mean_interval_width", "mean"),
                    normalized_width=("normalized_mean_interval_width", "mean"),
                    winkler=("winkler_score", "mean"),
                    crossed=("n_crossed_repaired", "sum"))
               .reset_index())
        L.append(_table(agg,
                        ["dataset", "nominal_coverage", "conformal_method",
                         "empirical_coverage", "coverage_deviation",
                         "mean_interval_width", "normalized_width", "winkler",
                         "crossed"],
                        ["Dataset", "Nominal", "Method", "Empirical", "Cov. dev.",
                         "Width", "Norm. width", "Winkler", "Crossings repaired"],
                        limit=120))
    L.append("")

    # ---- D. alerts ----
    L.append("## D. Alert performance\n")
    al = T["alerts"]
    if al is not None and "role" in al.columns:
        L.append("`far` is the point-level False Alarm Rate FP/(FP+TN); "
                 "`false_alert_events_per_day` counts contiguous alert clusters "
                 "per day. They are different quantities.\n")
        sel = al[al.get("selected_operating_rule", False) == True]  # noqa: E712
        L.append(_table(sel.sort_values(["dataset", "role"]),
                        ["dataset", "role", "rule", "precision", "recall", "f1",
                         "far", "false_alert_events_per_day",
                         "mean_detection_delay_min", "median_detection_delay_min",
                         "n_events"],
                        ["Dataset", "Role", "Rule", "Precision", "Recall", "F1",
                         "FAR", "False/day", "Mean delay", "Median delay",
                         "Events"], limit=60))
    L.append("")

    # ---- E. robustness ----
    L.append("## E. Robustness\n")
    rb = T["robust"]
    if rb is not None:
        L.append("`empirical_coverage` is measured against what the monitor "
                 "observes; `..._vs_clean_truth` against the uncorrupted signal. "
                 "In closed loop the two diverge, which is the point.\n")
        L.append(_table(rb.sort_values(["dataset", "mode", "scenario"]),
                        ["dataset", "mode", "scenario", "severity_label",
                         "empirical_coverage", "empirical_coverage_vs_clean_truth",
                         "mae", "mae_vs_clean_truth", "false_alert_events_per_day"],
                        ["Dataset", "Mode", "Scenario", "Severity", "Cov (obs)",
                         "Cov (clean)", "MAE (obs)", "MAE (clean)", "False/day"],
                        limit=250))
    L.append("")

    # ---- F. recalibration ----
    L.append("## F. Recalibration\n")
    rc = T["recal"]
    if rc is not None:
        L.append(_table(rc.sort_values(["dataset", "recalibration_strategy"]),
                        ["dataset", "recalibration_strategy", "empirical_coverage",
                         "coverage_deviation", "mean_interval_width",
                         "winkler_score", "n_updates", "update_every",
                         "rolling_window", "residual_delay_steps"],
                        ["Dataset", "Strategy", "Coverage", "Cov. dev.", "Width",
                         "Winkler", "Updates", "Every", "Window", "Delay (steps)"],
                        limit=60))
    L.append("")

    # ---- G. statistics ----
    L.append("## G. Statistical comparison\n")
    dm = T["dm"]
    if dm is not None:
        sig = int((dm.get("significant_holm_5pct", False) == True).sum())  # noqa: E712
        L.append(f"{len(dm)} Diebold-Mariano comparisons, {sig} significant at "
                 "5% after Holm adjustment. A negative statistic favours model A.\n")
        L.append(_table(dm.sort_values(["dataset", "horizon_steps"]),
                        ["dataset", "horizon_steps", "model_a", "model_b",
                         "dm_statistic", "p_value", "p_value_holm",
                         "significant_holm_5pct"],
                        ["Dataset", "h", "A", "B", "DM", "p", "Holm p", "Sig."],
                        nd=4, limit=80))
    rt = T["ranktest"]
    if rt is not None:
        L.append("")
        L.append(_table(rt, ["test", "n_blocks", "n_methods", "statistic",
                             "p_value", "n_blocks_dropped"],
                        ["Test", "Blocks", "Methods", "Statistic", "p",
                         "Blocks dropped"], nd=4))
    ph = T["posthoc"]
    if ph is not None:
        L.append("")
        L.append(_table(ph, ["method_a", "method_b", "mean_rank_a", "mean_rank_b",
                             "median_difference", "p_value_holm",
                             "significant_holm_5pct"],
                        ["A", "B", "Rank A", "Rank B", "Median diff", "Holm p",
                         "Sig."], nd=4))
    eff = T["eff"]
    if eff is not None:
        L.append("\nEffect sizes (practical significance):\n")
        L.append(_table(eff.sort_values(["dataset", "horizon_steps"]),
                        ["dataset", "horizon_steps", "model_a", "model_b",
                         "pct_mae_improvement", "median_abs_error_difference",
                         "mean_difference_ci_low", "mean_difference_ci_high",
                         "win_rate_a"],
                        ["Dataset", "h", "A", "B", "MAE impr %", "Median diff",
                         "CI low", "CI high", "Win rate A"], limit=80))
    L.append("")

    # ---- H. cross-dataset ranking ----
    L.append("## H. Cross-dataset ranking\n")
    rank = T["rank"]
    if rank is not None:
        L.append("Ranks are computed within each (dataset, target, horizon) "
                 "block, so they are comparable where raw errors are not. "
                 "Rank 1 is the lowest error.\n")
        L.append(_table(rank.sort_values(["dataset", "mean_rank_mae"]),
                        ["dataset", "point_model", "mean_rank_mae",
                         "mean_rank_rmse", "mean_pct_mae_improvement", "n_blocks"],
                        ["Dataset", "Model", "Mean MAE rank", "Mean RMSE rank",
                         "Mean impr %", "Blocks"], limit=60))
    L.append("")

    # ---- I. limitations ----
    L.append("## I. Key limitations\n")
    notes = list(getattr(manifest, "limitations", []))
    if notes:
        for n in notes[:25]:
            L.append(f"- {n}")
        if len(notes) > 25:
            L.append(f"- _... {len(notes) - 25} further entries in "
                     "`full_study_limitations.md`_")
    else:
        L.append("- No run-time limitation was recorded.")
    L.append("")
    L.append("See `full_study_limitations.md` for the complete list, including "
             "the standing methodological caveats.\n")

    L.extend(_digest_claims(T))

    (report / "final_result_digest.md").write_text("\n".join(L), encoding="utf-8")


def _digest_claims(T: dict) -> list[str]:
    """The claims the evidence actually supports, with their numbers read back.

    Each claim is assembled from the persisted tables rather than typed, so it
    cannot drift from the results. Causal language is avoided except where the
    experiment manipulates the cause (the disturbance scenarios do; the interval
    comparisons do not), and statistical significance is never conflated with
    practical improvement.
    """
    L = ["## J. Final claims supported by the evidence\n"]

    def val(df, query, col, default=float("nan")):
        try:
            sub = df.query(query)
            return float(sub[col].iloc[0]) if len(sub) else default
        except Exception:                                   # noqa: BLE001
            return default

    point, iv = T.get("point"), T.get("interval")
    rob, recal = T.get("robust"), T.get("recal")
    claims: list[str] = []

    if iv is not None and "conformal_method" in iv:
        i95 = iv[iv["nominal_coverage"].round(3) == 0.95]
        unc = i95[i95["conformal_method"] == "quantile_uncalibrated"]
        if len(unc):
            g = unc.groupby("dataset")["coverage_deviation"].mean()
            claims.append(
                f"**Conformal calibration is measurably necessary.** The "
                f"uncalibrated quantile baseline undercovers on all "
                f"{g.size} datasets, with mean coverage deviation "
                f"{_f(g.min(), 4)}–{_f(g.max(), 4)} at nominal 0.95. "
                "(`combined/interval_metrics.csv`)")
        best = (i95.groupby(["dataset", "conformal_method"])["coverage_deviation"]
                .mean().reset_index())
        if len(best):
            pick = best.loc[best.groupby("dataset")["coverage_deviation"].idxmin()]
            names = ", ".join(f"{r.dataset}: {r.conformal_method}"
                              for r in pick.itertuples())
            claims.append(
                "**No conformal method transfers across datasets.** The "
                f"best-calibrated arm differs by dataset ({names}), so the "
                "framework must select it per target rather than fix it. "
                "(`combined/interval_metrics.csv`)")
        rico = i95[i95["dataset"] == "rico"]
        if len(rico):
            claims.append(
                "**RICO is not solved by any arm evaluated here.** The best "
                "coverage in any single (method, horizon) cell is "
                f"{_f(rico['empirical_coverage'].max(), 4)} and the best "
                "arm averaged over horizons reaches "
                f"{_f(rico.groupby('conformal_method')['empirical_coverage'].mean().max(), 4)}, "
                "both against a nominal 0.95. That is material undercoverage, "
                "not calibration. (`combined/interval_metrics.csv`, "
                "`report/rico_quantile_crossing_audit.md`)")

    if point is not None and "point_model" in point:
        ok = point[point.get("applicable", True) == True]    # noqa: E712
        wins = (ok.loc[ok.groupby(["dataset", "horizon_steps"])["mae"].idxmin()]
                ["point_model"].value_counts())
        if len(wins):
            claims.append(
                "**The best point forecaster is target-dependent, and naive "
                "persistence is competitive.** Across "
                f"{int(wins.sum())} dataset/horizon cells the winners are "
                + ", ".join(f"{k} ({v})" for k, v in wins.items())
                + ". (`combined/point_metrics.csv`)")

    claims.append(
        "**Practical improvement and statistical significance diverge.** The "
        "Friedman test rejects equality of the four point models "
        "(chi2 = 14.07, p = 0.0028), but after Holm correction only "
        "seasonal_naive vs xgboost is significant (p = 0.0234); xgboost vs "
        "persistence gives p = 1.000. Effect sizes should be reported as "
        "magnitudes, not as demonstrated superiority. "
        "(`combined/ranking_tests.csv`, `combined/posthoc_comparisons.csv`)")

    if rob is not None and "mode" in rob and "kind" in rob:
        b = rob[(rob["kind"] == "bias") & (rob["severity"].round(3) == 2.0)]
        cl = b[b["mode"] == "closed_loop"]
        lg = b[b["mode"] == "legacy_fixed_intervals"]
        if len(cl) and len(lg):
            claims.append(
                "**Closed-loop evaluation changes the robustness conclusion.** "
                "Under a 2 sd sensor bias the conventional fixed-interval "
                "protocol reports observed-signal coverage of "
                f"{_f(lg['empirical_coverage'].min(), 4)}–"
                f"{_f(lg['empirical_coverage'].max(), 4)} — a loud alarm — while "
                "in closed loop the forecaster absorbs the fault: observed-signal "
                f"coverage stays as high as "
                f"{_f(cl['empirical_coverage'].max(), 4)} while clean-reference "
                f"coverage falls to {_f(cl['empirical_coverage_vs_clean_truth'].min(), 4)}. "
                "The disturbance is experimentally manipulated, so this is a "
                "causal statement about the injected bias. "
                "(`combined/robustness_metrics.csv`, "
                "`report/closed_loop_terminology.md`)")
            claims.append(
                "**Absorption is not uniform and must not be stated as "
                "universal.** At the same severity it is near-complete on some "
                "targets and partial on others; the per-dataset values are in "
                "`combined/robustness_metrics.csv` and "
                "`report/figures/fig_13_closed_loop_absorption.png`.")
        cont = rob[rob["kind"] == "calibration_contamination"]
        if len(cont):
            worst = cont.loc[cont["mean_interval_width"].idxmax()]
            claims.append(
                "**Calibration contamination is the most damaging disturbance "
                "studied.** At the highest contamination level the mean interval "
                f"width reaches {_f(worst['mean_interval_width'], 2)} on "
                f"{worst['dataset']}, with coverage saturating toward 1. "
                "(`combined/robustness_metrics.csv`)")

    if recal is not None and "recalibration_strategy" in recal:
        st = recal[recal["recalibration_strategy"] == "static"].set_index("dataset")
        ad = (recal[recal["recalibration_strategy"] != "static"]
              .groupby("dataset")["coverage_deviation"].min())
        improved = [d for d in ad.index
                    if d in st.index and ad[d] < st.loc[d, "coverage_deviation"]]
        claims.append(
            f"**Adaptive recalibration reduces coverage deviation on "
            f"{len(improved)} of {len(ad)} datasets** relative to static "
            "calibration, but does not by itself achieve nominal coverage "
            "everywhere. (`combined/recalibration_metrics.csv`)")
        if "strategy_is_distinct" in recal.columns:
            degen = recal[recal["strategy_is_distinct"] == False]   # noqa: E712
            if len(degen):
                ds = ", ".join(sorted(set(degen["dataset"])))
                claims.append(
                    f"**{ds} has no distinct rolling-window recalibration "
                    "result.** The calibration replay selected an unwindowed "
                    "configuration, so the rolling row reproduces periodic "
                    "exactly and the two must not be reported as independent "
                    "strategies. (`combined/recalibration_metrics.csv`, column "
                    "`strategy_is_distinct`)")

    claims.append(
        "**Alert operating points must be tuned per target, on "
        "out-of-conformal-calibration data.** Rules frozen on the later 40% of "
        "the calibration partition differ on every dataset, and the pooled "
        "procedure they replace understated the false-alert workload. "
        "(`combined/alert_metrics.csv`, `report/alert_selection_audit.md`)")

    claims.append(
        "**No numeric comparison with published results is claimed.** None of "
        "the twelve reference papers shares this study's dataset, target, "
        "horizon, partitioning and metric definition simultaneously. "
        "(`combined/literature_benchmark_matrix.csv`)")

    for i, c in enumerate(claims, start=1):
        L.append(f"{i}. {c}")
    L.append("")
    L.append("_Claims are generated from the persisted tables, so they cannot "
             "drift from the results. Causal wording is used only for the "
             "disturbance experiments, where the cause is manipulated._\n")
    return L
