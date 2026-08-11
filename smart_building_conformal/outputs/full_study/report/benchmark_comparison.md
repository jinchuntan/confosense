# Benchmark comparison

This document answers *how does ConfoSense compare with prior approaches* at two levels. Level A is the primary evidence: methods implemented and evaluated under one identical protocol here. Level B is contextual: what the literature establishes, classified by whether a numeric comparison is legitimate at all.

---

# A. Controlled internal benchmarks (primary evidence)

All arms share the same partitions, features, seeds, horizons and metric definitions, so differences between them are attributable to the method.

## A1. Point forecasting

MAE by dataset and horizon (lower is better):

| dataset | horizon_steps | attention_lstm | persistence | seasonal_naive | xgboost |
|---|---|---|---|---|---|
| bdg2 | 1 | 19.8654 | 18.9167 | 36.5351 | 21.3487 |
| bdg2 | 3 | 30.2781 | 35.9932 | 36.5265 | 28.1416 |
| bdg2 | 6 | 40.7041 | 60.9113 | 36.5308 | 31.6766 |
| pleia | 1 | 0.8029 | 0.2026 | 1.4768 | 0.3428 |
| pleia | 3 | 0.8126 | 0.3751 | 1.4771 | 0.5317 |
| pleia | 6 | 1.0566 | 0.5457 | 1.4774 | 0.6933 |
| pleia_energy | 1 | 0.1020 | 0.1417 | 0.1982 | 0.0977 |
| pleia_energy | 3 | 0.1056 | 0.1303 | 0.1982 | 0.1042 |
| pleia_energy | 6 | 0.1150 | 0.1417 | 0.1983 | 0.1117 |
| rico | 5 | 0.4443 | 0.1222 | nan | 0.0933 |
| rico | 15 | 0.5194 | 0.3495 | nan | 0.2198 |
| rico | 30 | 0.7511 | 0.6581 | nan | 0.3533 |
| rico | 60 | 0.9238 | 1.2029 | nan | 0.6163 |

Best arm per cell, with improvement over persistence:

| dataset | horizon_steps | point_model | mae | rmse | pct_mae_improvement |
|---|---|---|---|---|---|
| bdg2 | 1 | persistence | 18.9167 | 37.8422 | 0.0000 |
| bdg2 | 3 | xgboost | 28.1416 | 52.6496 | 21.8142 |
| bdg2 | 6 | xgboost | 31.6766 | 60.0627 | 47.9954 |
| pleia | 1 | persistence | 0.2026 | 0.3253 | 0.0000 |
| pleia | 3 | persistence | 0.3751 | 0.6058 | 0.0000 |
| pleia | 6 | persistence | 0.5457 | 0.8723 | 0.0000 |
| pleia_energy | 1 | xgboost | 0.0977 | 2.4510 | 31.0287 |
| pleia_energy | 3 | xgboost | 0.1042 | 2.4517 | 20.0748 |
| pleia_energy | 6 | xgboost | 0.1117 | 2.4524 | 21.1171 |
| rico | 5 | xgboost | 0.0933 | 0.1259 | 23.6623 |
| rico | 15 | xgboost | 0.2198 | 0.3200 | 37.1074 |
| rico | 30 | xgboost | 0.3533 | 0.5145 | 46.3199 |
| rico | 60 | xgboost | 0.6163 | 0.9040 | 48.7655 |

Mean within-dataset ranks:

