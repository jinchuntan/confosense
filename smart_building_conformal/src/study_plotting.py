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


# Figure 9(a,b) layout constants. Every display string is mapped to the exact
# CSV value; the mapping is checked against the CSV before anything is drawn, so
# an internal name can never leak into a label and a renamed scenario fails loudly
# instead of vanishing from the plot.
_ROB_DATASETS = [
    ("pleia", "PLEIAData temperature"),
    ("pleia_energy", "PLEIAData energy"),
    ("rico", "RICO HVAC"),
    ("bdg2", "BDG2 electricity"),
]
_ROB_MODES = [
    ("legacy_fixed_intervals", "Fixed interval", PALETTE[0]),
    ("closed_loop", "Closed loop", PALETTE[1]),
]
_ROB_SCENARIOS = [
    ("clean", "Clean"),
    ("random_missing_5pct", "Random missing 5%"),
    ("random_missing_10pct", "Random missing 10%"),
    ("random_missing_20pct", "Random missing 20%"),
    ("block_missing_5pct", "Block missing 5%"),
    ("block_missing_10pct", "Block missing 10%"),
    ("dropout_5pct", "Communication dropout 5%"),
    ("stuck_5pct", "Stuck sensor 5%"),
    ("bias_0.5sd", "Sensor bias 0.5 SD"),
    ("bias_1.0sd", "Sensor bias 1 SD"),
    ("bias_2.0sd", "Sensor bias 2 SD"),
    ("level_shift_1.0sd", "Level shift 1 SD"),
    ("level_shift_2.0sd", "Level shift 2 SD"),
    ("drift_1.0sd", "Gradual drift 1 SD"),
    ("drift_2.0sd", "Gradual drift 2 SD"),
]
_ROB_NOMINAL = 0.95


def _robustness_subfigure(df: pd.DataFrame, value_col: str, coverage_label: str,
                          stem: str, out: Path, made: list[str]) -> int:
    """Draw one coverage definition as a 2x2 horizontal grouped-bar figure.

    One dataset per panel, fixed-interval against closed-loop, scenarios on the
    y-axis in the fixed logical order, coverage on the x-axis. Saves PNG and PDF.
    Returns the number of finite values actually plotted.
    """
    y = np.arange(len(_ROB_SCENARIOS))
    bar_h = 0.38
    scen_labels = [lab for _, lab in _ROB_SCENARIOS]
    plotted = 0

    with plt.rc_context({
        "font.size": 9.5, "axes.titlesize": 10.5, "axes.labelsize": 9.5,
        "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9.5,
    }):
        fig, axes = plt.subplots(2, 2, figsize=(6.6, 8.8), sharex=True, sharey=True,
                                 constrained_layout=True)
        for ax, (ds_key, ds_label) in zip(axes.ravel(), _ROB_DATASETS):
            sub = df[df["dataset"] == ds_key]
            for i, (mode_key, mode_label, color) in enumerate(_ROB_MODES):
                # First mode sits on the upper side of each scenario group.
                offset = (0.5 - i) * bar_h
                vals = []
                for scen_key, _ in _ROB_SCENARIOS:
                    rows = sub[(sub["mode"] == mode_key) & (sub["scenario"] == scen_key)]
                    if len(rows) > 1:
                        raise ValueError(
                            f"{ds_key}/{mode_key}/{scen_key}: {len(rows)} rows; "
                            "expected one (refusing to average silently)")
                    v = float(rows[value_col].iloc[0]) if len(rows) else np.nan
                    vals.append(v)
                    plotted += int(np.isfinite(v))
                ax.barh(y + offset, vals, height=bar_h, color=color,
                        label=mode_label, zorder=3)
            ax.axvline(_ROB_NOMINAL, color="black", ls="--", lw=0.9, zorder=2)
            ax.set_xlim(0.0, 1.05)
            ax.set_title(ds_label)
            ax.grid(axis="x", alpha=0.3)
            ax.grid(axis="y", visible=False)

        # Shared y ordering, set once on the shared axis; Clean at the top.
        axes[0, 0].set_yticks(y)
        axes[0, 0].set_yticklabels(scen_labels)
        axes[0, 0].invert_yaxis()

        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="outside upper center", ncol=2, frameon=False)
        fig.supxlabel(coverage_label)

        out.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "pdf"):
            path = out / f"{stem}.{ext}"
            fig.savefig(path, bbox_inches="tight")
            made.append(str(path))
        plt.close(fig)
    return plotted


