"""Completion gate, extension summaries and the combined 264-candidate inventory.

The original accepted operational005 tables are read from their committed git
blobs at the frozen candidature commit and referenced by blob hash; nothing in
the original analysis directory is written.  All summaries are descriptive:
folds, model seeds, catalogue seeds and support views are not population
replicates, and no setting is selected from these test outcomes.
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from hc_common import (
    ANALYSIS, BASE_COMMIT, BLOCKS_PER_UNIT, FOLDS, HERE, LEVELS, OWNERS, RUN_ROOT, SEEDS, UNITS, VERSION,
    WORKTREE, atomic_json, atomic_text, digest, read, unit_name, utc, verify_extension_protocol,
)

ORIGINAL_ANALYSIS = "smart_building_conformal/outputs/operational005_causal_replay_v2/analysis_v1"
RESULTS = HERE / "results"
SUMMARY_KEYS = ["candidate_id", "method", "level", "strategy", "rule_id", "support"]
EXTRA_MEANS = {
    "mean_macro_event_recall": "macro_event_recall",
    "mean_custom_synthetic_f1": "custom_synthetic_f1",
    "mean_ordinary_episode_precision": "ordinary_matched_event_episode_precision",
    "mean_time_in_alert_fraction": "time_in_alert_fraction",
}


def git_blob(path: str) -> tuple[bytes, str]:
    spec = f"{BASE_COMMIT}:{path}"
    blob_sha = subprocess.run(["git", "-C", str(WORKTREE), "rev-parse", spec], capture_output=True, text=True,
                              check=True).stdout.strip()
    data = subprocess.run(["git", "-C", str(WORKTREE), "cat-file", "blob", blob_sha], capture_output=True,
                          check=True).stdout
    return data, blob_sha


def completion_gate() -> tuple[pd.DataFrame, dict]:
    owners = {}
    for fold in FOLDS:
        for seed in SEEDS:
            unit = unit_name(fold, seed)
            validation = read(OWNERS / unit / "OWNER_VALIDATION.json")
            resume = read(OWNERS / unit / "RESUME.json")
            if not validation.get("passed") or not resume.get("passed") or resume.get("models_fitted") != 0:
                raise ValueError(f"owner gate failed: {unit}")
            if validation["owner_manifest_sha256"] != digest(OWNERS / unit / "OWNER_MANIFEST.json"):
                raise ValueError(f"owner manifest changed after validation: {unit}")
            owners[unit] = {tag: r["calibrated_owner_sha256"] for tag, r in validation["levels"].items()}
    metrics, seen, maximum, frozen_checks, extended_checks, raw_bytes = [], set(), 0.0, 0, 0, 0
    status_rows = Counter()
    for fold in FOLDS:
        for seed in SEEDS:
            unit = unit_name(fold, seed)
            for index in range(BLOCKS_PER_UNIT):
                key = (unit, index)
                if key in seen:
                    raise ValueError("duplicate block")
                seen.add(key)
                stage = UNITS / unit / "blocks" / f"block_{index:03d}"
                marker = read(stage / "COMPLETE.json")
                if marker["status"] != "complete" or marker["models_fitted"] != 0:
                    raise ValueError(f"block marker: {key}")
                for name, expected in marker["files"].items():
                    if digest(stage / name) != expected:
                        raise ValueError(f"block file changed: {key} {name}")
                    raw_bytes += (stage / name).stat().st_size
                frozen = read(UNITS / unit / "validation" / f"block_{index:03d}.json")
                extended = read(UNITS / unit / "validation" / f"block_{index:03d}.extended.json")
                resume = read(UNITS / unit / "resume" / f"block_{index:03d}.json")
                if not (frozen.get("passed") and extended.get("passed") and resume.get("passed")
                        and resume.get("files_unchanged")):
                    raise ValueError(f"block gate failed: {key}")
                identity = read(stage / "identity.json")
                tag = f"l{round(float(identity['policy']['level']) * 1000):04d}"
                if identity["owner"]["owner"]["sha256"] != owners[unit][tag]:
                    raise ValueError(f"block owner differs from the validated owner: {key}")
                frozen_checks += frozen["checks"]
                extended_checks += extended["metric_checks"]
                maximum = max(maximum, frozen["maximum_absolute_difference"], extended["maximum_metric_absolute_difference"])
                for counts in extended["update_status_counts"].values():
                    for status, count in counts.items():
                        status_rows[(identity["policy"]["level"], identity["policy"]["strategy"], status)] += count
                metrics.append(pd.read_csv(stage / "metrics.csv"))
    table = pd.concat(metrics, ignore_index=True)
    queue = pd.read_csv(HERE / "extension_evaluation_queue.csv")
    if len(table) != 2970 or table.duplicated(["evaluation_id", "support"]).any():
        raise ValueError("extension metric matrix size")
    if set(table.evaluation_id) != set(queue.evaluation_id) or table.candidate_id.nunique() != 99:
        raise ValueError("extension metric identities differ from the frozen extension queue")
    if (table.groupby(["candidate_id", "support"]).size() != 15).any():
        raise ValueError("candidate fold/seed coverage")
    ledger = [json.loads(line) for line in (RUN_ROOT / "fit_ledger.jsonl").read_text(encoding="utf-8").splitlines() if line]
    fits = Counter()
    for row in ledger:
        if row.get("event") == "new_owner_operation":
            fits.update(row["operation_counts"])
    if dict(fits) != {"cqr_wrapper_fit": 45, "quantile_estimator_fit": 135, "calibrator_conformalize": 90}:
        raise ValueError(f"fit ledger differs from the authorised budget: {dict(fits)}")
    gate = {
        "owners_validated": len(owners), "owner_zero_fit_resumes": len(owners),
        "blocks": len(seen), "blocks_validated_frozen": len(seen), "blocks_validated_extended": len(seen),
        "blocks_zero_fit_resumed": len(seen), "evaluation_rows": int(table.evaluation_id.nunique()),
        "metric_view_rows": len(table), "candidates": int(table.candidate_id.nunique()),
        "frozen_validator_checks": frozen_checks, "extended_metric_checks": extended_checks,
        "maximum_validation_absolute_difference": maximum, "raw_block_bytes": raw_bytes,
        "fit_operations": dict(fits),
        "held_insufficient_support_rows": {f"{l}|{s}": c for (l, s, t), c in sorted(status_rows.items())
                                           if t == "held_insufficient_score_or_rank_support"},
    }
    return table, gate


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    summary = table.groupby(SUMMARY_KEYS, as_index=False).agg(
        evaluation_rows=("evaluation_id", "size"), event_count=("n_events", "sum"), detected_count=("n_detected", "sum"),
        mean_detection_rate=("event_recall_micro", "mean"), minimum_detection_rate=("event_recall_micro", "min"),
        maximum_detection_rate=("event_recall_micro", "max"),
        mean_restricted_detection_minutes=("restricted_mean_detection_minutes", "mean"),
        mean_clean_workload=("background_episodes_per_asset_day", "mean"),
        maximum_clean_workload=("background_episodes_per_asset_day", "max"))
    extra = table.groupby(SUMMARY_KEYS, as_index=False).agg(**{k: (v, "mean") for k, v in EXTRA_MEANS.items()})
    return summary.merge(extra, on=SUMMARY_KEYS, validate="one_to_one")


def figure(combined: pd.DataFrame, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    native = combined[combined.support == "native"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    colours = {0.95: "#9ec5f4", 0.975: "#5a9ce8", 0.99: "#1c6bc9", 0.995: "#0d366b"}
    for ax, method in zip(axes, ("cqr", "quantile_uncalibrated")):
        part = native[native.method == method]
        for level, sub in part.groupby("level"):
            ax.scatter(sub.mean_clean_workload, sub.mean_macro_event_recall, s=16, color=colours[float(level)],
                       label=f"{float(level):g}" + (" (original)" if float(level) == 0.95 else " (extension)"))
        ax.set_xscale("log")
        ax.set_title(method.replace("_", " "))
        ax.set_xlabel("mean clean episodes per asset-day")
        ax.grid(alpha=.3)
    axes[0].set_ylabel("mean macro event recall")
    axes[0].legend(title="nominal level", fontsize=8)
    fig.suptitle("BDG2 one-hour operational replay, native support (descriptive)")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def run() -> dict:
    verify_extension_protocol()
    table, gate = completion_gate()
    table["status"] = "validated_extension"
    original_metrics_bytes, metrics_blob = git_blob(f"{ORIGINAL_ANALYSIS}/operational_metrics.csv")
    original_summary_bytes, summary_blob = git_blob(f"{ORIGINAL_ANALYSIS}/candidate_summary.csv")
    original = pd.read_csv(io.BytesIO(original_metrics_bytes))
    if len(original) != 4950 or original.candidate_id.nunique() != 165:
        raise ValueError("original accepted metric table differs")
    if set(original.candidate_id) & set(table.candidate_id):
        raise ValueError("extension candidates overlap original accepted candidates")
    extension_summary = summarise(table)
    original_summary = summarise(original)
    frozen_summary = pd.read_csv(io.BytesIO(original_summary_bytes))
    check = original_summary[frozen_summary.columns].sort_values(SUMMARY_KEYS).reset_index(drop=True)
    pd.testing.assert_frame_equal(check, frozen_summary.sort_values(SUMMARY_KEYS).reset_index(drop=True),
                                  check_exact=False, rtol=1e-12, atol=1e-12)
    original_summary["source"] = f"original_accepted:{ORIGINAL_ANALYSIS}/operational_metrics.csv@{BASE_COMMIT[:10]}"
    extension_summary["source"] = f"extension:{VERSION}"
    combined_summary = pd.concat([original_summary, extension_summary], ignore_index=True)
    if combined_summary.candidate_id.nunique() != 264 or len(combined_summary) != 528:
        raise ValueError("combined candidate summary size")

    queue = pd.read_csv(HERE.parent / "operational005_causal_replay_20260925" / "evaluation_queue.csv")
    ext_queue = pd.read_csv(HERE / "extension_evaluation_queue.csv")
    inventory = queue[["evaluation_id", "candidate_id", "outer_fold", "model_seed", "method", "level", "strategy",
                       "every", "window", "rule_id", "execution_status"]].rename(
        columns={"execution_status": "original_execution_status"})
    owner_of = {}
    for fold in FOLDS:
        for seed in SEEDS:
            unit = unit_name(fold, seed)
            manifest = read(OWNERS / unit / "OWNER_MANIFEST.json")
            for tag, record in manifest["levels"].items():
                owner_of[(unit, tag)] = record["calibrated_owner_sha256"]
    sources, owners = [], []
    for row in inventory.itertuples():
        if row.original_execution_status == "ready":
            sources.append(f"original_accepted@{BASE_COMMIT[:10]}")
            owners.append(queue.loc[row.Index, "model_owner_sha256"])
        else:
            tag = f"l{round(float(row.level) * 1000):04d}"
            sources.append(f"extension:{VERSION}")
            owners.append(owner_of[(unit_name(int(row.outer_fold), int(row.model_seed)), tag)])
    inventory["result_source"] = sources
    inventory["model_owner_sha256"] = owners
    inventory["validated"] = True
    if len(inventory) != 3960 or inventory.candidate_id.nunique() != 264:
        raise ValueError("combined evaluation inventory size")
    if set(inventory[inventory.result_source.str.startswith("extension")].evaluation_id) != set(ext_queue.evaluation_id):
        raise ValueError("combined inventory extension rows differ from the extension queue")
    candidates = inventory.groupby(["candidate_id", "method", "level", "strategy", "every", "window", "rule_id",
                                    "result_source"], dropna=False, as_index=False).agg(evaluation_rows=("evaluation_id", "size"))
    if len(candidates) != 264 or (candidates.evaluation_rows != 15).any():
        raise ValueError("combined candidate inventory")

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    outputs = {
        "extension_operational_metrics.csv": table,
        "extension_candidate_summary.csv": extension_summary,
        "combined_candidate_summary.csv": combined_summary,
        "combined_evaluation_inventory.csv": inventory,
        "combined_candidate_inventory.csv": candidates,
    }
    for name, frame in outputs.items():
        frame.to_csv(ANALYSIS / name, index=False, lineterminator="\n")
    figure(combined_summary, ANALYSIS / "combined_tradeoff_native.png")

    native = combined_summary[combined_summary.support == "native"]
    by_level = native.groupby(["method", "level", "strategy"], as_index=False).agg(
        candidates=("candidate_id", "nunique"), mean_macro_event_recall=("mean_macro_event_recall", "mean"),
        mean_micro_recall=("mean_detection_rate", "mean"), mean_custom_synthetic_f1=("mean_custom_synthetic_f1", "mean"),
        mean_ordinary_precision=("mean_ordinary_episode_precision", "mean"),
        mean_clean_workload=("mean_clean_workload", "mean"),
        mean_restricted_detection_minutes=("mean_restricted_detection_minutes", "mean"))
    by_level.insert(0, "source", np.where(by_level.method.isin(["cqr", "quantile_uncalibrated"])
                                          & (by_level.level.astype(float) != 0.95), "extension", "original_accepted"))
    by_level.to_csv(ANALYSIS / "combined_by_method_level_strategy.csv", index=False, lineterminator="\n")
    result = {
        "passed": True, "version": VERSION, "utc": utc(), **gate,
        "original_accepted_metrics": {"path": f"{ORIGINAL_ANALYSIS}/operational_metrics.csv", "commit": BASE_COMMIT,
                                      "git_blob": metrics_blob, "rows": len(original), "candidates": 165},
        "original_candidate_summary": {"path": f"{ORIGINAL_ANALYSIS}/candidate_summary.csv", "commit": BASE_COMMIT,
                                       "git_blob": summary_blob, "recomputed_equal": True},
        "combined_candidates": 264, "combined_evaluation_rows": 3960,
        "combined_metric_view_rows_reference_only": 4950 + len(table),
        "native_and_common_are_views_not_experiments": True,
        "population_inference": "not performed", "selection_from_test_outcomes": "none",
    }
    atomic_json(ANALYSIS / "COMPLETION_VALIDATION.json", result)
    report = report_text(result, by_level)
    atomic_text(ANALYSIS / "REPORT.md", report)
    for name in [*outputs, "combined_tradeoff_native.png", "combined_by_method_level_strategy.csv",
                 "COMPLETION_VALIDATION.json", "REPORT.md"]:
        shutil.copyfile(ANALYSIS / name, RESULTS / name)
    print(json.dumps({k: result[k] for k in ("passed", "blocks", "evaluation_rows", "metric_view_rows",
                                               "combined_candidates", "combined_evaluation_rows")}))
    return result


def report_text(result: dict, by_level: pd.DataFrame) -> str:
    lines = [
        "# Operational005 high-coverage extension: BDG2 one-hour CQR and uncalibrated quantiles",
        "",
        "Descriptive results of the separately versioned extension. They are not part of the candidature",
        "report, and they do not change the accepted operational005 tables, figures or captions.",
        "",
        f"- {result['candidates']} previously unavailable candidates (90 CQR, 9 uncalibrated quantile) at nominal",
        "  0.975, 0.99 and 0.995, over three outer folds and five model seeds:",
        f"  {result['evaluation_rows']:,} evaluation rows in {result['blocks']} policy blocks.",
        "- 45 new CQR owners (135 quantile-estimator fits, 90 conformalize operations), one per unit and level,",
        "  shared by the CQR and uncalibrated-quantile candidates. No forecasting model was refitted.",
        f"- Every block passed the frozen validator and an extended independent validator "
        f"(maximum absolute difference {result['maximum_validation_absolute_difference']:.3g}) and resumed without change.",
        f"- Combined with the 165 accepted candidates: {result['combined_candidates']} candidates and "
        f"{result['combined_evaluation_rows']:,} evaluation rows. Native and common support are two views of the",
        "  same evaluations, not additional experiments.",
        "",
        "Folds, model seeds, catalogue seeds and support views are not independent population replicates, so no",
        "confidence interval or significance claim is made, and no setting is selected from these test outcomes.",
        "",
        "## Native-support means by method, nominal level and recalibration strategy",
        "",
        "Each row averages the candidates' fold/seed means over the three temporal rules (single sample, 3 of 3",
        "in 180 min, 4 of 6 in 360 min). Source: extension = completed here; original = accepted operational005 tables.",
        "",
        "| Method | Level | Strategy | Source | Candidates | Macro recall | Micro recall | Custom F1 | Episode precision | Clean episodes per asset-day | Restricted detection (min) |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in by_level.sort_values(["method", "strategy", "level"]).itertuples():
        source = "extension" if row.source == "extension" else "original"
        lines.append(f"| {row.method} | {float(row.level):g} | {row.strategy} | {source} | {row.candidates} | "
                     f"{row.mean_macro_event_recall:.3f} | {row.mean_micro_recall:.3f} | {row.mean_custom_synthetic_f1:.3f} | "
                     f"{row.mean_ordinary_precision:.3f} | {row.mean_clean_workload:.3f} | "
                     f"{row.mean_restricted_detection_minutes:.1f} |")
    held = result["held_insufficient_support_rows"]
    lines += ["", "Rows held at the previous correction because a scheduled update lacked score or rank support "
              "(all streams, all folds and seeds): " + (", ".join(f"{k}: {v:,}" for k, v in held.items()) if held else "none") + ".",
              "", "Original rows (every recentred EnbPI row, and the 0.95 CQR and uncalibrated-quantile rows) are "
              "recomputed from the accepted operational005 metric table read from its committed blob. Extension rows "
              "are the 0.975, 0.99 and 0.995 CQR and uncalibrated-quantile candidates completed here."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["run", "gate-only"])
    args = parser.parse_args()
    if args.action == "run":
        run()
    else:
        verify_extension_protocol()
        print(json.dumps(completion_gate()[1], default=str, indent=2))
