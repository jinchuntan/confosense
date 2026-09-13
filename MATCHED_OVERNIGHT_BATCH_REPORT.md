# Matched overnight batch completion report

All **12 authorized paired units completed**, actual exits 0: **96 tuning +24 final learned fits**, **36 point /72 interval cells**, **72 saved-model prediction checks**, and **12 zero-fit completed resumes**. Maximum observed prediction discrepancy: 0. Analysis performed zero fits.

All twelve protocols were frozen and checked before fitting. Scientific source is unchanged from d95405a: `cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e`. The evaluated orchestration commit is recorded in [evaluated_commit.json](review/matched_overnight_20260914/evaluated_commit.json). [Evidence index](review/matched_overnight_20260914/EVIDENCE_INDEX.md) and [progress/restart record](review/matched_overnight_20260914/PROGRESS_AND_RESTART.md) link exact commands and identities.

## Numerical findings for the comparable slice

- **PLEIA temperature:** persistence has the smallest MAE at all three horizons. At 60 minutes its MAE is 0.5479 °C, versus 4.2797 for XGBoost and 4.4636 for LSTM. Their 95% coverages are 95.31%, 31.08% and 27.49%. LSTM has lower Winkler scores than XGBoost at 30/60 minutes despite worse point errors and lower coverage; at 60 minutes the 95% scores are 56.8227 versus 65.6096. This trade-off does not establish adequate intervals.

- **PLEIA energy:** LSTM has slightly lower 10-minute MAE (0.120468 versus 0.123773 kWh), but worse RMSE and 95% Winkler (3.1671 versus 2.0013). Its narrower 95% interval (0.1423 versus 0.4104 kWh MPIW) covers only 60.31%, versus 80.29% for XGBoost. At 60 minutes, XGBoost has lower MAE (0.128768 versus 0.156833); all three models remain below nominal 95% coverage.

- **RICO:** persistence has the smallest point errors at all four horizons. At 60 minutes, persistence/XGBoost/LSTM MAE is 0.7157/1.1955/2.6363 °C. LSTM is narrower than XGBoost at 30/60 minutes but has severe undercoverage: at 60 minutes, MPIW is 2.2582 versus 3.8751 °C, coverage is 20.34% versus 81.56%, and Winkler is 67.4603 versus 13.2103.

- **BDG2:** XGBoost has the smallest MAE/RMSE and Winkler scores at all three fold-2 horizons. At six hours, persistence/XGBoost/LSTM MAE is 73.284/34.160/39.965 kWh. XGBoost/LSTM 95% MPIW is 248.751/276.343, Winkler 442.884/516.184, and coverage 94.98%/94.92%. LSTM uses 43.10× measured model-phase CPU. Pooled near-nominal coverage is not a per-building or prospective guarantee.

These are descriptive outcomes for the frozen fold-2/seed-42 slice, with dependent horizons and different target units. The extra fold and older pilots remain separate. No test result changed the experiment.

## Comparable fold-2 / seed-42 horizon results

These 13 task/horizon combinations use the eleven new fold-2 units plus the preserved RICO h5 and BDG2 h1 units. The new BDG2 h1/fold1 and older fold0 pilots remain in a [separate table](smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/analysis_v1/additional_folds_comparison.csv). Units, folds and dependent horizons are not pooled into a global ranking.

### PLEIA temperature

Errors, widths and Winkler scores: degrees C.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | model_phase_seconds | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | attention_lstm | 3.03129 | 3.33861 | 0.201272 | 3.44086 | 32.573 | 0.276875 | 4.1924 | 51.0326 | 211.043 | 206.203 |
| 10 | persistence | 0.239376 | 0.336674 | 0.94085 | 1.2 | 1.54723 | 0.965176 | 1.6 | 1.90443 | 0.0161262 | 0.015625 |
| 10 | xgboost | 2.26181 | 2.66629 | 0.256182 | 2.11076 | 28.7204 | 0.334107 | 2.68884 | 47.7803 | 4.07532 | 3.90625 |
| 30 | attention_lstm | 3.76055 | 4.08624 | 0.202988 | 4.64738 | 37.2246 | 0.252751 | 5.30735 | 60.2676 | 165.019 | 161.359 |
| 30 | persistence | 0.391592 | 0.565536 | 0.936308 | 2 | 2.66519 | 0.960028 | 2.4 | 3.27009 | 0.0083217 | 0 |
| 30 | xgboost | 3.52336 | 3.91737 | 0.213788 | 3.93511 | 38.4648 | 0.282931 | 4.71318 | 62.054 | 3.71029 | 3.71875 |
| 60 | attention_lstm | 4.46356 | 4.753 | 0.209347 | 6.3126 | 37.0383 | 0.274856 | 7.08433 | 56.8227 | 102.003 | 99.7188 |
| 60 | persistence | 0.547946 | 0.781775 | 0.91935 | 2.6 | 3.66834 | 0.953063 | 3.2 | 4.51422 | 0.0077634 | 0.015625 |
| 60 | xgboost | 4.27973 | 4.69144 | 0.244575 | 5.5327 | 40.7523 | 0.31079 | 6.30339 | 65.6096 | 3.69959 | 3.57812 |

