"""The ten primary dissertation figures, generated only from corrected CSVs.

Each figure is written as PNG **and** SVG with a ``.sha256`` sidecar recording
the hashes of the rendered files and of every source CSV, so a figure can be
traced to the exact data that produced it. Colour-blind-safe palette; CIs and
nominal reference lines where they apply; no hand-entered value anywhere.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

CB = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9",
      "#F0E442", "#000000"]
DS_ORDER = ["pleia", "pleia_energy", "rico", "bdg2"]


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _save(fig, out_dir: Path, name: str, sources: list[Path], index: list):
    png, svg = out_dir / f"{name}.png", out_dir / f"{name}.svg"
    fig.tight_layout()
    fig.savefig(png, dpi=150)
    fig.savefig(svg)
    side = out_dir / f"{name}.sha256"
    lines = [f"{_sha(png)}  {png.name}", f"{_sha(svg)}  {svg.name}"]
    for s in sources:
        if Path(s).exists():
            lines.append(f"{_sha(s)}  source:{Path(s).as_posix()}")
    side.write_text("\n".join(lines) + "\n", encoding="utf-8")
    index.append({"figure": name, "png": png.name, "svg": svg.name,
                  "sources": ";".join(Path(s).as_posix() for s in sources),
                  "source_sha256": ";".join(_sha(s)[:16] for s in sources
                                            if Path(s).exists())})
    import matplotlib.pyplot as plt
    plt.close(fig)


def build_all(metrics_dir, core_run, ext_run, out_dir) -> pd.DataFrame:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics_dir, out_dir = Path(metrics_dir), Path(out_dir)
    core_run, ext_run = Path(core_run), Path(ext_run)
    out_dir.mkdir(parents=True, exist_ok=True)
    index: list[dict] = []

    # 1 — point forecasting (extension point accuracy) ---------------------
    src = metrics_dir / "point_accuracy_summary.csv"
    if src.exists():
        df = pd.read_csv(src)
        fig, ax = plt.subplots(figsize=(7, 4))
        x = np.arange(len(df))
        ax.bar(x - 0.2, df["mae_persistence"], 0.4, label="persistence",
               color=CB[0], edgecolor="black", linewidth=0.3)
        ax.bar(x + 0.2, df["mae_xgboost"], 0.4, label="xgboost (tuned)",
               color=CB[1], edgecolor="black", linewidth=0.3)
        ax.set_xticks(x); ax.set_xticklabels(df["dataset"])
        ax.set_ylabel("clean outer-test MAE (target units)")
        ax.set_title("Point forecasting: MAE by dataset (3 folds, seed-aggregated)")
        ax.legend(frameon=False); ax.grid(alpha=0.25, axis="y")
        _save(fig, out_dir, "fig01_point_forecasting", [src], index)

    # 2 — prediction intervals vs own nominal ------------------------------
    src = metrics_dir / "NOMINAL_COVERAGE_AUDIT.csv"
    if src.exists():
        df = pd.read_csv(src)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for i, ds in enumerate(DS_ORDER):
            sub = df[df["dataset"] == ds]
            ax.scatter(sub["selected_nominal"] + (i - 1.5) * 0.002,
                       sub["empirical_coverage"], s=28, alpha=0.75,
                       color=CB[i], label=ds, edgecolor="black", linewidth=0.3)
        lim = np.linspace(0.9, 1.0, 10)
        ax.plot(lim, lim, "k--", linewidth=1, label="nominal = empirical")
        ax.set_xlabel("selected nominal level"); ax.set_ylabel("empirical coverage")
        ax.set_title("Interval coverage vs own selected nominal (all 60 units)")
        ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.25)
        _save(fig, out_dir, "fig02_interval_coverage", [src], index)

    # 3 — method-selection frequency ---------------------------------------
    frames = []
    for ds in DS_ORDER:
        p = core_run / ds / "selection.csv"
        if p.exists():
            d = pd.read_csv(p); d["dataset"] = ds; frames.append(d)
    if frames:
        sel = pd.concat(frames)
        chosen = sel[sel["decision"] == "selected"]
        fig, ax = plt.subplots(figsize=(7, 4))
        if len(chosen):
            counts = chosen.groupby(["interval_method"]).size()
            ax.bar(counts.index, counts.values, color=CB[2], edgecolor="black",
                   linewidth=0.3)
        ax.set_ylabel("feasible units selecting method")
        ax.set_title("Inner-selected interval method (12 feasible units)")
        ax.grid(alpha=0.25, axis="y")
        srcs = [core_run / ds / "selection.csv" for ds in DS_ORDER]
        _save(fig, out_dir, "fig03_method_selection", srcs, index)

    # 4 — paired ablation effects ------------------------------------------
    src = metrics_dir / "PAIRED_ABLATION_EFFECTS.csv"
    if src.exists():
        df = pd.read_csv(src)
        pooled = df[df["unit"].str.contains("pooled")]
        fig, ax = plt.subplots(figsize=(8, 4))
        y = np.arange(len(pooled))
        lo = pooled["workload_diff_ci95"].str.extract(r"\[(-?\d+\.?\d*)")[0].astype(float)
        hi = pooled["workload_diff_ci95"].str.extract(r", (-?\d+\.?\d*)\]")[0].astype(float)
        ax.errorbar(pooled["workload_diff_mean"], y,
                    xerr=[pooled["workload_diff_mean"] - lo,
                          hi - pooled["workload_diff_mean"]],
                    fmt="o", color=CB[3], capsize=4)
        ax.axvline(0, color="k", linewidth=1)
        ax.set_yticks(y); ax.set_yticklabels(pooled["contrast"])
        ax.set_xlabel("paired Δ background episodes / asset-day [95% CI]")
        ax.set_title("Paired ablation effects (12 units; exploratory)")
        ax.grid(alpha=0.25, axis="x")
        _save(fig, out_dir, "fig04_paired_ablation", [src], index)

    # 5 — recall vs workload trade-off --------------------------------------
    frames = []
    for ds in DS_ORDER:
        p = core_run / ds / "ablation.csv"
        if p.exists():
            d = pd.read_csv(p); d["dataset"] = ds; frames.append(d)
    if frames:
        abl = pd.concat(frames)
        abl = abl[abl["applicable"] == True]                     # noqa: E712
        fig, ax = plt.subplots(figsize=(7, 5))
        for i, lvl in enumerate(["baseline", "conformal_only", "temporal", "full"]):
            sub = abl[abl["ablation"] == lvl]
            ax.scatter(sub["background_episodes_per_asset_day"], sub["macro_recall"],
                       s=45, alpha=0.75, color=CB[i], label=lvl,
                       edgecolor="black", linewidth=0.3)
        ax.set_xlabel("background alert episodes / asset-day")
        ax.set_ylabel("macro synthetic-event recall")
        ax.set_title("Recall vs background workload across ablation levels")
        ax.legend(frameon=False); ax.grid(alpha=0.25)
        srcs = [core_run / ds / "ablation.csv" for ds in DS_ORDER]
        _save(fig, out_dir, "fig05_recall_workload", srcs, index)

    # 6 — alert reliability, three-tier corrected --------------------------
    src = metrics_dir / "final_cis_corrected.csv"
    if src.exists():
        df = pd.read_csv(src)
        rec = df[df["metric"] == "macro_event_recall_unitmean"]
        fig, ax = plt.subplots(figsize=(8, 4))
        width = 0.35
        for j, scope in enumerate(["all_60_units", "feasible_only"]):
            sub = rec[rec["scope"] == scope].set_index("dataset").reindex(DS_ORDER)
            ax.bar(np.arange(len(DS_ORDER)) + (j - 0.5) * width,
                   sub["estimate"], width, label=scope, color=CB[j],
                   edgecolor="black", linewidth=0.3)
        ax.set_xticks(range(len(DS_ORDER))); ax.set_xticklabels(DS_ORDER)
        ax.set_ylabel("event recall (unit-mean)")
        ax.set_title("Alert reliability: diagnostic vs feasible-only (corrected)")
        ax.legend(frameon=False); ax.grid(alpha=0.25, axis="y")
        _save(fig, out_dir, "fig06_alert_reliability", [src], index)

    # 7 — closed-loop fault absorption -------------------------------------
    frames = []
    for ds in DS_ORDER:
        p = ext_run / ds / "robustness_cells.csv"
        if p.exists():
            d = pd.read_csv(p); d["dataset"] = ds; frames.append(d)
    cells = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not cells.empty:
        f = cells[cells["family"] == "fault"]
        piv = (f.groupby(["dataset", "cell"])["delta_coverage_during_vs_pre"]
               .mean().unstack("dataset"))
        fig, ax = plt.subplots(figsize=(9, 5))
        piv.plot(kind="bar", ax=ax, color=CB[:piv.shape[1]], edgecolor="black",
                 linewidth=0.3)
        ax.set_ylabel("Δ coverage (during − pre), clean-truth reference")
        ax.set_title("Closed-loop fault absorption: coverage loss during faults")
        ax.legend(title="dataset", frameon=False, fontsize=8)
        ax.grid(alpha=0.25, axis="y")
        srcs = [ext_run / ds / "robustness_cells.csv" for ds in DS_ORDER]
        _save(fig, out_dir, "fig07_fault_absorption", srcs, index)

        # 8 — recalibration recovery ---------------------------------------
        r = cells[cells["family"] == "recovery"]
        if len(r):
            piv = (r.groupby(["dataset", "recal_policy"])["coverage_post"]
                   .mean().unstack("recal_policy"))
            fig, ax = plt.subplots(figsize=(8, 4.5))
            piv.plot(kind="bar", ax=ax, color=CB[:piv.shape[1]],
                     edgecolor="black", linewidth=0.3)
            ax.set_ylabel("post-fault coverage (clean truth)")
            ax.set_title("Recovery after a 2σ level-shift, by recalibration policy")
            ax.legend(title="policy", frameon=False); ax.grid(alpha=0.25, axis="y")
            _save(fig, out_dir, "fig08_recalibration_recovery", srcs, index)

        # 9 — calibration contamination ------------------------------------
        c = cells[cells["family"] == "contamination"]
        if len(c):
            piv = (c.groupby(["dataset", "cell"])["mean_width"].mean()
                   .unstack("cell"))
            fig, ax = plt.subplots(figsize=(8, 4.5))
            piv.plot(kind="bar", ax=ax, color=CB[:piv.shape[1]],
                     edgecolor="black", linewidth=0.3)
            ax.set_ylabel("mean interval width (target units)")
            ax.set_title("Calibration contamination inflates interval width")
            ax.legend(title="cell", frameon=False, fontsize=8)
            ax.grid(alpha=0.25, axis="y")
            _save(fig, out_dir, "fig09_contamination", srcs, index)

    # 10 — feasibility and abstention --------------------------------------
    src = metrics_dir / "OUTER_UNIT_LEDGER.csv"
    if src.exists():
        df = pd.read_csv(src)
        g = df.groupby("dataset")["operational_feasible"].agg(["sum", "count"])
        g = g.reindex(DS_ORDER)
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(g.index, g["count"], color="#cccccc", edgecolor="black",
               linewidth=0.3, label="units evaluated")
        ax.bar(g.index, g["sum"], color=CB[2], edgecolor="black",
               linewidth=0.3, label="feasible under frozen policy")
        ax.set_ylabel("evaluation units (5 seeds × 3 folds)")
        ax.set_title("Feasibility and abstention (no_feasible_configuration)")
        ax.legend(frameon=False); ax.grid(alpha=0.25, axis="y")
        _save(fig, out_dir, "fig10_feasibility", [src], index)

    idx = pd.DataFrame(index)
    if not idx.empty:
        idx.to_csv(out_dir / "figure_index_v2.csv", index=False)
    return idx
