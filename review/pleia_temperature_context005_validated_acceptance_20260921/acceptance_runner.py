"""Read-only acceptance runner for the PLEIA-temperature context005 pilot.

This runner intentionally lives outside ``smart_building_conformal/src``.  It
adopts the audited ``candidate_representation_compatible_v1`` by immutable
source identity, rather than changing the frozen validator or any scientific
implementation.  It never launches an experiment or fit.

Usage (from repository root)::

    C:/cfs_venv/Scripts/python.exe -B review/pleia_temperature_context005_validated_acceptance_20260921/acceptance_runner.py preflight
    C:/cfs_venv/Scripts/python.exe -B review/pleia_temperature_context005_validated_acceptance_20260921/acceptance_runner.py focused
    C:/cfs_venv/Scripts/python.exe -B review/pleia_temperature_context005_validated_acceptance_20260921/acceptance_runner.py full

The full action delegates to the exact audited candidate source with its own
``Operations(forbid=True)`` guard.  Outputs are written only to the separate
acceptance directory; the completed pilot tree is read-only and is compared
with its immutable ``COMPLETE.json`` manifest before validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SMART = REPO / "smart_building_conformal"
sys.path.insert(0, str(SMART))

AUDIT = REPO / "review" / "pleia_temperature_context005_validation_audit_20260919"
CANDIDATE = AUDIT / "candidate_validate_v1.py"
FOCUSED = AUDIT / "test_candidate_contract.py"
MECHANISM = AUDIT / "prove_mechanism.py"
RUN = SMART / "outputs" / "conditional_context005" / "pleia_f2_s42_C_v1"
DESIGN_ROOT = SMART / "protocols" / "conditional_context005"
OUT = SMART / "outputs" / "conditional_context005" / "pleia_f2_s42_C_v1_validated_acceptance_v1"

ENTRY_HEAD = "e52a3ba6b94996f51300af523f898207162cac79"
AUDIT_SOURCE_SHA256 = "14cab398cf5ec389a1eae0a2f22d832a56ada31add44f93f6a38ea3095d2a091"
FROZEN_SOURCE_SHA256 = "a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f"
EXPECTED_BRANCHES = {
    "main": "06fe967be2be8d7898812c0c2d6e464d4e942351",
    "review/pleia-temperature-context005-pilot-20260918": "571408be0b51e81c6987306a292afc7fcae2ff94",
    "review/pleia-temperature-context005-validation-audit-20260919": ENTRY_HEAD,
    "review/pleia-temperature-context005-validated-acceptance-20260921": ENTRY_HEAD,
    "review/pleia-energy-context005-multiseed-20260915": "80df3579dfe68ccf2c0d406c21c0fec967ff2b41",
}
DESIGNS = [
    "pleia_f2_s42_C_v1",
    "pleia_energy_f2_s42_C_v1",
    "pleia_energy_f2_s43_C_v1",
    "pleia_energy_f2_s44_C_v1",
    "pleia_energy_f2_s45_C_v1",
    "pleia_energy_f2_s46_C_v1",
]


def utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def git(*args: str, binary: bool = False) -> str | bytes:
    value = subprocess.check_output(["git", *args], cwd=REPO, text=not binary)
    return value if binary else value.strip()  # type: ignore[union-attr,return-value]


def status_entries() -> list[str]:
    raw = git("status", "--porcelain=v1")
    return [] if not raw else str(raw).splitlines()


def complete_integrity() -> dict:
    """Check exactly the declared completed-tree files, without discovering files."""
    complete = json.loads((RUN / "COMPLETE.json").read_text(encoding="utf-8"))
    declared = complete["files"]
    missing, mismatch = [], []
    missing_count, mismatch_count = 0, 0
    for rel, expected in declared.items():
        path = RUN / rel
        if not path.is_file():
            missing_count += 1
            if len(missing) < 50:
                missing.append(rel)
            continue
        actual = sha256(path)
        if actual != expected:
            mismatch_count += 1
            if len(mismatch) < 50:
                mismatch.append({"path": rel, "expected": expected, "actual": actual})
    ops = RUN / "operations.jsonl"
    return {
        "passed": not missing and not mismatch,
        "method": "exact file list and SHA-256 values declared by COMPLETE.json; no recursive discovery",
        "declared_files": len(declared),
        "missing_count": missing_count,
        "hash_mismatch_count": mismatch_count,
        "missing_examples": missing,
        "hash_mismatch_examples": mismatch,
        "complete_sha256": sha256(RUN / "COMPLETE.json"),
        "operations_bytes": ops.stat().st_size,
        "operations_sha256": sha256(ops),
        "operations_matches_complete": sha256(ops) == declared.get("operations.jsonl"),
        "protocol_sha256": complete["protocol_sha256"],
        "complete_exit_status": complete["actual_exit_status"],
    }


def protocol_compatibility() -> dict:
    from src.conditional_context005 import check_protocol
    from src.unit_checkpoint import source_digest

    current = source_digest()
    results = []
    for name in DESIGNS:
        design = DESIGN_ROOT / name
        protocol = json.loads((design / "frozen_protocol.json").read_text(encoding="utf-8"))
        result = {"design": name, "source_hash": protocol["source_hash"], "source_matches_frozen": protocol["source_hash"] == FROZEN_SOURCE_SHA256}
        try:
            check_protocol(design)
            result["check_protocol"] = "passed"
        except Exception as exc:  # preserve failure information in the receipt
            result["check_protocol"] = "failed"
            result["error"] = repr(exc)
        results.append(result)
    return {
        "current_source_digest": current,
        "expected_source_digest": FROZEN_SOURCE_SHA256,
        "source_digest_matches": current == FROZEN_SOURCE_SHA256,
        "all_check_protocol_passed": all(r["check_protocol"] == "passed" for r in results),
        "designs": results,
    }


def preservation_baseline() -> dict:
    refs = {}
    for branch, expected in EXPECTED_BRANCHES.items():
        actual = str(git("rev-parse", branch))
        refs[branch] = {"expected": expected, "actual": actual, "matches": actual == expected}
    candidate_blob = git("cat-file", "blob", f"{ENTRY_HEAD}:review/pleia_temperature_context005_validation_audit_20260919/candidate_validate_v1.py", binary=True)
    candidate_blob_sha256 = hashlib.sha256(candidate_blob).hexdigest()
    candidate_working = CANDIDATE.read_bytes()
    line_endings_only = candidate_working.replace(b"\r\n", b"\n") == candidate_blob.replace(b"\r\n", b"\n")
    status = status_entries()
    grouped = {}
    for entry in status:
        grouped.setdefault(entry[:2], []).append(entry[3:])
    return {
        "purpose": "preservation baseline before acceptance validation; pre-existing changes are retained and unstaged",
        "utc": utc(),
        "branch": str(git("branch", "--show-current")),
        "head": str(git("rev-parse", "HEAD")),
        "entry_head_expected": ENTRY_HEAD,
        "branch_heads": refs,
        "git_status": {"entry_count": len(status), "by_status": grouped, "sha256": hashlib.sha256("\n".join(status).encode()).hexdigest()},
        "excluded_stage_pattern_present": "/smart_building_conformal/outputs/conditional_context005/*/stages/" in (REPO / ".git" / "info" / "exclude").read_text(encoding="utf-8"),
        "validator": {
            "version": "candidate_representation_compatible_v1",
            "source_path": str(CANDIDATE.relative_to(REPO)).replace("\\", "/"),
            "working_tree_sha256": hashlib.sha256(candidate_working).hexdigest(),
            "audited_git_blob_sha256": candidate_blob_sha256,
            "expected_sha256": AUDIT_SOURCE_SHA256,
            "working_tree_byte_matches_committed_blob": candidate_working == candidate_blob,
            "working_tree_matches_committed_blob_after_line_ending_normalization_only": line_endings_only,
            "source_identity_matches": candidate_blob_sha256 == AUDIT_SOURCE_SHA256 and line_endings_only,
            "working_tree_byte_difference_note": "CRLF checkout representation only" if line_endings_only and candidate_working != candidate_blob else None,
            "audit_commit": ENTRY_HEAD,
        },
        "scientific_run": complete_integrity(),
        "protocol_compatibility": protocol_compatibility(),
        "no_new_experiments_or_fits_authorized": True,
    }


def preflight() -> int:
    started, cpu = time.perf_counter(), time.process_time()
    result = preservation_baseline()
    result["resources"] = {"wall_seconds": time.perf_counter() - started, "process_cpu_seconds": time.process_time() - cpu}
    write(OUT / "PRESERVATION_BASELINE.json", result)
    failed = not (result["scientific_run"]["passed"] and result["validator"]["source_identity_matches"] and result["protocol_compatibility"]["source_digest_matches"] and result["protocol_compatibility"]["all_check_protocol_passed"])
    print(json.dumps({"passed": not failed, "receipt": str(OUT / "PRESERVATION_BASELINE.json"), "declared_files": result["scientific_run"]["declared_files"]}, indent=2))
    return 1 if failed else 0


def source_reconcile() -> int:
    """Amend a completed baseline only for a confirmed CRLF checkout representation."""
    first = OUT / "PRESERVATION_BASELINE.json"
    if not first.exists():
        print("source reconciliation requires PRESERVATION_BASELINE.json", file=sys.stderr)
        return 1
    original = json.loads(first.read_text(encoding="utf-8"))
    candidate_blob = git("cat-file", "blob", f"{ENTRY_HEAD}:review/pleia_temperature_context005_validation_audit_20260919/candidate_validate_v1.py", binary=True)
    candidate_working = CANDIDATE.read_bytes()
    blob_sha = hashlib.sha256(candidate_blob).hexdigest()
    line_endings_only = candidate_working.replace(b"\r\n", b"\n") == candidate_blob.replace(b"\r\n", b"\n")
    validator = {"version": "candidate_representation_compatible_v1", "source_path": str(CANDIDATE.relative_to(REPO)).replace("\\", "/"),
                 "working_tree_sha256": hashlib.sha256(candidate_working).hexdigest(), "audited_git_blob_sha256": blob_sha,
                 "expected_sha256": AUDIT_SOURCE_SHA256, "working_tree_byte_matches_committed_blob": candidate_working == candidate_blob,
                 "working_tree_matches_committed_blob_after_line_ending_normalization_only": line_endings_only,
                 "source_identity_matches": blob_sha == AUDIT_SOURCE_SHA256 and line_endings_only,
                 "working_tree_byte_difference_note": "CRLF checkout representation only" if line_endings_only and candidate_working != candidate_blob else None,
                 "audit_commit": ENTRY_HEAD}
    compatibility = protocol_compatibility()
    result = {"purpose": "source-identity reconciliation without repeating the immutable-tree hash pass",
              "utc": utc(), "supersedes": str(first.relative_to(REPO)).replace("\\", "/"),
              "superseded_reason": "the first baseline compared working-tree CRLF bytes directly to the LF committed blob",
              "scientific_run": original["scientific_run"], "protocol_compatibility": compatibility,
              "validator": validator, "branch": str(git("branch", "--show-current")), "head": str(git("rev-parse", "HEAD")),
              "passed": bool(original["scientific_run"]["passed"] and validator["source_identity_matches"] and compatibility["source_digest_matches"] and compatibility["all_check_protocol_passed"])}
    suffix = "V2" if not (OUT / "PRESERVATION_BASELINE_V2.json").exists() else "V3"
    write(OUT / f"PRESERVATION_BASELINE_{suffix}.json", result)
    print(json.dumps({"passed": result["passed"], "validator": result["validator"]}, indent=2))
    return 0 if result["passed"] else 1


def full() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    start = {"purpose": "acceptance full validation launch", "utc": utc(), "pid": os.getpid(), "command": sys.argv, "candidate": str(CANDIDATE.relative_to(REPO)).replace("\\", "/"), "candidate_sha256": sha256(CANDIDATE), "fit_forbidden_guard": "candidate executes with src.intervals005_common.Operations(forbid=True)", "output": str((OUT / "validator_full").relative_to(REPO)).replace("\\", "/")}
    write(OUT / "FULL_VALIDATION_STARTED.json", start)
    baseline_path = OUT / "PRESERVATION_BASELINE_V3.json"
    if not baseline_path.exists():
        baseline_path = OUT / "PRESERVATION_BASELINE_V2.json"
    if not baseline_path.exists():
        write(OUT / "FULL_VALIDATION_RECEIPT.json", {"passed": False, "stage": "missing preservation baseline", "utc": utc()})
        return 1
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    before = baseline["scientific_run"]
    if not before["passed"]:
        write(OUT / "FULL_VALIDATION_RECEIPT.json", {"passed": False, "stage": "pre-validation integrity", "integrity": before, "utc": utc()})
        return 1
    old_out = os.environ.get("CANDIDATE_OUT")
    old_run = os.environ.get("CANDIDATE_RUN")
    old_limit = os.environ.get("CANDIDATE_LIMIT")
    os.environ["CANDIDATE_OUT"] = str(OUT / "validator_full")
    os.environ.pop("CANDIDATE_RUN", None)
    os.environ.pop("CANDIDATE_LIMIT", None)
    sys.path.insert(0, str(AUDIT))
    started, cpu = time.perf_counter(), time.process_time()
    exit_code = 0
    error = None
    try:
        runpy.run_path(str(CANDIDATE), run_name="__main__")
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    except Exception as exc:
        exit_code, error = 1, repr(exc)
    finally:
        if old_out is None: os.environ.pop("CANDIDATE_OUT", None)
        else: os.environ["CANDIDATE_OUT"] = old_out
        if old_run is None: os.environ.pop("CANDIDATE_RUN", None)
        else: os.environ["CANDIDATE_RUN"] = old_run
        if old_limit is None: os.environ.pop("CANDIDATE_LIMIT", None)
        else: os.environ["CANDIDATE_LIMIT"] = old_limit
    result_path = OUT / "validator_full" / "CANDIDATE_VALIDATION.json"
    candidate = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
    after = {"operations_sha256": sha256(RUN / "operations.jsonl"),
             "operations_matches_preflight": sha256(RUN / "operations.jsonl") == before["operations_sha256"],
             "completed_tree_unchanged_by_candidate": candidate.get("artifacts_unchanged") if candidate else False,
             "method": "the candidate hashes the complete run tree before and after validation; the immutable COMPLETE.json was checked at preflight"}
    receipt = {
        "purpose": "full post-results acceptance validation",
        "utc": utc(), "exit_code": exit_code, "error": error,
        "candidate_source_sha256": sha256(CANDIDATE), "candidate_version": candidate.get("version") if candidate else None,
        "fit_forbidden_guard": True,
        "candidate_passed": candidate.get("passed") if candidate else False,
        "candidate_artifacts_unchanged": candidate.get("artifacts_unchanged") if candidate else False,
        "assertions": candidate.get("totals", {}).get("assertions") if candidate else None,
        "violations": candidate.get("totals", {}).get("violations") if candidate else None,
        "sensitivity": candidate.get("sensitivity") if candidate else None,
        "integrity_before": before, "integrity_after": after,
        "resources": {"wall_seconds": time.perf_counter() - started, "process_cpu_seconds": time.process_time() - cpu, "candidate_resources": candidate.get("resources") if candidate else None},
        "passed": bool(exit_code == 0 and candidate and candidate.get("passed") and candidate.get("artifacts_unchanged") and after["operations_matches_preflight"]),
    }
    write(OUT / "FULL_VALIDATION_RECEIPT.json", receipt)
    print(json.dumps({k: receipt[k] for k in ["passed", "exit_code", "assertions", "violations", "resources"]}, indent=2, default=str))
    return 0 if receipt["passed"] else 1


def focused() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    start, cpu = time.perf_counter(), time.process_time()
    sys.path.insert(0, str(AUDIT))
    exit_code, error = 0, None
    try:
        runpy.run_path(str(FOCUSED), run_name="__main__")
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    except Exception as exc:
        exit_code, error = 1, repr(exc)
    result_path = SMART / "outputs" / "conditional_context005" / "pleia_f2_s42_C_v1_validation_audit" / "contract_tests" / "CONTRACT_TESTS.json"
    result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
    receipt = {"purpose": "focused acceptance/rejection contract recheck", "utc": utc(), "exit_code": exit_code, "error": error,
               "test_source": str(FOCUSED.relative_to(REPO)).replace("\\", "/"), "candidate_source_sha256": sha256(CANDIDATE),
               "result_source": str(result_path.relative_to(REPO)).replace("\\", "/"), "result": result,
               "resources": {"wall_seconds": time.perf_counter() - start, "process_cpu_seconds": time.process_time() - cpu},
               "passed": bool(exit_code == 0 and result and result.get("all_ok") and result.get("total") == 9)}
    write(OUT / "FOCUSED_TEST_RECEIPT.json", receipt)
    print(json.dumps({"passed": receipt["passed"], "tests": result.get("total") if result else None, "receipt": str(OUT / "FOCUSED_TEST_RECEIPT.json")}, indent=2))
    return 0 if receipt["passed"] else 1


def mechanism() -> int:
    """Re-run the documented threshold-boundary proof under its no-fit guard."""
    OUT.mkdir(parents=True, exist_ok=True)
    started, cpu = time.perf_counter(), time.process_time()
    sys.path.insert(0, str(AUDIT))
    exit_code, error = 0, None
    try:
        runpy.run_path(str(MECHANISM), run_name="__main__")
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    except Exception as exc:
        exit_code, error = 1, repr(exc)
    result_path = SMART / "outputs" / "conditional_context005" / "pleia_f2_s42_C_v1_validation_audit" / "MECHANISM_PROOF.json"
    result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
    cases = result.get("tree_routing_evidence", []) if result else []
    passed = bool(exit_code == 0 and result and result["feature_difference"]["within_frozen_tolerance"]
                  and len(cases) == 3 and all(c["manual_walk_matches_sklearn"]["engine"] and c["manual_walk_matches_sklearn"]["validator"] and c["stages_with_different_leaf"] == 1 and all(d["first_divergent_node"]["threshold_straddled"] for d in c["divergences"]) for c in cases))
    receipt = {"purpose": "threshold-boundary mechanism recheck", "utc": utc(), "exit_code": exit_code, "error": error,
               "source": str(MECHANISM.relative_to(REPO)).replace("\\", "/"), "source_sha256": sha256(MECHANISM),
               "result_source": str(result_path.relative_to(REPO)).replace("\\", "/"),
               "stage": result.get("stage") if result else None,
               "feature_max_difference": result.get("feature_difference", {}).get("max_overall") if result else None,
               "frozen_tolerance": result.get("feature_difference", {}).get("frozen_feature_tolerance") if result else None,
               "routing_cases": len(cases), "all_cases_single_threshold_straddle": passed,
               "resources": {"wall_seconds": time.perf_counter() - started, "process_cpu_seconds": time.process_time() - cpu}, "passed": passed}
    write(OUT / "THRESHOLD_BOUNDARY_RECEIPT.json", receipt)
    print(json.dumps(receipt, indent=2, default=str))
    return 0 if passed else 1


def summaries() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    source = RUN / "stages" / "tables"
    copied = {}
    for name in ["conditional_macro.csv", "fullstream_workload.csv", "inference.csv"]:
        src, dst = source / name, OUT / ("ACCEPTANCE_" + name.upper())
        shutil.copyfile(src, dst)
        copied[name] = {"source": str(src.relative_to(REPO)).replace("\\", "/"), "destination": str(dst.relative_to(REPO)).replace("\\", "/"), "sha256": sha256(dst), "bytes": dst.stat().st_size}
    write(OUT / "SUMMARY_EXPORT_RECEIPT.json", {"purpose": "directly accessible copies of unchanged saved summary tables", "utc": utc(), "copied": copied, "passed": True})
    print(json.dumps(copied, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preflight", "source-reconcile", "focused", "mechanism", "full", "summaries"])
    args = parser.parse_args()
    return {"preflight": preflight, "source-reconcile": source_reconcile, "focused": focused, "mechanism": mechanism, "full": full, "summaries": summaries}[args.action]()


if __name__ == "__main__":
    raise SystemExit(main())
