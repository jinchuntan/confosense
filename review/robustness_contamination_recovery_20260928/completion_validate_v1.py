"""Independent, zero-fit validator for completion_v1 robustness units."""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SMART = REPO / "smart_building_conformal"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(SMART))
import completion_v1 as C  # noqa: E402
import robustness_saved_owner_v1 as A  # noqa: E402
import validate_saved_owner_v1 as V  # noqa: E402
from src import metrics as M, split_integrity as SI, windowing  # noqa: E402
from src.intervals005_common import Operations  # noqa: E402
from src.intervals005_data import role_frame  # noqa: E402
from src.robustness_extension import (  # noqa: E402
    FAULT_TYPES, MAGNITUDE_FAULTS, WINDOW_FRAC, expected_cell_names,
    group_test_windows, segment_masks,
)
from src.unit_checkpoint import UnitCheckpoint  # noqa: E402

VERSION = "robustness_contamination_recovery005_completion_validator_v1"


def _load(key: str):
    store = UnitCheckpoint(C.FULL_ROOT, C.checkpoint_spec(), resume=True,
                           string_columns=("group_id", "row_id"))
    loaded = store.load(key)
    if loaded is None:
        raise ValueError(f"unit checkpoint absent: {key}")
    return store, loaded[0], loaded[1], store.verify(key)


def _rebuild_features(row: dict[str, Any], data, roles, prepared):
    test_rows = roles["test"]
    meta = data["meta"].iloc[test_rows].reset_index(drop=True).copy(); meta["group_id"] = meta.group_id.astype(str)
    clean = data["X"].iloc[test_rows].reset_index(drop=True)
    truth = np.asarray(data["y"])[test_rows]
    fcfg = windowing.feature_config(data["old_protocol"]["resolved_dataset_config"], prepared.series[0].covariates)
    scales = SI.training_scale(np.asarray(data["y"]), data["meta"], roles["fit"])
    windows = group_test_windows(data["meta"], test_rows, WINDOW_FRAC)
    masks = segment_masks(data["meta"], test_rows)
    result = {"clean": (clean, truth.copy())}
    definitions = [("zero_control", "level_shift", 0.0)]
    for kind in FAULT_TYPES:
        for magnitude in ((1.0, 2.0) if kind in MAGNITUDE_FAULTS else (1.0,)):
            definitions.append((f"{kind}@{magnitude if kind in MAGNITUDE_FAULTS else 'na'}", kind, magnitude))
    for name, kind, magnitude in definitions:
        result[name] = A.rebuild_fault(prepared, meta, clean, windows, scales, fcfg,
                                       int(row["horizon"]), kind, magnitude, int(row["model_seed"]))
    return meta, truth, windows, masks, scales, result


def validate_feature_evidence(frames, features, masks):
    audit = frames["feature_audit"].set_index("stream")
    if set(audit.index) != set(features) or len(audit) != 9:
        raise ValueError("feature-audit stream matrix mismatch")
    clean = features["clean"][0].to_numpy()
    for name, (X, observed) in features.items():
        if audit.loc[name, "feature_sha256"] != A.frame_hash(X):
            raise ValueError(f"feature hash mismatch: {name}")
        if audit.loc[name, "observed_sha256"] != A.ordered_hash(map(float.hex, observed)):
            raise ValueError(f"observed stream hash mismatch: {name}")
        changed = np.any(X.to_numpy() != clean, axis=1)
        if int(audit.loc[name, "changed_feature_rows"]) != int(changed.sum()):
            raise ValueError(f"changed-feature count mismatch: {name}")
        if int(audit.loc[name, "changed_pre_rows"]) != int((changed & masks["pre"]).sum()):
            raise ValueError(f"pre-window feature count mismatch: {name}")
        if name == "zero_control":
            np.testing.assert_array_equal(X.to_numpy(), clean)
            np.testing.assert_array_equal(observed, features["clean"][1])
        elif name != "clean" and (not changed.any() or (changed & masks["pre"]).any()):
            raise ValueError(f"causal feature propagation invalid: {name}")


def _quantiles(values: np.ndarray, level: float):
    alpha = (1.0 - level) / 2.0
    finite = np.asarray(values, float); finite = finite[np.isfinite(finite)]
    return float(np.quantile(finite, alpha)), float(np.quantile(finite, 1.0 - alpha))


