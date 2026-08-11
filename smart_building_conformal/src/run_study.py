"""Command-line driver for the full dissertation study.

    python -m src.run_study --config configs/study_full.yaml --dataset pleia --fast
    python -m src.run_study --config configs/study_full.yaml --all --resume

The preliminary experiment keeps its own entry point,
``python -m src.run_experiment --config configs/pleia_preliminary.yaml``, which
this module never touches and never overwrites: full-study outputs live under
``outputs/full_study/`` while the reported preliminary results stay in
``outputs/``.

Fast mode
---------
``--fast`` shrinks horizons, seeds, search iterations, epochs, bootstrap
replicates, BDG2 building count and disturbance repetitions. It does **not**
change methodology and does not skip stages — every code path a full run
exercises is exercised by a fast run, just with less of it. It is a smoke test,
not a second experiment, and every output it writes is stamped ``fast_mode``.

Resume
------
``--resume`` reuses stages recorded in the ledger for the *same* configuration
hash. If the configuration changed, the ledger is discarded and the mismatch is
reported rather than mixing results from two different configurations.
"""

from __future__ import annotations

import argparse
import copy
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import study_plotting, study_reporting
from .datasets.base import config_hash
from .manifest import ResumeLedger, RunManifest
from .study_runner import DatasetStudy

STAGES = ("prepare", "point", "intervals", "alerts", "recalibration",
          "robustness", "statistics")


