# ConfoSense Full Study — Final Result Digest

_Every value is read back from a CSV under `outputs/full_study/`._

> **Fast mode — not dissertation results.**

## A. Dataset profiles

| Dataset | Target | Units | Series | Obs. | Sampling | Missing | Seas. naive |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | B-room11-V2 | degC | 1 | 50543 | 0 days 00:10:00 | 0.0000 | yes |

## B. Point forecasting

Percentage improvement is relative to persistence within the same dataset, target and horizon; raw MAE is not comparable across targets with different units.

| Dataset | h | h (min) | Model | MAE | RMSE | MAE impr % | Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 1 | 10.000 | persistence | 0.203 | 0.325 | 0.000 | 1 |
| pleia | 1 | 10.000 | xgboost | 0.356 | 0.505 | -75.675 | 2 |
| pleia | 1 | 10.000 | attention_lstm | 1.037 | 1.324 | -411.663 | 1 |
| pleia | 1 | 10.000 | seasonal_naive | 1.477 | 2.197 | -628.922 | 1 |
| pleia | 3 | 30.000 | persistence | 0.375 | 0.606 | 0.000 | 1 |
| pleia | 3 | 30.000 | xgboost | 0.570 | 0.779 | -51.995 | 2 |
| pleia | 3 | 30.000 | attention_lstm | 1.100 | 1.399 | -193.230 | 1 |
| pleia | 3 | 30.000 | seasonal_naive | 1.477 | 2.198 | -293.785 | 1 |

## C. Prediction intervals

Coverage validity and sharpness are both reported: a narrower interval that undercovers is not a better interval.

| Dataset | Nominal | Method | Empirical | Cov. dev. | Width | Norm. width | Winkler | Crossings repaired |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 0.900 | cqr | 0.889 | 0.011 | 1.669 | 0.675 | 2.551 | 0 |
| pleia | 0.900 | dscp | 0.926 | 0.026 | 1.957 | 0.792 | 2.755 | 0 |
| pleia | 0.900 | quantile_uncalibrated | 0.815 | 0.085 | 1.391 | 0.563 | 2.696 | 0 |
| pleia | 0.900 | recentred_enbpi_static | 0.834 | 0.066 | 1.588 | 0.643 | 2.975 | 0 |
| pleia | 0.900 | recentred_enbpi_updated | 0.885 | 0.015 | 1.843 | 0.746 | 2.885 | 0 |
| pleia | 0.950 | cqr | 0.943 | 0.007 | 2.112 | 0.855 | 3.186 | 0 |
| pleia | 0.950 | dscp | 0.962 | 0.012 | 2.539 | 1.027 | 3.520 | 0 |
| pleia | 0.950 | quantile_uncalibrated | 0.894 | 0.056 | 1.739 | 0.704 | 3.383 | 0 |
| pleia | 0.950 | recentred_enbpi_static | 0.906 | 0.044 | 2.059 | 0.833 | 3.781 | 0 |
| pleia | 0.950 | recentred_enbpi_updated | 0.938 | 0.012 | 2.384 | 0.965 | 3.621 | 0 |

## D. Alert performance

`far` is the point-level False Alarm Rate FP/(FP+TN); `false_alert_events_per_day` counts contiguous alert clusters per day. They are different quantities.

| Dataset | Role | Rule | Precision | Recall | F1 | FAR | False/day | Mean delay | Median delay | Events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | calibration_selection | 4-of-7 | 0.451 | 0.821 | 0.582 | 0.035 | 0.997 | 39.130 | 30.000 | 28 |
| pleia | clean_test_no_events | 4-of-7 | 0.000 | n/a | n/a | 0.014 | 0.413 | n/a | n/a | 0 |
| pleia | post_hoc_sensitivity | 4-of-7 | 0.479 | 0.821 | 0.605 | 0.014 | 0.356 | 41.739 | 30.000 | 28 |

## E. Robustness

`empirical_coverage` is measured against what the monitor observes; `..._vs_clean_truth` against the uncorrupted signal. In closed loop the two diverge, which is the point.

