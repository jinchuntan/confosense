"""Create the compact scientific report, evidence index and completion record."""
from __future__ import annotations

import json
import numpy as np
import pandas as pd

from common import *


def markdown(frame, columns):
    data = frame[columns]
    def value(item):
        if pd.isna(item): return "unavailable"
        if isinstance(item, (float, np.floating)): return f"{item:.5g}"
        return str(item).replace("|", "\\|")
    return "\n".join(["| " + " | ".join(data.columns) + " |",
                       "| " + " | ".join(["---"] * len(data.columns)) + " |"] +
                      ["| " + " | ".join(value(item) for item in row) + " |"
                       for row in data.itertuples(index=False, name=None)])


def main():
    aggregate = read(ANALYSIS / "validation.json")
    independent = read(ANALYSIS / "independent_validation.json")
    packages = read(REVIEW / "RAW_PACKAGE_VALIDATION.json")
    if not aggregate["passed"] or not independent["passed"] or not packages["passed"]:
        raise ValueError("required aggregate/package evidence is incomplete")
    comparison = pd.read_csv(ANALYSIS / "five_seed_control_rule_channel.csv")
    interval = pd.read_csv(ANALYSIS / "five_seed_interval_diagnostics.csv")
    costs = pd.read_csv(ANALYSIS / "worker_cost_summary.csv")
    operations = pd.read_csv(ANALYSIS / "operation_reconciliation.csv")
    combined = comparison[comparison.channel == "combined"].sort_values(["rule_id", "control_id"])
    table_columns = ["control_id", "rule_id", "conditional_context_detection", "lower", "upper", "status_inference",
                     "seed_sd_detection", "mean_restricted_ttd_minutes", "mean_misses",
                     "mean_background_episodes_per_asset_day", "mean_fraction_time_in_alert"]
    clean = interval[(interval.scope == "fullstream_clean") & (interval.target == "clean_counterfactual")]
    clean_lookup = {row.control_id: row for row in clean.itertuples()}
    run_hours = float(costs.loc[costs.action == "run", "total_wall_seconds"].sum() / 3600)
    validation_hours = float(costs.loc[costs.action == "validate", "total_wall_seconds"].sum() / 3600)
    total_hours = float(costs.total_wall_seconds.sum() / 3600)
    peak_rss = int(costs.maximum_peak_working_set_bytes.max())
    minimum_disk = int(costs.minimum_disk_free_bytes.min())
    supported = independent["supported_bounds"]; unavailable = independent["unavailable_bounds"]
    report = ["# PLEIA-temperature conditional-context five-seed report", "",
        "The authorized outer-fold-2/horizon-1 batch completed model seeds 43--46 and reused accepted seed 42 without refitting or replaying it. All units retain 68 original contexts, 2,856 fixed fault slots, four 95% controls, five rules, three channels, and fault-slot replicate seeds 42/43. No tuning, model selection, feature changes, extra datasets, or result-driven protocol changes occurred.", "",
        "## Combined-channel detection and workload", "",
        "Point estimates average model seeds within each original context/stratum and then weight the 21 strata equally. Bounds use 2,000 paired chronological seven-context block draws with RNG seed 20240601. Workload, delay, misses and seed dispersion are descriptive; unsupported or degenerate population intervals remain unavailable.", "",
        markdown(combined, table_columns), "", "## Interval behavior", "",
        f"Across five seeds, full-clean rolling-CQR coverage is {clean_lookup['cqr_rolling'].mean_coverage:.4f} with mean width {clean_lookup['cqr_rolling'].mean_mpiw:.4f} °C. Persistence coverage is {clean_lookup['persistence_static'].mean_coverage:.4f} with mean width {clean_lookup['persistence_static'].mean_mpiw:.4f} °C. These results retain rather than tune away the adverse undercoverage and the rule-dependent detection/workload tradeoffs.", "",
        f"Original-context inference was supported for {supported} of 60 control/rule/channel cells; {unavailable} cells remain explicitly unavailable under the prespecified valid-draw and degeneracy gates.", "",
        "## Validation and computation", "",
        f"All four new seeds passed full explicit-path A-and-B-and-C validation, completed zero-fit resume, owner/native-seed verification, operation-budget reconciliation and artifact-integrity checks. Independent aggregation reproduced all {independent['cells']} endpoints and all saved draws; maximum point difference was {independent['maximum_absolute_point_difference']:.3g} and maximum bound difference was {independent['maximum_absolute_bound_difference']:.3g}.", "",
        f"The four new units used {run_hours:.3f} sequential run wall-hours and {validation_hours:.3f} validation wall-hours ({total_hours:.3f} hours across recorded freeze/readiness/run/validation/resume/verification phases). Maximum measured process-family working set was {peak_rss / 2**20:.1f} MiB; minimum free disk was {minimum_disk / 2**30:.2f} GiB. Raw evidence was packaged into {packages['parts']} verified parts totaling {packages['total_part_bytes'] / 2**30:.3f} GiB.", "",
        "Actual new operations were four CQR wrapper fits containing twelve native quantile-estimator fits, eight recorded nested conformalization calls representing four logical conformalizations, and four persistence-radius computations. Seed-42 refits and additional model-family fits were zero.", "",
        "## Interpretation limits", "",
        "The five model seeds are robustness repetitions within the same historical conditional fault challenge; they are not five buildings or 340 independent contexts. The 68 original contexts remain the observational units. This endpoint does not estimate natural fault prevalence, precision, F1, deployment feasibility, or complete the matched-forecasting, interval-method, or seasonal matrices. Full-study readiness remains false.", ""]
    atomic(REVIEW / "PLEIA_TEMPERATURE_CONTEXT005_FIVE_SEED_REPORT.md", "\n".join(report))
    completion = {"passed": True, "utc": now(), "branch": BRANCH, "source_hash": source_digest(),
                  "completed_new_seeds": list(SEEDS), "accepted_all_seeds": list(ALL_SEEDS),
                  "seed42_reused_without_rerun": True, "contexts": 68, "schedules_per_seed": 2856,
                  "new_event_records": 685440, "total_event_records": 856800,
                  "aggregate_cells": 60, "supported_bounds": supported, "unavailable_bounds": unavailable,
                  "full_validation_all_new_seeds": True, "completed_resume_zero_fit_all_new_seeds": True,
                  "new_operation_totals": aggregate["new_operation_totals"],
                  "run_wall_hours": run_hours, "validation_wall_hours": validation_hours,
                  "all_recorded_phase_wall_hours": total_hours, "peak_family_working_set_bytes": peak_rss,
                  "minimum_disk_free_bytes": minimum_disk, "raw_archive_parts": packages["parts"],
                  "raw_archive_bytes": packages["total_part_bytes"], "scientific_source_changed": False,
                  "matched_forecasting_complete": 70, "interval_quality_complete": 250,
                  "seasonal_unique_complete": 9, "full_study_ready": False}
    atomic(REVIEW / "BATCH_COMPLETION_RECORD.json", completion)
    output = "../../smart_building_conformal/outputs/conditional_context005/"
    lines = ["# PLEIA-temperature five-seed evidence index", "",
             "- [Five-seed report](PLEIA_TEMPERATURE_CONTEXT005_FIVE_SEED_REPORT.md)",
             "- [Batch completion record](BATCH_COMPLETION_RECORD.json)",
             "- [Frozen batch manifest](FROZEN_BATCH_MANIFEST.json)",
             "- [Evaluated commit](EVALUATED_COMMIT.json)",
             "- [Fresh launch capacity](LAUNCH_CAPACITY.json)",
             "- [Pre-fit validation](PREFIT_VALIDATION.json)",
             "- [Preservation baseline](PRESERVATION_BASELINE.json)",
             "- [Durable progress](PROGRESS_AND_RESTART.md)",
             "- [Raw-package validation](RAW_PACKAGE_VALIDATION.json)", "",
             "## New-seed acceptance", ""]
    for seed in SEEDS:
        unit = key(seed)
        lines.append(f"- Seed {seed}: [manifest]({unit}_execution_manifest.json), "
                     f"[protocol]({output.replace('outputs/', 'protocols/')}{unit}/frozen_protocol.json), "
                     f"[completion]({output}{unit}/COMPLETE.json), [operations]({output}{unit}/operations.jsonl), "
                     f"[full validation]({output}pleia_temperature_f2_context005_multiseed_v1_coordinator/seed_{seed}_validation/ADAPTER_VALIDATION_RECEIPT.json), "
                     f"[unit acceptance]({output}pleia_temperature_f2_context005_multiseed_v1_coordinator/seed_{seed}_acceptance.json), "
                     f"[zero-fit resume]({output}pleia_temperature_f2_context005_multiseed_v1_coordinator/seed_{seed}_completed_resume.json), "
                     f"[package manifest]({output}{unit}_publication_v1/parts_manifest.csv).")
    lines += ["", "## Five-seed result artifacts", "",
        f"- [All 60 comparisons]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/five_seed_control_rule_channel.csv)",
        f"- [Inference statuses]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/inference_bounds.csv)",
        f"- [Per-seed result table]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/per_seed_control_rule_channel.csv)",
        f"- [Original-context/seed contributions]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/original_context_seed_contributions.csv.gz)",
        f"- [Bootstrap design]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/bootstrap_design.json)",
        f"- [Saved draw estimates]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/bootstrap_draw_estimates.csv.gz)",
        f"- [Paired control contrasts]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/paired_control_detection_contrasts.csv)",
        f"- [Five-seed interval diagnostics]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/five_seed_interval_diagnostics.csv)",
        f"- [Operation reconciliation]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/operation_reconciliation.csv)",
        f"- [Resource-cost table]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/worker_costs_and_resources.csv)",
        f"- [Independent aggregate validation]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/independent_validation.json)",
        f"- [Detection figure PNG]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/five_seed_detection.png) and [PDF]({output}pleia_temperature_f2_context005_five_seed_analysis_v1/five_seed_detection.pdf)", ""]
    atomic(REVIEW / "EVIDENCE_INDEX.md", "\n".join(lines))
    print(json.dumps({"updated": True, "supported_bounds": supported, "unavailable_bounds": unavailable,
                      "run_wall_hours": run_hours, "validation_wall_hours": validation_hours}, indent=2))


if __name__ == "__main__":
    main()
