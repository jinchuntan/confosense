"""Pilot gate: one complete fold/seed unit across all three additional levels.

The full queue is released only after this gate passes.  It requires, for the
pilot unit, validated and zero-fit-resumed owners at 0.975, 0.99 and 0.995, and
all 33 policy blocks completed, validated by the frozen and extended validators
and resumed without change.  It summarises ownership, quantile levels, rank
support, chronology, delayed release, interval identity and held updates.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter

from hc_common import (
    BLOCKS_PER_UNIT, HERE, LEVELS, OWNERS, PILOT_UNIT, RUN_ROOT, UNITS, VERSION, atomic_json, digest,
    level_tag, read, unit_name, utc, verify_extension_protocol,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"PILOT_GATE_FAILURE: {message}")


def gate() -> dict:
    verify_extension_protocol(fold=PILOT_UNIT[0], seed=PILOT_UNIT[1])
    unit = unit_name(*PILOT_UNIT)
    owners = OWNERS / unit
    owner_validation = read(owners / "OWNER_VALIDATION.json")
    owner_resume = read(owners / "RESUME.json")
    require(owner_validation.get("passed") is True, "owner validation")
    require(owner_resume.get("passed") is True and owner_resume.get("models_fitted") == 0, "owner zero-fit resume")
    require(owner_validation["owner_manifest_sha256"] == digest(owners / "OWNER_MANIFEST.json"), "owner manifest identity")
    require(sorted(owner_validation["levels"]) == sorted(level_tag(level) for level in LEVELS), "owner levels")
    ledger = [json.loads(line) for line in (RUN_ROOT / "fit_ledger.jsonl").read_text(encoding="utf-8").splitlines() if line]
    pilot_fits = [row for row in ledger if row.get("event") == "new_owner_operation" and row.get("unit") == unit]
    fit_counts = Counter()
    for row in pilot_fits:
        fit_counts.update(row["operation_counts"])
    require(dict(fit_counts) == {"cqr_wrapper_fit": 3, "quantile_estimator_fit": 9, "calibrator_conformalize": 6},
            f"pilot fit ledger {dict(fit_counts)}")

    levels, statuses, max_metric = Counter(), Counter(), 0.0
    frozen_checks = extended_checks = 0
    for index in range(BLOCKS_PER_UNIT):
        stage = UNITS / unit / "blocks" / f"block_{index:03d}"
        marker = read(stage / "COMPLETE.json")
        require(marker["status"] == "complete" and marker["models_fitted"] == 0, f"block {index} marker")
        for name, expected in marker["files"].items():
            require(digest(stage / name) == expected, f"block {index} file {name}")
        frozen = read(UNITS / unit / "validation" / f"block_{index:03d}.json")
        extended = read(UNITS / unit / "validation" / f"block_{index:03d}.extended.json")
        resume = read(UNITS / unit / "resume" / f"block_{index:03d}.json")
        require(frozen.get("passed") is True and extended.get("passed") is True, f"block {index} validation")
        require(resume.get("passed") is True and resume.get("files_unchanged") is True, f"block {index} resume")
        identity = read(stage / "identity.json")
        levels[identity["policy"]["level"]] += 1
        frozen_checks += frozen["checks"]
        extended_checks += extended["metric_checks"]
        max_metric = max(max_metric, extended["maximum_metric_absolute_difference"], frozen["maximum_absolute_difference"])
        for counts in extended["update_status_counts"].values():
            for status, count in counts.items():
                statuses[(identity["policy"]["level"], identity["policy"]["strategy"], status)] += count
    require(dict(levels) == {0.975: 11, 0.99: 11, 0.995: 11}, f"pilot level coverage {dict(levels)}")
    held = {f"{level}|{strategy}|{status}": count for (level, strategy, status), count in sorted(statuses.items())
            if status == "held_insufficient_score_or_rank_support"}
    result = {
        "passed": True, "version": VERSION, "pilot_unit": unit, "utc": utc(),
        "owners": {tag: {k: record[k] for k in ("quantiles", "training_rows", "calibration_rows", "operational_cqr_rank",
                                                  "minimum_supported_pool", "rolling_window_rank_support",
                                                  "prediction_reproduction_max_difference",
                                                  "training_bin_thresholds_match_accepted_95_owner")}
                   for tag, record in owner_validation["levels"].items()},
        "chronology": owner_validation["chronology"],
        "calibration_feature_identity_max_difference": owner_validation["calibration_feature_identity_max_difference"],
        "pilot_fit_operations": dict(fit_counts),
        "blocks": BLOCKS_PER_UNIT, "blocks_by_level": {str(k): v for k, v in levels.items()},
        "frozen_validator_checks": frozen_checks, "extended_metric_checks": extended_checks,
        "maximum_metric_absolute_difference": max_metric,
        "held_insufficient_support_rows": held,
        "update_status_rows": {f"{l}|{s}|{t}": c for (l, s, t), c in sorted(statuses.items())},
        "zero_fit_resume": {"owners": True, "blocks": BLOCKS_PER_UNIT},
        "decision": "pilot passed; the supervisor continues with the remaining 14 units",
    }
    atomic_json(RUN_ROOT / "PILOT_VALIDATION.json", result)
    atomic_json(HERE / "PILOT_VALIDATION.json", result)
    print(json.dumps({"passed": True, "pilot_unit": unit, "max_metric_difference": max_metric}))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["gate"])
    parser.parse_args()
    gate()
