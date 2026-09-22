"""Independent reconstruction of the prespecified five-seed inference."""
from __future__ import annotations

import json
import numpy as np
import pandas as pd

from common import *
from src.operational004_design import STRATA
from src.unit_checkpoint import signature


def frame(path):
    return pd.read_csv(path, float_precision="round_trip",
                       dtype={"context_id": str, "group_id": str, "original_segment_id": str, "segment_id": str})


def main():
    result = read(ANALYSIS / "validation.json")
    if not result["passed"] or result["model_seeds"] != list(ALL_SEEDS):
        raise ValueError("aggregate validation source missing")
    saved = frame(ANALYSIS / "original_context_seed_contributions.csv.gz")
    original = pd.concat([frame(run(seed) / "stages" / "tables" / "original_context_contributions.csv.gz") for seed in ALL_SEEDS], ignore_index=True)
    sort = ["model_seed", "control_id", "rule_id", "channel", "context_id", "family", "severity"]
    pd.testing.assert_frame_equal(saved.sort_values(sort).reset_index(drop=True), original.sort_values(sort).reset_index(drop=True),
                                  check_exact=False, rtol=0, atol=0)
    contexts = frame(SEED42_DESIGN / "contexts.csv").drop_duplicates("context_id").reset_index(drop=True)
    rng = np.random.default_rng(20240601); parts = []
    groups = [part.sort_values("onset").index.to_numpy() for _, part in contexts.groupby(["outer_fold", "segment_id"], sort=True)]
    if any(len(group) < 7 for group in groups) or sum(len(group) // 7 for group in groups) < 5:
        raise ValueError("seven-context chronological block support unavailable")
    for group in groups:
        starts = rng.integers(len(group) - 6, size=(2000, int(np.ceil(len(group) / 7))))
        parts.append(group[(starts[:, :, None] + np.arange(7)).reshape(2000, -1)[:, :len(group)]])
    draws = np.concatenate(parts, axis=1); design_meta = read(ANALYSIS / "bootstrap_design.json")
    if draws.tolist() != design_meta["draws"] or signature(draws.tolist()) != design_meta["draw_hash"]:
        raise ValueError("bootstrap draw identity mismatch")
    key = ["context_id", "control_id", "rule_id", "channel", "family", "severity"]
    pooled = original.groupby(key, as_index=False).recall.mean(); lookup = {value: index for index, value in enumerate(contexts.context_id)}
    checks = []; drawrows = []
    for cell, part in pooled.groupby(["control_id", "rule_id", "channel"], sort=True):
        values = np.full((len(contexts), 21), np.nan)
        for row in part.itertuples():
            values[lookup[row.context_id], STRATA.index((row.family, row.severity))] = row.recall
        sampled = values[draws]; counts = np.isfinite(sampled).sum(axis=1)
        means = np.divide(np.nansum(sampled, axis=1), counts, out=np.full_like(counts, np.nan, dtype=float), where=counts > 0)
        estimates = means.mean(axis=1); valid = estimates[np.isfinite(estimates)]; supported = len(valid) >= 1900 and np.ptp(valid) > 0
        point = float(np.nanmean(values, axis=0).mean())
        checks.append({"control_id": cell[0], "rule_id": cell[1], "channel": cell[2], "point": point,
                       "status": "supported" if supported else "unavailable_valid_draw_or_degenerate",
                       "valid_draws": len(valid), "lower": float(np.quantile(valid, .025)) if supported else np.nan,
                       "upper": float(np.quantile(valid, .975)) if supported else np.nan})
        drawrows.extend({"control_id": cell[0], "rule_id": cell[1], "channel": cell[2], "draw": index, "value": float(value)}
                        for index, value in enumerate(estimates))
    checks = pd.DataFrame(checks)
    bounds = frame(ANALYSIS / "inference_bounds.csv")
    points = frame(ANALYSIS / "five_seed_control_rule_channel.csv")
    merged = checks.merge(bounds, on=["control_id", "rule_id", "channel"], suffixes=("_independent", "_saved"), validate="one_to_one")
    np.testing.assert_allclose(merged.lower_independent, merged.lower_saved, atol=1e-15, rtol=1e-13, equal_nan=True)
    np.testing.assert_allclose(merged.upper_independent, merged.upper_saved, atol=1e-15, rtol=1e-13, equal_nan=True)
    pointcheck = checks.merge(points[["control_id", "rule_id", "channel", "conditional_context_detection"]],
                              on=["control_id", "rule_id", "channel"], validate="one_to_one")
    np.testing.assert_allclose(pointcheck.point, pointcheck.conditional_context_detection, atol=1e-15, rtol=1e-13)
    saved_draws = frame(ANALYSIS / "bootstrap_draw_estimates.csv.gz").sort_values(["control_id", "rule_id", "channel", "draw"]).reset_index(drop=True)
    independent_draws = pd.DataFrame(drawrows).sort_values(["control_id", "rule_id", "channel", "draw"]).reset_index(drop=True)
    np.testing.assert_allclose(saved_draws.value, independent_draws.value, atol=1e-15, rtol=1e-13)
    for seed in SEEDS:
        if not read(acceptance(seed))["passed"]:
            raise ValueError(f"seed {seed} not accepted")
    csv(ANALYSIS / "independent_inference_checks.csv", checks)
    receipt = {"passed": True, "utc": now(), "source_hash": source_digest(), "contribution_rows": len(original),
               "original_contexts": len(contexts), "model_seeds": list(ALL_SEEDS), "draw_seed": 20240601,
               "draws": 2000, "draw_shape": list(draws.shape), "draw_hash": signature(draws.tolist()),
               "cells": len(checks), "supported_bounds": int((checks.status == "supported").sum()),
               "unavailable_bounds": int((checks.status != "supported").sum()),
               "maximum_absolute_point_difference": float(np.max(np.abs(pointcheck.point - pointcheck.conditional_context_detection))),
               "maximum_absolute_bound_difference": float(np.nanmax(np.r_[np.abs(merged.lower_independent - merged.lower_saved), np.abs(merged.upper_independent - merged.upper_saved)])),
               "paired_draws_shared_across_controls": True, "chronological_adjacent_seven_context_blocks": True,
               "completed_resume_zero_fit_all_new_seeds": True}
    atomic(ANALYSIS / "independent_validation.json", receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
