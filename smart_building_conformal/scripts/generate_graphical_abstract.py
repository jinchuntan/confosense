"""Graphical abstract for the ConfoSense framework (dissertation Appendix A).

This is a conceptual summary of *what the framework does*. It is deliberately
free of experimental values: no MAE/RMSE, coverage, precision, recall or any
other measured quantity appears, so the graphic stays valid once the full
dissertation experiments are complete.

Design notes / academic accuracy
--------------------------------
* PLEIAData, RICO HVAC and BDG2 are shown as separate public sources evaluated
  under a common protocol — never merged into one training set.
* DSCP is marked as the extended implementation; it is not presented as having
  produced results.
* Alerts are framed as monitoring / decision support. No control action, energy
  saving or emission claim is made or implied.
* The chronological train / calibration / test separation is shown explicitly.

This script is intentionally standalone (it carries its own small copy of the
palette and style helpers) so that regenerating the abstract can never perturb
the methodology figures produced by ``generate_methodology_figures.py``.

Usage
-----
    python scripts/generate_graphical_abstract.py

Writes ``graphical_abstract.png`` (300 dpi) and ``graphical_abstract.svg``
(vector, editable text) into ``outputs/figures/``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.font_manager import FontProperties, findfont
from matplotlib.patches import Arc, Ellipse, FancyArrowPatch, Polygon, Rectangle

# --------------------------------------------------------------------------- #
# Canvas and palette
# --------------------------------------------------------------------------- #
FIG_W, FIG_H = 11.0, 4.8          # inches; landscape, full-page placement

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
RED = "#e34948"

INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
RULE = "#c3c2b7"
HAIR = "#e1e0d9"
SURFACE = "#ffffff"

TITLE_FS = 9.5
ITEM_FS = 6.8
SMALL_FS = 6.2
TINY_FS = 5.7
NAME_FS = 15.0


def _tint(color: str, whiteness: float) -> tuple[float, float, float]:
    r, g, b = to_rgb(color)
    return (r + (1.0 - r) * whiteness,
            g + (1.0 - g) * whiteness,
            b + (1.0 - b) * whiteness)


def _resolve_font() -> str:
    for family in ("Arial", "Helvetica", "DejaVu Sans"):
        try:
            if findfont(FontProperties(family=family), fallback_to_default=False):
                return family
        except Exception:
            continue
    return "DejaVu Sans"


def _apply_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [_resolve_font(), "DejaVu Sans"],
        "mathtext.fontset": "stixsans",
        "figure.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        # Keep SVG text as real text elements so the file stays editable.
        "svg.fonttype": "none",
    })


# Axis units are 0..1 on both axes over a non-square canvas, so a visually
# circular shape needs its x-radius shrunk by the canvas aspect ratio.
def _rx(inches: float) -> float:
    return inches / FIG_W


def _ry(inches: float) -> float:
    return inches / FIG_H


def _txt(ax, x, y, s, size=ITEM_FS, color=INK_2, weight="normal",
         ha="center", va="center", style="normal"):
    return ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
                   ha=ha, va=va, style=style, zorder=6)


# --------------------------------------------------------------------------- #
# Layout geometry
# --------------------------------------------------------------------------- #
GAP = 0.018
W_STAGE = 0.1181
W_OUT = 0.1594
X_LEFT = 0.010

BLOCK_Y0, BLOCK_Y1 = 0.075, 0.925
EMPH_Y0, EMPH_Y1 = 0.045, 0.955          # stage 4 is drawn taller for emphasis

STAGE_X = [X_LEFT + i * (W_STAGE + GAP) for i in range(6)]
OUT_X0 = STAGE_X[5] + W_STAGE + GAP


def _stage_box(i: int) -> tuple[float, float, float, float]:
    """(x0, x1, y0, y1) for stage ``i`` (0-based)."""
    x0 = STAGE_X[i]
    if i == 3:
        return x0, x0 + W_STAGE, EMPH_Y0, EMPH_Y1
    return x0, x0 + W_STAGE, BLOCK_Y0, BLOCK_Y1


def _draw_block(ax, x0, x1, y0, y1, *, accent, fill=SURFACE,
                edge=RULE, lw=1.0, accent_h=0.011) -> None:
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=fill,
                           edgecolor=edge, linewidth=lw, zorder=2))
    ax.add_patch(Rectangle((x0, y1 - accent_h), x1 - x0, accent_h,
                           facecolor=accent, edgecolor="none", zorder=3))


def _title(ax, x0, x1, y1, lines: list[str], color=INK) -> float:
    """Draw the (1-2 line) stage title; return the y of the divider below it."""
    cx = 0.5 * (x0 + x1)
    y = y1 - 0.058
    for line in lines:
        _txt(ax, cx, y, line, size=TITLE_FS, color=color, weight="bold")
        y -= 0.040
    y_div = y + 0.012
    ax.plot([x0 + 0.010, x1 - 0.010], [y_div, y_div], color=HAIR,
            linewidth=0.9, zorder=4)
    return y_div


def _stack(ax, cx, y_top, items, *, size=ITEM_FS, step=0.040, color=INK_2,
           weight="normal") -> float:
    y = y_top
    for item in items:
        _txt(ax, cx, y, item, size=size, color=color, weight=weight)
        y -= step
    return y


def _down_arrow(ax, x, y_from, y_to, color=MUTED) -> None:
    ax.add_patch(FancyArrowPatch((x, y_from), (x, y_to), arrowstyle="-|>",
                                 mutation_scale=6, linewidth=0.8,
                                 color=color, zorder=5))


# --------------------------------------------------------------------------- #
# Stage 1 — Smart-building IoT data
# --------------------------------------------------------------------------- #
def _stage_data(ax) -> None:
    x0, x1, y0, y1 = _stage_box(0)
    cx = 0.5 * (x0 + x1)
    _draw_block(ax, x0, x1, y0, y1, accent=BLUE)
    _title(ax, x0, x1, y1, ["Smart-Building", "IoT Data"])

    # --- building icon ---
    bw, bh = 0.058, 0.082
    bx, by = cx - bw / 2, 0.660
    ax.add_patch(Rectangle((bx, by), bw, bh, facecolor=_tint(BLUE, 0.88),
                           edgecolor=BLUE, linewidth=1.1, zorder=4))
    for r in range(3):
        for c in range(3):
            ax.add_patch(Rectangle(
                (bx + 0.009 + c * 0.0155, by + 0.012 + r * 0.0225),
                0.0088, 0.0135, facecolor=SURFACE, edgecolor=BLUE,
                linewidth=0.5, zorder=5))
    # sensor node + signal arcs
    top = by + bh
    ax.plot([cx, cx], [top, top + 0.016], color=INK_2, linewidth=0.9, zorder=4)
    ax.add_patch(Ellipse((cx, top + 0.021), 2 * _rx(0.020), 2 * _ry(0.020),
                         facecolor=INK_2, edgecolor="none", zorder=5))
    for r_in in (0.055, 0.085):
        ax.add_patch(Arc((cx, top + 0.021), 2 * _rx(r_in), 2 * _ry(r_in),
                         theta1=35, theta2=145, color=MUTED, linewidth=0.8,
                         zorder=4))

    _stack(ax, cx, 0.598, [
        "Indoor temperature",
        "Energy consumption",
        "Weather",
        "HVAC operation",
        "Occupancy / presence",
    ], size=6.6, step=0.0405)

    # --- public datasets ---
    dx0, dx1 = x0 + 0.011, x1 - 0.011
    ax.add_patch(Rectangle((dx0, 0.118), dx1 - dx0, 0.222,
                           facecolor=_tint(BLUE, 0.94), edgecolor=HAIR,
                           linewidth=0.8, zorder=3))
    _txt(ax, cx, 0.310, "Public datasets", size=SMALL_FS, color=MUTED)
    _stack(ax, cx, 0.266, ["PLEIAData", "RICO HVAC", "BDG2"],
           size=7.0, step=0.038, color=INK, weight="bold")
    _txt(ax, cx, 0.142, "evaluated independently", size=TINY_FS,
         color=MUTED, style="italic")


# --------------------------------------------------------------------------- #
# Stage 2 — Data preparation & features
# --------------------------------------------------------------------------- #
def _stage_prep(ax) -> None:
    x0, x1, y0, y1 = _stage_box(1)
    cx = 0.5 * (x0 + x1)
    _draw_block(ax, x0, x1, y0, y1, accent=BLUE)
    _title(ax, x0, x1, y1, ["Data Preparation", "& Features"])

    # --- series with a gap being repaired ---
    sx = np.linspace(cx - 0.043, cx + 0.043, 9)
    sy = 0.712 + 0.020 * np.array([0.2, 0.9, 0.4, -0.3, 0.1, 0.6, -0.2, 0.5, 0.15])
    ax.plot(sx[:4], sy[:4], color=INK, linewidth=1.1, zorder=4)
    ax.plot(sx[3:6], sy[3:6], color=MUTED, linewidth=1.0,
            linestyle=(0, (2, 2)), zorder=4)
    ax.plot(sx[5:], sy[5:], color=INK, linewidth=1.1, zorder=4)
    ax.plot(sx[4:5], sy[4:5], linestyle="none", marker="o", markersize=3.2,
            markerfacecolor=SURFACE, markeredgecolor=MUTED,
            markeredgewidth=0.9, zorder=5)

    _stack(ax, cx, 0.626, [
        "Cleaning",
        "Resampling",
        "Missing-data handling",
        "Lag & temporal features",
    ], size=6.6, step=0.0405)

    # --- chronological split bar ---
    _txt(ax, cx, 0.428, "Chronological split", size=SMALL_FS, color=INK,
         weight="bold")
    bx0, bx1 = x0 + 0.013, x1 - 0.013
    bw = bx1 - bx0
    by, bh = 0.352, 0.040
    for frac0, frac1, hue in ((0.0, 0.6, BLUE), (0.6, 0.8, ORANGE),
                              (0.8, 1.0, AQUA)):
        ax.add_patch(Rectangle((bx0 + frac0 * bw, by), (frac1 - frac0) * bw, bh,
                               facecolor=_tint(hue, 0.72), edgecolor=hue,
                               linewidth=0.9, zorder=4))

    for j, (label, hue) in enumerate((("Train  60 %", BLUE),
                                      ("Calibration  20 %", ORANGE),
                                      ("Test  20 %", AQUA))):
        ly = 0.300 - j * 0.037
        ax.add_patch(Rectangle((x0 + 0.018, ly - 0.008), 0.010, 0.016,
                               facecolor=_tint(hue, 0.55), edgecolor=hue,
                               linewidth=0.7, zorder=4))
        _txt(ax, x0 + 0.034, ly, label, size=SMALL_FS, ha="left")

    ax.add_patch(Rectangle((x0 + 0.013, 0.140), (x1 - 0.013) - (x0 + 0.013),
                           0.042, facecolor=_tint(AQUA, 0.90),
                           edgecolor=_tint(AQUA, 0.55), linewidth=0.8, zorder=3))
    _txt(ax, cx, 0.161, "Chronology preserved", size=SMALL_FS, color=INK,
         weight="bold")


# --------------------------------------------------------------------------- #
# Stage 3 — Short-term forecasting
# --------------------------------------------------------------------------- #
def _stage_forecast(ax) -> None:
    x0, x1, y0, y1 = _stage_box(2)
    cx = 0.5 * (x0 + x1)
    _draw_block(ax, x0, x1, y0, y1, accent=BLUE)
    _title(ax, x0, x1, y1, ["Short-Term", "Forecasting"])

    # --- observed continuing into a point forecast ---
    ox = np.linspace(cx - 0.046, cx + 0.004, 26)
    oy = 0.712 + 0.020 * np.sin(np.linspace(0.0, 3.4, 26))
    ax.plot(ox, oy, color=INK, linewidth=1.2, zorder=4)
    fx = np.linspace(cx + 0.004, cx + 0.046, 16)
    fy = oy[-1] + np.linspace(0.0, 0.020, 16)
    ax.plot(fx, fy, color=BLUE, linewidth=1.2, linestyle=(0, (2.5, 2)),
            zorder=4)
    ax.plot([cx + 0.004], [oy[-1]], linestyle="none", marker="o",
            markersize=2.8, color=INK, zorder=5)
    ax.plot([fx[-1]], [fy[-1]], linestyle="none", marker="o", markersize=4.2,
            markerfacecolor=BLUE, markeredgecolor=SURFACE, markeredgewidth=0.9,
            zorder=5)
    ax.plot([cx + 0.004, cx + 0.004], [0.672, 0.762], color=MUTED,
            linewidth=0.7, linestyle=(0, (2, 2)), zorder=3)

    _stack(ax, cx, 0.612, [
        "Persistence",
        "Seasonal naïve",
        "XGBoost",
        "Attention-LSTM",
    ], size=6.8, step=0.042)

    # Box top aligned with the conformal block's output box for a shared baseline.
    ax.add_patch(Rectangle((x0 + 0.013, 0.240), (x1 - 0.013) - (x0 + 0.013),
                           0.120, facecolor=_tint(BLUE, 0.93),
                           edgecolor=_tint(BLUE, 0.60), linewidth=0.9, zorder=3))
    _txt(ax, cx, 0.323, "Point forecast", size=7.2, color=INK, weight="bold")
    _txt(ax, cx, 0.276, r"$\hat{y}_{t+h}$", size=9.0, color=INK)

    _txt(ax, cx, 0.150, "horizons h = 1, 3, 6", size=TINY_FS, color=MUTED)


# --------------------------------------------------------------------------- #
# Stage 4 — Conformal prediction (emphasised)
# --------------------------------------------------------------------------- #
def _stage_conformal(ax) -> None:
    x0, x1, y0, y1 = _stage_box(3)
    cx = 0.5 * (x0 + x1)
    _draw_block(ax, x0, x1, y0, y1, accent=BLUE, fill=_tint(BLUE, 0.955),
                edge=BLUE, lw=1.8, accent_h=0.016)
    _title(ax, x0, x1, y1, ["Conformal", "Prediction"])

    # --- point forecast becoming a calibrated interval ---
    # Band stops short of the right edge so the U / L labels stay well inside.
    gx = np.linspace(cx - 0.050, cx + 0.030, 40)
    gy = 0.735 + 0.016 * np.sin(np.linspace(0.4, 4.2, 40))
    half = np.linspace(0.008, 0.030, 40)
    ax.fill_between(gx, gy - half, gy + half, facecolor=_tint(BLUE, 0.72),
                    edgecolor="none", zorder=3)
    ax.plot(gx, gy + half, color=BLUE, linewidth=0.9, zorder=4)
    ax.plot(gx, gy - half, color=BLUE, linewidth=0.9, zorder=4)
    ax.plot(gx, gy, color=INK, linewidth=1.2, zorder=5)
    _txt(ax, gx[-1] + 0.006, gy[-1] + half[-1], "U", size=6.2, color=BLUE,
         weight="bold", ha="left")
    _txt(ax, gx[-1] + 0.006, gy[-1] - half[-1], "L", size=6.2, color=BLUE,
         weight="bold", ha="left")

    _txt(ax, cx, 0.648, "forecast + calibration", size=TINY_FS, color=MUTED,
         style="italic")

    _stack(ax, cx, 0.588, ["CQR", "Recentred EnbPI", "DSCP †"],
           size=7.2, step=0.042, color=INK, weight="bold")
    _txt(ax, cx, 0.442, "† extended implementation", size=TINY_FS, color=MUTED,
         style="italic")

    ax.add_patch(Rectangle((x0 + 0.012, 0.208), (x1 - 0.012) - (x0 + 0.012),
                           0.152, facecolor=SURFACE, edgecolor=BLUE,
                           linewidth=1.1, zorder=3))
    _txt(ax, cx, 0.330, "Calibrated", size=7.2, color=INK, weight="bold")
    _txt(ax, cx, 0.296, "prediction interval", size=7.2, color=INK,
         weight="bold")
    _txt(ax, cx, 0.243, r"$[L_{t+h},\ U_{t+h}]$", size=8.2, color=INK)

    _txt(ax, cx, 0.150, "nominal 90 % · 95 %", size=TINY_FS, color=MUTED)


# --------------------------------------------------------------------------- #
# Stage 5 — Interval-based alerting
# --------------------------------------------------------------------------- #
def _stage_alerting(ax) -> None:
    x0, x1, y0, y1 = _stage_box(4)
    cx = 0.5 * (x0 + x1)
    _draw_block(ax, x0, x1, y0, y1, accent=BLUE)
    _title(ax, x0, x1, y1, ["Interval-Based", "Alerting"])

    # --- observed signal breaching the upper bound ---
    ax_ = np.linspace(cx - 0.045, cx + 0.045, 30)
    base = 0.706 + 0.008 * np.sin(np.linspace(0.0, 3.0, 30))
    ax.fill_between(ax_, base - 0.024, base + 0.024,
                    facecolor=_tint(BLUE, 0.80), edgecolor="none", zorder=3)
    ax.plot(ax_, base + 0.024, color=BLUE, linewidth=0.8, zorder=4)
    ax.plot(ax_, base - 0.024, color=BLUE, linewidth=0.8, zorder=4)
    obs = base + np.concatenate([
        np.zeros(16),
        np.linspace(0.006, 0.046, 14),
    ])
    ax.plot(ax_, obs, color=INK, linewidth=1.2, zorder=5)
    out = obs > base + 0.024
    ax.plot(ax_[out], obs[out], linestyle="none", marker="s", markersize=3.4,
            markerfacecolor=RED, markeredgecolor=SURFACE, markeredgewidth=0.7,
            zorder=6)

    _txt(ax, cx, 0.612, "Interval violation", size=6.8, color=INK,
         weight="bold")
    _down_arrow(ax, cx, 0.590, 0.564)
    _txt(ax, cx, 0.540, "k-of-m aggregation", size=6.8, color=INK,
         weight="bold")
    _txt(ax, cx, 0.505, "(configurable, e.g. 3-of-5)", size=TINY_FS,
         color=MUTED, style="italic")
    _down_arrow(ax, cx, 0.484, 0.458)

    # --- alert marker ---
    ay = 0.420
    tri = np.array([[cx - 0.030, ay - 0.014],
                    [cx - 0.014, ay - 0.014],
                    [cx - 0.022, ay + 0.016]])
    ax.add_patch(Polygon(tri, closed=True, facecolor=_tint(RED, 0.35),
                         edgecolor=RED, linewidth=1.0, zorder=5))
    _txt(ax, cx - 0.022, ay - 0.004, "!", size=6.0, color=INK, weight="bold")
    _txt(ax, cx + 0.006, ay, "Alert", size=8.2, color=RED, weight="bold",
         ha="left")

    ax.add_patch(Rectangle((x0 + 0.013, 0.170), (x1 - 0.013) - (x0 + 0.013),
                           0.115, facecolor=_tint(BLUE, 0.95), edgecolor=HAIR,
                           linewidth=0.8, zorder=3))
    _txt(ax, cx, 0.250, "Monitoring &", size=SMALL_FS, color=INK)
    _txt(ax, cx, 0.216, "decision support", size=SMALL_FS, color=INK)
    _txt(ax, cx, 0.187, "(no automated control)", size=TINY_FS, color=MUTED,
         style="italic")


# --------------------------------------------------------------------------- #
# Stage 6 — Evaluation & robustness
# --------------------------------------------------------------------------- #
def _stage_evaluation(ax) -> None:
    x0, x1, y0, y1 = _stage_box(5)
    cx = 0.5 * (x0 + x1)
    _draw_block(ax, x0, x1, y0, y1, accent=BLUE)
    _title(ax, x0, x1, y1, ["Evaluation", "& Robustness"])

    groups = [
        ("Forecast", ["MAE • RMSE"]),
        ("Intervals", ["Coverage • Width", "Winkler score"]),
        ("Alerts", ["Precision • Recall • F1", "False alerts • Delay"]),
        ("Robustness", ["Missingness • Bias",
                        "Drift • Level shifts",
                        "Recalibration"]),
    ]

    y = 0.752
    for name, items in groups:
        _txt(ax, cx, y, name, size=6.9, color=INK, weight="bold")
        y -= 0.037
        for item in items:
            _txt(ax, cx, y, item, size=SMALL_FS, color=INK_2)
            y -= 0.035
        y -= 0.028

    ax.plot([x0 + 0.012, x1 - 0.012], [0.185, 0.185], color=HAIR,
            linewidth=0.9, zorder=4)
    _txt(ax, cx, 0.155, "common protocol", size=TINY_FS, color=MUTED,
         style="italic")
    _txt(ax, cx, 0.125, "across datasets", size=TINY_FS, color=MUTED,
         style="italic")


# --------------------------------------------------------------------------- #
# Output block — ConfoSense
# --------------------------------------------------------------------------- #
def _output_block(ax) -> None:
    x0, x1 = OUT_X0, OUT_X0 + W_OUT
    y0, y1 = BLOCK_Y0, BLOCK_Y1
    cx = 0.5 * (x0 + x1)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0,
                           facecolor=_tint(BLUE, 0.86), edgecolor=BLUE,
                           linewidth=1.8, zorder=2))
    ax.add_patch(Rectangle((x0, y1 - 0.016), x1 - x0, 0.016,
                           facecolor=BLUE, edgecolor="none", zorder=3))

    _txt(ax, cx, 0.800, "Integrated framework", size=SMALL_FS, color=INK_2)
    _txt(ax, cx, 0.724, "ConfoSense", size=NAME_FS, color=INK, weight="bold")
    ax.plot([x0 + 0.020, x1 - 0.020], [0.668, 0.668], color=BLUE,
            linewidth=1.0, zorder=4)

    _stack(ax, cx, 0.614, [
        "Reproducible",
        "uncertainty-aware forecasting",
        "and interval-based",
        "alerting framework",
    ], size=7.2, step=0.038, color=INK)

    _txt(ax, cx, 0.430, "for smart-building", size=6.9, color=INK_2)
    _txt(ax, cx, 0.396, "IoT monitoring", size=6.9, color=INK_2)

    # Six components feeding one pipeline.
    n = 6
    sw, sgap = 0.011, 0.008
    total = n * sw + (n - 1) * sgap
    sx = cx - total / 2
    for i in range(n):
        px = sx + i * (sw + sgap)
        ax.add_patch(Rectangle((px, 0.268), sw, 0.030,
                               facecolor=_tint(BLUE, 0.45), edgecolor=BLUE,
                               linewidth=0.7, zorder=4))
        if i < n - 1:
            ax.plot([px + sw, px + sw + sgap], [0.283, 0.283], color=BLUE,
                    linewidth=0.7, zorder=4)
    _txt(ax, cx, 0.222, "one reproducible pipeline", size=SMALL_FS, color=INK_2)

    ax.add_patch(Rectangle((x0 + 0.016, 0.118), (x1 - 0.016) - (x0 + 0.016),
                           0.062, facecolor=SURFACE,
                           edgecolor=_tint(BLUE, 0.55), linewidth=0.9,
                           zorder=3))
    _txt(ax, cx, 0.163, "open code · fixed seeds", size=TINY_FS, color=INK_2)
    _txt(ax, cx, 0.135, "public datasets", size=TINY_FS, color=INK_2)


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #
def _flow_arrows(ax) -> None:
    for i in range(6):
        x_from = STAGE_X[i] + W_STAGE
        x_to = (STAGE_X[i + 1] if i < 5 else OUT_X0)
        ax.add_patch(FancyArrowPatch(
            (x_from + 0.0012, 0.500), (x_to - 0.0012, 0.500),
            arrowstyle="-|>", mutation_scale=9,
            linewidth=1.4 if i == 5 else 1.2,
            color=BLUE if i == 5 else INK_2, zorder=7,
        ))


def graphical_abstract(out_dir: Path, dpi: int = 300,
                       formats: tuple[str, ...] = ("png", "svg")) -> list[Path]:
    _apply_style()
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")

    _stage_data(ax)
    _stage_prep(ax)
    _stage_forecast(ax)
    _stage_conformal(ax)
    _stage_alerting(ax)
    _stage_evaluation(ax)
    _output_block(ax)
    _flow_arrows(ax)

    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for ext in formats:
        path = out_dir / f"graphical_abstract.{ext}"
        fig.savefig(path, dpi=dpi)
        written.append(path)
    plt.close(fig)
    return written


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Generate the ConfoSense graphical abstract."
    )
    parser.add_argument("--outdir", default=str(repo_root / "outputs" / "figures"))
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    for path in graphical_abstract(Path(args.outdir), dpi=args.dpi):
        print(f"[figure] wrote {path}")


if __name__ == "__main__":
    main()
