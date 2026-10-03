"""Shared style, wording and checks for the Chapter 4 result figures.

Every ``figure_4_*.py`` script in this folder imports this module, so the
palette, series labels, horizon formatting and verification rules are the
same in every figure. Nothing here computes a scientific result: the figures
plot committed summary tables as stored.

Page geometry: the University of Malaya thesis rules set A4 margins of 2.0 cm
(top, right, bottom) and 4.0 cm (left), which leaves a 15.0 cm text block.
Every figure is drawn at that width and placed in the document at 100%, so
font sizes here are printed sizes: 9 pt text and 10 pt panel titles, inside
the APA 7 figure range of 8 to 14 pt. ``save_figure`` refuses an output wider
than the text block, any text smaller than 9 pt, overlapping text and labels
that cross their panel's frame.

Colour sets come from the validated dataviz reference palette and were checked
with its validator on the white dissertation surface, light mode, all pairs
(``validate_palette.js "<hexes>" --mode light --surface "#ffffff" --pairs all``):

====================  ======================================  =========  ============
Figure family         Slots                                   worst CVD  worst normal
====================  ======================================  =========  ============
point models          aqua, violet, blue, orange              9.2        16.3
interval methods      violet, blue, yellow, magenta, green    13.0       16.3
PLEIAData controls    violet, blue, orange, aqua              9.2        16.3
BDG2 methods          violet, blue, red                       13.0       16.3
====================  ======================================  =========  ============

Aqua, yellow and magenta sit below 3:1 contrast on white. Line series
therefore also carry distinct marker shapes, and every plotted value stays
available in the source tables.

Magnitudes (Figure 4.6) use the palette's blue sequential ramp, steps 100 to
700, which the validator's ``--ordinal`` check confirms is one hue with
monotone lightness. Two-state outcomes (Figure 4.7) carry no series identity:
the state of interest is secondary ink and the remainder a hatched neutral,
so the states also differ in grey-scale print.
"""

from __future__ import annotations

import csv
import itertools
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_agg import RendererAgg
from matplotlib.colors import to_hex, to_rgb
from matplotlib.font_manager import FontProperties, findfont
from matplotlib.lines import Line2D
from PIL import Image

OUT_DIR = Path(__file__).resolve().parent
REPO = OUT_DIR.parents[1]
TABLES = REPO / "review" / "candidature_evidence_package_20261002_v1" / "REPORT_TABLES"

DPI = 300
TEXT_WIDTH_CM = 21.0 - 4.0 - 2.0  # A4 less the UM left (4.0 cm) and right (2.0 cm) margins
FULL_WIDTH = TEXT_WIDTH_CM / 2.54  # inches
MIN_TEXT_PT = 9.0  # smallest printed text
TEXT_SIZE = 9.0    # labels, ticks, legends and annotations
TITLE_SIZE = 10.0  # bold panel titles
NOTE_SIZE = TEXT_SIZE  # annotations and reference-line labels

# --------------------------------------------------------------------------- #
# Palette: validated categorical slots (light surface) and ink tokens.
# --------------------------------------------------------------------------- #
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
GREEN = "#008300"
VIOLET = "#4a3aa7"
RED = "#e34948"

INK = "#0b0b0b"      # titles, axis labels, annotations
INK_2 = "#52514e"    # tick labels, reference lines, single derived series
MUTED = "#898781"    # spines, ticks and notes
RULE = "#c3c2b7"     # stems and connectors
GRID = "#e1e0d9"     # hairline gridlines
SURFACE = "#ffffff"  # white background, as required for the dissertation

# Blue sequential ramp, palette steps 100 to 700 (light to dark).
SEQUENTIAL_BLUE = (
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
    "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
)

LINE_WIDTH = 1.6
MARKER_SIZE = 6.0
# Matplotlib draws diamonds and squares larger, and triangles smaller, than a
# circle of the same nominal size; these factors even out their visual weight.
MARKER_SCALE = {"D": 0.82, "s": 0.9, "^": 1.1, "v": 1.1, "P": 1.05}
RING_WIDTH = 0.9  # white ring that keeps overlapping markers legible
REFERENCE_DASH = (0, (4, 3))


