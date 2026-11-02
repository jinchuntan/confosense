"""Separate genuinely changed flags from boundary changes and chance matches."""
import unittest
import numpy as np
from replay import attribution


class RecoveryAttribution(unittest.TestCase):
    def test_first_onset_and_restoration(self):
        flags = np.zeros((5, 8), bool)
        cf = np.zeros_like(flags)
        flags[0, 5] = True   # first alarm after the four-sample slot
        flags[1, 5] = True
        cf[1, 4:6] = True   # restoration moves the onset but retains the flag
        flags[2, 2:4] = True  # during event
        flags[3, 0:7] = True  # ongoing previous episode, no new onset
        flags[4, 1] = True  # before the first actually changed sample
        r = attribution(flags, cf, np.ones(5, int), np.full(5, 3))
        np.testing.assert_array_equal(r["history_only"], [1,0,0,0,0])
        np.testing.assert_array_equal(r["post_existing_flag"], [0,1,0,0,0])
        np.testing.assert_array_equal(r["during_change_span"], [0,0,1,0,0])
        np.testing.assert_array_equal(r["before_first_change"], [0,0,0,0,1])
        np.testing.assert_array_equal(r["hits"], [1,1,1,0,1])


if __name__ == "__main__":
    unittest.main()
