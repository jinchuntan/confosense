# Table and figure placement map

Derived from `final_tables_index.md` and `final_figures_index.md`. The guiding
constraint: the main body must stay readable. A results chapter that reproduces
every generated table becomes an output dump, and the reader loses the argument.

Classification: **MAIN BODY** · **APPENDIX** · **OMIT** (redundant with a
main-body item; keep the file, do not print it).

---

## 1. Tables

| ID | Ch. | § | Source file | Caption | Purpose | Main takeaway | Placement |
|---|---|---|---|---|---|---|---|
| T5.1 | 5 | 5.1 | `<dataset>/data_profiles/series_profile.csv` + `manifests/dataset_sources.json` | Dataset profiles: target, units, series, observations, sampling, span, horizons | Define what was analysed | Four targets of genuinely different character | **MAIN BODY** |
| T5.2 | 5 | 5.1 | `<dataset>/data_profiles/window_summary.csv` | Supervised window counts by partition at the operating horizon | Give every later metric a denominator | Group-safe partitions, no overlap | **MAIN BODY** |
| T5.3 | 5 | 5.2 | `combined/point_metrics.csv` | Best point forecaster per dataset and horizon | Headline accuracy result | XGBoost 9 of 13 cells; persistence 4 | **MAIN BODY** |
| T5.4 | 5 | 5.2 | `combined/model_rankings.csv` | Mean within-dataset ranks by point model | Per-dataset ordering | XGBoost ranks first on 3 of 4 datasets; persistence first on PLEIA temperature (rank 1.00) | **MAIN BODY** |
| T5.5 | 5 | 5.3 | `combined/interval_metrics.csv` | Interval performance at nominal 0.95, averaged over horizons | Core RQ2 evidence | Uncalibrated undercovers everywhere; no arm dominates | **MAIN BODY** |
| T5.6 | 5 | 5.3 | `combined/interval_metrics.csv` | Coverage at nominal 0.90 | Show the 0.95 finding is not level-specific | Same ordering at 0.90 | **APPENDIX** (B) |
| T5.7 | 5 | 5.4 | `<dataset>/metrics/alert_selection_split.csv` | Nested calibration split: block sizes, embargo, boundary | Evidence the rule saw no conformal residuals | Rule-block origins strictly postdate conformal targets | **MAIN BODY** |
| T5.8 | 5 | 5.4 | `combined/alert_metrics.csv` | Frozen operating rule evaluated on test | Core RQ3 evidence | Rule differs on all four datasets; F1 0.049–0.673 | **MAIN BODY** |
| T5.9 | 5 | 5.5 | `combined/robustness_metrics.csv` | Sensor bias under the fixed-interval protocol | The conventional reading | Fault is loud; clean-reference flat by construction | **MAIN BODY** |
| T5.10 | 5 | 5.5 | `combined/robustness_metrics.csv` | Calibration contamination at 1 / 5 / 10 % | Most damaging disturbance | 10 % makes intervals uninformative | **MAIN BODY** |
| T5.11 | 5 | 5.6 | `combined/robustness_metrics.csv` | 2 σ sensor bias, closed loop, both coverage definitions and clean-reference MAE | The study's headline robustness result | Forecaster absorbs the fault; monitor goes quiet | **MAIN BODY** |
| T5.12 | 5 | 5.7 | `combined/recalibration_metrics.csv` | Static / periodic / rolling recalibration with distinctness flag | RQ3 drift evidence | Adaptive helps on all four; BDG2 rolling not distinct | **MAIN BODY** |
| T5.13 | 5 | 5.8 | `combined/ranking_tests.csv` | Friedman test and mean ranks | Formal cross-dataset test | χ² = 14.07, p = 0.0028 | **MAIN BODY** |
| T5.14 | 5 | 5.8 | `combined/posthoc_comparisons.csv` | Holm-corrected Wilcoxon post-hoc | What survives correction | Only seasonal naive vs XGBoost | **MAIN BODY** |
| T5.15 | 5 | 5.8 | `combined/statistical_tests.csv` | Diebold–Mariano summary by model pair | Per-cell significance | 36 of 48 significant | **MAIN BODY** (summary only; full 48 rows to Appendix E) |
| T5.16 | 5 | 5.9 | `combined/confosense_configurations.csv` | Per-target framework configuration | Cross-dataset synthesis | No universal configuration | **MAIN BODY** |
| T6.1 | 6 | 6.6 | `combined/literature_benchmark_matrix.csv` | Comparability classification of the twelve reviewed studies | Justify the benchmarking position | 0 of 12 directly comparable | **MAIN BODY** (condensed: paper, comparability, arm) |
| T6.2 | 6 | 6.7 | `report/final_confosense_configuration.md` | Evidence class of each configurable choice | Separate validated selections from test-set comparisons | Point model and conformal method are comparisons, not selections | **MAIN BODY** |
| T6.3 | 6 | 6.2–6.4 | `combined/rq_ro_evidence_matrix.csv` | RQ/RO to evidence mapping | Traceability | Every RQ has named persisted evidence | **APPENDIX** (referenced from 6.1) |
| TA.1 | — | App. A | `<dataset>/data_profiles/target_selection.csv`, `run_audit.csv`, `subset_selection.csv` | Dataset selection audits | Show selection was performance-blind | No performance column exists | **APPENDIX** (A) |
| TA.2 | — | App. E | `combined/bootstrap_metrics.csv` | Moving-block bootstrap CIs, 48 rows | Uncertainty on point metrics | Every CI brackets its estimate | **APPENDIX** (E) |
| TA.3 | — | App. E | `combined/effect_sizes.csv` | Pairwise effect sizes | Magnitude alongside significance | XGBoost vs persistence −69.2 % to +48.8 % | **APPENDIX** (E) — cite two rows inline in 6.2 |
| TA.4 | — | App. F | `combined/rico_quantile_crossings.csv` | Crossings by horizon and nominal level | Quantify the CQR repair | 3,912 of 66,696 (5.87 %) | **APPENDIX** (F) — cite the total inline in 5.3 |
| TA.5 | — | App. F | `combined/rico_quantile_crossings_by_run.csv` | Crossings per experimental run | Show concentration | 16 of 42 runs affected | **APPENDIX** (F) |
| TA.6 | — | App. G | `combined/pleia_energy_meter_stalls.csv` | Meter-stall catch-up artefacts | Explain the RMSE | Stalls of 556 and 385 steps | **APPENDIX** (G) — cite inline in 4.4.1 |
| TA.7 | — | App. G | `combined/pleia_energy_artefact_sensitivity.csv` | Point metrics with and without the artefact | Quantify the distortion | RMSE 2.4510 → 0.1550 | **APPENDIX** (G) |
| TA.8 | — | App. G | `combined/pleia_energy_target_profile.json` | Target distribution statistics | Characterise the target | Skew 155, kurtosis 25,318 | **APPENDIX** (G) |
| TA.9 | — | App. H | `manifests/dataset_sources.json` | Provenance: DOIs, licences, checksums | Attribution and reproducibility | All four datasets attributed | **APPENDIX** (H) |
| TA.10 | — | App. H | `manifests/stage_provenance.json`, `run_history.jsonl` | Execution and stage provenance | Reproducibility record | fast_mode false, 0 failed stages | **APPENDIX** (H) |
| TA.11 | — | App. D | `combined/robustness_metrics.csv` (full) | All 15 scenarios × 2 modes, all datasets | Completeness | — | **APPENDIX** (D) |
| TA.12 | — | App. C | `combined/alert_metrics.csv` (full) | All rule surfaces incl. clean-test role | Completeness | — | **APPENDIX** (C) |
| — | — | — | `combined/robustness_metric_schema.csv` | Terminology definitions | Define observed-signal vs clean-reference | — | **MAIN BODY as prose in §3.8.1**, not as a table |

