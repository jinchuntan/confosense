"""Figure 4.6: mean clean reference coverage under sensor disturbances.

Caption title: Mean clean reference coverage under sensor disturbances

Source: review/candidature_evidence_package_20261002_v1/REPORT_TABLES/ROBUSTNESS_FAULT_SUMMARY.csv

Each setting has 15 fold-seed units (three outer folds x five model seeds),
and each unit is replayed with its own clean reference interval configuration
(saved owner, interval method, nominal level and recalibration policy). The
table summarises the units that share a configuration in one row, and
``cells`` counts those units. Each heatmap value pools a setting's rows for
one scenario with ``cells`` as weights:

    coverage = sum(cells * mean_coverage_during) / sum(cells)

The weights must total 15 for every setting and scenario. mean_coverage_during
is empirical coverage in the disturbance window, [25%, 55%) of each test
stream; the clean row is the same window of the undisturbed stream. All cells
share one colour scale from 0 to 1. Nominal levels differ between units (0.95
to 0.995), so no common coverage target is marked.

Severity. A level shift or gradual drift at severity 1 or 2 has magnitude
severity x s, where s is a training-only robust dispersion. The executed chain,
checked below against the committed code and its replay hash pins, is

    completion_v1.py (59 units) or robustness_saved_owner_v1.run_unit (pilot unit)
      -> src.split_integrity.training_scale(y, meta, roles["fit"])
      -> src.alerts_corrected.per_group_robust_scale(fit-role targets, fit-role groups)
      -> magnitude = severity * scale_map.get(group, scale_map["__pooled__"])

per_group_robust_scale gives a group 1.4826 x the median absolute deviation
(MAD) of its finite training targets when it has at least 20 of them and a
non-zero MAD. Other groups take the pooled training value, 1.4826 x the MAD of
all training targets (with the training standard deviation, then 1.0, as
degenerate-case fallbacks). A test group absent from training also takes the
pooled value: RICO roles are blocked by whole run, so every RICO test run uses
the pooled scale. The scale is therefore not a pooled sample standard
deviation.

Comparisons. The data file carries two different changes for every cell:

* same_window_reduction_pp = 100 * (clean - disturbed), both pooled over the
  same window with cells as weights. This is the reduction to quote with the
  figure.
* pre_minus_during_pp = 100 * (pre-window - disturbance-window coverage) of the
  same stream, the within-stream change quoted in RESULTS_FINDINGS.md. It also
  contains the clean stream's own change between the two windows.

The zero control (level_shift@0) is not plotted; verification requires it to
equal the clean row exactly. Cross-check: every pooled value equals the
unweighted mean of coverage_during over the 15 units in
review/robustness_contamination_recovery_20260928/AGGREGATE_CELL_METRICS.csv.

Outputs: figure_4_6_sensor_disturbance_coverage.png / .pdf and the derived
figure data figure_4_6_sensor_disturbance_coverage_data.csv.

Usage:
    python report_figures/chapter4/figure_4_6_sensor_disturbance_coverage.py
"""

from __future__ import annotations

import hashlib
import json
import math

import chapter4_style as c4
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle

