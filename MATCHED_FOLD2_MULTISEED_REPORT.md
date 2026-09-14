# Matched fold-2 multiseed comparison

Validated **26/52 new paired units**, seeds 43–44. Actual run exits are all 0: **208 tuning + 52 final learned fits**, **78 point and 156 interval cells**, **156 saved-model prediction checks**, and **26 zero-fit resumes**. Observed maximum artifact prediction discrepancy: 0. Actual seed paths and deterministic persistence aliases passed verification. No historical model was refitted.

[No-fitting failure diagnosis](MATCHED_FAILURE_DIAGNOSIS.md) found measured bias and distribution changes, without a new unresolved correctness defect. Scientific source stays `cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e`. [Evaluated source](review/matched_fold2_multiseed_20260914/evaluated_commit.json), [evidence index](review/matched_fold2_multiseed_20260914/EVIDENCE_INDEX.md), and [progress/restart](review/matched_fold2_multiseed_20260914/PROGRESS_AND_RESTART.md) retain identities and actual commands.

## Five-seed evidence and interpretation

[Every seed, metric and measured model cost](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/seed44_summary_v1/fold2_five_seed_comparison.csv) and [mean, sample standard deviation, minimum and maximum](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/seed44_summary_v1/training_seed_summary.csv) describe training randomness on identical fold-2 evaluation support. They are not population confidence intervals. Persistence seed rows are deterministic aliases, not independent replicates. All seeds remain visible; none is selected as best for reporting.

| dataset | physical_minutes | seeds | mae_difference_mean | mae_difference_min | mae_difference_max | lstm_lower_mae_seeds | winkler95_difference_mean | lstm_lower_winkler95_seeds | lstm_coverage95_mean | xgboost_coverage95_mean | mpiw95_difference_mean | cpu_ratio_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 60 | 3 | 1.58357 | 1.43653 | 1.86018 | 0 | 7.75343 | 0 | 0.949394 | 0.948653 | 5.59702 | 99.6477 |
| bdg2 | 180 | 3 | 5.19323 | 4.77752 | 5.93024 | 0 | 79.6867 | 0 | 0.949731 | 0.949076 | 32.4204 | 55.3995 |
| bdg2 | 360 | 3 | 6.5955 | 5.80442 | 8.08193 | 0 | 66.0937 | 0 | 0.951357 | 0.949394 | 35.4803 | 33.2074 |
| pleia | 10 | 3 | 0.894766 | 0.769482 | 1.10247 | 0 | 9.51627 | 0 | 0.284479 | 0.33764 | 1.48647 | 55.8007 |
| pleia | 30 | 3 | 0.255404 | 0.237183 | 0.273412 | 0 | -0.452344 | 2 | 0.274183 | 0.304869 | 0.580481 | 44.4966 |
| pleia | 60 | 3 | 0.268469 | 0.126363 | 0.495218 | 0 | -3.68571 | 2 | 0.264964 | 0.322297 | 0.621395 | 27.2092 |
| pleia_energy | 10 | 3 | -0.00806256 | -0.0224386 | 0.00155544 | 2 | 0.984181 | 0 | 0.607517 | 0.787087 | -0.263983 | 26.5941 |
| pleia_energy | 30 | 3 | 0.0230005 | 0.00805599 | 0.0377919 | 0 | 0.510647 | 0 | 0.655395 | 0.752902 | -0.0648872 | 19.9152 |
| pleia_energy | 60 | 3 | 0.0248631 | 0.0193678 | 0.028065 | 0 | 0.0265116 | 1 | 0.671949 | 0.706807 | 0.0327604 | 16.2973 |
| rico | 5 | 3 | 2.24951 | 1.97957 | 2.46308 | 0 | 66.4582 | 0 | 0.135834 | 0.67054 | 1.12662 | 22.3423 |
| rico | 15 | 3 | 2.29411 | 1.95815 | 2.49914 | 0 | 73.8599 | 0 | 0.118973 | 0.774048 | 0.400266 | 22.8635 |
| rico | 30 | 3 | 2.14796 | 1.9506 | 2.49124 | 0 | 72.2691 | 0 | 0.109604 | 0.812139 | -0.382219 | 24.8982 |
| rico | 60 | 3 | 1.53031 | 1.22803 | 1.92213 | 0 | 58.1253 | 0 | 0.196313 | 0.857128 | -2.25537 | 14.6891 |

Differences are LSTM minus XGBoost. CPU ratio is LSTM/XGBoost measured model-phase CPU. Lower width is not a benefit without coverage context. The [paired table](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/seed44_summary_v1/paired_model_contrasts.csv) explicitly distinguishes **signed deviation from nominal**, **absolute deviation from nominal**, and their paired differences at both 90% and 95%. Group and RICO-phase summaries retain original support; dependent horizons and seeds do not create independent buildings, acquisition runs or periods.