| dataset | point_model | mean_rank_mae | mean_rank_rmse | mean_pct_mae_improvement | n_blocks |
|---|---|---|---|---|---|
| bdg2 | attention_lstm | 2.3333 | 1.6667 | 14.6794 | 3 |
| bdg2 | persistence | 2.6667 | 3.0000 | 0.0000 | 3 |
| bdg2 | seasonal_naive | 3.3333 | 3.6667 | -18.1973 | 3 |
| bdg2 | xgboost | 1.6667 | 1.6667 | 18.9845 | 3 |
| pleia | attention_lstm | 3.0000 | 3.0000 | -168.8498 | 3 |
| pleia | persistence | 1.0000 | 1.0000 | 0.0000 | 3 |
| pleia | seasonal_naive | 4.0000 | 4.0000 | -364.4795 | 3 |
| pleia | xgboost | 2.0000 | 2.0000 | -45.9935 | 3 |
| pleia_energy | attention_lstm | 2.0000 | 2.0000 | 21.9507 | 3 |
| pleia_energy | persistence | 3.0000 | 3.0000 | 0.0000 | 3 |
| pleia_energy | seasonal_naive | 4.0000 | 4.0000 | -43.9621 | 3 |
| pleia_energy | xgboost | 1.0000 | 1.0000 | 24.0735 | 3 |
| rico | attention_lstm | 2.7500 | 2.5000 | -75.7944 | 4 |
| rico | persistence | 2.2500 | 2.5000 | 0.0000 | 4 |
| rico | xgboost | 1.0000 | 1.0000 | 38.9637 | 4 |

**Finding.** No point-forecasting arm wins everywhere. XGBoost wins on both energy targets and on RICO at every horizon; persistence wins on PLEIA indoor temperature at every horizon and on BDG2 at one hour. Attention-LSTM never wins a cell outright.

## A2. Prediction intervals

Averaged over horizons at nominal 0.95:

| dataset | conformal_method | coverage | coverage_deviation | mean_width | winkler |
|---|---|---|---|---|---|
| bdg2 | cqr | 0.9476 | 0.0033 | 138.8535 | 200.2521 |
| bdg2 | dscp | 0.9274 | 0.0226 | 147.0737 | 287.4609 |
| bdg2 | quantile_uncalibrated | 0.8390 | 0.1110 | 127.0172 | 200.2032 |
| bdg2 | recentred_enbpi_static | 0.9419 | 0.0081 | 187.2787 | 329.7039 |
| bdg2 | recentred_enbpi_updated | 0.9503 | 0.0008 | 203.5668 | 332.9632 |
| pleia | cqr | 0.9417 | 0.0083 | 2.5104 | 3.7967 |
| pleia | dscp | 0.9527 | 0.0135 | 2.8461 | 4.1529 |
| pleia | quantile_uncalibrated | 0.8795 | 0.0705 | 1.9717 | 4.2150 |
| pleia | recentred_enbpi_static | 0.8902 | 0.0598 | 2.2644 | 4.5361 |
| pleia | recentred_enbpi_updated | 0.9313 | 0.0187 | 2.7137 | 4.2553 |
| pleia_energy | cqr | 0.9664 | 0.0164 | 0.4363 | 1.6582 |
| pleia_energy | dscp | 0.9840 | 0.0340 | 0.9029 | 2.0311 |
| pleia_energy | quantile_uncalibrated | 0.8484 | 0.1016 | 0.2978 | 1.7070 |
| pleia_energy | recentred_enbpi_static | 0.9853 | 0.0353 | 1.4036 | 2.5462 |
| pleia_energy | recentred_enbpi_updated | 0.9511 | 0.0027 | 0.8907 | 2.2778 |
| rico | cqr | 0.7719 | 0.1781 | 2.4983 | 11.2602 |
| rico | dscp | 0.8972 | 0.0528 | 1.7902 | 3.3731 |
| rico | quantile_uncalibrated | 0.6304 | 0.3196 | 1.8094 | 12.6819 |
| rico | recentred_enbpi_static | 0.8722 | 0.0778 | 1.4266 | 4.3177 |
| rico | recentred_enbpi_updated | 0.9036 | 0.0464 | 1.7076 | 3.3217 |

Best calibrated arm per dataset (smallest coverage deviation):

