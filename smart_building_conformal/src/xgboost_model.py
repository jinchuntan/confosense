"""XGBoost point-forecasting model with a CPU-friendly time-series search.

Hyperparameters are selected with a randomized search evaluated by a
``TimeSeriesSplit`` cross-validator, which respects chronological order and is
run strictly on the training partition. The calibration and test partitions are
never seen during tuning.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from xgboost import XGBRegressor

# Documented search space. Kept modest so the whole search runs quickly on CPU.
PARAM_DISTRIBUTIONS = {
    "n_estimators": [200, 400, 600, 800],
    "max_depth": [3, 4, 5, 6, 8],
    "learning_rate": [0.01, 0.03, 0.05, 0.1],
    "subsample": [0.6, 0.8, 1.0],
    "colsample_bytree": [0.6, 0.8, 1.0],
    "min_child_weight": [1, 3, 5, 7],
    "reg_lambda": [0.0, 1.0, 5.0],
    "reg_alpha": [0.0, 0.5, 1.0],
}


def _base_estimator(seed: int, n_jobs: int) -> XGBRegressor:
    return XGBRegressor(
        objective="reg:squarederror",
        tree_method="hist",
        random_state=seed,
        n_jobs=n_jobs,
    )


def tune(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_iter: int = 20,
    n_splits: int = 3,
    seed: int = 42,
    n_jobs: int = -1,
) -> dict:
    """Randomized time-series search on the training data only."""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    search = RandomizedSearchCV(
        estimator=_base_estimator(seed, n_jobs=1),
        param_distributions=PARAM_DISTRIBUTIONS,
        n_iter=n_iter,
        scoring="neg_mean_absolute_error",
        cv=tscv,
        random_state=seed,
        n_jobs=n_jobs,
        refit=True,
        verbose=0,
    )
    search.fit(X_train.to_numpy(), y_train.to_numpy())
    return {
        "best_params": search.best_params_,
        "best_cv_mae": float(-search.best_score_),
        "estimator": search.best_estimator_,
    }


def fit_with_params(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: dict,
    seed: int,
    n_jobs: int = -1,
) -> XGBRegressor:
    """Refit an XGBoost regressor with fixed hyperparameters and a given seed."""
    model = _base_estimator(seed, n_jobs=n_jobs)
    model.set_params(**params)
    model.fit(X_train.to_numpy(), y_train.to_numpy())
    return model


def predict(model: XGBRegressor, X: pd.DataFrame) -> np.ndarray:
    return model.predict(X.to_numpy())
