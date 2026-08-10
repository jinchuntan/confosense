"""Standalone graphical-abstract *elements* for ConfoSense.

These are the individual building blocks of a simple graphical abstract, meant
to be exported once and then arranged manually in Canva / PowerPoint:

    ga_1_sensor_stream      Smart-building IoT data
    ga_2_conformal_forecast Forecast + conformal prediction   <- central graphic
    ga_3_interval_alert     Interval violation -> k-of-m -> alert
    ga_4_monitoring_output  Reliable monitoring / decision support
    ga_core_combined        Elements 1-3 chained into one strip

Academic accuracy
-----------------
Every signal here is *synthetic and illustrative*. Nothing in this module reads
a dataset, and no measured quantity appears anywhere: no MAE/RMSE, no coverage,
no interval width, no alert precision/recall/F1, no detection delay, no false
alerts per day. The graphics therefore stay valid regardless of how the
dissertation experiments turn out.

The elements are also deliberately conservative in what they claim:

* sensor variables are shown as *examples*; the caption states outright that the
  available variables differ by dataset, so no dataset is implied to contain all
  of them;
* alerts are framed as monitoring / decision support, and the monitoring element
  says explicitly that no automated control is performed;
* no energy-saving, emission or field-deployment claim is made or implied.

Every coordinate in this module is expressed in **inches**: each figure uses a
single full-canvas axes with ``xlim = (0, FIG_W)`` and ``ylim = (0, FIG_H)``, so
one data unit is one inch on both axes. Circles are therefore round, and layout
numbers can be reasoned about directly in physical page units.

Usage
-----
    python scripts/generate_graphical_abstract_elements.py

Writes PNG (300 dpi, white), SVG (vector, editable text) and a transparent PNG
for each element into ``outputs/figures/graphical_abstract/``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.font_manager import FontProperties, findfont
from matplotlib.patches import (
    Arc,
    Circle,
    FancyArrowPatch,
    FancyBboxPatch,
    Polygon,
    Rectangle,
)

# --------------------------------------------------------------------------- #
# Palette — restrained blue/teal, muted orange/red reserved for violations
# --------------------------------------------------------------------------- #
BLUE = "#2a78d6"
BLUE_D = "#1f5ea8"
TEAL = "#17957f"
ORANGE = "#d9722f"
RED = "#c94f43"

INK = "#101418"
INK_2 = "#4b5158"
MUTED = "#8b9097"
RULE = "#c7cbd0"
HAIR = "#e4e7ea"
SURFACE = "#ffffff"

FS_TITLE = 12.5
FS_SUB = 8.5
FS_LABEL = 9.0
FS_SMALL = 8.0
FS_TINY = 7.0


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
        # Fixed canvas, not a tight crop: every element then keeps the margins
        # laid out below, so the exported files share one visual rhythm.
        "savefig.bbox": "standard",
        # Keep SVG text as real text elements so the files stay editable.
        "svg.fonttype": "none",
    })


# --------------------------------------------------------------------------- #
# Small geometry / drawing helpers
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Box:
    """An axis-aligned rectangle in inches."""

    x0: float
    y0: float
    w: float
    h: float

    @property
    def x1(self) -> float:
        return self.x0 + self.w

    @property
    def y1(self) -> float:
        return self.y0 + self.h

    @property
    def cx(self) -> float:
        return self.x0 + self.w / 2.0

    @property
    def cy(self) -> float:
        return self.y0 + self.h / 2.0


def _canvas(fig_w: float, fig_h: float):
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, fig_w)
    ax.set_ylim(0.0, fig_h)
    ax.axis("off")
    return fig, ax


def _renderer(fig):
    try:
        return fig.canvas.get_renderer()
    except AttributeError:  # pragma: no cover - backend without a cached renderer
        fig.canvas.draw()
        return fig.canvas.get_renderer()


def _text_w(fig, ax, s: str, fs: float, **kw) -> float:
    """Width of ``s`` in inches, measured with the real renderer."""
    probe = ax.text(0.0, -100.0, s, fontsize=fs, **kw)
    bb = probe.get_window_extent(renderer=_renderer(fig))
    probe.remove()
    return bb.transformed(ax.transData.inverted()).width


def _txt(ax, x, y, s, *, size=FS_SMALL, color=INK_2, weight="normal",
         ha="center", va="center", style="normal", z=8):
    return ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
                   ha=ha, va=va, style=style, zorder=z)


def _rounded(ax, box: Box, *, face, edge, lw=1.0, r=0.06, z=2):
    ax.add_patch(FancyBboxPatch(
        (box.x0, box.y0), box.w, box.h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=face, edgecolor=edge, linewidth=lw, zorder=z))


def _hairline(ax, x0, x1, y, color=HAIR, lw=1.0):
    ax.plot([x0, x1], [y, y], color=color, linewidth=lw, zorder=3)


def _arrow(ax, x0, x1, y, *, color=INK_2, lw=1.4, scale=11.0, z=9):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>",
                                 mutation_scale=scale, linewidth=lw,
                                 color=color, zorder=z))


def _scaler(vmin: float, vmax: float, lo: float, hi: float):
    span = float(vmax - vmin)
    if abs(span) < 1e-12:
        span = 1.0
    return lambda v: lo + (np.asarray(v, float) - vmin) / span * (hi - lo)


def _smooth(y, k=(0.25, 0.5, 0.25)):
    kern = np.asarray(k, float)
    kern = kern / kern.sum()
    pad = len(kern) // 2
    return np.convolve(np.pad(np.asarray(y, float), pad, mode="edge"),
                       kern, mode="valid")


# --------------------------------------------------------------------------- #
# Synthetic, illustrative signals (no dataset is ever read)
# --------------------------------------------------------------------------- #
def _stream(n: int, seed: int, *, periods=2.2, noise=0.10, drift=0.0):
    """A smooth, irregular-looking series in roughly [-1, 1]."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, n)
    y = (np.sin(2.0 * np.pi * periods * t + 0.4)
         + 0.34 * np.sin(2.0 * np.pi * periods * 2.7 * t + 1.1)
         + 0.14 * np.sin(2.0 * np.pi * periods * 5.3 * t + 0.3)
         + drift * t)
    return _smooth(y + rng.normal(0.0, noise, n))


