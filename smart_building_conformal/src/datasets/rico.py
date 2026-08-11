"""RICO HVAC adapter — independent four-hour experimental runs.

Reference
---------
Thiry, Z., Ruocco, M., Nocente, A. and Oksavik, O. A. (2025). "The RICO dataset:
A multivariate HVAC indoors and outdoors time-series dataset." *Data in Brief*,
61, 111678. DOI: 10.1016/j.dib.2025.111678

Source
------
Official Zenodo deposit by SINTEF AS Digital, record 14871584
(DOI 10.60609/tw79-4k72), CC BY 4.0. Five ``RICO_Acquisition_*.hdf`` files plus a
README. No mirror is used. The files are pandas/PyTables HDF stores under the key
``all``; ``pandas.read_hdf`` is the primary reader, with a documented h5py block
reader as fallback so the adapter still works without PyTables installed.

Run segmentation (the rule everything else depends on)
------------------------------------------------------
The README documents three acquisition columns: ``Acquisition Phase``,
``Scheduler Step`` (the point number within a phase) and ``Flag`` (1 normal,
0 abnormal). A **run** is therefore the maximal contiguous ``Flag == 1`` block
inside one ``(Acquisition Phase, Scheduler Step)`` group. Verified against the
archive, this reproduces the paper's description exactly: each group yields one
contiguous block of 240 one-minute samples — the four-hour run — and the
surrounding ``Flag == 0`` samples are the settling/downtime periods the authors
mark as unusable. (Acquisition phase 3 records 16-hour scheduler groups because
of the scheduler-frequency mistake the README describes; taking the flagged block
recovers its four usable hours and needs no special case.)

Every run becomes its own :class:`~src.datasets.base.PreparedSeries`, which is
what enforces the two RICO-specific rules from the protocol:

* a run is assigned **whole** to train, calibration or test by
  :class:`~src.datasets.base.GroupPartitioner`, so no timestamp of a run can
  appear in two partitions;
* feature windows are built per series, so no lag or rolling window can reach
  from one run into another, and targets that would fall past a run's end simply
  do not exist.

Seasonality
-----------
``season_steps`` is ``None``. A four-hour run cannot contain a daily cycle, so the
seasonal-naive baseline is reported as *not applicable* for RICO rather than
fabricated from a cross-run lag — which would splice unrelated experiments
together.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import register
from .base import (
    DatasetAdapter,
    GroupPartitioner,
    PreparedDataset,
    PreparedSeries,
    Provenance,
    file_checksum,
)

ZENODO_RECORD = "14871584"
ZENODO_API = "https://zenodo.org/api/records/{record}"

# Room-temperature sensors as documented in the dataset README, section 2.
TEMPERATURE_SENSORS = {
    "B.RTD1": "Cell A Pt100 thermometer, centre of the room, 10 cm from the floor",
    "B.RTD2": "Pt100 air thermometer, 60 cm from the floor",
    "B.RTD3": "Pt100 air thermometer, 110 cm from the floor",
    "B.RTD6": "Globe thermometer, 160 cm from the floor",
}

DEFAULT_COVARIATES = [
    # Controlled inputs (documented section 1).
    "SB47", "SB46", "SB43", "EC3",
    "pid.SB47.setpoint", "pid.SB46.setpoint", "pid.SB43.setpoint", "pid.EC3.setpoint",
    # Supply/return water and duct temperatures.
    "RTD420", "RTD509", "RTD417", "RTD508", "RTD410.T", "RTD406A",
    # Outdoor weather (documented section 3).
    "WS1_Temperature", "WS1_Relative_humidity", "WS1_Solar_radiation", "WS1_Wind_speed",
]


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #
def _read_block_store(path: Path) -> pd.DataFrame:
    """Fallback reader for the pandas block layout, using h5py only.

    Kept so a missing PyTables install degrades to a slower path rather than
    blocking the dataset entirely. The layout (``axis0`` column names, ``axis1``
    epoch index, ``blockN_items`` / ``blockN_values``) is read explicitly.
    """
    import h5py

    with h5py.File(path, "r") as f:
        grp = f["all"]
        index = pd.to_datetime(np.asarray(grp["axis1"]), utc=True)
        frames = []
        for key in grp:
            if not key.endswith("_items"):
                continue
            prefix = key[: -len("_items")]
            names = [n.decode() if isinstance(n, bytes) else str(n)
                     for n in np.asarray(grp[f"{prefix}_items"])]
            values = np.asarray(grp[f"{prefix}_values"])
            frames.append(pd.DataFrame(values, columns=names, index=index))
    out = pd.concat(frames, axis=1)
    return out


def read_acquisition(path: Path) -> pd.DataFrame:
    """Read one acquisition file and return a tz-naive UTC-indexed frame."""
    try:
        df = pd.read_hdf(path, key="all")
    except ImportError:
        df = _read_block_store(path)
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)
    df = df.copy()
    df.index = idx
    df.index.name = "timestamp"
    return df.sort_index()


def download(raw_dir: Path, record: str = ZENODO_RECORD) -> list[Path]:
    """Fetch the official Zenodo deposit; already-complete files are skipped."""
    import requests

    raw_dir.mkdir(parents=True, exist_ok=True)
    meta = requests.get(ZENODO_API.format(record=record), timeout=120).json()
    paths = []
    for f in meta.get("files", []):
        dest = raw_dir / f["key"]
        if not (dest.exists() and dest.stat().st_size == f.get("size")):
            with requests.get(f["links"]["self"], stream=True, timeout=1800) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as out:
                    for chunk in resp.iter_content(1 << 20):
                        out.write(chunk)
        paths.append(dest)
    return paths


# --------------------------------------------------------------------------- #
# Run segmentation
# --------------------------------------------------------------------------- #
def segment_runs(
    df: pd.DataFrame,
    freq: pd.Timedelta,
    min_length: int,
    phase_col: str = "Acquisition Phase",
    step_col: str = "Scheduler Step",
    flag_col: str = "Flag",
) -> list[dict]:
    """Split one acquisition frame into flagged, contiguous, regular runs.

    A block is kept only if it is uniformly sampled at ``freq`` and at least
    ``min_length`` samples long; anything else is returned with a rejection
    reason so the audit file can account for every candidate.
    """
    runs = []
    for (phase, step), grp in df.groupby([phase_col, step_col], sort=True):
        grp = grp.sort_index()
        flag = grp[flag_col].to_numpy() if flag_col in grp.columns else np.ones(len(grp))
        keep = flag == 1
        if not keep.any():
            # The authors flagged this whole scheduler point as abnormal (the
            # entire acquisition 2 is marked this way because of the recording
            # bug its README documents). Record it so the audit accounts for
            # every group rather than letting it vanish silently.
            runs.append({
                "run_id": f"P{int(phase)}S{int(step)}", "phase": int(phase),
                "step": int(step), "frame": grp.iloc[0:0], "n": 0,
                "start": grp.index[0], "end": grp.index[-1],
                "accepted": False,
                "reason_excluded": "no sample flagged normal (Flag==1) by the authors",
            })
            continue
        # Maximal contiguous True blocks.
        edges = np.flatnonzero(np.diff(np.concatenate([[0], keep.view(np.int8), [0]])))
        for start, stop in zip(edges[::2], edges[1::2]):
            block = grp.iloc[start:stop]
            run_id = f"P{int(phase)}S{int(step)}"
            if len(runs):
                # Distinguish multiple flagged blocks inside one scheduler group.
                same = [r for r in runs if r["run_id"].startswith(run_id)]
                if same:
                    run_id = f"{run_id}B{len(same)}"
            gaps = block.index.to_series().diff().dropna().unique()
            regular = len(gaps) <= 1 and (len(gaps) == 0 or gaps[0] == freq)
            reason = ""
            if len(block) < min_length:
                reason = f"only {len(block)} flagged samples (< {min_length})"
            elif not regular:
                reason = f"irregular sampling within the run: {list(gaps)}"
            runs.append({
                "run_id": run_id, "phase": int(phase), "step": int(step),
                "frame": block, "n": len(block),
                "start": block.index[0], "end": block.index[-1],
                "accepted": reason == "", "reason_excluded": reason,
            })
    return runs


# --------------------------------------------------------------------------- #
# Adapter
# --------------------------------------------------------------------------- #
@register
class RicoAdapter(DatasetAdapter):
    dataset_id = "rico"

    def provenance(self) -> Provenance:
        return Provenance(
            dataset_id=self.dataset_id,
            official_source="Zenodo record 14871584 (SINTEF AS Digital)",
            doi="10.1016/j.dib.2025.111678",
            download_url=f"https://zenodo.org/records/{ZENODO_RECORD}",
            license="CC BY 4.0",
            citation=(
                "Thiry, Z., Ruocco, M., Nocente, A., Oksavik, O. A. (2025). The RICO "
                "dataset: A multivariate HVAC indoors and outdoors time-series "
                "dataset. Data in Brief, 61, 111678."
            ),
        )

    # ------------------------------------------------------------------ #
    def prepare(self, cfg: dict) -> PreparedDataset:
        rcfg = cfg.get("rico", {})
        raw_dir = Path(cfg["paths"]["raw_dir"]) / rcfg.get("subdir", "rico")
        files = sorted(raw_dir.glob("RICO_Acquisition_*.hdf"))
        if not files:
            if rcfg.get("auto_download", True):
                download(raw_dir)
                files = sorted(raw_dir.glob("RICO_Acquisition_*.hdf"))
            if not files:
                raise FileNotFoundError(
                    f"no RICO acquisition files under {raw_dir}; run "
                    "`python -m src.fetch_datasets --dataset rico` first"
                )

        freq = pd.Timedelta(rcfg.get("freq", "1min"))
        target_col = rcfg.get("target_column", "B.RTD3")
        min_length = int(rcfg.get("min_run_length", 120))
        max_gap = cfg.get("missing", {}).get("max_short_gap_steps", 3)

        if target_col not in TEMPERATURE_SENSORS:
            raise ValueError(
                f"target_column {target_col!r} is not one of the documented RICO "
                f"room-temperature sensors {sorted(TEMPERATURE_SENSORS)}"
            )

        # ---- read and segment ----
        all_runs, sensor_rows = [], []
        for path in files:
            df = read_acquisition(path)
            for col, desc in TEMPERATURE_SENSORS.items():
                if col in df.columns:
                    s = df[col].astype(float)
                    sensor_rows.append({
                        "file": path.name, "sensor": col, "description": desc,
                        "unit": "degC", "n": len(s),
                        "missing_fraction": float(s.isna().mean()),
                        "mean": float(s.mean()), "std": float(s.std()),
                        "min": float(s.min()), "max": float(s.max()),
                    })
            runs = segment_runs(df, freq, min_length)
            for r in runs:
                r["file"] = path.name
            all_runs.extend(runs)

        # ---- build one series per accepted run ----
        covariates = [c for c in rcfg.get("covariates", DEFAULT_COVARIATES)]
        series_list, run_rows = [], []
        for r in all_runs:
            frame = r["frame"]
            row = {
                "run_id": r["run_id"], "file": r["file"], "phase": r["phase"],
                "step": r["step"], "n_samples": r["n"],
                "start": r["start"], "end": r["end"],
                "duration_min": (r["end"] - r["start"]) / pd.Timedelta(minutes=1) + 1,
                "accepted": r["accepted"], "reason_excluded": r["reason_excluded"],
            }
            if not r["accepted"] or target_col not in frame.columns:
                if target_col not in frame.columns:
                    row["accepted"] = False
                    row["reason_excluded"] = f"target column {target_col} absent"
                run_rows.append(row)
                continue

            target = frame[target_col].astype(float)
            row["target_missing_fraction"] = float(target.isna().mean())
            row["target_std"] = float(target.std())

            out = pd.DataFrame(index=frame.index)
            out.index.name = "timestamp"
            out["target_was_missing"] = target.isna().astype(int)
            out["target"] = target.interpolate(method="time", limit=max_gap,
                                               limit_area="inside")
            present = []
            for col in covariates:
                if col in frame.columns:
                    s = frame[col].astype(float)
                    out[f"{col}_was_missing"] = s.isna().astype(int)
                    out[col] = s.interpolate(method="time", limit=max_gap,
                                             limit_area="inside")
                    present.append(col)

            series_list.append(PreparedSeries(
                dataset_id=self.dataset_id,
                target_id=target_col,
                frame=out,
                freq=freq,
                group_id=r["run_id"],
                season_steps=None,   # a 4 h run holds no daily cycle
                covariates=present,
                units="degC",
                metadata={"phase": r["phase"], "step": r["step"], "file": r["file"]},
            ))
            run_rows.append(row)

        if not series_list:
            raise RuntimeError("no RICO run passed segmentation and quality checks")

        # Covariate set must be identical across runs or the design matrices
        # would not be concatenable; intersect and record any dropped column.
        common = set(series_list[0].covariates)
        for s in series_list:
            common &= set(s.covariates)
        common_ordered = [c for c in covariates if c in common]
        dropped = [c for c in covariates if c not in common]
        for s in series_list:
            keep = ["target", "target_was_missing"] + common_ordered
            keep += [f"{c}_was_missing" for c in common_ordered
                     if f"{c}_was_missing" in s.frame.columns]
            s.frame = s.frame[[c for c in keep if c in s.frame.columns]]
            s.covariates = list(common_ordered)

        partitioner = GroupPartitioner(
            fractions=(cfg["split"]["train_frac"], cfg["split"]["calib_frac"],
                       1.0 - cfg["split"]["train_frac"] - cfg["split"]["calib_frac"])
        ).fit(series_list)

        prov = self.provenance()
        prov.archive_name = ", ".join(p.name for p in files)
        prov.checksum = ";".join(f"{p.name}={file_checksum(p)[:16]}" for p in files)
        prov.preprocessing = [
            f"runs = maximal contiguous Flag==1 blocks within (Acquisition Phase, Scheduler Step)",
            f"runs shorter than {min_length} samples or irregularly sampled were rejected",
            f"target = {target_col} ({TEMPERATURE_SENSORS[target_col]})",
            f"gaps up to {max_gap} steps interpolated within a run only",
            "seasonal-naive not applicable: a 4 h run contains no daily cycle",
        ]
        if dropped:
            prov.notes.append(f"covariates absent from some runs and dropped: {dropped}")

        n_unflagged = sum(1 for r in all_runs
                          if r["reason_excluded"].startswith("no sample flagged"))
        if n_unflagged:
            prov.notes.append(
                f"{n_unflagged} scheduler point(s) carried no Flag==1 sample and were "
                "excluded on the authors' own quality flag. Acquisition phase 2 is "
                "entirely unflagged, which matches the recording bug documented in "
                "the dataset README; excluding it is the authors' judgement, not ours."
            )

        return PreparedDataset(
            dataset_id=self.dataset_id,
            series=series_list,
            partitioner=partitioner,
            provenance=prov,
            target_description=(
                f"RICO indoor air temperature, {target_col} "
                f"({TEMPERATURE_SENSORS[target_col]})"
            ),
            metadata={
                "target_kind": "temperature",
                "run_audit": pd.DataFrame(run_rows),
                "sensor_audit": pd.DataFrame(sensor_rows),
                "target_column": target_col,
                "target_rationale": (
                    f"{target_col} is the documented Pt100 air thermometer at 110 cm, "
                    "the standard seated-occupant measurement height for indoor air "
                    "temperature, inside the actively controlled cell B. Chosen from "
                    "the README's sensor documentation before any model was fitted; "
                    "no forecast metric was consulted. B.RTD1 is excluded because the "
                    "README places it in cell A, which was not under control, and "
                    "B.RTD6 is a globe thermometer measuring operative rather than "
                    "air temperature."
                ),
                "n_runs_total": len(all_runs),
                "n_runs_accepted": len(series_list),
                "dropped_covariates": dropped,
            },
        )
