"""Durable, strictly sequential coordinator for the authorized temperature batch."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import traceback

from common import *


LEGACY_DIR = REPO / "review" / "context_replay005_implementation_20260914"
sys.path.insert(0, str(LEGACY_DIR))
current_common = sys.modules.get("common")
common_spec = importlib.util.spec_from_file_location("context005_reviewed_common", LEGACY_DIR / "common.py")
legacy_common = importlib.util.module_from_spec(common_spec); common_spec.loader.exec_module(legacy_common)
sys.modules["common"] = legacy_common
spec = importlib.util.spec_from_file_location("context005_reviewed_coordinator", LEGACY_DIR / "coordinator.py")
reviewed = importlib.util.module_from_spec(spec); spec.loader.exec_module(reviewed)
if current_common is not None: sys.modules["common"] = current_common
else: sys.modules.pop("common", None)
Engine = reviewed.Engine
exclusive_lock = reviewed._legacy.exclusive_lock


def save_external(engine: Engine) -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    engine.save()
    atomic(BACKUP / "latest_progress.json", engine.state)
    lines = ["# Temperature seeds 43--46 durable progress", "", f"Updated UTC: {now()}.",
             f"Status: **{engine.state.get('status')}**.", "",
             "Restart the sole coordinator from the repository root:", "",
             "```powershell", f"& {PYTHON} -B {REVIEW / 'coordinator.py'}", "```", "",
             "The exclusive lock prevents duplicate coordinators. Passed tasks are reused; known failed tasks require evidence-based investigation.", ""]
    for task, row in engine.state.get("tasks", {}).items():
        lines.append(f"- {task}: {row.get('status')}; exit {row.get('exit_code')}; receipt `{row.get('logger_receipt', row.get('log'))}`.")
    if engine.state.get("failure"):
        lines += ["", "Failure: " + engine.state["failure"]]
    atomic(REVIEW / "PROGRESS_AND_RESTART.md", "\n".join(lines) + "\n")


def argv(seed: int, action: str) -> list[str]:
    if action == "validate":
        return [PYTHON, "-B", str(VALIDATOR), "--design", str(design(seed)), "--run", str(run(seed)),
                "--output", str(validation(seed)), "--expected-dataset", "pleia", "--expected-fold", "2",
                "--expected-horizon", "1", "--expected-seed", str(seed)]
    if action == "verify":
        return [PYTHON, "-B", str(REVIEW / "verify_unit.py"), "--seed", str(seed)]
    receipt = str(resume(seed)) if action == "resume" else str(design(seed) / "readiness.json")
    out = [PYTHON, "-B", "-m", "src.conditional_context005", action,
           "--manifest", str(manifest(seed)), "--design", str(design(seed)), "--out", str(run(seed)),
           "--readiness", str(design(seed) / "readiness.json"), "--receipt", receipt]
    if action == "run" and (run(seed) / "checkpoint_manifest.json").exists():
        out.append("--resume-incomplete")
    return out


def disk_gate(required: int = DISK_FLOOR_BYTES) -> int:
    paths = (REPO, BASE, BACKUP)
    free = min(shutil.disk_usage(path).free for path in paths)
    if free < required:
        raise RuntimeError(f"disk gate failed: {free} < {required}")
    return free


def main(freeze_only: bool = False) -> None:
    os.chdir(SMART); BACKUP.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(BACKUP / "coordinator.lock"):
        engine = Engine(BATCH, logger=REVIEW / "monitor_command.py", poll_seconds=5)
        try:
            if git("branch", "--show-current") != BRANCH or git("rev-parse", "main") != MAIN:
                raise ValueError("branch/main preservation failure")
            if source_digest() != SOURCE_HASH:
                raise ValueError("scientific source changed")
            subprocess.run([PYTHON, "-B", "-c", "import src.conditional_context005,src.context005_metrics"], cwd=SMART, check=True)
            engine.reconcile(); save_external(engine)
            for seed in SEEDS:
                if not design(seed).exists():
                    engine.phase(f"seed_{seed}/freeze", lambda folder, s=seed: argv(s, "freeze"))
                if not (design(seed) / "readiness.json").exists():
                    engine.phase(f"seed_{seed}/readiness", lambda folder, s=seed: argv(s, "readiness"))
                save_external(engine)
            engine.phase("batch/preflight", lambda folder: [PYTHON, "-B", str(REVIEW / "preflight.py")]); save_external(engine)
            if freeze_only:
                engine.state.update(status="frozen_no_fits", active=None, disk_free_bytes=disk_gate(REQUIRED_FREE_BYTES))
                save_external(engine); print("FOUR AUTHORIZED TEMPERATURE DESIGNS FROZEN; NO FITS", flush=True); return
            frozen = read(REVIEW / "FROZEN_BATCH_MANIFEST.json")
            evaluated = read(REVIEW / "EVALUATED_COMMIT.json")
            if frozen["models_fitted"] != 0 or frozen["source_hash"] != source_digest():
                raise ValueError("pre-fit batch pin mismatch")
            subprocess.run(["git", "merge-base", "--is-ancestor", evaluated["evaluated_commit"], "HEAD"], cwd=REPO, check=True)
            for seed in SEEDS:
                engine.state.update(status=f"seed_{seed}_running", current_seed=seed, disk_free_bytes=disk_gate())
                save_external(engine)
                engine.phase(f"seed_{seed}/run", lambda folder, s=seed: argv(s, "run")); save_external(engine)
                engine.phase(f"seed_{seed}/validate", lambda folder, s=seed: argv(s, "validate")); save_external(engine)
                engine.phase(f"seed_{seed}/resume", lambda folder, s=seed: argv(s, "resume")); save_external(engine)
                engine.phase(f"seed_{seed}/verify", lambda folder, s=seed: argv(s, "verify")); save_external(engine)
                verified = read(acceptance(seed))
                if not verified["passed"]:
                    raise ValueError(f"seed {seed} acceptance failed")
                engine.state.setdefault("units", {})[str(seed)] = {"status": "accepted", "receipt": str(acceptance(seed))}
                save_external(engine)
            for task, script in (("final/analyze", "analyze.py"), ("final/validate_aggregate", "validate_aggregate.py"),
                                 ("final/package_raw", "pack_evidence.py"), ("final/update_documents", "update_documents.py")):
                engine.phase(task, lambda folder, name=script: [PYTHON, "-B", str(REVIEW / name)]); save_external(engine)
            engine.state.update(status="science_and_evidence_complete", active=None, disk_free_bytes=disk_gate())
            save_external(engine)
            print("ALL FOUR TEMPERATURE SEEDS, VALIDATION, ANALYSIS AND PACKAGING COMPLETE", flush=True)
        except BaseException as exc:
            engine.state.update(status="failed", failure=str(exc), traceback=traceback.format_exc())
            save_external(engine); raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--freeze-only", action="store_true")
    main(parser.parse_args().freeze_only)
