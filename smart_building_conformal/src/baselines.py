"""Naive forecasting baselines.

Both baselines are computed directly from the regularly-sampled target series so
that they never peek at the future: persistence uses the value observed at the
forecast origin, and the seasonal naive uses the value from exactly one daily
cycle before the target timestamp (which is always in the past for the short
horizons studied here).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def persistence_prediction(target: pd.Series, origins: pd.DatetimeIndex) -> np.ndarray:
    """Predict the target at ``origin + horizon`` with the value observed at ``origin``."""
    return target.reindex(origins).to_numpy(dtype=float)


def seasonal_naive_prediction(
    target: pd.Series,
    target_times: pd.DatetimeIndex,
    season_steps: int,
    freq: pd.Timedelta,
) -> np.ndarray:
    """Predict a target timestamp with the value one seasonal cycle earlier.

    If the required historical value is missing (e.g. it falls inside an
    unresolved long gap), the prediction is returned as NaN rather than being
    filled with any later value.
    """
    lagged_times = target_times - season_steps * freq
    return target.reindex(lagged_times).to_numpy(dtype=float)
