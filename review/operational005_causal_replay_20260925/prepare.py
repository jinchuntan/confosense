"""Freeze the exact candidate/evaluation/view queues without scientific work."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    CONFIG, ENTRY_COMMIT, HERE, REPO, SOURCE_HASH, VERSION, atomic_json,
    bundle_paths, csv_write, digest, owner_reference, read, signature,
)


def run() -> dict:
    config = read(CONFIG)
    bdg2 = next(item for item in config["resolved_datasets"] if item["dataset"] == "bdg2")
    candidates = bdg2["candidates"]
    if len(candidates) != 264 or len({item["candidate_id"] for item in candidates}) != 264:
        raise ValueError("frozen 264-candidate identity changed")

    definitions = []
    evaluations = []
    views = []
    owners: dict[tuple[int, int, str, float], dict] = {}
    for candidate in candidates:
        definitions.append({
            "candidate_id": candidate["candidate_id"],
            "method": candidate["method"],
            "level": candidate["level"],
            "strategy": candidate["strategy"],
            "every": candidate["every"],
            "window": candidate["window"],
            "rule_id": candidate["rule_id"],
            "window_minutes": candidate["window_minutes"],
            "k": candidate["k"],
            "m": candidate["m"],
            "min_samples": candidate["min_samples"],
            "candidate_signature": signature({k: v for k, v in candidate.items() if k != "candidate_id"}),
        })
        for fold in range(3):
            for seed in range(42, 47):
                key = (fold, seed, candidate["method"], float(candidate["level"]))
                if key not in owners:
                    owners[key] = owner_reference(*key)
                owner = owners[key]
                evaluation_id = f"bdg2_f{fold}_s{seed}_{candidate['candidate_id']}"
                policy_id = signature({k: candidate[k] for k in ("method", "level", "strategy", "every", "window")})[:20]
                owner_id = owner.get("owner", {}).get("sha256", "")
                calibration_id = owner.get("calibration_values", {}).get("sha256", "")
                row = {
                    "evaluation_id": evaluation_id,
                    "candidate_id": candidate["candidate_id"],
                    "dataset": "bdg2",
                    "horizon": 1,
                    "outer_fold": fold,
                    "model_seed": seed,
                    "level": candidate["level"],
                    "method": candidate["method"],
                    "strategy": candidate["strategy"],
                    "every": candidate["every"],
                    "window": candidate["window"],
                    "rule_id": candidate["rule_id"],
                    "policy_id": policy_id,
                    "native_support": True,
                    "common_support": True,
                    "model_owner_path": owner.get("owner", {}).get("path", ""),
                    "model_owner_sha256": owner_id,
                    "calibration_owner_path": owner.get("calibration_values", {}).get("path", ""),
                    "calibration_owner_sha256": calibration_id,
                    "interval_protocol_path": owner.get("interval_protocol", ""),
                    "interval_protocol_sha256": owner.get("interval_protocol_sha256", ""),
                    "fault_replay_identifier": f"bdg2_f{fold}_outer_test_catalogues_42_46_v1",
                    "clean_stream_identifier": f"bdg2_f{fold}_s{seed}_{policy_id}_clean_v1",
                    "conformalization_artifact_id": f"{owner_id[:16]}_l{str(candidate['level']).replace('.', 'p')}",
                    "canonical_evaluation": True,
                    "is_seed_or_fold_alias": False,
                    "alias_of": "",
                    "execution_status": "ready" if owner["available"] else "unavailable_missing_saved_owner",
                    "unavailable_reason": owner["reason"],
                }
                evaluations.append(row)
                for support in ("native", "common"):
                    views.append({
                        "view_id": f"{evaluation_id}_{support}",
                        "evaluation_id": evaluation_id,
                        "support": support,
                        "canonical_evaluation": support == "native",
                        "reporting_alias": support == "common",
                        "alias_of": f"{evaluation_id}_native" if support == "common" else "",
                        "execution_status": row["execution_status"],
                    })

    ready = [row for row in evaluations if row["execution_status"] == "ready"]
    unavailable = [row for row in evaluations if row["execution_status"] != "ready"]
    ready_definitions = {row["candidate_id"] for row in ready}
    if len(evaluations) != 3960 or len(views) != 7920:
        raise ValueError("fold/seed or view matrix changed")
    if len(ready_definitions) != 165 or len(ready) != 2475 or len(unavailable) != 1485:
        raise ValueError("saved-owner coverage differs from resolved 165/2475 scope")

    csv_write(HERE / "candidate_definitions.csv", definitions)
    csv_write(HERE / "evaluation_queue.csv", evaluations)
    csv_write(HERE / "metric_view_queue.csv", views)
    owner_rows = []
    for (fold, seed, method, level), owner in owners.items():
        owner_rows.append({
            "outer_fold": fold,
            "model_seed": seed,
            "method": method,
            "level": level,
            "available": owner["available"],
            "reason": owner["reason"],
            "owner_kind": owner["owner_kind"],
            "owner_path": owner.get("owner", {}).get("path", ""),
            "owner_sha256": owner.get("owner", {}).get("sha256", ""),
            "calibration_path": owner.get("calibration_values", {}).get("path", ""),
            "calibration_sha256": owner.get("calibration_values", {}).get("sha256", ""),
        })
    csv_write(HERE / "owner_inventory.csv", owner_rows)
    summary = {
        "version": VERSION,
        "authorization_source": "user attachment 57a4912c-2519-4677-9975-05d69fd83ec1",
        "entry_commit": ENTRY_COMMIT,
        "scientific_source_hash": SOURCE_HASH,
        "operational_configuration": CONFIG.relative_to(REPO).as_posix(),
        "operational_configuration_sha256": digest(CONFIG),
        "unique_candidate_definitions": 264,
        "evaluation_rows": 3960,
        "metric_view_rows": 7920,
        "ready_unique_candidate_definitions": len(ready_definitions),
        "ready_evaluation_rows": len(ready),
        "unavailable_unique_candidate_definitions": 264 - len(ready_definitions),
        "unavailable_evaluation_rows": len(unavailable),
        "unavailable_reason": "no exact saved 97.5/99/99.5 CQR or uncalibrated-quantile owner; fitting is forbidden",
        "catalogue_seeds": [42, 43, 44, 45, 46],
        "catalogues_are_independent_experiments": False,
        "native_common_are_metric_views": True,
        "population_inference_authorized": False,
        "full_study_ready": False,
    }
    atomic_json(HERE / "QUEUE_SUMMARY.json", summary)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["freeze"])
    parser.parse_args()
    run()
