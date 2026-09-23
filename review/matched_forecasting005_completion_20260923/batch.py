"""Bounded execution of the 125 remaining matched-forecasting005 units.

This is orchestration only.  Scientific fitting, validation, checkpointing and
resume remain in the frozen src.matched_forecasting005 implementation.
"""
from __future__ import annotations

import argparse
import csv as csv_module
import gzip
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SMART = ROOT / "smart_building_conformal"
REVIEW = Path(__file__).resolve().parent
OLD_REVIEW = ROOT / "review" / "matched_fold2_multiseed_20260914"
BASE = SMART / "outputs" / "matched_forecasting005"
PRIOR_ANALYSIS = BASE / "fold2_multiseed_batch_v1" / "analysis_v1"
BATCH = BASE / "core_completion_125_v1_coordinator"
ANALYSIS = BASE / "core_completion_195_v1_analysis"
PACKAGES = BASE / "core_completion_125_v1_packages"
BACKUP = Path("C:/Users/nigel/ConfoSenseBackups/matched_forecasting005_completion_20260923")
MATRIX = SMART / "outputs" / "amendment005" / "support_design_v1" / "experiment_matrix.csv"
QUEUE = PRIOR_ANALYSIS / "remaining_queue_updated.csv"
AUTH = SMART / "configs" / "matched_forecasting005_core_completion_125_v1.json"
PYTHON = "C:/cfs_venv/Scripts/python.exe"
BRANCH = "review/matched-forecasting005-completion-20260923"
ENTRY = "640aa76d0c4ff47d5fea09d160bfacf488b7c5e7"
SOURCE_HASH = "a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f"
SUBSTANTIVE_COMMIT = "be8487668e82fc91a42491fb26615c6cfbca0362"
PRIOR_EVALUATED = "60882c2c405a0e62358c88ea0b8cff3fb52b2f2a"
MODELS = ["persistence", "xgboost", "attention_lstm"]
LEVELS = [0.9, 0.95]
KEYCOLS = ["dataset", "horizon", "outer_fold", "model_seed"]
MINUTES = {"pleia": 10, "pleia_energy": 10, "rico": 1, "bdg2": 60}
UNITS = {"pleia": "degrees C", "pleia_energy": "kWh per 10 minutes",
         "rico": "degrees C", "bdg2": "kWh per hour"}
LABELS = {"pleia": "PLEIA temperature", "pleia_energy": "PLEIA energy",
          "rico": "RICO temperature", "bdg2": "BDG2 electricity"}
COLORS = {"persistence": "#555555", "xgboost": "#0072B2", "attention_lstm": "#D55E00"}
DISK_FLOOR = 8 * 2**30
PROJECTED_RUN_BYTES = 1_869_213_285
REQUIRED_FREE_BYTES = DISK_FLOOR + 5 * PROJECTED_RUN_BYTES + 2 * 2**30
RECOVERED_UNIT_CHECK_TASK = "pleia_energy_h1_f0_s43_v1/unit_check"
RECOVERED_UNIT_CHECK_ATTEMPT = "2026-09-23T055900469394+0000_23e1f57f"
RECOVERED_UNIT_CHECK_LOG_SHA256 = "697c36c756b8898c7aea6f45338a015b230bd632fe208bd2e4122dd2a026188e"
RECOVERED_ANALYSIS_TASK = "final/analyze"
RECOVERED_ANALYSIS_ATTEMPT = "2026-09-23T164031180513+0000_641174df"
RECOVERED_ANALYSIS_LOG_SHA256 = "b32480cd457013dc77bc877b903dbcb867283abc85d1ce9ae388d306a6c4b7ed"


# Reuse the already-tested durable process engine and arithmetic helpers.
sys.path.insert(0, str(OLD_REVIEW))
import common as legacy
legacy.BACKUP = BACKUP
import coordinator as durable
import seed_checks

spec = importlib.util.spec_from_file_location("matched_fold2_analysis", OLD_REVIEW / "analyze.py")
fold_analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fold_analysis)
base_analysis = fold_analysis.A

sys.path.insert(0, str(SMART))
from src.matched_models005 import forbid_fitting
from src.unit_checkpoint import source_digest

read = legacy.read
atomic = legacy.atomic
append = legacy.append
sha = legacy.sha
now = legacy.now
git = legacy.git


def csv_read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, float_precision="round_trip",
                       dtype={"row_id": str, "group_id": str})


def persistence_comparison(path: Path, columns: list[str]) -> pd.DataFrame:
    """Normalize the two serialized spellings of an absent group identifier."""
    frame = csv_read(path)[columns].copy()
    if "group_id" in frame and set(frame["group_id"].unique()).issubset({"", "None"}):
        frame["group_id"] = ""
    return frame


def key_list() -> list[tuple[str, int, int, int]]:
    q = pd.read_csv(QUEUE, keep_default_na=False)
    return [(r.dataset, int(r.horizon), int(r.outer_fold), int(r.model_seed))
            for r in q.itertuples(index=False)]


def stem(key) -> str:
    return f"{key[0]}_h{key[1]}_f{key[2]}_s{key[3]}_v1"


def paths(key) -> dict:
    name = stem(key)
    return {"key": list(key), "stem": name,
            "design": str(SMART / "protocols" / "matched_forecasting005" / (name + "_core_completion_v1")),
            "run": str(BASE / name)}


def argv(unit, action, receipt=None) -> list[str]:
    ds, horizon, outer, seed = unit["key"]
    command = [PYTHON, "-B", "-m", "src.matched_forecasting005", action,
               "--matrix", str(MATRIX), "--dataset", ds, "--horizon", str(horizon),
               "--outer-fold", str(outer), "--model-seed", str(seed),
               "--design-dir", unit["design"]]
    if action == "freeze":
        command += ["--authorization", str(AUTH)]
    elif action in ("run", "resume", "validate"):
        command += ["--out", unit["run"], "--readiness", str(Path(unit["design"]) / "readiness.json")]
    if receipt is not None:
        command += ["--receipt", str(receipt)]
    return command


def tree_record(path: Path) -> dict:
    rows = []
    total = 0
    for item in sorted(path.rglob("*")):
        if item.is_file():
            relative = item.relative_to(path).as_posix()
            size = item.stat().st_size
            rows.append((relative, size, sha(item)))
            total += size
    digest = hashlib.sha256("\n".join(f"{p}:{n}:{h}" for p, n, h in rows).encode()).hexdigest()
    return {"tree_sha256": digest, "files": len(rows), "bytes": total}


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def normalized_config(config: dict) -> dict:
    value = json.loads(json.dumps(config))
    value["outer_fold"] = 2
    value["model_seed"] = 42
    value["xgboost_fixed"]["random_state"] = 42
    for candidate in value["xgboost_wrapper_parameters"]:
        candidate["random_state"] = 42
    return value


def reconciliation() -> dict:
    matrix = pd.read_csv(MATRIX, keep_default_na=False)
    queue = pd.read_csv(QUEUE, keep_default_na=False)
    overlay = pd.read_csv(PRIOR_ANALYSIS / "completion_overlay.csv", keep_default_na=False)
    own = matrix[matrix.model.isin(MODELS)]
    matrix_keys = set(own[KEYCOLS].itertuples(index=False, name=None))
    completed = set()
    inconsistent = []
    for key, group in overlay[overlay.model.isin(MODELS)].groupby(KEYCOLS):
        flags = group.status.astype(str).str.startswith("completed")
        if flags.all():
            completed.add(tuple(key))
        elif flags.any():
            inconsistent.append(list(key))
    ordered = list(queue[KEYCOLS].itertuples(index=False, name=None))
    pending = set(ordered)
    result = {
        "passed": len(matrix_keys) == 195 and len(completed) == 70 and len(ordered) == len(pending) == 125,
        "matrix_units": len(matrix_keys), "completed_units": len(completed),
        "outstanding_units": len(ordered), "outstanding_distinct_keys": len(pending),
        "completed_queue_overlap": len(completed & pending),
        "union_units": len(completed | pending),
        "unaccounted_matrix_keys": [list(k) for k in sorted(matrix_keys - (completed | pending))],
        "unknown_keys": [list(k) for k in sorted((completed | pending) - matrix_keys)],
        "inconsistent_completion_keys": inconsistent,
        "queue_priority_unique": bool(queue.priority.is_unique),
        "queue_priority_monotonic": bool(queue.priority.is_monotonic_increasing),
        "learned_fit_budget": int(queue.learned_fit_invocations.sum()),
        "tuning_fit_budget": 8 * len(queue), "final_fit_budget": 2 * len(queue),
        "point_cells_to_add": 3 * len(queue), "interval_cells_to_add": 6 * len(queue),
        "first_key": list(ordered[0]), "last_key": list(ordered[-1]),
        "queue_sha256": sha(QUEUE), "matrix_sha256": sha(MATRIX),
    }
    result["passed"] = bool(result["passed"] and result["completed_queue_overlap"] == 0
                            and result["union_units"] == 195 and not inconsistent
                            and not result["unaccounted_matrix_keys"] and not result["unknown_keys"]
                            and result["queue_priority_unique"] and result["queue_priority_monotonic"]
                            and result["learned_fit_budget"] == 1250)
    return result


