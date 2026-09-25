"""Compact descriptive aggregation after every accepted replay block passes."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import HERE, OUTPUTS, UNITS, atomic_json, csv_write, read, verify_protocol

ANALYSIS = OUTPUTS / "analysis_v1"


def run():
    verify_protocol()
    metrics = []
    validations = 0; resumes = 0; blocks = 0
    for fold in range(3):
        for seed in range(42, 47):
            unit = UNITS / f"bdg2_f{fold}_s{seed}"
            for block in range(55):
                stage = unit / "blocks" / f"block_{block:03d}"
                validation = unit / "validation" / f"block_{block:03d}.json"
                resume = unit / "resume" / f"block_{block:03d}.json"
                if not (stage / "COMPLETE.json").exists(): raise ValueError("missing accepted replay block")
                if not validation.exists() or not read(validation).get("passed"): raise ValueError("missing independent validation")
                if not resume.exists() or not read(resume).get("passed"): raise ValueError("missing zero-fit resume")
                metrics.append(pd.read_csv(stage / "metrics.csv")); blocks += 1; validations += 1; resumes += 1
    table = pd.concat(metrics, ignore_index=True)
    if len(table) != 4950 or table.duplicated(["evaluation_id", "support"]).any():
        raise ValueError("accepted operational metric matrix mismatch")
    queue = pd.read_csv(HERE / "evaluation_queue.csv")
    unavailable = queue[queue.execution_status != "ready"]
    unavailable_views = []
    for row in unavailable.to_dict("records"):
        for support in ("native", "common"):
            unavailable_views.append({**row, "support": support, "status": "unavailable_missing_saved_owner",
                                      "n_events": np.nan, "n_detected": np.nan,
                                      "event_recall_micro": np.nan, "restricted_mean_detection_minutes": np.nan,
                                      "background_episodes_per_asset_day": np.nan})
    unavailable_table = pd.DataFrame(unavailable_views)
    table["status"] = "validated"
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    table.to_csv(ANALYSIS / "operational_metrics.csv", index=False)
    unavailable_table.to_csv(ANALYSIS / "unavailable_metrics.csv", index=False)
    summary = table.groupby(["candidate_id", "method", "level", "strategy", "rule_id", "support"], as_index=False).agg(
        evaluation_rows=("evaluation_id", "size"), event_count=("n_events", "sum"), detected_count=("n_detected", "sum"),
        mean_detection_rate=("event_recall_micro", "mean"), minimum_detection_rate=("event_recall_micro", "min"),
        maximum_detection_rate=("event_recall_micro", "max"), mean_restricted_detection_minutes=("restricted_mean_detection_minutes", "mean"),
        mean_clean_workload=("background_episodes_per_asset_day", "mean"), maximum_clean_workload=("background_episodes_per_asset_day", "max"))
    summary.to_csv(ANALYSIS / "candidate_summary.csv", index=False)
    native = summary[summary.support == "native"]
    fig, ax = plt.subplots(figsize=(8, 5))
    for method, part in native.groupby("method"):
        ax.scatter(part.mean_clean_workload, part.mean_detection_rate, s=14, alpha=.65, label=method)
    ax.set_xlabel("mean clean episodes per asset-day"); ax.set_ylabel("mean synthetic-event detection rate")
    ax.set_title("BDG2 operational replay: descriptive candidate trade-off"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(ANALYSIS / "operational_tradeoff.png", dpi=160); plt.close(fig)
    result = {"passed": True, "unique_candidate_definitions": 264, "ready_unique_candidates": 165,
              "unavailable_unique_candidates": 99, "evaluation_rows": 3960, "validated_evaluation_rows": 2475,
              "unavailable_evaluation_rows": 1485, "validated_metric_view_rows": len(table),
              "unavailable_metric_view_rows": len(unavailable_table), "policy_blocks": blocks,
              "independent_validations": validations, "zero_fit_resumes": resumes,
              "population_inference": "not performed", "full_study_ready": False}
    atomic_json(ANALYSIS / "analysis_validation.json", result)
    report = f"""# Bounded operational005 causal-replay analysis

All {result['validated_evaluation_rows']:,} executable fold/seed evaluation rows across 165 unique
candidate definitions passed independent block validation and zero-fit resume. The remaining
1,485 rows across 99 candidate definitions are explicitly unavailable because exact saved
97.5%, 99% and 99.5% CQR/uncalibrated-quantile owners do not exist and fitting was forbidden.

Native and common-support tables are reporting views of the same evaluations, not independent
experiments. Catalogue seeds are synthetic catalogue repetitions. Results are descriptive; no
population confidence interval is produced. Full-study readiness remains false.
"""
    (ANALYSIS / "REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps(result, indent=2)); return result


if __name__ == "__main__": run()
