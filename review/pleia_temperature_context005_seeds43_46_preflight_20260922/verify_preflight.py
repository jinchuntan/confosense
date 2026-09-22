"""Verify the bounded preflight package without fitting or scientific replay."""
from __future__ import annotations

import re

from common import *
from src.intervals005_common import source_digest


def main() -> None:
    output_receipt = REVIEW / "PACKAGE_VERIFICATION_V2.json"
    readiness = read(REVIEW / "PREFLIGHT_READINESS_V2.json")
    design_receipt = read(REVIEW / "DESIGN_PREFLIGHT.json")
    focused = read(REVIEW / "focused_tests_v2" / "FOCUSED_TEST_RECEIPT.json")
    baseline = read(REVIEW / "PRESERVATION_BASELINE.json")
    links = []
    missing_links = []
    for markdown in (REVIEW / "README.md", REVIEW / "PREFLIGHT_REPORT.md", REVIEW / "EVIDENCE_INDEX.md"):
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", markdown.read_text(encoding="utf-8")):
            if "://" in target:
                continue
            resolved = (markdown.parent / target).resolve()
            exists = resolved.exists() or resolved == output_receipt.resolve()
            links.append({"source": markdown.name, "target": target, "exists": exists})
            if not exists:
                missing_links.append({"source": markdown.name, "target": target})
    drafts = [read(manifest(seed)) for seed in SEEDS]
    protocols = [read(design(seed) / "frozen_protocol.json") for seed in SEEDS]
    current = {
        "complete_sha256": sha256(SEED42_RUN / "COMPLETE.json"),
        "operations_sha256": sha256(SEED42_RUN / "operations.jsonl"),
        "operations_bytes": (SEED42_RUN / "operations.jsonl").stat().st_size,
        "source_digest": source_digest(),
    }
    source_protocol_diff = git("diff", "--name-only", ENTRY, "--", "smart_building_conformal/src", "smart_building_conformal/protocols")
    checks = {
        "exact_seed_order": [row["model_seed"] for row in drafts] == list(SEEDS),
        "all_drafts_unauthorized": all(row["execution_authorized"] is False and row["authorization_kind"] == "preflight_only_not_authorized" for row in drafts),
        "all_draft_protocols_zero_fit": all(row["models_fitted"] == 0 and row["manifest"]["execution_authorized"] is False for row in protocols),
        "native_readiness_receipts_absent": all(not (design(seed) / "readiness.json").exists() for seed in SEEDS),
        "production_run_paths_absent": all(not proposed_run(seed).exists() for seed in SEEDS),
        "focused_tests_passed": focused["all_ok"] and focused["total"] == 12 and focused["models_fitted"] == 0,
        "draft_design_checks_passed": design_receipt["draft_design_checks_passed"] and design_receipt["models_fitted"] == 0,
        "execution_gate_rejected": design_receipt["unauthorized_execution_rejected"],
        "readiness_decision_is_not_authorized": readiness["execution_authorized"] is False and readiness["launch_ready"] is False and readiness["preflight_passed"] is False,
        "seed42_complete_unchanged": current["complete_sha256"] == baseline["seed42"]["complete_sha256"],
        "seed42_operations_unchanged": current["operations_sha256"] == baseline["seed42"]["operations_sha256"] and current["operations_bytes"] == baseline["seed42"]["operations_bytes"],
        "source_digest_unchanged": current["source_digest"] == SOURCE_HASH,
        "no_source_or_canonical_protocol_diff": source_protocol_diff == "",
        "all_local_links_exist": not missing_links,
    }
    result = {
        "purpose": "package-level verification of bounded temperature seeds 43--46 preflight",
        "utc": utc(), "checks": checks, "passed": all(checks.values()),
        "current_preservation_values": current, "source_protocol_diff": source_protocol_diff,
        "links_checked": links, "missing_links": missing_links,
        "actual_operations": {"models_fitted": 0, "calibrators_fitted": 0, "experiments_started": 0, "full_scientific_validations": 0, "five_seed_analyses": 0},
    }
    result["supersedes_failed_receipt"] = "PACKAGE_VERIFICATION.json (failed only because its own not-yet-written link was checked)"
    write_json(output_receipt, result)
    print({"passed": result["passed"], "checks": len(checks), "missing_links": len(missing_links), "models_fitted": 0})
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