**Main-body table count: 18.** That is a defensible density for a results and
discussion chapter of this scope.

---

## 2. Figures

| ID | Ch. | § | File | Caption | Purpose | Main takeaway | Placement |
|---|---|---|---|---|---|---|---|
| F5.1 | 5 | 5.2 | `fig_01_point_forecasting_comparison.png` | MAE by point model, dataset and horizon | Show accuracy at a glance | No model wins everywhere | **MAIN BODY** |
| F5.2 | 5 | 5.3 | `fig_02_coverage_vs_width.png` | Empirical coverage against mean interval width by method | Show the calibration–width trade-off | Uncalibrated sits low-left: narrow and undercovering | **MAIN BODY** |
| F5.3 | 5 | 5.3 | `fig_03_coverage_deviation_by_horizon.png` | Coverage deviation by horizon and method | Show horizon dependence | Deviation grows with horizon on RICO | **MAIN BODY** |
| F5.4 | 5 | 5.3 | `fig_04_winkler_comparison.png` | Winkler score by method and dataset | Show that Winkler and coverage disagree | Ranking differs from coverage on 2 of 4 datasets | **MAIN BODY** |
| F5.5 | 5 | 5.4 | `fig_05_alert_rule_sensitivity.png` | Precision, recall and F1 across k-of-m rules | Justify the operating point | Precision and recall trade monotonically with k | **MAIN BODY** |
| F5.6 | 5 | 5.4 | `fig_06_alert_tradeoff.png` | Recall against false-alert workload per day | Show budget attainability | RICO meets no rule within 1 alert/day | **MAIN BODY** |
| F5.7 | 5 | 5.5 | `fig_07_robustness_degradation.png` | Coverage under every disturbance, observed-signal and clean-reference panels | Show the full disturbance sweep | The two coverage definitions diverge in closed loop | **MAIN BODY** |
| F5.8 | 5 | 5.6 | `fig_13_closed_loop_absorption.png` | Sensor-bias sweep: both coverage definitions and clean-reference MAE | The headline robustness result | Forecaster absorbs the fault | **MAIN BODY** — the single most important figure |
| F5.9 | 5 | 5.7 | `fig_08_recalibration_recovery.png` | Coverage recovery in blocks after a disturbance onset | Show adaptation speed | Adaptive recovers faster than static | **MAIN BODY** |
| F5.10 | 5 | 5.8 | `fig_09_cross_dataset_rankings.png` | Mean model ranks across datasets | Visual for the Friedman analysis | XGBoost first, seasonal naive last | **APPENDIX** (E) — T5.4 and T5.13 already carry this; keep the main body lean |
| FA.1 | — | App. B | `fig_10_rico_interval_timeline.png` | Interval behaviour within one RICO run | Qualitative illustration | Interval width tracks regime changes | **APPENDIX** (B) |
| FA.2 | — | App. B | `fig_11_bdg2_interval_timeline.png` | Interval behaviour for one BDG2 building | Qualitative illustration | Daily load cycle and width | **APPENDIX** (B) |
| FA.3 | — | App. B | `fig_12_pleia_interval_timeline.png` | Interval behaviour for the PLEIA target | Qualitative illustration | Smooth target, narrow intervals | **APPENDIX** (B) — **or OMIT**: the three timelines make one point between them; one in the main body would be defensible, all three in the main body would not |

**Main-body figure count: 9.** One figure per results subsection plus the two
that carry the interval argument.

---

## 3. Redundancy notes

* `fig_09` duplicates T5.4 and T5.13 — appendix.
* The three interval timelines (`fig_10`–`fig_12`) are qualitative and make the
  same point; keep them together in one appendix section.
* `combined/statistical_tests.csv` has 48 rows; print the four-row summary in the
  main body and the full table in Appendix E.
* `combined/alert_metrics.csv` contains three roles (`calibration_selection`,
  `post_hoc_sensitivity`, `clean_test_no_events`); the main body needs only the
  frozen-rule rows from `post_hoc_sensitivity`, with the calibration surface in
  Appendix C.

---

## 4. Captioning conventions

1. Every caption states the nominal coverage level where one applies.
2. Every robustness caption states the evaluation mode **and** which reference
   signal the metric is computed against.
3. Every table caption names its persisted source file, so a reader can verify.
4. Units are given in the caption, never inferred from the column name.
5. Where a value is qualified by an audit (PLEIA energy RMSE, RICO CQR coverage,
   BDG2 rolling recalibration), the caption carries a one-line footnote pointing
   to the relevant appendix.