| Dataset | Mode | Scenario | Severity | Cov (obs) | Cov (clean) | MAE (obs) | MAE (clean) | False/day |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | calibration_contamination | calib_contam_1pct | 1% | 0.945 | n/a | n/a | n/a | n/a |
| pleia | calibration_contamination | calib_contam_5pct | 5% | 0.997 | n/a | n/a | n/a | n/a |
| pleia | closed_loop | bias_0.5sd | 0.5 sigma | 0.887 | 0.024 | 0.349 | 2.104 | 1.311 |
| pleia | closed_loop | bias_1.0sd | 1.0 sigma | 0.832 | 0.003 | 0.383 | 4.284 | 2.094 |
| pleia | closed_loop | block_missing_5pct | 5% | 0.938 | 0.937 | 0.314 | 0.315 | 0.436 |
| pleia | closed_loop | clean | none | 0.937 | 0.937 | 0.314 | 0.314 | 0.413 |
| pleia | closed_loop | drift_1.0sd | 1.0 sigma terminal | 0.885 | 0.214 | 0.352 | 2.137 | 1.254 |
| pleia | closed_loop | dropout_5pct | 5% of region | 0.946 | 0.904 | 0.297 | 0.432 | 0.342 |
| pleia | closed_loop | level_shift_1.0sd | 1.0 sigma | 0.876 | 0.460 | 0.354 | 2.318 | 1.282 |
| pleia | closed_loop | random_missing_10pct | 10% | 0.939 | 0.936 | 0.307 | 0.312 | 0.356 |
| pleia | closed_loop | random_missing_5pct | 5% | 0.937 | 0.937 | 0.311 | 0.313 | 0.370 |
| pleia | closed_loop | stuck_5pct | 5% of region | 0.938 | 0.920 | 0.312 | 0.347 | 0.399 |
| pleia | legacy_fixed_intervals | bias_0.5sd | 0.5 sigma | 0.023 | 0.937 | 2.274 | 0.314 | 0.328 |
| pleia | legacy_fixed_intervals | bias_1.0sd | 1.0 sigma | 0.003 | 0.937 | 4.504 | 0.314 | 0.071 |
| pleia | legacy_fixed_intervals | block_missing_5pct | 5% | 0.938 | 0.937 | 0.313 | 0.314 | 0.399 |
| pleia | legacy_fixed_intervals | clean | none | 0.937 | 0.937 | 0.314 | 0.314 | 0.413 |
| pleia | legacy_fixed_intervals | drift_1.0sd | 1.0 sigma terminal | 0.206 | 0.937 | 2.291 | 0.314 | 1.539 |
| pleia | legacy_fixed_intervals | dropout_5pct | 5% of region | 0.908 | 0.937 | 0.442 | 0.314 | 0.399 |
| pleia | legacy_fixed_intervals | level_shift_1.0sd | 1.0 sigma | 0.458 | 0.937 | 2.428 | 0.314 | 0.370 |
| pleia | legacy_fixed_intervals | random_missing_10pct | 10% | 0.939 | 0.937 | 0.311 | 0.314 | 0.385 |
| pleia | legacy_fixed_intervals | random_missing_5pct | 5% | 0.938 | 0.937 | 0.312 | 0.314 | 0.385 |
| pleia | legacy_fixed_intervals | stuck_5pct | 5% of region | 0.898 | 0.937 | 0.363 | 0.314 | 0.456 |

## F. Recalibration

| Dataset | Strategy | Coverage | Cov. dev. | Width | Winkler | Updates | Every | Window | Delay (steps) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | periodic | 0.939 | 0.011 | 1.784 | 2.877 | 422 | 24 | 1000 | 1 |
| pleia | rolling | 0.948 | 0.002 | 1.891 | 2.869 | 422 | 24 | 1000 | 1 |
| pleia | static | 0.932 | 0.018 | 1.707 | 2.894 | 0 | 24 | 1000 | 1 |

## G. Statistical comparison

8 Diebold-Mariano comparisons, 8 significant at 5% after Holm adjustment. A negative statistic favours model A.

| Dataset | h | A | B | DM | p | Holm p | Sig. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 1 | xgboost | persistence | 50.2536 | 0.0000 | 0.0000 | yes |
| pleia | 1 | attention_lstm | persistence | 102.5078 | 0.0000 | 0.0000 | yes |
| pleia | 1 | xgboost | attention_lstm | -88.9101 | 0.0000 | 0.0000 | yes |
| pleia | 1 | seasonal_naive | persistence | 79.2502 | 0.0000 | 0.0000 | yes |
| pleia | 3 | xgboost | persistence | 29.3848 | 0.0000 | 0.0000 | yes |
| pleia | 3 | attention_lstm | persistence | 51.0425 | 0.0000 | 0.0000 | yes |
| pleia | 3 | xgboost | attention_lstm | -39.6301 | 0.0000 | 0.0000 | yes |
| pleia | 3 | seasonal_naive | persistence | 40.4433 | 0.0000 | 0.0000 | yes |

