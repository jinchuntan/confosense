# ConfoSense Full Study — Final Result Digest

_Every value is read back from a CSV under `outputs/full_study/`._

_Generated from a full (non-fast) run: `fast_mode: false`._

## A. Dataset profiles

| Dataset | Target | Units | Series | Obs. | Sampling | Missing | Seas. naive |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | electricity | kWh | 10 | 175440 | 0 days 01:00:00 | 0.0000 | yes |
| pleia | B-room11-V2 | degC | 1 | 50543 | 0 days 00:10:00 | 0.0000 | yes |
| pleia_energy | blockB-dif_cons | kWh per interval | 1 | 50545 | 0 days 00:10:00 | 0.0000 | yes |
| rico | B.RTD3 | degC | 207 | 49680 | 0 days 00:01:00 | 0.0000 | no |

## B. Point forecasting

Percentage improvement is relative to persistence within the same dataset, target and horizon; raw MAE is not comparable across targets with different units.

| Dataset | h | h (min) | Model | MAE | RMSE | MAE impr % | Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | 60.000 | persistence | 18.917 | 37.842 | 0.000 | 1 |
| bdg2 | 1 | 60.000 | attention_lstm | 19.865 | 35.305 | -5.015 | 3 |
| bdg2 | 1 | 60.000 | xgboost | 21.349 | 39.710 | -12.856 | 5 |
| bdg2 | 1 | 60.000 | seasonal_naive | 36.535 | 79.070 | -93.136 | 1 |
| bdg2 | 3 | 180.000 | xgboost | 28.142 | 52.650 | 21.814 | 5 |
| bdg2 | 3 | 180.000 | attention_lstm | 30.278 | 57.164 | 15.878 | 3 |
| bdg2 | 3 | 180.000 | persistence | 35.993 | 70.023 | 0.000 | 1 |
| bdg2 | 3 | 180.000 | seasonal_naive | 36.527 | 79.076 | -1.482 | 1 |
| bdg2 | 6 | 360.000 | xgboost | 31.677 | 60.063 | 47.995 | 5 |
| bdg2 | 6 | 360.000 | seasonal_naive | 36.531 | 79.099 | 40.026 | 1 |
| bdg2 | 6 | 360.000 | attention_lstm | 40.704 | 75.029 | 33.175 | 3 |
| bdg2 | 6 | 360.000 | persistence | 60.911 | 106.777 | 0.000 | 1 |
| pleia | 1 | 10.000 | persistence | 0.203 | 0.325 | 0.000 | 1 |
| pleia | 1 | 10.000 | xgboost | 0.343 | 0.501 | -69.192 | 5 |
| pleia | 1 | 10.000 | attention_lstm | 0.803 | 1.074 | -296.276 | 3 |
| pleia | 1 | 10.000 | seasonal_naive | 1.477 | 2.197 | -628.922 | 1 |
| pleia | 3 | 30.000 | persistence | 0.375 | 0.606 | 0.000 | 1 |
| pleia | 3 | 30.000 | xgboost | 0.532 | 0.728 | -41.745 | 5 |
| pleia | 3 | 30.000 | attention_lstm | 0.813 | 1.075 | -116.651 | 3 |
| pleia | 3 | 30.000 | seasonal_naive | 1.477 | 2.198 | -293.785 | 1 |
| pleia | 6 | 60.000 | persistence | 0.546 | 0.872 | 0.000 | 1 |
| pleia | 6 | 60.000 | xgboost | 0.693 | 0.950 | -27.043 | 5 |
| pleia | 6 | 60.000 | attention_lstm | 1.057 | 1.369 | -93.622 | 3 |
| pleia | 6 | 60.000 | seasonal_naive | 1.477 | 2.198 | -170.731 | 1 |
| pleia_energy | 1 | 10.000 | xgboost | 0.098 | 2.451 | 31.029 | 5 |
| pleia_energy | 1 | 10.000 | attention_lstm | 0.102 | 2.451 | 28.035 | 3 |
| pleia_energy | 1 | 10.000 | persistence | 0.142 | 3.463 | 0.000 | 1 |
| pleia_energy | 1 | 10.000 | seasonal_naive | 0.198 | 3.468 | -39.848 | 1 |
| pleia_energy | 3 | 30.000 | xgboost | 0.104 | 2.452 | 20.075 | 5 |
| pleia_energy | 3 | 30.000 | attention_lstm | 0.106 | 2.452 | 18.990 | 3 |
| pleia_energy | 3 | 30.000 | persistence | 0.130 | 3.457 | 0.000 | 1 |
| pleia_energy | 3 | 30.000 | seasonal_naive | 0.198 | 3.468 | -52.069 | 1 |
| pleia_energy | 6 | 60.000 | xgboost | 0.112 | 2.452 | 21.117 | 5 |
| pleia_energy | 6 | 60.000 | attention_lstm | 0.115 | 2.453 | 18.827 | 3 |
| pleia_energy | 6 | 60.000 | persistence | 0.142 | 3.457 | 0.000 | 1 |
| pleia_energy | 6 | 60.000 | seasonal_naive | 0.198 | 3.469 | -39.970 | 1 |
| rico | 5 | 5.000 | xgboost | 0.093 | 0.126 | 23.662 | 5 |
| rico | 5 | 5.000 | persistence | 0.122 | 0.215 | 0.000 | 1 |
| rico | 5 | 5.000 | attention_lstm | 0.444 | 0.547 | -263.654 | 3 |
| rico | 15 | 15.000 | xgboost | 0.220 | 0.320 | 37.107 | 5 |
| rico | 15 | 15.000 | persistence | 0.350 | 0.601 | 0.000 | 1 |
| rico | 15 | 15.000 | attention_lstm | 0.519 | 0.676 | -48.605 | 3 |
| rico | 30 | 30.000 | xgboost | 0.353 | 0.515 | 46.320 | 5 |
| rico | 30 | 30.000 | persistence | 0.658 | 1.103 | 0.000 | 1 |
| rico | 30 | 30.000 | attention_lstm | 0.751 | 0.945 | -14.118 | 3 |
| rico | 60 | 60.000 | xgboost | 0.616 | 0.904 | 48.765 | 5 |
| rico | 60 | 60.000 | attention_lstm | 0.924 | 1.165 | 23.199 | 3 |
| rico | 60 | 60.000 | persistence | 1.203 | 1.890 | 0.000 | 1 |

Not applicable:

| Dataset | Model | Reason |
| --- | --- | --- |
| rico | seasonal_naive | not applicable: no series contains a full seasonal cycle |

## C. Prediction intervals

Coverage validity and sharpness are both reported: a narrower interval that undercovers is not a better interval.

