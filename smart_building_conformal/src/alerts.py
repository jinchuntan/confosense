"""Interval-based alerting: point violations, aggregation rules, synthetic event
injection, rule selection, and event-level scoring.

Design decisions (documented for the report):

* A *point violation* at time t is ``observed_t < lower_t or observed_t > upper_t``.
* The prediction interval is treated as fixed when events are injected: only the
  observed value is perturbed, isolating the alerting logic from feedback of the
  perturbation into model features. This is a deliberate simplification for a
  preliminary experiment.
* Aggregation rules ``k-of-m`` fire when at least ``k`` of the last ``m`` points
  (inclusive of the current one) are violations.
* Rule selection is performed only on calibration data (with its own injected
  events); the chosen rule is frozen before touching the test set.
* Detection is event-level: an event counts as detected (TP) if any alert fires
  inside its window (extended by a small tolerance); missed events are FN.
  False alerts are contiguous alert clusters outside every event window, and are
  reported both as a count (FP) and as a per-day frequency.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RULES: dict[str, tuple[int, int]] = {
    "1-of-1": (1, 1),
    "2-of-3": (2, 3),
    "3-of-5": (3, 5),
}


# --------------------------------------------------------------------------- #
# Violations and aggregation
# --------------------------------------------------------------------------- #
def point_violations(observed: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    observed = np.asarray(observed, dtype=float)
    return (observed < np.asarray(lower)) | (observed > np.asarray(upper))


def apply_rule(violations: np.ndarray, k: int, m: int) -> np.ndarray:
    """Return the alert flag for every position under a k-of-m rule."""
    v = pd.Series(np.asarray(violations, dtype=float))
    rolled = v.rolling(window=m, min_periods=1).sum().to_numpy()
    return rolled >= k


# --------------------------------------------------------------------------- #
# Synthetic event injection
# --------------------------------------------------------------------------- #
def _event_specs(cfg: dict) -> list[dict]:
    """Expand the configuration into a flat list of event specifications."""
    n = cfg.get("instances_per_type", 3)
    specs: list[dict] = []
    for mag in cfg.get("level_shift_sds", [0.5, 1.0, 2.0]):
        for _ in range(n):
            specs.append({"type": "level_shift", "severity": f"{mag}sd",
                          "magnitude_sd": mag, "duration": cfg.get("level_shift_steps", 12)})
    for label, mag in zip(("low", "high"), cfg.get("drift_sds", [1.0, 2.0])):
        for _ in range(n):
            specs.append({"type": "drift", "severity": label,
                          "magnitude_sd": mag, "duration": cfg.get("drift_steps", 36)})
    for _ in range(n):
        specs.append({"type": "spike", "severity": "spike",
                      "magnitude_sd": cfg.get("spike_sd", 4.0), "duration": 1})
    for _ in range(n):
        specs.append({"type": "stuck", "severity": "stuck",
                      "magnitude_sd": 0.0, "duration": cfg.get("stuck_steps", 18)})
    return specs


def _place_events(specs: list[dict], n: int, warmup: int, guard: int, seed: int) -> list[dict]:
    """Assign non-overlapping start positions using a fixed seed."""
    rng = np.random.default_rng(seed)
    occupied: list[tuple[int, int]] = []
    placed = []
    for spec in specs:
        dur = spec["duration"]
        hi = n - dur - guard
        if hi <= warmup:
            continue
        start = None
        for _ in range(200):
            cand = int(rng.integers(warmup, hi))
            window = (cand - guard, cand + dur + guard)
            if all(window[1] < a or window[0] > b for a, b in occupied):
                start = cand
                break
        if start is None:
            continue
        occupied.append((start, start + dur))
        e = dict(spec)
        e["start_index"] = start
        e["end_index"] = start + dur - 1
        placed.append(e)
    placed.sort(key=lambda e: e["start_index"])
    return placed


def inject_events(
    clean: np.ndarray,
    train_std: float,
    freq: pd.Timedelta,
    times: pd.DatetimeIndex,
    cfg: dict,
    seed: int,
    dataset_label: str,
) -> tuple[np.ndarray, pd.DataFrame]:
    """Return (perturbed_series, event_catalog) for a copy of ``clean``."""
    perturbed = np.array(clean, dtype=float, copy=True)
    n = len(perturbed)
    specs = _event_specs(cfg)
    events = _place_events(
        specs, n,
        warmup=cfg.get("warmup_steps", 6),
        guard=cfg.get("guard_steps", 6),
        seed=seed,
    )
    rng = np.random.default_rng(seed + 1)
    catalog = []
    for eid, e in enumerate(events):
        s, end = e["start_index"], e["end_index"]
        mag = e["magnitude_sd"] * train_std
        sign = 1.0 if rng.random() < 0.5 else -1.0
        if e["type"] == "level_shift":
            perturbed[s:end + 1] += sign * mag
        elif e["type"] == "drift":
            ramp = np.linspace(0.0, sign * mag, end - s + 1)
            perturbed[s:end + 1] += ramp
        elif e["type"] == "spike":
            perturbed[s] += sign * mag
        elif e["type"] == "stuck":
            perturbed[s:end + 1] = perturbed[s]
        catalog.append({
            "dataset": dataset_label,
            "event_id": eid,
            "event_type": e["type"],
            "severity": e["severity"],
            "magnitude_sd": e["magnitude_sd"],
            "start_index": s,
            "end_index": end,
            "start_time": times[s],
            "end_time": times[end],
            "n_steps": end - s + 1,
        })
    return perturbed, pd.DataFrame(catalog)


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def _event_mask(catalog: pd.DataFrame, n: int, tolerance: int) -> np.ndarray:
    mask = np.zeros(n, dtype=bool)
    for _, row in catalog.iterrows():
        s = int(row["start_index"])
        e = min(n - 1, int(row["end_index"]) + tolerance)
        mask[s:e + 1] = True
    return mask


def _count_clusters(flags: np.ndarray) -> int:
    """Number of contiguous True runs."""
    if not flags.any():
        return 0
    return int(np.sum(flags & ~np.concatenate([[False], flags[:-1]])))


def evaluate_alerts(
    alerts: np.ndarray,
    catalog: pd.DataFrame,
    n: int,
    freq: pd.Timedelta,
    tolerance: int,
) -> dict:
    """Event-level precision/recall/F1, false-alert rate and detection delay."""
    alerts = np.asarray(alerts, dtype=bool)
    freq_min = freq / pd.Timedelta(minutes=1)

    tp, fn, delays = 0, 0, []
    for _, row in catalog.iterrows():
        s = int(row["start_index"])
        e = min(n - 1, int(row["end_index"]) + tolerance)
        fired = np.where(alerts[s:e + 1])[0]
        if len(fired):
            tp += 1
            delays.append(int(fired[0]) * freq_min)  # steps from event start -> minutes
        else:
            fn += 1

    ev_mask = _event_mask(catalog, n, tolerance)
    false_flags = alerts & ~ev_mask
    fp = _count_clusters(false_flags)

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = (2 * precision * recall / (precision + recall)
          if precision and recall and np.isfinite(precision) and np.isfinite(recall) else float("nan"))

    days = (n * freq_min) / (60.0 * 24.0)
    false_per_day = fp / days if days else float("nan")

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_alert_events_per_day": false_per_day,
        "mean_detection_delay_min": float(np.mean(delays)) if delays else float("nan"),
        "median_detection_delay_min": float(np.median(delays)) if delays else float("nan"),
        "n_events": int(len(catalog)),
    }


def natural_false_alerts(alerts: np.ndarray, n: int, freq: pd.Timedelta) -> dict:
    """False-alert statistics on clean data (no injected events)."""
    freq_min = freq / pd.Timedelta(minutes=1)
    fp = _count_clusters(np.asarray(alerts, dtype=bool))
    days = (n * freq_min) / (60.0 * 24.0)
    return {
        "false_positives": fp,
        "false_alert_events_per_day": fp / days if days else float("nan"),
        "n_alert_timesteps": int(np.sum(alerts)),
    }


def select_rule(
    observed_calib: np.ndarray,
    lower_calib: np.ndarray,
    upper_calib: np.ndarray,
    train_std: float,
    freq: pd.Timedelta,
    times_calib: pd.DatetimeIndex,
    cfg: dict,
    seed: int,
) -> tuple[str, pd.DataFrame]:
    """Choose an aggregation rule using calibration data with injected events.

    Preference: highest recall among rules whose false-alert rate is within the
    configured budget; ties broken by shortest median detection delay. If no rule
    meets the budget, the rule with the lowest false-alert rate is chosen.
    """
    perturbed, catalog = inject_events(
        observed_calib, train_std, freq, times_calib,
        cfg["events"], seed=seed, dataset_label="calibration",
    )
    tolerance = cfg.get("detection_tolerance_steps", 6)
    budget = cfg.get("max_false_alerts_per_day", 1.0)
    n = len(perturbed)

    rows = []
    for name, (k, m) in RULES.items():
        viol = point_violations(perturbed, lower_calib, upper_calib)
        alerts = apply_rule(viol, k, m)
        metrics = evaluate_alerts(alerts, catalog, n, freq, tolerance)
        metrics["rule"] = name
        rows.append(metrics)
    table = pd.DataFrame(rows)

    within = table[table["false_alert_events_per_day"] <= budget]
    pool = within if len(within) else table
    pool = pool.sort_values(
        by=["recall", "median_detection_delay_min", "false_alert_events_per_day"],
        ascending=[False, True, True],
    )
    chosen = str(pool.iloc[0]["rule"])
    return chosen, table