def prepare() -> None:
    os.chdir(SMART)
    if git("branch", "--show-current") != BRANCH or git("rev-parse", HEAD := "HEAD") != ENTRY:
        raise ValueError("pre-fit preparation must start on the dedicated branch at the delivery entry")
    if source_digest() != SOURCE_HASH:
        raise ValueError("scientific source digest changed")
    BATCH.mkdir(parents=True, exist_ok=True)
    BACKUP.mkdir(parents=True, exist_ok=True)
    rec = reconciliation()
    if not rec["passed"]:
        raise ValueError("matrix reconciliation failed: " + json.dumps(rec))
    queue = pd.read_csv(QUEUE, keep_default_na=False)
    expected_auth = {
        "version": "matched_forecasting005_core_completion_125_v1",
        "authorization_source": "user attachment d5652872-75f0-47f3-ae11-6f6a2b19abcc",
        "entry_commit": ENTRY, "real_fitting_authorized": True,
        "allowed_units": [list(k) for k in key_list()], "models": MODELS,
        "nominal_levels": LEVELS, "tuning_fit_budget": 1000, "final_fit_budget": 250,
        "historical_refits_authorized": False, "additional_experiments_authorized": False,
        "nonblocking_launch_ram": True,
        "resource_policy": "CPU only; one numerical/Torch thread; n_jobs=1; lazy batch256; 256 MiB epoch floor; 8 GiB disk floor",
        "execution_order": "exact remaining_queue_updated.csv order; advance only after validation, group arithmetic and zero-fit resume",
        "provenance_note": "Runner parent/instruction fields remain historical; this versioned authorization is the current execution authority.",
    }
    if AUTH.exists():
        if read(AUTH) != expected_auth:
            raise ValueError("saved authorization differs")
    else:
        atomic(AUTH, expected_auth)
    disk = shutil.disk_usage(SMART)
    capacity = {"passed": disk.free >= REQUIRED_FREE_BYTES, "utc": now(),
                "shared_volume": str(SMART.drive or "C:"), "free_bytes": disk.free,
                "projected_new_raw_run_bytes": PROJECTED_RUN_BYTES,
                "copy_factor_for_raw_package_git_pack_backup_and_transient": 5,
                "metadata_and_protocol_allowance_bytes": 2 * 2**30,
                "disk_floor_bytes": DISK_FLOOR, "required_free_bytes": REQUIRED_FREE_BYTES,
                "estimate_basis": "dataset-specific mean output bytes from 52 accepted comparable runs times the 125-key dataset mix; not the temperature estimate"}
    atomic(REVIEW / "CAPACITY_DECISION.json", capacity)
    if not capacity["passed"]:
        raise OSError("capacity gate failed")
    atomic(REVIEW / "SCOPE_RECONCILIATION.json", {**rec, "utc": now(), "source_hash": source_digest()})
    probes = seed_checks.preflight()
    atomic(REVIEW / "NO_FIT_CORRECTNESS.json", {
        **probes, "reused_regression_checks": 30,
        "reused_regression_commit": PRIOR_EVALUATED,
        "reason": "forecasting runner/model/validator dependencies are unchanged from the evaluated 30-check receipt",
        "tiny_fits": 0,
    })
    baseline_ledger = pd.read_csv(PRIOR_ANALYSIS / "evidence_reuse_ledger.csv", keep_default_na=False)
    protocol_paths = {sha(path): path for path in (SMART / "protocols" / "matched_forecasting005").glob("*/frozen_protocol.json")}
    baselines = {}
    for row in baseline_ledger.itertuples(index=False):
        if int(row.outer_fold) == 2 and int(row.model_seed) == 42:
            baselines[(row.dataset, int(row.horizon))] = read(protocol_paths[row.protocol_hash])
    if len(baselines) != 13:
        raise ValueError("missing fold-2 seed-42 protocol baselines")
    scope = queue.copy()
    scope["batch_order"] = range(1, 126)
    scope["authorization_version"] = expected_auth["version"]
    scope.to_csv(REVIEW / "FROZEN_SCOPE.csv", index=False)
    units = []
    with forbid_fitting() as fit_calls:
        for order, key in enumerate(key_list(), 1):
            unit = paths(key)
            run = Path(unit["run"])
            if run.exists():
                raise ValueError(f"unexpected queued output requires reconciliation: {key}")
            design = Path(unit["design"])
            for action in ("freeze", "readiness"):
                log = BATCH / "preflight_v2" / f"{order:03d}_{action}.log"
                command = argv(unit, action)
                atomic(BATCH / "preflight_progress.json", {"status": "running", "order": order,
                       "planned": 125, "key": list(key), "phase": action, "models_fitted": 0, "utc": now()})
                receipt_path = Path(str(log) + ".json")
                if receipt_path.exists():
                    receipt = read(receipt_path)
                    if receipt["exit_status"] != 0 or receipt["command"] != command:
                        raise ValueError("preflight receipt mismatch: " + str(log))
                else:
                    if log.exists() or (action == "freeze" and design.exists()) or (action == "readiness" and (design / "readiness.json").exists()):
                        raise ValueError("incomplete preflight requires inspection: " + str(log))
                    legacy.logged(command, log)
            protocol_path = design / "frozen_protocol.json"
            ready_path = design / "readiness.json"
            protocol, ready = read(protocol_path), read(ready_path)
            if protocol["source_hash"] != SOURCE_HASH or not ready["first_unit_ready"] or ready["models_fitted"] != 0:
                raise ValueError("protocol/readiness identity failure")
            baseline = baselines[(key[0], key[1])]
            if normalized_config(protocol["config"]) != baseline["config"]:
                raise ValueError("non-key scientific configuration changed")
            for field in ("data_hash", "feature_names", "sequence_channels", "eligible_rows", "excluded_rows", "frequency", "target"):
                if protocol["support"][field] != baseline["support"][field]:
                    raise ValueError("dataset/schema support changed: " + field)
            selected = queue.iloc[order - 1]
            if tuple(selected[c] for c in KEYCOLS) != key:
                raise ValueError("queue order changed")
            unit.update(order=order, protocol_hash=sha(protocol_path), readiness_hash=sha(ready_path),
                        source_hash=protocol["source_hash"], data_hash=protocol["support"]["data_hash"],
                        role_bank_hash=protocol["support"]["role_bank_hash"],
                        commands={"run": argv(unit, "run"),
                                  "validate": argv(unit, "validate", BATCH / "receipts" / unit["stem"] / "audit_v1"),
                                  "resume": argv(unit, "resume", BATCH / "receipts" / unit["stem"] / "resume_v1.json") + ["--forbid-fits"]})
            units.append(unit)
            print(f"PREFLIGHT {order}/125 {unit['stem']}", flush=True)
    if fit_calls:
        raise AssertionError("pre-fit route invoked fitting")
    manifest = {"passed": True, "utc": now(), "entry_commit": ENTRY, "source_hash": source_digest(),
                "matrix_sha256": sha(MATRIX), "queue_sha256": sha(QUEUE), "scope_sha256": sha(REVIEW / "FROZEN_SCOPE.csv"),
                "authorization_sha256": sha(AUTH), "capacity_sha256": sha(REVIEW / "CAPACITY_DECISION.json"),
                "units": units, "planned_units": 125, "planned_tuning_fits": 1000,
                "planned_final_fits": 250, "all_frozen_before_any_fit": True,
                "historical_units_reused": 70, "historical_refits": 0, "full_study_ready": False}
    atomic(REVIEW / "FROZEN_BATCH_MANIFEST.json", manifest)
    atomic(REVIEW / "PREFIT_VALIDATION.json", {"passed": True, "models_fitted": 0,
           "units_frozen_and_ready": 125, "matrix_reconciled": True, "fit_budget": 1250,
           "source_hash": source_digest(), "reused_regression_checks": 30})
    atomic(BATCH / "preflight_progress.json", {"status": "all_125_ready", "models_fitted": 0, "utc": now()})
    print("ALL 125 OUTSTANDING UNITS FROZEN AND READY; ZERO FITS", flush=True)


def verify_frozen(manifest: dict) -> None:
    if source_digest() != SOURCE_HASH or manifest["source_hash"] != SOURCE_HASH:
        raise ValueError("scientific source changed")
    if [tuple(u["key"]) for u in manifest["units"]] != key_list() or len(manifest["units"]) != 125:
        raise ValueError("frozen queue changed")
    for path, expected in ((MATRIX, manifest["matrix_sha256"]), (QUEUE, manifest["queue_sha256"]),
                           (AUTH, manifest["authorization_sha256"]), (REVIEW / "FROZEN_SCOPE.csv", manifest["scope_sha256"])):
        if sha(path) != expected:
            raise ValueError("frozen input changed: " + str(path))
    for unit in manifest["units"]:
        if sha(Path(unit["design"]) / "frozen_protocol.json") != unit["protocol_hash"]:
            raise ValueError("protocol changed: " + unit["stem"])
        if sha(Path(unit["design"]) / "readiness.json") != unit["readiness_hash"]:
            raise ValueError("readiness changed: " + unit["stem"])


