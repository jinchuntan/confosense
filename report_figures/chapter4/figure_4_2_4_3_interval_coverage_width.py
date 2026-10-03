"""Figures 4.2 and 4.3: 95% interval coverage and width by forecast horizon.

Source: review/candidature_evidence_package_20261002_v1/REPORT_TABLES/INTERVAL_METHODS_COMMON_SUPPORT.csv

Rows are filtered to level = 0.95 and support = common. The stored summary
values (median_coverage, median_mpiw; medians of 15 fold-seed cells) are
plotted directly, with no further aggregation and no error bars.

Usage:
    python report_figures/chapter4/figure_4_2_4_3_interval_coverage_width.py
"""

from __future__ import annotations

import chapter4_style as c4
import matplotlib.pyplot as plt

SOURCE = c4.TABLES / "INTERVAL_METHODS_COMMON_SUPPORT.csv"
LEVEL = 0.95
SUPPORT = "common"

FIGURES = (
    {
        "stem": "figure_4_2_interval_coverage",
        "title": "Figure 4.2. Median empirical coverage of 95% prediction intervals by forecast horizon",
        "column": "median_coverage",
        "gid": "fig4.2|",
        "coverage": True,
        "ylabel": "Median empirical coverage",
        "caption": (
            "Median empirical coverage of nominal 95% prediction intervals from five interval methods on common "
            "support, by forecast horizon. Each point is the stored median of 15 fold-seed cells (three outer folds "
            "and five model seeds); the dashed line marks the nominal level of 0.95. CQR and the uncalibrated "
            "quantile intervals share one quantile model, and the two recentred EnbPI variants share one ensemble. "
            "DSCP uses the matched XGBoost forecaster, so a contrast with DSCP changes the forecaster as well as the "
            "interval construction."
        ),
    },
    {
        "stem": "figure_4_3_interval_width",
        "title": "Figure 4.3. Median width of 95% prediction intervals by forecast horizon",
        "column": "median_mpiw",
        "gid": "fig4.3|",
        "coverage": False,
        "ylabel": "Median MPIW (",
        "caption": (
            "Median width of the nominal 95% prediction intervals shown in Figure 4.2, measured as mean "
            "prediction-interval width (MPIW) in each task's target units (°C, kWh per 10 min or kWh per hour). Each "
            "point is the stored median of 15 fold-seed cells on common support. Widths are not comparable across "
            "panels and should be read together with the coverage in Figure 4.2."
        ),
    },
)


def select(frame):
    rows = frame[(frame["level"] == LEVEL) & (frame["support"] == SUPPORT)]
    if rows.duplicated(["task", "horizon_minutes", "method"]).any():
        raise ValueError("more than one summary row for a task, horizon and method")
    return rows


def build(rows, spec):
    fig, axes = plt.subplots(2, 2, figsize=(c4.FULL_WIDTH, 5.5), layout="constrained")
    for index, (ax, letter, task) in enumerate(zip(axes.flat, "abcd", c4.TASK_ORDER)):
        task_rows = rows[rows["task"] == task]
        for method, series in c4.METHOD_SERIES.items():
            subset = task_rows[task_rows["method"] == method].sort_values("horizon_minutes")
            if subset.empty:
                raise ValueError(f"no {method} rows for {task}")
            x = [c4.horizon_value(task, minutes) for minutes in subset["horizon_minutes"]]
            c4.plot_series(ax, x, subset[spec["column"]].tolist(), series, gid=f"{spec['gid']}{task}|{method}")
        c4.format_horizon_axis(ax, task, task_rows["horizon_minutes"].unique())
        if spec["coverage"]:
            ax.axhline(
                LEVEL, color=c4.INK_2, linewidth=0.9, linestyle=c4.REFERENCE_DASH,
                zorder=2, gid=f"{spec['gid']}reference|{task}",
            )
            ax.set_ylim(0, 1)
            ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
            if index % 2 == 0:
                ax.set_ylabel("Median empirical coverage")
        else:
            ax.set_ylim(bottom=0)
            ax.set_ylabel(f"Median MPIW ({c4.unit_label(task_rows['target_unit'])})")
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        c4.panel_title(ax, letter, task)
    handles = [c4.series_handle(series) for series in c4.METHOD_SERIES.values()]
    if spec["coverage"]:
        handles.append(c4.reference_handle("Nominal coverage (0.95)"))
    fig.legend(handles=handles, loc="outside upper center", ncol=3)
    return fig


def verify(fig, spec) -> c4.ValueCheck:
    check = c4.ValueCheck(spec["stem"])
    expected: dict[str, list[tuple[float, float]]] = {}
    for row in c4.read_rows(SOURCE):
        if float(row["level"]) != LEVEL or row["support"] != SUPPORT:
            continue
        point = (c4.horizon_value(row["task"], float(row["horizon_minutes"])), float(row[spec["column"]]))
        expected.setdefault(f"{spec['gid']}{row['task']}|{row['method']}", []).append(point)
    plotted = c4.artists_by_gid(fig, spec["gid"])
    references = {gid: plotted.pop(gid) for gid in list(plotted) if gid.startswith(f"{spec['gid']}reference|")}
    check.keys(plotted, expected, "plotted series")
    for gid, line in plotted.items():
        check.points(c4.line_points(line), expected[gid], gid)
        check.color(line.get_color(), c4.METHOD_SERIES[gid.rsplit("|", 1)[1]].color, gid)
    if spec["coverage"]:
        check.keys(references, {f"{spec['gid']}reference|{task}" for task in c4.TASK_ORDER}, "reference lines")
        for gid, line in references.items():
            for y in line.get_ydata():
                check.number(y, LEVEL, gid)
    # Guards against the coverage and width figures being swapped or duplicated.
    labels = [ax.get_ylabel() for ax in fig.axes if ax.get_ylabel()]
    if not labels or not all(label.startswith(spec["ylabel"]) for label in labels):
        raise AssertionError(f"{spec['stem']}: y-axis labels {labels} do not name {spec['ylabel']!r}")
    return check


def main() -> None:
    c4.apply_style()
    rows = select(c4.read_table(SOURCE))
    for spec in FIGURES:
        fig = build(rows, spec)
        check = verify(fig, spec)
        outputs = c4.save_figure(fig, spec["stem"], spec["title"])
        plt.close(fig)
        c4.report(check, [SOURCE], outputs, caption=spec["caption"])


if __name__ == "__main__":
    main()
