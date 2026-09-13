"""Common flat/lazy-sequence support and frozen, purged pilot membership."""
from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd
from . import split_integrity as SI, windowing
from .corrected_study import make_outer_folds


class LazySequences:
    """Keep raw per-series channels; materialise only requested batches."""
    def __init__(self, prepared, meta, seq_len):
        from .attention_lstm import build_channel_matrix
        self.seq_len = int(seq_len); self.channels = []; self.names = None
        self.series_index = np.full(len(meta), -1, dtype=int)
        self.positions = np.full(len(meta), -1, dtype=int)
        self.valid = np.zeros(len(meta), bool)
        for i, series in enumerate(prepared.series):
            channel, names = build_channel_matrix(series.frame, {"covariates": series.covariates})
            if self.names is not None and self.names != names:
                raise ValueError("sequence channel schema differs between series")
            self.names = names; self.channels.append(channel.astype(np.float32))
            mask = meta.group_id.isna() if pd.isna(series.group_id) else meta.group_id.eq(series.group_id)
            rows = np.flatnonzero(mask.to_numpy())
            pos = series.frame.index.get_indexer(pd.DatetimeIndex(meta.iloc[rows].origin_time))
            self.series_index[rows] = i; self.positions[rows] = pos
            bad = ~np.isfinite(channel).all(axis=1)
            cumulative = np.r_[0, np.cumsum(bad)]
            eligible = pos >= seq_len - 1
            good_pos = pos[eligible]
            self.valid[rows[eligible]] = (cumulative[good_pos+1] - cumulative[good_pos-seq_len+1]) == 0
        self.n_features = len(self.names or [])

    def take(self, rows):
        rows = np.asarray(rows, int)
        if not self.valid[rows].all():
            raise ValueError("requested ineligible sequence")
        out = np.empty((len(rows), self.seq_len, self.n_features), dtype=np.float32)
        offsets = np.arange(1-self.seq_len, 1)
        for group in np.unique(self.series_index[rows]):
            local = np.flatnonzero(self.series_index[rows] == group)
            out[local] = self.channels[group][self.positions[rows[local], None] + offsets]
        return out

    @property
    def stored_bytes(self):
        return sum(a.nbytes for a in self.channels) + self.series_index.nbytes + self.positions.nbytes + self.valid.nbytes


def build_support(prepared, dataset_cfg, horizon, seq_len):
    fcfg = windowing.feature_config(dataset_cfg, prepared.series[0].covariates)
    w = windowing.build_dataset_windows(prepared, horizon, fcfg)
    lazy = LazySequences(prepared, w["meta"], seq_len)
    keep = lazy.valid & np.isfinite(w["X"].to_numpy()).all(axis=1) & np.isfinite(w["y"])
    raw_rows = np.flatnonzero(keep)
    meta = w["meta"].iloc[raw_rows].reset_index(drop=True).copy()
    meta["row_id"] = [hashlib.sha256(f"{horizon}|{g}|{o}|{t}".encode()).hexdigest()
        for g, o, t in meta[["group_id", "origin_time", "target_time"]].itertuples(index=False, name=None)]
    if meta.row_id.duplicated().any():
        raise ValueError("duplicate common-support row ID")
    X = w["X"].iloc[raw_rows].reset_index(drop=True)
    y = w["y"][raw_rows]
    data_hash = hashlib.sha256(pd.util.hash_pandas_object(X, index=False).values.tobytes()
        + pd.util.hash_pandas_object(meta, index=False).values.tobytes()
        + b"".join(a.tobytes() for a in lazy.channels)).hexdigest()
    return dict(X=X, y=y, meta=meta, lazy=lazy, sequence_rows=raw_rows,
        eligible_rows=len(meta), flat_rows=len(w["meta"]), excluded_rows=int((~keep).sum()),
        data_hash=data_hash, feature_names=list(X.columns), sequence_channels=lazy.names)


def pilot_roles(meta, horizon, freq, outer_fold=0, n_outer=3):
    # Reserve final calibration BEFORE constructing inner tuning folds.
    fold = make_outer_folds(meta, "chronological", n_outer, horizon, freq)[outer_fold]
    pool = np.concatenate([fold["train"], fold["calibration"]])
    fit, calibration = SI.refit_split(meta, pool, "chronological")
    test = fold["test"]
    inner = [(fit[a], fit[b]) for a, b in SI.tuning_splits(meta.iloc[fit].reset_index(drop=True), 2)]
    SI.assert_boundary(meta, fit, calibration)
    SI.assert_boundary(meta, calibration, test)
    roles = dict(fit=fit, calibration=calibration, test=test)
    for i, (a,b) in enumerate(inner):
        SI.assert_boundary(meta, a,b)
        roles[f"inner{i}_train"], roles[f"inner{i}_validation"] = a,b
        if not set(a).union(b) <= set(fit):
            raise ValueError("tuning escaped final fitting block")
    return roles


def role_records(meta, roles):
    return {name: dict(n=len(idx), membership_hash=SI.membership_hash(meta, idx),
        row_id_hash=hashlib.sha256("\n".join(meta.iloc[idx].row_id).encode()).hexdigest(),
        origin_min=str(meta.iloc[idx].origin_time.min()), origin_max=str(meta.iloc[idx].origin_time.max()),
        target_min=str(meta.iloc[idx].target_time.min()), target_max=str(meta.iloc[idx].target_time.max()))
        for name,idx in roles.items()}
