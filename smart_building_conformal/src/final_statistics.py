"""Group-appropriate bootstrap confidence intervals for the corrected study.

The corrected engine writes, per dataset, ``outer_metrics.csv`` (per fold/seed),
``outer_per_group_coverage.csv`` (per run/building) and ``outer_per_event.csv``
(one row per injected event with its detection outcome). This module turns those
into >= 2000-replicate confidence intervals that **resample the correct unit**:

* RICO — the experimental **run**;
* BDG2 — the **building**;
* the single-series datasets (PLEIA temperature/energy) — moving **blocks** of the
  ordered contributions, never an IID bootstrap on serially dependent data.

Intervals are percentile CIs; the bootstrap generator seed is fixed so the CIs are
reproducible. Aggregation pools all predeclared model seeds (never a best seed).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_BOOT = 2000
GROUP_UNIT = {"rico": "group", "bdg2": "group"}   # else moving-block on rows


def _unit_indices(df: pd.DataFrame, dataset: str) -> list[np.ndarray]:
    """Positional index groups forming the resampling units for ``dataset``."""
    if GROUP_UNIT.get(dataset) == "group" and "group_id" in df and \
            df["group_id"].notna().any():
        return [np.asarray(idx) for _, idx in
                df.reset_index(drop=True).groupby("group_id").groups.items()]
    # single series: moving blocks over the row order
    n = len(df)
    if n == 0:
        return []
    block = max(1, int(round(np.sqrt(n))))
    starts = range(0, n, block)
    return [np.arange(s, min(s + block, n)) for s in starts]


def _bootstrap(df: pd.DataFrame, dataset: str, stat_fn, *,
               n_boot: int = DEFAULT_BOOT, seed: int = 20240601) -> dict:
    """Percentile CI for ``stat_fn(resampled_df)`` resampling the right unit."""
    df = df.reset_index(drop=True)
    units = _unit_indices(df, dataset)
    point = stat_fn(df)
    if not units or not np.isfinite(point):
        return {"estimate": point, "ci_low": np.nan, "ci_high": np.nan,
                "n_boot": 0, "n_units": len(units)}
    rng = np.random.default_rng(seed)
    reps = np.empty(n_boot)
    k = len(units)
    for b in range(n_boot):
        pick = rng.integers(0, k, size=k)
        idx = np.concatenate([units[j] for j in pick])
        reps[b] = stat_fn(df.iloc[idx])
    lo, hi = np.nanpercentile(reps, [2.5, 97.5])
    return {"estimate": float(point), "ci_low": float(lo), "ci_high": float(hi),
            "n_boot": n_boot, "n_units": k}


# ---- metric statistics -------------------------------------------------- #
def _macro_recall(df: pd.DataFrame) -> float:
    if df.empty or "detected" not in df:
        return float("nan")
    strata = df.groupby(["event_type", "severity"])["detected"].mean()
    return float(strata.mean()) if len(strata) else float("nan")


def _mean_coverage(df: pd.DataFrame) -> float:
    if df.empty or "empirical_coverage" not in df:
        return float("nan")
    if "n" in df:                       # exposure-weighted mean coverage
        w = df["n"].to_numpy(float)
        return float(np.average(df["empirical_coverage"], weights=w)) if w.sum() \
            else float(df["empirical_coverage"].mean())
    return float(df["empirical_coverage"].mean())


def dataset_cis(run_root: str | Path, dataset: str, *,
                n_boot: int = DEFAULT_BOOT) -> pd.DataFrame:
    """All headline CIs for one dataset directory of the corrected run."""
    d = Path(run_root) / dataset
    rows = []
    pe = d / "outer_per_event.csv"
    if pe.exists():
        ev = pd.read_csv(pe)
        if not ev.empty:
            rows.append({"dataset": dataset, "metric": "macro_event_recall",
                         **_bootstrap(ev, dataset, _macro_recall, n_boot=n_boot)})
    pg = d / "outer_per_group_coverage.csv"
    if pg.exists():
        cov = pd.read_csv(pg)
        if not cov.empty:
            rows.append({"dataset": dataset, "metric": "empirical_coverage",
                         **_bootstrap(cov, dataset, _mean_coverage, n_boot=n_boot)})
    om = d / "outer_metrics.csv"
    if om.exists():
        m = pd.read_csv(om)
        if not m.empty and "background_episodes_per_asset_day" in m:
            rows.append({"dataset": dataset,
                         "metric": "background_episodes_per_asset_day",
                         **_bootstrap(
                             m, dataset,
                             lambda x: float(np.nanmean(
                                 x["background_episodes_per_asset_day"])),
                             n_boot=n_boot)})
    return pd.DataFrame(rows)


def build_all_cis(run_root: str | Path, datasets: list[str], *,
                  n_boot: int = DEFAULT_BOOT, out_dir: str | Path | None = None
                  ) -> pd.DataFrame:
    """Concatenate every dataset's CIs; optionally write ``final_cis.csv``."""
    frames = [dataset_cis(run_root, ds, n_boot=n_boot) for ds in datasets]
    frames = [f for f in frames if not f.empty]
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if out_dir is not None and not out.empty:
        out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
        out.to_csv(out_dir / "final_cis.csv", index=False)
    return out
