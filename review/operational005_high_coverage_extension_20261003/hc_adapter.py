"""Run one extension policy block through the frozen operational005 block function.

The frozen ``adapter.run_block`` is executed unchanged.  Five module attributes are
substituted, and nothing else:

* ``policy_blocks``  -> the 33 previously unavailable policy groups (99 candidates)
* ``UNITS``          -> extension output storage on D:
* ``SavedOwner``     -> ``ExtensionOwner``, a hash-verified owner from the extension
                        owner checkpoints, built exactly as ``SavedOwner`` builds its
                        calibration scores and raw predictions
* ``load_unit``      -> the frozen loader with the source-content gate
* ``source_digest``/``VERSION`` -> report the true current source content digest and
                        the extension version in each block identity

Fault catalogues, severity scaling, causal feature reconstruction, delayed score
release, update schedules, residual windows, support views and metrics are all
the frozen code paths.  Estimator and calibrator fitting is disabled while a block
runs.
"""
from __future__ import annotations

from hc_common import single_thread_environment

single_thread_environment()

import argparse  # noqa: E402
import csv  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

from hc_common import (  # noqa: E402
    BLOCKS_PER_UNIT, FROZEN, LEVELS, OWNERS, RUN_ROOT, SCIENCE, UNITS, VERSION, digest, level_tag,
    read, signature, source_content_digest, tree, unit_name, verify_extension_protocol,
)
from hc_owner import frozen_adapter, load_unit, stage_keys  # noqa: E402

SRC = SCIENCE / "smart_building_conformal" / "src"
POLICY_FIELDS = ("method", "level", "strategy", "every", "window")


def extension_blocks(adapter) -> list[list[dict]]:
    """Group the unavailable candidates exactly as the frozen policy_blocks groups ready ones."""
    groups: dict[tuple, list[dict]] = {}
    for candidate in adapter.candidates():
        if candidate["method"] in {"cqr", "quantile_uncalibrated"} and float(candidate["level"]) in LEVELS:
            key = tuple(candidate[name] for name in POLICY_FIELDS)
            groups.setdefault(key, []).append(candidate)
    blocks = [sorted(rows, key=lambda item: item["candidate_id"])
              for _, rows in sorted(groups.items(), key=lambda item: str(item[0]))]
    if len(blocks) != BLOCKS_PER_UNIT or sum(map(len, blocks)) != 99 or any(len(rows) != 3 for rows in blocks):
        raise ValueError("extension policy block matrix changed")
    with (FROZEN / "evaluation_queue.csv").open(encoding="utf-8") as handle:
        queue = list(csv.DictReader(handle))
    unavailable = {row["candidate_id"] for row in queue if row["execution_status"] == "unavailable_missing_saved_owner"}
    ready = {row["candidate_id"] for row in queue if row["execution_status"] == "ready"}
    ids = {row["candidate_id"] for rows in blocks for row in rows}
    if ids != unavailable or ids & ready or len(ids | ready) != 264:
        raise ValueError("extension candidates differ from the frozen unavailable queue")
    return blocks


def mapie_alpha(level: float) -> float:
    """MAPIE 1.4.1 stores alpha = 1 - confidence_level computed in decimal arithmetic."""
    from decimal import Decimal
    return float(Decimal("1") - Decimal(str(level)))