STEM = "figure_4_6_sensor_disturbance_coverage"
CAPTION = "Mean clean reference coverage under sensor disturbances"
SOURCE = c4.TABLES / "ROBUSTNESS_FAULT_SUMMARY.csv"
ROBUSTNESS = c4.REPO / "review" / "robustness_contamination_recovery_20260928"
SRC = c4.REPO / "smart_building_conformal" / "src"
CELL_SOURCE = ROBUSTNESS / "AGGREGATE_CELL_METRICS.csv"
DATA = c4.OUT_DIR / f"{STEM}_data.csv"
GID = "fig4.6|"
UNITS = 15  # fold-seed units per setting and scenario
CLEAN, ZERO_CONTROL, HEADLINE = "clean", "zero_control", "level_shift@2.0"
SCENARIOS = {
    "clean": "Clean",
    "random_missing@na": "Random missingness",
    "dropout@na": "Dropout",
    "stuck@na": "Stuck sensor",
    "level_shift@1.0": "Level shift, severity 1",
    "level_shift@2.0": "Level shift, severity 2",
    "drift@1.0": "Gradual drift, severity 1",
    "drift@2.0": "Gradual drift, severity 2",
}
COLUMN_LABELS = {
    "PLEIAData temperature": "PLEIAData\ntemperature",
    "PLEIAData energy": "PLEIAData\nenergy",
    "RICO HVAC": "RICO\nHVAC",
    "BDG2 electricity": "BDG2\nelectricity",
}
CLEAN_GAP = 0.3  # extra space, in rows, between the clean reference and the disturbances
SCALE = Normalize(vmin=0.0, vmax=1.0)  # one coverage scale for every setting
CMAP = LinearSegmentedColormap.from_list("chapter4_sequential_blue", c4.SEQUENTIAL_BLUE)
SCALE_TICKS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
SCALE_LABEL = "Mean coverage during the disturbance window"
GAP_WIDTH = 1.5  # points of white between neighbouring cells

# Severity-scale provenance: committed statements the caption relies on. The two
# replay drivers are pinned by the robustness records; every file must also be
# byte-identical to the robustness delivery commit.
ROBUSTNESS_COMMIT = "1b94d7dc027fe2a15049c82ba3c9a721df329ece"
CONTRACT = ROBUSTNESS / "SCIENTIFIC_REPLAY_CONTRACT.json"
COMPLETION_PROTOCOL = ROBUSTNESS / "COMPLETION_PROTOCOL.json"
SCALE_STATEMENTS = {
    ROBUSTNESS / "completion_v1.py": (
        'scale_map = SI.training_scale(np.asarray(data["y"]), data["meta"], roles["fit"])',
        'magnitude = magnitude_sd * float(scale_map.get(item.group_id, scale_map["__pooled__"]))',
    ),
    ROBUSTNESS / "robustness_saved_owner_v1.py": (
        'scale_map = SI.training_scale(np.asarray(data["y"]), data["meta"], roles["fit"])',
        'magnitude = magnitude_sd * float(scale_map.get(item.group_id, scale_map["__pooled__"]))',
    ),
    SRC / "split_integrity.py": (
        "from .alerts_corrected import per_group_robust_scale",
        "sc = per_group_robust_scale(np.asarray(y)[idx], meta.iloc[idx].group_id.to_numpy())",
        'return {**sc["scale"], "__pooled__": sc["pooled_fallback"]}',
    ),
    SRC / "alerts_corrected.py": (
        "min_points: int = 20,",
        "k = 1.4826",
        "if len(v) < min_points:",
        "return float(s) if s > 0 else None",
        "pooled = mad_sigma(y) or (float(np.nanstd(y))",
        '"pooled_fallback": pooled,',
    ),
    SRC / "matched_data005.py": (  # RICO test runs never enter the fit role
        "SI.assert_boundary(meta, np.r_[fit, calibration], test, SI.GROUPED)",
    ),
}


def coverage_label(value: float) -> str:
    return f"{value:.3f}"


def points(value: float) -> str:
    return f"{value:.2f}".replace("-", "\N{MINUS SIGN}")


def listing(items: list[str]) -> str:
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def pool(weights: list[float], values: list[float]) -> tuple[float, float]:
    """Weighted mean and weight total; fsum keeps the result independent of row order."""
    total = math.fsum(weights)
    return math.fsum(w * v for w, v in zip(weights, values)) / total, total


def single(values, what: str) -> str:
    distinct = set(values)
    if len(distinct) != 1:
        raise ValueError(f"expected one {what}, found {sorted(distinct)}")
    return distinct.pop()


