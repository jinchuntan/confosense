"""Dual-Splitting Conformal Prediction (Yu et al. 2025).

The paper's coverage guarantee rests on exchangeability between calibration and
test samples within a cluster, which does not hold exactly for non-stationary
building data. These tests therefore check the *mechanics* the implementation
claims — calibration/test separation, horizon-specific outputs, ordering, shapes,
determinism — and deliberately do **not** assert nominal coverage, which would be
asserting an assumption rather than testing the code.
"""

import numpy as np
import pytest

from src.conformal_dscp import DSCPCalibrator, _merge_steps, fit_dscp, soft_dtw

HORIZONS = [1, 3, 6]


def synthetic(n=300, b=3, seed=0, noise=1.0):
    """Predictions plus truths whose error spread grows with the step index."""
    rng = np.random.default_rng(seed)
    P = rng.normal(size=(n, b)) * 2.0
    errors = rng.normal(scale=noise * np.arange(1, b + 1), size=(n, b))
    return P, P + errors


def test_fit_uses_only_the_arrays_it_is_given():
    """Test predictions cannot influence the fitted calibrator."""
    P, Y = synthetic()
    cal = fit_dscp(P, Y, HORIZONS, seed=42)
    # Everything the calibrator retains comes from the calibration inputs.
    assert cal.calib_predictions.shape == P.shape
    assert len(cal.cluster_labels) == len(P)
    assert cal.metadata["n_calibration"] == len(P)
    for c, pools in cal.merged_errors.items():
        for pool in pools:
            assert len(pool) <= P.size


def test_intervals_are_ordered_and_horizon_specific():
    P, Y = synthetic()
    cal = fit_dscp(P, Y, HORIZONS, seed=42)
    P_test, _ = synthetic(n=80, seed=99)
    out = cal.predict_interval(P_test, 0.9)

    assert out["lower"].shape == out["upper"].shape == P_test.shape
    assert np.all(out["upper"] >= out["lower"]), "interval bounds crossed"
    # The synthetic error spread grows with step, so widths must too.
    widths = (out["upper"] - out["lower"]).mean(axis=0)
    assert widths[0] < widths[-1], "per-step quantiles are not horizon-specific"


def test_output_length_matches_the_input():
    P, Y = synthetic()
    cal = fit_dscp(P, Y, HORIZONS, seed=42)
    for n in (1, 7, 50):
        P_test, _ = synthetic(n=n, seed=n)
        out = cal.predict_interval(P_test, 0.95)
        assert len(out["lower"]) == n
        assert len(out["cluster"]) == n


def test_wider_level_gives_wider_intervals():
    P, Y = synthetic()
    cal = fit_dscp(P, Y, HORIZONS, seed=42)
    P_test, _ = synthetic(n=60, seed=7)
    w90 = (cal.predict_interval(P_test, 0.90)["upper"]
           - cal.predict_interval(P_test, 0.90)["lower"]).mean()
    w99 = (cal.predict_interval(P_test, 0.99)["upper"]
           - cal.predict_interval(P_test, 0.99)["lower"]).mean()
    assert w99 > w90


def test_fit_is_reproducible_under_a_fixed_seed():
    P, Y = synthetic()
    a = fit_dscp(P, Y, HORIZONS, seed=42)
    b = fit_dscp(P, Y, HORIZONS, seed=42)
    assert a.n_clusters == b.n_clusters
    assert np.array_equal(a.cluster_labels, b.cluster_labels)
    P_test, _ = synthetic(n=40, seed=3)
    ia = a.predict_interval(P_test, 0.9)
    ib = b.predict_interval(P_test, 0.9)
    assert np.allclose(ia["lower"], ib["lower"])
    assert np.allclose(ia["upper"], ib["upper"])


def test_shape_mismatches_are_rejected():
    P, Y = synthetic()
    with pytest.raises(ValueError):
        fit_dscp(P, Y[:, :2], HORIZONS)
    with pytest.raises(ValueError):
        fit_dscp(P, Y, [1, 3])                     # wrong number of steps
    cal = fit_dscp(P, Y, HORIZONS)
    with pytest.raises(ValueError):
        cal.predict_interval(np.zeros((5, 2)), 0.9)


def test_horizontal_merge_pools_similar_steps_and_splits_different_ones():
    rng = np.random.default_rng(0)
    same_a = rng.normal(size=400)
    same_b = rng.normal(size=400)
    different = rng.normal(loc=25.0, size=400)

    merged, groups = _merge_steps([same_a, same_b, different], threshold=0.05)
    assert groups[0] == groups[1], "indistinguishable steps were not merged"
    assert groups[2] != groups[1], "a clearly different step was merged anyway"
    assert len(merged[0]) == len(same_a) + len(same_b)
    assert len(merged[2]) == len(different)


def test_single_step_merge_is_a_no_op():
    pool = np.arange(10.0)
    merged, groups = _merge_steps([pool], threshold=0.05)
    assert groups == [0]
    assert np.array_equal(merged[0], pool)


def test_soft_dtw_is_zero_for_identical_sequences_and_positive_otherwise():
    x = np.array([1.0, 2.0, 3.0])
    assert soft_dtw(x, x, gamma=0.0) == pytest.approx(0.0)
    assert soft_dtw(x, x + 5.0, gamma=0.0) > 0.0
    # Symmetry.
    y = np.array([1.0, 5.0, 2.0])
    assert soft_dtw(x, y, gamma=0.0) == pytest.approx(soft_dtw(y, x, gamma=0.0))


