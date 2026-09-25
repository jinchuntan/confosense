"""Zero-fit scope/prerequisite gate for the bounded operational005 request.

This module is intentionally outside ``smart_building_conformal/src``.  It
does not import a forecasting, conformal, or operational implementation and
does not write below any completed scientific output directory.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCI = ROOT / "smart_building_conformal"
CONFIG = SCI / "configs" / "operational_amendment004.json"
MATRIX = SCI / "outputs" / "amendment005" / "study_plan_v1" / "interval_method_matrix.csv"
OUTPUT_ROOT = SCI / "outputs" / "matched_intervals005"
PROTOCOL_ROOT = SCI / "protocols" / "matched_intervals005"
UNIT_RE = re.compile(r"bdg2_f([0-2])_s(42|43|44|45|46)(?:_method_completion_v1|_v[12])$")
STREAM_RE = re.compile(r"stream_h(\d+)_l(\d+)_(.+)$")
EXPECTED_SOURCE_HASH = "a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def current_source_digest() -> str:
    root = SCI / "src"
    manifest = "\n".join(
        f"{path.relative_to(root).as_posix()}:{sha256(path)}"
        for path in sorted(root.rglob("*.py"))
    )
    return hashlib.sha256(manifest.encode()).hexdigest()


def json_read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def csv_write(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def csv_header(path: Path) -> list[str]:
    opener = gzip.open if path.suffix == ".gz" else path.open
    kwargs = {"mode": "rt", "encoding": "utf-8", "newline": ""}
    with opener(path, **kwargs) as handle:  # type: ignore[arg-type]
        return next(csv.reader(handle))


def fail(code: str) -> None:
    raise ValueError(code)


def validate_guard_record(
    record: dict[str, Any], *, declared_events: set[str], expected_route: dict[str, Any]
) -> None:
    if record["event_id"] not in declared_events:
        fail("wrong_event_membership")
    if record["evidence_target_time"] > record["decision_time"]:
        fail("future_leakage")
    for key in ("method", "level", "horizon"):
        if record[key] != expected_route[key]:
            fail("wrong_method_level_horizon_routing")
    if not record["origin_time"] < record["target_time"]:
        fail("timestamp_mutation")
    if record["available"] != record["expected_available"]:
        fail("availability_mutation")
    if record["support_cohort"] != record["expected_support_cohort"]:
        fail("native_common_cohort_mismatch")
    if record["lower"] > record["upper"] or not isinstance(record["alert"], bool):
        fail("corrupted_alert_record")


def validate_alias_rows(rows: list[dict[str, Any]]) -> None:
    primary = [row["unique_evaluation_id"] for row in rows if not row["is_alias"]]
    if len(primary) != len(set(primary)):
        fail("duplicate_alias_counting")
    known = set(primary)
    if any(row["is_alias"] and row["unique_evaluation_id"] not in known for row in rows):
        fail("orphan_alias")


def guard_fixtures() -> list[dict[str, Any]]:
    base = {
        "event_id": "event-1",
        "evidence_target_time": "2026-01-01T01:00:00Z",
        "decision_time": "2026-01-01T01:00:00Z",
        "origin_time": "2026-01-01T00:00:00Z",
        "target_time": "2026-01-01T01:00:00Z",
        "method": "cqr",
        "level": 0.95,
        "horizon": 1,
        "available": True,
        "expected_available": True,
        "support_cohort": "native",
        "expected_support_cohort": "native",
        "lower": 0.0,
        "upper": 1.0,
        "alert": False,
    }
    route = {"method": "cqr", "level": 0.95, "horizon": 1}
    cases: list[tuple[str, dict[str, Any]]] = []
    for name, changes in (
        ("wrong_event_membership", {"event_id": "event-2"}),
        ("future_leakage", {"evidence_target_time": "2026-01-01T02:00:00Z"}),
        ("wrong_method_level_horizon_routing", {"level": 0.9}),
        ("timestamp_mutation", {"origin_time": "2026-01-01T01:00:00Z"}),
        ("availability_mutation", {"available": False}),
        ("native_common_cohort_mismatch", {"support_cohort": "common"}),
        ("corrupted_alert_record", {"lower": 2.0}),
    ):
        item = dict(base)
        item.update(changes)
        cases.append((name, item))

    results: list[dict[str, Any]] = []
    validate_guard_record(base, declared_events={"event-1"}, expected_route=route)
    for expected, item in cases:
        try:
            validate_guard_record(item, declared_events={"event-1"}, expected_route=route)
        except ValueError as exc:
            actual = str(exc)
        else:
            actual = "not_rejected"
        results.append({"fixture": expected, "expected_rejection": expected, "actual_rejection": actual,
                        "passed": actual == expected})

    alias_rows = [
        {"unique_evaluation_id": "u1", "is_alias": False},
        {"unique_evaluation_id": "u1", "is_alias": False},
    ]
    try:
        validate_alias_rows(alias_rows)
    except ValueError as exc:
        actual = str(exc)
    else:
        actual = "not_rejected"
    results.append({"fixture": "duplicate_alias_counting", "expected_rejection": "duplicate_alias_counting",
                    "actual_rejection": actual, "passed": actual == "duplicate_alias_counting"})
    return results


def saved_units() -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for protocol_dir in sorted(PROTOCOL_ROOT.iterdir()):
        match = UNIT_RE.fullmatch(protocol_dir.name)
        if not match:
            continue
        output_dir = OUTPUT_ROOT / protocol_dir.name
        if not output_dir.is_dir():
            fail(f"missing_output_bundle:{protocol_dir.name}")
        spec = protocol_dir / "method_specification.json"
        if not spec.exists():
            fail(f"missing_method_specification:{protocol_dir.name}")
        complete_path = output_dir / "COMPLETE.json"
        complete = json_read(complete_path)
        units.append({
            "unit": protocol_dir.name,
            "outer_fold": int(match.group(1)),
            "model_seed": int(match.group(2)),
            "protocol": spec,
            "protocol_sha256": sha256(spec),
            "output": output_dir,
            "complete": complete_path,
            "complete_sha256": sha256(complete_path),
            "source_hash": complete["source_hash"],
        })
    return units


def saved_streams(units: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    event_named: list[str] = []
    for unit in units:
        stages = unit["output"] / "stages"
        for stage in sorted(stages.glob("stream_*")):
            match = STREAM_RE.fullmatch(stage.name)
            issued = stage / "issued.csv.gz"
            if not match or not issued.exists():
                continue
            header = csv_header(issued)
            rows.append({
                "unit": unit["unit"],
                "outer_fold": unit["outer_fold"],
                "model_seed": unit["model_seed"],
                "horizon": int(match.group(1)),
                "level": int(match.group(2)) / 100,
                "saved_method": match.group(3),
                "issued_path": issued.relative_to(ROOT).as_posix(),
                "issued_sha256": sha256(issued),
                "has_event_identity": "event_id" in header,
                "has_alert_flags": all(name in header for name in
                                       ("numerical_violation", "availability_violation", "combined_violation")),
            })
        for direct in stages.glob("*"):
            if direct.is_file() and re.search(r"event|fault", direct.name, re.IGNORECASE):
                event_named.append(direct.relative_to(ROOT).as_posix())
    return rows, event_named


def saved_method(candidate: dict[str, Any]) -> str | None:
    if candidate["method"] in {"quantile_uncalibrated", "cqr"} and candidate["strategy"] == "static":
        return candidate["method"]
    if candidate["method"] == "recentred_enbpi" and candidate["strategy"] == "static":
        return "recentred_enbpi_static"
    if candidate["method"] == "recentred_enbpi" and candidate["strategy"] == "native_updated":
        return "recentred_enbpi_updated"
    return None


def old_event_sources() -> list[dict[str, Any]]:
    specs = [
        (0, SCI / "outputs" / "amendment004" / "bdg2_threefold_f0_s42_v1" / "units" / "outer0_model42"),
        (1, SCI / "outputs" / "amendment004" / "bdg2_threefold_f1_s42_v1" / "units" / "outer1_model42"),
        (2, SCI / "outputs" / "amendment004" / "bdg2_operational_pilot_f2_s42_v2" / "units" / "outer2_model42"),
    ]
    rows = []
    for fold, path in specs:
        payload = json_read(path / "payload.json")
        catalogue = path / "catalogues.csv.gz"
        streams = path / "streams.csv.gz"
        rows.append({
            "outer_fold": fold,
            "model_seed": payload["model_seed"],
            "candidate_count": len(payload["candidate_grid"]),
            "catalogue_path": catalogue.relative_to(ROOT).as_posix(),
            "catalogue_sha256": sha256(catalogue),
            "corrupted_stream_path": streams.relative_to(ROOT).as_posix(),
            "corrupted_stream_sha256": sha256(streams),
            "compatible_with_completed_interval_protocol": False,
            "reason": "separate amendment004 fitted owners; seed42 reduced nine-candidate replay only",
        })
    return rows


def run() -> int:
    started = time.perf_counter()
    initial_free = shutil.disk_usage(ROOT).free
    config = json_read(CONFIG)
    bdg2 = next(item for item in config["resolved_datasets"] if item["dataset"] == "bdg2")
    candidates = bdg2["candidates"]
    if len(candidates) != 264:
        fail(f"authority_candidate_count:{len(candidates)}")
    units = saved_units()
    expected_units = {(fold, seed) for fold in range(3) for seed in range(42, 47)}
    actual_units = {(item["outer_fold"], item["model_seed"]) for item in units}
    if actual_units != expected_units or len(units) != 15:
        fail("completed_bdg2_unit_matrix_mismatch")
    streams, event_named = saved_streams(units)
    stream_routes = {(row["horizon"], row["level"], row["saved_method"]) for row in streams}

    prerequisite_rows: list[dict[str, Any]] = []
    compatible = 0
    for candidate in candidates:
        mapped = saved_method(candidate)
        route = (1, float(candidate["level"]), mapped) if mapped else None
        exact_policy = route in stream_routes
        compatible += int(exact_policy)
        reasons = []
        if not exact_policy:
            reasons.append("no exact saved issued-stream policy")
        reasons.append("completed interval bundles contain no fault/event replay identities")
        prerequisite_rows.append({
            "candidate_id": candidate["candidate_id"],
            "method": candidate["method"],
            "level": candidate["level"],
            "strategy": candidate["strategy"],
            "rule_id": candidate["rule_id"],
            "mapped_saved_method": mapped or "",
            "exact_saved_issued_policy": exact_policy,
            "clean_workload_possible": exact_policy,
            "event_detection_possible": False,
            "full_evaluation_ready": False,
            "blocker": "; ".join(reasons),
        })

    guards = guard_fixtures()
    if not all(item["passed"] for item in guards):
        fail("zero_fit_guard_fixture_failure")
    old_events = old_event_sources()
    unique_routes = sorted(stream_routes, key=lambda x: (x[0], x[1], x[2]))
    code_hash = sha256(Path(__file__))
    source_hash = current_source_digest()
    if source_hash != EXPECTED_SOURCE_HASH:
        fail("current_scientific_source_digest_changed")
    evaluated_source_hashes = sorted({item["source_hash"] for item in units})
    now = datetime.now(timezone.utc).isoformat()
    design_units = int(config["design"]["outer_folds"]) * len(config["design"]["model_seeds"])
    result = {
        "status": "blocked_before_scientific_execution",
        "passed": False,
        "generated_utc": now,
        "models_fitted": 0,
        "conformalizations_performed": 0,
        "scientific_evaluations_started": 0,
        "scientific_runtime_seconds": 0,
        "scientific_peak_memory_bytes": None,
        "scientific_source_changed": False,
        "current_scientific_source_digest": source_hash,
        "current_scientific_source_digest_matches_authority": True,
        "accepted_input_evaluated_source_digests": evaluated_source_hashes,
        "accepted_input_source_identities_preserved": True,
        "preflight_code_sha256": code_hash,
        "authority": {
            "configuration": CONFIG.relative_to(ROOT).as_posix(),
            "configuration_sha256": sha256(CONFIG),
            "interval_matrix": MATRIX.relative_to(ROOT).as_posix(),
            "interval_matrix_sha256": sha256(MATRIX),
            "unique_candidate_definitions": len(candidates),
            "outer_folds": int(config["design"]["outer_folds"]),
            "model_seeds": config["design"]["model_seeds"],
            "candidate_fold_seed_applications": len(candidates) * design_units,
            "inner_selection_candidate_cells": len(candidates) * design_units * 2,
            "catalogue_seeds": config["design"]["catalogue_seeds"],
            "catalogue_seeds_are_independent_experiments": False,
        },
        "completed_interval_inputs": {
            "bdg2_fold_seed_units": len(units),
            "issued_stream_instances_all_horizons": len(streams),
            "unique_saved_routes": len(unique_routes),
            "saved_routes": [
                {"horizon": h, "level": level, "method": method} for h, level, method in unique_routes
            ],
            "event_or_fault_named_files_in_bundle_stages": event_named,
            "issued_streams_with_event_identity": sum(int(row["has_event_identity"]) for row in streams),
            "candidate_definitions_with_exact_saved_policy": compatible,
            "candidate_definitions_without_exact_saved_policy": len(candidates) - compatible,
            "clean_only_candidate_fold_seed_applications_possible": compatible * design_units,
            "event_detection_candidate_fold_seed_applications_possible": 0,
        },
        "prior_operational_event_sources": old_events,
        "zero_fit_guard_fixtures": guards,
        "blocking_assertions": [
            "The frozen 264-candidate grid and completed interval stream contract differ in levels, methods and update policies.",
            "Completed interval bundles contain clean issued streams and alert flags but no predeclared fault/event identity or corrupted causal replay.",
            "The preserved amendment004 event replays use separate fitted owners and cover only seed42 and nine reduced-grid candidates.",
            "Reconstructing the missing cells would require new owner inference and/or interval conformalization, forbidden by this authorization.",
            "An empty-event stream can support background workload only, not detection recall, F1 or restricted detection-time claims.",
        ],
        "next_action_requiring_authority": (
            "Provide a versioned operational queue whose routes exactly match the completed 90/95% issued streams and provide "
            "precomputed fault-corrupted issued streams with matching protocol identities; or separately authorize causal "
            "fault replay/inference and any required conformalization from preserved owners."
        ),
        "full_study_ready": False,
        "publication_ready": False,
    }

    result["preflight_resources"] = {
        "elapsed_seconds": time.perf_counter() - started,
        "minimum_observed_free_disk_bytes": min(initial_free, shutil.disk_usage(ROOT).free),
        "required_free_disk_floor_bytes": 8 * 2**30,
        "free_disk_floor_passed": min(initial_free, shutil.disk_usage(ROOT).free) >= 8 * 2**30,
        "peak_memory_not_applicable_reason": "no scientific evaluation process was launched",
    }

    csv_write(HERE / "candidate_prerequisites.csv", prerequisite_rows, list(prerequisite_rows[0]))
    csv_write(HERE / "saved_stream_inventory.csv", streams, list(streams[0]))
    csv_write(HERE / "prior_event_sources.csv", old_events, list(old_events[0]))
    csv_write(HERE / "zero_fit_guard_fixtures.csv", guards, list(guards[0]))
    (HERE / "PREFLIGHT_FAILURE.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    report = f"""# Operational005 zero-fit preflight blocker