@dataclass(frozen=True)
class Series:
    label: str
    color: str
    marker: str


MODEL_SERIES = {
    "persistence": Series("Persistence", AQUA, "o"),
    "seasonal_naive": Series("Seasonal naïve", VIOLET, "s"),
    "xgboost": Series("XGBoost", BLUE, "^"),
    "attention_lstm": Series("Attention-LSTM", ORANGE, "D"),
}

METHOD_SERIES = {
    "quantile_uncalibrated": Series("Uncalibrated quantile", VIOLET, "o"),
    "cqr": Series("CQR", BLUE, "s"),
    "recentred_enbpi_static": Series("Recentred EnbPI static", YELLOW, "^"),
    "recentred_enbpi_updated": Series("Recentred EnbPI updated", MAGENTA, "v"),
    "dscp": Series("DSCP", GREEN, "D"),
}

# --------------------------------------------------------------------------- #
# Tasks, units and horizons.
# --------------------------------------------------------------------------- #
TASK_ORDER = ("PLEIAData temperature", "PLEIAData energy", "RICO HVAC", "BDG2 electricity")
HOURLY_TASK = "BDG2 electricity"
UNIT_LABELS = {
    "degrees C": "°C",
    "kWh per 10 minutes": "kWh per 10 min",
    "kWh per hour": "kWh per hour",
}


def horizon_value(task: str, minutes: float) -> float:
    """Horizon in the display unit: hours for BDG2, minutes otherwise."""
    return minutes / 60.0 if task == HOURLY_TASK else float(minutes)


def horizon_unit(task: str) -> str:
    return "h" if task == HOURLY_TASK else "min"


def horizon_text(task: str, minutes: float) -> str:
    return f"{horizon_value(task, minutes):g} {horizon_unit(task)}"


def unit_label(units: Iterable[str]) -> str:
    distinct = set(units)
    if len(distinct) != 1:
        raise ValueError(f"expected one target unit, found {sorted(distinct)}")
    return UNIT_LABELS[distinct.pop()]


# --------------------------------------------------------------------------- #
# Style and drawing helpers.
# --------------------------------------------------------------------------- #
def _resolve_font() -> str:
    """First available family from a print-friendly preference list."""
    for family in ("Arial", "Helvetica", "DejaVu Sans"):
        try:
            path = findfont(FontProperties(family=family), fallback_to_default=False)
        except Exception:
            continue
        if path:
            return family
    return "DejaVu Sans"


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [_resolve_font(), "DejaVu Sans"],
            "mathtext.fontset": "stixsans",
            "font.size": TEXT_SIZE,
            "axes.titlesize": TITLE_SIZE,
            "axes.titleweight": "bold",
            "axes.titlecolor": INK,
            "axes.titlepad": 6,
            "axes.labelsize": TEXT_SIZE,
            "axes.labelcolor": INK,
            "axes.edgecolor": MUTED,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.unicode_minus": True,
            "xtick.labelsize": TEXT_SIZE,
            "ytick.labelsize": TEXT_SIZE,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelcolor": INK_2,
            "ytick.labelcolor": INK_2,
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "xtick.minor.size": 1.8,
            "ytick.minor.size": 1.8,
            "xtick.minor.width": 0.6,
            "ytick.minor.width": 0.6,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "legend.fontsize": TEXT_SIZE,
            "legend.title_fontsize": TEXT_SIZE,
            "legend.frameon": False,
            "legend.handletextpad": 0.5,
            "legend.columnspacing": 1.6,
            "lines.solid_capstyle": "round",
            "lines.solid_joinstyle": "round",
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def panel_title(ax, letter: str, text: str) -> None:
    ax.set_title(f"({letter}) {text}", loc="left")