def derive(frame) -> pd.DataFrame:
    if frame.duplicated(["task", "cell", "interval_method", "nominal_level", "recal_policy"]).any():
        raise ValueError("more than one summary row for a setting, scenario and configuration")
    records = []
    for task in c4.TASK_ORDER:
        task_rows = frame[frame["task"] == task]
        clean_rows = task_rows[task_rows["cell"] == CLEAN]
        clean, _ = pool([float(w) for w in clean_rows["cells"]], [float(v) for v in clean_rows["mean_coverage_during"]])
        for cell, label in SCENARIOS.items():
            rows = task_rows[task_rows["cell"] == cell]
            if rows.empty:
                raise ValueError(f"no rows for {task}, {cell}")
            weights = [float(w) for w in rows["cells"]]
            coverage, weight = pool(weights, [float(v) for v in rows["mean_coverage_during"]])
            pre, _ = pool(weights, [float(v) for v in rows["mean_coverage_pre"]])
            if weight != UNITS:
                raise ValueError(f"{task}, {cell}: weights total {weight:g}, expected {UNITS}")
            records.append(
                {
                    "row_order": len(records) + 1,
                    "dataset": single(rows["dataset"], "dataset"),
                    "task": task,
                    "cell": cell,
                    "scenario": label,
                    "weight_total": int(weight),
                    "configuration_rows": len(rows),
                    "mean_coverage_during": coverage,
                    "coverage_label": coverage_label(coverage),
                    "clean_mean_coverage_during": clean,
                    "same_window_reduction_pp": 100.0 * (clean - coverage),
                    "mean_coverage_pre": pre,
                    "pre_minus_during_pp": 100.0 * (pre - coverage),
                    "source_table": c4.repo_relative(SOURCE),
                    "source_commit": single(rows["source_commit"], "source commit"),
                    "source_path": single(rows["source_path"], "source path"),
                }
            )
    return pd.DataFrame(records)


def row_positions() -> dict[str, float]:
    """Top edge of each scenario row; the clean reference sits apart at the top."""
    positions, y = {}, 0.0
    for cell in SCENARIOS:
        positions[cell] = y
        y += 1.0 + (CLEAN_GAP if cell == CLEAN else 0.0)
    return positions


def build(data):
    fig, ax = plt.subplots(figsize=(c4.FULL_WIDTH, 3.75), layout="constrained")
    rows = row_positions()
    for record in data.itertuples(index=False):
        x, y = c4.TASK_ORDER.index(record.task), rows[record.cell]
        fill = CMAP(SCALE(record.mean_coverage_during))
        ax.add_patch(Rectangle(
            (x, y), 1.0, 1.0, facecolor=fill, edgecolor=c4.SURFACE, linewidth=GAP_WIDTH,
            gid=f"{GID}cell|{record.task}|{record.cell}",
        ))
        ax.text(
            x + 0.5, y + 0.5, record.coverage_label, ha="center", va="center_baseline",
            fontsize=c4.TEXT_SIZE, color=c4.label_color(fill), gid=f"{GID}label|{record.task}|{record.cell}",
        )
    bottom = max(rows.values()) + 1.0
    ax.set_xlim(0, len(c4.TASK_ORDER))
    ax.set_ylim(bottom, 0)
    ax.xaxis.tick_top()
    ax.set_xticks([index + 0.5 for index in range(len(c4.TASK_ORDER))],
                  [COLUMN_LABELS[task] for task in c4.TASK_ORDER])
    for label in ax.get_xticklabels():
        label.set_fontweight("bold")
    ax.set_yticks([rows[cell] + 0.5 for cell in SCENARIOS], list(SCENARIOS.values()))
    ax.tick_params(axis="x", length=0, pad=3, labelcolor=c4.INK)
    ax.tick_params(axis="y", length=0, pad=4)
    for spine in ax.spines.values():
        spine.set_visible(False)

    scale = fig.colorbar(
        ScalarMappable(norm=SCALE, cmap=CMAP), ax=ax, location="bottom",
        shrink=0.62, aspect=42, pad=0.03,
    )
    scale.ax.set_gid(f"{GID}scale")
    scale.solids.set_rasterized(False)  # Matplotlib rasterises long gradients; the PDF must stay vector
    scale.set_ticks(SCALE_TICKS, labels=[f"{tick:.1f}" for tick in SCALE_TICKS])
    scale.outline.set_visible(False)
    scale.ax.tick_params(length=2.5, width=0.6, color=c4.MUTED)
    scale.set_label(SCALE_LABEL, color=c4.INK, labelpad=3)
    return fig


