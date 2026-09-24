"""Seal the no-fit EnbPI rank-recovery evidence for coordinator restart."""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import subprocess

from adapter import HERE, REPO, SMART, SOURCE_HASH, source_digest
from corrected_validator_v1 import (
    VERSION, FROZEN_VALIDATOR_SHA256, corrected_source_sha256,
)
from src.intervals005_common import atomic, digest, frame, read, tree


COORDINATOR = SMART / "outputs/matched_intervals005/completion_52_v1_coordinator"
RECOVERY = COORDINATOR / "rank_recovery_v1"
RUN = SMART / "outputs/matched_intervals005/bdg2_f0_s46_method_completion_v1"
DESIGN = SMART / "protocols/matched_intervals005/bdg2_f0_s46_method_completion_v1"
FAILED_DIR = COORDINATOR / "validation/bdg2_f0_s46"
FAILED_LOG = COORDINATOR / (
    "attempts/2026-09-23T225509679650+0000_e0411b9e/command.log"
)


def returned_operation_counts(path: Path) -> dict[str, int]:
    counts = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("event") == "returned":
            counts[row["kind"]] += 1
    return dict(sorted(counts.items()))


def main() -> None:
    if source_digest() != SOURCE_HASH:
        raise ValueError("scientific source changed")
    before = tree(RUN)
    protocol = read(DESIGN / "frozen_protocol.json")
    diagnosis = read(RECOVERY / "diagnosis/diagnosis.json")
    validation = read(RECOVERY / "corrected_validation/bdg2_f0_s46/validation.json")
    resume = read(RECOVERY / "resumes/bdg2_f0_s46.json")
    completed = read(RECOVERY / "completed_bundle_check/validation.json")
    if not all(x["passed"] for x in (diagnosis, validation, completed)):
        raise ValueError("recovery evidence did not pass")
    if (resume["models_fitted"] or resume["calibrators_fitted"]
            or not resume["all_run_files_unchanged"]):
        raise ValueError("forbidden-fit resume gate failed")
    if not FAILED_DIR.exists() or any(FAILED_DIR.iterdir()):
        raise ValueError("original failed validation directory not preserved empty")

    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SMART)
    command = [
        r"C:\cfs_venv\Scripts\python.exe", "-B", "-m", "pytest", "-q",
        "-p", "no:cacheprovider", str(HERE / "test_corrected_validator_v1.py"),
    ]
    test = subprocess.run(command, cwd=REPO, env=environment, text=True,
                          capture_output=True, check=False)
    test_receipt = dict(
        command=command,
        exit_code=test.returncode,
        stdout=test.stdout,
        stderr=test.stderr,
        test_source_sha256=digest(HERE / "test_corrected_validator_v1.py"),
    )
    atomic(RECOVERY / "focused_tests.json", test_receipt)
    if test.returncode != 0 or "8 passed" not in test.stdout:
        raise ValueError("focused correction tests failed")

    actual_counts = returned_operation_counts(RUN / "operations.jsonl")
    expected_counts = protocol["expected_operations"]
    actual_counts = {name: actual_counts.get(name, 0) for name in expected_counts}
    if actual_counts != expected_counts:
        raise ValueError("saved operation counts changed")

    identities = []
    for horizon in protocol["scope"]["horizons"]:
        raw = RUN / f"stages/raw_h{horizon}_enbpi"
        for role in ("calibration", "test"):
            path = raw / f"{role}_metadata.csv.gz"
            identities.append(dict(
                horizon=horizon,
                role=role,
                rows=len(frame(path)),
                sha256=digest(path),
                path=str(path.relative_to(REPO)),
            ))

    after = tree(RUN)
    if before != after:
        raise ValueError("scientific artifact tree changed while sealing recovery")
    manifest = dict(
        version=VERSION,
        passed=True,
        established_cause="frozen independent-validator floating-point rank defect",
        correction_scope="external validator only; frozen scientific src and outputs unchanged",
        scientific_source_hash=SOURCE_HASH,
        correction_module_sha256=digest(HERE / "corrected_validator_v1.py"),
        corrected_validator_source_sha256=corrected_source_sha256(),
        frozen_validator_sha256=FROZEN_VALIDATOR_SHA256,
        diagnosis_sha256=digest(RECOVERY / "diagnosis/diagnosis.json"),
        corrected_validation_sha256=digest(RECOVERY / "corrected_validation/bdg2_f0_s46/validation.json"),
        completed_bundle_check_sha256=digest(RECOVERY / "completed_bundle_check/validation.json"),
        focused_tests_sha256=digest(RECOVERY / "focused_tests.json"),
        zero_fit_resume_sha256=digest(RECOVERY / "resumes/bdg2_f0_s46.json"),
        failed_log=str(FAILED_LOG.resolve()),
        failed_validation_preserved_sha256=digest(FAILED_LOG),
        failed_validation_directory=str(FAILED_DIR.resolve()),
        failed_validation_directory_preserved_empty=True,
        original_calibration_test_identities=identities,
        operation_counts=actual_counts,
        operation_counts_match_frozen_protocol=True,
        operations_sha256=digest(RUN / "operations.jsonl"),
        complete_manifest_sha256=digest(RUN / "COMPLETE.json"),
        scientific_tree_unchanged=True,
        completed_bundles_checked=completed["bundles_checked"],
        completed_bound_cells_checked=completed["bound_cells_checked"],
        completed_rows_checked=completed["rows_checked"],
        full_corrected_validation_passed=True,
        seed46_zero_fit_resume_passed=True,
        models_fitted=0,
        calibrators_fitted=0,
        tolerances_unchanged=True,
        remaining_authorized_bundles=47,
    )
    atomic(HERE / "INTERVAL_RANK_RECOVERY_V1.json", manifest)
    report = f"""# Interval-rank recovery v1

Cause: the frozen independent validator used ordinary `1-level` arithmetic,
while MAPIE 1.4.1 derives alpha through `Decimal` and applies its affine
reversed-probability expression.  For seed 46, horizon 1, level 0.9, this
crossed one order-statistic rank on each bound.  The lower residual changed by
`-0.023950805664043173`, exactly explaining the reported lower-bound offset.

The separately versioned external correction preserves the frozen scientific
source, package versions, outputs, failed attempt, tolerances, and protocol.
Full corrected validation passed all 30 method cells.  The seed-46 forbidden-fit
resume verified 138 stages with no file changes.  The four earlier bundles
passed {completed['bound_cells_checked']} affected bound cells over
{completed['rows_checked']} row/bound comparisons.  Focused tests: 8 passed.

Operation counts remain exactly equal to the frozen protocol and
`operations.jsonl` remains `{manifest['operations_sha256']}`.
"""
    atomic(HERE / "INTERVAL_RANK_RECOVERY_V1.md", report)
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