| Dataset | Nominal | Method | Empirical | Cov. dev. | Width | Norm. width | Winkler | Crossings repaired |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 0.900 | cqr | 0.899 | 0.003 | 105.404 | 0.437 | 157.575 | 0 |
| bdg2 | 0.900 | dscp | 0.869 | 0.031 | 105.187 | 0.436 | 215.237 | 0 |
| bdg2 | 0.900 | quantile_uncalibrated | 0.812 | 0.088 | 101.325 | 0.420 | 157.590 | 0 |
| bdg2 | 0.900 | recentred_enbpi_static | 0.892 | 0.008 | 129.827 | 0.538 | 246.046 | 0 |
| bdg2 | 0.900 | recentred_enbpi_updated | 0.904 | 0.004 | 139.828 | 0.579 | 247.014 | 0 |
| bdg2 | 0.950 | cqr | 0.948 | 0.003 | 138.853 | 0.575 | 200.252 | 0 |
| bdg2 | 0.950 | dscp | 0.927 | 0.023 | 147.074 | 0.609 | 287.461 | 0 |
| bdg2 | 0.950 | quantile_uncalibrated | 0.839 | 0.111 | 127.017 | 0.526 | 200.203 | 0 |
| bdg2 | 0.950 | recentred_enbpi_static | 0.942 | 0.008 | 187.279 | 0.776 | 329.704 | 0 |
| bdg2 | 0.950 | recentred_enbpi_updated | 0.950 | 0.001 | 203.567 | 0.843 | 332.963 | 0 |
| pleia | 0.900 | cqr | 0.893 | 0.008 | 2.017 | 0.816 | 3.030 | 0 |
| pleia | 0.900 | dscp | 0.912 | 0.023 | 2.211 | 0.895 | 3.274 | 0 |
| pleia | 0.900 | quantile_uncalibrated | 0.804 | 0.096 | 1.600 | 0.648 | 3.243 | 0 |
| pleia | 0.900 | recentred_enbpi_static | 0.814 | 0.086 | 1.740 | 0.704 | 3.573 | 0 |
| pleia | 0.900 | recentred_enbpi_updated | 0.873 | 0.027 | 2.101 | 0.851 | 3.410 | 0 |
| pleia | 0.950 | cqr | 0.942 | 0.008 | 2.510 | 1.016 | 3.797 | 0 |
| pleia | 0.950 | dscp | 0.953 | 0.013 | 2.846 | 1.152 | 4.153 | 0 |
| pleia | 0.950 | quantile_uncalibrated | 0.880 | 0.070 | 1.972 | 0.798 | 4.215 | 0 |
| pleia | 0.950 | recentred_enbpi_static | 0.890 | 0.060 | 2.264 | 0.917 | 4.536 | 0 |
| pleia | 0.950 | recentred_enbpi_updated | 0.931 | 0.019 | 2.714 | 1.098 | 4.255 | 0 |
| pleia_energy | 0.900 | cqr | 0.934 | 0.034 | 0.327 | 0.133 | 1.014 | 0 |
| pleia_energy | 0.900 | dscp | 0.969 | 0.069 | 0.728 | 0.295 | 1.336 | 0 |
| pleia_energy | 0.900 | quantile_uncalibrated | 0.775 | 0.125 | 0.226 | 0.091 | 1.038 | 0 |
| pleia_energy | 0.900 | recentred_enbpi_static | 0.965 | 0.065 | 0.860 | 0.349 | 1.505 | 0 |
| pleia_energy | 0.900 | recentred_enbpi_updated | 0.905 | 0.005 | 0.597 | 0.242 | 1.452 | 0 |
| pleia_energy | 0.950 | cqr | 0.966 | 0.016 | 0.436 | 0.177 | 1.658 | 0 |
| pleia_energy | 0.950 | dscp | 0.984 | 0.034 | 0.903 | 0.366 | 2.031 | 0 |
| pleia_energy | 0.950 | quantile_uncalibrated | 0.848 | 0.102 | 0.298 | 0.121 | 1.707 | 0 |
| pleia_energy | 0.950 | recentred_enbpi_static | 0.985 | 0.035 | 1.404 | 0.569 | 2.546 | 0 |
| pleia_energy | 0.950 | recentred_enbpi_updated | 0.951 | 0.003 | 0.891 | 0.361 | 2.278 | 0 |
| rico | 0.900 | cqr | 0.828 | 0.072 | 2.049 | 0.453 | 3.965 | 1354 |
| rico | 0.900 | dscp | 0.829 | 0.071 | 1.412 | 0.317 | 2.684 | 0 |
| rico | 0.900 | quantile_uncalibrated | 0.564 | 0.336 | 1.200 | 0.266 | 4.773 | 0 |
| rico | 0.900 | recentred_enbpi_static | 0.791 | 0.109 | 1.018 | 0.225 | 3.231 | 0 |
| rico | 0.900 | recentred_enbpi_updated | 0.824 | 0.076 | 1.245 | 0.274 | 2.787 | 0 |
| rico | 0.950 | cqr | 0.772 | 0.178 | 2.498 | 0.552 | 11.260 | 2558 |
| rico | 0.950 | dscp | 0.897 | 0.053 | 1.790 | 0.402 | 3.373 | 0 |
| rico | 0.950 | quantile_uncalibrated | 0.630 | 0.320 | 1.809 | 0.400 | 12.682 | 0 |
| rico | 0.950 | recentred_enbpi_static | 0.872 | 0.078 | 1.427 | 0.315 | 4.318 | 0 |
| rico | 0.950 | recentred_enbpi_updated | 0.904 | 0.046 | 1.708 | 0.376 | 3.322 | 0 |

## D. Alert performance

`far` is the point-level False Alarm Rate FP/(FP+TN); `false_alert_events_per_day` counts contiguous alert clusters per day. They are different quantities.

| Dataset | Role | Rule | Precision | Recall | F1 | FAR | False/day | Mean delay | Median delay | Events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | calibration_selection | 1-of-1 | 0.065 | 0.929 | 0.121 | 0.063 | 0.967 | 35.385 | 0.000 | 42 |
| bdg2 | clean_test_no_events | 1-of-1 | 0.000 | n/a | n/a | 0.057 | 1.002 | n/a | n/a | 0 |
| bdg2 | post_hoc_sensitivity | 1-of-1 | 0.025 | 0.881 | 0.049 | 0.057 | 0.986 | 30.811 | 0.000 | 42 |
| pleia | calibration_selection | 4-of-7 | 0.583 | 0.833 | 0.686 | 0.035 | 0.890 | 35.714 | 30.000 | 42 |
| pleia | clean_test_no_events | 4-of-7 | 0.000 | n/a | n/a | 0.014 | 0.413 | n/a | n/a | 0 |
| pleia | post_hoc_sensitivity | 4-of-7 | 0.576 | 0.810 | 0.673 | 0.013 | 0.356 | 38.824 | 30.000 | 42 |
| pleia_energy | calibration_selection | 2-of-3 | 0.542 | 0.619 | 0.578 | 0.015 | 0.784 | 55.000 | 15.000 | 42 |
| pleia_energy | clean_test_no_events | 2-of-3 | 0.000 | n/a | n/a | 0.009 | 0.584 | n/a | n/a | 0 |
| pleia_energy | post_hoc_sensitivity | 2-of-3 | 0.438 | 0.762 | 0.557 | 0.010 | 0.584 | 32.812 | 10.000 | 42 |
| rico | calibration_selection | 2-of-3 | 0.771 | 0.771 | 0.771 | 0.017 | 3.183 | 2.037 | 1.000 | 35 |
| rico | clean_test_no_events | 2-of-3 | 0.000 | n/a | n/a | 0.221 | 12.566 | n/a | n/a | 0 |
| rico | post_hoc_sensitivity | 2-of-3 | 0.312 | 0.875 | 0.461 | 0.208 | 11.946 | 2.286 | 1.000 | 40 |

