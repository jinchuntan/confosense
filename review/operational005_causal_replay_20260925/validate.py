"""Independent zero-fit validator for one saved operational policy block."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from common import CONFIG, REPO, SOURCE_HASH, UNITS, atomic_json, digest, read, verify_protocol

sys.path.insert(0, str(REPO / "smart_building_conformal"))
from src.intervals005_common import source_digest


def contiguous_parts(frame: pd.DataFrame):
    for group, part in frame.groupby("group_id", sort=True):
        part = part.sort_values("target_time", kind="stable")
        indices = part.index.to_numpy()
        times = pd.DatetimeIndex(part.target_time)
        cuts = np.r_[0, np.flatnonzero(np.diff(times.asi8) != pd.Timedelta("1h").value) + 1, len(part)]
        for a, b in zip(cuts, cuts[1:]):
            if a < b:
                yield str(group), indices[a:b]


def alerts(frame: pd.DataFrame, k: int, m: int) -> tuple[np.ndarray, list[dict]]:
    violation = (~frame.available.to_numpy(bool)) | frame.numerical_violation.to_numpy(bool)
    flags = np.zeros(len(frame), bool)
    episodes = []
    for group, indices in contiguous_parts(frame):
        values = violation[indices]
        cumulative = np.r_[0, np.cumsum(values)]
        counts = cumulative[1:] - cumulative[np.maximum(0, np.arange(len(indices)) + 1 - m)]
        active = counts >= k
        flags[indices] = active
        starts = np.flatnonzero(active & ~np.r_[False, active[:-1]])
        ends = np.flatnonzero(active & ~np.r_[active[1:], False])
        for start, end in zip(starts, ends):
            a, b = int(indices[start]), int(indices[end])
            episodes.append({"group_id": group, "onset": pd.Timestamp(frame.iloc[a].target_time),
                             "end": pd.Timestamp(frame.iloc[b].target_time), "used": False})
    return flags, episodes


def score(frame: pd.DataFrame, events: pd.DataFrame, k: int, m: int) -> dict:
    flags, episodes = alerts(frame, k, m)
    segment_end = {}
    for group, indices in contiguous_parts(frame):
        for index in indices:
            segment_end[(group, pd.Timestamp(frame.iloc[index].target_time))] = pd.Timestamp(frame.iloc[indices[-1]].target_time)
    waits = []
    detected = 0
    eligible = 0
    for event in events[events.effective.astype(bool)].sort_values(["group_id", "onset", "event_id"], kind="stable").to_dict("records"):
        onset = pd.Timestamp(event["onset"]); tolerance = pd.Timestamp(event["tolerance_end"])
        end = segment_end.get((str(event["group_id"]), onset))
        if end is None or tolerance > end:
            continue
        eligible += 1
        found = None
        for episode in episodes:
            if not episode["used"] and episode["group_id"] == str(event["group_id"]) and onset <= episode["onset"] <= tolerance:
                found = episode; episode["used"] = True; break
        followup = float((tolerance - onset) / pd.Timedelta(minutes=1))
        if found is not None:
            detected += 1
            waits.append(float((found["onset"] - onset) / pd.Timedelta(minutes=1)))
        else:
            waits.append(followup)
    return {"n_events": eligible, "n_detected": detected,
            "restricted_mean_detection_minutes": float(np.mean(waits)) if waits else np.nan,
            "restricted_wait_sum_minutes": float(np.sum(waits)),
            "episode_count": len(episodes), "time_in_alert_fraction": float(flags.mean())}


def validate_block(fold: int, seed: int, block_index: int) -> dict:
    verify_protocol()
    if source_digest() != SOURCE_HASH:
        raise ValueError("scientific source digest changed")
    stage = UNITS / f"bdg2_f{fold}_s{seed}" / "blocks" / f"block_{block_index:03d}"
    marker = read(stage / "COMPLETE.json")
    for name, expected in marker["files"].items():
        if digest(stage / name) != expected:
            raise ValueError(f"block artifact hash mismatch: {name}")
    identity = read(stage / "identity.json")
    if identity["models_fitted"] != 0 or identity["scientific_source_hash"] != SOURCE_HASH:
        raise ValueError("block source/fit identity mismatch")
    numeric_names = ("observed", "lower", "upper")
    exact_columns = {name: "string" for name in numeric_names}
    exact_columns.update({name + "_hex": "string" for name in numeric_names})
    streams = pd.read_csv(
        stage / "policy_streams.csv.gz", low_memory=False,
        dtype=exact_columns, keep_default_na=False,
    )
    for name in numeric_names:
        streams[name] = np.asarray(
            [float(value) if value else np.nan for value in streams[name]], dtype=np.float64
        )
    metrics = pd.read_csv(stage / "metrics.csv")
    catalogues = pd.read_csv(stage / "catalogues.csv.gz")
    expected_ids = {"clean", "42", "43", "44", "45", "46"}
    streams["stream_id"] = streams.stream_id.astype(str)
    if set(streams.stream_id) != expected_ids:
        raise ValueError("policy stream inventory mismatch")
    clean = streams[streams.stream_id == "clean"].reset_index(drop=True)
    if identity.get("numeric_evidence") != "decimal_roundtrip_plus_ieee754_hex_v2":
        raise ValueError("missing exact numeric evidence contract")
    for stream_id, part in streams.groupby("stream_id"):
        part = part.reset_index(drop=True)
        if list(part.row_id.astype(str)) != list(clean.row_id.astype(str)):
            raise ValueError("mutated replay row identity")
        if (pd.to_datetime(part.target_time) <= pd.to_datetime(part.origin_time)).any():
            raise ValueError("invalid target/origin time")
        released = pd.to_datetime(part.latest_released_target, errors="coerce")
        if (released.notna() & (released > pd.to_datetime(part.origin_time))).any():
            raise ValueError("future residual leakage")
        exact = {}
        for name in numeric_names:
            exact[name] = np.asarray([float.fromhex(value) for value in part[name + "_hex"]], dtype=np.float64)
            decimal = part[name].to_numpy(np.float64)
            same_bits = decimal.view(np.uint64) == exact[name].view(np.uint64)
            same_nan = np.isnan(decimal) & np.isnan(exact[name])
            if not np.all(same_bits | same_nan):
                raise ValueError(f"lossy or tampered exact numeric evidence: {name}")
        if (exact["lower"] > exact["upper"]).any() or not np.isfinite(
                np.column_stack((part.point.to_numpy(float), exact["lower"], exact["upper"]))).all():
            raise ValueError("corrupted bound")
        numerical = part.available.to_numpy(bool) & (
            (exact["observed"] < exact["lower"]) | (exact["observed"] > exact["upper"])
        )
        if not np.array_equal(numerical, part.numerical_violation.astype(bool).to_numpy()):
            raise ValueError("tampered numerical alert record")
        if not np.array_equal((~part.available.astype(bool)).to_numpy(), part.availability_violation.astype(bool).to_numpy()):
            raise ValueError("tampered availability alert record")
    config = read(CONFIG)
    candidate_map = {row["candidate_id"]: row for row in next(x for x in config["resolved_datasets"] if x["dataset"] == "bdg2")["candidates"]}
    common_ids = set(pd.read_csv(REPO / identity["owner"]["common_support"]).row_id.astype(str))
    checks = 0; maximum = 0.
    for saved in metrics.to_dict("records"):
        candidate = candidate_map[saved["candidate_id"]]
        ids = None if saved["support"] == "native" else common_ids
        clean_view = clean if ids is None else clean[clean.row_id.astype(str).isin(ids)].reset_index(drop=True)
        _, clean_episodes = alerts(clean_view, int(candidate["k"]), int(candidate["m"]))
        exposure = len(clean_view) / 24
        workload = len(clean_episodes) / exposure
        all_events = 0; all_detected = 0; wait_sum = 0.
        for catalogue_seed in range(42, 47):
            part = streams[streams.stream_id == str(catalogue_seed)].reset_index(drop=True)
            if ids is not None:
                part = part[part.row_id.astype(str).isin(ids)].reset_index(drop=True)
            events = catalogues[catalogues.catalogue_seed == catalogue_seed]
            result = score(part, events, int(candidate["k"]), int(candidate["m"]))
            all_events += result["n_events"]; all_detected += result["n_detected"]
            wait_sum += result["restricted_wait_sum_minutes"]
        reconstructed = {
            "background_episodes_per_asset_day": workload,
            "n_events": all_events,
            "n_detected": all_detected,
            "event_recall_micro": all_detected / all_events if all_events else np.nan,
            "restricted_mean_detection_minutes": wait_sum / all_events if all_events else np.nan,
            "support_rows": len(clean_view),
            "available_rows": int(clean_view.available.sum()),
            "unavailable_rows": int((~clean_view.available.astype(bool)).sum()),
        }
        for name, value in reconstructed.items():
            difference = abs(float(saved[name]) - float(value)); maximum = max(maximum, difference)
            if difference > 1e-10:
                raise ValueError(f"independent metric mismatch: {name} {difference}")
        checks += 3
    result = {"passed": True, "fold": fold, "model_seed": seed, "block_index": block_index,
              "metric_rows": len(metrics), "checks": checks, "maximum_absolute_difference": maximum,
              "models_fitted": 0, "source_hash": source_digest()}
    out = UNITS / f"bdg2_f{fold}_s{seed}" / "validation" / f"block_{block_index:03d}.json"
    atomic_json(out, result)
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["validate-block"])
    parser.add_argument("--fold", type=int, required=True)
    parser.add_argument("--model-seed", type=int, required=True)
    parser.add_argument("--block-index", type=int, required=True)
    args = parser.parse_args()
    validate_block(args.fold, args.model_seed, args.block_index)