The authorized operational evaluation did **not** start. The gate performed zero fits, zero
conformalizations and zero scientific evaluations. Its code SHA-256 is `{code_hash}`. The current
scientific tree remains `{EXPECTED_SOURCE_HASH}`. The 15 accepted input bundles retain their three
historical evaluated-source identities rather than being relabelled with the current digest.

## Resolved scope

The only versioned 264 authority is `smart_building_conformal/configs/operational_amendment004.json`.
It defines 264 unique BDG2 candidate policies. With three outer folds and five model seeds, that is
3,960 candidate/fold/seed applications (and 7,920 two-inner-role selection cells), not 264 independent
scientific evaluations. Five catalogue seeds are repeated synthetic catalogues, not independent
experiments.

The completed interval delivery supplies {len(streams)} saved BDG2 stream instances: 15 fold/seed
units crossed with 30 horizon/level/method routes. Those routes use horizons 1/3/6, levels 90%/95%
and the five completed interval methods. Only {compatible}/264 old candidate definitions have an
exact saved h1 policy route, which would yield {compatible * design_units} clean-only applications.

## Blocking scientific contract mismatch

The old grid additionally requires 97.5%, 99% and 99.5% levels and arbitrary periodic/rolling
policies that were never issued by the completed interval protocols. More decisively, none of the
completed bundle streams carries a fault/event identity or a fault-corrupted causal replay. The
older amendment-004 event artifacts are separate seed-42, nine-candidate runs with different fitted
owner identities; they cannot be relabelled as the completed interval streams.

