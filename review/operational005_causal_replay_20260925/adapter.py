"""Saved-owner causal fault replay for one checkpointed operational policy block.

The adapter imports the frozen amendment-004 event, replay and metric contracts,
but never calls a fitting or conformalization method.  Every model object is
restored from a completed, hash-verified interval bundle.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from common import (
    CONFIG, HERE, OUTPUTS, REPO, SOURCE_HASH, UNITS, VERSION, atomic_json,
    bundle_paths, csv_write, digest, owner_reference, read, signature, verify_protocol,
)

sys.path.insert(0, str(REPO / "smart_building_conformal"))
from src import split_integrity as SI, windowing
from src.intervals005_common import load_owner, source_digest
from src.intervals005_data import load_data, role_frame
from src.intervals005_owners import raw_predictions
from src.operational004_design import DESIGN, segments
from src.operational004_events import bank_support, catalogue
from src.operational004_metrics import (
    alert_on_stream, contributions, family_attribution, group_workload,
    pool_bank, summarize_bank,
)
from src.operational004_stream import corrupted_features, replay, stream_hash


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_ledger(path: Path, **record) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps({"utc": utc(), **record}, default=str, separators=(",", ":")) + "\n")


def frame(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, **kwargs)


class SavedOwner:
    fitted_models = 0

    def __init__(self, fold: int, seed: int, method: str, level: float, data, roles):
        reference = owner_reference(fold, seed, method, level)
        if not reference["available"]:
            raise ValueError(reference["reason"])
        self.method = method
        self.owner_kind = reference["owner_kind"]
        self.level = float(level)
        self.columns = list(data["X"].columns)
        self.reference = reference
        owner_path = REPO / reference["owner"]["path"]
        if digest(owner_path) != reference["owner"]["sha256"]:
            raise ValueError("saved owner hash mismatch")
        self.m = load_owner(owner_path)
        metadata = frame(REPO / reference["calibration_metadata"]["path"])
        values = frame(REPO / reference["calibration_values"]["path"])
        expected = role_frame(data, roles["calibration"])
        if list(metadata.row_id.astype(str)) != list(expected.row_id.astype(str)):
            raise ValueError("saved calibration row identity mismatch")
        np.testing.assert_allclose(metadata.y_true, expected.y_true, rtol=0, atol=1e-12)
        if len(values) != len(metadata):
            raise ValueError("saved calibration prediction length mismatch")
        score = (
            np.maximum(values.raw_lower.to_numpy() - metadata.y_true.to_numpy(),
                       metadata.y_true.to_numpy() - values.raw_upper.to_numpy())
            if self.owner_kind == "cqr"
            else metadata.y_true.to_numpy() - values.point.to_numpy()
        )
        if not np.isfinite(score).all():
            raise ValueError("saved operational calibration score is nonfinite")
        self.calibration = metadata[["group_id", "target_time"]].copy()
        self.calibration["group_id"] = self.calibration.group_id.astype(str)
        self.calibration["score"] = score
        self.fit_identity = signature({
            "owner_sha256": reference["owner"]["sha256"],
            "calibration_sha256": reference["calibration_values"]["sha256"],
            "method": method,
            "level": level,
            "columns": self.columns,
        })
        self.identity = {
            "estimator_class": type(self.m).__module__ + "." + type(self.m).__name__,
            "method": method,
            "level": level,
            "restored_owner_sha256": reference["owner"]["sha256"],
            "calibration_sha256": reference["calibration_values"]["sha256"],
            "fitted_models": 0,
        }

    def raw(self, X: pd.DataFrame) -> dict[str, np.ndarray]:
        if list(X.columns) != self.columns:
            raise ValueError("prediction feature schema mismatch")
        output = raw_predictions(self.m, self.owner_kind, X.to_numpy(), [self.level])[self.level]
        return {name: output[name].to_numpy(float) for name in
                ("point", "raw_lower", "raw_upper", "static_lower", "static_upper")}


def candidates() -> list[dict]:
    config = read(CONFIG)
    rows = next(item for item in config["resolved_datasets"] if item["dataset"] == "bdg2")["candidates"]
    if len(rows) != 264:
        raise ValueError("candidate authority changed")
    return rows


def policy_blocks() -> list[list[dict]]:
    groups: dict[tuple, list[dict]] = {}
    for candidate in candidates():
        owner = owner_reference(0, 42, candidate["method"], float(candidate["level"]))
        if not owner["available"]:
            continue
        key = tuple(candidate[name] for name in ("method", "level", "strategy", "every", "window"))
        groups.setdefault(key, []).append(candidate)
    blocks = [sorted(rows, key=lambda item: item["candidate_id"]) for _, rows in sorted(groups.items(), key=lambda item: str(item[0]))]
    if len(blocks) != 55 or sum(map(len, blocks)) != 165 or any(len(rows) != 3 for rows in blocks):
        raise ValueError("ready policy block matrix changed")
    return blocks


def load_unit(fold: int, seed: int):
    protocol_dir, _ = bundle_paths(fold, seed)
    protocol_path = protocol_dir / "frozen_protocol.json"
    protocol = read(protocol_path)
    if protocol["scope"] != {
        "dataset": "bdg2", "outer_fold": fold, "model_seed": seed,
        "horizons": [1, 3, 6], "levels": [0.9, 0.95],
        "methods": ["quantile_uncalibrated", "cqr", "recentred_enbpi_static", "recentred_enbpi_updated", "dscp"],
    }:
        raise ValueError("completed interval scope mismatch")
    data, roles, prepared = load_data(protocol["references"]["1"], None)
    if source_digest() != SOURCE_HASH:
        raise ValueError("frozen scientific source digest changed")
    test = role_frame(data, roles["test"])
    completed = frame(REPO / protocol["references"]["1"]["owner_directory"] / "predictions.csv.gz")
    if "nominal_level" in completed:
        completed = completed[completed.nominal_level == 0.9]
    if list(test.row_id.astype(str)) != list(completed.row_id.astype(str)):
        raise ValueError("completed forecasting test identity mismatch")
    return protocol, data, roles, prepared[0]


def replay_inputs(fold: int, seed: int, data, roles, prepared):
    test_rows = roles["test"]
    meta = data["meta"].iloc[test_rows].reset_index(drop=True).copy()
    meta["group_id"] = meta.group_id.astype(str)
    y = np.asarray(data["y"])[test_rows]
    clean_x = data["X"].iloc[test_rows].reset_index(drop=True)
    if not np.isfinite(y).all() or not data["available"][test_rows].all():
        raise ValueError("BDG2 operational target support unexpectedly unavailable")
    cfg = data["old_protocol"]["resolved_dataset_config"]
    fcfg = windowing.feature_config(cfg, prepared.series[0].covariates)
    scales = SI.training_scale(np.asarray(data["y"]), data["meta"], roles["fit"])
    clean_rebuilt = corrupted_features(prepared, meta, y, np.ones(len(y), bool), 1, fcfg, list(clean_x.columns))
    np.testing.assert_allclose(clean_rebuilt, clean_x, rtol=0, atol=0)
    observed = {"clean": y}
    available = {"clean": np.ones(len(y), bool)}
    catalogues = {}
    allocations = {}
    feature_sets = {"clean": clean_x}
    for catalogue_seed in DESIGN["catalogue_seeds"]:
        obs, flags, events, allocation = catalogue(y, meta, data["freq"], scales, "bdg2", "outer_test", fold, catalogue_seed)
        observed[catalogue_seed] = obs
        available[catalogue_seed] = flags
        catalogues[catalogue_seed] = events
        allocations[catalogue_seed] = allocation
        feature_sets[catalogue_seed] = corrupted_features(
            prepared, meta, obs, flags, 1, fcfg, list(clean_x.columns)
        )
    if not bank_support(list(catalogues.values())).support.all():
        raise ValueError("frozen outer-test catalogue lacks required stratum support")
    return meta, y, feature_sets, observed, available, catalogues, allocations


def event_view(events: pd.DataFrame, stream: pd.DataFrame, freq) -> pd.DataFrame:
    """Map one native catalogue into a reporting-only common-support view."""
    keys = {(str(row.group_id), str(pd.Timestamp(row.target_time))): i
            for i, row in stream.reset_index(drop=True).iterrows()}
    segment_at = {}
    for _, sid, rows in segments(stream.reset_index(drop=True), freq):
        for index in rows:
            segment_at[int(index)] = sid
    rows = []
    for event in events.to_dict("records"):
        start = keys.get((str(event["group_id"]), str(pd.Timestamp(event["onset"]))))
        end = keys.get((str(event["group_id"]), str(pd.Timestamp(event["end"]))))
        if start is None or end is None:
            continue
        item = dict(event)
        item.update(start_index=start, end_index=end, segment_id=segment_at[start])
        rows.append(item)
    return pd.DataFrame(rows, columns=events.columns)


def subset_replay(result: dict, row_ids: set[str]) -> dict:
    stream = result["stream"]
    stream = stream[stream.row_id.astype(str).isin(row_ids)].reset_index(drop=True)
    return {"stream": stream, "emitted_hash": stream_hash(stream)}


def metrics_for_view(candidate, clean_result, corrupt_results, catalogues, freq, support, row_ids=None):
    clean_replay = subset_replay(clean_result, row_ids) if row_ids is not None else clean_result
    clean = alert_on_stream(clean_replay, candidate, pd.DataFrame(), freq)
    bank_parts, per_events, saved_events = [], [], []
    for catalogue_seed in DESIGN["catalogue_seeds"]:
        source = corrupt_results[catalogue_seed]
        current = subset_replay(source, row_ids) if row_ids is not None else source
        events = event_view(catalogues[catalogue_seed], current["stream"], freq) if row_ids is not None else catalogues[catalogue_seed]
        corrupt = alert_on_stream(current, candidate, events, freq)
        bank_parts.append(contributions(clean, corrupt, events, freq))
        event_rows = corrupt["per_event"].copy()
        event_rows["catalogue_seed"] = catalogue_seed
        event_rows["support"] = support
        saved_events.append(event_rows)
        per_events.append(corrupt["per_event"])
    bank = pool_bank(bank_parts)
    summary = summarize_bank(bank, per_events)
    groups, portfolio = group_workload(bank, freq)
    summary.update(portfolio)
    summary.update(
        support=support,
        support_rows=len(clean["stream"]),
        available_rows=int(clean["stream"].available.sum()),
        unavailable_rows=int((~clean["stream"].available).sum()),
        population_inference="not_available",
    )
    return summary, pd.concat(saved_events, ignore_index=True), groups, family_attribution(pd.concat(per_events, ignore_index=True))


def verify_complete(path: Path) -> dict:
    marker = read(path / "COMPLETE.json")
    for name, expected in marker["files"].items():
        if digest(path / name) != expected:
            raise ValueError(f"completed replay changed: {path / name}")
    return marker


def run_block(fold: int, seed: int, block_index: int) -> dict:
    verify_protocol()
    blocks = policy_blocks()
    if block_index < 0 or block_index >= len(blocks):
        raise ValueError("unknown policy block")
    candidates_block = blocks[block_index]
    unit = UNITS / f"bdg2_f{fold}_s{seed}"
    stage = unit / "blocks" / f"block_{block_index:03d}"
    if (stage / "COMPLETE.json").exists():
        marker = verify_complete(stage)
        return {"status": "complete_zero_fit_resume", "stage": str(stage), "marker": marker}
    if stage.exists():
        raise ValueError(f"uncertain partial replay checkpoint preserved: {stage}")
    existing_partials = list(stage.parent.glob(stage.name + ".partial-*")) if stage.parent.exists() else []
    if existing_partials:
        raise ValueError(f"existing partial replay preserved: {existing_partials[0]}")
    partial = stage.with_name(stage.name + f".partial-{os.getpid()}")
    partial.mkdir(parents=True)
    ledger = unit / "operations.jsonl"
    start = time.perf_counter()
    append_ledger(ledger, event="started", phase="policy_block", fold=fold, model_seed=seed,
                  block_index=block_index, candidate_ids=[c["candidate_id"] for c in candidates_block])
    protocol, data, roles, prepared = load_unit(fold, seed)
    meta, truth, feature_sets, observed, available, catalogues, allocations = replay_inputs(
        fold, seed, data, roles, prepared
    )
    candidate0 = candidates_block[0]
    owner_method = "cqr" if candidate0["method"] == "quantile_uncalibrated" else candidate0["method"]
    owner = SavedOwner(fold, seed, owner_method, float(candidate0["level"]), data, roles)
    if candidate0["method"] == "quantile_uncalibrated":
        owner = copy.copy(owner)
        owner.method = "quantile_uncalibrated"
        owner.identity = dict(owner.identity, method=owner.method)
        owner.fit_identity = signature(dict(base=owner.fit_identity, method=owner.method))
    raw = {}
    for stream_id, features in feature_sets.items():
        values = owner.raw(features)
        raw[stream_id] = {"values": values, "fit_identity": owner.fit_identity,
                          "feature_hash": __import__("hashlib").sha256(
                              pd.util.hash_pandas_object(features, index=False).values.tobytes()).hexdigest()}
        append_ledger(ledger, event="returned", phase="saved_owner_inference", fold=fold,
                      model_seed=seed, block_index=block_index, stream_id=stream_id,
                      owner_sha256=owner.reference["owner"]["sha256"], rows=len(features), fits=0)
    clean_result = replay(owner, feature_sets["clean"], meta, observed["clean"], available["clean"],
                          candidate0, data["freq"], raw_prediction=raw["clean"])
    corrupt_results = {}
    for catalogue_seed in DESIGN["catalogue_seeds"]:
        corrupt_results[catalogue_seed] = replay(
            owner, feature_sets[catalogue_seed], meta, observed[catalogue_seed], available[catalogue_seed],
            candidate0, data["freq"], raw_prediction=raw[catalogue_seed]
        )
    for stream_id, result in [("clean", clean_result), *[(str(key), value) for key, value in corrupt_results.items()]]:
        replay_stream = result["stream"]
        append_ledger(
            ledger, event="returned", phase="replay_conformalization_update", fold=fold,
            model_seed=seed, block_index=block_index, stream_id=stream_id,
            owner_sha256=owner.reference["owner"]["sha256"],
            calibration_sha256=owner.reference["calibration_values"]["sha256"],
            method=candidate0["method"], level=candidate0["level"], strategy=candidate0["strategy"],
            replay_rows=len(replay_stream), conformalized_rows=len(replay_stream),
            update_operations=int(replay_stream.updated.astype(bool).sum()), fits=0,
            emitted_hash=result["emitted_hash"],
        )
    for result in [clean_result, *corrupt_results.values()]:
        released = pd.to_datetime(result["stream"].latest_released_target, errors="coerce")
        origins = pd.to_datetime(result["stream"].origin_time)
        if (released.notna() & (released > origins)).any():
            raise ValueError("future residual entered an issued interval")
    common_path = REPO / owner.reference["common_support"]
    common_ids = set(frame(common_path).row_id.astype(str))
    if not common_ids or not common_ids.issubset(set(meta.row_id.astype(str))):
        raise ValueError("common-support cohort mismatch")

    metric_rows, event_rows, group_rows, family_rows = [], [], [], []
    for candidate in candidates_block:
        for support, ids in (("native", None), ("common", common_ids)):
            summary, events, groups, families = metrics_for_view(
                candidate, clean_result, corrupt_results, catalogues, data["freq"], support, ids
            )
            append_ledger(
                ledger, event="returned", phase="operational_metrics", fold=fold,
                model_seed=seed, block_index=block_index, candidate_id=candidate["candidate_id"],
                support=support, catalogue_replays=len(DESIGN["catalogue_seeds"]),
                event_count=summary["n_events"], metric_rows=1, fits=0,
            )
            tag = {
                "evaluation_id": f"bdg2_f{fold}_s{seed}_{candidate['candidate_id']}",
                "candidate_id": candidate["candidate_id"], "dataset": "bdg2", "horizon": 1,
                "outer_fold": fold, "model_seed": seed, "method": candidate["method"],
                "level": candidate["level"], "strategy": candidate["strategy"],
                "every": candidate["every"], "window": candidate["window"],
                "rule_id": candidate["rule_id"], "support": support,
                "canonical_evaluation": support == "native", "reporting_alias": support == "common",
            }
            metric_rows.append({**tag, **summary})
            for key, value in tag.items():
                events[key] = value
                groups[key] = value
                families[key] = value
            event_rows.append(events); group_rows.append(groups); family_rows.append(families)

    policy_streams = []
    for stream_id, result in [("clean", clean_result), *[(str(s), corrupt_results[s]) for s in DESIGN["catalogue_seeds"]]]:
        compact = result["stream"][["row_id", "group_id", "origin_time", "target_time", "observed", "available",
                                    "point", "raw_lower", "raw_upper", "lower", "upper", "numerical_violation",
                                    "availability_violation", "combined_violation", "latest_released_target",
                                    "update_pool_n", "updated", "update_status"]].copy()
        compact["stream_id"] = stream_id
        policy_streams.append(compact)
    pd.concat(policy_streams, ignore_index=True).to_csv(partial / "policy_streams.csv.gz", index=False)
    pd.DataFrame(metric_rows).to_csv(partial / "metrics.csv", index=False)
    pd.concat(event_rows, ignore_index=True).to_csv(partial / "event_scores.csv.gz", index=False)
    pd.concat(group_rows, ignore_index=True).to_csv(partial / "group_metrics.csv", index=False)
    pd.concat(family_rows, ignore_index=True).to_csv(partial / "family_metrics.csv", index=False)
    pd.concat([pd.DataFrame(value).assign(catalogue_seed=key) for key, value in catalogues.items()], ignore_index=True).to_csv(partial / "catalogues.csv.gz", index=False)
    atomic_json(partial / "identity.json", {
        "version": VERSION, "fold": fold, "model_seed": seed, "block_index": block_index,
        "candidate_ids": [item["candidate_id"] for item in candidates_block],
        "policy": {key: candidate0[key] for key in ("method", "level", "strategy", "every", "window")},
        "owner": owner.reference, "fit_identity": owner.fit_identity,
        "interval_protocol_sha256": digest(bundle_paths(fold, seed)[0] / "frozen_protocol.json"),
        "scientific_source_hash": source_digest(), "models_fitted": 0, "new_seeds": 0,
        "native_rows": len(meta), "common_rows": len(common_ids), "catalogue_allocations": allocations,
    })
    files = {path.name: digest(path) for path in partial.iterdir() if path.is_file()}
    elapsed = time.perf_counter() - start
    marker = {"status": "complete", "files": files, "candidate_count": len(candidates_block),
              "metric_rows": len(metric_rows), "models_fitted": 0, "elapsed_seconds": elapsed,
              "completed_utc": utc()}
    atomic_json(partial / "COMPLETE.json", marker)
    stage.parent.mkdir(parents=True, exist_ok=True)
    os.replace(partial, stage)
    append_ledger(ledger, event="returned", phase="policy_block", fold=fold, model_seed=seed,
                  block_index=block_index, candidate_count=len(candidates_block), metric_rows=len(metric_rows),
                  fits=0, seconds=elapsed, bytes=sum(path.stat().st_size for path in stage.rglob("*") if path.is_file()))
    print(json.dumps(marker, indent=2))
    return marker


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["run-block"])
    parser.add_argument("--fold", type=int, required=True, choices=[0, 1, 2])
    parser.add_argument("--model-seed", type=int, required=True, choices=[42, 43, 44, 45, 46])
    parser.add_argument("--block-index", type=int, required=True)
    args = parser.parse_args()
    run_block(args.fold, args.model_seed, args.block_index)
