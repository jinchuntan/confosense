"""Statistical comparison of forecasting methods.

Four families, all implemented on numpy/scipy so no extra dependency is needed:

* **Moving-block bootstrap** — reused from :mod:`src.metrics`, but applied here
  to *every* point model rather than only the machine-learning ones. On this data
  persistence is frequently the strongest short-horizon baseline, so excluding
  simple models from the confidence-interval table would have hidden the actual
  winner.
* **Diebold–Mariano** — pairwise equal-predictive-accuracy test on the loss
  differential series, with the Harvey–Leybourne–Newbold small-sample correction
  and a Newey–West long-run variance. Valid only within a single
  (dataset, target, horizon, test period), which the caller is responsible for
  holding fixed.
* **Friedman** — rank-based test across repeated blocks (buildings, horizons,
  datasets) for three or more methods. Requires a complete methods × blocks
  matrix; incomplete designs are refused rather than silently imputed.
* **Holm** — step-down multiplicity correction, implemented directly (six lines)
  rather than by adding statsmodels for one function.

Effect sizes accompany every test, because a significant p-value on tens of
thousands of test points says almost nothing about whether a difference matters
operationally.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import metrics as M


# --------------------------------------------------------------------------- #
# Multiplicity correction
# --------------------------------------------------------------------------- #
def holm_adjust(pvalues) -> np.ndarray:
    """Holm–Bonferroni step-down adjusted p-values.

    Sorted ascending, each raw p is multiplied by the number of hypotheses still
    under test, then made monotone non-decreasing and clipped at 1.
    """
    p = np.asarray(pvalues, dtype=float)
    finite = np.isfinite(p)
    out = np.full(p.shape, np.nan)
    if not finite.any():
        return out
    vals = p[finite]
    order = np.argsort(vals)
    m = len(vals)
    adjusted = np.empty(m, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * vals[idx])
        adjusted[idx] = min(1.0, running)
    out[finite] = adjusted
    return out


# --------------------------------------------------------------------------- #
# Diebold-Mariano
# --------------------------------------------------------------------------- #
def diebold_mariano(
    y_true,
    pred_a,
    pred_b,
    *,
    horizon: int = 1,
    loss: str = "absolute",
) -> dict:
    """Test equal predictive accuracy of ``pred_a`` against ``pred_b``.

    A negative statistic means model A has the lower loss. The long-run variance
    uses ``horizon - 1`` autocovariance lags, which is the standard choice for
    an ``h``-step forecast whose errors are MA(h−1) under the null.
    """
    y = np.asarray(y_true, dtype=float)
    a = np.asarray(pred_a, dtype=float)
    b = np.asarray(pred_b, dtype=float)
    mask = np.isfinite(y) & np.isfinite(a) & np.isfinite(b)
    y, a, b = y[mask], a[mask], b[mask]
    n = len(y)
    result = {
        "n": n, "loss": loss, "horizon": horizon,
        "mean_loss_a": np.nan, "mean_loss_b": np.nan,
        "dm_statistic": np.nan, "p_value": np.nan, "mean_loss_differential": np.nan,
    }
    if n < 10:
        result["note"] = "too few paired observations for a DM test"
        return result

    if loss == "absolute":
        la, lb = np.abs(y - a), np.abs(y - b)
    elif loss == "squared":
        la, lb = (y - a) ** 2, (y - b) ** 2
    else:
        raise ValueError(f"unknown loss {loss!r}")

    d = la - lb
    dbar = float(np.mean(d))
    result["mean_loss_a"] = float(np.mean(la))
    result["mean_loss_b"] = float(np.mean(lb))
    result["mean_loss_differential"] = dbar

    # Newey-West long-run variance with h-1 lags.
    lags = max(0, horizon - 1)
    dc = d - dbar
    gamma0 = float(np.mean(dc * dc))
    lrv = gamma0
    for k in range(1, lags + 1):
        if k >= n:
            break
        gk = float(np.mean(dc[k:] * dc[:-k]))
        lrv += 2.0 * (1.0 - k / (lags + 1.0)) * gk
    if lrv <= 0:
        result["note"] = "non-positive long-run variance; DM statistic undefined"
        return result

    dm = dbar / np.sqrt(lrv / n)
    # Harvey-Leybourne-Newbold small-sample correction.
    corr = np.sqrt((n + 1 - 2 * horizon + horizon * (horizon - 1) / n) / n)
    dm_hln = dm * corr
    p = float(2 * stats.t.sf(abs(dm_hln), df=n - 1))

    result.update({"dm_statistic": float(dm_hln), "p_value": p,
                   "better_model": "a" if dbar < 0 else ("b" if dbar > 0 else "tie")})
    return result


def pairwise_dm_table(
    y_true,
    predictions: dict,
    pairs: list[tuple[str, str]],
    *,
    horizon: int,
    context: dict,
    loss: str = "absolute",
) -> pd.DataFrame:
    """Run a set of DM comparisons and Holm-adjust their p-values together."""
    rows = []
    for a, b in pairs:
        if a not in predictions or b not in predictions:
            continue
        pa, pb = np.asarray(predictions[a], float), np.asarray(predictions[b], float)
        if not np.isfinite(pa).any() or not np.isfinite(pb).any():
            # e.g. seasonal naive on a dataset where it is not applicable
            continue
        res = diebold_mariano(y_true, pa, pb, horizon=horizon, loss=loss)
        rows.append({**context, "model_a": a, "model_b": b, **res})
    if not rows:
        return pd.DataFrame()
    table = pd.DataFrame(rows)
    table["p_value_holm"] = holm_adjust(table["p_value"].to_numpy())
    table["significant_holm_5pct"] = table["p_value_holm"] < 0.05
    return table


# --------------------------------------------------------------------------- #
# Friedman + post-hoc
# --------------------------------------------------------------------------- #
def friedman_test(matrix: pd.DataFrame) -> dict:
    """Friedman test over a complete blocks (rows) x methods (columns) matrix.

    Lower values are assumed better, so ranks are ascending. Blocks with any
    missing entry are dropped and the number retained is reported, because
    ranking a method that is absent from some blocks would bias the comparison.
    """
    clean = matrix.dropna(axis=0, how="any")
    n_blocks, n_methods = clean.shape
    out = {
        "n_blocks": int(n_blocks), "n_methods": int(n_methods),
        "statistic": np.nan, "p_value": np.nan,
        "n_blocks_dropped": int(len(matrix) - n_blocks),
    }
    if n_methods < 3 or n_blocks < 3:
        out["note"] = ("Friedman needs at least 3 methods and 3 complete blocks; "
                       f"got {n_methods} methods over {n_blocks} blocks")
        return out
    stat, p = stats.friedmanchisquare(*[clean[c].to_numpy() for c in clean.columns])
    ranks = clean.rank(axis=1, ascending=True)
    out.update({
        "statistic": float(stat), "p_value": float(p),
        "mean_ranks": {c: float(ranks[c].mean()) for c in clean.columns},
    })
    return out


def nemenyi_style_posthoc(matrix: pd.DataFrame) -> pd.DataFrame:
    """Pairwise post-hoc comparison of mean ranks with Holm adjustment.

    Uses a Wilcoxon signed-rank test per pair over the matched blocks — an exact
    paired test that does not assume normality — rather than a critical-distance
    approximation, then applies Holm across the whole family.
    """
    clean = matrix.dropna(axis=0, how="any")
    cols = list(clean.columns)
    if len(clean) < 3 or len(cols) < 2:
        return pd.DataFrame()
    ranks = clean.rank(axis=1, ascending=True)
    rows = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            xa, xb = clean[a].to_numpy(), clean[b].to_numpy()
            if np.allclose(xa, xb):
                p = 1.0
            else:
                try:
                    p = float(stats.wilcoxon(xa, xb).pvalue)
                except ValueError:
                    p = np.nan
            rows.append({
                "method_a": a, "method_b": b, "n_blocks": len(clean),
                "mean_rank_a": float(ranks[a].mean()),
                "mean_rank_b": float(ranks[b].mean()),
                "median_difference": float(np.median(xa - xb)),
                "p_value": p,
            })
    table = pd.DataFrame(rows)
    if len(table):
        table["p_value_holm"] = holm_adjust(table["p_value"].to_numpy())
        table["significant_holm_5pct"] = table["p_value_holm"] < 0.05
    return table


# --------------------------------------------------------------------------- #
# Effect sizes
# --------------------------------------------------------------------------- #
def effect_sizes(y_true, pred_a, pred_b, *, n_boot: int = 1000, seed: int = 42) -> dict:
    """Practical-significance measures for A relative to B.

    Reports percentage MAE/RMSE improvement, the paired median absolute-error
    difference, and a moving-block bootstrap interval for the mean loss
    differential so the reader can see whether the difference is distinguishable
    from zero *and* whether it is large enough to matter.
    """
    y = np.asarray(y_true, dtype=float)
    a = np.asarray(pred_a, dtype=float)
    b = np.asarray(pred_b, dtype=float)
    mask = np.isfinite(y) & np.isfinite(a) & np.isfinite(b)
    y, a, b = y[mask], a[mask], b[mask]
    if len(y) < 2:
        return {"n": int(len(y))}

    mae_a, mae_b = M.mae(y, a), M.mae(y, b)
    rmse_a, rmse_b = M.rmse(y, a), M.rmse(y, b)
    ae_a, ae_b = np.abs(y - a), np.abs(y - b)
    d = ae_a - ae_b
    _, lo, hi = M.moving_block_bootstrap_ci(
        d, lambda x: float(np.mean(x)), n_boot=n_boot, seed=seed
    )
    return {
        "n": int(len(y)),
        "mae_a": mae_a, "mae_b": mae_b,
        "rmse_a": rmse_a, "rmse_b": rmse_b,
        "pct_mae_improvement": M.pct_improvement(mae_b, mae_a),
        "pct_rmse_improvement": M.pct_improvement(rmse_b, rmse_a),
        "median_abs_error_difference": float(np.median(d)),
        "mean_abs_error_difference": float(np.mean(d)),
        "mean_difference_ci_low": lo,
        "mean_difference_ci_high": hi,
        "win_rate_a": float(np.mean(ae_a < ae_b)),
    }


def bootstrap_all_point_models(
    y_true,
    predictions: dict,
    *,
    context: dict,
    n_boot: int = 1000,
    seed: int = 42,
) -> pd.DataFrame:
    """Moving-block bootstrap CIs for **every** point model, baselines included."""
    rows = []
    for name, pred in predictions.items():
        p = np.asarray(pred, dtype=float)
        if not np.isfinite(p).any():
            continue
        rows.append({**context, "model": name,
                     **M.bootstrap_point_metrics(y_true, p, n_boot=n_boot, seed=seed)})
    return pd.DataFrame(rows)


def ranking_matrix(
    long: pd.DataFrame,
    *,
    block_cols: list[str],
    method_col: str,
    value_col: str,
) -> pd.DataFrame:
    """Pivot a long metrics table into the blocks x methods matrix Friedman needs."""
    sub = long.dropna(subset=[value_col])
    if sub.empty:
        return pd.DataFrame()
    return sub.pivot_table(
        index=block_cols, columns=method_col, values=value_col, aggfunc="mean"
    )
