"""Figure 4.9: paired differences in conditional detection between rolling and static CQR.

Caption: Paired differences in conditional detection between rolling and static CQR

Sources (committed PLEIAData five-seed analyses):
    smart_building_conformal/outputs/conditional_context005/pleia_temperature_f2_context005_five_seed_analysis_v1/paired_control_detection_contrasts.csv
    smart_building_conformal/outputs/conditional_context005/pleia_energy_f2_context005_five_seed_analysis_v1/paired_control_detection_contrasts.csv

All ten paired contrasts are shown: two tasks x five temporal rules, with
control_a = cqr_static, control_b = cqr_rolling and channel = combined. Every
selected row is a supported "A minus B" contrast. The stored contrast is
static minus rolling, so the figure shows rolling minus static in percentage
points:

    estimate    = -point_difference * 100
    lower_bound = -upper * 100
    upper_bound = -lower * 100

The bounds are the stored 95% paired chronological block bounds (2.5% and
97.5% quantiles of 2,000 original-context block draws). No new interval is
computed for plotting and no significance mark is added.

Verification, read-only:
* each stored point difference equals static minus rolling detection in
  REPORT_TABLES/CONDITIONAL_ALERTS_PLEIA.csv;
* each stored bound equals the quantile of the paired per-draw differences in
  the committed bootstrap_draw_estimates.csv.gz, whose draw hash matches
  bootstrap_design.json.

Outputs: figure_4_9_paired_conditional_detection_differences.png / .pdf and
the derived figure data figure_4_9_paired_conditional_detection_differences_data.csv.

Usage:
    python report_figures/chapter4/figure_4_9_paired_conditional_detection_differences.py
"""

from __future__ import annotations

import csv
import gzip
import json
import math

import chapter4_style as c4
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

STEM = "figure_4_9_paired_conditional_detection_differences"
CAPTION = "Paired differences in conditional detection between rolling and static CQR"
ANALYSES = c4.REPO / "smart_building_conformal" / "outputs" / "conditional_context005"
FOLDERS = {
    "PLEIAData temperature": ANALYSES / "pleia_temperature_f2_context005_five_seed_analysis_v1",
    "PLEIAData energy": ANALYSES / "pleia_energy_f2_context005_five_seed_analysis_v1",
}
SOURCES = {task: folder / "paired_control_detection_contrasts.csv" for task, folder in FOLDERS.items()}
DRAWS = {task: folder / "bootstrap_draw_estimates.csv.gz" for task, folder in FOLDERS.items()}  # check only
DESIGNS = {task: folder / "bootstrap_design.json" for task, folder in FOLDERS.items()}          # check only
DETECTION_TABLE = c4.TABLES / "CONDITIONAL_ALERTS_PLEIA.csv"                                   # check only
DATA = c4.OUT_DIR / f"{STEM}_data.csv"
GID = "fig4.9|"
SELECTION = {"control_a": "cqr_static", "control_b": "cqr_rolling", "channel": "combined"}
# Labels and order match the temporal-rule legend of Figure 4.4.
RULES = {
    "single_sample": "1 of 1",
    "30min_3of3": "3 of 3 in 30 min",
    "60min_4of6": "4 of 6 in 60 min",
    "180min_3of18": "3 of 18 in 180 min",
    "360min_4of36": "4 of 36 in 360 min",
}
DRAW_COUNT = 2000
X_LABEL = "Rolling minus static CQR detection difference (percentage points)"
INTERVAL_LABEL = "95% paired chronological block interval"
CAPTION_TEXT = (
    "Paired differences in conditional context detection between rolling and static CQR, combined alarm channel, "
    "for all five temporal rules in the PLEIAData temperature and energy challenges. Differences are rolling minus "
    "static in percentage points: the stored static-minus-rolling contrast is negated and multiplied by 100, so "
    "its bounds become −100 × upper and −100 × lower. Horizontal lines show the stored 95% paired chronological "
    "block intervals, the 2.5% and 97.5% quantiles of 2,000 paired draws of seven-context blocks of the 68 "
    "original contexts. They describe the original-context design rather than a population, and they do not apply "
    "to workload or delay. The dashed line marks no difference."
)


def estimate_label(value: float) -> str:
    return f"{value:.2f}".replace("-", "\N{MINUS SIGN}")


