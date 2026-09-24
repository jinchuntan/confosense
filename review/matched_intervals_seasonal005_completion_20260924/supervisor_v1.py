"""Durable 120-second supervisor for the bounded completion and delivery.

The supervisor never performs scientific work itself.  It identifies exact
process families, adopts a single matching coordinator/worker/finisher, and
launches only the already-authorized coordinator or guarded finisher.  It
keeps one atomic status file and one append-only event log.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SMART = REPO / "smart_building_conformal"
PYTHON = Path("C:/cfs_venv/Scripts/python.exe")
COORDINATOR = HERE / "coordinator.py"
FINALIZER = HERE / "finalize.py"
RECOVERY_GATE = HERE / "IMPORT_BOOTSTRAP_RECOVERY_V2.json"
ROOT = SMART / "outputs/matched_intervals005/completion_52_v1_supervisor"
STATUS = ROOT / "status.json"
EVENTS = ROOT / "events.jsonl"
LOCK = ROOT / "supervisor.lock"
STOP = ROOT / "STOP"
PROGRESS = SMART / "outputs/matched_intervals005/completion_52_v1_coordinator/progress.json"
PUBLICATION = HERE / "PUBLICATION_RECEIPT.json"
BACKUP = Path("C:/Users/nigel/ConfoSenseBackups/matched_intervals_seasonal005_completion_20260924")
DISK_FLOOR = 8 * 2**30
INTERVAL = 120
MANAGED: dict[str, subprocess.Popen] = {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def event(kind: str, **fields) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    row = {"utc": now(), "event": kind, **fields}
    with EVENTS.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    current = [part for part in environment.get("PYTHONPATH", "").split(os.pathsep) if part]
    smart = str(SMART.resolve())
    environment["PYTHONPATH"] = os.pathsep.join(
        [smart, *[part for part in current if Path(part).resolve() != SMART.resolve()]]
    )
    return environment


def process_rows() -> list[dict]:
    expression = (
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" | "
        "Select-Object @{n='pid';e={$_.ProcessId}},@{n='ppid';e={$_.ParentProcessId}},"
        "@{n='created';e={$_.CreationDate.ToUniversalTime().ToString('o')}},"
        "@{n='exe';e={$_.ExecutablePath}},@{n='command';e={$_.CommandLine}},"
        "@{n='cpu_100ns';e={[int64]$_.KernelModeTime+[int64]$_.UserModeTime}},"
        "@{n='working_set';e={[int64]$_.WorkingSetSize}},"
        "@{n='read_bytes';e={[int64]$_.ReadTransferCount}},"
        "@{n='write_bytes';e={[int64]$_.WriteTransferCount}} | "
        "ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", expression],
        capture_output=True, text=True, timeout=30, check=True,
    )
    if not result.stdout.strip():
        return []
    value = json.loads(result.stdout)
    return value if isinstance(value, list) else [value]


def normalized(value: str | None) -> str:
    return (value or "").replace("/", "\\").lower()


def process_families(rows: list[dict], script: Path, argument: str | None = None) -> list[dict]:
    needle = normalized(str(script.resolve()))
    selected = []
    for row in rows:
        command = normalized(row.get("command"))
        if needle in command and (argument is None or argument.lower() in command):
            selected.append(row)
    pids = {int(row["pid"]) for row in selected}
    roots = [row for row in selected if int(row.get("ppid") or 0) not in pids]
    families = []
    for root in roots:
        members, pending = [], [int(root["pid"])]
        while pending:
            parent = pending.pop()
            direct = [row for row in selected if int(row["pid"]) == parent or int(row.get("ppid") or 0) == parent]
            for row in direct:
                if int(row["pid"]) not in {int(item["pid"]) for item in members}:
                    members.append(row)
                    pending.append(int(row["pid"]))
        families.append({"root": root, "members": sorted(members, key=lambda x: int(x["pid"]))})
    return families


def failure_class(progress: dict) -> str | None:
    if progress.get("status") != "blocked":
        return None
    failure = str(progress.get("failure", "")).lower()
    trace = str(progress.get("traceback", "")).lower()
    joined = failure + "\n" + trace
    if ("modulenotfounderror" in joined and "no module named 'src'" in joined) or \
            "validate_decimal_rank_v1 failed" in joined:
        return "recoverable_import"
    if "validate" in joined or "validation" in joined or "identity mismatch" in joined:
        return "hard_validation"
    return "recorded_failure"


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def recovery_gate_ready() -> bool:
    if not RECOVERY_GATE.exists():
        return False
    gate = read(RECOVERY_GATE)
    validation = read(Path(gate["validation_receipt"]))
    resume = read(Path(gate["resume_receipt"]))
    return bool(
        gate.get("passed")
        and gate.get("preserved_validator_sha256") == sha256(HERE / "corrected_validator_v1.py")
        and gate.get("bootstrap_entrypoint_sha256") == sha256(HERE / "corrected_validator_v2.py")
        and validation.get("passed") and validation.get("models_fitted") == 0
        and validation.get("calibrators_fitted") == 0
        and validation.get("source_artifacts_unchanged")
        and resume.get("status") == "complete" and resume.get("models_fitted") == 0
        and resume.get("calibrators_fitted") == 0 and resume.get("all_run_files_unchanged")
    )


def choose_action(*, progress: dict, coordinator_count: int, worker_count: int,
                  finalizer_count: int, delivery_complete: bool, recovery_ready: bool,
                  retries: int, finalizer_started: bool, free_bytes: int) -> tuple[str, str]:
    if coordinator_count > 1 or worker_count > 1 or finalizer_count > 1:
        return "block", "duplicate matching process families"
    if free_bytes < DISK_FLOOR:
        return "block", f"free disk below 8 GiB floor: {free_bytes}"
    if delivery_complete:
        if finalizer_count == 1:
            return "finalizing", "delivery checks passed; waiting for guarded finisher exit"
        return "delivered", "scoped publication receipt is present after final bundle and push"
    if progress.get("status") == "science_validated" and progress.get("completed_bundles") == 52:
        if coordinator_count or worker_count:
            return "wait", "science complete while coordinator family exits"
        if finalizer_count == 1:
            return "finalizing", "adopted guarded finisher"
        if finalizer_started:
            return "block", "guarded finisher exited before delivery receipt"
        return "launch_finalizer", "all 52 bundles are scientifically validated"
    if coordinator_count == 1:
        return "running", "adopted matching coordinator"
    if worker_count == 1:
        return "block", "scientific worker exists without its coordinator"
    classification = failure_class(progress)
    if classification == "recoverable_import" and recovery_ready and retries < 2:
        return "launch_coordinator", "versioned import recovery gate passed"
    if classification:
        return "block", classification
    if progress.get("status") in {"running", "recovering"}:
        return "block", "unexpected coordinator absence requires checkpoint/ledger reconciliation"
    return "block", "coordinator is absent without a classified recoverable state"


def launch(script: Path, argument: str, label: str) -> dict:
    BACKUP.mkdir(parents=True, exist_ok=True)
    stdout_path = BACKUP / f"supervisor_{label}.stdout.log"
    stderr_path = BACKUP / f"supervisor_{label}.stderr.log"
    stdout = stdout_path.open("ab", buffering=0)
    stderr = stderr_path.open("ab", buffering=0)
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    process = subprocess.Popen(
        [str(PYTHON), "-B", str(script), argument], cwd=SMART,
        env=child_environment(), stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
        close_fds=True, creationflags=flags,
    )
    stdout.close()
    stderr.close()
    MANAGED[label] = process
    record = {
        "pid": process.pid,
        "created_utc": now(),
        "executable": str(PYTHON),
        "argv": [str(PYTHON), "-B", str(script), argument],
        "cwd": str(SMART),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }
    event("process_launched", label=label, process=record)
    return record


def compact_family(family: dict) -> dict:
    root = family["root"]
    members = family["members"]
    return {
        "root_pid": int(root["pid"]),
        "root_created": root.get("created"),
        "root_executable": root.get("exe"),
        "root_command": root.get("command"),
        "member_pids": [int(item["pid"]) for item in members],
        "cpu_seconds": sum(int(item.get("cpu_100ns") or 0) for item in members) / 10_000_000,
        "working_set_bytes": sum(int(item.get("working_set") or 0) for item in members),
        "read_bytes": sum(int(item.get("read_bytes") or 0) for item in members),
        "write_bytes": sum(int(item.get("write_bytes") or 0) for item in members),
    }


def log_observation(progress: dict) -> dict | None:
    active = progress.get("active") or {}
    candidate = active.get("log")
    if not candidate and progress.get("status") == "blocked":
        failure = str(progress.get("failure", ""))
        marker = failure.rfind(";")
        candidate = failure[marker + 1:].strip() if marker >= 0 else None
    if not candidate:
        return None
    path = Path(candidate)
    if not path.is_file():
        return {"path": str(path), "present": False}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {
        "path": str(path), "present": True, "bytes": path.stat().st_size,
        "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        "tail": lines[-8:],
        "interpretation": "quiet output or unchanged counters alone are not treated as a hang",
    }


def managed_exit_updates(previous: dict) -> dict:
    updates = dict(previous.get("managed_child_exits", {}))
    for label, process in list(MANAGED.items()):
        code = process.poll()
        if code is None:
            continue
        row = {"pid": process.pid, "exit_code": code, "observed_utc": now()}
        updates[label] = row
        event("managed_child_exit", label=label, **row)
        del MANAGED[label]
    return updates


def inspect(previous: dict) -> tuple[dict, str, str]:
    progress = read(PROGRESS)
    rows = process_rows()
    coordinators = process_families(rows, COORDINATOR, "--run")
    workers = process_families(rows, HERE / "adapter.py")
    finalizers = process_families(rows, FINALIZER)
    free = shutil.disk_usage(SMART).free
    recovery_ready = recovery_gate_ready()
    retries = int(previous.get("coordinator_launches", 0))
    action, reason = choose_action(
        progress=progress, coordinator_count=len(coordinators), worker_count=len(workers),
        finalizer_count=len(finalizers), delivery_complete=PUBLICATION.exists(),
        recovery_ready=recovery_ready, retries=retries,
        finalizer_started=bool(previous.get("finalizer_launched_utc")), free_bytes=free,
    )
    state_map = {
        "running": "running", "wait": "running", "launch_coordinator": "recovering",
        "finalizing": "finalizing", "launch_finalizer": "finalizing",
        "delivered": "delivered", "block": "blocked_needs_attention",
    }
    status = {
        "version": "matched_intervals_seasonal005_supervisor_v1",
        "state": state_map[action],
        "checked_utc": now(),
        "last_scientific_progress_utc": progress.get("updated_utc"),
        "reason": reason,
        "coordinator_launches": retries,
        "finalizer_launched_utc": previous.get("finalizer_launched_utc"),
        "progress": {
            key: progress.get(key) for key in
            ("status", "phase", "frozen_bundles", "completed_bundles", "remaining_bundles", "active", "failure")
        },
        "processes": {
            "supervisor": {"pid": os.getpid(), "executable": sys.executable,
                           "argv": sys.argv, "cwd": os.getcwd()},
            "coordinator_families": [compact_family(x) for x in coordinators],
            "worker_families": [compact_family(x) for x in workers],
            "finalizer_families": [compact_family(x) for x in finalizers],
        },
        "free_disk_bytes": free,
        "disk_floor_bytes": DISK_FLOOR,
        "observation_errors": int(previous.get("observation_errors", 0)),
        "managed_child_exits": managed_exit_updates(previous),
        "latest_log": log_observation(progress),
    }
    return status, action, reason


def cycle(previous: dict) -> dict:
    status, action, reason = inspect(previous)
    if action == "launch_coordinator":
        status["coordinator_launches"] += 1
        status["last_coordinator_launch"] = launch(COORDINATOR, "--run", "coordinator")
    elif action == "launch_finalizer":
        launched = launch(FINALIZER, "--run", "finalizer")
        status["finalizer_launched_utc"] = launched["created_utc"]
        status["last_finalizer_launch"] = launched
    previous_state = previous.get("state")
    atomic(STATUS, status)
    if status["state"] != previous_state:
        event("state_changed", previous=previous_state, state=status["state"], reason=reason)
        if status["state"] in {"blocked_needs_attention", "delivered"}:
            print(f"SUPERVISOR {status['state']}: {reason}", flush=True)
    else:
        event("heartbeat", state=status["state"], completed=status["progress"].get("completed_bundles"),
              phase=status["progress"].get("phase"))
    return status


def acquire_lock():
    ROOT.mkdir(parents=True, exist_ok=True)
    handle = LOCK.open("a+b")
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    try:
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        handle.close()
        raise RuntimeError("another supervisor holds the single-instance lock") from exc
    return handle


def run(interval: int) -> None:
    lock = acquire_lock()
    previous = read(STATUS) if STATUS.exists() else {}
    event("supervisor_started", pid=os.getpid(), executable=sys.executable, argv=sys.argv,
          cwd=os.getcwd(), interval_seconds=interval)
    try:
        while True:
            if STOP.exists():
                stopped = {**previous, "state": "stopped_by_user", "checked_utc": now(),
                           "reason": f"stop marker present: {STOP}"}
                atomic(STATUS, stopped)
                event("state_changed", previous=previous.get("state"), state="stopped_by_user",
                      reason=stopped["reason"])
                return
            started = time.monotonic()
            try:
                previous = cycle(previous)
            except Exception as exc:
                previous = {
                    **previous, "state": "blocked_needs_attention", "checked_utc": now(),
                    "reason": f"transient observation error: {type(exc).__name__}: {exc}",
                    "observation_errors": int(previous.get("observation_errors", 0)) + 1,
                }
                atomic(STATUS, previous)
                event("observation_error", error=repr(exc), traceback=traceback.format_exc())
            if previous.get("state") == "delivered":
                event("supervisor_exited", state="delivered", reason=previous.get("reason"))
                return
            time.sleep(max(0, interval - (time.monotonic() - started)))
    finally:
        lock.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--check-once", action="store_true")
    parser.add_argument("--interval", type=int, default=INTERVAL)
    args = parser.parse_args()
    if args.run == args.check_once:
        parser.error("choose exactly one of --run or --check-once")
    if args.check_once:
        print(json.dumps(inspect(read(STATUS) if STATUS.exists() else {})[0], indent=2), flush=True)
    else:
        run(args.interval)


if __name__ == "__main__":
    main()