## E. Robustness

`empirical_coverage` is measured against what the monitor observes; `..._vs_clean_truth` against the uncorrupted signal. In closed loop the two diverge, which is the point.

| Dataset | Mode | Scenario | Severity | Cov (obs) | Cov (clean) | MAE (obs) | MAE (clean) | False/day |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | calibration_contamination | calib_contam_10pct | 10% | 1.000 | n/a | n/a | n/a | n/a |
| bdg2 | calibration_contamination | calib_contam_1pct | 1% | 0.954 | n/a | n/a | n/a | n/a |
| bdg2 | calibration_contamination | calib_contam_5pct | 5% | 0.999 | n/a | n/a | n/a | n/a |
| bdg2 | closed_loop | bias_0.5sd | 0.5 sigma | 0.963 | 0.165 | 27.060 | 123.454 | 0.610 |
| bdg2 | closed_loop | bias_1.0sd | 1.0 sigma | 0.939 | 0.063 | 27.790 | 241.444 | 0.825 |
| bdg2 | closed_loop | bias_2.0sd | 2.0 sigma | 0.888 | 0.053 | 44.166 | 472.006 | 0.871 |
| bdg2 | closed_loop | block_missing_10pct | 10% | 0.943 | 0.941 | 20.221 | 20.323 | 1.004 |
| bdg2 | closed_loop | block_missing_5pct | 5% | 0.942 | 0.942 | 20.127 | 20.164 | 1.009 |
| bdg2 | closed_loop | clean | none | 0.943 | 0.943 | 20.011 | 20.011 | 1.002 |
| bdg2 | closed_loop | drift_1.0sd | 1.0 sigma terminal | 0.966 | 0.257 | 24.277 | 123.476 | 0.587 |
| bdg2 | closed_loop | drift_2.0sd | 2.0 sigma terminal | 0.948 | 0.163 | 28.484 | 238.790 | 0.764 |
| bdg2 | closed_loop | dropout_5pct | 5% of region | 0.940 | 0.917 | 19.606 | 22.918 | 0.985 |
| bdg2 | closed_loop | level_shift_1.0sd | 1.0 sigma | 0.947 | 0.490 | 23.539 | 131.447 | 0.869 |
| bdg2 | closed_loop | level_shift_2.0sd | 2.0 sigma | 0.929 | 0.484 | 29.165 | 247.574 | 0.967 |
| bdg2 | closed_loop | random_missing_10pct | 10% | 0.944 | 0.941 | 19.656 | 19.916 | 0.975 |
| bdg2 | closed_loop | random_missing_20pct | 20% | 0.948 | 0.942 | 19.054 | 19.767 | 0.888 |
| bdg2 | closed_loop | random_missing_5pct | 5% | 0.943 | 0.942 | 19.862 | 19.990 | 0.982 |
| bdg2 | closed_loop | stuck_5pct | 5% of region | 0.945 | 0.921 | 19.888 | 24.311 | 0.943 |
| bdg2 | legacy_fixed_intervals | bias_0.5sd | 0.5 sigma | 0.135 | 0.943 | 123.404 | 20.011 | 1.253 |
| bdg2 | legacy_fixed_intervals | bias_1.0sd | 1.0 sigma | 0.022 | 0.943 | 244.910 | 20.011 | 0.210 |
| bdg2 | legacy_fixed_intervals | bias_2.0sd | 2.0 sigma | 0.001 | 0.943 | 489.522 | 20.011 | 0.011 |
| bdg2 | legacy_fixed_intervals | block_missing_10pct | 10% | 0.922 | 0.943 | 25.601 | 20.011 | 1.110 |
| bdg2 | legacy_fixed_intervals | block_missing_5pct | 5% | 0.933 | 0.943 | 22.807 | 20.011 | 1.060 |
| bdg2 | legacy_fixed_intervals | clean | none | 0.943 | 0.943 | 20.011 | 20.011 | 1.002 |
| bdg2 | legacy_fixed_intervals | drift_1.0sd | 1.0 sigma terminal | 0.281 | 0.943 | 125.489 | 20.011 | 1.409 |
| bdg2 | legacy_fixed_intervals | drift_2.0sd | 2.0 sigma terminal | 0.146 | 0.943 | 246.020 | 20.011 | 0.810 |
| bdg2 | legacy_fixed_intervals | dropout_5pct | 5% of region | 0.919 | 0.943 | 24.232 | 20.011 | 0.982 |
| bdg2 | legacy_fixed_intervals | level_shift_1.0sd | 1.0 sigma | 0.469 | 0.943 | 136.740 | 20.011 | 0.734 |
| bdg2 | legacy_fixed_intervals | level_shift_2.0sd | 2.0 sigma | 0.463 | 0.943 | 259.057 | 20.011 | 0.723 |
| bdg2 | legacy_fixed_intervals | random_missing_10pct | 10% | 0.861 | 0.943 | 44.522 | 20.011 | 2.663 |
| bdg2 | legacy_fixed_intervals | random_missing_20pct | 20% | 0.781 | 0.943 | 67.410 | 20.011 | 3.947 |
| bdg2 | legacy_fixed_intervals | random_missing_5pct | 5% | 0.902 | 0.943 | 31.904 | 20.011 | 1.869 |
| bdg2 | legacy_fixed_intervals | stuck_5pct | 5% of region | 0.901 | 0.943 | 30.633 | 20.011 | 0.938 |
| pleia | calibration_contamination | calib_contam_10pct | 10% | 1.000 | n/a | n/a | n/a | n/a |
| pleia | calibration_contamination | calib_contam_1pct | 1% | 0.945 | n/a | n/a | n/a | n/a |
| pleia | calibration_contamination | calib_contam_5pct | 5% | 0.997 | n/a | n/a | n/a | n/a |
| pleia | closed_loop | bias_0.5sd | 0.5 sigma | 0.887 | 0.024 | 0.349 | 2.104 | 1.311 |
| pleia | closed_loop | bias_1.0sd | 1.0 sigma | 0.832 | 0.003 | 0.383 | 4.284 | 2.094 |
| pleia | closed_loop | bias_2.0sd | 2.0 sigma | 0.258 | 0.001 | 1.655 | 7.361 | 2.265 |
| pleia | closed_loop | block_missing_10pct | 10% | 0.940 | 0.939 | 0.311 | 0.315 | 0.374 |
| pleia | closed_loop | block_missing_5pct | 5% | 0.938 | 0.937 | 0.314 | 0.315 | 0.436 |
| pleia | closed_loop | clean | none | 0.937 | 0.937 | 0.314 | 0.314 | 0.413 |
| pleia | closed_loop | drift_1.0sd | 1.0 sigma terminal | 0.885 | 0.214 | 0.352 | 2.137 | 1.254 |
| pleia | closed_loop | drift_2.0sd | 2.0 sigma terminal | 0.746 | 0.113 | 0.412 | 4.260 | 2.365 |
| pleia | closed_loop | dropout_5pct | 5% of region | 0.946 | 0.904 | 0.297 | 0.432 | 0.342 |
| pleia | closed_loop | level_shift_1.0sd | 1.0 sigma | 0.876 | 0.460 | 0.354 | 2.318 | 1.282 |
| pleia | closed_loop | level_shift_2.0sd | 2.0 sigma | 0.615 | 0.458 | 0.755 | 4.110 | 1.752 |
| pleia | closed_loop | random_missing_10pct | 10% | 0.939 | 0.936 | 0.307 | 0.312 | 0.356 |
| pleia | closed_loop | random_missing_20pct | 20% | 0.940 | 0.935 | 0.300 | 0.309 | 0.402 |
| pleia | closed_loop | random_missing_5pct | 5% | 0.937 | 0.937 | 0.311 | 0.313 | 0.370 |
| pleia | closed_loop | stuck_5pct | 5% of region | 0.938 | 0.920 | 0.312 | 0.347 | 0.399 |
| pleia | legacy_fixed_intervals | bias_0.5sd | 0.5 sigma | 0.023 | 0.937 | 2.274 | 0.314 | 0.328 |
| pleia | legacy_fixed_intervals | bias_1.0sd | 1.0 sigma | 0.003 | 0.937 | 4.504 | 0.314 | 0.071 |
| pleia | legacy_fixed_intervals | bias_2.0sd | 2.0 sigma | 0.000 | 0.937 | 8.974 | 0.314 | 0.014 |
| pleia | legacy_fixed_intervals | block_missing_10pct | 10% | 0.938 | 0.937 | 0.313 | 0.314 | 0.370 |
| pleia | legacy_fixed_intervals | block_missing_5pct | 5% | 0.938 | 0.937 | 0.313 | 0.314 | 0.399 |
| pleia | legacy_fixed_intervals | clean | none | 0.937 | 0.937 | 0.314 | 0.314 | 0.413 |
| pleia | legacy_fixed_intervals | drift_1.0sd | 1.0 sigma terminal | 0.206 | 0.937 | 2.291 | 0.314 | 1.539 |
| pleia | legacy_fixed_intervals | drift_2.0sd | 2.0 sigma terminal | 0.096 | 0.937 | 4.512 | 0.314 | 0.427 |
| pleia | legacy_fixed_intervals | dropout_5pct | 5% of region | 0.908 | 0.937 | 0.442 | 0.314 | 0.399 |
| pleia | legacy_fixed_intervals | level_shift_1.0sd | 1.0 sigma | 0.458 | 0.937 | 2.428 | 0.314 | 0.370 |
| pleia | legacy_fixed_intervals | level_shift_2.0sd | 2.0 sigma | 0.457 | 0.937 | 4.663 | 0.314 | 0.342 |
| pleia | legacy_fixed_intervals | random_missing_10pct | 10% | 0.939 | 0.937 | 0.311 | 0.314 | 0.385 |
| pleia | legacy_fixed_intervals | random_missing_20pct | 20% | 0.941 | 0.937 | 0.305 | 0.314 | 0.413 |
| pleia | legacy_fixed_intervals | random_missing_5pct | 5% | 0.938 | 0.937 | 0.312 | 0.314 | 0.385 |
| pleia | legacy_fixed_intervals | stuck_5pct | 5% of region | 0.898 | 0.937 | 0.363 | 0.314 | 0.456 |
| pleia_energy | calibration_contamination | calib_contam_10pct | 10% | 0.997 | n/a | n/a | n/a | n/a |
| pleia_energy | calibration_contamination | calib_contam_1pct | 1% | 0.984 | n/a | n/a | n/a | n/a |
| pleia_energy | calibration_contamination | calib_contam_5pct | 5% | 0.995 | n/a | n/a | n/a | n/a |
| pleia_energy | closed_loop | bias_0.5sd | 0.5 sigma | 0.977 | 0.456 | 0.096 | 0.225 | 0.556 |
| pleia_energy | closed_loop | bias_1.0sd | 1.0 sigma | 0.978 | 0.185 | 0.100 | 0.354 | 0.356 |
| pleia_energy | closed_loop | bias_2.0sd | 2.0 sigma | 0.976 | 0.180 | 0.134 | 0.622 | 0.356 |
| pleia_energy | closed_loop | block_missing_10pct | 10% | 0.972 | 0.971 | 0.101 | 0.102 | 0.631 |
| pleia_energy | closed_loop | block_missing_5pct | 5% | 0.972 | 0.972 | 0.098 | 0.099 | 0.637 |
| pleia_energy | closed_loop | clean | none | 0.973 | 0.973 | 0.093 | 0.093 | 0.584 |
| pleia_energy | closed_loop | drift_1.0sd | 1.0 sigma terminal | 0.976 | 0.607 | 0.100 | 0.209 | 0.598 |
| pleia_energy | closed_loop | drift_2.0sd | 2.0 sigma terminal | 0.979 | 0.403 | 0.106 | 0.341 | 0.442 |
| pleia_energy | closed_loop | dropout_5pct | 5% of region | 0.973 | 0.973 | 0.092 | 0.093 | 0.570 |
| pleia_energy | closed_loop | level_shift_1.0sd | 1.0 sigma | 0.976 | 0.664 | 0.099 | 0.198 | 0.342 |
| pleia_energy | closed_loop | level_shift_2.0sd | 2.0 sigma | 0.972 | 0.663 | 0.120 | 0.316 | 0.399 |
| pleia_energy | closed_loop | random_missing_10pct | 10% | 0.974 | 0.972 | 0.104 | 0.094 | 0.698 |
| pleia_energy | closed_loop | random_missing_20pct | 20% | 0.974 | 0.970 | 0.104 | 0.095 | 0.761 |
| pleia_energy | closed_loop | random_missing_5pct | 5% | 0.973 | 0.972 | 0.105 | 0.094 | 0.670 |
| pleia_energy | closed_loop | stuck_5pct | 5% of region | 0.974 | 0.966 | 0.090 | 0.095 | 0.541 |
| pleia_energy | legacy_fixed_intervals | bias_0.5sd | 0.5 sigma | 0.452 | 0.973 | 0.212 | 0.093 | 3.619 |
| pleia_energy | legacy_fixed_intervals | bias_1.0sd | 1.0 sigma | 0.264 | 0.973 | 0.375 | 0.093 | 3.861 |
| pleia_energy | legacy_fixed_intervals | bias_2.0sd | 2.0 sigma | 0.075 | 0.973 | 0.714 | 0.093 | 2.066 |
| pleia_energy | legacy_fixed_intervals | block_missing_10pct | 10% | 0.973 | 0.973 | 0.095 | 0.093 | 0.570 |
| pleia_energy | legacy_fixed_intervals | block_missing_5pct | 5% | 0.973 | 0.973 | 0.094 | 0.093 | 0.570 |
| pleia_energy | legacy_fixed_intervals | clean | none | 0.973 | 0.973 | 0.093 | 0.093 | 0.584 |
| pleia_energy | legacy_fixed_intervals | drift_1.0sd | 1.0 sigma terminal | 0.639 | 0.973 | 0.210 | 0.093 | 3.775 |
| pleia_energy | legacy_fixed_intervals | drift_2.0sd | 2.0 sigma terminal | 0.347 | 0.973 | 0.375 | 0.093 | 4.274 |
| pleia_energy | legacy_fixed_intervals | dropout_5pct | 5% of region | 0.973 | 0.973 | 0.093 | 0.093 | 0.570 |
| pleia_energy | legacy_fixed_intervals | level_shift_1.0sd | 1.0 sigma | 0.705 | 0.973 | 0.216 | 0.093 | 3.063 |
| pleia_energy | legacy_fixed_intervals | level_shift_2.0sd | 2.0 sigma | 0.562 | 0.973 | 0.384 | 0.093 | 1.895 |
| pleia_energy | legacy_fixed_intervals | random_missing_10pct | 10% | 0.974 | 0.973 | 0.104 | 0.093 | 0.655 |
| pleia_energy | legacy_fixed_intervals | random_missing_20pct | 20% | 0.976 | 0.973 | 0.103 | 0.093 | 0.641 |
| pleia_energy | legacy_fixed_intervals | random_missing_5pct | 5% | 0.974 | 0.973 | 0.105 | 0.093 | 0.627 |
| pleia_energy | legacy_fixed_intervals | stuck_5pct | 5% of region | 0.972 | 0.973 | 0.093 | 0.093 | 0.598 |
| rico | calibration_contamination | calib_contam_10pct | 10% | 1.000 | n/a | n/a | n/a | n/a |
| rico | calibration_contamination | calib_contam_1pct | 1% | 0.921 | n/a | n/a | n/a | n/a |
| rico | calibration_contamination | calib_contam_5pct | 5% | 1.000 | n/a | n/a | n/a | n/a |
| rico | closed_loop | bias_0.5sd | 0.5 sigma | 0.799 | 0.005 | 0.120 | 2.791 | 17.065 |
| rico | closed_loop | bias_1.0sd | 1.0 sigma | 0.600 | 0.000 | 0.247 | 5.440 | 32.734 |
| rico | closed_loop | bias_2.0sd | 2.0 sigma | 0.502 | 0.000 | 0.833 | 10.512 | 19.392 |
| rico | closed_loop | block_missing_10pct | 10% | 0.773 | 0.773 | 0.105 | 0.105 | 12.203 |
| rico | closed_loop | block_missing_5pct | 5% | 0.775 | 0.775 | 0.103 | 0.103 | 11.888 |
| rico | closed_loop | clean | none | 0.781 | 0.781 | 0.111 | 0.111 | 12.566 |
| rico | closed_loop | drift_1.0sd | 1.0 sigma terminal | 0.674 | 0.079 | 0.209 | 2.877 | 37.544 |
| rico | closed_loop | drift_2.0sd | 2.0 sigma terminal | 0.449 | 0.021 | 0.616 | 5.504 | 36.768 |
| rico | closed_loop | dropout_5pct | 5% of region | 0.779 | 0.776 | 0.119 | 0.120 | 13.497 |
| rico | closed_loop | level_shift_1.0sd | 1.0 sigma | 0.669 | 0.385 | 0.358 | 2.853 | 27.460 |
| rico | closed_loop | level_shift_2.0sd | 2.0 sigma | 0.624 | 0.385 | 0.889 | 5.388 | 20.168 |
| rico | closed_loop | random_missing_10pct | 10% | 0.781 | 0.781 | 0.111 | 0.111 | 12.778 |
| rico | closed_loop | random_missing_20pct | 20% | 0.781 | 0.781 | 0.111 | 0.112 | 13.236 |
| rico | closed_loop | random_missing_5pct | 5% | 0.780 | 0.780 | 0.111 | 0.111 | 12.778 |
| rico | closed_loop | stuck_5pct | 5% of region | 0.780 | 0.778 | 0.114 | 0.115 | 13.187 |
| rico | legacy_fixed_intervals | bias_0.5sd | 0.5 sigma | 0.049 | 0.781 | 2.858 | 0.111 | 3.878 |
| rico | legacy_fixed_intervals | bias_1.0sd | 1.0 sigma | 0.000 | 0.781 | 5.693 | 0.111 | 0.155 |
| rico | legacy_fixed_intervals | bias_2.0sd | 2.0 sigma | 0.000 | 0.781 | 11.364 | 0.111 | 0.155 |
| rico | legacy_fixed_intervals | block_missing_10pct | 10% | 0.784 | 0.781 | 0.112 | 0.111 | 15.048 |
| rico | legacy_fixed_intervals | block_missing_5pct | 5% | 0.783 | 0.781 | 0.112 | 0.111 | 13.652 |
| rico | legacy_fixed_intervals | clean | none | 0.781 | 0.781 | 0.111 | 0.111 | 12.566 |
| rico | legacy_fixed_intervals | drift_1.0sd | 1.0 sigma terminal | 0.194 | 0.781 | 2.860 | 0.111 | 2.637 |
| rico | legacy_fixed_intervals | drift_2.0sd | 2.0 sigma terminal | 0.131 | 0.781 | 5.694 | 0.111 | 1.707 |
| rico | legacy_fixed_intervals | dropout_5pct | 5% of region | 0.760 | 0.781 | 0.469 | 0.111 | 11.946 |
| rico | legacy_fixed_intervals | level_shift_1.0sd | 1.0 sigma | 0.425 | 0.781 | 2.896 | 0.111 | 3.878 |
| rico | legacy_fixed_intervals | level_shift_2.0sd | 2.0 sigma | 0.425 | 0.781 | 5.731 | 0.111 | 3.878 |
| rico | legacy_fixed_intervals | random_missing_10pct | 10% | 0.781 | 0.781 | 0.111 | 0.111 | 12.877 |
| rico | legacy_fixed_intervals | random_missing_20pct | 20% | 0.781 | 0.781 | 0.111 | 0.111 | 12.566 |
| rico | legacy_fixed_intervals | random_missing_5pct | 5% | 0.781 | 0.781 | 0.111 | 0.111 | 12.411 |
| rico | legacy_fixed_intervals | stuck_5pct | 5% of region | 0.738 | 0.781 | 0.226 | 0.111 | 12.721 |

