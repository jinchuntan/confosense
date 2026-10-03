"""Figure 4.7: observed and right-censored coverage recovery by recalibration strategy.

Caption: Observed and censored coverage recovery under static, periodic and rolling recalibration

Source: review/candidature_evidence_package_20261002_v1/REPORT_TABLES/ROBUSTNESS_RECOVERY_SUMMARY.csv

Recovery is assessed after level_shift@2 for each physical test group of the
15 fold-seed units of a setting, under each recalibration strategy. A case is
one test group within one fold and seed combination under the stated
strategy; group_policy_rows counts the evaluated cases of a setting and
strategy (BDG2 150, PLEIAData 15 each, RICO 625). Following
src.operational004_metrics.group_recovery, a case recovers at the first point
after the disturbance window where trailing coverage (one day of steps, or a
quarter of the follow-up if shorter) is within 0.05 of the group's pre-fault
coverage. Each bar is one stored row, shown as shares of its evaluated cases:

    observed share = 100 * observed_recoveries / group_policy_rows
    censored share = 100 * right_censored / group_policy_rows

Right-censored cases did not recover within their follow-up. They keep their
own hatched segment and are never given a recovery time; the figure plots no
recovery times at all. Each bar is labelled with its observed recoveries and
evaluated cases.

Cross-check: the counts are recounted from the 2,415 group-level rows in
review/robustness_contamination_recovery_20260928/AGGREGATE_RECOVERY_BY_GROUP.csv,
where no right-censored row carries a recovery time.

Outputs: figure_4_7_recalibration_recovery.png / .pdf and the derived figure
data figure_4_7_recalibration_recovery_data.csv.

Usage:
    python report_figures/chapter4/figure_4_7_recalibration_recovery.py
"""

from __future__ import annotations

import math
import re

import chapter4_style as c4
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

STEM = "figure_4_7_recalibration_recovery"
CAPTION = "Observed and censored coverage recovery under static, periodic and rolling recalibration"
SOURCE = c4.TABLES / "ROBUSTNESS_RECOVERY_SUMMARY.csv"
GROUP_SOURCE = c4.REPO / "review" / "robustness_contamination_recovery_20260928" / "AGGREGATE_RECOVERY_BY_GROUP.csv"
DATA = c4.OUT_DIR / f"{STEM}_data.csv"
GID = "fig4.7|"
STRATEGIES = {"static": "Static", "periodic": "Periodic", "rolling": "Rolling"}
GROUP_ROWS = 2415  # 805 test groups x three strategies
BAR_HEIGHT = 0.62
LABEL_X = 2.0  # percent; labels start just inside each observed segment
OBSERVED = {"facecolor": c4.INK_2}
CENSORED = {"facecolor": c4.GRID, "hatch": "////", "hatchcolor": c4.MUTED}
OBSERVED_LABEL = "Observed recovery"
CENSORED_LABEL = "Right-censored (no recovery within follow-up)"
X_LABEL = "Share of evaluated cases (%)"
CAPTION_TEXT = (
    "Recovery of interval coverage after a level shift at severity 2 under static, periodic and rolling "
    "recalibration. A case is one test group within one fold and seed combination under the stated recalibration "
    "strategy, so each setting contributes the same cases to every strategy (15 for each PLEIAData task, 625 for "
    "RICO HVAC and 150 for BDG2 electricity). A case recovers at the first point after the disturbance window at "
    "which coverage over a trailing window (one day of steps, or a quarter of the follow-up if shorter) is within "
    "0.05 of that group's pre-fault coverage. Solid segments are cases with an observed recovery; hatched segments "
    "are right-censored cases, in which no recovery was observed before follow-up ended. Censored cases are kept "
    "separate and are not assigned a recovery time. Labels give observed recoveries out of evaluated cases."
)


def count_label(observed: int, cases: int) -> str:
    return f"{observed:,} of {cases:,}"


def derive(frame) -> pd.DataFrame:
    if frame.duplicated(["task", "recovery_policy"]).any():
        raise ValueError("more than one recovery row for a setting and strategy")
    records = []
    for task in c4.TASK_ORDER:
        for strategy, label in STRATEGIES.items():
            selected = frame[(frame["task"] == task) & (frame["recovery_policy"] == strategy)]
            if len(selected) != 1:
                raise ValueError(f"expected one {strategy} row for {task}, found {len(selected)}")
            row = selected.iloc[0]
            cases, observed, censored = int(row["group_policy_rows"]), int(row["observed_recoveries"]), int(row["right_censored"])
            if observed + censored != cases:
                raise ValueError(f"{task}, {strategy}: observed and censored do not sum to the evaluated cases")
            records.append(
                {
                    "row_order": len(records) + 1,
                    "dataset": row["dataset"],
                    "task": task,
                    "cell": row["cell"],
                    "strategy": label,
                    "evaluated_cases": cases,
                    "observed_recoveries": observed,
                    "right_censored": censored,
                    "observed_share_pct": 100.0 * observed / cases,
                    "censored_share_pct": 100.0 * censored / cases,
                    "stored_observed_fraction": row["observed_fraction"],
                    "count_label": count_label(observed, cases),
                    "source_table": c4.repo_relative(SOURCE),
                    "source_commit": row["source_commit"],
                    "source_path": row["source_path"],
                }
            )
    return pd.DataFrame(records)


