"""Fit, conformalize and predict the missing 97.5/99/99.5% CQR owners of one unit.

Each owner is one MAPIE ConformalizedQuantileRegressor built by the established
matched-intervals005 factory (src.intervals005_owners.fit_owner and
conformalize_owner) on the original chronological fit and calibration roles of
the fold/seed unit.  The uncalibrated-quantile candidates share the same fitted
lower/upper/median estimators, exactly as the accepted 95% owners are shared.
"""
from __future__ import annotations

from hc_common import single_thread_environment

single_thread_environment()

import argparse  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from hc_common import (  # noqa: E402
    FROZEN, LEVELS, OWNERS, QUARANTINE, RUN_ROOT, SCIENCE, VERSION, append_ledger, atomic_json,
    digest, level_tag, read, signature, source_content_digest, tree, unit_name, utc,
    verify_extension_protocol,
)

SRC = SCIENCE / "smart_building_conformal" / "src"
EXPECTED_FIT_COUNTS = {"cqr_wrapper_fit": 1, "quantile_estimator_fit": 3}
EXPECTED_CAL_COUNTS = {"calibrator_conformalize": 2}


def frozen_adapter():
    if str(FROZEN) not in sys.path:
        sys.path.insert(0, str(FROZEN))
    import adapter
    if Path(adapter.__file__).resolve() != (FROZEN / "adapter.py").resolve():
        raise ValueError("frozen adapter resolved outside the science root")
    return adapter


def stage_keys(level: float) -> tuple[str, str, str]:
    tag = level_tag(level)
    return f"owner_fit_h1_cqr_{tag}", f"owner_cal_h1_cqr_{tag}", f"raw_h1_cqr_{tag}"


def load_unit(adapter, fold: int, seed: int, expected_source: str):
    """The frozen adapter.load_unit, with its byte-digest gate replaced by the content gate.

    The frozen gate compares the on-disk byte digest with the 2026-09 working-tree
    digest, whose line-ending mix no longer exists after the 2026-10-02 checkout.
    The committed source content is unchanged and pinned instead.
    """
    protocol_dir, _ = adapter.bundle_paths(fold, seed)
    protocol = adapter.read(protocol_dir / "frozen_protocol.json")
    if protocol["scope"] != {
        "dataset": "bdg2", "outer_fold": fold, "model_seed": seed,
        "horizons": [1, 3, 6], "levels": [0.9, 0.95],
        "methods": ["quantile_uncalibrated", "cqr", "recentred_enbpi_static", "recentred_enbpi_updated", "dscp"],
    }:
        raise ValueError("completed interval scope mismatch")
    data, roles, prepared = adapter.load_data(protocol["references"]["1"], None)
    if source_content_digest(SRC) != expected_source:
        raise ValueError("frozen scientific source content changed")
    test = adapter.role_frame(data, roles["test"])
    completed = adapter.frame(adapter.REPO / protocol["references"]["1"]["owner_directory"] / "predictions.csv.gz")
    if "nominal_level" in completed:
        completed = completed[completed.nominal_level == 0.9]
    if list(test.row_id.astype(str)) != list(completed.row_id.astype(str)):
        raise ValueError("completed forecasting test identity mismatch")
    return protocol, data, roles, prepared[0]


FACTORY_FIELDS = ("factory", "estimator_parameters", "wrapper_parameters", "objects_per_horizon",
                  "estimators_per_object", "sharing", "crossing")


def owner_spec(adapter, fold: int, seed: int, interval_protocol: dict, frequency) -> dict:
    """Require the factory-defining CQR fields of the unit's interval protocol.

    Older fold-2 bundles describe the alert sampling frequency and (bundle f2_s42)
    the native CQR score in pre-erratum wording; those descriptive fields are
    recorded, not compared.
    """
    from src.intervals005_owners import method_spec
    spec = method_spec(seed, frequency)
    frozen = interval_protocol["method_specification"]
    if spec["version"] != frozen["version"] or spec["seed"] != frozen["seed"] or any(
            signature(spec["cqr"][field]) != signature(frozen["cqr"][field]) for field in FACTORY_FIELDS):
        raise ValueError("established quantile-owner factory drifted from the interval protocol")
    documentation = sorted(
        [f"cqr.{k}" for k in spec["cqr"] if k not in FACTORY_FIELDS and signature(spec["cqr"][k]) != signature(frozen["cqr"].get(k))]
        + [k for k in spec if k != "cqr" and signature(spec[k]) != signature(frozen.get(k))])
    return {
        "factory_fields_compared": list(FACTORY_FIELDS),
        "documentation_fields_differing_from_interval_protocol": documentation,
        "version": VERSION, "unit": unit_name(fold, seed), "fold": fold, "model_seed": seed, "horizon": 1,
        "levels": list(LEVELS), "owner_kind": "cqr",
        "interval_protocol_sha256": digest(adapter.bundle_paths(fold, seed)[0] / "frozen_protocol.json"),
        "method_specification_signature": signature(spec),
        "source_content_digest": source_content_digest(SRC),
        "roles": {"fit": "fit", "calibration": "calibration", "prediction": ["calibration", "test"]},
    }


