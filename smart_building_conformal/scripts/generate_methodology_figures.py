"""Publication-quality methodology schematics for the dissertation.

These figures are **conceptual schematics**, not experimental results: nothing
here reads the dataset, the fitted models or any file under ``outputs/metrics``.
The illustrative series drawn in panel (a) is a fixed analytic curve (a sum of
sines) used purely to convey "a time series"; it is not PLEIAData and carries no
axis values.

Currently produced
------------------
``figure_2_split_and_sliding_window.png``
    Figure 2 of the methodology chapter. Panel (a) shows the chronological
    60/20/20 train / calibration / test partition; panel (b) shows the
    sliding-window input construction and the direct multi-horizon targets.

``figure_3_interval_alert_mechanism.png``
    Figure 3 of the methodology chapter. A stylised worked example of the
    alerting procedure: prediction interval -> interval violations -> k-of-m
    temporal aggregation -> first alert, with the detection delay marked. The
    series is simulated; it is not PLEIAData and reports no measured result.
    This figure is deliberately distinct from the empirical
    ``figure_7_alert_timeline.png`` produced by the experiment itself.

The horizons and split fractions drawn here mirror the preliminary PLEIAData
configuration in ``configs/pleia_preliminary.yaml`` (60/20/20; h = 1, 3, 6 steps
at 10-minute sampling = 10/30/60 minutes).

Usage
-----
    python scripts/generate_methodology_figures.py

Only the ``figure_2_*`` and ``figure_3_*`` files listed above are written; the
experiment's own figures 4-7 are never touched.
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
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Patch, Rectangle

# --------------------------------------------------------------------------- #
# Palette — validated categorical slots (light surface), restrained for print.
# --------------------------------------------------------------------------- #
BLUE = "#2a78d6"    # slot 1 -> Training / input window / prediction interval
ORANGE = "#eb6834"  # slot 2 -> Calibration / forecast targets
AQUA = "#1baf7a"    # slot 3 -> Test
RED = "#e34948"     # slot 8 -> interval violations and the aggregated alert
AMBER = "#fab219"   # event window wash (always accompanied by a text label)

INK = "#0b0b0b"      # primary ink
INK_2 = "#52514e"    # secondary ink
MUTED = "#898781"    # axis / de-emphasised labels
RULE = "#c3c2b7"     # baselines and hairlines
NOTE_BG = "#f2f2ee"
NOTE_EDGE = "#dedcd4"

SURFACE = "#ffffff"  # white background, as required for the dissertation


def _tint(color: str, whiteness: float) -> tuple[float, float, float]:
    """Blend ``color`` toward white; ``whiteness`` in [0, 1]."""
    r, g, b = to_rgb(color)
    return (
        r + (1.0 - r) * whiteness,
        g + (1.0 - g) * whiteness,
        b + (1.0 - b) * whiteness,
    )


def _resolve_font() -> str:
    """First available family from a print-friendly preference list."""
    for family in ("Arial", "Helvetica", "DejaVu Sans"):
        try:
            path = findfont(
                FontProperties(family=family), fallback_to_default=False
            )
        except Exception:
            continue
        if path:
            return family
    return "DejaVu Sans"


def _apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [_resolve_font(), "DejaVu Sans"],
            "mathtext.fontset": "stixsans",
            "figure.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
        }
    )


def _blank_axes(ax) -> None:
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")


def _panel_title(ax, label: str, text: str) -> None:
    ax.text(
        0.0, 0.955, label, transform=ax.transAxes,
        fontsize=10.5, fontweight="bold", color=INK,
        ha="left", va="baseline",
    )
    # Offset in points, so the gap is independent of the panel's width.
    ax.annotate(
        text, xy=(0.0, 0.955), xycoords=ax.transAxes,
        xytext=(27, 0), textcoords="offset points",
        fontsize=10.5, color=INK, ha="left", va="baseline",
    )


# --------------------------------------------------------------------------- #
# Panel (a) — chronological partition
# --------------------------------------------------------------------------- #
def _draw_partition(ax) -> None:
    _blank_axes(ax)
    _panel_title(ax, "(a)", "Chronological data partition")

    band_bottom, band_top = 0.50, 0.70
    band_h = band_top - band_bottom
    segments = [
        ("Training", 0.00, 0.60, BLUE, "60 %"),
        ("Calibration", 0.60, 0.80, ORANGE, "20 %"),
        ("Test", 0.80, 1.00, AQUA, "20 %"),
    ]

    for name, x0, x1, hue, share in segments:
        ax.add_patch(
            Rectangle(
                (x0, band_bottom), x1 - x0, band_h,
                facecolor=_tint(hue, 0.80), edgecolor=hue,
                linewidth=1.2, zorder=2,
            )
        )
        mid = 0.5 * (x0 + x1)
        # Segment name sits above the band: every segment is directly labelled,
        # so identity never rests on fill colour alone.
        ax.text(
            mid, 0.755, name, fontsize=9, fontweight="bold",
            color=INK, ha="center", va="baseline", zorder=4,
        )
        ax.text(
            mid, 0.522, share, fontsize=7.5, color=INK_2,
            ha="center", va="baseline", zorder=4,
        )

    # Illustrative (synthetic) series so the band reads as a time series.
    xs = np.linspace(0.0, 1.0, 800)
    ys = 0.615 + 0.042 * (
        0.55 * np.sin(2 * np.pi * 5.5 * xs)
        + 0.32 * np.sin(2 * np.pi * 2.3 * xs + 0.8)
        + 0.16 * np.sin(2 * np.pi * 11.0 * xs + 1.7)
    )
    ax.plot(xs, ys, color=INK_2, linewidth=0.8, zorder=3, solid_capstyle="round")

    # Boundary droplines from the band down to the time axis.
    for xb in (0.60, 0.80):
        ax.plot(
            [xb, xb], [0.435, band_bottom], color=MUTED,
            linewidth=0.8, linestyle=(0, (3, 2)), zorder=1,
        )

    # Time axis.
    ax.add_patch(
        FancyArrowPatch(
            (0.0, 0.415), (1.035, 0.415),
            arrowstyle="-|>", mutation_scale=9,
            linewidth=0.9, color=RULE, shrinkA=0, shrinkB=0, zorder=2,
        )
    )
    ax.text(0.0, 0.345, "earliest", fontsize=7, color=MUTED,
            ha="left", va="baseline")
    ax.text(0.5, 0.345, "Time", fontsize=7.5, color=MUTED,
            ha="center", va="baseline")
    ax.text(1.0, 0.345, "latest", fontsize=7, color=MUTED,
            ha="right", va="baseline")

    ax.text(
        0.5, 0.215,
        "train  <  calibration  <  test   (order preserved)",
        fontsize=7.8, color=INK_2, ha="center", va="baseline",
    )
    ax.text(
        0.5, 0.075, "No random shuffling",
        fontsize=8, color=INK, ha="center", va="baseline",
        bbox=dict(
            boxstyle="round,pad=0.38", facecolor=NOTE_BG,
            edgecolor=NOTE_EDGE, linewidth=0.6,
        ),
    )


# --------------------------------------------------------------------------- #
# Panel (b) — sliding window and direct multi-horizon targets
# --------------------------------------------------------------------------- #
def _draw_sliding_window(ax) -> None:
    _blank_axes(ax)
    _panel_title(ax, "(b)", "Sliding-window construction")

    origin_x = 0.520
    cell_y0, cell_y1 = 0.620, 0.740
    cell_mid = 0.5 * (cell_y0 + cell_y1)

    # ---- input window: five cells, the second holding the elision ---------- #
    strip_x0, strip_x1 = 0.030, 0.500
    n_cells = 5
    gap = 0.006
    cell_w = ((strip_x1 - strip_x0) - gap * (n_cells - 1)) / n_cells
    labels = [r"$x_{t-w+1}$", None, r"$x_{t-2}$", r"$x_{t-1}$", r"$x_{t}$"]

    centres = []
    for i, label in enumerate(labels):
        x0 = strip_x0 + i * (cell_w + gap)
        centre = x0 + 0.5 * cell_w
        centres.append(centre)
        is_gap_cell = label is None
        ax.add_patch(
            Rectangle(
                (x0, cell_y0), cell_w, cell_y1 - cell_y0,
                facecolor=SURFACE if is_gap_cell else _tint(BLUE, 0.78),
                edgecolor=RULE if is_gap_cell else BLUE,
                linewidth=0.8 if is_gap_cell else 1.2,
                linestyle=(0, (2, 2)) if is_gap_cell else "solid",
                zorder=2,
            )
        )
        if is_gap_cell:
            ax.text(centre, cell_mid, r"$\cdots$", fontsize=9, color=MUTED,
                    ha="center", va="center", zorder=3)
        else:
            # Labels sit below their cell so long subscripts never overflow.
            ax.text(centre, 0.545, label, fontsize=8, color=INK,
                    ha="center", va="baseline", zorder=3)

    # ---- bracket beneath the window --------------------------------------- #
    br_y, tick = 0.480, 0.018
    ax.plot([strip_x0, strip_x1], [br_y, br_y], color=MUTED,
            linewidth=0.9, zorder=2)
    for xb in (strip_x0, strip_x1):
        ax.plot([xb, xb], [br_y, br_y + tick], color=MUTED,
                linewidth=0.9, zorder=2)
    strip_mid = 0.5 * (strip_x0 + strip_x1)
    ax.plot([strip_mid, strip_mid], [br_y, br_y - tick], color=MUTED,
            linewidth=0.9, zorder=2)
    ax.text(strip_mid, 0.408, "Input window", fontsize=8.5,
            fontweight="bold", color=INK, ha="center", va="baseline")
    ax.text(strip_mid, 0.338, r"all inputs at or before $t$", fontsize=7.3,
            color=INK_2, ha="center", va="baseline")

    # ---- forecast origin --------------------------------------------------- #
    # Stops above the note box so the rule never strikes through the text.
    ax.plot(
        [origin_x, origin_x], [0.283, 0.845], color=INK_2,
        linewidth=1.1, linestyle=(0, (4, 3)), zorder=4,
    )
    ax.text(
        origin_x, 0.875, r"Forecast origin $t$", fontsize=8,
        fontweight="bold", color=INK, ha="center", va="baseline", zorder=5,
    )

    # ---- direct multi-horizon targets -------------------------------------- #
    tgt_x0, tgt_x1 = 0.605, 0.930
    box_h = 0.150
    targets = [
        (0.750, r"$\hat{y}_{t+1}$", "h = 1   ·   10 min"),
        (0.565, r"$\hat{y}_{t+3}$", "h = 3   ·   30 min"),
        (0.380, r"$\hat{y}_{t+6}$", "h = 6   ·   60 min"),
    ]

    for y_mid, sym, note in targets:
        ax.add_patch(
            Rectangle(
                (tgt_x0, y_mid - box_h / 2), tgt_x1 - tgt_x0, box_h,
                facecolor=_tint(ORANGE, 0.80), edgecolor=ORANGE,
                linewidth=1.2, zorder=2,
            )
        )
        centre = 0.5 * (tgt_x0 + tgt_x1)
        ax.text(centre, y_mid + 0.016, sym, fontsize=9, color=INK,
                ha="center", va="baseline", zorder=3)
        ax.text(centre, y_mid - 0.055, note, fontsize=7, color=INK_2,
                ha="center", va="baseline", zorder=3)

    # Fan of arrows: one per horizon, emphasising the *direct* strategy.
    for (y_mid, _, _), rad in zip(targets, (0.16, 0.0, -0.16)):
        ax.add_patch(
            FancyArrowPatch(
                (strip_x1 + 0.012, cell_mid), (tgt_x0 - 0.012, y_mid),
                connectionstyle=f"arc3,rad={rad}",
                arrowstyle="-|>", mutation_scale=8.5,
                linewidth=1.0, color=INK_2, zorder=3,
            )
        )

    # ---- notes ------------------------------------------------------------- #
    ax.text(
        0.5, 0.205, "No future information used in model inputs",
        fontsize=8, color=INK, ha="center", va="baseline",
        bbox=dict(
            boxstyle="round,pad=0.38", facecolor=NOTE_BG,
            edgecolor=NOTE_EDGE, linewidth=0.6,
        ),
    )
    ax.text(
        0.5, 0.070,
        "Direct strategy: a separate model is fitted per horizon",
        fontsize=7.3, color=INK_2, ha="center", va="baseline",
    )


# --------------------------------------------------------------------------- #
# Figure 3 — interval-based alert mechanism
# --------------------------------------------------------------------------- #
# Illustrative rule, matching the preliminary configuration's selected rule.
K_OF_M = (3, 5)

# Steps that are drawn as interval violations. One isolated violation sits well
# before the event (step 6): it deliberately does NOT raise an alert, which is
# the whole point of requiring k of the last m.
_VIOLATION_STEPS = {6: 0.20, 14: 0.16, 16: 0.34, 17: 0.52,
                    18: 0.62, 19: 0.45, 20: 0.28}
# Inside the event but back within the band — noise that breaks the run.
_NEAR_UPPER_STEPS = (15, 21, 22)
_EVENT_START, _EVENT_END = 14, 22


def _alert_example(n: int = 32) -> dict:
    """Build the stylised example series.

    Everything is analytic plus one fixed-seed jitter, so the figure is
    byte-reproducible. Violations are imposed by construction and the observed
    values are then clamped inside the band everywhere else, which guarantees
    the marked violations are exactly the points drawn outside the interval.
    """
    t = np.arange(n)
    pred = (22.0
            + 0.55 * np.sin(2 * np.pi * t / 17.0)
            + 0.18 * np.sin(2 * np.pi * t / 5.0 + 1.1))
    half = 0.62 + 0.10 * np.sin(2 * np.pi * t / 11.0 + 0.4)
    lower, upper = pred - half, pred + half

    obs = pred + np.random.default_rng(7).normal(0.0, 0.20, size=n)
    viol = np.zeros(n, dtype=bool)
    for step in _VIOLATION_STEPS:
        viol[step] = True

    for i in range(n):
        if viol[i]:
            obs[i] = upper[i] + _VIOLATION_STEPS[i]
        elif i in _NEAR_UPPER_STEPS:
            obs[i] = upper[i] - 0.10
        else:
            obs[i] = float(np.clip(obs[i], lower[i] + 0.07, upper[i] - 0.07))

    k, m = K_OF_M
    counts = np.array([viol[max(0, i - m + 1): i + 1].sum() for i in range(n)])
    alert = counts >= k
    return {
        "t": t, "obs": obs, "lower": lower, "upper": upper,
        "viol": viol, "counts": counts, "alert": alert,
        "first_alert": int(np.argmax(alert)),
    }


def _draw_signal_row(ax, ex: dict) -> None:
    t, obs = ex["t"], ex["obs"]
    lower, upper, viol = ex["lower"], ex["upper"], ex["viol"]

    ax.axvspan(_EVENT_START - 0.5, _EVENT_END + 0.5,
               facecolor=_tint(AMBER, 0.86), edgecolor="none", zorder=0)
    ax.fill_between(t, lower, upper, facecolor=_tint(BLUE, 0.86),
                    edgecolor="none", zorder=1)
    for bound in (lower, upper):
        ax.plot(t, bound, color=BLUE, linewidth=1.0, zorder=2)

    ax.plot(t, obs, color=INK, linewidth=1.2, zorder=3)
    ax.plot(t, obs, linestyle="none", marker="o", markersize=3.0,
            markerfacecolor=SURFACE, markeredgecolor=INK,
            markeredgewidth=0.9, zorder=4)
    # A surface ring keeps violation markers legible where they overlap the line.
    ax.plot(t[viol], obs[viol], linestyle="none", marker="s", markersize=5.8,
            markerfacecolor=RED, markeredgecolor=SURFACE,
            markeredgewidth=1.1, zorder=5)

    lo = min(lower.min(), obs.min())
    hi = max(upper.max(), obs.max())
    span = hi - lo
    ax.set_ylim(lo - 0.15 * span, hi + 0.70 * span)

    # Kept clear of the detection-delay label below it (which sits at 0.32).
    ax.text(0.5 * (_EVENT_START + _EVENT_END), hi + 0.58 * span,
            "Controlled event", fontsize=8, fontweight="bold",
            color=INK, ha="center", va="center")
    ax.text(0.0, hi + 0.58 * span,
            r"$D_e = t_{\mathrm{first\ alert}} - t_{\mathrm{event\ start}}$",
            fontsize=7.5, color=INK_2, ha="left", va="center")

    # Detection-delay bracket: event start -> first alert.
    y_br = hi + 0.24 * span
    tick = 0.055 * span
    first = ex["first_alert"]
    ax.plot([_EVENT_START, first], [y_br, y_br], color=INK_2,
            linewidth=1.0, zorder=6)
    for xb in (_EVENT_START, first):
        ax.plot([xb, xb], [y_br - tick, y_br + tick], color=INK_2,
                linewidth=1.0, zorder=6)
    ax.text(0.5 * (_EVENT_START + first), y_br + 0.08 * span,
            r"Detection delay $D_e$", fontsize=8, color=INK,
            ha="center", va="bottom", zorder=6)

    ax.set_ylabel("Sensor value\n(arb. units)", fontsize=7.5, color=INK_2)
    ax.set_yticks([])
    ax.legend(
        handles=[
            Line2D([], [], color=INK, linewidth=1.2, marker="o", markersize=3.2,
                   markerfacecolor=SURFACE, markeredgecolor=INK,
                   markeredgewidth=0.9, label="Observed"),
            Patch(facecolor=_tint(BLUE, 0.86), edgecolor=BLUE, linewidth=1.0,
                  label="Prediction interval"),
            Line2D([], [], linestyle="none", marker="s", markersize=5.4,
                   markerfacecolor=RED, markeredgecolor=SURFACE,
                   markeredgewidth=1.0, label="Interval violation"),
        ],
        loc="lower left", bbox_to_anchor=(0.0, 1.005), ncol=3,
        frameon=False, fontsize=7.5, handletextpad=0.5, columnspacing=1.6,
    )


def _draw_violation_row(ax, ex: dict) -> None:
    t, viol = ex["t"], ex["viol"]
    ax.axhline(0.0, color=RULE, linewidth=0.6, zorder=1)
    ax.plot(t[~viol], np.zeros((~viol).sum()), linestyle="none", marker="o",
            markersize=2.6, color=RULE, markeredgecolor="none", zorder=3)
    ax.plot(t[viol], np.zeros(viol.sum()), linestyle="none", marker="s",
            markersize=5.4, markerfacecolor=RED, markeredgecolor=SURFACE,
            markeredgewidth=1.0, zorder=4)
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    ax.set_ylabel("Violation\nindicator", fontsize=7.5, color=INK_2)


def _draw_aggregation_row(ax, ex: dict, n: int) -> None:
    t, counts = ex["t"], ex["counts"]
    k, m = K_OF_M
    first = ex["first_alert"]

    faces = [_tint(RED, 0.45) if c >= k else _tint(BLUE, 0.72) for c in counts]
    edges = [RED if c >= k else _tint(BLUE, 0.35) for c in counts]
    ax.bar(t, counts, width=0.62, color=faces, edgecolor=edges,
           linewidth=0.7, zorder=3)

    ax.axhline(k, color=INK_2, linestyle=(0, (4, 3)), linewidth=0.9, zorder=4)
    ax.text(n - 0.6, k + 0.15, f"k = {k}", fontsize=7.5, color=INK_2,
            ha="right", va="bottom", zorder=5)
    ax.text(0.2, 5.35, f"{k}-of-{m} aggregation", fontsize=8,
            fontweight="bold", color=INK, ha="left", va="center", zorder=5)

    ax.annotate(
        "Alert", xy=(first, counts[first] + 0.12), xytext=(first - 4.6, 5.3),
        fontsize=8, fontweight="bold", color=RED, ha="center", va="center",
        arrowprops=dict(arrowstyle="-|>", color=RED, linewidth=1.0,
                        shrinkA=2, shrinkB=2,
                        connectionstyle="arc3,rad=-0.2"),
        zorder=6,
    )

    ax.set_ylim(0, 6.0)
    ax.set_yticks([0, k, m])
    # Wrapped to three lines: the rotated label has to fit inside this panel's
    # height, so the row is given extra height ratio to match (see the figure).
    ax.set_ylabel(
        f"Number of violations\nin the most recent\nm = {m} observations",
        fontsize=7.5, color=INK_2,
    )
    ax.set_xlabel("Time step  (10-minute sampling)", fontsize=8, color=INK)
    ax.set_xticks(np.arange(0, n, 4))
    ax.grid(axis="y", color="#eeede8", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)


def figure_3_interval_alert_mechanism(out_path: Path, dpi: int = 300) -> Path:
    """Render Figure 3 (stylised alert mechanism) and return the written path."""
    _apply_style()
    n = 32
    ex = _alert_example(n)

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(7.2, 4.95), sharex=True,
        gridspec_kw=dict(height_ratios=[3.0, 0.52, 1.85], hspace=0.17,
                         left=0.125, right=0.985, top=0.905, bottom=0.105),
    )

    _draw_signal_row(ax1, ex)
    _draw_violation_row(ax2, ex)
    _draw_aggregation_row(ax3, ex, n)

    # Guides tying the three rows to the same two instants.
    for ax in (ax1, ax2, ax3):
        for xg in (_EVENT_START, ex["first_alert"]):
            ax.axvline(xg, color=MUTED, linestyle=(0, (3, 2)),
                       linewidth=0.8, zorder=2)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(RULE)
        ax.tick_params(colors=MUTED, labelsize=7.5, length=3, width=0.8)

    for ax in (ax1, ax2):
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(bottom=False)
    ax2.tick_params(left=False)
    ax1.tick_params(left=False)

    ax3.set_xlim(-0.9, n - 0.1)

    fig.text(
        0.995, 0.004, "Illustrative example based on the alerting procedure",
        ha="right", va="bottom", fontsize=6.5, color=MUTED, style="italic",
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    return out_path


# --------------------------------------------------------------------------- #
# Figure assembly
# --------------------------------------------------------------------------- #
def figure_2_split_and_sliding_window(out_path: Path, dpi: int = 300) -> Path:
    """Render Figure 2 and return the written path."""
    _apply_style()
    fig = plt.figure(figsize=(7.2, 3.6))
    gs = fig.add_gridspec(
        1, 2, width_ratios=[1.0, 1.25],
        left=0.02, right=0.985, bottom=0.03, top=0.95, wspace=0.11,
    )
    _draw_partition(fig.add_subplot(gs[0, 0]))
    _draw_sliding_window(fig.add_subplot(gs[0, 1]))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    return out_path


FIGURES = {
    "figure_2_split_and_sliding_window": figure_2_split_and_sliding_window,
    "figure_3_interval_alert_mechanism": figure_3_interval_alert_mechanism,
}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Generate methodology schematics (no data or results used)."
    )
    parser.add_argument(
        "--outdir", default=str(repo_root / "outputs" / "figures"),
        help="Directory for the generated figures.",
    )
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument(
        "--only", choices=sorted(FIGURES), default=None,
        help="Render a single figure instead of all of them.",
    )
    args = parser.parse_args()

    outdir = Path(args.outdir)
    names = [args.only] if args.only else sorted(FIGURES)
    for name in names:
        path = FIGURES[name](outdir / f"{name}.png", dpi=args.dpi)
        print(f"[figure] wrote {path}")


if __name__ == "__main__":
    main()
