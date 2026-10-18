#!/usr/bin/env python3
"""Reproduce the JBE operational figures from saved, pinned GitHub results.

Usage:
    python generate_jbe_figures.py
    python generate_jbe_figures.py --download
    python generate_jbe_figures.py --output-dir figures --dpi 600

The default run is offline. No forecasting models or experiments are run.
Every plotted point is a saved aggregate result. Recovery bars use saved counts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, PercentFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATASETS = ["pleia", "pleia_energy", "rico", "bdg2"]
DATASET_LABELS = {
    "pleia": "PLEIAData temperature",
    "pleia_energy": "PLEIAData energy",
    "rico": "RICO HVAC",
    "bdg2": "BDG2 electricity",
}
CONTROL_STYLE = {
    "quantile_static": ("Uncalibrated quantile", "X"),
    "cqr_static": ("Static CQR", "o"),
    "cqr_rolling": ("Rolling CQR", "s"),
    "cqr_periodic": ("Periodic CQR", "^"),
    "persistence_static": ("Persistence + conformal", "D"),
}
POLICIES = ["static", "periodic", "rolling"]
CMAP = "viridis_r"
FIGURE_NAMES = [
    "section_4_2_alert_tradeoffs",
    "section_4_3_coverage_recovery",
]

CAPTION_ALERT = (
    "Operational tradeoffs across interval and alert configurations. "
    "(a,b) PLEIAData temperature and energy at a 10-minute forecast horizon and "
    "nominal 95% coverage, using the combined numerical and availability stream. "
    "Each panel contains four interval controls evaluated under five aggregation "
    "rules. Detection is conditional on the 68 recorded historical contexts per "
    "target and uses the seed, context and disturbance-stratum weighting in "
    "Section 3.5. (c) BDG2 at a one-hour horizon and nominal 95% coverage: "
    "uncalibrated quantiles and static, periodic and rolling CQR under the three "
    "evaluated aggregation rules (33 configurations). (d) BDG2 periodic CQR "
    "updated every 12 hourly observations, with 1-of-1 aggregation and nominal "
    "coverage targets of 95%, 97.5%, 99% and 99.5%. BDG2 values are means of the "
    "15 chronological-evaluation and seed results, evaluated using the same "
    "eligible observations across configurations. Horizontal axes use logarithmic "
    "scales. Marker shapes identify the interval control; selected annotations "
    "identify aggregation rules or coverage targets. Marker colour indicates "
    "restricted mean detection time in minutes, with separate scales for "
    "PLEIAData (limit 110 minutes) and BDG2 (limit 360 minutes). Only the line in "
    "(d) connects results, to show the sequence of nominal coverage targets. "
    "Panels retain their distinct detection definitions and should be interpreted "
    "within each monitoring setting. All results are descriptive."
)
CAPTION_RECOVERY = (
    "Observed coverage recovery after the severity-two level shift under static, "
    "periodic and rolling calibration. Blue segments show the proportion of cases "
    "meeting the recovery criterion; hatched segments show cases without observed "
    "recovery before follow-up ended. Labels give observed recoveries divided by "
    "assessed cases. Recovery is the first complete post-disturbance rolling "
    "window with coverage against the retained clean reference within five "
    "percentage points of its pre-disturbance value. Each case is one building "
    "or experimental run within a chronological evaluation and model seed. "
    "Cases without observed recovery remain in the denominator and are "
    "right-censored. Follow-up duration and group structure differ between "
    "settings; the figure is a descriptive comparison within each setting."
)


def read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_inputs(manifest: dict, directory: Path) -> list[dict]:
    checks = []
    for source in manifest["sources"]:
        path = directory / source["file"]
        content = path.read_bytes()
        sha256 = hashlib.sha256(content).hexdigest()
        blob = hashlib.sha1(
            b"blob " + str(len(content)).encode("ascii") + b"\0" + content
        ).hexdigest()
        if sha256 != source["sha256"] or blob != source["git_blob_sha"]:
            raise ValueError(f"Source integrity check failed: {path.name}")
        checks.append({
            "file": path.name, "sha256": sha256,
            "git_blob_sha": blob, "verified": True,
        })
    return checks


def download_inputs(manifest: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for source in manifest["sources"]:
        url = (
            "https://raw.githubusercontent.com/"
            f"{source['repository']}/{source['commit']}/{source['repository_path']}"
        )
        request = urllib.request.Request(
            url, headers={"User-Agent": "JBE-figure-reproduction"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != source["sha256"]:
            raise ValueError(f"Downloaded checksum mismatch: {source['file']}")
        (directory / source["file"]).write_bytes(content)


def prepare_data(directory: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pleia = pd.read_csv(directory / "pleia_alerts.csv")
    pleia = pleia.loc[pleia["channel"].eq("combined")].copy()
    counts = pleia.groupby("dataset").size().to_dict()
    if counts != {"pleia": 20, "pleia_energy": 20}:
        raise ValueError(f"Unexpected PLEIAData point counts: {counts}")
    if pleia.duplicated(["dataset", "control_id", "rule_id"]).any():
        raise ValueError("Duplicate PLEIAData configuration.")
    if not pleia["nominal_level"].eq(0.95).all():
        raise ValueError("PLEIAData plot must retain nominal 95% coverage.")

    summary = pd.read_csv(directory / "bdg2_candidate_summary.csv")
    inventory = pd.read_csv(directory / "bdg2_candidate_inventory.csv")
    bdg2 = summary.merge(
        inventory[["candidate_id", "every", "window"]],
        on="candidate_id", how="left", validate="many_to_one", indicator=True,
    )
    if not bdg2["_merge"].eq("both").all():
        raise ValueError("Some BDG2 results lack inventory metadata.")
    bdg2 = bdg2.loc[bdg2["support"].eq("common")].copy()
    if bdg2["candidate_id"].duplicated().any():
        raise ValueError("Duplicate BDG2 common-observation configuration.")
    if not bdg2["evaluation_rows"].eq(15).all():
        raise ValueError("BDG2 values must retain all 15 recorded results.")
    bdg2["control_id"] = np.where(
        bdg2["method"].eq("quantile_uncalibrated"),
        "quantile_static", "cqr_" + bdg2["strategy"],
    )

    recovery = pd.read_csv(directory / "coverage_recovery.csv")
    if len(recovery) != 12 or recovery.duplicated(["dataset", "recovery_policy"]).any():
        raise ValueError("Expected 12 distinct dataset-policy recovery rows.")
    if not (
        recovery["observed_recoveries"] + recovery["right_censored"]
    ).eq(recovery["group_policy_rows"]).all():
        raise ValueError("Recovery counts do not sum to assessed cases.")
    recovery["observed_percent"] = (
        100 * recovery["observed_recoveries"] / recovery["group_policy_rows"]
    )
    recovery["not_observed_percent"] = (
        100 * recovery["right_censored"] / recovery["group_policy_rows"]
    )
    return pleia, bdg2, recovery


def style_axes(ax: plt.Axes, xlim: tuple[float, float], xticks: list[float]) -> None:
    ax.set_xscale("log")
    ax.set_xlim(*xlim)
    ax.xaxis.set_major_locator(FixedLocator(xticks))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.tick_params(which="minor", bottom=False)
    ax.set_ylim(0, 1.02)
    ax.set_yticks(np.arange(0, 1.01, .2))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.set_xlabel("Background episodes per asset-day\n(log scale)", fontsize=8.7)
    ax.grid(axis="y", color="#E3E7EB", linewidth=.65)
    ax.set_axisbelow(True)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color("#87929B")
        ax.spines[side].set_linewidth(.7)
    ax.tick_params(labelsize=8.2, color="#87929B", width=.7, length=3)


def scatter_controls(
    ax: plt.Axes,
    data: pd.DataFrame,
    x: str, y: str, delay: str,
    norm: colors.Normalize,
) -> None:
    for control, (_, marker) in CONTROL_STYLE.items():
        selected = data.loc[data["control_id"].eq(control)]
        if selected.empty:
            continue
        ax.scatter(
            selected[x], selected[y], c=selected[delay], cmap=CMAP, norm=norm,
            marker=marker, s=43 if marker != "X" else 48, edgecolors="#28313A",
            linewidths=.55, alpha=.96, zorder=3,
        )


def label_point(
    ax: plt.Axes, row: pd.Series, x: str, y: str,
    text: str, offset: tuple[float, float], ha: str = "center",
) -> None:
    ax.annotate(
        text, (row[x], row[y]), xytext=offset, textcoords="offset points",
        fontsize=7.5, ha=ha, va="center", zorder=8,
        bbox={"boxstyle": "round,pad=.19", "fc": "white", "ec": "none", "alpha": .94},
        arrowprops={"arrowstyle": "-", "color": "#6A7580", "lw": .65},
    )


def only(data: pd.DataFrame, **conditions) -> pd.Series:
    mask = pd.Series(True, index=data.index)
    for key, value in conditions.items():
        mask &= data[key].eq(value)
    matched = data.loc[mask]
    if len(matched) != 1:
        raise ValueError(f"Expected one result for {conditions}, got {len(matched)}.")
    return matched.iloc[0]


def save_figure(fig: plt.Figure, directory: Path, name: str, dpi: int) -> None:
    for ext in ["png", "pdf", "svg"]:
        metadata = (
            {"Creator": "generate_jbe_figures.py", "CreationDate": None, "ModDate": None}
            if ext == "pdf" else
            {"Creator": "generate_jbe_figures.py", "Date": None}
            if ext == "svg" else None
        )
        temporary = directory / f".{name}.tmp.{ext}"
        fig.savefig(
            temporary, dpi=dpi, facecolor="white", metadata=metadata,
        )
        temporary.replace(directory / f"{name}.{ext}")
    plt.close(fig)


def make_alert_figure(
    pleia: pd.DataFrame, bdg2: pd.DataFrame, directory: Path, dpi: int,
) -> list[dict]:
    fig = plt.figure(figsize=(7.48, 6.75))
    grid = fig.add_gridspec(
        2, 3, width_ratios=[1, 1, .045],
        left=.087, right=.925, bottom=.10, top=.835,
        wspace=.30, hspace=.58,
    )
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]),
            fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])]
    norms = [colors.Normalize(0, 110), colors.Normalize(0, 360)]
    plotted = []
    px = "mean_background_episodes_per_asset_day"
    py = "conditional_context_detection"
    pdly = "restricted_ttd_equal_stratum_minutes"
    for panel, dataset, ax in zip(["a", "b"], ["pleia", "pleia_energy"], axes[:2]):
        d = pleia.loc[pleia["dataset"].eq(dataset)].copy()
        scatter_controls(ax, d, px, py, pdly, norms[0])
        if dataset == "pleia":
            style_axes(ax, (.075, 6), [.1, .3, 1, 3])
        else:
            style_axes(ax, (.09, 27), [.1, .3, 1, 3, 10])
        ax.set_ylabel("Conditional detection (%)", fontsize=8.8)
        ax.set_title(
            f"({panel}) {DATASET_LABELS[dataset]}\n10-min horizon; nominal 95%",
            loc="left", fontweight="bold", fontsize=9.1, pad=9,
        )
        offsets = {
            "pleia": [(-9, -27), (-33, 39), (-8, -36)],
            "pleia_energy": [(-17, -29), (30, 12), (-6, -28)],
        }[dataset]
        for control, rule, text, offset in [
            ("cqr_rolling", "single_sample", "Rolling\n1-of-1", offsets[0]),
            ("cqr_rolling", "30min_3of3", "Rolling\n3-of-3", offsets[1]),
            ("cqr_static", "single_sample", "Static\n1-of-1", offsets[2]),
        ]:
            row = only(d, control_id=control, rule_id=rule)
            label_point(ax, row, px, py, text, offset)
        for _, row in d.iterrows():
            plotted.append({
                "panel": panel, "dataset": dataset, "source_file": "pleia_alerts.csv",
                "source_id": f"{dataset}:{row['control_id']}:{row['rule_id']}:combined",
                "control": row["control_id"], "rule_id": row["rule_id"],
                "nominal_coverage": row["nominal_level"],
                "detection_definition": "conditional_context_detection",
                "detection": row[py], "background_episodes_per_asset_day": row[px],
                "restricted_mean_detection_minutes": row[pdly],
            })

    bx, by, bdly = "mean_clean_workload", "mean_macro_event_recall", "mean_restricted_detection_minutes"
    d = bdg2.loc[
        bdg2["level"].eq(.95) &
        bdg2["method"].isin(["cqr", "quantile_uncalibrated"])
    ].copy()
    if len(d) != 33:
        raise ValueError(f"Expected 33 BDG2 nominal-95% configurations, got {len(d)}.")
    ax = axes[2]
    scatter_controls(ax, d, bx, by, bdly, norms[1])
    style_axes(ax, (.025, 2.1), [.03, .1, .3, 1])
    ax.set_ylabel("Macro event recall (%)", fontsize=8.8)
    ax.set_title(
        "(c) BDG2: aggregation and updates\n1-h horizon; nominal 95%",
        loc="left", fontweight="bold", fontsize=9.1, pad=9,
    )
    for rule, text, offset in [
        ("single_sample", "Static CQR\n1-of-1", (-39, 20)),
        ("180min_3of3", "Static CQR\n3-of-3", (32, 12)),
        ("360min_4of6", "Static CQR\n4-of-6", (62, -9)),
    ]:
        row = only(d, method="cqr", strategy="static", rule_id=rule)
        label_point(ax, row, bx, by, text, offset)
    for _, row in d.iterrows():
        plotted.append({
            "panel": "c", "dataset": "bdg2", "source_file": "bdg2_candidate_summary.csv",
            "source_id": row["candidate_id"], "control": row["control_id"],
            "rule_id": row["rule_id"], "nominal_coverage": row["level"],
            "update_every_steps": row["every"], "rolling_window_scores": row["window"],
            "detection_definition": "macro_event_recall",
            "detection": row[by], "background_episodes_per_asset_day": row[bx],
            "restricted_mean_detection_minutes": row[bdly],
        })

    d = bdg2.loc[
        bdg2["method"].eq("cqr") & bdg2["strategy"].eq("periodic") &
        bdg2["every"].eq(12) & bdg2["rule_id"].eq("single_sample")
    ].sort_values("level").copy()
    if list(d["level"]) != [.95, .975, .99, .995]:
        raise ValueError("Expected the four coverage targets for periodic 12-h CQR.")
    ax = axes[3]
    ax.plot(d[bx], d[by], color="#8995A1", lw=1.1, zorder=2)
    scatter_controls(ax, d, bx, by, bdly, norms[1])
    style_axes(ax, (.085, 1.5), [.1, .2, .5, 1])
    ax.set_ylabel("Macro event recall (%)", fontsize=8.8)
    ax.set_title(
        "(d) BDG2: coverage targets\nPeriodic CQR every 12 h; 1-of-1",
        loc="left", fontweight="bold", fontsize=9.1, pad=9,
    )
    for (_, row), offset in zip(d.iterrows(), [(0, 15), (8, 15), (12, 13), (11, -15)]):
        label_point(ax, row, bx, by, f"{100 * row['level']:g}%", offset)
        plotted.append({
            "panel": "d", "dataset": "bdg2", "source_file": "bdg2_candidate_summary.csv",
            "source_id": row["candidate_id"], "control": row["control_id"],
            "rule_id": row["rule_id"], "nominal_coverage": row["level"],
            "update_every_steps": row["every"], "rolling_window_scores": row["window"],
            "detection_definition": "macro_event_recall",
            "detection": row[by], "background_episodes_per_asset_day": row[bx],
            "restricted_mean_detection_minutes": row[bdly],
        })

    handles = [
        Line2D([], [], marker=marker, linestyle="", markersize=6.5,
               markerfacecolor="#B3BCC5", markeredgecolor="#28313A",
               markeredgewidth=.55, label=label)
        for label, marker in CONTROL_STYLE.values()
    ]
    fig.legend(
        handles=handles, loc="upper center", bbox_to_anchor=(.485, .985),
        ncol=3, frameon=False, fontsize=8.3, columnspacing=1.4,
        handletextpad=.55, labelspacing=.7,
    )
    for row_num, norm in enumerate(norms):
        cax = fig.add_subplot(grid[row_num, 2])
        bar = fig.colorbar(ScalarMappable(norm=norm, cmap=CMAP), cax=cax)
        bar.set_ticks([0, 55, 110] if row_num == 0 else [0, 180, 360])
        bar.ax.tick_params(labelsize=8, length=2, width=.5)
        bar.outline.set_linewidth(.5)
        bar.set_label("Restricted mean detection time (min)", fontsize=8.1, labelpad=8)
    save_figure(fig, directory, FIGURE_NAMES[0], dpi)
    pd.DataFrame(plotted).to_csv(
        directory / f"{FIGURE_NAMES[0]}_data.csv", index=False, float_format="%.12g",
    )
    return plotted


def make_recovery_figure(
    recovery: pd.DataFrame, directory: Path, dpi: int,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.4), sharey=True)
    fig.subplots_adjust(left=.095, right=.98, bottom=.12, top=.84, hspace=.43, wspace=.28)
    blue, gray = "#0072B2", "#F3F5F7"
    for panel, dataset, ax in zip("abcd", DATASETS, axes.flat):
        d = (
            recovery.loc[recovery["dataset"].eq(dataset)]
            .set_index("recovery_policy").loc[POLICIES].reset_index()
        )
        x = np.arange(3)
        ax.bar(
            x, d["observed_percent"], width=.58, color=blue,
            edgecolor=blue, linewidth=.6, zorder=3,
        )
        ax.bar(
            x, d["not_observed_percent"], bottom=d["observed_percent"],
            width=.58, color=gray, edgecolor="#8D98A2", hatch="////",
            linewidth=.6, zorder=3,
        )
        for xpos, (_, row) in zip(x, d.iterrows()):
            ax.text(
                xpos, 103.3,
                f"{int(row['observed_recoveries'])}/{int(row['group_policy_rows'])}",
                ha="center", va="bottom", fontsize=9, color="#25323E",
            )
        ax.set_title(
            f"({panel}) {DATASET_LABELS[dataset]}",
            loc="left", fontweight="bold", fontsize=10, pad=8,
        )
        ax.set_xticks(x, ["Static", "Periodic", "Rolling"])
        ax.set_ylim(0, 118)
        ax.set_xlim(-.6, 2.6)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
        ax.grid(axis="y", color="#E1E6EB", linewidth=.65, zorder=0)
        ax.tick_params(axis="both", labelsize=9, length=3, color="#87929B")
        if panel in ["a", "c"]:
            ax.set_ylabel("Share of assessed cases (%)", fontsize=9)
        for side in ["top", "right"]:
            ax.spines[side].set_visible(False)
        for side in ["left", "bottom"]:
            ax.spines[side].set_color("#87929B")
            ax.spines[side].set_linewidth(.7)
    fig.legend(
        handles=[
            Patch(facecolor=blue, edgecolor=blue, label="Observed coverage recovery"),
            Patch(facecolor=gray, edgecolor="#8D98A2", hatch="////",
                  label="Recovery not observed during follow-up"),
        ],
        loc="upper center", bbox_to_anchor=(.535, .985),
        frameon=False, fontsize=9, ncol=1, labelspacing=.6,
    )
    fig.text(
        .53, .028, "Labels show observed recoveries / assessed cases.",
        ha="center", fontsize=8.5, color="#52616D",
    )
    save_figure(fig, directory, FIGURE_NAMES[1], dpi)
    columns = [
        "dataset", "task", "recovery_policy", "group_policy_rows",
        "observed_recoveries", "right_censored", "observed_percent",
        "not_observed_percent", "horizon_minutes",
    ]
    recovery[columns].to_csv(
        directory / f"{FIGURE_NAMES[1]}_data.csv", index=False, float_format="%.12g",
    )


def verify_reported_values(
    pleia: pd.DataFrame, bdg2: pd.DataFrame, recovery: pd.DataFrame,
) -> dict:
    reference = only(
        bdg2, method="quantile_uncalibrated", level=.95,
        strategy="static", rule_id="single_sample",
    )
    calibrated = only(
        bdg2, method="cqr", level=.95, strategy="static", rule_id="single_sample",
    )
    reduction = 100 * (1 - calibrated["mean_clean_workload"] / reference["mean_clean_workload"])
    if round(reduction, 2) != 25.53:
        raise ValueError("Main workload contrast does not match Table 6.")
    expected = {
        "pleia": [10, 13, 15], "pleia_energy": [12, 13, 15],
        "rico": [578, 523, 312], "bdg2": [150, 150, 150],
    }
    for dataset, counts in expected.items():
        d = recovery.loc[recovery["dataset"].eq(dataset)].set_index("recovery_policy")
        got = list(d.loc[POLICIES, "observed_recoveries"].astype(int))
        if got != counts:
            raise ValueError(f"Recovery count mismatch for {dataset}: {got}")
    if not pleia["original_contexts"].eq(68).all():
        raise ValueError("PLEIAData context count changed.")
    return {
        "main_workload_reduction_percent": float(reduction),
        "main_macro_recall_reference": float(reference["mean_macro_event_recall"]),
        "main_macro_recall_static_cqr": float(calibrated["mean_macro_event_recall"]),
        "recovery_counts_match_manuscript": True,
        "pleia_contexts_per_target": 68,
        "no_new_model_fitting_or_experiments": True,
        "no_population_confidence_intervals_or_significance_claims": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "figures")
    parser.add_argument("--manifest", type=Path, default=ROOT / "SOURCE_MANIFEST.json")
    parser.add_argument("--download", action="store_true", help="Download the pinned CSV files first.")
    parser.add_argument("--dpi", type=int, default=600)
    args = parser.parse_args()
    manifest = read_manifest(args.manifest)
    if args.download:
        download_inputs(manifest, args.data_dir)
    checks = check_inputs(manifest, args.data_dir)
    pleia, bdg2, recovery = prepare_data(args.data_dir)
    reported = verify_reported_values(pleia, bdg2, recovery)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9,
        "axes.labelcolor": "#25323E", "text.color": "#25323E",
        "xtick.color": "#36434F", "ytick.color": "#36434F",
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "svg.hashsalt": "jbe-operational-figures-20261018",
        "savefig.pad_inches": .03,
    })
    plotted = make_alert_figure(pleia, bdg2, args.output_dir, args.dpi)
    make_recovery_figure(recovery, args.output_dir, args.dpi)
    output_sizes = {}
    for name in FIGURE_NAMES:
        for ext in ["png", "pdf", "svg"]:
            file = args.output_dir / f"{name}.{ext}"
            output_sizes[file.name] = file.stat().st_size
            if output_sizes[file.name] < 1000:
                raise ValueError(f"Incomplete figure output: {file.name}")
            if ext == "pdf" and not file.read_bytes().startswith(b"%PDF-"):
                raise ValueError(f"Invalid vector PDF: {file.name}")
    (args.output_dir / "CAPTIONS.md").write_text(
        "# Figure captions\n\n"
        "## Section 4.2: alert tradeoffs\n\n" + CAPTION_ALERT +
        "\n\n## Section 4.3: coverage recovery\n\n" + CAPTION_RECOVERY + "\n",
        encoding="utf-8",
    )
    validation = {
        "sources": checks,
        "plotted_points_by_panel": pd.DataFrame(plotted).groupby("panel").size().to_dict(),
        "recovery_bars": int(len(recovery)),
        "output_bytes": output_sizes,
        "manuscript_cross_checks": reported,
        "environment": {
            "python": platform.python_version(), "matplotlib": matplotlib.__version__,
            "numpy": np.__version__, "pandas": pd.__version__,
        },
        "outputs": {
            name: [f"{name}.{ext}" for ext in ["png", "pdf", "svg"]]
            for name in FIGURE_NAMES
        },
    }
    (args.output_dir / "VALIDATION.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps({
        "figures": FIGURE_NAMES,
        "plotted_points_by_panel": validation["plotted_points_by_panel"],
        "recovery_bars": validation["recovery_bars"],
        "dpi": args.dpi,
    }, indent=2))


if __name__ == "__main__":
    main()