def format_horizon_axis(ax, task: str, minutes: Iterable[float]) -> None:
    """Ticks at the evaluated horizons only, in physical time."""
    ticks = [horizon_value(task, value) for value in sorted(minutes)]
    ax.set_xticks(ticks, [f"{tick:g}" for tick in ticks])
    ax.set_xlim(0, 6.5 if task == HOURLY_TASK else 65)
    ax.set_xlabel(f"Forecast horizon ({horizon_unit(task)})")


def marker_size(marker: str, size: float = MARKER_SIZE) -> float:
    return size * MARKER_SCALE.get(marker, 1.0)


def plot_series(ax, x, y, series: Series, gid: str) -> Line2D:
    (line,) = ax.plot(
        x, y, color=series.color, marker=series.marker, linewidth=LINE_WIDTH,
        markersize=marker_size(series.marker), markeredgecolor=SURFACE,
        markeredgewidth=RING_WIDTH, label=series.label, gid=gid, zorder=3,
    )
    return line


def series_handle(series: Series) -> Line2D:
    return Line2D(
        [], [], color=series.color, marker=series.marker, linewidth=LINE_WIDTH,
        markersize=marker_size(series.marker), markeredgecolor=SURFACE,
        markeredgewidth=RING_WIDTH, label=series.label,
    )


def reference_handle(label: str) -> Line2D:
    return Line2D([], [], color=INK_2, linewidth=0.9, linestyle=REFERENCE_DASH, label=label)


def relative_luminance(color) -> float:
    """WCAG 2 relative luminance."""
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in to_rgb(color)]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first, second) -> float:
    lighter, darker = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


FILL_INK = "#000000"     # dark labels on coloured fills; INK peaks at 4.47:1 on mid-ramp blues
MIN_LABEL_CONTRAST = 4.5  # WCAG AA for normal-size text


def label_color(fill) -> str:
    """Black or white, whichever contrasts more with the fill behind a label."""
    return FILL_INK if contrast_ratio(FILL_INK, fill) >= contrast_ratio(SURFACE, fill) else SURFACE


# --------------------------------------------------------------------------- #
# Output and print-size checks. The inventory script reads LAYOUT and RESULTS.
# --------------------------------------------------------------------------- #
LAYOUT: dict[str, dict] = {}
RESULTS: list[dict] = []


def save_figure(fig, stem: str, title: str) -> tuple[Path, Path]:
    """Check printed text, write the 300 dpi PNG and the vector PDF, then check both files."""
    layout = check_layout(fig, stem)
    png, pdf = OUT_DIR / f"{stem}.png", OUT_DIR / f"{stem}.pdf"
    options = {"bbox_inches": "tight", "pad_inches": 0.03, "facecolor": SURFACE}
    fig.savefig(png, dpi=DPI, metadata={"Title": title}, **options)
    fig.savefig(pdf, metadata={"Title": title, "CreationDate": None}, **options)
    LAYOUT[stem] = {"title": title, **layout, **check_outputs(png, pdf)}
    return png, pdf


