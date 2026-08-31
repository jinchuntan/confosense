"""Reports are generated from CSVs, carry the honesty clause and safe terminology,
and never invent numbers.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import final_reports as R


def _setup(tmp_path):
    out = tmp_path / "out"; (out / "metrics").mkdir(parents=True)
    pd.DataFrame({"dataset": ["rico"], "metric": ["macro_event_recall"],
                  "estimate": [0.72], "ci_low": [0.61], "ci_high": [0.83],
                  "n_units": [20], "n_boot": [2000]}).to_csv(
        out / "metrics" / "final_cis.csv", index=False)
    run = tmp_path / "run"; (run / "rico").mkdir(parents=True)
    pd.DataFrame({"ablation": ["baseline", "full"], "applicable": [True, True],
                  "macro_recall": [0.9, 0.75],
                  "background_episodes_per_asset_day": [8.0, 0.9]}).to_csv(
        run / "rico" / "ablation.csv", index=False)
    pd.DataFrame({"decision": ["selected", "no_feasible_configuration"]}).to_csv(
        run / "rico" / "selection.csv", index=False)
    return run, out


def test_reports_use_csv_values_and_honesty_clause(tmp_path):
    run, out = _setup(tmp_path)
    written = R.build(run, out, ["rico"])
    assert "FINAL_DISSERTATION_RESULTS.md" in written
    txt = (out / "report" / "FINAL_DISSERTATION_RESULTS.md").read_text()
    assert "0.720" in txt                       # read from final_cis.csv
    assert "holdout" in txt                      # mandatory honesty clause
    assert "within-building" in txt              # safe BDG2 wording
    assert "no_feasible_configuration" in txt    # abstention kept in the report


def test_reports_report_nothing_when_cis_absent(tmp_path):
    run = tmp_path / "run"; (run / "rico").mkdir(parents=True)
    out = tmp_path / "out"
    R.build(run, out, ["rico"])
    txt = (out / "report" / "FINAL_DISSERTATION_RESULTS.md").read_text()
    # No CIs -> explicitly reports no number rather than fabricating one.
    assert "No corrected CIs" in txt or "not completed" in txt
