"""Back up the completed extension's scientific artifacts and verify the copy.

Additive and post-scientific: it reads the run root and writes zip archives
(stored, not recompressed) with a per-file manifest, then reopens every archive
member and compares its SHA-256 with the source file.  The science root is not
archived because every file in it is a pinned copy of an existing input listed
in SCIENCE_ROOT_MANIFEST.json.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import time
import zipfile
from pathlib import Path

from hc_common import HERE, RUN_ROOT, VERSION, atomic_json, digest, read, utc

BACKUP = Path(r"D:\ConfoSenseStorage\backups\operational005_high_coverage_extension_20261003\run_v1")
INCLUDED = ("owners", "units", "supervisor", "analysis_v1", "analysis_v1_superseded_r1_2", "quarantine", "fit_ledger.jsonl",
            "PILOT_VALIDATION.json", "SCIENCE_ROOT_MANIFEST.json")
PART_LIMIT = 80 * 2**20
STAMP = (2026, 10, 3, 0, 0, 0)


def source_files() -> list[Path]:
    files = []
    for name in INCLUDED:
        path = RUN_ROOT / name
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(p for p in sorted(path.rglob("*")) if p.is_file()
                         and not p.name.endswith(".lock") and ".tmp-" not in p.name)
    return files


def backup() -> dict:
    completion = read(RUN_ROOT / "analysis_v1" / "COMPLETION_VALIDATION.json")
    if not completion.get("passed"):
        raise ValueError("backup requires a passed completion validation")
    status = read(RUN_ROOT / "supervisor" / "status.json")
    if status.get("state") != "scientific_complete_delivery_pending":
        raise ValueError(f"supervisor has not released delivery: {status.get('state')}")
    if BACKUP.exists() and any(BACKUP.iterdir()):
        raise ValueError("backup destination already populated")
    BACKUP.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    files = source_files()
    records = [{"path": p.relative_to(RUN_ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": digest(p)} for p in files]
    parts, current, size = [], [], 0
    for record in records:
        if current and size + record["bytes"] > PART_LIMIT:
            parts.append(current)
            current, size = [], 0
        current.append(record)
        size += record["bytes"]
    if current:
        parts.append(current)
    archives = []
    for index, members in enumerate(parts, 1):
        name = f"hicov_run_part{index:03d}.zip"
        with zipfile.ZipFile(BACKUP / name, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
            for record in members:
                info = zipfile.ZipInfo(record["path"], STAMP)
                info.compress_type = zipfile.ZIP_STORED
                with (RUN_ROOT / record["path"]).open("rb") as source, archive.open(info, "w", force_zip64=True) as target:
                    shutil.copyfileobj(source, target, 2**20)
        archives.append({"archive": name, "bytes": (BACKUP / name).stat().st_size, "sha256": digest(BACKUP / name),
                         "members": len(members), "uncompressed_bytes": sum(r["bytes"] for r in members)})
    expected = {r["path"]: r["sha256"] for r in records}
    seen = {}
    for item in archives:
        with zipfile.ZipFile(BACKUP / item["archive"]) as archive:
            for info in archive.infolist():
                h = hashlib.sha256()
                with archive.open(info) as handle:
                    for block in iter(lambda: handle.read(2**20), b""):
                        h.update(block)
                seen[info.filename] = h.hexdigest()
    if seen != expected:
        raise ValueError("backup archive members differ from the source files")
    stable = all(digest(RUN_ROOT / r["path"]) == r["sha256"] for r in records)
    with (BACKUP / "external_file_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    with (BACKUP / "external_archive_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(archives[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(archives)
    result = {
        "version": VERSION, "status": "passed" if stable else "failed", "verified_utc": utc(),
        "source_root": str(RUN_ROOT), "destination": str(BACKUP),
        "source_files": len(records), "source_bytes": sum(r["bytes"] for r in records),
        "archives": len(archives), "archive_bytes": sum(a["bytes"] for a in archives),
        "source_manifest_sha256": digest(BACKUP / "external_file_manifest.csv"),
        "archive_manifest_sha256": digest(BACKUP / "external_archive_manifest.csv"),
        "all_archive_members_byte_verified": True, "source_stable_after_copy": stable,
        "included": list(INCLUDED),
        "excluded": "science_root (pinned copies of existing inputs; see SCIENCE_ROOT_MANIFEST.json)",
        "physical_disk_note": "the run root and this backup share the D: SSD; GitHub holds the compact results",
        "remaining_d_free_bytes": shutil.disk_usage(BACKUP).free,
        "backup_wall_seconds": time.perf_counter() - started,
        "completion_validation_sha256": digest(RUN_ROOT / "analysis_v1" / "COMPLETION_VALIDATION.json"),
    }
    atomic_json(BACKUP / "BACKUP_VERIFICATION.json", result)
    atomic_json(HERE / "BACKUP_VERIFICATION.json", result)
    if not stable:
        raise ValueError("source changed during backup")
    print(json.dumps({k: v for k, v in result.items() if k not in ("included",)}, indent=2))
    return result


def receipts() -> dict:
    """Copy compact owner receipts and summarise block validation and supervision."""
    from hc_common import BLOCKS_PER_UNIT, FOLDS, OWNERS, SEEDS, UNITS, csv_write, unit_name
    out = HERE / "receipts"
    rows = []
    for fold in FOLDS:
        for seed in SEEDS:
            unit = unit_name(fold, seed)
            for name in ("OWNER_MANIFEST.json", "OWNER_VALIDATION.json", "RESUME.json"):
                target = out / "owners" / unit / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(OWNERS / unit / name, target)
            for index in range(BLOCKS_PER_UNIT):
                stage = UNITS / unit / "blocks" / f"block_{index:03d}"
                identity = read(stage / "identity.json")
                frozen = read(UNITS / unit / "validation" / f"block_{index:03d}.json")
                extended = read(UNITS / unit / "validation" / f"block_{index:03d}.extended.json")
                resume = read(UNITS / unit / "resume" / f"block_{index:03d}.json")
                marker = read(stage / "COMPLETE.json")
                rows.append({
                    "unit": unit, "outer_fold": fold, "model_seed": seed, "block_index": index,
                    "method": identity["policy"]["method"], "level": identity["policy"]["level"],
                    "strategy": identity["policy"]["strategy"], "every": identity["policy"]["every"],
                    "window": identity["policy"]["window"], "candidate_ids": ";".join(identity["candidate_ids"]),
                    "owner_sha256": identity["owner"]["owner"]["sha256"],
                    "complete_sha256": digest(stage / "COMPLETE.json"), "block_bytes": sum(
                        (stage / name).stat().st_size for name in marker["files"]),
                    "elapsed_seconds": round(marker["elapsed_seconds"], 1),
                    "frozen_validator_passed": frozen["passed"], "frozen_checks": frozen["checks"],
                    "frozen_max_difference": frozen["maximum_absolute_difference"],
                    "extended_validator_passed": extended["passed"], "extended_metric_checks": extended["metric_checks"],
                    "extended_max_difference": extended["maximum_metric_absolute_difference"],
                    "held_insufficient_support_rows": sum(c.get("held_insufficient_score_or_rank_support", 0)
                                                          for c in extended["update_status_counts"].values()),
                    "zero_fit_resume_passed": resume["passed"], "resume_files_unchanged": resume["files_unchanged"],
                })
    csv_write(out / "BLOCK_VALIDATION_SUMMARY.csv", rows)
    shutil.copyfile(RUN_ROOT / "fit_ledger.jsonl", out / "fit_ledger.jsonl")
    events = [json.loads(line) for line in (RUN_ROOT / "supervisor" / "events.jsonl").read_text(encoding="utf-8").splitlines() if line]
    returned = [e for e in events if e["event"] == "task_returned"]
    durations = {}
    for e in returned:
        kind = e["task"].split("_bdg2")[0]
        durations.setdefault(kind, []).append(e["seconds"])
    status = read(RUN_ROOT / "supervisor" / "status.json")
    summary = {
        "version": VERSION, "utc": utc(), "events": len(events),
        "events_sha256": digest(RUN_ROOT / "supervisor" / "events.jsonl"),
        "supervisor_starts": sum(e["event"] == "supervisor_started" for e in events),
        "tasks_returned": len(returned), "nonzero_exits": sum(e["exit_code"] != 0 for e in returned),
        "retries_scheduled": sum(e["event"] == "retry_scheduled" for e in events),
        "blocked_events": [e for e in events if e["event"] == "blocked"],
        "resource_pauses": sum(e["event"] == "resource_pause" for e in events),
        "quarantine_events": sum(e["event"] == "quarantined_partials" for e in events),
        "task_seconds": {k: {"n": len(v), "mean": round(sum(v) / len(v), 1), "max": round(max(v), 1)}
                         for k, v in sorted(durations.items())},
        "peak_task_rss_bytes": max((e.get("peak_rss_bytes", 0) for e in returned), default=0),
        "final_state": status["state"], "minimum_available_ram_bytes_last_supervisor": status["minimum_available_ram_bytes"],
        "minimum_commit_available_bytes_last_supervisor": status["minimum_commit_available_bytes"],
        "minimum_free_disk_bytes_last_supervisor": status["minimum_free_disk_bytes"],
        "max_workers": status["control"]["max_workers"],
    }
    atomic_json(out / "SUPERVISOR_SUMMARY.json", summary)
    print(json.dumps({"blocks": len(rows), "owners": 15, **{k: summary[k] for k in ("nonzero_exits", "retries_scheduled")}}))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["backup", "receipts"])
    args = parser.parse_args()
    backup() if args.action == "backup" else receipts()
