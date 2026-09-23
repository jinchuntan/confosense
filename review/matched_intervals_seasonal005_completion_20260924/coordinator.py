"""Sequential, restartable execution of the authorized 52 method bundles."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

from adapter import (HERE, REPO, SMART, AUTH, SOURCE_HASH, bundle_paths,
                     digest, frame, read, source_digest, SCOPE)

sys.path.insert(0, str(REPO / "review/matched_intervals005_bdg2_20260914"))
_spec = importlib.util.spec_from_file_location(
    "existing_interval_coordinator", REPO / "review/matched_intervals005_bdg2_20260914/coordinator.py")
_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)
Engine, exclusive_lock = _legacy.Engine, _legacy.exclusive_lock

PYTHON = "C:/cfs_venv/Scripts/python.exe"
ROOT = SMART / "outputs/matched_intervals005/completion_52_v1_coordinator"
ADAPTER = HERE / "adapter.py"
SYNTHETIC = REPO / "review/matched_intervals005_bdg2_20260914/SYNTHETIC_ACCEPTANCE.json"
BRANCH = "review/matched-intervals-seasonal005-completion-20260924"
DISK_FLOOR = 8 * 2**30


def bundles() -> list[tuple[str, int, int]]:
    rows = frame(SCOPE)[["dataset", "outer_fold", "model_seed"]]
    return sorted((str(a), int(b), int(c)) for a, b, c in rows.itertuples(index=False, name=None))


def command(action: str, key: tuple[str, int, int], receipt: Path | None = None) -> list[str]:
    dataset, fold, seed = key
    args = [PYTHON, "-B", str(ADAPTER), action, "--dataset", dataset,
            "--fold", str(fold), "--seed", str(seed)]
    if action == "freeze":
        args += ["--synthetic-receipt", str(SYNTHETIC)]
    if receipt is not None:
        args += ["--receipt", str(receipt)]
    if action == "resume":
        args += ["--forbid-fits"]
    return args


def summary(engine: Engine, phase: str) -> None:
    queue = bundles()
    completed = []
    frozen = []
    for key in queue:
        design, output = bundle_paths(*key)
        if (design / "frozen_protocol.json").exists() and (design / "readiness.json").exists():
            frozen.append(key)
        if (output / "COMPLETE.json").exists() and (ROOT / "validation" / f"{key[0]}_f{key[1]}_s{key[2]}" / "validation.json").exists() and (ROOT / "resumes" / f"{key[0]}_f{key[1]}_s{key[2]}.json").exists():
            completed.append(key)
    free = shutil.disk_usage(SMART).free
    start = engine.state.setdefault("started_epoch", time.time())
    minimum = min(free, engine.state.get("minimum_free_disk_bytes", free))
    engine.state.update(phase=phase, frozen_bundles=len(frozen),
                        completed_bundles=len(completed), remaining_bundles=52-len(completed),
                        elapsed_seconds=time.time()-start, free_disk_bytes=free,
                        minimum_free_disk_bytes=minimum, full_study_ready=False,
                        restart_argv=[PYTHON, "-B", str(HERE / "coordinator.py"), "--run"])
    engine.save()
    print(json.dumps({k: engine.state[k] for k in
                      ("phase", "frozen_bundles", "completed_bundles", "remaining_bundles",
                       "elapsed_seconds", "free_disk_bytes", "minimum_free_disk_bytes")}), flush=True)


def check_capacity(remaining: list[tuple[str, int, int]]) -> None:
    free = shutil.disk_usage(SMART).free
    # Historical BDG2 ~0.49 GiB; other runs ~0.16 GiB. Allow headroom and
    # one same-volume backup copy; refine after actual new-bundle measurement.
    raw_budget = sum(int((.6 if key[0] == "bdg2" else .25) * 2**30) for key in remaining)
    projected = free - 2 * raw_budget
    if free < DISK_FLOOR or projected < DISK_FLOOR:
        raise ValueError(f"disk safety floor would be crossed: free={free}, remaining={len(remaining)}, projected={projected}")


def ready(engine: Engine, key: tuple[str, int, int]) -> None:
    name = f"{key[0]}_f{key[1]}_s{key[2]}"
    design, _ = bundle_paths(*key)
    protocol = design / "frozen_protocol.json"
    receipt = design / "readiness.json"
    if not protocol.exists():
        engine.phase(f"{name}/freeze", lambda _: command("freeze", key))
    if not receipt.exists():
        engine.phase(f"{name}/readiness", lambda _: command("readiness", key, receipt))
    if not read(receipt)["passed"]:
        raise ValueError(f"readiness failed: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefit", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.prefit == args.run:
        parser.error("choose exactly one of --prefit or --run")
    os.chdir(SMART)
    if subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip() != BRANCH:
        raise ValueError("wrong review branch")
    if source_digest() != SOURCE_HASH or read(AUTH)["scope_sha256"] != digest(SCOPE):
        raise ValueError("source or authorization changed")
    with exclusive_lock(ROOT / "coordinator.lock"):
        engine = Engine(ROOT, cwd=SMART, poll_seconds=10)
        engine.reconcile()
        try:
            queue = bundles()
            if len(queue) != 52:
                raise ValueError("scope changed")
            if args.prefit:
                check_capacity(queue)
                for key in queue:
                    dataset, fold, seed = key
                    if seed != 42 and fold < 2 and dataset != "rico":
                        continue  # exact seasonal stage hashes do not exist until seed 42 completes
                    ready(engine, key)
                    summary(engine, f"prefit/{dataset}_f{fold}_s{seed}")
                engine.state["status"] = "prefit_ready"
                summary(engine, "prefit_ready")
                return
            prefit = read(HERE / "PREFIT_COMMIT.json")
            if prefit["source_hash"] != SOURCE_HASH or prefit["adapter_sha256"] != digest(ADAPTER):
                raise ValueError("prefit identity mismatch")
            subprocess.run(["git", "merge-base", "--is-ancestor", prefit["commit"], "HEAD"], cwd=REPO, check=True)
            for ordinal, key in enumerate(queue):
                dataset, fold, seed = key
                name = f"{dataset}_f{fold}_s{seed}"
                check_capacity(queue[ordinal:])
                ready(engine, key)
                design, output = bundle_paths(*key)
                action = "resume" if (output / "checkpoint_manifest.json").exists() else "run"
                engine.phase(f"{name}/run", lambda _, a=action, k=key: command(a, k))
                validation = ROOT / "validation" / name
                engine.phase(f"{name}/validate", lambda _, k=key, p=validation: command("validate", k, p))
                resume = ROOT / "resumes" / f"{name}.json"
                resume.parent.mkdir(parents=True, exist_ok=True)
                engine.phase(f"{name}/completed_resume", lambda _, k=key, p=resume: command("resume", k, p))
                v, r = read(validation / "validation.json"), read(resume)
                expected = 40 if dataset == "rico" else 30
                if (not v["passed"] or v["method_cells"] != expected or
                    v["models_fitted"] or v["calibrators_fitted"] or
                    not v["source_artifacts_unchanged"] or
                    r["models_fitted"] or r["calibrators_fitted"] or
                    not r["all_run_files_unchanged"]):
                    raise ValueError(f"bundle validation/resume failed: {name}")
                summary(engine, f"validated/{name}")
            engine.state["status"] = "science_validated"
            summary(engine, "science_validated")
        except BaseException as exc:
            engine.state.update(status="blocked", failure=str(exc), traceback=traceback.format_exc())
            summary(engine, "blocked")
            raise


if __name__ == "__main__":
    main()
