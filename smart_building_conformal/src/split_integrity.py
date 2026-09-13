"""Shared temporal/group boundaries for selection, refitting and tuning.

Cuts are made on unique origin times (all buildings share a boundary), or on
whole experimental runs. Earlier targets must be strictly before the next
block's first origin, as required by the frozen protocol.
"""
from __future__ import annotations

import hashlib
import numpy as np
import pandas as pd

GROUPED = "whole_run_group_blocked"


def ordered_blocks(meta, indices, fractions, scheme="chronological"):
    indices = np.asarray(indices, dtype=int)
    sub = meta.iloc[indices]
    if scheme == GROUPED:
        units = sorted(pd.unique(sub.group_id), key=lambda g: (
            sub.loc[sub.group_id == g, "origin_time"].min(), str(g)))
        values = sub.group_id.to_numpy()
    else:
        units = sorted(pd.unique(sub.origin_time))
        values = sub.origin_time.to_numpy()
    if len(units) < len(fractions):
        raise ValueError("too few independent split units")
    cuts = [0] + [int(len(units) * f) for f in np.cumsum(fractions)[:-1]] + [len(units)]
    if any(a == b for a, b in zip(cuts, cuts[1:])):
        raise ValueError("empty split block")
    blocks = [indices[np.isin(values, units[a:b])] for a, b in zip(cuts, cuts[1:])]
    for i in range(len(blocks) - 1):
        start = meta.iloc[blocks[i + 1]].origin_time.min()
        if scheme == GROUPED:
            # Purge entire overlapping runs, never fragments of a run.
            left = meta.iloc[blocks[i]]
            bad = left.loc[left.target_time >= start, "group_id"].unique()
            blocks[i] = blocks[i][~left.group_id.isin(bad).to_numpy()]
        else:
            blocks[i] = blocks[i][(meta.iloc[blocks[i]].target_time < start).to_numpy()]
    for block in blocks:
        if not len(block):
            raise ValueError("embargo removed an entire split block")
    for left, right in zip(blocks, blocks[1:]):
        assert_boundary(meta, left, right, scheme)
    return blocks


def boundary_record(meta, left, right, scheme="chronological"):
    a, b = meta.iloc[left], meta.iloc[right]
    shared = set(a.group_id.dropna()) & set(b.group_id.dropna())
    return {
        "n_left": len(a), "n_right": len(b),
        "left_origin_min": str(a.origin_time.min()),
        "left_origin_max": str(a.origin_time.max()),
        "left_target_max": str(a.target_time.max()),
        "right_origin_min": str(b.origin_time.min()),
        "right_origin_max": str(b.origin_time.max()),
        "right_target_min": str(b.target_time.min()),
        "right_target_max": str(b.target_time.max()),
        "target_overlap_count": int((a.target_time >= b.origin_time.min()).sum()),
        "row_overlap_count": len(set(left) & set(right)),
        "shared_groups": ";".join(sorted(map(str, shared))),
        "run_intersections": len(shared) if scheme == GROUPED else 0,
        "left_membership_sha256": membership_hash(meta, left),
        "right_membership_sha256": membership_hash(meta, right),
    }


def assert_boundary(meta, left, right, scheme="chronological"):
    if not len(left) or not len(right):
        raise ValueError("empty temporal boundary")
    r = boundary_record(meta, left, right, scheme)
    if r["target_overlap_count"] or r["row_overlap_count"] or r["run_intersections"]:
        raise ValueError(f"unsafe {scheme} boundary: {r}")


def membership_hash(meta, indices):
    keys = meta.iloc[indices][["group_id", "origin_time", "target_time"]]
    return hashlib.sha256(keys.to_csv(index=False).encode()).hexdigest()


def refit_split(meta, indices, scheme=None):
    scheme = scheme or meta.attrs.get("split_scheme", "chronological")
    return ordered_blocks(meta, indices, [0.75, 0.25], scheme)


def tuning_splits(meta, n_splits, scheme=None):
    """Expanding validation within the supplied training pool only."""
    scheme = scheme or meta.attrs.get("split_scheme", "chronological")
    n = int(n_splits)
    blocks = ordered_blocks(meta, np.arange(len(meta)), [1 / (n + 1)] * (n + 1), scheme)
    out = []
    for j in range(1, len(blocks)):
        tr = np.concatenate(blocks[:j]); va = blocks[j]
        assert_boundary(meta, tr, va, scheme)
        out.append((tr, va))
    return out


def training_scale(y, meta, train_indices):
    from .alerts_corrected import per_group_robust_scale
    idx = np.asarray(train_indices, dtype=int)
    sc = per_group_robust_scale(np.asarray(y)[idx], meta.iloc[idx].group_id.to_numpy())
    return {**sc["scale"], "__pooled__": sc["pooled_fallback"]}


def causal_prepared(prepared, max_gap=3):
    """Undo locally marked interpolation and forward-fill using past values only.

    Upstream-imputed source values cannot be recovered without upstream flags;
    that provenance limitation is retained. No source frame is changed in place.
    """
    from dataclasses import replace
    series = []
    for s in prepared.series:
        frame = s.frame.copy()
        for flag in [c for c in frame if c.endswith("_was_missing")]:
            col = flag.removesuffix("_was_missing")
            if col in frame:
                frame[col] = frame[col].mask(frame[flag].astype(bool)).ffill(limit=max_gap)
        series.append(replace(s, frame=frame))
    return replace(prepared, series=series)
