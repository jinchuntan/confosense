# ConfoSense Full Study — Table-Ready Results

_Generated from the persisted CSV outputs._

## Point forecasting

| Dataset | Target | h (steps) | h (min) | Model | MAE | RMSE | MAE sd | MAE impr % | Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | B-room11-V2 | 1 | 10.000 | persistence | 0.203 | 0.325 | n/a | 0.000 | 1 |
| pleia | B-room11-V2 | 1 | 10.000 | seasonal_naive | 1.477 | 2.197 | n/a | -628.922 | 1 |
| pleia | B-room11-V2 | 1 | 10.000 | xgboost | 0.356 | 0.505 | 0.004 | -75.675 | 2 |
| pleia | B-room11-V2 | 1 | 10.000 | attention_lstm | 1.037 | 1.324 | 0.000 | -411.663 | 1 |
| pleia | B-room11-V2 | 3 | 30.000 | persistence | 0.375 | 0.606 | n/a | 0.000 | 1 |
| pleia | B-room11-V2 | 3 | 30.000 | seasonal_naive | 1.477 | 2.198 | n/a | -293.785 | 1 |
| pleia | B-room11-V2 | 3 | 30.000 | xgboost | 0.570 | 0.779 | 0.033 | -51.995 | 2 |
| pleia | B-room11-V2 | 3 | 30.000 | attention_lstm | 1.100 | 1.399 | 0.000 | -193.230 | 1 |

## Prediction intervals

| Dataset | h | Method | Nominal | Empirical | Cov. dev. | Width | Norm. width | Winkler |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 1 | cqr | 0.900 | 0.890 | 0.010 | 1.330 | 0.538 | 1.988 |
| pleia | 1 | quantile_uncalibrated | 0.900 | 0.826 | 0.074 | 1.154 | 0.467 | 2.075 |
| pleia | 1 | cqr | 0.950 | 0.937 | 0.013 | 1.648 | 0.667 | 2.510 |
| pleia | 1 | quantile_uncalibrated | 0.950 | 0.896 | 0.054 | 1.419 | 0.574 | 2.632 |
| pleia | 1 | recentred_enbpi_static | 0.900 | 0.852 | 0.048 | 1.357 | 0.549 | 2.447 |
| pleia | 1 | recentred_enbpi_static | 0.950 | 0.916 | 0.034 | 1.762 | 0.713 | 3.120 |
| pleia | 1 | recentred_enbpi_updated | 0.900 | 0.889 | 0.011 | 1.538 | 0.623 | 2.402 |
| pleia | 1 | recentred_enbpi_updated | 0.950 | 0.941 | 0.009 | 2.009 | 0.813 | 3.025 |
| pleia | 3 | cqr | 0.900 | 0.888 | 0.012 | 2.007 | 0.812 | 3.114 |
| pleia | 3 | quantile_uncalibrated | 0.900 | 0.805 | 0.095 | 1.627 | 0.659 | 3.317 |
| pleia | 3 | cqr | 0.950 | 0.948 | 0.002 | 2.576 | 1.043 | 3.861 |
| pleia | 3 | quantile_uncalibrated | 0.950 | 0.892 | 0.058 | 2.059 | 0.833 | 4.133 |
| pleia | 3 | recentred_enbpi_static | 0.900 | 0.817 | 0.083 | 1.818 | 0.736 | 3.504 |
| pleia | 3 | recentred_enbpi_static | 0.950 | 0.897 | 0.053 | 2.356 | 0.954 | 4.441 |
| pleia | 3 | recentred_enbpi_updated | 0.900 | 0.881 | 0.019 | 2.147 | 0.869 | 3.368 |
| pleia | 3 | recentred_enbpi_updated | 0.950 | 0.935 | 0.015 | 2.758 | 1.117 | 4.216 |
| pleia | 1 | dscp | 0.900 | 0.929 | 0.029 | 1.658 | 0.671 | 2.284 |
| pleia | 3 | dscp | 0.900 | 0.924 | 0.024 | 2.256 | 0.913 | 3.226 |
| pleia | 1 | dscp | 0.950 | 0.964 | 0.014 | 2.172 | 0.879 | 2.900 |
| pleia | 3 | dscp | 0.950 | 0.960 | 0.010 | 2.905 | 1.176 | 4.139 |

## Alert rules

