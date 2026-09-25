"""Write-once causal-replay protocol with pinned code and queue hashes."""
from __future__ import annotations

import json
import sys
from importlib.metadata import version

from common import (CONFIG, ENTRY_COMMIT, HERE, REPO, SCIENTIFIC_PYTHON, SOURCE_HASH,
                    VERSION, atomic_json, code_hashes, digest)


def run():
    path = HERE / "PROTOCOL.json"
    if path.exists(): raise ValueError("preserve existing protocol")
    names = ["common.py", "prepare.py", "adapter.py", "preflight.py", "validate.py", "coordinator.py",
             "supervisor.py", "aggregate.py", "test_guards.py", "freeze_protocol.py", "PROTOCOL_SCHEMA.json"]
    hashes = code_hashes(names)
    protocol = {
        "version": VERSION,
        "authorization_source": "user attachment 57a4912c-2519-4677-9975-05d69fd83ec1",
        "predecessor_protocols": {
            name: digest(HERE / name) for name in (
                "PROTOCOL_PREPARATION_FAILED_V1.json", "PROTOCOL_PREPARATION_FAILED_V2.json",
                "PROTOCOL_EXECUTION_FAILED_V1.json", "PROTOCOL_VALIDATION_FAILED_V2.json",
                "PROTOCOL_VALIDATION_FAILED_V2_1.json",
                "PROTOCOL_VALIDATED_V2_2.json",
            )
        },
        "preparation_corrections": [
            "standalone validator import path and runtime protocol-hash enforcement",
            "pin the populated scientific interpreter without adding psutil to it",
        ],
        "execution_correction": "preserve exact IEEE-754 observed/lower/upper values after v1 CSV boundary collapse",
        "validator_revision": "2.2 preserves exact decimal and hex tokens, including unavailable empty/nan tokens, and resumes the completed v2 block",
        "resume_revision": "2.3 clears stale live error/exit fields only after their failed receipts are preserved",
        "entry_commit": ENTRY_COMMIT,
        "scientific_source_hash": SOURCE_HASH,
        "runtime": {
            "python": str(SCIENTIFIC_PYTHON),
            "python_sha256": digest(SCIENTIFIC_PYTHON),
            "python_version": sys.version,
            "packages": {name: version(name) for name in (
                "numpy", "pandas", "scikit-learn", "xgboost", "MAPIE", "matplotlib"
            )},
        },
        "operational_configuration": CONFIG.relative_to(REPO).as_posix(),
        "operational_configuration_sha256": digest(CONFIG),
        "candidate_queue_sha256": digest(HERE / "evaluation_queue.csv"),
        "candidate_definitions_sha256": digest(HERE / "candidate_definitions.csv"),
        "metric_view_queue_sha256": digest(HERE / "metric_view_queue.csv"),
        "owner_inventory_sha256": digest(HERE / "owner_inventory.csv"),
        "queue_summary_sha256": digest(HERE / "QUEUE_SUMMARY.json"),
        "preflight_sha256": digest(HERE / "PREFLIGHT.json"),
        "adapter_sha256": hashes["adapter.py"],
        "validator_sha256": hashes["validate.py"],
        "code_hashes": hashes,
        "fault_specification_hashes": {
            name: digest(REPO / "smart_building_conformal" / "src" / name)
            for name in ("operational004_design.py", "operational004_events.py", "operational004_stream.py", "operational004_metrics.py")
        },
        "exact_scope": {"unique_candidate_definitions": 264, "evaluation_rows": 3960,
                        "ready_unique_candidate_definitions": 165, "ready_evaluation_rows": 2475,
                        "unavailable_unique_candidate_definitions": 99, "unavailable_evaluation_rows": 1485,
                        "policy_blocks_per_unit": 55, "units": 15},
        "fit_budget": {"forecasting_models": 0, "quantile_estimators": 0, "conformalizer_fits": 0, "new_seeds": 0},
        "disk_floor_bytes": 8 * 2**30,
        "supervisor_poll_seconds": 120,
        "publication_allowed_only_after": "all 2475 accepted evaluation rows validate and zero-fit resume; unavailable rows remain explicit",
        "population_inference": "not authorized",
        "full_study_ready": False,
    }
    atomic_json(path, protocol); print(json.dumps(protocol, indent=2)); return protocol


if __name__ == "__main__": run()
