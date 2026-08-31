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

    # Reproducibility pointer.
    (report_dir / "REPRODUCIBILITY.md").write_text(
        "# Reproducibility\n\nProtocol hash and executable config are pinned in "
        "`protocol/config_hash.txt`. Regenerate with `python -m src.corrected_study` "
        "then `python -m src.validate_final_study --mode publication`. All figures "
        "and reports are generated from the run CSVs; see `metrics/final_cis.csv` "
        "and `figures/figure_index.csv` for source hashes.\n", encoding="utf-8")
    written.append("REPRODUCIBILITY.md")
    return written
