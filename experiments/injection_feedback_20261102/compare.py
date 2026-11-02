"""Compare two injection protocols and a forecaster with delayed meter inputs."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "recovery_replay_20261102"))
from replay import RELATIVE, load_runner, ordered_predictions, prepared_data

STATES = ["miss", "before", "during", "after"]
PRED = ["raw_lower", "median", "raw_upper"]


def first_state(flags, ix, changed):
    local = flags[ix]
    onsets = local[:, 1:] & ~local[:, :-1]
    first = onsets.argmax(axis=1)
    begin = changed.argmax(axis=1)
    end = 3 - changed[:, ::-1].argmax(axis=1)
    return np.select([~onsets.any(axis=1), first < begin, first <= end], [0, 1, 2], default=3)


def delayed_features(study, frame, meter=None):
    x = study.features(frame, meter)
    delayed = [k for k in x if k.startswith(("lag_", "mean_", "std_")) or k == "target_was_missing"]
    x[delayed] = x[delayed].shift(4)
    return x


def delayed_input(study, frames, meta, values=None):
    parts = []
    for building, rows in meta.groupby("building", sort=False):
        f = frames[building]
        meter = f.y.copy()
        if values is not None:
            meter.loc[rows.time] = values[rows.index]
        parts.append(delayed_features(study, f, meter.to_numpy()).loc[rows.time])
    return pd.concat(parts, ignore_index=True)


def delayed_model(study, features, meta, masks):
    models = []
    for q in study.PROTOCOL["quantile_levels"]:
        model = HistGradientBoostingRegressor(loss="quantile", quantile=q, random_state=42,
                                              **study.PROTOCOL["hgb"])
        model.fit(features[masks["fit"]], meta.y[masks["fit"]])
        models.append(model)
    pred = {r: ordered_predictions(models, features[m]) for r, m in masks.items() if r != "fit"}
    calibration = meta[masks["calibration"]].reset_index(drop=True)
    selection = meta[masks["selection"]].reset_index(drop=True)
    # Separate-tail CQR uses no seasonal scale.
    p = pred["calibration"]
    levels = study.PROTOCOL["coverage_grid"]
    specs = [dict(method="asymmetric_cqr", level=level,
                  lower_correction=study.conformal_quantile(p[:, 0] - calibration.y, (1+level)/2),
                  upper_correction=study.conformal_quantile(calibration.y - p[:, 2], (1+level)/2))
             for level in levels]
    policy, _ = study.choose(selection, selection.y.to_numpy(), pred["selection"], None, specs, .5)
    if policy is None:
        raise ValueError("No feasible delayed CQR policy at the frozen budget")
    return models, policy, pred["test"]


def transitions(catalogue, left, right, sites):
    event = catalogue[["building", "family", "severity"]].copy()
    event["site"] = event.building.map(sites)
    event["from_state"] = np.take(STATES, left)
    event["to_state"] = np.take(STATES, right)
    return event.value_counts(sort=False).rename("count").reset_index()


def align_inputs(study, raw, runs, fold):
    env = json.loads((runs / "environment.json").read_text())
    directory = runs / f"f{fold}_s42"
    receipt = json.loads((directory / "COMPLETE.json").read_text())
    for name, key in [("study.py", "code_sha256"), ("protocol.json", "protocol_sha256")]:
        assert study.digest(study.HERE / name) == env[key] == receipt[key]
    for name, sha in env["raw_sha256"].items():
        assert study.digest(raw / name) == sha
    for name, sha in receipt["files"].items():
        assert study.digest(directory / name) == sha
    frames, sites, all_meta = prepared_data(study, raw)
    masks = study.partition(all_meta, study.PROTOCOL["fold_history_fractions"][fold])
    split = json.loads((directory / "split.json").read_text())
    for role, m in masks.items():
        membership = all_meta.loc[m, ["building", "time"]].to_csv(index=False).encode()
        assert hashlib.sha256(membership).hexdigest() == split[role]["membership_sha256"]
    return directory, frames, sites, all_meta, masks


def run(args):
    study = load_runner(args.runner)
    directory, frames, sites, all_meta, masks = align_inputs(study, args.raw, args.runs, args.fold)
    test = all_meta[masks["test"]].reset_index(drop=True)
    y = test.y.to_numpy()
    clean = pd.read_csv(directory / "clean_predictions.csv.gz", parse_dates=["time"],
                        float_precision="round_trip")
    pd.testing.assert_frame_equal(clean[["building", "time", "y"]], test[["building", "time", "y"]])
    clean_pred = clean[PRED].to_numpy()
    cal = pd.read_csv(directory / "calibration_predictions.csv.gz", parse_dates=["time"],
                      float_precision="round_trip")
    seasonal = study.get_scales(test, study.seasonal_scales(cal, cal.y - cal["median"]))
    policies = json.loads((directory / "selected.json").read_text())
    primary = next(i for i,p in enumerate(policies) if p["method"]=="asymmetric_cqr" and p["budget"]==.5)
    fitting = all_meta[masks["fit"]]
    scales = {b:max(float(1.4826*(g.y-g.y.median()).abs().median()),1e-6)
              for b,g in fitting.groupby("building")}
    if args.arm == "delay":
        models, delayed_policy, delayed_test = delayed_model(
            study, delayed_input(study, frames, all_meta), all_meta, masks)
        clean_flags = study.numerical_flags(y, study.candidate_bounds(delayed_test, delayed_policy, None))
        rate, active = study.workload(test, clean_flags)
        selection = dict(policy=delayed_policy, test_rows=len(y), background_episodes=int(study.starts(test,clean_flags).sum()),
                         background_rate=rate, time_in_alert=active)
        study.write_json(args.output / f"{args.cohort}_f{args.fold}_delay_policy.json", selection)
    else:
        # Reconstruct the unmodified stream and check emitted episodes by building and policy.
        workload = pd.read_csv(directory / "workload.csv")
        for i, p in enumerate(policies):
            flag = study.numerical_flags(y, study.candidate_bounds(clean_pred, p, seasonal))
            counts = test.assign(starts=study.starts(test,flag)).groupby("building").starts.sum().sort_index()
            saved = workload[workload.policy.eq(i)].set_index("building").background_episodes.sort_index()
            np.testing.assert_array_equal(counts, saved)
    tables = []
    with np.load(directory / "alert_flags.npz") as saved:
        for seed in study.PROTOCOL["event_catalogue_seeds"]:
            observed, cat = study.inject(test, y, scales, args.fold, seed)
            pd.testing.assert_frame_equal(cat, pd.read_csv(directory / f"catalogue_{seed}.csv.gz"), check_dtype=False)
            events = cat[cat.effective].sort_values(["building","start"]).reset_index(drop=True)
            ix = events.start.to_numpy()[:, None] + RELATIVE
            changed = observed[ix[:,1:5]] != y[ix[:,1:5]]
            assert changed.any(axis=1).all()
            if args.arm == "delay":
                forecast = ordered_predictions(models, delayed_input(study, frames, test, observed))
                lower, upper = study.candidate_bounds(forecast, delayed_policy, None)
                delayed = study.numerical_flags(observed, (lower, upper))
            for i, policy in enumerate(policies):
                if policy["budget"] < 0 or (args.arm == "delay" and i != primary):
                    continue
                if args.arm == "placement":
                    detached = study.numerical_flags(observed, study.candidate_bounds(clean_pred, policy, seasonal))
                for channel in ["numerical", "combined"]:
                    live = np.unpackbits(saved[f"c{seed}_p{i}_{channel}"])[:len(test)].astype(bool)
                    alt = delayed if args.arm == "delay" else detached
                    if channel == "combined":
                        alt = alt | ~np.isfinite(observed)
                    # Direction is always archived live detector -> new protocol or policy.
                    a, b = first_state(live, ix, changed), first_state(alt, ix, changed)
                    counts = transitions(events, a, b, sites)
                    tables.append(counts.assign(catalogue=seed, method=policy["method"],
                                                budget=policy["budget"], channel=channel))
    all_counts = pd.concat(tables,ignore_index=True).assign(cohort=args.cohort,fold=args.fold,arm=args.arm)
    all_counts.to_csv(args.output / f"{args.cohort}_f{args.fold}_{args.arm}.csv.gz",index=False)
    print(f"Completed {args.cohort} fold {args.fold} {args.arm}", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for n in ["raw", "runner", "runs", "output"]:
        p.add_argument(n,type=Path)
    p.add_argument("cohort")
    p.add_argument("fold",type=int,choices=[0,1,2])
    p.add_argument("arm",choices=["placement","delay"])
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    with threadpool_limits(limits=1):
        run(args)