### PLEIA temperature

Target units: degrees C. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | attention_lstm | 3.11305 | 3.47979 | 0.21076 | 3.33806 | 35.332 | 0.284479 | 4.18223 | 55.4647 | 208.719 |
| 10 | persistence | 0.239376 | 0.336674 | 0.94085 | 1.2 | 1.54723 | 0.965176 | 1.6 | 1.90443 | 0.0104167 |
| 10 | xgboost | 2.21828 | 2.61165 | 0.260052 | 2.12451 | 27.7493 | 0.33764 | 2.69577 | 45.9485 | 3.74479 |
| 30 | attention_lstm | 3.64687 | 3.98621 | 0.214327 | 4.50158 | 36.4041 | 0.274183 | 5.28065 | 57.3335 | 167.786 |
| 30 | persistence | 0.391592 | 0.565536 | 0.936308 | 2 | 2.66519 | 0.960028 | 2.4 | 3.27009 | 0.00520833 |
| 30 | xgboost | 3.39146 | 3.78339 | 0.232092 | 3.94811 | 35.9982 | 0.304869 | 4.70017 | 57.7859 | 3.77083 |
| 60 | attention_lstm | 4.66084 | 4.95999 | 0.199421 | 6.4219 | 39.8157 | 0.264964 | 7.28848 | 60.7562 | 99.3333 |
| 60 | persistence | 0.547946 | 0.781775 | 0.91935 | 2.6 | 3.66834 | 0.953063 | 3.2 | 4.51422 | 0.0104167 |
| 60 | xgboost | 4.39237 | 4.80714 | 0.244978 | 5.78105 | 41.0071 | 0.322297 | 6.66708 | 64.442 | 3.65104 |

### PLEIA energy

Target units: kWh per 10 minutes. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | attention_lstm | 0.124964 | 0.223484 | 0.5376 | 0.124957 | 1.7334 | 0.607517 | 0.157124 | 3.10028 | 100.568 |
| 10 | persistence | 0.127609 | 0.24188 | 0.560311 | 0.078125 | 2.09703 | 0.642879 | 0.125 | 3.78359 | 0.0104167 |
| 10 | xgboost | 0.133027 | 0.224162 | 0.678847 | 0.259379 | 1.53192 | 0.787087 | 0.421108 | 2.1161 | 3.77604 |
| 30 | attention_lstm | 0.143309 | 0.248137 | 0.565089 | 0.182535 | 1.74032 | 0.655395 | 0.228111 | 2.99093 | 71.901 |
| 30 | persistence | 0.131261 | 0.257542 | 0.571111 | 0.078125 | 2.18606 | 0.639245 | 0.125 | 3.96345 | 0.015625 |
| 30 | xgboost | 0.120308 | 0.225969 | 0.694526 | 0.220318 | 1.51151 | 0.752902 | 0.292998 | 2.48028 | 3.60938 |
| 60 | attention_lstm | 0.153281 | 0.263064 | 0.586185 | 0.209862 | 1.78746 | 0.671949 | 0.261728 | 3.03772 | 58.9844 |
| 60 | persistence | 0.129989 | 0.257545 | 0.560715 | 0.078125 | 2.15652 | 0.640658 | 0.125 | 3.89904 | 0.00520833 |
| 60 | xgboost | 0.128418 | 0.245332 | 0.637058 | 0.160852 | 1.77348 | 0.706807 | 0.228967 | 3.01121 | 3.61979 |

### RICO temperature

Target units: degrees C. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | attention_lstm | 2.52309 | 2.89723 | 0.118385 | 1.47308 | 38.0839 | 0.135834 | 1.68082 | 71.2831 | 113.672 |
| 5 | persistence | 0.0744708 | 0.12451 | 0.92821 | 0.4 | 0.601335 | 0.972388 | 0.6 | 0.780856 | 0.015625 |
| 5 | xgboost | 0.273584 | 0.437229 | 0.497776 | 0.339507 | 3.3465 | 0.67054 | 0.554194 | 4.82496 | 5.07292 |
| 15 | attention_lstm | 2.6939 | 3.07797 | 0.103638 | 1.44805 | 41.6716 | 0.118973 | 1.6392 | 78.683 | 104.755 |
| 15 | persistence | 0.209382 | 0.33076 | 0.915359 | 1 | 1.6583 | 0.962932 | 1.6 | 2.14624 | 0.0104167 |
| 15 | xgboost | 0.399789 | 0.57728 | 0.647428 | 0.812066 | 3.79331 | 0.774048 | 1.23893 | 4.8231 | 4.58333 |
| 30 | attention_lstm | 2.83125 | 3.18822 | 0.0914743 | 1.58156 | 43.2192 | 0.109604 | 1.87827 | 79.825 | 111.25 |
| 30 | persistence | 0.389696 | 0.599428 | 0.921612 | 2 | 3.00143 | 0.964132 | 3 | 3.8624 | 0.00520833 |
| 30 | xgboost | 0.683284 | 0.944727 | 0.642407 | 1.35087 | 6.3426 | 0.812139 | 2.26049 | 7.55595 | 4.47396 |
| 60 | attention_lstm | 2.77146 | 3.22322 | 0.163689 | 2.02125 | 39.1484 | 0.196313 | 2.41485 | 70.2352 | 58.2292 |
| 60 | persistence | 0.715675 | 1.04138 | 0.924188 | 3.6 | 5.10039 | 0.960851 | 5 | 6.39755 | 0.0104167 |
| 60 | xgboost | 1.24115 | 1.84853 | 0.655844 | 2.76227 | 10.9674 | 0.857128 | 4.67022 | 12.1099 | 3.98438 |

