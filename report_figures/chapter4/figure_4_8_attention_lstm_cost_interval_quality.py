"""Figure 4.8: computational cost and interval quality of Attention-LSTM relative to XGBoost.

Caption: Computational cost and interval quality of Attention-LSTM relative to XGBoost

Source: review/candidature_evidence_package_20261002_v1/REPORT_TABLES/ATTENTION_LSTM_VS_XGBOOST.csv

All 13 task-horizon rows are shown without further averaging, ordered by task
(PLEIAData temperature, PLEIAData energy, RICO HVAC, BDG2 electricity) and
then by increasing horizon. The 95% intervals are each forecasting model's
own split-conformal intervals, built from that model's calibration residuals;
the separate conformal-method comparison is not used.

(a) cpu_ratio_lstm_over_xgboost on a log axis, with a reference line at 1.
(b) Winkler improvement = 100 * (winkler95_xgboost - winkler95_attention_lstm)
    / winkler95_xgboost. Positive values mean a lower Winkler score for
    Attention-LSTM. The RICO HVAC rows lie far below the axis minimum, so
    their bars are truncated with a break mark and labelled with the exact
    value; the derived data file keeps the full values.
(c) coverage95_xgboost and coverage95_attention_lstm as paired dots on a
    common 0-1 axis, with a reference line at the nominal 0.95.

Outputs: figure_4_8_attention_lstm_cost_interval_quality.png / .pdf and the
derived figure data figure_4_8_attention_lstm_cost_interval_quality_data.csv.

Usage:
    python report_figures/chapter4/figure_4_8_attention_lstm_cost_interval_quality.py
"""

from __future__ import annotations

import math

import chapter4_style as c4
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
from matplotlib.transforms import blended_transform_factory

STEM = "figure_4_8_attention_lstm_cost_interval_quality"
CAPTION = "Computational cost and interval quality of Attention-LSTM relative to XGBoost"
SOURCE = c4.TABLES / "ATTENTION_LSTM_VS_XGBOOST.csv"
DATA = c4.OUT_DIR / f"{STEM}_data.csv"
GID = "fig4.8|"
ROWS = 13
NOMINAL = 0.95
WINKLER_AXIS = (-30.0, 10.0)  # bars below the minimum are truncated and labelled
HEADER_GAP = 0.45  # extra space, in rows, before each task header
HEADER_X = 0.006   # figure fraction where task headers start
RIGHT = 0.968      # figure fraction of the panels' right edge; keeps the "1.0" tick inside the text width
XGBOOST = c4.MODEL_SERIES["xgboost"]
LSTM = c4.MODEL_SERIES["attention_lstm"]
CAPTION_TEXT = (
    "Computational cost and interval quality of Attention-LSTM relative to XGBoost for the 13 matched task and "
    "horizon combinations. (a) Ratio of recorded process CPU time, Attention-LSTM to XGBoost (logarithmic axis). "
    "(b) Percentage improvement in the 95% Winkler score of Attention-LSTM over XGBoost, "
    "100 × (W_XGBoost − W_Attention-LSTM) / W_XGBoost; positive values favour Attention-LSTM, and the four RICO HVAC "
    "bars are truncated at −30% and labelled with their values. (c) Empirical coverage of each model's own 95% "
    "split-conformal intervals, built from that model's calibration residuals; the dashed line marks 0.95. Values "
    "are equal-fold summaries over three outer folds and five model seeds."
)


def percent_label(value: float) -> str:
    return f"{value:,.0f}%".replace("-", "\N{MINUS SIGN}")


def row_key(task: str, minutes: float) -> str:
    return f"{task}|{float(minutes):g}"