def progress(engine, manifest) -> None:
    accepted = [u for u in manifest["units"] if engine.state["units"].get(u["stem"], {}).get("accepted")]
    pending = [u["key"] for u in manifest["units"] if u not in accepted]
    durations = [engine.state["units"][u["stem"]]["total_phase_seconds"] for u in accepted]
    eta = float(np.mean(durations) * len(pending)) if durations else None
    engine.state.update(accepted_units=len(accepted), planned_units=125, cumulative_units=70 + len(accepted),
                        pending_keys=pending, new_tuning_fits=8 * len(accepted), new_final_fits=2 * len(accepted),
                        new_point_cells=3 * len(accepted), new_interval_cells=6 * len(accepted),
                        completed_zero_fit_resumes=len(accepted), estimated_remaining_seconds=eta,
                        full_study_ready=False, restart_argv=[PYTHON, "-B", str(REVIEW / "batch.py"), "coordinate"])
    engine.save()
    active = engine.state.get("active") or {}
    body = "# Matched-forecasting core-completion progress\n\n"
    body += f"Updated UTC: {now()}. Status: **{engine.state['status']}**. Accepted **{len(accepted)}/125 new units**; cumulative **{70 + len(accepted)}/195**.\n\n"
    body += f"Active task: `{active.get('task', 'none')}`; logger PID: `{active.get('logger_pid', 'none')}`; worker identity: `{json.dumps(active.get('worker_identity')) if active.get('worker_identity') else 'none'}`.\n\n"
    body += "Measured ETA after completed units: " + (f"{eta/3600:.2f} hours" if eta is not None else "pending first accepted unit") + ". This is a rolling execution estimate, not a deadline.\n\n"
    body += "Restart command:\n\n```powershell\nC:/cfs_venv/Scripts/python.exe -B review/matched_forecasting005_completion_20260923/batch.py coordinate\n```\n\n"
    body += "Completed checkpoints are identity-verified and reused. A recorded failed scientific command is not retried automatically.\n"
    atomic(REVIEW / "PROGRESS_AND_RESTART.md", body)
    BACKUP.mkdir(parents=True, exist_ok=True)
    atomic(BACKUP / "latest_progress.json", engine.state)


def canonical_persistence_run(key, manifest) -> tuple[Path | None, list | None]:
    ledger = pd.read_csv(PRIOR_ANALYSIS / "evidence_reuse_ledger.csv", keep_default_na=False)
    rows = ledger[(ledger.dataset == key[0]) & (ledger.horizon == key[1]) & (ledger.outer_fold == key[2])]
    if len(rows):
        row = rows.sort_values("model_seed").iloc[0]
        return ROOT / row.run_path, [row.dataset, int(row.horizon), int(row.outer_fold), int(row.model_seed)]
    for unit in manifest["units"]:
        other = unit["key"]
        if other[:3] == key[:3] and other[3] < key[3] and (Path(unit["run"]) / "run_summary.json").exists():
            return Path(unit["run"]), other
    return None, None