### PLEIA energy

Errors, widths and Winkler scores: kWh per 10 minutes.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | model_phase_seconds | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | attention_lstm | 0.120468 | 0.22024 | 0.54194 | 0.109886 | 1.75991 | 0.603109 | 0.142328 | 3.16709 | 92.4616 | 89.8906 |
| 10 | persistence | 0.127609 | 0.24188 | 0.560311 | 0.078125 | 2.09703 | 0.642879 | 0.125 | 3.78359 | 0.0078944 | 0.015625 |
| 10 | xgboost | 0.123773 | 0.214417 | 0.66882 | 0.21224 | 1.52126 | 0.802867 | 0.410432 | 2.00131 | 3.7429 | 3.5 |
| 30 | attention_lstm | 0.127527 | 0.240236 | 0.56556 | 0.132334 | 1.78741 | 0.65913 | 0.185932 | 3.0861 | 76.1045 | 73.8438 |
| 30 | persistence | 0.131261 | 0.257542 | 0.571111 | 0.078125 | 2.18606 | 0.639245 | 0.125 | 3.96345 | 0.0084585 | 0 |
| 30 | xgboost | 0.119472 | 0.226146 | 0.682043 | 0.198445 | 1.55319 | 0.735944 | 0.260202 | 2.61166 | 3.6441 | 3.57812 |
| 60 | attention_lstm | 0.156833 | 0.262396 | 0.588069 | 0.209189 | 1.77432 | 0.644898 | 0.23959 | 3.13759 | 60.0727 | 58.9531 |
| 60 | persistence | 0.129989 | 0.257545 | 0.560715 | 0.078125 | 2.15652 | 0.640658 | 0.125 | 3.89904 | 0.0073406 | 0 |
| 60 | xgboost | 0.128768 | 0.246122 | 0.616938 | 0.147875 | 1.81398 | 0.684768 | 0.210331 | 3.10888 | 3.7444 | 3.70312 |

### RICO temperature

Errors, widths and Winkler scores: degrees C.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | model_phase_seconds | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | attention_lstm | 2.22306 | 2.70229 | 0.16682 | 1.36187 | 33.3264 | 0.188104 | 1.50615 | 63.0626 | 157.731 | 151.984 |
| 5 | persistence | 0.0744708 | 0.12451 | 0.92821 | 0.4 | 0.601335 | 0.972388 | 0.6 | 0.780856 | 0.0083721 | 0.015625 |
| 5 | xgboost | 0.243495 | 0.411486 | 0.567994 | 0.342401 | 2.86658 | 0.734699 | 0.562503 | 4.11148 | 5.76032 | 5.48438 |
| 15 | attention_lstm | 2.38261 | 2.86615 | 0.152258 | 1.38662 | 36.2293 | 0.177976 | 1.55236 | 68.4665 | 125.75 | 123.172 |
| 15 | persistence | 0.209382 | 0.33076 | 0.915359 | 1 | 1.6583 | 0.962932 | 1.6 | 2.14624 | 0.0079055 | 0.015625 |
| 15 | xgboost | 0.42446 | 0.616662 | 0.601666 | 0.75426 | 4.46071 | 0.81176 | 1.52781 | 4.6402 | 5.45046 | 5.3125 |
| 30 | attention_lstm | 2.64775 | 3.09428 | 0.115951 | 1.47046 | 40.7209 | 0.135777 | 1.83603 | 73.9256 | 97.1437 | 94.6094 |
| 30 | persistence | 0.389696 | 0.599428 | 0.921612 | 2 | 3.00143 | 0.964132 | 3 | 3.8624 | 0.0077286 | 0.015625 |
| 30 | xgboost | 0.645699 | 0.905418 | 0.688405 | 1.43313 | 5.65221 | 0.849485 | 2.41651 | 6.75145 | 4.63065 | 4.53125 |
| 60 | attention_lstm | 2.63627 | 3.1144 | 0.175392 | 1.97962 | 36.8427 | 0.203356 | 2.25822 | 67.4603 | 49.5516 | 48.7656 |
| 60 | persistence | 0.715675 | 1.04138 | 0.924188 | 3.6 | 5.10039 | 0.960851 | 5 | 6.39755 | 0.0072464 | 0.015625 |
| 60 | xgboost | 1.1955 | 1.78819 | 0.642069 | 2.53537 | 10.7454 | 0.815597 | 3.87513 | 13.2103 | 3.82362 | 3.75 |