| dataset | conformal_method | coverage | coverage_deviation | mean_width | winkler |
|---|---|---|---|---|---|
| bdg2 | recentred_enbpi_updated | 0.9503 | 0.0008 | 203.5668 | 332.9632 |
| pleia | cqr | 0.9417 | 0.0083 | 2.5104 | 3.7967 |
| pleia_energy | recentred_enbpi_updated | 0.9511 | 0.0027 | 0.8907 | 2.2778 |
| rico | recentred_enbpi_updated | 0.9036 | 0.0464 | 1.7076 | 3.3217 |

Best arm per dataset by Winkler score:

| dataset | conformal_method | coverage | coverage_deviation | mean_width | winkler |
|---|---|---|---|---|---|
| bdg2 | quantile_uncalibrated | 0.8390 | 0.1110 | 127.0172 | 200.2032 |
| pleia | cqr | 0.9417 | 0.0083 | 2.5104 | 3.7967 |
| pleia_energy | cqr | 0.9664 | 0.0164 | 0.4363 | 1.6582 |
| rico | recentred_enbpi_updated | 0.9036 | 0.0464 | 1.7076 | 3.3217 |

**Findings.**

1. `quantile_uncalibrated` is the worst-calibrated arm on all four datasets (deviation 0.070-0.320). This is the quantitative case for conformal calibration and is the study's most robust interval result.
2. The best-calibrated arm differs by dataset: `recentred_enbpi_updated` on bdg2, pleia_energy and rico; `cqr` on pleia. No arm dominates.
3. On rico **no arm reaches nominal**; the best observed coverage is 0.904 against 0.95. See `rico_quantile_crossing_audit.md`.
4. Coverage and Winkler disagree on pleia_energy and bdg2: the best-calibrated arm is not the best-scoring arm, because Winkler also prices width. Both must be reported.

## A3. Alerting

F1 on the test partition for every candidate rule (post-hoc sensitivity; the frozen rule was chosen on calibration data alone):

| dataset | 1-of-1 | 2-of-3 | 3-of-5 | 4-of-7 |
|---|---|---|---|---|
| bdg2 | 0.0490 | 0.1370 | 0.2720 | 0.4000 |
| pleia | 0.1749 | 0.3303 | 0.4892 | 0.6733 |
| pleia_energy | 0.2483 | 0.5565 | 0.7126 | 0.7317 |
| rico | 0.3838 | 0.4605 | 0.5224 | 0.5344 |

Frozen operating rule per dataset, evaluated on test:

| dataset | rule | precision | recall | f1 | far | false_alert_events_per_day | median_detection_delay_min |
|---|---|---|---|---|---|---|---|
| bdg2 | 1-of-1 | 0.0252 | 0.8810 | 0.0490 | 0.0575 | 0.9858 | 0.0000 |
| pleia | 4-of-7 | 0.5763 | 0.8095 | 0.6733 | 0.0132 | 0.3562 | 30.0000 |
| pleia_energy | 2-of-3 | 0.4384 | 0.7619 | 0.5565 | 0.0102 | 0.5841 | 10.0000 |
| rico | 2-of-3 | 0.3125 | 0.8750 | 0.4605 | 0.2077 | 11.9457 | 1.0000 |

**Finding.** The best rule is dataset-specific and the spread is large (F1 0.05 to 0.67). Longer persistence windows trade recall for precision monotonically on three of four datasets. Selection procedure and the leakage fix are documented in `alert_selection_audit.md`.

## A4. Recalibration