def build(data):
    fig, axes = plt.subplots(
        2, 2, figsize=(c4.FULL_WIDTH, 3.35), layout="constrained", sharex=True, sharey=True
    )
    fig.get_layout_engine().set(wspace=0.08)  # keeps "100" in (c) clear of "0" in (d)
    positions = list(range(len(STRATEGIES)))
    for ax, letter, task in zip(axes.flat, "abcd", c4.TASK_ORDER):
        for y, record in zip(positions, data[data["task"] == task].itertuples(index=False)):
            key = f"{task}|{record.strategy}"
            (observed,) = ax.barh(y, record.observed_share_pct, height=BAR_HEIGHT, left=0.0,
                                  edgecolor=c4.SURFACE, linewidth=1.0, zorder=2, **OBSERVED)
            observed.set_gid(f"{GID}observed|{key}")
            if record.right_censored:
                (censored,) = ax.barh(y, record.censored_share_pct, height=BAR_HEIGHT, left=record.observed_share_pct,
                                      edgecolor=c4.SURFACE, linewidth=1.0, zorder=2, **CENSORED)
                censored.set_hatch_linewidth(0.6)
                censored.set_gid(f"{GID}censored|{key}")
            ax.text(LABEL_X, y, record.count_label, ha="left", va="center_baseline", fontsize=c4.NOTE_SIZE,
                    color=c4.label_color(OBSERVED["facecolor"]), zorder=3, gid=f"{GID}label|{key}")
        ax.set_yticks(positions, list(STRATEGIES.values()))
        ax.set_ylim(len(positions) - 0.5, -0.5)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.tick_params(axis="y", length=0, pad=4)
        ax.spines["left"].set_visible(False)
        ax.xaxis.grid(True)
        ax.set_axisbelow(True)
        c4.panel_title(ax, letter, task)
    fig.supxlabel(X_LABEL, fontsize=c4.TEXT_SIZE)
    censored_handle = Patch(edgecolor=c4.SURFACE, label=CENSORED_LABEL, **CENSORED)
    censored_handle.set_hatch_linewidth(0.6)
    fig.legend(
        handles=[Patch(edgecolor="none", label=OBSERVED_LABEL, **OBSERVED), censored_handle],
        loc="outside upper center", ncol=2, handlelength=1.6, handleheight=0.9,
    )
    return fig


def label_fits(fig, label, bar) -> bool:
    """The label sits inside its observed segment with room on both sides."""
    renderer = fig.canvas.get_renderer()
    text, segment = label.get_window_extent(renderer), bar.get_window_extent(renderer)
    return text.x0 >= segment.x0 + 2 and text.x1 <= segment.x1 - 2 and text.y0 >= segment.y0 and text.y1 <= segment.y1


