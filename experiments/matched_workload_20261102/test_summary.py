"""Checks of independent reconstruction from emitted episode onsets."""
import unittest
import numpy as np
import pandas as pd
from summarize import reconstruct_matches


class Reconstruction(unittest.TestCase):
    def setUp(self):
        self.meta = pd.DataFrame(dict(building=['a'] * 12,
            time=pd.date_range('2020', periods=12, freq='h')))

    def test_first_onset_and_restricted_miss(self):
        events = pd.DataFrame(dict(building=['a', 'a'], start=[2, 8],
            tolerance_end=[5, 10], onset=[self.meta.time[2], self.meta.time[8]]))
        onsets = np.zeros(12, bool)
        onsets[[1, 4, 5, 11]] = True
        hits, delays = reconstruct_matches(self.meta, onsets, events)
        np.testing.assert_array_equal(hits, [True, False])
        np.testing.assert_array_equal(delays, [120., 360.])

    def test_empty_alarm_stream(self):
        events = pd.DataFrame(dict(building=['a'], start=[2],
            tolerance_end=[5], onset=[self.meta.time[2]]))
        hits, delays = reconstruct_matches(self.meta, np.zeros(12, bool), events)
        np.testing.assert_array_equal(hits, [False])
        np.testing.assert_array_equal(delays, [360.])

    def test_reused_onset_is_rejected(self):
        events = pd.DataFrame(dict(building=['a', 'a'], start=[2, 3],
            tolerance_end=[5, 5], onset=[self.meta.time[2], self.meta.time[3]]))
        onsets = np.zeros(12, bool)
        onsets[4] = True
        with self.assertRaisesRegex(AssertionError, 'reused event onset'):
            reconstruct_matches(self.meta, onsets, events)


if __name__ == '__main__':
    unittest.main()
