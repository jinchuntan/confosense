# Matched fold-2 multiseed comparison

Validated **39/52 new paired units**, seeds 43–45. Actual run exits are all 0: **312 tuning + 78 final learned fits**, **117 point and 234 interval cells**, **234 saved-model prediction checks**, and **39 zero-fit resumes**. Observed maximum artifact prediction discrepancy: 0. Actual seed paths and deterministic persistence aliases passed verification. No historical model was refitted.

[No-fitting failure diagnosis](MATCHED_FAILURE_DIAGNOSIS.md) found measured bias and distribution changes, without a new unresolved correctness defect. Scientific source stays `cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e`. [Evaluated source](review/matched_fold2_multiseed_20260914/evaluated_commit.json), [evidence index](review/matched_fold2_multiseed_20260914/EVIDENCE_INDEX.md), and [progress/restart](review/matched_fold2_multiseed_20260914/PROGRESS_AND_RESTART.md) retain identities and actual commands.

## Five-seed evidence and interpretation

[Every seed, metric and measured model cost](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/seed45_summary_v1/fold2_five_seed_comparison.csv) and [mean, sample standard deviation, minimum and maximum](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/seed45_summary_v1/training_seed_summary.csv) describe training randomness on identical fold-2 evaluation support. They are not population confidence intervals. Persistence seed rows are deterministic aliases, not independent replicates. All seeds remain visible; none is selected as best for reporting.

| dataset | physical_minutes | seeds | mae_difference_mean | mae_difference_min | mae_difference_max | lstm_lower_mae_seeds | winkler95_difference_mean | lstm_lower_winkler95_seeds | lstm_coverage95_mean | xgboost_coverage95_mean | mpiw95_difference_mean | cpu_ratio_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 60 | 4 | 1.56962 | 1.43653 | 1.86018 | 0 | 7.98268 | 0 | 0.949184 | 0.9486 | 4.98846 | 91.4391 |
| bdg2 | 180 | 4 | 5.63645 | 4.77752 | 6.9661 | 0 | 80.542 | 0 | 0.949776 | 0.949213 | 32.0776 | 51.5727 |
| bdg2 | 360 | 4 | 6.81032 | 5.80442 | 8.08193 | 0 | 65.8721 | 0 | 0.951386 | 0.949365 | 33.7646 | 34.8247 |
| pleia | 10 | 4 | 1.01573 | 0.769482 | 1.37862 | 0 | 10.0946 | 0 | 0.285909 | 0.333274 | 1.7514 | 55.3765 |
| pleia | 30 | 4 | 0.238313 | 0.187038 | 0.273412 | 0 | -0.628778 | 3 | 0.280256 | 0.307636 | 0.56072 | 45.7943 |
| pleia | 60 | 4 | 0.254395 | 0.126363 | 0.495218 | 0 | -3.46502 | 3 | 0.270945 | 0.316418 | 0.640784 | 27.6449 |
| pleia_energy | 10 | 4 | -0.00243225 | -0.0224386 | 0.0144587 | 2 | 0.988027 | 0 | 0.604194 | 0.782477 | -0.24046 | 26.0971 |
| pleia_energy | 30 | 4 | 0.0259233 | 0.00805599 | 0.0377919 | 0 | 0.499007 | 0 | 0.645604 | 0.748133 | -0.0560162 | 19.6101 |
| pleia_energy | 60 | 4 | 0.0259034 | 0.0193678 | 0.0290243 | 0 | 0.097021 | 1 | 0.657969 | 0.705965 | 0.0291362 | 17.1975 |
| rico | 5 | 4 | 2.32387 | 1.97957 | 2.54696 | 0 | 68.3208 | 0 | 0.132593 | 0.675592 | 1.19032 | 21.6763 |
| rico | 15 | 4 | 2.34519 | 1.95815 | 2.49914 | 0 | 72.8083 | 0 | 0.129317 | 0.783295 | 0.538569 | 20.421 |
| rico | 30 | 4 | 2.22348 | 1.9506 | 2.49124 | 0 | 74.9226 | 0 | 0.110963 | 0.823432 | -0.456865 | 21.8691 |
| rico | 60 | 4 | 1.61473 | 1.22803 | 1.92213 | 0 | 61.251 | 0 | 0.182305 | 0.85964 | -2.27735 | 14.7689 |

Differences are LSTM minus XGBoost. CPU ratio is LSTM/XGBoost measured model-phase CPU. Lower width is not a benefit without coverage context. The [paired table](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/seed45_summary_v1/paired_model_contrasts.csv) explicitly distinguishes **signed deviation from nominal**, **absolute deviation from nominal**, and their paired differences at both 90% and 95%. Group and RICO-phase summaries retain original support; dependent horizons and seeds do not create independent buildings, acquisition runs or periods.

