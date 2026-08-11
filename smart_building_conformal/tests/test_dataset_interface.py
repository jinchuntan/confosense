"""The common prepared-data representation and its partitioners.

Small synthetic series only — no test downloads an external dataset.
"""

import numpy as np
import pandas as pd
import pytest

from src.datasets.base import (
    ChronologicalPartitioner,
    GroupPartitioner,
    PARTITIONS,
    PreparedDataset,
    PreparedSeries,
    Provenance,
    config_hash,
)


def make_series(n=200, group=None, start="2021-01-01", freq="10min", season=144):
    idx = pd.date_range(start, periods=n, freq=freq)
    frame = pd.DataFrame(
        {"target": np.linspace(20, 22, n), "tmed": np.zeros(n)}, index=idx)
    return PreparedSeries(
        dataset_id="synthetic", target_id="t", frame=frame,
        freq=pd.Timedelta(freq), group_id=group, season_steps=season,
        covariates=["tmed"], units="degC")


def test_series_requires_target_and_sorted_datetime_index():
    idx = pd.date_range("2021-01-01", periods=5, freq="10min")
    with pytest.raises(ValueError):
        PreparedSeries("d", "t", pd.DataFrame({"x": range(5)}, index=idx),
                       pd.Timedelta("10min"))
    with pytest.raises(TypeError):
        PreparedSeries("d", "t", pd.DataFrame({"target": range(5)}),
                       pd.Timedelta("10min"))
    unsorted = pd.DataFrame({"target": range(5)}, index=idx[::-1])
    with pytest.raises(ValueError):
        PreparedSeries("d", "t", unsorted, pd.Timedelta("10min"))


def test_seasonal_support_requires_a_full_cycle():
    assert make_series(n=200, season=144).seasonal_naive_supported
    assert not make_series(n=100, season=144).seasonal_naive_supported
    assert not make_series(n=100, season=None).seasonal_naive_supported


def test_dataset_rejects_mixed_sampling_intervals():
    a = make_series(freq="10min")
    b = make_series(freq="5min")
    with pytest.raises(ValueError):
        PreparedDataset("d", [a, b], ChronologicalPartitioner(),
                        Provenance("d", "src"))


def test_chronological_partitions_are_ordered_and_contiguous():
    s = make_series(n=1000)
    part = ChronologicalPartitioner(fractions=(0.6, 0.2, 0.2))
    labels = part.labels(s, s.frame.index)
    assert set(labels) == set(PARTITIONS)
    # Every train timestamp precedes every calibration one, and so on.
    for a, b in (("train", "calibration"), ("calibration", "test")):
        assert s.frame.index[labels == a].max() < s.frame.index[labels == b].min()
    # Fractions are respected to within one step.
    assert abs((labels == "train").mean() - 0.6) < 0.01


def test_group_partitioner_assigns_whole_groups_chronologically():
    series = [make_series(n=100, group=f"run{i}",
                          start=f"2021-01-{i+1:02d}") for i in range(10)]
    part = GroupPartitioner(fractions=(0.6, 0.2, 0.2)).fit(series)
    assignment = part.assignment
    assert len(assignment) == 10
    # A group maps to exactly one partition, and the ordering is chronological.
    order = {"train": 0, "calibration": 1, "test": 2}
    ranks = [order[assignment[f"run{i}"]] for i in range(10)]
    assert ranks == sorted(ranks)
    assert set(assignment.values()) == set(PARTITIONS)


def test_group_partitioner_refuses_unknown_group():
    series = [make_series(n=50, group="a"), make_series(n=50, group="b")]
    part = GroupPartitioner().fit(series)
    stranger = make_series(n=50, group="zzz")
    with pytest.raises(KeyError):
        part.labels(stranger, stranger.frame.index)


def test_split_summary_counts_every_row_once():
    series = [make_series(n=120, group=f"g{i}", start=f"2021-02-{i+1:02d}")
              for i in range(5)]
    ds = PreparedDataset("d", series, GroupPartitioner().fit(series),
                         Provenance("d", "src"))
    summary = ds.split_summary()
    assert summary[[f"n_{p}" for p in PARTITIONS]].to_numpy().sum() == 5 * 120


def test_config_hash_is_stable_and_order_insensitive():
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})
    assert config_hash({"a": 1}) != config_hash({"a": 2})
