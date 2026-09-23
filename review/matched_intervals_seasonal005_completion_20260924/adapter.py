"""Versioned scope and owner adapter for the remaining amendment-005 method bundles.

All scientific fitting, stream construction, checkpointing, and independent
validation stay in the frozen src implementation. This module only resolves the
newly completed forecasting owners and freezes an explicit cross-fold scope.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SMART = REPO / "smart_building_conformal"
sys.path.insert(0, str(SMART))

from src import matched_intervals005 as frozen
from src import intervals005_data as data_api
from src import intervals005_validate as validator
from src.intervals005_common import (
    LEVELS, METHODS, Operations, PhaseMeter, atomic, csv, digest, frame,
    now, packages, read, resources, source_digest, tree,
)
from src.intervals005_owners import method_spec
from src.model_comparison_pilot import prepare as pilot_prepare
from src.pilot_data import build_support, role_records
from src.matched_data005 import forecast_roles
from src.unit_checkpoint import signature

HERE = Path(__file__).resolve().parent
MATRIX = SMART / "outputs/amendment005/study_plan_v1/interval_method_matrix.csv"
SEASONAL_QUEUE = SMART / "outputs/amendment005/study_plan_v1/seasonal_execution_queue.csv"
LEDGER = SMART / "outputs/matched_forecasting005/core_completion_195_v1_analysis/cumulative_completion_reuse_ledger.csv"
SUPPORT = SMART / "outputs/amendment005/support_final_checks_v1/dscp_joint_origin_support.csv"
JOINT = SMART / "outputs/amendment005/support_final_checks_v1/dscp_joint_origin_membership.csv.gz"
PROTOCOLS = SMART / "protocols/matched_intervals005"
OUTPUTS = SMART / "outputs/matched_intervals005"
SCOPE = HERE / "remaining_scope.csv"
AUTH = HERE / "AUTHORIZATION.json"
SOURCE_HASH = "a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f"
ENTRY = "0c57f73618552514d41c6b78c631bd575beeebbc"
VERSION = "matched_intervals_seasonal005_completion_v1"
ACCEPTED = {("bdg2", 2, seed) for seed in range(42, 47)} | {
    (dataset, 2, 42) for dataset in ("pleia", "pleia_energy", "rico")
}
EXPECTED_NEW = {"pleia": 14, "pleia_energy": 14, "rico": 14, "bdg2": 10}


def bundle_name(dataset: str, fold: int, seed: int) -> str:
    return f"{dataset}_f{fold}_s{seed}_method_completion_v1"


def bundle_paths(dataset: str, fold: int, seed: int) -> tuple[Path, Path]:
    name = bundle_name(dataset, fold, seed)
    return PROTOCOLS / name, OUTPUTS / name


def scope_rows() -> pd.DataFrame:
    matrix = frame(MATRIX)
    keys = ["dataset", "outer_fold", "model_seed"]
    if len(matrix) != 1950 or matrix.duplicated(keys + ["horizon", "level", "method"]).any():
        raise ValueError("declared method matrix is not the exact 1,950-cell grid")
    accepted = matrix[keys].apply(tuple, axis=1).isin(ACCEPTED)
    if int(accepted.sum()) != 250:
        raise ValueError("accepted method-cell inventory changed")
    missing = matrix.loc[~accepted].copy()
    if len(missing) != 1700:
        raise ValueError("remaining method-cell count changed")
    bundles = missing[keys].drop_duplicates().reset_index(drop=True)
    counts = bundles.groupby("dataset").size().to_dict()
    if len(bundles) != 52 or counts != EXPECTED_NEW:
        raise ValueError(f"remaining bundle set changed: {counts}")
    if set(matrix.method) != set(METHODS) or set(matrix.level) != set(LEVELS):
        raise ValueError("frozen methods or levels changed")
    seasonal = frame(SEASONAL_QUEUE)
    if len(seasonal) != 27 or seasonal[["dataset", "horizon", "outer_fold"]].duplicated().any():
        raise ValueError("seasonal queue changed")
    return bundles


def accepted_evidence() -> None:
    """Check accepted run/validation/resume evidence without rerunning it."""
    for dataset, fold, seed in sorted(ACCEPTED):
        if dataset == "bdg2":
            name = "bdg2_f2_s42_v1" if seed == 42 else f"bdg2_f2_s{seed}_v2"
            progress = read(OUTPUTS / "bdg2_fold2_multiseed_v2_coordinator/progress.json") if seed > 42 else None
            if progress is not None:
                saved = progress["units"][str(seed)]
                if not (saved["complete"] and saved["validation"] and saved["zero_fit_resume"]):
                    raise ValueError(f"accepted BDG2 seed {seed} evidence incomplete")
        else:
            name = f"{dataset}_f2_s42_v{'2' if dataset == 'pleia_energy' else '1'}"
            progress = read(OUTPUTS / "four_settings_f2_s42_v2_coordinator/progress.json")
            saved = progress["units"][dataset]
            if not (saved["complete"] and saved["validation"] and saved["zero_fit_resume"]):
                raise ValueError(f"accepted {dataset} evidence incomplete")
        complete = read(OUTPUTS / name / "COMPLETE.json")
        if complete["status"] != "complete" or complete["method_cells"] != (40 if dataset == "rico" else 30):
            raise ValueError(f"accepted bundle marker incomplete: {name}")


def prepare_scope() -> dict:
    if source_digest() != SOURCE_HASH:
        raise ValueError("frozen scientific source digest changed")
    bundles = scope_rows()
    accepted_evidence()
    if SCOPE.exists() or AUTH.exists():
        raise ValueError("scope/authorization already exists; preserve frozen version")
    HERE.mkdir(parents=True, exist_ok=True)
    csv(SCOPE, bundles)
    seasonal = frame(SEASONAL_QUEUE)
    auth = {
        "version": VERSION,
        "authorization_source": "user attachment 703d57a7-b9d5-4806-a375-ce15906e6b33",
        "entry_commit": ENTRY,
        "scientific_source_hash": SOURCE_HASH,
        "matrix_sha256": digest(MATRIX),
        "seasonal_queue_sha256": digest(SEASONAL_QUEUE),
        "forecasting_ledger_sha256": digest(LEDGER),
        "scope_sha256": digest(SCOPE),
        "bundles": bundles.to_dict("records"),
        "accepted_method_cells": 250,
        "new_method_cells": 1700,
        "final_method_cells": 1950,
        "new_unique_seasonal_computations": int((seasonal.outer_fold != 2).sum()),
        "fit_ceiling": frozen.expected_operations({"horizons": [0] * 170}),
        "historical_forecasting_refits": 0,
        "full_study_ready": False,
    }
    auth["fit_ceiling"]["dscp_calibrator_fit"] = 52
    auth["fit_ceiling"]["kmeans_candidate_fit"] = 260
    atomic(AUTH, auth)
    return {"passed": True, "bundles": len(bundles), "new_cells": 1700,
            "new_unique_seasonal": auth["new_unique_seasonal_computations"],
            "fit_ceiling": auth["fit_ceiling"]}


def select_owner(ledger: pd.DataFrame, dataset: str, horizon: int, fold: int, seed: int) -> pd.Series:
    match = ledger[(ledger.dataset == dataset) & (ledger.horizon == horizon)
                   & (ledger.outer_fold == fold) & (ledger.model_seed == seed)
                   & (ledger.model == "xgboost")]
    if len(match) != 1:
        raise ValueError("missing or ambiguous exact matched XGBoost owner")
    return match.iloc[0]


def run_tree_hash(run: Path, historical: bool) -> str:
    rows = tree(run)
    if historical:
        content = "\n".join(f"{path}:{digest_value}" for path, digest_value in rows.items())
    else:
        content = "\n".join(f"{path}:{(run / path).stat().st_size}:{digest_value}" for path, digest_value in rows.items())
    return hashlib.sha256(content.encode()).hexdigest()


def pilot_compatibility(horizon: int, historical_protocol: Path, source_hash: str) -> Path:
    """Normalize only the old pilot metadata, after exact saved-membership replay."""
    old = read(historical_protocol)
    if (old["config"]["dataset"], old["config"]["outer_fold_id"], old["config"]["model_seed"]) != ("pleia", 0, 42):
        raise ValueError("pilot protocol has a different experiment key")
    pilot_dir = historical_protocol.parent
    membership = pilot_dir / "membership.csv.gz"
    boundaries = pilot_dir / "boundaries.csv"
    if digest(membership) != old["membership_sha256"] or digest(boundaries) != old["boundaries_sha256"]:
        raise ValueError("pilot membership or boundaries changed")
    config_path = SMART / old["config"]["study_config"]
    current_config_hash = digest(config_path)
    prepared = pilot_prepare(old["resolved_dataset_config"])
    data = build_support(prepared, old["resolved_dataset_config"], horizon, old["config"]["sequence_length"])
    roles = forecast_roles(data["meta"], horizon, prepared.freq, 0, False)
    recorded = frame(membership)
    recorded = recorded[recorded.horizon == horizon]
    if set(recorded.role) != set(roles):
        raise ValueError("pilot role set changed")
    columns = ["row_id", "group_id", "origin_time", "target_time"]
    for role, indices in roles.items():
        actual = data["meta"].iloc[indices][columns].reset_index(drop=True).copy()
        saved = recorded[recorded.role == role][columns].reset_index(drop=True).copy()
        for part in (actual, saved):
            part.group_id = part.group_id.fillna("").astype(str).replace({"None": "", "nan": ""})
            for field in ("origin_time", "target_time"):
                part[field] = pd.to_datetime(part[field]).astype(str)
        if not actual.equals(saved):
            raise ValueError(f"pilot horizon {horizon} {role} membership mismatch")
    records = role_records(data["meta"], roles)
    support = dict(data_hash=data["data_hash"], roles=records,
                   role_bank_hash=signature(records), feature_names=data["feature_names"],
                   sequence_channels=data["sequence_channels"])
    compat = dict(
        version=f"{VERSION}_pilot_owner_compat_v1",
        original_protocol=str(historical_protocol.relative_to(REPO)),
        original_protocol_hash=digest(historical_protocol),
        historical_source_identity=source_hash,
        source_hash=source_hash,
        input_hashes={str(path.relative_to(SMART)): digest(path) for path in
                      (historical_protocol, membership, boundaries)},
        original_config_file_hash=old["config_file_sha256"],
        current_config_file_hash=current_config_hash,
        original_config_file_changed_since_pilot=current_config_hash != old["config_file_sha256"],
        config=dict(dataset="pleia", horizon=horizon, outer_fold=0, model_seed=42,
                    sequence_length=old["config"]["sequence_length"]),
        resolved_dataset_config=old["resolved_dataset_config"], support=support,
        membership_equality="all pilot roles and rows, exact ordered identity",
    )
    path = HERE / f"pilot_compat_h{horizon}_v1.json"
    if path.exists():
        if read(path) != compat:
            raise ValueError("pilot compatibility record changed")
    else:
        atomic(path, compat)
    return path


def owner_references(dataset: str, fold: int, seed: int, horizons: list[int]) -> dict:
    ledger = frame(LEDGER)
    protocols = {digest(path): path for path in (SMART / "protocols/matched_forecasting005").glob("*/frozen_protocol.json")}
    pilot_protocol = SMART / "protocols/model_comparison_pilot_v1/frozen_protocol.json"
    protocols[digest(pilot_protocol)] = pilot_protocol
    references = {}
    for horizon in horizons:
        row = select_owner(ledger, dataset, horizon, fold, seed)
        run = REPO / row.run_path
        owner = REPO / row.model_owner_path
        if not owner.is_file() or digest(owner) != row.model_owner_sha256:
            raise ValueError(f"missing or corrupt exact XGBoost model: {owner}")
        directory = owner.parent
        if digest(directory / "COMPLETE.json") != row.model_owner_complete_sha256:
            raise ValueError("XGBoost owner completion marker changed")
        expected_owner = (f"h{horizon}_f{fold}_s{seed}_xgboost" if run.parent.name == "runs"
                          else f"{dataset}_h{horizon}_f{fold}_s{seed}_xgboost")
        if owner.name != "model.ubj" or directory.name != expected_owner:
            raise ValueError("XGBoost owner path does not match exact key")
        old_protocol = protocols.get(row.protocol_sha256)
        if old_protocol is None or digest(old_protocol) != row.protocol_sha256:
            raise ValueError("forecasting owner protocol missing")
        old = read(old_protocol)
        if old_protocol == pilot_protocol:
            if (dataset, fold, seed) != ("pleia", 0, 42) or horizon not in old["config"]["horizons"]:
                raise ValueError("pilot protocol key mismatch")
            normalized_protocol = pilot_compatibility(horizon, old_protocol, row.source_sha256)
        else:
            if old["source_hash"] != row.source_sha256:
                raise ValueError("historical owner source identity differs from its protocol")
            old_scope = old["config"]
            if (old_scope["dataset"], int(old_scope["horizon"]), int(old_scope["outer_fold"]), int(old_scope["model_seed"])) != (dataset, horizon, fold, seed):
                raise ValueError("forecasting protocol key mismatch")
            normalized_protocol = old_protocol
        if run_tree_hash(run, bool(row.historical_reuse)) != row.run_tree_sha256:
            raise ValueError("forecasting run-tree hash changed")
        acceptance_path, _, anchor = str(row.acceptance_reference).partition("#")
        acceptance = Path(acceptance_path)
        if not acceptance.is_absolute():
            acceptance = REPO / acceptance
        if not acceptance.is_file():
            raise ValueError(f"forecasting acceptance evidence absent: {acceptance}")
        if anchor:
            if anchor != f"{dataset}|{horizon}|{fold}|{seed}":
                raise ValueError("forecasting acceptance anchor mismatch")
            accepted = frame(acceptance)
            matched = accepted[(accepted.dataset == dataset) & (accepted.horizon == horizon)
                               & (accepted.outer_fold == fold) & (accepted.model_seed == seed)]
            if len(matched) != 1 or int(matched.iloc[0].historical_refits) != 0:
                raise ValueError("forecasting acceptance ledger key missing or refitted")
        references[str(horizon)] = {
            "protocol": str(normalized_protocol.relative_to(REPO)),
            "protocol_hash": digest(normalized_protocol),
            "original_protocol": str(old_protocol.relative_to(REPO)),
            "original_protocol_hash": row.protocol_sha256,
            "run": row.run_path,
            "run_file_tree_hash": row.run_tree_sha256,
            "source_hash": row.source_sha256,
            "owner_directory": str(directory.relative_to(REPO)),
            "owner_hashes": {path.name: digest(path) for path in directory.iterdir() if path.is_file()},
            "evaluated_commit": row.evaluated_commit,
            "acceptance_reference": str(acceptance),
            "historical_reuse": bool(row.historical_reuse),
        }
        data_api.check_historical(references[str(horizon)])
    return references


def authorized_bundle(dataset: str, fold: int, seed: int) -> tuple[dict, pd.DataFrame]:
    auth = read(AUTH)
    if auth["version"] != VERSION or auth["scientific_source_hash"] != SOURCE_HASH:
        raise ValueError("unsupported authorization")
    for path, key in ((MATRIX, "matrix_sha256"), (SEASONAL_QUEUE, "seasonal_queue_sha256"),
                      (LEDGER, "forecasting_ledger_sha256"), (SCOPE, "scope_sha256")):
        if digest(path) != auth[key]:
            raise ValueError(f"authorized scope input changed: {path}")
    key = (dataset, fold, seed)
    actual = set(frame(SCOPE)[["dataset", "outer_fold", "model_seed"]].itertuples(index=False, name=None))
    frozen_keys = {(row["dataset"], row["outer_fold"], row["model_seed"]) for row in auth["bundles"]}
    if key not in actual or actual != frozen_keys or len(actual) != 52:
        raise ValueError("bundle outside exact 52-bundle authorization")
    policy = frozen.scope_policy(dataset, fold)
    scope = dict(dataset=dataset, outer_fold=fold, model_seed=seed,
                 horizons=policy["horizons"], levels=LEVELS, methods=METHODS)
    cells = frame(MATRIX)
    cells = cells[(cells.dataset == dataset) & (cells.outer_fold == fold) & (cells.model_seed == seed)]
    from src.unit_checkpoint import require_cells
    require_cells(cells, ["horizon", "level", "method"],
                  [(h, level, method) for h in scope["horizons"] for level in LEVELS for method in METHODS])
    return scope, cells


def freeze(dataset: str, fold: int, seed: int, synthetic_receipt: Path) -> dict:
    synthetic_receipt = synthetic_receipt.resolve()
    scope, cells = authorized_bundle(dataset, fold, seed)
    synthetic = read(synthetic_receipt)
    if not synthetic["passed"] or synthetic["enbpi_base_fits_per_owner"] != 11:
        raise ValueError("existing synthetic operation contract is not verified")
    design, _ = bundle_paths(dataset, fold, seed)
    if design.exists():
        permitted = {"joint_fit.csv.gz", "joint_calibration.csv.gz", "joint_test.csv.gz",
                     "native_membership.csv.gz", "scope.csv", "method_specification.json"}
        actual = {path.name for path in design.iterdir()}
        if (design / "frozen_protocol.json").exists() or actual != permitted:
            raise ValueError("existing design is frozen or not the verified prefit partial")
    policy = frozen.scope_policy(dataset, fold)
    references = owner_references(dataset, fold, seed, scope["horizons"])
    design.mkdir(parents=True, exist_ok=True)
    roles_all, support, prepared, frequency = {}, {}, None, None
    with Operations(forbid=True), PhaseMeter() as meter:
        for horizon in scope["horizons"]:
            data, roles, prepared = data_api.load_data(references[str(horizon)], prepared)
            if data["freq"] != pd.Timedelta(policy["frequency"]):
                raise ValueError("dataset sampling frequency changed")
            frequency = data["freq"] if frequency is None else frequency
            roles_all[horizon] = {role: data_api.role_frame(data, roles[role]) for role in ("fit", "calibration", "test")}
            support[str(horizon)] = dict(
                data_hash=data["data_hash"], roles=data["old_protocol"]["support"]["roles"],
                features=data["feature_names"], frequency=str(data["freq"]),
                available_by_role={role: int(data["available"][indices].sum()) for role, indices in roles.items()},
                seasonal_available_by_role={role: int(np.isfinite(data["seasonal"][indices]).sum()) for role, indices in roles.items()},
            )
            if policy["seasonal"] and not np.isfinite(data["seasonal"][np.r_[roles["calibration"], roles["test"]]]).all():
                raise ValueError("seasonal support unavailable")
            if not policy["seasonal"] and np.isfinite(data["seasonal"]).any():
                raise ValueError("RICO seasonal baseline unexpectedly materialized")
            del data
        joint = {}
        for role in ("fit", "calibration", "test"):
            pieces = data_api.joint_join({h: roles_all[h][role] for h in scope["horizons"]}, scope["horizons"],
                                expected=data_api.expected_joint(dataset, fold, role), frequency=frequency)
            joint[role] = len(pieces[scope["horizons"][0]])
            csv(design / f"joint_{role}.csv.gz", pd.concat(
                [part.assign(horizon=h, role=role) for h, part in pieces.items()], ignore_index=True))
        if joint != policy["joint_support"]:
            raise ValueError("frozen joint support changed")
        csv(design / "native_membership.csv.gz", pd.concat(
            [part.assign(horizon=h, role=role) for h, rr in roles_all.items() for role, part in rr.items()],
            ignore_index=True))
    csv(design / "scope.csv", cells)
    spec = method_spec(seed, frequency)
    atomic(design / "method_specification.json", spec)
    alias = None
    if seed != 42 and policy["seasonal"]:
        _, source_run = bundle_paths(dataset, fold, 42) if fold != 2 else (
            None, OUTPUTS / f"{dataset}_f2_s42_v{'2' if dataset == 'pleia_energy' else '1'}")
        source_root = source_run / "stages"
        files = {}
        for horizon in scope["horizons"]:
            stage = source_root / f"seasonal_h{horizon}"
            files[str(horizon)] = {name: digest(stage / name) for name in (
                "calibration.csv.gz", "interval_90.csv.gz", "interval_95.csv.gz", "point.json", "calibration.json")}
        alias = dict(model_seed=42, root=str(source_root.relative_to(REPO)), files=files)
    expected_cells = frozen.expected_cells(scope)
    if alias:
        expected_cells.update(seasonal_point=0, seasonal_alias=len(scope["horizons"]),
                              seasonal_interval=0, seasonal_interval_alias=2 * len(scope["horizons"]))
    inputs = [MATRIX, SEASONAL_QUEUE, LEDGER, SUPPORT, JOINT, SCOPE, AUTH, synthetic_receipt]
    protocol = dict(
        version=VERSION, scope=scope, authorization=read(AUTH), entry_commit=ENTRY,
        historical_source_hashes=sorted({reference["source_hash"] for reference in references.values()}),
        source_hash=source_digest(), adapter_sha256=digest(Path(__file__)),
        validator_sha256=digest(Path(validator.__file__)),
        packages=packages(), references=references, support=support, joint_support=joint,
        method_specification=spec, seasonal_alias_source=alias,
        inputs={str(path.relative_to(REPO)): digest(path) for path in inputs},
        design_hashes=tree(design), expected_operations=frozen.expected_operations(scope),
        expected_cells=expected_cells,
        resource_policy=dict(device="cpu", threads=1, n_jobs=1, batch_size=256,
                             launch_ram_reference_bytes=3 * 2**30, nonblocking_launch_ram=True,
                             epoch_floor_bytes=256 * 2**20, disk_floor_bytes=8 * 2**30),
        tolerances=dict(prediction_atol=1e-7, prediction_rtol=1e-7,
                        metric_atol=1e-10, metric_rtol=1e-12),
        frozen_utc=now(), freeze_resources=meter.result, models_fitted=0, full_study_ready=False,
    )
    atomic(design / "frozen_protocol.json", protocol)
    frozen.check_protocol(design / "frozen_protocol.json")
    return {"frozen": True, "dataset": dataset, "fold": fold, "seed": seed,
            "joint_support": joint, "source_hash": protocol["source_hash"],
            "adapter_sha256": protocol["adapter_sha256"]}


def checked_protocol(path: Path) -> dict:
    protocol = read(path)
    if protocol["version"] != VERSION or protocol["source_hash"] != SOURCE_HASH:
        raise ValueError("unsupported versioned protocol or scientific source")
    if protocol["adapter_sha256"] != digest(Path(__file__)):
        raise ValueError("adapter identity changed")
    if protocol["validator_sha256"] != digest(Path(validator.__file__)):
        raise ValueError("independent validator identity changed")
    authorized_bundle(**{ "dataset": protocol["scope"]["dataset"],
                          "fold": protocol["scope"]["outer_fold"],
                          "seed": protocol["scope"]["model_seed"] })
    return frozen.check_protocol(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "freeze", "readiness", "run", "validate", "resume"])
    parser.add_argument("--dataset")
    parser.add_argument("--fold", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--synthetic-receipt")
    parser.add_argument("--receipt")
    parser.add_argument("--forbid-fits", action="store_true")
    args = parser.parse_args()
    from src.matched_forecasting005 import setup_threads
    setup_threads()
    if args.action == "prepare":
        result = prepare_scope()
    else:
        if args.dataset is None or args.fold is None or args.seed is None:
            parser.error("dataset, fold, and seed are required")
        design, output = bundle_paths(args.dataset, args.fold, args.seed)
        protocol = design / "frozen_protocol.json"
        if args.action == "freeze":
            if not args.synthetic_receipt:
                parser.error("freeze requires the accepted synthetic receipt")
            result = freeze(args.dataset, args.fold, args.seed, Path(args.synthetic_receipt))
        else:
            p = checked_protocol(protocol)
            if p["scope"] != dict(dataset=args.dataset, outer_fold=args.fold,
                                  model_seed=args.seed, horizons=frozen.scope_policy(args.dataset, args.fold)["horizons"],
                                  levels=LEVELS, methods=METHODS):
                raise ValueError("requested key differs from frozen protocol")
            if args.action == "readiness":
                if not args.receipt:
                    parser.error("readiness requires a receipt path")
                result = frozen.readiness(protocol, args.receipt)
            elif args.action == "validate":
                if not args.receipt:
                    parser.error("validation requires a receipt directory")
                result = validator.validate(protocol, output, args.receipt)
            else:
                result = frozen.execute(protocol, design / "readiness.json", output,
                                        resume=args.action == "resume", forbid=args.forbid_fits,
                                        receipt=args.receipt)
    print(json.dumps(result, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