def unit_check(stem_name: str, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    manifest = read(REVIEW / "FROZEN_BATCH_MANIFEST.json")
    unit = next(row for row in manifest["units"] if row["stem"] == stem_name)
    key = unit["key"]
    with forbid_fitting() as attempts:
        result = base_analysis.summarize(unit["run"], key, new=True)
        for name, rows in result.items():
            pd.DataFrame(rows).to_csv(output / (name + ".csv"), index=False)
        seeds = seed_checks.unit(unit)
        pd.DataFrame(seeds).to_csv(output / "actual_seed_metadata.csv", index=False)
        baseline_run, baseline_key = canonical_persistence_run(key, manifest)
        alias_status = "baseline_established"
        if baseline_run is not None:
            prior = base_analysis.model_dir(baseline_run, baseline_key, "persistence")
            current = base_analysis.model_dir(unit["run"], key, "persistence")
            for filename, columns in (("calibration.csv.gz", ["row_id", "group_id", "origin_time", "target_time", "y_true", "point", "absolute_error"]),
                                      ("predictions.csv.gz", ["row_id", "group_id", "origin_time", "target_time", "y_true", "point", "nominal_level", "lower", "upper"])):
                pd.testing.assert_frame_equal(persistence_comparison(prior / filename, columns),
                                              persistence_comparison(current / filename, columns),
                                              check_exact=True)
            alias_status = "exact_against_canonical"
    if attempts:
        raise AssertionError("unit check invoked fitting")
    atomic(output / "validation.json", {"passed": True, "models_fitted": 0,
           "group_to_pooled_reconstruction": True, "actual_seed_verified": True,
           "persistence_alias_status": alias_status, "persistence_canonical_key": baseline_key,
           "key": key, "source_hash": unit["source_hash"], "protocol_hash": unit["protocol_hash"]})


def accept(unit, engine) -> dict:
    name = unit["stem"]
    validation_task = engine.state["tasks"][name + "/validate"]
    resume_task = engine.state["tasks"][name + "/resume"]
    unit_task = engine.state["tasks"][name + "/unit_check"]
    audit = Path(validation_task["argv"][validation_task["argv"].index("--receipt") + 1])
    resume = Path(resume_task["argv"][resume_task["argv"].index("--receipt") + 1])
    checked = Path(unit_task["argv"][unit_task["argv"].index("--out") + 1])
    a, r, u = read(audit / "validation.json"), read(resume), read(checked / "validation.json")
    expected = {"point_cells": 3, "interval_cells": 6, "real_tuning_fits_verified": 8,
                "real_final_fits_verified": 2, "saved_model_prediction_checks": 6}
    if not a["passed"] or any(a[k] != value for k, value in expected.items()) or a["models_fitted"] != 0 or not a["all_run_files_unchanged"]:
        raise ValueError("independent unit validation failed")
    if r["models_fitted"] != 0 or r["reused_model_units"] != 3 or not r["all_run_files_unchanged"]:
        raise ValueError("completed zero-fit resume failed")
    if not u["passed"] or not u["actual_seed_verified"]:
        raise ValueError("unit arithmetic/seed check failed")
    journal = [json.loads(line) for line in (Path(unit["run"]) / "fit_calls.jsonl").read_text().splitlines()]
    starts = [row for row in journal if row["event"] == "started"]
    ends = [row for row in journal if row["event"] == "complete"]
    if len(starts) != len(ends) or len(ends) != 10:
        raise ValueError("fit-attempt budget/reconciliation failure")
    tree = tree_record(Path(unit["run"]))
    seconds = sum(engine.state["tasks"][name + "/" + phase]["seconds"] for phase in ("run", "validate", "resume", "unit_check"))
    return {"accepted": True, "utc": now(), "audit": str(audit), "resume": str(resume),
            "unit_check": str(checked), "tree": tree, "tuning_fits": 8, "final_fits": 2,
            "point_cells": 3, "interval_cells": 6, "saved_model_checks": 6,
            "zero_fit_resume": True, "total_phase_seconds": seconds}


def recover_investigated_unit_check(engine) -> bool:
    """Permit one zero-fit rerun after the documented null-spelling comparison bug."""
    record = engine.state["tasks"].get(RECOVERED_UNIT_CHECK_TASK)
    if not record or record.get("status") != "failed":
        return False
    if record.get("attempt_id") != RECOVERED_UNIT_CHECK_ATTEMPT:
        return False
    if sha(Path(record["log"])) != RECOVERED_UNIT_CHECK_LOG_SHA256:
        raise ValueError("investigated unit-check failure log changed")
    stem = RECOVERED_UNIT_CHECK_TASK.split("/")[0]
    for phase in ("run", "validate", "resume"):
        prior = engine.state["tasks"].get(stem + "/" + phase)
        if not prior or prior.get("status") != "passed":
            raise ValueError("cannot recover unit check before passed " + phase)
    audit = read(BATCH / "receipts" / stem / "audit_v1" / "validation.json")
    resume = read(BATCH / "receipts" / stem / "resume_v1.json")
    if not audit["passed"] or audit["real_tuning_fits_verified"] != 8 or audit["real_final_fits_verified"] != 2:
        raise ValueError("existing validator did not accept investigated unit")
    if audit["models_fitted"] != 0 or not audit["all_run_files_unchanged"]:
        raise ValueError("validation mutated investigated run")
    if resume["models_fitted"] != 0 or resume["reused_model_units"] != 3 or not resume["all_run_files_unchanged"]:
        raise ValueError("completed resume was not zero-fit and immutable")
    journal = [json.loads(line) for line in (BASE / stem / "fit_calls.jsonl").read_text().splitlines()]
    if sum(row["event"] == "started" for row in journal) != 10 or sum(row["event"] == "complete" for row in journal) != 10:
        raise ValueError("investigated unit fit journal is not exactly complete")
    failure = {"utc": now(), "failure": engine.state.pop("failure"),
               "traceback": engine.state.pop("traceback", None)}
    engine.state.setdefault("previous_failures", []).append(failure)
    engine.state.setdefault("investigated_failures", []).append({
        **record,
        "investigation": "historical empty string and current literal None both encode an absent group_id",
        "recovery": "normalize absent group_id only in the orchestration comparison; rerun unit_check only",
    })
    record = {**record, "status": "investigated_retry_authorized",
              "recovery_utc": now(), "scientific_commands_reused": ["run", "validate", "resume"]}
    engine.state["tasks"][RECOVERED_UNIT_CHECK_TASK] = record
    append(BATCH / "attempts.jsonl", {"event": "investigated_routine_failure", **failure,
           "task": RECOVERED_UNIT_CHECK_TASK, "attempt_id": RECOVERED_UNIT_CHECK_ATTEMPT})
    engine.save()
    return True


def recover_investigated_analysis(engine) -> bool:
    """Permit one zero-fit retry after the documented derived-column merge bug."""
    record = engine.state["tasks"].get(RECOVERED_ANALYSIS_TASK)
    if not record or record.get("status") != "failed":
        return False
    if record.get("attempt_id") != RECOVERED_ANALYSIS_ATTEMPT:
        return False
    if sha(Path(record["log"])) != RECOVERED_ANALYSIS_LOG_SHA256:
        raise ValueError("investigated analysis failure log changed")
    manifest = read(REVIEW / "FROZEN_BATCH_MANIFEST.json")
    accepted = [u for u in manifest["units"] if engine.state["units"].get(u["stem"], {}).get("accepted")]
    if len(accepted) != 125:
        raise ValueError("analysis recovery requires all 125 accepted units")
    if sum(engine.state["units"][u["stem"]]["tuning_fits"] for u in accepted) != 1000:
        raise ValueError("analysis recovery tuning-fit reconciliation failed")
    if sum(engine.state["units"][u["stem"]]["final_fits"] for u in accepted) != 250:
        raise ValueError("analysis recovery final-fit reconciliation failed")
    if ANALYSIS.exists() and any(ANALYSIS.iterdir()):
        raise ValueError("failed analysis left nonempty destination")
    failure = {"utc": now(), "failure": engine.state.pop("failure"),
               "traceback": engine.state.pop("traceback", None)}
    engine.state.setdefault("previous_failures", []).append(failure)
    engine.state.setdefault("investigated_failures", []).append({
        **record,
        "investigation": "historical rows had derived coverage-deviation columns and new rows did not",
        "recovery": "drop and recompute derived columns for all 585 point cells; rerun zero-fit analysis only",
    })
    record = {**record, "status": "investigated_retry_authorized",
              "recovery_utc": now(), "accepted_scientific_units_reused": 125}
    engine.state["tasks"][RECOVERED_ANALYSIS_TASK] = record
    append(BATCH / "attempts.jsonl", {"event": "investigated_routine_failure", **failure,
           "task": RECOVERED_ANALYSIS_TASK, "attempt_id": RECOVERED_ANALYSIS_ATTEMPT})
    engine.save()
    return True


def coordinate() -> None:
    os.chdir(SMART)
    BACKUP.mkdir(parents=True, exist_ok=True)
    with durable.exclusive_lock(BACKUP / "coordinator.lock"):
        manifest = read(REVIEW / "FROZEN_BATCH_MANIFEST.json")
        evaluated = read(REVIEW / "EVALUATED_COMMIT.json")
        if git("branch", "--show-current") != BRANCH:
            raise ValueError("wrong branch")
        subprocess.run(["git", "merge-base", "--is-ancestor", evaluated["commit"], "HEAD"], cwd=ROOT, check=True)
        verify_frozen(manifest)
        engine = durable.Engine(BATCH)
        try:
            recovered = (recover_investigated_unit_check(engine) or recover_investigated_analysis(engine)) if engine.state.get("failure") else False
            if engine.state.get("failure") and not recovered:
                previous = {"utc": now(), "failure": engine.state.pop("failure"), "traceback": engine.state.pop("traceback", None)}
                engine.state.setdefault("previous_failures", []).append(previous)
                append(BATCH / "attempts.jsonl", {"event": "coordinator_restart", **previous})
            engine.reconcile()
            for unit in manifest["units"]:
                name = unit["stem"]
                prior = engine.state["units"].get(name)
                if prior and prior.get("accepted"):
                    if tree_record(Path(unit["run"])) != prior["tree"]:
                        raise ValueError("accepted run changed: " + name)
                    continue
                verify_frozen(manifest)
                from src.pilot_resources import memory_snapshot
                resources = {"utc": now(), "key": unit["key"], "free_disk_bytes": shutil.disk_usage(SMART).free,
                             "available_ram_bytes": memory_snapshot()["available_ram_bytes"], "disk_floor_bytes": DISK_FLOOR}
                if resources["free_disk_bytes"] < DISK_FLOOR:
                    raise OSError("8 GiB disk floor violated")
                append(BATCH / "resources.jsonl", resources)
                engine.state["status"] = "running_units"
                progress(engine, manifest)
                def run_command(folder):
                    action = "resume" if (Path(unit["run"]) / "checkpoint_manifest.json").exists() else "run"
                    return argv(unit, action, folder / "partial_resume.json" if action == "resume" else None)
                engine.phase(name + "/run", run_command)
                def receipt_command(action, folder):
                    planned = unit["commands"][action]
                    receipt = Path(planned[planned.index("--receipt") + 1])
                    if receipt.exists():
                        return argv(unit, "validate", folder / "audit") if action == "validate" else argv(unit, "resume", folder / "resume.json") + ["--forbid-fits"]
                    return planned
                engine.phase(name + "/validate", lambda folder: receipt_command("validate", folder))
                engine.phase(name + "/resume", lambda folder: receipt_command("resume", folder))
                engine.phase(name + "/unit_check", lambda folder: [PYTHON, "-B", str(REVIEW / "batch.py"), "unit", "--stem", name, "--out", str(folder / "unit")])
                engine.state["units"][name] = accept(unit, engine)
                engine.state["status"] = "unit_accepted"
                progress(engine, manifest)
                print(f"ACCEPTED {unit['order']}/125 {name}", flush=True)
            engine.state["status"] = "analyzing"
            progress(engine, manifest)
            engine.phase("final/analyze", lambda folder: [PYTHON, "-B", str(REVIEW / "batch.py"), "analyze"])
            engine.phase("final/validate_analysis", lambda folder: [PYTHON, "-B", str(REVIEW / "batch.py"), "validate-analysis"])
            engine.state["status"] = "packaging"
            progress(engine, manifest)
            engine.phase("final/package", lambda folder: [PYTHON, "-B", str(REVIEW / "batch.py"), "package"])
            engine.state["status"] = "science_and_evidence_complete"
            progress(engine, manifest)
            print("ALL 125 UNITS, CUMULATIVE ANALYSIS, VALIDATION AND PACKAGING COMPLETE", flush=True)
        except BaseException as exc:
            engine.state.update(status="blocked", failure=str(exc), traceback=traceback.format_exc())
            progress(engine, manifest)
            print(engine.state["traceback"], flush=True)
            raise


def write_frame(path: Path, frame) -> None:
    pd.DataFrame(frame).to_csv(path, index=False)


def model_owner(run: Path, key, model: str) -> tuple[Path, Path]:
    directory = base_analysis.model_dir(run, key, model)
    matches = list(directory.glob({"persistence": "model.json", "xgboost": "model.ubj", "attention_lstm": "model.pt"}[model]))
    if len(matches) != 1:
        raise ValueError("model owner artifact missing")
    return directory, matches[0]


def analyze() -> None:
    if ANALYSIS.exists():
        if any(ANALYSIS.iterdir()):
            raise ValueError("analysis destination already exists and is nonempty")
    else:
        ANALYSIS.mkdir(parents=True)
    manifest = read(REVIEW / "FROZEN_BATCH_MANIFEST.json")
    state = read(BATCH / "progress.json")
    if sum(bool(state["units"].get(u["stem"], {}).get("accepted")) for u in manifest["units"]) != 125:
        raise ValueError("analysis requires all 125 accepted units")
    table_names = ["comparison", "group_metrics", "rico_phase_metrics", "equal_group_diagnostics", "model_costs", "target_diagnostics"]
    combined = {}
    prior_names = {"comparison": "combined_comparison.csv", **{name: name + ".csv" for name in table_names if name != "comparison"}}
    for name in table_names:
        combined[name] = csv_read(PRIOR_ANALYSIS / prior_names[name]).to_dict("records")
    new_costs, verification, fits, command_rows = [], [], [], []
    for unit in manifest["units"]:
        name, key, run = unit["stem"], unit["key"], Path(unit["run"])
        done = state["units"][name]
        if tree_record(run) != done["tree"]:
            raise ValueError("accepted run changed")
        group_dir = Path(done["unit_check"])
        for table in table_names:
            path = group_dir / (table + ".csv")
            if path.stat().st_size > 2:
                combined[table].extend(csv_read(path).to_dict("records"))
        audit = read(Path(done["audit"]) / "validation.json")
        rr, vr, zr = (state["tasks"][name + "/" + phase] for phase in ("run", "validate", "resume"))
        proc_path = Path(str(run) + ".process.json")
        if not proc_path.exists():
            proc_path = Path(rr["argv"][rr["argv"].index("--receipt") + 1] + ".process.json")
        proc = read(proc_path)
        env = read(run / "execution_environment.json")
        meta = dict(zip(KEYCOLS, key), source_run=run.relative_to(ROOT).as_posix(),
                    source_hash=unit["source_hash"], protocol_hash=unit["protocol_hash"],
                    target_units=UNITS[key[0]], physical_minutes=key[1] * MINUTES[key[0]])
        new_costs.append({**meta, "command_seconds": rr["seconds"], "process_cpu_seconds": proc["process_lifetime_cpu_seconds"],
                          "preparation_seconds": env["preparation_resources"]["seconds"],
                          "action_peak_rss_MiB": proc["action_resources"]["peak_rss_bytes"] / 2**20,
                          "lifetime_peak_rss_MiB": proc["ending_memory"]["lifetime_peak_rss_bytes"] / 2**20,
                          "validation_seconds": vr["seconds"], "validation_cpu_seconds": audit["total_validation_resources"]["process_cpu_seconds"],
                          "resume_seconds": zr["seconds"], "output_bytes": done["tree"]["bytes"]})
        reloaded = csv_read(Path(done["audit"]) / "saved_model_verification.csv")
        verification.append({**meta, "actual_exit": rr["exit_code"], "point_cells": 3, "interval_cells": 6,
                             "tuning_fits": 8, "final_fits": 2, "saved_model_checks": len(reloaded),
                             "max_absolute_prediction_difference": float(reloaded.max_absolute_difference.max()),
                             "completed_resume_fits": 0, "all_run_files_unchanged": True,
                             "actual_seed_verified": True, "audit": done["audit"], "resume": done["resume"]})
        fits.extend({**meta, **json.loads(line)} for line in (run / "fit_calls.jsonl").read_text().splitlines())
    for task, row in state["tasks"].items():
        command_rows.append({"task": task, **{field: row.get(field) for field in ("attempt_id", "argv", "cwd", "started_utc", "ended_utc", "exit_code", "logger_pid", "child_pid", "seconds", "log")}})
    frame = pd.DataFrame(combined["comparison"])
    derived = [f"{kind}_coverage_deviation{level}" for level in (90, 95)
               for kind in ("signed", "absolute")] + ["deterministic_baseline_alias"]
    frame = fold_analysis.add_deviations(frame.drop(columns=derived, errors="ignore"))
    if len(frame) != 585 or frame.duplicated(KEYCOLS + ["model"]).any():
        raise ValueError("cumulative point-cell coverage failure")
    actual_keys = set(frame[KEYCOLS].itertuples(index=False, name=None))
    matrix = pd.read_csv(MATRIX, keep_default_na=False)
    expected_keys = set(matrix[matrix.model.isin(MODELS)][KEYCOLS].itertuples(index=False, name=None))
    if actual_keys != expected_keys or len(actual_keys) != 195:
        raise ValueError("cumulative unit-key mismatch")
    write_frame(ANALYSIS / "all_unit_model_metrics.csv", frame)
    write_frame(ANALYSIS / "new_unit_model_metrics.csv", frame[frame.new_batch_unit == True])
    pairs = fold_analysis.paired(frame)
    write_frame(ANALYSIS / "paired_model_contrasts.csv", pairs)
    intervals = []
    for row in frame.to_dict("records"):
        for level in (90, 95):
            intervals.append({**{k: row[k] for k in [*KEYCOLS, "model", "physical_minutes", "target_units", "source_run", "source_hash", "protocol_hash", "n_calibration", "n_test", "deterministic_baseline_alias"]},
                              "nominal_level": level / 100,
                              **{metric: row[f"{metric}{level}"] for metric in ("coverage", "signed_coverage_deviation", "absolute_coverage_deviation", "mpiw", "winkler", "q", "rank")}})
    write_frame(ANALYSIS / "all_interval_cells.csv", intervals)
    for name in table_names:
        if name != "comparison":
            write_frame(ANALYSIS / (name + ".csv"), combined[name])
    seed_summary = fold_analysis.variability(frame)
    write_frame(ANALYSIS / "seed_within_fold_summary.csv", seed_summary)
    numeric = ["mae", "rmse", "coverage90", "coverage95", "mpiw90", "mpiw95", "winkler90", "winkler95", "model_phase_seconds", "process_cpu_seconds"]
    fold_means = frame.groupby(["dataset", "horizon", "outer_fold", "model"], as_index=False)[numeric].mean()
    fold_means["aggregation"] = "mean across five training seeds within one outer fold; descriptive only"
    write_frame(ANALYSIS / "fold_seed_means.csv", fold_means)
    cumulative = fold_means.groupby(["dataset", "horizon", "model"], as_index=False)[numeric].mean()
    cumulative["physical_minutes"] = cumulative.horizon * cumulative.dataset.map(MINUTES)
    cumulative["aggregation"] = "equal mean of three outer-fold seed means; overlapping folds; descriptive only"
    write_frame(ANALYSIS / "cumulative_descriptive_summary.csv", cumulative)
    inference = cumulative[["dataset", "horizon", "model", "physical_minutes"]].copy()
    inference["population_interval_status"] = "unavailable"
    inference["reason"] = "prespecified design supplies descriptive paired fold/seed results only; overlapping folds, training seeds and deterministic persistence aliases are not independent population samples"
    inference["lower"] = ""
    inference["upper"] = ""
    write_frame(ANALYSIS / "inference_status.csv", inference)
    write_frame(ANALYSIS / "new_run_costs.csv", new_costs)
    write_frame(ANALYSIS / "new_verification_summary.csv", verification)
    write_frame(ANALYSIS / "new_fit_attempts.csv", fits)
    write_frame(ANALYSIS / "command_attempts.csv", command_rows)
    overlay = pd.read_csv(PRIOR_ANALYSIS / "completion_overlay.csv", keep_default_na=False)
    remaining = pd.read_csv(QUEUE, keep_default_na=False)
    for unit in manifest["units"]:
        mask = pd.Series(True, index=overlay.index)
        qmask = pd.Series(True, index=remaining.index)
        for column, value in zip(KEYCOLS, unit["key"]):
            mask &= overlay[column] == value
            qmask &= remaining[column] == value
        mask &= overlay.model.isin(MODELS)
        if mask.sum() != 6 or overlay.loc[mask, "status"].str.startswith("completed").any() or qmask.sum() != 1:
            raise ValueError("completion overlay mismatch")
        overlay.loc[mask, "status"] = "completed_verified_core_completion_125_v1"
        overlay.loc[mask, "reason"] = "existing validator, saved-stream/group arithmetic, owner/seed checks and zero-fit resume"
        overlay.loc[mask, "preserved_path"] = Path(unit["run"]).relative_to(SMART).as_posix()
        remaining = remaining[~qmask]
    own_overlay = overlay[overlay.model.isin(MODELS)]
    if len(remaining) or len(own_overlay) != 1170 or not own_overlay.status.str.startswith("completed").all():
        raise ValueError("final completion coverage failure")
    write_frame(ANALYSIS / "completion_overlay_195.csv", overlay)
    write_frame(ANALYSIS / "remaining_queue_empty.csv", remaining)
    build_reuse_ledger(frame, manifest, state)
    make_figures(frame, cumulative)
    fit_frame = pd.DataFrame(fits)
    starts, ends = fit_frame[fit_frame.event == "started"], fit_frame[fit_frame.event == "complete"]
    if len(starts) != len(ends) or len(ends) != 1250 or (ends.phase == "tuning").sum() != 1000 or (ends.phase == "final_fit").sum() != 250:
        raise ValueError("aggregate fit journal mismatch")
    summary = {"passed": True, "status": "complete", "new_paired_units": 125,
               "new_tuning_fits": 1000, "new_final_fits": 250, "new_point_cells": 375,
               "new_interval_cells": 750, "saved_model_checks": 750,
               "completed_zero_fit_resumes": 125, "completed_paired_units": 195,
               "total_paired_units": 195, "completed_point_cells": 585,
               "completed_interval_cells": 1170, "remaining_paired_units": 0,
               "historical_units_reused": 70, "historical_refits": 0,
               "repeated_or_failed_learned_fits": 0,
               "maximum_prediction_difference": max(row["max_absolute_prediction_difference"] for row in verification),
               "new_run_wall_seconds": sum(row["command_seconds"] for row in new_costs),
               "new_run_cpu_seconds": sum(row["process_cpu_seconds"] for row in new_costs),
               "new_validation_wall_seconds": sum(row["validation_seconds"] for row in new_costs),
               "new_resume_wall_seconds": sum(row["resume_seconds"] for row in new_costs),
               "maximum_lifetime_peak_rss_MiB": max(row["lifetime_peak_rss_MiB"] for row in new_costs),
               "source_hash": SOURCE_HASH, "population_intervals_available": False,
               "full_study_ready": False}
    atomic(ANALYSIS / "analysis_validation.json", summary)
    write_report(cumulative, pd.DataFrame(pairs), summary)
    atomic(ANALYSIS / "COMPLETE.json", {"passed": True, "models_fitted": 0,
           "files": {p.relative_to(ANALYSIS).as_posix(): sha(p) for p in sorted(ANALYSIS.rglob("*")) if p.is_file()}})
    print(json.dumps(summary, indent=2), flush=True)


def build_reuse_ledger(frame: pd.DataFrame, manifest: dict, state: dict) -> None:
    prior = pd.read_csv(PRIOR_ANALYSIS / "evidence_reuse_ledger.csv", keep_default_na=False)
    prior_by_key = {tuple(row[c] for c in KEYCOLS): row for _, row in prior.iterrows()}
    protocols = {sha(path): path for path in (SMART / "protocols" / "matched_forecasting005").glob("*/frozen_protocol.json")}
    rows = []
    for key, group in frame.groupby(KEYCOLS):
        key = (key[0], int(key[1]), int(key[2]), int(key[3]))
        source_run = ROOT / group.source_run.iloc[0]
        source_hash_value = group.source_hash.iloc[0]
        protocol_hash = group.protocol_hash.iloc[0]
        is_new = key not in prior_by_key
        if is_new:
            unit = next(u for u in manifest["units"] if tuple(u["key"]) == key)
            evaluated_commit = read(source_run / "execution_environment.json")["code_commit"]
            acceptance = state["units"][unit["stem"]]["audit"] + "/validation.json"
            run_tree = state["units"][unit["stem"]]["tree"]["tree_sha256"]
        else:
            old = prior_by_key[key]
            evaluated_commit = old.evaluated_commit
            acceptance = str((PRIOR_ANALYSIS / "evidence_reuse_ledger.csv").relative_to(ROOT)) + "#" + "|".join(map(str, key))
            run_tree = old.run_file_tree_hash
        for model in MODELS:
            owner_dir, owner = model_owner(source_run, key, model)
            rows.append({"dataset": key[0], "horizon": key[1], "outer_fold": key[2], "model_seed": key[3],
                         "model": model, "run_path": source_run.relative_to(ROOT).as_posix(),
                         "run_tree_sha256": run_tree, "protocol_path": protocols.get(protocol_hash, Path("")).relative_to(ROOT).as_posix() if protocol_hash in protocols else "historical protocol identified by hash",
                         "protocol_sha256": protocol_hash, "source_sha256": source_hash_value,
                         "evaluated_commit": evaluated_commit, "model_owner_path": owner.relative_to(ROOT).as_posix(),
                         "model_owner_sha256": sha(owner), "model_owner_complete_sha256": sha(owner_dir / "COMPLETE.json"),
                         "acceptance_reference": acceptance, "historical_reuse": not is_new,
                         "historical_refits": 0})
    ledger = pd.DataFrame(rows)
    if len(ledger) != 585 or ledger.duplicated(KEYCOLS + ["model"]).any():
        raise ValueError("cumulative reuse ledger coverage failure")
    write_frame(ANALYSIS / "cumulative_completion_reuse_ledger.csv", ledger)


def make_figures(frame: pd.DataFrame, cumulative: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figure_dir = ANALYSIS / "figures"
    figure_dir.mkdir()
    for name, metric, ylabel, nominal in (("mae_by_fold", "mae", "MAE", None),
                                           ("coverage95_by_fold", "coverage95", "Achieved 95% coverage", 0.95),
                                           ("winkler95_by_fold", "winkler95", "95% Winkler score", None)):
        fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout="constrained")
        for ax, dataset in zip(axes.ravel(), LABELS):
            selected = frame[frame.dataset == dataset]
            for model in MODELS:
                for outer, part in selected[selected.model == model].groupby("outer_fold"):
                    means = part.groupby("physical_minutes")[metric].mean().sort_index()
                    ax.plot(means.index, means.values, color=COLORS[model], marker=["o", "s", "^"][int(outer)],
                            alpha=0.45 + 0.2 * int(outer), label=f"{model} fold {outer}")
            if nominal is not None:
                ax.axhline(nominal, color="black", linestyle="--", linewidth=1)
                ax.set_ylim(0, 1.03)
            ax.set_title(LABELS[dataset]); ax.set_xlabel("Physical horizon (minutes)"); ax.set_ylabel(ylabel)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="outside lower center", ncol=3, fontsize=8)
        files = []
        for extension in ("png", "pdf"):
            path = figure_dir / f"{name}.{extension}"
            fig.savefig(path, dpi=160)
            files.append({"path": path.name, "sha256": sha(path)})
        plt.close(fig)
        atomic(figure_dir / f"{name}.sources.json", {"source": "all_unit_model_metrics.csv",
               "source_sha256": sha(ANALYSIS / "all_unit_model_metrics.csv"),
               "meaning": "five-seed means shown separately for each overlapping outer fold; descriptive only",
               "files": files})