def drawn_text(fig) -> list[tuple[str, float, object]]:
    """(string, size in points, artist) for every piece of text the renderer draws."""
    drawn = []
    original = RendererAgg.draw_text

    def record(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        drawn.append((s, prop.get_size_in_points(), mtext))
        return original(self, gc, x, y, s, prop, angle, ismath=ismath, mtext=mtext)

    RendererAgg.draw_text = record
    try:
        fig.canvas.draw()
    finally:
        RendererAgg.draw_text = original
    return drawn


def check_layout(fig, stem: str) -> dict:
    """Printed text size and text collisions, measured at the 100% placement size."""
    drawn = drawn_text(fig)
    if not drawn:
        raise AssertionError(f"{stem}: no text was drawn")
    smallest = min(size for _, size, _ in drawn)
    if smallest < MIN_TEXT_PT:
        small = sorted({text for text, size, _ in drawn if size < MIN_TEXT_PT})
        raise AssertionError(f"{stem}: text below {MIN_TEXT_PT:g} pt: {small}")
    renderer = fig.canvas.get_renderer()
    artists = list(dict.fromkeys(artist for _, _, artist in drawn if artist is not None))
    boxes = [(artist.get_text(), artist.get_window_extent(renderer)) for artist in artists]
    clashes = []
    for (first, a), (second, b) in itertools.combinations(boxes, 2):
        # Boxes that only touch, within half a screen pixel, are not a collision.
        if min(a.x1, b.x1) - max(a.x0, b.x0) > 0.5 and min(a.y1, b.y1) - max(a.y0, b.y0) > 0.5:
            clashes.append((first, second))
    if clashes:
        raise AssertionError(f"{stem}: overlapping text {clashes}")
    # Labels placed inside a panel must not cross its spines.
    for ax in fig.axes:
        frame = ax.get_window_extent(renderer)
        for text in ax.texts:
            if not (text.get_visible() and text.get_text().strip()):
                continue
            box = text.get_window_extent(renderer)
            if (box.x0 < frame.x0 - 0.5 or box.x1 > frame.x1 + 0.5
                    or box.y0 < frame.y0 - 0.5 or box.y1 > frame.y1 + 0.5):
                raise AssertionError(f"{stem}: {text.get_text()!r} extends outside its panel")
    return {"min_text_pt": smallest, "max_text_pt": max(size for _, size, _ in drawn), "text_items": len(artists)}


def check_outputs(png: Path, pdf: Path) -> dict:
    with Image.open(png) as image:
        dpi = image.info.get("dpi", (0, 0))
        pixels = image.size
    if any(abs(value - DPI) > 0.5 for value in dpi):
        raise AssertionError(f"{png.name}: expected {DPI} dpi, found {dpi}")
    data = pdf.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise AssertionError(f"{pdf.name} is not a PDF")
    if b"/Subtype /Image" in data:
        raise AssertionError(f"{pdf.name} contains a raster image")
    if b"/Subtype /Type3" in data:
        raise AssertionError(f"{pdf.name} contains a Type 3 font")
    boxes = re.findall(rb"/MediaBox \[ *0 +0 +([\d.]+) +([\d.]+) *\]", data)
    if len(boxes) != 1:
        raise AssertionError(f"{pdf.name}: expected one page, found {len(boxes)}")
    png_cm = tuple(count / resolution * 2.54 for count, resolution in zip(pixels, dpi))
    pdf_cm = tuple(float(value) / 72 * 2.54 for value in boxes[0])
    for name, width in ((png.name, png_cm[0]), (pdf.name, pdf_cm[0])):
        if width > TEXT_WIDTH_CM + 0.01:
            raise AssertionError(f"{name}: {width:.2f} cm wide; the text block is {TEXT_WIDTH_CM:g} cm")
    return {"png_pixels": pixels, "print_cm": png_cm, "pdf_cm": pdf_cm}


# --------------------------------------------------------------------------- #
# Source reading, provenance and verification.
# --------------------------------------------------------------------------- #
def read_table(path: Path) -> pd.DataFrame:
    """Plotting read; round-trip parsing gives the same floats as ``float()``."""
    return pd.read_csv(path, float_precision="round_trip")


def read_rows(path: Path) -> list[dict[str, str]]:
    """Independent verification read with the standard-library parser."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO), *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def git_blob(path: Path, revision: str = "HEAD") -> bytes:
    """Committed bytes of ``path`` at ``revision`` (Git's stored form, independent of checkout line endings)."""
    result = subprocess.run(
        ["git", "-C", str(REPO), "cat-file", "blob", f"{revision}:{repo_relative(path)}"],
        check=True, capture_output=True,
    )
    return result.stdout


def git_provenance(path: Path) -> dict[str, str]:
    """Last commit of ``path``; refuses an uncommitted or locally edited file."""
    relative = repo_relative(path)
    try:
        commit = _git("log", "-1", "--format=%H", "--", relative)
        status = _git("status", "--porcelain", "--", relative)
    except (OSError, subprocess.CalledProcessError):
        return {"source_path": relative, "source_commit": "unavailable"}
    if not commit:
        raise RuntimeError(f"{relative} is not committed")
    if status:
        raise RuntimeError(f"{relative} differs from its committed version")
    return {"source_path": relative, "source_commit": commit}


def artists_by_gid(fig, prefix: str) -> dict:
    found = {}
    for artist in fig.findobj(lambda a: str(a.get_gid() or "").startswith(prefix)):
        gid = artist.get_gid()
        if gid in found:
            raise AssertionError(f"duplicate plotted artist {gid}")
        found[gid] = artist
    return found


def line_points(line) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in zip(line.get_xdata(), line.get_ydata())]


def scatter_points(collection) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in collection.get_offsets()]


