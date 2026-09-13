"""Render saved, validated pilot measurements into the repository Markdown report."""
import argparse
import json
from pathlib import Path

import pandas as pd


ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--report", required=True)
a = ap.parse_args()
base, report = Path(a.base), Path(a.report)
run, validation = base / "runs/pilot_v1_20260913", base / "validation"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in rows)
    return "\n".join(lines)


v = read(validation / "output_validation.json")
assert v["pilot_outputs_valid"] and v["point_cells"] == 9 and v["interval_cells"] == 18
completion = read(validation / "pilot_completion_resume.log.json")
reuse = read(validation / "resume_integrity.json")
assert completion["exit_status"] == 0 and reuse["passed"] and reuse["refits"] == 0
p = pd.read_csv(run / "point_summary.csv")
i = pd.read_csv(run / "interval_quality.csv")
cost = pd.read_csv(base / "tables/measured_cost_and_expansion_scenario.csv")
bdg = read(validation / "bdg2_preparation_memory.json")
names = {"persistence": "Persistence", "xgboost": "XGBoost", "attention_lstm": "Attention-LSTM"}
sections = ["## Completion evidence and measured results", """**Completed and output-validated.** The completion run returned **exit status 0**. All **9/9 point-summary cells** and **18/18 interval-quality cells** passed validation, with **zero missing, duplicate or failed cells**. All eighteen interval cells have sufficient finite calibration support. The validator recomputed point errors, coverage, MPIW, Winkler scores, radii, ranks and bounds from saved predictions/calibration errors, checked identical support across models and levels, matched membership to the frozen design, and verified all checkpoint artifact hashes.

The original five completed units were reused with all 35 files unchanged. A subsequent complete-run resume reused **all nine units with zero refits**, preserving all 63 unit files byte-for-byte. Its exit status and the output validator's exit status were both **0**. The interrupted original launch has **unknown exit status**, not a claimed success. The bounded pilot is complete; **global study readiness and publication readiness remain false**."""]
sections += ["### Point metrics", table(["Horizon (min)", "Model", "MAE (°C)", "RMSE (°C)"],
    [[int(r.horizon)*10, names[r.model], f"{r.mae:.4f}", f"{r.rmse:.4f}"] for r in p.itertuples()])]
sections += ["### Interval quality", "Coverage percentages below are empirical. Every cell evaluates 9,907 rows; horizon-specific calibration counts are given in the design table. MPIW and Winkler scores are in °C.",
    table(["Horizon (min)", "Model", "Nominal", "Coverage", "MPIW", "Winkler"],
    [[int(r.horizon)*10, names[r.model], f"{100*r.nominal_level:g}%", f"{100*r.coverage:.2f}%", f"{r.mpiw:.4f}", f"{r.winkler:.4f}"] for r in i.itertuples()])]
sections += ["### Model computation", "Measured time is in seconds; RSS is in MiB (2²⁰ bytes). These are the delivered units' measurements, spanning the original and resumed processes. Persistence's tiny final-fit value measures constructor overhead. Its point-summary tuning time is zero; the raw resource CSV retains the timing of the empty tuning branch.",
    table(["Horizon (min)", "Model", "Tuning s", "Final fit s", "Calibration s", "Inference s", "Rows/s", "Baseline RSS MiB", "Peak RSS MiB"],
    [[int(r.horizon)*10, names[r.model], f"{r.tuning_seconds:.3f}", f"{r.final_fit_seconds:.3f}", f"{r.calibration_seconds:.4f}", f"{r.inference_seconds:.4f}", f"{r.inference_rows_per_second:,.0f}", f"{r.baseline_rss_bytes/2**20:.1f}", f"{r.peak_rss_bytes/2**20:.1f}"] for r in p.itertuples()])]
sections += [f"The completion invocation ran from **{completion['started_utc']}** to **{completion['ended_utc']}**, taking **{completion['seconds']:.2f} seconds**. It reused five units and computed four; this is not a nine-unit fresh-run runtime. The delivered units' four measured phases sum to **{cost.model_compute_seconds.sum():.2f} seconds**. Data preparation, checkpoint I/O, validation and abandoned partial tuning are outside that phase sum."]
selections = []
for row in p.itertuples():
    if row.model == "persistence":
        continue
    payload = read(run / "units" / f"h{row.horizon}_f0_s42_{row.model}" / "payload.json")
    params = payload["parameters"]
    choice = (f"depth={params['max_depth']}; trees={params['n_estimators']}"
              if row.model == "xgboost" else f"learning rate={params['learning_rate']}; hidden size={params['hidden_size']}")
    selections.append([int(row.horizon)*10, names[row.model], payload["selected_candidate"],
                       choice, payload["final_epochs"] or "N/A"])
