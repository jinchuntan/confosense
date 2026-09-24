"""Verified external package of new raw runs and non-Git execution evidence."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path

from adapter import HERE, REPO, SMART, bundle_paths, digest, frame, read, tree
from aggregate import COORDINATOR, verify_new
from src.intervals005_common import Operations, atomic

BACKUP = Path("C:/Users/nigel/ConfoSenseBackups/matched_intervals_seasonal005_completion_20260924")
PACKAGES = SMART / "outputs/matched_intervals005/completion_52_v1_packages"
SUPERVISOR = SMART / "outputs/matched_intervals005/completion_52_v1_supervisor"
PART_BUDGET = 80 * 2**20
PART_LIMIT = 95 * 2**20
DISK_FLOOR = 8 * 2**30
STAMP = (2026, 9, 24, 0, 0, 0)


def sha_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def groups(files: list[Path]) -> list[list[Path]]:
    result, part, size = [], [], 0
    for path in files:
        length = path.stat().st_size
        if length > PART_BUDGET:
            raise ValueError(f"oversize individual evidence file: {path}")
        if part and size + length > PART_BUDGET:
            result.append(part)
            part, size = [], 0
        part.append(path)
        size += length
    if part:
        result.append(part)
    return result


def archive(name: str, files: list[Path], member_rows: list[dict], archive_rows: list[dict]) -> None:
    destination = BACKUP / "raw_and_execution_v1" / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    paths = [path.relative_to(REPO).as_posix() for path in files]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate backup member")
    if not destination.exists():
        partial = destination.with_suffix(destination.suffix + ".partial")
        if partial.exists():
            raise ValueError(f"unresolved partial archive: {partial}")
        with zipfile.ZipFile(partial, "x", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as packed:
            for path, relative in zip(files, paths):
                info = zipfile.ZipInfo(relative, STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                packed.writestr(info, path.read_bytes(), compresslevel=6)
        partial.replace(destination)
    if destination.stat().st_size >= PART_LIMIT:
        raise ValueError(f"backup part exceeds established 95 MiB limit: {destination}")
    with zipfile.ZipFile(destination) as packed:
        if packed.namelist() != paths:
            raise ValueError(f"backup member list changed: {destination}")
        for path, relative in zip(files, paths):
            saved = packed.read(relative)
            expected = digest(path)
            if len(saved) != path.stat().st_size or sha_bytes(saved) != expected:
                raise ValueError(f"archive/source byte mismatch: {relative}")
            member_rows.append(dict(archive=name, path=relative, bytes=len(saved), sha256=expected))
    archive_rows.append(dict(archive=name, bytes=destination.stat().st_size,
                             sha256=digest(destination), members=len(files),
                             uncompressed_bytes=sum(path.stat().st_size for path in files)))


def run() -> None:
    started = time.monotonic()
    cpu_started = time.process_time()
    if (PACKAGES / "external_backup_validation.json").exists():
        raise ValueError("backup already sealed; preserve it")
    scope = frame(HERE / "remaining_scope.csv")
    if len(scope) != 52:
        raise ValueError("scope changed")
    manifest_rows, archive_rows = [], []
    designs, runs = [], []
    prerequisite_rows = []
    for row in scope.itertuples(index=False):
        key = (str(row.dataset), int(row.outer_fold), int(row.model_seed))
        design, output = bundle_paths(*key)
        verify_new(*key)
        current = tree(output)
        marker = read(output / "COMPLETE.json")
        current.pop("COMPLETE.json")
        if current != marker["files"]:
            raise ValueError(f"scientific run changed before backup: {key}")
        designs.append(design)
        runs.append(output)
        protocol = read(design / "frozen_protocol.json")
        for horizon, reference in protocol["references"].items():
            owner = REPO / reference["owner_directory"] / "model.ubj"
            expected = reference["owner_hashes"]["model.ubj"]
            if digest(owner) != expected:
                raise ValueError(f"forecasting prerequisite changed: {owner}")
            prerequisite_rows.append(dict(
                dataset=key[0], outer_fold=key[1], model_seed=key[2], horizon=int(horizon),
                owner=owner.relative_to(REPO).as_posix(), owner_sha256=expected,
                owner_run=reference["run"], run_tree_sha256=reference["run_file_tree_hash"],
                original_protocol=reference["original_protocol"],
                original_protocol_sha256=reference["original_protocol_hash"],
                historical_source_sha256=reference["source_hash"],
                historical_reuse=reference["historical_reuse"]))
    if len(prerequisite_rows) != 170 or len({(r["dataset"], r["outer_fold"], r["model_seed"], r["horizon"]) for r in prerequisite_rows}) != 170:
        raise ValueError("forecasting prerequisite scope changed")
    prior = read(Path("C:/Users/nigel/ConfoSenseBackups/matched_forecasting005_completion_20260923/FINAL_DELIVERY_BUNDLE.json"))
    if not prior["passed"] or not prior["external_only_restore_verified"] or prior["commit"] != "0c57f73618552514d41c6b78c631bd575beeebbc":
        raise ValueError("verified external forecasting base unavailable")
    if digest(Path(prior["bundle"])) != prior["sha256"]:
        raise ValueError("forecasting base bundle bytes changed")
    forecast_backup = read(SMART / "outputs/matched_forecasting005/core_completion_125_v1_packages/external_backup_validation.json")
    if not forecast_backup["passed"] or forecast_backup["run_archives"] != 125 or not Path(forecast_backup["backup_root"]).is_dir():
        raise ValueError("verified external forecasting raw lineage unavailable")
    PACKAGES.mkdir(parents=True, exist_ok=True)
    prereq_path = PACKAGES / "forecasting_owner_prerequisites.csv"
    if prereq_path.exists():
        raise ValueError("prerequisite manifest already exists; preserve partial package attempt")
    with prereq_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(prerequisite_rows[0]))
        writer.writeheader()
        writer.writerows(prerequisite_rows)
    if shutil.disk_usage(BACKUP.parent).free < DISK_FLOOR + 4 * 2**30:
        raise ValueError("insufficient backup-volume safety capacity")
    for ordinal, output in enumerate(runs, 1):
        files = sorted((path for path in output.rglob("*") if path.is_file()),
                       key=lambda path: path.relative_to(REPO).as_posix())
        for number, part in enumerate(groups(files), 1):
            name = f"runs/{output.name}_part{number:02d}.zip"
            archive(name, part, manifest_rows, archive_rows)
        print(f"VERIFIED RAW BACKUP {ordinal}/52 {output.name}", flush=True)
    support = []
    for design in designs:
        support.extend(path for path in design.rglob("*") if path.is_file())
    support.extend(path for path in COORDINATOR.rglob("*") if path.is_file() and path.name != "coordinator.lock")
    support.extend(path for path in SUPERVISOR.rglob("*") if path.is_file() and path.name != "supervisor.lock")
    support.extend(path for path in HERE.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    support.append(prereq_path)
    support = sorted(set(support), key=lambda path: path.relative_to(REPO).as_posix())
    for number, part in enumerate(groups(support), 1):
        archive(f"support/support_part{number:02d}.zip", part, manifest_rows, archive_rows)
    with (PACKAGES / "external_file_manifest.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)
    with (PACKAGES / "external_archive_manifest.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(archive_rows[0]))
        writer.writeheader()
        writer.writerows(archive_rows)
    if len(set(row["path"] for row in manifest_rows)) != len(manifest_rows):
        raise ValueError("duplicate external backup path")
    for name in ("external_file_manifest.csv", "external_archive_manifest.csv"):
        source = PACKAGES / name
        destination = BACKUP / "raw_and_execution_v1" / name
        shutil.copy2(source, destination)
        if digest(source) != digest(destination):
            raise ValueError("external manifest copy changed")
    atomic(PACKAGES / "external_backup_validation.json", dict(
        passed=True, bundles=52, archives=len(archive_rows), members=len(manifest_rows),
        archive_bytes=sum(row["bytes"] for row in archive_rows),
        uncompressed_bytes=sum(row["uncompressed_bytes"] for row in archive_rows),
        maximum_archive_bytes=max(row["bytes"] for row in archive_rows),
        publication_limit_bytes=PART_LIMIT, backup_root=str(BACKUP),
        source_scope_sha256=digest(HERE / "remaining_scope.csv"),
        archive_manifest_sha256=digest(PACKAGES / "external_archive_manifest.csv"),
        file_manifest_sha256=digest(PACKAGES / "external_file_manifest.csv"),
        forecasting_owner_prerequisites=170,
        forecasting_owner_prerequisite_manifest_sha256=digest(prereq_path),
        verified_forecasting_base_commit=prior["commit"],
        verified_forecasting_base_bundle=prior["bundle"],
        verified_forecasting_base_bundle_sha256=prior["sha256"],
        remaining_free_bytes=shutil.disk_usage(BACKUP.parent).free,
        backup_wall_seconds=time.monotonic()-started,
        backup_process_cpu_seconds=time.process_time()-cpu_started,
        coverage="all 52 new run trees; all 52 designs; one coordinator attempts/receipts/progress tree; scoped review support files"))
    print(json.dumps(read(PACKAGES / "external_backup_validation.json"), indent=2), flush=True)


if __name__ == "__main__":
    with Operations(forbid=True):
        run()
