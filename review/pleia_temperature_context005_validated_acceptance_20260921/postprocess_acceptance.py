"""Create acceptance documentation only after all required read-only gates pass."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SMART = REPO / "smart_building_conformal"
OUT = SMART / "outputs" / "conditional_context005" / "pleia_f2_s42_C_v1_validated_acceptance_v1"
RUN_TABLES = SMART / "outputs" / "conditional_context005" / "pleia_f2_s42_C_v1" / "stages" / "tables"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def main() -> None:
    baseline = load("PRESERVATION_BASELINE_V3.json")
    focused = load("FOCUSED_TEST_RECEIPT.json")
    threshold = load("THRESHOLD_BOUNDARY_RECEIPT.json")
    full = load("FULL_VALIDATION_RECEIPT.json")
    gates = {
        "preservation_baseline": bool(baseline["passed"]),
        "focused_tests": bool(focused["passed"]),
        "threshold_boundary": bool(threshold["passed"]),
        "full_validator": bool(full["passed"]),
    }
    if not all(gates.values()):
        raise SystemExit("acceptance not issued; failed or missing gates: " + json.dumps(gates))

    exports = []
    for src_name, dst_name in [
        ("conditional_macro.csv", "ACCEPTANCE_CONDITIONAL_MACRO.csv"),
        ("fullstream_workload.csv", "ACCEPTANCE_FULLSTREAM_WORKLOAD.csv"),
        ("inference.csv", "ACCEPTANCE_INFERENCE.csv"),
    ]:
        src, dst = RUN_TABLES / src_name, OUT / dst_name
        shutil.copyfile(src, dst)
        exports.append({"source": relative(src), "path": relative(dst), "bytes": dst.stat().st_size, "sha256": sha(dst)})

    decision = {
        "purpose": "post-results validated acceptance decision",
        "utc": utc(),
        "decision": "accepted_under_amended_A_and_B_and_C_contract_v1",
        "not_a_claim": [
            "The original frozen validate action is not relabelled as passing.",
            "Sub-tolerance perturbation stability is not certified.",
            "No population uncertainty interval is available at one model seed.",
            "No energy uncertainty bound is transferred to temperature.",
        ],
        "gates": gates,
        "scope": {"dataset": "pleia", "target": "temperature", "outer_fold": 2, "horizon": 1, "model_seed": 42, "confidence": 0.95, "contexts": 68, "scheduled_fault_slots": 2856},
        "full_validation": {"assertions": full["assertions"], "violations": full["violations"], "candidate_version": full["candidate_version"], "resources": full["resources"], "sensitivity": full["sensitivity"]},
        "immutable_run": {"declared_files": baseline["scientific_run"]["declared_files"], "operations_bytes": baseline["scientific_run"]["operations_bytes"], "operations_sha256": baseline["scientific_run"]["operations_sha256"], "source_digest": baseline["protocol_compatibility"]["current_source_digest"]},
        "negative_findings_retained": {"rolling_cqr_clean_coverage": 0.9081, "nominal_coverage": 0.95, "rolling_cqr_shortfall": 0.0419, "persistence_dominates_every_tradeoff": False, "population_bounds_available": False},
        "summary_exports": exports,
    }
    (OUT / "ACCEPTANCE_DECISION.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = f"""# PLEIA-temperature context005 seed-42: validated acceptance

## Decision

**Accepted under post-results A ∧ B ∧ C contract v1.** This is acceptance of the completed PLEIA temperature pilot's saved scientific record under the separately versioned representation-compatible validator. It is not a claim that the original frozen `validate` action passed, and it does not modify `smart_building_conformal/src`, the frozen protocol, the saved model, or the completed pilot tree.

The full current validation passed **{full['assertions']:,} assertions**, with **{full['violations']} violations**. Its own whole-tree before/after check and the preflight `COMPLETE.json` check both report unchanged scientific artifacts. The validator ran with fitting and calibration forbidden.

## Scope and preserved identity

The accepted record is PLEIA indoor temperature, outer fold 2, horizon 1, model seed 42, 95% confidence, 68 contexts and 2,856 scheduled fault slots. The immutable completion manifest declares {baseline['scientific_run']['declared_files']:,} files. `operations.jsonl` remains {baseline['scientific_run']['operations_bytes']:,} bytes with SHA-256 `{baseline['scientific_run']['operations_sha256']}`. The frozen source digest remains `{baseline['protocol_compatibility']['current_source_digest']}` and `check_protocol` passed for this temperature design plus the five delivered PLEIA-energy seeds.

## Why the contract changed

The original one-step frozen action conflated independent feature provenance with stability of a discontinuous gradient-boosted-tree prediction under a sub-tolerance numerical representation change. The threshold proof reran on `context_3c2ed441cb78fe67ef35_v0`: scalar/vectorized features differed by at most `1.7763568394002505e-14`, within the unchanged `1e-10` tolerance, while three serialized-tree routing cases straddled exact thresholds. In every case the manual tree walk reproduced sklearn and exactly one boosting stage diverged.

