"""Independent zero-fit validation of extension owners and policy blocks.

validate-owners checks model ownership, quantile levels, the established factory
parameters, training and calibration identity against the accepted 95% owner of
the same unit, calibration rank support and prediction identity.

validate-block runs the frozen operational005 block validator unchanged (output
location and source identity substituted) and then an extended validator written
independently of the replay and metric code.  The extended validator

* rebuilds every issued interval of all six streams from the saved raw quantile
  predictions, saved calibration scores and released observations, reproducing
  the delayed score release, update schedule and rank rule, and requires bit
  equality;
* checks the clean stream against the owner's saved test predictions and the
  disturbed observations and fault catalogue against the accepted 95% block of
  the same unit (identical faults, severities and observation support);
* recomputes macro recall, micro recall, ordinary episode precision, custom
  synthetic F1, clean workload, time in alert and restricted detection time for
  both support views from the saved streams and catalogues.
"""
from __future__ import annotations

from hc_common import single_thread_environment

single_thread_environment()

import argparse  # noqa: E402
import gzip  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from hc_common import (  # noqa: E402
    FROZEN, LEVELS, OWNERS, RUN_ROOT, SCIENCE, UNITS, VERSION, atomic_json, digest, level_tag, read,
    source_content_digest, tree, unit_name, utc, verify_extension_protocol,
)
from hc_owner import EXPECTED_CAL_COUNTS, EXPECTED_FIT_COUNTS, frozen_adapter, load_unit, stage_keys  # noqa: E402

SRC = SCIENCE / "smart_building_conformal" / "src"
HOUR = pd.Timedelta("1h").value
METRIC_TOLERANCE = 1e-10
STREAM_IDS = ("clean", "42", "43", "44", "45", "46")
COMPARED_METRICS = (
    "macro_event_recall", "observed_strata_recall", "custom_synthetic_f1", "event_recall_micro",
    "ordinary_matched_event_episode_precision", "background_episodes_per_asset_day", "exposure_asset_days",
    "n_events", "n_detected", "corrupted_episode_count", "unmatched_episode_count", "time_in_alert_fraction",
    "observed_strata", "detected_delay_median_minutes", "detected_delay_q90_minutes", "undetected_fraction",
    "delay_restriction_minutes", "restricted_mean_detection_minutes", "support_rows", "available_rows",
    "unavailable_rows",
)


