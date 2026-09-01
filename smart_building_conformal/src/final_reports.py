"""Dissertation report suite, generated programmatically from corrected CSVs.

Every number in every report is read from a CSV produced by the corrected run
(``final_cis.csv``, ``ablation.csv``, ``selection.csv``); nothing is typed by
hand, extrapolated, or copied from the old study. The mandatory honesty clause is
embedded in each results-bearing report. Reports are (re)written only after the
corrected study, its CIs and figures exist.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

HONESTY = (
    "> The original test outputs were inspected and used to diagnose the "
    "pipeline, so they are no longer a pristine holdout. Corrected performance is "
    "therefore estimated through fully nested post-audit evaluation and is **not** "
    "presented as validation on an untouched holdout."
)


def _fmt(row) -> str:
    return (f"{row['estimate']:.3f} "
            f"(95% CI {row['ci_low']:.3f}–{row['ci_high']:.3f}; "
            f"n_units={int(row['n_units'])}, boot={int(row['n_boot'])})")


def _cis(out_root: Path) -> pd.DataFrame:
    p = out_root / "metrics" / "final_cis.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _concat_run(run_root: Path, datasets, name) -> pd.DataFrame:
    frames = []
    for ds in datasets:
        p = run_root / ds / name
        if p.exists():
            df = pd.read_csv(p); df["dataset"] = ds; frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _results_md(cis: pd.DataFrame, ablation: pd.DataFrame,
                selection: pd.DataFrame) -> str:
    lines = ["# Final dissertation results (corrected study)", "", HONESTY, ""]
    lines += ["Terminology: *synthetic-event recall* and *background alert "
              "episodes per monitored asset-day*; coverage is *empirical coverage "
              "under the evaluated time-series conditions*; BDG2 is *within-"
              "building temporal generalisation* only.", ""]
    lines.append("## Headline estimates with 95% CIs")
    if cis.empty:
        lines.append("_No corrected CIs are available yet — the run or its CI "
                     "stage has not completed. No number is reported._")
    else:
        for ds, sub in cis.groupby("dataset"):
            lines.append(f"### {ds}")
            for _, r in sub.iterrows():
                lines.append(f"- **{r['metric']}**: {_fmt(r)} "
                             f"[source: metrics/final_cis.csv]")
            lines.append("")
    # selection / abstention transparency
    if not selection.empty and "decision" in selection:
        vc = selection["decision"].value_counts().to_dict()
        lines += ["## Operational selection outcomes",
                  f"Across outer folds: {vc}. `no_feasible_configuration` is an "
                  "honest abstention, not a failure — it means no candidate met "
                  "the frozen recall/workload policy on inner data.", ""]
    if not ablation.empty and "macro_recall" in ablation:
        lines.append("## Ablation (same outer folds and event catalogues)")
        appl = ablation[ablation.get("applicable", True) == True]      # noqa: E712
        g = (appl.groupby("ablation")
             .agg(macro_recall=("macro_recall", "mean"),
                  background=("background_episodes_per_asset_day", "mean")))
        for level in ["baseline", "conformal_only", "temporal", "full"]:
            if level in g.index:
                lines.append(f"- **{level}**: recall {g.loc[level,'macro_recall']:.3f}, "
                             f"background {g.loc[level,'background']:.3f}/asset-day")
        lines.append("")
    # Auto-detected validity flags, so the report is self-critical rather than
    # quietly presenting a low-power or degenerate estimate as a clean result.
    if not cis.empty:
        flags = []
        for _, r in cis.iterrows():
            if r["ci_high"] - r["ci_low"] < 1e-9:
                flags.append(f"- {r['dataset']} {r['metric']}: zero-width CI over "
                             f"only {int(r['n_units'])} unit(s) — a degenerate, "
                             "low-power estimate, not a precise one.")
            if r["metric"] == "empirical_coverage" and r["ci_high"] < 0.95:
                flags.append(f"- {r['dataset']}: interval coverage upper CI "
                             f"{r['ci_high']:.3f} < 0.95 nominal — undercoverage "
                             "under the evaluated conditions.")
            if r["metric"] == "empirical_coverage" and r["ci_low"] > 0.995:
                flags.append(f"- {r['dataset']}: coverage ~1.0 — intervals so wide "
                             "they rarely alert (see near-zero recall/workload).")
        if flags:
            lines += ["## Validity flags (auto-detected)", *flags, ""]
    lines += ["## Do-not-claim", "- No universal superiority; comparisons are "
              "*among the evaluated methods*.", "- No real-world fault-detection "
              "precision; the datasets carry no comprehensive fault labels.",
              "- No unseen-building generalisation (within-building analysis only).",
              "- SDG 11 is described only as conceptual alignment, not measured "
              "impact.", ""]
    return "\n".join(lines)


def build(run_root: str | Path, out_root: str | Path, datasets: list[str]) -> list[str]:
    """Write the report suite from corrected CSVs; return the files written."""
    run_root = Path(run_root); out_root = Path(out_root)
    report_dir = out_root / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    cis = _cis(out_root)
    ablation = _concat_run(run_root, datasets, "ablation.csv")
    selection = _concat_run(run_root, datasets, "selection.csv")

    written = []
    (report_dir / "FINAL_DISSERTATION_RESULTS.md").write_text(
        _results_md(cis, ablation, selection), encoding="utf-8")
    written.append("FINAL_DISSERTATION_RESULTS.md")

    # Slide-ready values, strictly from the CIs table.
    slide = ["# Slide-ready values (corrected)", "", HONESTY, ""]
    if cis.empty:
        slide.append("_Pending the corrected run's CIs; no value is shown._")
    else:
        for _, r in cis.iterrows():
            slide.append(f"- {r['dataset']} — {r['metric']}: {_fmt(r)}")
    (report_dir / "SLIDE_READY_VALUES.md").write_text("\n".join(slide),
                                                      encoding="utf-8")
    written.append("SLIDE_READY_VALUES.md")

    # RQ/RO achievement, read from the CIs and ablation.
    rq = ["# Research questions and objectives — achievement", "", HONESTY, ""]
    def _get(ds, metric):
        m = cis[(cis["dataset"] == ds) & (cis["metric"] == metric)]
        return m.iloc[0] if len(m) else None
    rq.append("- **RQ (interval validity):** empirical coverage is estimated with "
              "group-appropriate CIs per dataset (see final_cis.csv). Where the "
              "upper CI is below the nominal level the finding is **undercoverage**, "
              "reported as such — *partially achieved*, not asserted as guaranteed.")
    rq.append("- **RQ (temporal alerting value):** the ablation isolates k-of-m "
              "aggregation on the same folds/catalogues; recall and background "
              "workload are reported per level. Conclusions are drawn only from the "
              "ablation table, *among the evaluated methods*.")
    rq.append("- **RO (leakage-controlled, reproducible pipeline):** *achieved* — "
              "nested selection on inner data only, horizon embargo, group-safe "
              "state, exposure-based events, and fail-closed integrity gates, all "
              "under a hashed frozen protocol; PUBLICATION_READY.json records the "
              "lineage.")
    rq.append("- **RO (fault-absorption / robustness):** *not evaluated in the "
              "nested engine* — the closed-loop robustness stage is not part of "
              "this end-to-end run; stated as a limitation, not a result.")
    (report_dir / "RQ_RO_ACHIEVEMENT.md").write_text("\n".join(rq), encoding="utf-8")
    written.append("RQ_RO_ACHIEVEMENT.md")

    # Claims register.
    reg = ["# Final claims register", "", HONESTY, "",
           "| claim | status | evidence | required caveat |",
           "|---|---|---|---|",
           "| Conformal calibration lowers background alert workload at comparable "
           "recall | retained (among evaluated methods) | ablation baseline vs "
           "conformal_only | not a real-FP-rate; synthetic events |",
           "| Updated recentred EnbPI is now causal & group-safe | retained | "
           "test_enbpi_causal; wired in engine | interval-quality claim only |",
           "| Distribution-free coverage guarantee | withdrawn | observed "
           "undercoverage on several datasets | report empirical coverage only |",
           "| Real-world fault-detection precision | withdrawn | no fault labels | "
           "use background-workload framing |",
           "| Unseen-building portability (BDG2) | withdrawn | within-building "
           "design | within-building temporal generalisation only |"]
    (report_dir / "FINAL_CLAIMS_REGISTER.md").write_text("\n".join(reg),
                                                         encoding="utf-8")
    written.append("FINAL_CLAIMS_REGISTER.md")

    # Limitations and validity.
    lim = ["# Limitations and validity", "", HONESTY, "",
           "- No untouched holdout remains; performance is nested post-audit "
           "estimation.", "- Several datasets show interval **undercoverage** "
           "under the evaluated conditions (see final_cis.csv validity flags).",
           "- RICO high-coverage operating levels yield very wide intervals that "
           "rarely alert, so its recall/workload CIs are degenerate and low-power "
           "(only a few runs).", "- Closed-loop robustness, calibration "
           "contamination and recalibration-recovery are not part of this nested "
           "run; the corresponding figures are therefore not produced.",
           "- Point-forecast skill is used for selection but not exported per "
           "outer fold, so a point-skill figure is not built here.",
           "- Synthetic-event incidence is a modelling choice; RICO uses a "
           "viability floor (realised > requested), recorded in event_allocation.csv."]
    (report_dir / "LIMITATIONS_AND_VALIDITY.md").write_text("\n".join(lim),
                                                            encoding="utf-8")
    written.append("LIMITATIONS_AND_VALIDITY.md")

    # Figures index (mirrors figure_index.csv if present).
    fidx = out_root / "figures" / "figure_index.csv"
    fig_lines = ["# Final figures index", ""]
    if fidx.exists():
        fi = pd.read_csv(fidx)
        fig_lines += ["| figure | source CSV | source sha256 |", "|---|---|---|"]
        for _, r in fi.iterrows():
            fig_lines.append(
                f"| {r['figure']} | {r['source_csv']} | "
                f"{str(r.get('source_sha256',''))[:16]}… |")
    else:
        fig_lines.append("_Figures not generated yet._")
    (report_dir / "FINAL_FIGURES_INDEX.md").write_text("\n".join(fig_lines),
                                                       encoding="utf-8")
    written.append("FINAL_FIGURES_INDEX.md")

    # Reproducibility pointer.
    (report_dir / "REPRODUCIBILITY.md").write_text(
        "# Reproducibility\n\nProtocol hash and executable config are pinned in "
        "`protocol/config_hash.txt`. Regenerate with `python -m src.corrected_study` "
        "then `python -m src.validate_final_study --mode publication`. All figures "
        "and reports are generated from the run CSVs; see `metrics/final_cis.csv` "
        "and `figures/figure_index.csv` for source hashes.\n", encoding="utf-8")
    written.append("REPRODUCIBILITY.md")
    return written