sections += ["Selected candidates are shown below; complete parameters remain in the frozen configuration and each unit's payload. Candidate choice and epoch counts came only from the frozen inner folds.",
             table(["Horizon (min)", "Model", "Candidate ID", "Parameters", "Final epochs"], selections)]
sections += ["### Separate BDG2 preparation measurement", f"**No BDG2 models were fitted** (`models_fitted=0`). The full retained ten-building cohort was processed, and every eligible sequence was traversed in batches of 256 at every configured horizon. The separate preparation command returned exit status **{read(validation / 'bdg2_preparation.log.json')['exit_status']}**. Its aggregate resource measurement was **{bdg['total_resources']['seconds']:.2f} seconds**, with sampled peak RSS **{bdg['total_resources']['peak_rss_bytes']/2**30:.3f} GiB** and minimum available system RAM **{bdg['total_resources']['min_available_ram_bytes']/2**30:.3f} GiB**. The aggregate includes the adapter and horizon stages; do not add it to those components.",
    table(["Horizon (hours)", "Eligible rows", "Channels", "Sequence length", "Lazy stored MiB", "Equivalent full tensor MiB", "Stage peak RSS MiB", "Stage seconds"],
    [[r["horizon"], r["rows"], r["n_channels"], r["sequence_length"], f"{r['lazy_stored_bytes']/2**20:.1f}", f"{r['equivalent_full_tensor_bytes']/2**20:.1f}", f"{r['resources']['peak_rss_bytes']/2**20:.1f}", f"{r['resources']['seconds']:.2f}"] for r in bdg["horizons"]])]
sections += ["The equivalent full-tensor figure is an arithmetic size estimate, not an allocated tensor or measured process peak. Lazy storage is only one component of memory: flat features, preprocessing copies, Python/library allocations and batching also consume RAM. This measurement establishes preparation feasibility for the retained cohort; it does not measure BDG2 tuning, fitting, calibration or inference cost."]
sections += ["### Expansion scenario", table(["Model", "Measured three-horizon phases (s)", "15 equal-cost repetitions (s)", "15 equal-cost repetitions (min)"],
    [[names[r.model], f"{r.model_compute_seconds:.2f}", f"{r.same_cost_15_repetitions_seconds:.2f}", f"{r.same_cost_15_repetitions_seconds/60:.2f}"] for r in cost.itertuples()]),
    f"Repeating this PLEIA three-horizon workload at identical cost for **three folds × five seeds** gives a mechanical scenario of **{cost.same_cost_15_repetitions_seconds.sum()/60:.2f} minutes** of measured model phases. This is a total 15-repetition scenario, not fifteen additional runs, not a confidence interval and not an ETA. Other folds have different fitting/calibration sizes and selected epoch counts; memory pressure, I/O, system load and interruptions also affect cost. **PLEIA energy, RICO and BDG2 model-fitting costs remain unmeasured.** No four-task runtime estimate or GPU speed-up is inferred. The full comparison's 195 paired units / 585 point cells / 1,170 interval-quality cells remains separate work; this pilot does not authorise that launch."]
sections += ["## Interpretation and remaining work", "Interpretation is completed after reading the saved tables and inspecting the comparison figure."]
text = report.read_text(encoding="utf-8")
interpretation_marker = "## Interpretation and remaining work"
if interpretation_marker in text:
    interpretation = text.split(interpretation_marker, 1)[1].strip()
    if interpretation and "Interpretation is completed after reading" not in interpretation:
        sections[-1] = interpretation
marker = "## Completion evidence and remaining work"
if marker not in text:
    marker = "## Completion evidence and measured results"
text = text.split(marker)[0].rstrip() + "\n\n" + "\n\n".join(sections) + "\n"
report.write_text(text, encoding="utf-8")
print(f"Wrote validated numerical results to {report}")
