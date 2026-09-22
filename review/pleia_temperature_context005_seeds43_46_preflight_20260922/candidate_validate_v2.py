"""Explicit-path adapter for the accepted A-and-B-and-C validator.

This interface validates design/run/owner identity before delegating to the
unchanged audited v1 implementation. Limited runs are test evidence only and
can never satisfy the full acceptance gate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from common import AUDIT, REPO, SEED42_RUN, SOURCE_HASH, read, sha256, utc

sys.path.insert(0, str(REPO / "smart_building_conformal"))
sys.path.insert(0, str(AUDIT))

from src.conditional_context005 import check_protocol, data_identity, load_data
from src.conformal_quantile import _sub_estimators
from src.intervals005_common import Operations, digest, load_owner, packages, signature, source_digest


VERSION = "candidate_representation_compatible_v2_explicit_paths"
V1 = AUDIT / "candidate_validate_v1.py"
AUDIT_COMMIT = "e52a3ba6b94996f51300af523f898207162cac79"
AUDITED_V1_SHA256 = "14cab398cf5ec389a1eae0a2f22d832a56ada31add44f93f6a38ea3095d2a091"


class IdentityError(ValueError):
    pass


def collision(output: Path, protected: Path) -> bool:
    return output == protected or output.is_relative_to(protected) or protected.is_relative_to(output)


def check_full_complete(run: Path, expected_protocol: str) -> dict[str, object]:
    complete_path = run / "COMPLETE.json"
    complete = read(complete_path)
    if complete["actual_exit_status"] != 0 or complete["protocol_sha256"] != expected_protocol:
        raise IdentityError("full_completion_identity_mismatch")
    missing = mismatched = 0
    for relative, expected in complete["files"].items():
        path = run / relative
        if not path.is_file():
            missing += 1
        elif sha256(path) != expected:
            mismatched += 1
    if missing or mismatched:
        raise IdentityError(f"full_completion_coverage_failed:missing={missing}:mismatched={mismatched}")
    return {"mode": "full", "declared_files": len(complete["files"]), "missing": missing, "mismatched": mismatched, "complete_sha256": sha256(complete_path)}


def check_limited_fixture(run: Path, expected_protocol: str) -> dict[str, object]:
    fixture_path = run / "LIMITED_FIXTURE.json"
    if not fixture_path.is_file():
        raise IdentityError("limited_fixture_receipt_missing")
    fixture = read(fixture_path)
    if fixture["source_protocol_sha256"] != expected_protocol:
        raise IdentityError("run_design_protocol_mismatch")
    source_complete = Path(fixture["source_complete_path"])
    if not source_complete.is_file() or sha256(source_complete) != fixture["source_complete_sha256"]:
        raise IdentityError("limited_fixture_source_completion_mismatch")
    return {"mode": "limited", "fixture_receipt": str(fixture_path), "source_complete_sha256": fixture["source_complete_sha256"], "full_coverage_checked": False}


def owner_identity(run: Path, expected: dict[str, object], protocol: dict[str, object], full: bool) -> dict[str, object]:
    identity_path = run / "stages" / "controls" / "identity.json"
    controls_path = run / "stages" / "controls" / "controls.pkl"
    identity = read(identity_path)
    for field in ("dataset", "model_seed", "source_hash"):
        wanted = expected["dataset"] if field == "dataset" else expected["seed"] if field == "model_seed" else SOURCE_HASH
        if identity[field] != wanted:
            raise IdentityError(f"saved_owner_{field}_mismatch")
    if identity["roles"] != protocol["data_identity"]["role_rows"] or identity["columns"] != protocol["data_identity"]["columns"]:
        raise IdentityError("saved_owner_data_identity_mismatch")
    models = load_owner(controls_path)
    for name, model in models.items():
        if model.identity["model_seed"] != expected["seed"] or model.identity["dataset"] != expected["dataset"]:
            raise IdentityError(f"saved_wrapper_identity_mismatch:{name}")
    estimators, _ = _sub_estimators(models["cqr"].owner)
    states = [estimator.get_params(deep=False).get("random_state") for estimator in estimators[:3]]
    if states != [expected["seed"]] * 3:
        raise IdentityError(f"native_estimator_random_state_mismatch:{states}")
    if full:
        calibrated = run / "stages" / "owner_cal_cqr" / "owner.pkl"
        fitted = run / "stages" / "owner_fit_cqr" / "owner.pkl"
        if digest(calibrated) != identity["owner_sha256"] or digest(fitted) != identity["fit_sha256"]:
            raise IdentityError("saved_owner_blob_identity_mismatch")
    return {"identity_path": str(identity_path), "controls_sha256": sha256(controls_path), "native_estimator_random_states": states, "owner_model_seed": identity["model_seed"], "full_owner_blob_hashes_checked": full}


def delegated_source_identity() -> dict[str, object]:
    relative = V1.relative_to(REPO).as_posix()
    committed = subprocess.check_output(["git", "cat-file", "blob", f"{AUDIT_COMMIT}:{relative}"], cwd=REPO)
    working = V1.read_bytes()
    committed_sha = hashlib.sha256(committed).hexdigest()
    normalized_match = working.replace(b"\r\n", b"\n") == committed.replace(b"\r\n", b"\n")
    if committed_sha != AUDITED_V1_SHA256 or not normalized_match:
        raise IdentityError("delegated_v1_source_identity_mismatch")
    return {"audit_commit": AUDIT_COMMIT, "audited_blob_sha256": committed_sha, "working_tree_sha256": hashlib.sha256(working).hexdigest(), "matches_after_line_ending_normalization_only": normalized_match}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", required=True, type=Path)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-dataset", required=True)
    parser.add_argument("--expected-fold", required=True, type=int)
    parser.add_argument("--expected-horizon", required=True, type=int)
    parser.add_argument("--expected-seed", required=True, type=int)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    design, run, output = (path.resolve() for path in (args.design, args.run, args.output))
    if output.exists() or collision(output, run) or collision(output, design):
        raise IdentityError("output_path_could_overwrite_or_mix_with_evidence")
    expected = {"dataset": args.expected_dataset, "fold": args.expected_fold, "horizon": args.expected_horizon, "seed": args.expected_seed}
    source_identity = delegated_source_identity()
    with Operations(forbid=True):
        protocol = check_protocol(design)
        manifest = protocol["manifest"]
        actual = {"dataset": manifest["dataset"], "fold": manifest["outer_fold"], "horizon": manifest["horizon"], "seed": manifest["model_seed"]}
        if actual != expected:
            raise IdentityError(f"expected_identity_mismatch:expected={expected}:actual={actual}")
        if protocol["source_hash"] != source_digest() or protocol["packages"] != packages():
            raise IdentityError("source_or_package_identity_mismatch")
        reconstructed = data_identity(load_data(manifest))
        if signature(reconstructed) != signature(protocol["data_identity"]):
            raise IdentityError("independently_reconstructed_data_identity_mismatch")
        protocol_sha = digest(design / "frozen_protocol.json")
        completion = check_limited_fixture(run, protocol_sha) if args.limit else check_full_complete(run, protocol_sha)
        owner = owner_identity(run, expected, protocol, full=not bool(args.limit))

    os.environ["CANDIDATE_RUN"] = str(run)
    os.environ["CANDIDATE_OUT"] = str(output)
    if args.limit:
        os.environ["CANDIDATE_LIMIT"] = str(args.limit)
    else:
        os.environ.pop("CANDIDATE_LIMIT", None)
    spec = importlib.util.spec_from_file_location("candidate_validate_v1_delegated", V1)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load audited candidate")
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)
    candidate.A = SimpleNamespace(DESIGN=design)
    candidate.main()
    report = read(output / "CANDIDATE_VALIDATION.json")
    receipt = {
        "purpose": "explicit-path A-and-B-and-C validation adapter receipt",
        "utc": utc(), "version": VERSION, "delegated_validator": str(V1.relative_to(REPO)).replace("\\", "/"),
        "delegated_validator_sha256": sha256(V1), "design": str(design), "run": str(run), "output": str(output),
        "delegated_source_identity": source_identity,
        "expected_identity": expected, "completion": completion, "owner": owner,
        "limited": bool(args.limit), "limited_variants": args.limit,
        "limited_receipt_cannot_satisfy_full_acceptance_gate": bool(args.limit),
        "candidate_passed": report["passed"], "candidate_assertions": report["totals"]["assertions"], "candidate_violations": report["totals"]["violations"],
        "artifacts_unchanged": report["artifacts_unchanged"],
        "full_acceptance_gate_satisfied": bool(not args.limit and report["passed"] and report["artifacts_unchanged"] and completion["missing"] == 0 and completion["mismatched"] == 0),
        "fit_and_calibration_forbidden": True,
    }
    (output / "ADAPTER_VALIDATION_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("version", "limited", "candidate_passed", "candidate_assertions", "candidate_violations", "full_acceptance_gate_satisfied")}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