def reconcile_partials(root: Path, ledger: Path) -> list[str]:
    """Preserve, then set aside, fit partials left by a dead worker (never reused)."""
    moved = []
    for partial in sorted(root.glob(".partial_*")):
        if (partial / "COMPLETE.json").exists():
            continue
        target = QUARANTINE / root.name / f"{partial.name}_{utc().replace(':', '').replace('.', '')}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(partial), str(target))
        append_ledger(ledger, event="quarantined_incomplete_partial", source=str(partial), target=str(target))
        moved.append(str(target))
    return moved


def counts(stage: Path) -> dict[str, int]:
    return read(stage / "operation_counts.json")["counts"]


def fit_unit(fold: int, seed: int, *, reconcile: bool = False) -> dict:
    extension = verify_extension_protocol(fold=fold, seed=seed)
    adapter = frozen_adapter()
    from src.intervals005_common import Stages, csv, load_owner
    from src.intervals005_owners import conformalize_owner, fit_owner, raw_predictions
    from src.matched_forecasting005 import setup_threads
    setup_threads()
    unit = unit_name(fold, seed)
    root = OWNERS / unit
    ledger = RUN_ROOT / "fit_ledger.jsonl"
    protocol, data, roles, _ = load_unit(adapter, fold, seed, extension["source_content_digest"])
    spec = owner_spec(adapter, fold, seed, protocol, data["freq"])
    if reconcile and root.exists():
        reconcile_partials(root, ledger)
    stages = Stages(root, spec, resume=(root / "checkpoint_manifest.json").exists())
    X = data["X"]
    y = data["y"]
    fit_rows, cal_rows = roles["fit"], roles["calibration"]
    records = {}
    for level in LEVELS:
        tag = level_tag(level)
        fit_key, cal_key, raw_key = stage_keys(level)
        existed = {key: stages.get(key) is not None for key in (fit_key, cal_key, raw_key)}
        fitted = fit_owner(stages, fit_key, "cqr", level, seed, X.iloc[fit_rows], y[fit_rows])
        calibrated = conformalize_owner(stages, cal_key, fitted, X.iloc[cal_rows], y[cal_rows])

        def raw_work(out: Path, level=level, tag=tag, calibrated=calibrated) -> dict:
            owner = load_owner(calibrated / "owner.pkl")
            written = {}
            for role in ("calibration", "test"):
                rows = roles[role]
                predictions = raw_predictions(owner, "cqr", X.iloc[rows].to_numpy(), [level])[level]
                csv(out / f"{role}_metadata.csv.gz", adapter.role_frame(data, rows))
                csv(out / f"{role}_{tag}.csv.gz", predictions)
                written[role] = len(predictions)
            return {"owner_sha256": digest(calibrated / "owner.pkl"), "kind": "cqr", "levels": [level], "rows": written}

        raw = stages.run(raw_key, raw_work)
        fit_counts, cal_counts = counts(fitted), counts(calibrated)
        if fit_counts != EXPECTED_FIT_COUNTS or cal_counts != EXPECTED_CAL_COUNTS:
            raise ValueError(f"unexpected owner operation counts at {tag}: {fit_counts} {cal_counts}")
        for key, path, operation_counts in ((fit_key, fitted, fit_counts), (cal_key, calibrated, cal_counts)):
            if not existed[key]:
                append_ledger(ledger, event="new_owner_operation", unit=unit, fold=fold, model_seed=seed,
                              level=level, stage=key, operation_counts=operation_counts,
                              owner_sha256=digest(path / "owner.pkl"),
                              operations=read(path / "operation_counts.json")["operations"])
        records[tag] = {
            "level": level,
            "stages": {key: {"path": (root / "stages" / key).relative_to(RUN_ROOT).as_posix(),
                             "complete_sha256": digest(root / "stages" / key / "COMPLETE.json"),
                             "files": tree(root / "stages" / key),
                             "reused_existing_checkpoint": existed[key]}
                       for key in (fit_key, cal_key, raw_key)},
            "fitted_owner_sha256": digest(fitted / "owner.pkl"),
            "calibrated_owner_sha256": digest(calibrated / "owner.pkl"),
            "calibration_values_sha256": digest(raw / f"calibration_{tag}.csv.gz"),
            "calibration_metadata_sha256": digest(raw / "calibration_metadata.csv.gz"),
            "test_values_sha256": digest(raw / f"test_{tag}.csv.gz"),
            "operation_counts": {"fit": fit_counts, "conformalize": cal_counts},
            "payload": {"fit": read(fitted / "stage.json")["payload"],
                        "conformalize": read(calibrated / "stage.json")["payload"],
                        "raw": read(raw / "stage.json")["payload"]},
        }
    manifest = {
        "version": VERSION, "unit": unit, "fold": fold, "model_seed": seed, "spec": spec,
        "stage_identity": stages.identity, "levels": records,
        "fit_rows": int(len(fit_rows)), "calibration_rows": int(len(cal_rows)), "test_rows": int(len(roles["test"])),
        "new_estimator_fits_by_level": {tag: 0 if r["stages"][stage_keys(r["level"])[0]]["reused_existing_checkpoint"]
                                        else EXPECTED_FIT_COUNTS["quantile_estimator_fit"] for tag, r in records.items()},
        "utc": utc(),
    }
    if (root / "OWNER_MANIFEST.json").exists():
        prior = read(root / "OWNER_MANIFEST.json")
        if signature(_stable(prior["levels"])) != signature(_stable(records)):
            raise ValueError("owner checkpoints differ from the recorded owner manifest")
        manifest = prior
    else:
        atomic_json(root / "OWNER_MANIFEST.json", manifest)
    print(json.dumps({"unit": unit, "levels": list(records), "status": "owners_complete"}))
    return manifest


