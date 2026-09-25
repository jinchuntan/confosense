"""Two-minute durable supervisor with a single-instance lock."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

from common import (HERE, OUTPUTS, SCIENTIFIC_PYTHON, SUPERVISOR, atomic_json,
                    process_identity, read, verify_protocol)

STATUS = SUPERVISOR / "status.json"
EVENTS = SUPERVISOR / "events.jsonl"
LOCK = SUPERVISOR / "supervisor.lock"
PROGRESS = OUTPUTS / "coordinator" / "progress.json"


def utc(): return datetime.now(timezone.utc).isoformat()


def event(**row):
    with EVENTS.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps({"utc": utc(), **row}, separators=(",", ":")) + "\n")


def status(worker=None, **updates):
    value = read(STATUS) if STATUS.exists() else {}
    process = None
    if worker is not None and worker.poll() is None:
        process = process_identity(worker.pid)
    progress = read(PROGRESS) if PROGRESS.exists() else None
    scientific_worker = None
    if progress and progress.get("current_scientific_worker"):
        recorded = progress["current_scientific_worker"]
        active = process_identity(int(recorded["pid"]))
        if active is not None and active.get("creation_time") == recorded.get("creation_time"):
            scientific_worker = dict(recorded, **active)
    value.update(updates, heartbeat_utc=utc(), supervisor_pid=os.getpid(), worker=process,
                 scientific_worker=scientific_worker, scientific_progress=progress,
                 free_disk_bytes=shutil.disk_usage(OUTPUTS).free)
    atomic_json(STATUS, value)


def run():
    verify_protocol()
    SUPERVISOR.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit("supervisor lock already exists; inspect identity before recovery")
    os.write(fd, json.dumps({"pid": os.getpid(), "created_utc": utc()}).encode()); os.close(fd)
    stdout = (SUPERVISOR / "coordinator.stdout.log").open("a", encoding="utf-8")
    stderr = (SUPERVISOR / "coordinator.stderr.log").open("a", encoding="utf-8")
    worker = subprocess.Popen([str(SCIENTIFIC_PYTHON), "-B", str(HERE / "coordinator.py"), "run"], cwd=HERE,
                              stdout=stdout, stderr=stderr, text=True)
    event(event="coordinator_started", pid=worker.pid)
    status(worker, state="running", poll_seconds=120, started_utc=utc(), last_error=None,
           coordinator_exit_code=None, finished_utc=None)
    try:
        while worker.poll() is None:
            time.sleep(120)
            status(worker, state="running")
        code = worker.returncode
        state = "scientific_complete_delivery_pending" if code == 0 else "blocked"
        status(worker, state=state, coordinator_exit_code=code, finished_utc=utc())
        event(event="coordinator_returned", exit_code=code, state=state)
        return code
    except BaseException as exc:
        status(worker, state="supervisor_error", last_error=repr(exc))
        event(event="supervisor_error", error=repr(exc))
        raise
    finally:
        stdout.close(); stderr.close()
        if LOCK.exists(): LOCK.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=["run"]); parser.parse_args()
    raise SystemExit(run())
