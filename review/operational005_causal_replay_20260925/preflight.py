"""Zero-fit saved-owner and exact-queue gate before the first real replay."""
from __future__ import annotations

import json
import time
from unittest.mock import patch

import numpy as np
import pandas as pd
from mapie.regression import ConformalizedQuantileRegressor, TimeSeriesRegressor
from xgboost import XGBRegressor

from adapter import SavedOwner, load_unit, policy_blocks
from common import HERE, SOURCE_HASH, atomic_json, bundle_paths, digest, owner_reference
from src.intervals005_common import source_digest


def forbidden(*args, **kwargs):
    raise AssertionError("fit or conformalize forbidden by operational005 preflight")


def run() -> dict:
    started = time.perf_counter()
    if source_digest() != SOURCE_HASH:
        raise ValueError("scientific source digest changed")
    owner_checks = []
    for fold in range(3):
        for seed in range(42, 47):
            protocol, output = bundle_paths(fold, seed)
            for method, level in (("cqr", .95), ("quantile_uncalibrated", .95),
                                  ("recentred_enbpi", .95), ("recentred_enbpi", .995)):
                ref = owner_reference(fold, seed, method, level)
                if not ref["available"]:
                    raise ValueError("required saved owner unexpectedly unavailable")
                owner_checks.append({
                    "outer_fold": fold, "model_seed": seed, "method": method, "level": level,
                    "owner_sha256": ref["owner"]["sha256"], "protocol_sha256": ref["interval_protocol_sha256"],
                })
            for method in ("cqr", "quantile_uncalibrated"):
                if owner_reference(fold, seed, method, .975)["available"]:
                    raise ValueError("missing high-level quantile owner was silently substituted")

    with patch.object(ConformalizedQuantileRegressor, "fit", forbidden), \
         patch.object(ConformalizedQuantileRegressor, "conformalize", forbidden), \
         patch.object(TimeSeriesRegressor, "fit", forbidden), \
         patch.object(TimeSeriesRegressor, "conformalize", forbidden), \
         patch.object(XGBRegressor, "fit", forbidden):
        _, data, roles, _ = load_unit(0, 42)
        rows = roles["test"][:64]
        X = data["X"].iloc[rows].reset_index(drop=True)
        numerical = []
        for method, level, raw_stage in (
            ("cqr", .95, "raw_h1_cqr_l95"),
            ("recentred_enbpi", .95, "raw_h1_enbpi"),
        ):
            owner = SavedOwner(0, 42, method, level, data, roles)
            actual = owner.raw(X)
            _, output = bundle_paths(0, 42)
            expected = pd.read_csv(output / "stages" / raw_stage / "test_95.csv.gz", nrows=64)
            maximum = 0.
            for key in ("point", "raw_lower", "raw_upper", "static_lower", "static_upper"):
                difference = float(np.max(np.abs(actual[key] - expected[key].to_numpy())))
                maximum = max(maximum, difference)
                np.testing.assert_allclose(actual[key], expected[key], rtol=1e-7, atol=1e-7)
            numerical.append({"method": method, "level": level, "rows": len(X), "maximum_absolute_difference": maximum})
        high = SavedOwner(0, 42, "recentred_enbpi", .995, data, roles).raw(X)
        if not all(np.isfinite(high[key]).all() for key in high):
            raise ValueError("saved EnbPI owner cannot project the frozen 99.5% level")

    result = {
        "passed": True,
        "models_fitted": 0,
        "conformalizers_fitted": 0,
        "scientific_source_hash": source_digest(),
        "policy_blocks_per_unit": len(policy_blocks()),
        "ready_candidates_per_unit": sum(map(len, policy_blocks())),
        "saved_owner_hash_checks": len(owner_checks),
        "saved_prediction_checks": numerical,
        "saved_enbpi_high_level_projection_finite": True,
        "missing_high_level_quantile_owners_rejected": True,
        "elapsed_seconds": time.perf_counter() - started,
    }
    atomic_json(HERE / "PREFLIGHT.json", result)
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
