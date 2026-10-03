"""Figure 4.1: point-forecast MAE by forecast horizon.

Source: review/candidature_evidence_package_20261002_v1/REPORT_TABLES/POINT_FORECASTING.csv

The stored aggregate MAE values are plotted directly, with no confidence
intervals, interpolation or re-aggregation. The table has no seasonal-naive
row for RICO HVAC (the baseline is inapplicable under the frozen design), so
that series is absent from panel (c).

Usage:
    python report_figures/chapter4/figure_4_1_point_forecasting_mae.py
"""

from __future__ import annotations

import chapter4_style as c4
import matplotlib.pyplot as plt

STEM = "figure_4_1_point_forecasting_mae"
TITLE = "Figure 4.1. Point-forecast MAE by forecast horizon"
SOURCE = c4.TABLES / "POINT_FORECASTING.csv"
GID = "fig4.1|"
EXPECTED_ABSENT = [("RICO HVAC", "seasonal_naive")]
CAPTION_TEXT = (
    "Mean absolute error (MAE) of persistence, seasonal naïve, XGBoost and Attention-LSTM point forecasts at "
    "each evaluated horizon. Each point is the stored equal-weight mean of the three outer-fold means, each "
    "averaged over five model seeds; seasonal naïve is deterministic, so its value is the mean of three unique "
    "fold computations. MAE is in each task's target units (°C, kWh per 10 min or kWh per hour), so values are "
    "not comparable across panels. Seasonal naïve is not applicable to RICO HVAC under the frozen design. Folds "
    "overlap and seeds are not independent replicates, so no intervals are shown."
)


def build(frame):
    if frame.duplicated(["task", "horizon_minutes", "model"]).any():
        raise ValueError("more than one MAE row for a task, horizon and model")
    fig, axes = plt.subplots(2, 2, figsize=(c4.FULL_WIDTH, 5.3), layout="constrained")
    absent = []
    for ax, letter, task in zip(axes.flat, "abcd", c4.TASK_ORDER):
        rows = frame[frame["task"] == task]
        for model, series in c4.MODEL_SERIES.items():
            subset = rows[rows["model"] == model].sort_values("horizon_minutes")
            if subset.empty:
                absent.append((task, model))
                continue
            x = [c4.horizon_value(task, minutes) for minutes in subset["horizon_minutes"]]
            c4.plot_series(ax, x, subset["mae"].tolist(), series, gid=f"{GID}{task}|{model}")
        c4.format_horizon_axis(ax, task, rows["horizon_minutes"].unique())
        ax.set_ylim(bottom=0)
        ax.set_ylabel(f"MAE ({c4.unit_label(rows['target_unit'])})")
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        c4.panel_title(ax, letter, task)
        if any(missing_task == task for missing_task, _ in absent):
            ax.text(
                0.97, 0.05, f"{c4.MODEL_SERIES['seasonal_naive'].label} not applicable",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=c4.NOTE_SIZE, color=c4.MUTED,
            )
    if absent != EXPECTED_ABSENT:
        raise ValueError(f"unexpected missing series: {absent}")
    fig.legend(
        handles=[c4.series_handle(series) for series in c4.MODEL_SERIES.values()],
        loc="outside upper center", ncol=4,
    )
    return fig


def verify(fig) -> c4.ValueCheck:
    check = c4.ValueCheck(STEM)
    expected: dict[str, list[tuple[float, float]]] = {}
    for row in c4.read_rows(SOURCE):
        point = (c4.horizon_value(row["task"], float(row["horizon_minutes"])), float(row["mae"]))
        expected.setdefault(f"{GID}{row['task']}|{row['model']}", []).append(point)
    plotted = c4.artists_by_gid(fig, GID)
    check.keys(plotted, expected, "plotted series")
    for gid, line in plotted.items():
        check.points(c4.line_points(line), expected[gid], gid)
        check.color(line.get_color(), c4.MODEL_SERIES[gid.rsplit("|", 1)[1]].color, gid)
    return check


def main() -> None:
    c4.apply_style()
    fig = build(c4.read_table(SOURCE))
    check = verify(fig)
    outputs = c4.save_figure(fig, STEM, TITLE)
    plt.close(fig)
    c4.report(check, [SOURCE], outputs, caption=CAPTION_TEXT)


if __name__ == "__main__":
    main()
