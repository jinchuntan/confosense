"""Group-appropriate bootstrap CIs: correct resampling unit, reproducibility,
and sane coverage of the point estimate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import final_statistics as S


def test_rico_resamples_runs_not_rows():
    df = pd.DataFrame({"group_id": ["r1"] * 10 + ["r2"] * 10 + ["r3"] * 10})
    units = S._unit_indices(df, "rico")
    assert len(units) == 3                      # one unit per run
    assert sum(len(u) for u in units) == 30


def test_series_uses_moving_blocks():
    df = pd.DataFrame({"x": range(100)})
    units = S._unit_indices(df, "pleia")
    # sqrt(100)=10 -> ~10 blocks; never one-row IID units
    assert 5 <= len(units) <= 20
    assert max(len(u) for u in units) > 1


def test_bootstrap_ci_is_reproducible_and_brackets_point():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"group_id": np.repeat([f"b{i}" for i in range(12)], 20),
                       "event_type": "bias", "severity": "1.0sd",
                       "detected": rng.random(240) < 0.7})
    a = S._bootstrap(df, "bdg2", S._macro_recall, n_boot=500, seed=1)
    b = S._bootstrap(df, "bdg2", S._macro_recall, n_boot=500, seed=1)
    assert a == b                               # fixed seed -> reproducible
    assert a["ci_low"] <= a["estimate"] <= a["ci_high"]
    assert a["n_units"] == 12


def test_macro_recall_weights_strata_equally():
    df = pd.DataFrame({"event_type": ["a", "a", "b"], "severity": ["s", "s", "s"],
                       "detected": [True, True, False]})
    # macro = mean(recall_a=1.0, recall_b=0.0) = 0.5, not micro 2/3
    assert abs(S._macro_recall(df) - 0.5) < 1e-9


def test_dataset_cis_reads_engine_outputs(tmp_path):
    d = tmp_path / "rico"; d.mkdir()
    pd.DataFrame({"group_id": np.repeat(["r1", "r2", "r3", "r4"], 10),
                  "event_type": "bias", "severity": "1.0sd",
                  "detected": [True] * 25 + [False] * 15}).to_csv(
        d / "outer_per_event.csv", index=False)
    pd.DataFrame({"group_id": ["r1", "r2", "r3", "r4"],
                  "empirical_coverage": [0.94, 0.95, 0.93, 0.96],
                  "n": [100, 120, 90, 110]}).to_csv(
        d / "outer_per_group_coverage.csv", index=False)
    pd.DataFrame({"background_episodes_per_asset_day": [0.5, 0.7, 0.6]}).to_csv(
        d / "outer_metrics.csv", index=False)
    out = S.dataset_cis(tmp_path, "rico", n_boot=200)
    metrics = set(out["metric"])
    assert {"macro_event_recall", "empirical_coverage",
            "background_episodes_per_asset_day"} <= metrics
    for _, r in out.iterrows():
        assert r["ci_low"] <= r["estimate"] <= r["ci_high"]
