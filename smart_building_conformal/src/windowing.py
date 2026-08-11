"""Group-safe supervised windowing over the common prepared-data representation.

The preliminary driver built its design matrix from a single PLEIAData frame.
The full study has to do the same for datasets made of many independent blocks —
RICO experimental runs and BDG2 buildings — where a lag or rolling window that
reached across a block boundary would be meaningless (and, for RICO, would leak
one run's observations into another's features).

The guarantee here is structural rather than checked after the fact: features are
built **one :class:`~src.datasets.base.PreparedSeries` at a time** by
:func:`src.features.build_supervised`, and the per-series matrices are only
concatenated once they are complete. A window therefore cannot span two series,
because no code path ever hands two series to the feature builder together.

Partition labels are likewise resolved per series through the dataset's
:class:`~src.datasets.base.Partitioner`, so a chronologically split dataset and a
run-partitioned one both arrive here as the same ``partition`` column.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import features
from .datasets.base import PARTITIONS, PreparedDataset, PreparedSeries


def feature_config(cfg: dict, covariates: list[str]) -> dict:
    """Translate a study config's ``features`` block into the builder's schema."""
    f = cfg.get("features", {})
    return {
        "target_lags": f.get("target_lags", [1, 2, 3]),
        "rolling_windows": f.get("rolling_windows", [6]),
        "include_weekly": f.get("include_weekly", False),
        "covariates": list(covariates),
    }


def build_series_windows(
    series: PreparedSeries,
    horizon: int,
    fcfg: dict,
) -> dict | None:
    """Supervised matrices for exactly one series, or ``None`` if none survive.

    A series shorter than the feature warm-up plus the horizon yields no complete
    rows; that is normal for short RICO runs at the longest horizon and is
    reported as a reduced sample count rather than an error.
    """
    sup = features.build_supervised(
        series.frame, horizon, series.freq, series.season_steps, fcfg
    )
    if len(sup["X"]) == 0:
        return None
    meta = sup["meta"].copy()
    meta.insert(0, "group_id", series.group_id)
    meta.insert(0, "target_id", series.target_id)
    meta.insert(0, "dataset", series.dataset_id)
    return {"X": sup["X"].reset_index(drop=True), "meta": meta,
            "feature_names": sup["feature_names"]}


def build_dataset_windows(
    prepared: PreparedDataset,
    horizon: int,
    fcfg: dict,
) -> dict:
    """Concatenate per-series windows into one design matrix with partitions.

    Returns ``X`` (features), ``y`` (direct target at origin + horizon), ``meta``
    (dataset / group / origin / target time and the leak-free baselines), and a
    boolean mask per partition.
    """
    X_parts, meta_parts, names = [], [], None
    skipped: list[str] = []

    for series in prepared.series:
        built = build_series_windows(series, horizon, fcfg)
        if built is None:
            skipped.append(str(series.group_id))
            continue
        if names is None:
            names = built["feature_names"]
        elif built["feature_names"] != names:
            raise ValueError(
                f"{series.label}: feature columns differ from earlier series; "
                "every series of a dataset must produce the same schema"
            )
        labels = prepared.partitioner.labels(
            series, pd.DatetimeIndex(built["meta"]["origin_time"])
        )
        m = built["meta"]
        m["partition"] = labels
        X_parts.append(built["X"])
        meta_parts.append(m)

    if not X_parts:
        raise ValueError(
            f"{prepared.dataset_id}: no series produced a complete window at "
            f"horizon {horizon} (all {len(prepared.series)} series too short)"
        )

    X = pd.concat(X_parts, ignore_index=True)
    meta = pd.concat(meta_parts, ignore_index=True)
    y = meta["y_true"].to_numpy(dtype=float)
    idx = {p: (meta["partition"] == p).to_numpy() for p in PARTITIONS}

    return {
        "X": X, "y": y, "meta": meta, "idx": idx,
        "feature_names": names, "horizon": horizon,
        "skipped_groups": skipped,
        "seasonal_naive_supported": prepared.seasonal_naive_supported,
    }


def build_dataset_sequences(
    prepared: PreparedDataset,
    horizon: int,
    seq_len: int,
    meta: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """LSTM input windows aligned row-for-row with an existing ``meta`` frame.

    Sequences are cut inside a single series, so like the flat features they
    cannot span a run or building boundary. They are then reindexed onto
    ``meta``'s ``(group_id, origin_time)`` keys, which is what keeps the flat and
    sequence views of the same forecast origin on the same row. Origins with no
    complete sequence (too close to the start of their series) get an all-NaN
    window, and the caller drops them.
    """
    from . import attention_lstm

    frames, names = [], None
    for series in prepared.series:
        chan, chan_names = attention_lstm.build_channel_matrix(
            series.frame, {"covariates": series.covariates}
        )
        if names is None:
            names = chan_names
        Xseq, _, pos = attention_lstm.build_sequences(
            chan, series.frame["target"].to_numpy(), seq_len, horizon
        )
        if len(pos) == 0:
            continue
        frames.append(pd.DataFrame({
            "group_id": series.group_id,
            "origin_time": series.frame.index[pos],
            "row": np.arange(len(pos)),
        }).assign(_seq=list(Xseq)))

    n_feat = len(names) if names else 1
    if not frames:
        return (np.full((len(meta), seq_len, n_feat), np.nan, dtype=np.float32),
                np.zeros(len(meta), dtype=bool), names or [])

    lookup = pd.concat(frames, ignore_index=True)
    key = ["group_id", "origin_time"]
    merged = meta[key].merge(
        lookup[key + ["_seq"]], on=key, how="left", validate="one_to_one"
    )
    have = merged["_seq"].notna().to_numpy()
    out = np.full((len(meta), seq_len, n_feat), np.nan, dtype=np.float32)
    if have.any():
        out[have] = np.stack(merged.loc[have, "_seq"].to_list()).astype(np.float32)
    return out, have, names


def subset(obj, mask: np.ndarray):
    """Mask a frame or array, always returning a positionally-indexed result."""
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        return obj.loc[mask].reset_index(drop=True)
    return np.asarray(obj)[mask]


def window_summary(windows: dict) -> pd.DataFrame:
    """Per-partition row counts, used for the split-integrity audit files."""
    meta = windows["meta"]
    rows = []
    for p in PARTITIONS:
        sub = meta[meta["partition"] == p]
        rows.append({
            "horizon": windows["horizon"],
            "partition": p,
            "n_rows": len(sub),
            "n_groups": sub["group_id"].nunique(dropna=False),
            "origin_start": sub["origin_time"].min() if len(sub) else pd.NaT,
            "origin_end": sub["origin_time"].max() if len(sub) else pd.NaT,
        })
    return pd.DataFrame(rows)
