"""Retrospective BDG2 comparison with thresholds selected before test replay.

Run from the repository root. This module deliberately does not import the
historical coordinators or change their source identities.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
PROTOCOL = json.loads((HERE / "protocol.json").read_text())
HOUR = pd.Timedelta(hours=1)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def features(frame, observed=None):
    """Features for target hour u use measurements at or before u-1 only."""
    y = frame.y if observed is None else pd.Series(observed, index=frame.index)
    filled = y.ffill(limit=3)
    history = filled.shift(1)
    x = pd.DataFrame(index=frame.index)
    for lag in [0, 1, 2, 3, 6, 12, 24]:
        x[f"lag_{lag}"] = filled.shift(1 + lag)
    for lag in [24, 168]:
        x[f"season_{lag}"] = filled.shift(lag)
    for window in [6, 24]:
        x[f"mean_{window}"] = history.rolling(window, min_periods=window // 2).mean()
        x[f"std_{window}"] = history.rolling(window, min_periods=window // 2).std()
    for name, value, period in [("hour", frame.index.hour, 24),
                                ("dow", frame.index.dayofweek, 7)]:
        x[name + "_sin"] = np.sin(2 * np.pi * value / period)
        x[name + "_cos"] = np.cos(2 * np.pi * value / period)
    x["target_was_missing"] = y.isna().shift(1, fill_value=True).astype(float)
    for col in ["airTemperature", "dewTemperature"]:
        v = frame[col]
        x[col] = v.ffill(limit=3).shift(1)
        x[col + "_was_missing"] = v.isna().shift(1, fill_value=True).astype(float)
    return x


def read_data(raw):
    bids = PROTOCOL["buildings"]
    meters = pd.read_csv(raw / "electricity.csv", usecols=["timestamp"] + bids,
                         parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    metadata = pd.read_csv(raw / "metadata.csv").set_index("building_id")
    weather = pd.read_csv(raw / "weather.csv", usecols=["timestamp", "site_id",
        "airTemperature", "dewTemperature"], parse_dates=["timestamp"])
    frames = {}
    for bid in bids:
        s = meters[bid]
        s = s.loc[s.first_valid_index():s.last_valid_index()]
        idx = pd.date_range(s.index[0], s.index[-1], freq="h")
        site = metadata.loc[bid, "site_id"]
        w = weather[weather.site_id.eq(site)].drop_duplicates("timestamp").set_index("timestamp")
        f = pd.DataFrame({"y": s.reindex(idx)}, index=idx)
        f[["airTemperature", "dewTemperature"]] = w.reindex(idx)[["airTemperature", "dewTemperature"]]
        frames[bid] = f
    return frames, metadata.loc[bids, "site_id"].astype(str).to_dict()


def partition(meta, fraction):
    """Global calendar boundaries, with target-to-origin one-hour embargoes."""
    times = pd.DatetimeIndex(sorted(meta.time.unique()))
    n = len(times)
    history = int(round(n * fraction))
    fit_end = int(history * .75)
    cal_end = int(history * .875)
    test_end = min(n, history + int(round(n * PROTOCOL["test_fraction"])))
    bounds = [times[fit_end], times[cal_end], times[history],
              times[test_end] if test_end < n else times[-1] + HOUR]
    # Targets in the earlier part must precede the next part's first origin.
    t = pd.DatetimeIndex(meta.time)
    masks = {"fit": t < bounds[0] - HOUR,
             "calibration": (t >= bounds[0]) & (t < bounds[1] - HOUR),
             "selection": (t >= bounds[1]) & (t < bounds[2] - HOUR),
             "test": (t >= bounds[2]) & (t < bounds[3] - HOUR)}
    for a, b in zip(masks, list(masks)[1:]):
        assert not np.any(masks[a] & masks[b])
        assert t[masks[a]].max() < t[masks[b]].min() - HOUR
    return masks


def starts(meta, flags):
    """Episode starts break at building boundaries and missing support hours."""
    flags = np.asarray(flags, bool)
    times = pd.DatetimeIndex(meta.time).asi8
    group = meta.building.to_numpy()
    boundary = np.r_[True, (group[1:] != group[:-1]) | (np.diff(times) != HOUR.value)]
    return flags & (boundary | ~np.r_[False, flags[:-1]])


def workload(meta, flags):
    return float(starts(meta, flags).sum() * 24 / len(meta)), float(np.mean(flags))


def conformal_quantile(values, level):
    values = np.sort(np.asarray(values)[np.isfinite(values)])
    rank = math.ceil((len(values) + 1) * level)
    if not 1 <= rank <= len(values):
        raise ValueError("unsupported finite-sample conformal rank")
    return float(values[rank - 1])


def seasonal_keys(meta):
    t = pd.DatetimeIndex(meta.time)
    return list(zip(meta.building, t.hour, t.dayofweek >= 5))


def seasonal_scales(meta, errors):
    data = pd.DataFrame(seasonal_keys(meta), columns=["building", "hour", "weekend"])
    data["error"] = np.abs(errors)
    pooled = data.groupby("building").error.median().clip(lower=1e-6).to_dict()
    by_cell = data.groupby(["building", "hour", "weekend"]).error.agg(["median", "count"])
    scales = {key: max(float(row["median"]), .05 * pooled[key[0]], 1e-6)
              for key, row in by_cell.iterrows() if row["count"] >= 10}
    return scales, pooled


def get_scales(meta, scales):
    cells, pooled = scales
    return np.array([cells.get(key, pooled[key[0]]) for key in seasonal_keys(meta)])


def candidate_bounds(pred, spec, scale):
    lower, point, upper = pred.T
    method = spec["method"]
    if method == "seasonal_residual":
        lo, hi = point - spec["threshold"] * scale, point + spec["threshold"] * scale
    elif method == "scaled_quantile":
        center = (lower + upper) / 2
        radius = np.maximum(np.abs(upper - lower) / 2, 1e-6) * spec["threshold"]
        lo, hi = center - radius, center + radius
    elif method in ("symmetric_cqr", "quantile_score_threshold"):
        lo, hi = lower - spec["threshold"], upper + spec["threshold"]
    elif method == "asymmetric_cqr":
        lo, hi = lower - spec["lower_correction"], upper + spec["upper_correction"]
    elif method == "raw_reference":
        lo, hi = lower, upper
    else:
        raise ValueError(method)
    # A negative conformal correction can create an empty set. Do not turn it
    # into a different nonempty interval by swapping its endpoints.
    return lo, hi


def numerical_flags(y, bounds):
    lo, hi = bounds
    return np.isfinite(y) & ((y < lo) | (y > hi))


def candidates(pred, y, scale):
    lower, point, upper = pred.T
    out = []
    for level in PROTOCOL["coverage_grid"]:
        q = conformal_quantile(np.maximum(lower - y, y - upper), level)
        out.append(dict(method="symmetric_cqr", level=level, threshold=q))
        out.append(dict(method="asymmetric_cqr", level=level,
            lower_correction=conformal_quantile(lower - y, 1 - (1 - level) / 2),
            upper_correction=conformal_quantile(y - upper, 1 - (1 - level) / 2)))
    normalized = np.abs(y - point) / scale
    radius = np.maximum(np.abs(upper - lower) / 2, 1e-6)
    scaled_score = np.abs(y - (lower + upper) / 2) / radius
    for method, score in [("seasonal_residual", normalized), ("scaled_quantile", scaled_score)]:
        thresholds = list(PROTOCOL["candidate_multipliers"])
        thresholds += [conformal_quantile(score, l) for l in PROTOCOL["coverage_grid"]]
        for q in sorted(set(thresholds)):
            out.append(dict(method=method, threshold=q))
    return out


def choose(meta, y, pred, scale, specs, budget):
    """Uses only the original selection stream, never injected/test outcomes."""
    rows = []
    for spec in specs:
        rate, active = workload(meta, numerical_flags(y, candidate_bounds(pred, spec, scale)))
        rows.append(dict(**spec, selection_workload=rate, selection_time_in_alert=active))
    feasible = [r for r in rows if r["selection_workload"] <= budget + 1e-12
                and r["selection_time_in_alert"] <= PROTOCOL["max_time_in_alert"]]
    if not feasible:
        return None, rows
    best = min(feasible, key=lambda r: (budget - r["selection_workload"],
        r["selection_time_in_alert"], json.dumps(r, sort_keys=True)))
    return best, rows


def inject(meta, y, train_scales, fold, seed):
    """Original seven disturbance families, with a new deterministic schedule.

    Four-hour events and the complete follow-up stay in one contiguous segment.
    Placement never receives predictions, thresholds, or detection results.
    """
    observed = y.copy()
    events = []
    strata = [(f, s) for f in PROTOCOL["families"] for s in PROTOCOL["severities"]]
    for bid, part in meta.groupby("building", sort=True):
        rows = part.index.to_numpy()
        times = pd.DatetimeIndex(part.time)
        n = len(rows)
        ns = int(hashlib.sha256(f"matched-workload-v1:{fold}:{seed}:{bid}".encode()).hexdigest()[:16], 16)
        rng = np.random.default_rng(ns)
        options = [j for j in range(1, n - 6)
                   if times[j + 6] - times[j - 1] == 7 * HOUR]
        rng.shuffle(options)
        occupied = np.zeros(n, bool)
        target = int(round(n / 24 * PROTOCOL["event_incidence_per_asset_day"]))
        count = 0
        for j in options:
            if count >= target:
                break
            if occupied[max(0, j - 6):j + 10].any():
                continue
            occupied[max(0, j - 6):j + 10] = True
            family, severity = strata[(count + seed - 42) % len(strata)]
            sign = 1 if (count // len(strata) + seed) % 2 else -1
            pick = rows[j:j + 4]
            values = y[pick].copy()
            original = values.copy()
            fraction = {.5: .25, 1.: .5, 2.: 1.}[severity]
            size = math.ceil(4 * fraction)
            a = (4 - size) // 2
            if family == "random_missing":
                values[rng.random(4) < .2 * severity] = np.nan
            elif family == "block_missing":
                values[a:a + size] = np.nan
            elif family == "stuck":
                values[a:a + size] = y[rows[j - 1]] if a == 0 else values[a - 1]
            elif family == "dropout":
                values[a:a + size] = 0
            else:
                u = np.linspace(0, 1, 4)
                shape = np.minimum(np.minimum(4 * u, 1), 4 * (1 - u)) if family == "bias" else u if family == "drift" else np.ones(4)
                values += sign * severity * train_scales[bid] * shape
            effective = bool((~np.isfinite(values)).any() or np.any(values != original))
            observed[pick] = values
            events.append(dict(event_id=f"f{fold}_c{seed}_{bid}_{count}", building=bid,
                family=family, severity=severity, sign=sign, start=int(pick[0]),
                end=int(pick[-1]), tolerance_end=int(rows[j + 6]), effective=effective,
                onset=str(times[j]), catalogue_seed=seed))
            count += 1
    return observed, pd.DataFrame(events)


def score_events(meta, flags, events, channel):
    beginnings = starts(meta, flags)
    used = set()
    rows = []
    for event in events[events.effective].sort_values(["building", "start"]).to_dict("records"):
        choices = np.flatnonzero(beginnings[event["start"]:event["tolerance_end"] + 1]) + event["start"]
        found = next((int(i) for i in choices if int(i) not in used), None)
        if found is not None:
            used.add(found)
        delay = float((pd.Timestamp(meta.iloc[found].time) - pd.Timestamp(event["onset"])) / pd.Timedelta(minutes=1)) if found is not None else 360.
        rows.append(dict(**event, channel=channel, detected=found is not None,
            restricted_delay_minutes=delay))
    return pd.DataFrame(rows)


def unit(raw, out, fold, seed):
    started = time.monotonic()
    directory = out / f"f{fold}_s{seed}"
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory / "COMPLETE.json"
    if marker.exists():
        saved = json.loads(marker.read_text())
        if saved["protocol_sha256"] != digest(HERE / "protocol.json") or saved["code_sha256"] != digest(__file__):
            raise ValueError("resume identity mismatch")
        for name, checksum in saved["files"].items():
            if digest(directory / name) != checksum:
                raise ValueError("resume artifact mismatch")
        return str(directory)
    with threadpool_limits(limits=1):
        frames, sites = read_data(raw)
        xparts, mparts = [], []
        for bid, frame in frames.items():
            x = features(frame)
            valid = x.notna().all(axis=1) & frame.y.notna()
            xparts.append(x.loc[valid].reset_index(drop=True))
            mparts.append(pd.DataFrame(dict(building=bid, time=frame.index[valid],
                y=frame.y[valid].to_numpy(), site=sites[bid])))
        X = pd.concat(xparts, ignore_index=True)
        meta = pd.concat(mparts, ignore_index=True)
        y = meta.y.to_numpy()
        masks = partition(meta, PROTOCOL["fold_history_fractions"][fold])
        boundaries = {}
        for role, mask in masks.items():
            p = meta.loc[mask]
            boundaries[role] = dict(n=len(p), first_target=str(p.time.min()),
                last_target=str(p.time.max()), membership_sha256=hashlib.sha256(
                    p[["building", "time"]].to_csv(index=False).encode()).hexdigest())
        write_json(directory / "split.json", boundaries)
        models = []
        for q in PROTOCOL["quantile_levels"]:
            model = HistGradientBoostingRegressor(loss="quantile", quantile=q,
                random_state=seed, **PROTOCOL["hgb"])
            model.fit(X.loc[masks["fit"]], y[masks["fit"]])
            models.append(model)
        joblib.dump(models, directory / "models.joblib", compress=3)

        def predict(x):
            p = np.column_stack([model.predict(x) for model in models])
            p[:, 0], p[:, 2] = np.minimum(p[:, 0], p[:, 2]), np.maximum(p[:, 0], p[:, 2])
            return p

        predictions = {r: predict(X.loc[m]) for r, m in masks.items() if r != "fit"}
        cal_meta = meta.loc[masks["calibration"]].reset_index(drop=True)
        cal_y = y[masks["calibration"]]
        scales = seasonal_scales(cal_meta, cal_y - predictions["calibration"][:, 1])
        cal_scale = get_scales(cal_meta, scales)
        for role in ["calibration", "selection"]:
            audit_pred = meta.loc[masks[role], ["building", "time", "y"]].reset_index(drop=True)
            audit_pred[["raw_lower", "median", "raw_upper"]] = predictions[role]
            audit_pred["seasonal_scale"] = get_scales(audit_pred, scales)
            audit_pred.to_csv(directory / f"{role}_predictions.csv.gz", index=False)
        specs = candidates(predictions["calibration"], cal_y, cal_scale)
        selection_meta = meta.loc[masks["selection"]].reset_index(drop=True)
        selection_scale = get_scales(selection_meta, scales)
        selected, audit, unsupported = [], [], []
        for method in ["asymmetric_cqr", "symmetric_cqr", "scaled_quantile", "seasonal_residual"]:
            for budget in PROTOCOL["budgets"]:
                chosen, surface = choose(selection_meta, selection_meta.y.to_numpy(),
                    predictions["selection"], selection_scale,
                    [s for s in specs if s["method"] == method], budget)
                audit.extend(dict(**r, budget=budget) for r in surface)
                if chosen is None:
                    unsupported.append(dict(method=method, budget=budget,
                        reason="no selection candidate satisfies workload and active-time limits"))
                else:
                    selected.append(dict(**chosen, budget=budget))
        selected += [dict(method="raw_reference", budget=-1., threshold=0.),
            dict(**next(s for s in specs if s["method"] == "asymmetric_cqr" and s["level"] == .95), budget=-1.)]
        # Freeze selected settings before calculating any test alert performance.
        write_json(directory / "selected.json", selected)
        write_json(directory / "unsupported.json", unsupported)
        pd.DataFrame(audit).to_csv(directory / "selection_surface.csv.gz", index=False)
        test_meta = meta.loc[masks["test"]].reset_index(drop=True)
        test_y = test_meta.y.to_numpy()
        test_scale = get_scales(test_meta, scales)
        native = predictions["test"]
        original_stream = test_meta[["building", "time"]].copy()
        original_stream[["y", "raw_lower", "median", "raw_upper"]] = np.column_stack([test_y, native])
        original_stream.to_csv(directory / "clean_predictions.csv.gz", index=False)
        train_scales = {}
        for bid, p in meta.loc[masks["fit"]].groupby("building"):
            v = p.y.to_numpy()
            train_scales[bid] = max(float(1.4826 * np.median(np.abs(v - np.median(v)))), 1e-6)
        summaries, scored = [], []
        alias_checks = 0
        clean_flags = {}
        packed_flags = {}
        for k, spec in enumerate(selected):
            flags = numerical_flags(test_y, candidate_bounds(native, spec, test_scale))
            clean_flags[k] = flags
            packed_flags[f"clean_p{k}"] = np.packbits(flags)
            for bid, p in test_meta.groupby("building", sort=True):
                ix = p.index.to_numpy()
                rate, active = workload(p.reset_index(drop=True), flags[ix])
                summaries.append(dict(fold=fold, seed=seed, policy=k, method=spec["method"],
                    budget=spec["budget"], building=bid, site=sites[bid],
                    exposure_days=len(ix) / 24, background_episodes=int(starts(p.reset_index(drop=True), flags[ix]).sum()),
                    background_episodes_per_asset_day=rate, time_in_alert_fraction=active,
                    selection_workload=spec.get("selection_workload", np.nan)))
        write_json(directory / "pre_test_policy_hash.json", {"selected_sha256": digest(directory / "selected.json")})
        for cat_seed in PROTOCOL["event_catalogue_seeds"]:
            observed, events = inject(test_meta, test_y, train_scales, fold, cat_seed)
            events.to_csv(directory / f"catalogue_{cat_seed}.csv.gz", index=False)
            corrupt_parts = []
            for bid, f in frames.items():
                f = f.copy()
                p = test_meta[test_meta.building.eq(bid)]
                corrupt_y = f.y.copy()
                corrupt_y.loc[p.time] = observed[p.index]
                xx = features(f, corrupt_y.to_numpy()).loc[p.time]
                corrupt_parts.append(xx.reset_index(drop=True))
            corrupt_x = pd.concat(corrupt_parts, ignore_index=True)
            assert len(corrupt_x) == len(test_meta)
            corrupt_pred = predict(corrupt_x)
            for k, spec in enumerate(selected):
                numerical = numerical_flags(observed, candidate_bounds(corrupt_pred, spec, test_scale))
                if spec["method"] == "symmetric_cqr":
                    raw_score = np.maximum(corrupt_pred[:, 0] - observed,
                                           observed - corrupt_pred[:, 2])
                    np.testing.assert_array_equal(numerical,
                        np.isfinite(observed) & (raw_score > spec["threshold"]))
                    alias_checks += 1
                channels = dict(numerical=numerical, combined=numerical | ~np.isfinite(observed),
                                clean_window=clean_flags[k])
                for channel, flags in channels.items():
                    if channel != "clean_window":
                        packed_flags[f"c{cat_seed}_p{k}_{channel}"] = np.packbits(flags)
                    score = score_events(test_meta, flags, events, channel)
                    score = score.assign(fold=fold, seed=seed, policy=k,
                        method=spec["method"], budget=spec["budget"])
                    scored.append(score)
        pd.DataFrame(summaries).to_csv(directory / "workload.csv", index=False)
        np.savez_compressed(directory / "alert_flags.npz", **packed_flags)
        pd.concat(scored, ignore_index=True).to_csv(directory / "events.csv.gz", index=False)
        files = {p.name: digest(p) for p in directory.iterdir() if p.is_file() and p.name != "COMPLETE.json"}
        write_json(marker, dict(protocol_sha256=digest(HERE / "protocol.json"),
            code_sha256=digest(__file__), files=files, alias_checks=alias_checks,
            fitted_estimators=3, elapsed_seconds=time.monotonic() - started))
        print(f"Completed fold {fold}, seed {seed} in {time.monotonic()-started:.1f}s", flush=True)
    return str(directory)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    environment = dict(python=platform.python_version(), platform=platform.platform(),
        packages={p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scikit-learn", "scipy", "threadpoolctl"]},
        raw_sha256={n: digest(args.raw / n) for n in ["electricity.csv", "metadata.csv", "weather.csv"]},
        protocol_sha256=digest(HERE / "protocol.json"), code_sha256=digest(__file__))
    environment_file = args.out / "environment.json"
    if environment_file.exists() and json.loads(environment_file.read_text()) != environment:
        raise ValueError("environment or input bytes changed during resume")
    write_json(environment_file, environment)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(unit, args.raw, args.out, f, s)
                   for f in range(3) for s in PROTOCOL["seeds"]]
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
