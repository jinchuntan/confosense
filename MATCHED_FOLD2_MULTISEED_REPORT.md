# Matched fold-2 multiseed comparison

Validated **13/52 new paired units**, seeds 43–43. Actual run exits are all 0: **104 tuning + 26 final learned fits**, **39 point and 78 interval cells**, **78 saved-model prediction checks**, and **13 zero-fit resumes**. Observed maximum artifact prediction discrepancy: 0. Actual seed paths and deterministic persistence aliases passed verification. No historical model was refitted.

[No-fitting failure diagnosis](MATCHED_FAILURE_DIAGNOSIS.md) found measured bias and distribution changes, without a new unresolved correctness defect. Scientific source stays `cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e`. [Evaluated source](review/matched_fold2_multiseed_20260914/evaluated_commit.json), [evidence index](review/matched_fold2_multiseed_20260914/EVIDENCE_INDEX.md), and [progress/restart](review/matched_fold2_multiseed_20260914/PROGRESS_AND_RESTART.md) retain identities and actual commands.

## Five-seed evidence and interpretation

[Every seed, metric and measured model cost](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/seed43_summary_v1/fold2_five_seed_comparison.csv) and [mean, sample standard deviation, minimum and maximum](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/seed43_summary_v1/training_seed_summary.csv) describe training randomness on identical fold-2 evaluation support. They are not population confidence intervals. Persistence seed rows are deterministic aliases, not independent replicates. All seeds remain visible; none is selected as best for reporting.

| dataset | physical_minutes | seeds | mae_difference_mean | mae_difference_min | mae_difference_max | lstm_lower_mae_seeds | winkler95_difference_mean | lstm_lower_winkler95_seeds | lstm_coverage95_mean | xgboost_coverage95_mean | mpiw95_difference_mean | cpu_ratio_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 60 | 2 | 1.65708 | 1.45398 | 1.86018 | 0 | 9.35897 | 0 | 0.950678 | 0.948427 | 7.57859 | 109.563 |
| bdg2 | 180 | 2 | 5.40108 | 4.87192 | 5.93024 | 0 | 83.9443 | 0 | 0.949581 | 0.949249 | 32.2121 | 51.7368 |
| bdg2 | 360 | 2 | 5.85229 | 5.80442 | 5.90016 | 0 | 67.1949 | 0 | 0.951703 | 0.949148 | 34.1383 | 35.5062 |
| pleia | 10 | 2 | 0.790913 | 0.769482 | 0.812343 | 0 | 6.36147 | 0 | 0.285657 | 0.330675 | 1.42749 | 55.0483 |
| pleia | 30 | 2 | 0.2464 | 0.237183 | 0.255618 | 0 | -1.82254 | 2 | 0.276572 | 0.297466 | 0.656816 | 42.7097 |
| pleia | 60 | 2 | 0.155095 | 0.126363 | 0.183827 | 0 | -6.67871 | 2 | 0.27203 | 0.31826 | 0.559109 | 27.2267 |
| pleia_energy | 10 | 2 | -0.0128716 | -0.0224386 | -0.00330454 | 2 | 0.912773 | 0 | 0.620723 | 0.787019 | -0.276511 | 26.5043 |
| pleia_energy | 30 | 2 | 0.0229239 | 0.00805599 | 0.0377919 | 0 | 0.431303 | 0 | 0.659887 | 0.7366 | -0.0425115 | 20.4671 |
| pleia_energy | 60 | 2 | 0.0276107 | 0.0271564 | 0.028065 | 0 | 0.0621661 | 0 | 0.665994 | 0.70758 | 0.0286874 | 16.0326 |
| rico | 5 | 2 | 2.14272 | 1.97957 | 2.30588 | 0 | 62.2374 | 0 | 0.174356 | 0.704671 | 1.134 | 20.7142 |
| rico | 15 | 2 | 2.19159 | 1.95815 | 2.42503 | 0 | 69.6794 | 0 | 0.144772 | 0.794675 | 0.34303 | 19.2636 |
| rico | 30 | 2 | 2.24665 | 2.00205 | 2.49124 | 0 | 75.836 | 0 | 0.113539 | 0.81916 | -0.398114 | 22.9816 |
| rico | 60 | 2 | 1.68145 | 1.44077 | 1.92213 | 0 | 66.0907 | 0 | 0.170343 | 0.842939 | -2.23155 | 15.0473 |

Differences are LSTM minus XGBoost. CPU ratio is LSTM/XGBoost measured model-phase CPU. Lower width is not a benefit without coverage context. The [paired table](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/seed43_summary_v1/paired_model_contrasts.csv) explicitly distinguishes **signed deviation from nominal**, **absolute deviation from nominal**, and their paired differences at both 90% and 95%. Group and RICO-phase summaries retain original support; dependent horizons and seeds do not create independent buildings, acquisition runs or periods.

