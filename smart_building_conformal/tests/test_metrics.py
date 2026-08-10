import numpy as np

from src import metrics as M


def test_mae_rmse_basic():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    p = np.array([1.0, 2.0, 4.0, 6.0])
    assert M.mae(y, p) == 0.75
    assert abs(M.rmse(y, p) - np.sqrt((0 + 0 + 1 + 4) / 4)) < 1e-12


def test_metrics_ignore_nan_pairs():
    y = np.array([1.0, 2.0, np.nan, 4.0])
    p = np.array([1.0, np.nan, 3.0, 5.0])
    # only positions 0 and 3 are jointly valid -> errors 0 and 1
    assert M.mae(y, p) == 0.5
    assert M.n_valid(y, p) == 2


def test_pct_improvement():
    assert M.pct_improvement(2.0, 1.0) == 50.0
    assert np.isnan(M.pct_improvement(0.0, 1.0))


def test_coverage_and_width():
    y = np.array([0.0, 0.5, 2.0])
    lo = np.array([-1.0, -1.0, -1.0])
    up = np.array([1.0, 1.0, 1.0])
    # first two inside, last outside -> coverage 2/3
    assert abs(M.empirical_coverage(y, lo, up) - 2 / 3) < 1e-12
    assert M.mean_interval_width(lo, up) == 2.0
    assert M.median_interval_width(lo, up) == 2.0
    assert abs(M.coverage_deviation(2 / 3, 0.9) - abs(2 / 3 - 0.9)) < 1e-12


def test_winkler_penalises_misses():
    y = np.array([0.0, 0.0])
    lo = np.array([-1.0, -1.0])
    up = np.array([1.0, 1.0])
    # both inside -> winkler == width == 2
    assert M.winkler_score(y, lo, up, alpha=0.1) == 2.0
    # move one point outside -> score must increase
    y2 = np.array([0.0, 5.0])
    assert M.winkler_score(y2, lo, up, alpha=0.1) > 2.0


def test_bootstrap_ci_brackets_point_estimate():
    rng = np.random.default_rng(0)
    y = rng.normal(size=500)
    p = y + rng.normal(scale=0.5, size=500)
    res = M.bootstrap_point_metrics(y, p, n_boot=200, seed=1)
    assert res["mae_ci_low"] <= res["mae"] <= res["mae_ci_high"]
    assert res["rmse_ci_low"] <= res["rmse"] <= res["rmse_ci_high"]
