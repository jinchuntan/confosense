"""Rebuild the two submitted Table 6 columns, including its custom F1."""

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

METRICS = {
    "macro_event_recall": "mean_macro_event_recall",
    "ordinary_matched_event_episode_precision": "mean_ordinary_episode_precision",
    "custom_synthetic_f1": "mean_custom_synthetic_f1",
    "background_episodes_per_asset_day": "mean_clean_workload",
    "restricted_mean_detection_minutes": "mean_restricted_detection_minutes",
}
SUBMITTED = {
    "quantile_uncalibrated": [0.8039, 0.2052, 0.3212, 1.5023, 131.49],
    "cqr": [0.8082, 0.2577, 0.3811, 1.1188, 125.47],
}


def verify(directory, out):
    cells = pd.read_csv(directory / "op_metrics.csv")
    summary = pd.read_csv(directory / "combined_candidate_summary.csv")
    methods = {}
    for candidate, method in [
        ("c0000_f5146f1247fa", "quantile_uncalibrated"),
        ("c0012_23099bed3753", "cqr"),
    ]:
        unit = cells.query("candidate_id==@candidate and support=='common'")
        saved = summary.query(
            "candidate_id==@candidate and support=='common'"
        ).squeeze()
        assert len(unit) == 15 and set(zip(unit.outer_fold, unit.model_seed)) == {
            (f, s) for f in range(3) for s in range(42, 47)
        }
        assert (
            unit.method.eq(method).all()
            and unit.level.eq(0.95).all()
            and unit.rule_id.eq("single_sample").all()
        )
        assert (
            unit.n_events.sum() == saved.event_count == 49350
            and unit.n_detected.sum() == saved.detected_count
        )
        averages = unit[list(METRICS)].mean()
        np.testing.assert_allclose(
            averages, saved[list(METRICS.values())].astype(float), rtol=0, atol=1e-10
        )
        rounded = [round(v, 4 if i < 4 else 2) for i, v in enumerate(averages)]
        np.testing.assert_equal(rounded, SUBMITTED[method])
        methods[method] = averages
    result = pd.DataFrame(methods)
    rates = result.loc["background_episodes_per_asset_day"]
    assert round(100 * (1 - rates.cqr / rates.quantile_uncalibrated), 2) == 25.53
    out.parent.mkdir(exist_ok=True, parents=True)
    result.to_csv(out, index_label="metric")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("out", type=Path)
    args = p.parse_args()
    verify(args.source, args.out)
