"""Full robustness protocol: disturbance scenarios in open and closed loop.

The preliminary probe in :mod:`src.robustness` covered five scenarios and held
the prediction intervals fixed once a disturbance was injected. That was adequate
for a progress report and is explicitly flagged there as a limitation. This
module implements the dissertation protocol and keeps both behaviours available.

Scenarios (each reproducible from a recorded seed)
--------------------------------------------------
=====================  =========================================================
``random_missing``     5 / 10 / 20 % of test observations dropped at random
``block_missing``      contiguous outages, length scaled to the sampling interval
``bias``               constant sensor offset of 0.5 / 1.0 / 2.0 sigma
``level_shift``        a sudden, sustained step part-way through the test period
``drift``              a linear ramp reaching 1 sigma / 2 sigma by the end
``stuck``              the sensor freezes at its last value
``dropout``            a communications outage repeating the last good reading
``calibration_contamination``  1 / 5 / 10 % of the *calibration* set corrupted
=====================  =========================================================

``sigma`` is always the **training** standard deviation. Estimating it on the
partition about to be perturbed would let the disturbance size depend on the
held-out data.

Two evaluation modes
--------------------
``legacy_fixed_intervals``
    Only the observed value is perturbed; the intervals computed on clean
    features stay put. Preserved so the preliminary numbers remain reproducible.

``closed_loop`` *(primary)*
    The perturbation is written into the observation series, lagged and rolling
    features are recomputed from that corrupted history, the model re-forecasts
    from it, conformal scores update only as ground truth arrives, and alerts are
    driven by the resulting moving intervals. This is what a deployed system
    would actually experience: a bad reading contaminates tomorrow's features,
    not just today's residual.

Causality in closed loop is structural, not policed after the fact. Features are
built by :func:`src.features.build_supervised`, whose every term is a backward
shift, a backward-looking rolling window, or a deterministic calendar attribute
of the target timestamp; recalibration draws on
:class:`~src.residuals.DelayedResidualPool`. No forward-looking quantity exists
for a perturbed value to leak through.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from . import alert_study, alerts as alert_mod
from . import metrics as M
from . import recalibration as recal
from .residuals import DelayedResidualPool

MODES = ("legacy_fixed_intervals", "closed_loop")


# --------------------------------------------------------------------------- #
# Perturbations (pure: never modify their input)
# --------------------------------------------------------------------------- #
def _copy(series: pd.Series) -> pd.Series:
    return series.copy(deep=True)


def random_missing(series: pd.Series, mask: np.ndarray, param: float,
                   scale: float, rng: np.random.Generator) -> pd.Series:
    out = _copy(series)
    idx = np.flatnonzero(mask)
    if len(idx):
        drop = rng.choice(idx, size=int(round(param * len(idx))), replace=False)
        out.iloc[drop] = np.nan
    return out


def block_missing(series: pd.Series, mask: np.ndarray, param: float,
                  scale: float, rng: np.random.Generator, *, block: int = 12) -> pd.Series:
    """Contiguous outages totalling ``param`` of the region, in blocks of ``block``."""
    out = _copy(series)
    idx = np.flatnonzero(mask)
    if not len(idx):
        return out
    n_drop = int(round(param * len(idx)))
    n_blocks = max(1, n_drop // max(1, block))
    for _ in range(n_blocks):
        start = int(rng.integers(idx[0], max(idx[0] + 1, idx[-1] - block)))
        out.iloc[start:start + block] = np.nan
    return out


def bias(series: pd.Series, mask: np.ndarray, param: float,
         scale: float, rng: np.random.Generator) -> pd.Series:
    out = _copy(series)
    out.iloc[np.flatnonzero(mask)] += param * scale
    return out


def level_shift(series: pd.Series, mask: np.ndarray, param: float,
                scale: float, rng: np.random.Generator, *, at: float = 0.5) -> pd.Series:
    """A step applied from a fixed fraction ``at`` through the perturbed region."""
    out = _copy(series)
    idx = np.flatnonzero(mask)
    if len(idx):
        onset = idx[int(len(idx) * at)]
        out.iloc[onset:] += param * scale
    return out


def drift(series: pd.Series, mask: np.ndarray, param: float,
          scale: float, rng: np.random.Generator) -> pd.Series:
    out = _copy(series)
    idx = np.flatnonzero(mask)
    if len(idx):
        out.iloc[idx] += np.linspace(0.0, param * scale, len(idx))
    return out


def stuck(series: pd.Series, mask: np.ndarray, param: float,
          scale: float, rng: np.random.Generator) -> pd.Series:
    """Sensor freezes for ``param`` of the region, starting mid-way."""
    out = _copy(series)
    idx = np.flatnonzero(mask)
    if len(idx):
        n = max(1, int(round(param * len(idx))))
        start = idx[len(idx) // 2]
        out.iloc[start:start + n] = out.iloc[start]
    return out


def dropout(series: pd.Series, mask: np.ndarray, param: float,
            scale: float, rng: np.random.Generator) -> pd.Series:
    """Communications outage: the last good reading is repeated forward."""
    out = _copy(series)
    idx = np.flatnonzero(mask)
    if len(idx):
        n = max(1, int(round(param * len(idx))))
        start = idx[len(idx) // 3]
        last = out.iloc[start - 1] if start > 0 else out.iloc[start]
        out.iloc[start:start + n] = last
    return out


PERTURBATIONS: dict[str, Callable] = {
    "random_missing": random_missing,
    "block_missing": block_missing,
    "bias": bias,
    "level_shift": level_shift,
    "drift": drift,
    "stuck": stuck,
    "dropout": dropout,
}


@dataclass
class Scenario:
    name: str
    kind: str
    severity: float
    label: str = ""

    def describe(self) -> dict:
        return {"scenario": self.name, "kind": self.kind,
                "severity": self.severity, "severity_label": self.label or str(self.severity)}


def default_scenarios(cfg: dict) -> list[Scenario]:
    """Build the scenario list from configuration."""
    s: list[Scenario] = [Scenario("clean", "none", 0.0, "none")]
    for p in cfg.get("random_missing", [0.05, 0.10, 0.20]):
        s.append(Scenario(f"random_missing_{int(p*100)}pct", "random_missing", p, f"{int(p*100)}%"))
    for p in cfg.get("block_missing", [0.05, 0.10]):
        s.append(Scenario(f"block_missing_{int(p*100)}pct", "block_missing", p, f"{int(p*100)}%"))
    for p in cfg.get("bias_sds", [0.5, 1.0, 2.0]):
        s.append(Scenario(f"bias_{p}sd", "bias", p, f"{p} sigma"))
    for p in cfg.get("level_shift_sds", [1.0, 2.0]):
        s.append(Scenario(f"level_shift_{p}sd", "level_shift", p, f"{p} sigma"))
    for p in cfg.get("drift_sds", [1.0, 2.0]):
        s.append(Scenario(f"drift_{p}sd", "drift", p, f"{p} sigma terminal"))
    for p in cfg.get("stuck_fractions", [0.05]):
        s.append(Scenario(f"stuck_{int(p*100)}pct", "stuck", p, f"{int(p*100)}% of region"))
    for p in cfg.get("dropout_fractions", [0.05]):
        s.append(Scenario(f"dropout_{int(p*100)}pct", "dropout", p, f"{int(p*100)}% of region"))
    return s


def contamination_levels(cfg: dict) -> list[float]:
    return list(cfg.get("calibration_contamination", [0.01, 0.05, 0.10]))


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def evaluate_intervals_and_alerts(
    y_true: np.ndarray,
    observed: np.ndarray,
    point: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    level: float,
    rule: tuple[int, int],
    freq: pd.Timedelta,
) -> dict:
    """Point, interval and alert-workload metrics for one perturbed run.

    Two truths are in play and conflating them hides the whole effect:

    ``observed``
        what the monitor actually receives. The alert logic reacts to this, and
        so does the headline ``empirical_coverage`` — "does the interval still
        contain the reading the sensor reported?" is the question a disturbance
        study is asking, and it is the quantity that moves when a sensor drifts.

    ``y_true``
        the clean value the sensor *should* have reported. Metrics against it
        carry the ``_vs_clean_truth`` suffix and answer a different question:
        how much did the forecast itself degrade once the corrupted history fed
        back into its features?

    In ``legacy_fixed_intervals`` mode the forecast never sees the perturbation,
    so the clean-truth metrics stay flat by construction and only the observed
    ones move. In ``closed_loop`` both move, which is exactly the difference the
    two modes exist to expose.
    """
    k, m = rule
    violations = alert_mod.point_violations(observed, lower, upper)
    alerts = alert_mod.apply_rule(violations, k, m)
    n = len(observed)
    freq_min = freq / pd.Timedelta(minutes=1)
    days = (n * freq_min) / (60.0 * 24.0)
    clusters = alert_mod._count_clusters(alerts)

    seen = M.interval_metrics(observed, lower, upper, level)
    clean = M.interval_metrics(y_true, lower, upper, level)
    return {
        "n_test": int(n),
        # Against the clean truth: forecast quality.
        "mae_vs_clean_truth": M.mae(y_true, point),
        "rmse_vs_clean_truth": M.rmse(y_true, point),
        "empirical_coverage_vs_clean_truth": clean["empirical_coverage"],
        "coverage_deviation_vs_clean_truth": clean["coverage_deviation"],
        # Against what the monitor sees: what the alert logic reacts to.
        "mae": M.mae(observed, point), "rmse": M.rmse(observed, point),
        **seen,
        "alert_rate": float(np.mean(alerts)),
        "n_alert_clusters": int(clusters),
        "false_alert_events_per_day": clusters / days if days else float("nan"),
        "n_violation_steps": int(np.sum(violations)),
    }


def coverage_recovery(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    level: float,
    onset_index: int,
    block: int,
) -> pd.DataFrame:
    """Block-wise coverage either side of a disturbance onset."""
    return recal.recovery_profile(y_true, lower, upper, level, onset_index, block)


def build_pool(
    calib_resid: np.ndarray,
    calib_target_times: pd.DatetimeIndex,
    test_resid: np.ndarray,
    test_origin_times: pd.DatetimeIndex,
    test_target_times: pd.DatetimeIndex,
    horizon: int,
) -> DelayedResidualPool:
    """Convenience wrapper so callers do not import :mod:`src.residuals` directly."""
    return DelayedResidualPool.build(
        calib_resid, calib_target_times, test_resid,
        test_origin_times, test_target_times, horizon,
    )


def perturb_series(
    target: pd.Series,
    region_mask: np.ndarray,
    scenario: Scenario,
    scale: float,
    seed: int,
    *,
    block_steps: int = 12,
    max_gap: int = 3,
) -> pd.Series:
    """Apply one scenario to a copy of ``target`` over ``region_mask``.

    Missingness scenarios are re-imputed with the pipeline's own short-gap rule
    afterwards, so what reaches the model is what the real preprocessing would
    have produced from a lossy sensor — not a silently dropped row.
    """
    if scenario.kind == "none":
        return target.copy(deep=True)
    fn = PERTURBATIONS[scenario.kind]
    rng = np.random.default_rng(seed)
    kwargs = {}
    if scenario.kind == "block_missing":
        kwargs["block"] = block_steps
    out = fn(target, region_mask, scenario.severity, scale, rng, **kwargs)
    if scenario.kind in ("random_missing", "block_missing"):
        out = out.interpolate(method="time", limit=max_gap, limit_area="inside")
    return out