def verify(fig) -> c4.ValueCheck:
    check = c4.ValueCheck(STEM)
    source = {(row["task"], row["recovery_policy"]): row for row in c4.read_rows(SOURCE)}
    wanted = {(task, strategy) for task in c4.TASK_ORDER for strategy in STRATEGIES}
    check.keys({"|".join(key) for key in source}, {"|".join(key) for key in wanted}, "settings and strategies")

    # Recount every case from the group-level rows.
    groups: dict[tuple[str, str], dict[str, int]] = {}
    times_on_censored = times_missing_on_observed = 0
    rows = c4.read_rows(GROUP_SOURCE)
    for row in rows:
        dataset = re.fullmatch(r"(.+)_h\d+_f\d_s\d+", row["unit"]).group(1)
        counts = groups.setdefault((dataset, row["cell"]), {"observed": 0, "right_censored": 0})
        counts[row["status"]] += 1
        if (row["status"] == "right_censored") != (row["recovery_censored"] == "True"):
            raise AssertionError(f"{STEM}: {row['unit']} {row['group_id']}: status and censoring flag disagree")
        if row["status"] == "right_censored" and row["recovery_minutes"]:
            times_on_censored += 1
        if row["status"] == "observed" and not row["recovery_minutes"]:
            times_missing_on_observed += 1
    if len(rows) != GROUP_ROWS or times_on_censored or times_missing_on_observed:
        raise AssertionError(f"{STEM}: {len(rows)} group rows, {times_on_censored} censored rows with a time, "
                             f"{times_missing_on_observed} observed rows without one")
    for (task, strategy), row in source.items():
        cases, observed, censored = int(row["group_policy_rows"]), int(row["observed_recoveries"]), int(row["right_censored"])
        recount = groups[(row["dataset"], row["cell"])]
        if (observed, censored) != (recount["observed"], recount["right_censored"]) or observed + censored != cases:
            raise AssertionError(f"{STEM}: {task}, {strategy}: counts disagree with {GROUP_SOURCE.name}")
        if not math.isclose(float(row["observed_fraction"]), observed / cases, rel_tol=0, abs_tol=1e-11):
            raise AssertionError(f"{STEM}: {task}, {strategy}: stored fraction disagrees with the counts")
    check.note(f"all 12 rows recounted from the {GROUP_ROWS:,} group-level rows; observed + censored = evaluated cases")
    check.note("no right-censored group row carries a recovery time, and no recovery time is plotted")

    written = c4.read_rows(DATA)
    if len(written) != len(source):
        raise AssertionError(f"{STEM}: {len(written)} data rows, expected {len(source)}")
    fig.canvas.draw()  # final constrained layout, so label and bar extents can be measured
    plotted = c4.artists_by_gid(fig, GID)
    for index, (ax, task) in enumerate(zip(fig.axes, c4.TASK_ORDER)):
        check.text(ax.get_title(loc="left").split(") ", 1)[1], task, "panel order")
        # The y axis is shared; strategy names are printed in the left column only.
        check.text(" / ".join(f"{tick:g}" for tick in ax.get_yticks()), "0 / 1 / 2", f"{task} strategy rows")
        if index % 2 == 0:
            check.text(" / ".join(label.get_text() for label in ax.get_yticklabels()),
                       " / ".join(STRATEGIES.values()), f"{task} strategy order")
        for y, (strategy, label) in enumerate(STRATEGIES.items()):
            row, key = source[(task, strategy)], f"{task}|{label}"
            cases, observed, censored = int(row["group_policy_rows"]), int(row["observed_recoveries"]), int(row["right_censored"])
            observed_share, censored_share = 100.0 * observed / cases, 100.0 * censored / cases
            bar = plotted.pop(f"{GID}observed|{key}")
            check.number(bar.get_x(), 0.0, f"{key} observed start")
            check.number(bar.get_width(), observed_share, f"{key} observed share")
            check.number(bar.get_y() + bar.get_height() / 2, y, f"{key} row", tolerance=1e-12)
            check.color(bar.get_facecolor(), OBSERVED["facecolor"], f"{key} observed colour")
            segment = plotted.pop(f"{GID}censored|{key}", None)
            if (segment is not None) != (censored > 0):
                raise AssertionError(f"{STEM}: {key}: censored segment does not match {censored} censored cases")
            if segment is not None:
                check.number(segment.get_x(), observed_share, f"{key} censored start")
                # Matplotlib stores a stacked width as (left + width) - left, which can move the last bit.
                check.number(segment.get_width(), censored_share, f"{key} censored share", tolerance=1e-12)
                check.number(segment.get_x() + segment.get_width(), 100.0, f"{key} bar end", tolerance=1e-12)
                check.color(segment.get_facecolor(), CENSORED["facecolor"], f"{key} censored colour")
                check.text(segment.get_hatch(), CENSORED["hatch"], f"{key} censored hatch")
            text = plotted.pop(f"{GID}label|{key}")
            check.text(text.get_text(), count_label(observed, cases), f"{key} label")
            if not label_fits(fig, text, bar):
                raise AssertionError(f"{STEM}: {key}: label does not fit inside the observed segment")
            if c4.contrast_ratio(text.get_color(), bar.get_facecolor()) < c4.MIN_LABEL_CONTRAST:
                raise AssertionError(f"{STEM}: {key}: label contrast below {c4.MIN_LABEL_CONTRAST}:1")
            record = written[c4.TASK_ORDER.index(task) * len(STRATEGIES) + y]
            check.text(f"{record['task']}|{record['strategy']}", key, "data row order")
            check.text(record["count_label"], count_label(observed, cases), f"{key} data label")
            for column, value in (
                ("evaluated_cases", cases), ("observed_recoveries", observed), ("right_censored", censored),
                ("observed_share_pct", observed_share), ("censored_share_pct", censored_share),
            ):
                check.number(float(record[column]), value, f"{key} data {column}")
    check.note("every count label fits inside its observed segment")
    if plotted:
        raise AssertionError(f"{STEM}: unverified artists {sorted(plotted)}")
    legend = fig.legends[0]
    check.text(" / ".join(text.get_text() for text in legend.get_texts()),
               f"{OBSERVED_LABEL} / {CENSORED_LABEL}", "legend")
    return check


def main() -> None:
    c4.apply_style()
    data = derive(c4.read_table(SOURCE))
    data.to_csv(DATA, index=False, lineterminator="\n")
    fig = build(data)
    check = verify(fig)
    outputs = c4.save_figure(fig, STEM, f"Figure 4.7. {CAPTION}")
    plt.close(fig)
    c4.report(check, [SOURCE, GROUP_SOURCE], [DATA, *outputs], caption=CAPTION_TEXT)


if __name__ == "__main__":
    main()