## F. Recalibration

| Dataset | Strategy | Coverage | Cov. dev. | Width | Winkler | Updates | Every | Window | Delay (steps) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | periodic | 0.859 | 0.091 | 127.375 | 194.025 | 1460 | 24 | n/a | 1 |
| bdg2 | rolling | 0.859 | 0.091 | 127.375 | 194.025 | 1460 | 24 | n/a | 1 |
| bdg2 | static | 0.843 | 0.107 | 126.210 | 202.331 | 0 | 24 | n/a | 1 |
| pleia | periodic | 0.939 | 0.011 | 1.784 | 2.877 | 422 | 24 | 1000.000 | 1 |
| pleia | rolling | 0.948 | 0.002 | 1.891 | 2.869 | 422 | 24 | 1000.000 | 1 |
| pleia | static | 0.932 | 0.018 | 1.707 | 2.894 | 0 | 24 | 1000.000 | 1 |
| pleia_energy | periodic | 0.972 | 0.022 | 0.847 | 2.060 | 71 | 144 | 1000.000 | 1 |
| pleia_energy | rolling | 0.929 | 0.021 | 0.458 | 1.866 | 71 | 144 | 1000.000 | 1 |
| pleia_energy | static | 0.981 | 0.031 | 0.941 | 2.099 | 0 | 144 | 1000.000 | 1 |
| rico | periodic | 0.926 | 0.024 | 0.571 | 0.855 | 619 | 15 | 500.000 | 5 |
| rico | rolling | 0.912 | 0.038 | 0.529 | 0.830 | 619 | 15 | 500.000 | 5 |
| rico | static | 0.905 | 0.045 | 0.536 | 0.925 | 0 | 15 | 500.000 | 5 |

