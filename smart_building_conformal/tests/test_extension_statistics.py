"""Paired robustness inference: pairing, seed aggregation, Holm monotonicity."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import extension_statistics as ES


def _cells(tmp_path):
    rows = []
    for fold in (0, 1, 2):
        for seed in (42, 43):
            for cell, fam, covd, bg in [("clean", "clean", 0.95, 1.0),
                                        ("level_shift@2.0", "fault", 0.40, 1.5),
                                        ("zero_control", "fault", 0.95, 1.0)]:
                rows.append({"dataset": "pleia", "outer_fold": fold, "seed": seed,
                             "cell": cell, "family": fam,
                             "coverage_during": covd, "coverage_all": covd,
                             "coverage_post": covd,
                             "background_per_asset_day": bg, "mean_width": 2.0})
    d = tmp_path / "run" / "pleia"; d.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(d / "robustness_cells.csv", index=False)
    return tmp_path / "run"


def test_paired_deltas_are_seed_aggregated_to_folds(tmp_path):
    run = _cells(tmp_path)
    out = ES.build(run, ["pleia"], tmp_path / "out")
    row = out[(out["contrast"] == "level_shift@2.0 - clean")
              & (out["endpoint"] == "coverage_during")
              & (out["scope"] == "pleia")].iloc[0]
    assert row["n_units"] == 3                 # folds, not 6 seed-rows
    assert abs(row["delta_mean"] - (-0.55)) < 1e-9


def test_small_n_reports_na_not_degenerate_ci(tmp_path):
    run = _cells(tmp_path)
    out = ES.build(run, ["pleia"], tmp_path / "out")
    pooled = out[(out["scope"] == "pooled")
                 & (out["endpoint"] == "coverage_during")].iloc[0]
    assert pooled["ci_low"] == "NA"            # 3 units < 4 -> NA, never fake CI


def test_holm_is_monotone_and_bounded():
    p = [0.01, 0.04, 0.03, 0.20]
    adj = ES.holm(p)
    assert all(0 <= a <= 1 for a in adj)
    assert all(a >= r for a, r in zip(adj, p))     # adjusted >= raw