class ValueCheck:
    """Compares plotted artist data with values read from the source files."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.values = 0
        self.max_difference = 0.0
        self.notes: list[str] = []

    def note(self, text: str) -> None:
        """Records a passed source-consistency check, reported with the plotted values."""
        self.notes.append(text)

    def number(self, plotted: float, expected: float, what: str, tolerance: float = 0.0) -> None:
        difference = abs(float(plotted) - float(expected))
        if not difference <= tolerance:
            raise AssertionError(f"{self.name}: {what}: plotted {plotted!r}, source {expected!r}")
        self.values += 1
        self.max_difference = max(self.max_difference, difference)

    def points(self, plotted, expected, what: str) -> None:
        plotted, expected = sorted(plotted), sorted(expected)
        if len(plotted) != len(expected):
            raise AssertionError(
                f"{self.name}: {what}: {len(plotted)} plotted points, {len(expected)} source rows"
            )
        for (px, py), (ex, ey) in zip(plotted, expected):
            self.number(px, ex, f"{what} x")
            self.number(py, ey, f"{what} y")

    def keys(self, plotted: Iterable[str], expected: Iterable[str], what: str) -> None:
        plotted, expected = set(plotted), set(expected)
        if plotted != expected:
            raise AssertionError(
                f"{self.name}: {what}: missing {sorted(expected - plotted)}, "
                f"unexpected {sorted(plotted - expected)}"
            )

    def text(self, plotted: str, expected: str, what: str) -> None:
        if plotted != expected:
            raise AssertionError(f"{self.name}: {what}: plotted {plotted!r}, expected {expected!r}")

    def color(self, plotted, expected: str, what: str) -> None:
        if to_hex(plotted) != to_hex(expected):
            raise AssertionError(f"{self.name}: {what}: colour {to_hex(plotted)}, expected {expected}")

    def summary(self) -> str:
        return (
            f"{self.name}: {self.values} plotted values match the source "
            f"(max |difference| = {self.max_difference:.3g})"
        )


def report(check: ValueCheck, sources: Iterable[Path], outputs: Iterable[Path],
           caption: str = "", accompanying: str = "") -> None:
    """Print the verification summary and register it, with the final caption text, for the inventory."""
    print(check.summary())
    for note in check.notes:
        print(f"  checked {note}")
    provenance = [git_provenance(source) for source in sources]
    for item in provenance:
        print(f"  source  {item['source_path']} @ {item['source_commit'][:10]}")
    outputs = [repo_relative(output) for output in outputs]
    for output in outputs:
        print(f"  wrote   {output}")
    layout = LAYOUT[check.name]
    width, height = layout["print_cm"]
    print(f"  print   {width:.2f} x {height:.2f} cm at 100%; text {layout['min_text_pt']:g}-{layout['max_text_pt']:g} pt")
    RESULTS.append({
        "stem": check.name, "values": check.values, "max_difference": check.max_difference,
        "notes": list(check.notes), "sources": provenance, "outputs": outputs,
        "caption": caption, "accompanying": accompanying,
    })
