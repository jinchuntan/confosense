"""Validate, preserve, and publish the completed operational005 replay.

This delivery layer is additive.  It never invokes the replay adapter or fits a
model.  It may run only after the frozen coordinator and supervisor have
finished successfully.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from pandas.testing import assert_frame_equal

from common import (HERE, OUTPUTS, REPO, SOURCE_HASH, UNITS, atomic_json,
                    digest, read, verify_protocol)


VERSION = "operational005_causal_replay_delivery_v1.3"
ROOT = OUTPUTS / "completion_delivery_v1"
PROGRESS = ROOT / "progress.json"
EVENTS = ROOT / "events.jsonl"
LOCK = ROOT / "delivery.lock"
ANALYSIS = OUTPUTS / "analysis_v1"
SUPERVISOR_STATUS = OUTPUTS / "supervisor" / "status.json"
COORDINATOR_PROGRESS = OUTPUTS / "coordinator" / "progress.json"

BACKUP = Path(r"D:\ConfoSenseStorage\backups\operational005_causal_replay_20260925\raw_and_execution_v2")
ARCHIVES = Path(r"D:\ConfoSenseStorage\archives\operational005_causal_replay_20260925\git_delivery_v1")
TEMP = Path(r"D:\ConfoSenseStorage\temp")
RECOVERY_REPO = Path(r"D:\ConfoSenseStorage\backups\robustness_contamination_recovery005_20260928\git_delivery_v1\recovery_22e774566")

TARGET_BRANCH = "review/operational005-causal-replay-20260925"
BASE_COMMIT = "3057f5a84f678596188943f6186ede4d6a8f2621"
BACKUP_PREREQUISITE = "1b94d7dc027fe2a15049c82ba3c9a721df329ece"
DISK_FLOOR = 8 * 2**30
PART_BUDGET = 80 * 2**20
PART_LIMIT = 95 * 2**20
ZIP_STAMP = (2026, 10, 1, 0, 0, 0)

REVIEW_REL = "review/operational005_causal_replay_20260925"
ANALYSIS_REL = "smart_building_conformal/outputs/operational005_causal_replay_v2/analysis_v1"
SUBSTANTIVE_PATHS = [
    f"{REVIEW_REL}/parallel_reverse_v1.py",
    f"{REVIEW_REL}/completion_delivery_v1.py",
    f"{REVIEW_REL}/completion_supervisor_v1.py",
    f"{REVIEW_REL}/DELIVERY_VALIDATION_FAILURE_V1.json",
    f"{REVIEW_REL}/DELIVERY_VALIDATION_CORRECTION_V1_1.md",
    f"{REVIEW_REL}/PUBLICATION_PREFLIGHT_FAILURE_V1_1.json",
    f"{REVIEW_REL}/PUBLICATION_PREFLIGHT_CORRECTION_V1_2.md",
    f"{REVIEW_REL}/PUBLICATION_CREDENTIAL_GATE_FAILURE_V1_2.json",
    f"{REVIEW_REL}/PUBLICATION_CREDENTIAL_GATE_CORRECTION_V1_3.md",
    f"{REVIEW_REL}/COMPLETION_VALIDATION.json",
    f"{REVIEW_REL}/BACKUP_VERIFICATION.json",
    f"{REVIEW_REL}/OPERATIONAL_REPORT.md",
    f"{REVIEW_REL}/EVIDENCE_INDEX.md",
    f"{REVIEW_REL}/PREPUBLICATION_MANIFEST.json",
    f"{ANALYSIS_REL}/operational_metrics.csv",
    f"{ANALYSIS_REL}/unavailable_metrics.csv",
    f"{ANALYSIS_REL}/candidate_summary.csv",
    f"{ANALYSIS_REL}/operational_tradeoff.png",
    f"{ANALYSIS_REL}/analysis_validation.json",
    f"{ANALYSIS_REL}/REPORT.md",
]
RECEIPT_PATHS = [
    f"{REVIEW_REL}/GITHUB_REMOTE_READBACK.json",
    f"{REVIEW_REL}/READBACK_MANIFEST.csv",
    f"{REVIEW_REL}/DELIVERY_RECEIPT.json",
]


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def event(name: str, **values: Any) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps({"utc": utc(), "event": name, **values}, default=str,
                                separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def progress(**values: Any) -> dict[str, Any]:
    value = read(PROGRESS) if PROGRESS.exists() else {}
    value.update(values, version=VERSION, updated_utc=utc(), pid=os.getpid())
    atomic_json(PROGRESS, value)
    return value


def sha256_stream(stream) -> tuple[str, int]:
    value = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(2**20), b""):
        value.update(block)
        size += len(block)
    return value.hexdigest(), size


def git(*arguments: str, env: dict[str, str] | None = None, check: bool = True) -> str:
    result = subprocess.run(["git", *arguments], cwd=REPO, env=env, capture_output=True,
                            text=True, check=False)
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(arguments)} failed ({result.returncode}): {result.stderr[-4000:]}")
    return result.stdout.strip()


def final_science_gate() -> tuple[dict[str, Any], dict[str, Any]]:
    verify_protocol()
    supervisor = read(SUPERVISOR_STATUS)
    coordinator = read(COORDINATOR_PROGRESS)
    if supervisor.get("state") != "scientific_complete_delivery_pending":
        raise ValueError(f"frozen supervisor has not released delivery: {supervisor.get('state')}")
    if supervisor.get("coordinator_exit_code") != 0:
        raise ValueError("frozen coordinator did not exit successfully")
    expected = {
        "status": "scientific_complete", "current_phase": "delivery_pending",
        "completed_policy_blocks": 825, "remaining_policy_blocks": 0,
        "validated_policy_blocks": 825, "zero_fit_resumed_policy_blocks": 825,
        "completed_evaluation_rows": 2475, "remaining_ready_evaluation_rows": 0,
    }
    for name, wanted in expected.items():
        if coordinator.get(name) != wanted:
            raise ValueError(f"final coordinator gate mismatch: {name}={coordinator.get(name)!r}")
    if coordinator.get("exact_error") is not None or coordinator.get("current_scientific_worker") is not None:
        raise ValueError("coordinator retained an error or scientific worker")
    return supervisor, coordinator


def _frame_key(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.sort_values(["evaluation_id", "support"], kind="stable").reset_index(drop=True)


def validate_completion() -> dict[str, Any]:
    started = time.perf_counter()
    supervisor, coordinator = final_science_gate()
    metric_parts: list[pd.DataFrame] = []
    operation_counts: Counter[str] = Counter()
    helper_claims: set[int] = set()
    helper_claim_root = OUTPUTS / "parallel_reverse_v1" / "claims"
    if helper_claim_root.exists():
        for path in sorted(helper_claim_root.glob("queue_*.json")):
            value = read(path)
            if value.get("status") == "accepted":
                ordinal = int(value["queue_ordinal"])
                if ordinal in helper_claims:
                    raise ValueError("duplicate helper claim ordinal")
                helper_claims.add(ordinal)

    seen_blocks: set[tuple[int, int, int]] = set()
    maximum_validation_difference = 0.0
    raw_bytes = 0
    for fold in range(3):
        for seed in range(42, 47):
            unit = UNITS / f"bdg2_f{fold}_s{seed}"
            operation_path = unit / "operations.jsonl"
            with operation_path.open("r", encoding="utf-8") as handle:
                operations = [json.loads(line) for line in handle if line.strip()]
            for row in operations:
                if row.get("event") == "returned":
                    phase = str(row.get("phase"))
                    operation_counts[phase] += 1
                    if int(row.get("fits", 0) or 0) != 0:
                        raise ValueError(f"nonzero fit recorded in {operation_path}")
            for block in range(55):
                key = (fold, seed, block)
                if key in seen_blocks:
                    raise ValueError(f"duplicate block identity: {key}")
                seen_blocks.add(key)
                stage = unit / "blocks" / f"block_{block:03d}"
                marker = read(stage / "COMPLETE.json")
                if marker.get("status") != "complete" or marker.get("models_fitted") != 0:
                    raise ValueError(f"invalid completion marker: {key}")
                for name, expected_hash in marker["files"].items():
                    path = stage / name
                    if digest(path) != expected_hash:
                        raise ValueError(f"stage hash mismatch: {path}")
                    raw_bytes += path.stat().st_size
                validation = read(unit / "validation" / f"block_{block:03d}.json")
                if (not validation.get("passed") or validation.get("models_fitted") != 0 or
                        validation.get("source_hash") != SOURCE_HASH):
                    raise ValueError(f"independent validation gate failed: {key}")
                maximum_validation_difference = max(
                    maximum_validation_difference,
                    float(validation.get("maximum_absolute_difference", 0.0)),
                )
                resume = read(unit / "resume" / f"block_{block:03d}.json")
                if (not resume.get("passed") or not resume.get("files_unchanged") or
                        resume.get("models_fitted") != 0):
                    raise ValueError(f"zero-fit resume gate failed: {key}")
                metric_parts.append(pd.read_csv(stage / "metrics.csv"))

    if len(seen_blocks) != 825:
        raise ValueError("accepted block identity count changed")
    metrics = pd.concat(metric_parts, ignore_index=True)
    if len(metrics) != 4950 or metrics.duplicated(["evaluation_id", "support"]).any():
        raise ValueError("validated metric-view matrix is incomplete or duplicated")
    if metrics.evaluation_id.nunique() != 2475:
        raise ValueError("unique accepted evaluation-row count changed")
    if set(metrics.support.astype(str)) != {"native", "common"}:
        raise ValueError("native/common support views changed")

    queue = pd.read_csv(HERE / "evaluation_queue.csv")
    if len(queue) != 3960 or queue.evaluation_id.nunique() != 3960:
        raise ValueError("evaluation queue identity changed")
    ready = queue[queue.execution_status == "ready"]
    unavailable = queue[queue.execution_status != "ready"]
    if (len(ready) != 2475 or ready.candidate_id.nunique() != 165 or
            len(unavailable) != 1485 or unavailable.candidate_id.nunique() != 99):
        raise ValueError("ready/unavailable queue coverage changed")
    if set(metrics.evaluation_id.astype(str)) != set(ready.evaluation_id.astype(str)):
        raise ValueError("accepted metric identities do not exactly match the ready queue")

    published_metrics = pd.read_csv(ANALYSIS / "operational_metrics.csv")
    expected_published_columns = set(metrics.columns) | {"status"}
    if set(published_metrics.columns) != expected_published_columns:
        raise ValueError("published operational metric schema is not raw metrics plus status")
    if set(published_metrics.status.astype(str)) != {"validated"}:
        raise ValueError("published operational metric status is not uniformly validated")
    assert_frame_equal(_frame_key(metrics),
                       _frame_key(published_metrics[list(metrics.columns)]), check_dtype=False,
                       check_exact=False, rtol=1e-12, atol=1e-12)
    unavailable_metrics = pd.read_csv(ANALYSIS / "unavailable_metrics.csv")
    if (len(unavailable_metrics) != 2970 or
            unavailable_metrics.evaluation_id.nunique() != 1485 or
            set(unavailable_metrics.support.astype(str)) != {"native", "common"} or
            set(unavailable_metrics.status.astype(str)) != {"unavailable_missing_saved_owner"}):
        raise ValueError("explicit unavailable-result matrix changed")
    if set(unavailable_metrics.evaluation_id.astype(str)) & set(metrics.evaluation_id.astype(str)):
        raise ValueError("ready and unavailable evaluation identities overlap")

    grouping = ["candidate_id", "method", "level", "strategy", "rule_id", "support"]
    columns = ["n_events", "n_detected", "event_recall_micro",
               "restricted_mean_detection_minutes", "background_episodes_per_asset_day"]
    rebuilt = metrics.groupby(grouping, as_index=False).agg(
        evaluation_rows=("evaluation_id", "size"), event_count=("n_events", "sum"),
        detected_count=("n_detected", "sum"), mean_detection_rate=("event_recall_micro", "mean"),
        minimum_detection_rate=("event_recall_micro", "min"),
        maximum_detection_rate=("event_recall_micro", "max"),
        mean_restricted_detection_minutes=("restricted_mean_detection_minutes", "mean"),
        mean_clean_workload=("background_episodes_per_asset_day", "mean"),
        maximum_clean_workload=("background_episodes_per_asset_day", "max"),
    )
    summary = pd.read_csv(ANALYSIS / "candidate_summary.csv")
    assert_frame_equal(rebuilt.sort_values(grouping).reset_index(drop=True),
                       summary.sort_values(grouping).reset_index(drop=True), check_dtype=False,
                       check_exact=False, rtol=1e-12, atol=1e-12)
    if not (ANALYSIS / "operational_tradeoff.png").is_file():
        raise ValueError("compact operational figure is absent")
    aggregate_receipt = read(ANALYSIS / "analysis_validation.json")
    required_aggregate = {
        "passed": True, "unique_candidate_definitions": 264,
        "ready_unique_candidates": 165, "unavailable_unique_candidates": 99,
        "evaluation_rows": 3960, "validated_evaluation_rows": 2475,
        "unavailable_evaluation_rows": 1485, "validated_metric_view_rows": 4950,
        "unavailable_metric_view_rows": 2970, "policy_blocks": 825,
        "independent_validations": 825, "zero_fit_resumes": 825,
        "population_inference": "not performed", "full_study_ready": False,
    }
    for name, expected in required_aggregate.items():
        if aggregate_receipt.get(name) != expected:
            raise ValueError(f"aggregate receipt mismatch: {name}")

    expected_operations = {
        "policy_block": 825,
        "saved_owner_inference": 4950,
        "replay_conformalization_update": 4950,
        "operational_metrics": 4950,
    }
    if dict(operation_counts) != expected_operations:
        raise ValueError(f"operation accounting mismatch: {dict(operation_counts)}")
    if len(helper_claims) != 312:
        raise ValueError(f"helper accepted-claim count changed: {len(helper_claims)}")

    native = summary[summary.support == "native"]
    result = {
        "version": VERSION,
        "status": "passed",
        "validated_utc": utc(),
        "accepted_policy_blocks": 825,
        "unique_accepted_blocks": len(seen_blocks),
        "accepted_evaluation_rows": 2475,
        "unique_accepted_evaluation_rows": int(metrics.evaluation_id.nunique()),
        "validated_metric_view_rows": len(metrics),
        "helper_accepted_blocks": len(helper_claims),
        "unavailable_candidates": 99,
        "unavailable_evaluation_rows": 1485,
        "unavailable_metric_view_rows": len(unavailable_metrics),
        "operation_counts": dict(operation_counts),
        "models_fitted": 0,
        "maximum_validation_absolute_difference": maximum_validation_difference,
        "raw_stage_bytes": raw_bytes,
        "coordinator_peak_scientific_rss_bytes": coordinator.get("peak_scientific_rss_bytes"),
        "minimum_free_disk_bytes": coordinator.get("minimum_free_disk_bytes"),
        "helper_orchestration_sha256": digest(HERE / "parallel_reverse_v1.py"),
        "protocol_sha256": digest(HERE / "PROTOCOL.json"),
        "scientific_source_sha256": SOURCE_HASH,
        "descriptive_native_detection_rate_range": [
            float(native.mean_detection_rate.min()), float(native.mean_detection_rate.max())],
        "descriptive_native_clean_workload_range": [
            float(native.mean_clean_workload.min()), float(native.mean_clean_workload.max())],
        "population_inference": "unavailable; folds, model seeds, catalogue seeds and support views are not independent population replicates",
        "full_study_ready": False,
        "validation_wall_seconds": time.perf_counter() - started,
        "aggregate_receipt_sha256": digest(ANALYSIS / "analysis_validation.json"),
        "supervisor_final_heartbeat_utc": supervisor.get("heartbeat_utc"),
    }
    atomic_json(HERE / "COMPLETION_VALIDATION.json", result)
    return result


def backup_sources() -> list[Path]:
    excluded_roots = {ROOT.resolve(), (OUTPUTS / "completion_supervisor_v1").resolve()}
    files: list[Path] = []
    for path in OUTPUTS.rglob("*"):
        if not path.is_file() or path.name.endswith(".lock") or ".tmp-" in path.name:
            continue
        resolved = path.resolve()
        if any(root == resolved or root in resolved.parents for root in excluded_roots):
            continue
        files.append(path)
    for path in HERE.iterdir():
        if path.is_file() and path.name not in {"DELIVERY_RECEIPT.json", "GITHUB_REMOTE_READBACK.json",
                                                "READBACK_MANIFEST.csv"}:
            files.append(path)
    unique = {path.resolve(): path for path in files}
    return sorted(unique.values(), key=lambda path: path.relative_to(REPO).as_posix())


def source_manifest(files: Iterable[Path]) -> list[dict[str, Any]]:
    result = []
    for ordinal, path in enumerate(files, 1):
        stat = path.stat()
        if stat.st_size > PART_BUDGET:
            raise ValueError(f"backup member exceeds 80 MiB: {path}")
        result.append({"path": path.relative_to(REPO).as_posix(), "bytes": stat.st_size,
                       "mtime_ns": stat.st_mtime_ns, "sha256": digest(path)})
        if ordinal % 250 == 0:
            progress(current_phase="backup_manifest", backup_manifest_files=ordinal)
    return result


def manifest_groups(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    group: list[dict[str, Any]] = []
    size = 0
    for row in rows:
        if group and size + int(row["bytes"]) > PART_BUDGET:
            groups.append(group)
            group, size = [], 0
        group.append(row)
        size += int(row["bytes"])
    if group:
        groups.append(group)
    return groups


def write_archive(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    if partial.exists():
        raise ValueError(f"preserved unresolved partial backup archive: {partial}")
    names = [row["path"] for row in rows]
    if not path.exists():
        with zipfile.ZipFile(partial, "x", zipfile.ZIP_DEFLATED, compresslevel=6,
                             allowZip64=True) as packed:
            for row in rows:
                source = REPO / row["path"]
                info = zipfile.ZipInfo(row["path"], ZIP_STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                with source.open("rb") as incoming, packed.open(info, "w", force_zip64=True) as outgoing:
                    shutil.copyfileobj(incoming, outgoing, length=2**20)
        partial.replace(path)
    if path.stat().st_size > PART_LIMIT:
        raise ValueError(f"backup archive exceeds 95 MiB: {path}")
    with zipfile.ZipFile(path) as packed:
        if packed.namelist() != names:
            raise ValueError(f"backup archive membership changed: {path}")
        for row in rows:
            with packed.open(row["path"], "r") as stream:
                actual_hash, actual_bytes = sha256_stream(stream)
            if actual_hash != row["sha256"] or actual_bytes != row["bytes"]:
                raise ValueError(f"backup member verification failed: {row['path']}")
    return {"archive": path.name, "bytes": path.stat().st_size, "sha256": digest(path),
            "members": len(rows), "uncompressed_bytes": sum(int(row["bytes"]) for row in rows)}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def backup() -> dict[str, Any]:
    validation = read(HERE / "COMPLETION_VALIDATION.json")
    if validation.get("status") != "passed":
        raise ValueError("completion validation has not passed")
    if BACKUP.exists() and (BACKUP / "BACKUP_VERIFICATION.json").exists():
        existing = read(BACKUP / "BACKUP_VERIFICATION.json")
        if existing.get("status") == "passed":
            shutil.copy2(BACKUP / "BACKUP_VERIFICATION.json", HERE / "BACKUP_VERIFICATION.json")
            return existing
    BACKUP.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(BACKUP).free < DISK_FLOOR + 24 * 2**30:
        raise ValueError("D: lacks backup size plus the 8 GiB safety floor")
    started = time.perf_counter()
    files = backup_sources()
    rows = source_manifest(files)
    if not rows:
        raise ValueError("empty backup source scope")
    manifest_path = BACKUP / "external_file_manifest.csv"
    if manifest_path.exists():
        existing_rows = list(csv.DictReader(manifest_path.open("r", encoding="utf-8", newline="")))
        normalized = [{"path": row["path"], "bytes": str(row["bytes"]),
                       "mtime_ns": str(row["mtime_ns"]), "sha256": row["sha256"]} for row in rows]
        if existing_rows != normalized:
            raise ValueError("existing backup source manifest conflicts with live evidence")
    else:
        write_csv(manifest_path, rows)
    archive_rows = []
    groups = manifest_groups(rows)
    for number, group in enumerate(groups, 1):
        archive_rows.append(write_archive(BACKUP / f"operational_raw_part{number:03d}.zip", group))
        progress(current_phase="backup_archives", backup_archives_completed=number,
                 backup_archives_total=len(groups))
    archive_manifest_path = BACKUP / "external_archive_manifest.csv"
    write_csv(archive_manifest_path, archive_rows)

    # Re-hash every source after archive verification: a changing live source
    # can never be silently accepted as a stable backup.
    for ordinal, row in enumerate(rows, 1):
        source = REPO / row["path"]
        stat = source.stat()
        if (stat.st_size != row["bytes"] or stat.st_mtime_ns != row["mtime_ns"] or
                digest(source) != row["sha256"]):
            raise ValueError(f"backup source changed during packaging: {source}")
        if ordinal % 250 == 0:
            progress(current_phase="backup_source_stability", backup_sources_rechecked=ordinal)
    result = {
        "version": VERSION, "status": "passed", "verified_utc": utc(),
        "destination": str(BACKUP), "source_files": len(rows),
        "source_bytes": sum(int(row["bytes"]) for row in rows),
        "archives": len(archive_rows), "archive_bytes": sum(row["bytes"] for row in archive_rows),
        "maximum_archive_bytes": max(row["bytes"] for row in archive_rows),
        "source_manifest": str(manifest_path), "source_manifest_sha256": digest(manifest_path),
        "archive_manifest": str(archive_manifest_path),
        "archive_manifest_sha256": digest(archive_manifest_path),
        "source_stable_after_copy": True, "all_archive_members_byte_verified": True,
        "scientific_scope": "all operational005 causal-replay v2 blocks, validations, zero-fit resumes, ledgers, coordinator/supervisor/helper evidence, aggregate outputs and versioned support available before publication",
        "backup_wall_seconds": time.perf_counter() - started,
        "remaining_d_free_bytes": shutil.disk_usage(BACKUP).free,
        "historical_lineage": {
            "prerequisite_commit": BACKUP_PREREQUISITE,
            "recovery_repository": str(RECOVERY_REPO),
            "storage_relocation_record": r"D:\ConfoSenseStorage\STORAGE_LOCATION.json",
        },
    }
    atomic_json(BACKUP / "BACKUP_VERIFICATION.json", result)
    shutil.copy2(BACKUP / "BACKUP_VERIFICATION.json", HERE / "BACKUP_VERIFICATION.json")
    return result


def write_documents() -> None:
    validation = read(HERE / "COMPLETION_VALIDATION.json")
    backup_receipt = read(HERE / "BACKUP_VERIFICATION.json")
    low, high = validation["descriptive_native_detection_rate_range"]
    workload_low, workload_high = validation["descriptive_native_clean_workload_range"]
    report = f"""# Operational005 bounded causal-replay results