def derive() -> pd.DataFrame:
    records = []
    for task, path in SOURCES.items():
        provenance = c4.git_provenance(path)
        frame = c4.read_table(path)
        for rule_id, rule_label in RULES.items():
            mask = frame["rule_id"] == rule_id
            for column, value in SELECTION.items():
                mask &= frame[column] == value
            selected = frame[mask]
            if len(selected) != 1:
                raise ValueError(f"{task}: expected one {rule_id} contrast, found {len(selected)}")
            row = selected.iloc[0]
            if row["definition"] != "A minus B" or row["status"] != "supported":
                raise ValueError(f"{task}: {rule_id} contrast is not a supported A-minus-B row")
            estimate = -row["point_difference"] * 100
            records.append(
                {
                    "row_order": len(records) + 1,
                    "task": task,
                    "rule_id": rule_id,
                    "rule_label": rule_label,
                    "row_label": f"{task}, {rule_label}",
                    "control_a": row["control_a"],
                    "control_b": row["control_b"],
                    "channel": row["channel"],
                    "stored_definition": row["definition"],
                    "stored_point_difference": row["point_difference"],
                    "stored_lower": row["lower"],
                    "stored_upper": row["upper"],
                    "estimate_pp": estimate,
                    "lower_bound_pp": -row["upper"] * 100,
                    "upper_bound_pp": -row["lower"] * 100,
                    "estimate_label": estimate_label(estimate),
                    "status": row["status"],
                    "valid_draws": row["valid_draws"],
                    "draw_hash": row["draw_hash"],
                    **provenance,
                }
            )
    return pd.DataFrame(records)


def build(data):
    fig, axes = plt.subplots(2, 1, figsize=(c4.FULL_WIDTH, 4.6), layout="constrained", sharex=True)
    positions = list(range(len(RULES)))
    for ax, letter, task in zip(axes, "ab", FOLDERS):
        rows = data[data["task"] == task]
        for y, row in zip(positions, rows.itertuples(index=False)):
            ax.axhline(y, color=c4.GRID, linewidth=0.5, zorder=0)
            ax.plot(
                [row.lower_bound_pp, row.upper_bound_pp], [y, y], color=c4.INK_2, linewidth=1.6,
                marker="|", markersize=7, markeredgewidth=1.6, solid_capstyle="butt", zorder=2,
                gid=f"{GID}interval|{row.row_label}",
            )
            ax.plot(
                [row.estimate_pp], [y], linestyle="none", marker="o", markersize=6.5, color=c4.INK,
                markeredgecolor=c4.SURFACE, markeredgewidth=c4.RING_WIDTH, zorder=3,
                gid=f"{GID}estimate|{row.row_label}",
            )
            ax.annotate(
                row.estimate_label, xy=(row.estimate_pp, y), xytext=(0, 5.5), textcoords="offset points",
                ha="center", va="bottom", fontsize=c4.TEXT_SIZE, color=c4.INK, gid=f"{GID}label|{row.row_label}",
            )
        ax.axvline(0.0, color=c4.INK_2, linewidth=0.9, linestyle=c4.REFERENCE_DASH, zorder=1,
                   gid=f"{GID}reference|{task}")
        ax.set_yticks(positions, rows["rule_label"].tolist())
        ax.set_ylim(positions[-1] + 0.55, positions[0] - 0.85)
        ax.tick_params(axis="y", length=0, pad=4)
        ax.spines["left"].set_visible(False)
        ax.xaxis.grid(True)
        ax.set_axisbelow(True)
        c4.panel_title(ax, letter, task)
    axes[-1].set_xlim(-20, 45)
    axes[-1].set_xticks(range(-20, 41, 10))
    axes[-1].set_xlabel(X_LABEL)
    handles = [
        Line2D([], [], linestyle="none", marker="o", markersize=6.5, color=c4.INK,
               markeredgecolor=c4.SURFACE, markeredgewidth=c4.RING_WIDTH, label="Point estimate"),
        Line2D([], [], color=c4.INK_2, linewidth=1.6, marker="|", markersize=7, markeredgewidth=1.6,
               label=INTERVAL_LABEL),
    ]
    fig.legend(handles=handles, loc="outside upper center", ncol=2)
    return fig


