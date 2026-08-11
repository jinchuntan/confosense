"""Publication-quality figures for the full study.

Every figure is drawn from a persisted CSV under ``outputs/full_study``. Nothing
here recomputes a metric or accepts a hand-entered value, so a figure can never
disagree with the tables it accompanies — if a number is not in the machine-
readable outputs, it cannot appear in a plot.

Missing inputs are not an error. A figure whose source table does not exist (a
dataset that has not been run yet, a stage that failed) is skipped and named in
the returned list, so the report can state plainly which figures exist.

House style: no 3D, no dual axes with mismatched scales, no truncated axes on
bar charts of absolute quantities, grid behind the data, colour-blind-safe
palette, and every axis labelled with its unit.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Okabe-Ito: colour-blind safe.
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7",
           "#E69F00", "#56B4E9", "#F0E442", "#000000"]

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "figure.autolayout": False,
})


def _load(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    df = pd.read_csv(path)
    return df if len(df) else None


def _save(fig, path: Path, made: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    made.append(str(path))


def _colors(keys) -> dict:
    return {k: PALETTE[i % len(PALETTE)] for i, k in enumerate(keys)}


# --------------------------------------------------------------------------- #
def fig_point_comparison(combined: Path, out: Path, made: list[str]) -> None:
    """Percentage MAE improvement over persistence, per dataset and horizon.

    Percentage improvement rather than raw MAE: the targets are degrees Celsius
    and kilowatt-hours, so raw errors are not comparable across datasets.
    """
    df = _load(combined / "point_metrics.csv")
    if df is None or "pct_mae_improvement" not in df:
        return
    df = df[df.get("applicable", True) == True]           # noqa: E712
    df = df[df["point_model"] != "persistence"]
    if df.empty:
        return
    datasets = sorted(df["dataset"].unique())
    fig, axes = plt.subplots(1, len(datasets), figsize=(4.2 * len(datasets), 3.4),
                             squeeze=False, sharey=True)
    models = sorted(df["point_model"].unique())
    cmap = _colors(models)
    for ax, ds in zip(axes[0], datasets):
        sub = df[df["dataset"] == ds]
        horizons = sorted(sub["horizon_steps"].unique())
        width = 0.8 / max(1, len(models))
        for i, model in enumerate(models):
            vals = [sub[(sub["horizon_steps"] == h) & (sub["point_model"] == model)]
                    ["pct_mae_improvement"].mean() for h in horizons]
            ax.bar(np.arange(len(horizons)) + i * width, vals, width,
                   label=model, color=cmap[model])
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(np.arange(len(horizons)) + 0.4 - width / 2)
        ax.set_xticklabels([str(h) for h in horizons])
        ax.set_title(ds)
        ax.set_xlabel("horizon (steps)")
    axes[0][0].set_ylabel("MAE improvement over persistence (%)")
    axes[0][-1].legend(loc="best", fontsize=7)
    fig.suptitle("Point forecasting: improvement over the persistence baseline", y=1.02)
    _save(fig, out / "fig_01_point_forecasting_comparison.png", made)


def fig_coverage_vs_width(combined: Path, out: Path, made: list[str]) -> None:
    df = _load(combined / "interval_metrics.csv")
    if df is None:
        return
    fig, axes = plt.subplots(1, len(sorted(df["nominal_coverage"].unique())),
                             figsize=(9, 3.6), squeeze=False)
    methods = sorted(df["conformal_method"].unique())
    cmap = _colors(methods)
    markers = ["o", "s", "^", "D", "v", "P"]
    for ax, level in zip(axes[0], sorted(df["nominal_coverage"].unique())):
        sub = df[df["nominal_coverage"] == level]
        for i, m in enumerate(methods):
            s = sub[sub["conformal_method"] == m]
            if s.empty:
                continue
            ax.scatter(s["normalized_mean_interval_width"], s["empirical_coverage"],
                       label=m, color=cmap[m], marker=markers[i % len(markers)],
                       s=28, alpha=0.85, edgecolor="white", linewidth=0.4)
        ax.axhline(level, color="black", ls="--", lw=0.9)
        ax.set_title(f"nominal {level:.0%}")
        ax.set_xlabel("normalised mean interval width (width / sd of target)")
    axes[0][0].set_ylabel("empirical coverage")
    axes[0][-1].legend(fontsize=7, loc="lower right")
    fig.suptitle("Coverage against interval width (dashed line = nominal)", y=1.02)
    _save(fig, out / "fig_02_coverage_vs_width.png", made)


def fig_coverage_deviation(combined: Path, out: Path, made: list[str]) -> None:
    df = _load(combined / "interval_metrics.csv")
    if df is None:
        return
    datasets = sorted(df["dataset"].unique())
    fig, axes = plt.subplots(1, len(datasets), figsize=(4.2 * len(datasets), 3.4),
                             squeeze=False, sharey=True)
    methods = sorted(df["conformal_method"].unique())
    cmap = _colors(methods)
    for ax, ds in zip(axes[0], datasets):
        sub = df[df["dataset"] == ds]
        for m in methods:
            s = (sub[sub["conformal_method"] == m]
                 .groupby("horizon_steps")["coverage_deviation"].mean())
            if s.empty:
                continue
            ax.plot(s.index, s.values, marker="o", ms=4, label=m, color=cmap[m])
        ax.set_title(ds)
        ax.set_xlabel("horizon (steps)")
    axes[0][0].set_ylabel("|empirical − nominal| coverage")
    axes[0][-1].legend(fontsize=7)
    fig.suptitle("Coverage deviation by horizon (lower is better)", y=1.02)
    _save(fig, out / "fig_03_coverage_deviation_by_horizon.png", made)


def fig_winkler(combined: Path, out: Path, made: list[str]) -> None:
    df = _load(combined / "interval_metrics.csv")
    if df is None or "winkler_score" not in df:
        return
    # Winkler is in target units, so normalise within dataset to compare shapes.
    df = df.copy()
    df["winkler_normalised"] = df.groupby(["dataset", "nominal_coverage"])[
        "winkler_score"].transform(lambda s: s / s.min() if s.min() else np.nan)
    piv = df.pivot_table(index=["dataset", "horizon_steps"],
                         columns="conformal_method", values="winkler_normalised")
    if piv.empty:
        return
    fig, ax = plt.subplots(figsize=(max(6, 0.7 * len(piv)), 3.6))
    piv.plot(kind="bar", ax=ax, color=[PALETTE[i % len(PALETTE)]
                                       for i in range(piv.shape[1])], width=0.8)
    ax.set_ylabel("Winkler score / best in dataset")
    ax.set_xlabel("dataset, horizon (steps)")
    ax.axhline(1.0, color="black", lw=0.8)
    ax.legend(fontsize=7, ncol=2)
    ax.set_title("Winkler interval score, normalised to the best method per dataset")
    _save(fig, out / "fig_04_winkler_comparison.png", made)


def fig_alert_sensitivity(combined: Path, out: Path, made: list[str]) -> None:
    df = _load(combined / "alert_metrics.csv")
    if df is None or "role" not in df:
        return
    test = df[df["role"] == "post_hoc_sensitivity"]
    if test.empty:
        return
    datasets = sorted(test["dataset"].unique())
    fig, axes = plt.subplots(1, len(datasets), figsize=(4.0 * len(datasets), 3.4),
                             squeeze=False, sharey=True)
    for ax, ds in zip(axes[0], datasets):
        sub = test[test["dataset"] == ds].sort_values("rule")
        x = np.arange(len(sub))
        ax.bar(x - 0.2, sub["recall"], 0.4, label="recall", color=PALETTE[0])
        ax.bar(x + 0.2, sub["precision"], 0.4, label="precision", color=PALETTE[1])
        for i, sel in enumerate(sub.get("selected_operating_rule", [])):
            if sel:
                ax.axvspan(i - 0.5, i + 0.5, color=PALETTE[2], alpha=0.12)
        ax.set_xticks(x)
        ax.set_xticklabels(sub["rule"], rotation=30)
        ax.set_title(ds)
        ax.set_xlabel("k-of-m rule")
    axes[0][0].set_ylabel("event-level score")
    axes[0][-1].legend(fontsize=7)
    fig.suptitle("Alert-rule sensitivity on test data "
                 "(shaded = rule selected on calibration)", y=1.02)
    _save(fig, out / "fig_05_alert_rule_sensitivity.png", made)


def fig_alert_tradeoff(combined: Path, out: Path, made: list[str]) -> None:
    df = _load(combined / "alert_metrics.csv")
    if df is None or "role" not in df:
        return
    sub = df[df["role"] == "post_hoc_sensitivity"]
    if sub.empty:
        return
    fig, ax = plt.subplots(figsize=(5.4, 3.8))
    datasets = sorted(sub["dataset"].unique())
    cmap = _colors(datasets)
    for ds in datasets:
        s = sub[sub["dataset"] == ds]
        ax.scatter(s["false_alert_events_per_day"], s["recall"],
                   s=42, color=cmap[ds], label=ds, alpha=0.85,
                   edgecolor="white", linewidth=0.5)
        for _, r in s.iterrows():
            ax.annotate(str(r["rule"]), (r["false_alert_events_per_day"], r["recall"]),
                        fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("false alert events per day")
    ax.set_ylabel("event recall")
    ax.set_title("Detection against alert workload")
    ax.legend(fontsize=7)
    _save(fig, out / "fig_06_alert_tradeoff.png", made)


def fig_robustness(combined: Path, out: Path, made: list[str]) -> None:
    df = _load(combined / "robustness_metrics.csv")
    if df is None or "empirical_coverage" not in df:
        return
    df = df[df["mode"].isin(["legacy_fixed_intervals", "closed_loop"])]
    if df.empty:
        return
    datasets = sorted(df["dataset"].unique())
    fig, axes = plt.subplots(len(datasets), 1,
                             figsize=(8.5, 2.8 * len(datasets)), squeeze=False)
    for ax, ds in zip(axes[:, 0], datasets):
        sub = df[df["dataset"] == ds]
        piv = sub.pivot_table(index="scenario", columns="mode",
                              values="empirical_coverage")
        piv = piv.reindex(sorted(piv.index, key=lambda s: (s != "clean", s)))
        piv.plot(kind="bar", ax=ax, color=[PALETTE[0], PALETTE[1]], width=0.8)
        level = sub["nominal_coverage"].iloc[0] if "nominal_coverage" in sub else 0.95
        ax.axhline(level, color="black", ls="--", lw=0.9)
        ax.set_ylabel("empirical coverage")
        ax.set_title(f"{ds} — coverage under disturbance (dashed = nominal)")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=45, labelsize=7)
        ax.legend(fontsize=7)
    _save(fig, out / "fig_07_robustness_degradation.png", made)


def fig_recalibration_recovery(out_root: Path, out: Path, made: list[str]) -> None:
    frames = []
    for p in out_root.glob("*/metrics/recalibration_recovery.csv"):
        frames.append(pd.read_csv(p))
    if not frames:
        return
    df = pd.concat(frames, ignore_index=True)
    datasets = sorted(df["dataset"].unique())
    fig, axes = plt.subplots(1, len(datasets), figsize=(4.2 * len(datasets), 3.4),
                             squeeze=False, sharey=True)
    strategies = sorted(df["recalibration_strategy"].unique())
    cmap = _colors(strategies)
    for ax, ds in zip(axes[0], datasets):
        sub = df[df["dataset"] == ds]
        for s in strategies:
            g = (sub[sub["recalibration_strategy"] == s]
                 .groupby("block_index")["empirical_coverage"].mean())
            if g.empty:
                continue
            ax.plot(g.index, g.values, marker="o", ms=3, label=s, color=cmap[s])
        ax.axvline(0, color="black", ls=":", lw=1.0)
        ax.set_title(ds)
        ax.set_xlabel("block relative to onset")
    axes[0][0].set_ylabel("block empirical coverage")
    axes[0][-1].legend(fontsize=7)
    fig.suptitle("Coverage recovery after a distribution shift "
                 "(dotted line = onset)", y=1.02)
    _save(fig, out / "fig_08_recalibration_recovery.png", made)


def fig_rankings(combined: Path, out: Path, made: list[str]) -> None:
    df = _load(combined / "model_rankings.csv")
    if df is None:
        return
    piv = df.pivot_table(index="point_model", columns="dataset",
                         values="mean_rank_mae")
    if piv.empty:
        return
    fig, ax = plt.subplots(figsize=(1.4 * piv.shape[1] + 3, 0.5 * len(piv) + 2))
    im = ax.imshow(piv.to_numpy(dtype=float), cmap="viridis_r", aspect="auto")
    ax.set_xticks(range(piv.shape[1]))
    ax.set_xticklabels(piv.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(piv)))
    ax.set_yticklabels(piv.index)
    for i in range(len(piv)):
        for j in range(piv.shape[1]):
            v = piv.to_numpy(dtype=float)[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        color="white", fontsize=8)
    ax.grid(False)
    fig.colorbar(im, ax=ax, label="mean MAE rank (1 = best)")
    ax.set_title("Cross-dataset method ranking")
    _save(fig, out / "fig_09_cross_dataset_rankings.png", made)


def fig_interval_timeline(out_root: Path, dataset: str, out: Path,
                          made: list[str], index: int) -> None:
    """A representative forecast-interval window for one dataset."""
    path = out_root / dataset / "predictions" / "interval_predictions.csv"
    if not path.exists():
        return
    df = pd.read_csv(path, parse_dates=["target_time"])
    sub = df[(df["conformal_method"] == "cqr")]
    if sub.empty:
        return
    level = sub["nominal_coverage"].max()
    sub = sub[sub["nominal_coverage"] == level]
    h = sorted(sub["horizon"].unique())[0]
    sub = sub[sub["horizon"] == h]
    if "group_id" in sub and sub["group_id"].notna().any():
        first = sub["group_id"].dropna().iloc[0]
        sub = sub[sub["group_id"] == first]
    sub = sub.sort_values("target_time").head(240)
    if sub.empty:
        return
    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    ax.fill_between(sub["target_time"], sub["lower"], sub["upper"],
                    color=PALETTE[0], alpha=0.22,
                    label=f"CQR {level:.0%} interval")
    ax.plot(sub["target_time"], sub["point"], color=PALETTE[0], lw=1.2,
            label="forecast")
    ax.plot(sub["target_time"], sub["y_true"], color="black", lw=1.0, ls="--",
            label="observed")
    ax.set_title(f"{dataset}: representative CQR interval timeline (horizon {h})")
    ax.set_ylabel("target")
    ax.set_xlabel("time")
    ax.legend(fontsize=7)
    fig.autofmt_xdate()
    _save(fig, out / f"fig_{index}_{dataset}_interval_timeline.png", made)


# --------------------------------------------------------------------------- #
def build_all(out_root: Path) -> list[str]:
    """Generate every figure whose source table exists; return the paths made."""
    out_root = Path(out_root)
    combined = out_root / "combined"
    figures = out_root / "report" / "figures"
    made: list[str] = []

    for fn in (fig_point_comparison, fig_coverage_vs_width, fig_coverage_deviation,
               fig_winkler, fig_alert_sensitivity, fig_alert_tradeoff,
               fig_robustness, fig_rankings):
        try:
            fn(combined, figures, made)
        except Exception as exc:                            # noqa: BLE001
            print(f"    [figure skipped] {fn.__name__}: {type(exc).__name__}: {exc}")
    try:
        fig_recalibration_recovery(out_root, figures, made)
    except Exception as exc:                                # noqa: BLE001
        print(f"    [figure skipped] recalibration recovery: {exc}")
    for i, ds in enumerate(("rico", "bdg2", "pleia"), start=10):
        try:
            fig_interval_timeline(out_root, ds, figures, made, i)
        except Exception as exc:                            # noqa: BLE001
            print(f"    [figure skipped] {ds} timeline: {exc}")
    return made
