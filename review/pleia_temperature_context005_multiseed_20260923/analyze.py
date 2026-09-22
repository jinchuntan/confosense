"""Prespecified five-seed temperature aggregation and original-context inference."""
from __future__ import annotations

import itertools
import os

for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import *
from src.conformal_quantile import _sub_estimators
from src.context005_metrics import inference
from src.intervals005_common import Operations, load_owner
from src.operational004_design import STRATA


CONTROLS = ["quantile_static", "cqr_static", "cqr_rolling", "persistence_static"]
RULES = ["single_sample", "30min_3of3", "60min_4of6", "180min_3of18", "360min_4of36"]
CHANNELS = ["numerical_only", "availability_only", "combined"]
KEYS = ["dataset", "outer_fold", "control_id", "rule_id", "channel", "context_id",
        "original_segment_id", "group_id", "family", "severity"]


def frame(path):
    try:
        return pd.read_csv(path, float_precision="round_trip",
                           dtype={"row_id": str, "context_id": str, "group_id": str,
                                  "original_segment_id": str, "segment_id": str})
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def validate_contribution_keys(data):
    full = KEYS + ["model_seed"]
    if data.duplicated(full).any():
        raise ValueError("duplicate model-seed contribution key")
    sets = data.groupby(KEYS, dropna=False).model_seed.agg(lambda values: tuple(sorted(values)))
    if not sets.map(lambda values: values == ALL_SEEDS).all():
        raise ValueError("model-seed completeness mismatch")
    invariant = data.groupby(KEYS, dropna=False).effective_slots.nunique()
    if not invariant.eq(1).all():
        raise ValueError("effective-slot support differs across seeds")
    return {"passed": True, "rows": len(data), "keys": len(sets), "seeds": list(ALL_SEEDS),
            "minimum_effective_slots": int(data.effective_slots.min()),
            "maximum_effective_slots": int(data.effective_slots.max())}


def weighted(part):
    n = part.n.sum()
    return pd.Series({"n": int(n), "unavailable_n": int(part.unavailable_n.sum()),
                      "coverage": float((part.coverage * part.n).sum() / n),
                      "mpiw": float((part.mpiw * part.n).sum() / n),
                      "winkler": float((part.winkler * part.n).sum() / n)})


def macro_from_contributions(contrib):
    seedavg = contrib.groupby(
        [key for key in KEYS if key not in ("dataset", "outer_fold", "original_segment_id", "group_id")]
        + ["original_segment_id", "group_id"], as_index=False, dropna=False
    ).agg(recall=("recall", "mean"), restricted_delay=("restricted_delay", "mean"),
          effective_slots=("effective_slots", "first"))
    strata = seedavg.groupby(["control_id", "rule_id", "channel", "family", "severity"], as_index=False).agg(
        recall=("recall", "mean"), restricted_ttd_minutes=("restricted_delay", "mean"),
        original_contexts=("context_id", "nunique"))
    rows = []
    for key, group in strata.groupby(["control_id", "rule_id", "channel"], sort=True):
        supported = len(group) == 21 and group.original_contexts.min() >= 5
        rows.append(dict(zip(("control_id", "rule_id", "channel"), key),
                         conditional_context_detection=float(group.recall.mean()) if supported else np.nan,
                         restricted_ttd_equal_stratum_minutes=float(group.restricted_ttd_minutes.mean()) if supported else np.nan,
                         supported_strata=int((group.original_contexts >= 5).sum()),
                         minimum_original_contexts=int(group.original_contexts.min()),
                         status="supported_point_estimate" if supported else "unavailable_support"))
    return seedavg, strata, pd.DataFrame(rows)


def estimator_states(seed):
    owner = load_owner(run(seed) / "stages" / "owner_fit_cqr" / "owner.pkl")
    estimators, _ = _sub_estimators(owner)
    return [item.get_params(deep=False)["random_state"] for item in estimators[:3]]