def draw_bounds(task: str) -> dict[str, tuple[float, float, int]]:
    """2.5% and 97.5% quantiles of per-draw static minus rolling detection, by rule."""
    values: dict[tuple[str, str], dict[int, float]] = {}
    with gzip.open(DRAWS[task], "rt", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["channel"] == SELECTION["channel"] and row["rule_id"] in RULES and \
                    row["control_id"] in (SELECTION["control_a"], SELECTION["control_b"]):
                values.setdefault((row["control_id"], row["rule_id"]), {})[int(row["draw"])] = float(row["value"])
    bounds = {}
    for rule_id in RULES:
        static, rolling = values[(SELECTION["control_a"], rule_id)], values[(SELECTION["control_b"], rule_id)]
        if set(static) != set(rolling) or len(static) != DRAW_COUNT:
            raise AssertionError(f"{STEM}: {task}, {rule_id}: draws are not paired across controls")
        differences = np.array([static[draw] - rolling[draw] for draw in sorted(static)])
        lower, upper = np.quantile(differences, [0.025, 0.975])
        bounds[rule_id] = (float(lower), float(upper), len(differences))
    return bounds


def verify(fig) -> c4.ValueCheck:
    check = c4.ValueCheck(STEM)
    expected = []
    for task, path in SOURCES.items():
        rows = {row["rule_id"]: row for row in c4.read_rows(path)
                if all(row[column] == value for column, value in SELECTION.items()) and row["rule_id"] in RULES}
        if set(rows) != set(RULES):
            raise AssertionError(f"{STEM}: {task}: contrasts found for {sorted(rows)}")
        for rule_id, rule_label in RULES.items():
            row = rows[rule_id]
            difference, lower, upper = float(row["point_difference"]), float(row["lower"]), float(row["upper"])
            expected.append({
                "task": task, "rule_id": rule_id, "rule_label": rule_label, "label": f"{task}, {rule_label}",
                "difference": difference, "lower": lower, "upper": upper,
                "valid_draws": int(row["valid_draws"]), "draw_hash": row["draw_hash"],
                "estimate": -difference * 100, "low": -upper * 100, "high": -lower * 100,
            })

    # The stored contrast must equal static minus rolling detection in the report table.
    detection = {(row["task"], row["control_id"], row["rule_id"]): float(row["conditional_context_detection"])
                 for row in c4.read_rows(DETECTION_TABLE) if row["channel"] == "combined"}
    for item in expected:
        static = detection[(item["task"], SELECTION["control_a"], item["rule_id"])]
        rolling = detection[(item["task"], SELECTION["control_b"], item["rule_id"])]
        if not math.isclose(item["difference"], static - rolling, rel_tol=0, abs_tol=1e-12):
            raise AssertionError(f"{STEM}: {item['label']}: contrast disagrees with {DETECTION_TABLE.name}")
    check.note(f"all ten point differences equal static minus rolling detection in {DETECTION_TABLE.name}")

    # The stored bounds must be the quantiles of the committed paired draws.
    largest = 0.0
    for task in FOLDERS:
        design = json.loads(DESIGNS[task].read_text(encoding="utf-8"))
        bounds = draw_bounds(task)
        for item in (entry for entry in expected if entry["task"] == task):
            lower, upper, draws = bounds[item["rule_id"]]
            if item["draw_hash"] != design["draw_hash"] or item["valid_draws"] != draws:
                raise AssertionError(f"{STEM}: {item['label']}: draw design does not match the stored contrast")
            for stored, rederived in ((item["lower"], lower), (item["upper"], upper)):
                if abs(stored - rederived) > 1e-12:
                    raise AssertionError(f"{STEM}: {item['label']}: stored bound {stored!r}, draws give {rederived!r}")
                largest = max(largest, abs(stored - rederived))
    check.note(f"all 20 stored bounds equal the 2.5%/97.5% quantiles of {DRAW_COUNT:,} paired draws "
               f"(max |difference| = {largest:.2g})")

    written = c4.read_rows(DATA)
    plotted = c4.artists_by_gid(fig, GID)
    if len(written) != len(expected):
        raise AssertionError(f"{STEM}: {len(written)} data rows, expected {len(expected)}")
    for ax, task in zip(fig.axes, FOLDERS):
        check.text(ax.get_title(loc="left").split(") ", 1)[1], task, "panel order")
        ticks = list(ax.get_yticks())
        labels = [label.get_text() for label in ax.get_yticklabels()]
        items = [item for item in expected if item["task"] == task]
        if len(ticks) != len(items):
            raise AssertionError(f"{STEM}: {task}: {len(ticks)} plotted rows, expected {len(items)}")
        for y, label, item in zip(ticks, labels, items):
            name = item["label"]
            check.text(label, item["rule_label"], f"{name} row label")
            check.points(c4.line_points(plotted.pop(f"{GID}estimate|{name}")), [(item["estimate"], y)], f"{name} estimate")
            check.points(c4.line_points(plotted.pop(f"{GID}interval|{name}")),
                         [(item["low"], y), (item["high"], y)], f"{name} interval")
            annotation = plotted.pop(f"{GID}label|{name}")
            check.text(annotation.get_text(), estimate_label(item["estimate"]), f"{name} annotation")
            check.number(annotation.xy[0], item["estimate"], f"{name} annotation position")
        for value in plotted.pop(f"{GID}reference|{task}").get_xdata():
            check.number(value, 0.0, f"{task} zero reference line")
    for index, item in enumerate(expected):
        record, name = written[index], item["label"]
        check.text(record["row_label"], name, f"data row {index + 1} label")
        check.text(record["estimate_label"], estimate_label(item["estimate"]), f"data row {index + 1} estimate label")
        for column, value in (
            ("stored_point_difference", item["difference"]),
            ("stored_lower", item["lower"]),
            ("stored_upper", item["upper"]),
            ("estimate_pp", item["estimate"]),
            ("lower_bound_pp", item["low"]),
            ("upper_bound_pp", item["high"]),
        ):
            check.number(float(record[column]), value, f"data row {index + 1} {column}")
    if plotted:
        raise AssertionError(f"{STEM}: unverified artists {sorted(plotted)}")
    return check


def main() -> None:
    c4.apply_style()
    data = derive()
    data.to_csv(DATA, index=False, lineterminator="\n")
    fig = build(data)
    check = verify(fig)
    outputs = c4.save_figure(fig, STEM, f"Figure 4.9. {CAPTION}")
    plt.close(fig)
    c4.report(check, [*SOURCES.values(), DETECTION_TABLE, *DRAWS.values(), *DESIGNS.values()], [DATA, *outputs],
              caption=CAPTION_TEXT)


if __name__ == "__main__":
    main()