### BDG2 electricity

Target units: kWh per hour. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | attention_lstm | 19.3044 | 36.5558 | 0.900885 | 98.0959 | 178.454 | 0.949394 | 142.002 | 239.853 | 944.526 |
| 60 | persistence | 20.988 | 41.6714 | 0.894919 | 115.806 | 207.414 | 0.946767 | 165.4 | 273.691 | 0.0260417 |
| 60 | xgboost | 17.7209 | 34.8973 | 0.902771 | 93.3412 | 171.928 | 0.948653 | 136.405 | 232.1 | 9.42708 |
| 180 | attention_lstm | 33.252 | 65.3423 | 0.905456 | 166.161 | 315.406 | 0.949731 | 238.319 | 436.465 | 492.526 |
| 180 | persistence | 42.8035 | 78.6988 | 0.897835 | 250 | 402.06 | 0.945987 | 344.2 | 504.752 | 0.0260417 |
| 180 | xgboost | 28.0587 | 53.5303 | 0.906168 | 144.372 | 262.498 | 0.949076 | 205.898 | 356.778 | 8.90625 |
| 360 | attention_lstm | 40.8174 | 77.4048 | 0.904532 | 200.536 | 371.071 | 0.951357 | 283.988 | 510.367 | 292.089 |
| 360 | persistence | 73.284 | 119.93 | 0.897546 | 406.312 | 580.272 | 0.944226 | 498 | 703.035 | 0.0260417 |
| 360 | xgboost | 34.2219 | 66.9186 | 0.90792 | 176.236 | 323.714 | 0.949394 | 248.508 | 444.274 | 8.76042 |

## Measured cost and acceptance

| model_seed | units | run_wall_seconds | run_cpu_seconds | validation_wall_seconds | resume_wall_seconds | peak_lifetime_rss_MiB |
| --- | --- | --- | --- | --- | --- | --- |
| 43 | 13 | 2784.46 | 2707.36 | 259.51 | 215.397 | 1186.92 |
| 44 | 13 | 3082.43 | 2987.31 | 280.574 | 220.931 | 1186.72 |

New model commands used **1.6297 wall hours** and **1.5819 process CPU hours**. Independent validation adds 9.00 wall minutes; zero-fit resume adds 7.27. Maximum lifetime peak RSS: 1186.92 MiB. These exclude preflight, diagnosis, orchestration, aggregation and publication. Separate actual command logs retain those costs. Nested phase timers must not be added twice.

CPU-only, one numerical/Torch thread, n_jobs=1, lazy batch256, the nonblocking 3 GiB launch reference, 256 MiB epoch floor and 8 GiB disk guard were preserved. All per-unit saved-stream arithmetic, finite-sample ranks, inner selection/epochs, serialized-model reconstruction, group-to-pooled squared-error arithmetic and immutable zero-fit resumes passed. No clipping, outer-result retuning or model-ranking gate was used. Original phase timing measurements stay attached to their original executions.

## Remaining work

Cumulative **44/195 paired units, 132/585 point cells and 264/1170 interval cells**. Fold 2 contains 39 paired units; five additional-fold units stay separate. **151 paired units / 1510 learned fits remain** in the matched core queue. Updated same-dataset planning scenario: 3.97–102.62 model-hours; this excludes preparation and verification and is not a confidence interval or deadline.

The [implementation readiness map](MATCHED_METHOD_READINESS_MAP.md) identifies the smallest next adapter package for broader conformal methods and causal alerting. Static own-model absolute-error split conformal does not complete CQR, EnbPI, DSCP, seasonal, operational, conditional-challenge, contamination/recovery or robustness obligations. Remaining outer folds are still necessary. RICO historical use and phase imbalance, recurring known BDG2 buildings, and the inspected historical periods limit claims. Full-study readiness remains false; no unlisted fits are launched.
