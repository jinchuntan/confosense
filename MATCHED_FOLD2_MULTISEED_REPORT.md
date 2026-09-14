# Matched fold-2 multiseed comparison

Validated **52/52 new paired units**, seeds 43–46. Actual run exits are all 0: **416 tuning + 104 final learned fits**, **156 point and 312 interval cells**, **312 saved-model prediction checks**, and **52 zero-fit resumes**. Observed maximum artifact prediction discrepancy: 0. Actual seed paths and deterministic persistence aliases passed verification. No historical model was refitted.

[No-fitting failure diagnosis](MATCHED_FAILURE_DIAGNOSIS.md) found measured bias and distribution changes, without a new unresolved correctness defect. Scientific source stays `cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e`. [Evaluated source](review/matched_fold2_multiseed_20260914/evaluated_commit.json), [evidence index](review/matched_fold2_multiseed_20260914/EVIDENCE_INDEX.md), and [progress/restart](review/matched_fold2_multiseed_20260914/PROGRESS_AND_RESTART.md) retain identities and actual commands.

## Five-seed evidence and interpretation

[Every seed, metric and measured model cost](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/analysis_v1/fold2_five_seed_comparison.csv) and [mean, sample standard deviation, minimum and maximum](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/analysis_v1/training_seed_summary.csv) describe training randomness on identical fold-2 evaluation support. They are not population confidence intervals. Persistence seed rows are deterministic aliases, not independent replicates. All seeds remain visible; none is selected as best for reporting.

| dataset | physical_minutes | seeds | mae_difference_mean | mae_difference_min | mae_difference_max | lstm_lower_mae_seeds | winkler95_difference_mean | lstm_lower_winkler95_seeds | lstm_coverage95_mean | xgboost_coverage95_mean | mpiw95_difference_mean | cpu_ratio_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 60 | 5 | 1.70466 | 1.43653 | 2.24482 | 0 | 7.89683 | 0 | 0.949209 | 0.948839 | 4.99201 | 86.6814 |
| bdg2 | 180 | 5 | 5.24307 | 3.66955 | 6.9661 | 0 | 76.5282 | 0 | 0.950208 | 0.949284 | 30.1274 | 56.5056 |
| bdg2 | 360 | 5 | 6.83414 | 5.80442 | 8.08193 | 0 | 64.9654 | 0 | 0.95213 | 0.949423 | 34.3412 | 34.2093 |
| pleia | 10 | 5 | 0.982142 | 0.769482 | 1.37862 | 0 | 8.3671 | 0 | 0.290663 | 0.329 | 1.78655 | 55.6362 |
| pleia | 30 | 5 | 0.296409 | 0.187038 | 0.528796 | 0 | -0.411313 | 3 | 0.275704 | 0.305118 | 0.677315 | 45.4219 |
| pleia | 60 | 5 | 0.16867 | -0.174228 | 0.495218 | 1 | -5.63639 | 4 | 0.271828 | 0.306753 | 0.598746 | 27.254 |
| pleia_energy | 10 | 5 | -0.000101804 | -0.0224386 | 0.0144587 | 2 | 1.01924 | 0 | 0.604825 | 0.791501 | -0.249825 | 25.8794 |
| pleia_energy | 30 | 5 | 0.0268554 | 0.00805599 | 0.0377919 | 0 | 0.411492 | 0 | 0.649823 | 0.739356 | -0.0378058 | 19.5171 |
| pleia_energy | 60 | 5 | 0.0256686 | 0.0193678 | 0.0290243 | 0 | 0.0313173 | 2 | 0.662744 | 0.70213 | 0.0363251 | 17.0898 |
| rico | 5 | 5 | 2.41115 | 1.97957 | 2.76027 | 0 | 68.6033 | 0 | 0.133985 | 0.679061 | 1.3587 | 21.8496 |
| rico | 15 | 5 | 2.44387 | 1.95815 | 2.83862 | 0 | 73.8712 | 0 | 0.128109 | 0.801715 | 0.616985 | 20.3479 |
| rico | 30 | 5 | 2.35891 | 1.9506 | 2.9006 | 0 | 76.7734 | 0 | 0.108934 | 0.833494 | -0.353878 | 20.281 |
| rico | 60 | 5 | 1.80038 | 1.22803 | 2.543 | 0 | 66.3679 | 0 | 0.165574 | 0.856455 | -2.1374 | 14.177 |

Differences are LSTM minus XGBoost. CPU ratio is LSTM/XGBoost measured model-phase CPU. Lower width is not a benefit without coverage context. The [paired table](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/analysis_v1/paired_model_contrasts.csv) explicitly distinguishes **signed deviation from nominal**, **absolute deviation from nominal**, and their paired differences at both 90% and 95%. Group and RICO-phase summaries retain original support; dependent horizons and seeds do not create independent buildings, acquisition runs or periods.

