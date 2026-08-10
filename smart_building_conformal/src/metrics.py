"""Point-forecast and prediction-interval evaluation metrics.

All functions ignore NaN prediction/target pairs so that models which
legitimately abstain (e.g. seasonal naive at the start of the series) are not
penalised for producing an undefined forecast. The number of valid pairs used
is always available through :func:`n_valid` so that coverage of the evaluation
itself can be reported.
"""

from __future__ import annotations

from typing import Callable

import numpy as np


def _valid_mask(*arrays: np.ndarray) -> np.ndarray:
    """Boolean mask of positions that are finite in every supplied array."""
    mask = np.ones(len(arrays[0]), dtype=bool)
    for a in arrays:
        mask &= np.isfinite(np.asarray(a, dtype=float))
    return mask


def n_valid(y_true: np.ndarray, y_pred: np.ndarray) -> int:
    return int(_valid_mask(y_true, y_pred).sum())


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    m = _valid_mask(y_true, y_pred)
    if not m.any():
        return float("nan")
    return float(np.mean(np.abs(np.asarray(y_true)[m] - np.asarray(y_pred)[m])))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    m = _valid_mask(y_true, y_pred)
    if not m.any():
        return float("nan")
    diff = np.asarray(y_true)[m] - np.asarray(y_pred)[m]
    return float(np.sqrt(np.mean(diff ** 2)))


def pct_improvement(baseline: float, candidate: float) -> float:
    """Percentage improvement of ``candidate`` over ``baseline`` (higher is better).

    A positive value means the candidate reduced the error relative to the
    baseline. Returns NaN when the baseline is not usable.
    """
    if baseline is None or not np.isfinite(baseline) or baseline == 0:
        return float("nan")
    return float(100.0 * (baseline - candidate) / baseline)


