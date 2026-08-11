"""Direct multi-horizon feature construction.

For a forecast horizon ``h`` (in resampled steps) every feature is evaluated at
the origin time ``t`` and uses only information available at or before ``t``,
plus deterministic calendar attributes of the target time ``t + h``. The target
is the observed value at ``t + h``. Rows whose features or target fall inside an
unresolved long gap contain NaNs and are removed, which is exactly how forecast
windows that would cross a long gap are excluded.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import baselines


def _cyclical(values: np.ndarray, period: int) -> tuple[np.ndarray, np.ndarray]:
    angle = 2.0 * np.pi * values / period
    return np.sin(angle), np.cos(angle)


def build_supervised(
    df: pd.DataFrame,
    horizon: int,
    freq: pd.Timedelta,
    season_steps: int | None,
    cfg: dict,
) -> dict:
    """Assemble the supervised learning matrices for one horizon.

    Returns a dict with:
      ``X``      feature frame indexed by origin time,
      ``y``      target (value at origin + horizon),
      ``meta``   origin/target times plus leak-free baseline predictions,
      ``feature_names`` ordered list of feature columns.
    All frames share the same (post-filtering) index.

    ``season_steps`` may be ``None`` for a series with no meaningful seasonal
    cycle — a RICO four-hour run, for instance. The seasonal lag features are
    then omitted and ``seasonal_naive_pred`` is returned as NaN, so the baseline
    is reported as *not applicable* rather than faked with an invented lag.
    """
    target = df["target"].astype(float)
    grid = df.index
    target_time = grid + horizon * freq

    feats: dict[str, np.ndarray | pd.Series] = {}

    # Recent target lags, including the current value (lag 0 == persistence input).
    for k in cfg["target_lags"]:
        feats[f"target_lag_{k}"] = target.shift(k)

    # Daily (and optional weekly) seasonal lag relative to the *target* time.
    # Skipped entirely when the series carries no valid seasonal cycle.
    if season_steps is not None:
        feats["target_daily_lag"] = target.shift(season_steps - horizon)
        if cfg.get("include_weekly", False):
            feats["target_weekly_lag"] = target.shift(7 * season_steps - horizon)

    # Rolling statistics over a short window and a full daily window (ending at t).
    for w in cfg["rolling_windows"]:
        min_p = max(2, w // 2)
        feats[f"target_rollmean_{w}"] = target.rolling(w, min_periods=min_p).mean()
        feats[f"target_rollstd_{w}"] = target.rolling(w, min_periods=min_p).std()

    # Cyclical calendar features of the target timestamp (deterministic, not leakage).
    hod = target_time.hour + target_time.minute / 60.0
    sin_h, cos_h = _cyclical(hod.to_numpy(dtype=float), 24)
    feats["hour_sin"], feats["hour_cos"] = sin_h, cos_h
    dow = target_time.dayofweek.to_numpy(dtype=float)
    sin_d, cos_d = _cyclical(dow, 7)
    feats["dow_sin"], feats["dow_cos"] = sin_d, cos_d

    # Present-time covariates and missingness indicators supplied by prepare_data.
    for col in cfg.get("covariates", []):
        if col in df.columns:
            feats[col] = df[col]
    for col in df.columns:
        if col.endswith("_was_missing"):
            feats[col] = df[col]

    X = pd.DataFrame(feats, index=grid)
    y = target.shift(-horizon)
    y.name = "y"

    meta = pd.DataFrame(
        {
            "origin_time": grid,
            "target_time": target_time,
            "y_true": y.to_numpy(),
            "persistence_pred": baselines.persistence_prediction(target, grid),
            "seasonal_naive_pred": (
                baselines.seasonal_naive_prediction(target, target_time, season_steps, freq)
                if season_steps is not None
                else np.full(len(grid), np.nan)
            ),
        },
        index=grid,
    )

    # Keep only rows with a complete feature vector and an observed target.
    valid = X.notna().all(axis=1) & y.notna()
    X, y, meta = X.loc[valid], y.loc[valid], meta.loc[valid]

    return {
        "X": X,
        "y": y,
        "meta": meta.reset_index(drop=True),
        "feature_names": list(X.columns),
    }
