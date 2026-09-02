"""Paired inference for the robustness extension (amendment 003).

Every contrast is **paired within a unit** (dataset × fold × seed shares its
folds, pipeline and fault windows across cells), seeds are aggregated before
inference, and the bootstrap resamples the correct independent unit (BDG2 would
be buildings, but robustness cells aggregate a whole unit's groups, so the
independent unit here is the dataset-fold; datasets with 3 folds report
descriptive values with ``NA — insufficient independent groups``). Holm's
procedure is applied within each dataset's primary-endpoint family, as
predeclared. The bootstrap generator seed is fixed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BOOT_SEED = 20240601
N_BOOT = 2000
PRIMARY_DELTAS = ["delta_coverage_during_vs_pre", "background_per_asset_day"]


def _load_cells(run_root: str | Path, datasets: list[str]) -> pd.DataFrame:
    frames = []
    for ds in datasets:
        p = Path(run_root) / ds / "robustness_cells.csv"
        if p.exists():
            df = pd.read_csv(p)
            df["dataset"] = ds
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _paired_delta(cells: pd.DataFrame, cell_name: str, ref_name: str,
                  value: str) -> pd.DataFrame:
    """Within-unit difference cell − reference, seed-aggregated to fold level."""
    key = ["dataset", "outer_fold", "seed"]
    a = cells[cells["cell"] == cell_name].set_index(key)[value]
    b = cells[cells["cell"] == ref_name].set_index(key)[value]
    d = (a - b).dropna().rename("delta").reset_index()
    if d.empty:
        return d
    return d.groupby(["dataset", "outer_fold"])["delta"].mean().reset_index()


def _boot_ci(vals: np.ndarray, rng) -> tuple:
    if len(vals) < 4:
        return (np.nan, np.nan, "NA_insufficient_independent_groups(<4)")
    reps = [np.mean(vals[rng.integers(0, len(vals), len(vals))])
            for _ in range(N_BOOT)]
    return (float(np.percentile(reps, 2.5)), float(np.percentile(reps, 97.5)),
            "paired_percentile_bootstrap")


def holm(pvals: list[float]) -> list[float]:
    """Holm step-down adjusted p-values (monotone)."""
    order = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * pvals[idx])
        adj[idx] = min(1.0, running)
    return adj.tolist()


def _sign_p(vals: np.ndarray) -> float:
    """Two-sided sign-flip permutation p for mean != 0 (exact enough at n<=15)."""
    n = len(vals)
    if n < 3:
        return np.nan
    obs = abs(np.mean(vals))
    rng = np.random.default_rng(BOOT_SEED + 1)
    reps = 4096
    cnt = 0
    for _ in range(reps):
        signs = rng.choice([-1.0, 1.0], size=n)
        if abs(np.mean(vals * signs)) >= obs - 1e-12:
            cnt += 1
    return cnt / reps


def build(run_root: str | Path, datasets: list[str],
          out_dir: str | Path) -> pd.DataFrame:
    """Write ``robustness_effects.csv`` with paired deltas, CIs and Holm p."""
    cells = _load_cells(run_root, datasets)
    if cells.empty:
        return pd.DataFrame()
    rng = np.random.default_rng(BOOT_SEED)
    rows = []
    fault_cells = sorted(c for c in cells["cell"].unique()
                         if cells.loc[cells["cell"] == c, "family"].iloc[0]
                         == "fault" and c != "zero_control")
    contrasts = ([(c, "clean", "coverage_during") for c in fault_cells]
                 + [(c, "clean", "background_per_asset_day") for c in fault_cells]
                 + [("contam@0.05", "contam_clean_ref", "coverage_all"),
                    ("contam@0.10", "contam_clean_ref", "coverage_all"),
                    ("contam@0.05", "contam_clean_ref", "mean_width"),
                    ("contam@0.10", "contam_clean_ref", "mean_width"),
                    ("recovery_periodic", "recovery_static", "coverage_post"),
                    ("recovery_rolling", "recovery_static", "coverage_post")])
    for cell_name, ref, value in contrasts:
        d = _paired_delta(cells, cell_name, ref, value)
        if d.empty:
            continue
        pooled = d["delta"].to_numpy(float)
        lo, hi, meth = _boot_ci(pooled, rng)
        rows.append({"contrast": f"{cell_name} - {ref}", "endpoint": value,
                     "scope": "pooled", "n_units": len(pooled),
                     "delta_mean": round(float(np.mean(pooled)), 4),
                     "ci_low": (round(lo, 4) if np.isfinite(lo) else "NA"),
                     "ci_high": (round(hi, 4) if np.isfinite(hi) else "NA"),
                     "p_raw": _sign_p(pooled), "method": meth})
        for ds in datasets:
            sub = d[d["dataset"] == ds]["delta"].to_numpy(float)
            if len(sub) == 0:
                continue
            rows.append({"contrast": f"{cell_name} - {ref}", "endpoint": value,
                         "scope": ds, "n_units": len(sub),
                         "delta_mean": round(float(np.mean(sub)), 4),
                         "ci_low": "NA", "ci_high": "NA",
                         "p_raw": _sign_p(sub),
                         "method": "descriptive(n=3 folds)"})
    out = pd.DataFrame(rows)
    # Holm within each dataset scope over the primary-endpoint family
    out["p_holm"] = np.nan
    for scope, sub in out.groupby("scope"):
        fam = sub[sub["endpoint"].isin(["coverage_during",
                                        "background_per_asset_day"])]
        idx = fam.index[fam["p_raw"].notna()]
        if len(idx):
            out.loc[idx, "p_holm"] = holm(out.loc[idx, "p_raw"].tolist())
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / "robustness_effects.csv", index=False)
    return out


def point_summary(run_root: str | Path, datasets: list[str],
                  out_dir: str | Path) -> pd.DataFrame:
    """Point MAE/RMSE by dataset/model, paired vs persistence per unit."""
    frames = []
    for ds in datasets:
        p = Path(run_root) / ds / "point_accuracy.csv"
        if p.exists():
            df = pd.read_csv(p)
            df["dataset"] = ds
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    pa = pd.concat(frames, ignore_index=True)
    key = ["dataset", "outer_fold", "seed"]
    piv = pa.pivot_table(index=key, columns="model", values="mae")
    piv = piv.groupby(level=["dataset", "outer_fold"]).mean()
    rows = []
    for ds, sub in piv.groupby(level="dataset"):
        if "xgboost" in sub and "persistence" in sub:
            d = (sub["xgboost"] - sub["persistence"]).dropna()
            rows.append({"dataset": ds,
                         "mae_persistence": round(float(sub["persistence"].mean()), 4),
                         "mae_xgboost": round(float(sub["xgboost"].mean()), 4),
                         "paired_delta_xgb_minus_pers":
                             round(float(d.mean()), 4) if len(d) else np.nan,
                         "n_folds": len(d),
                         "note": "negative delta = xgboost better; n=3 folds, descriptive"})
    out = pd.DataFrame(rows)
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / "point_accuracy_summary.csv", index=False)
    return out
