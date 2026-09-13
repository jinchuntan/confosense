"""Evidence-status reports: never promote stale CSVs into current findings."""
from pathlib import Path
import pandas as pd
from .evidence_status import DATASETS, run_status

DS = list(DATASETS)
HONESTY = (
    "> Previously inspected test data remain previously inspected. A corrected "
    "rerun or additional seeds do not create an untouched holdout. Historical "
    "results require recomputation after the integration repairs; passing "
    "software tests does not establish scientific validity.")


def build(out_root, core_run, ext_run, datasets=DS):
    out_root = Path(out_root)
    report, metrics = out_root / "report", out_root / "metrics"
    report.mkdir(parents=True, exist_ok=True)
    core_state, _ = run_status(core_run)
    ext_state, _ = run_status(ext_run, "extension")
    status = [HONESTY, "", f"Core source: `{core_run}` — **{core_state}**.",
              f"Extension source: `{ext_run}` — **{ext_state}**.", "",
              "Current numerical dissertation findings are not established by this report. "
              "See repository-root `INTEGRATION_REPAIR_REPORT.md` for repairs, "
              "unresolved design decisions and the required rerun.", ""]
    written = []

    def write(name, title, lines):
        (report / name).write_text("\n".join([f"# {title}", "", *status, *lines]) + "\n",
                                  encoding="utf-8")
        written.append(name)

    ledger_path = metrics / "OUTER_UNIT_LEDGER.csv"
    accounting = ["Historical accounting only; these are dispositions of the archived run, "
                  "not feasibility findings for repaired code."]
    if ledger_path.exists():
        ledger = pd.read_csv(ledger_path)
        for ds, sub in ledger.groupby("dataset"):
            if ds in datasets:
                feasible = sub.operational_feasible.astype(str).str.lower().eq("true").sum()
                accounting.append(f"- {ds}: {feasible}/{len(sub)} archived units feasible; "
                                  f"{len(sub)-feasible} `no_feasible_configuration` outcomes. "
                                  "Source: `metrics/OUTER_UNIT_LEDGER.csv`.")
    else:
        accounting.append("Historical ledger missing; no counts reported.")
    write("FINAL_DISSERTATION_RESULTS.md", "Dissertation evidence status", accounting + ["",
        "No corrected CIs for the repaired execution are available. `final_cis.csv` is "
        "superseded statistically. `final_cis_corrected.csv` corrects historical inference "
        "but still describes the pre-repair computation. Neither supplies current findings.",
        "BDG2 supports within-building temporal evaluation only. Equal-recall workload "
        "improvement, real-fault precision and unseen-building portability are not established."])
    write("ROBUSTNESS_RESULTS.md", "Robustness evidence status", [
        "A missing full extension supplies no fault, contamination or recovery results. "
        "Smoke cells verify execution only. Closed-loop fault absorption is a hypothesis "
        "to test, not an achievement established here.",
        "A repaired full extension must verify every dataset/fold/seed/cell, retained "
        "prediction bounds, clean/zero identity, and group-specific recovery accounting."])
    timing_lines = []
    if ext_state != "missing":
        label = "SMOKE ONLY" if ext_state == "smoke" else "UNVALIDATED RUN TIMING"
        for ds in datasets:
            p = Path(ext_run) / ds / "unit_timing.csv"
            if p.exists():
                frame = pd.read_csv(p)
                timing_lines.append(f"- {label}; {ds}; n={len(frame)}: interval fit mean "
                    f"{frame.unit_fit_seconds.mean():.1f}s. Source: `{p}`.")
    write("COMPUTATIONAL_EFFICIENCY.md", "Computational evidence status", timing_lines + [
        "No validated Attention-LSTM/XGBoost resource comparison is available. "
        "Do not extrapolate full-run cost from smoke timings. The next comparison "
        "must measure tuning, refitting and inference separately, plus process peak "
        "memory, on matched support. PyTorch in the existing environment is CPU-only."])
    write("DISSERTATION_CHAPTER_4_RESULTS.md", "Chapter 4 preparation", [
        "Pending repaired evidence: data/support inventory; Attention-LSTM, XGBoost and "
        "persistence across declared horizons; model-specific 90%/95% intervals; "
        "feasibility and abstentions; paired ablations; robustness; measured resources."])
    write("DISSERTATION_CHAPTER_5_DISCUSSION.md", "Chapter 5 preparation", [
        "Discuss findings after repaired runs and inference. Preserve limitations from "
        "previous test inspection, synthetic fault generation, dependent seeds and small "
        "independent group counts. A paired difference in recall is not an equal-recall "
        "comparison. RICO runs used for fitting cannot be called untouched tests."])
    write("SLIDE_READY_VALUES.md", "Slide evidence status", [
        "No current performance values are approved by this generator for slides. "
        "Use the integration audit only as software-repair evidence. Rebuild performance "
        "tables and figures after the required experiments and statistical validation."])
    write("RQ_RO_ACHIEVEMENT.md", "Research question and objective status", [
        "- Point forecasting: multi-horizon Attention-LSTM/XGBoost evidence missing.",
        "- Interval quality: comparable model-specific 90%/95% evidence missing.",
        "- Alerting: historical estimates invalidated for current claims; rerun required.",
        "- Leakage control: repaired paths tested; scientific design reconciliation pending.",
        "- Robustness/recovery: completed full extension evidence missing."])
    write("CONTRIBUTIONS_LIMITATIONS_FUTURE_WORK.md", "Contributions under evaluation", [
        "Candidate contributions are the auditable interval-alert pipeline and explicit "
        "feasibility accounting. Their empirical benefit remains to be evaluated after "
        "repair. LSTM comparisons, matched-budget alerting, full robustness, memory "
        "measurement and wider independent evaluation are outstanding. No claim is made "
        "that the remaining RICO runs are untouched."])
    write("FINAL_TABLES_INDEX.md", "Historical tables inventory", [
        "All listed tables are retained historical artifacts unless a later source-linked "
        "scientific validation explicitly replaces their evidence status.",
        *[f"- `metrics/{p.name}`" for p in sorted(metrics.glob("*.csv"))]])
    write("FINAL_FIGURES_INDEX.md", "Historical figures inventory", [
        "Existing figures are preserved, not current dissertation findings. The v1 "
        "coverage figure uses superseded `final_cis.csv`; rebuild it from validated "
        "rerun inference. An image checksum alone does not validate its scientific source."])
    return written
