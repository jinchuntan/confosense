# Final dissertation structure

**Master of Computer Science (Applied Computing), Universiti Malaya — WOC7024 Dissertation**

Status: the implementation and experimental study are **frozen**. This document
proposes the chapter structure to write against. It changes no result, and it
does not alter the research questions or objectives.

Lower-level headings below refine the agreed high-level structure where the
frozen evidence suggests a clearer arrangement; every refinement is flagged
`[refined]` with a one-line reason.

---

## Chapter 1 — Introduction

| § | Heading | Note |
|---|---|---|
| 1.1 | Research Background | |
| 1.2 | Problem Statement | |
| 1.3 | Research Questions | RQ1–RQ3 unchanged |
| 1.4 | Research Objectives | RO1–RO3 unchanged |
| 1.5 | Research Significance | |
| 1.6 | Research Scope | |
| 1.7 | Dissertation Organisation | |

## Chapter 2 — Literature Review

| § | Heading | Note |
|---|---|---|
| 2.1 | Smart-Building Short-Term Forecasting | |
| 2.2 | Probabilistic Forecasting and Uncertainty Quantification | |
| 2.3 | Conformal Prediction for Time-Series Forecasting | |
| 2.4 | Multistep Conformal Prediction | |
| 2.5 | Interval-Based Alerting and Anomaly Monitoring | |
| 2.6 | Public Smart-Building Datasets and Benchmark Studies | |
| 2.7 | Comparability of Published Benchmarks | `[refined]` new subsection. The comparability classification in `combined/literature_benchmark_matrix.csv` is a reviewed output in its own right and belongs in Chapter 2, so Chapter 6 can refer back rather than re-arguing it |
| 2.8 | Critical Synthesis and Research Gaps | renumbered from 2.7 |
| 2.9 | Chapter Summary | renumbered from 2.8 |

## Chapter 3 — Research Methodology

| § | Heading | Note |
|---|---|---|
| 3.1 | Research Design | |
| 3.2 | Proposed ConfoSense Framework | |
| 3.3 | Dataset Selection and Experimental Setting | |
| 3.4 | Data Preprocessing and Feature Engineering | |
| 3.5 | Point Forecasting Methods | |
| 3.6 | Conformal Prediction Methods | |
| 3.7 | Interval-Based Alert Generation | |
| 3.7.1 | Nested Calibration Split for Rule Selection | `[refined]` the leakage-safe split is a methodological contribution and needs its own numbered subsection, not a paragraph |
| 3.8 | Robustness Evaluation | |
| 3.8.1 | Evaluation Modes and Reference Signals | `[refined]` the observed-signal / clean-reference distinction must be defined before any result uses it |
| 3.9 | Recalibration Strategies | |
| 3.10 | Evaluation Metrics | |
| 3.11 | Statistical Analysis | |
| 3.12 | Reproducibility and Ethical Considerations | |
| 3.13 | Chapter Summary | |

## Chapter 4 — Experimental Setup

| § | Heading | Note |
|---|---|---|
| 4.1 | Experimental Overview | |
| 4.2 | Computing Environment | |
| 4.3 | PLEIAData Temperature Experiment | |
| 4.4 | PLEIAData Energy Experiment | |
| 4.4.1 | Target Definition and Meter-Stall Artefacts | `[refined]` a reader must meet the artefacts before Chapter 5 quotes an RMSE that one of them dominates |
| 4.5 | RICO HVAC Experiment | |
| 4.6 | BDG2 Cross-Building Experiment | |
| 4.7 | Forecast Horizons and Model Configurations | |
| 4.8 | Conformal and Alert Configurations | |
| 4.9 | Robustness and Recalibration Configuration | |
| 4.10 | Experimental Controls and Leakage Prevention | |
| 4.11 | Chapter Summary | |

## Chapter 5 — Results

| § | Heading | Note |
|---|---|---|
| 5.1 | Dataset Profiles | |
| 5.2 | Point Forecasting Results | |
| 5.3 | Prediction Interval Results | |
| 5.4 | Alert-Rule Selection and Alert Performance | |
| 5.5 | Robustness Results | fixed-interval (legacy) protocol |
| 5.6 | Closed-Loop Disturbance Analysis | |
| 5.7 | Recalibration Results | |
| 5.8 | Statistical Analysis | |
| 5.9 | Cross-Dataset Comparative Results | |
| 5.10 | Chapter Summary | |

Detailed content, sources and prohibited claims: `chapter5_results_blueprint.md`.

## Chapter 6 — Discussion

| § | Heading | Note |
|---|---|---|
| 6.1 | Overview | |
| 6.2 | RQ1: Integrated Uncertainty-Aware Monitoring Framework | |
| 6.3 | RQ2: Conformal Prediction Across Smart-Building Datasets | |
| 6.4 | RQ3: Alert Reliability and Robustness | |
| 6.5 | Comparison with Controlled Benchmark Methods | primary comparative evidence |
| 6.6 | Comparison with Published Literature | contextual evidence only |
| 6.7 | Definition and Configuration of ConfoSense | |
| 6.8 | Practical Implications for Smart-Building Monitoring | |
| 6.9 | Limitations | |
| 6.10 | Chapter Summary | |

Detailed content: `chapter6_discussion_blueprint.md`; wording for 6.6 and 6.7 in
`benchmarking_and_contribution_wording.md`.

## Chapter 7 — Conclusion and Future Work

| § | Heading |
|---|---|
| 7.1 | Research Summary |
| 7.2 | Findings Against Research Objectives |
| 7.3 | Methodological Contribution |
| 7.4 | Experimental Contribution |
| 7.5 | Applied Monitoring Contribution |
| 7.6 | Limitations |
| 7.7 | Future Work |
| 7.8 | Conclusion |

## References

## Appendices

| Appendix | Content | Source |
|---|---|---|
| A | Dataset selection audits (PLEIA target, RICO run acceptance, BDG2 subset) | `<dataset>/data_profiles/` |
| B | Full interval metric tables at both nominal levels and all horizons | `combined/interval_metrics.csv` |
| C | Complete alert-rule surfaces (calibration, test, clean-test) | `combined/alert_metrics.csv` |
| D | Complete robustness scenario tables, both modes | `combined/robustness_metrics.csv` |
| E | Statistical test tables (bootstrap CIs, all 48 Diebold–Mariano tests) | `combined/bootstrap_metrics.csv`, `combined/statistical_tests.csv` |
| F | RICO quantile-crossing audit incl. per-run counts | `combined/rico_quantile_crossings*.csv` |
| G | PLEIA energy target audit (distribution, meter stalls, sensitivity) | `combined/pleia_energy_*` |
| H | Reproducibility record: manifests, provenance, stage provenance, environment | `manifests/` |
| I | Preliminary experiment (progress report) results, retained for continuity | `outputs/` (Part 1) |

---

## Writing sequence recommended

1. Chapter 3 and Chapter 4 first — they are the most complete in the progress
   report and need mainly tense and scope corrections.
2. Chapter 5 next, straight from `chapter5_results_blueprint.md`.
3. Chapter 6 after Chapter 5 is fixed, so no interpretation precedes its result.
4. Chapter 2 revision, informed by what Chapter 6 actually needs to compare.
5. Chapter 1 and Chapter 7 last, once the findings are settled.
