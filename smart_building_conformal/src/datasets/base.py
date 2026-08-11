"""Common prepared-data representation shared by every ConfoSense dataset.

The preliminary experiment was written around a single PLEIAData frame. The full
study has to run the same forecasting / conformal / alert / robustness code over
three sources with different structure:

* **PLEIAData** — one long, regularly sampled indoor-temperature series.
* **RICO** — 305 independent four-hour experimental *runs*; a run must never be
  split across partitions, and no feature window may cross a run boundary.
* **BDG2** — many independent *buildings*, each with its own chronological
  train / calibration / test periods.

Rather than scatter ``if dataset == ...`` branches through the driver, every
adapter lowers its source into a list of :class:`PreparedSeries`. A series is one
contiguous, regularly sampled block of observations belonging to exactly one
group (a RICO run, a BDG2 building, or the single implicit group of PLEIAData).

Two invariants follow *by construction* from that representation, which is the
whole point of it:

1. Supervised windows are built one series at a time and concatenated
   afterwards, so a lag/rolling window can never reach across a group boundary.
2. Partition assignment is resolved per series, so a group-partitioned dataset
   (RICO) can hand back whole runs while a chronologically partitioned one
   (PLEIAData, BDG2) can hand back time boundaries — without the caller caring
   which happened.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
import pandas as pd

PARTITIONS = ("train", "calibration", "test")


# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #
@dataclass
class Provenance:
    """Everything needed to say where a dataset came from and what we did to it.

    ``checksum`` is of the downloaded archive, not of the derived frames, so it
    identifies the upstream artefact rather than our preprocessing.
    """

    dataset_id: str
    official_source: str
    doi: str = ""
    download_url: str = ""
    retrieved_at: str = ""
    archive_name: str = ""
    checksum: str = ""
    checksum_algorithm: str = "sha256"
    license: str = ""
    citation: str = ""
    preprocessing: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def file_checksum(path: Path, algorithm: str = "sha256", chunk: int = 1 << 20) -> str:
    """Streaming checksum so multi-GB archives do not have to be held in memory."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def config_hash(cfg: dict) -> str:
    """Stable hash of a configuration mapping, used to detect resume mismatches."""
    payload = json.dumps(cfg, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# --------------------------------------------------------------------------- #
# Prepared series
# --------------------------------------------------------------------------- #
@dataclass
class PreparedSeries:
    """One contiguous, regularly sampled block of observations.

    ``frame`` carries a ``target`` column plus any covariate and ``*_was_missing``
    columns, indexed by a monotonically increasing DatetimeIndex on a fixed grid.

    ``season_steps`` is ``None`` when the series is too short (or too irregular)
    for a meaningful seasonal cycle — RICO's four-hour runs, for instance. The
    seasonal-naive baseline is then reported as *not applicable* rather than
    faked with a cross-run lag.
    """

    dataset_id: str
    target_id: str
    frame: pd.DataFrame
    freq: pd.Timedelta
    group_id: str | None = None
    season_steps: int | None = None
    covariates: list[str] = field(default_factory=list)
    units: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if "target" not in self.frame.columns:
            raise ValueError(f"{self.label}: frame must contain a 'target' column")
        if not isinstance(self.frame.index, pd.DatetimeIndex):
            raise TypeError(f"{self.label}: frame must be indexed by DatetimeIndex")
        if not self.frame.index.is_monotonic_increasing:
            raise ValueError(f"{self.label}: frame index must be sorted ascending")

    @property
    def label(self) -> str:
        return f"{self.dataset_id}:{self.group_id or '-'}:{self.target_id}"

    @property
    def n(self) -> int:
        return len(self.frame)

    @property
    def start(self) -> pd.Timestamp:
        return self.frame.index[0]

    @property
    def end(self) -> pd.Timestamp:
        return self.frame.index[-1]

    @property
    def seasonal_naive_supported(self) -> bool:
        """A seasonal lag is only usable if a full cycle fits inside the series."""
        return self.season_steps is not None and self.n > self.season_steps

    def target_std(self, upto: pd.Timestamp | None = None) -> float:
        """Target standard deviation, optionally restricted to before ``upto``.

        Perturbation magnitudes are expressed in units of this, so it must be
        computed on training data only — never on the held-out period it is
        later used to perturb.
        """
        s = self.frame["target"]
        if upto is not None:
            s = s.loc[s.index < upto]
        return float(s.std())


# --------------------------------------------------------------------------- #
# Partitioning
# --------------------------------------------------------------------------- #
@dataclass
class Partitioner(ABC):
    """Assigns every forecast origin to train / calibration / test."""

    fractions: tuple[float, float, float] = (0.6, 0.2, 0.2)

    @abstractmethod
    def labels(self, series: PreparedSeries, origins: pd.DatetimeIndex) -> np.ndarray:
        """Partition label for each origin time of ``series``."""

    @abstractmethod
    def describe(self) -> dict:
        """Serialisable description for the split-summary audit file."""


@dataclass
class ChronologicalPartitioner(Partitioner):
    """Split one series in time: train < calibration < test.

    Boundaries are derived per series from its own index, so a multi-building
    dataset gets a chronological split *inside* each building.
    """

    _boundaries: dict = field(default_factory=dict, repr=False)

    def boundaries(self, series: PreparedSeries) -> tuple[pd.Timestamp, pd.Timestamp]:
        if series.label not in self._boundaries:
            idx = series.frame.index
            f_train, f_calib, _ = self.fractions
            i1 = int(len(idx) * f_train)
            i2 = int(len(idx) * (f_train + f_calib))
            self._boundaries[series.label] = (idx[i1], idx[i2])
        return self._boundaries[series.label]

    def labels(self, series: PreparedSeries, origins: pd.DatetimeIndex) -> np.ndarray:
        b1, b2 = self.boundaries(series)
        out = np.full(len(origins), "test", dtype=object)
        out[origins < b2] = "calibration"
        out[origins < b1] = "train"
        return out

    def describe(self) -> dict:
        return {"strategy": "chronological", "fractions": list(self.fractions),
                "boundaries": {k: [str(v[0]), str(v[1])]
                               for k, v in self._boundaries.items()}}


@dataclass
class GroupPartitioner(Partitioner):
    """Assign whole groups to a partition — used for RICO experimental runs.

    Groups are ordered chronologically by their start time and then cut at the
    configured fractions, so the split stays chronological at run granularity
    while guaranteeing that no run contributes rows to two partitions.
    """

    assignment: dict[str, str] = field(default_factory=dict)

    def fit(self, series_list: list[PreparedSeries]) -> "GroupPartitioner":
        ordered = sorted(
            {s.group_id: s.start for s in series_list}.items(),
            key=lambda kv: (kv[1], str(kv[0])),
        )
        n = len(ordered)
        f_train, f_calib, _ = self.fractions
        i1, i2 = int(n * f_train), int(n * (f_train + f_calib))
        for rank, (gid, _) in enumerate(ordered):
            part = "train" if rank < i1 else ("calibration" if rank < i2 else "test")
            self.assignment[str(gid)] = part
        return self

    def labels(self, series: PreparedSeries, origins: pd.DatetimeIndex) -> np.ndarray:
        part = self.assignment.get(str(series.group_id))
        if part is None:
            raise KeyError(
                f"group {series.group_id!r} has no partition; call fit() with the "
                "complete series list before requesting labels"
            )
        return np.full(len(origins), part, dtype=object)

    def describe(self) -> dict:
        counts = {p: sum(1 for v in self.assignment.values() if v == p)
                  for p in PARTITIONS}
        return {"strategy": "group", "fractions": list(self.fractions),
                "n_groups": len(self.assignment), "groups_per_partition": counts,
                "assignment": dict(self.assignment)}


# --------------------------------------------------------------------------- #
# Prepared dataset
# --------------------------------------------------------------------------- #
@dataclass
class PreparedDataset:
    """A dataset lowered into the common representation."""

    dataset_id: str
    series: list[PreparedSeries]
    partitioner: Partitioner
    provenance: Provenance
    target_description: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.series:
            raise ValueError(f"{self.dataset_id}: no series were prepared")
        freqs = {s.freq for s in self.series}
        if len(freqs) > 1:
            raise ValueError(f"{self.dataset_id}: mixed sampling intervals {freqs}")

    @property
    def freq(self) -> pd.Timedelta:
        return self.series[0].freq

    @property
    def is_grouped(self) -> bool:
        return any(s.group_id is not None for s in self.series)

    @property
    def seasonal_naive_supported(self) -> bool:
        """Only claim seasonal-naive support if *every* series can carry it."""
        return all(s.seasonal_naive_supported for s in self.series)

    def group_ids(self) -> list[str]:
        return [str(s.group_id) for s in self.series if s.group_id is not None]

    def split_summary(self) -> pd.DataFrame:
        rows = []
        for s in self.series:
            labels = self.partitioner.labels(s, s.frame.index)
            row = {"dataset": self.dataset_id, "group_id": s.group_id,
                   "target_id": s.target_id, "n_rows": s.n,
                   "start": s.start, "end": s.end,
                   "freq": str(s.freq), "season_steps": s.season_steps,
                   "seasonal_naive_supported": s.seasonal_naive_supported}
            for p in PARTITIONS:
                row[f"n_{p}"] = int(np.sum(labels == p))
            rows.append(row)
        return pd.DataFrame(rows)

    def horizon_minutes(self, horizon_steps: int) -> float:
        return horizon_steps * self.freq / pd.Timedelta(minutes=1)


class DatasetAdapter(ABC):
    """Turns a raw source into a :class:`PreparedDataset`."""

    dataset_id: str = ""

    @abstractmethod
    def provenance(self) -> Provenance:
        """Describe the upstream source. Must not require the data to be present."""

    @abstractmethod
    def prepare(self, cfg: dict) -> PreparedDataset:
        """Download if needed, clean, and lower into the common representation."""

    def profile(self, prepared: PreparedDataset) -> pd.DataFrame:
        """Per-series audit rows written to ``data_profiles/``."""
        rows = []
        for s in prepared.series:
            target = s.frame["target"]
            rows.append({
                "dataset": s.dataset_id, "group_id": s.group_id,
                "target_id": s.target_id, "units": s.units,
                "n_rows": s.n, "start": s.start, "end": s.end,
                "freq": str(s.freq),
                "missing_fraction": float(target.isna().mean()),
                "mean": float(target.mean()), "std": float(target.std()),
                "min": float(target.min()), "max": float(target.max()),
                "season_steps": s.season_steps,
                "seasonal_naive_supported": s.seasonal_naive_supported,
            })
        return pd.DataFrame(rows)
