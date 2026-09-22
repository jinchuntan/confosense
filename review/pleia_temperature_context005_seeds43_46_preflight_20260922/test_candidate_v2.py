"""Focused no-fit tests for the explicit-path validator adapter."""
from __future__ import annotations

import gzip
import json
import os
import pickle
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from common import *
from src.intervals005_common import digest


ADAPTER = REVIEW / "candidate_validate_v2.py"
OLD_RUNNER = AUDIT / "run_stage.py"
RESULTS = REVIEW / "focused_tests_v2"


def build_sandbox(root: Path) -> tuple[Path, str]:
    variants = pd.read_csv(SEED42_RUN / "stages" / "tables" / "variants.csv", keep_default_na=False, dtype={"context_id": str})
    head = variants.head(1)
    stages = sorted(set(head.canonical_stage) | set(head.stage))
    (root / "stages" / "tables").mkdir(parents=True)
    head.to_csv(root / "stages" / "tables" / "variants.csv", index=False)
    shutil.copytree(SEED42_RUN / "stages" / "controls", root / "stages" / "controls")
    for stage in stages:
        shutil.copytree(SEED42_RUN / "stages" / stage, root / "stages" / stage)
    complete = SEED42_RUN / "COMPLETE.json"
    receipt = {
        "purpose": "disposable one-variant fixture copied from accepted seed-42 run",
        "source_run": str(SEED42_RUN.resolve()), "source_complete_path": str(complete.resolve()),
        "source_complete_sha256": sha256(complete),
        "source_protocol_sha256": digest(SEED42_DESIGN / "frozen_protocol.json"),
        "limited": True, "full_coverage_checked": False,
    }
    (root / "LIMITED_FIXTURE.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return root, str(head.iloc[0].canonical_stage)


def rewrite_gz(path: Path, mutate) -> None:
    frame = pd.read_csv(path, keep_default_na=False, float_precision="round_trip")
    mutate(frame)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as packed:
            frame.to_csv(packed, index=False, lineterminator="\n")


def run_adapter(run: Path, output: Path, *, design_path: Path = SEED42_DESIGN, expected_seed: int = 42) -> tuple[subprocess.CompletedProcess[str], dict | None]:
    command = [PYTHON, "-B", str(ADAPTER), "--design", str(design_path), "--run", str(run), "--output", str(output),
               "--expected-dataset", "pleia", "--expected-fold", "2", "--expected-horizon", "1", "--expected-seed", str(expected_seed), "--limit", "1"]
    process = subprocess.run(command, cwd=SMART, capture_output=True, text=True)
    report_path = output / "CANDIDATE_VALIDATION.json"
    return process, read(report_path) if report_path.exists() else None


def run_old(run: Path, output: Path) -> tuple[subprocess.CompletedProcess[str], dict | None]:
    env = dict(os.environ, CANDIDATE_RUN=str(run), CANDIDATE_OUT=str(output), CANDIDATE_LIMIT="1")
    process = subprocess.run([PYTHON, "-B", str(OLD_RUNNER), "candidate_validate_v1.py"], cwd=SMART, env=env, capture_output=True, text=True)
    report_path = output / "CANDIDATE_VALIDATION.json"
    return process, read(report_path) if report_path.exists() else None


def corrupt_feature(run: Path, stage: str) -> None:
    rewrite_gz(run / "stages" / stage / "features.csv.gz", lambda frame: frame.__setitem__("target_rollmean_6", frame["target_rollmean_6"].where(frame.index != 5, frame["target_rollmean_6"].astype(float) + 0.5)))


def corrupt_observation(run: Path, stage: str) -> None:
    def mutate(frame): frame.loc[7, "observed"] = float(frame.loc[7, "observed"]) + 1.0
    rewrite_gz(run / "stages" / stage / "observations.csv.gz", mutate)


def corrupt_prediction(run: Path, stage: str) -> None:
    def mutate(frame): frame.loc[9, "raw_upper"] = float(frame.loc[9, "raw_upper"]) + 0.25
    rewrite_gz(run / "stages" / stage / "cqr_static_issued.csv.gz", mutate)


def corrupt_interval(run: Path, stage: str) -> None:
    def mutate(frame): frame.loc[11, "lower"] = float(frame.loc[11, "lower"]) - 0.3
    rewrite_gz(run / "stages" / stage / "cqr_rolling_issued.csv.gz", mutate)


def corrupt_update(run: Path, stage: str) -> None:
    def mutate(frame):
        if len(frame): frame.loc[0, "correction_lower"] = float(frame.loc[0, "correction_lower"]) + 0.2
    rewrite_gz(run / "stages" / stage / "cqr_rolling_updates.csv.gz", mutate)


def corrupt_alert(run: Path, stage: str) -> None:
    def mutate(frame): frame.loc[3, "alert_combined"] = not bool(frame.loc[3, "alert_combined"])
    rewrite_gz(run / "stages" / stage / "cqr_static_single_sample_alerts.csv.gz", mutate)


def corrupt_release(run: Path, stage: str) -> None:
    def mutate(frame):
        if len(frame): frame.loc[2, "score"] = float(frame.loc[2, "score"]) + 0.4
    rewrite_gz(run / "stages" / stage / "cqr_static_released.csv.gz", mutate)


def corrupt_owner(run: Path, stage: str) -> None:
    path = run / "stages" / "controls" / "controls.pkl"
    with path.open("rb") as handle:
        wrappers = pickle.load(handle)
    estimator = wrappers["cqr"].owner._mapie_quantile_regressor.estimators_[1]
    estimator._baseline_prediction = estimator._baseline_prediction + 0.05
    with path.open("wb") as handle:
        pickle.dump(wrappers, handle, protocol=5)


CORRUPTIONS = [
    ("reject_feature_corruption", corrupt_feature, "A_feature_provenance"),
    ("reject_observation_corruption", corrupt_observation, "A_observations"),
    ("reject_prediction_corruption", corrupt_prediction, "B_model_application"),
    ("reject_interval_corruption", corrupt_interval, "C_interval_construction"),
    ("reject_causal_update_corruption", corrupt_update, "C_rolling_state"),
    ("reject_alert_flag_corruption", corrupt_alert, "C_alert_flags"),
    ("reject_released_score_corruption", corrupt_release, "C_released_scores"),
    ("reject_model_corruption", corrupt_owner, "B_model_application"),
]


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=False)
    rows = []
    with tempfile.TemporaryDirectory(prefix="candidate_v2_accept_") as temp:
        run, _ = build_sandbox(Path(temp) / "run")
        new_process, new = run_adapter(run, Path(temp) / "new")
        old_process, old = run_old(run, Path(temp) / "old")
        equivalent = bool(new and old and new["passed"] and old["passed"] and new["totals"] == old["totals"] and new["by_kind"] == old["by_kind"])
        rows.append({"test": "accept_unmodified_and_old_new_equivalence", "expected": "pass_and_exact_match", "observed": "pass_and_exact_match" if equivalent else "mismatch", "ok": equivalent,
                     "detail": "bounded seed-42 numerical totals and categories match v1 exactly", "new_exit": new_process.returncode, "old_exit": old_process.returncode})
    print(rows[-1])

    for name, mutate, expected_kind in CORRUPTIONS:
        with tempfile.TemporaryDirectory(prefix="candidate_v2_corrupt_") as temp:
            run, stage = build_sandbox(Path(temp) / "run")
            mutate(run, stage)
            process, report = run_adapter(run, Path(temp) / "out")
            kinds = sorted({item["kind"] for item in report["candidate_violations"]}) if report else []
            ok = bool(process.returncode != 0 and report and not report["passed"] and expected_kind in kinds)
            rows.append({"test": name, "expected": "reject", "observed": "reject" if ok else "unexpected", "ok": ok, "detail": ";".join(kinds), "exit": process.returncode})
        print(rows[-1])

    with tempfile.TemporaryDirectory(prefix="candidate_v2_wrong_seed_") as temp:
        run, _ = build_sandbox(Path(temp) / "run")
        process, report = run_adapter(run, Path(temp) / "out", expected_seed=43)
        combined = process.stdout + process.stderr
        ok = process.returncode != 0 and report is None and "expected_identity_mismatch" in combined
        rows.append({"test": "reject_wrong_expected_seed", "expected": "reject_before_validation", "observed": "reject" if ok else "unexpected", "ok": ok, "detail": combined[-500:], "exit": process.returncode})
    print(rows[-1])

    with tempfile.TemporaryDirectory(prefix="candidate_v2_crosswire_") as temp:
        run, _ = build_sandbox(Path(temp) / "run")
        process, report = run_adapter(run, Path(temp) / "out", design_path=design(43), expected_seed=43)
        combined = process.stdout + process.stderr
        ok = process.returncode != 0 and report is None and "run_design_protocol_mismatch" in combined
        rows.append({"test": "reject_seed43_design_with_seed42_owner_run", "expected": "reject_before_validation", "observed": "reject" if ok else "unexpected", "ok": ok, "detail": combined[-500:], "exit": process.returncode})
    print(rows[-1])

    with tempfile.TemporaryDirectory(prefix="candidate_v2_collision_") as temp:
        run, _ = build_sandbox(Path(temp) / "run")
        process, report = run_adapter(run, run)
        combined = process.stdout + process.stderr
        ok = process.returncode != 0 and report is None and "output_path_could_overwrite_or_mix_with_evidence" in combined
        rows.append({"test": "reject_output_path_overwrite", "expected": "reject_before_validation", "observed": "reject" if ok else "unexpected", "ok": ok, "detail": combined[-500:], "exit": process.returncode})
    print(rows[-1])

    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "focused_test_results.csv", index=False, lineterminator="\n")
    result = {
        "purpose": "focused no-fit tests of explicit-path validator interface",
        "utc": utc(), "total": len(rows), "passed": int(frame.ok.sum()), "failed": int((~frame.ok).sum()), "all_ok": bool(frame.ok.all()),
        "models_fitted": 0, "full_scientific_validation_performed": False,
        "limited_receipts_satisfy_full_acceptance_gate": False,
        "pending_execution_checks": ["Seeds 43--46 native estimator random_state and complete fitted-owner blob identity require future authorized fitted owners; static propagation and seed-42 native identity are checked now."],
        "results": rows,
    }
    write_json(RESULTS / "FOCUSED_TEST_RECEIPT.json", result)
    print({"total": len(rows), "passed": result["passed"], "failed": result["failed"], "all_ok": result["all_ok"]})
    if not result["all_ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