The frozen causal-replay extension completed **825/825 policy blocks** and **2,475/2,475 executable evaluation rows** covering 165 candidate definitions. Every block passed independent validation and an unchanged-artifact zero-fit resume. The reverse helper contributed {validation['helper_accepted_blocks']} disjoint accepted blocks and stopped at its declared convergence guard. Replay fitting remained zero.

The compact native-support candidate summaries have descriptive mean detection rates ranging from {low:.6g} to {high:.6g}, and mean clean-stream workloads ranging from {workload_low:.6g} to {workload_high:.6g} episodes per asset-day. These ranges are descriptive trade-off evidence, not a universal ranking or a population estimate; unfavorable and negative results remain in the published tables.

The other **99 candidate definitions / 1,485 evaluation rows** remain explicitly unavailable because their exact saved owners do not exist and fitting was forbidden. Native and common support are two reporting views of the same evaluations. Folds, model seeds, catalogue seeds, groups and stream rows are not treated as independent population replicates, so population intervals were not produced.

The verified external package contains {backup_receipt['source_files']:,} files and {backup_receipt['source_bytes']:,} source bytes in {backup_receipt['archives']} byte-verified archive parts under `{backup_receipt['destination']}`.
"""
    (HERE / "OPERATIONAL_REPORT.md").write_text(report, encoding="utf-8")
    index = f"""# Operational005 causal-replay evidence index

