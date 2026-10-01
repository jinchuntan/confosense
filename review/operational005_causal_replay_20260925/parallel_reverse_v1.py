"""Bounded reverse-queue helper for a second operational005 worker.

This orchestration layer does not change the frozen adapter, validator, protocol,
owners, or scientific settings.  It works from the final queue item backwards,
while the original coordinator works forwards, and stops before the two queues
can converge.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

from common import (
    HERE,
    OUTPUTS,
    SCIENTIFIC_PYTHON,
    UNITS,
    atomic_json,
    digest,
    process_identity,
    read,
    verify_protocol,
)


VERSION = "operational005_parallel_reverse_v1"
ROOT = OUTPUTS / "parallel_reverse_v1"
STATUS = ROOT / "status.json"
EVENTS = ROOT / "events.jsonl"
LOCK = ROOT / "worker.lock"
CLAIMS = ROOT / "claims"
ATTEMPTS = ROOT / "attempts"
FORWARD_PROGRESS = OUTPUTS / "coordinator" / "progress.json"
FORWARD_STATUS = OUTPUTS / "supervisor" / "status.json"
TOTAL_BLOCKS = 3 * 5 * 55
CONVERGENCE_GAP = 8
DISK_FLOOR = 8 * 2**30
RAM_FLOOR = 3 * 2**30
COMMIT_FLOOR = 3 * 2**30


class SafeStop(RuntimeError):
    """A normal stop before another block or phase may start."""


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def event(**row) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps({"utc": utc(), **row}, separators=(",", ":")) + "\n")


def write_status(**updates) -> dict:
    value = read(STATUS) if STATUS.exists() else {}
    value.update(updates, heartbeat_utc=utc(), pid=os.getpid(), version=VERSION)
    atomic_json(STATUS, value)
    return value


def coordinates(ordinal: int) -> tuple[int, int, int]:
    if ordinal < 0 or ordinal >= TOTAL_BLOCKS:
        raise ValueError(f"invalid queue ordinal: {ordinal}")
    fold, remainder = divmod(ordinal, 5 * 55)
    seed_offset, block = divmod(remainder, 55)
    return fold, 42 + seed_offset, block


def ordinal(fold: int, seed: int, block: int) -> int:
    return fold * 5 * 55 + (seed - 42) * 55 + block


def paths(fold: int, seed: int, block: int) -> tuple[Path, Path, Path]:
    unit = UNITS / f"bdg2_f{fold}_s{seed}"
    return (
        unit / "blocks" / f"block_{block:03d}",
        unit / "validation" / f"block_{block:03d}.json",
        unit / "resume" / f"block_{block:03d}.json",
    )


def marker_passes(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return bool(read(path).get("passed"))
    except (OSError, ValueError, json.JSONDecodeError):
        return False


def accepted(fold: int, seed: int, block: int) -> bool:
    stage, validation, resume = paths(fold, seed, block)
    return (stage / "COMPLETE.json").exists() and marker_passes(validation) and marker_passes(resume)


def verify_stage(stage: Path) -> None:
    marker = read(stage / "COMPLETE.json")
    if marker.get("status") != "complete" or marker.get("models_fitted") != 0:
        raise ValueError(f"invalid block completion marker: {stage}")
    for name, expected in marker["files"].items():
        if digest(stage / name) != expected:
            raise ValueError(f"block artifact hash mismatch: {stage / name}")


def tree(path: Path) -> dict[str, str]:
    return {item.relative_to(path).as_posix(): digest(item)
            for item in sorted(path.rglob("*")) if item.is_file()}


def resources() -> dict:
    script = (
        "$os=Get-CimInstance Win32_OperatingSystem;"
        "$m=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory;"
        "$c=Get-CimInstance Win32_LogicalDisk -Filter \"DeviceID='C:'\";"
        "$d=Get-CimInstance Win32_LogicalDisk -Filter \"DeviceID='D:'\";"
        "[pscustomobject]@{physical_free_bytes=[int64]$os.FreePhysicalMemory*1024;"
        "commit_headroom_bytes=[int64]$m.CommitLimit-[int64]$m.CommittedBytes;"
        "c_free_bytes=[int64]$c.FreeSpace;d_free_bytes=[int64]$d.FreeSpace}"
        "|ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        capture_output=True, text=True, check=False,
    )
    if result.returncode or not result.stdout.strip():
        raise SafeStop("resource query failed")
    return json.loads(result.stdout)


def require_resources() -> dict:
    value = resources()
    failures = []
    if value["physical_free_bytes"] < RAM_FLOOR:
        failures.append("physical RAM below 3 GiB")
    if value["commit_headroom_bytes"] < COMMIT_FLOOR:
        failures.append("Windows commit headroom below 3 GiB")
    if value["c_free_bytes"] < DISK_FLOOR:
        failures.append("C: below 8 GiB disk floor")
    if value["d_free_bytes"] < DISK_FLOOR:
        failures.append("D: below 8 GiB disk floor")
    if failures:
        raise SafeStop("; ".join(failures))
    return value


def direct_process(pid: int) -> dict | None:
    """Read the identity of exactly *pid*, without descending into its children."""
    pid = int(pid)
    script = (
        f'$p=Get-CimInstance Win32_Process -Filter "ProcessId = {pid}";'
        f'$g=Get-Process -Id {pid} -ErrorAction SilentlyContinue;'
        'if($null -ne $p -and $null -ne $g){'
        '[pscustomobject]@{pid=[int]$p.ProcessId;'
        'creation_time=$g.StartTime.ToUniversalTime().ToString("o");'
        'executable=$p.ExecutablePath;command=$p.CommandLine;'
        'cpu_seconds=[double]$g.CPU;rss_bytes=[int64]$g.WorkingSet64}'
        '|ConvertTo-Json -Compress}'
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        capture_output=True, text=True, check=False,
    )
    if result.returncode or not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def forward_identity() -> tuple[dict, dict, int]:
    progress = read(FORWARD_PROGRESS)
    status = read(FORWARD_STATUS)
    if status.get("state") != "running" or progress.get("status") != "running":
        raise SafeStop("forward supervisor/coordinator is not running")
    heartbeat = datetime.fromisoformat(status["heartbeat_utc"])
    if (datetime.now(timezone.utc) - heartbeat).total_seconds() > 300:
        raise SafeStop("forward supervisor heartbeat is stale")
    supervisor = direct_process(int(status["supervisor_pid"]))
    if supervisor is None or "supervisor.py run" not in (supervisor.get("command") or ""):
        raise SafeStop("forward supervisor identity could not be verified")
    coordinator = direct_process(int(progress["coordinator_pid"]))
    if coordinator is None or "coordinator.py run" not in (coordinator.get("command") or ""):
        raise SafeStop("forward coordinator identity could not be verified")
    fields = (progress.get("current_fold"), progress.get("current_model_seed"), progress.get("current_block"))
    if any(value is None for value in fields):
        raise SafeStop("forward queue position is unavailable")
    position = ordinal(int(fields[0]), int(fields[1]), int(fields[2]))
    return progress, status, position


def require_separation(target: int) -> tuple[dict, int]:
    progress, _, forward = forward_identity()
    gap = target - forward
    if gap <= CONVERGENCE_GAP:
        raise SafeStop(f"queue convergence guard reached: target={target}, forward={forward}, gap={gap}")
    return progress, gap


def next_target() -> tuple[int, int, int, int] | None:
    _, _, forward = forward_identity()
    for target in range(TOTAL_BLOCKS - 1, forward + CONVERGENCE_GAP, -1):
        fold, seed, block = coordinates(target)
        if not accepted(fold, seed, block):
            return target, fold, seed, block
    return None


def claim(target: int, fold: int, seed: int, block: int) -> Path:
    CLAIMS.mkdir(parents=True, exist_ok=True)
    path = CLAIMS / f"queue_{target:03d}.json"
    value = {
        "version": VERSION,
        "queue_ordinal": target,
        "fold": fold,
        "model_seed": seed,
        "block_index": block,
        "claimed_utc": utc(),
        "owner_pid": os.getpid(),
        "status": "claimed",
    }
    if path.exists():
        prior = read(path)
        expected = (prior.get("queue_ordinal"), prior.get("fold"), prior.get("model_seed"), prior.get("block_index"))
        if expected != (target, fold, seed, block):
            raise ValueError(f"claim identity mismatch: {path}")
        value["recovered_claim"] = True
    atomic_json(path, value)
    return path


def command(phase: str, target: int, fold: int, seed: int, block: int) -> tuple[Path, Path, int]:
    resource = require_resources()
    _, gap = require_separation(target)
    script = HERE / ("adapter.py" if phase in {"run", "resume"} else "validate.py")
    action = "run-block" if phase in {"run", "resume"} else "validate-block"
    argv = [
        str(SCIENTIFIC_PYTHON), "-B", str(script), action,
        "--fold", str(fold), "--model-seed", str(seed), "--block-index", str(block),
    ]
    ATTEMPTS.mkdir(parents=True, exist_ok=True)
    identity = f"q{target:03d}_f{fold}_s{seed}_b{block:03d}_{phase}_{int(time.time() * 1000)}"
    stdout_path = ATTEMPTS / f"{identity}.stdout.log"
    stderr_path = ATTEMPTS / f"{identity}.stderr.log"
    started = utc()
    event(event="phase_started", phase=phase, queue_ordinal=target, fold=fold,
          model_seed=seed, block_index=block, argv=argv, gap=gap, resources=resource)
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        child = subprocess.Popen(argv, cwd=HERE, stdout=stdout, stderr=stderr, text=True)
        observed = None
        for _ in range(20):
            observed = process_identity(child.pid)
            if observed is not None:
                break
            if child.poll() is not None:
                break
            time.sleep(0.25)
        if observed is None:
            if child.poll() is None:
                child.terminate()
                child.wait()
            raise RuntimeError("parallel scientific worker identity could not be verified")
        scientific = dict(observed, phase=phase, queue_ordinal=target, fold=fold,
                          model_seed=seed, block_index=block)
        peak = 0
        while child.poll() is None:
            current = process_identity(child.pid)
            if current is not None and current.get("creation_time") == scientific.get("creation_time"):
                peak = max(peak, int(current.get("rss_bytes", 0)))
            write_status(state="running", current_phase=phase, current_queue_ordinal=target,
                         current_fold=fold, current_model_seed=seed, current_block=block,
                         current_scientific_worker=scientific, phase_peak_rss_bytes=peak,
                         last_resource_gate=resource, current_gap=gap)
            time.sleep(5)
        code = int(child.returncode)
    write_status(current_scientific_worker=None, phase_peak_rss_bytes=peak)
    event(event="phase_returned", phase=phase, queue_ordinal=target, fold=fold,
          model_seed=seed, block_index=block, exit_code=code, started_utc=started,
          stdout=str(stdout_path), stderr=str(stderr_path), phase_peak_rss_bytes=peak)
    if code:
        tail = stderr_path.read_text(encoding="utf-8", errors="replace")[-4000:]
        raise RuntimeError(f"{phase} failed with exit {code}: {tail}")
    return stdout_path, stderr_path, peak


def process_target(target: int, fold: int, seed: int, block: int) -> dict:
    require_separation(target)
    stage, validation, resume = paths(fold, seed, block)
    claim_path = claim(target, fold, seed, block)
    started = time.perf_counter()
    if not (stage / "COMPLETE.json").exists():
        command("run", target, fold, seed, block)
    verify_stage(stage)
    if not validation.exists():
        command("validate", target, fold, seed, block)
    if not marker_passes(validation):
        raise ValueError(f"parallel validation is not passing: {validation}")
    if not resume.exists():
        before = tree(stage)
        stdout_path, stderr_path, peak = command("resume", target, fold, seed, block)
        after = tree(stage)
        passed = before == after
        atomic_json(resume, {
            "passed": passed,
            "exit_code": 0,
            "files_unchanged": passed,
            "models_fitted": 0,
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "peak_rss_bytes": peak,
            "utc": utc(),
            "parallel_orchestration_version": VERSION,
        })
    if not marker_passes(resume):
        raise ValueError(f"parallel zero-fit resume is not passing: {resume}")
    verify_stage(stage)
    receipt = {
        "version": VERSION,
        "status": "accepted",
        "queue_ordinal": target,
        "fold": fold,
        "model_seed": seed,
        "block_index": block,
        "models_fitted": 0,
        "validation_passed": True,
        "zero_fit_resume_passed": True,
        "elapsed_seconds": time.perf_counter() - started,
        "completed_utc": utc(),
    }
    atomic_json(claim_path, receipt)
    event(event="block_accepted", **receipt)
    return receipt


def check() -> int:
    protocol = verify_protocol()
    for value in range(TOTAL_BLOCKS):
        if ordinal(*coordinates(value)) != value:
            raise AssertionError(f"queue coordinate round-trip failed: {value}")
    resource = require_resources()
    progress, status, forward = forward_identity()
    target = next_target()
    if target is None:
        raise SafeStop("no separated reverse-queue target remains")
    queue_ordinal, fold, seed, block = target
    _, gap = require_separation(queue_ordinal)
    result = {
        "passed": True,
        "version": VERSION,
        "script_sha256": digest(Path(__file__)),
        "protocol_version": protocol["version"],
        "forward_supervisor_pid": status["supervisor_pid"],
        "forward_position": forward,
        "forward_phase": progress.get("current_phase"),
        "proposed_target": {
            "queue_ordinal": queue_ordinal,
            "fold": fold,
            "model_seed": seed,
            "block_index": block,
            "gap": gap,
        },
        "resources": resource,
        "fit_budget": {"forecasting_models": 0, "quantile_estimators": 0,
                       "conformalizer_fits": 0, "new_seeds": 0},
    }
    print(json.dumps(result, indent=2))
    return 0


def run(max_blocks: int) -> int:
    verify_protocol()
    ROOT.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit("parallel worker lock exists; refusing duplicate")
    os.write(descriptor, json.dumps({"pid": os.getpid(), "created_utc": utc(),
                                     "version": VERSION}).encode("utf-8"))
    os.close(descriptor)
    completed = 0
    write_status(state="starting", started_utc=utc(), script_sha256=digest(Path(__file__)),
                 max_blocks=max_blocks, completed_by_parallel_worker=0, exact_error=None)
    try:
        while max_blocks <= 0 or completed < max_blocks:
            require_resources()
            target = next_target()
            if target is None:
                write_status(state="safe_stop", exact_error=None,
                             stop_reason="no separated reverse-queue target remains")
                return 0
            queue_ordinal, fold, seed, block = target
            receipt = process_target(queue_ordinal, fold, seed, block)
            completed += 1
            write_status(state="running", current_phase="checkpointed", current_queue_ordinal=queue_ordinal,
                         current_fold=fold, current_model_seed=seed, current_block=block,
                         completed_by_parallel_worker=completed, last_completed=receipt,
                         last_scientific_progress_utc=receipt["completed_utc"], exact_error=None)
        write_status(state="pilot_complete" if max_blocks == 1 else "bounded_complete",
                     current_scientific_worker=None, completed_by_parallel_worker=completed,
                     finished_utc=utc())
        return 0
    except SafeStop as exc:
        write_status(state="safe_stop", current_scientific_worker=None,
                     stop_reason=str(exc), exact_error=None, finished_utc=utc())
        event(event="safe_stop", reason=str(exc))
        return 0
    except BaseException as exc:
        write_status(state="blocked", current_scientific_worker=None,
                     exact_error=repr(exc), finished_utc=utc())
        event(event="blocked", error=repr(exc))
        raise
    finally:
        if LOCK.exists():
            try:
                value = json.loads(LOCK.read_text(encoding="utf-8"))
            except (OSError, ValueError, json.JSONDecodeError):
                value = {}
            if value.get("pid") == os.getpid():
                LOCK.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["check", "run"])
    parser.add_argument("--max-blocks", type=int, default=0,
                        help="0 continues until convergence/resource stop; 1 is the bounded pilot")
    arguments = parser.parse_args()
    if arguments.action == "check":
        raise SystemExit(check())
    raise SystemExit(run(arguments.max_blocks))
