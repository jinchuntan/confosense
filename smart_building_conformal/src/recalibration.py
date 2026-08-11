"""Static, periodic and rolling recalibration of conformal interval widths.

All three strategies share one construction — a signed-residual split-conformal
interval

    [ŷ_i + Q_{α/2}(R_i),  ŷ_i + Q_{1−α/2}(R_i)]

— and differ only in which residual set ``R_i`` they are allowed to use at test
origin ``i``:

``static``
    Calibration residuals only. Never updated, so the interval cannot react to a
    distribution shift; it is the reference against which recovery is measured.

``periodic``
    Every ``update_every`` steps the quantiles are recomputed from *all*
    residuals observed so far (expanding pool). Between updates the width is
    held, which is how a deployed system that recalibrates on a schedule
    actually behaves.

``rolling``
    As periodic, but the pool is truncated to the most recent ``window``
    residuals, so old regimes age out. The window is taken over calibration and
    observed test residuals *together*: at the start of the test period its most
    recent residuals are the tail of calibration, and those are displaced by test
    residuals as they are observed. Excluding calibration would leave the window
    empty until ``min_samples`` test residuals had accrued, which would make the
    early test period silently fall back to static calibration.

Every pool comes from :class:`~src.residuals.DelayedResidualPool`, so no strategy
can consume a residual before its ground truth has been observed — the leakage
fix described in that module applies to all of them by construction.

Parameters (``update_every``, ``window``, ``min_samples``) are chosen on
calibration data by :func:`select_settings`; test metrics never inform them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import metrics as M
from .residuals import DelayedResidualPool

STRATEGIES = ("static", "periodic", "rolling")


def _signed_quantiles(pool: np.ndarray, level: float) -> tuple[float, float]:
    """Lower/upper signed-residual quantiles for a ``level`` interval."""
    alpha = 1.0 - level
    if len(pool) == 0:
        return float("nan"), float("nan")
    return (float(np.quantile(pool, alpha / 2.0)),
            float(np.quantile(pool, 1.0 - alpha / 2.0)))


@dataclass
class RecalibrationResult:
    lower: np.ndarray
    upper: np.ndarray
    point: np.ndarray
    n_updates: int
    pool_sizes: np.ndarray
    strategy: str
    settings: dict


def apply_strategy(
    point: np.ndarray,
    pool: DelayedResidualPool,
    level: float,
    strategy: str,
    *,
    update_every: int = 48,
    window: int | None = None,
    min_samples: int = 50,
) -> RecalibrationResult:
    """Produce recalibrated intervals for one test sequence.

    The quantile pair in force at position ``i`` is recomputed only at update
    boundaries; in between it is carried forward, which is both cheaper and a
    faithful model of scheduled recalibration.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown recalibration strategy {strategy!r}")

    point = np.asarray(point, dtype=float)
    n = len(point)
    lower = np.empty(n, dtype=float)
    upper = np.empty(n, dtype=float)
    sizes = np.zeros(n, dtype=int)

    # Baseline quantiles from calibration alone; also the fallback whenever an
    # adaptive pool has not yet reached ``min_samples``.
    base_lo, base_hi = _signed_quantiles(
        pool.calib_residuals[np.isfinite(pool.calib_residuals)], level
    )

    if strategy == "static":
        lower[:] = point + base_lo
        upper[:] = point + base_hi
        sizes[:] = len(pool.calib_residuals)
        return RecalibrationResult(lower, upper, point, 0, sizes, strategy,
                                   {"source": "calibration_only"})

    step = max(1, int(update_every))
    q_lo, q_hi = base_lo, base_hi
    n_updates = 0

    for i in range(n):
        if i % step == 0:
            candidate = pool.pool_at(
                i, window=window if strategy == "rolling" else None,
                include_calibration=True,
            )
            if len(candidate) >= min_samples:
                q_lo, q_hi = _signed_quantiles(candidate, level)
                n_updates += 1
                sizes[i] = len(candidate)
            else:
                # Not enough observed residuals yet: keep the calibration-based
                # width rather than a noisy quantile from a handful of points.
                q_lo, q_hi = base_lo, base_hi
                sizes[i] = len(candidate)
        else:
            sizes[i] = sizes[i - 1]
        lower[i] = point[i] + q_lo
        upper[i] = point[i] + q_hi

    return RecalibrationResult(
        lower, upper, point, n_updates, sizes, strategy,
        {"update_every": step, "window": window, "min_samples": min_samples,
         "include_calibration": True},
    )