def validate_bounds(frames, row, owner, features):
    streams, calibration = frames["streams"], frames["calibration"]
    raw_cache = {}
    for name, (X, _) in features.items():
        raw_cache[name] = owner.raw(X)
    for cell, part in streams.groupby("cell", sort=False):
        part = part.reset_index(drop=True); policy = part.recal_policy.iloc[0]
        feature_name = str(part.feature_stream.iloc[0])
        if part.family.iloc[0] == "contamination":
            residual = calibration.residual.to_numpy(float).copy()
            rate = {"contam_clean_ref": 0.0, "contam@0.05": .05, "contam@0.1": .10}[cell]
            if rate:
                chosen = np.random.default_rng(int(row["model_seed"]) + 11).choice(
                    len(residual), size=int(round(rate * len(residual))), replace=False)
                sigma = float(frames["contamination_evidence"].train_only_pooled_sigma.iloc[0])
                residual[chosen] += 2.0 * sigma
            qlo, qhi = _quantiles(residual, float(row["historical_level"]))
            raw = raw_cache["clean"]
            expected_point = raw["point"]; expected_lo = expected_point + qlo; expected_hi = expected_point + qhi
        elif policy in {"periodic", "rolling", "native_updated"}:
            expected_lo, expected_hi = V.independent_adaptive_bounds(
                part, calibration, float(row["historical_level"]), policy)
            expected_point = raw_cache[feature_name]["point"]
        elif policy == "native_static":
            raw = raw_cache[feature_name]; expected_point = raw["point"]
            if row["historical_interval_method"] == "quantile_uncalibrated":
                expected_lo = np.minimum(raw["raw_lower"], raw["raw_upper"])
                expected_hi = np.maximum(raw["raw_lower"], raw["raw_upper"])
            else:
                expected_lo, expected_hi = raw["static_lower"], raw["static_upper"]
        else:
            raise ValueError(f"validator has no reconstruction for {cell}/{policy}")
        np.testing.assert_allclose(part.point, expected_point, rtol=1e-12, atol=1e-10)
        np.testing.assert_allclose(part.lower, expected_lo, rtol=1e-12, atol=1e-10)
        np.testing.assert_allclose(part.upper, expected_hi, rtol=1e-12, atol=1e-10)


def validate_metrics(frames, level: float):
    streams = frames["streams"]; metrics = frames["cell_metrics"].set_index("cell")
    if set(metrics.index) != set(expected_cell_names(False)) or len(metrics) != 15:
        raise ValueError("cell matrix mismatch")
    for cell, part in streams.groupby("cell", sort=False):
        part = part.reset_index(drop=True); expected = metrics.loc[cell]
        cover = ((part.y_clean >= part.lower) & (part.y_clean <= part.upper)).to_numpy()
        position = np.zeros(len(part), dtype=float)
        for _, group in part.groupby("group_id", sort=False):
            rows = group.index.to_numpy(); order = np.argsort(pd.DatetimeIndex(group.target_time).asi8, kind="stable")
            rank = np.empty(len(rows)); rank[order] = np.arange(len(rows)) / max(1, len(rows)); position[rows] = rank
        masks = {"pre": position < .25, "during": (position >= .25) & (position < .55), "post": position >= .55}
        values = {
            "coverage_all": float(cover.mean()), "coverage_pre": float(cover[masks["pre"]].mean()),
            "coverage_during": float(cover[masks["during"]].mean()), "coverage_post": float(cover[masks["post"]].mean()),
            "mean_width": float((part.upper - part.lower).mean()),
            "median_width": float((part.upper - part.lower).median()),
            "winkler": float(M.winkler_score(part.y_clean.to_numpy(), part.lower.to_numpy(),
                                               part.upper.to_numpy(), 1.0 - level)),
        }
        for name, actual in values.items():
            if not math.isclose(float(expected[name]), actual, rel_tol=1e-12, abs_tol=1e-10):
                raise ValueError(f"metric mismatch {cell}/{name}: {expected[name]} != {actual}")


def validate_recovery(frames, payload, truth, windows, freq):
    streams = frames["streams"]; saved_groups = frames["recovery_by_group"]
    summaries = {x["cell"]: x for x in payload["recovery_summaries"]}
    string_windows = {str(key): value for key, value in windows.items()}
    for cell in ("recovery_static", "recovery_periodic", "recovery_rolling"):
        part = streams[streams.cell == cell].reset_index(drop=True)
        groups, summary = V.independent_recovery(part, truth, string_windows, freq)
        saved = saved_groups[saved_groups.cell == cell].drop(columns="cell").reset_index(drop=True)
        pd.testing.assert_frame_equal(saved[groups.columns], groups, check_exact=False,
                                      rtol=1e-12, atol=1e-10, check_dtype=False)
        for name, value in summary.items():
            observed = summaries[cell].get(name)
            if value is None:
                if observed is not None: raise ValueError(f"unavailable recovery metric changed: {cell}/{name}")
            elif isinstance(value, (float, int)):
                if not math.isclose(float(observed), float(value), rel_tol=1e-12, abs_tol=1e-10):
                    raise ValueError(f"recovery summary mismatch: {cell}/{name}")
            elif observed != value:
                raise ValueError(f"recovery status mismatch: {cell}/{name}")