def seed_summary(seed):
    tables = run(seed) / "stages" / "tables"
    events = frame(tables / "events.csv.gz")
    strata = frame(tables / "strata.csv")
    macros = frame(tables / "conditional_macro.csv")
    workload = frame(tables / "fullstream_workload.csv")
    if (len(events), len(strata), len(macros), len(workload)) != (171360, 1260, 60, 60):
        raise ValueError(f"seed {seed} result shape mismatch")
    workagg = workload.groupby(["control_id", "rule_id", "channel"], as_index=False).agg(
        eligible_rows=("eligible_rows", "sum"), asset_days=("asset_days", "sum"),
        background_episodes=("episodes", "sum"), alert_rows=("alert_rows", "sum"),
        time_in_alert_days=("time_in_alert_days", "sum"))
    workagg["background_episodes_per_asset_day"] = workagg.background_episodes / workagg.asset_days
    workagg["fraction_time_in_alert"] = workagg.time_in_alert_days / workagg.asset_days
    rows = []
    for macro in macros.itertuples():
        ss = strata[(strata.control_id == macro.control_id) & (strata.rule_id == macro.rule_id) & (strata.channel == macro.channel)]
        ev = events[(events.control_id == macro.control_id) & (events.rule_id == macro.rule_id) & (events.channel == macro.channel)]
        eligible = ev[ev.effective & ev.eligible]; found = eligible[eligible.detected]
        work = workagg[(workagg.control_id == macro.control_id) & (workagg.rule_id == macro.rule_id) & (workagg.channel == macro.channel)].iloc[0]
        rows.append({"model_seed": seed, "control_id": macro.control_id, "rule_id": macro.rule_id,
                     "channel": macro.channel, "conditional_context_detection": macro.conditional_context_macro,
                     "restricted_ttd_equal_stratum_minutes": float(ss.restricted_mean_detection_minutes.mean()),
                     "detected": int(eligible.detected.sum()), "misses": int((~eligible.detected).sum()),
                     "detected_delay_median_minutes": float(found.delay_minutes.median()) if len(found) else np.nan,
                     "detected_delay_q90_minutes": float(found.delay_minutes.quantile(.9)) if len(found) else np.nan,
                     "supported_strata": int(macro.supported_strata), "original_eligible_rows": int(work.eligible_rows),
                     "original_asset_days": float(work.asset_days), "background_episodes": int(work.background_episodes),
                     "background_episodes_per_asset_day": float(work.background_episodes_per_asset_day),
                     "alert_rows": int(work.alert_rows), "time_in_alert_days": float(work.time_in_alert_days),
                     "fraction_time_in_alert": float(work.fraction_time_in_alert)})
    return pd.DataFrame(rows), events, strata, workload


def interval_rows(seed):
    root = run(seed); variants = frame(root / "stages" / "tables" / "variants.csv")
    cache = {}; rows = []
    for variant in variants.itertuples():
        if variant.canonical_stage not in cache:
            cache[variant.canonical_stage] = frame(root / "stages" / variant.canonical_stage / "interval_diagnostics.csv")
        for row in cache[variant.canonical_stage].to_dict("records"):
            rows.append({"model_seed": seed, "context_id": variant.context_id, "ordinal": variant.ordinal,
                         "family": variant.family, "severity": variant.severity, "effective": variant.effective,
                         "null": variant.null, "alias": variant.alias, "canonical_stage": variant.canonical_stage, **row})
    detail = pd.DataFrame(rows); output = []
    scopes = [("identity", detail.ordinal == 0), ("all_scheduled_fault_slots", detail.ordinal > 0),
              ("effective_fault_slots", (detail.ordinal > 0) & detail.effective)]
    for scope, mask in scopes:
        for key, group in detail[mask].groupby(["control_id", "target"]):
            output.append({"model_seed": seed, "scope": scope, "control_id": key[0], "target": key[1],
                           "streams": group[["context_id", "ordinal"]].drop_duplicates().shape[0], **weighted(group)})
    full = [frame(stage / "interval_diagnostics.csv") for stage in sorted((root / "stages").glob("fullstream_*"))]
    full = pd.concat(full, ignore_index=True)
    for key, group in full.groupby(["control_id", "target"]):
        output.append({"model_seed": seed, "scope": "fullstream_clean", "control_id": key[0],
                       "target": key[1], "streams": len(group), **weighted(group)})
    return pd.DataFrame(output)


