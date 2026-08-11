"""Alert rules, event scoring, and the two distinct false-alarm measures."""

import numpy as np
import pandas as pd
import pytest

from src import alert_study, alerts as base

FREQ = pd.Timedelta("10min")


def _times(n):
    return pd.date_range("2021-09-01", periods=n, freq="10min")


# --------------------------------------------------------------------------- #
# k-of-m aggregation
# --------------------------------------------------------------------------- #
def test_k_of_m_fires_exactly_when_k_of_the_last_m_are_violations():
    v = np.array([0, 1, 1, 0, 0, 1, 1, 1, 0], dtype=bool)
    got = base.apply_rule(v, 2, 3)
    expected = [sum(v[max(0, i - 2): i + 1]) >= 2 for i in range(len(v))]
    assert list(got) == expected

    # 1-of-1 is just the violation series itself.
    assert list(base.apply_rule(v, 1, 1)) == list(v)
    # A rule that can never be met never fires.
    assert not base.apply_rule(v, 5, 5).any()


def test_rule_parsing_accepts_configured_names_and_rejects_nonsense():
    assert alert_study.parse_rules(["2-of-3", "4-of-7"]) == {
        "2-of-3": (2, 3), "4-of-7": (4, 7)}
    assert alert_study.parse_rules(["5-of-9"])["5-of-9"] == (5, 9)
    with pytest.raises(ValueError):
        alert_study.parse_rules(["7-of-3"])          # k > m
    with pytest.raises(ValueError):
        alert_study.parse_rules(["nonsense"])


# --------------------------------------------------------------------------- #
# The two false-alarm measures
# --------------------------------------------------------------------------- #
def test_far_is_a_point_rate_over_non_event_timesteps():
    alerts = np.array([1, 1, 0, 0, 0, 0, 1, 0, 0, 0], dtype=bool)
    event = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0], dtype=bool)
    out = alert_study.false_alarm_rate(alerts, event)
    # Outside the event there are 8 steps, of which 1 alerts.
    assert out["point_false_positives"] == 1
    assert out["point_true_negatives"] == 7
    assert out["far"] == pytest.approx(1 / 8)


def test_far_and_false_alerts_per_day_are_different_quantities():
    """A single long alert run is one workload event but many false points."""
    n = 144                                        # one day at 10-min sampling
    alerts = np.zeros(n, dtype=bool)
    alerts[100:140] = True                         # one contiguous cluster
    event = np.zeros(n, dtype=bool)

    far = alert_study.false_alarm_rate(alerts, event)["far"]
    per_day = base.natural_false_alerts(alerts, n, FREQ)

    assert far == pytest.approx(40 / n)            # 40 offending timesteps
    assert per_day["false_positives"] == 1         # but only one cluster
    assert per_day["false_alert_events_per_day"] == pytest.approx(1.0)
    assert far != per_day["false_alert_events_per_day"]


def test_false_alerts_per_day_scales_with_the_observation_span():
    n = 144 * 2                                    # two days at 10-min sampling
    alerts = np.zeros(n, dtype=bool)
    alerts[10] = alerts[100] = alerts[200] = True  # three separate clusters
    out = base.natural_false_alerts(alerts, n, FREQ)
    assert out["false_positives"] == 3
    assert out["false_alert_events_per_day"] == pytest.approx(1.5)


# --------------------------------------------------------------------------- #
# Event matching and detection delay
# --------------------------------------------------------------------------- #
def _catalog(rows):
    return pd.DataFrame([{"start_index": s, "end_index": e} for s, e in rows])


def test_event_is_detected_when_an_alert_falls_in_its_tolerance_window():
    n = 100
    alerts = np.zeros(n, dtype=bool)
    alerts[52] = True                              # inside the event
    cat = _catalog([(50, 55)])
    out = base.evaluate_alerts(alerts, cat, n, FREQ, tolerance=6)
    assert out["true_positives"] == 1
    assert out["false_negatives"] == 0
    assert out["recall"] == pytest.approx(1.0)
    # Delay is measured in minutes from the event start.
    assert out["mean_detection_delay_min"] == pytest.approx(2 * 10.0)