## G. Statistical comparison

48 Diebold-Mariano comparisons, 36 significant at 5% after Holm adjustment. A negative statistic favours model A.

| Dataset | h | A | B | DM | p | Holm p | Sig. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | xgboost | persistence | 16.3233 | 0.0000 | 0.0000 | yes |
| bdg2 | 1 | attention_lstm | persistence | 8.2872 | 0.0000 | 0.0000 | yes |
| bdg2 | 1 | xgboost | attention_lstm | 11.5309 | 0.0000 | 0.0000 | yes |
| bdg2 | 1 | seasonal_naive | persistence | 49.3276 | 0.0000 | 0.0000 | yes |
| bdg2 | 3 | xgboost | persistence | -21.3268 | 0.0000 | 0.0000 | yes |
| bdg2 | 3 | attention_lstm | persistence | -16.2903 | 0.0000 | 0.0000 | yes |
| bdg2 | 3 | xgboost | attention_lstm | -6.8255 | 0.0000 | 0.0000 | yes |
| bdg2 | 3 | seasonal_naive | persistence | 0.9063 | 0.3648 | 0.3648 | no |
| bdg2 | 6 | xgboost | persistence | -37.5717 | 0.0000 | 0.0000 | yes |
| bdg2 | 6 | attention_lstm | persistence | -27.1772 | 0.0000 | 0.0000 | yes |
| bdg2 | 6 | xgboost | attention_lstm | -16.9909 | 0.0000 | 0.0000 | yes |
| bdg2 | 6 | seasonal_naive | persistence | -27.2287 | 0.0000 | 0.0000 | yes |
| pleia | 1 | xgboost | persistence | 46.7874 | 0.0000 | 0.0000 | yes |
| pleia | 1 | attention_lstm | persistence | 84.2269 | 0.0000 | 0.0000 | yes |
| pleia | 1 | xgboost | attention_lstm | -68.8557 | 0.0000 | 0.0000 | yes |
| pleia | 1 | seasonal_naive | persistence | 79.2502 | 0.0000 | 0.0000 | yes |
| pleia | 3 | xgboost | persistence | 28.5067 | 0.0000 | 0.0000 | yes |
| pleia | 3 | attention_lstm | persistence | 39.0416 | 0.0000 | 0.0000 | yes |
| pleia | 3 | xgboost | attention_lstm | -29.2653 | 0.0000 | 0.0000 | yes |
| pleia | 3 | seasonal_naive | persistence | 40.4433 | 0.0000 | 0.0000 | yes |
| pleia | 6 | xgboost | persistence | 13.8221 | 0.0000 | 0.0000 | yes |
| pleia | 6 | attention_lstm | persistence | 26.6103 | 0.0000 | 0.0000 | yes |
| pleia | 6 | xgboost | attention_lstm | -20.9092 | 0.0000 | 0.0000 | yes |
| pleia | 6 | seasonal_naive | persistence | 24.5574 | 0.0000 | 0.0000 | yes |
| pleia_energy | 1 | xgboost | persistence | -1.8183 | 0.0691 | 0.2072 | no |
| pleia_energy | 1 | attention_lstm | persistence | -1.6349 | 0.1021 | 0.2072 | no |
| pleia_energy | 1 | xgboost | attention_lstm | -7.2611 | 0.0000 | 0.0000 | yes |
| pleia_energy | 1 | seasonal_naive | persistence | 1.6446 | 0.1001 | 0.2072 | no |
| pleia_energy | 3 | xgboost | persistence | -1.0814 | 0.2796 | 0.5591 | no |
| pleia_energy | 3 | attention_lstm | persistence | -1.0255 | 0.3051 | 0.5591 | no |
| pleia_energy | 3 | xgboost | attention_lstm | -1.5698 | 0.1165 | 0.3495 | no |
| pleia_energy | 3 | seasonal_naive | persistence | 1.9757 | 0.0482 | 0.1929 | no |
| pleia_energy | 6 | xgboost | persistence | -1.2330 | 0.2176 | 0.4352 | no |
| pleia_energy | 6 | attention_lstm | persistence | -1.1086 | 0.2676 | 0.4352 | no |
| pleia_energy | 6 | xgboost | attention_lstm | -2.6826 | 0.0073 | 0.0293 | yes |
| pleia_energy | 6 | seasonal_naive | persistence | 1.6446 | 0.1001 | 0.3002 | no |
| rico | 5 | xgboost | persistence | -7.3847 | 0.0000 | 0.0000 | yes |
| rico | 5 | attention_lstm | persistence | 39.6610 | 0.0000 | 0.0000 | yes |
| rico | 5 | xgboost | attention_lstm | -46.3507 | 0.0000 | 0.0000 | yes |
| rico | 15 | xgboost | persistence | -7.0515 | 0.0000 | 0.0000 | yes |
| rico | 15 | attention_lstm | persistence | 7.6544 | 0.0000 | 0.0000 | yes |
| rico | 15 | xgboost | attention_lstm | -14.9637 | 0.0000 | 0.0000 | yes |
| rico | 30 | xgboost | persistence | -6.8749 | 0.0000 | 0.0000 | yes |
| rico | 30 | attention_lstm | persistence | 2.4484 | 0.0144 | 0.0144 | yes |
| rico | 30 | xgboost | attention_lstm | -10.6538 | 0.0000 | 0.0000 | yes |
| rico | 60 | xgboost | persistence | -5.9851 | 0.0000 | 0.0000 | yes |
| rico | 60 | attention_lstm | persistence | -1.9254 | 0.0542 | 0.0542 | no |
| rico | 60 | xgboost | attention_lstm | -4.1780 | 0.0000 | 0.0001 | yes |