def _forecast_series(n_hist: int, n_fut: int, seed: int = 11) -> dict:
    """Observed history + future, a point forecast and a conformal interval.

    Two future observations are placed outside the interval on purpose: a
    graphical abstract should show that a calibrated interval is *not* a
    guarantee for every single step.
    """
    rng = np.random.default_rng(seed)
    n = n_hist + n_fut
    t = np.arange(n, dtype=float)
    base = (1.00 * np.sin(2.0 * np.pi * t / 26.0 + 0.6)
            + 0.34 * np.sin(2.0 * np.pi * t / 9.5 + 1.9)
            + 0.10 * np.sin(2.0 * np.pi * t / 4.3))
    obs = _smooth(base + rng.normal(0.0, 0.075, n))

    h = np.arange(1, n_fut + 1, dtype=float)
    fc = _smooth(base[n_hist:] + 0.05 * h / n_fut + rng.normal(0.0, 0.02, n_fut))
    half = 0.20 + 0.30 * (h / n_fut) ** 0.75
    lo, up = fc - half, fc + half

    fut = obs[n_hist:].copy()
    i_up = max(1, int(round(0.34 * n_fut)))
    i_lo = min(n_fut - 2, int(round(0.74 * n_fut)))
    fut[i_up] = up[i_up] + 0.26
    fut[i_up - 1] += 0.09
    fut[min(i_up + 1, n_fut - 1)] += 0.07
    fut[i_lo] = lo[i_lo] - 0.21
    fut[i_lo - 1] -= 0.07
    obs = np.concatenate([obs[:n_hist], fut])

    return {"obs": obs, "fc": fc, "lo": lo, "up": up,
            "n_hist": n_hist, "n_fut": n_fut}


# --------------------------------------------------------------------------- #
# Hand-drawn glyphs (no external or copyrighted icon assets)
# --------------------------------------------------------------------------- #
def _icon_thermometer(ax, cx, cy, s, color):
    w = 0.17 * s
    bulb_r = 0.17 * s
    bulb_y = cy - 0.5 * s + bulb_r
    top = cy + 0.5 * s
    ax.add_patch(FancyBboxPatch((cx - w / 2, bulb_y), w, top - bulb_y,
                                boxstyle=f"round,pad=0,rounding_size={w / 2}",
                                facecolor=SURFACE, edgecolor=color,
                                linewidth=1.2, zorder=5))
    ax.add_patch(Circle((cx, bulb_y), bulb_r, facecolor=color,
                        edgecolor=color, linewidth=1.2, zorder=6))
    ax.plot([cx, cx], [bulb_y, cy + 0.10 * s], color=color, linewidth=1.7,
            solid_capstyle="round", zorder=6)
    for f in (0.20, 0.34):
        ax.plot([cx + w / 2, cx + w / 2 + 0.11 * s], [cy + f * s, cy + f * s],
                color=color, linewidth=0.9, zorder=6)


def _icon_bolt(ax, cx, cy, s, color):
    pts = np.array([[0.07, 0.50], [-0.24, 0.02], [-0.03, 0.02],
                    [-0.10, -0.50], [0.24, -0.02], [0.03, -0.02]])
    ax.add_patch(Polygon(np.column_stack([cx + pts[:, 0] * s,
                                          cy + pts[:, 1] * s]),
                         closed=True, facecolor=_tint(color, 0.72),
                         edgecolor=color, linewidth=1.2, joinstyle="round",
                         zorder=5))


