# Dissertation handoff

Everything needed to write the results and discussion chapters. Every numerical statement names the file it came from; all paths are relative to `outputs/full_study/` unless stated otherwise.

## 1. Final dataset definitions

| dataset | n_series | train | calibration | test | horizons |
|---|---|---|---|---|---|
| pleia | 1 | 29318 | 10109 | 10108 | 1,3,6 |
| pleia_energy | 1 | 29320 | 10109 | 10108 | 1,3,6 |
| rico | 207 | 27404 | 9061 | 9282 | 5,15,30,60 |
| bdg2 | 10 | 103527 | 34987 | 34838 | 1,3,6 |

Targets, units, provenance, DOIs, licences and checksums: `manifests/dataset_sources.json`. Selection audits: `<dataset>/data_profiles/`. RICO uses 207 of 287 scheduler groups, excluding 80 on the dataset authors' own `Flag` field (`rico/data_profiles/run_audit.csv`). BDG2 uses 10 of 1,258 eligible buildings across 6 sites and 3 use types (`bdg2/data_profiles/subset_selection.csv`); the selection audit contains no performance column.

## 2. Final experimental design

* chronological 60/20/20 train / calibration / test, group-safe; RICO partitions whole experimental runs, BDG2 partitions within each building (`<dataset>/data_profiles/partitioning.json`)
* direct horizon-specific models; no recursive feeding
* nominal coverage levels 0.90 and 0.95
* alert rules frozen on the later 40% of calibration (`<dataset>/metrics/alert_selection_split.csv`)
* recalibration parameters from a calibration replay with an h-step embargo (`<dataset>/metrics/recalibration_selection.csv`)
* residual availability enforced: a residual is usable at origin t only once its target time has passed
* `fast_mode: False`, 0 failed stages, config hash `7e82f1cb6f19273e` at the time of the full execution (`manifests/run_history.jsonl`; per-stage provenance in `manifests/stage_provenance.json`)

## 3. Final model / configuration matrix

See `report/final_confosense_configuration.md` and `combined/confosense_configurations.csv`. The critical distinction is recorded there: XGBoost hyperparameters, the alert rule and the recalibration settings are **validated selections** made without test data; the point-model family and the conformal method are **reported comparisons** on test data and must not be described as selections.

## 4. Point forecasting findings

| dataset | horizon_steps | point_model | mae | pct_mae_improvement |
|---|---|---|---|---|
| bdg2 | 1 | persistence | 18.9167 | 0.0000 |
| bdg2 | 3 | xgboost | 28.1416 | 21.8142 |
| bdg2 | 6 | xgboost | 31.6766 | 47.9954 |
| pleia | 1 | persistence | 0.2026 | 0.0000 |
| pleia | 3 | persistence | 0.3751 | 0.0000 |
| pleia | 6 | persistence | 0.5457 | 0.0000 |
| pleia_energy | 1 | xgboost | 0.0977 | 31.0287 |
| pleia_energy | 3 | xgboost | 0.1042 | 20.0748 |
| pleia_energy | 6 | xgboost | 0.1117 | 21.1171 |
| rico | 5 | xgboost | 0.0933 | 23.6623 |
| rico | 15 | xgboost | 0.2198 | 37.1074 |
| rico | 30 | xgboost | 0.3533 | 46.3199 |
| rico | 60 | xgboost | 0.6163 | 48.7655 |

Source: `combined/point_metrics.csv`.

## 5. Prediction interval findings

