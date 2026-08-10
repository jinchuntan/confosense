import numpy as np
import pandas as pd

from src import alerts


def test_point_violations():
    obs = np.array([0.0, 5.0, -5.0, 1.0])
    lo = np.array([-1.0, -1.0, -1.0, -1.0])
    up = np.array([1.0, 1.0, 1.0, 1.0])
    v = alerts.point_violations(obs, lo, up)
    assert list(v) == [False, True, True, False]


def test_apply_rule_k_of_m():
    v = np.array([0, 1, 1, 0, 1, 0, 0], dtype=bool)
    # 1-of-1 mirrors the violations exactly
    assert list(alerts.apply_rule(v, 1, 1)) == list(v)
    # 2-of-3: fires where >=2 of the trailing 3 are violations
    got = alerts.apply_rule(v, 2, 3)
    assert list(got) == [False, False, True, True, True, False, False]


def test_inject_events_are_reproducible_and_non_overlapping():
    n = 2000
    clean = np.zeros(n)
    times = pd.date_range("2023-01-01", periods=n, freq="10min")
    cfg = {"instances_per_type": 2, "level_shift_steps": 12, "drift_steps": 24,
           "stuck_steps": 12, "warmup_steps": 6, "guard_steps": 6}
    p1, cat1 = alerts.inject_events(clean, 1.0, pd.Timedelta("10min"), times, cfg, seed=42, dataset_label="test")
    p2, cat2 = alerts.inject_events(clean, 1.0, pd.Timedelta("10min"), times, cfg, seed=42, dataset_label="test")
    assert np.allclose(p1, p2)
    assert cat1.equals(cat2)
    # no two events overlap
    spans = sorted(zip(cat1["start_index"], cat1["end_index"]))
    for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
        assert e1 < s2


def test_evaluate_alerts_detects_injected_event():
    n = 500
    times = pd.date_range("2023-01-01", periods=n, freq="10min")
    catalog = pd.DataFrame([{
        "start_index": 100, "end_index": 110, "start_time": times[100],
        "end_time": times[110], "event_type": "level_shift", "severity": "1.0sd",
    }])
    alerts_flags = np.zeros(n, dtype=bool)
    alerts_flags[103] = True  # a single alert inside the event window
    res = alerts.evaluate_alerts(alerts_flags, catalog, n, pd.Timedelta("10min"), tolerance=6)
    assert res["true_positives"] == 1
    assert res["false_negatives"] == 0
    assert res["recall"] == 1.0
    # detection delay is (103 - 100) steps * 10 min = 30 min
    assert res["mean_detection_delay_min"] == 30.0


def test_select_rule_returns_valid_rule():
    rng = np.random.default_rng(0)
    n = 3000
    obs = rng.normal(size=n)
    lo = np.full(n, -2.0)
    up = np.full(n, 2.0)
    times = pd.date_range("2023-01-01", periods=n, freq="10min")
    cfg = {
        "events": {"instances_per_type": 2, "level_shift_steps": 12, "drift_steps": 24,
                   "stuck_steps": 12, "warmup_steps": 6, "guard_steps": 6},
        "detection_tolerance_steps": 6,
        "max_false_alerts_per_day": 5.0,
    }
    rule, table = alerts.select_rule(obs, lo, up, 1.0, pd.Timedelta("10min"), times, cfg, seed=42)
    assert rule in alerts.RULES
    assert set(table["rule"]) == set(alerts.RULES)