class ExtensionOwner:
    """Saved-owner view of a hash-verified extension CQR owner (no fitting here)."""

    fitted_models = 0

    def __init__(self, adapter, fold: int, seed: int, level: float, data, roles):
        from src.intervals005_common import load_owner
        unit = unit_name(fold, seed)
        root = OWNERS / unit
        validation = root / "OWNER_VALIDATION.json"
        if not validation.exists() or not read(validation).get("passed"):
            raise ValueError("extension owner has not passed independent validation")
        manifest = read(root / "OWNER_MANIFEST.json")
        tag = level_tag(level)
        record = manifest["levels"][tag]
        for key, stage in record["stages"].items():
            path = RUN_ROOT / stage["path"]
            if tree(path) != stage["files"]:
                raise ValueError(f"extension owner checkpoint changed: {key}")
        _, cal_key, raw_key = stage_keys(level)
        owner_path = root / "stages" / cal_key / "owner.pkl"
        raw = root / "stages" / raw_key
        if digest(owner_path) != record["calibrated_owner_sha256"]:
            raise ValueError("extension owner hash mismatch")
        self.method = "cqr"
        self.owner_kind = "cqr"
        self.level = float(level)
        self.columns = list(data["X"].columns)
        self.m = load_owner(owner_path)
        if float(self.m._alpha) != mapie_alpha(level):
            raise ValueError("extension owner nominal level mismatch")
        metadata = adapter.frame(raw / "calibration_metadata.csv.gz")
        values = adapter.frame(raw / f"calibration_{tag}.csv.gz")
        expected = adapter.role_frame(data, roles["calibration"])
        if list(metadata.row_id.astype(str)) != list(expected.row_id.astype(str)):
            raise ValueError("extension calibration row identity mismatch")
        np.testing.assert_allclose(metadata.y_true, expected.y_true, rtol=0, atol=1e-12)
        if len(values) != len(metadata):
            raise ValueError("extension calibration prediction length mismatch")
        score = np.maximum(values.raw_lower.to_numpy() - metadata.y_true.to_numpy(),
                           metadata.y_true.to_numpy() - values.raw_upper.to_numpy())
        if not np.isfinite(score).all():
            raise ValueError("extension calibration score is nonfinite")
        self.calibration = metadata[["group_id", "target_time"]].copy()
        self.calibration["group_id"] = self.calibration.group_id.astype(str)
        self.calibration["score"] = score
        protocol_dir, output_dir = adapter.bundle_paths(fold, seed)
        common = output_dir / "stages" / "dscp_joint" / "test_h1.csv.gz"
        self.reference = {
            "available": True,
            "reason": "",
            "owner_kind": "cqr",
            "owner": {"root": str(RUN_ROOT), "path": owner_path.relative_to(RUN_ROOT).as_posix(),
                      "sha256": record["calibrated_owner_sha256"], "bytes": owner_path.stat().st_size},
            "fitted_owner_sha256": record["fitted_owner_sha256"],
            "calibration_metadata": {"root": str(RUN_ROOT),
                                     "path": (raw / "calibration_metadata.csv.gz").relative_to(RUN_ROOT).as_posix(),
                                     "sha256": record["calibration_metadata_sha256"]},
            "calibration_values": {"root": str(RUN_ROOT),
                                   "path": (raw / f"calibration_{tag}.csv.gz").relative_to(RUN_ROOT).as_posix(),
                                   "sha256": record["calibration_values_sha256"]},
            "interval_protocol": (protocol_dir / "frozen_protocol.json").relative_to(adapter.REPO).as_posix(),
            "interval_protocol_sha256": digest(protocol_dir / "frozen_protocol.json"),
            "common_support": common.relative_to(adapter.REPO).as_posix(),
            "common_support_sha256": digest(common),
            "evaluated_source_hash": source_content_digest(SRC),
            "extension_owner_manifest_sha256": digest(root / "OWNER_MANIFEST.json"),
            "extension_owner_validation_sha256": digest(validation),
        }
        self.fit_identity = signature({
            "owner_sha256": record["calibrated_owner_sha256"],
            "calibration_sha256": record["calibration_values_sha256"],
            "method": "cqr",
            "level": level,
            "columns": self.columns,
        })
        self.identity = {
            "estimator_class": type(self.m).__module__ + "." + type(self.m).__name__,
            "method": "cqr",
            "level": level,
            "restored_owner_sha256": record["calibrated_owner_sha256"],
            "calibration_sha256": record["calibration_values_sha256"],
            "fitted_models": 0,
            "owner_fitted_in_extension_stage": stage_keys(level)[0],
        }

    def raw(self, X):
        from src.intervals005_owners import raw_predictions
        if list(X.columns) != self.columns:
            raise ValueError("prediction feature schema mismatch")
        output = raw_predictions(self.m, self.owner_kind, X.to_numpy(), [self.level])[self.level]
        return {name: output[name].to_numpy(float) for name in
                ("point", "raw_lower", "raw_upper", "static_lower", "static_upper")}


class FittingDisabled:
    """Make any estimator or calibrator fit raise while a replay block runs."""

    def __enter__(self):
        from mapie.regression import ConformalizedQuantileRegressor, TimeSeriesRegressor
        from mapie.regression.quantile_regression import _MapieQuantileRegressor
        from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
        from xgboost import XGBRegressor
        self.saved = []
        targets = [(HistGradientBoostingRegressor, "fit"), (RandomForestRegressor, "fit"), (XGBRegressor, "fit"),
                   (ConformalizedQuantileRegressor, "fit"), (ConformalizedQuantileRegressor, "conformalize"),
                   (TimeSeriesRegressor, "fit"), (TimeSeriesRegressor, "conformalize"),
                   (_MapieQuantileRegressor, "fit"), (_MapieQuantileRegressor, "conformalize")]
        for cls, name in targets:
            self.saved.append((cls, name, cls.__dict__.get(name)))

            def refuse(*args, _name=f"{cls.__name__}.{name}", **kwargs):
                raise AssertionError(f"fitting/calibration forbidden in a replay block: {_name}")
            setattr(cls, name, refuse)
        return self

    def __exit__(self, *exc):
        for cls, name, original in reversed(self.saved):
            if original is None:
                delattr(cls, name)
            else:
                setattr(cls, name, original)


def install(fold: int, seed: int):
    extension = verify_extension_protocol(fold=fold, seed=seed)
    adapter = frozen_adapter()
    frozen_version = adapter.VERSION
    blocks = extension_blocks(adapter)
    adapter.policy_blocks = lambda: blocks
    adapter.UNITS = UNITS
    adapter.load_unit = lambda f, s: load_unit(adapter, f, s, extension["source_content_digest"])

    def owner_factory(f, s, method, level, data, roles):
        if method != "cqr" or (f, s) != (fold, seed):
            raise ValueError("extension owner request outside the CQR/quantile scope")
        return ExtensionOwner(adapter, f, s, level, data, roles)

    adapter.SavedOwner = owner_factory
    adapter.source_digest = lambda: source_content_digest(SRC)
    adapter.VERSION = f"{frozen_version}+{VERSION}"
    return adapter, blocks


def run_block(fold: int, seed: int, block_index: int) -> dict:
    adapter, blocks = install(fold, seed)
    if not 0 <= block_index < len(blocks):
        raise ValueError("unknown extension policy block")
    with FittingDisabled():
        result = adapter.run_block(fold, seed, block_index)
    print(json.dumps({"status": result.get("status", "complete"), "unit": unit_name(fold, seed),
                      "block_index": block_index}, default=str))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["run-block", "list-blocks"])
    parser.add_argument("--fold", type=int, choices=[0, 1, 2], default=0)
    parser.add_argument("--model-seed", type=int, choices=[42, 43, 44, 45, 46], default=42)
    parser.add_argument("--block-index", type=int)
    args = parser.parse_args()
    if args.action == "list-blocks":
        _, blocks = install(args.fold, args.model_seed)
        for index, rows in enumerate(blocks):
            print(index, {k: rows[0][k] for k in POLICY_FIELDS}, [r["candidate_id"] for r in rows])
    else:
        run_block(args.fold, args.model_seed, args.block_index)