# --------------------------------------------------------------------------- #
def load_config(path: str) -> dict:
    """Load a study config, resolving an optional ``extends:`` parent.

    The per-dataset configs (``pleia_full.yaml`` and friends) are thin files that
    extend ``study_full.yaml`` and narrow it to one dataset, so the shared
    settings exist in exactly one place and cannot drift between files.
    """
    p = Path(path)
    with open(p, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    parent = cfg.pop("extends", None)
    if parent:
        base = load_config(str((p.parent / parent).resolve()))
        only = cfg.pop("only_datasets", None)
        cfg = _deep_update(base, cfg)
        if only:
            cfg["datasets"] = {k: v for k, v in cfg.get("datasets", {}).items()
                               if k in set(only)}
    return cfg


def resolve_dataset_config(study: dict, dataset_id: str) -> dict:
    """Merge the study-wide defaults with one dataset's overrides."""
    cfg = copy.deepcopy(study.get("defaults", {}))
    blocks = study.get("datasets", {})
    if dataset_id not in blocks:
        raise KeyError(
            f"dataset {dataset_id!r} is not configured; available: {sorted(blocks)}"
        )
    _deep_update(cfg, blocks[dataset_id])
    cfg.setdefault("seed", study.get("seed", 42))
    return cfg


def _deep_update(base: dict, extra: dict) -> dict:
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v
    return base


def apply_fast_overrides(cfg: dict) -> dict:
    """Shrink every expensive knob while keeping all code paths live."""
    fast = cfg.get("fast", {})
    if "horizons" in fast:
        cfg["horizons"] = list(fast["horizons"])
    elif len(cfg.get("horizons", [])) > 2:
        cfg["horizons"] = cfg["horizons"][:2]      # DSCP needs >= 2 horizons
    if "coverage_levels" in fast:
        cfg["coverage_levels"] = list(fast["coverage_levels"])

    cfg["models"]["xgboost"].update(
        {"search_iter": 4, "cv_splits": 2, "seeds": 2})
    cfg["models"]["lstm"].update({"max_epochs": 3, "seeds": 1})
    cfg["conformal"]["cqr"]["seeds"] = 2
    cfg["conformal"]["enbpi"].update(
        {"n_resamplings": 5, "seeds": 1, "update_step": 50, "base_n_estimators": 60})
    cfg.setdefault("bootstrap", {})["n_boot"] = 100
    cfg["alerts"]["events"]["instances_per_type"] = 2
    rob = cfg.setdefault("robustness", {})
    rob["random_missing"] = rob.get("random_missing", [0.05, 0.10, 0.20])[:2]
    rob["block_missing"] = rob.get("block_missing", [0.05])[:1]
    rob["bias_sds"] = rob.get("bias_sds", [0.5, 1.0, 2.0])[:2]
    rob["level_shift_sds"] = rob.get("level_shift_sds", [1.0, 2.0])[:1]
    rob["drift_sds"] = rob.get("drift_sds", [1.0, 2.0])[:1]
    rob["calibration_contamination"] = rob.get(
        "calibration_contamination", [0.01, 0.05, 0.10])[:2]
    if "selection" in cfg.get("bdg2", {}):
        cfg["bdg2"]["selection"]["n_buildings"] = min(
            fast.get("bdg2_buildings", 3),
            cfg["bdg2"]["selection"].get("n_buildings", 10))
    cfg["fast_mode"] = True
    return cfg


# --------------------------------------------------------------------------- #
def discover_datasets(out_root: Path) -> list[str]:
    """Dataset directories that already hold metrics under ``out_root``.

    The combined tables are rebuilt from everything on disk rather than only the
    datasets run in this invocation. Otherwise re-running one dataset — which is
    exactly what ``--resume`` and ``--dataset`` are for — would silently rewrite
    the cross-dataset tables with a single dataset in them.
    """
    return sorted(p.parent.name for p in out_root.glob("*/metrics")
                  if p.is_dir() and p.parent.name not in {"combined", "report",
                                                          "manifests"})


def combine_outputs(out_root: Path, datasets: list[str]) -> dict:
    """Concatenate the per-dataset tables into the cross-dataset views."""
    combined = out_root / "combined"
    combined.mkdir(parents=True, exist_ok=True)
    datasets = sorted(set(datasets) | set(discover_datasets(out_root)))
    mapping = {
        "point_metrics.csv": "point_metrics.csv",
        "interval_metrics.csv": "interval_metrics.csv",
        "alert_metrics.csv": "alert_metrics.csv",
        "robustness_metrics.csv": "robustness_metrics.csv",
        "recalibration_metrics.csv": "recalibration_metrics.csv",
        "bootstrap_metrics.csv": "bootstrap_metrics.csv",
        "diebold_mariano.csv": "statistical_tests.csv",
        "effect_sizes.csv": "effect_sizes.csv",
    }
    written = {}
    for src, dest in mapping.items():
        frames = []
        for d in datasets:
            p = out_root / d / "metrics" / src
            if p.exists():
                frames.append(pd.read_csv(p))
        if frames:
            df = pd.concat(frames, ignore_index=True)
            df.to_csv(combined / dest, index=False)
            written[dest] = len(df)
    return written


def build_rankings(out_root: Path) -> pd.DataFrame:
    """Within-dataset method rankings plus the Friedman/Holm analysis."""
    from . import statistics as S

    combined = out_root / "combined"
    point_path = combined / "point_metrics.csv"
    if not point_path.exists():
        return pd.DataFrame()
    point = pd.read_csv(point_path)
    point = point[point.get("applicable", True) == True]  # noqa: E712
    if point.empty or "mae" not in point.columns:
        return pd.DataFrame()

    # Rank models inside each (dataset, target, horizon) block: comparing raw MAE
    # across targets with different units would be meaningless.
    block = ["dataset", "target", "horizon_steps"]
    point["rank_mae"] = point.groupby(block)["mae"].rank(ascending=True)
    point["rank_rmse"] = point.groupby(block)["rmse"].rank(ascending=True)
    rankings = (point.groupby(["dataset", "point_model"])
                .agg(mean_rank_mae=("rank_mae", "mean"),
                     mean_rank_rmse=("rank_rmse", "mean"),
                     mean_pct_mae_improvement=("pct_mae_improvement", "mean"),
                     n_blocks=("rank_mae", "size"))
                .reset_index())
    rankings.to_csv(combined / "model_rankings.csv", index=False)

    matrix = S.ranking_matrix(point, block_cols=block,
                              method_col="point_model", value_col="mae")
    tests = []
    if not matrix.empty:
        fr = S.friedman_test(matrix)
        tests.append({"test": "friedman", "scope": "point models across "
                      "dataset/target/horizon blocks", **{
                          k: v for k, v in fr.items() if k != "mean_ranks"},
                      "mean_ranks": fr.get("mean_ranks")})
        post = S.nemenyi_style_posthoc(matrix)
        if len(post):
            post.insert(0, "test", "wilcoxon_holm_posthoc")
            post.to_csv(combined / "posthoc_comparisons.csv", index=False)
    if tests:
        pd.DataFrame(tests).to_csv(combined / "ranking_tests.csv", index=False)
    return rankings


# --------------------------------------------------------------------------- #
def main() -> None:
    p = argparse.ArgumentParser(description="Run the ConfoSense full study.")
    p.add_argument("--config", default="configs/study_full.yaml")
    p.add_argument("--dataset", action="append", default=None,
                   help="dataset id; repeatable")
    p.add_argument("--all", action="store_true", help="run every configured dataset")
    p.add_argument("--fast", action="store_true", help="smoke-test settings")
    p.add_argument("--resume", action="store_true",
                   help="reuse stages already completed under the same config hash")
    p.add_argument("--stage", action="append", default=None,
                   choices=list(STAGES), help="run only these stages; repeatable")
    p.add_argument("--horizon", action="append", type=int, default=None,
                   help="restrict to these horizons; repeatable")
    p.add_argument("--method", action="append", default=None,
                   help="restrict interval methods (debugging aid)")
    p.add_argument("--outputs", default=None, help="override the output root")
    args = p.parse_args()

    logging.disable(logging.INFO)   # MAPIE logs a line per re-sorted prediction
    study = load_config(args.config)

    wanted = list(args.dataset or [])
    if args.all or not wanted:
        wanted = list(study.get("datasets", {}).keys())

    out_root = Path(args.outputs or study.get("paths", {}).get(
        "full_study_dir", "outputs/full_study"))
    out_root.mkdir(parents=True, exist_ok=True)

    manifest = RunManifest(config_path=args.config, config=study,
                           output_dir=out_root, fast=args.fast, datasets=wanted)
    if args.fast:
        manifest.note_limitation(
            "Run executed in --fast smoke-test mode: reduced horizons, seeds, "
            "search iterations, epochs, bootstrap replicates and disturbance "
            "repetitions. Numbers are not the full-study results."
        )

    ledger = ResumeLedger(out_root / "manifests" / "resume_ledger.json",
                          config_hash(study), enabled=args.resume)
    for note in ledger.mismatches:
        print(f"[resume] {note}")
        manifest.note_limitation(note)

    t0 = time.time()
    for dataset_id in wanted:
        print(f"[{dataset_id}] starting ...")
        try:
            cfg = resolve_dataset_config(study, dataset_id)
        except KeyError as exc:
            manifest.record(f"{dataset_id}:config", "failed", reason=str(exc))
            continue
        if args.fast:
            cfg = apply_fast_overrides(cfg)
        if args.horizon:
            cfg["horizons"] = [h for h in cfg["horizons"] if h in set(args.horizon)] \
                or list(args.horizon)
        np.random.seed(cfg["seed"])

        study_obj = DatasetStudy(dataset_id, cfg, out_root, manifest, ledger,
                                 fast=args.fast, only_stages=args.stage)
        study_obj.run()

    # ---- cross-dataset combination, figures, report ----
    print("[combined] merging metric tables ...")
    written = combine_outputs(out_root, wanted)
    manifest.record("combined:tables", "completed", rows_per_table=written)
    try:
        build_rankings(out_root)
        manifest.record("combined:rankings", "completed")
    except Exception as exc:                                # noqa: BLE001
        manifest.record("combined:rankings", "failed", reason=str(exc))

    print("[combined] figures ...")
    try:
        made = study_plotting.build_all(out_root)
        manifest.record("combined:figures", "completed", details={"n": len(made)})
    except Exception as exc:                                # noqa: BLE001
        manifest.record("combined:figures", "failed", reason=str(exc))
        manifest.note_limitation(f"figure generation failed: {exc}")

    print("[combined] report ...")
    try:
        study_reporting.build(out_root, manifest, fast=args.fast)
        manifest.record("combined:report", "completed")
    except Exception as exc:                                # noqa: BLE001
        manifest.record("combined:report", "failed", reason=str(exc))

    payload = manifest.write()
    print(f"[done] {time.time() - t0:.1f}s | completed {payload['n_completed']}, "
          f"failed {payload['n_failed']}, skipped {payload['n_skipped']}")
    print(f"[done] outputs under {out_root}")


if __name__ == "__main__":
    main()
