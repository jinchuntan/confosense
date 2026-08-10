"""Conformalized Quantile Regression (CQR) via MAPIE 1.4.1.

The quantile estimator is a ``HistGradientBoostingRegressor`` with the pinball
loss. MAPIE clones it to fit the lower, upper and median quantiles on the
training data, calibrates the interval on the calibration data, and produces
test intervals. A separate model is conformalized for each nominal level.

API used (MAPIE 1.4.1):
    ConformalizedQuantileRegressor(estimator, confidence_level).fit(...)
        .conformalize(...).predict_interval(...)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from mapie.regression import ConformalizedQuantileRegressor


def _quantile_estimator(seed: int) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        loss="quantile",
        max_iter=300,
        learning_rate=0.05,
        max_depth=None,
        min_samples_leaf=50,
        random_state=seed,
    )


def fit_cqr(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_calib: pd.DataFrame,
    y_calib: pd.Series,
    confidence_level: float,
    seed: int = 42,
) -> ConformalizedQuantileRegressor:
    """Fit the quantile models on training data and conformalize on calibration."""
    cqr = ConformalizedQuantileRegressor(
        estimator=_quantile_estimator(seed),
        confidence_level=confidence_level,
    )
    cqr.fit(X_train.to_numpy(), y_train.to_numpy())
    cqr.conformalize(X_calib.to_numpy(), y_calib.to_numpy())
    return cqr


def cqr_interval(model: ConformalizedQuantileRegressor, X: pd.DataFrame) -> dict:
    """Return point/lower/upper for an already-conformalized CQR model."""
    point, intervals = model.predict_interval(X.to_numpy())
    arr = np.asarray(intervals)
    return {
        "point": np.asarray(point).ravel(),
        "lower": arr[:, 0, 0],
        "upper": arr[:, 1, 0],
    }


def run_cqr(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_calib: pd.DataFrame,
    y_calib: pd.Series,
    X_test: pd.DataFrame,
    confidence_level: float,
    seed: int = 42,
) -> dict:
    """Fit, conformalize and predict a CQR interval on the test set."""
    model = fit_cqr(X_train, y_train, X_calib, y_calib, confidence_level, seed)
    return cqr_interval(model, X_test)
