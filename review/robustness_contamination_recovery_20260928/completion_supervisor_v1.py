"""120-second identity-checked supervisor for robustness completion v1."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SMART = HERE.parents[1] / "smart_building_conformal"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(SMART))
import completion_v1 as C  # noqa: E402
import robustness_saved_owner_v1 as A  # noqa: E402

VERSION = "robustness_contamination_recovery005_supervisor_v1"
ROOT = C.OUTPUT_ROOT / "completion_59_v1_supervisor"
STATUS = ROOT / "status.json"
EVENTS = ROOT / "events.jsonl"
LOCK = ROOT / "supervisor.lock"


def process_identity(pid: int):
    script = (
        f"$p=Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\" -ErrorAction SilentlyContinue;"
        "if($null -eq $p){'null'}else{$p|Select-Object ProcessId,CreationDate,ExecutablePath,CommandLine|ConvertTo-Json -Compress}"
    )
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", script],
                            capture_output=True, text=True, timeout=30)
    text = result.stdout.strip()
    return None if not text or text == "null" else json.loads(text)


def append(value):
    ROOT.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, default=str) + "\n"); handle.flush(); os.fsync(handle.fileno())


def write(value):
    value["heartbeat_utc"] = A.utc(); A.atomic_json(STATUS, value)


def run() -> int:
    C.completion_protocol(); ROOT.mkdir(parents=True, exist_ok=True)
    try: handle = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError: raise RuntimeError(f"supervisor lock already exists: {LOCK}")
    os.write(handle, json.dumps({"pid": os.getpid(), "created_utc": A.utc(), "command": sys.argv}).encode()); os.close(handle)
    command = [str(C.SCIENTIFIC_PYTHON), "-u", str(HERE / "completion_coordinator_v1.py")]
    log = (ROOT / "coordinator.log").open("a", encoding="utf-8")
    process = subprocess.Popen(command, cwd=C.REPO, stdout=log, stderr=subprocess.STDOUT)
    state = {"version": VERSION, "status": "running", "supervisor_pid": os.getpid(),
             "supervisor_created_utc": A.utc(), "poll_seconds": 120,
             "supervisor_identity": process_identity(os.getpid()),
             "coordinator_launcher_pid": process.pid, "coordinator_command": command,
             "coordinator_created_utc": A.utc(), "coordinator_identity": None}
    append({"utc": A.utc(), "event": "supervisor_started", "pid": os.getpid(), "coordinator_pid": process.pid})
    try:
        while process.poll() is None:
            progress = C.OUTPUT_ROOT / "completion_59_v1_coordinator" / "progress.json"
            progress_value = A.read(progress) if progress.exists() else None
            actual_pid = int(progress_value["coordinator_pid"]) if progress_value else process.pid
            identity = process_identity(actual_pid)
            expected_script = str(HERE / "completion_coordinator_v1.py").lower()
            command_line = str((identity or {}).get("CommandLine", "")).lower()
            if identity is None or int(identity["ProcessId"]) != actual_pid or expected_script not in command_line:
                state.update(status="blocked_identity_mismatch", coordinator_identity=identity)
                write(state); append({"utc": A.utc(), "event": "identity_mismatch", "identity": identity})
                return 2
            state["coordinator_pid"] = actual_pid; state["coordinator_identity"] = identity
            state["progress"] = progress_value
            state["resource_snapshot"] = A.resources(); write(state)
            time.sleep(120)
        code = process.returncode; log.flush()
        progress = C.OUTPUT_ROOT / "completion_59_v1_coordinator" / "progress.json"
        state.update(status="complete" if code == 0 else ("paused" if code == 20 else "blocked"),
                     coordinator_exit_code=code, coordinator_identity=None,
                     progress=A.read(progress) if progress.exists() else None,
                     completed_utc=A.utc())
        write(state); append({"utc": A.utc(), "event": "supervisor_finished", "exit_code": code})
        return code
    finally:
        log.close()
        if LOCK.exists(): LOCK.unlink()


if __name__ == "__main__": raise SystemExit(run())
