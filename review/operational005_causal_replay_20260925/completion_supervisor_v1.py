"""Guard the live frozen supervisor, then run operational delivery once.

The frozen supervisor remains solely responsible for reconciliation and
aggregation.  This additive continuation polls it every 120 seconds and will
not start delivery until that exact supervisor exits successfully.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import OUTPUTS, SCIENTIFIC_PYTHON, atomic_json, read, verify_protocol


VERSION = "operational005_completion_supervisor_v1.3"
ROOT = OUTPUTS / "completion_supervisor_v1"
STATUS = ROOT / "status.json"
EVENTS = ROOT / "events.jsonl"
LOCK = ROOT / "supervisor.lock"
FROZEN_STATUS = OUTPUTS / "supervisor" / "status.json"
FROZEN_PROGRESS = OUTPUTS / "coordinator" / "progress.json"
HERE = Path(__file__).resolve().parent
DELIVERY_PROGRESS = OUTPUTS / "completion_delivery_v1" / "progress.json"
POLL_SECONDS = 120


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def event(name: str, **values: Any) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps({"utc": utc(), "event": name, **values}, default=str,
                                separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write(**values: Any) -> dict[str, Any]:
    state = read(STATUS) if STATUS.exists() else {}
    state.update(values, version=VERSION, heartbeat_utc=utc(), supervisor_pid=os.getpid(),
                 poll_seconds=POLL_SECONDS)
    atomic_json(STATUS, state)
    return state


def exact_process(pid: int) -> dict[str, Any] | None:
    script = (
        f'$p=Get-CimInstance Win32_Process -Filter "ProcessId = {int(pid)}";'
        f'$g=Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue;'
        'if($null -ne $p -and $null -ne $g){'
        '[pscustomobject]@{pid=[int]$p.ProcessId;'
        'creation_time=$g.StartTime.ToUniversalTime().ToString("o");'
        'executable=$p.ExecutablePath;command=$p.CommandLine;'
        'cpu_seconds=[double]$g.CPU;rss_bytes=[int64]$g.WorkingSet64}'
        '|ConvertTo-Json -Compress}'
    )
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", script],
                            capture_output=True, text=True, check=False)
    if result.returncode or not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def age_seconds(timestamp: str) -> float:
    return (datetime.now(timezone.utc) - datetime.fromisoformat(timestamp)).total_seconds()


def queue_ordinal(progress: dict[str, Any]) -> int | None:
    values = (progress.get("current_fold"), progress.get("current_model_seed"),
              progress.get("current_block"))
    if any(value is None for value in values):
        return None
    fold, seed, block = map(int, values)
    return fold * 275 + (seed - 42) * 55 + block


def wait_for_frozen_supervisor() -> tuple[dict[str, Any], dict[str, Any]]:
    initial_status = read(FROZEN_STATUS)
    initial_progress = read(FROZEN_PROGRESS)
    if (initial_status.get("state") == "scientific_complete_delivery_pending" and
            initial_status.get("coordinator_exit_code") == 0 and
            initial_progress.get("status") == "scientific_complete" and
            initial_progress.get("current_phase") == "delivery_pending"):
        write(state="reconciliation_complete", frozen_supervisor=initial_status,
              frozen_progress=initial_progress, actual_progress_observed=True,
              adopted_completed_frozen_supervisor=True, error=None, started_utc=utc())
        event("completed_frozen_supervisor_adopted", progress=initial_progress)
        return initial_status, initial_progress
    if initial_status.get("state") != "running" or initial_progress.get("status") != "running":
        raise ValueError("frozen supervisor/coordinator was not running at adoption")
    supervisor_pid = int(initial_status["supervisor_pid"])
    coordinator_pid = int(initial_progress["coordinator_pid"])
    supervisor_identity = exact_process(supervisor_pid)
    coordinator_identity = exact_process(coordinator_pid)
    if (supervisor_identity is None or
            "supervisor.py run" not in str(supervisor_identity.get("command", ""))):
        raise ValueError("frozen supervisor identity could not be verified")
    if (coordinator_identity is None or
            "coordinator.py run" not in str(coordinator_identity.get("command", ""))):
        raise ValueError("frozen coordinator identity could not be verified")
    adopted = {
        "supervisor": supervisor_identity, "coordinator": coordinator_identity,
        "progress_ordinal": queue_ordinal(initial_progress),
        "progress_heartbeat_utc": initial_progress.get("heartbeat_utc"),
    }
    write(state="watching_reconciliation", adopted=adopted,
          frozen_progress=initial_progress, error=None, started_utc=utc())
    event("frozen_supervisor_adopted", supervisor=supervisor_identity,
          coordinator=coordinator_identity)
    previous_ordinal = queue_ordinal(initial_progress)
    previous_cpu = float(coordinator_identity.get("cpu_seconds", 0.0))
    while True:
        status = read(FROZEN_STATUS)
        progress = read(FROZEN_PROGRESS)
        supervisor_now = exact_process(supervisor_pid)
        coordinator_now = exact_process(coordinator_pid)
        if status.get("state") == "running":
            if supervisor_now is None or supervisor_now.get("creation_time") != supervisor_identity.get("creation_time"):
                raise ValueError("frozen supervisor identity changed while state remained running")
            if coordinator_now is None or coordinator_now.get("creation_time") != coordinator_identity.get("creation_time"):
                raise ValueError("frozen coordinator identity changed while state remained running")
            if age_seconds(status["heartbeat_utc"]) > 300:
                raise ValueError("frozen supervisor heartbeat exceeded 300 seconds")
            ordinal = queue_ordinal(progress)
            cpu_now = float(coordinator_now.get("cpu_seconds", 0.0))
            actual_progress = ((ordinal is not None and previous_ordinal is not None and ordinal > previous_ordinal) or
                               cpu_now > previous_cpu + 1.0 or
                               progress.get("status") == "scientific_complete")
            write(state="watching_reconciliation", frozen_supervisor=status,
                  frozen_progress=progress, frozen_supervisor_identity=supervisor_now,
                  frozen_coordinator_identity=coordinator_now,
                  actual_progress_observed=actual_progress, previous_queue_ordinal=previous_ordinal,
                  current_queue_ordinal=ordinal, coordinator_cpu_delta=cpu_now - previous_cpu,
                  error=None)
            event("reconciliation_observed", prior_ordinal=previous_ordinal,
                  ordinal=ordinal, coordinator_cpu_delta=cpu_now - previous_cpu,
                  actual_progress=actual_progress, phase=progress.get("current_phase"))
            previous_ordinal, previous_cpu = ordinal, cpu_now
            time.sleep(POLL_SECONDS)
            continue
        if status.get("state") == "scientific_complete_delivery_pending":
            if status.get("coordinator_exit_code") != 0:
                raise ValueError("frozen coordinator exit was not zero")
            if progress.get("status") != "scientific_complete" or progress.get("current_phase") != "delivery_pending":
                raise ValueError("frozen completion state and progress disagree")
            if coordinator_now is not None:
                time.sleep(5)
                continue
            write(state="reconciliation_complete", frozen_supervisor=status,
                  frozen_progress=progress, actual_progress_observed=True)
            event("reconciliation_complete", progress=progress)
            return status, progress
        raise ValueError(f"frozen supervisor stopped in unexpected state: {status.get('state')}")


def run_delivery() -> dict[str, Any]:
    if DELIVERY_PROGRESS.exists():
        prior = read(DELIVERY_PROGRESS)
        if prior.get("status") == "complete":
            return prior
        corrected_validation_failure = (
            "DataFrame shape mismatch" in str(prior.get("error")) and
            (HERE / "DELIVERY_VALIDATION_FAILURE_V1.json").is_file() and
            (HERE / "DELIVERY_VALIDATION_CORRECTION_V1_1.md").is_file())
        corrected_publication_failure = (
            "PREPUBLICATION_MANIFEST.json" in str(prior.get("error")) and
            (HERE / "PUBLICATION_PREFLIGHT_FAILURE_V1_1.json").is_file() and
            (HERE / "PUBLICATION_PREFLIGHT_CORRECTION_V1_2.md").is_file())
        corrected_credential_gate_failure = (
            "credential-pattern gate failed" in str(prior.get("error")) and
            (HERE / "PUBLICATION_CREDENTIAL_GATE_FAILURE_V1_2.json").is_file() and
            (HERE / "PUBLICATION_CREDENTIAL_GATE_CORRECTION_V1_3.md").is_file())
        known_corrected_failure = (prior.get("status") == "blocked" and
                                   (corrected_validation_failure or corrected_publication_failure or
                                    corrected_credential_gate_failure))
        if prior.get("status") == "running" or (prior.get("status") == "blocked" and not known_corrected_failure):
            raise ValueError(f"existing delivery state requires inspection: {prior.get('status')}")
        if known_corrected_failure:
            event("adopting_corrected_delivery_retry", prior=prior)
    stdout_path = ROOT / "delivery.stdout.log"
    stderr_path = ROOT / "delivery.stderr.log"
    command = [str(SCIENTIFIC_PYTHON), "-B", str(HERE / "completion_delivery_v1.py")]
    with stdout_path.open("a", encoding="utf-8") as stdout, stderr_path.open("a", encoding="utf-8") as stderr:
        process = subprocess.Popen(command, cwd=HERE, stdout=stdout, stderr=stderr, text=True,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        launch_identity = exact_process(process.pid)
        if launch_identity is None or "completion_delivery_v1.py" not in str(launch_identity.get("command", "")):
            if process.poll() is None:
                process.terminate()
                process.wait()
            raise ValueError("delivery process identity could not be verified")
        write(state="delivery_running", delivery_command=command,
              delivery_launch_identity=launch_identity, delivery_stdout=str(stdout_path),
              delivery_stderr=str(stderr_path), error=None)
        event("delivery_started", identity=launch_identity, command=command)
        while process.poll() is None:
            identity = exact_process(process.pid)
            delivery = read(DELIVERY_PROGRESS) if DELIVERY_PROGRESS.exists() else None
            if identity is None and process.poll() is not None:
                break
            if identity is None or identity.get("creation_time") != launch_identity.get("creation_time"):
                raise ValueError("delivery process identity changed")
            if delivery and delivery.get("updated_utc") and age_seconds(delivery["updated_utc"]) > 600:
                raise ValueError("delivery progress heartbeat exceeded 600 seconds")
            write(state="delivery_running", delivery_identity=identity,
                  delivery_progress=delivery, error=None)
            event("delivery_observed", identity=identity, delivery_progress=delivery)
            time.sleep(POLL_SECONDS)
        code = int(process.returncode)
    delivery = read(DELIVERY_PROGRESS) if DELIVERY_PROGRESS.exists() else None
    if code != 0 or not delivery or delivery.get("status") != "complete":
        tail = stderr_path.read_text(encoding="utf-8", errors="replace")[-4000:]
        raise RuntimeError(f"delivery exited {code} without completion: {tail}")
    event("delivery_returned", exit_code=code, delivery_progress=delivery)
    return delivery


def run() -> int:
    verify_protocol()
    ROOT.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"completion supervisor lock exists: {LOCK}") from exc
    os.write(descriptor, json.dumps({"pid": os.getpid(), "created_utc": utc(),
                                     "version": VERSION}).encode("utf-8"))
    os.close(descriptor)
    try:
        wait_for_frozen_supervisor()
        delivery = run_delivery()
        write(state="complete", delivery_progress=delivery, completed_utc=utc(), error=None)
        event("completion_supervisor_finished", delivery=delivery)
        return 0
    except BaseException as exc:
        write(state="blocked", error=repr(exc), blocked_utc=utc())
        event("completion_supervisor_blocked", error=repr(exc))
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