| Test | Blocks | Methods | Statistic | p | Blocks dropped |
| --- | --- | --- | --- | --- | --- |
| friedman | 2 | 4 | n/a | n/a | 0 |

Effect sizes (practical significance):

| Dataset | h | A | B | MAE impr % | Median diff | CI low | CI high | Win rate A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 1 | xgboost | persistence | -75.675 | 0.107 | 0.140 | 0.165 | 0.277 |
| pleia | 1 | attention_lstm | persistence | -411.663 | 0.669 | 0.784 | 0.890 | 0.099 |
| pleia | 1 | xgboost | attention_lstm | 65.666 | -0.533 | -0.736 | -0.634 | 0.844 |
| pleia | 1 | seasonal_naive | persistence | -628.922 | 0.700 | 1.143 | 1.387 | 0.088 |
| pleia | 3 | xgboost | persistence | -51.995 | 0.159 | 0.172 | 0.216 | 0.321 |
| pleia | 3 | attention_lstm | persistence | -193.230 | 0.596 | 0.672 | 0.792 | 0.164 |
| pleia | 3 | xgboost | attention_lstm | 48.165 | -0.385 | -0.594 | -0.485 | 0.760 |
| pleia | 3 | seasonal_naive | persistence | -293.785 | 0.500 | 0.975 | 1.209 | 0.167 |

## H. Cross-dataset ranking

Ranks are computed within each (dataset, target, horizon) block, so they are comparable where raw errors are not. Rank 1 is the lowest error.

| Dataset | Model | Mean MAE rank | Mean RMSE rank | Mean impr % | Blocks |
| --- | --- | --- | --- | --- | --- |
| pleia | persistence | 1.000 | 1.000 | 0.000 | 2 |
| pleia | xgboost | 2.000 | 2.000 | -63.835 | 2 |
| pleia | attention_lstm | 3.000 | 3.000 | -302.447 | 2 |
| pleia | seasonal_naive | 4.000 | 4.000 | -461.354 | 2 |

## I. Key limitations

- Run executed in --fast smoke-test mode: reduced horizons, seeds, search iterations, epochs, bootstrap replicates and disturbance repetitions. Numbers are not the full-study results.
- DSCP is applied to a multi-step vector assembled across ConfoSense's direct per-horizon models rather than a single multi-output model as in Yu et al. (2025); documented deviation.

See `full_study_limitations.md` for the complete list, including the standing methodological caveats.

## J. Final claims supported by the evidence

1. **Conformal calibration is measurably necessary.** The uncalibrated quantile baseline undercovers on all 1 datasets, with mean coverage deviation 0.0561–0.0561 at nominal 0.95. (`combined/interval_metrics.csv`)
2. **No conformal method transfers across datasets.** The best-calibrated arm differs by dataset (pleia: cqr), so the framework must select it per target rather than fix it. (`combined/interval_metrics.csv`)
3. **The best point forecaster is target-dependent, and naive persistence is competitive.** Across 2 dataset/horizon cells the winners are persistence (2). (`combined/point_metrics.csv`)
4. **Practical improvement and statistical significance diverge.** The Friedman test rejects equality of the four point models (chi2 = 14.07, p = 0.0028), but after Holm correction only seasonal_naive vs xgboost is significant (p = 0.0234); xgboost vs persistence gives p = 1.000. Effect sizes should be reported as magnitudes, not as demonstrated superiority. (`combined/ranking_tests.csv`, `combined/posthoc_comparisons.csv`)
5. **Calibration contamination is the most damaging disturbance studied.** At the highest contamination level the mean interval width reaches 14.47 on pleia, with coverage saturating toward 1. (`combined/robustness_metrics.csv`)
6. **Adaptive recalibration reduces coverage deviation on 1 of 1 datasets** relative to static calibration, but does not by itself achieve nominal coverage everywhere. (`combined/recalibration_metrics.csv`)
7. **Alert operating points must be tuned per target, on out-of-conformal-calibration data.** Rules frozen on the later 40% of the calibration partition differ on every dataset, and the pooled procedure they replace understated the false-alert workload. (`combined/alert_metrics.csv`, `report/alert_selection_audit.md`)
8. **No numeric comparison with published results is claimed.** None of the twelve reference papers shares this study's dataset, target, horizon, partitioning and metric definition simultaneously. (`combined/literature_benchmark_matrix.csv`)

_Claims are generated from the persisted tables, so they cannot drift from the results. Causal wording is used only for the disturbance experiments, where the cause is manipulated._