### BDG2 electricity

Errors, widths and Winkler scores: kWh per hour.

| physical_minutes | model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | model_phase_seconds | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | attention_lstm | 19.2083 | 36.035 | 0.902569 | 98.6019 | 176.577 | 0.949625 | 141.039 | 236.977 | 1529.5 | 1391.42 |
| 60 | persistence | 20.988 | 41.6714 | 0.894919 | 115.806 | 207.414 | 0.946767 | 165.4 | 273.691 | 0.0274112 | 0.03125 |
| 60 | xgboost | 17.7543 | 34.9583 | 0.903753 | 93.588 | 172.169 | 0.947835 | 135.844 | 232.592 | 10.0366 | 9.67188 |
| 180 | attention_lstm | 32.8997 | 65.8941 | 0.904388 | 163.775 | 316.764 | 0.949769 | 236.053 | 441.107 | 529.542 | 518.938 |
| 180 | persistence | 42.8035 | 78.6988 | 0.897835 | 250 | 402.06 | 0.945987 | 344.2 | 504.752 | 0.0294164 | 0.03125 |
| 180 | xgboost | 26.9694 | 52.1084 | 0.906033 | 139.05 | 256.06 | 0.950115 | 201.509 | 349.485 | 9.91255 | 9.625 |
| 360 | attention_lstm | 39.9648 | 77.6988 | 0.905254 | 197.425 | 372.377 | 0.949163 | 276.343 | 516.184 | 398.228 | 387.891 |
| 360 | persistence | 73.284 | 119.93 | 0.897546 | 406.312 | 580.272 | 0.944226 | 498 | 703.035 | 0.0201202 | 0.03125 |
| 360 | xgboost | 34.1603 | 66.7785 | 0.908661 | 177.189 | 322.912 | 0.949827 | 248.751 | 442.884 | 9.26431 | 9 |

## Actual computational measurements

| dataset | horizon | outer_fold | command_seconds | process_cpu_seconds | preparation_seconds | validation_seconds | resume_seconds | lifetime_peak_rss_MiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia_energy | 1 | 2 | 110.986 | 105.188 | 3.44221 | 31.2058 | 9.68546 | 592.508 |
| pleia_energy | 3 | 2 | 93.3911 | 89.1562 | 3.47918 | 11.8869 | 8.74119 | 610.359 |
| pleia_energy | 6 | 2 | 77.4838 | 74.3438 | 3.4665 | 11.281 | 8.46922 | 609.43 |
| rico | 15 | 2 | 150.439 | 144.984 | 9.89595 | 24.8277 | 21.9542 | 622.637 |
| rico | 30 | 2 | 119.675 | 115.312 | 8.94737 | 25.8121 | 21.8657 | 629.047 |
| rico | 60 | 2 | 70.4713 | 67.7344 | 8.74211 | 23.0052 | 21.4364 | 612.527 |
| bdg2 | 3 | 2 | 578.645 | 564.828 | 16.4124 | 27.8934 | 21.8956 | 984.559 |
| bdg2 | 6 | 2 | 441.966 | 429.062 | 13.891 | 27.6223 | 21.3344 | 984.543 |
| bdg2 | 1 | 1 | 1191.66 | 1160.16 | 15.8688 | 31.6065 | 23.348 | 983.328 |
| pleia | 1 | 2 | 234.542 | 227.438 | 8.31026 | 14.7389 | 12.5482 | 1186.22 |
| pleia | 3 | 2 | 185.809 | 180.25 | 6.91818 | 14.9608 | 12.1545 | 1186.97 |
| pleia | 6 | 2 | 122.987 | 118.594 | 7.21129 | 15.037 | 12.721 | 1186.52 |

Total new-run wall time: **56.30 minutes**; process lifetime CPU: **54.62 minutes**. Validation adds 4.33 wall minutes and completed resume 3.27 minutes. These sums exclude freeze/readiness, orchestration, reporting and publication. [Command attempts](smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/analysis_v1/command_attempts.csv) preserve separate measured phases; do not add nested fit timers twice.