def _icon_hvac(ax, cx, cy, s, color):
    w, h = 0.64 * s, 0.42 * s
    y0 = cy - 0.02 * s
    ax.add_patch(FancyBboxPatch((cx - w / 2, y0), w, h,
                                boxstyle="round,pad=0,rounding_size=0.03",
                                facecolor=_tint(color, 0.88), edgecolor=color,
                                linewidth=1.2, zorder=5))
    for i in range(3):
        y = y0 + (i + 1) * h / 4.0
        ax.plot([cx - w / 2 + 0.07 * s, cx + w / 2 - 0.07 * s], [y, y],
                color=color, linewidth=0.9, zorder=6)
    u = np.linspace(0.0, 2.0 * np.pi, 60)
    xs = np.linspace(cx - 0.24 * s, cx + 0.24 * s, 60)
    for j, off in enumerate((0.0, 0.15)):
        ax.plot(xs, y0 - (0.10 + off) * s + 0.045 * s * np.sin(u + 0.9 * j),
                color=_tint(color, 0.25 + 0.25 * j), linewidth=1.1, zorder=5)


def _icon_weather(ax, cx, cy, s, color):
    sun = (cx + 0.19 * s, cy + 0.17 * s)
    r = 0.155 * s
    for k in range(8):
        a = k * np.pi / 4.0
        ax.plot([sun[0] + 1.35 * r * np.cos(a), sun[0] + 1.95 * r * np.cos(a)],
                [sun[1] + 1.35 * r * np.sin(a), sun[1] + 1.95 * r * np.sin(a)],
                color=color, linewidth=1.0, solid_capstyle="round", zorder=4)
    ax.add_patch(Circle(sun, r, facecolor=_tint(color, 0.70), edgecolor=color,
                        linewidth=1.2, zorder=5))
    cw, ch = 0.66 * s, 0.27 * s
    ax.add_patch(FancyBboxPatch((cx - 0.40 * s, cy - 0.26 * s), cw, ch,
                                boxstyle=f"round,pad=0,rounding_size={ch / 2}",
                                facecolor=SURFACE, edgecolor=color,
                                linewidth=1.2, zorder=6))
    ax.add_patch(Circle((cx - 0.14 * s, cy - 0.055 * s), 0.145 * s,
                        facecolor=SURFACE, edgecolor=color, linewidth=1.2,
                        zorder=5))


def _bell(ax, cx, y_base, h, *, face, edge, lw=1.5, rings=True, z=6):
    """A simple alert bell whose base bar sits on ``y_base``."""
    w = 0.40 * h
    body_h = 0.78 * h
    ys = np.linspace(0.0, 1.0, 70)
    hw = w * (1.0 - 0.58 * ys ** 1.9)
    top_r = hw[-1]
    yb = y_base + 0.09 * h
    right = np.column_stack([cx + hw, yb + ys * (body_h - top_r)])
    ang = np.linspace(0.0, np.pi, 40)
    dome = np.column_stack([cx + top_r * np.cos(ang),
                            yb + (body_h - top_r) + top_r * np.sin(ang)])
    left = right[::-1].copy()
    left[:, 0] = 2.0 * cx - left[:, 0]
    ax.add_patch(Polygon(np.vstack([right, dome, left]), closed=True,
                         facecolor=face, edgecolor=edge, linewidth=lw,
                         joinstyle="round", zorder=z))
    ax.add_patch(FancyBboxPatch((cx - 1.22 * w, y_base), 2.44 * w, 0.085 * h,
                                boxstyle="round,pad=0,rounding_size=0.02",
                                facecolor=edge, edgecolor=edge,
                                linewidth=lw * 0.6, zorder=z + 1))
    ax.add_patch(Circle((cx, y_base - 0.065 * h), 0.075 * h, facecolor=edge,
                        edgecolor=edge, linewidth=lw * 0.6, zorder=z + 1))
    if rings:
        cy_ring = yb + 0.62 * body_h
        for rad in (0.78 * h, 0.98 * h):
            for t1, t2 in ((-26.0, 26.0), (154.0, 206.0)):
                ax.add_patch(Arc((cx, cy_ring), rad, rad, theta1=t1, theta2=t2,
                                 color=_tint(edge, 0.42), linewidth=1.2,
                                 zorder=z - 1))


# --------------------------------------------------------------------------- #
# Reusable panels — each draws inside a Box so elements can share them
# --------------------------------------------------------------------------- #
def _panel_stream(ax, box: Box, *, compact: bool = False, seed: int = 4):
    """Stacked sensor lanes: one prominent stream plus quieter companions."""
    lanes = [(BLUE, 1.9, 0.52, seed), (TEAL, 1.2, 0.26, seed + 1)]
    if not compact:
        lanes.append((_tint(BLUE_D, 0.42), 1.1, 0.22, seed + 2))

    n = 60 if compact else 96
    xs = np.linspace(box.x0, box.x1, n)
    total = sum(f for _, _, f, _ in lanes)
    gap = 0.10 if compact else 0.12
    free = box.h - gap * (len(lanes) - 1)
    y_top = box.y1
    for color, lw, frac, sd in lanes:
        lane_h = free * frac / total
        y = _scaler(-1.45, 1.45, y_top - lane_h, y_top)(
            _stream(n, sd, periods=2.4 if lw > 1.5 else 3.1,
                    noise=0.09 if lw > 1.5 else 0.12))
        ax.plot(xs, y, color=color, linewidth=lw, solid_capstyle="round",
                solid_joinstyle="round", zorder=5)
        _hairline(ax, box.x0, box.x1, y_top - lane_h - gap * 0.45,
                  color=HAIR, lw=0.8)
        y_top -= lane_h + gap

    if not compact:  # a few sample markers hint at discrete sensor readings
        y = _scaler(-1.45, 1.45,
                    box.y1 - free * lanes[0][2] / total, box.y1)(
            _stream(n, seed, periods=2.4, noise=0.09))
        idx = np.linspace(4, n - 5, 6).astype(int)
        ax.plot(xs[idx], y[idx], linestyle="none", marker="o", markersize=3.0,
                markerfacecolor=SURFACE, markeredgecolor=BLUE,
                markeredgewidth=1.0, zorder=6)


