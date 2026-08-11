"""Delayed residual availability — the high-priority leakage requirement.

For a forecast issued at origin t targeting t+h, the residual cannot enter any
adaptive pool until y_{t+h} has actually been observed. These tests prove that no
future residual is consumed early, at h = 1 and at h > 1.
"""

import numpy as np
import pandas as pd
import pytest

from src import recalibration as recal
from src.residuals import DelayedResidualPool, availability_frontier


def _times(n, h, freq="10min", start="2021-06-01"):
    origins = pd.date_range(start, periods=n, freq=freq)
    targets = origins + h * pd.Timedelta(freq)
    return origins, targets


def test_frontier_is_exactly_h_steps_behind():
    n, h = 50, 6
    origins, targets = _times(n, h)
    frontier = availability_frontier(origins, targets)
    # At origin i exactly the residuals whose target has already landed are
    # observable, and on a regular grid that is the prefix 0 .. i-h.
    assert list(frontier) == [max(0, i - h + 1) for i in range(n)]
    for i in range(n):
        expected = int(np.sum(targets <= origins[i]))
        assert frontier[i] == expected
        # Nothing from the present or future is ever counted.
        if frontier[i] > 0:
            assert targets[frontier[i] - 1] <= origins[i]
        if frontier[i] < n:
            assert targets[frontier[i]] > origins[i]


def test_horizon_one_still_respects_a_one_step_delay():
    origins, targets = _times(20, 1)
    frontier = availability_frontier(origins, targets)
    assert frontier[0] == 0            # nothing observed before the first origin
    assert list(frontier) == list(range(20))


def test_pool_never_returns_an_unobserved_residual():
    n, h = 60, 6
    origins, targets = _times(n, h)
    test_resid = np.arange(n, dtype=float)          # residual j has value j
    calib_resid = -np.ones(5)
    calib_targets = pd.date_range("2021-05-01", periods=5, freq="10min")

    pool = DelayedResidualPool.build(calib_resid, calib_targets, test_resid,
                                     origins, targets, h)
    for i in range(n):
        usable = pool.pool_at(i, include_calibration=False)
        # Values are the indices, so the maximum tells us the newest residual used.
        if len(usable):
            newest = int(usable.max())
            assert targets[newest] <= origins[i], (
                f"residual {newest} used at origin {i} but its truth lands later")
        assert len(usable) == int(np.sum(targets <= origins[i]))


def test_pool_rejects_calibration_overlapping_the_test_period():
    n, h = 30, 3
    origins, targets = _times(n, h)
    # Calibration truth that lands *after* the first test origin must be refused.
    bad_targets = pd.DatetimeIndex([origins[5]] * 4)
    with pytest.raises(ValueError, match="overlap"):
        DelayedResidualPool.build(np.zeros(4), bad_targets, np.zeros(n),
                                  origins, targets, h)


def test_rolling_window_keeps_only_the_most_recent_available_residuals():
    n, h = 80, 4
    origins, targets = _times(n, h)
    pool = DelayedResidualPool.build(
        np.zeros(0), pd.DatetimeIndex([]), np.arange(n, dtype=float),
        origins, targets, h)
    win = 10
    for i in range(30, n):
        usable = pool.pool_at(i, window=win, include_calibration=False)
        assert len(usable) <= win
        assert int(usable.max()) == int(np.sum(targets <= origins[i])) - 1


def test_static_strategy_never_consumes_a_test_residual():
    """Static calibration must be identical whatever the test residuals are."""
    n, h = 40, 6
    origins, targets = _times(n, h)
    calib = np.random.default_rng(0).normal(size=200)
    calib_targets = pd.date_range("2021-05-01", periods=200, freq="10min")
    point = np.zeros(n)

    a = DelayedResidualPool.build(calib, calib_targets, np.zeros(n), origins, targets, h)
    b = DelayedResidualPool.build(calib, calib_targets, np.full(n, 1e6), origins, targets, h)
    ra = recal.apply_strategy(point, a, 0.9, "static")
    rb = recal.apply_strategy(point, b, 0.9, "static")
    assert np.allclose(ra.lower, rb.lower)
    assert np.allclose(ra.upper, rb.upper)


def test_adaptive_strategy_ignores_residuals_that_have_not_landed_yet():
    """Corrupting only the not-yet-observable tail must not move early intervals."""
    n, h = 120, 12
    origins, targets = _times(n, h)
    rng = np.random.default_rng(1)
    calib = rng.normal(size=300)
    calib_targets = pd.date_range("2021-05-01", periods=300, freq="10min")
    resid = rng.normal(size=n)
    point = np.zeros(n)

    clean = DelayedResidualPool.build(calib, calib_targets, resid.copy(),
                                      origins, targets, h)
    tainted_resid = resid.copy()
    tainted_resid[60:] = 1e6                      # only the later half is absurd
    tainted = DelayedResidualPool.build(calib, calib_targets, tainted_resid,
                                        origins, targets, h)

    a = recal.apply_strategy(point, clean, 0.9, "periodic", update_every=1, min_samples=5)
    b = recal.apply_strategy(point, tainted, 0.9, "periodic", update_every=1, min_samples=5)

    # Residual 60 only becomes observable at origin 60 + h; every interval
    # strictly before that must be untouched by the corruption.
    cutoff = 60 + h
    assert np.allclose(a.lower[:cutoff], b.lower[:cutoff])
    assert np.allclose(a.upper[:cutoff], b.upper[:cutoff])
    # And it must genuinely bite afterwards, or the test would prove nothing.
    assert not np.allclose(a.upper[cutoff:], b.upper[cutoff:])


def test_settings_selection_embargoes_the_calibration_replay_split():
    """Splitting calibration for a replay must purge the horizon-length overlap.

    Without an embargo the first block's last forecast targets t+h, which lands
    after the second block's first origin, so the replay would score itself with
    a residual that had not yet been observed. This reproduces exactly the case
    that fails on RICO (1-minute sampling, horizon 5).
    """
    n, h = 600, 5
    origins = pd.date_range("2024-02-04", periods=n, freq="1min")
    targets = origins + h * pd.Timedelta("1min")
    rng = np.random.default_rng(0)
    point = rng.normal(size=n)
    truth = point + rng.normal(scale=0.3, size=n)

    out = recal.select_settings(
        point, truth, origins, targets, level=0.9, horizon=h,
        grid={"update_every": [30, 60], "window": [100, 200], "min_samples": 20},
    )
    assert out["selection"] == "calibration_replay"
    assert out["update_every"] in (30, 60)

    # The embargo must be exactly h steps: the last retained "known" target has
    # to land no later than the first replayed origin.
    cut = n // 2
    assert targets[cut - 1] <= origins[cut + h], "embargo is too small"
    assert targets[cut - 1] > origins[cut], "test is vacuous without an embargo"


def test_settings_selection_reports_when_calibration_is_too_short():
    n, h = 30, 10
    origins = pd.date_range("2024-02-04", periods=n, freq="1min")
    out = recal.select_settings(
        np.zeros(n), np.zeros(n), origins, origins + h * pd.Timedelta("1min"),
        level=0.9, horizon=h, grid={"update_every": [12], "window": [50]},
    )
    assert out["selection"] == "insufficient_calibration_data"
    assert out["update_every"] == 12