def verify_severity_scale(check: c4.ValueCheck) -> None:
    """The documented severity scale is the committed, hash-pinned code that ran."""
    contract = json.loads(c4.git_blob(CONTRACT).decode("utf-8-sig"))
    protocol = json.loads(c4.git_blob(COMPLETION_PROTOCOL).decode("utf-8-sig"))
    pins = {
        ROBUSTNESS / "robustness_saved_owner_v1.py": contract["saved_owner_adapter_sha256"],
        ROBUSTNESS / "completion_v1.py": protocol["source_sha256"]["completion_v1.py"],
    }
    for path, pin in pins.items():
        if hashlib.sha256(c4.git_blob(path)).hexdigest() != pin:
            raise AssertionError(f"{STEM}: {path.name} differs from its replay pin")
    for path, statements in SCALE_STATEMENTS.items():
        code = c4.git_blob(path)
        if code != c4.git_blob(path, ROBUSTNESS_COMMIT):
            raise AssertionError(f"{STEM}: {path.name} changed after the robustness delivery")
        missing = [statement for statement in statements if statement not in code.decode("utf-8")]
        if missing:
            raise AssertionError(f"{STEM}: {path.name} lacks {missing}")
    check.note("severity scale: completion_v1.py and robustness_saved_owner_v1.py match their replay pins and call "
               "split_integrity.training_scale -> alerts_corrected.per_group_robust_scale "
               "(1.4826 x MAD, at least 20 finite values, pooled fallback); RICO test runs are whole-run blocked "
               "from training, so they take the pooled value; all five files equal the robustness delivery commit")