def empirical_coverage(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    m = _valid_mask(y_true, lower, upper)
    if not m.any():
        return float("nan")
    yt, lo, up = np.asarray(y_true)[m], np.asarray(lower)[m], np.asarray(upper)[m]
    inside = (yt >= lo) & (yt <= up)
    return float(np.mean(inside))


def coverage_deviation(empirical: float, nominal: float) -> float:
    """Absolute deviation of empirical coverage from the nominal level."""
    return float(abs(empirical - nominal))


def interval_width(lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    return np.asarray(upper, dtype=float) - np.asarray(lower, dtype=float)


def mean_interval_width(lower: np.ndarray, upper: np.ndarray) -> float:
    m = _valid_mask(lower, upper)
    if not m.any():
        return float("nan")
    return float(np.mean(interval_width(np.asarray(lower)[m], np.asarray(upper)[m])))


def median_interval_width(lower: np.ndarray, upper: np.ndarray) -> float:
    m = _valid_mask(lower, upper)
    if not m.any():
        return float("nan")
    return float(np.median(interval_width(np.asarray(lower)[m], np.asarray(upper)[m])))


def winkler_score(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    alpha: float,
) -> float:
    """Mean Winkler interval score for a (1 - alpha) prediction interval.

    The Winkler score rewards narrow intervals and penalises observations that
    fall outside the interval, with the penalty scaled by ``2 / alpha``.
    Lower is better.
    """
    m = _valid_mask(y_true, lower, upper)
    if not m.any():
        return float("nan")
    yt, lo, up = np.asarray(y_true)[m], np.asarray(lower)[m], np.asarray(upper)[m]
    width = up - lo
    score = width.copy()
    below = yt < lo
    above = yt > up
    score[below] += (2.0 / alpha) * (lo[below] - yt[below])
    score[above] += (2.0 / alpha) * (yt[above] - up[above])
    return float(np.mean(score))


def interval_metrics(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    nominal: float,
) -> dict:
    """Bundle the standard interval metrics for one (method, horizon, level)."""
    alpha = 1.0 - nominal
    cov = empirical_coverage(y_true, lower, upper)
    return {
        "empirical_coverage": cov,
        "coverage_deviation": coverage_deviation(cov, nominal),
        "mean_interval_width": mean_interval_width(lower, upper),
        "median_interval_width": median_interval_width(lower, upper),
        "winkler_score": winkler_score(y_true, lower, upper, alpha),
        "n_valid": int(_valid_mask(y_true, lower, upper).sum()),
    }


def moving_block_bootstrap_ci(
    per_obs: np.ndarray,
    reducer: Callable[[np.ndarray], float],
    n_boot: int = 1000,
    block_size: int | None = None,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Moving-block bootstrap confidence interval for a mean-type statistic.

    Parameters
    ----------
    per_obs
        Per-observation quantity whose reduced value is the statistic of
        interest (e.g. absolute errors for MAE, squared errors for RMSE,
        the in/out indicator for coverage, or the width for mean width).
    reducer
        Maps the per-observation vector to the scalar statistic.
    block_size
        Length of the contiguous blocks. Defaults to ``round(n ** (1/3))``,
        a common choice that preserves short-range temporal dependence.

    Returns
    -------
    (point_estimate, ci_low, ci_high)
    """
    x = np.asarray(per_obs, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    point = float(reducer(x)) if n else float("nan")
    if n < 2:
        return point, float("nan"), float("nan")
    if block_size is None:
        block_size = max(1, int(round(n ** (1.0 / 3.0))))
    block_size = min(block_size, n)
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block_size))
    max_start = n - block_size
    stats = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        idx = (starts[:, None] + np.arange(block_size)[None, :]).ravel()[:n]
        stats[b] = reducer(x[idx])
    low = float(np.percentile(stats, 100 * (1 - ci) / 2))
    high = float(np.percentile(stats, 100 * (1 + ci) / 2))
    return point, low, high


# Reducers for the bootstrap helper.
def _mean(x: np.ndarray) -> float:
    return float(np.mean(x))


def _rmse_reducer(sq_err: np.ndarray) -> float:
    return float(np.sqrt(np.mean(sq_err)))


def bootstrap_point_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_boot: int = 1000,
    seed: int = 42,
) -> dict:
    """Bootstrap CIs for MAE and RMSE using the moving-block scheme."""
    m = _valid_mask(y_true, y_pred)
    err = np.asarray(y_true)[m] - np.asarray(y_pred)[m]
    mae_pt, mae_lo, mae_hi = moving_block_bootstrap_ci(
        np.abs(err), _mean, n_boot=n_boot, seed=seed
    )
    rmse_pt, rmse_lo, rmse_hi = moving_block_bootstrap_ci(
        err ** 2, _rmse_reducer, n_boot=n_boot, seed=seed
    )
    return {
        "mae": mae_pt, "mae_ci_low": mae_lo, "mae_ci_high": mae_hi,
        "rmse": rmse_pt, "rmse_ci_low": rmse_lo, "rmse_ci_high": rmse_hi,
    }


def bootstrap_interval_metrics(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    n_boot: int = 1000,
    seed: int = 42,
) -> dict:
    """Bootstrap CIs for empirical coverage and mean interval width."""
    m = _valid_mask(y_true, lower, upper)
    yt, lo, up = np.asarray(y_true)[m], np.asarray(lower)[m], np.asarray(upper)[m]
    inside = ((yt >= lo) & (yt <= up)).astype(float)
    width = up - lo
    cov_pt, cov_lo, cov_hi = moving_block_bootstrap_ci(inside, _mean, n_boot=n_boot, seed=seed)
    w_pt, w_lo, w_hi = moving_block_bootstrap_ci(width, _mean, n_boot=n_boot, seed=seed)
    return {
        "coverage": cov_pt, "coverage_ci_low": cov_lo, "coverage_ci_high": cov_hi,
        "width": w_pt, "width_ci_low": w_lo, "width_ci_high": w_hi,
    }