def operation_row(seed):
    rows = [__import__("json").loads(line) for line in (run(seed) / "operations.jsonl").read_text(encoding="utf-8").splitlines()]
    returned = pd.DataFrame([row for row in rows if row.get("event") == "returned"])
    counts = returned.groupby("kind").size().to_dict()
    expected = {"calibrator_conformalize": 2, "cqr_wrapper_fit": 1, "quantile_estimator_fit": 3}
    if counts != expected:
        raise ValueError(f"seed {seed} operation mismatch: {counts}")
    states = estimator_states(seed)
    if states != [seed, seed, seed]:
        raise ValueError(f"seed {seed} native estimator mismatch: {states}")
    identity = read(run(seed) / "stages" / "controls" / "identity.json")
    return {"model_seed": seed, "cqr_wrapper_fit": 1, "quantile_estimator_fit": 3,
            "nested_calibrator_conformalize": 2, "logical_conformalizations": 1,
            "persistence_radius_computations": 1, "persistence_learned_fits": 0,
            "estimator_random_states": ";".join(map(str, states)), "owner_sha256": identity["owner_sha256"]}


def draw_estimates(pooled, contexts, draws):
    lookup = {context: index for index, context in enumerate(contexts.context_id)}; rows = []
    for key, part in pooled.groupby(["control_id", "rule_id", "channel"]):
        values = np.full((len(contexts), 21), np.nan)
        for row in part.itertuples():
            values[lookup[row.context_id], STRATA.index((row.family, row.severity))] = row.recall
        estimates = np.nanmean(values[draws], axis=1).mean(axis=1)
        rows.extend({"control_id": key[0], "rule_id": key[1], "channel": key[2],
                     "draw": index, "value": float(value)} for index, value in enumerate(estimates))
    return pd.DataFrame(rows)