- [Frozen protocol](PROTOCOL.json), [candidate queue](evaluation_queue.csv), [candidate definitions](candidate_definitions.csv), and [owner inventory](owner_inventory.csv)
- [Parallel reverse helper](parallel_reverse_v1.py), [completion validator/delivery](completion_delivery_v1.py), and [guarded delivery supervisor](completion_supervisor_v1.py)
- [Independent completion validation](COMPLETION_VALIDATION.json) and [operational report](OPERATIONAL_REPORT.md)
- [Validated operational metrics](../../{ANALYSIS_REL}/operational_metrics.csv), [candidate summary](../../{ANALYSIS_REL}/candidate_summary.csv), [explicitly unavailable metrics](../../{ANALYSIS_REL}/unavailable_metrics.csv), and [trade-off figure](../../{ANALYSIS_REL}/operational_tradeoff.png)
- [Aggregate validation](../../{ANALYSIS_REL}/analysis_validation.json) and [aggregate report](../../{ANALYSIS_REL}/REPORT.md)
- [Verified external backup](BACKUP_VERIFICATION.json)
- [Commit-pinned HTTPS readback](GITHUB_REMOTE_READBACK.json) and [final delivery receipt](DELIVERY_RECEIPT.json)

The readback receipt verifies the earlier substantive commit, not itself. Raw replay evidence remains outside Git in the D: package recorded by the backup receipt. The separate operational policy execution is complete, but population inference remains unavailable under the recorded dependent design.
"""
    (HERE / "EVIDENCE_INDEX.md").write_text(index, encoding="utf-8")


def credentials_gate(paths: list[str]) -> None:
    # Assemble signatures so this scanner's own source does not contain and
    # consequently flag the credential byte sequences that it detects.
    signatures = (b"gh" + b"p_", b"github" + b"_pat_", b"AK" + b"IA",
                  b"-----BEGIN " + b"PRIVATE KEY-----",
                  b"-----BEGIN " + b"OPENSSH PRIVATE KEY-----")
    suspicious = []
    for relative in paths:
        path = REPO / relative
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf"}:
            continue
        payload = path.read_bytes()
        if any(signature in payload for signature in signatures):
            suspicious.append(relative)
    if suspicious:
        raise ValueError(f"credential-pattern gate failed for {suspicious}")


def temporary_index(base: str, paths: list[str]) -> tuple[dict[str, str], list[str]]:
    TEMP.mkdir(parents=True, exist_ok=True)
    index = TEMP / f"operational005-index-{uuid.uuid4().hex}"
    environment = dict(os.environ, GIT_INDEX_FILE=str(index))
    git("read-tree", base, env=environment)
    git("add", "--", *paths, env=environment)
    staged = git("diff", "--cached", "--name-only", base, env=environment).splitlines()
    unexpected = sorted(set(staged) - set(paths))
    if unexpected:
        raise ValueError(f"unexpected staged paths: {unexpected}")
    if not staged:
        raise ValueError("explicit publication allowlist produced no staged change")
    return environment, staged


def create_commit(base: str, paths: list[str], message: str) -> tuple[str, list[str], int]:
    environment, staged = temporary_index(base, paths)
    numstat = git("diff", "--cached", "--numstat", base, env=environment)
    staged_bytes = sum((REPO / path).stat().st_size for path in staged)
    event("staging_inspected", base=base, paths=staged, file_count=len(staged),
          bytes=staged_bytes, numstat=numstat.splitlines())
    tree = git("write-tree", env=environment)
    commit = git("commit-tree", tree, "-p", base, "-m", message, env=environment)
    Path(environment["GIT_INDEX_FILE"]).unlink(missing_ok=True)
    return commit, staged, staged_bytes


def remote_head() -> str | None:
    output = git("ls-remote", "--heads", "origin", TARGET_BRANCH)
    return output.split()[0] if output else None


def make_bundle(commit: str, prerequisite: str, label: str) -> dict[str, Any]:
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    short = commit[:9]
    backup_ref = f"refs/backup/operational005-causal-replay/{label}-{short}"
    git("update-ref", backup_ref, commit)
    revisions = git("rev-list", backup_ref, f"^{prerequisite}").splitlines()
    objects = git("rev-list", "--objects", backup_ref, f"^{prerequisite}").splitlines()
    if not revisions or not objects:
        raise ValueError("empty incremental Git backup revision set")
    bundle = ARCHIVES / f"operational_{label}_{short}_from_{prerequisite[:9]}.bundle"
    if bundle.exists():
        raise ValueError(f"preserve existing bundle instead of overwriting: {bundle}")
    git("bundle", "create", str(bundle), backup_ref, f"^{prerequisite}")
    heads = git("bundle", "list-heads", str(bundle))
    verify = git("bundle", "verify", str(bundle))
    advertised = [line for line in heads.splitlines() if line.endswith(" " + backup_ref)]
    if len(advertised) != 1 or advertised[0].split()[0] != commit:
        raise ValueError("incremental bundle advertised tip mismatch")
    return {"status": "passed", "bundle": str(bundle), "bundle_bytes": bundle.stat().st_size,
            "bundle_sha256": digest(bundle), "advertised_ref": backup_ref,
            "advertised_tip": commit, "prerequisite_commit": prerequisite,
            "revision_set_commits": len(revisions), "revision_set_object_lines": len(objects),
            "bundle_verify": "passed", "bundle_verify_output": verify}


def recovery_fetch(bundle_record: dict[str, Any], destination_ref: str) -> dict[str, Any]:
    if not RECOVERY_REPO.is_dir():
        raise ValueError("verified external recovery repository is absent")
    git_dir = RECOVERY_REPO / ".git"
    alternates = git_dir / "objects" / "info" / "alternates"
    if alternates.exists() and alternates.read_text(encoding="utf-8").strip():
        raise ValueError("external recovery repository unexpectedly uses object alternates")
    prior = subprocess.run(["git", "-C", str(RECOVERY_REPO), "cat-file", "-e",
                            f"{bundle_record['prerequisite_commit']}^{{commit}}"], check=False)
    if prior.returncode:
        raise ValueError("external recovery repository lacks the declared prerequisite")
    result = subprocess.run(["git", "-C", str(RECOVERY_REPO), "fetch", bundle_record["bundle"],
                             f"{bundle_record['advertised_ref']}:{destination_ref}"],
                            capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"external bundle recovery failed: {result.stderr[-4000:]}")
    restored = subprocess.check_output(["git", "-C", str(RECOVERY_REPO), "rev-parse", destination_ref],
                                       text=True).strip()
    if restored != bundle_record["advertised_tip"]:
        raise ValueError("external recovery restored the wrong commit")
    fsck = subprocess.run(["git", "-C", str(RECOVERY_REPO), "fsck", "--full"],
                          capture_output=True, text=True, check=False)
    if fsck.returncode:
        raise RuntimeError(f"external recovery fsck failed: {fsck.stderr[-4000:]}")
    return {"status": "passed", "repository": str(RECOVERY_REPO),
            "inputs": "verified external prerequisite repository plus the new incremental bundle only",
            "restored_commit": restored, "destination_ref": destination_ref,
            "object_alternates_present": False, "github_used_for_recovery": False,
            "full_fsck_exit": fsck.returncode}


def blob_oid(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()


def https_readback(commit: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scope = [REVIEW_REL, ANALYSIS_REL]
    lines = git("ls-tree", "-r", "--full-tree", commit, "--", *scope).splitlines()
    blobs = []
    for line in lines:
        metadata, path = line.split("\t", 1)
        mode, kind, oid = metadata.split()
        if kind == "blob":
            blobs.append((mode, oid, path))
    if not blobs:
        raise ValueError("empty commit-pinned readback scope")
    destination = ARCHIVES / f"https_readback_{commit[:9]}"
    if destination.exists():
        raise ValueError(f"preserve existing readback directory: {destination}")
    rows = []
    total = 0
    for ordinal, (mode, oid, path) in enumerate(blobs, 1):
        quoted = urllib.parse.quote(path, safe="/")
        url = f"https://raw.githubusercontent.com/jinchuntan/confosense/{commit}/{quoted}"
        payload = None
        last_error: Exception | None = None
        for attempt in range(6):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "ConfoSense-commit-pinned-readback"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = response.read()
                break
            except Exception as exc:  # transient publication propagation/network failure
                last_error = exc
                time.sleep(min(30, 2 ** attempt))
        if payload is None:
            raise RuntimeError(f"HTTPS readback failed for {path}: {last_error!r}")
        if blob_oid(payload) != oid:
            raise ValueError(f"commit-pinned blob mismatch: {path}")
        saved = destination / path
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(payload)
        rows.append({"path": path, "mode": mode, "git_blob_oid": oid,
                     "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
        total += len(payload)
        if ordinal % 10 == 0:
            progress(current_phase="https_readback", readback_files=ordinal,
                     readback_files_total=len(blobs))
    receipt = {"version": VERSION, "status": "passed", "verified_utc": utc(),
               "commit": commit,
               "base_url": f"https://raw.githubusercontent.com/jinchuntan/confosense/{commit}/",
               "scope": "every committed blob under the versioned operational review directory and compact operational analysis_v1 directory at the substantive commit",
               "scope_prefixes": scope, "files": len(rows), "bytes": total,
               "comparison": "downloaded byte streams were hashed as Git blobs and matched commit-pinned blob IDs",
               "readback_copy": str(destination),
               "receipt_self_verified": False}
    return receipt, rows


def publish() -> dict[str, Any]:
    final_science_gate()
    validation = read(HERE / "COMPLETION_VALIDATION.json")
    backup_receipt = read(HERE / "BACKUP_VERIFICATION.json")
    if validation.get("status") != "passed" or backup_receipt.get("status") != "passed":
        raise ValueError("publication gates have not passed")
    if git("rev-parse", "HEAD") != BASE_COMMIT:
        raise ValueError("working repository HEAD changed after delivery plan was frozen")
    if git("rev-parse", f"refs/heads/{TARGET_BRANCH}") != BACKUP_PREREQUISITE:
        raise ValueError("local review branch unexpectedly advanced")
    if remote_head() != BACKUP_PREREQUISITE:
        raise ValueError("remote review branch diverged; refusing overwrite")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", BACKUP_PREREQUISITE,
                               BASE_COMMIT], cwd=REPO, check=False)
    if ancestor.returncode:
        raise ValueError("publication base is not a descendant of the verified backup prerequisite")

    write_documents()
    manifest_rows = []
    for relative in SUBSTANTIVE_PATHS:
        if relative.endswith("PREPUBLICATION_MANIFEST.json"):
            continue
        path = REPO / relative
        if not path.is_file():
            raise ValueError(f"publication allowlist file absent: {relative}")
        manifest_rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)})
    atomic_json(HERE / "PREPUBLICATION_MANIFEST.json", {
        "version": VERSION, "created_utc": utc(), "base_commit": BASE_COMMIT,
        "target_branch": TARGET_BRANCH, "allowlist_files_excluding_this_manifest": manifest_rows,
        "allowlist_file_count_including_this_manifest": len(SUBSTANTIVE_PATHS),
        "bulk_output_directories_staged": False,
    })
    credentials_gate(SUBSTANTIVE_PATHS)
    substantive, staged, staged_bytes = create_commit(
        BASE_COMMIT, SUBSTANTIVE_PATHS, "Complete operational005 causal replay")
    git("update-ref", f"refs/heads/{TARGET_BRANCH}", substantive, BACKUP_PREREQUISITE)
    substantive_bundle = make_bundle(substantive, BACKUP_PREREQUISITE, "substantive")
    substantive_recovery = recovery_fetch(
        substantive_bundle, f"refs/recovery/operational-substantive-{substantive[:9]}")
    if remote_head() != BACKUP_PREREQUISITE:
        raise ValueError("remote review branch changed before substantive push")
    git("push", "origin", f"{substantive_bundle['advertised_ref']}:refs/heads/{TARGET_BRANCH}")
    if remote_head() != substantive:
        raise ValueError("remote substantive head verification failed")

    readback, rows = https_readback(substantive)
    atomic_json(HERE / "GITHUB_REMOTE_READBACK.json", readback)
    write_csv(HERE / "READBACK_MANIFEST.csv", rows)
    delivery_receipt = {
        "version": VERSION, "status": "passed", "created_utc": utc(),
        "branch": TARGET_BRANCH, "base_commit": BASE_COMMIT,
        "substantive_commit": substantive, "main_modified": False, "force_push": False,
        "staging": {"explicit_allowlist": SUBSTANTIVE_PATHS, "files": len(staged),
                    "bytes": staged_bytes, "bulk_outputs_staged": False},
        "completion_validation": validation,
        "raw_scientific_backup": backup_receipt,
        "git_backup": substantive_bundle,
        "external_recovery": substantive_recovery,
        "https_readback": readback,
        "receipt_scope": "this receipt records verification of the earlier substantive commit and does not claim to verify itself",
        "operational_scope_closed": True,
        "population_inference": "unavailable under the recorded dependent design",
    }
    atomic_json(HERE / "DELIVERY_RECEIPT.json", delivery_receipt)
    credentials_gate(RECEIPT_PATHS)
    receipt_commit, receipt_staged, receipt_bytes = create_commit(
        substantive, RECEIPT_PATHS, "Record operational005 delivery verification")
    git("update-ref", f"refs/heads/{TARGET_BRANCH}", receipt_commit, substantive)
    receipt_bundle = make_bundle(receipt_commit, substantive, "receipt")
    receipt_recovery = recovery_fetch(
        receipt_bundle, f"refs/recovery/operational-receipt-{receipt_commit[:9]}")
    if remote_head() != substantive:
        raise ValueError("remote review branch changed before receipt push")
    git("push", "origin", f"{receipt_bundle['advertised_ref']}:refs/heads/{TARGET_BRANCH}")
    if remote_head() != receipt_commit:
        raise ValueError("remote receipt head verification failed")
    final = {
        "version": VERSION, "status": "passed", "completed_utc": utc(),
        "branch": TARGET_BRANCH, "substantive_commit": substantive,
        "receipt_commit": receipt_commit, "remote_head": receipt_commit,
        "receipt_staged_files": receipt_staged, "receipt_staged_bytes": receipt_bytes,
        "substantive_bundle": substantive_bundle, "receipt_bundle": receipt_bundle,
        "substantive_external_recovery": substantive_recovery,
        "receipt_external_recovery": receipt_recovery,
        "https_readback": readback, "main_modified": False, "force_push": False,
    }
    atomic_json(ARCHIVES / "FINAL_DELIVERY.json", final)
    return final


def run() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    previous = read(PROGRESS) if PROGRESS.exists() else None
    try:
        descriptor = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"delivery lock exists: {LOCK}") from exc
    os.write(descriptor, json.dumps({"pid": os.getpid(), "created_utc": utc(),
                                     "version": VERSION}).encode("utf-8"))
    os.close(descriptor)
    progress(status="running", current_phase="receipt_revalidation", error=None,
             started_utc=utc(), base_commit=BASE_COMMIT, target_branch=TARGET_BRANCH,
             recovered_from_failure=previous if previous and previous.get("status") == "blocked" else None)
    event("delivery_started", pid=os.getpid())
    try:
        validation_path = HERE / "COMPLETION_VALIDATION.json"
        validation = read(validation_path)
        required_validation = {
            "status": "passed", "accepted_policy_blocks": 825,
            "unique_accepted_blocks": 825, "accepted_evaluation_rows": 2475,
            "unique_accepted_evaluation_rows": 2475, "models_fitted": 0,
            "scientific_source_sha256": SOURCE_HASH,
            "protocol_sha256": digest(HERE / "PROTOCOL.json"),
            "helper_orchestration_sha256": digest(HERE / "parallel_reverse_v1.py"),
            "aggregate_receipt_sha256": digest(ANALYSIS / "analysis_validation.json"),
        }
        mismatches = {key: (validation.get(key), expected)
                      for key, expected in required_validation.items()
                      if validation.get(key) != expected}
        if mismatches:
            raise ValueError(f"completed validation receipt identity mismatch: {mismatches}")
        event("completion_validation_receipt_reused", receipt=str(validation_path),
              receipt_sha256=digest(validation_path))
        progress(current_phase="verified_backup", completion_validation=validation)
        backup_receipt = backup()
        progress(current_phase="publication", backup=backup_receipt)
        final = publish()
        progress(status="complete", current_phase="complete", final_delivery=final,
                 completed_utc=utc(), error=None)
        event("delivery_complete", substantive_commit=final["substantive_commit"],
              receipt_commit=final["receipt_commit"])
        return 0
    except BaseException as exc:
        progress(status="blocked", error=repr(exc), blocked_utc=utc())
        event("delivery_blocked", error=repr(exc))
        raise
    finally:
        if LOCK.exists():
            try:
                owner = read(LOCK)
            except Exception:
                owner = {}
            if owner.get("pid") == os.getpid():
                LOCK.unlink()


if __name__ == "__main__":
    raise SystemExit(run())
