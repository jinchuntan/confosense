"""Create draft manifests and preservation/capacity evidence; never fit or run."""
from __future__ import annotations

import copy
import json
import os
import platform
import shutil
import subprocess

from common import *
from src.intervals005_common import memory_snapshot, packages, source_digest


EXPECTED_REFS = {
    "main": MAIN,
    "review/pleia-temperature-context005-pilot-20260918": "571408be0b51e81c6987306a292afc7fcae2ff94",
    "review/pleia-temperature-context005-validation-audit-20260919": "e52a3ba6b94996f51300af523f898207162cac79",
    "review/pleia-temperature-context005-validated-acceptance-20260921": ENTRY,
    "review/pleia-energy-context005-multiseed-20260915": "80df3579dfe68ccf2c0d406c21c0fec967ff2b41",
}


def directory_size(root: Path) -> tuple[int, int]:
    total = count = 0
    stack = [root]
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    stat = entry.stat()
                    total += stat.st_size
                    count += 1
    return total, count


def workers() -> list[dict[str, object]]:
    command = "Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" | Select-Object ProcessId,ParentProcessId,CreationDate,Name,CommandLine | ConvertTo-Json -Compress"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, check=True)
    if not result.stdout.strip():
        return []
    rows = json.loads(result.stdout)
    if isinstance(rows, dict):
        rows = [rows]
    found = []
    needles = ("pleia_f2_s43_C_v1", "pleia_f2_s44_C_v1", "pleia_f2_s45_C_v1", "pleia_f2_s46_C_v1")
    for row in rows:
        text = row.get("CommandLine") or ""
        if any(needle in text for needle in needles):
            found.append(row)
    return found