def test_alert_just_past_the_tolerance_is_a_miss_and_a_false_alert():
    n = 100
    alerts = np.zeros(n, dtype=bool)
    alerts[70] = True                              # event ends 55, +6 tolerance
    cat = _catalog([(50, 55)])
    out = base.evaluate_alerts(alerts, cat, n, FREQ, tolerance=6)
    assert out["true_positives"] == 0
    assert out["false_negatives"] == 1
    assert out["false_positives"] == 1


def test_detection_delay_uses_the_first_alert_in_the_window():
    n = 100
    alerts = np.zeros(n, dtype=bool)
    alerts[53] = alerts[54] = alerts[55] = True
    cat = _catalog([(50, 58)])
    out = base.evaluate_alerts(alerts, cat, n, FREQ, tolerance=6)
    assert out["mean_detection_delay_min"] == pytest.approx(30.0)
    assert out["median_detection_delay_min"] == pytest.approx(30.0)


def test_precision_recall_f1_are_consistent():
    n = 200
    alerts = np.zeros(n, dtype=bool)
    alerts[20] = True                              # detects event 1
    alerts[150] = True                             # spurious
    cat = _catalog([(18, 25), (100, 110)])
    out = base.evaluate_alerts(alerts, cat, n, FREQ, tolerance=4)
    assert out["true_positives"] == 1
    assert out["false_negatives"] == 1
    assert out["false_positives"] == 1
    assert out["precision"] == pytest.approx(0.5)
    assert out["recall"] == pytest.approx(0.5)
    assert out["f1"] == pytest.approx(0.5)


# --------------------------------------------------------------------------- #
# Injection
# --------------------------------------------------------------------------- #
def _clean(n=600):
    rng = np.random.default_rng(0)
    return 20 + np.sin(np.arange(n) / 30) + rng.normal(0, 0.05, n)


def test_injection_never_modifies_the_clean_array_in_place():
    clean = _clean()
    snapshot = clean.copy()
    cfg = {"instances_per_type": 2, "warmup_steps": 5, "guard_steps": 5}
    perturbed, cat = alert_study.inject_events(
        clean, 1.0, FREQ, _times(len(clean)), cfg, seed=1,
        dataset="d", target="t", partition="test")
    assert np.array_equal(clean, snapshot), "the held-out clean array was mutated"
    assert perturbed is not clean
    assert not np.array_equal(perturbed, clean)
    assert len(cat) > 0


def test_catalog_records_every_required_field():
    clean = _clean()
    cfg = {"instances_per_type": 2, "warmup_steps": 5, "guard_steps": 5}
    _, cat = alert_study.inject_events(
        clean, 1.0, FREQ, _times(len(clean)), cfg, seed=7,
        dataset="pleia", target="V2", partition="test")
    required = {"dataset", "target", "event_type", "severity", "start_index",
                "end_index", "start_time", "end_time", "duration_steps",
                "injected_magnitude", "seed"}
    assert required <= set(cat.columns)
    assert (cat["end_index"] >= cat["start_index"]).all()
    assert (cat["duration_steps"] >= 1).all()
    assert (cat["seed"] == 7).all()


def test_injection_is_reproducible_and_seed_dependent():
    clean = _clean()
    cfg = {"instances_per_type": 2, "warmup_steps": 5, "guard_steps": 5}
    args = (clean, 1.0, FREQ, _times(len(clean)), cfg)
    kw = dict(dataset="d", target="t", partition="test")
    a, ca = alert_study.inject_events(*args, seed=5, **kw)
    b, cb = alert_study.inject_events(*args, seed=5, **kw)
    c, _ = alert_study.inject_events(*args, seed=6, **kw)
    assert np.array_equal(a, b)
    assert ca.equals(cb)
    assert not np.array_equal(a, c)


