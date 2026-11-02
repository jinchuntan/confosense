import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from compare import delayed_features, first_state, load_runner
from controls import repeated


class FeedbackTests(unittest.TestCase):
    def test_first_state_uses_earliest_onset_and_actual_change_span(self):
        flags = np.array([[0,0,0,0,0,0,0,0], [0,1,0,0,0,1,0,0],
                          [0,0,1,1,0,0,0,0], [0,0,0,0,1,1,0,0]], dtype=bool)
        ix = np.arange(flags.size).reshape(flags.shape)
        changed = np.tile([False,True,True,False],(4,1))
        np.testing.assert_array_equal(first_state(flags.ravel(),ix,changed),[0,1,2,3])

    def test_missing_breaks_repeated_value_run(self):
        np.testing.assert_array_equal(repeated([2,2,2,np.nan,np.nan,2,2]),[0,1,2,0,0,0,1])

    def test_delayed_meter_features_exclude_last_four_values(self):
        study = load_runner(Path(__file__).resolve().parents[1] / "matched_workload_20261102")
        timestamps = pd.date_range("2020-01-01", periods=240, freq="h")
        frame = pd.DataFrame(dict(y=np.arange(240.),airTemperature=18.,dewTemperature=12.),index=timestamps)
        baseline = delayed_features(study,frame)
        corrupt = frame.y.copy()
        corrupt.iloc[-5:-1] += 100
        altered = delayed_features(study,frame,corrupt.to_numpy())
        pd.testing.assert_series_equal(baseline.iloc[-1],altered.iloc[-1])
        self.assertEqual(baseline.iloc[-1]["lag_0"],frame.y.iloc[-6])
        self.assertEqual(baseline.iloc[-1]["season_24"],frame.y.iloc[-25])
