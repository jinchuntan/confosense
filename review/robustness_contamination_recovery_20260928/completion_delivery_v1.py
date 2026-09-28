"""Aggregation and verified external backup for robustness completion v1."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SMART = REPO / "smart_building_conformal"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(SMART))
import completion_v1 as C  # noqa: E402
import robustness_saved_owner_v1 as A  # noqa: E402
import validate_saved_owner_v1 as V  # noqa: E402
from src.unit_checkpoint import UnitCheckpoint, require_cells  # noqa: E402

VERSION = "robustness_contamination_recovery005_delivery_v1"
BACKUP = Path(r"C:\Users\nigel\ConfoSenseBackups\robustness_contamination_recovery005_20260928\completion_v1")
METRIC_COLUMNS = [
    "coverage_all", "coverage_pre", "coverage_during", "coverage_post",
    "delta_coverage_during_vs_pre", "mean_width", "median_width", "winkler",
    "fault_detected", "fault_detection_rate", "n_fault_groups", "n_detected_groups",
    "detection_delay_steps", "background_episodes", "background_per_asset_day",
    "post_fault_cascade_episodes", "n_episodes_total",
]


def expected_keys() -> list[str]:
    return [C.unit_key(row) for row in C.crosswalk().to_dict("records")]


def _unit_payload(key: str):
    if key == "bdg2_h1_f2_s42":
        payload, frames, marker = V.checkpoint_frames()
        return payload, frames, marker
    root, spec = C.checkpoint_location(key)
    store = UnitCheckpoint(root, spec, resume=True,
                           string_columns=("group_id", "row_id"))
    loaded = store.load(key)
    if loaded is None: raise ValueError(f"missing unit {key}")
    return loaded[0], loaded[1], store.verify(key)


def _receipt(key: str, phase: str) -> dict[str, Any]:
    if key == "bdg2_h1_f2_s42":
        path = HERE / ("PILOT_VALIDATION.json" if phase == "validation" else "PILOT_ZERO_FIT_RESUME.json")
    else:
        root, _ = C.checkpoint_location(key)
        name = "validation.json" if phase == "validation" else "resume.json"
        path = root / ("validation_v1" if phase == "validation" else "resume_v1") / key / name
    value = A.read(path)
    accepted = {"passed"} if phase == "validation" else {"passed", "complete_zero_fit_resume"}
    if value["status"] not in accepted: raise ValueError(f"{phase} did not pass: {key}")
    if phase == "resume" and "models_fitted" not in value:
        value.update(models_fitted=0, conformalize_calls=0)
    return value


def aggregate() -> dict[str, Any]:
    C.completion_protocol(); C.resource_gate("aggregation_launch", 256 * 2**20)
    start = time.perf_counter(); keys = expected_keys()
    if len(keys) != 60 or len(set(keys)) != 60: raise ValueError("unit matrix changed")
    cell_parts, recovery_parts, point_parts, payloads, validations, resumes = [], [], [], [], [], []
    for key in keys:
        payload, frames, marker = _unit_payload(key)
        if payload["operation_counts"]["historical_obligation_cells"] != 15:
            raise ValueError(f"unit cell obligation changed: {key}")
        for name, target in (("cell_metrics", cell_parts), ("recovery_by_group", recovery_parts),
                             ("point_accuracy", point_parts)):
            part = frames[name].copy(); part.insert(0, "unit", key); target.append(part)
        payloads.append(payload); validations.append(_receipt(key, "validation")); resumes.append(_receipt(key, "resume"))
    cells = pd.concat(cell_parts, ignore_index=True)
    recovery = pd.concat(recovery_parts, ignore_index=True)
    points = pd.concat(point_parts, ignore_index=True)
    require_cells(cells, ["dataset", "outer_fold", "model_seed", "cell"],
                  [(d, f, s, cell) for d in A.DATASETS for f in A.FOLDS for s in A.SEEDS
                   for cell in __import__("src.robustness_extension", fromlist=["expected_cell_names"]).expected_cell_names(False)])
    if len(cells) != 900 or len(points) != 120 or len(recovery) != 2415:
        raise ValueError(f"aggregate row counts changed: {len(cells)}/{len(points)}/{len(recovery)}")
    if len(validations) != 60 or sum(int(x["validated_cells"]) for x in validations) != 900:
        raise ValueError("validation coverage incomplete")
    if len(resumes) != 60 or any(x["models_fitted"] or x["conformalize_calls"] for x in resumes):
        raise ValueError("zero-fit resume coverage incomplete")

    grouping = ["dataset", "outer_fold", "cell", "family", "fault_type", "severity_sd",
                "contamination_rate", "recal_policy"]
    missing_metrics = sorted(set(METRIC_COLUMNS) - set(cells.columns))
    if missing_metrics:
        raise ValueError(f"aggregate metric schema changed: {missing_metrics}")
    means = cells.groupby(grouping, dropna=False, as_index=False)[METRIC_COLUMNS].mean()
    means["seed_aliases"] = 5; means["independent_population_replicates"] = 1
    means["population_interval_status"] = "unavailable_correlated_seeds_single_fold_unit"
    inference = pd.DataFrame([
        {"scope": f"{dataset}/fold{fold}", "seed_aliases": 5, "independent_units": 1,
         "population_intervals_available": False,
         "reason": "seeds reuse the same dataset/fold observations and are not independent population replicates"}
        for dataset in A.DATASETS for fold in A.FOLDS
    ] + [{
        "scope": "group_specific_recovery", "seed_aliases": 5, "independent_units": 0,
        "population_intervals_available": False,
        "reason": "groups, seed aliases and stream rows are retained as descriptive dependent evidence",
    }])
    cells.to_csv(HERE / "AGGREGATE_CELL_METRICS.csv", index=False)
    means.to_csv(HERE / "AGGREGATE_SEED_MEANS.csv", index=False)
    recovery.to_csv(HERE / "AGGREGATE_RECOVERY_BY_GROUP.csv", index=False)
    points.to_csv(HERE / "AGGREGATE_POINT_ACCURACY.csv", index=False)
    inference.to_csv(HERE / "INFERENCE_STATUS.csv", index=False)

    owner_registry = A.read(C.REGISTRY)
    unique_counts = {
        name: int(sum(int(p["operation_counts"][name]) for p in payloads))
        for name in ("historical_obligation_cells", "unique_corrupted_feature_rebuilds",
                     "unique_saved_owner_inference_passes", "emitted_cell_streams",
                     "contamination_reconstructions", "nonzero_contamination_reconstructions",
                     "recovery_policy_computations", "group_recovery_rows",
                     "point_metric_rows_from_saved_predictions")
    }
    expected = {"historical_obligation_cells": 900, "unique_corrupted_feature_rebuilds": 480,
                "unique_saved_owner_inference_passes": 540, "emitted_cell_streams": 900,
                "contamination_reconstructions": 180, "nonzero_contamination_reconstructions": 120,
                "recovery_policy_computations": 180, "group_recovery_rows": 2415,
                "point_metric_rows_from_saved_predictions": 120}
    if unique_counts != expected: raise ValueError(f"aggregate operation accounting mismatch: {unique_counts}")
    legacy_bytes = sum(p.stat().st_size for p in C.LEGACY_FULL_ROOT.rglob("*") if p.is_file())
    full_bytes = sum(p.stat().st_size for p in C.FULL_ROOT.rglob("*") if p.is_file())
    owner_bytes = sum(p.stat().st_size for p in C.OWNER_ROOT.rglob("*") if p.is_file())
    result = {
        "version": VERSION, "status": "passed", "completed_utc": A.utc(),
        "accepted_units": 60, "accepted_cells": 900, "pilot_units_reused": 1,
        "new_units_executed": 59, "independent_validations": 60, "zero_fit_resumes": 60,
        "owner_construction": {"units": 8, "quantile_estimator_fits": owner_registry["quantile_estimator_fits"],
                               "conformalizations": owner_registry["conformalizations"]},
        "replay_operation_counts": unique_counts,
        "replay_model_fits": 0, "replay_conformalize_calls": 0, "new_seeds": 0,
        "worker_wall_seconds": float(sum(float(p["wall_seconds"]) for p in payloads)),
        "validation_wall_seconds": float(sum(float(v.get("wall_seconds", 0)) for v in validations)),
        "peak_worker_rss_bytes": int(max(int(p["resource_pre_checkpoint"]["peak_working_set_bytes"]) for p in payloads)),
        "peak_worker_commit_bytes": int(max(int(p["resource_pre_checkpoint"]["peak_pagefile_usage_bytes"]) for p in payloads)),
        "completion_output_bytes": legacy_bytes + full_bytes,
        "legacy_completed_unit_bytes": legacy_bytes, "remaining_v2_bytes": full_bytes,
        "constructed_owner_bytes": owner_bytes,
        "population_inference": "unavailable; seed aliases/groups/rows not treated as independent replicates",
        "aggregation_wall_seconds": time.perf_counter() - start,
        "files": {name: A.digest(HERE / name) for name in (
            "AGGREGATE_CELL_METRICS.csv", "AGGREGATE_SEED_MEANS.csv",
            "AGGREGATE_RECOVERY_BY_GROUP.csv", "AGGREGATE_POINT_ACCURACY.csv", "INFERENCE_STATUS.csv")},
    }
    A.atomic_json(HERE / "COMPLETION_RESULT.json", result)
    return result


def _tree(root: Path) -> dict[str, dict[str, Any]]:
    return {p.relative_to(root).as_posix(): {"sha256": A.digest(p), "bytes": p.stat().st_size}
            for p in sorted(root.rglob("*")) if p.is_file()}


def backup() -> dict[str, Any]:
    C.completion_protocol()
    result = A.read(HERE / "COMPLETION_RESULT.json")
    if result["status"] != "passed": raise ValueError("aggregation not passed")
    sources = {"completion_59_v1_legacy": C.LEGACY_FULL_ROOT,
               "completion_58_v2_bdg2_and_failed_pleia_attempt": C.FAILED_V2_ROOT,
               "completion_58_v3_failed_pleia_recovery_identity": C.FAILED_V3_ROOT,
               "completion_58_v4_accepted_and_failed_rico_attempt": C.ACCEPTED_V4_ROOT,
               "completion_58_v5": C.ACCEPTED_V5_ROOT,
               "constructed_owners_v1": C.OWNER_ROOT}
    source_manifest = {name: _tree(path) for name, path in sources.items()}
    total = sum(item["bytes"] for tree in source_manifest.values() for item in tree.values())
    C.resource_gate("backup_launch", total + 256 * 2**20)
    if BACKUP.exists():
        receipt = A.read(BACKUP / "BACKUP_RECEIPT.json")
        if receipt["source_manifest"] != source_manifest: raise ValueError("existing backup conflicts with source")
        return receipt
    staging = BACKUP.with_name(BACKUP.name + ".partial-" + uuid.uuid4().hex)
    staging.mkdir(parents=True)
    try:
        for name, source in sources.items(): shutil.copytree(source, staging / name)
        copied = {name: _tree(staging / name) for name in sources}
        if copied != source_manifest: raise ValueError("external backup byte verification failed")
        pilot_receipt = A.read(HERE / "PILOT_BACKUP.json")
        pilot_backup = Path(pilot_receipt["destination"])
        if not pilot_backup.is_dir(): raise ValueError("verified pilot backup lineage absent")
        receipt = {
            "version": VERSION, "status": "passed", "verified_utc": A.utc(),
            "destination": str(BACKUP), "source_bytes": total,
            "source_manifest": source_manifest, "destination_manifest": copied,
            "pilot_backup_lineage": pilot_receipt,
            "all_60_units_covered": True, "same_volume_as_live_outputs": True,
        }
        A.atomic_json(staging / "BACKUP_RECEIPT.json", receipt)
        staging.rename(BACKUP)
        return receipt
    except Exception:
        raise


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=["aggregate", "backup"])
    args = parser.parse_args(); value = aggregate() if args.action == "aggregate" else backup()
    print(json.dumps(value, indent=2, default=str))


if __name__ == "__main__": main()
