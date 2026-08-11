# Progress report → final dissertation migration plan

**Scope note.** The progress-report document itself is not held in this
repository, so this plan is keyed to the section structure of a WOC7024 progress
report as described (Introduction, Literature Review, Methodology, Risk, Ethics,
Sustainability, preliminary results, timeline) and to the repository's own record
of what the progress report contained: the preliminary PLEIAData experiment
described in Part 1 of `README.md` and reproduced under `outputs/`. **Confirm the
section numbers against your actual document before applying.** The disposition
and the reasoning transfer regardless of numbering.

Dispositions used:

| Code | Meaning |
|---|---|
| **KEEP** | Keep as-is |
| **MINOR** | Keep with minor revision |
| **PAST** | Rewrite in past tense; the work is done |
| **MOVE** | Move to another chapter |
| **REPLACE** | Replace with full-study results |
| **APPENDIX** | Remove from the main body, retain as appendix |

---

## 1. Introduction

| Progress-report section | Disposition | Reason |
|---|---|---|
| Research background | **KEEP** | Motivation is unchanged by the results. |
| Problem statement | **MINOR** | The study now supplies the empirical case. Add one sentence citing the measured failure of uncalibrated quantile intervals on all four datasets (deviation 0.0705–0.3196 at nominal 0.95, `combined/interval_metrics.csv`) so the problem is evidenced rather than asserted. |
| Research questions | **KEEP** | Frozen. Do not reword. |
| Research objectives | **KEEP** | Frozen. Do not reword. |
| Research significance | **PAST** | Rewrite "this research will contribute" as delivered contributions. Replace "expected contribution" wholesale — see §7 below. |
| Research scope | **MINOR** | Scope grew from one PLEIAData target to four targets across three sources. State the final scope: 4 targets, 3 datasets, 13 dataset/horizon cells, 5 interval methods, 4 alert rules, 15 disturbance scenarios × 2 modes, 3 recalibration strategies. |
| Dissertation organisation | **MINOR** | Update to the seven-chapter structure in `final_dissertation_structure.md`. |

**Language to remove from Chapter 1:** "will be evaluated", "planned", "the next
phase", "expected contribution", "pending". Every item they referred to has been
executed (`manifests/run_history.jsonl`, `manifests/stage_provenance.json`).

---

## 2. Literature Review

| Progress-report section | Disposition | Reason |
|---|---|---|
| Smart-building forecasting | **KEEP** | Still current. |
| Probabilistic forecasting / UQ | **MINOR** | Add the distinction the study relies on: an uncalibrated quantile band versus a conformalized one. |
| Conformal prediction background | **MINOR** | Tighten to what the study actually implements: split conformal, CQR, EnbPI, DSCP. |
| Multistep conformal prediction | **MINOR** | Foreground DSCP (Yu et al., 2025) since it is implemented here, and state up front that this study assembles the multi-step vector across direct per-horizon models rather than one multi-output model. |
| Interval-based alerting | **MINOR** | Add the operating-point framing (k-of-m persistence, false-alert budget) that the study uses. |
| Dataset review | **MINOR** | Three datasets now, not one: PLEIAData, RICO, BDG2, with DOIs and licences from `manifests/dataset_sources.json`. |
| Comparison table of prior studies | **REPLACE** | Replace with the audited comparability classification: `combined/literature_benchmark_matrix.csv`, 12 papers, 0 DIRECTLY_COMPARABLE, 7 PARTIALLY_COMPARABLE, 5 CONTEXTUAL_ONLY. A progress-report table implying head-to-head comparability is no longer defensible. |
| Research gap statement | **PAST** | The gaps are now addressed. Rewrite as "this study addressed …" and point forward to the RQ/RO evidence matrix. |

---

## 3. Methodology

This is the chapter that survives best. Most of it needs tense correction, not
rewriting.

| Progress-report section | Disposition | Reason |
|---|---|---|
| Research design | **PAST** | Was written as a plan; the design was executed in full. |
| Proposed framework diagram | **MINOR** | Keep the diagram; relabel the alert block to show the nested calibration split, and the robustness block to show the two evaluation modes. |
| Dataset description | **REPLACE** | Progress report covered PLEIAData only. Replace with all four targets and their audited selection rules (`<dataset>/data_profiles/`). |
| Preprocessing / feature engineering | **MINOR** | Unchanged in substance; note that seasonal features are disabled where no full cycle exists (RICO). |
| Point forecasting methods | **PAST** | Same four arms as planned; rewrite in past tense. |
| Conformal methods | **PAST + MINOR** | CQR and EnbPI as planned; **DSCP was added** and must now be described. Also state that the EnbPI arm is a documented *recentred* adaptation and is never called plain EnbPI. |
| Alert generation | **REWRITE** | The progress-report procedure scored rules on the same calibration sample that conformalized the model. That is superseded. Describe the nested chronological split (60 % conformal / 40 % rule block, exact embargo) and cite `report/alert_selection_audit.md` and `<dataset>/metrics/alert_selection_split.csv`. **This is the single most important methodological change since the progress report.** |
| Robustness evaluation | **REWRITE** | The progress report described a small perturbation probe. The final study runs 15 scenarios in two modes plus three contamination levels, and defines observed-signal versus clean-reference metrics. See `report/closed_loop_terminology.md`. |
| Recalibration | **PAST** | Executed as planned; add the h-step embargo in the calibration replay. |
| Evaluation metrics | **MINOR** | Add Winkler score, coverage deviation, the two distinct false-alarm measures (point-level FAR versus false alerts per day), and detection delay. |
| Statistical analysis | **PAST** | Executed: bootstrap CIs, Diebold–Mariano with HLN correction, Friedman, Holm-corrected post-hoc. |
| Reproducibility | **PAST + MINOR** | Now evidenced: config hashing, seeds, thread pinning, provenance with checksums, resume ledger, 170 passing tests. |
| **Risk management** | **APPENDIX** | Forward-looking project-risk register. The risks either materialised and were handled or did not occur; a risk table in the main body of a completed dissertation reads as unfinished work. Retain as an appendix only if the programme requires it. |
| **Sustainability** | **MOVE** | Move into §3.12 Reproducibility and Ethical Considerations as a short subsection, or into §6.8 Practical Implications. It does not warrant a standalone chapter-level section in the final document. |
| **Ethics** | **KEEP → §3.12** | Keep the substance; merge into the reproducibility/ethics section. All datasets are public with recorded licences (`manifests/dataset_sources.json`), so the ethics position is short and factual. |
| **Project timeline / Gantt** | **REMOVE** | A completed dissertation does not carry a forward plan. |

