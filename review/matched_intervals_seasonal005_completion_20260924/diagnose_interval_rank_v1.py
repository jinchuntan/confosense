"""Zero-fit diagnosis of the saved seed-46 EnbPI quantile-rank mismatch."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
import math
import os
from pathlib import Path
import warnings

import numpy as np
import pandas as pd

from adapter import REPO, SMART
from corrected_validator_v1 import (
    VERSION, FROZEN_VALIDATOR_SHA256, corrected_source_sha256,
    mapie_alpha, mapie_asymmetric_arguments, mapie_quantile_probability,
)
from src.intervals005_common import Operations, atomic, digest, frame, load_owner, packages, read, tree
from src.intervals005_data import load_data, role_frame


RUN = SMART / "outputs/matched_intervals005/bdg2_f0_s46_method_completion_v1"
DESIGN = SMART / "protocols/matched_intervals005/bdg2_f0_s46_method_completion_v1"
FAILED_LOG = SMART / (
    "outputs/matched_intervals005/completion_52_v1_coordinator/attempts/"
    "2026-09-23T225509679650+0000_e0411b9e/command.log"
)
MAPIE_UTILS = Path(r"C:\cfs_venv\Lib\site-packages\mapie\utils.py")
MAPIE_INTERFACE = Path(r"C:\cfs_venv\Lib\site-packages\mapie\conformity_scores\interface.py")
LEVELS = (0.9, 0.95)


def lower_quantile(sorted_values: np.ndarray, probability: float) -> tuple[float, int]:
    """Independent scalar implementation of numpy's one-dimensional lower quantile."""
    index = int(math.floor(probability * (len(sorted_values) - 1)))
    return float(sorted_values[index]), index


def probability_records(level: float, n: int, symmetric: bool) -> list[dict]:
    ordinary_alpha = 1 - level
    decimal_alpha = mapie_alpha(level)
    if symmetric:
        arguments = [("lower", level, False), ("upper", level, False)]
        mapie_arguments = [("lower", level, False), ("upper", level, False)]
    else:
        ordinary_beta = ordinary_alpha / 2
        beta_np, upper_np = mapie_asymmetric_arguments(level)
        arguments = [("lower", ordinary_beta, True), ("upper", 1 - ordinary_beta, False)]
        mapie_arguments = [("lower", beta_np, True), ("upper", upper_np, False)]
    rows = []
    for (bound, ordinary_argument, reverse), (_, mapie_argument, _) in zip(arguments, mapie_arguments):
        ordinary_probability = 1 - ordinary_argument if reverse else ordinary_argument
        mapie_probability = mapie_quantile_probability(mapie_argument, reverse)
        ordinary_numerator = int(math.ceil(ordinary_probability * (n + 1)))
        mapie_numerator = int(math.ceil(mapie_probability * (n + 1)))
        ordinary_corrected = min(1.0, max(0.0, ordinary_numerator / n))
        mapie_corrected = min(1.0, max(0.0, mapie_numerator / n))
        rows.append(dict(
            bound=bound,
            reversed=reverse,
            level=level,
            level_repr=repr(level),
            level_hex=level.hex(),
            ordinary_alpha_repr=repr(ordinary_alpha),
            ordinary_alpha_hex=ordinary_alpha.hex(),
            decimal_alpha_repr=repr(decimal_alpha),
            decimal_alpha_hex=decimal_alpha.hex(),
            ordinary_quantile_argument_repr=repr(ordinary_argument),
            mapie_quantile_argument_repr=repr(mapie_argument),
            ordinary_probability_repr=repr(ordinary_probability),
            ordinary_probability_hex=ordinary_probability.hex(),
            mapie_probability_repr=repr(mapie_probability),
            mapie_probability_hex=mapie_probability.hex(),
            n_finite=n,
            ordinary_ceiling_numerator=ordinary_numerator,
            mapie_ceiling_numerator=mapie_numerator,
            ordinary_corrected_probability_repr=repr(ordinary_corrected),
            mapie_corrected_probability_repr=repr(mapie_corrected),
        ))
    return rows


def signed_quantile(sorted_scores: np.ndarray, probability: float, reverse: bool) -> tuple[float, int]:
    signed = -1 if reverse else 1
    signed_sorted = np.sort(signed * sorted_scores)
    value, signed_index = lower_quantile(signed_sorted, probability)
    original_index = len(sorted_scores) - 1 - signed_index if reverse else signed_index
    return signed * value, original_index