| dataset | conformal_method | coverage | deviation | winkler |
|---|---|---|---|---|
| bdg2 | cqr | 0.9476 | 0.0033 | 200.2521 |
| bdg2 | dscp | 0.9274 | 0.0226 | 287.4609 |
| bdg2 | quantile_uncalibrated | 0.8390 | 0.1110 | 200.2032 |
| bdg2 | recentred_enbpi_static | 0.9419 | 0.0081 | 329.7039 |
| bdg2 | recentred_enbpi_updated | 0.9503 | 0.0008 | 332.9632 |
| pleia | cqr | 0.9417 | 0.0083 | 3.7967 |
| pleia | dscp | 0.9527 | 0.0135 | 4.1529 |
| pleia | quantile_uncalibrated | 0.8795 | 0.0705 | 4.2150 |
| pleia | recentred_enbpi_static | 0.8902 | 0.0598 | 4.5361 |
| pleia | recentred_enbpi_updated | 0.9313 | 0.0187 | 4.2553 |
| pleia_energy | cqr | 0.9664 | 0.0164 | 1.6582 |
| pleia_energy | dscp | 0.9840 | 0.0340 | 2.0311 |
| pleia_energy | quantile_uncalibrated | 0.8484 | 0.1016 | 1.7070 |
| pleia_energy | recentred_enbpi_static | 0.9853 | 0.0353 | 2.5462 |
| pleia_energy | recentred_enbpi_updated | 0.9511 | 0.0027 | 2.2778 |
| rico | cqr | 0.7719 | 0.1781 | 11.2602 |
| rico | dscp | 0.8972 | 0.0528 | 3.3731 |
| rico | quantile_uncalibrated | 0.6304 | 0.3196 | 12.6819 |
| rico | recentred_enbpi_static | 0.8722 | 0.0778 | 4.3177 |
| rico | recentred_enbpi_updated | 0.9036 | 0.0464 | 3.3217 |

Source: `combined/interval_metrics.csv` (nominal 0.95, averaged over horizons).

## 6. Alert findings

| dataset | rule | precision | recall | f1 | far | false_alert_events_per_day | median_detection_delay_min |
|---|---|---|---|---|---|---|---|
| bdg2 | 1-of-1 | 0.0252 | 0.8810 | 0.0490 | 0.0575 | 0.9858 | 0.0000 |
| pleia | 4-of-7 | 0.5763 | 0.8095 | 0.6733 | 0.0132 | 0.3562 | 30.0000 |
| pleia_energy | 2-of-3 | 0.4384 | 0.7619 | 0.5565 | 0.0102 | 0.5841 | 10.0000 |
| rico | 2-of-3 | 0.3125 | 0.8750 | 0.4605 | 0.2077 | 11.9457 | 1.0000 |

Sources: `combined/alert_metrics.csv`, `report/alert_selection_audit.md`.

## 7. Robustness findings

Closed-loop, 2 sd sensor bias:

| dataset | empirical_coverage | empirical_coverage_vs_clean_truth | mae_vs_clean_truth | alert_rate |
|---|---|---|---|---|
| bdg2 | 0.8876 | 0.0529 | 472.0058 | 0.1124 |
| pleia | 0.2580 | 0.0006 | 7.3606 | 0.7315 |
| pleia_energy | 0.9763 | 0.1804 | 0.6216 | 0.0058 |
| rico | 0.5025 | 0.0001 | 10.5115 | 0.4972 |

Sources: `combined/robustness_metrics.csv`, `report/closed_loop_terminology.md`, `combined/robustness_metric_schema.csv`.

## 8. Recalibration findings

| dataset | recalibration_strategy | empirical_coverage | coverage_deviation | winkler_score | strategy_is_distinct |
|---|---|---|---|---|---|
| bdg2 | static | 0.8432 | 0.1068 | 202.3312 | True |
| bdg2 | periodic | 0.8592 | 0.0908 | 194.0248 | True |
| bdg2 | rolling | 0.8592 | 0.0908 | 194.0248 | False |
| pleia | static | 0.9324 | 0.0176 | 2.8942 | True |
| pleia | periodic | 0.9390 | 0.0110 | 2.8773 | True |
| pleia | rolling | 0.9480 | 0.0020 | 2.8687 | True |
| pleia_energy | static | 0.9810 | 0.0310 | 2.0993 | True |
| pleia_energy | periodic | 0.9724 | 0.0224 | 2.0596 | True |
| pleia_energy | rolling | 0.9293 | 0.0207 | 1.8660 | True |
| rico | static | 0.9051 | 0.0449 | 0.9248 | True |
| rico | periodic | 0.9256 | 0.0244 | 0.8547 | True |
| rico | rolling | 0.9119 | 0.0381 | 0.8301 | True |

