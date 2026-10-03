"""Figures 4.4 and 4.5: detection or recall against background alert workload.

Sources (review/candidature_evidence_package_20261002_v1/REPORT_TABLES/):

* Figure 4.4: CONDITIONAL_ALERTS_PLEIA.csv, channel = combined
  (4 controls x 5 temporal rules per task).
* Figure 4.5: OPERATIONAL_ALERTS_BDG2_H1.csv, support = common
  (165 configurations).

Each point is one stored aggregate row, plotted without further averaging.
PLEIAData reports conditional context detection and BDG2 reports mean macro
event recall. They are different endpoints and keep separate axis labels. The
dashed line marks one background episode per asset-day. The counts in the
Figure 4.5 colour legend are evaluated monitoring configurations per interval
method (3 + 30 + 132 = 165), recounted from the source table during
verification.

Usage:
    python report_figures/chapter4/figure_4_4_4_5_alert_tradeoffs.py
"""

from __future__ import annotations

import chapter4_style as c4
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
from matplotlib.transforms import blended_transform_factory

PLEIA_SOURCE = c4.TABLES / "CONDITIONAL_ALERTS_PLEIA.csv"
BDG2_SOURCE = c4.TABLES / "OPERATIONAL_ALERTS_BDG2_H1.csv"
WORKLOAD = "mean_background_episodes_per_asset_day"
WORKLOAD_LABEL = "Mean background episodes per asset-day (log scale)"
REFERENCE_WORKLOAD = 1.0
BDG2_CONFIGURATIONS = 165

PLEIA = {
    "stem": "figure_4_4_pleia_alert_tradeoffs",
    "title": "Figure 4.4. PLEIAData conditional context detection against background alert workload",
    "gid": "fig4.4|",
    "endpoint": "conditional_context_detection",
    "tasks": ("PLEIAData temperature", "PLEIAData energy"),
    "caption": (
        "Conditional context detection against mean background alert episodes per asset-day (logarithmic axis) "
        "for the PLEIAData temperature and energy challenges: four 95% interval controls (colour) under five "
        "temporal k-of-m rules (marker shape), combined alarm channel, one-step (10 min) horizon, outer fold 2 and "
        "model seeds 42 to 46. Detection averages the model seeds within each of 68 original contexts and weights "
        "the 21 declared fault strata equally. It is a conditional synthetic-fault endpoint, not deployment "
        "precision or prevalence-weighted recall. The dashed line marks one background episode per asset-day."
    ),
}
BDG2 = {
    "stem": "figure_4_5_bdg2_alert_tradeoffs",
    "title": "Figure 4.5. BDG2 mean macro event recall against background alert workload",
    "gid": "fig4.5|",
    "endpoint": "mean_macro_event_recall",
    "caption": (
        "Mean macro event recall against mean background alert episodes per asset-day (logarithmic axis) for the "
        "165 monitoring configurations evaluated on common support in the BDG2 one-hour causal replay. Colour "
        "shows the interval method and marker shape the temporal rule. The counts in the legend are numbers of "
        "evaluated configurations (3 + 30 + 132 = 165), not buildings, events or replicates. Each point averages "
        "three outer folds and five model seeds with fixed event catalogues, and macro recall weights the 21 event "
        "type and severity strata equally. The dashed line marks one background episode per asset-day."
    ),
}

# Colour = interval control / method (validated sets, see chapter4_style).
CONTROLS = {
    "quantile_static": ("Uncalibrated quantile, static", c4.VIOLET),
    "cqr_static": ("CQR, static", c4.BLUE),
    "cqr_rolling": ("CQR, rolling", c4.ORANGE),
    "persistence_static": ("Persistence split-conformal, static", c4.AQUA),
}
BDG2_METHODS = {
    "quantile_uncalibrated": ("Uncalibrated quantile", c4.VIOLET),
    "cqr": ("CQR", c4.BLUE),
    "recentred_enbpi": ("Recentred EnbPI", c4.RED),
}

# Marker = temporal k-of-m rule; the k-of-m shapes match across both figures.
PLEIA_RULES = {
    "single_sample": ("1 of 1", "o"),
    "30min_3of3": ("3 of 3 in 30 min", "s"),
    "60min_4of6": ("4 of 6 in 60 min", "^"),
    "180min_3of18": ("3 of 18 in 180 min", "D"),
    "360min_4of36": ("4 of 36 in 360 min", "P"),
}
BDG2_RULES = {
    "single_sample": ("1 of 1", "o"),
    "180min_3of3": ("3 of 3 in 180 min", "s"),
    "360min_4of6": ("4 of 6 in 360 min", "^"),
}