def select_settings(
    calib_point: np.ndarray,
    calib_truth: np.ndarray,
    calib_origin_times: pd.DatetimeIndex,
    calib_target_times: pd.DatetimeIndex,
    level: float,
    horizon: int,
    grid: dict,
) -> dict:
    """Choose ``update_every`` / ``window`` on calibration data only.

    The calibration partition is split chronologically: the first block plays the
    role of "already calibrated", the second is replayed as if it were unseen
    test data. The setting whose replayed coverage deviation is smallest wins,
    with narrower mean width as the tie-break. No test observation is touched.

    The two blocks are separated by an **embargo** of ``horizon`` steps. Without
    it the split leaks: the first block's last forecast targets ``t + h``, which
    lands *after* the second block's first origin, so replaying from that origin
    would use a residual whose ground truth had not yet arrived. The embargo is
    the same purged-split idea used for cross-validating time series, and it is
    what keeps this parameter search honest at horizons greater than one.
    """
    point = np.asarray(calib_point, dtype=float)
    truth = np.asarray(calib_truth, dtype=float)
    origins = pd.DatetimeIndex(calib_origin_times)
    targets = pd.DatetimeIndex(calib_target_times)
    n = len(point)
    cut = n // 2
    embargo = max(1, int(horizon))
    start_b = cut + embargo
    fallback = {"update_every": grid.get("update_every", [48])[0],
                "window": grid.get("window", [500])[0],
                "min_samples": grid.get("min_samples", 50)}
    if cut < 10 or n - start_b < 10:
        return {**fallback, "selection": "insufficient_calibration_data"}

    resid_a = truth[:cut] - point[:cut]
    resid_b = truth[start_b:] - point[start_b:]
    # The replay pool must not see a residual before its ground truth lands.
    pool = DelayedResidualPool.build(
        resid_a, targets[:cut], resid_b,
        origins[start_b:], targets[start_b:], horizon,
    )

    rows = []
    for strategy in ("periodic", "rolling"):
        for every in grid.get("update_every", [48]):
            windows = grid.get("window", [500]) if strategy == "rolling" else [None]
            for w in windows:
                res = apply_strategy(
                    point[start_b:], pool, level, strategy,
                    update_every=every, window=w,
                    min_samples=grid.get("min_samples", 50),
                )
                cov = M.empirical_coverage(truth[start_b:], res.lower, res.upper)
                rows.append({
                    "strategy": strategy, "update_every": every, "window": w,
                    "replay_coverage": cov,
                    "replay_coverage_deviation": abs(cov - level),
                    "replay_mean_width": M.mean_interval_width(res.lower, res.upper),
                })
    table = pd.DataFrame(rows).sort_values(
        ["replay_coverage_deviation", "replay_mean_width"]
    )
    best = table.iloc[0]
    return {
        "update_every": int(best["update_every"]),
        "window": int(best["window"]) if pd.notna(best["window"]) else None,
        "min_samples": grid.get("min_samples", 50),
        "selection": "calibration_replay",
        "table": table,
    }


def recovery_profile(
    truth: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    level: float,
    shift_index: int,
    block: int,
) -> pd.DataFrame:
    """Rolling coverage in blocks either side of a disturbance onset.

    Used for the "coverage recovery after disturbance" analysis: block 0 is the
    first block after ``shift_index``, negative blocks precede it. A strategy has
    recovered once its block coverage returns to within the pre-shift band.
    """
    truth = np.asarray(truth, dtype=float)
    rows = []
    n = len(truth)
    starts = list(range(shift_index % block, n, block))
    for s in starts:
        e = min(s + block, n)
        if e - s < max(5, block // 4):
            continue
        cov = M.empirical_coverage(truth[s:e], lower[s:e], upper[s:e])
        rows.append({
            "block_start": s,
            "block_index": (s - shift_index) // block,
            "n": e - s,
            "empirical_coverage": cov,
            "coverage_deviation": abs(cov - level),
            "mean_interval_width": M.mean_interval_width(lower[s:e], upper[s:e]),
            "post_shift": s >= shift_index,
        })
    return pd.DataFrame(rows)