def validate_operations(payload, groups: int):
    expected = {
        "historical_obligation_cells": 15, "unique_corrupted_feature_rebuilds": 8,
        "unique_saved_owner_inference_passes": 9, "emitted_cell_streams": 15,
        "contamination_reconstructions": 3, "nonzero_contamination_reconstructions": 2,
        "recovery_policy_computations": 3, "point_metric_rows_from_saved_predictions": 2,
        "model_fits": 0, "conformalize_calls": 0, "new_seeds": 0,
        "group_recovery_rows": 3 * groups,
    }
    actual = payload["operation_counts"]
    for name, value in expected.items():
        if int(actual.get(name, -1)) != value:
            raise ValueError(f"operation-accounting mismatch: {name}: {actual.get(name)} != {value}")


def validate_unit(key: str) -> dict[str, Any]:
    C.completion_protocol(); launch = C.resource_gate("validation_launch")
    original = C.selected_row(key); row = C.resolved_row(original)
    before = A.digest(C.FULL_ROOT / "units" / key / "COMPLETE.json")
    start = time.perf_counter()
    with Operations(None, stage="independent_completion_validation", forbid=True) as attempts:
        _, payload, frames, complete = _load(key)
        _, data, roles, prepared = A.load_unit(original)
        owner = A.SavedOwner(row, data, roles)
        meta, truth, windows, masks, scales, features = _rebuild_features(row, data, roles, prepared)
        V.validate_zero_streams(frames["streams"])
        V.validate_delayed_release(frames["streams"])
        validate_feature_evidence(frames, features, masks)
        contamination = frames["contamination_evidence"]
        sigma = float(scales["__pooled__"])
        V.validate_contamination(contamination, frames["calibration"], frames["streams"], sigma,
                                 seed=int(row["model_seed"]))
        validate_bounds(frames, row, owner, features)
        validate_metrics(frames, float(row["historical_level"]))
        validate_recovery(frames, payload, truth, windows, data["freq"])
        validate_operations(payload, int(meta.group_id.nunique()))
        expected_points = C.point_accuracy(row, role_frame(data, roles["test"]).reset_index(drop=True))
        pd.testing.assert_frame_equal(frames["point_accuracy"], expected_points,
                                      check_exact=False, rtol=1e-12, atol=1e-10, check_dtype=False)
    if attempts.rows:
        raise ValueError("validator unexpectedly executed fitting or conformalization")
    after = A.digest(C.FULL_ROOT / "units" / key / "COMPLETE.json")
    if after != before:
        raise ValueError("validator changed completed checkpoint")
    final = C.resource_gate("validation_complete")
    result = {
        "version": VERSION, "status": "passed", "validated_utc": A.utc(), "unit": key,
        "validated_cells": 15, "validated_stream_rows": len(frames["streams"]),
        "zero_control_exact": True, "calibration_only_contamination": True,
        "causal_feature_propagation": True, "delayed_residual_availability": True,
        "group_recovery_and_censoring": True, "operation_accounting": True,
        "models_fitted": 0, "conformalize_calls": 0,
        "checkpoint_complete_sha256": after, "checkpoint_files": complete["hashes"],
        "wall_seconds": time.perf_counter() - start,
        "resource_launch": launch, "resource_complete": final,
    }
    destination = C.FULL_ROOT / "validation_v1" / key
    if destination.exists():
        saved = A.read(destination / "validation.json")
        if saved["checkpoint_complete_sha256"] != after or saved["status"] != "passed":
            raise ValueError("existing validation receipt conflicts")
        return saved
    destination.mkdir(parents=True); A.atomic_json(destination / "validation.json", result)
    A.atomic_json(destination / "COMPLETE.json", {"files": {"validation.json": A.digest(destination / "validation.json")}})
    return result


def resume_unit(key: str) -> dict[str, Any]:
    C.completion_protocol(); before = A.digest(C.FULL_ROOT / "units" / key / "COMPLETE.json")
    start = time.perf_counter()
    with Operations(None, stage="completion_zero_fit_resume", forbid=True) as attempts:
        result = C.resume_unit(key)
    after = A.digest(C.FULL_ROOT / "units" / key / "COMPLETE.json")
    if attempts.rows or before != after or result["status"] != "complete_zero_fit_resume":
        raise ValueError("zero-fit resume invariant failed")
    receipt = {
        "version": VERSION, "status": "passed", "unit": key, "utc": A.utc(),
        "models_fitted": 0, "conformalize_calls": 0,
        "checkpoint_complete_sha256_before": before,
        "checkpoint_complete_sha256_after": after,
        "wall_seconds": time.perf_counter() - start,
    }
    destination = C.FULL_ROOT / "resume_v1" / key
    if destination.exists():
        saved = A.read(destination / "resume.json")
        if saved["checkpoint_complete_sha256_after"] != after:
            raise ValueError("existing resume receipt conflicts")
        return saved
    destination.mkdir(parents=True); A.atomic_json(destination / "resume.json", receipt)
    A.atomic_json(destination / "COMPLETE.json", {"files": {"resume.json": A.digest(destination / "resume.json")}})
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=["validate", "resume"])
    parser.add_argument("--unit", required=True); args = parser.parse_args()
    result = validate_unit(args.unit) if args.action == "validate" else resume_unit(args.unit)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