---

## 4. Experimental setup

The progress report had no separate setup chapter; this is largely new writing.

| Item | Disposition | Source |
|---|---|---|
| Computing environment | **NEW** | Python 3.11.9 in a clean virtual environment; package versions, thread configuration and seeds in `manifests/` |
| Per-dataset experiments | **NEW** | `<dataset>/data_profiles/`, `manifests/dataset_sources.json` |
| Horizons and configurations | **PARTIAL REUSE** | Progress-report PLEIA settings still apply to §4.3; the rest is new |
| Leakage prevention | **NEW** | Group-safe windowing, delayed residual availability, nested alert split, embargoed calibration replay |

---

## 5. Preliminary results (progress report)

| Progress-report content | Disposition | Reason |
|---|---|---|
| Preliminary PLEIAData point results | **REPLACE** | Superseded by the full study's PLEIA temperature results (`combined/point_metrics.csv`). |
| Preliminary CQR / EnbPI intervals | **REPLACE** | Superseded by five interval arms at two nominal levels. |
| Preliminary alerting results | **REPLACE** | Superseded, and the selection procedure itself changed — the preliminary rule was chosen under the pooled procedure this study replaced. |
| Preliminary robustness probe | **REPLACE** | Superseded by 15 scenarios × 2 modes plus contamination. |
| Preliminary figures | **APPENDIX** | Retain in Appendix I for continuity with the Proposal Defence; do not place in the main body. |
| Statement that results are preliminary | **REMOVE** | No longer true of the study. Keep one sentence in Appendix I noting that the preliminary experiment remains reproducible and unmodified. |

**Do not delete the preliminary experiment from the repository.** It stays as a
frozen, reproducible baseline; it simply leaves the main body of the
dissertation.

---

## 6. Global language sweep

Search the whole document for these and resolve each:

| Phrase | Action |
|---|---|
| "will be evaluated" / "will be implemented" | → past tense; the work is complete |
| "planned" / "is planned to" | → delete or convert to what was done |
| "preliminary" | → keep **only** when referring to Appendix I |
| "the next phase" / "future stage" | → delete; move genuine future items to §7.7 Future Work |
| "expected contribution" | → "contribution", with the evidence cited |
| "pending" / "to be determined" | → resolve against the frozen outputs; nothing is pending |
| "proposed method" (when meaning the executed one) | → "the framework" or "ConfoSense", past tense |
| "EnbPI" alone | → "recentred EnbPI" — the adaptation is documented and must not be blurred |

---

## 7. "Expected contribution" → delivered contribution

Replace the progress report's expected-contribution paragraph with three
delivered contributions, each pointing at persisted evidence:

1. **Methodological.** A leakage-safe operating-point selection procedure for
   interval-based alerting: a nested chronological split inside the calibration
   partition with an exact embargo, so alert rules are never tuned on the
   residuals that set the conformal quantile. Evidence:
   `report/alert_selection_audit.md`, `<dataset>/metrics/alert_selection_split.csv`.
   Changing to it moved 2 of 4 frozen rules.

2. **Experimental.** A single controlled protocol under which four point
   forecasters, five interval methods, four alert rules, three recalibration
   strategies and fifteen disturbance scenarios in two evaluation modes were
   compared across four heterogeneous smart-building targets. Evidence:
   `combined/` (20 tables), `manifests/stage_provenance.json`.

3. **Applied.** A dual-mode robustness evaluation that separates observed-signal
   from clean-reference metrics, and which shows that the conventional
   fixed-interval protocol misstates fault sensitivity. Evidence:
   `combined/robustness_metrics.csv`, `report/closed_loop_terminology.md`,
   `report/figures/fig_13_closed_loop_absorption.png`.

---

## 8. Items that must be added because they did not exist at progress-report time

| Item | Where it belongs | Source |
|---|---|---|
| DSCP method description | §2.4, §3.6 | `report/final_result_digest.md`, `<dataset>/models/dscp_level*.json` |
| Nested alert-selection split | §3.7.1 | `report/alert_selection_audit.md` |
| Observed-signal / clean-reference terminology | §3.8.1 | `report/closed_loop_terminology.md`, `combined/robustness_metric_schema.csv` |
| PLEIA energy meter-stall artefacts | §4.4.1, Appendix G | `report/pleia_energy_audit.md` |
| RICO quantile-crossing audit | §5.3 caveat, Appendix F | `report/rico_quantile_crossing_audit.md` |
| BDG2 rolling-recalibration degeneracy | §5.7 | `combined/recalibration_metrics.csv` (`strategy_is_distinct`) |
| Literature comparability classification | §2.7, §6.6 | `combined/literature_benchmark_matrix.csv` |
| ConfoSense as a configurable framework | §3.2, §6.7 | `report/final_confosense_configuration.md` |