def diff_stats(actual: np.ndarray, expected: np.ndarray, tolerance=1e-7) -> dict:
    delta = np.asarray(actual, float) - np.asarray(expected, float)
    return dict(
        rows=int(delta.size),
        differing_rows=int(np.count_nonzero(np.abs(delta) > tolerance)),
        exact_equal_rows=int(np.count_nonzero(delta == 0)),
        minimum_difference=float(np.min(delta)),
        maximum_difference=float(np.max(delta)),
        maximum_absolute_difference=float(np.max(np.abs(delta))),
        unique_difference_count=int(np.unique(delta).size),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    receipt = Path(args.receipt).resolve()
    if receipt.exists():
        raise ValueError("preserve existing diagnosis; use a new receipt directory")
    receipt.mkdir(parents=True)

    protocol = read(DESIGN / "frozen_protocol.json")
    before_tree = tree(RUN)
    before_ops = digest(RUN / "operations.jsonl")
    boundary_rows, summary_rows, all_rows = [], [], []
    prepared = None

    with Operations(forbid=True):
        for horizon in protocol["scope"]["horizons"]:
            data, roles, prepared = load_data(protocol["references"][str(horizon)], prepared)
            calibration_meta = role_frame(data, roles["calibration"])
            test_meta = role_frame(data, roles["test"])
            stage = RUN / "stages"
            owner = load_owner(stage / f"owner_cal_h{horizon}_enbpi/owner.pkl")
            saved_scores = np.load(stage / f"owner_cal_h{horizon}_enbpi/native_conformity_scores.npy")
            np.testing.assert_allclose(saved_scores, owner.conformity_scores_, atol=0, rtol=0, equal_nan=True)

            raw_path = stage / f"raw_h{horizon}_enbpi"
            saved_cal_meta = frame(raw_path / "calibration_metadata.csv.gz")
            saved_test_meta = frame(raw_path / "test_metadata.csv.gz")
            if list(saved_cal_meta.row_id) != list(calibration_meta.row_id):
                raise ValueError("original calibration identity mismatch")
            if list(saved_test_meta.row_id) != list(test_meta.row_id):
                raise ValueError("original test identity mismatch")

            X_cal = data["X"].iloc[roles["calibration"]].to_numpy()
            predictions = np.column_stack(
                [estimator.predict(X_cal) for estimator in owner.estimator_.estimators_]
            ).astype(np.float64)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                oob = np.nanmean(np.where(owner.estimator_.k_ == 1, predictions, np.nan), axis=1)
            reconstructed_scores = calibration_meta.y_true.to_numpy() - oob
            if owner.conformity_score_function_.sym:
                reconstructed_scores = np.abs(reconstructed_scores)
            np.testing.assert_allclose(
                owner.conformity_scores_, reconstructed_scores, atol=1e-7, rtol=1e-7,
                equal_nan=True,
            )
            finite = np.asarray(owner.conformity_scores_)[np.isfinite(owner.conformity_scores_)]
            sorted_scores = np.sort(finite)

            X_test = data["X"].iloc[roles["test"]].to_numpy()
            native_point = owner.estimator_.single_estimator_.predict(X_test).astype(np.float64)
            ensemble_point, native_intervals = owner.predict(
                X_test, ensemble=True, confidence_level=list(LEVELS)
            )
            native_intervals = np.asarray(native_intervals)
            shift = native_point - np.asarray(ensemble_point).ravel()

            for level_index, level in enumerate(LEVELS):
                records = probability_records(
                    level, len(finite), bool(owner.conformity_score_function_.sym)
                )
                quantiles = {}
                for record in records:
                    ordinary_corrected = float(record["ordinary_corrected_probability_repr"])
                    mapie_corrected = float(record["mapie_corrected_probability_repr"])
                    ordinary_q, ordinary_index = signed_quantile(
                        sorted_scores, ordinary_corrected, bool(record["reversed"])
                    )
                    corrected_q, corrected_index = signed_quantile(
                        sorted_scores, mapie_corrected, bool(record["reversed"])
                    )
                    record.update(
                        horizon=horizon,
                        score_symmetry=bool(owner.conformity_score_function_.sym),
                        score_count=int(np.asarray(owner.conformity_scores_).size),
                        finite_score_count=int(len(finite)),
                        nonfinite_score_count=int(np.count_nonzero(~np.isfinite(owner.conformity_scores_))),
                        nan_score_count=int(np.count_nonzero(np.isnan(owner.conformity_scores_))),
                        positive_infinity_count=int(np.count_nonzero(np.isposinf(owner.conformity_scores_))),
                        negative_infinity_count=int(np.count_nonzero(np.isneginf(owner.conformity_scores_))),
                        ordinary_selected_rank_one_based=ordinary_index + 1,
                        mapie_selected_rank_one_based=corrected_index + 1,
                        rank_difference=corrected_index - ordinary_index,
                        ordinary_residual=ordinary_q,
                        mapie_residual=corrected_q,
                        residual_difference=corrected_q - ordinary_q,
                        lower_neighbour=(float(sorted_scores[min(ordinary_index, corrected_index) - 1])
                                         if min(ordinary_index, corrected_index) > 0 else None),
                        upper_neighbour=(float(sorted_scores[max(ordinary_index, corrected_index) + 1])
                                         if max(ordinary_index, corrected_index) + 1 < len(sorted_scores) else None),
                    )
                    boundary_rows.append(record)
                    quantiles[record["bound"]] = (ordinary_q, corrected_q)

                saved = frame(raw_path / f"test_{int(level * 100)}.csv.gz")
                saved_point = saved.point.to_numpy(np.float32).astype(np.float64)
                np.testing.assert_array_equal(saved_point, native_point)
                ordinary_lower_q, corrected_lower_q = quantiles["lower"]
                ordinary_upper_q, corrected_upper_q = quantiles["upper"]
                independent_lower = native_point + corrected_lower_q
                independent_upper = native_point + corrected_upper_q
                ordinary_lower = native_point + ordinary_lower_q
                ordinary_upper = native_point + ordinary_upper_q
                production_lower = native_intervals[:, 0, level_index] + shift
                production_upper = native_intervals[:, 1, level_index] + shift

                np.testing.assert_allclose(saved.static_lower, independent_lower, atol=1e-7, rtol=1e-7)
                np.testing.assert_allclose(saved.static_upper, independent_upper, atol=1e-7, rtol=1e-7)
                np.testing.assert_allclose(saved.static_lower, production_lower, atol=1e-7, rtol=1e-7)
                np.testing.assert_allclose(saved.static_upper, production_upper, atol=1e-7, rtol=1e-7)

                for bound, actual, corrected, ordinary, production in (
                    ("lower", saved.static_lower.to_numpy(), independent_lower, ordinary_lower, production_lower),
                    ("upper", saved.static_upper.to_numpy(), independent_upper, ordinary_upper, production_upper),
                ):
                    row = dict(horizon=horizon, level=level, bound=bound)
                    row.update({"saved_vs_corrected_" + k: v for k, v in diff_stats(actual, corrected).items()})
                    row.update({"saved_vs_ordinary_" + k: v for k, v in diff_stats(actual, ordinary).items()})
                    row.update({"saved_vs_restored_native_" + k: v for k, v in diff_stats(actual, production).items()})
                    summary_rows.append(row)

                all_rows.append(pd.DataFrame(dict(
                    horizon=horizon,
                    level=level,
                    row_id=test_meta.row_id,
                    saved_lower=saved.static_lower,
                    saved_upper=saved.static_upper,
                    corrected_lower=independent_lower,
                    corrected_upper=independent_upper,
                    ordinary_lower=ordinary_lower,
                    ordinary_upper=ordinary_upper,
                    saved_minus_corrected_lower=saved.static_lower.to_numpy() - independent_lower,
                    saved_minus_corrected_upper=saved.static_upper.to_numpy() - independent_upper,
                    saved_minus_ordinary_lower=saved.static_lower.to_numpy() - ordinary_lower,
                    saved_minus_ordinary_upper=saved.static_upper.to_numpy() - ordinary_upper,
                )))

    after_tree = tree(RUN)
    after_ops = digest(RUN / "operations.jsonl")
    if after_tree != before_tree or after_ops != before_ops:
        raise ValueError("zero-fit diagnosis mutated saved scientific artifacts")

    boundary = pd.DataFrame(boundary_rows)
    summaries = pd.DataFrame(summary_rows)
    differences = pd.concat(all_rows, ignore_index=True)
    boundary.to_csv(receipt / "rank_boundaries.csv", index=False)
    summaries.to_csv(receipt / "bound_comparison_summary.csv", index=False)
    differences.to_csv(
        receipt / "all_row_differences.csv.gz", index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    diagnosis = dict(
        passed=True,
        established_cause="frozen validator floating-point rank reconstruction defect",
        rank_difference_fully_explains_saved_offset=bool(
            (summaries["saved_vs_corrected_differing_rows"] == 0).all()
            and (summaries["saved_vs_restored_native_differing_rows"] == 0).all()
        ),
        correction_version=VERSION,
        frozen_validator_sha256=FROZEN_VALIDATOR_SHA256,
        corrected_validator_source_sha256=corrected_source_sha256(),
        mapie_version=packages()["mapie"],
        mapie_utils_sha256=digest(MAPIE_UTILS),
        mapie_interface_sha256=digest(MAPIE_INTERFACE),
        failed_log=str(FAILED_LOG.relative_to(REPO)),
        failed_log_sha256=digest(FAILED_LOG),
        protocol_sha256=digest(DESIGN / "frozen_protocol.json"),
        complete_manifest_sha256=digest(RUN / "COMPLETE.json"),
        operations_sha256_before=before_ops,
        operations_sha256_after=after_ops,
        scientific_tree_unchanged=True,
        fitting_forbidden=True,
        models_fitted=0,
        calibrators_fitted=0,
        tolerances_unchanged=True,
        boundary_rows=boundary_rows,
        bound_summary_rows=summary_rows,
        all_row_difference_rows=len(differences),
    )
    atomic(receipt / "diagnosis.json", diagnosis)
    atomic(receipt / "COMPLETE.json", {"files": tree(receipt)})
    print(json.dumps(diagnosis, indent=2), flush=True)


if __name__ == "__main__":
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(variable, "1")
    main()