### PLEIA temperature

Target units: degrees C. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | attention_lstm | 3.06676 | 3.41536 | 0.214697 | 3.36455 | 34.2195 | 0.285657 | 4.13541 | 54.2995 | 206.078 |
| 10 | persistence | 0.239376 | 0.336674 | 0.94085 | 1.2 | 1.54723 | 0.965176 | 1.6 | 1.90443 | 0.015625 |
| 10 | xgboost | 2.27585 | 2.67888 | 0.255425 | 2.13186 | 28.81 | 0.330675 | 2.70792 | 47.9381 | 3.75 |
| 30 | attention_lstm | 3.66792 | 4.00034 | 0.217573 | 4.61968 | 35.8509 | 0.276572 | 5.37441 | 56.5 | 160.797 |
| 30 | persistence | 0.391592 | 0.565536 | 0.936308 | 2 | 2.66519 | 0.960028 | 2.4 | 3.27009 | 0 |
| 30 | xgboost | 3.42152 | 3.80652 | 0.223933 | 3.95671 | 36.3905 | 0.297466 | 4.7176 | 58.3225 | 3.76562 |
| 60 | attention_lstm | 4.55427 | 4.85058 | 0.202735 | 6.33041 | 38.5607 | 0.27203 | 7.18614 | 58.5749 | 97.8359 |
| 60 | persistence | 0.547946 | 0.781775 | 0.91935 | 2.6 | 3.66834 | 0.953063 | 3.2 | 4.51422 | 0.0078125 |
| 60 | xgboost | 4.39918 | 4.81586 | 0.243969 | 5.76297 | 41.279 | 0.31826 | 6.62703 | 65.2536 | 3.59375 |

### PLEIA energy

Target units: kWh per 10 minutes. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | attention_lstm | 0.124581 | 0.223976 | 0.559806 | 0.130861 | 1.70794 | 0.620723 | 0.162062 | 3.06213 | 100.023 |
| 10 | persistence | 0.127609 | 0.24188 | 0.560311 | 0.078125 | 2.09703 | 0.642879 | 0.125 | 3.78359 | 0.015625 |
| 10 | xgboost | 0.137452 | 0.229135 | 0.676441 | 0.270538 | 1.56818 | 0.787019 | 0.438573 | 2.14936 | 3.76562 |
| 30 | attention_lstm | 0.143146 | 0.249415 | 0.571364 | 0.179651 | 1.74697 | 0.659887 | 0.225293 | 3.01194 | 74.3438 |
| 30 | persistence | 0.131261 | 0.257542 | 0.571111 | 0.078125 | 2.18606 | 0.639245 | 0.125 | 3.96345 | 0.0078125 |
| 30 | xgboost | 0.120222 | 0.226053 | 0.676542 | 0.200297 | 1.55344 | 0.7366 | 0.267804 | 2.58064 | 3.63281 |
| 60 | attention_lstm | 0.155782 | 0.263723 | 0.588675 | 0.21121 | 1.78882 | 0.665994 | 0.257478 | 3.07388 | 58.1094 |
| 60 | persistence | 0.129989 | 0.257545 | 0.560715 | 0.078125 | 2.15652 | 0.640658 | 0.125 | 3.89904 | 0 |
| 60 | xgboost | 0.128171 | 0.245745 | 0.639295 | 0.162569 | 1.76773 | 0.70758 | 0.228791 | 3.01171 | 3.625 |

### RICO temperature

Target units: degrees C. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | attention_lstm | 2.40864 | 2.8497 | 0.152324 | 1.48163 | 35.9209 | 0.174356 | 1.70487 | 66.8259 | 110.711 |
| 5 | persistence | 0.0744708 | 0.12451 | 0.92821 | 0.4 | 0.601335 | 0.972388 | 0.6 | 0.780856 | 0.015625 |
| 5 | xgboost | 0.265915 | 0.434514 | 0.523355 | 0.34065 | 3.21798 | 0.704671 | 0.570869 | 4.58851 | 5.27344 |
| 15 | attention_lstm | 2.59558 | 3.03027 | 0.125211 | 1.48097 | 39.5375 | 0.144772 | 1.68614 | 74.2209 | 94.1875 |
| 15 | persistence | 0.209382 | 0.33076 | 0.915359 | 1 | 1.6583 | 0.962932 | 1.6 | 2.14624 | 0.0078125 |
| 15 | xgboost | 0.40399 | 0.582258 | 0.642115 | 0.816928 | 3.85973 | 0.794675 | 1.34311 | 4.54155 | 4.78125 |
| 30 | attention_lstm | 2.91455 | 3.29759 | 0.0895396 | 1.53084 | 45.2432 | 0.113539 | 1.87049 | 83.2028 | 103.352 |
| 30 | persistence | 0.389696 | 0.599428 | 0.921612 | 2 | 3.00143 | 0.964132 | 3 | 3.8624 | 0.0078125 |
| 30 | xgboost | 0.667901 | 0.92675 | 0.652406 | 1.36456 | 6.13138 | 0.81916 | 2.2686 | 7.36678 | 4.5 |
| 60 | attention_lstm | 2.90226 | 3.37068 | 0.144322 | 1.84345 | 42.9123 | 0.170343 | 2.18337 | 78.5569 | 55.3594 |
| 60 | persistence | 0.715675 | 1.04138 | 0.924188 | 3.6 | 5.10039 | 0.960851 | 5 | 6.39755 | 0.015625 |
| 60 | xgboost | 1.22081 | 1.82761 | 0.664673 | 2.77686 | 10.6757 | 0.842939 | 4.41492 | 12.4662 | 3.6875 |

