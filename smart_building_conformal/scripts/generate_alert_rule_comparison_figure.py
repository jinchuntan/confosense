"""Proposal-Defence figure: 3-of-5 versus 4-of-7 temporal alert aggregation.

Presentation artefact only. It fits no model, tunes no rule and writes no metric:
it replays what the audited full study already persisted and draws it.

How the plotted series are obtained
-----------------------------------
Everything is reconstructed from files under ``outputs/full_study/`` with no
random number generator involved:

* observed test values, point forecast and the 95% CQR bounds come straight from
  ``pleia/predictions/interval_predictions.csv`` filtered to
  ``conformal_method == "cqr"``, ``horizon == 1``, ``nominal_coverage == 0.95``;
* the perturbed signal is rebuilt by replaying
  ``pleia/data_profiles/injected_event_catalog.csv``. That file records each
  event's type, index range and **realised signed magnitude**, so the injection
  is reproduced arithmetically rather than re-sampled;
* point violations and the two k-of-m alert series are computed by the study's
  own :mod:`src.alerts` functions, so their semantics cannot drift from the run.

The reconstruction is then *proved* faithful: every metric is recomputed with
:func:`src.alert_study.score_rule` and compared against the persisted rows of
``combined/alert_metrics.csv``. Any mismatch aborts before a figure is drawn, so
the slide can never disagree with the dissertation.

Window selection rule (documented, first-qualifying, not best-qualifying)
-------------------------------------------------------------------------
Candidate windows are formed around each sustained test event — every
``event_id`` whose ``duration_steps`` is at least ``SUSTAINED_MIN_STEPS``,
padded by ``WINDOW_PAD_STEPS`` on each side. Isolated one-step spikes are
skipped because a spike cannot exercise a persistence rule.

A candidate qualifies when it contains the three things the figure has to show:

1. a sustained injected disturbance (true by construction);
2. at least ``MIN_NUISANCE_VIOLATIONS`` interval violations lying outside every
   event window, so nuisance behaviour is visible;
3. strictly fewer 4-of-7 alert steps than 3-of-5 alert steps, so the effect of
   the aggregation rule is visible at all.

Candidates are examined in ``event_id`` order and **the first qualifying one is
taken**. The window with the largest difference between the rules is deliberately
*not* selected, and the run prints both so the choice can be audited. Criterion 3
is a representativeness requirement rather than an outcome filter: without it the
figure would illustrate nothing, and on this dataset most windows fail it because
the two rules genuinely agree there — a fact reported in the accompanying text
rather than hidden.

Usage
-----
    python scripts/generate_alert_rule_comparison_figure.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import alert_study                                       # noqa: E402
from src import alerts as base                                    # noqa: E402

OUT = ROOT / "outputs" / "full_study"
FIGS = OUT / "report" / "figures"
CONFIG = ROOT / "configs" / "study_full.yaml"

DATASET = "pleia"
HORIZON = 1
METHOD = "cqr"
LEVEL = 0.95
RULES = {"3-of-5": (3, 5), "4-of-7": (4, 7)}

SUSTAINED_MIN_STEPS = 12      # an event long enough to exercise a k-of-m rule
WINDOW_PAD_STEPS = 60         # 10 hours either side at 10-minute sampling
MIN_NUISANCE_VIOLATIONS = 1   # the window must show some non-event violations

# Okabe-Ito derived, validated for colour-vision deficiency and for >= 3:1
# contrast against a white surface (see the palette validation in the report).
C_SIGNAL = "#333333"
C_BAND = "#0072B2"
C_VIOLATION = "#CC3311"       # red (Tol); CVD-separable from band and alert
C_ALERT = "#8C4B78"           # dark plum, distinct from both
C_EVENT = "#9E9E9E"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.bbox": "tight",
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "figure.facecolor": "white",
    "axes.facecolor": "white",
})


# --------------------------------------------------------------------------- #
def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, int, pd.Timedelta]:
    """Persisted intervals, persisted test event catalogue, tolerance, freq."""
    iv = pd.read_csv(OUT / DATASET / "predictions" / "interval_predictions.csv")
    iv = iv[(iv["conformal_method"] == METHOD)
            & (iv["horizon"] == HORIZON)
            & (np.isclose(iv["nominal_coverage"], LEVEL))].reset_index(drop=True)
    if iv.empty:
        raise SystemExit("no persisted CQR intervals for the requested cell")
    iv["target_time"] = pd.to_datetime(iv["target_time"])

    cat = pd.read_csv(OUT / DATASET / "data_profiles" / "injected_event_catalog.csv")
    cat = cat[cat["partition"] == "test"].reset_index(drop=True)
    if cat.empty:
        raise SystemExit("no persisted test-partition events")

    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    acfg = dict(cfg["defaults"]["alerts"])
    acfg.update(cfg["datasets"][DATASET].get("alerts", {}))
    tolerance = int(acfg.get("detection_tolerance_steps", 6))

    freq = pd.Timedelta(iv["target_time"].diff().dropna().mode().iloc[0])
    return iv, cat, tolerance, freq


def replay_perturbation(y_true: np.ndarray, cat: pd.DataFrame) -> np.ndarray:
    """Rebuild the perturbed signal from the persisted catalogue, without an RNG.

    The catalogue stores the *realised* signed magnitude of every event, so each
    injection is reproduced arithmetically. The branch structure mirrors
    :func:`src.alert_study.inject_events` exactly.
    """
    perturbed = np.array(y_true, dtype=float, copy=True)
    for row in cat.sort_values("event_id").itertuples():
        s, e = int(row.start_index), int(row.end_index)
        mag = float(row.injected_magnitude)
        kind = row.event_type
        if kind == "spike":
            perturbed[s] += mag
        elif kind in ("bias_positive", "bias_negative", "level_shift"):
            perturbed[s:e + 1] += mag
        elif kind == "drift":
            perturbed[s:e + 1] += np.linspace(0.0, mag, e - s + 1)
        elif kind == "stuck":
            perturbed[s:e + 1] = perturbed[s]
        elif kind == "dropout":
            perturbed[s:e + 1] = perturbed[s - 1] if s > 0 else perturbed[s]
        else:                                                     # pragma: no cover
            raise SystemExit(f"unhandled event type {kind!r} in the catalogue")
    return perturbed


def verify_against_persisted(perturbed, lower, upper, cat, freq, tolerance) -> pd.DataFrame:
    """Recompute both rules and require an exact match with the audited metrics.

    Without this the figure would merely be *plausible*. With it, the plotted
    violations and alerts are demonstrably the same objects that produced the
    numbers in the dissertation.
    """
    persisted = pd.read_csv(OUT / "combined" / "alert_metrics.csv")
    persisted = persisted[(persisted["dataset"] == DATASET)
                          & (persisted["role"] == "post_hoc_sensitivity")]
    persisted = persisted.set_index("rule")

    checked = ["precision", "recall", "f1", "far", "false_alert_events_per_day",
               "median_detection_delay_min", "mean_detection_delay_min",
               "n_violation_steps", "n_alert_steps"]
    rows, failures = [], []
    for name, (k, m) in RULES.items():
        got = alert_study.score_rule(perturbed, lower, upper, cat, k, m,
                                     freq, tolerance)
        want = persisted.loc[name]
        for col in checked:
            a, b = float(got[col]), float(want[col])
            if not np.isclose(a, b, rtol=0, atol=1e-6, equal_nan=True):
                failures.append(f"{name}.{col}: recomputed {a} vs persisted {b}")
        rows.append({"rule": name, **{c: float(got[c]) for c in checked}})

    if failures:
        raise SystemExit("reconstruction does not reproduce the audited metrics:\n  "
                         + "\n  ".join(failures))
    return pd.DataFrame(rows)


def select_window(cat, n, violations, ev_mask, alerts) -> tuple[int, int, pd.Series, list]:
    """First qualifying window in event order. See the module docstring.

    Returns the window, its anchor event, and the full audit of every candidate
    so the caller can print what was skipped and confirm that the *first*
    qualifying window was taken rather than the most flattering one.
    """
    sustained = cat[cat["duration_steps"] >= SUSTAINED_MIN_STEPS]
    if sustained.empty:
        raise SystemExit("no sustained event in the persisted test catalogue")

    audit, chosen = [], None
    for row in sustained.sort_values("event_id").itertuples():
        lo = max(0, int(row.start_index) - WINDOW_PAD_STEPS)
        hi = min(n - 1, int(row.end_index) + WINDOW_PAD_STEPS)
        sl = slice(lo, hi + 1)
        nuisance = int((violations[sl] & ~ev_mask[sl]).sum())
        a35 = int(alerts["3-of-5"][sl].sum())
        a47 = int(alerts["4-of-7"][sl].sum())
        qualifies = nuisance >= MIN_NUISANCE_VIOLATIONS and a47 < a35
        audit.append({"event_id": int(row.event_id), "event_type": row.event_type,
                      "severity": row.severity, "lo": lo, "hi": hi,
                      "nuisance_violations": nuisance,
                      "alert_steps_3of5": a35, "alert_steps_4of7": a47,
                      "difference": a35 - a47, "qualifies": qualifies})
        if qualifies and chosen is None:
            chosen = (lo, hi, cat[cat["event_id"] == row.event_id].iloc[0])

    if chosen is None:
        raise SystemExit("no candidate window met the representativeness criteria")
    return (*chosen, audit)


# --------------------------------------------------------------------------- #
def draw(frame: pd.DataFrame, cat_win: pd.DataFrame, metrics: pd.DataFrame,
         lo: int, hi: int) -> Path:
    t = frame["timestamp"]
    fig, axes = plt.subplots(2, 1, figsize=(12.8, 7.0), sharex=True, sharey=True)

    y_min = min(frame["lower"].min(), frame["observed"].min())
    y_max = max(frame["upper"].max(), frame["observed"].max())
    pad = 0.10 * (y_max - y_min)
    strip = y_min - pad * 0.55            # where the alert strip sits

    for ax, (title, col) in zip(axes, [("(a) 3-of-5 Temporal Aggregation", "alert_3of5"),
                                       ("(b) 4-of-7 Temporal Aggregation", "alert_4of7")]):
        for row in cat_win.itertuples():
            ax.axvspan(frame["timestamp"].iloc[max(0, int(row.start_index) - lo)],
                       frame["timestamp"].iloc[min(len(frame) - 1,
                                                   int(row.end_index) - lo)],
                       color=C_EVENT, alpha=0.18, lw=0, zorder=0)

        ax.fill_between(t, frame["lower"], frame["upper"], color=C_BAND,
                        alpha=0.18, lw=0, zorder=1)
        ax.plot(t, frame["observed"], color=C_SIGNAL, lw=1.2, zorder=3)

        v = frame["interval_violation"].to_numpy(bool)
        ax.plot(t[v], frame["observed"].to_numpy()[v], linestyle="none",
                marker="o", ms=3.4, color=C_VIOLATION,
                markeredgecolor="white", markeredgewidth=0.3, zorder=4)

        a = frame[col].to_numpy(bool)
        ax.plot(t[a], np.full(a.sum(), strip), linestyle="none", marker="s",
                ms=4.2, color=C_ALERT, zorder=4)
        ax.axhline(strip, color=C_ALERT, lw=0.5, alpha=0.25, zorder=1)

        rule = "3-of-5" if col.endswith("3of5") else "4-of-7"
        row = metrics.set_index("rule").loc[rule]
        ax.set_title(
            f"{title}   —   {int(a.sum())} alert steps in this window   |   "
            f"whole test partition: F1 {row['f1']:.3f}, "
            f"{row['false_alert_events_per_day']:.3f} false alerts/day, "
            f"median delay {row['median_detection_delay_min']:.0f} min",
            loc="left", fontsize=9.5)
        ax.set_ylabel("indoor temperature (degC)")
        ax.set_ylim(y_min - pad, y_max + pad * 0.45)

    axes[1].set_xlabel("test-partition time")
    fig.autofmt_xdate(rotation=0, ha="center")

    handles = [
        Line2D([], [], color=C_SIGNAL, lw=1.2, label="observed (perturbed) signal"),
        Patch(facecolor=C_BAND, alpha=0.18, label="95% CQR prediction interval"),
        Patch(facecolor=C_EVENT, alpha=0.18, label="injected disturbance window"),
        Line2D([], [], linestyle="none", marker="o", ms=4.2, color=C_VIOLATION,
               label="point interval violation (identical in both panels)"),
        Line2D([], [], linestyle="none", marker="s", ms=4.6, color=C_ALERT,
               label="aggregated alert"),
    ]
    axes[0].legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.42),
                   ncol=5, fontsize=8.5, handletextpad=0.5, columnspacing=1.4)

    m = metrics.set_index("rule")
    note = (
        f"3-of-5 $\\rightarrow$ 4-of-7: recall maintained at "
        f"{m.loc['3-of-5', 'recall']:.3f}, precision increased from "
        f"{m.loc['3-of-5', 'precision']:.3f} to {m.loc['4-of-7', 'precision']:.3f}, "
        f"F1 increased from {m.loc['3-of-5', 'f1']:.3f} to "
        f"{m.loc['4-of-7', 'f1']:.3f}, and false alerts decreased from "
        f"{m.loc['3-of-5', 'false_alert_events_per_day']:.3f} to "
        f"{m.loc['4-of-7', 'false_alert_events_per_day']:.3f} per day;\n"
        f"median delay increased from "
        f"{m.loc['3-of-5', 'median_detection_delay_min']:.0f} to "
        f"{m.loc['4-of-7', 'median_detection_delay_min']:.0f} min."
    )
    fig.text(0.5, 0.055, note, ha="center", va="top", fontsize=9.5,
             color="#222222", linespacing=1.5)
    fig.text(0.5, -0.035,
             "PLEIAData B-room11-V2, h = 1 (10 min), CQR at nominal 0.95. Identical "
             "test observations, prediction intervals, injected events and point "
             "violations in both panels; only the k-of-m rule differs.\nMetrics are "
             "whole-test-partition values from the same updated leakage-safe "
             "evaluation.",
             ha="center", va="top", fontsize=8, color="#666666", linespacing=1.4)

    fig.subplots_adjust(hspace=0.32, bottom=0.20, top=0.88)
    FIGS.mkdir(parents=True, exist_ok=True)
    p150 = FIGS / "fig_pleia_3of5_vs_4of7_alert_comparison.png"
    p300 = FIGS / "fig_pleia_3of5_vs_4of7_alert_comparison_300dpi.png"
    fig.savefig(p150, dpi=150, facecolor="white")
    fig.savefig(p300, dpi=300, facecolor="white")
    plt.close(fig)
    return p150


# --------------------------------------------------------------------------- #
def main() -> None:
    iv, cat, tolerance, freq = load_inputs()
    y_true = iv["y_true"].to_numpy(float)
    lower = iv["lower"].to_numpy(float)
    upper = iv["upper"].to_numpy(float)
    times = pd.DatetimeIndex(iv["target_time"])
    n = len(y_true)

    # Integrity: catalogue indices must address the same rows as the intervals.
    first = cat.sort_values("event_id").iloc[0]
    if pd.Timestamp(first["start_time"]) != times[int(first["start_index"])]:
        raise SystemExit(
            "catalogue index does not align with the persisted interval rows: "
            f"event 0 start_time {first['start_time']} vs "
            f"target_time[{int(first['start_index'])}] = "
            f"{times[int(first['start_index'])]}")

    perturbed = replay_perturbation(y_true, cat)
    metrics = verify_against_persisted(perturbed, lower, upper, cat, freq, tolerance)
    print("reconstruction reproduces the audited metrics exactly:")
    print(metrics.to_string(index=False))

    violations = base.point_violations(perturbed, lower, upper)
    alerts = {name: base.apply_rule(violations, k, m) for name, (k, m) in RULES.items()}
    ev_mask = base._event_mask(cat, n, tolerance)

    lo, hi, anchor, audit = select_window(cat, n, violations, ev_mask, alerts)
    sl = slice(lo, hi + 1)
    aud = pd.DataFrame(audit)
    qualifying = aud[aud["qualifies"]]
    best = qualifying.loc[qualifying["difference"].idxmax()]
    print(f"\nwindow rule: sustained events (>= {SUSTAINED_MIN_STEPS} steps) padded "
          f"{WINDOW_PAD_STEPS} steps, first one with >= {MIN_NUISANCE_VIOLATIONS} "
          "non-event violation and fewer 4-of-7 than 3-of-5 alert steps")
    print(f"{len(aud)} candidates examined, {len(qualifying)} qualified "
          f"({len(aud) - len(qualifying)} skipped: the two rules agree there or "
          "the window shows no nuisance violation)")
    print(f"SELECTED   event_id={int(anchor['event_id'])} "
          f"type={anchor['event_type']} severity={anchor['severity']} "
          f"indices {int(anchor['start_index'])}-{int(anchor['end_index'])} "
          f"(difference {int(aud.loc[aud.event_id == anchor['event_id'], 'difference'].iloc[0])})")
    print(f"NOT taken  largest-difference candidate was event_id="
          f"{int(best['event_id'])} (difference {int(best['difference'])})")
    print(f"plotted indices {lo}-{hi}  ({times[lo]} to {times[hi]})")
    aud.to_csv(FIGS / "fig_pleia_3of5_vs_4of7_window_selection_audit.csv", index=False)

    frame = pd.DataFrame({
        "timestamp": times[sl],
        "observed": perturbed[sl],
        "point_forecast": iv["point"].to_numpy(float)[sl],
        "lower": lower[sl],
        "upper": upper[sl],
        "interval_violation": violations[sl].astype(int),
        "injected_event": ev_mask[sl].astype(int),
        "alert_3of5": alerts["3-of-5"][sl].astype(int),
        "alert_4of7": alerts["4-of-7"][sl].astype(int),
    })
    csv = FIGS / "fig_pleia_3of5_vs_4of7_alert_comparison_data.csv"
    FIGS.mkdir(parents=True, exist_ok=True)
    frame.to_csv(csv, index=False)

    cat_win = cat[(cat["end_index"] >= lo) & (cat["start_index"] <= hi)]
    print(f"\nplotted window contents: {len(frame)} steps, "
          f"{int(frame['interval_violation'].sum())} violations "
          f"({int((frame['interval_violation'] & ~frame['injected_event'].astype(bool)).sum())} "
          f"outside any event window), {len(cat_win)} injected events, "
          f"3-of-5 alert steps {int(frame['alert_3of5'].sum())}, "
          f"4-of-7 alert steps {int(frame['alert_4of7'].sum())}")

    path = draw(frame, cat_win, metrics, lo, hi)
    print(f"\nwrote {path}")
    print(f"wrote {path.with_name(path.stem + '_300dpi.png')}")
    print(f"wrote {csv}")


if __name__ == "__main__":
    main()