def _panel_forecast(ax, box: Box, *, compact: bool = False, seed: int = 11) -> dict:
    """The core element: observed signal, point forecast, conformal interval."""
    # Compact panels give the interval roughly half the width: in a small panel
    # the conformal band is the message, not the run-up to it.
    n_hist = 16 if compact else 46
    n_fut = 12 if compact else 18
    d = _forecast_series(n_hist, n_fut, seed)
    n = n_hist + n_fut

    left = 0.10 if compact else 0.28
    right = 0.10 if compact else 0.62
    xs = np.linspace(box.x0 + left, box.x1 - right, n)
    m = _scaler(min(d["lo"].min(), d["obs"].min()),
                max(d["up"].max(), d["obs"].max()),
                box.y0 + 0.08, box.y1 - (0.08 if compact else 0.16))

    xf, fut = xs[n_hist:], d["obs"][n_hist:]
    ax.fill_between(xf, m(d["lo"]), m(d["up"]), facecolor=_tint(BLUE, 0.80),
                    edgecolor="none", zorder=2)
    ax.plot(xf, m(d["up"]), color=_tint(BLUE, 0.30), linewidth=1.0, zorder=3)
    ax.plot(xf, m(d["lo"]), color=_tint(BLUE, 0.30), linewidth=1.0, zorder=3)

    ax.plot(xs[:n_hist], m(d["obs"][:n_hist]), color=INK,
            linewidth=1.5 if compact else 1.7, solid_capstyle="round", zorder=5)
    ax.plot(xs[n_hist - 1:], m(d["obs"][n_hist - 1:]), color=INK,
            linewidth=1.2 if compact else 1.4, zorder=5)
    if not compact:
        ax.plot(xf, m(fut), linestyle="none", marker="o", markersize=2.6,
                markerfacecolor=SURFACE, markeredgecolor=INK,
                markeredgewidth=0.8, zorder=6)

    ax.plot(xf, m(d["fc"]), color=BLUE, linewidth=1.5 if compact else 1.8,
            linestyle=(0, (3.2, 1.8)), zorder=4)

    x_origin = 0.5 * (xs[n_hist - 1] + xs[n_hist])
    ax.plot([x_origin, x_origin], [box.y0 + 0.01, box.y1 - 0.01], color=MUTED,
            linewidth=1.1, linestyle=(0, (2.4, 2.0)), zorder=6)

    out = (fut > d["up"]) | (fut < d["lo"])
    ax.plot(xf[out], m(fut[out]), linestyle="none", marker="o",
            markersize=4.2 if compact else 5.2, markerfacecolor=ORANGE,
            markeredgecolor=SURFACE, markeredgewidth=1.0, zorder=7)

    if not compact:
        _txt(ax, xf[-1] + 0.09, m(d["up"][-1]), r"$U_{t+h}$", size=FS_SMALL,
             color=BLUE_D, ha="left")
        _txt(ax, xf[-1] + 0.09, m(d["lo"][-1]), r"$L_{t+h}$", size=FS_SMALL,
             color=BLUE_D, ha="left")

    return {"xs": xs, "y": m(d["obs"]), "x_origin": x_origin,
            "x_last": xf[-1], "n_hist": n_hist,
            "x_out": xf[out], "y_out": m(fut[out]), "map": m, "data": d}


