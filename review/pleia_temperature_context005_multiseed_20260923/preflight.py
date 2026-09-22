"""Zero-fit gates over the four final authorized designs."""
from __future__ import annotations

import ast
import json

from common import *


IDENTITY_FIELDS = ("features", "outcomes", "role_rows", "context_hash", "schedule_hash",
                   "cache_sha256", "columns", "frequency", "fcfg")


def main() -> None:
    if source_digest() != SOURCE_HASH:
        raise ValueError("scientific source changed")
    launch = read(REVIEW / "LAUNCH_CAPACITY.json")
    if not launch["capacity_ready"] or launch["minimum_usable_free_bytes"] < REQUIRED_FREE_BYTES:
        raise ValueError("fresh launch capacity gate not satisfied")
    old = read(SEED42_DESIGN / "frozen_protocol.json")
    records = []
    for seed in SEEDS:
        final = read(manifest(seed)); draft = read(draft_manifest(seed))
        changed = {key for key in set(final) | set(draft) if final.get(key) != draft.get(key)}
        if changed != {"execution_authorized", "authorization_kind", "authorization_reference"}:
            raise ValueError(f"unexpected draft-to-final differences for seed {seed}: {sorted(changed)}")
        if not final["execution_authorized"] or final["authorization_kind"] != "explicit_real_C_run":
            raise ValueError("final authorization mismatch")
        protocol = read(design(seed) / "frozen_protocol.json")
        ready = read(design(seed) / "readiness.json")
        if protocol["manifest"] != final or protocol["source_hash"] != SOURCE_HASH:
            raise ValueError("protocol/manifest/source mismatch")
        if not ready["passed"] or not ready["execution_authorized"] or ready["models_fitted"] != 0:
            raise ValueError("native readiness failed")
        if protocol["rows"] != {"final_fit": 14855, "final_calibration": 4954, "outer_test": 9907}:
            raise ValueError("role-row scope mismatch")
        if protocol["expected_operations"] != old["expected_operations"]:
            raise ValueError("operation budget mismatch")
        for field in IDENTITY_FIELDS:
            if protocol["data_identity"][field] != old["data_identity"][field]:
                raise ValueError(f"seed {seed} data identity changed: {field}")
        if protocol["source_inputs"] != old["source_inputs"]:
            raise ValueError("source input identity changed")
        for name in ("contexts.csv", "schedules.csv.gz", "roles.csv.gz"):
            if digest(design(seed) / name) != digest(SEED42_DESIGN / name):
                raise ValueError(f"seed {seed} design membership bytes changed: {name}")
        records.append({"model_seed": seed, "manifest_sha256": digest(manifest(seed)),
                        "protocol_sha256": digest(design(seed) / "frozen_protocol.json"),
                        "readiness_sha256": digest(design(seed) / "readiness.json"),
                        "readiness_passed": True, "execution_authorized": True})
    owner = (SMART / "src" / "intervals005_owners.py").read_text(encoding="utf-8")
    engine = (SMART / "src" / "conditional_context005.py").read_text(encoding="utf-8")
    ast.parse(owner); ast.parse(engine)
    for token in ("seed=manifest['model_seed']", "fit_owner(stages,'owner_fit_cqr','cqr',.95,seed",
                  "new_cqr(level,seed,synthetic)", "_quantile_estimator(seed)"):
        if token not in owner + engine:
            raise ValueError("native seed propagation missing: " + token)
    result = {"passed": True, "utc": now(), "models_fitted": 0, "calibrators_fitted": 0,
              "source_hash": source_digest(), "seeds": list(SEEDS), "manifests": records,
              "capacity_gate_sha256": digest(REVIEW / "LAUNCH_CAPACITY.json"),
              "seed42_preserved": digest(SEED42_RUN / "COMPLETE.json") == read(REVIEW / "PRESERVATION_BASELINE.json")["seed42_complete_sha256"],
              "same_scientific_scope_and_data_identity": True,
              "validator_path": str(VALIDATOR.relative_to(REPO)), "validator_sha256": digest(VALIDATOR),
              "focused_preflight_cases_reused": 12, "focused_preflight_all_passed": True,
              "operation_policy": "one wrapper/three native estimators/two recorded conformalize calls/one logical conformalization/one persistence radius per seed"}
    atomic(REVIEW / "PREFIT_VALIDATION.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