Source: `combined/recalibration_metrics.csv`.

## 9. Statistical findings

Friedman chi2 = 14.0667, p = 0.002816, 9 complete blocks, 4 dropped (RICO has no seasonal naive). Mean ranks: xgboost 1.556, persistence 2.222, attention_lstm 2.444, seasonal_naive 3.778. Holm post-hoc: only seasonal_naive vs xgboost significant (p = 0.0234); xgboost vs persistence p = 1.000. Diebold-Mariano: 36 of 48 significant after Holm. Sources: `combined/ranking_tests.csv`, `combined/posthoc_comparisons.csv`, `combined/statistical_tests.csv`, `combined/bootstrap_metrics.csv`.

## 10. Benchmark comparison

See `report/benchmark_comparison.md`. Zero of twelve reference papers are directly comparable, so no numeric superiority over published work is claimed anywhere in this study.

## 11-13. RQ evidence

See `report/rq_ro_evidence_matrix.md` and `combined/rq_ro_evidence_matrix.csv` for RQ1-RQ3 with named evidence.

## 14. Methodological limitations

* Anomalies are injected, not observed. Alert precision and recall measure sensitivity to controlled disturbances, not real fault detection performance.
* The point-model family and conformal method were compared on test data; the framework has no pre-registered calibration-side model-selection protocol.
* DSCP uses a multi-step vector assembled across direct per-horizon models rather than one multi-output model, a documented deviation from Yu et al. (2025).
* EnbPI is a documented *recentred* adaptation and is never called plain EnbPI.
* CQR required 2,558 crossed intervals to be order-repaired on RICO at the 0.95 level (`report/rico_quantile_crossing_audit.md`).
* The frozen alert rule is selected against a conformal model calibrated on 60% of the calibration partition, while reported test intervals use 100% of it.
* BDG2 has no distinct rolling-window recalibration result.

## 15. Dataset limitations

* PLEIA is one room in one block; no cross-room generalisation is claimed.
* The PLEIA energy target contains two meter-stall catch-up artefacts, one in calibration and one in test; RMSE on that target is not interpretable without `report/pleia_energy_audit.md`.
* 80 RICO scheduler points are excluded on the authors' quality flag.
* BDG2 is 10 of 1,258 eligible buildings; results are not population-level.

## 16. Computational limitations

* The BDG2 interval stage takes about 2.6 h, dominated by EnbPI's online updates; `update_step` is the lever.
* XGBoost refits are single-threaded to remove thread-order nondeterminism, costing roughly 1.6x on the point stage.
* Reproducibility is verified same-machine; torch results may vary across hardware.

## 17. Claims the dissertation CAN make

1. Conformal calibration measurably improves interval coverage over an uncalibrated quantile baseline on all four targets.
2. The best point forecaster is target-dependent; naive persistence is competitive and sometimes best.
3. No conformal method transfers across all four datasets.
4. Closed-loop evaluation changes the robustness conclusion relative to conventional fixed-interval evaluation.
5. Calibration contamination is the most damaging disturbance studied.
6. Adaptive recalibration reduces coverage deviation on all four datasets.
7. Alert operating points must be tuned per target, on out-of-conformal-calibration data.
8. The framework, its provenance and its results are reproducible from the recorded configuration hash, seeds and checksums.

## 18. Claims the dissertation MUST NOT make

1. That ConfoSense outperforms any published method numerically - no reference paper is directly comparable.
2. That XGBoost is significantly better than persistence - the Holm post-hoc gives p = 1.000.
3. That RICO's run structure *causes* CQR to fail - that is an untested hypothesis.
4. That any method is well calibrated on RICO - none reaches nominal.
5. That the framework detects real building faults - all events are injected.
6. That BDG2 has separate periodic and rolling recalibration results.
7. That the conformal method or point model was *selected* by the framework - those are test-set comparisons.
8. That the PLEIA energy RMSE reflects load volatility - it reflects one meter-stall artefact.

## 19. Final table index

See `report/final_tables_index.md`.

## 20. Final figure index

See `report/final_figures_index.md`. 13 figures are present under `report/figures/`.