| Test | Blocks | Methods | Statistic | p | Blocks dropped |
| --- | --- | --- | --- | --- | --- |
| friedman | 9 | 4 | 14.0667 | 0.0028 | 4 |

| A | B | Rank A | Rank B | Median diff | Holm p | Sig. |
| --- | --- | --- | --- | --- | --- | --- |
| attention_lstm | persistence | 2.4444 | 2.2222 | -0.0248 | 1.0000 | no |
| attention_lstm | seasonal_naive | 2.4444 | 3.7778 | -0.4208 | 0.3711 | no |
| attention_lstm | xgboost | 2.4444 | 1.5556 | 0.2810 | 0.3711 | no |
| persistence | seasonal_naive | 2.2222 | 3.7778 | -0.5333 | 0.3867 | no |
| persistence | xgboost | 2.2222 | 1.5556 | 0.0262 | 1.0000 | no |
| seasonal_naive | xgboost | 3.7778 | 1.5556 | 0.9454 | 0.0234 | yes |

Effect sizes (practical significance):

| Dataset | h | A | B | MAE impr % | Median diff | CI low | CI high | Win rate A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | xgboost | persistence | -12.856 | 2.262 | 1.890 | 2.970 | 0.351 |
| bdg2 | 1 | attention_lstm | persistence | -4.713 | 2.859 | 0.490 | 1.340 | 0.361 |
| bdg2 | 1 | xgboost | attention_lstm | -7.729 | -0.749 | 0.948 | 2.155 | 0.537 |
| bdg2 | 1 | seasonal_naive | persistence | -93.136 | 0.400 | 15.463 | 19.716 | 0.306 |
| bdg2 | 3 | xgboost | persistence | 21.814 | 1.071 | -9.158 | -6.568 | 0.436 |
| bdg2 | 3 | attention_lstm | persistence | 16.088 | 1.480 | -6.767 | -4.800 | 0.413 |
| bdg2 | 3 | xgboost | attention_lstm | 6.851 | -0.358 | -3.354 | -0.844 | 0.517 |
| bdg2 | 3 | seasonal_naive | persistence | -1.482 | 0.000 | -1.218 | 2.477 | 0.418 |
| bdg2 | 6 | xgboost | persistence | 47.995 | -3.514 | -31.863 | -26.763 | 0.545 |
| bdg2 | 6 | attention_lstm | persistence | 33.325 | 0.057 | -22.594 | -18.193 | 0.499 |
| bdg2 | 6 | xgboost | attention_lstm | 22.027 | -3.663 | -10.748 | -7.184 | 0.611 |
| bdg2 | 6 | seasonal_naive | persistence | 40.026 | -2.110 | -26.750 | -21.759 | 0.539 |
| pleia | 1 | xgboost | persistence | -69.192 | 0.093 | 0.129 | 0.152 | 0.281 |
| pleia | 1 | attention_lstm | persistence | -296.276 | 0.406 | 0.552 | 0.651 | 0.162 |
| pleia | 1 | xgboost | attention_lstm | 57.304 | -0.281 | -0.509 | -0.415 | 0.764 |
| pleia | 1 | seasonal_naive | persistence | -628.922 | 0.700 | 1.147 | 1.406 | 0.088 |
| pleia | 3 | xgboost | persistence | -41.745 | 0.136 | 0.139 | 0.173 | 0.326 |
| pleia | 3 | attention_lstm | persistence | -116.651 | 0.312 | 0.394 | 0.484 | 0.260 |
| pleia | 3 | xgboost | attention_lstm | 34.575 | -0.160 | -0.326 | -0.245 | 0.660 |
| pleia | 3 | seasonal_naive | persistence | -293.785 | 0.500 | 0.971 | 1.234 | 0.167 |
| pleia | 6 | xgboost | persistence | -27.043 | 0.126 | 0.117 | 0.174 | 0.383 |
| pleia | 6 | attention_lstm | persistence | -93.622 | 0.414 | 0.459 | 0.567 | 0.263 |
| pleia | 6 | xgboost | attention_lstm | 34.386 | -0.257 | -0.418 | -0.315 | 0.671 |
| pleia | 6 | seasonal_naive | persistence | -170.731 | 0.400 | 0.798 | 1.065 | 0.237 |
| pleia_energy | 1 | xgboost | persistence | 31.029 | -0.003 | -0.093 | -0.016 | 0.557 |
| pleia_energy | 1 | attention_lstm | persistence | 28.035 | -0.001 | -0.089 | -0.012 | 0.517 |
| pleia_energy | 1 | xgboost | attention_lstm | 4.160 | -0.003 | -0.007 | -0.002 | 0.559 |
| pleia_energy | 1 | seasonal_naive | persistence | -39.848 | 0.008 | -0.005 | 0.125 | 0.344 |
| pleia_energy | 3 | xgboost | persistence | 20.075 | -0.001 | -0.079 | 0.003 | 0.516 |
| pleia_energy | 3 | attention_lstm | persistence | 18.990 | 0.003 | -0.075 | 0.002 | 0.448 |
| pleia_energy | 3 | xgboost | attention_lstm | 1.339 | -0.003 | -0.005 | 0.002 | 0.566 |
| pleia_energy | 3 | seasonal_naive | persistence | -52.069 | 0.008 | 0.005 | 0.138 | 0.308 |
| pleia_energy | 6 | xgboost | persistence | 21.117 | -0.000 | -0.083 | -0.002 | 0.504 |
| pleia_energy | 6 | attention_lstm | persistence | 18.827 | 0.007 | -0.078 | 0.001 | 0.400 |
| pleia_energy | 6 | xgboost | attention_lstm | 2.821 | -0.006 | -0.007 | 0.000 | 0.602 |
| pleia_energy | 6 | seasonal_naive | persistence | -39.970 | 0.008 | -0.008 | 0.129 | 0.338 |
| rico | 5 | xgboost | persistence | 23.662 | 0.007 | -0.043 | -0.014 | 0.468 |
| rico | 5 | attention_lstm | persistence | -282.985 | 0.285 | 0.294 | 0.364 | 0.123 |
| rico | 5 | xgboost | attention_lstm | 79.147 | -0.296 | -0.385 | -0.320 | 0.905 |
| rico | 15 | xgboost | persistence | 37.107 | -0.030 | -0.173 | -0.087 | 0.558 |
| rico | 15 | attention_lstm | persistence | -57.137 | 0.167 | 0.129 | 0.250 | 0.343 |
| rico | 15 | xgboost | attention_lstm | 58.058 | -0.205 | -0.352 | -0.254 | 0.738 |
| rico | 30 | xgboost | persistence | 46.320 | -0.124 | -0.379 | -0.234 | 0.636 |
| rico | 30 | attention_lstm | persistence | -20.905 | 0.199 | 0.038 | 0.218 | 0.399 |
| rico | 30 | xgboost | attention_lstm | 53.662 | -0.238 | -0.467 | -0.343 | 0.722 |
| rico | 60 | xgboost | persistence | 48.765 | -0.275 | -0.718 | -0.454 | 0.687 |
| rico | 60 | attention_lstm | persistence | 18.905 | -0.021 | -0.368 | -0.080 | 0.514 |
| rico | 60 | xgboost | attention_lstm | 34.290 | -0.229 | -0.402 | -0.228 | 0.626 |