def verify(fig) -> c4.ValueCheck:
    check = c4.ValueCheck(STEM)

    # Independent read of the summary: weights, the exact zero control, and the pooled values.
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in c4.read_rows(SOURCE):
        groups.setdefault((row["task"], row["cell"]), []).append(row)
    wanted = {(task, cell) for task in c4.TASK_ORDER for cell in [*SCENARIOS, ZERO_CONTROL]}
    check.keys({"|".join(key) for key in groups}, {"|".join(key) for key in wanted}, "settings and scenarios")
    during, pre, delta, dataset = {}, {}, {}, {}
    for (task, cell), rows in groups.items():
        weights = [float(row["cells"]) for row in rows]
        during[(task, cell)], weight = pool(weights, [float(row["mean_coverage_during"]) for row in rows])
        pre[(task, cell)], _ = pool(weights, [float(row["mean_coverage_pre"]) for row in rows])
        delta[(task, cell)], _ = pool(weights, [float(row["mean_delta_coverage_during_vs_pre"]) for row in rows])
        if weight != UNITS:
            raise AssertionError(f"{STEM}: {task}, {cell}: weights total {weight:g}, expected {UNITS}")
        dataset[task] = single([row["dataset"] for row in rows], "dataset")
    check.note(f"cells weights total {UNITS} in all {len(groups)} setting-scenario groups "
               f"({len(c4.TASK_ORDER) * len(SCENARIOS)} plotted, {len(c4.TASK_ORDER)} zero controls)")
    for task in c4.TASK_ORDER:
        if during[(task, ZERO_CONTROL)] != during[(task, CLEAN)]:
            raise AssertionError(f"{STEM}: {task}: zero control differs from clean")
    check.note("zero control (level_shift@0) equals clean exactly in all four settings")

    # Same-window comparison: disturbances leave the pre-window untouched, so pre-minus-during
    # differs from the same-window reduction only by the clean stream's own change between windows.
    largest = 0.0
    for (task, cell), value in during.items():
        if pre[(task, cell)] != pre[(task, CLEAN)]:
            raise AssertionError(f"{STEM}: {task}, {cell}: pre-window coverage differs from clean")
        largest = max(largest, abs((value - pre[(task, cell)]) - delta[(task, cell)]))
    if largest > 1e-12:
        raise AssertionError(f"{STEM}: stored during-minus-pre deltas disagree with the windows by {largest}")
    check.note("pre-window coverage equals clean in every disturbance, so same-window reductions use the same "
               f"window; stored during-minus-pre deltas agree with the pooled windows (max |difference| = {largest:.2g})")

    # Cross-check against the 900-cell unit-level source.
    units: dict[tuple[str, str], dict[str, float]] = {}
    for row in c4.read_rows(CELL_SOURCE):
        units.setdefault((row["dataset"], row["cell"]), {})[row["unit"]] = float(row["coverage_during"])
    largest = 0.0
    for (task, cell), value in during.items():
        values = units[(dataset[task], cell)]
        if len(values) != UNITS:
            raise AssertionError(f"{STEM}: {task}, {cell}: {len(values)} units in {CELL_SOURCE.name}")
        difference = abs(math.fsum(values.values()) / UNITS - value)
        if difference > 1e-12:
            raise AssertionError(f"{STEM}: {task}, {cell}: pooled value differs from the unit mean by {difference}")
        largest = max(largest, difference)
    check.note(f"pooled values equal the 15-unit means in {CELL_SOURCE.name} (max |difference| = {largest:.2g})")
    verify_severity_scale(check)

    # Plotted cells, labels, axes and the shared scale.
    ax = next(axis for axis in fig.axes if axis.get_gid() != f"{GID}scale")
    rows = row_positions()
    check.text(" / ".join(label.get_text() for label in ax.get_xticklabels()),
               " / ".join(COLUMN_LABELS[task] for task in c4.TASK_ORDER), "column order")
    check.text(" / ".join(label.get_text() for label in ax.get_yticklabels()),
               " / ".join(SCENARIOS.values()), "row order")
    written = {(row["task"], row["cell"]): row for row in c4.read_rows(DATA)}
    if len(written) != len(c4.TASK_ORDER) * len(SCENARIOS):
        raise AssertionError(f"{STEM}: {len(written)} data rows")
    plotted = c4.artists_by_gid(fig, GID)
    lowest_contrast = math.inf
    for task in c4.TASK_ORDER:
        for cell, label in SCENARIOS.items():
            value, name = during[(task, cell)], f"{task}, {label}"
            x, y = c4.TASK_ORDER.index(task), rows[cell]
            fill = CMAP(SCALE(value))
            patch = plotted.pop(f"{GID}cell|{task}|{cell}")
            if tuple(patch.get_facecolor()) != tuple(fill):
                raise AssertionError(f"{STEM}: {name}: cell colour does not encode {value!r}")
            check.number(patch.get_x(), x, f"{name} cell column")
            check.number(patch.get_y(), y, f"{name} cell row")
            text = plotted.pop(f"{GID}label|{task}|{cell}")
            check.text(text.get_text(), coverage_label(value), f"{name} label")
            check.number(float(text.get_text()), round(value, 3), f"{name} label value")
            check.number(text.get_position()[0], x + 0.5, f"{name} label column")
            check.number(text.get_position()[1], y + 0.5, f"{name} label row")
            check.color(text.get_color(), c4.label_color(fill), f"{name} label colour")
            contrast = c4.contrast_ratio(text.get_color(), fill)
            if contrast < c4.MIN_LABEL_CONTRAST:
                raise AssertionError(f"{STEM}: {name}: label contrast {contrast:.2f}:1")
            lowest_contrast = min(lowest_contrast, contrast)
            record = written[(task, cell)]
            check.text(record["coverage_label"], coverage_label(value), f"{name} data label")
            for column, expected in (
                ("mean_coverage_during", value),
                ("weight_total", UNITS),
                ("clean_mean_coverage_during", during[(task, CLEAN)]),
                ("same_window_reduction_pp", 100.0 * (during[(task, CLEAN)] - value)),
                ("mean_coverage_pre", pre[(task, cell)]),
                ("pre_minus_during_pp", 100.0 * (pre[(task, cell)] - value)),
            ):
                check.number(float(record[column]), expected, f"{name} data {column}")
    check.note(f"cell labels contrast with their fills at {lowest_contrast:.2f}:1 or more")
    scale = plotted.pop(f"{GID}scale")
    for limit, value in zip(scale.get_xlim(), (0.0, 1.0)):
        check.number(limit, value, "colour scale limit")
    check.text(scale.get_xlabel(), SCALE_LABEL, "colour scale label")
    if plotted:
        raise AssertionError(f"{STEM}: unverified artists {sorted(plotted)}")
    return check