### BDG2 electricity

Target units: kWh per hour. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | attention_lstm | 19.4093 | 36.875 | 0.903074 | 99.4007 | 179.537 | 0.950678 | 143.894 | 241.92 | 1052.62 |
| 60 | persistence | 20.988 | 41.6714 | 0.894919 | 115.806 | 207.414 | 0.946767 | 165.4 | 273.691 | 0.0234375 |
| 60 | xgboost | 17.7522 | 34.9474 | 0.903074 | 93.4884 | 172.148 | 0.948427 | 136.316 | 232.561 | 9.57812 |
| 180 | attention_lstm | 33.1736 | 65.7105 | 0.90485 | 164.444 | 315.705 | 0.949581 | 236.748 | 438.394 | 473.188 |
| 180 | persistence | 42.8035 | 78.6988 | 0.897835 | 250 | 402.06 | 0.945987 | 344.2 | 504.752 | 0.03125 |
| 180 | xgboost | 27.7726 | 53.1217 | 0.906192 | 142.92 | 260.566 | 0.949249 | 204.536 | 354.45 | 9.125 |
| 360 | attention_lstm | 40.0573 | 77.2516 | 0.906784 | 199.645 | 369.637 | 0.951703 | 282.048 | 510.862 | 314.977 |
| 360 | persistence | 73.284 | 119.93 | 0.897546 | 406.312 | 580.272 | 0.944226 | 498 | 703.035 | 0.0234375 |
| 360 | xgboost | 34.205 | 66.8343 | 0.908285 | 176.714 | 323.399 | 0.949148 | 247.91 | 443.667 | 8.83594 |

## Measured cost and acceptance

| model_seed | units | run_wall_seconds | run_cpu_seconds | validation_wall_seconds | resume_wall_seconds | peak_lifetime_rss_MiB |
| --- | --- | --- | --- | --- | --- | --- |
| 43 | 13 | 2784.46 | 2707.36 | 259.51 | 215.397 | 1186.92 |

New model commands used **0.7735 wall hours** and **0.7520 process CPU hours**. Independent validation adds 4.33 wall minutes; zero-fit resume adds 3.59. Maximum lifetime peak RSS: 1186.92 MiB. These exclude preflight, diagnosis, orchestration, aggregation and publication. Separate actual command logs retain those costs. Nested phase timers must not be added twice.

CPU-only, one numerical/Torch thread, n_jobs=1, lazy batch256, the nonblocking 3 GiB launch reference, 256 MiB epoch floor and 8 GiB disk guard were preserved. All per-unit saved-stream arithmetic, finite-sample ranks, inner selection/epochs, serialized-model reconstruction, group-to-pooled squared-error arithmetic and immutable zero-fit resumes passed. No clipping, outer-result retuning or model-ranking gate was used. Original phase timing measurements stay attached to their original executions.

## Remaining work

Cumulative **31/195 paired units, 93/585 point cells and 186/1170 interval cells**. Fold 2 contains 26 paired units; five additional-fold units stay separate. **164 paired units / 1640 learned fits remain** in the matched core queue. Updated same-dataset planning scenario: 4.18–107.70 model-hours; this excludes preparation and verification and is not a confidence interval or deadline.

The [implementation readiness map](MATCHED_METHOD_READINESS_MAP.md) identifies the smallest next adapter package for broader conformal methods and causal alerting. Static own-model absolute-error split conformal does not complete CQR, EnbPI, DSCP, seasonal, operational, conditional-challenge, contamination/recovery or robustness obligations. Remaining outer folds are still necessary. RICO historical use and phase imbalance, recurring known BDG2 buildings, and the inspected historical periods limit claims. Full-study readiness remains false; no unlisted fits are launched.
