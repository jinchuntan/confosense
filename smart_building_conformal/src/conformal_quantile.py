"""Uncalibrated quantile-regression intervals — the reference CQR is measured against.

CQR takes a quantile regressor's raw ``[q_{α/2}, q_{1−α/2}]`` band and widens (or
narrows) it by a conformity quantile estimated on calibration data. Reporting
only the conformalized band leaves the obvious question unanswered: *how much did
conformal calibration actually change?* This module answers it by extracting the
band **before** that correction.

The intervals here are not a re-fit approximation. MAPIE's
:class:`ConformalizedQuantileRegressor` keeps the three fitted sub-estimators it
conformalizes — lower, upper and median, in that order, each carrying its own
``quantile`` parameter — and this module predicts directly from those objects.
The uncalibrated and CQR bands therefore share identical training data, identical
hyperparameters and identical random seeds, so the only difference between them
*is* the conformal step.

Naming: these appear in every output table as ``quantile_uncalibrated``, never
merged into or labelled as ``cqr``. They carry no coverage guarantee, and on
building data they are typically too narrow — which is the point of showing them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from mapie.regression import ConformalizedQuantileRegressor

METHOD_NAME = "quantile_uncalibrated"


def _sub_estimators(model: ConformalizedQuantileRegressor):
    """Return (lower, upper, median) sub-estimators with their quantile levels.

    Raises if the expected structure is absent, rather than silently falling back
    to a differently-trained model that would make the comparison invalid.
    """
    inner = getattr(model, "_mapie_quantile_regressor", None)
    estimators = getattr(inner, "estimators_", None)
    if inner is None or not estimators or len(estimators) < 2:
        raise RuntimeError(
            "the installed MAPIE build does not expose the fitted quantile "
            "sub-estimators; the uncalibrated baseline cannot be derived from "
            "the same models CQR conformalizes"
        )
    levels = [getattr(e, "quantile", None) for e in estimators[:3]]
    return estimators, levels


def quantile_interval(model: ConformalizedQuantileRegressor, X: pd.DataFrame) -> dict:
    """Raw quantile band from the models CQR was built on (no conformal step).

    The lower/upper crossing that quantile regressors occasionally produce is
    repaired by ordering the pair, exactly as MAPIE does internally, so the
    interval stays well-formed without altering its width elsewhere.
    """
    estimators, levels = _sub_estimators(model)
    arr = X.to_numpy() if isinstance(X, pd.DataFrame) else np.asarray(X)
    lower = np.asarray(estimators[0].predict(arr), dtype=float).ravel()
    upper = np.asarray(estimators[1].predict(arr), dtype=float).ravel()
    if len(estimators) > 2:
        point = np.asarray(estimators[2].predict(arr), dtype=float).ravel()
    else:
        point = 0.5 * (lower + upper)

    lo = np.minimum(lower, upper)
    hi = np.maximum(lower, upper)
    return {
        "point": point, "lower": lo, "upper": hi,
        "quantile_levels": levels,
        "n_crossed": int(np.sum(lower > upper)),
    }