### PLEIA temperature

Target units: degrees C. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | attention_lstm | 3.24024 | 3.60413 | 0.211507 | 3.6074 | 35.6796 | 0.290663 | 4.50691 | 55.1609 | 207.953 |
| 10 | persistence | 0.239376 | 0.336674 | 0.94085 | 1.2 | 1.54723 | 0.965176 | 1.6 | 1.90443 | 0.009375 |
| 10 | xgboost | 2.2581 | 2.64647 | 0.249944 | 2.14821 | 28.2446 | 0.329 | 2.72036 | 46.7938 | 3.74063 |
| 30 | attention_lstm | 3.66576 | 4.00409 | 0.209529 | 4.51073 | 36.6115 | 0.275704 | 5.34299 | 56.941 | 170.338 |
| 30 | persistence | 0.391592 | 0.565536 | 0.936308 | 2 | 2.66519 | 0.960028 | 2.4 | 3.27009 | 0.00625 |
| 30 | xgboost | 3.36935 | 3.75746 | 0.230887 | 3.91849 | 35.7344 | 0.305118 | 4.66567 | 57.3523 | 3.75 |
| 60 | attention_lstm | 4.68091 | 4.98835 | 0.204058 | 6.47929 | 39.9533 | 0.271828 | 7.39215 | 60.4114 | 99.5062 |
| 60 | persistence | 0.547946 | 0.781775 | 0.91935 | 2.6 | 3.66834 | 0.953063 | 3.2 | 4.51422 | 0.015625 |
| 60 | xgboost | 4.51224 | 4.91017 | 0.233613 | 5.91684 | 41.9364 | 0.306753 | 6.7934 | 66.0478 | 3.65313 |

### PLEIA energy

Target units: kWh per 10 minutes. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | attention_lstm | 0.129399 | 0.225896 | 0.524821 | 0.134636 | 1.74209 | 0.604825 | 0.170692 | 3.07251 | 96.775 |
| 10 | persistence | 0.127609 | 0.24188 | 0.560311 | 0.078125 | 2.09703 | 0.642879 | 0.125 | 3.78359 | 0.009375 |
| 10 | xgboost | 0.129501 | 0.219596 | 0.673806 | 0.239873 | 1.52636 | 0.791501 | 0.420517 | 2.05328 | 3.73438 |
| 30 | attention_lstm | 0.146718 | 0.248723 | 0.560008 | 0.190802 | 1.73581 | 0.649823 | 0.2351 | 2.97786 | 70.7625 |
| 30 | persistence | 0.131261 | 0.257542 | 0.571111 | 0.078125 | 2.18606 | 0.639245 | 0.125 | 3.96345 | 0.015625 |
| 30 | xgboost | 0.119862 | 0.225689 | 0.681659 | 0.204867 | 1.54511 | 0.739356 | 0.272906 | 2.56637 | 3.625 |
| 60 | attention_lstm | 0.153721 | 0.262858 | 0.576885 | 0.207309 | 1.80876 | 0.662744 | 0.258889 | 3.07409 | 61.4562 |
| 60 | persistence | 0.129989 | 0.257545 | 0.560715 | 0.078125 | 2.15652 | 0.640658 | 0.125 | 3.89904 | 0.003125 |
| 60 | xgboost | 0.128053 | 0.245035 | 0.630504 | 0.153972 | 1.7912 | 0.70213 | 0.222564 | 3.04277 | 3.59375 |

### RICO temperature

Target units: degrees C. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | attention_lstm | 2.68244 | 3.04918 | 0.104993 | 1.54375 | 40.5902 | 0.133985 | 1.91826 | 73.3614 | 108.338 |
| 5 | persistence | 0.0744708 | 0.12451 | 0.92821 | 0.4 | 0.601335 | 0.972388 | 0.6 | 0.780856 | 0.0125 |
| 5 | xgboost | 0.271294 | 0.435985 | 0.512517 | 0.349825 | 3.27808 | 0.679061 | 0.559561 | 4.75805 | 4.95 |
| 15 | attention_lstm | 2.85366 | 3.2314 | 0.0922241 | 1.52758 | 44.095 | 0.128109 | 2.00856 | 78.4763 | 98.4656 |
| 15 | persistence | 0.209382 | 0.33076 | 0.915359 | 1 | 1.6583 | 0.962932 | 1.6 | 2.14624 | 0.00625 |
| 15 | xgboost | 0.409784 | 0.590955 | 0.629775 | 0.793828 | 4.00633 | 0.801715 | 1.39157 | 4.60509 | 4.875 |
| 30 | attention_lstm | 3.02097 | 3.38963 | 0.0883266 | 1.70838 | 45.8384 | 0.108934 | 2.08158 | 83.5794 | 91.2938 |
| 30 | persistence | 0.389696 | 0.599428 | 0.921612 | 2 | 3.00143 | 0.964132 | 3 | 3.8624 | 0.009375 |
| 30 | xgboost | 0.662065 | 0.91626 | 0.650424 | 1.34465 | 6.06303 | 0.833494 | 2.43546 | 6.806 | 4.52187 |
| 60 | attention_lstm | 3.02622 | 3.46276 | 0.141432 | 2.11452 | 43.1457 | 0.165574 | 2.48572 | 78.287 | 55.0875 |
| 60 | persistence | 0.715675 | 1.04138 | 0.924188 | 3.6 | 5.10039 | 0.960851 | 5 | 6.39755 | 0.009375 |
| 60 | xgboost | 1.22584 | 1.82728 | 0.656486 | 2.6939 | 10.8788 | 0.856455 | 4.62313 | 11.9191 | 3.89375 |