## H. Cross-dataset ranking

Ranks are computed within each (dataset, target, horizon) block, so they are comparable where raw errors are not. Rank 1 is the lowest error.

| Dataset | Model | Mean MAE rank | Mean RMSE rank | Mean impr % | Blocks |
| --- | --- | --- | --- | --- | --- |
| bdg2 | xgboost | 1.667 | 1.667 | 18.984 | 3 |
| bdg2 | attention_lstm | 2.333 | 1.667 | 14.679 | 3 |
| bdg2 | persistence | 2.667 | 3.000 | 0.000 | 3 |
| bdg2 | seasonal_naive | 3.333 | 3.667 | -18.197 | 3 |
| pleia | persistence | 1.000 | 1.000 | 0.000 | 3 |
| pleia | xgboost | 2.000 | 2.000 | -45.994 | 3 |
| pleia | attention_lstm | 3.000 | 3.000 | -168.850 | 3 |
| pleia | seasonal_naive | 4.000 | 4.000 | -364.479 | 3 |
| pleia_energy | xgboost | 1.000 | 1.000 | 24.074 | 3 |
| pleia_energy | attention_lstm | 2.000 | 2.000 | 21.951 | 3 |
| pleia_energy | persistence | 3.000 | 3.000 | 0.000 | 3 |
| pleia_energy | seasonal_naive | 4.000 | 4.000 | -43.962 | 3 |
| rico | xgboost | 1.000 | 1.000 | 38.964 | 4 |
| rico | persistence | 2.250 | 2.500 | 0.000 | 4 |
| rico | attention_lstm | 2.750 | 2.500 | -75.794 | 4 |

