"""Corrected, group-safe, physical-time alerting primitives.

This module implements the alerting corrections the audit requires without
disturbing the preliminary :mod:`src.alerts` / :mod:`src.alert_study` code that
the committed preliminary experiment still reproduces. The corrected nested study
imports these primitives:

* **D3 — physical-time rules.** :func:`convert_physical_rule` turns a wall-clock
  ``k-of-(window)`` rule into a ``k-of-m`` step rule for a given sampling
  frequency and marks it ``not_applicable`` (with a reason) when the window holds
  fewer steps than the required violations — never silently coercing it.
* **D2 — group-safe state.** :func:`apply_rule_grouped`, :func:`alert_episodes`
  and every counter here reset at each run/building boundary; no k-of-m window,
  episode or cooldown ever spans two groups.
* **D6 — one-to-one, onset-aware matching.** :func:`match_events` builds alert
  episodes first, then matches at most one episode to at most one event, and only
  credits an episode whose onset lands inside the event (plus tolerance) — an
  alarm already active before the event onset earns no detection credit.
* **D8 — honest metrics.** Recall is macro-averaged across type x severity;
  unmatched episodes are *background alert episodes per monitored asset-day*, not
  "false positives". Precision is available but labelled prevalence-dependent.
* **D7 — abstention.** :func:`select_pipeline` returns
  ``no_feasible_configuration`` when no candidate meets the frozen recall and
  workload constraints, rather than force-selecting the least-bad one.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# D3 — physical-time rule conversion
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RuleConversion:
    name: str
    window_minutes: float
    required_violations: int
    freq_minutes: float
    m_steps: int
    k: int
    applicable: bool
    reason: str


def convert_physical_rule(
    window_minutes: float,
    required_violations: int,
    freq_minutes: float,
    name: str | None = None,
) -> RuleConversion:
    """Convert a wall-clock rule to a ``k-of-m`` step rule for one frequency.

    ``m`` is the number of samples spanning ``window_minutes`` at ``freq_minutes``
    sampling. A rule that needs more violations than the window has steps is
    infeasible at that frequency and is returned with ``applicable=False`` and a
    recorded reason — it is never rounded into a different rule.
    """
    if freq_minutes <= 0:
        raise ValueError("freq_minutes must be positive")
    if required_violations < 1:
        raise ValueError("required_violations must be >= 1")
    m = int(np.floor(window_minutes / freq_minutes + 1e-9))
    label = name or f"{window_minutes:g}min-{required_violations}"
    if m < 1:
        return RuleConversion(label, window_minutes, required_violations,
                              freq_minutes, m, required_violations, False,
                              f"window {window_minutes} min < one sample "
                              f"({freq_minutes} min): rule not applicable")
    if required_violations > m:
        return RuleConversion(label, window_minutes, required_violations,
                              freq_minutes, m, required_violations, False,
                              f"needs {required_violations} violations in {m} "
                              f"steps: impossible at {freq_minutes}-min sampling")
    return RuleConversion(label, window_minutes, required_violations,
                          freq_minutes, m, required_violations, True,
                          "converted from physical time")


# --------------------------------------------------------------------------- #
# D2 — group-safe violations, aggregation and episodes
# --------------------------------------------------------------------------- #
def point_violations(observed, lower, upper) -> np.ndarray:
    observed = np.asarray(observed, dtype=float)
    return (observed < np.asarray(lower)) | (observed > np.asarray(upper))


def apply_rule_grouped(violations, k: int, m: int, groups) -> np.ndarray:
    """k-of-m alert flag, with the rolling window reset at every group boundary.

    ``violations`` and ``groups`` are aligned and assumed already ordered by time
    within each group (the study orders test rows that way). The rolling sum never
    reaches back across a run or building boundary.
    """
    v = np.asarray(violations, dtype=float)
    g = np.asarray(groups)
    out = np.zeros(len(v), dtype=bool)
    for grp in pd.unique(g):
        idx = np.nonzero(g == grp)[0]
        rolled = (pd.Series(v[idx]).rolling(window=m, min_periods=1)
                  .sum().to_numpy())
        out[idx] = rolled >= k
    return out


def alert_episodes(alerts, groups, *, cooldown_steps: int = 0) -> list[dict]:
    """Contiguous alert runs within a group, merged across gaps <= cooldown.

    Returns one dict per episode with ``group``, ``start`` (== ``onset``) and
    ``end`` positional indices into the original arrays. Episodes never span two
    groups.
    """
    a = np.asarray(alerts, dtype=bool)
    g = np.asarray(groups)
    episodes: list[dict] = []
    for grp in pd.unique(g):
        idx = np.nonzero(g == grp)[0]
        sub = a[idx]
        i = 0
        n = len(sub)
        while i < n:
            if not sub[i]:
                i += 1
                continue
            start = i
            end = i
            j = i + 1
            gap = 0
            while j < n:
                if sub[j]:
                    end = j
                    gap = 0
                else:
                    gap += 1
                    if gap > cooldown_steps:
                        break
                j += 1
            episodes.append({"group": grp, "start": int(idx[start]),
                             "end": int(idx[end]), "onset": int(idx[start])})
            i = end + 1
    episodes.sort(key=lambda e: e["start"])
    return episodes


# --------------------------------------------------------------------------- #
# D6 — one-to-one, onset-aware matching
# --------------------------------------------------------------------------- #
def match_events(
    episodes: list[dict],
    catalog: pd.DataFrame,
    *,
    tolerance_steps: int,
    freq_minutes: float,
    overlap_tolerance_steps: int = 0,
) -> dict:
    """Match episodes to injected events one-to-one, onset-aware.

    An event is *detected* only by an episode whose onset falls in
    ``[event_start, event_end + tolerance]`` **and** at or after the event onset
    (an alarm already active before the event began earns no credit). Each episode
    detects at most one event and each event is detected by at most one episode;
    matching is greedy by earliest eligible onset. Episodes matching no event and
    whose onset lies outside every event window are *background* episodes.
    """
    tol = int(tolerance_steps) + int(overlap_tolerance_steps)
    events = catalog.reset_index(drop=True)
    used_ep = set()
    matched = []            # (event_row_index, episode_index, delay_steps)

    # Group episodes by group for same-group matching only.
    eps_by_group: dict = {}
    for ei, ep in enumerate(episodes):
        eps_by_group.setdefault(ep["group"], []).append(ei)

    for ev_i, ev in events.iterrows():
        g = ev.get("group_id", None)
        s = int(ev["start_index"])
        e = int(ev["end_index"])
        window_hi = e + tol
        best = None
        for ei in eps_by_group.get(g, []):
            if ei in used_ep:
                continue
            onset = episodes[ei]["onset"]
            if s <= onset <= window_hi:            # onset-aware + tolerance
                if best is None or onset < episodes[best]["onset"]:
                    best = ei
        if best is not None:
            used_ep.add(best)
            matched.append((int(ev_i), best, episodes[best]["onset"] - s))

    detected = {m[0] for m in matched}
    # Background episodes: unmatched AND onset outside every event window (same grp).
    ev_windows: dict = {}
    for _, ev in events.iterrows():
        ev_windows.setdefault(ev.get("group_id", None), []).append(
            (int(ev["start_index"]), int(ev["end_index"]) + tol))
    background = []
    for ei, ep in enumerate(episodes):
        if ei in used_ep:
            continue
        onset = ep["onset"]
        inside = any(lo <= onset <= hi
                     for lo, hi in ev_windows.get(ep["group"], []))
        if not inside:
            background.append(ei)

    rows = []
    for ev_i, ev in events.iterrows():
        is_det = ev_i in detected
        delay = next((m[2] for m in matched if m[0] == ev_i), None)
        rows.append({
            "event_id": ev.get("event_id", ev_i),
            "event_type": ev.get("event_type", ""),
            "severity": ev.get("severity", ""),
            "group_id": ev.get("group_id", None),
            "detected": bool(is_det),
            "detection_delay_steps": (int(delay) if delay is not None else np.nan),
            "detection_delay_min": (float(delay) * freq_minutes
                                    if delay is not None else np.nan),
        })
    per_event = pd.DataFrame(rows)
    return {
        "per_event": per_event,
        "n_events": int(len(events)),
        "n_detected": int(len(detected)),
        "n_background_episodes": int(len(background)),
        "matched_pairs": matched,
        "background_episode_indices": background,
    }


# --------------------------------------------------------------------------- #
# D8 — honest metrics
# --------------------------------------------------------------------------- #
def macro_event_recall(per_event: pd.DataFrame) -> dict:
    """Recall macro-averaged across event type x severity strata.

    Macro recall weights every (type, severity) stratum equally, so a common
    easy-to-detect event cannot dominate a rare hard one. Micro recall (pooled)
    is reported alongside for reference.
    """
    if per_event.empty:
        return {"macro_recall": float("nan"), "micro_recall": float("nan"),
                "by_stratum": {}}
    strata = per_event.groupby(["event_type", "severity"])["detected"].mean()
    micro = float(per_event["detected"].mean())
    return {
        "macro_recall": float(strata.mean()),
        "micro_recall": micro,
        "by_stratum": {f"{t}|{s}": float(v) for (t, s), v in strata.items()},
        "n_strata": int(len(strata)),
    }


def background_workload_per_asset_day(
    n_background_episodes: int,
    groups,
    freq_minutes: float,
) -> dict:
    """Background alert episodes per monitored asset-day.

    The denominator is the monitored exposure: total observed asset-time summed
    over groups, in days. This is the honest workload measure — it counts alarms
    the operator would field on clean data, not "false positives against real
    faults" (the public datasets carry no comprehensive fault labels).
    """
    g = np.asarray(groups)
    total_steps = len(g)
    asset_days = (total_steps * freq_minutes) / (60.0 * 24.0)
    return {
        "n_background_episodes": int(n_background_episodes),
        "monitored_asset_days": float(asset_days),
        "background_episodes_per_asset_day":
            (n_background_episodes / asset_days) if asset_days else float("nan"),
    }


def precision_prevalence_dependent(n_detected: int, n_background: int) -> dict:
    """Precision, explicitly labelled prevalence-dependent (secondary only)."""
    denom = n_detected + n_background
    return {
        "precision_prevalence_dependent":
            (n_detected / denom) if denom else float("nan"),
        "note": "prevalence-dependent: reflects the injected event incidence, "
                "not a real-world false-positive rate",
    }


# --------------------------------------------------------------------------- #
# D7 — feasibility-constrained selection with abstention
# --------------------------------------------------------------------------- #
NO_FEASIBLE = "no_feasible_configuration"


def select_pipeline(
    surface: pd.DataFrame,
    *,
    min_recall: float,
    workload_max: float,
    beta: float = 1.0,
    use_confidence_bounds: bool = True,
) -> dict:
    """Freeze one pipeline from an inner-selection surface, or abstain.

    A candidate is feasible when its recall (lower CI bound if available) meets
    ``min_recall`` and its background workload (upper CI bound if available) is at
    or below ``workload_max``. Among feasible candidates the macro F-beta is
    maximised, ties broken by shorter median detection delay. If nothing is
    feasible the decision is :data:`NO_FEASIBLE` — never a forced least-bad pick.
    """
    if surface.empty:
        return {"decision": NO_FEASIBLE, "reason": "empty selection surface"}
    df = surface.copy()
    rcol = ("macro_recall_lower_ci" if use_confidence_bounds
            and "macro_recall_lower_ci" in df else "macro_recall")
    wcol = ("workload_upper_ci" if use_confidence_bounds
            and "workload_upper_ci" in df else "background_episodes_per_asset_day")
    feasible = df[(df[rcol] >= min_recall) & (df[wcol] <= workload_max)]
    if feasible.empty:
        return {
            "decision": NO_FEASIBLE,
            "reason": (f"no candidate met macro recall >= {min_recall} and "
                       f"background workload <= {workload_max}/asset-day"),
            "n_candidates": int(len(df)),
        }
    if "macro_fbeta" not in feasible:
        b2 = beta * beta
        prec = feasible.get("precision_prevalence_dependent", feasible[rcol])
        rec = feasible[rcol]
        feasible = feasible.assign(
            macro_fbeta=(1 + b2) * prec * rec / (b2 * prec + rec).replace(0, np.nan))
    delay_col = ("median_detection_delay_min" if "median_detection_delay_min"
                 in feasible else rcol)
    ordered = feasible.sort_values(
        by=["macro_fbeta", delay_col], ascending=[False, True])
    best = ordered.iloc[0]
    return {
        "decision": "selected",
        "rule": str(best.get("rule", "")),
        "chosen": best.to_dict(),
        "reason": (f"feasible (recall>={min_recall}, workload<={workload_max}); "
                   "max macro F-beta, ties by detection delay; inner data only"),
        "n_feasible": int(len(feasible)),
        "n_candidates": int(len(df)),
    }