def write_report(cumulative: pd.DataFrame, pairs: pd.DataFrame, summary: dict) -> None:
    selected = cumulative[["dataset", "physical_minutes", "model", "mae", "rmse", "coverage90", "coverage95", "mpiw95", "winkler95", "process_cpu_seconds"]]
    report = "# Matched-forecasting amendment-005 cumulative completion\n\n"
    report += "All 125 authorized outstanding paired units completed and passed the existing validator plus completed zero-fit resume. Combined with 70 preserved units, the declared own-model comparison is 195/195 units, 585/585 point cells and 1,170/1,170 interval cells.\n\n"
    report += "The new execution used 1,000 tuning and 250 final learned fits, exactly the authorized 1,250-fit ceiling. Persistence used zero learned fits; historical units were not refitted.\n\n"
    report += "## Equal-fold descriptive results\n\n"
    report += "Values below first average five training seeds within each outer fold, then average the three overlapping folds equally. They are descriptive and are not population intervals.\n\n"
    report += base_analysis.table(selected, list(selected.columns)) + "\n"
    report += "## Validation and computation\n\n"
    report += f"New run commands used {summary['new_run_wall_seconds']/3600:.3f} wall hours and {summary['new_run_cpu_seconds']/3600:.3f} process CPU hours. Independent per-unit validation added {summary['new_validation_wall_seconds']/3600:.3f} wall hours; completed resumes added {summary['new_resume_wall_seconds']/3600:.3f} hours. Peak lifetime RSS was {summary['maximum_lifetime_peak_rss_MiB']:.1f} MiB.\n\n"
    report += "All saved metric arithmetic, common target identities, finite-sample radii, inner selection, final epochs, native seeds, serialized-model reload predictions, original-group/RICO-phase reconstructions and run-tree integrity passed.\n\n"
    report += "## Interpretation limits and remaining obligations\n\n"
    report += "Outer folds overlap, model seeds repeat training on the same fold support, and persistence aliases are deterministic. Population intervals therefore remain unavailable under the established design; no alternative inference was introduced. RICO acquisition phases and recurring known BDG2 buildings retain their earlier limitations.\n\n"
    report += "This closes only the declared own-model matched comparison. The separate 1,950-cell CQR/EnbPI/DSCP method matrix, seasonal computations, operational-grid work, and robustness/contamination/recovery obligations remain incomplete. Full-study readiness remains false.\n"
    atomic(REVIEW / "MATCHED_FORECASTING005_CUMULATIVE_REPORT.md", report)
    index = "# Matched-forecasting005 core-completion evidence index\n\n"
    index += "- [Technical report](MATCHED_FORECASTING005_CUMULATIVE_REPORT.md)\n"
    index += "- [Frozen scope](FROZEN_SCOPE.csv)\n- [Batch manifest](FROZEN_BATCH_MANIFEST.json)\n"
    index += "- [Pre-fit validation](PREFIT_VALIDATION.json)\n- [Progress/restart](PROGRESS_AND_RESTART.md)\n"
    index += "- [Cumulative validation](../../smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/analysis_validation.json)\n"
    index += "- [All unit/model metrics](../../smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/all_unit_model_metrics.csv)\n"
    index += "- [All interval cells](../../smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/all_interval_cells.csv)\n"
    index += "- [Inference status](../../smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/inference_status.csv)\n"
    index += "- [Cumulative completion/reuse ledger](../../smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/cumulative_completion_reuse_ledger.csv)\n"
    index += "- [MAE figure](../../smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/figures/mae_by_fold.png)\n"
    index += "- [Coverage figure](../../smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/figures/coverage95_by_fold.png)\n"
    index += "- [Winkler figure](../../smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/figures/winkler95_by_fold.png)\n"
    atomic(REVIEW / "EVIDENCE_INDEX.md", index)