def derive(frame) -> pd.DataFrame:
    if len(frame) != ROWS or frame.duplicated(["task", "horizon_minutes"]).any():
        raise ValueError(f"expected {ROWS} unique task-horizon rows")
    order = {task: index for index, task in enumerate(c4.TASK_ORDER)}
    frame = frame.assign(task_order=frame["task"].map(order)).sort_values(["task_order", "horizon_minutes"])
    xgboost, lstm = frame["winkler95_xgboost"], frame["winkler95_attention_lstm"]
    improvement = 100.0 * (xgboost - lstm) / xgboost
    return pd.DataFrame(
        {
            "row_order": range(1, ROWS + 1),
            "dataset": frame["dataset"].to_numpy(),
            "task": frame["task"].to_numpy(),
            "horizon_minutes": frame["horizon_minutes"].to_numpy(),
            "horizon_label": [c4.horizon_text(t, m) for t, m in zip(frame["task"], frame["horizon_minutes"])],
            "cpu_ratio_lstm_over_xgboost": frame["cpu_ratio_lstm_over_xgboost"].to_numpy(),
            "winkler95_xgboost": xgboost.to_numpy(),
            "winkler95_attention_lstm": lstm.to_numpy(),
            "winkler_improvement_pct": improvement.to_numpy(),
            "winkler_bar_truncated": (improvement < WINKLER_AXIS[0]).to_numpy(),
            "winkler_bar_display_pct": improvement.clip(lower=WINKLER_AXIS[0]).to_numpy(),
            "coverage95_xgboost": frame["coverage95_xgboost"].to_numpy(),
            "coverage95_attention_lstm": frame["coverage95_attention_lstm"].to_numpy(),
            "source_table": c4.repo_relative(SOURCE),
            "source_commit": frame["source_commit"].to_numpy(),
            "source_path": frame["source_path"].to_numpy(),
        }
    )


def row_positions(data) -> tuple[list[float], dict[str, float]]:
    """Data rows top to bottom, with a header row before each task."""
    positions, headers, y = [], {}, 0.0
    for task in c4.TASK_ORDER:
        if headers:
            y += HEADER_GAP
        headers[task] = y
        y += 1.0
        for _ in range(int((data["task"] == task).sum())):
            positions.append(y)
            y += 1.0
    return positions, headers


