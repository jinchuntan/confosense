"""Reconcile one completed unit with its authorized budget and acceptance gates."""
from __future__ import annotations

import argparse
import json

from common import *
from src.conformal_quantile import _sub_estimators
from src.intervals005_common import load_owner


def main(seed: int) -> None:
    root = run(seed)
    complete = read(root / "COMPLETE.json")
    protocol_sha = digest(design(seed) / "frozen_protocol.json")
    if complete["actual_exit_status"] != 0 or complete["protocol_sha256"] != protocol_sha:
        raise ValueError("completion/protocol identity mismatch")
    rows = [json.loads(line) for line in (root / "operations.jsonl").read_text(encoding="utf-8").splitlines()]
    returned = [row for row in rows if row.get("event") == "returned"]
    counts = {kind: sum(row.get("kind") == kind for row in returned) for kind in
              ("cqr_wrapper_fit", "quantile_estimator_fit", "calibrator_conformalize")}
    expected = {"cqr_wrapper_fit": 1, "quantile_estimator_fit": 3, "calibrator_conformalize": 2}
    if counts != expected:
        raise ValueError(f"operation budget mismatch: {counts}")
    identity = read(root / "stages" / "controls" / "identity.json")
    if identity["model_seed"] != seed or identity["dataset"] != "pleia":
        raise ValueError("saved owner identity mismatch")
    owners = load_owner(root / "stages" / "controls" / "controls.pkl")
    estimators, _ = _sub_estimators(owners["cqr"].owner)
    states = [model.get_params(deep=False).get("random_state") for model in estimators[:3]]
    if states != [seed, seed, seed]:
        raise ValueError(f"native estimator seed mismatch: {states}")
    validated = read(validation(seed) / "ADAPTER_VALIDATION_RECEIPT.json")
    resumed = read(resume(seed))
    if not validated["full_acceptance_gate_satisfied"] or not validated["candidate_passed"]:
        raise ValueError("full A-and-B-and-C validation did not pass")
    if not resumed["passed"] or any(resumed[name] for name in ("models_fitted", "calibrators_fitted", "replay_updates")) or not resumed["scientific_artifacts_unchanged"]:
        raise ValueError("completed zero-fit resume did not pass")
    receipt = {"passed": True, "utc": now(), "model_seed": seed, "dataset": "pleia",
               "protocol_sha256": protocol_sha, "complete_sha256": digest(root / "COMPLETE.json"),
               "declared_files": len(complete["files"]), "operation_counts": counts,
               "logical_conformalizations": 1, "persistence_radius_computations": 1,
               "native_estimator_random_states": states, "owner_sha256": identity["owner_sha256"],
               "full_validation_passed": True, "validation_assertions": validated["candidate_assertions"],
               "validation_violations": validated["candidate_violations"],
               "completed_resume_zero_fit": True, "scientific_artifacts_unchanged": True}
    atomic(acceptance(seed), receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    main(parser.parse_args().seed)
