"""Sequential durable coordinator for the authorized robustness completion."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import completion_runtime_v1 as R  # noqa: E402

VERSION = "robustness_contamination_recovery005_coordinator_v1"
ROOT = R.OUTPUT_ROOT / "completion_59_v1_coordinator"
PROGRESS = ROOT / "progress.json"
EVENTS = ROOT / "events.jsonl"
LOCK = ROOT / "coordinator.lock"
PYTHON = str(R.SCIENTIFIC_PYTHON)


def append_event(value: dict[str, Any]) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, default=str) + "\n"); handle.flush(); os.fsync(handle.fileno())


def write_progress(value: dict[str, Any]) -> None:
    value["updated_utc"] = R.utc(); R.atomic_json(PROGRESS, value)


def tasks():
    records = R.crosswalk_records()
    missing = [R.unit_key(x) for x in records if x["interval_owner_support"] != "exact_saved_owner"]
    remaining = [R.unit_key(x) for x in records if R.unit_key(x) != "bdg2_h1_f2_s42"]
    result = []
    result += [("owner_construct", key, HERE / "completion_v1.py", ["construct-owner", "--unit", key, "--resume"]) for key in missing]
    result += [("owner_registry", "all", HERE / "completion_v1.py", ["build-owner-registry"])]
    result += [("run", key, HERE / "completion_v1.py", ["run-unit", "--unit", key, "--resume"]) for key in remaining]
    result += [("validate", key, HERE / "completion_validate_v1.py", ["validate", "--unit", key]) for key in remaining]
    result += [("resume", key, HERE / "completion_validate_v1.py", ["resume", "--unit", key]) for key in remaining]
    result += [("aggregate", "all", HERE / "completion_delivery_v1.py", ["aggregate"])]
    result += [("backup", "all", HERE / "completion_delivery_v1.py", ["backup"])]
    return result


def complete(phase: str, key: str) -> bool:
    try:
        if phase == "owner_construct":
            value = R.read(R.OWNER_ROOT / key / "owner_result.json")
            return value["status"] == "complete" and R.digest(R.REPO / value["owner_path"]) == value["owner_sha256"]
        if phase == "owner_registry":
            value = R.read(R.REGISTRY); return value["units"] == 8 and value["quantile_estimator_fits"] == 24
        if phase == "run":
            manifest = R.read(R.FULL_ROOT / "checkpoint_manifest.json")
            unit = R.FULL_ROOT / "units" / key; marker = R.read(unit / "COMPLETE.json")
            if marker["spec_hash"] != manifest["spec_hash"]: return False
            return all((unit / name).is_file() and R.digest(unit / name) == expected
                       for name, expected in marker["hashes"].items())
        if phase == "validate":
            value = R.read(R.FULL_ROOT / "validation_v1" / key / "validation.json")
            return value["status"] == "passed" and value["checkpoint_complete_sha256"] == R.digest(R.FULL_ROOT / "units" / key / "COMPLETE.json")
        if phase == "resume":
            value = R.read(R.FULL_ROOT / "resume_v1" / key / "resume.json")
            return value["status"] == "passed" and value["checkpoint_complete_sha256_after"] == R.digest(R.FULL_ROOT / "units" / key / "COMPLETE.json")
        if phase == "aggregate": return R.read(HERE / "COMPLETION_RESULT.json")["status"] == "passed"
        if phase == "backup": return R.read(Path(r"C:\Users\nigel\ConfoSenseBackups\robustness_contamination_recovery005_20260928\completion_v1\BACKUP_RECEIPT.json"))["status"] == "passed"
    except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError):
        return False
    return False


def run(run_token: str) -> int:
    R.completion_protocol(); ROOT.mkdir(parents=True, exist_ok=True)
    try:
        handle = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise RuntimeError(f"coordinator identity lock already exists: {LOCK}")
    os.write(handle, json.dumps({"pid": os.getpid(), "created_utc": R.utc(), "command": sys.argv,
                                "run_token": run_token}).encode()); os.close(handle)
    queue = tasks(); state = {
        "version": VERSION, "run_token": run_token, "status": "running", "coordinator_pid": os.getpid(),
        "coordinator_created_utc": R.utc(), "total_tasks": len(queue), "completed_tasks": 0,
        "accepted_units": 1, "accepted_cells": 15, "current_phase": "preflight",
        "current_unit": None, "scientific_progress_utc": None, "worker": None,
    }
    write_progress(state); append_event({"utc": R.utc(), "event": "coordinator_started", "pid": os.getpid()})
    try:
        for ordinal, (phase, key, script, arguments) in enumerate(queue, start=1):
            if complete(phase, key):
                state["completed_tasks"] += 1
                if phase == "run":
                    state["accepted_units"] += 1; state["accepted_cells"] += 15
                continue
            while True:
                if (ROOT / "PAUSE_REQUESTED").exists():
                    state.update(status="paused_at_safe_boundary", current_phase=phase, current_unit=key, worker=None)
                    write_progress(state); append_event({"utc": R.utc(), "event": "pause_reached", "phase": phase, "unit": key})
                    return 20
                try:
                    gate = R.resource_gate(f"coordinator_pre_{phase}")
                    break
                except RuntimeError as exc:
                    state.update(status="waiting_resource_gate", current_phase=phase, current_unit=key,
                                 worker=None, resource_error=str(exc), resource_snapshot=R.resources())
                    write_progress(state); append_event({"utc": R.utc(), "event": "resource_wait", "phase": phase, "unit": key, "error": str(exc)})
                    time.sleep(120)
            command = [PYTHON, "-u", str(script), *arguments]
            attempt = ROOT / "attempts" / f"{ordinal:04d}_{phase}_{key}"
            attempt.mkdir(parents=True, exist_ok=False)
            (attempt / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
            stdout = (attempt / "stdout.log").open("w", encoding="utf-8")
            stderr = (attempt / "stderr.log").open("w", encoding="utf-8")
            process = subprocess.Popen(command, cwd=R.REPO, stdout=stdout, stderr=stderr)
            state.update(status="running", current_phase=phase, current_unit=key,
                         worker={"pid": process.pid, "created_utc": R.utc(), "executable": PYTHON,
                                 "command": command, "attempt": attempt.relative_to(R.REPO).as_posix()},
                         resource_snapshot=gate)
            write_progress(state); append_event({"utc": R.utc(), "event": "worker_started", "phase": phase, "unit": key, "pid": process.pid})
            while process.poll() is None:
                state["worker"]["last_observed_alive_utc"] = R.utc(); write_progress(state); time.sleep(10)
            stdout.close(); stderr.close(); code = process.returncode
            append_event({"utc": R.utc(), "event": "worker_exited", "phase": phase, "unit": key, "pid": process.pid, "exit_code": code})
            if code != 0 or not complete(phase, key):
                state.update(status="blocked", current_phase=phase, current_unit=key, worker=None,
                             error=f"worker exit {code}; completion evidence absent or invalid",
                             failed_attempt=attempt.relative_to(R.REPO).as_posix())
                write_progress(state); return int(code or 1)
            state["completed_tasks"] += 1; state["scientific_progress_utc"] = R.utc(); state["worker"] = None
            if phase == "run": state["accepted_units"] += 1; state["accepted_cells"] += 15
            write_progress(state)
        state.update(status="complete", current_phase="complete", current_unit=None, worker=None,
                     accepted_units=60, accepted_cells=900, completed_utc=R.utc())
        write_progress(state); append_event({"utc": R.utc(), "event": "coordinator_complete"}); return 0
    finally:
        if LOCK.exists(): LOCK.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--run-token", required=True)
    raise SystemExit(run(parser.parse_args().run_token))
