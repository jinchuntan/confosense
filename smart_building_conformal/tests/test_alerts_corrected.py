"""Corrected alerting primitives: group-safety, physical time, one-to-one
onset-aware matching, honest metrics and feasibility abstention (D2/D3/D6/D7/D8).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import alerts_corrected as AC


# ---- D3: physical-time rule conversion ---------------------------------- #
def test_physical_time_rule_conversion_feasible():
    # 15-minute window at 1-min sampling -> 15 steps; 3 violations feasible.
    r = AC.convert_physical_rule(15, 3, freq_minutes=1.0)
    assert r.applicable and r.m_steps == 15 and r.k == 3


def test_physical_time_rule_infeasible_is_marked_not_coerced():
    # "2 violations in 5 minutes" at 10-min PLEIA sampling: the window is < 1
    # sample, so the rule is not applicable and is not silently coerced.
    r = AC.convert_physical_rule(5, 2, freq_minutes=10.0)
    assert not r.applicable and "not applicable" in r.reason


def test_physical_time_rule_infeasible_when_more_violations_than_steps():
    # 30-minute window at 60-min (hourly BDG2) sampling -> 0 steps; infeasible.
    r = AC.convert_physical_rule(30, 3, freq_minutes=60.0)
    assert not r.applicable


# ---- D2: group-safe state ----------------------------------------------- #
def test_kofm_window_resets_at_group_boundary():
    # Two violations straddling a group boundary must NOT satisfy 2-of-3.
    viol = np.array([0, 1, 1, 0])          # positions 1,2 are violations
    groups = np.array(["A", "A", "B", "B"])  # boundary between pos 1 and 2
    alerts = AC.apply_rule_grouped(viol, k=2, m=3, groups=groups)
    # Within group A only one violation; within B only one -> no 2-of-3 anywhere.
    assert not alerts.any()


def test_kofm_fires_within_a_single_group():
    viol = np.array([1, 1, 0, 0])
    groups = np.array(["A", "A", "A", "A"])
    alerts = AC.apply_rule_grouped(viol, k=2, m=3, groups=groups)
    assert alerts[1]        # two of the last three at pos 1


def test_episodes_never_span_two_groups():
    alerts = np.array([1, 1, 1, 1])
    groups = np.array(["A", "A", "B", "B"])
    eps = AC.alert_episodes(alerts, groups)
    assert len(eps) == 2
    assert {e["group"] for e in eps} == {"A", "B"}


# ---- D6: one-to-one, onset-aware matching ------------------------------- #
def _catalog(rows):
    return pd.DataFrame(rows)


def test_alarm_active_before_onset_earns_no_credit():
    # Episode spans positions 0-5; event onset is at position 3. The episode was
    # already active before the onset, so it must NOT count as a detection.
    episodes = [{"group": "A", "start": 0, "end": 5, "onset": 0}]
    cat = _catalog([{"event_id": 0, "event_type": "bias", "severity": "1.0sd",
                     "group_id": "A", "start_index": 3, "end_index": 5}])
    res = AC.match_events(episodes, cat, tolerance_steps=1, freq_minutes=1.0)
    assert res["n_detected"] == 0


def test_new_onset_inside_event_window_is_detected():
    episodes = [{"group": "A", "start": 4, "end": 6, "onset": 4}]
    cat = _catalog([{"event_id": 0, "event_type": "bias", "severity": "1.0sd",
                     "group_id": "A", "start_index": 3, "end_index": 6}])
    res = AC.match_events(episodes, cat, tolerance_steps=1, freq_minutes=1.0)
    assert res["n_detected"] == 1
    assert int(res["per_event"].iloc[0]["detection_delay_steps"]) == 1


def test_matching_is_one_to_one():
    # One episode cannot detect two events; the second event stays a miss.
    episodes = [{"group": "A", "start": 5, "end": 5, "onset": 5}]
    cat = _catalog([
        {"event_id": 0, "event_type": "bias", "severity": "1.0sd",
         "group_id": "A", "start_index": 5, "end_index": 6},
        {"event_id": 1, "event_type": "bias", "severity": "1.0sd",
         "group_id": "A", "start_index": 5, "end_index": 6},
    ])
    res = AC.match_events(episodes, cat, tolerance_steps=1, freq_minutes=1.0)
    assert res["n_detected"] == 1
    assert res["per_event"]["detected"].sum() == 1


def test_background_episode_outside_events_counted_not_as_false_positive():
    episodes = [{"group": "A", "start": 50, "end": 52, "onset": 50}]
    cat = _catalog([{"event_id": 0, "event_type": "bias", "severity": "1.0sd",
                     "group_id": "A", "start_index": 5, "end_index": 6}])
    res = AC.match_events(episodes, cat, tolerance_steps=1, freq_minutes=1.0)
    assert res["n_background_episodes"] == 1 and res["n_detected"] == 0


# ---- D8: honest metrics ------------------------------------------------- #
def test_macro_recall_weights_strata_equally():
    per_event = pd.DataFrame({
        "event_type": ["a", "a", "a", "b"],
        "severity": ["s", "s", "s", "s"],
        "detected": [True, True, True, False],
    })
    m = AC.macro_event_recall(per_event)
    # micro = 3/4 = 0.75; macro = mean(recall_a=1.0, recall_b=0.0) = 0.5
    assert abs(m["micro_recall"] - 0.75) < 1e-9
    assert abs(m["macro_recall"] - 0.5) < 1e-9


def test_background_workload_per_asset_day():
    groups = np.array(["A"] * 1440)          # one day at 1-min sampling
    w = AC.background_workload_per_asset_day(3, groups, freq_minutes=1.0)
    assert abs(w["monitored_asset_days"] - 1.0) < 1e-6
    assert abs(w["background_episodes_per_asset_day"] - 3.0) < 1e-6


# ---- D7: abstention ----------------------------------------------------- #
def test_no_feasible_configuration_when_constraints_unmet():
    surface = pd.DataFrame({
        "rule": ["1-of-1", "2-of-3"],
        "macro_recall": [0.30, 0.20],
        "background_episodes_per_asset_day": [5.0, 4.0],
    })
    out = AC.select_pipeline(surface, min_recall=0.60, workload_max=1.0,
                             use_confidence_bounds=False)
    assert out["decision"] == AC.NO_FEASIBLE


def test_feasible_candidate_is_selected():
    surface = pd.DataFrame({
        "rule": ["1-of-1", "3-of-5"],
        "macro_recall": [0.80, 0.70],
        "background_episodes_per_asset_day": [0.5, 0.2],
        "macro_fbeta": [0.75, 0.72],
        "median_detection_delay_min": [3.0, 5.0],
    })
    out = AC.select_pipeline(surface, min_recall=0.60, workload_max=1.0,
                             use_confidence_bounds=False)
    assert out["decision"] == "selected" and out["rule"] == "1-of-1"