| Dataset | Role | Rule | Precision | Recall | F1 | FAR | False/day | Mean delay | Median delay | Selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | calibration_selection | 1-of-1 | 0.105 | 0.964 | 0.190 | 0.109 | 8.156 | 17.778 | 0.000 | no |
| pleia | calibration_selection | 2-of-3 | 0.215 | 0.929 | 0.349 | 0.077 | 3.384 | 29.231 | 10.000 | no |
| pleia | calibration_selection | 3-of-5 | 0.338 | 0.893 | 0.490 | 0.049 | 1.745 | 34.400 | 20.000 | no |
| pleia | calibration_selection | 4-of-7 | 0.451 | 0.821 | 0.582 | 0.035 | 0.997 | 39.130 | 30.000 | yes |
| pleia | post_hoc_sensitivity | 1-of-1 | 0.063 | 0.893 | 0.117 | 0.063 | 5.314 | 12.000 | 0.000 | no |
| pleia | post_hoc_sensitivity | 2-of-3 | 0.137 | 0.821 | 0.235 | 0.041 | 2.066 | 22.609 | 10.000 | no |
| pleia | post_hoc_sensitivity | 3-of-5 | 0.264 | 0.821 | 0.400 | 0.025 | 0.912 | 32.609 | 20.000 | no |
| pleia | post_hoc_sensitivity | 4-of-7 | 0.479 | 0.821 | 0.605 | 0.014 | 0.356 | 41.739 | 30.000 | yes |
| pleia | clean_test_no_events | 1-of-1 | 0.000 | n/a | n/a | 0.063 | 5.613 | n/a | n/a | no |
| pleia | clean_test_no_events | 2-of-3 | 0.000 | n/a | n/a | 0.041 | 2.180 | n/a | n/a | no |
| pleia | clean_test_no_events | 3-of-5 | 0.000 | n/a | n/a | 0.025 | 0.954 | n/a | n/a | no |
| pleia | clean_test_no_events | 4-of-7 | 0.000 | n/a | n/a | 0.014 | 0.413 | n/a | n/a | yes |

## Robustness

| Dataset | Mode | Scenario | Severity | MAE | Coverage | Cov. dev. | Width | False/day |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | legacy_fixed_intervals | clean | none | 0.314 | 0.937 | 0.013 | 1.648 | 0.413 |
| pleia | closed_loop | clean | none | 0.314 | 0.937 | 0.013 | 1.648 | 0.413 |
| pleia | legacy_fixed_intervals | random_missing_5pct | 5% | 0.312 | 0.938 | 0.012 | 1.648 | 0.385 |
| pleia | closed_loop | random_missing_5pct | 5% | 0.311 | 0.937 | 0.013 | 1.642 | 0.370 |
| pleia | legacy_fixed_intervals | random_missing_10pct | 10% | 0.311 | 0.939 | 0.011 | 1.648 | 0.385 |
| pleia | closed_loop | random_missing_10pct | 10% | 0.307 | 0.939 | 0.011 | 1.634 | 0.356 |
| pleia | legacy_fixed_intervals | block_missing_5pct | 5% | 0.313 | 0.938 | 0.012 | 1.648 | 0.399 |
| pleia | closed_loop | block_missing_5pct | 5% | 0.314 | 0.938 | 0.012 | 1.648 | 0.436 |
| pleia | legacy_fixed_intervals | bias_0.5sd | 0.5 sigma | 2.274 | 0.023 | 0.927 | 1.648 | 0.328 |
| pleia | closed_loop | bias_0.5sd | 0.5 sigma | 0.349 | 0.887 | 0.063 | 1.585 | 1.311 |
| pleia | legacy_fixed_intervals | bias_1.0sd | 1.0 sigma | 4.504 | 0.003 | 0.947 | 1.648 | 0.071 |
| pleia | closed_loop | bias_1.0sd | 1.0 sigma | 0.383 | 0.832 | 0.118 | 1.688 | 2.094 |
| pleia | legacy_fixed_intervals | level_shift_1.0sd | 1.0 sigma | 2.428 | 0.458 | 0.492 | 1.648 | 0.370 |
| pleia | closed_loop | level_shift_1.0sd | 1.0 sigma | 0.354 | 0.876 | 0.074 | 1.631 | 1.282 |
| pleia | legacy_fixed_intervals | drift_1.0sd | 1.0 sigma terminal | 2.291 | 0.206 | 0.744 | 1.648 | 1.539 |
| pleia | closed_loop | drift_1.0sd | 1.0 sigma terminal | 0.352 | 0.885 | 0.065 | 1.603 | 1.254 |
| pleia | legacy_fixed_intervals | stuck_5pct | 5% of region | 0.363 | 0.898 | 0.052 | 1.648 | 0.456 |
| pleia | closed_loop | stuck_5pct | 5% of region | 0.312 | 0.938 | 0.012 | 1.628 | 0.399 |
| pleia | legacy_fixed_intervals | dropout_5pct | 5% of region | 0.442 | 0.908 | 0.042 | 1.648 | 0.399 |
| pleia | closed_loop | dropout_5pct | 5% of region | 0.297 | 0.946 | 0.004 | 1.613 | 0.342 |
| pleia | calibration_contamination | calib_contam_1pct | 1% | n/a | 0.945 | 0.005 | 1.853 | n/a |
| pleia | calibration_contamination | calib_contam_5pct | 5% | n/a | 0.997 | 0.047 | 14.469 | n/a |