### BDG2 electricity

Target units: kWh per hour. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | attention_lstm | 19.4531 | 36.6469 | 0.900375 | 97.5318 | 178.644 | 0.949209 | 141.768 | 240.426 | 816.75 |
| 60 | persistence | 20.988 | 41.6714 | 0.894919 | 115.806 | 207.414 | 0.946767 | 165.4 | 273.691 | 0.021875 |
| 60 | xgboost | 17.7485 | 34.9613 | 0.903054 | 93.5283 | 172.204 | 0.948839 | 136.776 | 232.529 | 9.375 |
| 180 | attention_lstm | 33.483 | 65.1879 | 0.905739 | 165.179 | 313.451 | 0.950208 | 237.287 | 434.381 | 494.931 |
| 180 | persistence | 42.8035 | 78.6988 | 0.897835 | 250 | 402.06 | 0.945987 | 344.2 | 504.752 | 0.028125 |
| 180 | xgboost | 28.2399 | 53.7454 | 0.906501 | 145.556 | 263.487 | 0.949284 | 207.159 | 357.853 | 8.7625 |
| 360 | attention_lstm | 41.0339 | 77.2062 | 0.906588 | 199.889 | 368.972 | 0.95213 | 283.207 | 509.328 | 298.534 |
| 360 | persistence | 73.284 | 119.93 | 0.897546 | 406.312 | 580.272 | 0.944226 | 498 | 703.035 | 0.021875 |
| 360 | xgboost | 34.1998 | 66.9261 | 0.907488 | 175.894 | 323.659 | 0.949423 | 248.866 | 444.362 | 8.7125 |

## Measured cost and acceptance

| model_seed | units | run_wall_seconds | run_cpu_seconds | validation_wall_seconds | resume_wall_seconds | peak_lifetime_rss_MiB |
| --- | --- | --- | --- | --- | --- | --- |
| 43 | 13 | 2784.46 | 2707.36 | 259.51 | 215.397 | 1186.92 |
| 44 | 13 | 3082.43 | 2987.31 | 280.574 | 220.931 | 1186.72 |
| 45 | 13 | 2688.63 | 2611.17 | 264.253 | 215.001 | 1187.03 |
| 46 | 13 | 2969.43 | 2895.89 | 255.988 | 215.938 | 1186.57 |

New model commands used **3.2014 wall hours** and **3.1116 process CPU hours**. Independent validation adds 17.67 wall minutes; zero-fit resume adds 14.45. Maximum lifetime peak RSS: 1187.03 MiB. These exclude preflight, diagnosis, orchestration, aggregation and publication. Separate actual command logs retain those costs. Nested phase timers must not be added twice.

CPU-only, one numerical/Torch thread, n_jobs=1, lazy batch256, the nonblocking 3 GiB launch reference, 256 MiB epoch floor and 8 GiB disk guard were preserved. All per-unit saved-stream arithmetic, finite-sample ranks, inner selection/epochs, serialized-model reconstruction, group-to-pooled squared-error arithmetic and immutable zero-fit resumes passed. No clipping, outer-result retuning or model-ranking gate was used. Original phase timing measurements stay attached to their original executions.

## Remaining work

Cumulative **70/195 paired units, 210/585 point cells and 420/1170 interval cells**. Fold 2 contains 65 paired units; five additional-fold units stay separate. **125 paired units / 1250 learned fits remain** in the matched core queue. Updated same-dataset planning scenario: 3.48–91.78 model-hours; this excludes preparation and verification and is not a confidence interval or deadline.

The [implementation readiness map](MATCHED_METHOD_READINESS_MAP.md) identifies the smallest next adapter package for broader conformal methods and causal alerting. Static own-model absolute-error split conformal does not complete CQR, EnbPI, DSCP, seasonal, operational, conditional-challenge, contamination/recovery or robustness obligations. Remaining outer folds are still necessary. RICO historical use and phase imbalance, recurring known BDG2 buildings, and the inspected historical periods limit claims. Full-study readiness remains false; no unlisted fits are launched.
