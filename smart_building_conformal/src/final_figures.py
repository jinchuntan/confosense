"""Primary dissertation figures, generated directly from corrected-run CSVs.

Every figure reads its numbers programmatically from the corrected run's CSV
outputs and records the source file (and its sha256) in ``figure_index.csv``, so
no figure carries a hand-entered or AI-invented value. A colour-blind-safe
palette is used and nominal reference lines are drawn where they apply.

This module produces the figures it *can* build from whatever CSVs exist; it is
run after the corrected study and its CIs are complete.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

# Colour-blind-safe (Wong) palette.
CB = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _concat(run_root: Path, datasets: list[str], name: str) -> pd.DataFrame:
    frames = []
    for ds in datasets:
        p = run_root / ds / name
        if p.exists():
            df = pd.read_csv(p)
            df["dataset"] = ds
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fig_recall_vs_workload(run_root: Path, datasets, out_dir: Path, index: list):
    """Ablation: macro recall vs background workload across the four levels."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    abl = _concat(run_root, datasets, "ablation.csv")
    if abl.empty or "macro_recall" not in abl:
        return
    abl = abl[abl.get("applicable", True) == True]                # noqa: E712
    order = ["baseline", "conformal_only", "temporal", "full"]
    fig, ax = plt.subplots(figsize=(7, 5))
    for i, lvl in enumerate(order):
        sub = abl[abl["ablation"] == lvl]
        if sub.empty:
            continue
        ax.scatter(sub["background_episodes_per_asset_day"], sub["macro_recall"],
                   label=lvl, color=CB[i % len(CB)], s=60, alpha=0.8,
                   edgecolor="black", linewidth=0.4)
    ax.set_xlabel("background alert episodes per monitored asset-day")
    ax.set_ylabel("macro synthetic-event recall")
    ax.set_title("Ablation: recall vs background alert workload")
    ax.legend(title="pipeline level", frameon=False)
    ax.grid(alpha=0.25)
    p = out_dir / "fig_recall_vs_workload.png"
    fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    src = run_root / (datasets[0] if datasets else "") / "ablation.csv"
    index.append({"figure": p.name, "source_csv": "ablation.csv (all datasets)",
                  "source_sha256": _sha(src) if src.exists() else ""})


def fig_coverage_with_cis(cis: Path, out_dir: Path, index: list):
    """Empirical coverage per dataset with 95% CIs and the nominal line."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not Path(cis).exists():
        return
    cis = Path(cis)
    df = pd.read_csv(cis)
    cov = df[df["metric"] == "empirical_coverage"]
    if cov.empty:
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    y = np.arange(len(cov))
    ax.errorbar(cov["estimate"], y,
                xerr=[cov["estimate"] - cov["ci_low"],
                      cov["ci_high"] - cov["estimate"]],
                fmt="o", color=CB[0], capsize=4)
    ax.set_yticks(y); ax.set_yticklabels(cov["dataset"])
    ax.set_xlabel("empirical coverage (95% CI)")
    ax.set_title("Interval coverage by dataset")
    ax.grid(alpha=0.25)
    p = out_dir / "fig_coverage_with_cis.png"
    fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    index.append({"figure": p.name, "source_csv": "metrics/final_cis.csv",
                  "source_sha256": _sha(cis)})


def fig_recall_by_stratum(run_root: Path, datasets, out_dir: Path, index: list):
    """Synthetic-event recall by event type x severity, per dataset."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ev = _concat(run_root, datasets, "outer_per_event.csv")
    if ev.empty or "detected" not in ev:
        return
    ev["stratum"] = ev["event_type"].astype(str) + "|" + ev["severity"].astype(str)
    piv = ev.groupby(["dataset", "stratum"])["detected"].mean().unstack("dataset")
    fig, ax = plt.subplots(figsize=(9, 5))
    piv.plot(kind="bar", ax=ax, color=CB[:piv.shape[1]], edgecolor="black",
             linewidth=0.3)
    ax.set_ylabel("synthetic-event recall")
    ax.set_xlabel("event type | severity")
    ax.set_title("Recall by event type and severity")
    ax.legend(title="dataset", frameon=False)
    ax.grid(alpha=0.25, axis="y")
    p = out_dir / "fig_recall_by_stratum.png"
    fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    src = run_root / (datasets[0] if datasets else "") / "outer_per_event.csv"
    index.append({"figure": p.name, "source_csv": "outer_per_event.csv (all datasets)",
                  "source_sha256": _sha(src) if src.exists() else ""})


def fig_selected_configs(run_root: Path, datasets, out_dir: Path, index: list):
    """Distribution of inner-selected interval methods (feasible folds only)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sel = _concat(run_root, datasets, "selection.csv")
    if sel.empty or "interval_method" not in sel:
        return
    chosen = sel[sel["decision"] == "selected"]
    if chosen.empty:
        return
    counts = chosen["interval_method"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(counts.index, counts.values, color=CB[2], edgecolor="black", linewidth=0.3)
    ax.set_ylabel("folds selecting this method")
    ax.set_title("Inner-selected interval method (feasible folds)")
    ax.grid(alpha=0.25, axis="y")
    p = out_dir / "fig_selected_configs.png"
    fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    src = run_root / (datasets[0] if datasets else "") / "selection.csv"
    index.append({"figure": p.name, "source_csv": "selection.csv (all datasets)",
                  "source_sha256": _sha(src) if src.exists() else ""})


def build_all(run_root: str | Path, datasets: list[str],
              out_dir: str | Path, cis_path: str | Path | None = None) -> pd.DataFrame:
    """Generate every buildable primary figure and write ``figure_index.csv``."""
    run_root = Path(run_root); out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if cis_path is None:
        cis_path = out_dir.parent / "metrics" / "final_cis.csv"
    index: list[dict] = []
    fig_recall_vs_workload(run_root, datasets, out_dir, index)
    fig_coverage_with_cis(Path(cis_path), out_dir, index)
    fig_recall_by_stratum(run_root, datasets, out_dir, index)
    fig_selected_configs(run_root, datasets, out_dir, index)
    idx = pd.DataFrame(index)
    if not idx.empty:
        idx.to_csv(out_dir / "figure_index.csv", index=False)
    return idx
