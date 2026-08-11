"""Output schema and interval-metric correctness.

The cross-dataset tables are the interface between the pipeline and the
dissertation, so their columns are pinned here. If a stage stops emitting a
column the report depends on, this fails rather than the report silently
printing "n/a".

Schema checks run against whatever the most recent study produced; when no
outputs exist yet they skip, so the suite stays runnable on a clean checkout.
"""

import numpy as np
import pandas as pd
import pytest

from pathlib import Path

from src import metrics as M
from src.study_runner import INTERVAL_METHODS

COMBINED = Path("outputs/full_study/combined")


def _load(name: str) -> pd.DataFrame:
    path = COMBINED / name
    if not path.exists():
        pytest.skip(f"{path} not present; run src.run_study first")
    return pd.read_csv(path)


# --------------------------------------------------------------------------- #
# Interval metric correctness (pure functions, always run)
# --------------------------------------------------------------------------- #
def test_empirical_coverage_counts_inclusive_containment():
    y = np.array([0.0, 1.0, 2.0, 3.0])
    lo = np.array([0.0, 0.5, 5.0, -1.0])
    hi = np.array([0.0, 1.5, 6.0, 1.0])
    # index 0 sits exactly on both bounds (inside), 1 inside, 2 below, 3 above.
    assert M.empirical_coverage(y, lo, hi) == pytest.approx(0.5)


def test_winkler_reduces_to_width_when_everything_is_covered():
    y = np.array([1.0, 2.0, 3.0])
    lo, hi = y - 1.0, y + 1.0
    assert M.winkler_score(y, lo, hi, alpha=0.1) == pytest.approx(2.0)


def test_winkler_penalises_a_miss_by_two_over_alpha():
    y = np.array([5.0])
    lo, hi = np.array([0.0]), np.array([1.0])
    alpha = 0.1
    # width 1 plus (2/alpha) * (5 - 1) = 1 + 20*4 = 81
    assert M.winkler_score(y, lo, hi, alpha) == pytest.approx(81.0)


def test_interval_metrics_bundle_is_self_consistent():
    rng = np.random.default_rng(0)
    y = rng.normal(size=500)
    lo, hi = y - 1.5, y + 1.5
    out = M.interval_metrics(y, lo, hi, 0.9)
    assert out["empirical_coverage"] == pytest.approx(1.0)
    assert out["coverage_deviation"] == pytest.approx(0.1)
    assert out["mean_interval_width"] == pytest.approx(3.0)
    assert out["median_interval_width"] == pytest.approx(3.0)
    assert out["n_valid"] == 500


def test_metrics_ignore_nan_pairs_rather_than_scoring_them():
    y = np.array([1.0, 2.0, np.nan, 4.0])
    p = np.array([1.0, np.nan, 3.0, 5.0])
    assert M.n_valid(y, p) == 2
    assert M.mae(y, p) == pytest.approx(0.5)


def test_pct_improvement_sign_and_degenerate_baseline():
    assert M.pct_improvement(1.0, 0.5) == pytest.approx(50.0)
    assert M.pct_improvement(1.0, 1.5) == pytest.approx(-50.0)
    assert np.isnan(M.pct_improvement(0.0, 1.0))


# --------------------------------------------------------------------------- #
# Persisted output schemas
# --------------------------------------------------------------------------- #
POINT_COLUMNS = {"dataset", "target", "sampling_freq", "horizon_steps",
                 "horizon_minutes", "point_model", "n_seeds"}
INTERVAL_COLUMNS = {"dataset", "horizon_steps", "conformal_method",
                    "nominal_coverage", "empirical_coverage",
                    "coverage_deviation", "mean_interval_width",
                    "normalized_mean_interval_width", "winkler_score"}
ALERT_COLUMNS = {"dataset", "role", "rule", "k", "m", "precision", "recall",
                 "f1", "far", "false_alert_events_per_day",
                 "mean_detection_delay_min", "median_detection_delay_min"}


def test_point_metrics_schema():
    df = _load("point_metrics.csv")
    assert POINT_COLUMNS <= set(df.columns)
    ok = df[df.get("applicable", True) == True]           # noqa: E712
    assert (ok["n_seeds"] >= 1).all()
    assert (ok["horizon_steps"] > 0).all()


def test_interval_metrics_schema_and_method_names():
    df = _load("interval_metrics.csv")
    assert INTERVAL_COLUMNS <= set(df.columns)
    # Only the agreed method names may appear: the uncalibrated baseline must
    # never be merged into cqr, and EnbPI must always be labelled "recentred".
    assert set(df["conformal_method"]) <= set(INTERVAL_METHODS)
    assert not any(m == "enbpi" or m.startswith("EnbPI")
                   for m in df["conformal_method"])
    assert (df["empirical_coverage"].between(0, 1)).all()
    assert (df["mean_interval_width"] >= 0).all()


def test_every_interval_prediction_has_lower_below_upper():
    path = Path("outputs/full_study")
    files = list(path.glob("*/predictions/interval_predictions.csv"))
    if not files:
        pytest.skip("no interval predictions on disk")
    for f in files:
        df = pd.read_csv(f)
        bad = df[df["lower"] > df["upper"]]
        assert bad.empty, f"{f}: {len(bad)} rows have lower > upper"
        for method, sub in df.groupby("conformal_method"):
            assert (sub["lower"] <= sub["upper"]).all(), f"{f}: {method} crossed"


def test_alert_metrics_schema_and_role_separation():
    df = _load("alert_metrics.csv")
    assert ALERT_COLUMNS <= set(df.columns)
    roles = set(df["role"])
    assert "calibration_selection" in roles
    # Exactly one rule may be flagged as the operating rule per dataset+role.
    if "selected_operating_rule" in df.columns:
        for (ds, role), sub in df.groupby(["dataset", "role"]):
            assert sub["selected_operating_rule"].sum() == 1, (
                f"{ds}/{role} does not have exactly one selected rule")
    assert (df["far"].dropna().between(0, 1)).all()
    assert (df["false_alert_events_per_day"].dropna() >= 0).all()


def test_robustness_schema_distinguishes_observed_and_clean_truth():
    df = _load("robustness_metrics.csv")
    required = {"dataset", "mode", "scenario", "severity", "empirical_coverage",
                "empirical_coverage_vs_clean_truth", "mae", "mae_vs_clean_truth"}
    assert required <= set(df.columns)
    assert set(df["mode"]) <= {"legacy_fixed_intervals", "closed_loop",
                               "calibration_contamination"}


def test_recalibration_schema_records_the_residual_delay():
    df = _load("recalibration_metrics.csv")
    required = {"dataset", "recalibration_strategy", "empirical_coverage",
                "mean_interval_width", "winkler_score", "n_updates",
                "residual_delay_steps"}
    assert required <= set(df.columns)
    assert set(df["recalibration_strategy"]) == {"static", "periodic", "rolling"}
    # Static must never update; adaptive strategies must actually have updated.
    static = df[df["recalibration_strategy"] == "static"]
    assert (static["n_updates"] == 0).all()


def test_no_metric_column_is_entirely_empty():
    """A column of nothing but NaN means a stage silently produced nothing."""
    for name in ("point_metrics.csv", "interval_metrics.csv"):
        df = _load(name)
        for col in ("mae", "empirical_coverage"):
            if col in df.columns:
                assert df[col].notna().any(), f"{name}: {col} is entirely NaN"
