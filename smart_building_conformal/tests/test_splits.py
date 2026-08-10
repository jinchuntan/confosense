import numpy as np
import pandas as pd

from src import prepare_data as P


def _grid(n):
    return pd.date_range("2021-01-01", periods=n, freq="10min")


def test_boundaries_are_contiguous_and_ordered():
    idx = _grid(1000)
    t_train_end, t_calib_end = P.chronological_split_boundaries(idx, 0.6, 0.2)
    assert t_train_end < t_calib_end
    labels = P.assign_split(idx, t_train_end, t_calib_end)
    assert (labels == "train").sum() == 600
    assert (labels == "calibration").sum() == 200
    assert (labels == "test").sum() == 200


def test_split_regions_do_not_overlap_in_time():
    idx = _grid(1000)
    bnd = P.chronological_split_boundaries(idx, 0.6, 0.2)
    labels = P.assign_split(idx, *bnd)
    train_max = idx[labels == "train"].max()
    calib_min = idx[labels == "calibration"].min()
    calib_max = idx[labels == "calibration"].max()
    test_min = idx[labels == "test"].min()
    assert train_max < calib_min
    assert calib_max < test_min


def test_split_summary_enforces_chronology():
    idx = _grid(500)
    processed = pd.DataFrame({"target": np.arange(500.0)}, index=idx)
    bnd = P.chronological_split_boundaries(idx, 0.6, 0.2)
    summary = P.split_summary(processed, bnd, {"split": {}})
    assert list(summary["split"]) == ["train", "calibration", "test"]
    assert summary.loc[0, "end"] < summary.loc[1, "start"]
    assert summary.loc[1, "end"] < summary.loc[2, "start"]