class ValidationFailure(Exception):
    """A scientific validation failure (never retried by the supervisor)."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationFailure(message)


def round_trip(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, float_precision="round_trip", **kwargs)


def mapie_alpha(level: float) -> float:
    from decimal import Decimal
    return float(Decimal("1") - Decimal(str(level)))


# --------------------------------------------------------------------------- owners

def validate_owners(fold: int, seed: int) -> dict:
    extension = verify_extension_protocol(fold=fold, seed=seed)
    adapter = frozen_adapter()
    from src.conformal_cqr import _quantile_estimator
    from src.conformal_quantile import _sub_estimators
    from src.intervals005_common import Operations, load_owner
    from src.intervals005_owners import raw_predictions
    unit = unit_name(fold, seed)
    root = OWNERS / unit
    manifest = read(root / "OWNER_MANIFEST.json")
    report: dict = {"version": VERSION, "unit": unit, "fold": fold, "model_seed": seed, "levels": {}}
    with Operations(forbid=True):
        protocol, data, roles, _ = load_unit(adapter, fold, seed, extension["source_content_digest"])
        _, bundle = adapter.bundle_paths(fold, seed)
        reference = {name: bundle / "stages" / name for name in
                     ("owner_fit_h1_cqr_l95", "owner_cal_h1_cqr_l95", "raw_h1_cqr_l95")}
        reference_fit_ops = read(reference["owner_fit_h1_cqr_l95"] / "operation_counts.json")["operations"]
        reference_cal_ops = read(reference["owner_cal_h1_cqr_l95"] / "operation_counts.json")["operations"]
        reference_owner = load_owner(reference["owner_cal_h1_cqr_l95"] / "owner.pkl")
        reference_estimators, _ = _sub_estimators(reference_owner)
        X = data["X"]
        fit_rows, cal_rows, test_rows = roles["fit"], roles["calibration"], roles["test"]

        # Chronological roles: fit precedes calibration precedes test within every
        # group, and no calibration target matures after the first test origin.
        meta = data["meta"]
        times = {role: meta.iloc[roles[role]][["group_id", "origin_time", "target_time"]].assign(
            group_id=lambda f: f.group_id.astype(str),
            origin_time=lambda f: pd.to_datetime(f.origin_time), target_time=lambda f: pd.to_datetime(f.target_time))
            for role in ("fit", "calibration", "test")}
        per_group = []
        for group in sorted(set(times["test"].group_id)):
            fit_g = times["fit"][times["fit"].group_id == group]
            cal_g = times["calibration"][times["calibration"].group_id == group]
            test_g = times["test"][times["test"].group_id == group]
            per_group.append({
                "group_id": group,
                "fit_before_calibration": bool(fit_g.empty or cal_g.empty
                                               or fit_g.target_time.max() <= cal_g.origin_time.min()),
                "calibration_before_test": bool(cal_g.empty or cal_g.target_time.max() <= test_g.origin_time.min()),
            })
        chronology = {
            "fit_max_target": str(times["fit"].target_time.max()),
            "calibration_min_origin": str(times["calibration"].origin_time.min()),
            "calibration_max_target": str(times["calibration"].target_time.max()),
            "test_min_origin": str(times["test"].origin_time.min()),
            "global_calibration_targets_before_first_test_origin":
                bool(times["calibration"].target_time.max() < times["test"].origin_time.min()),
            "groups": len(per_group),
            "groups_fit_before_calibration": sum(g["fit_before_calibration"] for g in per_group),
            "groups_calibration_before_test": sum(g["calibration_before_test"] for g in per_group),
        }
        require(chronology["global_calibration_targets_before_first_test_origin"],
                "calibration target matures after the first test origin")
        require(chronology["groups_fit_before_calibration"] == len(per_group), "fit/calibration chronology violated")
        require(chronology["groups_calibration_before_test"] == len(per_group), "calibration/test chronology violated")
        report["chronology"] = chronology

        # Calibration feature identity: the accepted 95% owner reproduces its own
        # saved calibration predictions from this unit's reconstructed features.
        saved95 = round_trip(reference["raw_h1_cqr_l95"] / "calibration_95.csv.gz")
        again95 = raw_predictions(reference_owner, "cqr", X.iloc[cal_rows].to_numpy(), [0.95])[0.95]
        difference95 = max(float(np.max(np.abs(saved95[c].to_numpy() - again95[c].to_numpy())))
                           for c in ("point", "raw_lower", "raw_upper", "static_lower", "static_upper"))
        require(difference95 == 0.0, f"calibration features differ from the accepted owner's ({difference95})")
        report["calibration_feature_identity_max_difference"] = difference95
        reference_cal_meta = round_trip(reference["raw_h1_cqr_l95"] / "calibration_metadata.csv.gz",
                                        dtype={"row_id": str, "group_id": str})
        reference_test_meta = round_trip(reference["raw_h1_cqr_l95"] / "test_metadata.csv.gz",
                                         dtype={"row_id": str, "group_id": str})

        for level in LEVELS:
            tag = level_tag(level)
            record = manifest["levels"][tag]
            fit_key, cal_key, raw_key = stage_keys(level)
            for key in (fit_key, cal_key, raw_key):
                path = RUN_ROOT / record["stages"][key]["path"]
                require(tree(path) == record["stages"][key]["files"], f"owner stage changed: {key}")
                marker = read(path / "COMPLETE.json")
                files = dict(tree(path)); files.pop("COMPLETE.json")
                require(marker["files"] == files and marker["key"] == key, f"owner stage marker mismatch: {key}")
            fit_path = root / "stages" / fit_key
            cal_path = root / "stages" / cal_key
            raw_path = root / "stages" / raw_key
            require(digest(fit_path / "owner.pkl") == record["fitted_owner_sha256"], "fitted owner hash")
            require(digest(cal_path / "owner.pkl") == record["calibrated_owner_sha256"], "calibrated owner hash")
            require(read(cal_path / "stage.json")["payload"]["source_fitted_owner_sha256"] == record["fitted_owner_sha256"],
                    "calibrated owner does not descend from the fitted owner")
            fitted = load_owner(fit_path / "owner.pkl")
            owner = load_owner(cal_path / "owner.pkl")
            for candidate in (fitted, owner):
                require(type(candidate).__name__ == "ConformalizedQuantileRegressor", "owner class")
                require(float(candidate._alpha) == mapie_alpha(level), "owner nominal level")
            estimators, quantiles = _sub_estimators(owner)
            alpha = mapie_alpha(level)
            expected_quantiles = [alpha / 2, 1 - alpha / 2, 0.5]
            nominal = [(1 - level) / 2, 1 - (1 - level) / 2, 0.5]
            require(len(estimators) == 3 and [float(q) for q in quantiles] == expected_quantiles,
                    f"quantile levels at {tag}: {quantiles}")
            require(all(abs(a - b) <= 1e-12 for a, b in zip(quantiles, nominal)), "quantile levels off nominal")
            factory = _quantile_estimator(seed).get_params()
            factory.pop("quantile")
            for estimator, expected_quantile in zip(estimators, expected_quantiles):
                params = estimator.get_params()
                require(type(estimator).__name__ == "HistGradientBoostingRegressor", "estimator class")
                require(float(params.pop("quantile")) == expected_quantile, "estimator quantile")
                require(params == factory, f"estimator parameters differ from the established factory at {tag}")
            # Training feature identity: histogram bin thresholds are fitted from the
            # training features alone and must equal those of the accepted 95% owner.
            for estimator, ref in zip(estimators, reference_estimators):
                require(estimator.n_features_in_ == ref.n_features_in_, "feature count")
                mine, theirs = estimator._bin_mapper.bin_thresholds_, ref._bin_mapper.bin_thresholds_
                require(len(mine) == len(theirs) and all(np.array_equal(a, b) for a, b in zip(mine, theirs)),
                        "training features differ from the accepted owner")
            fit_ops = read(fit_path / "operation_counts.json")
            cal_ops = read(cal_path / "operation_counts.json")
            require(fit_ops["counts"] == EXPECTED_FIT_COUNTS and cal_ops["counts"] == EXPECTED_CAL_COUNTS,
                    "operation counts")
            for mine_ops, theirs_ops in ((fit_ops["operations"], reference_fit_ops), (cal_ops["operations"], reference_cal_ops)):
                require(len(mine_ops) == len(theirs_ops), "operation inventory length")
                for a, b in zip(mine_ops, theirs_ops):
                    require(a["kind"] == b["kind"] and a["n_rows"] == b["n_rows"] and a["target_hash"] == b["target_hash"],
                            "training or calibration rows differ from the accepted owner")
            require(fit_ops["operations"][0]["n_rows"] == len(fit_rows), "fit row count")
            require(cal_ops["operations"][0]["n_rows"] == len(cal_rows), "calibration row count")
            require([round(op["parameters"]["quantile"], 12) for op in fit_ops["operations"][:3]]
                    == [round(q, 12) for q in expected_quantiles], "recorded fit quantiles")
            # Prediction identity: saved raw predictions are reproduced by the owner.
            cal_meta = round_trip(raw_path / "calibration_metadata.csv.gz", dtype={"row_id": str, "group_id": str})
            test_meta = round_trip(raw_path / "test_metadata.csv.gz", dtype={"row_id": str, "group_id": str})
            pd.testing.assert_frame_equal(cal_meta, reference_cal_meta)
            pd.testing.assert_frame_equal(test_meta, reference_test_meta)
            prediction_difference = 0.0
            for role, rows in (("calibration", cal_rows), ("test", test_rows)):
                saved = round_trip(raw_path / f"{role}_{tag}.csv.gz")
                again = raw_predictions(owner, "cqr", X.iloc[rows].to_numpy(), [level])[level]
                for column in ("point", "raw_lower", "raw_upper", "static_raw_lower", "static_raw_upper",
                               "static_lower", "static_upper"):
                    prediction_difference = max(prediction_difference,
                                                float(np.max(np.abs(saved[column].to_numpy() - again[column].to_numpy()))))
            require(prediction_difference == 0.0, f"owner predictions not reproduced ({prediction_difference})")
            # Calibration rank support for the operational CQR rule and MAPIE's native rule.
            n_cal = len(cal_rows)
            rank = math.ceil((n_cal + 1) * level)
            scores = np.load(cal_path / "native_conformity_scores.npy")
            cal_values = round_trip(raw_path / f"calibration_{tag}.csv.gz")
            y_cal = cal_meta.y_true.to_numpy()
            static_cover = float(np.mean((y_cal >= cal_values.static_lower) & (y_cal <= cal_values.static_upper)))
            raw_cover = float(np.mean((y_cal >= np.minimum(cal_values.raw_lower, cal_values.raw_upper))
                                      & (y_cal <= np.maximum(cal_values.raw_lower, cal_values.raw_upper))))
            require(1 <= rank <= n_cal, "operational CQR calibration rank unsupported")
            require(np.isfinite(scores).all() and scores.shape[0] == n_cal, "native conformity scores")
            report["levels"][tag] = {
                "level": level,
                "fitted_owner_sha256": record["fitted_owner_sha256"],
                "calibrated_owner_sha256": record["calibrated_owner_sha256"],
                "quantiles": [float(q) for q in quantiles],
                "estimator_parameters_match_factory": True,
                "training_rows": len(fit_rows), "calibration_rows": n_cal, "test_rows": len(test_rows),
                "training_target_hash_matches_accepted_95_owner": True,
                "calibration_target_hash_matches_accepted_95_owner": True,
                "training_bin_thresholds_match_accepted_95_owner": True,
                "operational_cqr_rank": rank, "operational_cqr_rank_supported": True,
                "rolling_window_rank_support": {str(w): math.ceil((w + 1) * level) <= w for w in (200, 500)},
                "minimum_supported_pool": next(n for n in range(1, 10_000) if math.ceil((n + 1) * level) <= n),
                "native_conformity_scores": int(scores.shape[0]),
                "prediction_reproduction_max_difference": prediction_difference,
                "raw_quantile_crossings_calibration": int(np.sum(cal_values.raw_lower > cal_values.raw_upper)),
                "calibration_raw_quantile_coverage": raw_cover,
                "calibration_static_cqr_coverage": static_cover,
            }
    result = {**report, "passed": True, "models_fitted": 0, "calibrators_fitted": 0,
              "owner_manifest_sha256": digest(root / "OWNER_MANIFEST.json"),
              "source_content_digest": source_content_digest(SRC), "utc": utc()}
    atomic_json(root / "OWNER_VALIDATION.json", result)
    print(json.dumps({"passed": True, "unit": unit}))
    return result


# --------------------------------------------------------------------------- blocks

def exact_streams(path: Path) -> pd.DataFrame:
    names = ("observed", "lower", "upper")
    dtype = {f"{name}_hex": str for name in names}
    dtype.update(row_id=str, group_id=str, stream_id=str, update_status=str)
    frame = pd.read_csv(path, dtype=dtype, keep_default_na=False, na_values={"point": [""], "raw_lower": [""],
                        "raw_upper": [""]}, float_precision="round_trip", low_memory=False)
    for name in names:
        frame[name] = np.array([float.fromhex(value) for value in frame[name + "_hex"]], dtype=np.float64)
    for name in ("available", "numerical_violation", "availability_violation", "combined_violation", "updated"):
        frame[name] = frame[name].astype(str).map({"True": True, "False": False})
        if frame[name].isna().any():
            raise ValidationFailure(f"non-boolean {name}")
    frame["origin_time"] = pd.to_datetime(frame.origin_time)
    frame["target_time"] = pd.to_datetime(frame.target_time)
    frame["latest_released_target"] = pd.to_datetime(frame.latest_released_target.replace("", None))
    frame["update_pool_n"] = frame.update_pool_n.astype(int)
    return frame


def segment_rows(frame: pd.DataFrame) -> list[tuple[str, str, np.ndarray]]:
    groups = frame.group_id.astype(str).to_numpy()
    targets = frame.target_time.to_numpy("datetime64[ns]").astype(np.int64)
    out = []
    for group in sorted(set(groups)):
        rows = np.flatnonzero(groups == group)
        rows = rows[np.argsort(targets[rows], kind="stable")]
        cuts = np.r_[0, np.flatnonzero(np.diff(targets[rows]) != HOUR) + 1, len(rows)]
        for i, (a, b) in enumerate(zip(cuts, cuts[1:])):
            if a < b:
                out.append((group, f"{group}:segment:{i}", rows[a:b]))
    return out


def cqr_quantile(scores: list[float], level: float) -> float | None:
    values = np.sort(np.asarray(scores, float)[np.isfinite(scores)])
    rank = math.ceil((len(values) + 1) * level)
    if not 1 <= rank <= len(values):
        return None
    return float(values[rank - 1])


def rebuild_intervals(stream: pd.DataFrame, calibration: pd.DataFrame, candidate: dict) -> dict[str, np.ndarray]:
    """Independent causal replay of one stream from saved raw predictions and scores."""
    method, strategy, level = candidate["method"], candidate["strategy"], float(candidate["level"])
    every = int(candidate["every"]) if strategy != "static" else 0
    window = int(candidate["window"]) if strategy == "rolling" else None
    n = len(stream)
    observed = stream.observed.to_numpy(float)
    available = stream.available.to_numpy(bool)
    raw_lower = stream.raw_lower.to_numpy(float)
    raw_upper = stream.raw_upper.to_numpy(float)
    targets = stream.target_time.to_numpy("datetime64[ns]").astype(np.int64)
    origins = stream.origin_time.to_numpy("datetime64[ns]").astype(np.int64)
    lower = np.full(n, np.nan)
    upper = np.full(n, np.nan)
    updated = np.zeros(n, bool)
    pool = np.zeros(n, int)
    latest = np.full(n, np.iinfo(np.int64).min, dtype=np.int64)
    status = np.full(n, "static", dtype=object)
    base = cqr_quantile(list(calibration.score), level)
    if base is None:
        raise ValidationFailure("initial calibration rank unsupported")
    by_group = {group: part.sort_values("target_time", kind="stable") for group, part in calibration.groupby("group_id")}
    for group, _, rows in segment_rows(stream):
        local = by_group.get(group, calibration.sort_values("target_time", kind="stable"))
        history = [float(v) for v in local.score if np.isfinite(v)]
        q = base
        released = 0
        for ordinal, i in enumerate(rows):
            while released < ordinal and targets[rows[released]] <= origins[i]:
                old = rows[released]
                released += 1
                if available[old]:
                    history.append(float(max(raw_lower[old] - observed[old], observed[old] - raw_upper[old])))
            pool[i] = len(history)
            if released:
                latest[i] = targets[rows[released - 1]]
            if strategy != "static":
                if ordinal % every == 0:
                    scores = history[-window:] if strategy == "rolling" else history
                    proposed = cqr_quantile(scores, level) if len(scores) >= 50 else None
                    if proposed is not None:
                        q = proposed
                        updated[i] = True
                        status[i] = "updated"
                    else:
                        status[i] = "held_insufficient_score_or_rank_support"
                    pool[i] = len(scores)
                else:
                    status[i] = "held_between_updates"
            if method == "quantile_uncalibrated" or strategy == "static":
                continue
            lower[i], upper[i] = sorted((raw_lower[i] - q, raw_upper[i] + q))
    return {"lower": lower, "upper": upper, "updated": updated, "pool": pool, "latest": latest, "status": status}


def alerts(frame: pd.DataFrame, k: int, m: int) -> tuple[np.ndarray, list[dict], dict]:
    available = frame.available.to_numpy(bool)
    observed = frame.observed.to_numpy(float)
    with np.errstate(invalid="ignore"):
        numerical = available & ((observed < frame.lower.to_numpy(float)) | (observed > frame.upper.to_numpy(float)))
    violation = ~available | numerical
    flags = np.zeros(len(frame), bool)
    episodes = []
    segment_end = {}
    segment_at = {}
    targets = frame.target_time.to_numpy("datetime64[ns]")
    for group, sid, rows in segment_rows(frame):
        segment_end[sid] = pd.Timestamp(targets[rows[-1]])
        for row in rows:
            segment_at[int(row)] = sid
        cumulative = np.r_[0, np.cumsum(violation[rows])]
        count = cumulative[1:] - cumulative[np.maximum(0, np.arange(len(rows)) + 1 - m)]
        active = count >= k
        flags[rows] = active
        starts = np.flatnonzero(active & ~np.r_[False, active[:-1]])
        ends = np.flatnonzero(active & ~np.r_[active[1:], False])
        for start, end in zip(starts, ends):
            a = int(rows[start])
            episodes.append({"group_id": group, "segment_id": sid, "start_index": a,
                             "onset": pd.Timestamp(targets[a]), "episode_id": f"combined:{sid}:{a}"})
    return flags, episodes, {"segment_end": segment_end, "segment_at": segment_at}


def view_events(events: pd.DataFrame, frame: pd.DataFrame, segment_at: dict) -> pd.DataFrame:
    keys = {(g, pd.Timestamp(t)): i for i, (g, t) in enumerate(zip(frame.group_id.astype(str), frame.target_time))}
    kept = []
    for event in events.to_dict("records"):
        start = keys.get((str(event["group_id"]), pd.Timestamp(event["onset"])))
        end = keys.get((str(event["group_id"]), pd.Timestamp(event["end"])))
        if start is None or end is None:
            continue
        kept.append({**event, "start_index": start, "segment_id": segment_at[start]})
    return pd.DataFrame(kept, columns=list(events.columns))


def score_catalogue(frame: pd.DataFrame, events: pd.DataFrame, k: int, m: int, strata: list, common: bool):
    flags, episodes, segments = alerts(frame, k, m)
    if common:
        events = view_events(events, frame, segments["segment_at"])
    options: dict[tuple, list[dict]] = {}
    for episode in sorted(episodes, key=lambda e: (e["group_id"], str(e["onset"]), e["episode_id"])):
        options.setdefault((episode["group_id"], episode["segment_id"]), []).append(episode)
    used = set()
    n = np.zeros(len(strata))
    tp = np.zeros(len(strata))
    per_event = []
    eligible = events[events.effective.astype(bool)].sort_values(["group_id", "onset", "event_id"], kind="stable")
    for event in eligible.to_dict("records"):
        onset = pd.Timestamp(event["onset"])
        end = pd.Timestamp(event["tolerance_end"])
        segment = event["segment_id"]
        full = segment in segments["segment_end"] and end <= segments["segment_end"][segment]
        found = None
        if full:
            for episode in options.get((str(event["group_id"]), segment), []):
                if episode["episode_id"] not in used and onset <= episode["onset"] <= end:
                    found = episode
                    used.add(episode["episode_id"])
                    break
        if not full:
            continue
        j = strata.index((event["family"], float(event["severity"])))
        n[j] += 1
        tp[j] += found is not None
        per_event.append({"detected": found is not None,
                          "delay": (found["onset"] - onset) / pd.Timedelta(minutes=1) if found else np.nan,
                          "followup": (end - onset) / pd.Timedelta(minutes=1)})
    return {"n": n, "tp": tp, "episodes": len(episodes), "unmatched": len(episodes) - len(used),
            "alert_rows": int(flags.sum()), "rows": len(frame), "per_event": per_event}


def reconstruct_metrics(streams: dict, catalogues: pd.DataFrame, candidate: dict, strata: list,
                        common_ids: set | None) -> dict:
    k, m = int(candidate["k"]), int(candidate["m"])

    def view(frame):
        if common_ids is None:
            return frame.reset_index(drop=True)
        return frame[frame.row_id.isin(common_ids)].reset_index(drop=True)

    clean = view(streams["clean"])
    _, clean_episodes, _ = alerts(clean, k, m)
    exposure = len(clean) / 24.0
    parts = [score_catalogue(view(streams[str(seed)]), catalogues[catalogues.catalogue_seed == seed],
                             k, m, strata, common_ids is not None) for seed in range(42, 47)]
    n = sum(p["n"] for p in parts)
    tp = sum(p["tp"] for p in parts)
    corrupted = sum(p["episodes"] for p in parts)
    unmatched = sum(p["unmatched"] for p in parts)
    with np.errstate(invalid="ignore", divide="ignore"):
        recalls = np.where(n > 0, tp / np.where(n > 0, n, 1), np.nan)
        custom = np.where(n > 0, 2 * tp / (n + tp + unmatched / len(strata)), np.nan)
    events = [e for p in parts for e in p["per_event"]]
    detected = np.array([e["delay"] for e in events if e["detected"]], float)
    tau = min(e["followup"] for e in events) if events else np.nan
    waits = np.array([min(e["delay"] if e["detected"] else e["followup"], tau) for e in events], float)
    micro = float(tp.sum() / n.sum()) if n.sum() else np.nan
    return {
        "macro_event_recall": float(np.mean(recalls)),
        "observed_strata_recall": float(np.nanmean(recalls)) if (n > 0).any() else np.nan,
        "custom_synthetic_f1": float(np.mean(custom)),
        "event_recall_micro": micro,
        "ordinary_matched_event_episode_precision": float(tp.sum() / corrupted) if corrupted else np.nan,
        "background_episodes_per_asset_day": len(clean_episodes) / exposure,
        "exposure_asset_days": exposure,
        "n_events": int(n.sum()), "n_detected": int(tp.sum()),
        "corrupted_episode_count": int(corrupted), "unmatched_episode_count": int(unmatched),
        "time_in_alert_fraction": float(np.mean([p["alert_rows"] / p["rows"] for p in parts])),
        "observed_strata": int((n > 0).sum()),
        "detected_delay_median_minutes": float(np.median(detected)) if len(detected) else np.nan,
        "detected_delay_q90_minutes": float(np.quantile(detected, .9)) if len(detected) else np.nan,
        "undetected_fraction": 1 - micro if n.sum() else np.nan,
        "delay_restriction_minutes": float(tau),
        "restricted_mean_detection_minutes": float(waits.mean()) if len(waits) else np.nan,
        "support_rows": len(clean), "available_rows": int(clean.available.sum()),
        "unavailable_rows": int((~clean.available).sum()),
    }


def frozen_validation(fold: int, seed: int, block_index: int) -> dict:
    if str(FROZEN) not in sys.path:
        sys.path.insert(0, str(FROZEN))
    import validate as frozen
    if Path(frozen.__file__).resolve() != (FROZEN / "validate.py").resolve():
        raise ValueError("frozen validator resolved outside the science root")
    current = source_content_digest(SRC)
    frozen.UNITS = UNITS
    frozen.SOURCE_HASH = current
    frozen.source_digest = lambda: current
    return frozen.validate_block(fold, seed, block_index)


def validate_block(fold: int, seed: int, block_index: int) -> dict:
    extension = verify_extension_protocol(fold=fold, seed=seed)
    import hc_adapter
    adapter = frozen_adapter()
    from src.operational004_design import STRATA
    unit = unit_name(fold, seed)
    stage = UNITS / unit / "blocks" / f"block_{block_index:03d}"
    marker = read(stage / "COMPLETE.json")
    for name, expected in marker["files"].items():
        require(digest(stage / name) == expected, f"block artifact hash mismatch: {name}")
    require(marker.get("models_fitted") == 0, "block recorded a fit")
    frozen_result = frozen_validation(fold, seed, block_index)
    require(frozen_result.get("passed") is True, "frozen validator did not pass")

    blocks = hc_adapter.extension_blocks(adapter)
    candidates = blocks[block_index]
    identity = read(stage / "identity.json")
    level = float(candidates[0]["level"])
    tag = level_tag(level)
    owner_manifest = read(OWNERS / unit / "OWNER_MANIFEST.json")
    record = owner_manifest["levels"][tag]
    require(identity["candidate_ids"] == [c["candidate_id"] for c in candidates], "block candidate identity")
    require(identity["owner"]["owner"]["sha256"] == record["calibrated_owner_sha256"], "block owner identity")
    require(identity["owner"]["calibration_values"]["sha256"] == record["calibration_values_sha256"], "block calibration identity")
    require(identity["models_fitted"] == 0 and identity["scientific_source_hash"] == extension["source_content_digest"],
            "block fit/source identity")
    require(identity["version"].endswith("+" + VERSION), "block version identity")
    policy = {key: candidates[0][key] for key in hc_adapter.POLICY_FIELDS}
    require(identity["policy"] == policy, "block policy identity")

    streams_frame = exact_streams(stage / "policy_streams.csv.gz")
    require(set(streams_frame.stream_id) == set(STREAM_IDS), "stream inventory")
    streams = {sid: part.reset_index(drop=True) for sid, part in streams_frame.groupby("stream_id")}
    accepted_root = SCIENCE / "smart_building_conformal/outputs/operational005_causal_replay_v2/units" / unit / "blocks/block_000"
    accepted = exact_streams(accepted_root / "policy_streams.csv.gz")
    for sid in STREAM_IDS:
        mine = streams[sid]
        theirs = accepted[accepted.stream_id == sid].reset_index(drop=True)
        require(list(mine.row_id) == list(theirs.row_id), f"row identity differs from accepted block: {sid}")
        require(mine.origin_time.equals(theirs.origin_time) and mine.target_time.equals(theirs.target_time),
                f"timing differs from accepted block: {sid}")
        require(list(mine.observed_hex) == list(theirs.observed_hex) and mine.available.equals(theirs.available),
                f"disturbed observations differ from the accepted block: {sid}")
        require((mine.target_time > mine.origin_time).all(), "target must follow origin")
        released = mine.latest_released_target
        require(not (released.notna() & (released > mine.origin_time)).any(), "future residual leakage")
    with gzip.open(stage / "catalogues.csv.gz", "rb") as a, gzip.open(accepted_root / "catalogues.csv.gz", "rb") as b:
        require(a.read() == b.read(), "fault catalogue differs from the accepted block")
    require(identity["catalogue_allocations"] == read(accepted_root / "identity.json")["catalogue_allocations"],
            "catalogue allocation differs from the accepted block")

    raw_dir = OWNERS / unit / "stages" / stage_keys(level)[2]
    saved_test = round_trip(raw_dir / f"test_{tag}.csv.gz")
    saved_test_meta = round_trip(raw_dir / "test_metadata.csv.gz", dtype={"row_id": str, "group_id": str})
    clean = streams["clean"]
    require(list(saved_test_meta.row_id) == list(clean.row_id), "clean stream row order")
    for column in ("point", "raw_lower", "raw_upper"):
        require(np.array_equal(saved_test[column].to_numpy(), clean[column].to_numpy()),
                f"clean-stream {column} differs from the owner's saved test predictions")

    # Calibration scores read exactly as the frozen SavedOwner reads them.
    cal_meta = pd.read_csv(raw_dir / "calibration_metadata.csv.gz")
    cal_values = pd.read_csv(raw_dir / f"calibration_{tag}.csv.gz")
    calibration = pd.DataFrame({
        "group_id": cal_meta.group_id.astype(str),
        "target_time": pd.to_datetime(cal_meta.target_time),
        "score": np.maximum(cal_values.raw_lower.to_numpy() - cal_meta.y_true.to_numpy(),
                            cal_meta.y_true.to_numpy() - cal_values.raw_upper.to_numpy()),
    })
    candidate0 = candidates[0]
    status_counts = {}
    for sid in STREAM_IDS:
        stream = streams[sid]
        rebuilt = rebuild_intervals(stream, calibration, candidate0)
        if candidate0["method"] == "quantile_uncalibrated":
            low = np.minimum(stream.raw_lower.to_numpy(), stream.raw_upper.to_numpy())
            high = np.maximum(stream.raw_lower.to_numpy(), stream.raw_upper.to_numpy())
            require(np.array_equal(low, stream.lower.to_numpy()) and np.array_equal(high, stream.upper.to_numpy()),
                    f"uncalibrated bounds are not the ordered raw quantiles: {sid}")
        elif candidate0["strategy"] == "static":
            if sid == "clean":
                require(np.array_equal(saved_test.static_lower.to_numpy(), stream.lower.to_numpy())
                        and np.array_equal(saved_test.static_upper.to_numpy(), stream.upper.to_numpy()),
                        "clean static CQR bounds differ from the owner's saved static intervals")
            shift_low = float(np.median(saved_test.raw_lower - saved_test.static_raw_lower))
            shift_high = float(np.median(saved_test.static_raw_upper - saved_test.raw_upper))
            a = stream.raw_lower.to_numpy() - shift_low
            b = stream.raw_upper.to_numpy() + shift_high
            scale = np.maximum(1.0, np.abs(stream.lower.to_numpy()))
            require(np.all(np.abs(np.minimum(a, b) - stream.lower.to_numpy()) <= 1e-9 * scale)
                    and np.all(np.abs(np.maximum(a, b) - stream.upper.to_numpy()) <= 1e-9 * np.maximum(1.0, np.abs(stream.upper.to_numpy()))),
                    f"static CQR bounds are not the fixed native correction: {sid}")
        else:
            require(np.array_equal(rebuilt["lower"].view(np.uint64), stream.lower.to_numpy().view(np.uint64))
                    and np.array_equal(rebuilt["upper"].view(np.uint64), stream.upper.to_numpy().view(np.uint64)),
                    f"rebuilt adaptive CQR bounds differ: {sid}")
        require(np.array_equal(rebuilt["updated"], stream.updated.to_numpy(bool)), f"update flags differ: {sid}")
        require(np.array_equal(rebuilt["pool"], stream.update_pool_n.to_numpy(int)), f"update pool sizes differ: {sid}")
        require(list(rebuilt["status"]) == list(stream.update_status), f"update statuses differ: {sid}")
        latest = stream.latest_released_target.to_numpy("datetime64[ns]").astype(np.int64)
        require(np.array_equal(rebuilt["latest"], latest), f"delayed score release differs: {sid}")
        status_counts[sid] = {str(k): int(v) for k, v in stream.update_status.value_counts().sort_index().items()}

    common_ids = set(pd.read_csv(SCIENCE / identity["owner"]["common_support"], dtype={"row_id": str}).row_id)
    catalogues = pd.read_csv(stage / "catalogues.csv.gz")
    metrics = pd.read_csv(stage / "metrics.csv")
    strata = [tuple(item) for item in STRATA]
    maximum = 0.0
    checks = 0
    by_id = {c["candidate_id"]: c for c in candidates}
    for saved in metrics.to_dict("records"):
        candidate = by_id[saved["candidate_id"]]
        rebuilt = reconstruct_metrics(streams, catalogues, candidate, strata,
                                      None if saved["support"] == "native" else common_ids)
        for name in COMPARED_METRICS:
            a, b = float(saved[name]), float(rebuilt[name])
            if np.isnan(a) and np.isnan(b):
                checks += 1
                continue
            difference = abs(a - b)
            maximum = max(maximum, difference)
            require(difference <= METRIC_TOLERANCE, f"independent metric mismatch {saved['candidate_id']} "
                                                    f"{saved['support']} {name}: {a} vs {b}")
            checks += 1
    require(len(metrics) == 6 and set(metrics.support) == {"native", "common"}, "metric view inventory")
    result = {
        "passed": True, "version": VERSION, "unit": unit, "fold": fold, "model_seed": seed,
        "block_index": block_index, "candidate_ids": identity["candidate_ids"], "policy": policy,
        "frozen_validator": {"passed": True, "checks": frozen_result["checks"],
                             "maximum_absolute_difference": frozen_result["maximum_absolute_difference"]},
        "interval_reconstruction": "bit-identical for adaptive CQR; exact for uncalibrated and clean static",
        "update_status_counts": status_counts,
        "metric_checks": checks, "maximum_metric_absolute_difference": maximum,
        "comparability": "fault catalogue, allocations and disturbed observations identical to accepted block_000",
        "models_fitted": 0, "source_content_digest": source_content_digest(SRC), "utc": utc(),
    }
    atomic_json(UNITS / unit / "validation" / f"block_{block_index:03d}.extended.json", result)
    print(json.dumps({"passed": True, "unit": unit, "block_index": block_index, "metric_checks": checks,
                      "maximum_metric_absolute_difference": maximum}))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["validate-owners", "validate-block"])
    parser.add_argument("--fold", type=int, required=True, choices=[0, 1, 2])
    parser.add_argument("--model-seed", type=int, required=True, choices=[42, 43, 44, 45, 46])
    parser.add_argument("--block-index", type=int)
    args = parser.parse_args()
    try:
        if args.action == "validate-owners":
            validate_owners(args.fold, args.model_seed)
        else:
            validate_block(args.fold, args.model_seed, args.block_index)
    except (ValidationFailure, AssertionError) as exc:
        print(f"SCIENTIFIC_VALIDATION_FAILURE: {exc}", file=sys.stderr)
        raise SystemExit(3)