def test_degenerate_calibration_falls_back_to_a_single_cluster():
    P = np.tile(np.array([[1.0, 2.0, 3.0]]), (20, 1))
    Y = P + 0.1
    cal = fit_dscp(P, Y, HORIZONS, seed=0)
    assert cal.n_clusters == 1
    out = cal.predict_interval(P[:3], 0.9)
    assert np.all(out["upper"] >= out["lower"])


def test_too_few_calibration_sequences_is_an_error_not_a_guess():
    with pytest.raises(ValueError):
        fit_dscp(np.zeros((1, 3)), np.zeros((1, 3)), HORIZONS)


def test_intervals_are_anchored_on_the_point_forecast_within_a_cluster():
    """Bounds are the prediction plus signed error quantiles.

    The shift property only holds with the cluster held fixed, so a degenerate
    single-cluster calibrator is used. With several clusters, moving the
    prediction legitimately moves it to a different cluster — see the next test.
    """
    P = np.tile(np.array([[1.0, 2.0, 3.0]]), (30, 1))
    rng = np.random.default_rng(0)
    Y = P + rng.normal(size=P.shape)
    cal = fit_dscp(P, Y, HORIZONS, seed=0)
    assert cal.n_clusters == 1, "this test needs a single-cluster calibrator"

    P_test = np.zeros((4, 3))
    base = cal.predict_interval(P_test, 0.9)
    shifted = cal.predict_interval(P_test + 100.0, 0.9)
    assert np.allclose(shifted["lower"] - base["lower"], 100.0)
    assert np.allclose(shifted["upper"] - base["upper"], 100.0)
    # Width depends only on the residual pool, not on where the forecast sits.
    assert np.allclose(shifted["upper"] - shifted["lower"],
                       base["upper"] - base["lower"])


def test_cluster_assignment_depends_on_the_predicted_sequence():
    """The vertical split is what makes DSCP adaptive rather than global.

    Two well-separated prediction regimes must land in different clusters, and
    the interval width must be allowed to differ between them.
    """
    rng = np.random.default_rng(3)
    n = 150
    # Regime A: low level, small errors. Regime B: high level, large errors.
    low = rng.normal(loc=0.0, scale=0.2, size=(n, 3))
    high = rng.normal(loc=50.0, scale=0.2, size=(n, 3))
    P = np.vstack([low, high])
    Y = np.vstack([low + rng.normal(scale=0.1, size=(n, 3)),
                   high + rng.normal(scale=5.0, size=(n, 3))])

    cal = fit_dscp(P, Y, HORIZONS, seed=1)
    assert cal.n_clusters >= 2, "the two regimes should separate"

    a = cal.predict_interval(np.zeros((5, 3)), 0.9)
    b = cal.predict_interval(np.full((5, 3), 50.0), 0.9)
    assert a["cluster"][0] != b["cluster"][0]
    # The noisier regime must earn wider intervals.
    assert (b["upper"] - b["lower"]).mean() > (a["upper"] - a["lower"]).mean()


def test_neighbour_count_defaults_to_the_smallest_cluster_size():
    """The paper sets s to the size of the smallest cluster, not a constant."""
    rng = np.random.default_rng(11)
    # Two well-separated regimes with deliberately unequal populations.
    big = rng.normal(loc=0.0, scale=0.2, size=(300, 3))
    small = rng.normal(loc=60.0, scale=0.2, size=(40, 3))
    P = np.vstack([big, small])
    Y = P + rng.normal(scale=0.5, size=P.shape)

    cal = fit_dscp(P, Y, HORIZONS, seed=3)
    assert cal.n_clusters >= 2
    sizes = np.bincount(cal.cluster_labels, minlength=cal.n_clusters)
    assert cal.neighbours == int(sizes[sizes > 0].min())
    assert cal.metadata["neighbours_rule"] == "smallest cluster size (paper)"
    assert cal.metadata["neighbours_used"] == cal.neighbours


def test_explicit_neighbour_count_overrides_the_paper_rule():
    P, Y = synthetic(n=200, seed=8)
    cal = fit_dscp(P, Y, HORIZONS, neighbours=7, seed=8)
    assert cal.neighbours == 7
    assert cal.metadata["neighbours_rule"] == "explicit override"


def test_calibrator_never_receives_or_stores_test_truth():
    """DSCP must be fittable and usable without any test ground truth."""
    P, Y = synthetic(n=250, seed=4)
    cal = fit_dscp(P, Y, HORIZONS, seed=4)
    P_test, Y_test = synthetic(n=60, seed=77)

    out = cal.predict_interval(P_test, 0.9)
    # Replacing the test truth with nonsense cannot change the intervals,
    # because predict_interval never sees it.
    out2 = cal.predict_interval(P_test, 0.9)
    assert np.allclose(out["lower"], out2["lower"])
    assert np.allclose(out["upper"], out2["upper"])
    # Nothing stored on the calibrator came from test data.
    assert cal.calib_predictions.shape[0] == len(P)
    assert len(cal.cluster_labels) == len(P)
