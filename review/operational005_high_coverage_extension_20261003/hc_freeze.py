"""Derive and freeze the extension queue and protocol before any fitting.

The queue is derived from the frozen operational005 candidate definitions and
evaluation queue.  Before scheduling, the step checks for later completed work
(accepted blocks, published metrics, other branches, existing extension
checkpoints) and searches saved owners and backup archives for an exact
97.5/99/99.5% BDG2 one-hour quantile owner that could be reused.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

from hc_common import (
    BASE_COMMIT, BLOCKS_PER_UNIT, BRANCH, ENTRY_COMMIT, EXTENSION_CODE, FOLDS, FROZEN, FROZEN_PROTOCOL_SHA256,
    FROZEN_REL, FROZEN_TAG, HERE, HISTORICAL_SOURCE_BYTE_DIGEST, LEVELS, MANIFEST_PATH, OWNERS, PILOT_UNIT,
    PRIMARY, PROTOCOL_PATH, RUN_ROOT, SCIENCE, SCIENTIFIC_PYTHON, SEEDS, UNITS, VERSION, atomic_json,
    csv_write, digest, extension_code_hashes, lf_digest, read, source_content_digest, unit_name, utc,
)

ORCHESTRATION_CODE = ("hc_supervisor.py",)
STORAGE = Path(r"D:\ConfoSenseStorage")


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(PRIMARY), *args], capture_output=True, text=True, check=True).stdout


def later_work(unavailable_ids: set[str]) -> dict:
    """Evidence that none of the 99 candidates was completed after the frozen replay."""
    accepted_root = PRIMARY / "smart_building_conformal/outputs/operational005_causal_replay_v2"
    blocks = sorted(accepted_root.glob("units/bdg2_f*_s*/blocks/block_*/identity.json"))
    accepted_ids = set()
    for path in blocks:
        accepted_ids.update(read(path)["candidate_ids"])
    metrics = accepted_root / "analysis_v1" / "operational_metrics.csv"
    metric_ids = {row["candidate_id"] for row in rows(metrics)}
    branches = [line.strip() for line in git("branch", "-a", "--format=%(refname:short)").splitlines() if line.strip()]
    related = [b for b in branches if any(word in b.lower() for word in ("high-coverage", "high_coverage", "hicov", "extension"))]
    existing = {
        "owners": sorted(p.name for p in OWNERS.glob("bdg2_f*_s*")) if OWNERS.exists() else [],
        "unit_blocks": sorted(p.relative_to(UNITS).as_posix() for p in UNITS.glob("*/blocks/block_*")) if UNITS.exists() else [],
    }
    result = {
        "accepted_block_identities_scanned": len(blocks),
        "accepted_candidates_in_blocks": len(accepted_ids),
        "extension_candidates_in_accepted_blocks": sorted(accepted_ids & unavailable_ids),
        "published_metric_candidates": len(metric_ids),
        "extension_candidates_in_published_metrics": sorted(metric_ids & unavailable_ids),
        "branches_scanned": len(branches),
        "related_branches": related,
        "existing_extension_checkpoints": existing,
    }
    if len(blocks) != 825 or result["extension_candidates_in_accepted_blocks"] or result["extension_candidates_in_published_metrics"]:
        raise ValueError("later completed work overlaps the extension scope; reconcile before scheduling")
    if [b for b in related if b not in (BRANCH, f"origin/{BRANCH}")]:
        raise ValueError(f"another extension branch exists: {related}")
    if existing["owners"] or existing["unit_blocks"]:
        raise ValueError("extension checkpoints already exist; freeze must precede execution")
    return result


def saved_owner_search() -> dict:
    """Search saved stages and archives for an exact high-level BDG2 h1 CQR owner."""
    exact, high_level_any, stage_files = [], [], 0
    outputs = PRIMARY / "smart_building_conformal" / "outputs"
    candidates = [p for pattern in ("*/*/stages/*/stage.json", "*/*/*/stages/*/stage.json", "*/stages/*/stage.json")
                  for p in outputs.glob(pattern)]
    for stage_json in candidates:
        if not stage_json.parent.name.startswith(("owner_fit_", "owner_cal_")):
            continue
        stage_files += 1
        payload = read(stage_json).get("payload", {})
        level = payload.get("level")
        name = stage_json.parent.name
        if level is not None and float(level) in LEVELS:
            high_level_any.append(stage_json.relative_to(PRIMARY).as_posix())
            if "bdg2" in stage_json.as_posix() and "_h1_" in name and payload.get("kind") == "cqr":
                exact.append(stage_json.relative_to(PRIMARY).as_posix())
    patterns = ("cqr_l97", "cqr_l99", "cqr_l0975", "cqr_l0990", "cqr_l0995", "l975", "l995")
    archive_hits, archives = [], 0
    for root in (STORAGE / "backups", STORAGE / "archives"):
        for archive in root.rglob("*.zip"):
            archives += 1
            try:
                names = zipfile.ZipFile(archive).namelist()
            except zipfile.BadZipFile:
                continue
            archive_hits.extend(f"{archive}::{n}" for n in names
                                if "bdg2" in n.lower() and "owner" in n.lower() and any(p in n.lower() for p in patterns))
    pickles = [p.relative_to(STORAGE).as_posix() for root in (STORAGE / "backups", STORAGE / "archives")
               for p in root.rglob("owner.pkl")]
    result = {
        "owner_stage_records_scanned": stage_files,
        "high_level_owner_stages_any_dataset": high_level_any,
        "exact_bdg2_h1_high_level_cqr_owners": exact,
        "zip_archives_scanned": archives,
        "archive_high_level_bdg2_owner_entries": archive_hits[:50],
        "loose_backup_owner_pickles": pickles[:50],
        "reusable_owners": 0,
        "decision": "no exact saved owner at 0.975/0.99/0.995 for BDG2 h1; fit 45 new CQR owners",
    }
    if exact or archive_hits:
        raise ValueError("candidate reusable owners found; reconcile their identities before fitting")
    return result


def run() -> dict:
    if PROTOCOL_PATH.exists():
        raise ValueError("extension protocol already frozen; issue a versioned revision instead")
    manifest = read(MANIFEST_PATH)
    if source_content_digest(SCIENCE / "smart_building_conformal" / "src") != manifest["source_content_digest"]:
        raise ValueError("science-root source differs from its manifest")
    frozen = read(FROZEN / "PROTOCOL.json")
    if digest(FROZEN / "PROTOCOL.json") != FROZEN_PROTOCOL_SHA256:
        raise ValueError("frozen operational005 protocol identity")
    definitions = rows(FROZEN / "candidate_definitions.csv")
    queue = rows(FROZEN / "evaluation_queue.csv")
    owners = rows(FROZEN / "owner_inventory.csv")
    completion = read(HERE.parent / "operational005_causal_replay_20260925" / "COMPLETION_VALIDATION.json")
    unavailable = [r for r in queue if r["execution_status"] == "unavailable_missing_saved_owner"]
    unavailable_ids = {r["candidate_id"] for r in unavailable}
    by_id = {r["candidate_id"]: r for r in definitions}
    composition = Counter((by_id[c]["method"], by_id[c]["level"]) for c in unavailable_ids)
    expected_composition = {("cqr", "0.975"): 30, ("cqr", "0.99"): 30, ("cqr", "0.995"): 30,
                            ("quantile_uncalibrated", "0.975"): 3, ("quantile_uncalibrated", "0.99"): 3,
                            ("quantile_uncalibrated", "0.995"): 3}
    if (len(definitions) != 264 or len(queue) != 3960 or len(unavailable) != 1485 or len(unavailable_ids) != 99
            or dict(composition) != expected_composition):
        raise ValueError("frozen unavailable scope differs from 99 candidates / 1,485 rows")
    if {(int(r["outer_fold"]), int(r["model_seed"])) for r in unavailable} != {(f, s) for f in FOLDS for s in SEEDS}:
        raise ValueError("fold/seed matrix differs")
    if completion["unavailable_evaluation_rows"] != 1485 or completion["accepted_evaluation_rows"] != 2475:
        raise ValueError("frozen completion counts differ")
    unavailable_owners = [r for r in owners if r["available"] == "False"]
    if len(unavailable_owners) != 90 or {r["method"] for r in unavailable_owners} != {"cqr", "quantile_uncalibrated"}:
        raise ValueError("frozen owner inventory differs")

    sys.path.insert(0, str(FROZEN))
    import adapter  # noqa: F401  (frozen; science-root copy)
    import hc_adapter
    blocks = hc_adapter.extension_blocks(adapter)
    block_of = {c["candidate_id"]: i for i, block in enumerate(blocks) for c in block}

    later = later_work(unavailable_ids)
    search = saved_owner_search()

    evaluation_rows = []
    for row in sorted(unavailable, key=lambda r: (int(r["outer_fold"]), int(r["model_seed"]), r["candidate_id"])):
        fold, seed = int(row["outer_fold"]), int(row["model_seed"])
        level = float(row["level"])
        tag = f"l{round(level * 1000):04d}"
        evaluation_rows.append({
            **{k: row[k] for k in ("evaluation_id", "candidate_id", "dataset", "horizon", "outer_fold", "model_seed",
                                   "level", "method", "strategy", "every", "window", "rule_id", "policy_id",
                                   "native_support", "common_support", "fault_replay_identifier",
                                   "clean_stream_identifier", "canonical_evaluation", "is_seed_or_fold_alias", "alias_of")},
            "original_execution_status": row["execution_status"],
            "original_unavailable_reason": row["unavailable_reason"],
            "extension_unit": unit_name(fold, seed),
            "extension_block_index": block_of[row["candidate_id"]],
            "extension_owner_stage": f"owners/{unit_name(fold, seed)}/stages/owner_cal_h1_cqr_{tag}",
            "extension_owner_shared_by": "cqr+quantile_uncalibrated",
            "execution_status": "scheduled_extension",
        })
    view_rows = [{"view_id": f"{r['evaluation_id']}_{support}", "evaluation_id": r["evaluation_id"], "support": support,
                  "canonical_evaluation": support == "native", "reporting_alias": support == "common",
                  "alias_of": f"{r['evaluation_id']}_native" if support == "common" else ""}
                 for r in evaluation_rows for support in ("native", "common")]
    block_rows = []
    for fold in FOLDS:
        for seed in SEEDS:
            for index, block in enumerate(blocks):
                c0 = block[0]
                block_rows.append({"unit": unit_name(fold, seed), "outer_fold": fold, "model_seed": seed, "block_index": index,
                                   "method": c0["method"], "level": c0["level"], "strategy": c0["strategy"],
                                   "every": c0["every"], "window": "" if c0["window"] is None else c0["window"],
                                   "candidate_ids": ";".join(c["candidate_id"] for c in block),
                                   "pilot": (fold, seed) == PILOT_UNIT})
    owner_rows = [{"unit": unit_name(f, s), "outer_fold": f, "model_seed": s, "level": level,
                   "fit_stage": f"owner_fit_h1_cqr_l{round(level * 1000):04d}",
                   "calibration_stage": f"owner_cal_h1_cqr_l{round(level * 1000):04d}",
                   "prediction_stage": f"raw_h1_cqr_l{round(level * 1000):04d}",
                   "quantile_estimator_fits": 3, "cqr_wrapper_fits": 1, "conformalize_operations": 2,
                   "shared_by": "cqr+quantile_uncalibrated"}
                  for f in FOLDS for s in SEEDS for level in LEVELS]
    if len(evaluation_rows) != 1485 or len(view_rows) != 2970 or len(block_rows) != 495 or len(owner_rows) != 45:
        raise ValueError("derived extension queue size")
    csv_write(HERE / "extension_evaluation_queue.csv", evaluation_rows)
    csv_write(HERE / "extension_metric_view_queue.csv", view_rows)
    csv_write(HERE / "extension_block_queue.csv", block_rows)
    csv_write(HERE / "extension_owner_queue.csv", owner_rows)
    atomic_json(HERE / "LATER_WORK_CHECK.json", later)
    atomic_json(HERE / "SAVED_OWNER_SEARCH.json", search)

    from importlib.metadata import version
    protocol = {
        "version": VERSION,
        "frozen_utc": utc(),
        "authorization": "explicit user instruction of 2026-10-03 (see AUTHORIZATION_REFERENCE.md): fit and "
                         "conformalize the missing BDG2 one-hour CQR/uncalibrated-quantile owners at 0.975, 0.99 "
                         "and 0.995 for this separate extension only",
        "branch": BRANCH, "base_commit": BASE_COMMIT, "frozen_tag": FROZEN_TAG,
        "frozen_operational005": {"path": FROZEN_REL, "protocol_sha256": FROZEN_PROTOCOL_SHA256,
                                  "version": frozen["version"], "entry_commit": ENTRY_COMMIT,
                                  "historical_fit_budget": frozen["fit_budget"],
                                  "historical_fit_budget_note": "describes the delivered zero-fit replay; unchanged"},
        "source_identity": {
            "source_content_digest": manifest["source_content_digest"],
            "historical_source_byte_digest": HISTORICAL_SOURCE_BYTE_DIGEST,
            "note": "git shows no src change between the entry commit and the base commit; the 2026-09 byte "
                    "digest depended on a working-tree line-ending mix that the 2026-10-02 checkout replaced. "
                    "The extension pins committed content (CRLF-normalised digest, equal to the git-blob digest).",
        },
        "source_content_digest": manifest["source_content_digest"],
        "science_root": str(SCIENCE),
        "science_root_manifest_lf_sha256": lf_digest(MANIFEST_PATH),
        "runtime": {
            "python": str(SCIENTIFIC_PYTHON), "python_sha256": digest(SCIENTIFIC_PYTHON),
            "python_version": sys.version,
            "packages": {name: version(name) for name in ("numpy", "pandas", "scikit-learn", "xgboost", "MAPIE", "matplotlib")},
            "threads": {"OMP_NUM_THREADS": 1, "OPENBLAS_NUM_THREADS": 1, "MKL_NUM_THREADS": 1,
                        "NUMEXPR_NUM_THREADS": 1, "torch": 1},
        },
        "extension_code_lf_sha256": extension_code_hashes(),
        "orchestration_code_lf_sha256": {name: lf_digest(HERE / name) for name in ORCHESTRATION_CODE},
        "extension_artifact_lf_sha256": {name: lf_digest(HERE / name) for name in (
            "extension_evaluation_queue.csv", "extension_metric_view_queue.csv", "extension_block_queue.csv",
            "extension_owner_queue.csv", "LATER_WORK_CHECK.json", "SAVED_OWNER_SEARCH.json")},
        "scope": {
            "dataset": "bdg2", "horizon": 1, "levels": list(LEVELS), "methods": ["cqr", "quantile_uncalibrated"],
            "candidates": 99, "cqr_candidates": 90, "quantile_uncalibrated_candidates": 9,
            "outer_folds": list(FOLDS), "model_seeds": list(SEEDS), "units": 15,
            "evaluation_rows": 1485, "metric_view_rows": 2970, "policy_blocks_per_unit": BLOCKS_PER_UNIT,
            "policy_blocks": 495, "accepted_blocks_not_rerun": 825, "accepted_evaluation_rows_not_rerun": 2475,
            "combined_candidates_if_complete": 264, "combined_evaluation_rows_if_complete": 3960,
            "native_and_common_are_views_not_experiments": True,
        },
        "fit_budget": {
            "forecasting_models": 0, "new_seeds": 0, "owners": 45, "cqr_wrapper_fits": 45,
            "quantile_estimator_fits": 135, "conformalize_operations": 90,
            "factory": "src.intervals005_owners.fit_owner/conformalize_owner with src.conformal_cqr._quantile_estimator(seed)",
            "roles": "original chronological fit and calibration roles of each fold/seed interval bundle",
            "sharing": "one owner per unit and level, shared by CQR and uncalibrated-quantile candidates",
            "forbidden": "refitting forecasting, EnbPI, DSCP or the accepted 95% owners; substituting 95% quantiles",
        },
        "frozen_replay_substitutions": [
            "adapter.policy_blocks -> the 33 previously unavailable policy groups",
            "adapter.UNITS -> extension storage on D:",
            "adapter.SavedOwner -> ExtensionOwner (hash-verified extension owner; SavedOwner score construction)",
            "adapter.load_unit -> frozen loader with the source-content gate",
            "adapter.source_digest/VERSION -> current content digest and '<frozen>+<extension>' version labels",
        ],
        "comparability": {
            "unchanged": ["candidate IDs", "fault catalogues and seeds", "severity scaling", "alert rules",
                          "update schedules", "residual windows", "minimum update support (50)", "rank rule",
                          "observation support", "native and common support views", "metric definitions",
                          "causal feature reconstruction", "delayed residual release"],
            "insufficient_support": "held updates are preserved as recorded statuses; no interval is invented",
            "selection": "no setting is selected from test outcomes; descriptive summaries only",
            "population_inference": "not authorized",
        },
        "pilot": {"unit": unit_name(*PILOT_UNIT), "blocks": BLOCKS_PER_UNIT, "levels": list(LEVELS),
                  "gate": "hc_pilot_gate.py; the full queue continues automatically only after it passes"},
        "resources": {"initial_scientific_workers": 1, "maximum_scientific_workers": 3,
                      "worker_launch_min_available_ram_bytes": 2 * 2**30,
                      "worker_launch_min_commit_headroom_bytes": 3 * 2**30,
                      "disk_floor_bytes": 8 * 2**30, "max_attempts_per_task": 3},
        "storage": {"run_root": str(RUN_ROOT), "owners": str(OWNERS), "units": str(UNITS)},
        "later_work_check_lf_sha256": lf_digest(HERE / "LATER_WORK_CHECK.json"),
        "saved_owner_search_lf_sha256": lf_digest(HERE / "SAVED_OWNER_SEARCH.json"),
        "full_study_ready": False,
    }
    atomic_json(PROTOCOL_PATH, protocol)
    print(json.dumps({"frozen": True, "candidates": 99, "evaluation_rows": 1485, "blocks": 495, "owners": 45,
                      "reusable_owners": 0}, indent=2))
    return protocol


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["freeze"])
    parser.parse_args()
    run()