def log_ratio_axis(ax) -> None:
    ax.set_xscale("log")
    ax.set_xlim(0.8, 150)
    ax.xaxis.set_major_locator(FixedLocator([1, 3, 10, 30, 100]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.xaxis.set_minor_formatter(NullFormatter())


def break_mark(ax, x: float, y: float) -> None:
    """Two white slashes across a truncated bar, just inside the axis minimum."""
    for offset in (1.6, 2.9):
        ax.plot(
            [x + offset - 0.55, x + offset + 0.55], [y + 0.42, y - 0.42],
            color=c4.SURFACE, linewidth=1.3, solid_capstyle="butt", zorder=3,
        )


def fit_label_column(fig, grid, headers) -> None:
    """Move the panels right until the widest task header clears panel (a)."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    right = max(text.get_window_extent(renderer).x1 for text in headers) / fig.bbox.width
    grid.update(left=right + 0.012)


def build(data):
    fig = plt.figure(figsize=(c4.FULL_WIDTH, 4.7))
    grid = fig.add_gridspec(1, 3, left=0.25, right=RIGHT, bottom=0.14, top=0.895, wspace=0.24)
    ax_cpu = fig.add_subplot(grid[0, 0])
    ax_winkler = fig.add_subplot(grid[0, 1], sharey=ax_cpu)
    ax_coverage = fig.add_subplot(grid[0, 2], sharey=ax_cpu)
    positions, header_rows = row_positions(data)

    for y, row in zip(positions, data.itertuples(index=False)):
        key = row_key(row.task, row.horizon_minutes)
        for ax in (ax_cpu, ax_winkler, ax_coverage):
            ax.axhline(y, color=c4.GRID, linewidth=0.5, zorder=0)

        ratio = row.cpu_ratio_lstm_over_xgboost
        ax_cpu.plot([1.0, ratio], [y, y], color=c4.RULE, linewidth=1.2, solid_capstyle="butt",
                    zorder=2, gid=f"{GID}cpu-stem|{key}")
        ax_cpu.plot([ratio], [y], linestyle="none", marker="o", markersize=5.5, color=c4.INK_2,
                    markeredgecolor=c4.SURFACE, markeredgewidth=0.8, zorder=3, gid=f"{GID}cpu|{key}")

        (bar,) = ax_winkler.barh(y, row.winkler_bar_display_pct, height=0.62, color=c4.INK_2, zorder=2)
        bar.set_gid(f"{GID}winkler|{key}")
        if row.winkler_bar_truncated:
            break_mark(ax_winkler, WINKLER_AXIS[0], y)
            ax_winkler.text(
                WINKLER_AXIS[0] + 5.0, y, percent_label(row.winkler_improvement_pct),
                ha="left", va="center", fontsize=c4.NOTE_SIZE, color=c4.SURFACE, zorder=4,
                gid=f"{GID}winkler-label|{key}",
            )

        ax_coverage.plot([row.coverage95_xgboost, row.coverage95_attention_lstm], [y, y],
                         color=c4.RULE, linewidth=1.2, solid_capstyle="butt", zorder=2)
        # The smaller diamond goes on top, so the triangle's corners stay
        # visible where the two coverages coincide.
        for model, series, value in (
            ("xgboost", XGBOOST, row.coverage95_xgboost),
            ("attention_lstm", LSTM, row.coverage95_attention_lstm),
        ):
            ax_coverage.plot(
                [value], [y], linestyle="none", marker=series.marker,
                markersize=c4.marker_size(series.marker), color=series.color,
                markeredgecolor=c4.SURFACE, markeredgewidth=c4.RING_WIDTH, zorder=3,
                gid=f"{GID}coverage|{model}|{key}",
            )

    reference = {"color": c4.INK_2, "linewidth": 0.9, "linestyle": c4.REFERENCE_DASH, "zorder": 1}
    ax_cpu.axvline(1.0, gid=f"{GID}cpu-reference", **reference)
    ax_coverage.axvline(NOMINAL, gid=f"{GID}coverage-reference", **reference)
    ax_winkler.axvline(0.0, color=c4.INK_2, linewidth=0.8, zorder=3)

    log_ratio_axis(ax_cpu)
    ax_winkler.set_xlim(*WINKLER_AXIS)
    ax_winkler.set_xticks([-30, -20, -10, 0, 10])
    ax_coverage.set_xlim(0, 1)
    # At 9 pt the narrow panel fits three labelled ticks; minor ticks keep the 0.1 steps.
    ax_coverage.set_xticks([0, 0.5, 1.0], ["0.0", "0.5", "1.0"])
    ax_coverage.set_xticks([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9], minor=True)

    ax_cpu.set_yticks(positions, data["horizon_label"].tolist())
    ax_cpu.set_ylim(positions[-1] + 0.7, -0.7)
    for ax in (ax_cpu, ax_winkler, ax_coverage):
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0, pad=3)
    for ax in (ax_winkler, ax_coverage):
        ax.tick_params(axis="y", labelleft=False)

    ax_cpu.set_xlabel("Attention-LSTM to\nXGBoost CPU ratio")
    ax_winkler.set_xlabel("Winkler improvement\nof Attention-LSTM (%)")
    ax_coverage.set_xlabel("Empirical coverage\n(own 95% intervals)")
    c4.panel_title(ax_cpu, "a", "CPU cost")
    c4.panel_title(ax_winkler, "b", "Winkler score")
    c4.panel_title(ax_coverage, "c", "Coverage")

    to_rows = blended_transform_factory(fig.transFigure, ax_cpu.transData)
    headers = [
        fig.text(HEADER_X, y, task, transform=to_rows, ha="left", va="center",
                 fontweight="bold", color=c4.INK, gid=f"{GID}header|{task}")
        for task, y in header_rows.items()
    ]
    fit_label_column(fig, grid, headers)

    handles = [
        Line2D([], [], linestyle="none", marker=series.marker, markersize=c4.marker_size(series.marker),
               color=series.color, markeredgecolor=c4.SURFACE, markeredgewidth=c4.RING_WIDTH,
               label=series.label)
        for series in (XGBOOST, LSTM)
    ]
    handles.append(c4.reference_handle(f"Nominal coverage ({NOMINAL:g})"))
    left = ax_cpu.get_position().x0
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=((left + RIGHT) / 2, 1.0), ncol=3)
    return fig


def verify(fig) -> c4.ValueCheck:
    check = c4.ValueCheck(STEM)
    source = {row_key(row["task"], float(row["horizon_minutes"])): row for row in c4.read_rows(SOURCE)}
    if len(source) != ROWS:
        raise AssertionError(f"{STEM}: expected {ROWS} source rows, found {len(source)}")
    order = sorted(
        source,
        key=lambda key: (c4.TASK_ORDER.index(source[key]["task"]), float(source[key]["horizon_minutes"])),
    )
    written = c4.read_rows(DATA)
    plotted = c4.artists_by_gid(fig, GID)
    ax_cpu = fig.axes[0]
    ticks = list(ax_cpu.get_yticks())
    labels = [label.get_text() for label in ax_cpu.get_yticklabels()]
    if len(ticks) != ROWS or len(written) != ROWS:
        raise AssertionError(f"{STEM}: expected {ROWS} plotted rows and {ROWS} data rows")

    for index, key in enumerate(order):
        row = source[key]
        task, minutes = row["task"], float(row["horizon_minutes"])
        y = ticks[index]
        ratio = float(row["cpu_ratio_lstm_over_xgboost"])
        xgb_winkler, lstm_winkler = float(row["winkler95_xgboost"]), float(row["winkler95_attention_lstm"])
        improvement = 100.0 * (xgb_winkler - lstm_winkler) / xgb_winkler
        display = max(improvement, WINKLER_AXIS[0])
        coverage = {
            "xgboost": float(row["coverage95_xgboost"]),
            "attention_lstm": float(row["coverage95_attention_lstm"]),
        }

        # Consistency of the source row itself (not plotted directly).
        stored_difference = float(row["winkler95_difference_lstm_minus_xgboost"])
        cpu_seconds = float(row["process_cpu_seconds_attention_lstm"]) / float(row["process_cpu_seconds_xgboost"])
        if not math.isclose(improvement, -100.0 * stored_difference / xgb_winkler, rel_tol=1e-9):
            raise AssertionError(f"{STEM}: {key}: improvement disagrees with the stored difference")
        if not math.isclose(ratio, cpu_seconds, rel_tol=1e-9):
            raise AssertionError(f"{STEM}: {key}: CPU ratio disagrees with the stored CPU seconds")

        check.text(labels[index], c4.horizon_text(task, minutes), f"row {index + 1} label")
        check.points(c4.line_points(plotted.pop(f"{GID}cpu|{key}")), [(ratio, y)], f"{key} CPU ratio")
        check.points(c4.line_points(plotted.pop(f"{GID}cpu-stem|{key}")), [(1.0, y), (ratio, y)], f"{key} CPU stem")
        bar = plotted.pop(f"{GID}winkler|{key}")
        check.number(bar.get_x(), 0.0, f"{key} Winkler bar base")
        check.number(bar.get_width(), display, f"{key} Winkler bar")
        check.number(bar.get_y() + bar.get_height() / 2, y, f"{key} Winkler bar row", tolerance=1e-12)
        label = plotted.pop(f"{GID}winkler-label|{key}", None)
        if (label is not None) != (improvement < WINKLER_AXIS[0]):
            raise AssertionError(f"{STEM}: {key}: truncation label does not match the truncation rule")
        if label is not None:
            check.text(label.get_text(), percent_label(improvement), f"{key} truncated Winkler label")
        for model, value in coverage.items():
            check.points(c4.line_points(plotted.pop(f"{GID}coverage|{model}|{key}")), [(value, y)],
                         f"{key} {model} coverage")

        record = written[index]
        check.text(record["task"], task, f"data row {index + 1} task")
        check.text(record["horizon_label"], c4.horizon_text(task, minutes), f"data row {index + 1} horizon")
        check.text(record["winkler_bar_truncated"], str(improvement < WINKLER_AXIS[0]), f"data row {index + 1} truncation")
        for column, value in (
            ("horizon_minutes", minutes),
            ("cpu_ratio_lstm_over_xgboost", ratio),
            ("winkler95_xgboost", xgb_winkler),
            ("winkler95_attention_lstm", lstm_winkler),
            ("winkler_improvement_pct", improvement),
            ("winkler_bar_display_pct", display),
            ("coverage95_xgboost", coverage["xgboost"]),
            ("coverage95_attention_lstm", coverage["attention_lstm"]),
        ):
            check.number(float(record[column]), value, f"data row {index + 1} {column}")

    for gid, x in ((f"{GID}cpu-reference", 1.0), (f"{GID}coverage-reference", NOMINAL)):
        for value in plotted.pop(gid).get_xdata():
            check.number(value, x, gid)
    headers = {gid: plotted.pop(gid) for gid in list(plotted) if gid.startswith(f"{GID}header|")}
    check.keys([text.get_text() for text in headers.values()], c4.TASK_ORDER, "task headers")
    if plotted:
        raise AssertionError(f"{STEM}: unverified artists {sorted(plotted)}")
    return check


def main() -> None:
    c4.apply_style()
    data = derive(c4.read_table(SOURCE))
    data.to_csv(DATA, index=False, lineterminator="\n")
    fig = build(data)
    check = verify(fig)
    outputs = c4.save_figure(fig, STEM, f"Figure 4.8. {CAPTION}")
    plt.close(fig)
    c4.report(check, [SOURCE], [DATA, *outputs], caption=CAPTION_TEXT)


if __name__ == "__main__":
    main()