def _panel_violation(ax, box: Box, *, seed: int = 5, n_marks: int = 5) -> dict:
    """A short observed segment that level-shifts out of its interval.

    The excursion is a smooth step rather than an unbounded ramp: it keeps the
    interval band large enough to stay legible, and it leaves the last three of
    the five sampled steps outside the band, matching the ``3-of-5`` example
    used in the k-of-m caption.
    """
    n = 70
    xs = np.linspace(box.x0 + 0.06, box.x1 - 0.06, n)
    u = np.linspace(0.0, 1.0, n)
    fc = 0.10 * np.sin(2.0 * np.pi * 1.1 * u + 0.5)
    half = np.full(n, 0.42)
    obs = _smooth(fc + 0.10 * np.sin(2.0 * np.pi * 2.3 * u)
                  + np.random.default_rng(seed).normal(0.0, 0.030, n)
                  + 0.95 / (1.0 + np.exp(-(u - 0.42) / 0.06)))

    m = _scaler(min((fc - half).min(), obs.min()) - 0.05,
                max((fc + half).max(), obs.max()) + 0.05,
                box.y0 + 0.05, box.y1 - 0.05)
    ax.fill_between(xs, m(fc - half), m(fc + half),
                    facecolor=_tint(BLUE, 0.80), edgecolor="none", zorder=2)
    ax.plot(xs, m(fc + half), color=_tint(BLUE, 0.30), linewidth=1.0, zorder=3)
    ax.plot(xs, m(fc - half), color=_tint(BLUE, 0.30), linewidth=1.0, zorder=3)
    ax.plot(xs, m(obs), color=INK, linewidth=1.6, solid_capstyle="round",
            zorder=5)

    idx = np.linspace(6, n - 4, n_marks).astype(int)
    flags = obs[idx] > (fc + half)[idx]
    for i, flag in zip(idx, flags):
        ax.plot([xs[i]], [m(obs[i])], linestyle="none", marker="o",
                markersize=5.0 if flag else 3.4,
                markerfacecolor=ORANGE if flag else SURFACE,
                markeredgecolor=SURFACE if flag else INK_2,
                markeredgewidth=1.0 if flag else 0.9, zorder=7)
    return {"flags": np.asarray(flags, bool), "x_marks": xs[idx]}


def _panel_steps(ax, fig, box: Box, flags, *, fs=FS_TINY):
    """A row of m recent time steps, violations highlighted."""
    n = len(flags)
    gap = 0.09
    side = min((box.w - gap * (n - 1)) / n, box.h)
    x = box.cx - (n * side + gap * (n - 1)) / 2.0
    y = box.cy - side / 2.0
    for flag in flags:
        cell = Box(x, y, side, side)
        _rounded(ax, cell, face=_tint(ORANGE, 0.72) if flag else SURFACE,
                 edge=ORANGE if flag else RULE, lw=1.3 if flag else 1.0,
                 r=0.05, z=4)
        if flag:
            _txt(ax, cell.cx, cell.cy, "!", size=fs + 2.0, color=RED,
                 weight="bold")
        else:
            ax.add_patch(Circle((cell.cx, cell.cy), 0.035,
                                facecolor=RULE, edgecolor="none", zorder=5))
        x += side + gap
    return Box(box.cx - (n * side + gap * (n - 1)) / 2.0, y,
               n * side + gap * (n - 1), side)


def _chip_row(ax, fig, cx, cy, labels, *, fs=FS_TINY, h=0.24, padx=0.11,
              gap=0.10, face=None, edge=None, color=INK_2):
    face = _tint(BLUE, 0.93) if face is None else face
    edge = _tint(BLUE, 0.62) if edge is None else edge
    widths = [_text_w(fig, ax, s, fs) + 2.0 * padx for s in labels]
    total = sum(widths) + gap * (len(labels) - 1)
    x = cx - total / 2.0
    for s, w in zip(labels, widths):
        _rounded(ax, Box(x, cy - h / 2.0, w, h), face=face, edge=edge, lw=0.9,
                 r=h / 2.0, z=4)
        _txt(ax, x + w / 2.0, cy, s, size=fs, color=color)
        x += w + gap
    return total


def _legend_row(ax, fig, cx, y, entries, *, fs=FS_SMALL, gap=0.30, sw=0.28,
                pad=0.10):
    widths = [_text_w(fig, ax, label, fs) for _, label in entries]
    total = sum(sw + pad + w for w in widths) + gap * (len(entries) - 1)
    x = cx - total / 2.0
    for (kind, label), w in zip(entries, widths):
        xm = x + sw / 2.0
        if kind == "obs":
            ax.plot([x, x + sw], [y, y], color=INK, linewidth=1.7, zorder=6)
        elif kind == "fc":
            ax.plot([x, x + sw], [y, y], color=BLUE, linewidth=1.8,
                    linestyle=(0, (3.0, 1.7)), zorder=6)
        elif kind == "band":
            ax.add_patch(Rectangle((x, y - 0.065), sw, 0.13,
                                   facecolor=_tint(BLUE, 0.80),
                                   edgecolor=_tint(BLUE, 0.30), linewidth=0.9,
                                   zorder=6))
        elif kind == "viol":
            ax.plot([xm], [y], linestyle="none", marker="o", markersize=5.0,
                    markerfacecolor=ORANGE, markeredgecolor=SURFACE,
                    markeredgewidth=1.0, zorder=6)
        _txt(ax, x + sw + pad, y, label, size=fs, color=INK_2, ha="left")
        x += sw + pad + w + gap
    return total


def _element_header(ax, fig, x0, x1, y, title, *, subtitle=None,
                    size=FS_TITLE, rule=True):
    _txt(ax, x0, y, title, size=size, color=INK, weight="bold", ha="left")
    y_rule = y - 0.24
    if subtitle:
        _txt(ax, x0, y - 0.22, subtitle, size=FS_SUB, color=MUTED, ha="left")
        y_rule = y - 0.40
    if rule:
        _hairline(ax, x0, x1, y_rule)
    return y_rule


