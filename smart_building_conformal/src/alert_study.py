"""Full-study alerting: event catalogue, k-of-m sensitivity, and scoring.

Extends the preliminary :mod:`src.alerts` rather than replacing it — that module
is left untouched so the committed preliminary experiment keeps reproducing —
and adds the three things the dissertation protocol requires.

**A richer disturbance catalogue.** Seven controlled event types: isolated spike,
sustained positive bias, sustained negative bias, abrupt level shift, gradual
drift, stuck sensor, and temporary dropout. Positive and negative bias are kept
as *separate* types with a fixed sign rather than one type with a random sign,
because an interval method can easily be asymmetric and a signed breakdown is
what exposes that. Every injected event records its dataset, target, type,
severity, index and timestamp bounds, duration, realised magnitude and seed.

**Rule selection that never sees the test set.** :func:`rule_surface` scores every
candidate k-of-m rule on *calibration* data with its own injected events;
:func:`select_rule` freezes one operating rule from that surface alone. The same
surface is then computed on test data for reporting, but it is labelled
``post_hoc_sensitivity`` and is never fed back into the choice — the distinction
is carried in the output rows themselves, not just in prose.

**Two false-alarm measures, kept apart.** ``far`` is the point-level False Alarm
Rate, FP / (FP + TN) over timesteps outside any event window.
``false_alert_events_per_day`` counts contiguous alert *clusters* outside event
windows, normalised by the observation span. They answer different questions —
one is a rate per opportunity, the other a workload per day — and conflating them
under the name "FAR" would misreport both.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import alerts as base

# Candidate aggregation rules. The list is configurable; these are the defaults.
CANDIDATE_RULES: dict[str, tuple[int, int]] = {
    "1-of-1": (1, 1),
    "2-of-3": (2, 3),
    "3-of-5": (3, 5),
    "4-of-7": (4, 7),
}

EVENT_TYPES = (
    "spike", "bias_positive", "bias_negative", "level_shift",
    "drift", "stuck", "dropout",
)


def parse_rules(names: list[str] | None) -> dict[str, tuple[int, int]]:
    """Resolve configured rule names like ``"3-of-5"`` into ``(k, m)`` pairs."""
    if not names:
        return dict(CANDIDATE_RULES)
    out = {}
    for name in names:
        if name in CANDIDATE_RULES:
            out[name] = CANDIDATE_RULES[name]
            continue
        try:
            k, m = name.lower().split("-of-")
            k, m = int(k), int(m)
        except ValueError as exc:
            raise ValueError(f"cannot parse alert rule {name!r}; expected 'k-of-m'") from exc
        if not 1 <= k <= m:
            raise ValueError(f"invalid alert rule {name!r}: need 1 <= k <= m")
        out[name] = (k, m)
    return out


# --------------------------------------------------------------------------- #
# Event injection
# --------------------------------------------------------------------------- #
def _event_specs(cfg: dict) -> list[dict]:
    """Expand the configuration into a flat list of event specifications."""
    n = int(cfg.get("instances_per_type", 3))
    specs: list[dict] = []

    for mag in cfg.get("spike_sds", [4.0]):
        for _ in range(n):
            specs.append({"type": "spike", "severity": f"{mag}sd",
                          "magnitude_sd": mag, "duration": 1, "sign": +1})
    for mag in cfg.get("bias_sds", [0.5, 1.0, 2.0]):
        for sign, kind in ((+1, "bias_positive"), (-1, "bias_negative")):
            for _ in range(n):
                specs.append({"type": kind, "severity": f"{mag}sd",
                              "magnitude_sd": mag,
                              "duration": int(cfg.get("bias_steps", 18)), "sign": sign})
    for mag in cfg.get("level_shift_sds", [0.5, 1.0, 2.0]):
        for _ in range(n):
            specs.append({"type": "level_shift", "severity": f"{mag}sd",
                          "magnitude_sd": mag,
                          "duration": int(cfg.get("level_shift_steps", 12)), "sign": +1})
    for mag in cfg.get("drift_sds", [1.0, 2.0]):
        for _ in range(n):
            specs.append({"type": "drift", "severity": f"{mag}sd",
                          "magnitude_sd": mag,
                          "duration": int(cfg.get("drift_steps", 36)), "sign": +1})
    for _ in range(n):
        specs.append({"type": "stuck", "severity": "stuck", "magnitude_sd": 0.0,
                      "duration": int(cfg.get("stuck_steps", 18)), "sign": 0})
    for _ in range(n):
        specs.append({"type": "dropout", "severity": "dropout", "magnitude_sd": 0.0,
                      "duration": int(cfg.get("dropout_steps", 12)), "sign": 0})
    return specs


def inject_events(
    clean: np.ndarray,
    scale: float,
    freq: pd.Timedelta,
    times: pd.DatetimeIndex,
    cfg: dict,
    seed: int,
    *,
    dataset: str,
    target: str,
    partition: str,
    group_ids: np.ndarray | None = None,
) -> tuple[np.ndarray, pd.DataFrame]:
    """Inject the configured catalogue into a **copy** of ``clean``.

    ``clean`` is never modified: a fresh array is allocated and returned, so the
    held-out observations stay pristine for every other scenario. ``scale`` is a
    dispersion estimated on *training* data, so event magnitudes never depend on
    the partition being perturbed.

    Events are placed inside a single group where ``group_ids`` is supplied, so a
    RICO event cannot straddle two experimental runs.
    """
    perturbed = np.array(clean, dtype=float, copy=True)
    n = len(perturbed)
    specs = _event_specs(cfg)
    placed = base._place_events(
        specs, n,
        warmup=int(cfg.get("warmup_steps", 6)),
        guard=int(cfg.get("guard_steps", 6)),
        seed=seed,
    )

    rng = np.random.default_rng(seed + 1)
    rows = []
    eid = 0
    for e in placed:
        s, end = e["start_index"], e["end_index"]
        if group_ids is not None and len(set(np.asarray(group_ids)[s:end + 1])) > 1:
            continue                      # would cross a run/building boundary
        mag = e["magnitude_sd"] * scale
        sign = e.get("sign", 1)
        if e["type"] == "spike":
            direction = 1.0 if rng.random() < 0.5 else -1.0
            perturbed[s] += direction * mag
            realised = direction * mag
        elif e["type"] in ("bias_positive", "bias_negative", "level_shift"):
            direction = float(sign) if sign else (1.0 if rng.random() < 0.5 else -1.0)
            perturbed[s:end + 1] += direction * mag
            realised = direction * mag
        elif e["type"] == "drift":
            direction = 1.0 if rng.random() < 0.5 else -1.0
            perturbed[s:end + 1] += np.linspace(0.0, direction * mag, end - s + 1)
            realised = direction * mag
        elif e["type"] == "stuck":
            perturbed[s:end + 1] = perturbed[s]
            realised = 0.0
        elif e["type"] == "dropout":
            # A communications outage: the last good reading is repeated, which
            # is what a gap-filled telemetry pipeline actually presents.
            perturbed[s:end + 1] = perturbed[s - 1] if s > 0 else perturbed[s]
            realised = 0.0
        else:                                            # pragma: no cover
            continue

        rows.append({
            "dataset": dataset, "target": target, "partition": partition,
            "event_id": eid, "event_type": e["type"], "severity": e["severity"],
            "magnitude_sd": e["magnitude_sd"], "injected_magnitude": realised,
            "scale_used": scale,
            "start_index": s, "end_index": end, "duration_steps": end - s + 1,
            "start_time": times[s], "end_time": times[end],
            "group_id": (np.asarray(group_ids)[s] if group_ids is not None else None),
            "seed": seed,
        })
        eid += 1

    return perturbed, pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def false_alarm_rate(alerts: np.ndarray, event_mask: np.ndarray) -> dict:
    """Point-level FAR = FP / (FP + TN) over timesteps outside any event."""
    alerts = np.asarray(alerts, dtype=bool)
    outside = ~np.asarray(event_mask, dtype=bool)
    fp = int(np.sum(alerts & outside))
    tn = int(np.sum(~alerts & outside))
    denom = fp + tn
    return {"point_false_positives": fp, "point_true_negatives": tn,
            "far": (fp / denom) if denom else float("nan")}


def score_rule(
    observed: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    catalog: pd.DataFrame,
    k: int,
    m: int,
    freq: pd.Timedelta,
    tolerance: int,
) -> dict:
    """Event-level and point-level metrics for one k-of-m rule."""
    violations = base.point_violations(observed, lower, upper)
    alerts = base.apply_rule(violations, k, m)
    n = len(observed)
    ev = base.evaluate_alerts(alerts, catalog, n, freq, tolerance)
    mask = base._event_mask(catalog, n, tolerance) if len(catalog) else np.zeros(n, bool)
    far = false_alarm_rate(alerts, mask)
    return {**ev, **far, "k": k, "m": m,
            "n_violation_steps": int(np.sum(violations)),
            "n_alert_steps": int(np.sum(alerts))}


def rule_surface(
    observed: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    catalog: pd.DataFrame,
    rules: dict[str, tuple[int, int]],
    freq: pd.Timedelta,
    tolerance: int,
    *,
    context: dict,
    role: str,
) -> pd.DataFrame:
    """Score every candidate rule; ``role`` records what the surface is *for*.

    ``role`` is ``calibration_selection`` when the surface drives the choice and
    ``post_hoc_sensitivity`` when it is reported after the rule has been frozen.
    """
    rows = []
    for name, (k, m) in rules.items():
        rows.append({**context, "role": role, "rule": name,
                     **score_rule(observed, lower, upper, catalog, k, m, freq, tolerance)})
    return pd.DataFrame(rows)


def select_rule(surface: pd.DataFrame, budget: float) -> tuple[str, str]:
    """Freeze one operating rule from a **calibration** surface.

    Highest recall among rules whose false-alert workload is within ``budget``,
    ties broken by shorter median detection delay then fewer false alerts. If no
    rule meets the budget, the quietest rule is taken and that is stated in the
    returned rationale rather than passed over.
    """
    if surface.empty:
        raise ValueError("cannot select an alert rule from an empty surface")
    within = surface[surface["false_alert_events_per_day"] <= budget]
    if len(within):
        # Budget satisfied: buy as much recall as it affords.
        ordered = within.sort_values(
            by=["recall", "median_detection_delay_min", "false_alert_events_per_day"],
            ascending=[False, True, True],
        )
        note = f"within the budget of {budget} false alerts/day"
    else:
        # Budget missed by every candidate. Taking the highest-recall rule here
        # would hand the operator the *noisiest* option precisely when none is
        # quiet enough, so the quietest is taken instead and the shortfall is
        # stated rather than passed over.
        ordered = surface.sort_values(
            by=["false_alert_events_per_day", "recall", "median_detection_delay_min"],
            ascending=[True, False, True],
        )
        note = (f"no candidate met the budget of {budget} false alerts/day, so the "
                "rule with the lowest false-alert frequency was taken")
    chosen = str(ordered.iloc[0]["rule"])
    reason = (
        f"selected on calibration data only: highest event recall among rules {note}; "
        "ties broken by median detection delay then false-alert frequency. No test "
        "observation influenced this choice."
    )
    return chosen, reason