def validate_analysis() -> None:
    summary = read(ANALYSIS / "analysis_validation.json")
    frame = csv_read(ANALYSIS / "all_unit_model_metrics.csv")
    intervals = csv_read(ANALYSIS / "all_interval_cells.csv")
    overlay = csv_read(ANALYSIS / "completion_overlay_195.csv")
    ledger = csv_read(ANALYSIS / "cumulative_completion_reuse_ledger.csv")
    if not summary["passed"] or len(frame) != 585 or len(intervals) != 1170 or len(ledger) != 585:
        raise ValueError("analysis row-count validation failed")
    if frame.duplicated(KEYCOLS + ["model"]).any() or intervals.duplicated(KEYCOLS + ["model", "nominal_level"]).any():
        raise ValueError("analysis duplicate cells")
    own = overlay[overlay.model.isin(MODELS)]
    if len(own) != 1170 or not own.status.str.startswith("completed").all():
        raise ValueError("overlay validation failed")
    max_point = 0.0
    max_interval = 0.0
    manifest = read(REVIEW / "FROZEN_BATCH_MANIFEST.json")
    for unit in manifest["units"]:
        key = unit["key"]
        points = csv_read(Path(unit["run"]) / "point_summary.csv")
        saved_intervals = csv_read(Path(unit["run"]) / "interval_quality.csv")
        for model in MODELS:
            actual = frame[(frame.dataset == key[0]) & (frame.horizon == key[1]) & (frame.outer_fold == key[2]) & (frame.model_seed == key[3]) & (frame.model == model)].iloc[0]
            expected = points[points.model == model].iloc[0]
            for field in ("mae", "rmse"):
                max_point = max(max_point, abs(float(actual[field]) - float(expected[field])))
            for level in LEVELS:
                row = intervals[(intervals.dataset == key[0]) & (intervals.horizon == key[1]) & (intervals.outer_fold == key[2]) & (intervals.model_seed == key[3]) & (intervals.model == model) & np.isclose(intervals.nominal_level.astype(float), level)].iloc[0]
                expected_interval = saved_intervals[(saved_intervals.model == model) & np.isclose(saved_intervals.nominal_level.astype(float), level)].iloc[0]
                for field in ("coverage", "mpiw", "winkler", "q"):
                    max_interval = max(max_interval, abs(float(row[field]) - float(expected_interval[field])))
    for row in ledger.itertuples(index=False):
        owner = ROOT / row.model_owner_path
        if not owner.is_file() or sha(owner) != row.model_owner_sha256:
            raise ValueError("owner ledger hash mismatch")
    receipt = {"passed": True, "utc": now(), "unit_keys": 195, "point_cells": 585,
               "interval_cells": 1170, "completion_ledger_rows": 585,
               "maximum_absolute_point_difference": max_point,
               "maximum_absolute_interval_difference": max_interval,
               "historical_units_reused": 70, "new_units": 125,
               "population_inference_status": "unavailable_under_prespecified_design",
               "full_study_ready": False}
    atomic(ANALYSIS / "independent_validation.json", receipt)
    complete = read(ANALYSIS / "COMPLETE.json")
    complete["files"]["independent_validation.json"] = sha(ANALYSIS / "independent_validation.json")
    atomic(ANALYSIS / "COMPLETE.json", complete)
    print(json.dumps(receipt, indent=2), flush=True)