| dataset | recalibration_strategy | empirical_coverage | coverage_deviation | winkler_score | rolling_window | strategy_is_distinct |
|---|---|---|---|---|---|---|
| bdg2 | static | 0.8432 | 0.1068 | 202.3312 | nan | True |
| bdg2 | periodic | 0.8592 | 0.0908 | 194.0248 | nan | True |
| bdg2 | rolling | 0.8592 | 0.0908 | 194.0248 | nan | False |
| pleia | static | 0.9324 | 0.0176 | 2.8942 | 1000.0000 | True |
| pleia | periodic | 0.9390 | 0.0110 | 2.8773 | 1000.0000 | True |
| pleia | rolling | 0.9480 | 0.0020 | 2.8687 | 1000.0000 | True |
| pleia_energy | static | 0.9810 | 0.0310 | 2.0993 | 1000.0000 | True |
| pleia_energy | periodic | 0.9724 | 0.0224 | 2.0596 | 1000.0000 | True |
| pleia_energy | rolling | 0.9293 | 0.0207 | 1.8660 | 1000.0000 | True |
| rico | static | 0.9051 | 0.0449 | 0.9248 | 500.0000 | True |
| rico | periodic | 0.9256 | 0.0244 | 0.8547 | 500.0000 | True |
| rico | rolling | 0.9119 | 0.0381 | 0.8301 | 500.0000 | True |

**Finding.** Adaptive recalibration improves coverage deviation on all four datasets relative to static. On bdg2 the `rolling` row is **not a distinct strategy** (`strategy_is_distinct = False`): the calibration replay selected an unwindowed configuration, so it reproduces `periodic` exactly.

## A5. Statistical support

| test | scope | n_blocks | n_methods | statistic | p_value | n_blocks_dropped | mean_ranks |
|---|---|---|---|---|---|---|---|
| friedman | point models across dataset/target/horizon blocks | 9 | 4 | 14.0667 | 0.0028 | 4 | {'attention_lstm': 2.4444444444444446, 'persistence': 2.2222222222222223, 'seasonal_naive': 3.7777777777777777, 'xgboost': 1.5555555555555556} |

| test | method_a | method_b | n_blocks | mean_rank_a | mean_rank_b | median_difference | p_value | p_value_holm | significant_holm_5pct |
|---|---|---|---|---|---|---|---|---|---|
| wilcoxon_holm_posthoc | attention_lstm | persistence | 9 | 2.4444 | 2.2222 | -0.0248 | 1.0000 | 1.0000 | False |
| wilcoxon_holm_posthoc | attention_lstm | seasonal_naive | 9 | 2.4444 | 3.7778 | -0.4208 | 0.0742 | 0.3711 | False |
| wilcoxon_holm_posthoc | attention_lstm | xgboost | 9 | 2.4444 | 1.5556 | 0.2810 | 0.0742 | 0.3711 | False |
| wilcoxon_holm_posthoc | persistence | seasonal_naive | 9 | 2.2222 | 3.7778 | -0.5333 | 0.1289 | 0.3867 | False |
| wilcoxon_holm_posthoc | persistence | xgboost | 9 | 2.2222 | 1.5556 | 0.0262 | 1.0000 | 1.0000 | False |
| wilcoxon_holm_posthoc | seasonal_naive | xgboost | 9 | 3.7778 | 1.5556 | 0.9454 | 0.0039 | 0.0234 | True |

**Finding.** The Friedman test rejects equality of the four point models (p = 0.0028), but the Holm-corrected post-hoc finds only seasonal_naive vs xgboost significant (p = 0.0234). XGBoost is **not** significantly better than persistence across blocks (p = 1.000). Statistical significance and practical improvement diverge here and must be reported separately.

---

# B. Published literature (contextual evidence)

**0 of 12 papers are DIRECTLY_COMPARABLE.** No published result in this set shares our dataset, target, horizon, partitioning and metric definition simultaneously, so **this study reports no numeric superiority over any published result.** The matrix below records what each paper contributes instead.