def main() -> None:
    if git("branch", "--show-current") != BRANCH:
        raise ValueError("wrong preflight review branch")
    if git("rev-parse", "HEAD") != ENTRY:
        raise ValueError("preflight preparation must begin at accepted delivery head")
    refs = {name: git("rev-parse", name) for name in EXPECTED_REFS}
    if refs != EXPECTED_REFS:
        raise ValueError(f"historical reference moved: {refs}")
    if source_digest() != SOURCE_HASH:
        raise ValueError("frozen scientific source digest changed")

    protocol = read(SEED42_DESIGN / "frozen_protocol.json")
    if packages() != protocol["packages"]:
        raise ValueError("installed packages differ from the accepted frozen protocol")
    seed42 = read(SEED42_MANIFEST)
    if seed42["dataset"] != "pleia" or seed42["model_seed"] != 42:
        raise ValueError("unexpected seed-42 temperature manifest")

    for seed in SEEDS:
        if proposed_run(seed).exists():
            raise ValueError(f"proposed production run path already exists: {proposed_run(seed)}")
        draft = copy.deepcopy(seed42)
        draft.update(model_seed=seed, execution_authorized=False,
                     authorization_kind="preflight_only_not_authorized", unit_key=key(seed))
        write_json(manifest(seed), draft)

    raw_bytes, raw_files = directory_size(SEED42_RUN)
    package = read(REPO / "review" / "pleia_temperature_context005_pilot_20260918" / "TEMPERATURE_RAW_PACKAGE_VALIDATION.json")
    working = shutil.disk_usage(REPO)
    backup = shutil.disk_usage(BACKUP.parent)
    retained_raw = 4 * raw_bytes
    packaged = 4 * int(package["total_part_bytes"])
    backup_objects = packaged
    restore_scratch = raw_bytes + int(package["total_part_bytes"])
    temporary_peak = int(package["total_part_bytes"])
    projected_incremental = retained_raw + packaged + backup_objects + restore_scratch + temporary_peak
    required_before_launch = projected_incremental + 8 * 2**30
    memory = memory_snapshot()
    capacity = {
        "utc": utc(), "working_volume": str(REPO.drive), "backup_volume": str(BACKUP.drive),
        "working_and_backup_share_volume": REPO.drive.lower() == BACKUP.drive.lower(),
        "working_free_bytes": working.free, "backup_free_bytes": backup.free,
        "local_compute": {"platform": platform.platform(), "cpu_logical_count": os.cpu_count(), "available_ram_bytes": memory["available_ram_bytes"], "physical_ram_bytes": memory["physical_ram_bytes"], "launch_ram_reference_bytes": 3 * 2**30, "launch_ram_reference_met": memory["available_ram_bytes"] >= 3 * 2**30},
        "engine_disk_floor_bytes": 8 * 2**30,
        "seed42_raw_run": {"files": raw_files, "bytes": raw_bytes},
        "seed42_packaged_raw_bytes": int(package["total_part_bytes"]),
        "projection": {
            "four_retained_raw_runs_bytes": retained_raw,
            "four_packaged_raw_sets_bytes": packaged,
            "external_backup_objects_bytes": backup_objects,
            "one_restore_test_scratch_bytes": restore_scratch,
            "one_package_temporary_peak_bytes": temporary_peak,
            "incremental_bytes": projected_incremental,
            "required_free_before_launch_including_8GiB_floor": required_before_launch,
            "current_deficit_bytes": max(0, required_before_launch - working.free),
        },
        "capacity_ready": bool(working.free >= required_before_launch and backup.free >= required_before_launch),
        "note": "Planning projection; revise from measured new-unit phases after execution authorization. Working and backup paths currently share one volume.",
    }
    write_json(REVIEW / "RESOURCE_BUDGET.json", capacity)

    status = git("status", "--porcelain=v1", "--untracked-files=normal").splitlines()
    grouped: dict[str, int] = {}
    for entry in status:
        grouped[entry[:2]] = grouped.get(entry[:2], 0) + 1
    complete = read(SEED42_RUN / "COMPLETE.json")
    owner = read(SEED42_RUN / "stages" / "controls" / "identity.json")
    baseline = {
        "purpose": "bounded preservation baseline before temperature seeds 43--46 zero-fit preflight",
        "utc": utc(), "branch": BRANCH, "entry_commit": ENTRY, "prior_heads": refs,
        "source_digest": source_digest(), "packages": packages(),
        "targeted_source_protocol_diff_from_entry": git("diff", "--name-only", ENTRY, "--", "smart_building_conformal/src", "smart_building_conformal/protocols"),
        "working_status_group_counts": grouped,
        "matching_workers": workers(),
        "proposed_run_paths_absent": {key(seed): not proposed_run(seed).exists() for seed in SEEDS},
        "seed42": {
            "complete_sha256": sha256(SEED42_RUN / "COMPLETE.json"),
            "declared_files": len(complete["files"]), "raw_files": raw_files, "raw_bytes": raw_bytes,
            "operations_sha256": sha256(SEED42_RUN / "operations.jsonl"),
            "operations_bytes": (SEED42_RUN / "operations.jsonl").stat().st_size,
            "protocol_sha256": sha256(SEED42_DESIGN / "frozen_protocol.json"),
            "owner_identity_sha256": sha256(SEED42_RUN / "stages" / "controls" / "identity.json"),
            "controls_sha256": sha256(SEED42_RUN / "stages" / "controls" / "controls.pkl"),
            "owner_identity": owner,
        },
        "authorization": {"experiments": False, "full_validation": False, "five_seed_analysis": False, "focused_no_fit_tests": True},
    }
    write_json(REVIEW / "PRESERVATION_BASELINE.json", baseline)

    commands = {
        "status": "future_commands_only_not_run",
        "required_prior_action": "Create new final authorized manifests and final frozen protocols after explicit user authorization; never edit these draft manifests in place.",
        "one_worker_at_a_time": True, "threads": 1, "device": "cpu",
        "per_seed_template": {
            "freeze": [PYTHON, "-B", "-m", "src.conditional_context005", "freeze", "--manifest", "<FINAL_AUTHORIZED_MANIFEST>", "--design", "<FINAL_DESIGN>"],
            "readiness": [PYTHON, "-B", "-m", "src.conditional_context005", "readiness", "--design", "<FINAL_DESIGN>", "--receipt", "<FINAL_DESIGN>/readiness.json"],
            "run": [PYTHON, "-B", "-m", "src.conditional_context005", "run", "--manifest", "<FINAL_AUTHORIZED_MANIFEST>", "--design", "<FINAL_DESIGN>", "--out", "<RUN>", "--readiness", "<FINAL_DESIGN>/readiness.json"],
            "resume_incomplete": [PYTHON, "-B", "-m", "src.conditional_context005", "run", "--manifest", "<FINAL_AUTHORIZED_MANIFEST>", "--design", "<FINAL_DESIGN>", "--out", "<RUN>", "--readiness", "<FINAL_DESIGN>/readiness.json", "--resume-incomplete"],
            "amended_full_validation": [PYTHON, "-B", str(REVIEW / "candidate_validate_v2.py"), "--design", "<FINAL_DESIGN>", "--run", "<RUN>", "--output", "<NEW_VALIDATION_OUTPUT>", "--expected-dataset", "pleia", "--expected-fold", "2", "--expected-horizon", "1", "--expected-seed", "<SEED>"],
            "completed_zero_fit_resume": [PYTHON, "-B", "-m", "src.conditional_context005", "resume", "--design", "<FINAL_DESIGN>", "--out", "<RUN>", "--readiness", "<FINAL_DESIGN>/readiness.json", "--receipt", "<NEW_RESUME_RECEIPT>"],
        },
        "monitoring": "Record the actual worker PID/family, CPU, RSS, durable stage journal, exit status and per-phase elapsed time; silence alone is not inactivity.",
        "restart": "Resume only the exact matching seed unit after protocol, manifest, owner and checkpoint identity checks; preserve successful stages and never reuse another seed's owner.",
        "aggregation": {"seeds": list(ALL_SEEDS), "draws": 2000, "rng_seed": 20240601, "block_length_original_contexts": 7,
                        "method": "average seeds within original context/stratum, pair controls on the same contexts, then use existing chronological fold/segment blocks and support/degeneracy rules", "authorized_now": False},
    }
    write_json(REVIEW / "FUTURE_COMMANDS.json", commands)
    print({"prepared": True, "seeds": SEEDS, "capacity_ready": capacity["capacity_ready"], "models_fitted": 0})


if __name__ == "__main__":
    main()
