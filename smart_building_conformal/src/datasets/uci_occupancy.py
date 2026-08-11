"""UCI Occupancy Detection adapter — auxiliary pipeline-portability check only.

This dataset is **not** a fifth primary benchmark. It exists to answer one
question: can the generic ConfoSense pipeline ingest an independent public
building-sensor dataset and run data loading, partitioning, feature generation,
point forecasting, conformal calibration and reporting with only a small
dataset-specific adapter? Its results are auxiliary evidence about the software,
not dissertation evidence about forecasting.

Reference
---------
Candanedo, L. M. and Feldheim, V. (2016). "Accurate occupancy detection of an
office room from light, temperature, humidity and CO2 measurements using
statistical learning models." *Energy and Buildings*, 112, 28-39.

Source
------
UCI Machine Learning Repository dataset 357, DOI 10.24432/C5X01N, CC BY 4.0.
Archive ``occupancy+detection.zip`` from the official ``archive.ics.uci.edu``
static endpoint; no mirror is used.

What the archive actually contains (verified, not assumed)
----------------------------------------------------------
Three text files totalling 20,560 rows, each a gap-free one-minute series with
no missing values and no duplicate timestamps. Recorded timestamps carry about
one second of jitter (interval counts split between 59 s, 60 s and 61 s), so the
index is rounded to the minute; after rounding each file spans exactly
``n_rows - 1`` minutes, confirming there is no internal gap to interpolate.

The three files are **disjoint in time and not contiguous**, and — this matters —
their chronological order is not the order their names suggest:

===================  ===================  ===================  =============
file                 start                end                  gap to next
===================  ===================  ===================  =============
datatest.txt         2015-02-02 14:19     2015-02-04 10:43     7 h 08 min
datatraining.txt     2015-02-04 17:51     2015-02-10 09:33     1 d 05 h 15 min
datatest2.txt        2015-02-11 14:48     2015-02-18 09:19     -
===================  ===================  ===================  =============

The file named ``datatraining`` is the *middle* segment. Concatenating the three
into one index would manufacture continuity across a seven-hour and a
twenty-nine-hour gap, so each file becomes its own
:class:`~src.datasets.base.PreparedSeries`: feature windows are built per series
and therefore cannot reach across a gap.

Partitioning
------------
Because the segments are disjoint *and* already ordered in time, a cut on the
pooled timeline yields partitions that are strictly ordered in wall-clock time
with no interleaving — which the per-series
:class:`~src.datasets.base.ChronologicalPartitioner` would not give here (it
would put segment 1's test period before segment 2's training period). The small
:class:`PooledChronologicalPartitioner` below therefore cuts once, globally.

It is deliberately defined in this module rather than in ``datasets/base.py``:
the four frozen primary experiments must not have their core partitioning code
touched by an auxiliary check. If it proves generally useful it can be promoted
later.

Seasonality
-----------
``season_steps`` is ``None``. The shortest segment is about 1.85 days, so a
1,440-step daily lag would consume the majority of it, and the seasonal-naive
baseline is not part of this auxiliary check in any case. The seasonal features
are therefore omitted rather than fabricated.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import register
from .base import (
    DatasetAdapter,
    Partitioner,
    PreparedDataset,
    PreparedSeries,
    Provenance,
    file_checksum,
)

DOWNLOAD_URL = "https://archive.ics.uci.edu/static/public/357/occupancy+detection.zip"
ARCHIVE_NAME = "occupancy+detection.zip"
MEMBERS = ("datatest.txt", "datatraining.txt", "datatest2.txt")
TARGET_COLUMN = "Temperature"
COVARIATE_COLUMNS = ("Humidity", "Light", "CO2", "HumidityRatio")


def download(raw_dir: Path) -> Path:
    """Fetch the official archive into ``raw_dir`` and extract it. Idempotent."""
    import requests

    raw_dir.mkdir(parents=True, exist_ok=True)
    archive = raw_dir / ARCHIVE_NAME
    if not archive.exists():
        with requests.get(DOWNLOAD_URL, stream=True, timeout=600) as resp:
            resp.raise_for_status()
            with open(archive, "wb") as f:
                for chunk in resp.iter_content(1 << 20):
                    f.write(chunk)
    if not all((raw_dir / m).exists() for m in MEMBERS):
        with zipfile.ZipFile(archive) as z:
            z.extractall(raw_dir)
    return archive


# --------------------------------------------------------------------------- #
@dataclass
class PooledChronologicalPartitioner(Partitioner):
    """One chronological cut across every series, not one cut per series.

    ``ChronologicalPartitioner`` splits each series independently, which is right
    for a multi-building panel where every building spans the same calendar
    period. Here the series are consecutive recording segments, so an independent
    per-series split would interleave the partitions in wall-clock time: the
    first segment's test rows would precede the second segment's training rows,
    and a model would be fitted on observations recorded *after* forecasts it is
    scored on. Cutting the pooled timeline once removes that entirely.

    Boundaries are supplied by the adapter, which computes them from the pooled,
    time-ordered row sequence.
    """

    boundary_train_end: pd.Timestamp = field(default=None)
    boundary_calib_end: pd.Timestamp = field(default=None)

    def labels(self, series: PreparedSeries, origins: pd.DatetimeIndex) -> np.ndarray:
        if self.boundary_train_end is None or self.boundary_calib_end is None:
            raise ValueError("pooled boundaries were never set by the adapter")
        out = np.full(len(origins), "test", dtype=object)
        out[origins < self.boundary_calib_end] = "calibration"
        out[origins < self.boundary_train_end] = "train"
        return out

    def describe(self) -> dict:
        return {
            "strategy": "pooled_chronological",
            "fractions": list(self.fractions),
            "boundary_train_end": str(self.boundary_train_end),
            "boundary_calib_end": str(self.boundary_calib_end),
            "rationale": (
                "segments are disjoint and already ordered in time, so a single "
                "cut on the pooled timeline keeps train < calibration < test in "
                "wall-clock order with no interleaving between segments"
            ),
        }


# --------------------------------------------------------------------------- #
def read_segment(path: Path) -> pd.DataFrame:
    """Read one archive member onto a verified regular one-minute index.

    Raises if the file is not gap-free after rounding, rather than silently
    interpolating: a hidden gap would let a feature window span a recording
    break, which is the one thing the segmentation exists to prevent.
    """
    raw = pd.read_csv(path)
    if "date" not in raw.columns:
        raise ValueError(f"{path.name}: no 'date' column; not a UCI occupancy file")
    idx = pd.to_datetime(raw["date"]).dt.round("1min")
    frame = raw.drop(columns=["date"]).copy()
    frame.index = pd.DatetimeIndex(idx, name="timestamp")
    frame = frame[~frame.index.duplicated(keep="first")].sort_index()

    expected = pd.date_range(frame.index[0], frame.index[-1], freq="1min")
    if len(frame) != len(expected) or not frame.index.equals(expected):
        missing = len(expected) - len(frame)
        raise ValueError(
            f"{path.name}: index is not a gap-free one-minute grid after rounding "
            f"({len(frame)} rows against {len(expected)} expected, {missing} absent)"
        )
    return frame


@register
class UciOccupancyAdapter(DatasetAdapter):
    """Auxiliary adapter. Small by design: everything generic is reused."""

    dataset_id = "uci_occupancy"

    def provenance(self) -> Provenance:
        return Provenance(
            dataset_id=self.dataset_id,
            official_source="UCI Machine Learning Repository, dataset 357",
            doi="10.24432/C5X01N",
            download_url=DOWNLOAD_URL,
            archive_name=ARCHIVE_NAME,
            license="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            citation=(
                "Candanedo, L. M. and Feldheim, V. (2016). Accurate occupancy "
                "detection of an office room from light, temperature, humidity "
                "and CO2 measurements using statistical learning models. Energy "
                "and Buildings, 112, 28-39. Dataset: Candanedo, L. (2016). "
                "Occupancy Detection [Dataset]. UCI Machine Learning Repository. "
                "https://doi.org/10.24432/C5X01N"
            ),
            preprocessing=[
                "timestamps rounded to the minute (source carries ~1 s jitter)",
                "each archive member kept as a separate segment; no concatenation "
                "across the 7 h 08 min and 1 d 05 h 15 min recording gaps",
                "target is Temperature (degC); Occupancy is not used",
                "no resampling, interpolation or outlier removal was required: "
                "every segment is gap-free and complete after rounding",
            ],
            notes=[
                "auxiliary pipeline-portability check, not a primary benchmark",
                "chronological order of the members is datatest, datatraining, "
                "datatest2 — the file named 'datatraining' is the middle segment",
            ],
        )

    # ------------------------------------------------------------------ #
    def prepare(self, cfg: dict) -> PreparedDataset:
        ucfg = cfg.get("uci_occupancy", {})
        raw_dir = Path(cfg["paths"]["raw_dir"]) / ucfg.get("subdir", "uci_occupancy")
        archive = raw_dir / ARCHIVE_NAME
        if ucfg.get("auto_download", True):
            archive = download(raw_dir)

        target_col = ucfg.get("target_column", TARGET_COLUMN)
        covariates = list(ucfg.get("covariates", COVARIATE_COLUMNS))

        segments: list[tuple[str, pd.DataFrame]] = []
        for member in MEMBERS:
            path = raw_dir / member
            if not path.exists():
                raise FileNotFoundError(
                    f"{path} is absent; run with uci_occupancy.auto_download or "
                    f"fetch {DOWNLOAD_URL} manually"
                )
            frame = read_segment(path)
            if target_col not in frame.columns:
                raise ValueError(f"{member}: no {target_col!r} column")
            keep = frame[[target_col, *[c for c in covariates if c in frame.columns]]]
            keep = keep.rename(columns={target_col: "target"})
            segments.append((Path(member).stem, keep))

        # Order the segments by their own start time rather than by filename.
        segments.sort(key=lambda kv: kv[1].index[0])

        freq = pd.Timedelta(ucfg.get("freq", "1min"))
        series = [
            PreparedSeries(
                dataset_id=self.dataset_id,
                target_id=f"{name}:{target_col}",
                frame=frame,
                freq=freq,
                group_id=name,
                season_steps=None,       # see the module docstring
                covariates=[c for c in covariates if c in frame.columns],
                units="degC",
                metadata={"source_file": f"{name}.txt", "n_rows": len(frame)},
            )
            for name, frame in segments
        ]

        partitioner = self._fit_partitioner(series, cfg)

        prov = self.provenance()
        if archive.exists():
            prov.checksum = file_checksum(archive)
        prov.retrieved_at = pd.Timestamp.utcnow().isoformat()

        gaps = [
            {
                "from_segment": segments[i][0],
                "to_segment": segments[i + 1][0],
                "gap": str(segments[i + 1][1].index[0] - segments[i][1].index[-1]),
            }
            for i in range(len(segments) - 1)
        ]

        return PreparedDataset(
            dataset_id=self.dataset_id,
            series=series,
            partitioner=partitioner,
            provenance=prov,
            target_description=(
                f"{target_col} (degC), the documented indoor air temperature "
                "channel of the UCI Occupancy Detection office room. Selected "
                "because it is a continuous environmental variable compatible "
                "with this framework — not on any forecasting-performance "
                "criterion. Occupancy is a binary label and is not used, since "
                "ConfoSense is evaluated here as a continuous-variable "
                "forecasting and uncertainty framework."
            ),
            metadata={
                "target_kind": "temperature",
                "target_column": target_col,
                "target_rationale": (
                    "single documented continuous temperature channel; "
                    "no performance criterion entered the choice"
                ),
                "auxiliary": True,
                "segment_gaps": gaps,
                "segment_order": [name for name, _ in segments],
            },
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _fit_partitioner(series: list[PreparedSeries], cfg: dict) -> Partitioner:
        """Cut the pooled, time-ordered row sequence at the configured fractions."""
        split = cfg.get("split", {})
        f_train = float(split.get("train_frac", 0.6))
        f_calib = float(split.get("calib_frac", 0.2))

        stamps = np.sort(np.concatenate(
            [s.frame.index.to_numpy() for s in series]))
        n = len(stamps)
        i1 = int(n * f_train)
        i2 = int(n * (f_train + f_calib))
        return PooledChronologicalPartitioner(
            fractions=(f_train, f_calib, 1.0 - f_train - f_calib),
            boundary_train_end=pd.Timestamp(stamps[i1]),
            boundary_calib_end=pd.Timestamp(stamps[i2]),
        )

    # ------------------------------------------------------------------ #
    def profile(self, prepared: PreparedDataset) -> pd.DataFrame:
        """Generic per-series profile plus the segment provenance columns."""
        df = super().profile(prepared)
        df.insert(1, "source_file",
                  [s.metadata.get("source_file", "") for s in prepared.series])
        return df
