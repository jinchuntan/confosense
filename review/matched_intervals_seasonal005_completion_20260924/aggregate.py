"""No-fit cumulative analysis of the 250 accepted and 1,700 new method cells."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from adapter import (HERE, REPO, SMART, SOURCE_HASH, accepted_evidence,
                     bundle_paths, digest, frozen, read, source_digest)
from src.intervals005_common import Operations, atomic

OUTPUT = SMART / "outputs/matched_intervals005/completion_52_v1_analysis"
COORDINATOR = SMART / "outputs/matched_intervals005/completion_52_v1_coordinator"
RANK_RECOVERY = COORDINATOR / "rank_recovery_v1"
UNITS = {"bdg2": "kWh", "pleia": "°C", "pleia_energy": "kWh", "rico": "°C"}


def accepted_run(dataset: str, fold: int, seed: int) -> Path:
    if dataset == "bdg2":
        name = "bdg2_f2_s42_v1" if seed == 42 else f"bdg2_f2_s{seed}_v2"
    else:
        name = f"{dataset}_f2_s42_v{'2' if dataset == 'pleia_energy' else '1'}"
    return SMART / "outputs/matched_intervals005" / name


def rows_for_run(run: Path, provenance: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tables = run / "stages/tables"
    native = pd.read_csv(tables / "native_support_metrics.csv")
    common = pd.read_csv(tables / "common_support_metrics.csv")
    seasonal_point = pd.read_csv(tables / "seasonal_point_metrics.csv")
    seasonal_interval = pd.read_csv(tables / "seasonal_interval_metrics.csv")
    for part in (native, common, seasonal_point, seasonal_interval):
        part["provenance"] = provenance
        part["run"] = str(run.relative_to(REPO)).replace("\\", "/")
    return native, common, seasonal_point, seasonal_interval


def new_receipts(name: str) -> tuple[Path, Path]:
    """Resolve standard receipts or the separately versioned seed-46 recovery."""
    candidates = (
        (COORDINATOR / "validation" / name, COORDINATOR / "resumes" / f"{name}.json"),
        (RANK_RECOVERY / "corrected_validation" / name,
         RANK_RECOVERY / "resumes" / f"{name}.json"),
    )
    present = [(validation, resume) for validation, resume in candidates
               if (validation / "validation.json").is_file() and resume.is_file()]
    if len(present) != 1:
        raise ValueError(f"missing or ambiguous validation/resume evidence: {name}")
    return present[0]


def verify_new(dataset: str, fold: int, seed: int) -> Path:
    design, run = bundle_paths(dataset, fold, seed)
    name = f"{dataset}_f{fold}_s{seed}"
    p = read(design / "frozen_protocol.json")
    validation, resume = new_receipts(name)
    v = read(validation / "validation.json")
    r = read(resume)
    marker = read(run / "COMPLETE.json")
    expected = 40 if dataset == "rico" else 30
    if (p["source_hash"] != SOURCE_HASH or marker["method_cells"] != expected or
        not v["passed"] or v["method_cells"] != expected or
        v["models_fitted"] or v["calibrators_fitted"] or
        not v["source_artifacts_unchanged"] or
        r["models_fitted"] or r["calibrators_fitted"] or
        not r["all_run_files_unchanged"]):
        raise ValueError(f"new bundle not fully accepted: {name}")
    counts = read(run / "stages/tables/operation_counts.json")
    if any(counts.get(key, 0) != value for key, value in p["expected_operations"].items()):
        raise ValueError(f"operation budget mismatch: {name}")
    return run


def unique_keys(frame: pd.DataFrame, keys: list[str], expected: int) -> None:
    if len(frame) != expected or frame.duplicated(keys).any():
        raise ValueError(f"wrong row count or duplicate key: {keys}, {len(frame)} != {expected}")


def aggregate() -> None:
    if source_digest() != SOURCE_HASH:
        raise ValueError("scientific source changed")
    accepted_evidence()
    if OUTPUT.exists():
        raise ValueError("analysis output already exists; preserve it")
    scope = pd.read_csv(HERE / "remaining_scope.csv")
    accepted = [("bdg2", 2, seed) for seed in range(42, 47)] + [
        (dataset, 2, 42) for dataset in ("pleia", "pleia_energy", "rico")]
    new = [(str(x.dataset), int(x.outer_fold), int(x.model_seed)) for x in scope.itertuples(index=False)]
    if len(new) != 52 or len(set(new)) != 52 or len(accepted) != 8:
        raise ValueError("bundle scope changed")
    parts = {name: [] for name in ("native", "common", "seasonal_point", "seasonal_interval")}
    workload_parts = []
    operation_sum = {key: 0 for key in read(HERE / "AUTHORIZATION.json")["fit_ceiling"]}
    progress = read(COORDINATOR / "progress.json")
    costs = []
    for dataset, fold, seed in accepted + new:
        run = (accepted_run(dataset, fold, seed) if (dataset, fold, seed) in accepted
               else verify_new(dataset, fold, seed))
        provenance = "accepted_prior" if (dataset, fold, seed) in accepted else "new_validated"
        for name, part in zip(parts, rows_for_run(run, provenance)):
            parts[name].append(part)
        workload = pd.read_csv(run / "stages/tables/background_workload.csv")
        workload = workload[workload.group_id == "__pooled__"].copy()
        workload.insert(0, "dataset", dataset)
        workload.insert(1, "outer_fold", fold)
        workload.insert(2, "model_seed", seed)
        workload["provenance"] = provenance
        workload_parts.append(workload)
        if provenance == "new_validated":
            counts = read(run / "stages/tables/operation_counts.json")
            for key in operation_sum:
                operation_sum[key] += counts.get(key, 0)
            name = f"{dataset}_f{fold}_s{seed}"
            stage_cost = pd.read_csv(run / "stages/tables/stage_costs.csv")
            validation_dir, resume_path = new_receipts(name)
            validation = read(validation_dir / "validation.json")
            tasks = progress["tasks"]
            resume_task = tasks.get(f"{name}/completed_resume", {})
            costs.append(dict(dataset=dataset, outer_fold=fold, model_seed=seed,
                              run_wall_seconds=tasks[f"{name}/run"]["seconds"],
                              validation_wall_seconds=validation["resources"]["seconds"],
                              resume_wall_seconds=resume_task.get("seconds", np.nan),
                              resume_wall_seconds_recorded="seconds" in resume_task,
                              validation_receipt=validation_dir.relative_to(REPO).as_posix(),
                              resume_receipt=resume_path.relative_to(REPO).as_posix(),
                              run_stage_cpu_seconds=stage_cost.process_cpu_seconds.sum(),
                              validation_cpu_seconds=validation["resources"]["process_cpu_seconds"],
                              run_peak_rss_bytes=stage_cost.lifetime_peak_rss_bytes.max(),
                              validation_peak_rss_bytes=validation["resources"]["lifetime_peak_rss_bytes"]))
    ceiling = read(HERE / "AUTHORIZATION.json")["fit_ceiling"]
    if operation_sum != ceiling:
        raise ValueError(f"cumulative operation totals differ: {operation_sum} != {ceiling}")
    tables = {name: pd.concat(chunks, ignore_index=True) for name, chunks in parts.items()}
    keys = ["dataset", "outer_fold", "model_seed", "horizon", "level", "method"]
    for view in ("native", "common"):
        unique_keys(tables[view], keys, 1950)
        if set(tables[view].provenance.value_counts().to_dict().items()) != {
            ("accepted_prior", 250), ("new_validated", 1700)}:
            raise ValueError("accepted/new cell provenance mismatch")
    point = tables["seasonal_point"]
    interval = tables["seasonal_interval"]
    unique_keys(point, ["dataset", "outer_fold", "model_seed", "horizon"], 135)
    unique_keys(interval, keys, 270)
    if set(point.dataset) != {"bdg2", "pleia", "pleia_energy"}:
        raise ValueError("RICO seasonal must be inapplicable")
    for (dataset, fold, horizon), group in point.groupby(["dataset", "outer_fold", "horizon"]):
        if len(group) != 5 or set(group.model_seed) != set(range(42, 47)):
            raise ValueError("missing seasonal aliases")
        for metric in ("n", "mae", "rmse"):
            if not np.allclose(group[metric], group.iloc[0][metric], rtol=0, atol=1e-10):
                raise ValueError(f"seed alias changed seasonal point metric: {dataset}/{fold}/{horizon}")
    for (dataset, fold, horizon, level), group in interval.groupby(["dataset", "outer_fold", "horizon", "level"]):
        if len(group) != 5 or set(group.model_seed) != set(range(42, 47)):
            raise ValueError("missing seasonal interval aliases")
        for metric in ("n", "coverage", "mpiw", "winkler"):
            if not np.allclose(group[metric], group.iloc[0][metric], rtol=0, atol=1e-10):
                raise ValueError(f"seed alias changed seasonal interval metric: {dataset}/{fold}/{horizon}/{level}")
    unique_point = point[point.model_seed == 42].copy()
    unique_interval = interval[interval.model_seed == 42].copy()
    unique_keys(unique_point, ["dataset", "outer_fold", "horizon"], 27)
    unique_keys(unique_interval, ["dataset", "outer_fold", "horizon", "level"], 54)
    OUTPUT.mkdir(parents=True)
    for name, data in tables.items():
        data.to_csv(OUTPUT / f"{name}_metrics.csv", index=False)
    unique_point.to_csv(OUTPUT / "seasonal_unique_point_metrics.csv", index=False)
    unique_interval.to_csv(OUTPUT / "seasonal_unique_interval_metrics.csv", index=False)
    contrasts = []
    index = ["dataset", "outer_fold", "model_seed", "horizon", "level"]
    for view in ("native", "common"):
        for key, group in tables[view].groupby(index):
            group = group.set_index("method")
            for left, right in (("cqr", "quantile_uncalibrated"),
                                ("recentred_enbpi_updated", "recentred_enbpi_static")):
                row = dict(zip(index, key), support=view, left_method=left, right_method=right,
                           n=int(group.loc[left, "n"]))
                for metric in ("coverage", "mpiw", "winkler", "mae", "rmse"):
                    row[f"{metric}_difference"] = float(group.loc[left, metric] - group.loc[right, metric])
                contrasts.append(row)
    contrasts = pd.DataFrame(contrasts)
    unique_keys(contrasts, index + ["support", "left_method"], 1560)
    contrasts.to_csv(OUTPUT / "shared_owner_contrasts.csv", index=False)
    costs = pd.DataFrame(costs)
    if len(costs) != 52:
        raise ValueError("worker-cost coverage changed")
    costs.to_csv(OUTPUT / "new_bundle_costs.csv", index=False)
    workload = pd.concat(workload_parts, ignore_index=True)
    unique_keys(workload, keys + ["channel"], 5850)
    if (workload.event_count != 0).any() or not workload.event_recall_status.eq("not_estimable_empty_event_catalogue").all():
        raise ValueError("clean-stream workload was mislabelled as event detection")
    workload.to_csv(OUTPUT / "background_workload_pooled.csv", index=False)
    summary = tables["common"].groupby(["dataset", "level", "method"], as_index=False).agg(
        cells=("horizon", "size"), median_n=("n", "median"),
        median_coverage=("coverage", "median"), median_width=("mpiw", "median"),
        median_winkler=("winkler", "median"), median_mae=("mae", "median"))
    summary["target_unit"] = summary.dataset.map(UNITS)
    summary.to_csv(OUTPUT / "descriptive_common_summary.csv", index=False)
    figure(OUTPUT, tables["common"])
    report(OUTPUT, tables, contrasts, summary, operation_sum, unique_point, unique_interval, costs,
           progress["minimum_free_disk_bytes"])
    atomic(OUTPUT / "analysis_validation.json", dict(
        passed=True, accepted_method_cells=250, new_method_cells=1700,
        total_method_cells=1950, native_rows=1950, common_rows=1950,
        unique_seasonal_computations=27, new_unique_seasonal_computations=18,
        seasonal_point_alias_rows=135, seasonal_interval_alias_rows=270,
        operation_totals=operation_sum, models_fitted_by_analysis=0,
        recorded_run_validation_resume_wall_seconds=float(
            costs[["run_wall_seconds", "validation_wall_seconds", "resume_wall_seconds"]].sum().sum()),
        resume_wall_seconds_recorded=int(costs.resume_wall_seconds_recorded.sum()),
        measured_run_stage_and_validation_cpu_seconds=float(costs[["run_stage_cpu_seconds", "validation_cpu_seconds"]].to_numpy().sum()),
        peak_measured_rss_bytes=int(max(costs.run_peak_rss_bytes.max(), costs.validation_peak_rss_bytes.max())),
        minimum_post_bundle_free_disk_bytes=int(progress["minimum_free_disk_bytes"]),
        full_study_ready=False))
    print(json.dumps(read(OUTPUT / "analysis_validation.json"), indent=2), flush=True)


def figure(out: Path, common: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    methods = list(frozen.METHODS)
    labels = [m.replace("_", "\n") for m in methods]
    fig, axes = plt.subplots(4, 2, figsize=(14, 16), layout="constrained")
    for i, dataset in enumerate(("bdg2", "pleia", "pleia_energy", "rico")):
        subset = common[common.dataset == dataset]
        for j, metric in enumerate(("coverage", "winkler")):
            ax = axes[i, j]
            positions = np.arange(len(methods))
            for offset, level in ((-.17, .9), (.17, .95)):
                med = subset[subset.level == level].groupby("method")[metric].median().reindex(methods)
                ax.bar(positions + offset, med, width=.32, label=f"{int(level*100)}%")
            ax.set_xticks(positions, labels, fontsize=7)
            ax.set_title(f"{dataset}: median {metric} across declared fold/seed/horizon cells")
            ax.set_ylabel("fraction" if metric == "coverage" else UNITS[dataset])
            if metric == "coverage":
                ax.set_ylim(0, 1)
            ax.grid(axis="y", alpha=.2)
    axes[0, 0].legend()
    fig.savefig(out / "common_support_descriptive.png", dpi=145)
    plt.close(fig)
    atomic(out / "figure_sources.json", dict(
        source="common_metrics.csv", source_sha256=digest(out / "common_metrics.csv"),
        figure="common_support_descriptive.png", figure_sha256=digest(out / "common_support_descriptive.png"),
        interpretation="medians are descriptive, not population intervals"))


def report(out: Path, tables: dict, contrasts: pd.DataFrame, summary: pd.DataFrame,
           operations: dict, unique_point: pd.DataFrame, unique_interval: pd.DataFrame,
           costs: pd.DataFrame, minimum_free_disk_bytes: int) -> None:
    lines = ["# Bounded matched interval-method and seasonal completion", "",
             "All 1,950 declared method cells are present once in each native/common evaluation view: 250 accepted historical cells and 1,700 newly validated cells. All 27 unique applicable seasonal dataset/fold/horizon computations are present; 18 are new. The 135 seasonal point and 270 interval seed rows are aliases, not independent repetitions. RICO seasonal remains inapplicable.", "",
             "The analyses are descriptive across fixed folds and model seeds. Overlapping observations, folds and seed aliases are not independent population replicates. No population interval, significance claim, or cross-target numerical ranking is made. Full-study readiness is false; operational-grid and robustness/contamination/recovery obligations remain.", "",
             "Widths, Winkler scores, MAE and RMSE use target units: BDG2 and PLEIA energy kWh; PLEIA temperature and RICO °C. Coverage is a fraction. Native and common rows are two views of the same cells, not 3,900 experiments. Availability counts and original masks are retained in the full CSVs.", "",
             "## Descriptive common-support results", "",
             "| Dataset | Level | Method | Cells | Median coverage | Median width | Median Winkler | Unit |",
             "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |"]
    for row in summary.itertuples(index=False):
        lines.append(f"| {row.dataset} | {row.level:.2f} | {row.method} | {row.cells} | {row.median_coverage:.3f} | {row.median_width:.3f} | {row.median_winkler:.3f} | {row.target_unit} |")
    lines += ["", "[Common-support descriptive figure](common_support_descriptive.png) and [source hashes](figure_sources.json).", "",
              "## Shared-owner comparisons", ""]
    for left, right in (("cqr", "quantile_uncalibrated"),
                        ("recentred_enbpi_updated", "recentred_enbpi_static")):
        for dataset in ("bdg2", "pleia", "pleia_energy", "rico"):
            group = contrasts[(contrasts.support == "common") &
                              (contrasts.left_method == left) & (contrasts.dataset == dataset)]
            lines.append(f"{dataset}, {left} versus {right}: median coverage difference {group.coverage_difference.median():+.4f} (fraction), median width difference {group.mpiw_difference.median():+.4f} {UNITS[dataset]}, and median Winkler difference {group.winkler_difference.median():+.4f} {UNITS[dataset]}. These are descriptive cell summaries; see the per-cell CSV for unfavorable cases.")
            lines.append("")
    lines += ["CQR and raw quantiles share their frozen owner. Static and updated EnbPI share their frozen EnbPI owner. DSCP reuses each exact matched XGBoost forecasting owner, so method contrasts with DSCP also change predictor. [All native cells](native_metrics.csv), [all common cells](common_metrics.csv), [paired differences](shared_owner_contrasts.csv), [unique seasonal point](seasonal_unique_point_metrics.csv) and [seasonal interval](seasonal_unique_interval_metrics.csv) retain the full evidence, including unfavorable results.", "",
              "Seasonal-naive predictions use the declared daily period, each dataset/fold/horizon's own rows and pre-test calibration. Compare their saved point and interval metrics on their declared support; an alias is not a second learned computation. [Pooled clean-stream workload](background_workload_pooled.csv) reports background episodes/exposure only. Its event catalogues are empty, so recall, F1 and confirmed false-alarm rates are not estimable.", "",
              "## Actual new operation ledger totals", ""]
    for key, value in operations.items():
        lines.append(f"- {key}: {value}")
    lines += ["", "CQR/EnbPI wrapper counts enclose nested estimator fits; they are not additional predictive fits. The 2,890 new predictive-estimator fits are 1,020 quantile plus 1,870 XGBoost; DSCP and KMeans are separate calibrator/candidate counts. No historical forecasting refit or random-forest fallback occurred.", ""]
    wall = costs[["run_wall_seconds", "validation_wall_seconds", "resume_wall_seconds"]].sum().sum()
    recorded_resumes = int(costs.resume_wall_seconds_recorded.sum())
    cpu = costs[["run_stage_cpu_seconds", "validation_cpu_seconds"]].to_numpy().sum()
    peak = max(costs.run_peak_rss_bytes.max(), costs.validation_peak_rss_bytes.max())
    lines += ["## Measured resources", "",
              f"Across the 52 new bundles, recorded run/validation/resume worker wall time summed to {wall/3600:.3f} hours; resume duration is present for {recorded_resumes}/52 bundles, while both manually recovered zero-fit resumes retain pass receipts without invented durations. Measured run-stage plus validation CPU time summed to {cpu/3600:.3f} hours; this excludes preparation, resume and process-launch overhead, so it is not a whole-batch CPU total. Peak recorded lifetime RSS was {peak/2**30:.3f} GiB. The minimum free disk recorded at post-bundle checkpoints was {minimum_free_disk_bytes/2**30:.3f} GiB; transient between-checkpoint minima are not claimed. [Per-bundle costs](new_bundle_costs.csv) retain the exact components. External backup and publication times are separately scoped.", ""]
    (out / "CUMULATIVE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    with Operations(forbid=True):
        aggregate()