CPU-only, one numerical/Torch thread, n_jobs=1, lazy batch256, nonblocking 3 GiB launch reference, 256 MiB epoch floor and 8 GiB disk checks were retained. Sampled 50 ms memory peaks can miss brief allocations; lifetime high-water marks are separate. Original temperature pilot per-model CPU was not recorded and remains explicitly unmeasured; it is not inferred from wall time.

## Integrity and supported interpretation

Independent saved-stream arithmetic, exact own-model residual order statistics, tuning and epoch reconstruction, training-only normalization, matching target identities, saved-model reconstruction and immutable completed resume all passed. Group-to-pooled RMSE is reconstructed from count-weighted squared errors, never an average of group RMSE. [Group](smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/analysis_v1/group_metrics.csv), [RICO phase](smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/analysis_v1/rico_phase_metrics.csv) and [equal-group diagnostic](smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/analysis_v1/equal_group_diagnostics.csv) tables remain separate.

PLEIA-energy zeros, repeated/stall/catch-up values and all negative predictions/bounds remain unaltered. Target/negative-output diagnostics are published. RICO uses whole chronological acquisition runs: the fold-2 test has one phase-1 run, six phase-3 runs and 34 phase-4 runs, with historical training reuse. This cannot establish phase-conditional population coverage. BDG2 evaluates ten recurring known buildings, not unseen buildings. Single-seed, temporally dependent multi-horizon comparisons do not establish statistical superiority/equivalence or prospective/conditional coverage. Undercoverage remains a reported result.

The initial new preparation helper stopped after a successful first freeze/readiness because its in-memory authorization keys were tuples rather than JSON lists. The helper now reads the unchanged saved authorization; successful checks were reused and no model had been fitted. Its original traceback and retry log are preserved. No scientific-source repair or result invalidation occurred.

The first coordinator subsequently exited 1 after Windows denied an atomic progress-file replacement. The independent PLEIA-temperature h1 worker finished with exit 0. A bounded bookkeeping retry was verified with injected transient/persistent denials and committed separately at bdfb651; restart adopted the actual success receipt and continued validation. All affected run files remain byte-identical and no learned fit was repeated. See [recovery record](review/matched_overnight_20260914/RECOVERY_PROGRESS_WRITE.md) and [independent preservation check](smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/analysis_v1/coordinator_recovery_validation.json). Twenty-six distinct regression/orchestration checks passed, with zero tiny learned fits.

The models use identical eligible target IDs within a unit and the frozen permitted causal variables, but flat features and 24-step sequences are different representations and effective histories. The protocol records their separate schemas. Candidate selection, final epochs, estimator identity and support counts are explicit in the combined CSV; this does not isolate architecture from representation.

## Completion and outstanding work

**18/195 paired units; 54/585 point cells; 108/1170 interval cells. 177 paired units /1,770 learned fits remain** in the matched core queue. The original matrix and prior completion records are preserved. The updated same-dataset timing scenario is 5.77–113.11 model-hours, excluding preparation/I/O/verification; this is a planning range, not a deadline.

The next concrete study stage is the matched fold-2 all-horizon slice at model seed 43: thirteen paired units (PLEIA temperature h1/3/6, PLEIA energy h1/3/6, RICO h5/15/30/60 and BDG2 h1/3/6), 104 tuning+26 final learned fits, 39 point/78 interval cells, with fresh authorization/freeze/readiness and the same per-unit checks. This is a proposed bounded replication stage; it has not been launched. Further seeds/folds, seasonal baselines, broader CQR/EnbPI/DSCP methods, operational selection/recalibration, conditional challenge, contamination/recovery and robustness remain separate obligations. The dissertation/full study is not complete or publication-ready.

The resumed coordinator exited **0** after the recorded progress-write recovery. Calendar time from its first launch through automatic reporting was **69.89 minutes**, including the recovery gap. Both outer command attempts and their measured scopes are in [the delivery timing record](review/matched_overnight_20260914/delivery_v1/coordinator_timing.json). Noninteractive Git authentication failed; the authorized review publication was completed using the existing signed-in GitHub Desktop workflow, followed by remote verification.

[Final delivery validation](review/matched_overnight_20260914/delivery_v1/delivery_validation.json), [selected model configurations](review/matched_overnight_20260914/delivery_v1/selected_configurations.csv), and the [unlaunched thirteen-unit seed-43 proposal](review/matched_overnight_20260914/delivery_v1/proposed_seed43_replication.csv) provide the corresponding machine-readable records.
