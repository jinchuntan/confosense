"""Preliminary robustness checks.

Small, clearly-labelled stress tests applied to the test region of the target
series only. The training-fit models and the frozen alert rule are reused; the
perturbed test inputs are re-imputed with the same short-gap rule as the main
pipeline, features are rebuilt, and point / interval / alert metrics are
recomputed. This is a preliminary probe, not the full dissertation robustness
study.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from . import features as feat
from . import metrics as M
from . import alerts as alert_mod


def _reimpute_short_gaps(series: pd.Series, max_gap: int) -> pd.Series:
    return series.interpolate(method="time", limit=max_gap, limit_area="inside")


def _perturb(
    df: pd.DataFrame,
    test_mask: np.ndarray,
    scenario: str,
    param: float,
    train_std: float,
    max_gap: int,
    seed: int,
) -> pd.DataFrame:
    out = df.copy()
    target = out["target"].copy()
    idx = np.where(test_mask)[0]
    if scenario == "missing":
        rng = np.random.default_rng(seed)
        drop = rng.choice(idx, size=int(round(param * len(idx))), replace=False)
        target.iloc[drop] = np.nan
        target = _reimpute_short_gaps(target, max_gap)
    elif scenario == "level_shift":
        target.iloc[idx] += param * train_std
    elif scenario == "drift":
        target.iloc[idx] += np.linspace(0.0, param * train_std, len(idx))
    out["target"] = target
    return out


def run(
    df: pd.DataFrame,
    test_start_time,
    freq: pd.Timedelta,
    season_steps: int,
    feature_cfg: dict,
    predict_fn: Callable[[pd.DataFrame], tuple[np.ndarray, np.ndarray, np.ndarray]],
    rule: tuple[int, int],
    train_std: float,
    nominal_level: float,
    cfg: dict,
    seed: int = 42,
) -> pd.DataFrame:
    """Run the robustness scenarios and return a tidy metrics table."""
    horizon = cfg.get("horizon", 1)
    max_gap = cfg.get("max_short_gap_steps", 3)
    k, m = rule
    grid = df.index
    test_mask = np.asarray(grid >= test_start_time)

    scenarios = [
        ("clean", "none", 0.0),
        ("missing_5pct", "missing", 0.05),
        ("missing_10pct", "missing", 0.10),
        ("level_shift_1sd", "level_shift", 1.0),
        ("drift", "drift", cfg.get("drift_sd", 1.0)),
    ]

    rows = []
    for name, kind, param in scenarios:
        pdf = df if kind == "none" else _perturb(
            df, test_mask, kind, param, train_std, max_gap, seed
        )
        sup = feat.build_supervised(pdf, horizon, freq, season_steps, feature_cfg)
        meta = sup["meta"]
        keep = meta["origin_time"] >= test_start_time
        X = sup["X"].loc[keep.values]
        y_true = meta.loc[keep, "y_true"].to_numpy()
        if len(X) == 0:
            continue

        point, lower, upper = predict_fn(X)
        viol = alert_mod.point_violations(y_true, lower, upper)
        alerts = alert_mod.apply_rule(viol, k, m)
        n = len(y_true)
        freq_min = freq / pd.Timedelta(minutes=1)
        days = (n * freq_min) / (60.0 * 24.0)
        n_false_clusters = alert_mod._count_clusters(alerts)

        # For the shift/drift scenarios the whole test region is the event, so
        # "recall" is whether the rule fired at all during that region.
        recall = float(alerts.any()) if kind in ("level_shift", "drift") else float("nan")

        rows.append({
            "scenario": name,
            "n_test": n,
            "mae": M.mae(y_true, point),
            "rmse": M.rmse(y_true, point),
            "empirical_coverage": M.empirical_coverage(y_true, lower, upper),
            "mean_interval_width": M.mean_interval_width(lower, upper),
            "alert_recall": recall,
            "false_alert_events_per_day": n_false_clusters / days if days else float("nan"),
            "nominal_level": nominal_level,
        })

    return pd.DataFrame(rows)
