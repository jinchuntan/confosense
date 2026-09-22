"""Freeze draft designs, compare identities, and prove the authorization gate."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from common import *
from src.conditional_context005 import freeze, execute
from src.intervals005_common import Operations, digest, source_digest


IDENTITY_FIELDS = ("features", "outcomes", "role_rows", "context_hash", "schedule_hash", "cache_sha256", "columns", "frequency", "fcfg")


def main() -> None:
    if git("branch", "--show-current") != BRANCH or source_digest() != SOURCE_HASH:
        raise ValueError("wrong branch or changed scientific source")
    seed42 = read(SEED42_DESIGN / "frozen_protocol.json")
    budget = read(REVIEW / "RESOURCE_BUDGET.json")
    records = []
    for seed in SEEDS:
        target = design(seed)
        if target.exists():
            protocol = read(target / "frozen_protocol.json")
            if protocol["manifest"] != read(manifest(seed)):
                raise ValueError(f"preserve mismatching draft design: {target}")
        else:
            result = freeze(manifest(seed), target)
            if result["models_fitted"] != 0:
                raise ValueError("draft freeze performed a fit")
        protocol = read(target / "frozen_protocol.json")
        mismatches = [field for field in IDENTITY_FIELDS if protocol["data_identity"][field] != seed42["data_identity"][field]]
        byte_identity = {name: digest(target / name) == digest(SEED42_DESIGN / name) for name in ("contexts.csv", "schedules.csv.gz", "roles.csv.gz")}
        manifest_diff = sorted(key for key in protocol["manifest"] if protocol["manifest"].get(key) != seed42["manifest"].get(key))
        record = {
            "unit_key": key(seed), "model_seed": seed, "manifest_sha256": digest(manifest(seed)),
            "protocol_sha256": digest(target / "frozen_protocol.json"), "manifest_differences_from_seed42": manifest_diff,
            "data_identity_mismatches": mismatches, "design_file_byte_identity": byte_identity,
            "source_inputs_match": protocol["source_inputs"] == seed42["source_inputs"],
            "rows_match": protocol["rows"] == seed42["rows"],
            "expected_operations_match": protocol["expected_operations"] == seed42["expected_operations"],
            "execution_authorized": protocol["manifest"]["execution_authorized"], "models_fitted": protocol["models_fitted"],
        }
        record["passed"] = bool(not mismatches and all(byte_identity.values()) and record["source_inputs_match"] and record["rows_match"] and record["expected_operations_match"] and not record["execution_authorized"] and record["models_fitted"] == 0 and manifest_diff == ["authorization_kind", "execution_authorized", "model_seed", "unit_key"])
        records.append(record)

    seed = SEEDS[0]
    unauthorized_rejected = False
    rejection = None
    with tempfile.TemporaryDirectory(prefix="temperature_preflight_gate_") as tmp:
        receipt = Path(tmp) / "readiness.json"
        write_json(receipt, {"passed": True, "protocol_sha256": records[0]["protocol_sha256"]})
        try:
            with Operations(forbid=True):
                execute(design(seed), Path(tmp) / "run", receipt)
        except PermissionError as exc:
            unauthorized_rejected = True
            rejection = repr(exc)

    result = {
        "purpose": "zero-fit draft-design and authorization-gate preflight",
        "utc": utc(), "drafts": records, "draft_design_checks_passed": all(row["passed"] for row in records),
        "native_readiness": {"attempted": False, "passed": False, "reason": "shared working/backup volume is below the frozen 8 GiB disk floor", "current_free_bytes": budget["working_free_bytes"], "required_floor_bytes": budget["engine_disk_floor_bytes"]},
        "unauthorized_execution_rejected": unauthorized_rejected, "unauthorized_execution_error": rejection,
        "models_fitted": 0, "calibrators_fitted": 0, "experiment_runs_started": 0,
        "preflight_passed": bool(all(row["passed"] for row in records) and unauthorized_rejected and budget["capacity_ready"]),
        "blocking_conditions": [] if budget["capacity_ready"] else ["insufficient shared-volume free space for projected four-seed retained runs/packages/backups and the unchanged 8 GiB floor"],
    }
    write_json(REVIEW / "DESIGN_PREFLIGHT.json", result)
    print({"draft_design_checks_passed": result["draft_design_checks_passed"], "unauthorized_execution_rejected": unauthorized_rejected, "preflight_passed": result["preflight_passed"], "models_fitted": 0})


if __name__ == "__main__":
    main()
