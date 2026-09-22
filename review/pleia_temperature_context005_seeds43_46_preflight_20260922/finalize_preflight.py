"""Consolidate bounded preflight evidence; never launch scientific work."""
from __future__ import annotations

import csv
import hashlib
import subprocess

from common import *
from src.intervals005_common import digest, source_digest


def main() -> None:
    baseline = read(REVIEW / "PRESERVATION_BASELINE.json")
    budget = read(REVIEW / "RESOURCE_BUDGET.json")
    designs = read(REVIEW / "DESIGN_PREFLIGHT.json")
    focused = read(REVIEW / "focused_tests_v2" / "FOCUSED_TEST_RECEIPT.json")
    seed42_complete_unchanged = sha256(SEED42_RUN / "COMPLETE.json") == baseline["seed42"]["complete_sha256"]
    seed42_operations_unchanged = sha256(SEED42_RUN / "operations.jsonl") == baseline["seed42"]["operations_sha256"]
    source_unchanged = source_digest() == SOURCE_HASH
    rows = []
    for record in designs["drafts"]:
        seed = record["model_seed"]
        protocol = read(design(seed) / "frozen_protocol.json")
        m = protocol["manifest"]
        rows.append({
            "unit_key": key(seed), "model_seed": seed, "dataset": m["dataset"], "physical_target": "temperature_C",
            "outer_fold": m["outer_fold"], "horizon": m["horizon"], "sampling": protocol["data_identity"]["frequency"],
            "confidence_level": m["controls"][0]["level"], "controls": ";".join(item["control_id"] for item in m["controls"]),
            "rules": ";".join(item["rule_id"] for item in m["rules"]), "channels": "numerical_only;availability_only;combined",
            "contexts": m["expected_contexts"], "scheduled_fault_slots": m["expected_schedules"], "fault_schedule_replicates": "42;43",
            "fit_rows": protocol["rows"]["final_fit"], "calibration_rows": protocol["rows"]["final_calibration"], "outer_test_rows": protocol["rows"]["outer_test"],
            "rolling_every": 24, "rolling_window": 250, "rolling_min_samples": 50,
            "endpoint": m["endpoint"], "selection": m["selection"], "execution_authorized": m["execution_authorized"],
            "feature_hash": protocol["data_identity"]["features"], "outcome_hash": protocol["data_identity"]["outcomes"],
            "context_hash": protocol["data_identity"]["context_hash"], "schedule_hash": protocol["data_identity"]["schedule_hash"],
            "cache_sha256": protocol["data_identity"]["cache_sha256"], "data_identity_matches_seed42": not record["data_identity_mismatches"],
            "source_inputs_match_seed42": record["source_inputs_match"], "design_files_byte_match_seed42": all(record["design_file_byte_identity"].values()),
            "draft_protocol_sha256": record["protocol_sha256"], "draft_passed": record["passed"],
        })
    comparison = REVIEW / "MANIFEST_COMPARISON.csv"
    with comparison.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    technical = bool(designs["draft_design_checks_passed"] and designs["unauthorized_execution_rejected"] and focused["all_ok"] and seed42_complete_unchanged and seed42_operations_unchanged and source_unchanged)
    v1_relative = (AUDIT / "candidate_validate_v1.py").relative_to(REPO).as_posix()
    v1_blob = subprocess.check_output(["git", "cat-file", "blob", f"e52a3ba6b94996f51300af523f898207162cac79:{v1_relative}"], cwd=REPO)
    v1_working = (AUDIT / "candidate_validate_v1.py").read_bytes()
    decision = {
        "purpose": "bounded zero-fit preflight readiness for PLEIA-temperature model seeds 43--46",
        "utc": utc(), "branch": BRANCH, "entry_commit": ENTRY,
        "validator": {"version": "candidate_representation_compatible_v2_explicit_paths", "path": str((REVIEW / "candidate_validate_v2.py").relative_to(REPO)).replace("\\", "/"), "sha256": sha256(REVIEW / "candidate_validate_v2.py"), "delegated_v1_working_tree_sha256": sha256(AUDIT / "candidate_validate_v1.py"), "delegated_v1_audited_blob_sha256": hashlib.sha256(v1_blob).hexdigest(), "delegated_v1_matches_audited_after_line_ending_normalization_only": v1_working.replace(b"\r\n", b"\n") == v1_blob.replace(b"\r\n", b"\n")},
        "draft_manifests": [{"seed": seed, "path": str(manifest(seed).relative_to(REPO)).replace("\\", "/"), "sha256": sha256(manifest(seed)), "execution_authorized": read(manifest(seed))["execution_authorized"]} for seed in SEEDS],
        "draft_design_checks_passed": designs["draft_design_checks_passed"], "focused_tests": {"passed": focused["passed"], "total": focused["total"], "all_ok": focused["all_ok"]},
        "old_new_limited_equivalence": focused["results"][0]["ok"],
        "seed42_complete_unchanged": seed42_complete_unchanged, "seed42_operations_unchanged": seed42_operations_unchanged, "source_unchanged": source_unchanged,
        "scientific_files_changed": False, "models_fitted": 0, "calibrators_fitted": 0, "experiments_started": 0, "full_scientific_validations_run": 0, "five_seed_analysis_run": False,
        "technical_preflight_checks_passed": technical,
        "capacity_ready": budget["capacity_ready"], "preflight_passed": bool(technical and budget["capacity_ready"]),
        "execution_authorized": False, "launch_ready": False,
        "blockers": designs["blocking_conditions"],
        "pending_execution_verification": focused["pending_execution_checks"],
        "planned_shapes_not_observed_results": {"contexts_per_seed": 68, "fault_slots_per_seed": 2856, "context_stages_per_seed": 2924, "event_control_rule_channel_rows_per_seed": 171360, "four_seed_context_stages": 11696, "four_seed_event_rows": 685440, "new_per_seed_macro_rows": 240, "five_seed_macro_rows": 300},
        "planned_operations_not_spent": {"per_seed": {"cqr_wrapper_fit": 1, "native_quantile_estimator_fit": 3, "recorded_nested_conformalize_calls": 2, "logical_conformalizations": 1, "persistence_radius": 1}, "four_seeds": {"cqr_wrapper_fit": 4, "native_quantile_estimator_fit": 12, "recorded_nested_conformalize_calls": 8, "logical_conformalizations": 4, "persistence_radius": 4}, "xgboost_lstm_enbpi_dscp_tuning_seed42_refits": 0},
        "remaining_decision": "Increase free capacity to the documented budget, then obtain explicit authorization for seeds 43--46. Only then create new final authorized manifests/protocols and launch one worker at a time; do not edit or execute these drafts.",
    }
    decision["supersedes_provisional_receipt"] = "PREFLIGHT_READINESS.json"
    write_json(REVIEW / "PREFLIGHT_READINESS_V2.json", decision)
    print({"technical_preflight_checks_passed": technical, "capacity_ready": budget["capacity_ready"], "preflight_passed": decision["preflight_passed"], "execution_authorized": False, "models_fitted": 0})


if __name__ == "__main__":
    main()
