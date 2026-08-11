"""Disturbance scenarios and the closed-loop evaluation path.

Two properties matter most and are checked directly rather than assumed:

1. a perturbation never mutates the clean array it was given, so the held-out
   test data survives intact for every other scenario;
2. the closed-loop path is causal — a value corrupted at time *t* changes
   features at and after *t*, and never before it.
"""

import numpy as np
import pandas as pd
import pytest

from src import features, robustness_study as rob

FREQ = pd.Timedelta("10min")
FCFG = {"target_lags": [1, 2, 3], "rolling_windows": [6],
        "include_weekly": False, "covariates": []}


def _series(n=400):
    idx = pd.date_range("2021-07-01", periods=n, freq="10min")
    rng = np.random.default_rng(0)
    return pd.Series(20 + np.sin(np.arange(n) / 25) + rng.normal(0, 0.05, n), index=idx)


ALL_KINDS = ["random_missing", "block_missing", "bias", "level_shift",
             "drift", "stuck", "dropout"]


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_perturbation_never_mutates_its_input(kind):
    s = _series()
    snapshot = s.copy(deep=True)
    mask = np.zeros(len(s), dtype=bool)
    mask[200:] = True
    scenario = rob.Scenario(f"{kind}_test", kind, 0.5)

    out = rob.perturb_series(s, mask, scenario, scale=1.0, seed=3)
    pd.testing.assert_series_equal(s, snapshot)
    assert out is not s
    assert len(out) == len(s)


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_perturbation_is_confined_to_the_selected_region(kind):
    s = _series()
    mask = np.zeros(len(s), dtype=bool)
    mask[200:] = True
    scenario = rob.Scenario(f"{kind}_test", kind, 0.5)
    out = rob.perturb_series(s, mask, scenario, scale=1.0, seed=3)
    # Everything before the region must be untouched.
    pd.testing.assert_series_equal(out.iloc[:200], s.iloc[:200])


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_perturbation_is_reproducible_from_its_seed(kind):
    s = _series()
    mask = np.ones(len(s), dtype=bool)
    scenario = rob.Scenario(f"{kind}_test", kind, 0.5)
    a = rob.perturb_series(s, mask, scenario, 1.0, seed=11)
    b = rob.perturb_series(s, mask, scenario, 1.0, seed=11)
    pd.testing.assert_series_equal(a, b)


def test_bias_shifts_by_exactly_the_requested_multiple_of_sigma():
    s = _series()
    mask = np.ones(len(s), dtype=bool)
    out = rob.perturb_series(s, mask, rob.Scenario("b", "bias", 2.0), scale=0.5, seed=0)
    assert np.allclose((out - s).to_numpy(), 1.0)


def test_drift_ramps_from_zero_to_the_terminal_magnitude():
    s = _series()
    mask = np.ones(len(s), dtype=bool)
    out = rob.perturb_series(s, mask, rob.Scenario("d", "drift", 2.0), scale=1.0, seed=0)
    delta = (out - s).to_numpy()
    assert delta[0] == pytest.approx(0.0)
    assert delta[-1] == pytest.approx(2.0)
    assert np.all(np.diff(delta) >= -1e-12)          # monotone ramp


def test_stuck_freezes_the_reading():
    s = _series()
    mask = np.ones(len(s), dtype=bool)
    out = rob.perturb_series(s, mask, rob.Scenario("s", "stuck", 0.1), scale=1.0, seed=0)
    changed = np.flatnonzero((out != s).to_numpy())
    assert len(changed) > 0
    frozen = out.iloc[changed[0] - 1: changed[-1] + 1]
    assert frozen.nunique() == 1


def test_missingness_is_reimputed_so_the_model_sees_a_complete_series():
    s = _series()
    mask = np.ones(len(s), dtype=bool)
    out = rob.perturb_series(s, mask, rob.Scenario("m", "random_missing", 0.05),
                             scale=1.0, seed=1, max_gap=3)
    # Short gaps are filled by the pipeline's own rule; long runs may remain NaN.
    assert out.isna().mean() < 0.05
    assert not out.equals(s)


def test_clean_scenario_is_an_exact_copy():
    s = _series()
    out = rob.perturb_series(s, np.ones(len(s), bool),
                             rob.Scenario("clean", "none", 0.0), 1.0, seed=0)
    pd.testing.assert_series_equal(out, s)


# --------------------------------------------------------------------------- #
# Closed-loop causality
# --------------------------------------------------------------------------- #
def test_closed_loop_perturbation_propagates_forward_only():
    """A corrupted observation must change later features, never earlier ones."""
    s = _series(400)
    onset = 250
    frame = pd.DataFrame({"target": s, "target_was_missing": 0}, index=s.index)

    corrupted = frame.copy(deep=True)
    corrupted.iloc[onset, corrupted.columns.get_loc("target")] += 50.0

    a = features.build_supervised(frame, 1, FREQ, None, FCFG)
    b = features.build_supervised(corrupted, 1, FREQ, None, FCFG)

    common = a["X"].index.intersection(b["X"].index)
    onset_time = s.index[onset]
    before = common[common < onset_time]
    after = common[common >= onset_time]

    assert np.allclose(a["X"].loc[before].to_numpy(), b["X"].loc[before].to_numpy()), \
        "a future corruption changed a past feature row"
    assert not np.allclose(a["X"].loc[after].to_numpy(), b["X"].loc[after].to_numpy()), \
        "the corruption never reached the later features"


def test_region_mask_from_a_datetime_index_is_a_plain_boolean_array():
    """Guards the closed-loop mask construction against an Index/ndarray mix-up."""
    idx = pd.date_range("2021-07-01", periods=50, freq="10min")
    region = np.asarray(idx >= idx[25])
    assert isinstance(region, np.ndarray)
    assert region.dtype == bool
    assert region.sum() == 25


# --------------------------------------------------------------------------- #
def test_evaluation_separates_observed_from_clean_truth():
    n = 200
    y_clean = np.zeros(n)
    observed = np.zeros(n)
    observed[100:] = 5.0                              # the sensor starts lying
    point = np.zeros(n)
    lower, upper = np.full(n, -1.0), np.full(n, 1.0)

    out = rob.evaluate_intervals_and_alerts(
        y_clean, observed, point, lower, upper, 0.95, (1, 1), FREQ)

    # The forecast is perfect against reality...
    assert out["empirical_coverage_vs_clean_truth"] == pytest.approx(1.0)
    assert out["mae_vs_clean_truth"] == pytest.approx(0.0)
    # ...but half of what the monitor sees falls outside the interval.
    assert out["empirical_coverage"] == pytest.approx(0.5)
    assert out["n_violation_steps"] == 100
    assert out["alert_rate"] == pytest.approx(0.5)


def test_default_scenarios_cover_the_required_protocol():
    kinds = {s.kind for s in rob.default_scenarios({})}
    assert kinds == {"none", *ALL_KINDS}
    assert rob.contamination_levels({}) == [0.01, 0.05, 0.10]
    assert set(rob.MODES) == {"legacy_fixed_intervals", "closed_loop"}