The adopted A ∧ B ∧ C contract therefore verifies: (A) independent causal features, observations, order, availability and identity; (B) serialized-model application to A-verified production features; and (C) interval/release/update state, alerts, events, and workload. It does **not** certify prediction stability under a sub-tolerance representation perturbation. See [VALIDATION_CONTRACT_AMENDMENT.md](VALIDATION_CONTRACT_AMENDMENT.md).

## Rejection evidence

All nine focused disposable-sandbox cases passed: one unmodified acceptance plus rejections for feature, observation, prediction/model application, interval, rolling update, alert flag, released-score and serialized-model corruption. Nothing in the genuine pilot tree was altered.

## Scientific limitations retained

Rolling CQR clean-stream coverage is **0.9081**, below nominal 0.95 by 0.0419; that finding is retained, not repaired away. Persistence does not dominate every detection/workload trade-off. This is a single-model-seed descriptive pilot, so population bounds are unavailable. No energy uncertainty bounds are transferred to temperature.

## Direct summaries

- [Conditional control/rule/channel macro summary](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_CONDITIONAL_MACRO.csv)
- [Full clean-stream workload summary](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_FULLSTREAM_WORKLOAD.csv)
- [Inference-status summary](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_INFERENCE.csv)

The operational receipts and evidence index are linked from [EVIDENCE_INDEX.md](EVIDENCE_INDEX.md).
"""
    (HERE / "VALIDATED_ACCEPTANCE_REPORT.md").write_text(report, encoding="utf-8")

    attempts = """# Recovery and runner attempts

This file preserves acceptance-runner failures separately from scientific validation results.

1. `preflight` attempt 001 exited before opening the repository because the new runner resolved its root one parent too high (`fatal: not a git repository`). It did not create an output receipt or access the pilot.
2. `PRESERVATION_BASELINE.json` completed the exact 127,161-file integrity pass but marked validator identity false because it compared CRLF checkout bytes directly with the LF Git blob. This was a source-representation check defect, not a candidate or scientific failure.
3. `PRESERVATION_BASELINE_V2.json` correctly attempted that reconciliation but a runner helper stripped the final newline from a binary Git blob before hashing. It is retained as an invalid tooling attempt.
4. `PRESERVATION_BASELINE_V3.json` fixes the binary handling, pins the audited Git blob SHA-256, confirms the only working-tree difference is CRLF representation, and passes. It reuses the exact successful manifest hash pass rather than repeating destructive or unnecessary work.

No attempt changed `src`, a frozen protocol, the completed pilot, a model, or any fit/calibration state.
"""
    (HERE / "RECOVERY_AND_ATTEMPTS.md").write_text(attempts, encoding="utf-8")

    index = """# Validated-acceptance evidence index

- [Acceptance decision](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_DECISION.json)
- [Acceptance report](VALIDATED_ACCEPTANCE_REPORT.md)
- [Contract amendment](VALIDATION_CONTRACT_AMENDMENT.md)
- [Versioned candidate validator](../pleia_temperature_context005_validation_audit_20260919/candidate_validate_v1.py)
- [Focused contract-test source](../pleia_temperature_context005_validation_audit_20260919/test_candidate_contract.py)
- [Reproducible runner](acceptance_runner.py)
- [Backup/readback utility](delivery_tools.py)
- [Preservation baseline V3](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/PRESERVATION_BASELINE_V3.json)
- [Focused tests receipt](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/FOCUSED_TEST_RECEIPT.json)
- [Threshold-boundary receipt](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/THRESHOLD_BOUNDARY_RECEIPT.json)
- [Full validation receipt](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/FULL_VALIDATION_RECEIPT.json)
- [Full candidate results](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/validator_full/CANDIDATE_VALIDATION.json)
- [Recovery and failed tooling attempts](RECOVERY_AND_ATTEMPTS.md)
- [Direct conditional summary](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_CONDITIONAL_MACRO.csv)
- [Direct workload summary](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_FULLSTREAM_WORKLOAD.csv)
- [Direct inference summary](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_INFERENCE.csv)
"""
    (HERE / "EVIDENCE_INDEX.md").write_text(index, encoding="utf-8")

    paths = [p for p in [OUT / "ACCEPTANCE_DECISION.json", *[OUT / Path(e["path"]).name for e in exports], *HERE.glob("*.md"), HERE / "acceptance_runner.py", HERE / "postprocess_acceptance.py"] if p.is_file()]
    with (HERE / "EVIDENCE_MANIFEST.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        for p in sorted(set(paths)):
            writer.writerow({"path": relative(p), "bytes": p.stat().st_size, "sha256": sha(p)})
    print(json.dumps({"decision": decision["decision"], "gates": gates, "exports": exports}, indent=2))


if __name__ == "__main__":
    main()