| paper | topic | data | comparability | confosense_arm | notes |
|---|---|---|---|---|---|
| Xu & Xie (2023) | EnbPI: ensemble batch prediction intervals for time series | solar / traffic / electricity benchmarks | PARTIALLY_COMPARABLE | recentred_enbpi_static / recentred_enbpi_updated | Method source for our EnbPI arm. Our implementation is a documented *recentred* adaptation and runs on different data, targets and horizons, so published interval widths are not comparable to ours. Comparable in protocol shape: coverage and width at a nominal level on held-out time. |
| Massidda & Marrocu (2023) | Quantile regression for short-term building load | building electrical load | PARTIALLY_COMPARABLE | cqr / quantile_uncalibrated | Supports the uncalibrated-quantile baseline as a realistic incumbent. Different buildings, different horizon set, no conformal calibration, so no numeric comparison is made. |
| Ibarra et al. (2023) | PLEIAData: smart-building dataset description | PLEIAData | CONTEXTUAL_ONLY | dataset provenance | Source and documentation for our PLEIA temperature and energy targets. Reports no forecasting benchmark we can compare against. |
| Zhang et al. (2024) | Conformal prediction for building energy forecasting | building energy | PARTIALLY_COMPARABLE | cqr | Closest published protocol to our interval arm. Different buildings and split fractions; coverage is comparable as a concept, magnitudes are not. |
| Stjelja et al. (2024) | Data quality and anomaly handling in building data | building monitoring data | CONTEXTUAL_ONLY | robustness / event catalogue | Motivates the disturbance catalogue and the meter-stall finding in the PLEIA energy audit. No forecasting numbers to compare. |
| Sousa et al. (2024) | Probabilistic load forecasting evaluation | load forecasting | PARTIALLY_COMPARABLE | winkler_score / coverage | Supports Winkler score plus coverage as the reporting pair. Different data and horizons. |
| Arpogaus et al. (2025) | Distributional forecasting for energy time series | energy time series | PARTIALLY_COMPARABLE | interval arm generally | Alternative distributional approach not implemented here; contextual for the discussion of what conformal buys over parametric distributions. |
| Nguyen et al. (2025) | Fault detection in HVAC systems | HVAC | CONTEXTUAL_ONLY | alert arm | Motivates interval-violation alerting and the k-of-m persistence rule. Uses labelled real faults; ours are injected, so precision/recall are not comparable quantities. |
| Thiry et al. (2025) | RICO: HVAC experimental dataset | RICO | CONTEXTUAL_ONLY | dataset provenance | Source, sensor documentation and the `Flag` quality field we use to exclude 80 scheduler points. No forecasting benchmark. |
| Yu et al. (2025) | Dual-Splitting Conformal Prediction (arXiv:2503.21251) | energy time series | PARTIALLY_COMPARABLE | dscp | Method source for our DSCP arm, reimplemented from the paper. Our vector is assembled across direct per-horizon models rather than one multi-output model, and the data differ, so published numbers are not comparable. |
| Park et al. (2025) | Smart building anomaly detection | building monitoring | CONTEXTUAL_ONLY | alert arm | Contextual for the alerting design and the false-alerts-per-day workload framing. |
| Von Krannichfeldt et al. (2026) | Online conformal prediction for energy | energy forecasting | PARTIALLY_COMPARABLE | recalibration arm | Closest published work to our static/periodic/rolling recalibration comparison. Different update schedules and data; supports the design, supplies no directly comparable number. |

Machine-readable: `outputs/full_study/combined/literature_benchmark_matrix.csv`.

## How to use this in the dissertation

Permissible: *"EnbPI (Xu & Xie, 2023) and DSCP (Yu et al., 2025) were reimplemented and evaluated under a single protocol alongside CQR and an uncalibrated baseline; under that protocol no method dominated across datasets."*

Not permissible: *"ConfoSense outperforms Zhang et al. (2024)"* — different buildings, different splits, different metric conventions.

## Sources

* `combined/point_metrics.csv`, `combined/model_rankings.csv`
* `combined/interval_metrics.csv`
* `combined/alert_metrics.csv`
* `combined/recalibration_metrics.csv`
* `combined/ranking_tests.csv`, `combined/posthoc_comparisons.csv`
* `combined/literature_benchmark_matrix.csv`
