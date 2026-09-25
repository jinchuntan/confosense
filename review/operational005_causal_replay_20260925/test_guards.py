"""Small zero-fit guard fixtures; never a substitute for scientific rules."""
from __future__ import annotations

import copy
import math
import unittest


def validate(record, expected):
    for key in ("candidate_id", "fault_id", "outer_fold", "model_seed", "level", "method", "strategy"):
        if record[key] != expected[key]:
            raise ValueError(f"wrong_{key}_ownership")
    if record["released_target_time"] > record["issue_time"]:
        raise ValueError("future_released_residual")
    if record["feature_hash_before"] != record["feature_hash_after"] and not record["declared_feature_fault"]:
        raise ValueError("changed_features_without_declared_fault")
    if record["forecast_hash_before"] != record["forecast_hash_after"] and not record["declared_feature_fault"]:
        raise ValueError("changed_forecast_without_declared_fault")
    if record["row_id_before"] != record["row_id_after"]:
        raise ValueError("mutated_row_identity")
    if record["available"] != record["expected_available"]:
        raise ValueError("mutated_availability")
    if record["segment_id"] != record["expected_segment_id"]:
        raise ValueError("incorrect_segment_boundary")
    if record["support"] != record["expected_support"]:
        raise ValueError("native_common_cohort_mismatch")
    if record["lower"] > record["upper"]:
        raise ValueError("tampered_conformalized_bounds")
    if record["completed_exists"]:
        raise ValueError("overwrite_completed_replay")


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.expected = dict(candidate_id="c1", fault_id="f1", outer_fold=0, model_seed=42,
                             level=.95, method="cqr", strategy="static")
        self.base = dict(self.expected, released_target_time=1, issue_time=1,
                         feature_hash_before="a", feature_hash_after="a",
                         forecast_hash_before="b", forecast_hash_after="b",
                         declared_feature_fault=False, row_id_before="r", row_id_after="r",
                         available=True, expected_available=True, segment_id="s",
                         expected_segment_id="s", support="native", expected_support="native",
                         lower=0., upper=1., completed_exists=False)

    def reject(self, field, value, message):
        item = copy.deepcopy(self.base); item[field] = value
        with self.assertRaisesRegex(ValueError, message):
            validate(item, self.expected)

    def test_wrong_candidate_fault_owner(self):
        self.reject("candidate_id", "c2", "wrong_candidate_id_ownership")

    def test_wrong_fold_seed_level_method_policy(self):
        for field, value in (("outer_fold", 1), ("model_seed", 43), ("level", .99),
                             ("method", "recentred_enbpi"), ("strategy", "rolling")):
            self.reject(field, value, f"wrong_{field}_ownership")

    def test_future_leakage(self): self.reject("released_target_time", 2, "future_released_residual")
    def test_changed_features(self): self.reject("feature_hash_after", "x", "changed_features_without_declared_fault")
    def test_changed_forecast(self): self.reject("forecast_hash_after", "x", "changed_forecast_without_declared_fault")
    def test_row_identity(self): self.reject("row_id_after", "x", "mutated_row_identity")
    def test_availability(self): self.reject("available", False, "mutated_availability")
    def test_segment(self): self.reject("segment_id", "x", "incorrect_segment_boundary")
    def test_cohort(self): self.reject("support", "common", "native_common_cohort_mismatch")
    def test_bounds(self): self.reject("lower", 2., "tampered_conformalized_bounds")
    def test_completed_overwrite(self): self.reject("completed_exists", True, "overwrite_completed_replay")

    def test_duplicate_alias_counting(self):
        rows = [("u1", False), ("u1", False)]
        primary = [key for key, alias in rows if not alias]
        self.assertNotEqual(len(primary), len(set(primary)))

    def test_ieee754_boundary_survives_evidence_roundtrip(self):
        observed = 0.0007
        lower = math.nextafter(observed, math.inf)
        self.assertTrue(observed < lower)
        self.assertEqual(float.fromhex(observed.hex()), observed)
        self.assertEqual(float.fromhex(lower.hex()), lower)
        self.assertTrue(float.fromhex(observed.hex()) < float.fromhex(lower.hex()))

    def test_tampered_exact_bound_is_rejected(self):
        lower = math.nextafter(0.0007, math.inf)
        with self.assertRaisesRegex(ValueError, "tampered_conformalized_bounds"):
            validate(dict(self.base, lower=float.fromhex(lower.hex()), upper=0.0007), self.expected)

    def test_unavailable_nan_hex_token_is_parseable(self):
        self.assertEqual(float("nan").hex(), "nan")
        self.assertTrue(math.isnan(float.fromhex("nan")))

    def test_empty_decimal_unavailable_token_is_parseable(self):
        values = [float(value) if value else float("nan") for value in ("", "0.0007")]
        self.assertTrue(math.isnan(values[0]))
        self.assertEqual(values[1], 0.0007)


if __name__ == "__main__":
    unittest.main()
