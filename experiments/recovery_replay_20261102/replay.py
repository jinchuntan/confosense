"""Attribute credited post-recovery onsets by removing one injected event at a time."""
import argparse
import importlib.util
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RELATIVE = np.arange(-1, 7)  # Include the hour before onset to reconstruct episode starts.


def load_runner(path):
    spec = importlib.util.spec_from_file_location("frozen_forecaster", path / "study.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepared_data(study, raw):
    frames, sites = study.read_data(raw)
    parts = []
    for building, frame in frames.items():
        valid = study.features(frame).notna().all(axis=1) & frame.y.notna()
        part = frame.loc[valid, ["y"]].copy()
        part["building"] = building
        part["time"] = part.index
        parts.append(part.reset_index(drop=True))
    return frames, sites, pd.concat(parts, ignore_index=True)


def ordered_predictions(models, features):
    lower, center, upper = (model.predict(features) for model in models)
    return np.column_stack([np.minimum(lower, upper), center, np.maximum(lower, upper)])


def paired_features(study, frames, meta, events, observed):
    # Replay the full original prefix. Rolling standard deviation can have
    # slightly different floating-point state when a long series is truncated.
    full_parts, restored_parts = [], []
    for building, group in events.groupby("building", sort=False):
        frame = frames[building]
        meter = frame.y.copy()
        supported = meta[meta.building.eq(building)]
        meter.loc[supported.time] = observed[supported.index]
        origins = frame.index.get_indexer(meta.time.iloc[group.start])
        if (origins < 1).any():
            raise ValueError("Missing pre-event observations")
        source = study.features(frame, meter.to_numpy())
        keep = (origins[:, None] + RELATIVE).ravel()
        full_parts.append(source.iloc[keep].reset_index(drop=True))
        for origin in origins:
            end = origin + 7
            repaired = meter.iloc[:end].copy()
            repaired.iloc[origin:origin + 4] = frame.y.iloc[origin:origin + 4].to_numpy()
            features = study.features(frame.iloc[:end], repaired.to_numpy())
            restored_parts.append(features.iloc[-8:].reset_index(drop=True))
    return pd.concat(full_parts, ignore_index=True), pd.concat(restored_parts, ignore_index=True)


def attribution(factual, restored, first_change, last_change):
    start = factual[:, 1:] & ~factual[:, :-1]
    cf_start = restored[:, 1:] & ~restored[:, :-1]
    hit = start.any(axis=1)
    when = start.argmax(axis=1)
    row = np.arange(len(hit))
    after = hit & (when > last_change)
    flag_removed = ~restored[row, when + 1]
    history_only = after & flag_removed
    return dict(events=np.ones(len(hit), dtype=int), hits=hit,
                before_first_change=hit & (when < first_change),
                during_change_span=hit & (when >= first_change) & (when <= last_change),
                after_last_change=after, after_slot=hit & (when > 3),
                history_only=history_only,
                history_only_after_slot=history_only & (when > 3),
                history_only_no_cf_hit=history_only & ~cf_start.any(axis=1),
                post_existing_flag=after & ~flag_removed)


def write_example(path, events, measures, indices, meta, values, original,
                  factual_bounds, restored_bounds, factual_flags, restored_flags):
    # Illustrate the first qualifying non-missing event in the sorted catalogue.
    eligible = measures["history_only"] & ~events.family.isin(["random_missing", "block_missing"])
    if not eligible.any():
        return False
    i = np.flatnonzero(eligible)[0]
    event = events.iloc[i]
    shape = values.shape
    fl, fu = (v.reshape(shape)[i] for v in factual_bounds)
    rl, ru = (v.reshape(shape)[i] for v in restored_bounds)
    trace = pd.DataFrame(dict(event_id=event.event_id, family=event.family,
        time=meta.time.iloc[indices[i]].to_numpy(), offset_hour=RELATIVE,
        original=original[i], observed=values[i], factual_lower=fl, factual_upper=fu,
        restored_lower=rl, restored_upper=ru, factual_flag=factual_flags[i],
        restored_flag=restored_flags[i]))
    trace.to_csv(path, index=False)
    return True


def run(study, raw, runs, label, example=None):
    env = json.loads((runs / "environment.json").read_text())
    assert study.digest(study.HERE / "study.py") == env["code_sha256"]
    assert study.digest(study.HERE / "protocol.json") == env["protocol_sha256"]
    for filename, expected in env["raw_sha256"].items():
        assert study.digest(raw / filename) == expected
    frames, sites, all_meta = prepared_data(study, raw)
    totals = []
    for fold, history in enumerate(study.PROTOCOL["fold_history_fractions"]):
        directory = runs / f"f{fold}_s42"
        receipt = json.loads((directory / "COMPLETE.json").read_text())
        assert receipt["code_sha256"] == env["code_sha256"]
        assert receipt["protocol_sha256"] == env["protocol_sha256"]
        for filename, expected in receipt["files"].items():
            assert study.digest(directory / filename) == expected
        models = joblib.load(directory / "models.joblib")
        policies = json.loads((directory / "selected.json").read_text())
        split = study.partition(all_meta, history)
        fit = all_meta.loc[split["fit"]]
        scales = {name: max(float(1.4826 * (p.y - p.y.median()).abs().median()), 1e-6)
                  for name, p in fit.groupby("building")}
        meta = all_meta.loc[split["test"]].reset_index(drop=True)
        clean = pd.read_csv(directory / "clean_predictions.csv.gz", parse_dates=["time"])
        pd.testing.assert_frame_equal(clean[["building", "time"]], meta[["building", "time"]])
        np.testing.assert_allclose(clean.y, meta.y)
        cal = pd.read_csv(directory / "calibration_predictions.csv.gz", parse_dates=["time"], float_precision="round_trip")
        seasonal = study.get_scales(meta, study.seasonal_scales(cal, cal.y - cal["median"]))
        with np.load(directory / "alert_flags.npz") as saved:
            for seed in study.PROTOCOL["event_catalogue_seeds"]:
                observed, catalogue = study.inject(meta, meta.y.to_numpy(), scales, fold, seed)
                stored = pd.read_csv(directory / f"catalogue_{seed}.csv.gz")
                pd.testing.assert_frame_equal(catalogue, stored, check_dtype=False)
                events = catalogue[catalogue.effective].sort_values(["building","start"]).reset_index(drop=True)
                indices = events.start.to_numpy()[:, None] + RELATIVE
                values = observed[indices]
                original = meta.y.to_numpy()[indices]
                changed = values[:, 1:5] != original[:, 1:5]
                assert changed.any(axis=1).all()
                np.testing.assert_array_equal(values[:, [0,5,6,7]], original[:, [0,5,6,7]])
                first = changed.argmax(axis=1)
                last = 3 - changed[:, ::-1].argmax(axis=1)
                xf, xr = paired_features(study, frames, meta, events, observed)
                pf, pr = ordered_predictions(models, xf), ordered_predictions(models, xr)
                scale = seasonal[indices].ravel()
                for k, policy in enumerate(policies):
                    if policy["budget"] < 0:
                        continue
                    shape = values.shape
                    factual_bounds = study.candidate_bounds(pf, policy, scale)
                    restored_bounds = study.candidate_bounds(pr, policy, scale)
                    f = study.numerical_flags(values.ravel(), factual_bounds).reshape(shape)
                    r = study.numerical_flags(original.ravel(), restored_bounds).reshape(shape)
                    for channel in ("numerical", "combined"):
                        factual = f if channel == "numerical" else f | ~np.isfinite(values)
                        key = f"c{seed}_p{k}_{channel}"
                        np.testing.assert_array_equal(factual, np.unpackbits(saved[key])[indices].astype(bool))
                        pre = RELATIVE < first[:,None]
                        np.testing.assert_array_equal(factual[pre], r[pre])
                        measures = attribution(factual, r, first, last)
                        assert np.all(measures["hits"] == (measures["before_first_change"].astype(int)
                                      + measures["during_change_span"] + measures["after_last_change"]))
                        if (example is not None and channel == "numerical"
                                and policy["method"] == "asymmetric_cqr" and policy["budget"] == .5):
                            if write_example(example, events, measures, indices, meta, values, original,
                                             factual_bounds, restored_bounds, factual, r):
                                example = None
                        data = events[["building","family","severity"]].assign(**measures)
                        strata = data.groupby(["building","family","severity"]).sum().reset_index()
                        totals.append(strata.assign(cohort=label, fold=fold, catalogue=seed,
                            site=strata.building.map(sites), method=policy["method"],
                            channel=channel, budget=policy["budget"]))
        print(f"Verified factual replay and event restoration for {label} fold {fold}", flush=True)
    return pd.concat(totals, ignore_index=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("raw", type=Path)
    cli.add_argument("runner", type=Path)
    cli.add_argument("runs", type=Path)
    cli.add_argument("cohort")
    cli.add_argument("output", type=Path)
    cli.add_argument("--example", type=Path, help="Write one deterministic non-missing illustration")
    args = cli.parse_args()
    counts = run(load_runner(args.runner), args.raw, args.runs, args.cohort, args.example)
    counts.to_csv(args.output, index=False)