def method_entry(label: str, configurations: int) -> str:
    """Colour-legend entry; the count is of evaluated monitoring configurations."""
    return f"{label} ({configurations} evaluated configurations)"


def scatter(ax, x, y, color: str, marker: str, size: float, gid: str):
    return ax.scatter(
        list(x), list(y), s=c4.marker_size(marker, size) ** 2, marker=marker,
        facecolors=color, edgecolors=c4.SURFACE, linewidths=0.8, gid=gid, zorder=3,
    )


def workload_axis(ax, ticks, limits) -> None:
    ax.set_xscale("log")
    ax.set_xlim(*limits)
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_ylim(0, 1)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.grid(True, which="major")
    ax.set_axisbelow(True)


def reference_line(ax, gid: str, labelled: bool, side: str = "left", top: bool = True) -> None:
    """Dashed reference at one episode per asset-day, labelled in a corner of the line with room."""
    ax.axvline(
        REFERENCE_WORKLOAD, color=c4.INK_2, linewidth=0.9, linestyle=c4.REFERENCE_DASH,
        zorder=2, gid=gid,
    )
    if labelled:
        ax.text(
            REFERENCE_WORKLOAD * (0.9 if side == "left" else 1.1), 0.985 if top else 0.015,
            "1 episode per asset-day", transform=blended_transform_factory(ax.transData, ax.transAxes),
            ha="right" if side == "left" else "left", va="top" if top else "bottom",
            fontsize=c4.NOTE_SIZE, color=c4.INK_2,
        )


def legends(fig, colours: dict, rules: dict, colour_title: str, rule_columns: int) -> None:
    colour_handles = [Patch(facecolor=color, edgecolor="none", label=label) for label, color in colours.values()]
    rule_handles = [
        Line2D(
            [], [], linestyle="none", marker=marker, markersize=c4.marker_size(marker, 6.5),
            markerfacecolor=c4.INK_2, markeredgecolor=c4.SURFACE, label=label,
        )
        for label, marker in rules.values()
    ]
    fig.legend(
        handles=colour_handles, title=colour_title, loc="outside upper left",
        alignment="left", handlelength=1.3, handleheight=0.8,
    )
    fig.legend(
        handles=rule_handles, title="Temporal alert rule", loc="outside upper right",
        alignment="left", ncol=rule_columns,
    )


def build_pleia(frame):
    rows = frame[frame["channel"] == "combined"]
    if rows.duplicated(["task", "control_id", "rule_id"]).any():
        raise ValueError("more than one combined-channel row for a task, control and rule")
    fig, axes = plt.subplots(
        1, 2, figsize=(c4.FULL_WIDTH, 4.0), layout="constrained", sharex=True, sharey=True
    )
    for ax, letter, task in zip(axes, "ab", PLEIA["tasks"]):
        task_rows = rows[rows["task"] == task]
        if len(task_rows) != len(CONTROLS) * len(PLEIA_RULES):
            raise ValueError(f"{task}: expected {len(CONTROLS) * len(PLEIA_RULES)} rows, found {len(task_rows)}")
        for control, (_, color) in CONTROLS.items():
            for rule, (_, marker) in PLEIA_RULES.items():
                row = task_rows[(task_rows["control_id"] == control) & (task_rows["rule_id"] == rule)]
                if len(row) != 1:
                    raise ValueError(f"{task}: no single row for {control} and {rule}")
                scatter(ax, row[WORKLOAD], row[PLEIA["endpoint"]], color, marker, 7.0,
                        gid=f"{PLEIA['gid']}{task}|{control}|{rule}")
        workload_axis(ax, [0.1, 0.3, 1, 3, 10, 30], (0.07, 30))
        # At 15 cm and 9 pt the label fits only right of the line in panel (a), and only
        # below the points: the top-right corner holds the 0.909 persistence point.
        reference_line(ax, f"{PLEIA['gid']}reference|{task}", labelled=letter == "a", side="right", top=False)
        c4.panel_title(ax, letter, task)
    axes[0].set_ylabel("Conditional context detection")
    fig.supxlabel(WORKLOAD_LABEL, fontsize=c4.TEXT_SIZE)
    legends(fig, CONTROLS, PLEIA_RULES, "Interval control", rule_columns=2)
    return fig


