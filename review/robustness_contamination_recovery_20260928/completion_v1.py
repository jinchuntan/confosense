"""Versioned completion of the frozen 900-cell robustness extension.

This additive module leaves the preparation/pilot implementation untouched.  It
constructs only the eight authorized exact CQR owners, executes one remaining
historical unit at a time, and supports content-verified zero-fit resumes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SMART = REPO / "smart_building_conformal"
SCIENTIFIC_PYTHON = Path(r"C:\cfs_venv\Scripts\python.exe")
OUTPUT_ROOT = SMART / "outputs" / "robustness_contamination_recovery005"
OWNER_ROOT = OUTPUT_ROOT / "constructed_owners_v1"
FULL_ROOT = OUTPUT_ROOT / "completion_59_v1"
PROTOCOL = HERE / "COMPLETION_PROTOCOL.json"
REGISTRY = HERE / "CONSTRUCTED_OWNERS.json"
VERSION = "robustness_contamination_recovery005_completion_v1"
DISK_FLOOR = 8 * 2**30
UNIT_ALLOWANCE = 512 * 2**20
LAUNCH_HEADROOM = 3 * 2**30
RSS_LIMIT = 3 * 2**30

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SMART))
import robustness_saved_owner_v1 as A  # noqa: E402
from src import metrics as M, split_integrity as SI, windowing  # noqa: E402
from src.intervals005_common import Stages, atomic, csv as write_frame, load_owner, read  # noqa: E402
from src.intervals005_data import role_frame  # noqa: E402
from src.intervals005_owners import conformalize_owner, fit_owner, raw_predictions  # noqa: E402
from src.operational004_metrics import group_recovery  # noqa: E402
from src.robustness_extension import (  # noqa: E402
    FAULT_TYPES, MAGNITUDE_FAULTS, WINDOW_FRAC, expected_cell_names,
    group_test_windows, score_cell, segment_masks,
)
from src.unit_checkpoint import UnitCheckpoint, require_cells  # noqa: E402


def completion_protocol() -> dict[str, Any]:
    value = A.read(PROTOCOL)
    required = {
        "preparation_commit": "138c9d6d47b01953669d8d4b88e4e662ac5e2fc4",
        "preparation_crosswalk_sha256": A.digest(HERE / "CROSSWALK.csv"),
        "preparation_protocol_sha256": A.digest(HERE / "PROTOCOL.json"),
    }
    for key, actual in required.items():
        if value[key] != actual:
            raise ValueError(f"completion protocol identity mismatch: {key}")
    for name, expected in value["source_sha256"].items():
        if A.digest(HERE / name) != expected:
            raise ValueError(f"completion source identity mismatch: {name}")
    return value


def crosswalk() -> pd.DataFrame:
    frame = pd.read_csv(HERE / "CROSSWALK.csv", keep_default_na=False)
    if len(frame) != 60 or int(frame.historical_obligation_cells.astype(int).sum()) != 900:
        raise ValueError("frozen crosswalk no longer represents 60 units / 900 cells")
    return frame


def unit_key(row: dict[str, Any]) -> str:
    return f"{row['dataset']}_h{int(row['horizon'])}_f{int(row['outer_fold'])}_s{int(row['model_seed'])}"


def selected_row(key: str) -> dict[str, Any]:
    frame = crosswalk()
    keys = frame.apply(lambda r: unit_key(r.to_dict()), axis=1)
    hit = frame[keys == key]
    if len(hit) != 1:
        raise ValueError(f"crosswalk key missing or ambiguous: {key}")
    return hit.iloc[0].to_dict()


def resource_gate(stage: str, allowance: int = UNIT_ALLOWANCE) -> dict[str, Any]:
    value = A.resources(); value.update(stage=stage, utc=A.utc(), disk_allowance_bytes=int(allowance))
    if value["disk_free_bytes"] < DISK_FLOOR + allowance:
        raise RuntimeError("completion disk resource gate failed")
    if value["physical_available_bytes"] < LAUNCH_HEADROOM:
        raise RuntimeError("completion physical-RAM resource gate failed")
    if value["commit_headroom_bytes"] < LAUNCH_HEADROOM:
        raise RuntimeError("completion Windows-commit resource gate failed")
    if value["peak_working_set_bytes"] > RSS_LIMIT:
        raise RuntimeError("completion worker exceeded 3 GiB RSS limit")
    return value


def _owner_spec(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "purpose": "authorized exact higher-level owner construction",
        "unit": unit_key(row),
        "crosswalk_sha256": A.digest(HERE / "CROSSWALK.csv"),
        "preparation_protocol_sha256": A.digest(HERE / "PROTOCOL.json"),
        "owner_kind": "cqr",
        "level": float(row["historical_level"]),
        "seed": int(row["model_seed"]),
        "maximum_quantile_estimator_fits": 3,
        "maximum_conformalizations": 1,
    }


def construct_owner(key: str, *, resume: bool) -> dict[str, Any]:
    completion_protocol()
    if Path(sys.executable).resolve() != SCIENTIFIC_PYTHON.resolve():
        raise ValueError(f"wrong scientific interpreter: {sys.executable}")
    row = selected_row(key)
    if row["interval_owner_support"] != "requires_authorized_owner_construction":
        raise ValueError("owner construction requested for a saved-owner unit")
    if row["interval_owner_kind"] != "cqr" or int(row["missing_owner_estimator_fits"]) != 3:
        raise ValueError("authorized missing-owner contract changed")
    launch = resource_gate("owner_construct_launch")
    _, data, roles, _ = A.load_unit(row)
    root = OWNER_ROOT / key
    stages = Stages(root, _owner_spec(row), resume=resume)
    X, y = data["X"], np.asarray(data["y"])
    fitted = fit_owner(
        stages, "owner_fit_exact", "cqr", float(row["historical_level"]),
        int(row["model_seed"]), X.iloc[roles["fit"]], y[roles["fit"]],
    )
    calibrated = conformalize_owner(
        stages, "owner_cal_exact", fitted,
        X.iloc[roles["calibration"]], y[roles["calibration"]],
    )

    def calibration_reference(out: Path):
        owner = load_owner(calibrated / "owner.pkl")
        values = raw_predictions(
            owner, "cqr", X.iloc[roles["calibration"]].to_numpy(),
            [float(row["historical_level"])],
        )[float(row["historical_level"])]
        metadata = role_frame(data, roles["calibration"])
        write_frame(out / "calibration_metadata.csv.gz", metadata)
        write_frame(out / "calibration_values.csv.gz", values)
        return {
            "owner_sha256": A.digest(calibrated / "owner.pkl"),
            "calibration_rows": len(values), "inference_only": True,
        }

    reference = stages.run("calibration_reference", calibration_reference)
    fit_counts = A.read(fitted / "operation_counts.json")["counts"]
    cal_counts = A.read(calibrated / "operation_counts.json")["counts"]
    if int(fit_counts.get("quantile_estimator_fit", 0)) != 3:
        raise ValueError(f"owner fit count is not exactly three: {fit_counts}")
    if int(cal_counts.get("calibrator_conformalize", 0)) != 1:
        raise ValueError(f"owner conformalization count is not exactly one: {cal_counts}")
    final = resource_gate("owner_construct_complete")
    result = {
        "status": "complete", "unit": key,
        "historical_method": row["historical_interval_method"],
        "level": float(row["historical_level"]), "owner_kind": "cqr",
        "owner_path": (calibrated / "owner.pkl").relative_to(REPO).as_posix(),
        "owner_sha256": A.digest(calibrated / "owner.pkl"),
        "calibration_metadata_path": (reference / "calibration_metadata.csv.gz").relative_to(REPO).as_posix(),
        "calibration_metadata_sha256": A.digest(reference / "calibration_metadata.csv.gz"),
        "calibration_values_path": (reference / "calibration_values.csv.gz").relative_to(REPO).as_posix(),
        "calibration_values_sha256": A.digest(reference / "calibration_values.csv.gz"),
        "quantile_estimator_fits": 3, "conformalizations": 1,
        "fit_operation_counts": fit_counts, "conformalize_operation_counts": cal_counts,
        "resource_launch": launch, "resource_complete": final,
        "checkpoint_manifest_sha256": A.digest(root / "checkpoint_manifest.json"),
    }
    atomic(root / "owner_result.json", result)
    return result


def build_owner_registry() -> dict[str, Any]:
    completion_protocol()
    missing = crosswalk().query("interval_owner_support != 'exact_saved_owner'")
    owners = []
    for item in missing.to_dict("records"):
        key = unit_key(item); path = OWNER_ROOT / key / "owner_result.json"
        if not path.is_file():
            raise ValueError(f"missing constructed owner: {key}")
        result = A.read(path)
        for stem in ("owner", "calibration_metadata", "calibration_values"):
            if A.digest(REPO / result[f"{stem}_path"]) != result[f"{stem}_sha256"]:
                raise ValueError(f"constructed owner artifact changed: {key}/{stem}")
        owners.append(result)
    if len(owners) != 8 or sum(x["quantile_estimator_fits"] for x in owners) != 24 or sum(x["conformalizations"] for x in owners) != 8:
        raise ValueError("constructed owner operation budget mismatch")
    value = {
        "version": VERSION, "created_utc": A.utc(), "owners": owners,
        "units": 8, "quantile_estimator_fits": 24, "conformalizations": 8,
        "crosswalk_sha256": A.digest(HERE / "CROSSWALK.csv"),
    }
    A.atomic_json(REGISTRY, value)
    return value


def resolved_row(row: dict[str, Any]) -> dict[str, Any]:
    if row["interval_owner_support"] == "exact_saved_owner":
        return row
    registry = A.read(REGISTRY)
    hit = [x for x in registry["owners"] if x["unit"] == unit_key(row)]
    if len(hit) != 1:
        raise ValueError("constructed owner registry missing unit")
    out = dict(row); owner = hit[0]
    out.update(
        interval_owner_support="exact_saved_owner",
        support_reason="authorized exact higher-level owner constructed",
        interval_owner_path=owner["owner_path"],
        interval_owner_sha256=owner["owner_sha256"],
        calibration_metadata_path=owner["calibration_metadata_path"],
        calibration_metadata_sha256=owner["calibration_metadata_sha256"],
        calibration_values_path=owner["calibration_values_path"],
        calibration_values_sha256=owner["calibration_values_sha256"],
    )
    return out


def checkpoint_spec() -> dict[str, Any]:
    protocol = completion_protocol()
    if not REGISTRY.is_file():
        raise ValueError("constructed-owner registry absent")
    return {
        "version": VERSION, "purpose": "remaining 59 frozen robustness units",
        "preparation_commit": protocol["preparation_commit"],
        "crosswalk_sha256": A.digest(HERE / "CROSSWALK.csv"),
        "preparation_protocol_sha256": A.digest(HERE / "PROTOCOL.json"),
        "completion_protocol_sha256": A.digest(PROTOCOL),
        "constructed_owner_registry_sha256": A.digest(REGISTRY),
        "cells": expected_cell_names(False), "fit_budget_during_replay": 0,
    }


def point_accuracy(row: dict[str, Any], test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in ("persistence", "xgboost"):
        path = REPO / row[f"{model}_predictions_path"]
        if A.digest(path) != row[f"{model}_predictions_sha256"]:
            raise ValueError(f"saved {model} prediction hash mismatch")
        values = pd.read_csv(path)
        source_level = None
        point_column = "point" if "point" in values else ("prediction" if "prediction" in values else "y_pred")
        if "nominal_level" in values:
            if values.groupby("row_id", sort=False)[point_column].nunique(dropna=False).max() != 1:
                raise ValueError(f"saved {model} point prediction changes across nominal levels")
            exact = values[np.isclose(values.nominal_level, float(row["historical_level"]))]
            if len(exact):
                values = exact.reset_index(drop=True); source_level = float(row["historical_level"])
            else:
                source_level = float(values.nominal_level.iloc[0])
                values = values.drop_duplicates("row_id", keep="first").reset_index(drop=True)
        if list(values.row_id.astype(str)) != list(test.row_id.astype(str)):
            raise ValueError(f"saved {model} prediction identity mismatch")
        pred, truth = values[point_column].to_numpy(float), test.y_true.to_numpy(float)
        rows.append({
            "model": model, "mae": M.mae(truth, pred), "rmse": M.rmse(truth, pred),
            "saved_prediction_sha256": row[f"{model}_predictions_sha256"],
            "saved_point_level_selected": source_level, "level_invariant_verified": True, "fits": 0,
        })
    return pd.DataFrame(rows)


def run_unit(key: str, *, resume: bool) -> dict[str, Any]:
    completion_protocol()
    if Path(sys.executable).resolve() != SCIENTIFIC_PYTHON.resolve():
        raise ValueError(f"wrong scientific interpreter: {sys.executable}")
    original = selected_row(key)
    pilot_key = "bdg2_h1_f2_s42"
    if key == pilot_key:
        raise ValueError("accepted pilot must be reused, not repeated")
    row = resolved_row(original)
    initial = resource_gate("unit_launch")
    store = UnitCheckpoint(FULL_ROOT, checkpoint_spec(), resume=resume, string_columns=("group_id", "row_id"))
    loaded = store.load(key) if resume else None
    if loaded is not None:
        payload, frames = loaded
        if payload["operation_counts"]["model_fits"] or payload["operation_counts"]["conformalize_calls"]:
            raise ValueError("resume found fitting in replay unit")
        return {"status": "complete_zero_fit_resume", "unit": key,
                "payload": payload, "frame_rows": {name: len(frame) for name, frame in frames.items()}}

    start = time.perf_counter()
    _, data, roles, prepared = A.load_unit(original)
    owner = A.SavedOwner(row, data, roles)
    test_rows = roles["test"]
    meta = data["meta"].iloc[test_rows].reset_index(drop=True).copy(); meta["group_id"] = meta.group_id.astype(str)
    test = role_frame(data, test_rows).reset_index(drop=True)
    clean_X = data["X"].iloc[test_rows].reset_index(drop=True)
    truth = np.asarray(data["y"])[test_rows]
    if not np.isfinite(truth).all() or not np.asarray(data["available"])[test_rows].all():
        raise ValueError("test support is not fully observed")
    fcfg = windowing.feature_config(data["old_protocol"]["resolved_dataset_config"], prepared.series[0].covariates)
    scale_map = SI.training_scale(np.asarray(data["y"]), data["meta"], roles["fit"])
    windows = group_test_windows(data["meta"], test_rows, WINDOW_FRAC)
    masks = segment_masks(data["meta"], test_rows)
    groups = meta.group_id.to_numpy(); origins = pd.DatetimeIndex(meta.origin_time); targets = pd.DatetimeIndex(meta.target_time)
    delay = A.delayed_evidence(meta)
    feature_sets: dict[str, tuple[pd.DataFrame, np.ndarray]] = {"clean": (clean_X, truth.copy())}
    audit_rows = [{"stream": "clean", "feature_sha256": A.frame_hash(clean_X),
                   "observed_sha256": A.ordered_hash(map(float.hex, truth)),
                   "changed_feature_rows": 0, "changed_pre_rows": 0}]
    rebuilds = [("zero_control", "level_shift", 0.0)]
    for kind in FAULT_TYPES:
        for magnitude in ((1.0, 2.0) if kind in MAGNITUDE_FAULTS else (1.0,)):
            rebuilds.append((f"{kind}@{magnitude if kind in MAGNITUDE_FAULTS else 'na'}", kind, magnitude))
    clean_values = clean_X.to_numpy()
    for name, kind, magnitude in rebuilds:
        X2, observed = A.rebuild_fault(prepared, meta, clean_X, windows, scale_map, fcfg,
                                       int(row["horizon"]), kind, magnitude, int(row["model_seed"]))
        feature_sets[name] = (X2, observed)
        changed = np.any(X2.to_numpy() != clean_values, axis=1)
        audit_rows.append({"stream": name, "feature_sha256": A.frame_hash(X2),
                           "observed_sha256": A.ordered_hash(map(float.hex, observed)),
                           "changed_feature_rows": int(changed.sum()),
                           "changed_pre_rows": int((changed & masks["pre"]).sum())})
        if name == "zero_control":
            np.testing.assert_array_equal(X2.to_numpy(), clean_values); np.testing.assert_array_equal(observed, truth)
        elif not changed.any() or (changed & masks["pre"]).any():
            raise ValueError(f"causal feature propagation invariant failed: {name}")
        resource_gate(f"feature_rebuild:{name}")

    raw_bank = {}
    for name, (features, _) in feature_sets.items():
        raw_bank[name] = owner.raw(features); resource_gate(f"saved_owner_inference:{name}")
    selected_strategy = A.historical_strategy(row)
    streams, cells, recovery_rows, recovery_summaries, contamination_rows = [], [], [], [], []
    events = A._fault_events(windows)
    freq_minutes = data["freq"] / pd.Timedelta(minutes=1)
    tolerance = int(data["old_protocol"]["resolved_dataset_config"].get("alerts", {}).get("detection_tolerance_steps", 6))

    def emit(cell: str, family: str, features_name: str, observed: np.ndarray,
             lower: np.ndarray, upper: np.ndarray, point: np.ndarray, *, fault_type="",
             severity=np.nan, contam=np.nan, strategy=""):
        metric = score_cell(truth, observed, lower, upper, groups, meta, masks, freq_minutes,
                            int(row["rule_k"]), int(row["rule_m"]), float(row["historical_level"]), tolerance)
        metric.update({
            "dataset": row["dataset"], "horizon": int(row["horizon"]),
            "outer_fold": int(row["outer_fold"]), "model_seed": int(row["model_seed"]),
            "family": family, "cell": cell, "fault_type": fault_type,
            "severity_sd": severity, "contamination_rate": contam, "recal_policy": strategy,
            "interval_method": row["historical_interval_method"],
            "nominal_level": float(row["historical_level"]), "owner_sha256": row["interval_owner_sha256"],
            "model_fits": 0, "conformalize_calls": 0,
        }); cells.append(metric)
        frame = meta[["row_id", "group_id", "origin_time", "target_time"]].copy()
        frame["cell"] = cell; frame["family"] = family; frame["feature_stream"] = features_name
        frame["recal_policy"] = strategy; frame["y_clean"] = truth; frame["y_observed"] = observed
        frame["point"] = point; frame["lower"] = lower; frame["upper"] = upper
        frame["covered_clean"] = (truth >= lower) & (truth <= upper)
        frame["released_rows"] = delay.released_rows.to_numpy()
        frame["latest_released_target"] = delay.latest_released_target.to_numpy(); streams.append(frame)

    for cell in ["clean", "zero_control", "random_missing@na", "dropout@na", "stuck@na",
                 "level_shift@1.0", "level_shift@2.0", "drift@1.0", "drift@2.0"]:
        feature_name = "clean" if cell == "clean" else cell
        _, observed = feature_sets[feature_name]; raw = raw_bank[feature_name]
        lower, upper, applied = A.issue_bounds(owner, raw, observed, groups, origins, targets, selected_strategy)
        kind = "" if cell == "clean" else ("level_shift" if cell == "zero_control" else cell.split("@")[0])
        severity = 0.0 if cell == "zero_control" else (float(cell.split("@")[1]) if "@" in cell and cell.split("@")[1] != "na" else np.nan)
        emit(cell, "clean" if cell == "clean" else "fault", feature_name, observed,
             lower, upper, raw["point"], fault_type=kind, severity=severity, strategy=applied)

    clean_raw = raw_bank["clean"]; base_residual = owner.calibration.residual.to_numpy(float)
    pooled_sigma = float(scale_map["__pooled__"])
    for rate, cell in ((0.0, "contam_clean_ref"), (0.05, "contam@0.05"), (0.10, "contam@0.1")):
        residual = base_residual.copy(); chosen = np.array([], dtype=int)
        if rate:
            chosen = np.random.default_rng(int(row["model_seed"]) + 11).choice(
                len(residual), size=int(round(rate * len(residual))), replace=False)
            residual[chosen] += 2.0 * pooled_sigma
        alpha = (1.0 - float(row["historical_level"])) / 2.0
        qlo, qhi = np.quantile(residual, alpha), np.quantile(residual, 1.0 - alpha)
        emit(cell, "contamination", "clean", truth.copy(), clean_raw["point"] + qlo,
             clean_raw["point"] + qhi, clean_raw["point"], contam=rate,
             strategy="calibration_only_signed_residual")
        for index in chosen:
            item = owner.calibration.iloc[int(index)]
            contamination_rows.append({
                "cell": cell, "calibration_index": int(index), "row_id": item.row_id,
                "group_id": item.group_id, "original_target": item.y_true,
                "contaminated_target": item.y_true + 2.0 * pooled_sigma,
                "delta": 2.0 * pooled_sigma, "train_only_pooled_sigma": pooled_sigma,
            })

    _, recovery_observed = feature_sets["level_shift@2.0"]; recovery_raw = raw_bank["level_shift@2.0"]
    for strategy in ("static", "periodic", "rolling"):
        lower, upper, applied = A.issue_bounds(owner, recovery_raw, recovery_observed,
                                               groups, origins, targets, strategy)
        cell = f"recovery_{strategy}"
        emit(cell, "recovery", "level_shift@2.0", recovery_observed, lower, upper,
             recovery_raw["point"], fault_type="level_shift", severity=2.0, strategy=applied)
        current = streams[-1].reset_index(drop=True)
        per_group, summary = group_recovery(current, truth, events, data["freq"])
        per_group.insert(0, "cell", cell); recovery_rows.append(per_group)
        recovery_summaries.append({"cell": cell, **summary})

    cell_frame = pd.DataFrame(cells); require_cells(cell_frame, ["cell"], [(name,) for name in expected_cell_names(False)])
    stream_frame = pd.concat(streams, ignore_index=True)
    require_cells(stream_frame[["cell"]].drop_duplicates(), ["cell"], [(name,) for name in expected_cell_names(False)])
    clean_stream = stream_frame[stream_frame.cell == "clean"].reset_index(drop=True)
    zero_stream = stream_frame[stream_frame.cell == "zero_control"].reset_index(drop=True)
    pd.testing.assert_frame_equal(clean_stream.drop(columns=["cell", "family", "feature_stream"]),
                                  zero_stream.drop(columns=["cell", "family", "feature_stream"]), check_exact=True)
    points = point_accuracy(row, test); final_resource = resource_gate("pre_checkpoint")
    operation_counts = {
        "historical_obligation_cells": 15, "unique_corrupted_feature_rebuilds": 8,
        "unique_saved_owner_inference_passes": 9, "emitted_cell_streams": 15,
        "contamination_reconstructions": 3, "nonzero_contamination_reconstructions": 2,
        "recovery_policy_computations": 3,
        "group_recovery_rows": int(sum(len(x) for x in recovery_rows)),
        "point_metric_rows_from_saved_predictions": 2,
        "model_fits": 0, "conformalize_calls": 0, "new_seeds": 0,
    }
    elapsed = time.perf_counter() - start
    payload = {
        "version": VERSION, "unit": key, "crosswalk_unit": row["current_unit_id"],
        "owner_sha256": row["interval_owner_sha256"],
        "calibration_sha256": row["calibration_values_sha256"],
        "owner_origin": "constructed_exact" if original["interval_owner_support"] != "exact_saved_owner" else "preexisting_exact",
        "operation_counts": operation_counts, "wall_seconds": elapsed,
        "resource_launch": initial, "resource_pre_checkpoint": final_resource,
        "cell_metrics": cells, "recovery_summaries": recovery_summaries,
    }
    frames = {
        "streams": stream_frame, "calibration": owner.calibration,
        "feature_audit": pd.DataFrame(audit_rows),
        "contamination_evidence": pd.DataFrame(contamination_rows),
        "recovery_by_group": pd.concat(recovery_rows, ignore_index=True),
        "point_accuracy": points, "cell_metrics": cell_frame,
    }
    store.save(key, payload, frames); marker = store.verify(key)
    return {
        "status": "complete", "completed_utc": A.utc(), "unit": key, "cells": 15,
        "wall_seconds": elapsed, "peak_working_set_bytes": final_resource["peak_working_set_bytes"],
        "peak_pagefile_usage_bytes": final_resource["peak_pagefile_usage_bytes"],
        "checkpoint_complete_sha256": A.digest(FULL_ROOT / "units" / key / "COMPLETE.json"),
        "checkpoint_files": marker["hashes"], "operation_counts": operation_counts,
    }


def resume_unit(key: str) -> dict[str, Any]:
    return run_unit(key, resume=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["construct-owner", "build-owner-registry", "run-unit", "resume-unit"])
    parser.add_argument("--unit")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.action == "construct-owner":
        if not args.unit: parser.error("--unit is required")
        result = construct_owner(args.unit, resume=args.resume)
    elif args.action == "build-owner-registry":
        result = build_owner_registry()
    elif args.action == "run-unit":
        if not args.unit: parser.error("--unit is required")
        result = run_unit(args.unit, resume=args.resume)
    else:
        if not args.unit: parser.error("--unit is required")
        result = resume_unit(args.unit)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