Consequently the saved streams can support clean background workload only. They cannot support
event recall, F1 or restricted detection time. Filling the missing inputs would require new owner
inference and/or conformalization, both expressly forbidden. No supervisor was launched because
there is no valid scientific queue to supervise.

All eight small zero-fit rejection fixtures passed: wrong event membership, future leakage, wrong
method/level/horizon routing, timestamp mutation, availability mutation, native/common cohort
mismatch, duplicate alias counting and corrupted alert records.

See `PREFLIGHT_FAILURE.json`, `candidate_prerequisites.csv`, `saved_stream_inventory.csv`,
`prior_event_sources.csv` and `zero_fit_guard_fixtures.csv` for the machine-readable evidence.
Full-study readiness and publication readiness remain false.
"""
    (HERE / "PREFLIGHT_BLOCKER.md").write_text(report, encoding="utf-8")
    manifest_names = [
        "PROTOCOL.json",
        "operational_preflight.py",
        "test_operational_preflight.py",
        "PREFLIGHT_BLOCKER.md",
        "PREFLIGHT_FAILURE.json",
        "candidate_prerequisites.csv",
        "saved_stream_inventory.csv",
        "prior_event_sources.csv",
        "zero_fit_guard_fixtures.csv",
    ]
    manifest = [
        {"path": name, "bytes": (HERE / name).stat().st_size, "sha256": sha256(HERE / name)}
        for name in manifest_names
    ]
    csv_write(HERE / "EVIDENCE_MANIFEST.csv", manifest, ["path", "bytes", "sha256"])
    print(json.dumps({
        "status": result["status"],
        "unique_candidates": len(candidates),
        "candidate_fold_seed_applications": len(candidates) * design_units,
        "exact_saved_policies": compatible,
        "event_ready_applications": 0,
        "zero_fit_guards_passed": sum(int(item["passed"]) for item in guards),
        "preflight_code_sha256": code_hash,
    }, indent=2))
    return 2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["run", "guards"])
    args = parser.parse_args()
    if args.action == "guards":
        results = guard_fixtures()
        print(json.dumps(results, indent=2))
        raise SystemExit(0 if all(item["passed"] for item in results) else 1)
    raise SystemExit(run())


if __name__ == "__main__":
    main()