def test_events_do_not_straddle_a_group_boundary():
    n = 600
    clean = _clean(n)
    groups = np.array(["A"] * 300 + ["B"] * 300)
    cfg = {"instances_per_type": 3, "warmup_steps": 5, "guard_steps": 5}
    _, cat = alert_study.inject_events(
        clean, 1.0, FREQ, _times(n), cfg, seed=2,
        dataset="rico", target="t", partition="test", group_ids=groups)
    for _, r in cat.iterrows():
        span = set(groups[int(r["start_index"]): int(r["end_index"]) + 1])
        assert len(span) == 1, "an event crossed a run boundary"


# --------------------------------------------------------------------------- #
# Rule selection
# --------------------------------------------------------------------------- #
def test_rule_selection_prefers_recall_within_the_false_alert_budget():
    surface = pd.DataFrame([
        {"rule": "1-of-1", "recall": 1.00, "median_detection_delay_min": 0.0,
         "false_alert_events_per_day": 9.0},
        {"rule": "2-of-3", "recall": 0.90, "median_detection_delay_min": 10.0,
         "false_alert_events_per_day": 0.8},
        {"rule": "3-of-5", "recall": 0.70, "median_detection_delay_min": 20.0,
         "false_alert_events_per_day": 0.4},
    ])
    chosen, reason = alert_study.select_rule(surface, budget=1.0)
    assert chosen == "2-of-3"          # 1-of-1 has the best recall but busts budget
    assert "calibration data only" in reason


def test_rule_selection_falls_back_and_says_so_when_no_rule_meets_budget():
    surface = pd.DataFrame([
        {"rule": "2-of-3", "recall": 0.9, "median_detection_delay_min": 10.0,
         "false_alert_events_per_day": 8.0},
        {"rule": "3-of-5", "recall": 0.8, "median_detection_delay_min": 20.0,
         "false_alert_events_per_day": 5.0},
    ])
    chosen, reason = alert_study.select_rule(surface, budget=1.0)
    assert chosen == "3-of-5"
    assert "no candidate met the budget" in reason


def test_rule_surface_labels_its_role_and_scores_every_candidate():
    n = 300
    clean = _clean(n)
    lower = clean - 0.5
    upper = clean + 0.5
    cat = _catalog([(50, 60)])
    rules = alert_study.parse_rules(["1-of-1", "2-of-3", "3-of-5"])
    surf = alert_study.rule_surface(
        clean, lower, upper, cat, rules, FREQ, 5,
        context={"dataset": "d"}, role="calibration_selection")
    assert len(surf) == 3
    assert set(surf["rule"]) == set(rules)
    assert (surf["role"] == "calibration_selection").all()
    for col in ("precision", "recall", "f1", "far",
                "false_alert_events_per_day", "mean_detection_delay_min",
                "median_detection_delay_min", "k", "m"):
        assert col in surf.columns


# --------------------------------------------------------------------------- #
# Nested calibration split: the rule must not be tuned on the conformal sample
# --------------------------------------------------------------------------- #
def _calib_times(n, h=3):
    """Windows at a fixed horizon: target = origin + h steps."""
    origin = pd.date_range("2021-09-01", periods=n, freq="10min")
    target = origin + h * FREQ
    return origin, target


def test_subsplit_puts_every_rule_timestamp_after_every_conformal_timestamp():
    """The whole point: rule tuning must see only post-conformal observations."""
    o, t = _calib_times(1000)
    s = alert_study.chronological_subsplit(o, t, 0.6, min_samples=10)
    conf, rule = s["conformal_mask"], s["rule_mask"]
    assert conf.any() and rule.any()
    assert not (conf & rule).any(), "a window landed in both blocks"

    # Strictly later on every timestamp that exists, origins included.
    assert o[rule].min() > t[conf].max()
    assert t[rule].min() > t[conf].max()
    assert s["rule_first_origin"] > s["conformal_last_target"]