def captions(data) -> tuple[str, str]:
    """Caption and accompanying text, with comparisons formatted from full-precision values."""
    headline = data[data["cell"] == HEADLINE].set_index("task")
    reductions = listing([f"{points(headline.loc[task, 'same_window_reduction_pp'])} ({task})" for task in c4.TASK_ORDER])
    within = listing([points(headline.loc[task, "pre_minus_during_pp"]) for task in c4.TASK_ORDER])
    caption = (
        "Mean empirical coverage of each setting's clean reference prediction intervals during the disturbance "
        "window (25% to 55% of each test stream), under clean conditions and seven sensor disturbances. Each of "
        "the 15 fold-seed units per setting keeps its own historically selected interval "
        "configuration; summary rows are pooled with their cell counts as weights, which total 15 for every setting "
        "and scenario. The Clean row covers the same window of the undisturbed stream, and every cell uses one "
        "coverage scale from 0 to 1. Nominal levels differ between units (0.95 to 0.995), so no common coverage "
        "target is drawn. Severity 1 and severity 2 set the size of a level shift or gradual drift to one or two "
        "units of a training-only robust dispersion: 1.4826 times the median absolute deviation of the training "
        "targets, estimated separately for each physical group with at least 20 finite training values and a "
        "non-zero median absolute deviation, and otherwise taken from the pooled training estimate. RICO HVAC test "
        "runs are held out from training as whole runs, so their disturbances use the pooled estimate."
    )
    accompanying = (
        "Compared with the clean reference over the same window, with cell counts as aggregation weights, level "
        f"shift at severity 2 lowers mean coverage by {reductions} percentage points. These same-window reductions "
        "differ from the within-stream changes between the pre-fault and disturbance windows recorded in "
        f"RESULTS_FINDINGS.md ({within} percentage points in the same order), because the latter also include each "
        "clean stream's own change in coverage between the two windows."
    )
    return caption, accompanying


def reduction_table(data) -> str:
    """Same-window reductions for every disturbance, for use alongside the figure."""
    lines = [
        "| Disturbance | " + " | ".join(c4.TASK_ORDER) + " |",
        "|---|" + "---:|" * len(c4.TASK_ORDER),
    ]
    table = data.set_index(["cell", "task"])
    for cell, label in SCENARIOS.items():
        if cell == CLEAN:
            continue
        values = [points(table.loc[(cell, task), "same_window_reduction_pp"]) for task in c4.TASK_ORDER]
        lines.append(f"| {label} | " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> None:
    c4.apply_style()
    data = derive(c4.read_table(SOURCE))
    data.to_csv(DATA, index=False, lineterminator="\n")
    fig = build(data)
    check = verify(fig)
    outputs = c4.save_figure(fig, STEM, f"Figure 4.6. {CAPTION}")
    plt.close(fig)
    caption, accompanying = captions(data)
    accompanying += ("\n\nSame-window reduction in mean coverage relative to clean (percentage points; cells-weighted, "
                     "full-precision sources rounded to two decimals):\n\n" + reduction_table(data))
    c4.report(
        check,
        [SOURCE, CELL_SOURCE, CONTRACT, COMPLETION_PROTOCOL, *SCALE_STATEMENTS],
        [DATA, *outputs], caption=caption, accompanying=accompanying,
    )


if __name__ == "__main__":
    main()