def _stable(records: dict) -> dict:
    """Owner identity without the first-run/reuse flags."""
    stable = json.loads(json.dumps(records))
    for record in stable.values():
        for stage in record["stages"].values():
            stage.pop("reused_existing_checkpoint", None)
    return stable


def resume_unit(fold: int, seed: int) -> dict:
    """Zero-fit resume: every owner stage must already exist and stay byte-identical."""
    extension = verify_extension_protocol(fold=fold, seed=seed)
    adapter = frozen_adapter()
    from src.intervals005_common import Operations, Stages
    unit = unit_name(fold, seed)
    root = OWNERS / unit
    if not (root / "checkpoint_manifest.json").exists() or not (root / "OWNER_MANIFEST.json").exists():
        raise ValueError("owner resume requires completed owner checkpoints")
    before = tree(root)
    with Operations(forbid=True):
        protocol, data, roles, _ = load_unit(adapter, fold, seed, extension["source_content_digest"])
        spec = owner_spec(adapter, fold, seed, protocol, data["freq"])
        stages = Stages(root, spec, resume=True)
        for level in LEVELS:
            for key in stage_keys(level):
                if stages.get(key) is None:
                    raise ValueError(f"owner resume found a missing stage: {key}")
    after = tree(root)
    manifest = read(root / "OWNER_MANIFEST.json")
    for record in manifest["levels"].values():
        for key, stage in record["stages"].items():
            path = RUN_ROOT / stage["path"]
            if tree(path) != stage["files"] or digest(path / "COMPLETE.json") != stage["complete_sha256"]:
                raise ValueError(f"owner checkpoint differs from the owner manifest: {key}")
    result = {"passed": before == after, "unit": unit, "files_unchanged": before == after,
              "stages_verified": 3 * len(LEVELS), "models_fitted": 0, "calibrators_fitted": 0,
              "forbidden_fit_guard": "src.intervals005_common.Operations(forbid=True)", "utc": utc()}
    if not result["passed"]:
        raise ValueError("owner resume changed checkpoint files")
    atomic_json(root / "RESUME.json", result)
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["fit-unit", "resume-unit"])
    parser.add_argument("--fold", type=int, required=True, choices=[0, 1, 2])
    parser.add_argument("--model-seed", type=int, required=True, choices=[42, 43, 44, 45, 46])
    parser.add_argument("--reconcile-partials", action="store_true")
    args = parser.parse_args()
    if args.action == "fit-unit":
        fit_unit(args.fold, args.model_seed, reconcile=args.reconcile_partials)
    else:
        resume_unit(args.fold, args.model_seed)
