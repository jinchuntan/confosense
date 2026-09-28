"""Versioned saved-owner Amendment-003 robustness extension.

This module is deliberately outside the frozen scientific source tree.  It
maps the sixty historical obligations to the matched-forecasting/interval
artifacts, runs one checkpointed unit without fitting, and records enough
stream evidence for a separately implemented validator.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import csv
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
import shutil
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SMART = REPO / "smart_building_conformal"
HERE = Path(__file__).resolve().parent
INTERVAL_PROTOCOLS = SMART / "protocols" / "matched_intervals005"
INTERVAL_OUTPUTS = SMART / "outputs" / "matched_intervals005"
HISTORICAL = SMART / "outputs" / "final_dissertation_v2" / "runs" / "full_20260831_220811"
MATRIX = SMART / "outputs" / "amendment005" / "support_design_v1" / "experiment_matrix.csv"
OUTPUT_ROOT = SMART / "outputs" / "robustness_contamination_recovery005"
PILOT_ROOT = OUTPUT_ROOT / "pilot_bdg2_h1_f2_s42_v1"
VERSION = "robustness_contamination_recovery005_saved_owner_v1"
SCIENTIFIC_PYTHON = Path(r"C:\cfs_venv\Scripts\python.exe")

sys.path.insert(0, str(SMART))
from src import metrics as M, split_integrity as SI, windowing  # noqa: E402
from src.intervals005_common import load_owner  # noqa: E402
from src.intervals005_data import load_data, role_frame  # noqa: E402
from src.intervals005_owners import raw_predictions  # noqa: E402
from src.interval_stream import recalibrated_bounds  # noqa: E402
from src.operational004_metrics import group_recovery  # noqa: E402
from src.residuals import availability_frontier  # noqa: E402
from src.robustness_extension import (  # noqa: E402
    FAULT_TYPES, MAGNITUDE_FAULTS, RANDOM_MISSING_FRACTION, SEGMENTS,
    WINDOW_FRAC, apply_fault_to_frame, expected_cell_names,
    group_test_windows, score_cell, segment_masks,
)
from src.unit_checkpoint import UnitCheckpoint, require_cells  # noqa: E402


PRIMARY_HORIZON = {"pleia": 1, "pleia_energy": 1, "rico": 5, "bdg2": 1}
DATASETS = tuple(PRIMARY_HORIZON)
SEEDS = (42, 43, 44, 45, 46)
FOLDS = (0, 1, 2)
DISK_FLOOR = 8 * 2**30
PILOT_DISK_ALLOWANCE = 512 * 2**20
PILOT_RSS_LIMIT = 3 * 2**30
LAUNCH_HEADROOM = 3 * 2**30


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def signature(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, default=str, separators=(",", ":")
    ).encode()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def csv_write(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    fields = list(rows[0]) if rows else []
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def ordered_hash(values: Iterable[Any]) -> str:
    return hashlib.sha256("\n".join(map(str, values)).encode()).hexdigest()


def frame_hash(frame: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(
        frame.reset_index(drop=True), index=False
    ).values.tobytes()).hexdigest()


def historical_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dataset in DATASETS:
        rows.extend(read(HISTORICAL / dataset / "provenance.json"))
    if len(rows) != 60:
        raise ValueError(f"historical obligation changed: {len(rows)} units")
    keys = [(r["dataset"], int(r["horizon"]), int(r["outer_fold"]), int(r["seed"])) for r in rows]
    if len(set(keys)) != 60:
        raise ValueError("duplicate historical unit")
    return rows


@contextlib.contextmanager
def smart_working_directory():
    previous = Path.cwd()
    os.chdir(SMART)
    try:
        yield
    finally:
        os.chdir(previous)


def load_matched_data(reference: dict[str, Any], prepared=None):
    """Call the historical loader from the working directory frozen in its paths."""
    with smart_working_directory():
        return load_data(reference, prepared)


def bundle_paths(dataset: str, fold: int, seed: int) -> tuple[Path, Path]:
    candidates = []
    for protocol_dir in INTERVAL_PROTOCOLS.glob(f"{dataset}_f{fold}_s{seed}_*"):
        frozen = protocol_dir / "frozen_protocol.json"
        output = INTERVAL_OUTPUTS / protocol_dir.name
        complete = output / "COMPLETE.json"
        if not frozen.is_file() or not complete.is_file():
            continue
        scope = read(frozen)["scope"]
        if (scope["dataset"], int(scope["outer_fold"]), int(scope["model_seed"])) == (dataset, fold, seed):
            candidates.append((protocol_dir, output))
    if len(candidates) != 1:
        raise ValueError(f"ambiguous completed interval bundle {dataset}/f{fold}/s{seed}: {candidates}")
    return candidates[0]


def verified_stage_file(stage: Path, name: str) -> dict[str, Any]:
    marker = read(stage / "COMPLETE.json")
    path = stage / name
    actual = digest(path)
    if marker["files"].get(name) != actual:
        raise ValueError(f"stage artifact hash mismatch: {path}")
    return {"path": path.relative_to(REPO).as_posix(), "sha256": actual, "bytes": path.stat().st_size}


def owner_reference(dataset: str, fold: int, seed: int, horizon: int,
                    method: str, level: float) -> dict[str, Any]:
    protocol_dir, output = bundle_paths(dataset, fold, seed)
    if method in {"cqr", "quantile_uncalibrated"}:
        if level not in {0.9, 0.95}:
            return {
                "available": False, "owner_kind": "cqr",
                "reason": "exact saved CQR/quantile owner absent at historical level",
                "required_estimator_fits": 3, "required_conformalizations": 1,
            }
        owner_kind, label = "cqr", str(int(round(level * 100)))
        owner_stage = output / "stages" / f"owner_cal_h{horizon}_cqr_l{label}"
        raw_stage = output / "stages" / f"raw_h{horizon}_cqr_l{label}"
        values_name = f"calibration_{label}.csv.gz"
    elif method in {"recentred_enbpi_static", "recentred_enbpi_updated"}:
        owner_kind, label = "enbpi", "95"
        owner_stage = output / "stages" / f"owner_cal_h{horizon}_enbpi"
        raw_stage = output / "stages" / f"raw_h{horizon}_enbpi"
        values_name = "calibration_95.csv.gz"
    else:
        return {
            "available": False, "owner_kind": "",
            "reason": f"historical method {method!r} has no saved-owner adapter",
            "required_estimator_fits": None, "required_conformalizations": None,
        }
    frozen = protocol_dir / "frozen_protocol.json"
    return {
        "available": True, "owner_kind": owner_kind, "reason": "",
        "required_estimator_fits": 0, "required_conformalizations": 0,
        "owner": verified_stage_file(owner_stage, "owner.pkl"),
        "calibration_metadata": verified_stage_file(raw_stage, "calibration_metadata.csv.gz"),
        "calibration_values": verified_stage_file(raw_stage, values_name),
        "interval_protocol": frozen.relative_to(REPO).as_posix(),
        "interval_protocol_sha256": digest(frozen),
        "interval_output": output.relative_to(REPO).as_posix(),
        "interval_complete_sha256": digest(output / "COMPLETE.json"),
    }


def point_reference(reference: dict[str, Any], dataset: str, horizon: int,
                    fold: int, seed: int, model: str) -> dict[str, Any]:
    selected = REPO / reference["owner_directory"]
    if not selected.name.endswith("_xgboost"):
        raise ValueError("matched forecasting reference is not the declared XGBoost anchor")
    unit = selected.with_name(selected.name.removesuffix("_xgboost") + f"_{model}")
    marker = read(unit / "COMPLETE.json")
    model_name = "model.json" if model == "persistence" else "model.ubj"
    result = {}
    names = [model_name, "predictions.csv.gz", "calibration.csv.gz"]
    if (unit / "fitting_membership.csv.gz").exists():
        names.append("fitting_membership.csv.gz")
    for name in names:
        path = unit / name
        actual = digest(path)
        if marker["hashes"].get(name) != actual:
            raise ValueError(f"forecast owner artifact hash mismatch: {path}")
        result[name] = {"path": path.relative_to(REPO).as_posix(), "sha256": actual,
                        "bytes": path.stat().st_size}
    result["complete"] = {"path": (unit / "COMPLETE.json").relative_to(REPO).as_posix(),
                          "sha256": digest(unit / "COMPLETE.json")}
    return result


def _role_identity(data, roles: dict[str, np.ndarray], role: str) -> dict[str, Any]:
    frame = role_frame(data, roles[role])
    return {
        f"{role}_n": len(frame),
        f"{role}_row_id_sha256": ordered_hash(frame.row_id.astype(str)),
        f"{role}_group_sequence_sha256": ordered_hash(frame.group_id.astype(str)),
        f"{role}_time_identity_sha256": ordered_hash(
            frame.origin_time.astype(str) + "|" + frame.target_time.astype(str)
        ),
        f"{role}_groups": int(frame.group_id.astype(str).nunique()),
    }


def build_crosswalk() -> dict[str, Any]:
    matrix = pd.read_csv(MATRIX)
    historical = historical_rows()
    role_cache: dict[tuple[str, int], dict[str, Any]] = {}
    rows = []
    for old in sorted(historical, key=lambda r: (r["dataset"], int(r["outer_fold"]), int(r["seed"]))):
        dataset, fold, seed = old["dataset"], int(old["outer_fold"]), int(old["seed"])
        horizon = int(old["horizon"])
        if horizon != PRIMARY_HORIZON[dataset]:
            raise ValueError("historical primary horizon changed")
        protocol_dir, output = bundle_paths(dataset, fold, seed)
        protocol = read(protocol_dir / "frozen_protocol.json")
        reference = protocol["references"][str(horizon)]
        selected = matrix[(matrix.dataset == dataset) & (matrix.horizon == horizon) &
                          (matrix.outer_fold == fold) & (matrix.model_seed == seed)]
        if selected.empty or selected.role_bank_hash.nunique() != 1 or any(
            selected[name].nunique() != 1 for name in ("fit_n", "calibration_n", "test_n")
        ):
            raise ValueError(f"matched role authority changed for {dataset}/f{fold}/s{seed}")
        cache_key = (dataset, fold)
        if cache_key not in role_cache:
            data, roles, _ = load_matched_data(reference, None)
            identity: dict[str, Any] = {}
            for role in ("fit", "calibration", "test"):
                identity.update(_role_identity(data, roles, role))
            role_cache[cache_key] = identity
        identity = role_cache[cache_key]
        for name in ("fit_n", "calibration_n", "test_n"):
            if int(selected.iloc[0][name]) != int(identity[name]):
                raise ValueError(f"role count mismatch for {dataset}/f{fold}/s{seed}/{name}")
        interval = owner_reference(dataset, fold, seed, horizon,
                                   old["interval_method"], float(old["operating_level"]))
        persistence = point_reference(reference, dataset, horizon, fold, seed, "persistence")
        xgboost = point_reference(reference, dataset, horizon, fold, seed, "xgboost")
        selected_point = persistence if old["point_model"] == "persistence" else xgboost
        row = {
            "legacy_unit_id": f"{dataset}_h{horizon}_f{fold}_s{seed}_amendment003",
            "current_unit_id": f"{dataset}_h{horizon}_f{fold}_s{seed}_matched_roles_v005",
            "identity_version": "rico_whole_run_group_blocked_v005" if dataset == "rico" else "matched_roles_v005",
            "dataset": dataset, "horizon": horizon, "outer_fold": fold, "model_seed": seed,
            "legacy_config_sha256": old["config_hash"],
            "historical_point_model": old["point_model"],
            "historical_interval_method": old["interval_method"],
            "historical_level": float(old["operating_level"]),
            "historical_recalibration": old["recalibration"],
            "rule_k": int(old["rule_k"]), "rule_m": int(old["rule_m"]),
            "operational_feasible": bool(old["operational_feasible"]),
            "role_bank_sha256": selected.iloc[0].role_bank_hash,
            **identity,
            "interval_bundle": output.relative_to(REPO).as_posix(),
            "interval_protocol_sha256": interval.get("interval_protocol_sha256", ""),
            "interval_owner_support": "exact_saved_owner" if interval["available"] else "requires_authorized_owner_construction",
            "interval_owner_kind": interval["owner_kind"],
            "interval_owner_path": interval.get("owner", {}).get("path", ""),
            "interval_owner_sha256": interval.get("owner", {}).get("sha256", ""),
            "calibration_metadata_path": interval.get("calibration_metadata", {}).get("path", ""),
            "calibration_metadata_sha256": interval.get("calibration_metadata", {}).get("sha256", ""),
            "calibration_values_path": interval.get("calibration_values", {}).get("path", ""),
            "calibration_values_sha256": interval.get("calibration_values", {}).get("sha256", ""),
            "support_reason": interval["reason"],
            "missing_owner_estimator_fits": interval["required_estimator_fits"],
            "missing_owner_conformalizations": interval["required_conformalizations"],
            "selected_point_owner_path": selected_point["model.json" if old["point_model"] == "persistence" else "model.ubj"]["path"],
            "selected_point_owner_sha256": selected_point["model.json" if old["point_model"] == "persistence" else "model.ubj"]["sha256"],
            "persistence_owner_sha256": persistence["model.json"]["sha256"],
            "persistence_predictions_path": persistence["predictions.csv.gz"]["path"],
            "persistence_predictions_sha256": persistence["predictions.csv.gz"]["sha256"],
            "xgboost_owner_sha256": xgboost["model.ubj"]["sha256"],
            "xgboost_predictions_path": xgboost["predictions.csv.gz"]["path"],
            "xgboost_predictions_sha256": xgboost["predictions.csv.gz"]["sha256"],
            "historical_obligation_cells": 15,
        }
        rows.append(row)
    if len(rows) != 60 or sum(r["historical_obligation_cells"] for r in rows) != 900:
        raise ValueError("crosswalk does not preserve the 900-cell obligation")
    unsupported = [r for r in rows if r["interval_owner_support"] != "exact_saved_owner"]
    if len(unsupported) != 8:
        raise ValueError(f"saved-owner support changed: expected 8 missing, found {len(unsupported)}")
    csv_write(HERE / "CROSSWALK.csv", rows)
    summary = {
        "version": VERSION, "created_utc": utc(), "units": 60, "cells": 900,
        "exact_saved_owner_units": 52, "missing_exact_owner_units": 8,
        "missing_exact_owner_cells": 120,
        "missing_owner_estimator_fits": sum(int(r["missing_owner_estimator_fits"] or 0) for r in unsupported),
        "missing_owner_conformalizations": sum(int(r["missing_owner_conformalizations"] or 0) for r in unsupported),
        "rico_identity_version": "rico_whole_run_group_blocked_v005",
        "operational_replay_dependency": False,
        "crosswalk_sha256": digest(HERE / "CROSSWALK.csv"),
        "unsupported_units": [{k: r[k] for k in (
            "legacy_unit_id", "historical_interval_method", "historical_level",
            "support_reason", "missing_owner_estimator_fits", "missing_owner_conformalizations"
        )} for r in unsupported],
    }
    atomic_json(HERE / "CROSSWALK_SUMMARY.json", summary)
    return summary


class _PerformanceInformation(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong), ("CommitTotal", ctypes.c_size_t),
        ("CommitLimit", ctypes.c_size_t), ("CommitPeak", ctypes.c_size_t),
        ("PhysicalTotal", ctypes.c_size_t), ("PhysicalAvailable", ctypes.c_size_t),
        ("SystemCache", ctypes.c_size_t), ("KernelTotal", ctypes.c_size_t),
        ("KernelPaged", ctypes.c_size_t), ("KernelNonpaged", ctypes.c_size_t),
        ("PageSize", ctypes.c_size_t), ("HandleCount", ctypes.c_ulong),
        ("ProcessCount", ctypes.c_ulong), ("ThreadCount", ctypes.c_ulong),
    ]


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def resources() -> dict[str, int]:
    ctypes.windll.psapi.GetPerformanceInfo.argtypes = [
        ctypes.POINTER(_PerformanceInformation), wintypes.DWORD
    ]
    ctypes.windll.psapi.GetPerformanceInfo.restype = wintypes.BOOL
    ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(_ProcessMemoryCounters), wintypes.DWORD
    ]
    ctypes.windll.psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    info = _PerformanceInformation(); info.cb = ctypes.sizeof(info)
    if not ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(info), info.cb):
        raise OSError("GetPerformanceInfo failed")
    counters = _ProcessMemoryCounters(); counters.cb = ctypes.sizeof(counters)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    free = shutil.disk_usage(REPO.anchor).free
    return {
        "physical_available_bytes": int(info.PhysicalAvailable * info.PageSize),
        "commit_headroom_bytes": int((info.CommitLimit - info.CommitTotal) * info.PageSize),
        "disk_free_bytes": int(free), "working_set_bytes": int(counters.WorkingSetSize),
        "peak_working_set_bytes": int(counters.PeakWorkingSetSize),
        "pagefile_usage_bytes": int(counters.PagefileUsage),
        "peak_pagefile_usage_bytes": int(counters.PeakPagefileUsage),
    }


def resource_gate(stage: str) -> dict[str, Any]:
    value = resources(); value["stage"] = stage; value["utc"] = utc()
    if value["disk_free_bytes"] < DISK_FLOOR + PILOT_DISK_ALLOWANCE:
        raise RuntimeError("pilot disk resource gate failed")
    if value["physical_available_bytes"] < LAUNCH_HEADROOM:
        raise RuntimeError("pilot physical-RAM resource gate failed")
    if value["commit_headroom_bytes"] < LAUNCH_HEADROOM:
        raise RuntimeError("pilot Windows-commit resource gate failed")
    if value["peak_working_set_bytes"] > PILOT_RSS_LIMIT:
        raise RuntimeError("pilot worker exceeded 3 GiB RSS limit")
    return value


class SavedOwner:
    fitted_models = 0

    def __init__(self, row: dict[str, Any], data, roles):
        if row["interval_owner_support"] != "exact_saved_owner":
            raise ValueError(row["support_reason"])
        path = REPO / row["interval_owner_path"]
        if digest(path) != row["interval_owner_sha256"]:
            raise ValueError("saved interval owner hash mismatch")
        self.owner = load_owner(path)
        self.owner_kind = row["interval_owner_kind"]
        self.method = row["historical_interval_method"]
        self.level = float(row["historical_level"])
        self.horizon = int(row["horizon"])
        self.columns = list(data["X"].columns)
        metadata = pd.read_csv(REPO / row["calibration_metadata_path"])
        values = pd.read_csv(REPO / row["calibration_values_path"])
        expected = role_frame(data, roles["calibration"])
        if list(metadata.row_id.astype(str)) != list(expected.row_id.astype(str)):
            raise ValueError("calibration identity mismatch")
        np.testing.assert_allclose(metadata.y_true, expected.y_true, rtol=0, atol=1e-12)
        if len(values) != len(metadata) or not np.isfinite(values.point).all():
            raise ValueError("invalid saved calibration prediction")
        self.calibration = metadata[["row_id", "group_id", "origin_time", "target_time", "y_true"]].copy()
        self.calibration["group_id"] = self.calibration.group_id.astype(str)
        self.calibration["point"] = values.point.to_numpy(float)
        self.calibration["residual"] = self.calibration.y_true - self.calibration.point
        self.identity = signature({
            "owner_sha256": row["interval_owner_sha256"],
            "calibration_sha256": row["calibration_values_sha256"],
            "method": self.method, "level": self.level, "columns": self.columns,
        })

    def raw(self, X: pd.DataFrame) -> dict[str, np.ndarray]:
        if list(X.columns) != self.columns:
            raise ValueError("prediction feature schema mismatch")
        result = raw_predictions(self.owner, self.owner_kind, X.to_numpy(), [self.level])[self.level]
        return {name: result[name].to_numpy(float) for name in (
            "point", "raw_lower", "raw_upper", "static_lower", "static_upper"
        )}


def _row_dict(dataset: str, fold: int, seed: int) -> dict[str, Any]:
    frame = pd.read_csv(HERE / "CROSSWALK.csv", keep_default_na=False)
    hit = frame[(frame.dataset == dataset) & (frame.outer_fold == fold) & (frame.model_seed == seed)]
    if len(hit) != 1:
        raise ValueError("crosswalk unit missing or ambiguous")
    return hit.iloc[0].to_dict()


def load_unit(row: dict[str, Any]):
    protocol = read(REPO / row["interval_bundle"].replace("outputs", "protocols", 1) / "frozen_protocol.json")
    reference = protocol["references"][str(int(row["horizon"]))]
    data, roles, prepared = load_matched_data(reference, None)
    for role in ("fit", "calibration", "test"):
        actual = _role_identity(data, roles, role)
        for key, value in actual.items():
            expected = row[key]
            if str(value) != str(expected):
                raise ValueError(f"crosswalk identity changed: {key}")
    return protocol, data, roles, prepared[0]


def _window_for(windows: dict, group: Any) -> pd.DatetimeIndex:
    if group in windows:
        return windows[group]
    for key, value in windows.items():
        if str(key) == str(group):
            return value
    if len(windows) == 1:
        return next(iter(windows.values()))
    raise ValueError(f"fault window absent for group {group!r}")


def rebuild_fault(prepared, meta_test: pd.DataFrame, clean_X: pd.DataFrame,
                  windows: dict, scale_map: dict, fcfg, horizon: int,
                  kind: str, magnitude_sd: float, seed: int):
    series = []
    for item in prepared.series:
        magnitude = magnitude_sd * float(scale_map.get(item.group_id, scale_map["__pooled__"]))
        series.append(replace(item, frame=apply_fault_to_frame(
            item.frame, _window_for(windows, item.group_id), kind, magnitude, seed + 7
        )))
    built = windowing.build_dataset_windows(replace(prepared, series=series), horizon, fcfg)
    lookup = built["meta"][["group_id", "origin_time"]].copy(); lookup["row"] = np.arange(len(lookup))
    selected = meta_test[["group_id", "origin_time"]].merge(
        lookup, on=["group_id", "origin_time"], how="left", validate="one_to_one"
    )
    if selected.row.isna().any():
        raise ValueError("fault rebuild lost frozen test identities")
    indices = selected.row.to_numpy(int)
    X = built["X"].iloc[indices].reset_index(drop=True)
    y = np.asarray(built["y"])[indices]
    if list(X.columns) != list(clean_X.columns):
        raise ValueError("fault rebuild changed feature schema")
    return X, y


def delayed_evidence(meta: pd.DataFrame) -> pd.DataFrame:
    out = meta[["row_id", "group_id", "origin_time", "target_time"]].copy().reset_index(drop=True)
    released = np.zeros(len(out), dtype=int)
    latest = np.full(len(out), np.datetime64("NaT"), dtype="datetime64[ns]")
    for group, part in out.groupby("group_id", sort=False):
        rows = part.index.to_numpy()
        order = np.argsort(pd.DatetimeIndex(part.target_time).asi8, kind="stable")
        rows = rows[order]
        frontier = availability_frontier(
            pd.DatetimeIndex(out.loc[rows, "origin_time"]),
            pd.DatetimeIndex(out.loc[rows, "target_time"]),
        )
        released[rows] = frontier
        targets = pd.DatetimeIndex(out.loc[rows, "target_time"]).to_numpy()
        for local, count in enumerate(frontier):
            if count:
                latest[rows[local]] = targets[count - 1]
    out["released_rows"] = released
    out["latest_released_target"] = latest
    return out[["released_rows", "latest_released_target"]]


def issue_bounds(owner: SavedOwner, raw: dict[str, np.ndarray], y_observed: np.ndarray,
                 groups: np.ndarray, origins: pd.DatetimeIndex, targets: pd.DatetimeIndex,
                 strategy: str) -> tuple[np.ndarray, np.ndarray, str]:
    if strategy == "static":
        if owner.method == "quantile_uncalibrated":
            return np.minimum(raw["raw_lower"], raw["raw_upper"]), np.maximum(raw["raw_lower"], raw["raw_upper"]), "native_static"
        return raw["static_lower"], raw["static_upper"], "native_static"
    kwargs = {}
    actual = strategy
    if strategy == "native_updated":
        actual, kwargs = "periodic", {"update_every": 1, "min_samples": 1, "window": None}
    values = recalibrated_bounds(
        actual, raw["point"], y_observed, owner.calibration.y_true,
        owner.calibration.point, groups, origins, targets,
        owner.calibration.group_id.to_numpy(), owner.calibration.target_time,
        owner.level, owner.horizon, **kwargs,
    )
    return values[0], values[1], strategy


def historical_strategy(row: dict[str, Any]) -> str:
    recal = row["historical_recalibration"]
    if recal in {"periodic", "rolling"}:
        return recal
    if row["historical_interval_method"] == "recentred_enbpi_updated":
        return "native_updated"
    return "static"


def _fault_events(windows: dict) -> pd.DataFrame:
    rows = []
    for group, times in windows.items():
        rows.append({"group_id": str(group), "onset": times.min(), "end": times.max(),
                     "effective": bool(len(times))})
    return pd.DataFrame(rows)


def point_accuracy(row: dict[str, Any], test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in ("persistence", "xgboost"):
        path = REPO / row[f"{model}_predictions_path"]
        if digest(path) != row[f"{model}_predictions_sha256"]:
            raise ValueError(f"saved {model} prediction hash mismatch")
        values = pd.read_csv(path)
        if "nominal_level" in values:
            # Point predictions are repeated for each saved split-conformal
            # level. Verify the repetition before selecting the pilot's exact
            # historical level; it is not an additional prediction operation.
            point_column = "point" if "point" in values else "prediction"
            if values.groupby("row_id", sort=False)[point_column].nunique(dropna=False).max() != 1:
                raise ValueError(f"saved {model} point prediction changes across nominal levels")
            values = values[np.isclose(values.nominal_level, float(row["historical_level"]))].reset_index(drop=True)
        if list(values.row_id.astype(str)) != list(test.row_id.astype(str)):
            raise ValueError(f"saved {model} prediction identity mismatch")
        pred_col = "point" if "point" in values else ("prediction" if "prediction" in values else "y_pred")
        pred = values[pred_col].to_numpy(float)
        truth = test.y_true.to_numpy(float)
        rows.append({"model": model, "mae": M.mae(truth, pred), "rmse": M.rmse(truth, pred),
                     "saved_prediction_sha256": row[f"{model}_predictions_sha256"], "fits": 0})
    return pd.DataFrame(rows)


def run_pilot(*, resume: bool = False) -> dict[str, Any]:
    if Path(sys.executable).resolve() != SCIENTIFIC_PYTHON.resolve():
        raise ValueError(f"wrong scientific interpreter: {sys.executable}")
    if not (HERE / "CROSSWALK.csv").exists():
        raise ValueError("crosswalk must be frozen before pilot")
    row = _row_dict("bdg2", 2, 42)
    if (int(row["horizon"]), row["historical_interval_method"], float(row["historical_level"])) != (1, "cqr", .95):
        raise ValueError("authorized pilot key no longer has the declared exact owner")
    if row["interval_owner_support"] != "exact_saved_owner":
        raise ValueError("authorized pilot owner is unsupported")
    initial = resource_gate("launch")
    protocol_hash = digest(HERE / "PROTOCOL.json")
    spec = {
        "version": VERSION, "unit": row["current_unit_id"], "cells": expected_cell_names(False),
        "crosswalk_sha256": digest(HERE / "CROSSWALK.csv"), "protocol_sha256": protocol_hash,
        "owner_sha256": row["interval_owner_sha256"], "fit_budget": 0,
    }
    store = UnitCheckpoint(PILOT_ROOT, spec, resume=resume, string_columns=("group_id", "row_id"))
    key = "bdg2_h1_f2_s42"
    loaded = store.load(key) if resume else None
    if loaded is not None:
        payload, frames = loaded
        if payload["operation_counts"]["model_fits"] != 0 or payload["operation_counts"]["conformalize_calls"] != 0:
            raise ValueError("resume found non-zero-fit pilot")
        return {"status": "complete_zero_fit_resume", "unit": key,
                "payload": payload, "frame_rows": {k: len(v) for k, v in frames.items()}}

    start = time.perf_counter()
    protocol, data, roles, prepared = load_unit(row)
    owner = SavedOwner(row, data, roles)
    test_rows = roles["test"]
    meta = data["meta"].iloc[test_rows].reset_index(drop=True).copy()
    meta["group_id"] = meta.group_id.astype(str)
    test = role_frame(data, test_rows).reset_index(drop=True)
    clean_X = data["X"].iloc[test_rows].reset_index(drop=True)
    truth = np.asarray(data["y"])[test_rows]
    if not np.isfinite(truth).all() or not np.asarray(data["available"])[test_rows].all():
        raise ValueError("pilot test support is not fully observed")
    fcfg = windowing.feature_config(data["old_protocol"]["resolved_dataset_config"], prepared.series[0].covariates)
    scale_map = SI.training_scale(np.asarray(data["y"]), data["meta"], roles["fit"])
    windows = group_test_windows(data["meta"], test_rows, WINDOW_FRAC)
    masks = segment_masks(data["meta"], test_rows)
    groups = meta.group_id.to_numpy(); origins = pd.DatetimeIndex(meta.origin_time); targets = pd.DatetimeIndex(meta.target_time)
    delay = delayed_evidence(meta)
    feature_sets: dict[str, tuple[pd.DataFrame, np.ndarray]] = {"clean": (clean_X, truth.copy())}
    audit_rows = [{"stream": "clean", "feature_sha256": frame_hash(clean_X),
                   "observed_sha256": ordered_hash(map(float.hex, truth)),
                   "changed_feature_rows": 0, "changed_pre_rows": 0}]
    rebuilds = [("zero_control", "level_shift", 0.0)]
    for kind in FAULT_TYPES:
        magnitudes = (1.0, 2.0) if kind in MAGNITUDE_FAULTS else (1.0,)
        for magnitude in magnitudes:
            rebuilds.append((f"{kind}@{magnitude if kind in MAGNITUDE_FAULTS else 'na'}", kind, magnitude))
    clean_values = clean_X.to_numpy()
    for name, kind, magnitude in rebuilds:
        X2, observed = rebuild_fault(prepared, meta, clean_X, windows, scale_map, fcfg,
                                     int(row["horizon"]), kind, magnitude, int(row["model_seed"]))
        feature_sets[name] = (X2, observed)
        changed = np.any(X2.to_numpy() != clean_values, axis=1)
        audit_rows.append({
            "stream": name, "feature_sha256": frame_hash(X2),
            "observed_sha256": ordered_hash(map(float.hex, observed)),
            "changed_feature_rows": int(changed.sum()),
            "changed_pre_rows": int((changed & masks["pre"]).sum()),
        })
        if name == "zero_control":
            np.testing.assert_array_equal(X2.to_numpy(), clean_values)
            np.testing.assert_array_equal(observed, truth)
        elif not changed.any() or (changed & masks["pre"]).any():
            raise ValueError(f"causal feature propagation invariant failed: {name}")
        resource_gate(f"feature_rebuild:{name}")

    raw_bank: dict[str, dict[str, np.ndarray]] = {}
    for name, (features, _) in feature_sets.items():
        raw_bank[name] = owner.raw(features)
        resource_gate(f"saved_owner_inference:{name}")
    selected_strategy = historical_strategy(row)
    streams = []
    cells = []
    recovery_rows = []
    recovery_summaries = []
    contamination_rows = []
    events = _fault_events(windows)
    freq_minutes = data["freq"] / pd.Timedelta(minutes=1)
    tolerance = int(data["old_protocol"]["resolved_dataset_config"].get("alerts", {}).get("detection_tolerance_steps", 6))

    def emit(cell: str, family: str, features_name: str, observed: np.ndarray,
             lower: np.ndarray, upper: np.ndarray, point: np.ndarray,
             *, fault_type="", severity=np.nan, contam=np.nan, strategy=""):
        metric = score_cell(truth, observed, lower, upper, groups, meta, masks,
                            freq_minutes, int(row["rule_k"]), int(row["rule_m"]),
                            float(row["historical_level"]), tolerance)
        metric.update({
            "dataset": "bdg2", "horizon": 1, "outer_fold": 2, "model_seed": 42,
            "family": family, "cell": cell, "fault_type": fault_type,
            "severity_sd": severity, "contamination_rate": contam,
            "recal_policy": strategy, "interval_method": row["historical_interval_method"],
            "nominal_level": float(row["historical_level"]), "owner_sha256": row["interval_owner_sha256"],
            "model_fits": 0, "conformalize_calls": 0,
        })
        cells.append(metric)
        frame = meta[["row_id", "group_id", "origin_time", "target_time"]].copy()
        frame["cell"] = cell; frame["family"] = family; frame["feature_stream"] = features_name
        frame["recal_policy"] = strategy
        frame["y_clean"] = truth; frame["y_observed"] = observed; frame["point"] = point
        frame["lower"] = lower; frame["upper"] = upper
        frame["covered_clean"] = (truth >= lower) & (truth <= upper)
        frame["released_rows"] = delay.released_rows.to_numpy()
        frame["latest_released_target"] = delay.latest_released_target.to_numpy()
        streams.append(frame)

    # Clean, zero, and seven declared fault cells use the historical pipeline policy.
    for cell in ["clean", "zero_control", "random_missing@na", "dropout@na", "stuck@na",
                 "level_shift@1.0", "level_shift@2.0", "drift@1.0", "drift@2.0"]:
        features_name = "clean" if cell == "clean" else cell
        _, observed = feature_sets[features_name]
        raw = raw_bank[features_name]
        lower, upper, applied = issue_bounds(owner, raw, observed, groups, origins, targets, selected_strategy)
        kind = "" if cell == "clean" else ("level_shift" if cell == "zero_control" else cell.split("@")[0])
        severity = 0.0 if cell == "zero_control" else (float(cell.split("@")[1]) if "@" in cell and cell.split("@")[1] != "na" else np.nan)
        emit(cell, "clean" if cell == "clean" else "fault", features_name, observed,
             lower, upper, raw["point"], fault_type=kind, severity=severity, strategy=applied)

    # Calibration-only contamination: preserve the Amendment-003 uniform
    # signed-residual construction. The clean test stream and saved owner stay fixed.
    clean_raw = raw_bank["clean"]
    base_residual = owner.calibration.residual.to_numpy(float)
    pooled_sigma = float(scale_map["__pooled__"])
    for rate, cell in ((0.0, "contam_clean_ref"), (0.05, "contam@0.05"), (0.10, "contam@0.1")):
        residual = base_residual.copy(); selected = np.array([], dtype=int)
        if rate:
            selected = np.random.default_rng(int(row["model_seed"]) + 11).choice(
                len(residual), size=int(round(rate * len(residual))), replace=False
            )
            residual[selected] += 2.0 * pooled_sigma
        alpha = (1.0 - float(row["historical_level"])) / 2.0
        qlo, qhi = np.quantile(residual, alpha), np.quantile(residual, 1.0 - alpha)
        lower, upper = clean_raw["point"] + qlo, clean_raw["point"] + qhi
        emit(cell, "contamination", "clean", truth.copy(), lower, upper, clean_raw["point"],
             contam=rate, strategy="calibration_only_signed_residual")
        for index in selected:
            item = owner.calibration.iloc[int(index)]
            contamination_rows.append({
                "cell": cell, "calibration_index": int(index), "row_id": item.row_id,
                "group_id": item.group_id, "original_target": item.y_true,
                "contaminated_target": item.y_true + 2.0 * pooled_sigma,
                "delta": 2.0 * pooled_sigma, "train_only_pooled_sigma": pooled_sigma,
            })

    # Recovery policies reuse the already-built level-shift@2 stream and raw
    # prediction pass; only the causal recalibration policy differs.
    _, recovery_observed = feature_sets["level_shift@2.0"]
    recovery_raw = raw_bank["level_shift@2.0"]
    for strategy in ("static", "periodic", "rolling"):
        lower, upper, applied = issue_bounds(
            owner, recovery_raw, recovery_observed, groups, origins, targets, strategy
        )
        cell = f"recovery_{strategy}"
        emit(cell, "recovery", "level_shift@2.0", recovery_observed,
             lower, upper, recovery_raw["point"], fault_type="level_shift", severity=2.0,
             strategy=applied)
        current = streams[-1].reset_index(drop=True)
        per_group, summary = group_recovery(current, truth, events, data["freq"])
        per_group.insert(0, "cell", cell); recovery_rows.append(per_group)
        recovery_summaries.append({"cell": cell, **summary})

    cell_frame = pd.DataFrame(cells)
    require_cells(cell_frame, ["cell"], [(name,) for name in expected_cell_names(False)])
    stream_frame = pd.concat(streams, ignore_index=True)
    require_cells(stream_frame[["cell"]].drop_duplicates(), ["cell"],
                  [(name,) for name in expected_cell_names(False)])
    clean_stream = stream_frame[stream_frame.cell == "clean"].reset_index(drop=True)
    zero_stream = stream_frame[stream_frame.cell == "zero_control"].reset_index(drop=True)
    pd.testing.assert_frame_equal(
        clean_stream.drop(columns=["cell", "family", "feature_stream"]),
        zero_stream.drop(columns=["cell", "family", "feature_stream"]),
        check_exact=True,
    )
    points = point_accuracy(row, test)
    final_resource = resource_gate("pre_checkpoint")
    operation_counts = {
        "historical_obligation_cells": 15,
        "unique_corrupted_feature_rebuilds": 8,
        "unique_saved_owner_inference_passes": 9,
        "emitted_cell_streams": 15,
        "contamination_reconstructions": 3,
        "nonzero_contamination_reconstructions": 2,
        "recovery_policy_computations": 3,
        "group_recovery_rows": int(sum(len(x) for x in recovery_rows)),
        "point_metric_rows_from_saved_predictions": 2,
        "model_fits": 0, "conformalize_calls": 0, "new_seeds": 0,
    }
    elapsed = time.perf_counter() - start
    payload = {
        "version": VERSION, "unit": key, "crosswalk_unit": row["current_unit_id"],
        "owner_sha256": row["interval_owner_sha256"], "calibration_sha256": row["calibration_values_sha256"],
        "operation_counts": operation_counts, "wall_seconds": elapsed,
        "resource_launch": initial, "resource_pre_checkpoint": final_resource,
        "scientific_suitability": "exact saved CQR 0.95 owner; historical primary horizon/fold/seed; 10 BDG2 groups; no fits",
        "cell_metrics": cells, "recovery_summaries": recovery_summaries,
    }
    frames = {
        "streams": stream_frame,
        "calibration": owner.calibration,
        "feature_audit": pd.DataFrame(audit_rows),
        "contamination_evidence": pd.DataFrame(contamination_rows),
        "recovery_by_group": pd.concat(recovery_rows, ignore_index=True),
        "point_accuracy": points,
        "cell_metrics": cell_frame,
    }
    store.save(key, payload, frames)
    store.require_complete([key])
    marker = store.verify(key)
    output_bytes = sum(p.stat().st_size for p in PILOT_ROOT.rglob("*") if p.is_file())
    result = {
        "status": "complete", "completed_utc": utc(), "unit": key,
        "cells": 15, "models_fitted": 0, "conformalize_calls": 0,
        "wall_seconds": elapsed, "output_bytes": output_bytes,
        "peak_working_set_bytes": final_resource["peak_working_set_bytes"],
        "peak_pagefile_usage_bytes": final_resource["peak_pagefile_usage_bytes"],
        "checkpoint_complete_sha256": digest(PILOT_ROOT / "units" / key / "COMPLETE.json"),
        "checkpoint_files": marker["hashes"], "operation_counts": operation_counts,
        "recovery_summaries": recovery_summaries,
    }
    atomic_json(HERE / "PILOT_RESULT.json", result)
    return result


def operation_budget() -> dict[str, Any]:
    value = {
        "version": VERSION,
        "scope": {"units": 60, "cells": 900, "clean": 60, "zero_controls": 60,
                  "fault_cells": 420, "contamination_cells": 180, "recovery_cells": 180},
        "unique_operations": {
            "corrupted_feature_rebuilds": 480,
            "saved_owner_inference_passes": 540,
            "emitted_cell_streams": 900,
            "contamination_reconstructions": 180,
            "nonzero_contamination_reconstructions": 120,
            "recovery_policy_computations": 180,
            "point_metric_rows_from_saved_predictions": 120,
            "unit_checkpoint_validations": 60,
            "zero_fit_resume_validations": 60,
        },
        "not_double_counted": {
            "recovery_level_shift_2_reuses_fault_feature_and_prediction_stream": True,
            "contamination_cells_reuse_clean_test_features_and_point_predictions": True,
            "zero_control_is_a_distinct_rebuild_and_evidence stream": True,
        },
        "currently_supported": {"units": 52, "cells": 780, "new_model_fits": 0,
                                "new_conformalizations": 0},
        "missing_owner_construction": {"units": 8, "cells": 120,
                                       "quantile_estimator_fits": 24,
                                       "owner_conformalizations": 8},
        "full_scope_after_owner_authorization": {"new_model_fits": 24,
                                                  "new_conformalizations": 8},
    }
    atomic_json(HERE / "OPERATION_BUDGET.json", value)
    return value


def freeze_protocol() -> dict[str, Any]:
    crosswalk = read(HERE / "CROSSWALK_SUMMARY.json")
    budget = operation_budget()
    protocol = {
        "version": VERSION, "frozen_utc": utc(),
        "authorization_scope": "implementation plus one zero-fit BDG2 h1/f2/s42 pilot",
        "historical_scope": {"units": 60, "cells_per_unit": 15, "cells": 900,
                             "cell_names": expected_cell_names(False)},
        "fault_contract": {
            "types": list(FAULT_TYPES), "magnitude_faults": sorted(MAGNITUDE_FAULTS),
            "severities_sd": [1.0, 2.0], "random_missing_fraction": RANDOM_MISSING_FRACTION,
            "window_fraction": list(WINDOW_FRAC), "segments": SEGMENTS,
            "zero_control": "level_shift@0 through identical rebuild/replay machinery",
            "contamination": "calibration targets only; 5%/10%; +2 train-only pooled sigma; clean test",
            "recovery": "level_shift@2; static/periodic/rolling; group physical follow-up and right censoring",
        },
        "crosswalk": crosswalk, "operation_budget": budget,
        "pilot": {"dataset": "bdg2", "horizon": 1, "outer_fold": 2, "model_seed": 42,
                  "interval_method": "cqr", "level": .95, "new_model_fits": 0,
                  "new_conformalizations": 0, "rss_limit_bytes": PILOT_RSS_LIMIT,
                  "additional_disk_limit_bytes": PILOT_DISK_ALLOWANCE,
                  "disk_floor_bytes": DISK_FLOOR},
        "prohibited_until_separate_authorization": {
            "missing_owner_quantile_estimator_fits": 24,
            "missing_owner_conformalizations": 8,
            "remaining_units": 59,
        },
        "inputs": {
            "amendment003": digest(SMART / "outputs/final_dissertation_v2/protocol/protocol_amendment_003.md"),
            "frozen_protocol": digest(SMART / "outputs/final_dissertation_v2/protocol/frozen_protocol.yaml"),
            "historical_provenance": {d: digest(HISTORICAL / d / "provenance.json") for d in DATASETS},
            "experiment_matrix": digest(MATRIX), "crosswalk": digest(HERE / "CROSSWALK.csv"),
            "adapter": digest(Path(__file__)),
            "independent_validator": digest(HERE / "validate_saved_owner_v1.py"),
            "focused_tests": digest(HERE / "test_saved_owner_v1.py"),
        },
        "operational_replay_dependency": False,
    }
    atomic_json(HERE / "PROTOCOL.json", protocol)
    return protocol


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "run-pilot", "resume-pilot", "resources"])
    args = parser.parse_args()
    if args.action == "prepare":
        print(json.dumps(build_crosswalk(), indent=2)); print(json.dumps(freeze_protocol(), indent=2))
    elif args.action == "run-pilot":
        print(json.dumps(run_pilot(resume=False), indent=2))
    elif args.action == "resume-pilot":
        print(json.dumps(run_pilot(resume=True), indent=2))
    else:
        print(json.dumps(resources(), indent=2))


if __name__ == "__main__":
    main()
