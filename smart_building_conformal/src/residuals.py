"""Delayed residual availability for adaptive conformal calibration.

The preliminary experiment folded each test residual into the recalibration pool
as soon as its forecast *origin* was passed. For a direct model at horizon ``h``
that is optimistic: a forecast issued at origin ``t`` for target ``t + h`` cannot
be scored until ``y_{t+h}`` has actually been observed, which is ``h`` steps
later. Consuming it any earlier lets the interval react to information the
operator would not yet hold — a genuine, if subtle, form of look-ahead. The
preliminary report flags this as a limitation; this module is the fix.

The rule implemented here is exactly one line of arithmetic:

    residual j is usable at origin time t  ⟺  target_time[j] ≤ t

Because ``target_time`` is monotone whenever ``origin_time`` is, the usable set
at any origin is always a *prefix* of the residual sequence, so the availability
frontier can be computed for the whole test set in one vectorised
``searchsorted`` rather than a Python loop.

Calibration residuals need no special handling: every partition is chronological
(or, for RICO, whole runs ordered in time), so a calibration target time always
precedes the first test origin. That is asserted rather than assumed —
:func:`DelayedResidualPool.build` refuses to construct a pool whose calibration
residuals are not fully observed before the test period opens.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def availability_frontier(
    origin_times: pd.DatetimeIndex,
    target_times: pd.DatetimeIndex,
) -> np.ndarray:
    """Number of residuals observable at each origin.

    ``frontier[i]`` is the count of positions ``j`` whose ground truth has landed
    by ``origin_times[i]``; residuals ``[0, frontier[i])`` are therefore the
    complete set an online method may legitimately use when forecasting from
    origin ``i``.
    """
    origins = pd.DatetimeIndex(origin_times)
    targets = pd.DatetimeIndex(target_times)
    if len(origins) != len(targets):
        raise ValueError("origin_times and target_times must be the same length")
    if not targets.is_monotonic_increasing:
        # Sorting would silently reorder the residual sequence and break the
        # prefix property the rest of this module relies on.
        raise ValueError("target_times must be non-decreasing")
    return np.searchsorted(targets.to_numpy(), origins.to_numpy(), side="right")


@dataclass
class DelayedResidualPool:
    """Residuals usable at each test origin, respecting observation delay.

    ``calib_residuals`` are available throughout (their targets all precede the
    test period). ``test_residuals`` become available progressively according to
    :func:`availability_frontier`.
    """

    calib_residuals: np.ndarray
    test_residuals: np.ndarray
    frontier: np.ndarray
    horizon: int

    @classmethod
    def build(
        cls,
        calib_residuals: np.ndarray,
        calib_target_times: pd.DatetimeIndex,
        test_residuals: np.ndarray,
        test_origin_times: pd.DatetimeIndex,
        test_target_times: pd.DatetimeIndex,
        horizon: int,
    ) -> "DelayedResidualPool":
        calib_targets = pd.DatetimeIndex(calib_target_times)
        test_origins = pd.DatetimeIndex(test_origin_times)
        if len(calib_targets) and len(test_origins):
            if calib_targets.max() > test_origins.min():
                raise ValueError(
                    "calibration targets overlap the test period: a calibration "
                    "residual would not yet be observed at the first test origin"
                )
        return cls(
            calib_residuals=np.asarray(calib_residuals, dtype=float),
            test_residuals=np.asarray(test_residuals, dtype=float),
            frontier=availability_frontier(test_origins, test_target_times),
            horizon=int(horizon),
        )

    def __len__(self) -> int:
        return len(self.test_residuals)

    def pool_at(
        self,
        i: int,
        *,
        window: int | None = None,
        include_calibration: bool = True,
    ) -> np.ndarray:
        """Residuals a method may use when forecasting from test origin ``i``.

        ``window`` keeps only the most recent ``window`` residuals (rolling
        recalibration); ``None`` keeps every observed residual (expanding).
        """
        k = int(self.frontier[i])
        observed = self.test_residuals[:k]
        if include_calibration:
            pool = np.concatenate([self.calib_residuals, observed])
        else:
            pool = observed
        pool = pool[np.isfinite(pool)]
        if window is not None and len(pool) > window:
            pool = pool[-window:]
        return pool

    def first_usable_index(self) -> int:
        """First test position at which any test residual has become available."""
        nz = np.nonzero(self.frontier > 0)[0]
        return int(nz[0]) if len(nz) else len(self.frontier)