def package() -> None:
    if PACKAGES.exists():
        raise ValueError("package destination already exists")
    PACKAGES.mkdir(parents=True)
    manifest = read(REVIEW / "FROZEN_BATCH_MANIFEST.json")
    state = read(BATCH / "progress.json")
    member_rows, package_rows = [], []
    fixed = (2026, 9, 23, 0, 0, 0)
    for unit in manifest["units"]:
        run = Path(unit["run"])
        if tree_record(run) != state["units"][unit["stem"]]["tree"]:
            raise ValueError("run changed before packaging")
        archive = PACKAGES / (unit["stem"] + ".zip")
        files = sorted(path for path in run.rglob("*") if path.is_file())
        with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as packed:
            for path in files:
                relative = path.relative_to(run).as_posix()
                info = zipfile.ZipInfo(relative, fixed)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                packed.writestr(info, path.read_bytes(), compresslevel=6)
        if archive.stat().st_size >= 95 * 2**20:
            raise ValueError("archive exceeds 95 MiB publication limit")
        with zipfile.ZipFile(archive) as packed:
            if packed.namelist() != [p.relative_to(run).as_posix() for p in files]:
                raise ValueError("archive member order mismatch")
            for path in files:
                relative = path.relative_to(run).as_posix()
                data = packed.read(relative)
                if hashlib.sha256(data).hexdigest() != sha(path):
                    raise ValueError("archive byte mismatch")
                member_rows.append({"unit": unit["stem"], "archive": archive.name, "path": relative,
                                    "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        package_rows.append({"unit": unit["stem"], "archive": archive.name, "bytes": archive.stat().st_size,
                             "sha256": sha(archive), "members": len(files),
                             "uncompressed_bytes": sum(p.stat().st_size for p in files)})
        print(f"PACKAGED {unit['order']}/125 {unit['stem']}", flush=True)
    with gzip.GzipFile(filename="", mode="wb", fileobj=(PACKAGES / "raw_file_manifest.csv.gz").open("wb"), mtime=0) as raw:
        import io
        text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        writer = csv_module.DictWriter(text, fieldnames=list(member_rows[0]))
        writer.writeheader(); writer.writerows(member_rows); text.flush()
    write_frame(PACKAGES / "package_manifest.csv", package_rows)
    receipt = {"passed": True, "utc": now(), "units": 125, "archives": len(package_rows),
               "members": len(member_rows), "archive_bytes": sum(row["bytes"] for row in package_rows),
               "uncompressed_bytes": sum(row["uncompressed_bytes"] for row in package_rows),
               "maximum_archive_bytes": max(row["bytes"] for row in package_rows),
               "publication_limit_bytes": 95 * 2**20,
               "reconstruction": "extract each unit archive into its named empty run directory and verify raw_file_manifest.csv.gz"}
    atomic(PACKAGES / "validation.json", receipt)
    print(json.dumps(receipt, indent=2), flush=True)