def test_subsplit_embargoes_the_windows_that_straddle_the_boundary():
    """A window whose origin precedes the cut but whose target follows it
    overlaps both blocks and must be dropped, not assigned."""
    o, t = _calib_times(1000, h=3)
    s = alert_study.chronological_subsplit(o, t, 0.6, min_samples=10)
    assert s["n_embargoed"] > 0
    assert (s["n_conformal"] + s["n_rule"] + s["n_embargoed"]) == s["n_calibration"]
    straddling = s["embargoed_mask"]
    assert (o[straddling] <= s["boundary_time"]).all()
    assert (t[straddling] > s["boundary_time"]).all()


def test_subsplit_is_chronological_not_shuffled():
    o, t = _calib_times(500)
    s = alert_study.chronological_subsplit(o, t, 0.6, min_samples=10)
    conf = np.flatnonzero(s["conformal_mask"])
    rule = np.flatnonzero(s["rule_mask"])
    # Times are already sorted here, so a chronological cut is a contiguous
    # prefix and suffix; a shuffled split would interleave the positions.
    assert conf.max() < rule.min()
    assert np.array_equal(conf, np.arange(conf.min(), conf.max() + 1))


def test_subsplit_honours_the_requested_fraction():
    o, t = _calib_times(1000)
    for frac in (0.5, 0.6, 0.8):
        s = alert_study.chronological_subsplit(o, t, frac, min_samples=10)
        assert abs(s["realised_fraction"] - frac) < 0.02


def test_subsplit_reports_unusable_rather_than_selecting_from_a_handful():
    o, t = _calib_times(50)
    s = alert_study.chronological_subsplit(o, t, 0.6, min_samples=200)
    assert s["usable"] is False
    assert "below the minimum" in s["reason"]


def test_subsplit_rejects_degenerate_fractions_and_empty_input():
    o, t = _calib_times(100)
    for bad in (0.0, 1.0, -0.5, 1.5):
        with pytest.raises(ValueError):
            alert_study.chronological_subsplit(o, t, bad)
    empty = pd.DatetimeIndex([])
    with pytest.raises(ValueError):
        alert_study.chronological_subsplit(empty, empty, 0.6)


def test_subsplit_never_touches_test_observations():
    """The split is defined on calibration windows alone; no test timestamp can
    enter either block."""
    o, t = _calib_times(1000)
    test_start = t.max() + pd.Timedelta("1D")
    s = alert_study.chronological_subsplit(o, t, 0.6, min_samples=10)
    for mask in (s["conformal_mask"], s["rule_mask"]):
        assert (t[mask] < test_start).all()
        assert (o[mask] < test_start).all()
    assert s["rule_last_target"] < test_start


def test_subsplit_is_deterministic():
    o, t = _calib_times(777)
    a = alert_study.chronological_subsplit(o, t, 0.6, min_samples=10)
    b = alert_study.chronological_subsplit(o, t, 0.6, min_samples=10)
    assert np.array_equal(a["conformal_mask"], b["conformal_mask"])
    assert np.array_equal(a["rule_mask"], b["rule_mask"])
    assert a["boundary_time"] == b["boundary_time"]


def test_selected_rule_is_deterministic_under_a_fixed_seed():
    """Same intervals, same injected events, same seed -> same frozen rule."""
    n = 900
    clean = _clean(n)
    times = _times(n)
    rules = alert_study.parse_rules(["1-of-1", "2-of-3", "3-of-5", "4-of-7"])

    def choose():
        pert, cat = alert_study.inject_events(
            clean, 1.0, FREQ, times, {"instances_per_type": 2}, seed=7,
            dataset="d", target="t", partition="calibration_rule_block")
        surf = alert_study.rule_surface(
            pert, clean - 1.0, clean + 1.0, cat, rules, FREQ, 5,
            context={"dataset": "d"}, role="calibration_selection")
        return alert_study.select_rule(surf, 1.0)

    first, second = choose(), choose()
    assert first == second
