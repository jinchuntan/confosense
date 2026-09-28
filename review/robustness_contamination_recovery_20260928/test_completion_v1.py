"""Focused zero-fit tests for the authorized completion layer."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
SMART = HERE.parents[1] / "smart_building_conformal"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(SMART))
import completion_v1 as C  # noqa: E402
import completion_runtime_v1 as R  # noqa: E402
import completion_validate_v1 as V  # noqa: E402


def test_frozen_scope_and_exact_missing_owner_budget():
    frame = C.crosswalk(); missing = frame[frame.interval_owner_support != "exact_saved_owner"]
    assert len(frame) == 60 and frame.historical_obligation_cells.astype(int).sum() == 900
    assert len(missing) == 8
    assert missing.missing_owner_estimator_fits.astype(int).sum() == 24
    assert missing.missing_owner_conformalizations.astype(int).sum() == 8
    assert set(missing.historical_level.astype(float)) == {.975, .99, .995}


def test_high_level_contamination_quantiles_are_not_fixed_to_095():
    residual = np.arange(400, dtype=float)
    lo95, hi95 = V._quantiles(residual, .95)
    lo995, hi995 = V._quantiles(residual, .995)
    assert lo995 < lo95 and hi995 > hi95


def test_dynamic_group_operation_accounting_and_corruption_rejected():
    counts = {
        "historical_obligation_cells": 15, "unique_corrupted_feature_rebuilds": 8,
        "unique_saved_owner_inference_passes": 9, "emitted_cell_streams": 15,
        "contamination_reconstructions": 3, "nonzero_contamination_reconstructions": 2,
        "recovery_policy_computations": 3, "group_recovery_rows": 9,
        "point_metric_rows_from_saved_predictions": 2, "model_fits": 0,
        "conformalize_calls": 0, "new_seeds": 0,
    }
    V.validate_operations({"operation_counts": counts}, groups=3)
    with pytest.raises(ValueError, match="group_recovery_rows"):
        V.validate_operations({"operation_counts": dict(counts, group_recovery_rows=10)}, groups=3)


def test_feature_evidence_rejects_deliberately_corrupted_hash():
    masks = {"pre": np.array([True, False, False])}
    clean = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
    features = {"clean": (clean, np.array([1.0, 2.0, 3.0]))}
    for name in ("zero_control", "random_missing@na", "dropout@na", "stuck@na",
                 "level_shift@1.0", "level_shift@2.0", "drift@1.0", "drift@2.0"):
        changed = clean.copy()
        if name != "zero_control": changed.loc[2, "x"] += 1.0
        features[name] = (changed, np.array([1.0, 2.0, 3.0]))
    rows = []
    for name, (frame, observed) in features.items():
        changed = np.any(frame.to_numpy() != clean.to_numpy(), axis=1)
        rows.append({"stream": name, "feature_sha256": C.A.frame_hash(frame),
                     "observed_sha256": C.A.ordered_hash(map(float.hex, observed)),
                     "changed_feature_rows": int(changed.sum()),
                     "changed_pre_rows": int((changed & masks["pre"]).sum())})
    audit = pd.DataFrame(rows); V.validate_feature_evidence({"feature_audit": audit}, features, masks)
    audit.loc[audit.stream == "drift@2.0", "feature_sha256"] = "corrupt"
    with pytest.raises(ValueError, match="feature hash mismatch"):
        V.validate_feature_evidence({"feature_audit": audit}, features, masks)


def test_pleia_none_group_uses_raw_identity_for_fault_rebuild():
    row = C.selected_row("pleia_h1_f0_s42")
    _, data, roles, prepared = C.A.load_unit(row)
    test_rows = roles["test"]
    raw_meta = data["meta"].iloc[test_rows].reset_index(drop=True).copy()
    assert raw_meta.group_id.map(lambda value: value is None).all()
    clean = data["X"].iloc[test_rows].reset_index(drop=True)
    truth = np.asarray(data["y"])[test_rows]
    fcfg = C.windowing.feature_config(data["old_protocol"]["resolved_dataset_config"],
                                      prepared.series[0].covariates)
    scales = C.SI.training_scale(np.asarray(data["y"]), data["meta"], roles["fit"])
    windows = C.group_test_windows(data["meta"], test_rows, C.WINDOW_FRAC)
    rebuilt, observed = C.rebuild_test_fault(prepared, raw_meta, clean, windows, scales, fcfg,
                                             1, "level_shift", 0.0, 42)
    pd.testing.assert_frame_equal(rebuilt, clean, check_exact=True)
    np.testing.assert_array_equal(observed, truth)
    string_meta = raw_meta.copy(); string_meta["group_id"] = string_meta.group_id.astype(str)
    with pytest.raises(ValueError, match="lost frozen test identities"):
        C.rebuild_test_fault(prepared, string_meta, clean, windows, scales, fcfg,
                             1, "level_shift", 0.0, 42)


def test_missing_group_identity_is_canonical_for_recovery():
    times = pd.date_range("2026-01-01", periods=12, freq="h")
    windows = {np.nan: pd.DatetimeIndex(times[3:7])}
    events = C.fault_events(windows)
    assert events.group_id.tolist() == ["None"]
    stream = pd.DataFrame({
        "group_id": ["None"] * len(times), "target_time": times,
        "lower": np.zeros(len(times)), "upper": np.ones(len(times)),
    })
    groups, summary = V.V.independent_recovery(
        stream, np.full(len(times), .5), {C.group_label(np.nan): windows[np.nan]},
        pd.Timedelta(hours=1),
    )
    assert groups.group_id.tolist() == ["None"]
    assert summary["status"] == "descriptive_group_recovery"


def test_control_record_atomic_replace_retries_transient_access_denial(tmp_path, monkeypatch):
    destination = tmp_path / "progress.json"
    real_replace = R.os.replace
    calls = []

    def flaky_replace(source, target):
        calls.append((source, target))
        if len(calls) < 3:
            raise PermissionError("simulated transient OneDrive access denial")
        return real_replace(source, target)

    monkeypatch.setattr(R.os, "replace", flaky_replace)
    monkeypatch.setattr(R.time, "sleep", lambda _: None)
    R.atomic_json(destination, {"status": "running"})
    assert len(calls) == 3
    assert R.read(destination) == {"status": "running"}


def test_rico_fault_rebuild_changes_only_outer_test_groups_without_fitting():
    row = C.selected_row("rico_h5_f0_s42")
    _, data, roles, prepared = C.A.load_unit(row)
    test_rows = roles["test"]
    meta = data["meta"].iloc[test_rows].reset_index(drop=True).copy()
    clean = data["X"].iloc[test_rows].reset_index(drop=True)
    truth = np.asarray(data["y"])[test_rows]
    fcfg = C.windowing.feature_config(data["old_protocol"]["resolved_dataset_config"],
                                      prepared.series[0].covariates)
    scales = C.SI.training_scale(np.asarray(data["y"]), data["meta"], roles["fit"])
    windows = C.group_test_windows(data["meta"], test_rows, C.WINDOW_FRAC)
    assert len(windows) == 43 and C._test_window(windows, "P1S1") is None
    rebuilt_zero, observed_zero = C.rebuild_test_fault(
        prepared, meta, clean, windows, scales, fcfg, 5, "level_shift", 0.0, 42)
    pd.testing.assert_frame_equal(rebuilt_zero, clean, check_exact=True)
    np.testing.assert_array_equal(observed_zero, truth)
    rebuilt_fault, _ = C.rebuild_test_fault(
        prepared, meta, clean, windows, scales, fcfg, 5, "level_shift", 2.0, 42)
    assert np.any(rebuilt_fault.to_numpy() != clean.to_numpy())


def test_checkpoint_pins_are_full_sha256_and_route_to_preserved_roots():
    contract = C.A.read(C.SCIENTIFIC_CONTRACT)
    for root_name in ("v2_root", "v4_root", "v5_root"):
        assert all(len(value) == 64 for value in contract[root_name]["accepted_unit_hashes"].values())
    assert C.checkpoint_location("pleia_h1_f0_s42")[0] == C.ACCEPTED_V4_ROOT
    assert C.checkpoint_location("rico_h5_f0_s42")[0] == C.ACCEPTED_V5_ROOT
