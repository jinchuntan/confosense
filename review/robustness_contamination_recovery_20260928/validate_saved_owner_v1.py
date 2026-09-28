"""Independent validation for the saved-owner Amendment-003 pilot.

The validator does not call the adapter's cell or bound-emission functions. It
reconstructs adaptive bounds with a small scalar implementation, recomputes
cell and group-recovery metrics, and fails closed on altered evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SMART = REPO / "smart_building_conformal"
HERE = Path(__file__).resolve().parent
PILOT = SMART / "outputs" / "robustness_contamination_recovery005" / "pilot_bdg2_h1_f2_s42_v1"
UNIT = "bdg2_h1_f2_s42"
sys.path.insert(0, str(SMART))
sys.path.insert(0, str(HERE))

from src import metrics as M, split_integrity as SI, windowing  # noqa: E402
from src.intervals005_common import load_owner  # noqa: E402
from src.intervals005_data import load_data, role_frame  # noqa: E402
from src.intervals005_owners import raw_predictions  # noqa: E402
from src.robustness_extension import (  # noqa: E402
    FAULT_TYPES, MAGNITUDE_FAULTS, WINDOW_FRAC, apply_fault_to_frame,
    expected_cell_names, group_test_windows, segment_masks,
)
import robustness_saved_owner_v1 as A  # noqa: E402


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def checkpoint_frames() -> tuple[dict[str, Any], dict[str, pd.DataFrame], dict[str, Any]]:
    manifest = json.loads((PILOT / "checkpoint_manifest.json").read_text(encoding="utf-8"))
    unit = PILOT / "units" / UNIT
    complete = json.loads((unit / "COMPLETE.json").read_text(encoding="utf-8"))
    if complete["spec_hash"] != manifest["spec_hash"] or complete["key"] != UNIT:
        raise ValueError("checkpoint identity mismatch")
    for name, expected in complete["hashes"].items():
        if digest(unit / name) != expected:
            raise ValueError(f"checkpoint byte corruption: {name}")
    payload = json.loads((unit / "payload.json").read_text(encoding="utf-8"))
    frames = {}
    for name, filename in complete["frames"].items():
        try:
            frames[name] = pd.read_csv(unit / filename, float_precision="round_trip",
                                       converters={"group_id": str, "row_id": str})
        except pd.errors.EmptyDataError:
            frames[name] = pd.DataFrame()
    return payload, frames, complete


def validate_zero_streams(streams: pd.DataFrame) -> None:
    clean = streams[streams.cell == "clean"].reset_index(drop=True)
    zero = streams[streams.cell == "zero_control"].reset_index(drop=True)
    if len(clean) == 0 or len(clean) != len(zero):
        raise ValueError("zero-control stream missing")
    excluded = {"cell", "family", "feature_stream"}
    columns = [name for name in clean.columns if name not in excluded]
    pd.testing.assert_frame_equal(clean[columns], zero[columns], check_exact=True)


def validate_causal_audit(audit: pd.DataFrame) -> None:
    expected = {"clean", "zero_control", "random_missing@na", "dropout@na", "stuck@na",
                "level_shift@1.0", "level_shift@2.0", "drift@1.0", "drift@2.0"}
    if set(audit.stream) != expected or audit.stream.duplicated().any():
        raise ValueError("feature audit stream matrix mismatch")
    zero = audit.set_index("stream").loc["zero_control"]
    clean = audit.set_index("stream").loc["clean"]
    if (zero.feature_sha256, zero.observed_sha256) != (clean.feature_sha256, clean.observed_sha256):
        raise ValueError("zero-control feature evidence differs")
    if int(zero.changed_feature_rows) != 0:
        raise ValueError("zero-control features changed")
    fault = audit[~audit.stream.isin(["clean", "zero_control"])]
    if (fault.changed_feature_rows.astype(int) <= 0).any():
        raise ValueError("nonzero fault did not propagate into later features")
    if (fault.changed_pre_rows.astype(int) != 0).any():
        raise ValueError("fault changed a pre-window feature row")


def validate_delayed_release(streams: pd.DataFrame) -> None:
    origins = pd.to_datetime(streams.origin_time)
    targets = pd.to_datetime(streams.target_time)
    latest = pd.to_datetime(streams.latest_released_target, errors="coerce")
    if (targets <= origins).any():
        raise ValueError("forecast target does not follow origin")
    if (latest.notna() & (latest > origins)).any():
        raise ValueError("future residual appears in released evidence")
    for (_, group), part in streams.groupby(["cell", "group_id"], sort=False):
        ordered = part.sort_values("target_time", kind="stable")
        independent = np.searchsorted(
            pd.DatetimeIndex(ordered.target_time).asi8,
            pd.DatetimeIndex(ordered.origin_time).asi8,
            side="right",
        )
        np.testing.assert_array_equal(ordered.released_rows.to_numpy(int), independent)


def validate_contamination(evidence: pd.DataFrame, calibration: pd.DataFrame,
                           streams: pd.DataFrame, sigma: float, seed: int = 42) -> None:
    test_ids = set(streams.row_id.astype(str))
    cal_ids = list(calibration.row_id.astype(str))
    if set(evidence.row_id.astype(str)) & test_ids:
        raise ValueError("contamination evidence touches a test identity")
    if not set(evidence.row_id.astype(str)).issubset(set(cal_ids)):
        raise ValueError("contamination evidence contains a non-calibration identity")
    for rate, cell in ((.05, "contam@0.05"), (.10, "contam@0.1")):
        part = evidence[evidence.cell == cell]
        expected = np.random.default_rng(seed + 11).choice(
            len(calibration), size=int(round(rate * len(calibration))), replace=False
        )
        if set(part.calibration_index.astype(int)) != set(map(int, expected)):
            raise ValueError(f"contamination identity selection mismatch: {cell}")
        if part.row_id.duplicated().any() or len(part) != len(expected):
            raise ValueError(f"contamination count/uniqueness mismatch: {cell}")
        np.testing.assert_allclose(part.delta, 2.0 * sigma, rtol=0, atol=0)
        np.testing.assert_allclose(part.contaminated_target - part.original_target,
                                   2.0 * sigma, rtol=0, atol=1e-12)
    contamination_streams = streams[streams.family == "contamination"]
    for _, part in contamination_streams.groupby("cell"):
        np.testing.assert_allclose(part.y_observed, part.y_clean, rtol=0, atol=0)


def _quantiles(values: np.ndarray, level: float) -> tuple[float, float]:
    alpha = 1.0 - level
    finite = np.asarray(values, float); finite = finite[np.isfinite(finite)]
    return float(np.quantile(finite, alpha / 2.0)), float(np.quantile(finite, 1.0 - alpha / 2.0))


def independent_adaptive_bounds(stream: pd.DataFrame, calibration: pd.DataFrame,
                                level: float, strategy: str) -> tuple[np.ndarray, np.ndarray]:
    """Scalar reconstruction independent of interval_stream.recalibrated_bounds."""
    frame = stream.reset_index(drop=True)
    lower = np.empty(len(frame)); upper = np.empty(len(frame))
    for group, part in frame.groupby("group_id", sort=False):
        rows = part.index.to_numpy()
        order = np.argsort(pd.DatetimeIndex(part.target_time).asi8, kind="stable")
        rows = rows[order]
        local_cal = calibration[calibration.group_id.astype(str) == str(group)].copy()
        if local_cal.empty:
            local_cal = calibration.copy()
        local_cal = local_cal.sort_values("target_time", kind="stable")
        base = local_cal.residual.to_numpy(float)
        qlo, qhi = _quantiles(base, level)
        test_residual = frame.y_observed.to_numpy(float)[rows] - frame.point.to_numpy(float)[rows]
        targets = pd.DatetimeIndex(frame.target_time.iloc[rows]).asi8
        origins = pd.DatetimeIndex(frame.origin_time.iloc[rows]).asi8
        frontier = np.searchsorted(targets, origins, side="right")
        if strategy == "native_updated":
            actual, every, window, minimum = "periodic", 1, None, 1
        else:
            actual, every, window, minimum = strategy, 48, 250, 30
        for ordinal, row_index in enumerate(rows):
            if actual != "static" and ordinal % every == 0:
                pool = np.concatenate([base, test_residual[:frontier[ordinal]]])
                pool = pool[np.isfinite(pool)]
                if actual == "rolling" and len(pool) > window:
                    pool = pool[-window:]
                if len(pool) >= minimum:
                    qlo, qhi = _quantiles(pool, level)
            lower[row_index] = frame.point.iloc[row_index] + qlo
            upper[row_index] = frame.point.iloc[row_index] + qhi
    return lower, upper


def _bundle_data(row: dict[str, Any]):
    protocol_path = REPO / row["interval_bundle"].replace("outputs", "protocols", 1) / "frozen_protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    data, roles, prepared = A.load_matched_data(
        protocol["references"][str(int(row["horizon"]))], None
    )
    return data, roles, prepared[0]


def _rebuild_recovery_features(row: dict[str, Any], data, roles, prepared):
    test_rows = roles["test"]
    meta = data["meta"].iloc[test_rows].reset_index(drop=True)
    clean = data["X"].iloc[test_rows].reset_index(drop=True)
    fcfg = windowing.feature_config(data["old_protocol"]["resolved_dataset_config"], prepared.series[0].covariates)
    scales = SI.training_scale(np.asarray(data["y"]), data["meta"], roles["fit"])
    windows = group_test_windows(data["meta"], test_rows, WINDOW_FRAC)
    series = []
    for item in prepared.series:
        window = next(value for key, value in windows.items() if str(key) == str(item.group_id))
        magnitude = 2.0 * float(scales.get(item.group_id, scales["__pooled__"]))
        series.append(replace(item, frame=apply_fault_to_frame(
            item.frame, window, "level_shift", magnitude, int(row["model_seed"]) + 7
        )))
    built = windowing.build_dataset_windows(replace(prepared, series=series), 1, fcfg)
    lookup = built["meta"][["group_id", "origin_time"]].copy(); lookup["row"] = np.arange(len(lookup))
    selected = meta[["group_id", "origin_time"]].merge(
        lookup, on=["group_id", "origin_time"], how="left", validate="one_to_one"
    )
    X = built["X"].iloc[selected.row.to_numpy(int)].reset_index(drop=True)
    if list(X.columns) != list(clean.columns):
        raise ValueError("validator recovery feature schema mismatch")
    return X


def validate_bounds(frames: dict[str, pd.DataFrame], row: dict[str, Any]) -> None:
    streams, calibration = frames["streams"], frames["calibration"]
    for cell, part in streams.groupby("cell", sort=False):
        part = part.reset_index(drop=True)
        if part.family.iloc[0] == "contamination":
            residual = calibration.residual.to_numpy(float).copy()
            rate = {"contam_clean_ref": 0.0, "contam@0.05": .05, "contam@0.1": .10}[cell]
            if rate:
                selected = np.random.default_rng(53).choice(
                    len(residual), size=int(round(rate * len(residual))), replace=False
                )
                sigma = float(frames["contamination_evidence"].train_only_pooled_sigma.iloc[0])
                residual[selected] += 2.0 * sigma
            qlo, qhi = _quantiles(residual, .95)
            expected_lo, expected_hi = part.point.to_numpy() + qlo, part.point.to_numpy() + qhi
        elif part.recal_policy.iloc[0] in {"periodic", "rolling", "native_updated"}:
            expected_lo, expected_hi = independent_adaptive_bounds(
                part, calibration, .95, part.recal_policy.iloc[0]
            )
        elif cell == "recovery_static":
            data, roles, prepared = _bundle_data(row)
            X = _rebuild_recovery_features(row, data, roles, prepared)
            owner = load_owner(REPO / row["interval_owner_path"])
            raw = raw_predictions(owner, "cqr", X.to_numpy(), [.95])[.95]
            expected_lo, expected_hi = raw.static_lower.to_numpy(), raw.static_upper.to_numpy()
        else:
            raise ValueError(f"validator has no bound reconstruction for {cell}")
        np.testing.assert_allclose(part.lower, expected_lo, rtol=1e-12, atol=1e-10)
        np.testing.assert_allclose(part.upper, expected_hi, rtol=1e-12, atol=1e-10)


def validate_cell_metrics(frames: dict[str, pd.DataFrame]) -> None:
    streams = frames["streams"]
    metrics = frames["cell_metrics"].set_index("cell")
    if set(metrics.index) != set(expected_cell_names(False)) or len(metrics) != 15:
        raise ValueError("pilot cell matrix mismatch")
    for cell, part in streams.groupby("cell", sort=False):
        part = part.reset_index(drop=True); expected = metrics.loc[cell]
        cover = ((part.y_clean >= part.lower) & (part.y_clean <= part.upper)).to_numpy()
        n = len(part); position = np.zeros(n, dtype=float)
        for _, group in part.groupby("group_id", sort=False):
            rows = group.index.to_numpy(); order = np.argsort(pd.DatetimeIndex(group.target_time).asi8, kind="stable")
            rank = np.empty(len(rows)); rank[order] = np.arange(len(rows)) / max(1, len(rows)); position[rows] = rank
        masks = {"pre": position < .25, "during": (position >= .25) & (position < .55), "post": position >= .55}
        values = {
            "coverage_all": float(cover.mean()),
            "coverage_pre": float(cover[masks["pre"]].mean()),
            "coverage_during": float(cover[masks["during"]].mean()),
            "coverage_post": float(cover[masks["post"]].mean()),
            "mean_width": float((part.upper - part.lower).mean()),
            "median_width": float((part.upper - part.lower).median()),
            "winkler": float(M.winkler_score(part.y_clean.to_numpy(), part.lower.to_numpy(),
                                               part.upper.to_numpy(), .05)),
        }
        for name, value in values.items():
            if not math.isclose(float(expected[name]), value, rel_tol=1e-12, abs_tol=1e-10):
                raise ValueError(f"metric mismatch {cell}/{name}: {expected[name]} != {value}")


def independent_recovery(stream: pd.DataFrame, truth: np.ndarray,
                         windows: dict[str, pd.DatetimeIndex], freq: pd.Timedelta):
    rows = []
    for group, part in stream.groupby("group_id", sort=True):
        times = pd.to_datetime(part.target_time)
        window_times = windows[str(group)]
        onset, end = window_times.min(), window_times.max()
        pre = (times < onset).to_numpy(); post = (times > end).to_numpy()
        idx = part.index.to_numpy()
        cover = (truth[idx] >= part.lower.to_numpy()) & (truth[idx] <= part.upper.to_numpy())
        post_rows = np.flatnonzero(post)
        if not pre.any() or not len(post_rows):
            rows.append({"group_id": group, "status": "insufficient_recovery_support",
                         "recovery_minutes": np.nan, "recovery_censored": True,
                         "followup_minutes": 0.0})
            continue
        baseline = float(cover[pre].mean())
        window = max(1, min(int(pd.Timedelta(days=1) / freq), len(post_rows) // 4))
        rolling = pd.Series(cover[post].astype(float)).rolling(window, min_periods=window).mean().to_numpy()
        success = np.flatnonzero(np.abs(rolling - baseline) <= .05)
        at = float((times.iloc[post_rows[success[0]]] - end) / pd.Timedelta(minutes=1)) if len(success) else np.nan
        rows.append({"group_id": group, "status": "observed" if len(success) else "right_censored",
                     "pre_coverage": baseline, "window_steps": window,
                     "recovery_minutes": at, "recovery_censored": not len(success),
                     "followup_minutes": float((times.iloc[post_rows[-1]] - end) / pd.Timedelta(minutes=1))})
    result = pd.DataFrame(rows)
    valid = result[result.status != "insufficient_recovery_support"]
    if valid.empty:
        return result, {"status": "insufficient_recovery_support"}
    tau = float(valid.followup_minutes.min())
    waits = np.where(valid.recovery_censored, np.inf, valid.recovery_minutes)
    median = float(np.sort(waits)[math.ceil(len(waits) / 2) - 1])
    return result, {
        "status": "descriptive_group_recovery", "groups": len(valid),
        "common_horizon_minutes": tau, "probability_recovered_by_horizon": float(np.mean(waits <= tau)),
        "restricted_mean_recovery_minutes": float(np.minimum(waits, tau).mean()),
        "median_recovery_minutes": median if np.isfinite(median) else None,
        "censored_groups": int(valid.recovery_censored.sum()),
    }


def validate_recovery(frames: dict[str, pd.DataFrame], payload: dict[str, Any]) -> None:
    streams = frames["streams"]
    clean = streams[streams.cell == "clean"].reset_index(drop=True)
    truth = clean.y_clean.to_numpy(float)
    windows = {}
    for group, part in clean.groupby("group_id", sort=False):
        times = pd.DatetimeIndex(part.target_time).sort_values(); n = len(times)
        windows[str(group)] = times[int(np.floor(.25 * n)):int(np.floor(.55 * n))]
    saved_groups = frames["recovery_by_group"]
    saved_summary = {r["cell"]: r for r in payload["recovery_summaries"]}
    for cell in ("recovery_static", "recovery_periodic", "recovery_rolling"):
        part = streams[streams.cell == cell].reset_index(drop=True)
        groups, summary = independent_recovery(part, truth, windows, pd.Timedelta(hours=1))
        saved = saved_groups[saved_groups.cell == cell].drop(columns="cell").reset_index(drop=True)
        pd.testing.assert_frame_equal(saved[groups.columns], groups, check_exact=False,
                                      rtol=1e-12, atol=1e-10, check_dtype=False)
        for name, value in summary.items():
            observed = saved_summary[cell].get(name)
            if value is None:
                if observed is not None:
                    raise ValueError(f"recovery unavailable metric changed {cell}/{name}")
            elif isinstance(value, (float, int)):
                if not math.isclose(float(observed), float(value), rel_tol=1e-12, abs_tol=1e-10):
                    raise ValueError(f"recovery summary mismatch {cell}/{name}")
            elif observed != value:
                raise ValueError(f"recovery status mismatch {cell}/{name}")


def validate_operations(payload: dict[str, Any]) -> None:
    expected = {
        "historical_obligation_cells": 15,
        "unique_corrupted_feature_rebuilds": 8,
        "unique_saved_owner_inference_passes": 9,
        "emitted_cell_streams": 15,
        "contamination_reconstructions": 3,
        "nonzero_contamination_reconstructions": 2,
        "recovery_policy_computations": 3,
        "point_metric_rows_from_saved_predictions": 2,
        "model_fits": 0, "conformalize_calls": 0, "new_seeds": 0,
    }
    actual = payload["operation_counts"]
    for name, value in expected.items():
        if int(actual.get(name, -1)) != value:
            raise ValueError(f"operation-accounting mismatch: {name}")
    if int(actual["group_recovery_rows"]) != 30:
        raise ValueError("expected three policies x ten BDG2 groups")


def run() -> dict[str, Any]:
    protocol = json.loads((HERE / "PROTOCOL.json").read_text(encoding="utf-8"))
    if digest(HERE / "robustness_saved_owner_v1.py") != protocol["inputs"]["adapter"]:
        raise ValueError("frozen adapter changed after pilot protocol")
    payload, frames, complete = checkpoint_frames()
    crosswalk = pd.read_csv(HERE / "CROSSWALK.csv", keep_default_na=False)
    hit = crosswalk[(crosswalk.dataset == "bdg2") & (crosswalk.outer_fold == 2) & (crosswalk.model_seed == 42)]
    if len(hit) != 1:
        raise ValueError("pilot crosswalk row missing")
    row = hit.iloc[0].to_dict()
    validate_zero_streams(frames["streams"])
    validate_causal_audit(frames["feature_audit"])
    validate_delayed_release(frames["streams"])
    sigma = float(frames["contamination_evidence"].train_only_pooled_sigma.iloc[0])
    validate_contamination(frames["contamination_evidence"], frames["calibration"],
                           frames["streams"], sigma)
    validate_bounds(frames, row)
    validate_cell_metrics(frames)
    validate_recovery(frames, payload)
    validate_operations(payload)
    if frames["point_accuracy"].fits.astype(int).sum() != 0 or len(frames["point_accuracy"]) != 2:
        raise ValueError("point evidence did not remain zero-fit")
    result = {
        "status": "passed", "validated_utc": A.utc(), "unit": UNIT,
        "validated_cells": 15, "validated_stream_rows": len(frames["streams"]),
        "zero_control_exact": True, "calibration_only_contamination": True,
        "causal_feature_propagation": True, "delayed_residual_availability": True,
        "group_recovery_and_censoring": True, "operation_accounting": True,
        "models_fitted": 0, "conformalize_calls": 0,
        "checkpoint_complete_sha256": digest(PILOT / "units" / UNIT / "COMPLETE.json"),
        "checkpoint_files": complete["hashes"],
        "recovery_summaries": payload["recovery_summaries"],
    }
    A.atomic_json(HERE / "PILOT_VALIDATION.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=["validate"])
    parser.parse_args(); print(json.dumps(run(), indent=2))
