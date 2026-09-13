"""One fitted interval estimator shared by core and robustness evaluation."""
from __future__ import annotations
import time
import numpy as np
import pandas as pd
from . import conformal_cqr, conformal_quantile, conformal_enbpi, recalibration
from .residuals import DelayedResidualPool


def group_mask(groups, group):
    values = np.asarray(groups)
    return pd.isna(values) if pd.isna(group) else values == group


def recalibrated_bounds(strategy, point, y_observed, y_calib, point_calib,
                        groups, origins, targets, calib_groups, calib_targets,
                        level, horizon, *, update_every=48, window=250,
                        min_samples=30):
    """Use only this asset's observable residuals; unseen runs start from
    the fixed, pre-test calibration pool, never another test run's updates.
    """
    point = np.asarray(point, float)
    observed = np.asarray(y_observed, float)
    if observed.shape != point.shape:
        raise ValueError("observed outcomes must align with point predictions")
    cal_res = np.asarray(y_calib, float) - np.asarray(point_calib, float)
    lower = np.empty(len(point)); upper = np.empty(len(point))
    ct = pd.DatetimeIndex(calib_targets)
    origins, targets = pd.DatetimeIndex(origins), pd.DatetimeIndex(targets)
    for group in pd.unique(groups):
        rows = np.flatnonzero(group_mask(groups, group))
        rows = rows[np.argsort(targets.values[rows], kind="stable")]
        cm = group_mask(calib_groups, group)
        if not cm.any():
            # Whole-run holdout: shared historical calibration is explicit;
            # online test residuals below are still isolated to this new run.
            cm = np.ones(len(cal_res), bool)
        pool = DelayedResidualPool.build(cal_res[cm], ct[cm],
            observed[rows] - point[rows], origins[rows], targets[rows], horizon)
        result = recalibration.apply_strategy(point[rows], pool, level, strategy,
            update_every=update_every, window=window, min_samples=min_samples)
        lower[rows], upper[rows] = result.lower, result.upper
    return lower, upper


class IntervalEstimator:
    """CQR/quantiles own HistGBR; EnbPI owns its fitted base predictor.

    This is not a wrapper around a separately selected LSTM/XGBoost point model.
    Every calibration prediction is made by the SAME fitted predictor as test.
    """
    def __init__(self, method, level, X_tr, y_tr, X_ca, y_ca, meta_ca,
                 horizon, seed=42):
        self.method, self.level, self.horizon = method, float(level), int(horizon)
        self.meta_ca = meta_ca.copy(); self.y_ca = np.asarray(y_ca, float)
        self.seed = int(seed); start = time.perf_counter()
        self.fallback = None
        if method in ("cqr", "quantile_uncalibrated"):
            self.m = conformal_cqr.fit_cqr(X_tr, pd.Series(y_tr), X_ca,
                                          pd.Series(y_ca), self.level, seed=self.seed)
            self.estimator_class = "sklearn.ensemble.HistGradientBoostingRegressor"
            self.point_ca = conformal_cqr.cqr_interval(self.m, X_ca)["point"]
        elif method in ("recentred_enbpi_static", "recentred_enbpi_updated"):
            from mapie.regression import TimeSeriesRegressor
            from mapie.subsample import BlockBootstrap
            base, name = conformal_enbpi._build_base(self.seed, {"base_n_estimators": 60})
            self.estimator_class = type(base).__module__ + "." + type(base).__name__
            if name != "XGBRegressor":
                self.fallback = {"requested": "XGBRegressor", "actual": name,
                                 "reason": getattr(base, "_confosense_fallback_reason",
                                                   "XGBoost construction unavailable")}
            self.m = TimeSeriesRegressor(estimator=base, method="enbpi",
                cv=BlockBootstrap(n_resamplings=5, length=24, overlapping=True,
                                  random_state=self.seed),
                agg_function="mean", random_state=self.seed, n_jobs=1)
            self.m.fit(X_tr.to_numpy(), np.asarray(y_tr))
            self.m.conformalize(X_ca.to_numpy(), np.asarray(y_ca))
            self.point_ca = np.asarray(self.m.predict(X_ca.to_numpy(), ensemble=False)).ravel()
        else:
            raise ValueError(f"unsupported single-horizon interval method {method!r}")
        self.fit_seconds = time.perf_counter() - start
        self.resid_ca = self.y_ca - self.point_ca

    @property
    def identity(self):
        return {"estimator_class": self.estimator_class, "model_seed": self.seed,
                "interval_method": self.method, "fallback": self.fallback,
                "calibration_predictor_class": self.estimator_class,
                "unseen_group_calibration": "fixed_historical_pool; isolated_test_updates"}

    def predict(self, X_te, *, y_obs, groups, o_te, t_te):
        if self.method == "cqr":
            r = conformal_cqr.cqr_interval(self.m, X_te)
        elif self.method == "quantile_uncalibrated":
            r = conformal_quantile.quantile_interval(self.m, X_te)
        elif self.method == "recentred_enbpi_static":
            r = conformal_enbpi._recentered_intervals(self.m, X_te.to_numpy(), [self.level])[self.level]
        else:
            point = np.asarray(self.m.predict(X_te.to_numpy(), ensemble=False)).ravel()
            # Same signed-residual online construction, updated every origin.
            lo, hi = recalibrated_bounds("periodic", point, y_obs, self.y_ca,
                self.point_ca, groups, o_te, t_te, self.meta_ca.group_id.to_numpy(),
                self.meta_ca.target_time, self.level, self.horizon,
                update_every=1, min_samples=1, window=None)
            r = {"point": point, "lower": lo, "upper": hi}
        return tuple(np.asarray(r[k], float) for k in ("point", "lower", "upper"))

    def stream(self, X_te, *, y_obs, groups, o_te, t_te, strategy="static"):
        point, lo, hi = self.predict(X_te, y_obs=y_obs, groups=groups, o_te=o_te, t_te=t_te)
        if strategy != "static":
            lo, hi = recalibrated_bounds(strategy, point, y_obs, self.y_ca,
                self.point_ca, groups, o_te, t_te, self.meta_ca.group_id.to_numpy(),
                self.meta_ca.target_time, self.level, self.horizon)
        return {"point": point, "lower": lo, "upper": hi,
                "calibration_point": self.point_ca, "identity": self.identity}