def build_bdg2(frame):
    rows = frame[frame["support"] == "common"]
    if len(rows) != BDG2_CONFIGURATIONS or rows["candidate_id"].duplicated().any():
        raise ValueError(f"expected {BDG2_CONFIGURATIONS} unique common-support configurations")
    fig, ax = plt.subplots(figsize=(c4.FULL_WIDTH, 4.4), layout="constrained")
    plotted = 0
    # The largest group is drawn first so the three uncalibrated points stay on top.
    for method in reversed(list(BDG2_METHODS)):
        _, color = BDG2_METHODS[method]
        for rule, (_, marker) in BDG2_RULES.items():
            subset = rows[(rows["method"] == method) & (rows["rule_id"] == rule)].sort_values("candidate_id")
            if subset.empty:
                raise ValueError(f"no configurations for {method} and {rule}")
            scatter(ax, subset[WORKLOAD], subset[BDG2["endpoint"]], color, marker, 5.8,
                    gid=f"{BDG2['gid']}{method}|{rule}")
            plotted += len(subset)
    if plotted != BDG2_CONFIGURATIONS:
        raise ValueError(f"plotted {plotted} of {BDG2_CONFIGURATIONS} configurations")
    workload_axis(ax, [0.003, 0.01, 0.03, 0.1, 0.3, 1, 3], (0.002, 3))
    reference_line(ax, f"{BDG2['gid']}reference", labelled=True)
    ax.set_ylabel("Mean macro event recall")
    ax.set_xlabel(WORKLOAD_LABEL)
    counts = rows["method"].value_counts()
    methods = {method: (method_entry(label, counts[method]), color) for method, (label, color) in BDG2_METHODS.items()}
    legends(fig, methods, BDG2_RULES, "Interval method", rule_columns=1)
    return fig


def verify_bdg2_legend(fig, check: c4.ValueCheck) -> None:
    """Each colour-legend count equals that method's evaluated configurations in the source."""
    counts: dict[str, int] = {}
    for row in c4.read_rows(BDG2_SOURCE):
        if row["support"] == "common":
            counts[row["method"]] = counts.get(row["method"], 0) + 1
    if sum(counts.values()) != BDG2_CONFIGURATIONS or set(counts) != set(BDG2_METHODS):
        raise AssertionError(f"{BDG2['stem']}: unexpected configuration counts {counts}")
    legend = next(item for item in fig.legends if item.get_title().get_text() == "Interval method")
    entries = [text.get_text() for text in legend.get_texts()]
    expected = [method_entry(label, counts[method]) for method, (label, _) in BDG2_METHODS.items()]
    if len(entries) != len(expected):
        raise AssertionError(f"{BDG2['stem']}: {len(entries)} colour-legend entries, expected {len(expected)}")
    for entry, wanted in zip(entries, expected):
        check.text(entry, wanted, "colour-legend entry")


def verify(fig, spec, source, keep, key_columns, colours) -> c4.ValueCheck:
    check = c4.ValueCheck(spec["stem"])
    expected: dict[str, list[tuple[float, float]]] = {}
    for row in c4.read_rows(source):
        if keep(row):
            gid = spec["gid"] + "|".join(row[column] for column in key_columns)
            expected.setdefault(gid, []).append((float(row[WORKLOAD]), float(row[spec["endpoint"]])))
    plotted = c4.artists_by_gid(fig, spec["gid"])
    references = {gid: plotted.pop(gid) for gid in list(plotted) if gid.startswith(f"{spec['gid']}reference")}
    check.keys(plotted, expected, "plotted groups")
    for gid, collection in plotted.items():
        check.points(c4.scatter_points(collection), expected[gid], gid)
        check.color(collection.get_facecolor()[0], colours[gid.split("|")[-2]][1], gid)
    if not references:
        raise AssertionError(f"{spec['stem']}: reference line missing")
    for gid, line in references.items():
        for x in line.get_xdata():
            check.number(x, REFERENCE_WORKLOAD, gid)
    return check


def main() -> None:
    c4.apply_style()
    jobs = (
        (PLEIA, PLEIA_SOURCE, build_pleia, lambda row: row["channel"] == "combined",
         ("task", "control_id", "rule_id"), CONTROLS),
        (BDG2, BDG2_SOURCE, build_bdg2, lambda row: row["support"] == "common",
         ("method", "rule_id"), BDG2_METHODS),
    )
    for spec, source, build, keep, key_columns, colours in jobs:
        fig = build(c4.read_table(source))
        check = verify(fig, spec, source, keep, key_columns, colours)
        if spec is BDG2:
            verify_bdg2_legend(fig, check)
        outputs = c4.save_figure(fig, spec["stem"], spec["title"])
        plt.close(fig)
        c4.report(check, [source], outputs, caption=spec["caption"])


if __name__ == "__main__":
    main()
