"""Zero-fit invariant tests for the versioned robustness saved-owner adapter."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
SMART = HERE.parents[1] / "smart_building_conformal"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(SMART))

import robustness_saved_owner_v1 as A  # noqa: E402
import validate_saved_owner_v1 as V  # noqa: E402


def _stream(cell: str, n: int = 8) -> pd.DataFrame:
    origin = pd.date_range("2024-01-01", periods=n, freq="1h")
    target = origin + pd.Timedelta(hours=1)
    return pd.DataFrame({
        "row_id": [f"r{i}" for i in range(n)], "group_id": "g",
        "origin_time": origin, "target_time": target, "cell": cell,
        "family": "clean", "feature_stream": cell, "recal_policy": "periodic",
        "y_clean": np.arange(n, dtype=float), "y_observed": np.arange(n, dtype=float),
        "point": np.arange(n, dtype=float), "lower": np.arange(n) - 1.0,
        "upper": np.arange(n) + 1.0, "covered_clean": True,
        "released_rows": np.arange(n),
        "latest_released_target": [pd.NaT, *target[:-1]],
    })


def test_zero_control_exact_and_corruption_rejected():
    clean = _stream("clean"); zero = _stream("zero_control")
    V.validate_zero_streams(pd.concat([clean, zero], ignore_index=True))
    corrupt = zero.copy(); corrupt.loc[3, "upper"] += .01
    with pytest.raises(AssertionError):
        V.validate_zero_streams(pd.concat([clean, corrupt], ignore_index=True))


def test_causal_feature_audit_rejects_pre_window_change():
    names = ["clean", "zero_control", "random_missing@na", "dropout@na", "stuck@na",
             "level_shift@1.0", "level_shift@2.0", "drift@1.0", "drift@2.0"]
    rows = [{"stream": name, "feature_sha256": "same" if name in {"clean", "zero_control"} else name,
             "observed_sha256": "same" if name in {"clean", "zero_control"} else name,
             "changed_feature_rows": 0 if name in {"clean", "zero_control"} else 2,
             "changed_pre_rows": 0} for name in names]
    V.validate_causal_audit(pd.DataFrame(rows))
    rows[-1]["changed_pre_rows"] = 1
    with pytest.raises(ValueError, match="pre-window"):
        V.validate_causal_audit(pd.DataFrame(rows))


def test_delayed_release_rejects_future_residual():
    stream = _stream("clean")
    V.validate_delayed_release(stream)
    stream.loc[3, "latest_released_target"] = pd.Timestamp(stream.loc[3, "origin_time"]) + pd.Timedelta(hours=1)
    with pytest.raises(ValueError, match="future residual"):
        V.validate_delayed_release(stream)


def test_calibration_only_contamination_rejects_test_identity():
    n = 20
    calibration = pd.DataFrame({"row_id": [f"c{i}" for i in range(n)], "group_id": "g",
                                "y_true": np.arange(n), "point": np.arange(n), "residual": 0.0})
    streams = _stream("contam@0.05", n=4); streams["family"] = "contamination"
    sigma = 2.0; evidence = []
    for rate, cell in ((.05, "contam@0.05"), (.10, "contam@0.1")):
        selected = np.random.default_rng(53).choice(n, size=int(round(rate * n)), replace=False)
        for index in selected:
            evidence.append({"cell": cell, "calibration_index": index,
                             "row_id": calibration.row_id.iloc[index], "group_id": "g",
                             "original_target": float(index), "contaminated_target": float(index) + 4,
                             "delta": 4.0, "train_only_pooled_sigma": sigma})
    evidence = pd.DataFrame(evidence)
    V.validate_contamination(evidence, calibration, streams, sigma)
    corrupt = evidence.copy(); corrupt.loc[0, "row_id"] = streams.row_id.iloc[0]
    with pytest.raises(ValueError, match="test identity"):
        V.validate_contamination(corrupt, calibration, streams, sigma)


def test_scalar_adaptive_bounds_respect_observation_delay():
    stream = _stream("clean", n=6)
    stream["point"] = 0.0
    stream["y_observed"] = [0, 0, 0, 100, 100, 100]
    calibration = pd.DataFrame({
        "group_id": "g", "target_time": pd.date_range("2023-01-01", periods=40, freq="1h"),
        "residual": np.zeros(40),
    })
    lower, upper = V.independent_adaptive_bounds(stream, calibration, .95, "native_updated")
    assert upper[3] == 0.0  # row 3's residual is unavailable at its own origin
    assert upper[5] > 0.0  # earlier shifted residuals have subsequently matured
    assert np.all(lower <= upper)


def test_group_recovery_preserves_right_censoring_and_rmst():
    n = 40; frame = _stream("recovery_static", n=n)
    frame["group_id"] = np.repeat(["a", "b"], n // 2)
    frame["lower"] = -1.0; frame["upper"] = 1.0
    truth = np.zeros(n); truth[15:20] = 5.0; truth[30:40] = 5.0
    windows = {
        "a": pd.DatetimeIndex(frame.loc[5:9, "target_time"]),
        "b": pd.DatetimeIndex(frame.loc[25:29, "target_time"]),
    }
    groups, summary = V.independent_recovery(frame.reset_index(drop=True), truth, windows, pd.Timedelta(hours=1))
    assert len(groups) == 2
    assert summary["groups"] == 2
    assert "restricted_mean_recovery_minutes" in summary
    assert summary["censored_groups"] >= 1


def test_operation_accounting_rejects_nested_double_count():
    counts = {
        "historical_obligation_cells": 15, "unique_corrupted_feature_rebuilds": 8,
        "unique_saved_owner_inference_passes": 9, "emitted_cell_streams": 15,
        "contamination_reconstructions": 3, "nonzero_contamination_reconstructions": 2,
        "recovery_policy_computations": 3, "group_recovery_rows": 30,
        "point_metric_rows_from_saved_predictions": 2, "model_fits": 0,
        "conformalize_calls": 0, "new_seeds": 0,
    }
    V.validate_operations({"operation_counts": counts})
    corrupt = dict(counts, unique_corrupted_feature_rebuilds=11)
    with pytest.raises(ValueError, match="operation-accounting"):
        V.validate_operations({"operation_counts": corrupt})


def test_fault_zero_definitions_remain_exact_identity():
    index = pd.date_range("2024-01-01", periods=40, freq="1h")
    frame = pd.DataFrame({"target": np.linspace(0, 1, 40)}, index=index)
    window = index[10:22]
    for kind in A.FAULT_TYPES:
        pd.testing.assert_frame_equal(A.apply_fault_to_frame(frame, window, kind, 0.0, 49), frame)
