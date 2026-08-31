"""Figures build from CSVs and record their source hash (no hand-entered values)."""

from __future__ import annotations

import pandas as pd

from src import final_figures as F


def test_recall_vs_workload_figure_builds_from_csv(tmp_path):
    run = tmp_path / "run"
    d = run / "pleia"; d.mkdir(parents=True)
    pd.DataFrame({
        "ablation": ["baseline", "conformal_only", "temporal", "full"],
        "applicable": [True, True, True, True],
        "macro_recall": [0.9, 0.85, 0.7, 0.75],
        "background_episodes_per_asset_day": [8.0, 6.0, 1.5, 1.2],
    }).to_csv(d / "ablation.csv", index=False)
    out = tmp_path / "figs"
    idx = F.build_all(run, ["pleia"], out)
    assert (out / "fig_recall_vs_workload.png").exists()
    assert not idx.empty
    # the index records a source csv and a non-empty content hash
    assert idx.iloc[0]["source_sha256"]
