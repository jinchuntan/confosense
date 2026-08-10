"""Target selection, dataset construction and chronological splitting.

Reads the authors' analysis-ready long-format room file, selects one indoor
temperature series with a reproducible rule, resamples it onto a regular grid,
applies documented outlier and missing-data handling, and produces the
train/calibration/test partition together with an audit of every decision.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import plotting


# --------------------------------------------------------------------------- #
# Chronological splitting (pure functions, exercised directly by the tests)
# --------------------------------------------------------------------------- #
def chronological_split_boundaries(index: pd.DatetimeIndex, train_frac: float, calib_frac: float):
    """Return the two timestamps that separate train | calibration | test.

    Boundaries are taken at position quantiles of the ordered index so that the
    partitions are strictly contiguous in time.
    """
    n = len(index)
    ordered = index.sort_values()
    i_train = int(np.floor(n * train_frac))
    i_calib = int(np.floor(n * (train_frac + calib_frac)))
    return ordered[i_train], ordered[i_calib]


def assign_split(times: pd.DatetimeIndex, t_train_end, t_calib_end) -> np.ndarray:
    """Label each timestamp as train / calibration / test."""
    times = pd.DatetimeIndex(times)
    labels = np.where(times < t_train_end, "train",
                      np.where(times < t_calib_end, "calibration", "test"))
    return labels


# --------------------------------------------------------------------------- #
# Target selection
# --------------------------------------------------------------------------- #
def load_room_table(cfg: dict) -> pd.DataFrame:
    ds = cfg["dataset"]
    path = Path(cfg["paths"]["interim_dir"]) / ds["room_all_file"]
    df = pd.read_csv(path, sep=ds["csv_sep"])
    df[ds["timestamp_col"]] = pd.to_datetime(df[ds["timestamp_col"]], utc=True, format="mixed")
    # Work in tz-naive UTC to keep resampling/reindexing simple.
    df[ds["timestamp_col"]] = df[ds["timestamp_col"]].dt.tz_convert("UTC").dt.tz_localize(None)
    return df


def select_target(df: pd.DataFrame, cfg: dict) -> tuple[dict, pd.DataFrame]:
    """Rank candidate rooms and pick one; return (choice, audit_table)."""
    ds, ts = cfg["dataset"], cfg["dataset"]["timestamp_col"]
    freq = pd.Timedelta(cfg["resample"]["freq"])
    tgt = ds["target_var"]
    sel = cfg["target_selection"]

    rows = []
    for (block, room), g in df.groupby([ds["block_col"], ds["room_col"]]):
        g = g.sort_values(ts)
        v = g[tgt].astype(float)
        t0, t1 = g[ts].min(), g[ts].max()
        expected = int((t1 - t0) / freq) + 1
        n_valid = int(v.notna().sum())
        coverage = n_valid / expected if expected else 0.0
        dup_frac = float((v.diff() == 0).mean())
        rows.append({
            "block": block, "room": int(room),
            "start": t0, "end": t1, "span_days": (t1 - t0).days,
            "n_rows": len(g), "n_valid": n_valid,
            "coverage": round(coverage, 5),
            "missing_fraction": round(1 - coverage, 5),
            "std": round(float(v.std()), 4),
            "mean": round(float(v.mean()), 4),
            "forward_fill_fraction": round(dup_frac, 5),
        })
    audit = pd.DataFrame(rows)

    audit["passes_quality"] = (audit["std"] > sel["min_std"]) & (audit["n_valid"] >= sel["min_valid_obs"])
    ranked = audit[audit["passes_quality"]].sort_values(
        by=["coverage", "span_days", "n_valid", "forward_fill_fraction", "block", "room"],
        ascending=[False, False, False, True, True, True],
    )
    if ranked.empty:
        raise RuntimeError("No candidate room passed the quality filter.")
    best = ranked.iloc[0]

    audit["selected"] = (audit["block"] == best["block"]) & (audit["room"] == best["room"])
    reason = (
        "All candidates share the full span and complete coverage in the "
        "authors' gap-filled file; after excluding near-constant sensors "
        f"(std>{sel['min_std']}), the least forward-filled series was chosen "
        "(lowest fraction of consecutive-duplicate values), with (block, room) "
        "as the final deterministic tie-break."
    )
    audit["selection_reason"] = ""
    audit.loc[audit["selected"], "selection_reason"] = reason

    choice = {
        "block": str(best["block"]),
        "room": int(best["room"]),
        "sensor_variable": tgt,
        "start": best["start"], "end": best["end"],
        "n_valid": int(best["n_valid"]),
        "missing_fraction": float(best["missing_fraction"]),
        "resample_freq": cfg["resample"]["freq"],
        "reason": reason,
    }
    return choice, audit


# --------------------------------------------------------------------------- #
# Dataset construction
# --------------------------------------------------------------------------- #
def build_dataset(df: pd.DataFrame, choice: dict, cfg: dict) -> pd.DataFrame:
    ds, ts = cfg["dataset"], cfg["dataset"]["timestamp_col"]
    freq = pd.Timedelta(cfg["resample"]["freq"])
    cov = cfg["covariates"]
    room = df[(df[ds["block_col"]] == choice["block"]) & (df[ds["room_col"]] == choice["room"])].copy()
    room = room.sort_values(ts).set_index(ts)

    # Regular grid over the observed span.
    grid = pd.date_range(room.index.min(), room.index.max(), freq=freq)
    room = room[~room.index.duplicated(keep="first")].reindex(grid)
    room.index.name = "timestamp"

    out = pd.DataFrame(index=grid)
    out.index.name = "timestamp"

    # Target with physical-range outlier removal, then short-gap interpolation.
    target = room[ds["target_var"]].astype(float)
    lo, hi = cfg["outliers"]["target_min"], cfg["outliers"]["target_max"]
    n_outliers = int(((target < lo) | (target > hi)).sum())
    target = target.mask((target < lo) | (target > hi))
    out["target_was_missing"] = target.isna().astype(int)
    max_gap = cfg["missing"]["max_short_gap_steps"]
    out["target"] = target.interpolate(method="time", limit=max_gap, limit_area="inside")

    # Continuous covariates: short-gap interpolate. Categorical HVAC: short ffill.
    continuous = [cov["outdoor_temp"], cov["humidity"], cov["radiation"], cov["setpoint"]]
    for col in continuous:
        if col in room:
            s = room[col].astype(float)
            out[f"{col}_was_missing"] = s.isna().astype(int)
            out[col] = s.interpolate(method="time", limit=max_gap, limit_area="inside")
    for col in [cov["hvac_state"]] + cov["hvac_mode_onehot"]:
        if col in room:
            s = room[col].astype(float)
            out[col] = s.ffill(limit=max_gap)

    attrs = {
        "block": choice["block"], "room": choice["room"],
        "freq": cfg["resample"]["freq"], "n_outliers_removed": n_outliers,
        "outlier_bounds": (lo, hi),
    }
    out.attrs.update(attrs)
    return out


def split_summary(processed: pd.DataFrame, boundaries, cfg: dict) -> pd.DataFrame:
    t_train_end, t_calib_end = boundaries
    labels = assign_split(processed.index, t_train_end, t_calib_end)
    rows = []
    for name in ["train", "calibration", "test"]:
        mask = labels == name
        sub = processed.index[mask]
        rows.append({
            "split": name,
            "n_steps": int(mask.sum()),
            "start": sub.min() if len(sub) else None,
            "end": sub.max() if len(sub) else None,
            "fraction": round(mask.mean(), 4),
        })
    summary = pd.DataFrame(rows)
    # Chronology assertions demanded by the specification.
    assert summary.loc[0, "end"] < summary.loc[1, "start"], "train must precede calibration"
    assert summary.loc[1, "end"] < summary.loc[2, "start"], "calibration must precede test"
    return summary


def run(cfg: dict) -> dict:
    """Execute steps 2-5 and persist their artefacts."""
    out_dir = Path(cfg["paths"]["outputs_dir"])
    prof = out_dir / "data_profiles"
    prof.mkdir(parents=True, exist_ok=True)

    df = load_room_table(cfg)
    choice, audit = select_target(df, cfg)
    audit.to_csv(prof / "target_selection.csv", index=False)

    processed = build_dataset(df, choice, cfg)
    proc_dir = Path(cfg["paths"]["processed_dir"])
    proc_dir.mkdir(parents=True, exist_ok=True)
    processed.to_parquet(proc_dir / "target_dataset.parquet")

    pre = pd.DataFrame([{
        "dataset": "PLEIAData",
        "block": choice["block"], "room": choice["room"],
        "sensor_variable": choice["sensor_variable"],
        "start": choice["start"], "end": choice["end"],
        "n_valid_raw": choice["n_valid"],
        "missing_fraction": choice["missing_fraction"],
        "resample_freq": choice["resample_freq"],
        "n_outliers_removed": processed.attrs.get("n_outliers_removed"),
        "target_min_bound": cfg["outliers"]["target_min"],
        "target_max_bound": cfg["outliers"]["target_max"],
        "n_processed_steps": len(processed),
    }])
    pre.to_csv(prof / "preprocessing_summary.csv", index=False)

    boundaries = chronological_split_boundaries(
        processed.index, cfg["split"]["train_frac"], cfg["split"]["calib_frac"]
    )
    summary = split_summary(processed, boundaries, cfg)
    summary.to_csv(prof / "split_summary.csv", index=False)

    plotting.plot_data_split(
        processed["target"], boundaries[0], boundaries[1],
        out_dir / "figures" / "figure_4_data_split.png",
    )

    return {
        "processed": processed,
        "choice": choice,
        "boundaries": boundaries,
        "split_summary": summary,
    }


def main() -> None:
    import argparse
    import yaml

    parser = argparse.ArgumentParser(description="Prepare the PLEIAData target dataset.")
    parser.add_argument("--config", default="configs/pleia_preliminary.yaml")
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    result = run(cfg)
    print("Selected target:", result["choice"])
    print(result["split_summary"].to_string(index=False))


if __name__ == "__main__":
    main()