# --------------------------------------------------------------------------- #
# Element 1 — smart-building sensor stream
# --------------------------------------------------------------------------- #
def element_1_sensor_stream():
    fig, ax = _canvas(4.9, 3.1)
    _element_header(ax, fig, 0.28, 4.62, 2.86, "Smart-Building IoT Data",
                    subtitle="Public sensor streams")

    _panel_stream(ax, Box(0.30, 1.16, 4.30, 1.16))

    icons = [
        (_icon_thermometer, "Indoor\ntemperature"),
        (_icon_bolt, "Energy"),
        (_icon_hvac, "HVAC"),
        (_icon_weather, "Weather"),
    ]
    x0, x1 = 0.26, 4.64
    slot = (x1 - x0) / len(icons)
    for i, (draw, label) in enumerate(icons):
        cx = x0 + (i + 0.5) * slot
        draw(ax, cx, 0.80, 0.40, BLUE if i % 2 == 0 else TEAL)
        _txt(ax, cx, 0.46, label, size=FS_TINY + 0.5, color=INK_2,
             va="top", z=8)

    _txt(ax, 2.45, 0.13,
         "Illustrative schematic — available variables differ by dataset",
         size=FS_TINY - 0.4, color=MUTED, style="italic")
    return fig


# --------------------------------------------------------------------------- #
# Element 2 — forecast + conformal prediction (central graphic)
# --------------------------------------------------------------------------- #
def element_2_conformal_forecast():
    fig, ax = _canvas(5.7, 3.6)
    _element_header(ax, fig, 0.30, 5.40, 3.36, "Forecast + Conformal Prediction")

    box = Box(0.30, 1.12, 5.10, 1.90)
    info = _panel_forecast(ax, box)

    # Minimal time axis: one baseline, two named instants, no ticks or values.
    y_ax = 1.02
    _arrow(ax, 0.30, 5.44, y_ax, color=RULE, lw=1.0, scale=8.0, z=3)
    for x, label in ((info["x_origin"], r"$t$"), (info["x_last"], r"$t+h$")):
        ax.plot([x, x], [y_ax - 0.05, y_ax + 0.05], color=RULE, linewidth=1.0,
                zorder=4)
        _txt(ax, x, 0.84, label, size=FS_LABEL + 0.5, color=INK)

    # "Observed" sits in the empty strip above the history and is tied to the
    # curve by a leader dropped over a local minimum, so it can never collide.
    xs, y = info["xs"], info["y"]
    n_hist = info["n_hist"]
    lo_i, hi_i = int(0.15 * n_hist), int(0.62 * n_hist)
    j = lo_i + int(np.argmin(y[lo_i:hi_i]))
    y_label = box.y1 - 0.13
    ax.plot([xs[j], xs[j]], [y[j] + 0.07, y_label - 0.10], color=RULE,
            linewidth=0.9, zorder=4)
    _txt(ax, xs[j], y_label, "Observed", size=FS_LABEL, color=INK)

    # Two legend rows: a single row wide enough for all four entries would not
    # fit the canvas, and shrinking the type would hurt small-size readability.
    _legend_row(ax, fig, 2.85, 0.54, [
        ("obs", "Observed"),
        ("fc", r"Point forecast  $\hat{y}_{t+h}$"),
    ])
    _legend_row(ax, fig, 2.85, 0.22, [
        ("band", r"Prediction interval  $[L_{t+h},\,U_{t+h}]$"),
        ("viol", "Observation outside interval"),
    ])
    return fig


# --------------------------------------------------------------------------- #
# Element 3 — interval violation and alert
# --------------------------------------------------------------------------- #
def element_3_interval_alert():
    fig_w = 6.8
    fig, ax = _canvas(fig_w, 2.45)
    _element_header(ax, fig, 0.24, fig_w - 0.24, 2.22, "Interval Violations → Alert",
                    size=FS_TITLE - 1.0)

    y_mid = 1.22           # arrows and glyph centres share one optical line
    y_head = 1.80          # the three block headings share one baseline
    y_cap = 0.62           # the sub-captions share another

    # --- observed signal leaving its prediction interval ---
    left = Box(0.24, 0.84, 1.56, 0.78)
    res = _panel_violation(ax, left)
    _txt(ax, left.cx, y_head, "Observed + interval", size=FS_LABEL, color=INK,
         weight="bold")
    _txt(ax, left.cx, y_cap, "signal leaves the interval", size=FS_TINY,
         color=MUTED, va="top")

    _arrow(ax, 1.92, 2.34, y_mid)

    # --- the same steps as a small violation counter ---
    mid = Box(2.48, 0.92, 1.44, 0.60)
    _panel_steps(ax, fig, mid, res["flags"])
    _txt(ax, mid.cx, y_head, "Interval violations", size=FS_LABEL, color=INK,
         weight="bold")
    _txt(ax, mid.cx, y_cap, "m recent steps", size=FS_TINY, color=MUTED,
         va="top")

    # --- k-of-m temporal aggregation ---
    _arrow(ax, 4.06, 4.76, y_mid)
    _txt(ax, 4.41, 1.48, "k-of-m", size=FS_LABEL, color=INK, weight="bold")
    _txt(ax, 4.41, y_cap + 0.22, "(configurable,\ne.g. 3-of-5)",
         size=FS_TINY - 0.3, color=MUTED, va="top", style="italic")

    # --- alert ---
    right_cx = 5.78
    _txt(ax, right_cx, y_head, "Interval-Based Alert", size=FS_LABEL,
         color=RED, weight="bold")
    _bell(ax, right_cx, 0.92, 0.62, face=_tint(ORANGE, 0.74), edge=RED)
    _txt(ax, right_cx, y_cap, "Monitoring / decision support", size=FS_TINY,
         color=MUTED, va="top")

    _txt(ax, fig_w / 2.0, 0.14, "Conceptual schematic — no experimental values",
         size=FS_TINY - 0.4, color=MUTED, style="italic")
    return fig


