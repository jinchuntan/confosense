"""Publication-quality figures for the preliminary experiment.

Every figure is written to ``outputs/figures`` at 150 dpi with a non-interactive
backend so the pipeline runs headless.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def _save(fig, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_data_split(series: pd.Series, t_train_end, t_calib_end, path) -> None:
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(series.index, series.values, color="#333333", lw=0.6)
    ymin, ymax = np.nanmin(series.values), np.nanmax(series.values)
    ax.axvspan(series.index[0], t_train_end, color="#4C72B0", alpha=0.12, label="Train (60%)")
    ax.axvspan(t_train_end, t_calib_end, color="#DD8452", alpha=0.15, label="Calibration (20%)")
    ax.axvspan(t_calib_end, series.index[-1], color="#55A868", alpha=0.15, label="Test (20%)")
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Time")
    ax.set_ylabel("Indoor temperature (°C)")
    ax.set_title("Chronological train / calibration / test split of the target series")
    ax.legend(loc="upper right", ncol=3, fontsize=8)
    _save(fig, path)


def plot_point_forecasts(window: pd.DataFrame, actual_col: str, model_cols: list[str], path) -> None:
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(window.index, window[actual_col], color="black", lw=1.6, label="Actual")
    for col in model_cols:
        if col in window:
            ax.plot(window.index, window[col], lw=1.0, alpha=0.9, label=col)
    ax.set_xlabel("Time")
    ax.set_ylabel("Indoor temperature (°C)")
    ax.set_title("Point forecasts on the first continuous test window (horizon 1)")
    ax.legend(loc="best", fontsize=8, ncol=3)
    _save(fig, path)


def plot_metric_comparison(metrics: pd.DataFrame, path) -> None:
    horizons = sorted(metrics["horizon"].unique())
    models = list(dict.fromkeys(metrics["model"]))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharex=True)
    for ax, metric in zip(axes, ["mae", "rmse"]):
        width = 0.8 / max(1, len(horizons))
        x = np.arange(len(models))
        for i, h in enumerate(horizons):
            sub = metrics[metrics["horizon"] == h].set_index("model").reindex(models)
            ax.bar(x + i * width, sub[metric].values, width=width, label=f"h={h}")
        ax.set_xticks(x + width * (len(horizons) - 1) / 2)
        ax.set_xticklabels(models, rotation=20, ha="right")
        ax.set_ylabel(metric.upper())
        ax.set_title(f"{metric.upper()} by model and horizon")
        ax.legend(fontsize=8)
    _save(fig, path)


def plot_conformal_intervals(df: pd.DataFrame, title: str, path) -> None:
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.fill_between(df["target_time"], df["lower"], df["upper"],
                    color="#4C72B0", alpha=0.25, label="Prediction interval")
    ax.plot(df["target_time"], df["y_true"], color="black", lw=1.2, label="Actual")
    ax.plot(df["target_time"], df["point"], color="#C44E52", lw=1.0, label="Point forecast")
    viol = df[(df["y_true"] < df["lower"]) | (df["y_true"] > df["upper"])]
    ax.scatter(viol["target_time"], viol["y_true"], color="#C44E52", s=18, zorder=5,
               label="Interval violation")
    ax.set_xlabel("Time")
    ax.set_ylabel("Indoor temperature (°C)")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8, ncol=2)
    _save(fig, path)


def plot_alert_timeline(df: pd.DataFrame, catalog: pd.DataFrame, title: str, path) -> None:
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.fill_between(df["target_time"], df["lower"], df["upper"],
                    color="#4C72B0", alpha=0.22, label="Prediction interval")
    ax.plot(df["target_time"], df["observed"], color="black", lw=1.1, label="Observed (perturbed)")

    for _, row in catalog.iterrows():
        ax.axvspan(row["start_time"], row["end_time"], color="#DD8452", alpha=0.20)
    # A single proxy handle for the event shading.
    ax.axvspan(df["target_time"].iloc[0], df["target_time"].iloc[0],
               color="#DD8452", alpha=0.20, label="Injected event")

    viol = df[df["violation"]]
    ax.scatter(viol["target_time"], viol["observed"], color="#C44E52", s=14, zorder=5,
               label="Point violation")
    alert = df[df["alert"]]
    y0 = np.nanmin(df["lower"].values)
    ax.scatter(alert["target_time"], np.full(len(alert), y0), marker="^",
               color="#8172B3", s=26, zorder=6, label="Aggregated alert")

    ax.set_xlabel("Time")
    ax.set_ylabel("Indoor temperature (°C)")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8, ncol=2)
    _save(fig, path)
