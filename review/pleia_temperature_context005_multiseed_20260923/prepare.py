"""Create new authorized manifests and a fresh, non-destructive launch record."""
from __future__ import annotations

import copy
import importlib.metadata
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from common import *


def volume(path: Path) -> dict[str, object]:
    path.mkdir(parents=True, exist_ok=True)
    resolved = path.resolve()
    usage = shutil.disk_usage(resolved)
    return {"path": str(resolved), "volume": resolved.drive, "free_bytes": usage.free}


def command(seed: int, action: str) -> list[str]:
    base = [PYTHON, "-B", "-m", "src.conditional_context005", action,
            "--manifest", str(manifest(seed)), "--design", str(design(seed)),
            "--out", str(run(seed)), "--readiness", str(design(seed) / "readiness.json")]
    if action == "readiness":
        base += ["--receipt", str(design(seed) / "readiness.json")]
    elif action == "resume":
        base += ["--receipt", str(resume(seed))]
    return base


def main() -> None:
    if git("branch", "--show-current") != BRANCH:
        raise ValueError("wrong execution review branch")
    if git("rev-parse", "main") != MAIN or source_digest() != SOURCE_HASH:
        raise ValueError("preserved main or scientific source changed")
    subprocess_result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ENTRY, "HEAD"], cwd=REPO
    )
    if subprocess_result.returncode:
        raise ValueError("execution branch does not descend from completed preflight")
    seed42 = read(SEED42_MANIFEST)
    if seed42["dataset"] != "pleia" or seed42["model_seed"] != 42:
        raise ValueError("seed-42 manifest identity mismatch")
    for seed in SEEDS:
        draft = read(draft_manifest(seed))
        if draft["execution_authorized"] or draft["authorization_kind"] != "preflight_only_not_authorized":
            raise ValueError("historical draft authorization changed")
        final = copy.deepcopy(draft)
        final["execution_authorized"] = True
        final["authorization_kind"] = "explicit_real_C_run"
        final["authorization_reference"] = "ConfoSense_Temperature_Seeds43-46_Execution_Prompt_2026-09-22.md"
        if manifest(seed).exists() and read(manifest(seed)) != final:
            raise ValueError(f"preserve differing final manifest: {manifest(seed)}")
        if not manifest(seed).exists():
            atomic(manifest(seed), final)
        for unused in (design(seed), run(seed), validation(seed), resume(seed), publication(seed)):
            if unused.exists():
                raise ValueError(f"new production path already exists: {unused}")

    BACKUP.mkdir(parents=True, exist_ok=True)
    measurements = {
        "working": volume(REPO),
        "package": volume(BASE),
        "temporary": volume(Path(tempfile.gettempdir())),
        "backup": volume(BACKUP),
    }
    usable = min(int(row["free_bytes"]) for row in measurements.values())
    launch = {
        "purpose": "fresh authorized launch capacity gate; historical preflight failure remains unchanged",
        "utc": now(), "required_free_bytes": REQUIRED_FREE_BYTES,
        "disk_floor_bytes": DISK_FLOOR_BYTES, "measurements": measurements,
        "minimum_usable_free_bytes": usable,
        "capacity_ready": usable >= REQUIRED_FREE_BYTES,
        "working_package_temporary_backup_share_volume": len({row["volume"] for row in measurements.values()}) == 1,
    }
    if not launch["capacity_ready"]:
        raise RuntimeError(f"capacity gate failed: {usable} < {REQUIRED_FREE_BYTES}")
    atomic(REVIEW / "LAUNCH_CAPACITY.json", launch)

    prior = {}
    for line in git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads").splitlines():
        ref, sha = line.split(" ", 1)
        if ref != f"refs/heads/{BRANCH}":
            prior[ref] = sha
    baseline = {
        "purpose": "authorized temperature seeds 43--46 production preservation baseline",
        "utc": now(), "entry_commit": ENTRY, "branch": BRANCH, "main": MAIN,
        "source_hash": source_digest(), "prior_heads": prior,
        "seed42_complete_sha256": digest(SEED42_RUN / "COMPLETE.json"),
        "seed42_operations_sha256": digest(SEED42_RUN / "operations.jsonl"),
        "seed42_protocol_sha256": digest(SEED42_DESIGN / "frozen_protocol.json"),
        "seed42_acceptance_decision_sha256": digest(SEED42_ACCEPTANCE / "ACCEPTANCE_DECISION.json"),
        "preflight_delivery_commit": ENTRY,
        "authorized_model_seeds": list(SEEDS), "reused_model_seed": 42,
    }
    atomic(REVIEW / "PRESERVATION_BASELINE.json", baseline)
    atomic(REVIEW / "USER_AUTHORIZATION.txt",
           "User authorized the bounded PLEIA-temperature fold-2/h1 model-seed 43--46 production batch, required validation, five-seed analysis, backup and review-branch publication in ConfoSense_Temperature_Seeds43-46_Execution_Prompt_2026-09-22.md.\n")
    commands = {}
    for seed in SEEDS:
        commands[str(seed)] = {action: command(seed, action) for action in ("freeze", "readiness", "run", "resume")}
        commands[str(seed)]["validate"] = [PYTHON, "-B", str(VALIDATOR),
            "--design", str(design(seed)), "--run", str(run(seed)), "--output", str(validation(seed)),
            "--expected-dataset", "pleia", "--expected-fold", "2", "--expected-horizon", "1", "--expected-seed", str(seed)]
    scope = {
        "version": "pleia_temperature_context005_multiseed_batch_v1",
        "dataset": "pleia", "outer_fold": 2, "horizon": 1,
        "model_seeds": list(SEEDS), "reused_seed": 42, "fault_slot_seeds": [42, 43],
        "contexts": 68, "schedules_per_seed": 2856,
        "controls": ["quantile_static", "cqr_static", "cqr_rolling", "persistence_static"],
        "rules": ["single_sample", "30min_3of3", "60min_4of6", "180min_3of18", "360min_4of36"],
        "channels": ["numerical_only", "availability_only", "combined"],
        "confidence_level": 0.95, "selection": "none", "source_hash": SOURCE_HASH,
        "execution_authorized": True, "authorization_kind": "explicit_real_C_run",
        "one_worker_at_a_time": True, "device": "cpu", "threads": 1,
        "expected_new_operations": {"cqr_wrapper_fit": 4, "quantile_estimator_fit": 12,
            "calibrator_conformalize": 8, "logical_conformalizations": 4, "persistence_radius": 4},
        "five_seed_analysis": {"draws": 2000, "rng_seed": 20240601,
            "block_length_original_contexts": 7, "average_seeds_within_context_stratum": True},
        "commands": commands,
    }
    atomic(REVIEW / "BATCH_SCOPE.json", scope)
    versions = {name: importlib.metadata.version(name) for name in
                ("numpy", "pandas", "scipy", "scikit-learn", "mapie", "xgboost", "torch")}
    print(json.dumps({"prepared": True, "capacity": launch, "packages": versions}, indent=2))


if __name__ == "__main__":
    main()