def fig_robustness(combined: Path, out: Path, made: list[str]) -> None:
    """Figure 9(a) and 9(b): coverage under every disturbance, per dataset.

    Two quantities share the word "coverage" and must never appear on one axis,
    so they are drawn as two separate 2x2 figures:

    * **9(a) observed-signal coverage** (``empirical_coverage``) — does the
      interval contain the reading the sensor actually reported?
    * **9(b) clean-reference coverage** (``empirical_coverage_vs_clean_truth``) —
      does it contain the value the sensor *should* have reported?

    Reporting only the first makes a closed-loop run look healthy at exactly the
    moment the forecast has been captured by the fault, which is why the two are
    kept apart. Every value is read straight from ``robustness_metrics.csv`` and
    is neither recomputed nor rounded.
    """
    full = _load(combined / "robustness_metrics.csv")
    if full is None or "empirical_coverage" not in full.columns:
        return

    wanted = [m for m, _, _ in _ROB_MODES]
    df = full[full["mode"].isin(wanted)].copy()
    outside = full[~full["mode"].isin(wanted)]

    # Validation: nothing may be dropped except rows outside the two required
    # modes, and the display mapping must correspond to real CSV values.
    assert len(df) + len(outside) == len(full)
    assert set(outside["mode"].unique()) <= {"calibration_contamination"}, (
        f"unexpected modes excluded: {sorted(set(outside['mode'].unique()))}")
    assert set(df["dataset"].unique()) == {d for d, _ in _ROB_DATASETS}, (
        f"unexpected datasets: {sorted(set(df['dataset'].unique()))}")
    assert set(df["scenario"].unique()) == {s for s, _ in _ROB_SCENARIOS}, (
        "scenario set differs from the mapped display order: "
        f"{sorted(set(df['scenario'].unique()))}")
    expected_rows = len(_ROB_DATASETS) * len(_ROB_MODES) * len(_ROB_SCENARIOS)
    assert len(df) == expected_rows, (
        f"expected {expected_rows} in-scope rows, found {len(df)}")

    specs = [
        ("empirical_coverage", "Observed-signal coverage",
         "fig_07a_observed_signal_coverage"),
        ("empirical_coverage_vs_clean_truth", "Clean-reference coverage",
         "fig_07b_clean_reference_coverage"),
    ]
    for col, label, stem in specs:
        if col not in df.columns:
            continue
        n = _robustness_subfigure(df, col, label, stem, out, made)
        print(f"    [fig_robustness] {stem}: plotted {n} values "
              f"({len(_ROB_DATASETS)} datasets x {len(_ROB_MODES)} modes "
              f"x {len(_ROB_SCENARIOS)} scenarios)")


def fig_closed_loop_absorption(combined: Path, out: Path, made: list[str]) -> None:
    """The bias sweep, with both coverage definitions and clean-reference MAE.

    This is the figure behind the study's headline robustness claim, so it shows
    the quantities the claim rests on side by side rather than asking a reader to
    hold two tables in mind.
    """
    df = _load(combined / "robustness_metrics.csv")
    if df is None or "kind" not in df:
        return
    b = df[(df["kind"] == "bias")
           & df["mode"].isin(["legacy_fixed_intervals", "closed_loop"])].copy()
    if b.empty or "empirical_coverage_vs_clean_truth" not in b.columns:
        return
    b["sigma"] = b["severity"].astype(float)
    datasets = sorted(b["dataset"].unique())
    fig, axes = plt.subplots(len(datasets), 2,
                             figsize=(11.0, 3.1 * len(datasets)), squeeze=False)
    fig.subplots_adjust(hspace=0.55, wspace=0.28)
    for r, ds in enumerate(datasets):
        sub = b[b["dataset"] == ds].sort_values("sigma")
        level = sub["nominal_coverage"].iloc[0]
        ax = axes[r, 0]
        for mode, style in (("legacy_fixed_intervals", "--o"), ("closed_loop", "-s")):
            m = sub[sub["mode"] == mode]
            ax.plot(m["sigma"], m["empirical_coverage"], style, color=PALETTE[1],
                    label=f"observed-signal ({mode})", ms=4)
            ax.plot(m["sigma"], m["empirical_coverage_vs_clean_truth"], style,
                    color=PALETTE[0], label=f"clean-reference ({mode})", ms=4)
        ax.axhline(level, color="black", ls=":", lw=0.9)
        ax.set_ylim(-0.05, 1.05)
        ax.set_ylabel("coverage")
        ax.set_xlabel("sensor bias (training sd)")
        ax.set_title(f"{ds} — coverage under sensor bias", fontsize=9)
        ax.legend(fontsize=6)

        ax = axes[r, 1]
        for mode, style in (("legacy_fixed_intervals", "--o"), ("closed_loop", "-s")):
            m = sub[sub["mode"] == mode]
            ax.plot(m["sigma"], m["mae_vs_clean_truth"], style, ms=4, label=mode)
        ax.set_ylabel(f"clean-reference MAE ({sub['units'].iloc[0]})")
        ax.set_xlabel("sensor bias (training sd)")
        ax.set_title(f"{ds} — forecast error against the clean reference", fontsize=9)
        ax.legend(fontsize=6)
    _save(fig, out / "fig_13_closed_loop_absorption.png", made)


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
               fig_robustness, fig_closed_loop_absorption, fig_rankings):
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