def main():
    if ANALYSIS.exists():
        raise ValueError("preserve completed aggregate analysis")
    ANALYSIS.mkdir(parents=True)
    with Operations(forbid=True):
        baseline = read(REVIEW / "PRESERVATION_BASELINE.json")
        if source_digest() != SOURCE_HASH or digest(SEED42_RUN / "COMPLETE.json") != baseline["seed42_complete_sha256"]:
            raise ValueError("source or accepted seed 42 changed")
        summaries = []; events = []; strata = []; workloads = []; contributions = []; intervals = []; operations = []
        for seed in ALL_SEEDS:
            complete = read(run(seed) / "COMPLETE.json")
            if complete["actual_exit_status"] != 0:
                raise ValueError(f"seed {seed} incomplete")
            summary, event, stratum, workload = seed_summary(seed)
            summaries.append(summary); events.append(event.assign(model_seed=seed)); strata.append(stratum.assign(model_seed=seed))
            workloads.append(workload.assign(model_seed=seed))
            contributions.append(frame(run(seed) / "stages" / "tables" / "original_context_contributions.csv.gz"))
            intervals.append(interval_rows(seed)); operations.append(operation_row(seed))
        summaries = pd.concat(summaries, ignore_index=True); events = pd.concat(events, ignore_index=True)
        strata = pd.concat(strata, ignore_index=True); workloads = pd.concat(workloads, ignore_index=True)
        contributions = pd.concat(contributions, ignore_index=True); intervals = pd.concat(intervals, ignore_index=True)
        operations = pd.DataFrame(operations)
        if len(summaries) != 300 or len(events) != 856800:
            raise ValueError("five-seed result cardinality mismatch")
        keycheck = validate_contribution_keys(contributions)
        event_key = ["context_id", "family", "severity", "replicate", "slot_sign", "mask_seed", "control_id", "rule_id", "channel"]
        invariant = events.groupby(event_key, dropna=False).agg(seeds=("model_seed", "nunique"),
            effective=("effective", "nunique"), null=("null", "nunique"), alias=("alias", "nunique"), eligible=("eligible", "nunique"))
        if not (invariant.seeds.eq(5) & invariant[["effective", "null", "alias", "eligible"]].eq(1).all(axis=1)).all():
            raise ValueError("event support/null/alias/eligibility differs across seeds")
        contexts = frame(SEED42_DESIGN / "contexts.csv")
        bounds, drawmeta = inference(contributions, contexts, "pleia", expected_seeds=ALL_SEEDS)
        if drawmeta["status"] != "draws_generated" or len(drawmeta["draws"]) != 2000:
            raise ValueError("prespecified original-context draws unavailable")
        draws = np.asarray(drawmeta["draws"], dtype=int)
        seedavg, stratum_avg, macro = macro_from_contributions(contributions)
        comparison = macro.merge(bounds, on=["control_id", "rule_id", "channel"], suffixes=("", "_inference"), validate="one_to_one")
        seed_stats = summaries.groupby(["control_id", "rule_id", "channel"], as_index=False).agg(
            seed_mean_detection=("conditional_context_detection", "mean"), seed_sd_detection=("conditional_context_detection", "std"),
            seed_min_detection=("conditional_context_detection", "min"), seed_max_detection=("conditional_context_detection", "max"),
            mean_restricted_ttd_minutes=("restricted_ttd_equal_stratum_minutes", "mean"), mean_detected=("detected", "mean"),
            mean_misses=("misses", "mean"), mean_background_episodes_per_asset_day=("background_episodes_per_asset_day", "mean"),
            mean_fraction_time_in_alert=("fraction_time_in_alert", "mean"), mean_original_asset_days=("original_asset_days", "mean"))
        comparison = comparison.merge(seed_stats, on=["control_id", "rule_id", "channel"], validate="one_to_one")
        if not np.allclose(comparison.conditional_context_detection, comparison.seed_mean_detection, atol=1e-14):
            raise ValueError("seed pooling order disagreement")
        pooled = contributions.groupby(["context_id", "control_id", "rule_id", "channel", "family", "severity"], as_index=False).recall.mean()
        draw_values = draw_estimates(pooled, contexts, draws)
        contrasts = []
        for left, right in itertools.combinations(CONTROLS, 2):
            pivot = draw_values[draw_values.control_id.isin((left, right))].pivot(
                index=["rule_id", "channel", "draw"], columns="control_id", values="value").reset_index()
            pivot["difference"] = pivot[left] - pivot[right]
            for key, group in pivot.groupby(["rule_id", "channel"]):
                values = group.difference.to_numpy(); good = len(values) >= 1900 and np.ptp(values) > 0
                selected = comparison[(comparison.rule_id == key[0]) & (comparison.channel == key[1])]
                point = float(selected[selected.control_id == left].conditional_context_detection.iloc[0] - selected[selected.control_id == right].conditional_context_detection.iloc[0])
                contrasts.append({"control_a": left, "control_b": right, "definition": "A minus B", "rule_id": key[0],
                    "channel": key[1], "point_difference": point, "status": "supported" if good else "unavailable_valid_draw_or_degenerate",
                    "valid_draws": len(values), "lower": float(np.quantile(values, .025)) if good else np.nan,
                    "upper": float(np.quantile(values, .975)) if good else np.nan, "draw_hash": drawmeta["draw_hash"]})
        contrasts = pd.DataFrame(contrasts)
        interval_five = intervals.groupby(["scope", "control_id", "target"], as_index=False).agg(
            seeds=("model_seed", "nunique"), mean_streams=("streams", "mean"), total_n=("n", "sum"),
            total_unavailable_n=("unavailable_n", "sum"), mean_coverage=("coverage", "mean"),
            seed_sd_coverage=("coverage", "std"), mean_mpiw=("mpiw", "mean"), mean_winkler=("winkler", "mean"))
        csv(ANALYSIS / "per_seed_control_rule_channel.csv", summaries)
        csv(ANALYSIS / "five_seed_control_rule_channel.csv", comparison)
        csv(ANALYSIS / "per_seed_stratum_metrics.csv", strata)
        csv(ANALYSIS / "original_context_seed_contributions.csv.gz", contributions)
        csv(ANALYSIS / "original_context_seed_averages.csv.gz", seedavg)
        csv(ANALYSIS / "five_seed_stratum_averages.csv", stratum_avg)
        csv(ANALYSIS / "inference_bounds.csv", bounds)
        csv(ANALYSIS / "bootstrap_draw_estimates.csv.gz", draw_values)
        atomic(ANALYSIS / "bootstrap_design.json", drawmeta)
        csv(ANALYSIS / "paired_control_detection_contrasts.csv", contrasts)
        csv(ANALYSIS / "per_seed_background_workload.csv", workloads)
        csv(ANALYSIS / "per_seed_interval_diagnostics.csv", intervals)
        csv(ANALYSIS / "five_seed_interval_diagnostics.csv", interval_five)
        csv(ANALYSIS / "operation_reconciliation.csv", operations)
        progress = read(BATCH / "progress.json"); costs = []
        for seed in SEEDS:
            for action in ("freeze", "readiness", "run", "validate", "resume", "verify"):
                record = progress["tasks"][f"seed_{seed}/{action}"]
                resource = read(record["logger_receipt"])
                costs.append({"model_seed": seed, "action": action, "actual_exit_status": record["exit_code"],
                              "wall_seconds": record["seconds"], "cpu_seconds": resource.get("family_cpu_seconds"),
                              "peak_family_working_set_bytes": resource.get("peak_family_working_set_bytes"),
                              "minimum_disk_free_bytes": resource.get("minimum_disk_free_bytes"),
                              "started_utc": record["started_utc"], "ended_utc": record["ended_utc"],
                              "logger_receipt": record["logger_receipt"]})
        costs = pd.DataFrame(costs); csv(ANALYSIS / "worker_costs_and_resources.csv", costs)
        cost_summary = costs.groupby("action", as_index=False).agg(units=("model_seed", "size"),
            total_wall_seconds=("wall_seconds", "sum"), total_cpu_seconds=("cpu_seconds", "sum"),
            mean_wall_seconds=("wall_seconds", "mean"), maximum_peak_working_set_bytes=("peak_family_working_set_bytes", "max"),
            minimum_disk_free_bytes=("minimum_disk_free_bytes", "min"))
        csv(ANALYSIS / "worker_cost_summary.csv", cost_summary)
        plot = comparison[comparison.channel == "combined"].copy()
        figure, axes = plt.subplots(2, 2, figsize=(13, 8), sharey=True); colors = plt.cm.tab10(np.linspace(0, 1, 5))
        for axis, control in zip(axes.flat, CONTROLS):
            part = plot[plot.control_id == control].set_index("rule_id").loc[RULES].reset_index(); x = np.arange(5)
            axis.bar(x, part.conditional_context_detection, color=colors)
            axis.errorbar(x, part.conditional_context_detection,
                yerr=np.vstack([part.conditional_context_detection - part.lower, part.upper - part.conditional_context_detection]),
                fmt="none", ecolor="black", capsize=3)
            axis.set_title(control); axis.set_xticks(x, RULES, rotation=30, ha="right"); axis.set_ylim(0, 1); axis.grid(axis="y", alpha=.25)
        figure.supylabel("Conditional detection"); figure.suptitle("PLEIA temperature: five-seed mean and original-context block interval")
        figure.tight_layout(); figure.savefig(ANALYSIS / "five_seed_detection.png", dpi=170); figure.savefig(ANALYSIS / "five_seed_detection.pdf"); plt.close(figure)
        atomic(ANALYSIS / "five_seed_detection.sources.json", {"source_files": {name: digest(ANALYSIS / name) for name in
            ("five_seed_control_rule_channel.csv", "inference_bounds.csv")}, "draw_hash": drawmeta["draw_hash"]})
        newops = operations[operations.model_seed.isin(SEEDS)]
        result = {"passed": True, "utc": now(), "source_hash": source_digest(), "model_seeds": list(ALL_SEEDS),
                  "new_model_seeds": list(SEEDS), "seed42_reused_without_rerun": True, "contexts": 68,
                  "contexts_not_pseudoreplicated": 68, "schedules_per_seed": 2856, "event_records": len(events),
                  "seed_specific_macro_cells": len(summaries), "aggregate_cells": len(comparison),
                  "contribution_validation": keycheck, "event_support_invariant": True,
                  "inference_status_counts": bounds.status.value_counts().to_dict(), "draw_hash": drawmeta["draw_hash"], "draws": 2000,
                  "new_operation_totals": {column: int(newops[column].sum()) for column in
                    ("cqr_wrapper_fit", "quantile_estimator_fit", "nested_calibrator_conformalize",
                     "logical_conformalizations", "persistence_radius_computations", "persistence_learned_fits")},
                  "matched_forecasting_complete": 70, "interval_quality_complete": 250,
                  "seasonal_unique_complete": 9, "full_study_ready": False}
        atomic(ANALYSIS / "validation.json", result)
        print(__import__("json").dumps(result, indent=2))


if __name__ == "__main__":
    main()