# --------------------------------------------------------------------------- #
# Element 4 — robustness / monitoring output
# --------------------------------------------------------------------------- #
def element_4_monitoring_output():
    fig, ax = _canvas(5.1, 3.05)

    card = Box(0.26, 0.62, 4.58, 2.24)
    _rounded(ax, card, face=SURFACE, edge="none", lw=0.0, r=0.10, z=2)
    # Rounded header, then a plain rectangle to square off its lower corners.
    _rounded(ax, Box(card.x0, card.y1 - 0.50, card.w, 0.50),
             face=_tint(BLUE, 0.94), edge="none", lw=0.0, r=0.10, z=3)
    ax.add_patch(Rectangle((card.x0, card.y1 - 0.50), card.w, 0.22,
                           facecolor=_tint(BLUE, 0.94), edgecolor="none",
                           zorder=3))
    _hairline(ax, card.x0, card.x1, card.y1 - 0.50, color=_tint(BLUE, 0.72))

    _txt(ax, card.x0 + 0.22, card.y1 - 0.25, "Reliable Monitoring",
         size=FS_TITLE - 0.5, color=INK, weight="bold", ha="left")
    _bell(ax, card.x1 - 0.34, card.y1 - 0.37, 0.30, face=_tint(ORANGE, 0.74),
          edge=RED, lw=1.1, rings=False, z=6)

    # --- forecast + interval sparkline ---
    spark = Box(card.x0 + 0.22, 1.62, 1.92, 0.56)
    _panel_forecast(ax, spark, compact=True, seed=3)
    _txt(ax, spark.cx, 1.48, "Forecast + prediction interval", size=FS_TINY,
         color=MUTED, va="top")

    # --- qualitative status rows (no measured quantity appears) ---
    rows = [(TEAL, "Calibrated intervals"),
            (BLUE, "Continuous monitoring"),
            (ORANGE, "Interval-based alerts")]
    x_dot = card.x0 + 2.42
    for i, (color, label) in enumerate(rows):
        y = 2.12 - i * 0.24
        ax.add_patch(Circle((x_dot, y), 0.052, facecolor=color,
                            edgecolor="none", zorder=6))
        _txt(ax, x_dot + 0.16, y, label, size=FS_SMALL, color=INK_2, ha="left")

    _hairline(ax, card.x0 + 0.22, card.x1 - 0.22, 1.30)
    _txt(ax, card.cx, 1.16, "Robust to changing sensor conditions",
         size=FS_TINY, color=MUTED, va="top")
    _chip_row(ax, fig, card.cx, 0.86,
              ["Missingness", "Drift", "Bias", "Level shift"])

    # Border last, so nothing painted inside can eat into the card outline.
    _rounded(ax, card, face="none", edge=_tint(BLUE, 0.35), lw=1.4, r=0.10,
             z=7)

    _txt(ax, 2.55, 0.36, "Decision Support", size=FS_TITLE - 1.0, color=INK,
         weight="bold")
    _txt(ax, 2.55, 0.13, "monitoring support only — no automated control",
         size=FS_TINY - 0.4, color=MUTED, style="italic")
    return fig


