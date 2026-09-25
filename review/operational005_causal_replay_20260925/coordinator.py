"""Sequential, checkpoint-aware coordinator for 15 x 55 replay blocks."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from common import (HERE, OUTPUTS, SCIENTIFIC_PYTHON, UNITS, atomic_json, digest,
                    process_identity, read, verify_protocol)
from adapter import policy_blocks, verify_complete

ROOT = OUTPUTS / "coordinator"
PROGRESS = ROOT / "progress.json"
EVENTS = ROOT / "events.jsonl"
FLOOR = 8 * 2**30


def utc(): return datetime.now(timezone.utc).isoformat()


def event(**row):
    ROOT.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps({"utc": utc(), **row}, separators=(",", ":")) + "\n")


def write_progress(**updates):
    state = read(PROGRESS) if PROGRESS.exists() else {}
    state.update(updates, heartbeat_utc=utc())
    atomic_json(PROGRESS, state)
    return state


def tree(path: Path):
    return {p.relative_to(path).as_posix(): digest(p) for p in sorted(path.rglob("*")) if p.is_file()}


def command(phase: str, fold: int, seed: int, block: int):
    script = HERE / ("adapter.py" if phase in {"run", "resume"} else "validate.py")
    action = "run-block" if phase in {"run", "resume"} else "validate-block"
    argv = [str(SCIENTIFIC_PYTHON), "-B", str(script), action, "--fold", str(fold), "--model-seed", str(seed), "--block-index", str(block)]
    attempts = ROOT / "attempts"; attempts.mkdir(parents=True, exist_ok=True)
    identity = f"f{fold}_s{seed}_b{block:03d}_{phase}_{int(time.time()*1000)}"
    out = attempts / (identity + ".stdout.log"); err = attempts / (identity + ".stderr.log")
    started = utc(); event(event="phase_started", phase=phase, fold=fold, model_seed=seed, block_index=block, argv=argv)
    with out.open("w", encoding="utf-8") as stdout, err.open("w", encoding="utf-8") as stderr:
        result = subprocess.Popen(argv, cwd=HERE, stdout=stdout, stderr=stderr, text=True)
        observed = process_identity(result.pid)
        if observed is None:
            result.terminate(); result.wait()
            raise ValueError("could not verify scientific worker identity")
        identity = dict(observed, phase=phase, fold=fold, model_seed=seed, block_index=block)
        write_progress(current_scientific_worker=identity)
        peak = 0; last_status = 0.0
        while result.poll() is None:
            observed = process_identity(result.pid)
            if observed is not None and observed.get("creation_time") == identity["creation_time"]:
                peak = max(peak, int(observed["rss_bytes"]))
            now = time.monotonic()
            if now - last_status >= 5:
                prior_peak = read(PROGRESS).get("peak_scientific_rss_bytes", 0)
                write_progress(peak_scientific_rss_bytes=max(prior_peak, peak), current_scientific_worker=identity)
                last_status = now
            time.sleep(5)
        prior_peak = read(PROGRESS).get("peak_scientific_rss_bytes", 0)
        write_progress(peak_scientific_rss_bytes=max(prior_peak, peak), current_scientific_worker=None)
    event(event="phase_returned", phase=phase, fold=fold, model_seed=seed, block_index=block,
          exit_code=result.returncode, stdout=str(out), stderr=str(err), started_utc=started,
          phase_peak_rss_bytes=peak)
    return result.returncode, out, err


def completed_counts():
    blocks = 0; validations = 0; resumes = 0; bytes_total = 0
    for fold in range(3):
        for seed in range(42, 47):
            unit = UNITS / f"bdg2_f{fold}_s{seed}"
            for block in range(55):
                path = unit / "blocks" / f"block_{block:03d}"
                if (path / "COMPLETE.json").exists():
                    verify_complete(path); blocks += 1
                    bytes_total += sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
                validation = unit / "validation" / f"block_{block:03d}.json"
                if validation.exists() and read(validation).get("passed"): validations += 1
                receipt = unit / "resume" / f"block_{block:03d}.json"
                if receipt.exists() and read(receipt).get("passed"): resumes += 1
    return blocks, validations, resumes, bytes_total


def completed_unique_candidates() -> int:
    completed = 0
    for block in range(55):
        accepted = True
        for fold in range(3):
            for seed in range(42, 47):
                unit = UNITS / f"bdg2_f{fold}_s{seed}"
                stage = unit / "blocks" / f"block_{block:03d}" / "COMPLETE.json"
                validation = unit / "validation" / f"block_{block:03d}.json"
                resume = unit / "resume" / f"block_{block:03d}.json"
                if not (stage.exists() and validation.exists() and resume.exists()
                        and read(validation).get("passed") and read(resume).get("passed")):
                    accepted = False
                    break
            if not accepted:
                break
        completed += 3 if accepted else 0
    return completed


def run():
    verify_protocol()
    ROOT.mkdir(parents=True, exist_ok=True)
    run_started = time.perf_counter()
    initial_blocks = completed_counts()[0]
    total_blocks = 15 * len(policy_blocks())
    write_progress(status="running", total_policy_blocks=total_blocks, ready_evaluation_rows=2475,
                   unavailable_evaluation_rows=1485, coordinator_pid=os.getpid(), started_utc=utc(),
                   current_phase="preflight", last_scientific_progress_utc=None, retry_count=0)
    for fold in range(3):
        for seed in range(42, 47):
            for block in range(55):
                free = shutil.disk_usage(OUTPUTS).free
                if free < FLOOR:
                    write_progress(status="blocked", current_phase="disk_floor", exact_error="free disk below 8 GiB")
                    return 2
                stage = UNITS / f"bdg2_f{fold}_s{seed}" / "blocks" / f"block_{block:03d}"
                validation = UNITS / f"bdg2_f{fold}_s{seed}" / "validation" / f"block_{block:03d}.json"
                resume = UNITS / f"bdg2_f{fold}_s{seed}" / "resume" / f"block_{block:03d}.json"
                write_progress(current_fold=fold, current_model_seed=seed, current_block=block,
                               current_phase="run", free_disk_bytes=free)
                if not (stage / "COMPLETE.json").exists():
                    code, out, err = command("run", fold, seed, block)
                    if code:
                        message = err.read_text(encoding="utf-8", errors="replace")[-4000:]
                        write_progress(status="blocked", current_phase="run", exact_error=message)
                        return code
                    write_progress(last_scientific_progress_utc=utc())
                else:
                    verify_complete(stage)
                if not validation.exists():
                    write_progress(current_phase="validate")
                    code, out, err = command("validate", fold, seed, block)
                    if code:
                        message = err.read_text(encoding="utf-8", errors="replace")[-4000:]
                        write_progress(status="blocked", current_phase="validate", exact_error=message)
                        return code
                elif not read(validation).get("passed"):
                    write_progress(status="blocked", current_phase="validate", exact_error="saved validation is not passing")
                    return 2
                if not resume.exists():
                    before = tree(stage)
                    write_progress(current_phase="zero_fit_resume")
                    code, out, err = command("resume", fold, seed, block)
                    after = tree(stage)
                    passed = code == 0 and before == after
                    atomic_json(resume, {"passed": passed, "exit_code": code, "files_unchanged": before == after,
                                         "models_fitted": 0, "utc": utc(), "stdout": str(out), "stderr": str(err)})
                    if not passed:
                        write_progress(status="blocked", current_phase="zero_fit_resume", exact_error="resume changed or failed")
                        return 2
                blocks, validations, resumes, bytes_total = completed_counts()
                unique_candidates = completed_unique_candidates()
                average = bytes_total / blocks if blocks else None
                remaining = total_blocks - blocks
                progressed = blocks - initial_blocks
                seconds_per_block = ((time.perf_counter() - run_started) / progressed) if progressed else None
                write_progress(completed_policy_blocks=blocks, remaining_policy_blocks=remaining,
                               validated_policy_blocks=validations, zero_fit_resumed_policy_blocks=resumes,
                               completed_evaluation_rows=blocks * 3, remaining_ready_evaluation_rows=remaining * 3,
                               completed_unique_candidates=unique_candidates,
                               remaining_ready_unique_candidates=165 - unique_candidates,
                               observed_replay_bytes=bytes_total, estimated_final_replay_bytes=average * total_blocks if average else None,
                               mean_seconds_per_new_block=seconds_per_block,
                               estimated_remaining_seconds=seconds_per_block * remaining if seconds_per_block else None,
                               first_block_bytes=bytes_total if blocks == 1 else read(PROGRESS).get("first_block_bytes"),
                               minimum_free_disk_bytes=min(free, read(PROGRESS).get("minimum_free_disk_bytes", free)),
                               last_scientific_progress_utc=utc(), current_phase="checkpointed")
    write_progress(current_phase="aggregate")
    argv = [str(SCIENTIFIC_PYTHON), "-B", str(HERE / "aggregate.py")]
    result = subprocess.run(argv, cwd=HERE)
    if result.returncode:
        write_progress(status="blocked", current_phase="aggregate", exact_error="aggregation failed")
        return result.returncode
    write_progress(status="scientific_complete", current_phase="delivery_pending", completed_policy_blocks=total_blocks,
                   remaining_policy_blocks=0, completed_evaluation_rows=2475, remaining_ready_evaluation_rows=0)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=["run"]); parser.parse_args()
    raise SystemExit(run())