def backup_bulk() -> None:
    """Copy verified run archives and package non-Git execution evidence."""
    package_validation = read(PACKAGES / "validation.json")
    if not package_validation.get("passed") or int(package_validation["archives"]) != 125:
        raise ValueError("run-package validation is not complete")
    package_manifest = csv_read(PACKAGES / "package_manifest.csv")
    if len(package_manifest) != 125 or package_manifest.archive.duplicated().any():
        raise ValueError("run-package manifest coverage failure")

    destination = BACKUP / "raw_and_execution_evidence_v1"
    run_destination = destination / "run_packages"
    support_destination = destination / "support_evidence"
    run_destination.mkdir(parents=True, exist_ok=True)
    support_destination.mkdir(parents=True, exist_ok=True)

    copied_rows = []
    for row in package_manifest.itertuples(index=False):
        source = PACKAGES / row.archive
        target = run_destination / row.archive
        expected = str(row.sha256)
        if not target.exists():
            partial = target.with_suffix(target.suffix + ".partial")
            if partial.exists():
                raise ValueError(f"unresolved partial backup: {partial}")
            shutil.copy2(source, partial)
            if sha(partial) != expected:
                raise ValueError(f"copied archive hash mismatch: {row.archive}")
            partial.replace(target)
        if target.stat().st_size != int(row.bytes) or sha(target) != expected:
            raise ValueError(f"external archive verification failed: {row.archive}")
        copied_rows.append({"archive": row.archive, "bytes": int(row.bytes), "sha256": expected,
                            "external_relative_path": target.relative_to(BACKUP).as_posix()})
        print(f"BACKED UP RUN ARCHIVE {len(copied_rows)}/125 {row.archive}", flush=True)

    for name in ("package_manifest.csv", "raw_file_manifest.csv.gz", "validation.json"):
        source = PACKAGES / name
        target = run_destination / name
        expected = sha(source)
        if not target.exists():
            shutil.copy2(source, target)
        if sha(target) != expected:
            raise ValueError(f"external package metadata mismatch: {name}")

    manifest = read(REVIEW / "FROZEN_BATCH_MANIFEST.json")
    support_paths = []
    for unit in manifest["units"]:
        support_paths.extend(path for path in Path(unit["design"]).rglob("*") if path.is_file())
        process = BASE / f"{unit['stem']}.process.json"
        if not process.is_file():
            raise ValueError(f"missing process receipt: {process}")
        support_paths.append(process)
    support_paths.extend(path for path in BATCH.rglob("*") if path.is_file())
    support_paths = sorted(set(support_paths), key=lambda path: path.relative_to(ROOT).as_posix())

    maximum_uncompressed = 80 * 2**20
    groups, group, group_bytes = [], [], 0
    for path in support_paths:
        size = path.stat().st_size
        if size > maximum_uncompressed:
            raise ValueError(f"support file exceeds part budget: {path}")
        if group and group_bytes + size > maximum_uncompressed:
            groups.append(group)
            group, group_bytes = [], 0
        group.append(path)
        group_bytes += size
    if group:
        groups.append(group)

    fixed = (2026, 9, 24, 0, 0, 0)
    support_members, support_parts = [], []
    for number, files in enumerate(groups, 1):
        archive = support_destination / f"support_{number:02d}.zip"
        expected_names = [path.relative_to(ROOT).as_posix() for path in files]
        if not archive.exists():
            partial = archive.with_suffix(archive.suffix + ".partial")
            if partial.exists():
                raise ValueError(f"unresolved partial support archive: {partial}")
            with zipfile.ZipFile(partial, "x", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as packed:
                for path, relative in zip(files, expected_names):
                    info = zipfile.ZipInfo(relative, fixed)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    packed.writestr(info, path.read_bytes(), compresslevel=6)
            partial.replace(archive)
        if archive.stat().st_size >= 95 * 2**20:
            raise ValueError(f"support archive exceeds 95 MiB limit: {archive}")
        with zipfile.ZipFile(archive) as packed:
            if packed.namelist() != expected_names:
                raise ValueError(f"support archive membership mismatch: {archive}")
            for path, relative in zip(files, expected_names):
                data = packed.read(relative)
                digest = hashlib.sha256(data).hexdigest()
                if digest != sha(path):
                    raise ValueError(f"support archive byte mismatch: {relative}")
                support_members.append({"archive": archive.name, "path": relative,
                                        "bytes": len(data), "sha256": digest})
        support_parts.append({"archive": archive.name, "bytes": archive.stat().st_size,
                              "sha256": sha(archive), "members": len(files),
                              "uncompressed_bytes": sum(path.stat().st_size for path in files),
                              "external_relative_path": archive.relative_to(BACKUP).as_posix()})
        print(f"VERIFIED SUPPORT ARCHIVE {number}/{len(groups)} {archive.name}", flush=True)

    write_frame(PACKAGES / "external_run_archive_manifest.csv", copied_rows)
    write_frame(PACKAGES / "external_support_archive_manifest.csv", support_parts)
    with gzip.GzipFile(filename="", mode="wb", fileobj=(PACKAGES / "external_support_file_manifest.csv.gz").open("wb"), mtime=0) as raw:
        import io
        text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        writer = csv_module.DictWriter(text, fieldnames=list(support_members[0]))
        writer.writeheader(); writer.writerows(support_members); text.flush()
    receipt = {
        "passed": True, "utc": now(), "backup_root": str(BACKUP),
        "run_archives": len(copied_rows),
        "run_archive_bytes": sum(row["bytes"] for row in copied_rows),
        "support_archives": len(support_parts),
        "support_archive_bytes": sum(row["bytes"] for row in support_parts),
        "support_members": len(support_members),
        "support_uncompressed_bytes": sum(row["uncompressed_bytes"] for row in support_parts),
        "maximum_support_archive_bytes": max(row["bytes"] for row in support_parts),
        "publication_limit_bytes": 95 * 2**20,
        "coverage": "125 verified run archives plus all 125 frozen protocols, process receipts, and coordinator attempts/receipts/journals",
    }
    atomic(PACKAGES / "external_backup_validation.json", receipt)
    print(json.dumps(receipt, indent=2), flush=True)


def stage_plan() -> None:
    """Write the exact compact publication allowlist outside the repository."""
    manifest = read(REVIEW / "FROZEN_BATCH_MANIFEST.json")
    selected = {ROOT / "PROJECT_RECOVERY_STATUS.md"}
    selected.update(path for path in REVIEW.rglob("*")
                    if path.is_file() and "__pycache__" not in path.parts)
    for unit in manifest["units"]:
        run = Path(unit["run"])
        selected.update(path for path in run.iterdir() if path.is_file())
        selected.add(BASE / f"{unit['stem']}.process.json")
    selected.update(BATCH / name for name in ("attempts.jsonl", "progress.json", "resources.jsonl"))
    selected.update(path for path in ANALYSIS.rglob("*") if path.is_file())
    selected.update(path for path in PACKAGES.iterdir() if path.is_file() and path.suffix != ".zip")
    missing = sorted(path for path in selected if not path.is_file())
    if missing:
        raise ValueError(f"publication allowlist has missing paths: {missing[:3]}")
    relative = sorted(path.relative_to(ROOT).as_posix() for path in selected)
    stage_file = BACKUP / "substantive_stage_paths.txt"
    stage_file.write_text("\n".join(relative) + "\n", encoding="utf-8", newline="\n")
    receipt = {"passed": True, "utc": now(), "paths": len(relative),
               "bytes": sum((ROOT / path).stat().st_size for path in relative),
               "maximum_bytes": max((ROOT / path).stat().st_size for path in relative),
               "allowlist": str(stage_file)}
    atomic(BACKUP / "substantive_stage_plan.json", receipt)
    print(json.dumps(receipt, indent=2), flush=True)


def delivery_receipts() -> None:
    """Verify the substantive commit remotely and record the external recovery proof."""
    remote_line = subprocess.check_output(
        ["git", "ls-remote", "origin", f"refs/heads/{BRANCH}"], cwd=ROOT, text=True
    ).strip()
    remote_commit = remote_line.split()[0] if remote_line else ""
    if remote_commit != SUBSTANTIVE_COMMIT:
        raise ValueError(f"remote branch mismatch: {remote_commit}")

    readback_paths = [
        "PROJECT_RECOVERY_STATUS.md",
        "review/matched_forecasting005_completion_20260923/MATCHED_FORECASTING005_CUMULATIVE_REPORT.md",
        "review/matched_forecasting005_completion_20260923/EVIDENCE_INDEX.md",
        "smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/analysis_validation.json",
        "smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/independent_validation.json",
        "smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/inference_status.csv",
        "smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/cumulative_completion_reuse_ledger.csv",
        "smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/paired_model_contrasts.csv",
        "smart_building_conformal/outputs/matched_forecasting005/core_completion_195_v1_analysis/figures/mae_by_fold.png",
        "smart_building_conformal/outputs/matched_forecasting005/core_completion_125_v1_packages/validation.json",
        "smart_building_conformal/outputs/matched_forecasting005/core_completion_125_v1_packages/external_backup_validation.json",
        "smart_building_conformal/outputs/matched_forecasting005/core_completion_125_v1_packages/external_run_archive_manifest.csv",
        "smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f1_s42_v1/checkpoint_manifest.json",
        "smart_building_conformal/outputs/matched_forecasting005/pleia_h6_f0_s46_v1/run_summary.json",
        "smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_INFERENCE.csv",
    ]
    downloads = []
    for path in readback_paths:
        expected = subprocess.check_output(["git", "show", f"{SUBSTANTIVE_COMMIT}:{path}"], cwd=ROOT)
        url = ("https://raw.githubusercontent.com/jinchuntan/confosense/" + SUBSTANTIVE_COMMIT + "/"
               + urllib.parse.quote(path, safe="/"))
        error = None
        for attempt in range(1, 4):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "ConfoSense-delivery-verifier/1"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    status = response.status
                    actual = response.read()
                break
            except Exception as exc:
                error = exc
                if attempt == 3:
                    raise
                time.sleep(attempt)
        if status != 200 or actual != expected:
            raise ValueError(f"commit-pinned HTTPS mismatch: {path}; status={status}; error={error}")
        downloads.append({"path": path, "url": url, "http_status": status, "bytes": len(actual),
                          "sha256": hashlib.sha256(actual).hexdigest(), "exact_commit_blob_match": True})
        print(f"HTTPS READBACK {len(downloads)}/{len(readback_paths)} {path}", flush=True)

    bundle_paths = [
        Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_validated_acceptance_20260921/recovery_18d8_v6/base_c143.bundle"),
        Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_pilot_20260918/temperature_delivery_v2_571408be.bundle"),
        BACKUP / "recovery_prerequisite_f28eb4c6_from_571408be.bundle",
        Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_multiseed_20260923/substantive_475f92e3e2e42e6ae4cdefd6ece748c56474de1d_v1/temperature_multiseed_475f92e3e2e42e6ae4cdefd6ece748c56474de1d.bundle"),
        BACKUP / "matched_forecasting_completion_be8487668e82_from_475f92e3e2e4.bundle",
    ]
    bundle_rows = []
    for path in bundle_paths:
        if not path.is_file():
            raise ValueError(f"missing recovery bundle: {path}")
        bundle_rows.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)})
        print(f"HASHED RECOVERY BUNDLE {len(bundle_rows)}/{len(bundle_paths)} {path.name}", flush=True)

    recovery = {
        "passed": True, "utc": now(),
        "method": "git init in an empty temporary repository followed only by fetches from the external bundle paths below",
        "temporary_repository": "C:\\Users\\nigel\\AppData\\Local\\Temp\\confosense-external-recovery-be8487668e82",
        "network_used": False, "working_repository_objects_used": False, "github_used": False,
        "initial_missing_prerequisite": "f28eb4c6edc3362ad930ec949fd4363a2ce759fb",
        "resolution": "added the scoped 571408be..59b842b5 prerequisite bundle, which includes f28eb4c6 and acceptance 18d8dd15",
        "verified_commits": {
            "acceptance": "18d8dd15d06459b3b54ba629e9948b78494f4c8f",
            "preflight_prerequisite": "f28eb4c6edc3362ad930ec949fd4363a2ce759fb",
            "temperature_substantive": "475f92e3e2e42e6ae4cdefd6ece748c56474de1d",
            "temperature_delivery": "640aa76d0c4ff47d5fea09d160bfacf488b7c5e7",
            "exact_restored_commit": SUBSTANTIVE_COMMIT,
        },
        "restored_result_check": {"passed": True, "paired_units": 195, "new_tuning_fits": 1000,
                                  "new_final_fits": 250},
        "git_fsck_full_no_dangling": "passed", "bundle_chain": bundle_rows,
    }
    atomic(REVIEW / "EXTERNAL_RECOVERY_RECEIPT.json", recovery)
    bulk = read(PACKAGES / "external_backup_validation.json")
    delivery = {
        "passed": True, "utc": now(), "substantive_commit_verified": SUBSTANTIVE_COMMIT,
        "receipt_commit_scope": "this later receipt verifies the earlier substantive commit; it does not self-verify",
        "remote": "https://github.com/jinchuntan/confosense.git", "remote_branch": BRANCH,
        "remote_ref_at_verification": remote_commit, "remote_ref_verified": True,
        "https_readback": {
            "commit_pinned": True,
            "scope": "the 15 representative publication, validation, package, checkpoint, figure, and preserved blank-inference files listed here; not every tracked file or external raw archive",
            "files": downloads,
        },
        "substantive_stage": {"allowlist": str(BACKUP / "substantive_stage_paths.txt"),
                              "files": 1047, "bytes": 26721674, "maximum_file_bytes": 7344487},
        "bulk_backup": bulk,
        "external_recovery_receipt": "EXTERNAL_RECOVERY_RECEIPT.json",
    }
    atomic(REVIEW / "DELIVERY_RECEIPT.json", delivery)
    print(json.dumps({"passed": True, "remote_commit": remote_commit,
                      "https_files": len(downloads), "recovery_bundles": len(bundle_rows)}, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "coordinate", "unit", "analyze", "validate-analysis", "package", "backup", "stage-plan", "delivery-receipts"])
    parser.add_argument("--stem")
    parser.add_argument("--out")
    args = parser.parse_args()
    if args.action == "prepare": prepare()
    elif args.action == "coordinate": coordinate()
    elif args.action == "unit": unit_check(args.stem, Path(args.out))
    elif args.action == "analyze": analyze()
    elif args.action == "validate-analysis": validate_analysis()
    elif args.action == "package": package()
    elif args.action == "backup": backup_bulk()
    elif args.action == "stage-plan": stage_plan()
    elif args.action == "delivery-receipts": delivery_receipts()


if __name__ == "__main__":
    main()
