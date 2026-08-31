"""Updated recentred EnbPI is causal and group-safe (audit item C1).

These exercise the online-interval core ``_updated_intervals_causal`` directly,
which is where the observation-delay and group-isolation guarantees live, so the
tests are fast and pin the exact properties the audit requires without training a
MAPIE ensemble.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.conformal_enbpi import _updated_intervals_causal


def _times(n, start="2020-01-01", freq="h"):
    return pd.date_range(start, periods=n, freq=freq)


def test_enbpi_no_early_residual():
    # A single group. The final test residual is enormous; because its target is
    # observed only at the very end, it must not widen any earlier interval.
    n = 10
    origins = _times(n)
    horizon = 1
    targets = origins + pd.Timedelta(hours=horizon)
    point = np.zeros(n)
    test_res = np.full(n, 0.1)
    test_res[-1] = 1000.0                      # a future shock
    calib_res = np.array([-0.1, 0.0, 0.1])
    calib_targets = _times(3, start="2019-12-31")
    out = _updated_intervals_causal(
        point_test=point, calib_residuals=calib_res,
        calib_groups=np.zeros(3, dtype=int), calib_target_times=calib_targets,
        test_residuals=test_res, test_groups=np.zeros(n, dtype=int),
        test_origin_times=origins, test_target_times=targets, horizon=horizon,
        confidence_levels=[0.9], window=None)
    up = out[0.9]["upper"]
    # No interval before the last origin may reflect the 1000.0 shock.
    assert up[:-1].max() < 10.0, "a future residual leaked into earlier intervals"


def test_enbpi_no_cross_group_update():
    # Two groups interleaved in time. Group B has a large positive residual bias;
    # group A's intervals must never absorb group B's residuals.
    n = 6
    origins = _times(n)
    horizon = 1
    targets = origins + pd.Timedelta(hours=horizon)
    groups = np.array(["A", "B", "A", "B", "A", "B"])
    test_res = np.where(groups == "B", 50.0, 0.1)
    point = np.zeros(n)
    calib_res = np.array([-0.1, 0.1])
    out = _updated_intervals_causal(
        point_test=point, calib_residuals=calib_res,
        calib_groups=np.array(["A", "B"]),
        calib_target_times=_times(2, start="2019-12-31"),
        test_residuals=test_res, test_groups=groups,
        test_origin_times=origins, test_target_times=targets, horizon=horizon,
        confidence_levels=[0.9], window=None)
    up = out[0.9]["upper"]
    a_rows = groups == "A"
    assert up[a_rows].max() < 10.0, "group B's residuals leaked into group A"


def test_future_residual_corruption_cannot_change_earlier_intervals():
    n = 8
    origins = _times(n)
    targets = origins + pd.Timedelta(hours=1)
    point = np.zeros(n)
    calib_res = np.array([-0.2, 0.0, 0.2])
    calib_targets = _times(3, start="2019-12-31")
    base = np.array([0.1, -0.1, 0.15, -0.05, 0.2, -0.2, 0.05, -0.15])
    kw = dict(point_test=point, calib_residuals=calib_res,
              calib_groups=np.zeros(3, dtype=int), calib_target_times=calib_targets,
              test_groups=np.zeros(n, dtype=int), test_origin_times=origins,
              test_target_times=targets, horizon=1, confidence_levels=[0.9],
              window=None)
    a = _updated_intervals_causal(test_residuals=base.copy(), **kw)[0.9]["upper"]
    corrupted = base.copy()
    corrupted[-1] = 999.0                       # corrupt only the last outcome
    b = _updated_intervals_causal(test_residuals=corrupted, **kw)[0.9]["upper"]
    assert np.allclose(a[:-1], b[:-1]), "changing a future outcome altered the past"


def test_grouped_results_invariant_to_group_processing_order():
    n = 6
    origins = _times(n)
    targets = origins + pd.Timedelta(hours=1)
    g1 = np.array(["A", "B", "A", "B", "A", "B"])
    # Same data, groups relabelled so the unique() iteration order differs.
    res = np.array([0.1, 0.3, 0.2, 0.4, 0.15, 0.35])
    point = np.zeros(n)
    kw = dict(point_test=point, calib_residuals=np.array([0.0, 0.1]),
              calib_target_times=_times(2, start="2019-12-31"),
              test_residuals=res, test_origin_times=origins,
              test_target_times=targets, horizon=1, confidence_levels=[0.9],
              window=None)
    out1 = _updated_intervals_causal(
        test_groups=g1, calib_groups=np.array(["A", "B"]), **kw)[0.9]["upper"]
    # Reverse the physical order in which groups first appear.
    g2 = np.array(["B", "A", "B", "A", "B", "A"])
    res2 = np.array([0.3, 0.1, 0.4, 0.2, 0.35, 0.15])
    kw2 = dict(kw)
    out2 = _updated_intervals_causal(
        test_groups=g2, calib_groups=np.array(["A", "B"]),
        **{**kw2, "test_residuals": res2})[0.9]["upper"]
    # Group A rows in run 1 correspond to positions where g1==A; in run 2 g2==A.
    assert np.allclose(np.sort(out1), np.sort(out2)), \
        "per-group intervals depended on the order groups were processed"