# --------------------------------------------------------------------------- #
# Element 5 — simple combined core graphic
# --------------------------------------------------------------------------- #
def element_5_core_combined():
    fig_w, fig_h = 11.0, 2.75
    fig, ax = _canvas(fig_w, fig_h)

    margin, arrow_w, gap = 0.26, 0.46, 0.06
    n = 4
    panel_w = (fig_w - 2 * margin - n_arrows_w(n, arrow_w, gap)) / n
    xs = []
    x = margin
    for _ in range(n):
        xs.append(x)
        x += panel_w + gap + arrow_w + gap

    y_title = 2.52
    y_top, y_bot = 1.98, 0.44
    titles = [("Smart-Building", "IoT Data"),
              ("Forecast +", "Conformal Prediction"),
              ("Interval", "Violation"),
              ("Interval-Based", "Alert")]
    for x0, (l1, l2) in zip(xs, titles):
        cx = x0 + panel_w / 2.0
        _txt(ax, cx, y_title, l1, size=FS_LABEL + 0.5, color=INK, weight="bold")
        _txt(ax, cx, y_title - 0.21, l2, size=FS_LABEL + 0.5, color=INK,
             weight="bold")
    _hairline(ax, margin, fig_w - margin, y_top + 0.10)

    y_cap = 0.32           # one caption baseline shared by all four panels

    # 1 — sensor streams with small unlabelled sensor glyphs
    p1 = Box(xs[0], 1.02, panel_w, 0.92)
    _panel_stream(ax, p1, compact=True)
    for i, draw in enumerate((_icon_thermometer, _icon_bolt, _icon_hvac,
                              _icon_weather)):
        draw(ax, p1.x0 + (i + 0.5) * p1.w / 4.0, 0.72, 0.30,
             BLUE if i % 2 == 0 else TEAL)
    _txt(ax, p1.cx, y_cap, "dynamic sensor streams", size=FS_TINY, color=MUTED)

    # 2 — forecast + conformal interval
    p2 = Box(xs[1], 0.84, panel_w, 1.14)
    info = _panel_forecast(ax, p2, compact=True)
    ax.plot([info["x_origin"], info["x_origin"]], [0.70, 0.78], color=RULE,
            linewidth=1.0, zorder=4)
    _txt(ax, info["x_origin"], 0.58, r"$t$", size=FS_SMALL + 0.5, color=INK)
    _txt(ax, 0.5 * (info["x_origin"] + info["x_last"]), y_cap,
         r"$[L_{t+h},\,U_{t+h}]$", size=FS_SMALL, color=BLUE_D)

    # 3 — interval violation + k-of-m
    p3 = Box(xs[2], 1.02, panel_w, 0.92)
    res = _panel_violation(ax, p3)
    _panel_steps(ax, fig, Box(p3.x0 + 0.30, 0.60, p3.w - 0.60, 0.34),
                 res["flags"])
    _txt(ax, p3.cx, y_cap, "k-of-m aggregation", size=FS_TINY, color=MUTED)

    # 4 — alert
    p4 = Box(xs[3], 0.44, panel_w, 1.54)
    _bell(ax, p4.cx, 1.02, 0.74, face=_tint(ORANGE, 0.74), edge=RED)
    _txt(ax, p4.cx, 0.66, "Alert", size=FS_TITLE - 0.5, color=RED,
         weight="bold")
    _txt(ax, p4.cx, y_cap, "monitoring / decision support", size=FS_TINY,
         color=MUTED)

    for x0 in xs[:-1]:
        xa = x0 + panel_w + gap
        _arrow(ax, xa, xa + arrow_w, 1.24, color=INK_2, lw=1.6, scale=13.0)

    _txt(ax, fig_w / 2.0, 0.13,
         "Illustrative schematic — synthetic signals, no experimental values",
         size=FS_TINY - 0.4, color=MUTED, style="italic")
    return fig


def n_arrows_w(n_panels: int, arrow_w: float, gap: float) -> float:
    return (n_panels - 1) * (arrow_w + 2.0 * gap)


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #
ELEMENTS = {
    "1": ("ga_1_sensor_stream", element_1_sensor_stream),
    "2": ("ga_2_conformal_forecast", element_2_conformal_forecast),
    "3": ("ga_3_interval_alert", element_3_interval_alert),
    "4": ("ga_4_monitoring_output", element_4_monitoring_output),
    "5": ("ga_core_combined", element_5_core_combined),
}


def generate(out_dir: Path, *, dpi: int = 300, keys=None,
             transparent: bool = True, svg: bool = False) -> list[Path]:
    """One 300 dpi PNG per element by default; SVG only when asked for.

    Transparent PNGs drop onto any light Canva/PowerPoint background and look
    identical to opaque ones on white, so a single file per element covers the
    normal case without leaving near-duplicate exports lying around.
    """
    _apply_style()
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for key in (keys or ELEMENTS):
        stem, builder = ELEMENTS[key]
        fig = builder()
        path = out_dir / f"{stem}.png"
        fig.savefig(path, dpi=dpi, transparent=transparent)
        written.append(path)
        if svg:
            path = out_dir / f"{stem}.svg"
            fig.savefig(path, dpi=dpi, transparent=transparent)
            written.append(path)
        plt.close(fig)
    return written


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Generate the ConfoSense graphical-abstract elements.")
    parser.add_argument(
        "--outdir",
        default=str(root / "outputs" / "figures" / "graphical_abstract"))
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--only", nargs="*", choices=sorted(ELEMENTS),
                        help="element keys to rebuild (default: all)")
    parser.add_argument("--svg", action="store_true",
                        help="also write an editable SVG per element")
    parser.add_argument("--white-bg", action="store_true",
                        help="opaque white background instead of transparent")
    args = parser.parse_args()

    for path in generate(Path(args.outdir), dpi=args.dpi, keys=args.only,
                         transparent=not args.white_bg, svg=args.svg):
        print(f"[element] wrote {path}")


if __name__ == "__main__":
    main()