### PLEIA temperature

Target units: degrees C. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | attention_lstm | 3.22468 | 3.59801 | 0.207909 | 3.50018 | 36.2165 | 0.285909 | 4.40437 | 56.201 | 207.473 |
| 10 | persistence | 0.239376 | 0.336674 | 0.94085 | 1.2 | 1.54723 | 0.965176 | 1.6 | 1.90443 | 0.0117188 |
| 10 | xgboost | 2.20895 | 2.5995 | 0.256561 | 2.09739 | 27.7323 | 0.333274 | 2.65297 | 46.1064 | 3.75 |
| 30 | attention_lstm | 3.61442 | 3.95744 | 0.214571 | 4.45683 | 36.1312 | 0.280256 | 5.26526 | 56.4607 | 172.422 |
| 30 | persistence | 0.391592 | 0.565536 | 0.936308 | 2 | 2.66519 | 0.960028 | 2.4 | 3.27009 | 0.0078125 |
| 30 | xgboost | 3.3761 | 3.76492 | 0.23279 | 3.94882 | 35.6603 | 0.307636 | 4.70454 | 57.0895 | 3.76562 |
| 60 | attention_lstm | 4.65225 | 4.95922 | 0.204199 | 6.41346 | 39.9123 | 0.270945 | 7.31019 | 60.6264 | 100.398 |
| 60 | persistence | 0.547946 | 0.781775 | 0.91935 | 2.6 | 3.66834 | 0.953063 | 3.2 | 4.51422 | 0.0117188 |
| 60 | xgboost | 4.39785 | 4.79935 | 0.240512 | 5.8001 | 40.7763 | 0.316418 | 6.6694 | 64.0914 | 3.63281 |

### PLEIA energy

Target units: kWh per 10 minutes. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | attention_lstm | 0.127941 | 0.225761 | 0.526496 | 0.128999 | 1.75117 | 0.604194 | 0.164012 | 3.10452 | 98.1094 |
| 10 | persistence | 0.127609 | 0.24188 | 0.560311 | 0.078125 | 2.09703 | 0.642879 | 0.125 | 3.78359 | 0.0078125 |
| 10 | xgboost | 0.130374 | 0.220979 | 0.672302 | 0.243013 | 1.53241 | 0.782477 | 0.404472 | 2.1165 | 3.75391 |
| 30 | attention_lstm | 0.146214 | 0.249152 | 0.551605 | 0.184964 | 1.75586 | 0.645604 | 0.229827 | 3.01466 | 70.4297 |
| 30 | persistence | 0.131261 | 0.257542 | 0.571111 | 0.078125 | 2.18606 | 0.639245 | 0.125 | 3.96345 | 0.015625 |
| 30 | xgboost | 0.12029 | 0.22605 | 0.689967 | 0.214559 | 1.5269 | 0.748133 | 0.285843 | 2.51566 | 3.58984 |
| 60 | attention_lstm | 0.15359 | 0.263315 | 0.572323 | 0.202859 | 1.82905 | 0.657969 | 0.254821 | 3.11237 | 62.5039 |
| 60 | persistence | 0.129989 | 0.257545 | 0.560715 | 0.078125 | 2.15652 | 0.640658 | 0.125 | 3.89904 | 0.00390625 |
| 60 | xgboost | 0.127687 | 0.244561 | 0.635788 | 0.157266 | 1.77547 | 0.705965 | 0.225685 | 3.01535 | 3.63281 |

### RICO temperature

Target units: degrees C. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | attention_lstm | 2.59448 | 2.96913 | 0.115767 | 1.51339 | 39.1798 | 0.132593 | 1.74187 | 73.0725 | 109.621 |
| 5 | persistence | 0.0744708 | 0.12451 | 0.92821 | 0.4 | 0.601335 | 0.972388 | 0.6 | 0.780856 | 0.015625 |
| 5 | xgboost | 0.270611 | 0.433322 | 0.499827 | 0.339767 | 3.29249 | 0.675592 | 0.551544 | 4.75177 | 5.04297 |
| 15 | attention_lstm | 2.75164 | 3.14083 | 0.101998 | 1.51235 | 42.2688 | 0.129317 | 1.84079 | 77.5611 | 95.0352 |
| 15 | persistence | 0.209382 | 0.33076 | 0.915359 | 1 | 1.6583 | 0.962932 | 1.6 | 2.14624 | 0.0078125 |
| 15 | xgboost | 0.406451 | 0.585646 | 0.635203 | 0.798433 | 3.93933 | 0.783295 | 1.30222 | 4.75284 | 4.69531 |
| 30 | attention_lstm | 2.89484 | 3.26407 | 0.0944307 | 1.6181 | 44.1707 | 0.110963 | 1.89486 | 82.0377 | 98.0664 |
| 30 | persistence | 0.389696 | 0.599428 | 0.921612 | 2 | 3.00143 | 0.964132 | 3 | 3.8624 | 0.0078125 |
| 30 | xgboost | 0.671353 | 0.928571 | 0.644026 | 1.34103 | 6.21423 | 0.823432 | 2.35173 | 7.11513 | 4.5 |
| 60 | attention_lstm | 2.84735 | 3.28675 | 0.155857 | 2.04007 | 40.46 | 0.182305 | 2.4115 | 73.1095 | 57.7422 |
| 60 | persistence | 0.715675 | 1.04138 | 0.924188 | 3.6 | 5.10039 | 0.960851 | 5 | 6.39755 | 0.0078125 |
| 60 | xgboost | 1.23263 | 1.83004 | 0.650769 | 2.69699 | 10.9541 | 0.85964 | 4.68886 | 11.8585 | 3.92578 |

