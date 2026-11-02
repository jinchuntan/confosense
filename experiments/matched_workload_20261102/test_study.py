"""Scientific safeguards, using small constructed streams only."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("matched_workload", Path(__file__).with_name("study.py"))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class Safeguards(unittest.TestCase):
    def test_no_future_measurement_enters_features(self):
        idx = pd.date_range("2020-01-01", periods=400, freq="h")
        f = pd.DataFrame({"y": np.arange(400.), "airTemperature": 20.,
                          "dewTemperature": 10.}, index=idx)
        before = s.features(f)
        changed = f.copy()
        changed.loc[idx[240]:, "y"] = -9999
        pd.testing.assert_frame_equal(before.iloc[:241], s.features(changed).iloc[:241])

    def test_splits_have_target_to_origin_embargo(self):
        m = pd.DataFrame(dict(time=pd.date_range("2020", periods=1000, freq="h")))
        roles = s.partition(m, .6)
        for a, b in zip(roles, list(roles)[1:]):
            self.assertLess(m.loc[roles[a], "time"].max(), m.loc[roles[b], "time"].min() - s.HOUR)

    def test_episode_count_breaks_at_gaps_and_assets(self):
        m = pd.DataFrame(dict(building=["a", "a", "a", "b"],
            time=pd.to_datetime(["2020-01-01 00:00", "2020-01-01 01:00",
                                 "2020-01-01 03:00", "2020-01-01 03:00"])))
        np.testing.assert_array_equal(s.starts(m, [1, 1, 1, 1]), [1, 0, 1, 1])

    def test_conformal_equals_raw_score_cutoff_including_empty_sets(self):
        rng = np.random.default_rng(9)
        p = rng.normal(size=(200, 3))
        p[:, 0], p[:, 2] = np.minimum(p[:, 0], p[:, 2]), np.maximum(p[:, 0], p[:, 2])
        y = rng.normal(size=200)
        y[4] = np.nan
        for threshold in [-2., -.1, 0., .7, 3.]:
            flags = s.numerical_flags(y, s.candidate_bounds(p,
                dict(method="symmetric_cqr", threshold=threshold), np.ones(200)))
            raw = np.maximum(p[:, 0] - y, y - p[:, 2])
            np.testing.assert_array_equal(flags, np.isfinite(y) & (raw > threshold))

    def test_selection_rejects_continuous_alarm_gaming(self):
        m = pd.DataFrame(dict(building="a", time=pd.date_range("2020", periods=500, freq="h")))
        pred = np.tile([0., .5, 1.], (500, 1))
        y = np.full(500, 2.)
        chosen, _ = s.choose(m, y, pred, np.ones(500),
            [dict(method="scaled_quantile", threshold=.1)], 1.)
        self.assertIsNone(chosen)  # One long episode is not a quiet stream.

    def test_existing_episode_does_not_detect_new_event(self):
        m = pd.DataFrame(dict(building="a", time=pd.date_range("2020", periods=10, freq="h")))
        events = pd.DataFrame([dict(building="a", start=2, tolerance_end=8,
                                   onset=str(m.iloc[2].time), effective=True)])
        out = s.score_events(m, np.ones(10, bool), events, "combined")
        self.assertFalse(out.iloc[0].detected)
        self.assertEqual(out.iloc[0].restricted_delay_minutes, 360.)

    def test_chance_match_is_scored_on_original_stream(self):
        m = pd.DataFrame(dict(building="a", time=pd.date_range("2020", periods=10, freq="h")))
        events = pd.DataFrame([dict(building="a", start=2, tolerance_end=8,
                                   onset=str(m.iloc[2].time), effective=True)])
        flags = np.zeros(10, bool)
        flags[4] = True
        out = s.score_events(m, flags, events, "clean_window")
        self.assertTrue(out.iloc[0].detected)
        self.assertEqual(out.iloc[0].restricted_delay_minutes, 120.)

    def test_no_event_or_followup_crosses_missing_support_gap(self):
        idx = pd.date_range("2020", periods=500, freq="h").delete(range(200, 210))
        m = pd.DataFrame(dict(building="a", time=idx))
        y = np.arange(len(m), dtype=float)
        observed, events = s.inject(m, y, {"a": 10.}, 0, 42)
        for e in events.to_dict("records"):
            self.assertEqual(m.iloc[e["tolerance_end"]].time - m.iloc[e["start"] - 1].time, 7 * s.HOUR)
        observed2, events2 = s.inject(m, y, {"a": 10.}, 0, 42)
        np.testing.assert_array_equal(observed, observed2)
        pd.testing.assert_frame_equal(events, events2)


if __name__ == "__main__":
    unittest.main()