## Recalibration

| Dataset | Strategy | Coverage | Cov. dev. | Width | Winkler | Updates | Every | Window |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | static | 0.932 | 0.018 | 1.707 | 2.894 | 0 | 24 | 1000 |
| pleia | periodic | 0.939 | 0.011 | 1.784 | 2.877 | 422 | 24 | 1000 |
| pleia | rolling | 0.948 | 0.002 | 1.891 | 2.869 | 422 | 24 | 1000 |

## Bootstrap confidence intervals

| Dataset | h | Model | MAE | MAE lo | MAE hi | RMSE | RMSE lo | RMSE hi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 1 | persistence | 0.203 | 0.190 | 0.214 | 0.325 | 0.303 | 0.345 |
| pleia | 1 | seasonal_naive | 1.477 | 1.347 | 1.593 | 2.197 | 2.004 | 2.338 |
| pleia | 1 | xgboost | 0.356 | 0.337 | 0.374 | 0.505 | 0.474 | 0.531 |
| pleia | 1 | attention_lstm | 1.037 | 0.986 | 1.096 | 1.324 | 1.253 | 1.398 |
| pleia | 3 | persistence | 0.375 | 0.345 | 0.397 | 0.606 | 0.551 | 0.654 |
| pleia | 3 | seasonal_naive | 1.477 | 1.346 | 1.591 | 2.198 | 2.007 | 2.339 |
| pleia | 3 | xgboost | 0.570 | 0.540 | 0.600 | 0.779 | 0.731 | 0.828 |
| pleia | 3 | attention_lstm | 1.100 | 1.041 | 1.169 | 1.399 | 1.324 | 1.483 |

## Diebold-Mariano tests

| Dataset | h | A | B | DM | p | Holm p | Significant |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 1 | xgboost | persistence | 50.254 | 0.000 | 0.000 | yes |
| pleia | 1 | attention_lstm | persistence | 102.508 | 0.000 | 0.000 | yes |
| pleia | 1 | xgboost | attention_lstm | -88.910 | 0.000 | 0.000 | yes |
| pleia | 1 | seasonal_naive | persistence | 79.250 | 0.000 | 0.000 | yes |
| pleia | 3 | xgboost | persistence | 29.385 | 0.000 | 0.000 | yes |
| pleia | 3 | attention_lstm | persistence | 51.042 | 0.000 | 0.000 | yes |
| pleia | 3 | xgboost | attention_lstm | -39.630 | 0.000 | 0.000 | yes |
| pleia | 3 | seasonal_naive | persistence | 40.443 | 0.000 | 0.000 | yes |

## Model rankings

| Dataset | Model | Mean MAE rank | Mean RMSE rank | Mean impr % | Blocks |
| --- | --- | --- | --- | --- | --- |
| pleia | attention_lstm | 3.000 | 3.000 | -302.447 | 2 |
| pleia | persistence | 1.000 | 1.000 | 0.000 | 2 |
| pleia | seasonal_naive | 4.000 | 4.000 | -461.354 | 2 |
| pleia | xgboost | 2.000 | 2.000 | -63.835 | 2 |

## Post-hoc comparisons (Holm-adjusted)

_not produced by this run_
