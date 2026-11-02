"""Independently audit saved flags and produce building-balanced comparisons."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def episode_starts(meta, flags):
    # This implementation is separate from study.starts.
    t = pd.to_datetime(meta.time).to_numpy(dtype="datetime64[ns]")
    b = meta.building.to_numpy()
    onsets = np.zeros(len(meta), bool)
    for i in range(len(meta)):
        new_segment = i == 0 or b[i] != b[i - 1] or t[i] - t[i - 1] != np.timedelta64(1, "h")
        onsets[i] = flags[i] and (new_segment or not flags[i - 1])
    return onsets


def validate(directory, protocol_hash, source_hash):
    marker = json.loads((directory / "COMPLETE.json").read_text())
    assert marker["protocol_sha256"] == protocol_hash
    assert marker["code_sha256"] == source_hash
    for name, expected in marker["files"].items():
        assert digest(directory / name) == expected, (directory, name)
    pred = pd.read_csv(directory / "clean_predictions.csv.gz")
    policies = json.loads((directory / "selected.json").read_text())
    assert digest(directory / "selected.json") == json.loads((directory / "pre_test_policy_hash.json").read_text())["selected_sha256"]
    flags = np.load(directory / "alert_flags.npz")
    workload = pd.read_csv(directory / "workload.csv")
    events = pd.read_csv(directory / "events.csv.gz")
    checks = 0
    cached_starts = {}
    for k, policy in enumerate(policies):
        clean = np.unpackbits(flags[f"clean_p{k}"])[:len(pred)].astype(bool)
        onsets = episode_starts(pred, clean)
        for row in workload[workload.policy.eq(k)].itertuples():
            mask = pred.building.eq(row.building).to_numpy()
            assert onsets[mask].sum() == row.background_episodes
            assert abs(clean[mask].mean() - row.time_in_alert_fraction) < 1e-12
            assert abs(mask.sum() / 24 - row.exposure_days) < 1e-10
            checks += 1
    # Event windows are disjoint; new-onset matching is independently reconstructed
    # from saved emitted flags, not from reported detection labels.
    for (policy, cat, channel), part in events.groupby(["policy", "catalogue_seed", "channel"]):
        key = f"clean_p{policy}" if channel == "clean_window" else f"c{cat}_p{policy}_{channel}"
        if key not in cached_starts:
            cached_starts[key] = episode_starts(pred,
                np.unpackbits(flags[key])[:len(pred)].astype(bool))
        onsets = cached_starts[key]
        used = set()
        for row in part.sort_values(["building", "start"]).itertuples():
            possibilities = [int(i) for i in np.flatnonzero(onsets[row.start:row.tolerance_end + 1]) + row.start if int(i) not in used]
            hit = bool(possibilities)
            if hit:
                used.add(possibilities[0])
            delay = (pd.Timestamp(pred.iloc[possibilities[0]].time) - pd.Timestamp(row.onset)).total_seconds() / 60 if hit else 360.
            assert hit == row.detected, (directory, row.event_id, channel)
            assert delay == row.restricted_delay_minutes
            checks += 1
    # Check all calibration/selection predictions precede the test origins.
    splits = json.loads((directory / "split.json").read_text())
    names = ["fit", "calibration", "selection", "test"]
    for left, right in zip(names, names[1:]):
        assert pd.Timestamp(splits[left]["last_target"]) < pd.Timestamp(splits[right]["first_target"]) - pd.Timedelta(hours=1)
    return workload, events, checks


def summarize(results):
    here = Path(__file__).parent
    protocol = json.loads((here / "protocol.json").read_text())
    env = json.loads((results / "environment.json").read_text())
    directories = [results / f"f{f}_s{s}" for f in range(3) for s in protocol["seeds"]]
    workloads, event_tables = [], []
    checks = 0
    for directory in directories:
        w, e, n = validate(directory, env["protocol_sha256"], env["code_sha256"])
        workloads.append(w)
        event_tables.append(e)
        checks += n
    w = pd.concat(workloads, ignore_index=True)
    e = pd.concat(event_tables, ignore_index=True)
    keys = ["fold", "seed", "method", "budget", "building", "channel", "family", "severity"]
    strata = e.groupby(keys).agg(n_events=("detected", "size"),
        n_detected=("detected", "sum"), restricted_delay_minutes=("restricted_delay_minutes", "mean")).reset_index()
    strata["recall"] = strata.n_detected / strata.n_events
    strata["observed_strata"] = 1
    metrics = strata.groupby(keys[:6]).agg(macro_recall=("recall", "mean"),
        observed_strata=("observed_strata", "sum")).reset_index()
    delays = e.groupby(keys[:6]).restricted_delay_minutes.mean().rename("restricted_delay_minutes").reset_index()
    metrics = metrics.merge(delays, on=keys[:6], validate="one_to_one")
    numerical = metrics[metrics.channel.eq("numerical")].copy()
    # Average seeds within each fold, and then equally average the three periods.
    building_keys = ["method", "budget", "building", "channel"]
    by_fold = metrics.groupby(building_keys + ["fold"])[["macro_recall", "restricted_delay_minutes", "observed_strata"]].mean().reset_index()
    by_building = by_fold.groupby(building_keys)[["macro_recall", "restricted_delay_minutes", "observed_strata"]].mean().reset_index()
    bw = w.groupby(["method", "budget", "building", "site", "fold"])[["background_episodes_per_asset_day", "time_in_alert_fraction", "selection_workload"]].mean().reset_index()
    bw = bw.groupby(["method", "budget", "building", "site"])[["background_episodes_per_asset_day", "time_in_alert_fraction", "selection_workload"]].mean().reset_index()
    by_building = by_building.merge(bw, on=["method", "budget", "building"], validate="many_to_one")
    by_building.to_csv(results / "by_building.csv", index=False)
    summary = by_building.groupby(["method", "budget", "channel"])[[
        "macro_recall", "restricted_delay_minutes", "background_episodes_per_asset_day",
        "time_in_alert_fraction", "selection_workload", "observed_strata"]].mean().reset_index()
    summary.to_csv(results / "summary.csv", index=False)
    strata.groupby(["method", "budget", "channel", "family", "severity"])[["recall", "restricted_delay_minutes"]].mean().reset_index().to_csv(results / "by_disturbance.csv", index=False)
    strata.to_csv(results / "stratum_counts.csv.gz", index=False)
    # Paired site-cluster intervals; model seeds/catalogues are not new assets.
    rng = np.random.default_rng(protocol["bootstrap"]["seed"])
    differences = []
    for budget in protocol["budgets"]:
        for channel in ["combined", "numerical", "clean_window"]:
            reference = by_building[(by_building.method == "seasonal_residual") & (by_building.budget == budget) & (by_building.channel == channel)]
            for method in ["asymmetric_cqr", "symmetric_cqr", "scaled_quantile"]:
                treatment = by_building[(by_building.method == method) & (by_building.budget == budget) & (by_building.channel == channel)]
                pair = treatment.merge(reference, on=["building", "site"], suffixes=("_a", "_b"), validate="one_to_one")
                if len(pair) != len(protocol["buildings"]):
                    continue
                sites = sorted(pair.site.unique())
                draws = rng.integers(len(sites), size=(protocol["bootstrap"]["replicates"], len(sites)))
                for metric in ["macro_recall", "restricted_delay_minutes", "background_episodes_per_asset_day"]:
                    delta = pair[metric + "_a"] - pair[metric + "_b"]
                    sums = np.array([delta[pair.site.eq(site)].sum() for site in sites])
                    counts = np.array([pair.site.eq(site).sum() for site in sites])
                    sample = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
                    differences.append(dict(method=method, reference="seasonal_residual", budget=budget,
                        channel=channel, metric=metric, mean_difference=float(delta.mean()),
                        lower_95=float(np.quantile(sample, .025)), upper_95=float(np.quantile(sample, .975)),
                        n_sites=len(sites), n_buildings=len(pair)))
    pd.DataFrame(differences).to_csv(results / "paired_site_intervals.csv", index=False)
    json_out = dict(completed_units=len(directories), independent_flag_and_match_checks=checks,
        minimum_observed_strata=int(metrics.observed_strata.min()),
        conformal_score_equivalence_checks=sum(json.loads((d / "COMPLETE.json").read_text())["alias_checks"] for d in directories),
        source_sha256=env["code_sha256"], protocol_sha256=env["protocol_sha256"],
        interpretation="Retrospective descriptive comparison. Six observed sites; intervals condition on fitted models and do not establish population generalisation or noninferiority.")
    (results / "VALIDATION.json").write_text(json.dumps(json_out, indent=2) + "\n")
    print(json.dumps(json_out, indent=2))
    print(summary[summary.channel.eq("combined")].to_string(index=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("results", type=Path)
    summarize(p.parse_args().results)