## I. Key limitations

- No run-time limitation was recorded.

See `full_study_limitations.md` for the complete list, including the standing methodological caveats.

## J. Final claims supported by the evidence

1. **Conformal calibration is measurably necessary.** The uncalibrated quantile baseline undercovers on all 4 datasets, with mean coverage deviation 0.0705–0.3196 at nominal 0.95. (`combined/interval_metrics.csv`)
2. **No conformal method transfers across datasets.** The best-calibrated arm differs by dataset (bdg2: recentred_enbpi_updated, pleia: cqr, pleia_energy: recentred_enbpi_updated, rico: recentred_enbpi_updated), so the framework must select it per target rather than fix it. (`combined/interval_metrics.csv`)
3. **RICO is not solved by any arm evaluated here.** The best coverage in any single (method, horizon) cell is 0.9293 and the best arm averaged over horizons reaches 0.9036, both against a nominal 0.95. That is material undercoverage, not calibration. (`combined/interval_metrics.csv`, `report/rico_quantile_crossing_audit.md`)
4. **The best point forecaster is target-dependent, and naive persistence is competitive.** Across 13 dataset/horizon cells the winners are xgboost (9), persistence (4). (`combined/point_metrics.csv`)
5. **Practical improvement and statistical significance diverge.** The Friedman test rejects equality of the four point models (chi2 = 14.07, p = 0.0028), but after Holm correction only seasonal_naive vs xgboost is significant (p = 0.0234); xgboost vs persistence gives p = 1.000. Effect sizes should be reported as magnitudes, not as demonstrated superiority. (`combined/ranking_tests.csv`, `combined/posthoc_comparisons.csv`)
6. **Closed-loop evaluation changes the robustness conclusion.** Under a 2 sd sensor bias the conventional fixed-interval protocol reports observed-signal coverage of 0.0000–0.0749 — a loud alarm — while in closed loop the forecaster absorbs the fault: observed-signal coverage stays as high as 0.9763 while clean-reference coverage falls to 0.0001. The disturbance is experimentally manipulated, so this is a causal statement about the injected bias. (`combined/robustness_metrics.csv`, `report/closed_loop_terminology.md`)
7. **Absorption is not uniform and must not be stated as universal.** At the same severity it is near-complete on some targets and partial on others; the per-dataset values are in `combined/robustness_metrics.csv` and `report/figures/fig_13_closed_loop_absorption.png`.
8. **Calibration contamination is the most damaging disturbance studied.** At the highest contamination level the mean interval width reaches 1468.76 on bdg2, with coverage saturating toward 1. (`combined/robustness_metrics.csv`)
9. **Adaptive recalibration reduces coverage deviation on 4 of 4 datasets** relative to static calibration, but does not by itself achieve nominal coverage everywhere. (`combined/recalibration_metrics.csv`)
10. **bdg2 has no distinct rolling-window recalibration result.** The calibration replay selected an unwindowed configuration, so the rolling row reproduces periodic exactly and the two must not be reported as independent strategies. (`combined/recalibration_metrics.csv`, column `strategy_is_distinct`)
11. **Alert operating points must be tuned per target, on out-of-conformal-calibration data.** Rules frozen on the later 40% of the calibration partition differ on every dataset, and the pooled procedure they replace understated the false-alert workload. (`combined/alert_metrics.csv`, `report/alert_selection_audit.md`)
12. **No numeric comparison with published results is claimed.** None of the twelve reference papers shares this study's dataset, target, horizon, partitioning and metric definition simultaneously. (`combined/literature_benchmark_matrix.csv`)

_Claims are generated from the persisted tables, so they cannot drift from the results. Causal wording is used only for the disturbance experiments, where the cause is manipulated._