### BDG2 electricity

Target units: kWh per hour. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | attention_lstm | 19.3334 | 36.5645 | 0.900837 | 97.6615 | 178.549 | 0.949184 | 141.49 | 240.418 | 862.117 |
| 60 | persistence | 20.988 | 41.6714 | 0.894919 | 115.806 | 207.414 | 0.946767 | 165.4 | 273.691 | 0.0234375 |
| 60 | xgboost | 17.7638 | 34.9459 | 0.90301 | 93.5155 | 172.163 | 0.9486 | 136.502 | 232.436 | 9.37109 |
| 180 | attention_lstm | 33.821 | 65.684 | 0.905102 | 166.683 | 316.585 | 0.949776 | 238.93 | 438.006 | 454.277 |
| 180 | persistence | 42.8035 | 78.6988 | 0.897835 | 250 | 402.06 | 0.945987 | 344.2 | 504.752 | 0.0273438 |
| 180 | xgboost | 28.1846 | 53.6744 | 0.906106 | 145.057 | 263.222 | 0.949213 | 206.853 | 357.464 | 8.79688 |
| 360 | attention_lstm | 40.9865 | 77.3821 | 0.906142 | 201.127 | 370.275 | 0.951386 | 282.435 | 510.068 | 303.844 |
| 360 | persistence | 73.284 | 119.93 | 0.897546 | 406.312 | 580.272 | 0.944226 | 498 | 703.035 | 0.0234375 |
| 360 | xgboost | 34.1762 | 66.9032 | 0.907672 | 175.913 | 323.59 | 0.949365 | 248.671 | 444.195 | 8.70703 |

## Measured cost and acceptance

| model_seed | units | run_wall_seconds | run_cpu_seconds | validation_wall_seconds | resume_wall_seconds | peak_lifetime_rss_MiB |
| --- | --- | --- | --- | --- | --- | --- |
| 43 | 13 | 2784.46 | 2707.36 | 259.51 | 215.397 | 1186.92 |
| 44 | 13 | 3082.43 | 2987.31 | 280.574 | 220.931 | 1186.72 |
| 45 | 13 | 2688.63 | 2611.17 | 264.253 | 215.001 | 1187.03 |

New model commands used **2.3765 wall hours** and **2.3072 process CPU hours**. Independent validation adds 13.41 wall minutes; zero-fit resume adds 10.86. Maximum lifetime peak RSS: 1187.03 MiB. These exclude preflight, diagnosis, orchestration, aggregation and publication. Separate actual command logs retain those costs. Nested phase timers must not be added twice.

CPU-only, one numerical/Torch thread, n_jobs=1, lazy batch256, the nonblocking 3 GiB launch reference, 256 MiB epoch floor and 8 GiB disk guard were preserved. All per-unit saved-stream arithmetic, finite-sample ranks, inner selection/epochs, serialized-model reconstruction, group-to-pooled squared-error arithmetic and immutable zero-fit resumes passed. No clipping, outer-result retuning or model-ranking gate was used. Original phase timing measurements stay attached to their original executions.

## Remaining work

Cumulative **57/195 paired units, 171/585 point cells and 342/1170 interval cells**. Fold 2 contains 52 paired units; five additional-fold units stay separate. **138 paired units / 1380 learned fits remain** in the matched core queue. Updated same-dataset planning scenario: 3.76–97.20 model-hours; this excludes preparation and verification and is not a confidence interval or deadline.

The [implementation readiness map](MATCHED_METHOD_READINESS_MAP.md) identifies the smallest next adapter package for broader conformal methods and causal alerting. Static own-model absolute-error split conformal does not complete CQR, EnbPI, DSCP, seasonal, operational, conditional-challenge, contamination/recovery or robustness obligations. Remaining outer folds are still necessary. RICO historical use and phase imbalance, recurring known BDG2 buildings, and the inspected historical periods limit claims. Full-study readiness remains false; no unlisted fits are launched.
