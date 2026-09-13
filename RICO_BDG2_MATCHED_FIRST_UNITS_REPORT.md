# First matched RICO and BDG2 units

14 September 2026. **Both authorized experiments completed with actual exit 0.** RICO h5/f2/seed42 ran first; after its independent validation and zero-fit resume, BDG2 h1/f2/seed42 ran. Total: **16 tuning + 4 final learned fits**, six point and twelve interval cells. No tiny learned fits or additional queue units were run in this task.

Evaluated pre-fit commit: `350ef4fd1c92c12a982df2b8366023937515b65b`; source SHA-256 `cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e`. Both active protocols were frozen before either fit. The [joint manifest](review/matched_rico_bdg2_20260914/joint_pre_fit_manifest.json) binds the current handoff/authorization separately from the original runner/design provenance. The [evidence index](review/matched_rico_bdg2_20260914/EVIDENCE_INDEX.md) links all fitted artifacts, per-row streams, CSVs, resource logs and validation receipts.

## RICO: five-minute B.RTD3 temperature forecast

The values below are in degrees Celsius; coverage is a proportion. The pooled estimates weight target rows equally.

| model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | model_phase_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence | 0.0744708 | 0.12451 | 0.92821 | 0.4 | 0.601335 | 0.972388 | 0.6 | 0.780856 | 0.0083721 |
| xgboost | 0.243495 | 0.411486 | 0.567994 | 0.342401 | 2.86658 | 0.734699 | 0.562503 | 4.11148 | 5.76032 |
| attention_lstm | 2.22306 | 2.70229 | 0.16682 | 1.36187 | 33.3264 | 0.188104 | 1.50615 | 63.0626 | 157.731 |


Support: **12,932 fit / 4,452 calibration / 8,692 test rows**, respectively **61/21/41 complete original runs**. This is the first evaluation batch, outer fold 2, under amendment-005's five chronological run batches. It is not the old single-run test. Calibration residuals are pooled across earlier runs; new evaluation runs have no within-run calibration observations.

Persistence has the smallest observed errors on this test block. XGBoost and especially LSTM have substantial interval undercoverage: their 95% intervals cover approximately 73.47% and 18.81% of test targets, versus 97.24% for persistence. The much larger LSTM error is a validated outcome, not a reason to change candidates or rerun this unit. Phase differences and calibration-to-test shift limit transport of the pooled residual distribution; this descriptive result alone does not identify a causal explanation or a new implementation defect.

The test comprises one phase-1 run, six phase-3 runs and 34 phase-4 runs. All 41 were used in historical training under at least one legacy fold; they are not globally untouched holdouts. Within this new unit, fitting/calibration precede the evaluation runs. This post-inspection, phase-imbalanced evidence cannot establish prospective or phase-conditional coverage. A phase-stratified population interval is unavailable with only one phase-1 run; no phase is dropped to obtain one.

Phase summaries (sample-weighted within each phase):

| phase | model | nominal_level | original_runs | n | mae | rmse | coverage | mpiw | winkler |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | persistence | 0.9 | 1 | 212 | 0.0509434 | 0.0733305 | 0.995283 | 0.4 | 0.4 |
| 3 | persistence | 0.9 | 6 | 1272 | 0.0777516 | 0.130944 | 0.915094 | 0.4 | 0.62956 |
| 4 | persistence | 0.9 | 34 | 7208 | 0.0745838 | 0.124541 | 0.928552 | 0.4 | 0.602275 |
| 1 | persistence | 0.95 | 1 | 212 | 0.0509434 | 0.0733305 | 1 | 0.6 | 0.6 |
| 3 | persistence | 0.95 | 6 | 1272 | 0.0777516 | 0.130944 | 0.96934 | 0.6 | 0.813836 |
| 4 | persistence | 0.95 | 34 | 7208 | 0.0745838 | 0.124541 | 0.972114 | 0.6 | 0.780355 |
| 1 | xgboost | 0.9 | 1 | 212 | 0.0527736 | 0.0701323 | 0.990566 | 0.342401 | 0.343378 |
| 3 | xgboost | 0.9 | 6 | 1272 | 0.246034 | 0.312002 | 0.415881 | 0.342401 | 2.64785 |
| 4 | xgboost | 0.9 | 34 | 7208 | 0.248657 | 0.43227 | 0.582408 | 0.342401 | 2.9794 |
| 1 | xgboost | 0.95 | 1 | 212 | 0.0527736 | 0.0701323 | 1 | 0.562503 | 0.562503 |
| 3 | xgboost | 0.95 | 6 | 1272 | 0.246034 | 0.312002 | 0.60456 | 0.562503 | 3.09678 |
| 4 | xgboost | 0.95 | 34 | 7208 | 0.248657 | 0.43227 | 0.749861 | 0.562503 | 4.39492 |
| 1 | attention_lstm | 0.9 | 1 | 212 | 0.131521 | 0.145095 | 1 | 1.36187 | 1.36187 |
| 3 | attention_lstm | 0.9 | 6 | 1272 | 2.03348 | 2.27409 | 0.0691824 | 1.36187 | 28.917 |
| 4 | attention_lstm | 0.9 | 34 | 7208 | 2.31803 | 2.80938 | 0.159545 | 1.36187 | 35.0447 |
| 1 | attention_lstm | 0.95 | 1 | 212 | 0.131521 | 0.145095 | 1 | 1.50615 | 1.50615 |
| 3 | attention_lstm | 0.95 | 6 | 1272 | 2.03348 | 2.27409 | 0.072327 | 1.50615 | 53.9362 |
| 4 | attention_lstm | 0.95 | 34 | 7208 | 2.31803 | 2.80938 | 0.184656 | 1.50615 | 66.4836 |


Every original run also has a separate row in [group_metrics.csv](smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/group_metrics.csv). The distinctly labelled equal-run diagnostics are in [equal_group_diagnostics.csv](smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/equal_group_diagnostics.csv). Neither is relabelled as the pooled result.

## BDG2: one-hour energy forecast

Errors, widths and Winkler scores are in kWh for the hourly observations; coverage is a proportion.

| model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | model_phase_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence | 20.988 | 41.6714 | 0.894919 | 115.806 | 207.414 | 0.946767 | 165.4 | 273.691 | 0.0274112 |
| xgboost | 17.7543 | 34.9583 | 0.903753 | 93.588 | 172.169 | 0.947835 | 135.844 | 232.592 | 10.0366 |
| attention_lstm | 19.2083 | 36.035 | 0.902569 | 98.6019 | 176.577 | 0.949625 | 141.039 | 236.977 | 1529.5 |


Support: **51,664 fit / 17,370 calibration / 34,640 test rows** across the same ten retained buildings. Chronological splits and all flat-feature histories/lazy sequences remain within buildings. This is forecasting in known buildings, not unseen-building generalization. Pooled errors are sample-weighted and can be dominated by larger loads. Each building's 90%/95% point and interval summaries are published separately in `group_metrics.csv`; equal-building diagnostics remain separate.

XGBoost has the smallest observed MAE/RMSE and Winkler scores on this unit. LSTM improves point errors over persistence but has larger errors, wider intervals and much higher measured cost than XGBoost. Both learned models are close to the nominal interval levels in the pooled test; this does not establish coverage for each building or for unseen buildings. These are descriptive one-fold/one-seed results, not a general model ranking.

## Frozen construction and selected configurations

Persistence reads the actual last-observation feature `target_lag_0` and has no learned fit. XGBoost is the fitted `xgboost.sklearn.XGBRegressor`, histogram trees, squared-error objective, 400 trees, depth 3 or 5, learning rate .05, subsample/column fraction .8, seed42 and `n_jobs=1`, with all remaining pinned parameters unchanged. Full wrapper and actual booster configurations are saved.

Attention-LSTM retains hidden64/dropout.2/batch256, 24-step sequences, candidate learning rates .001/.0005, maximum30 epochs/patience5, Adam/MSE and training-only channel/target normalization. Both learned models use two purged inner folds, equally weighted original-unit validation MAE and exact candidate-order ties. LSTM improvement must exceed 1e-6; final epochs equal the ceiling of the selected candidate's mean best inner epoch. Final calibration/test results select no hyperparameters, epochs or preprocessing.

Candidate IDs are zero-based (XGBoost 0=depth3, 1=depth5; LSTM 0=.001, 1=.0005):

| dataset | model | selected_candidate | final_epochs |
| --- | --- | --- | --- |
| rico | persistence | 0 |  |
| rico | xgboost | 1 |  |
| rico | attention_lstm | 1 | 18.0 |
| bdg2 | persistence | 0 |  |
| bdg2 | xgboost | 1 |  |
| bdg2 | attention_lstm | 0 | 29.0 |


Each fitted model supplies its own absolute calibration residuals. The symmetric radius is the one-based ordered residual at `ceil((n+1)*level)`. No interpolated/clipped rank, residual sharing, recalibration or interval truncation is used. The 90%/95% intervals share one model fit. Insufficient rank remains an explicit unavailable status; both actual units have sufficient calibration support.

| dataset | model | n_calibration | rank90 | q90 | rank95 | q95 |
| --- | --- | --- | --- | --- | --- | --- |
| rico | persistence | 4452 | 4008 | 0.2 | 4231 | 0.3 |
| rico | xgboost | 4452 | 4008 | 0.171201 | 4231 | 0.281252 |
| rico | attention_lstm | 4452 | 4008 | 0.680936 | 4231 | 0.753073 |
| bdg2 | persistence | 17370 | 15634 | 57.903 | 16503 | 82.7 |
| bdg2 | xgboost | 17370 | 15634 | 46.794 | 16503 | 67.922 |
| bdg2 | attention_lstm | 17370 | 15634 | 49.3009 | 16503 | 70.5194 |


All models share exact target IDs and permitted causal variables. Flat features and 24-step sequence channels are different representations and effective histories. Their names, physical frequency and exact role dates are in the protocols and [fresh_role_support.csv](review/matched_rico_bdg2_20260914/fresh_role_support.csv). The generic support `target` field is null because these adapters store target selection in nested configuration/source; RICO explicitly resolves `rico.target_column=B.RTD3`, while BDG2's electricity loader and retained building IDs are bound by the source/configuration and data hashes.

## Actual costs and verification

| dataset | model | tuning_seconds | final_fit_seconds | calibration_seconds | inference_seconds | inference_rows_per_second | process_cpu_seconds | baseline_rss_MiB | peak_rss_MiB | incremental_peak_rss_MiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rico | persistence | 0 | 0.0005202 | 0.0039245 | 0.0039274 | 2.21317e+06 | 0.015625 | 412.789 | 412.953 | 0.164062 |
| rico | xgboost | 3.8201 | 1.62327 | 0.11665 | 0.200288 | 43397.5 | 5.48438 | 411.984 | 524.246 | 112.262 |
| rico | attention_lstm | 114.358 | 42.6571 | 0.230838 | 0.485597 | 17899.6 | 151.984 | 513.941 | 620.031 | 106.09 |
| bdg2 | persistence | 0 | 0.0006069 | 0.0082996 | 0.0185047 | 1.87196e+06 | 0.03125 | 431.039 | 431.621 | 0.582031 |
| bdg2 | xgboost | 6.68644 | 2.72521 | 0.209485 | 0.415462 | 83377.2 | 9.67188 | 433.238 | 548.18 | 114.941 |
| bdg2 | attention_lstm | 618.077 | 901.599 | 3.22261 | 6.60563 | 5244.01 | 1391.42 | 538.59 | 650.383 | 111.793 |


| dataset | command_seconds | process_cpu_seconds | preparation_seconds | preparation_peak_rss_MiB | action_peak_rss_MiB | lifetime_peak_rss_MiB | validation_seconds | resume_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rico | 183.966 | 175.531 | 9.97719 | 436.969 | 620.031 | 621.879 | 29.741 | 27.2861 |
| bdg2 | 1587.35 | 1443.11 | 14.9093 | 920.418 | 920.23 | 983.934 | 45.1975 | 24.6434 |


The environment is the existing CPU-only Intel i7-12700H setup, one numerical/Torch thread and `n_jobs=1`. The 3 GiB launch reference is nonblocking and actual readings are in `model_costs.csv`; the 256 MiB epoch floor and 8 GiB free-disk checks remain. Memory samples are 50 ms apart and can miss short peaks; lifetime high-water marks are separate. Model phases exclude preparation, serialization, checkpoint writing, validation/resume and interpreter startup. Nested per-fit timers must not be added again to enclosing tuning/final phases. Detailed CPU/memory/throughput and serialization/I/O records are published.

For **each unit**, independent arithmetic passed all three point and six interval cells, exact own-residual ranks/bounds, common targets, candidate and epoch selection, training-only normalization and six saved-model calibration/test prediction checks at the declared 1e-7 absolute/relative tolerance. Completed resume forbade all learned fitting routes, performed zero new fits and left every run file unchanged. Group-weighted recomputation independently reproduces the pooled metrics. Passing integrity checks does not certify nominal coverage.

The only production repair was a narrow no-fit guard exception for the exact deterministic `GroupPartitioner.fit` method, demonstrated necessary by failed RICO readiness. Fifteen no-fit regression checks passed; no synthetic fits were repeated. Initial protocols and the failed readiness remain preserved. A separate helper's wrong-working-directory attempt entered a download path and was stopped; its log and unused downloads are preserved, and the corrected helper uses existing project data. Both repairs preceded all real fitting, invalidated no completed numerical result and caused no real refit. See [pre-fit record](review/matched_rico_bdg2_20260914/PRE_FIT_EXECUTION.md) and the successful/failed command ledger.

The combined-report v1 attempt subsequently failed on the older temperature pilot's provenance layout: its executed source hash is stored in the checkpoint specification, not at the top of the protocol. The corrected v2 reader uses that original specification and verifies the original protocol digest. The failed partial report, exact failed helper source and [reporting attempt exits](review/matched_rico_bdg2_20260914/reporting_attempts.json) are preserved. This reporting-only repair changes no source identity or numerical result and triggers no fitting.

Negative points/lower bounds are counted per original group in `group_metrics.csv`. Original zero/repeated/negative targets are retained in `target_diagnostics.csv`; no post-hoc cleaning or clipping was applied. Frozen causal imputation, phase/load shifts and temporal dependence limit interpretation.

## Available evidence across four settings

The following descriptive contrasts preserve each target's units/horizon/fold/seed. LSTM-minus-XGBoost errors and interval scores are paired on the same rows. No Celsius/kWh errors are averaged into a global ranking. The uneven six-unit pilot set is not a completed four-task study or five-seed inference; no general superiority/equivalence conclusion follows.

| dataset | horizon | outer_fold | model_seed | target_units | mae_lstm_minus_xgboost | rmse_lstm_minus_xgboost | coverage95_lstm_minus_xgboost | mpiw95_lstm_minus_xgboost | winkler95_lstm_minus_xgboost | lstm_to_xgboost_model_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | 2 | 42 | kWh per hour | 1.45398 | 1.07662 | 0.00178984 | 5.19472 | 4.38547 | 152.393 |
| pleia | 1 | 0 | 42 | degrees C | 0.116573 | 0.133312 | -0.0135258 | 0.396875 | 0.609057 | 57.5142 |
| pleia | 3 | 0 | 42 | degrees C | 0.0918638 | 0.149344 | 0.0167558 | 0.555051 | 0.967717 | 55.1775 |
| pleia | 6 | 0 | 42 | degrees C | 0.487424 | 0.581842 | -0.0745937 | 1.1183 | 4.6778 | 33.2727 |
| pleia_energy | 1 | 0 | 42 | kWh per 10 minutes | -2.46737e-05 | 0.00143469 | 0.00302755 | 0.049647 | 0.0110317 | 70.966 |
| rico | 5 | 2 | 42 | degrees C | 1.97957 | 2.29081 | -0.546595 | 0.943643 | 58.9511 | 27.3824 |


[all_four_settings.csv](smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/all_four_settings.csv) includes all 18 model rows and both interval levels, including the three historical temperature horizons and energy h1. [evidence_reuse_ledger.csv](smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/evidence_reuse_ledger.csv) retains their original source/protocol/run-tree hashes; no historical model was refitted. Interval width must be read with achieved coverage and Winkler, not in isolation.

The new completion overlay records **6/195 paired units, 18/585 point cells and 36/1,170 interval cells complete**, leaving **189 units / 1,890 learned fits**. Original matrices and earlier overlays are unchanged. Seasonal, broader interval methods, DSCP, operational/conditional challenge and robustness remain separate obligations.

The [concrete next-batch proposal](MATCHED_NEXT_BATCH_PROPOSAL.md) enumerates twelve units selected for coverage and feasibility. It is **not authorized or launched** by this task. Full-study readiness remains false.

## Exact target-time support

| dataset | role | n | groups | target_min | target_max |
| --- | --- | --- | --- | --- | --- |
| rico | fit | 12932 | 61 | 2023-07-26 15:29:00 | 2023-08-07 23:00:00 |
| rico | calibration | 4452 | 21 | 2023-08-07 23:29:00 | 2023-08-12 03:00:00 |
| rico | test | 8692 | 41 | 2023-08-12 07:29:00 | 2024-02-04 11:00:00 |
| bdg2 | fit | 51664 | 10 | 2016-01-08 00:00:00 | 2016-08-12 01:00:00 |
| bdg2 | calibration | 17370 | 10 | 2016-08-12 04:00:00 | 2016-10-23 12:00:00 |
| bdg2 | test | 34640 | 10 | 2016-10-23 14:00:00 | 2017-03-17 08:00:00 |


## Verification and negative-output totals

| dataset | actual_exit | point_cells | interval_cells | saved_model_checks | maximum_prediction_difference | completed_resume_fits | all_run_files_unchanged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rico | 0 | 3 | 6 | 6 | 0 | 0 | True |
| bdg2 | 0 | 3 | 6 | 6 | 0 | 0 | True |


| dataset | model | nominal_level | negative_points | negative_lower_bounds |
| --- | --- | --- | --- | --- |
| bdg2 | attention_lstm | 0.9 | 667 | 10565 |
| bdg2 | attention_lstm | 0.95 | 667 | 12156 |
| bdg2 | persistence | 0.9 | 0 | 11064 |
| bdg2 | persistence | 0.95 | 0 | 12241 |
| bdg2 | xgboost | 0.9 | 13 | 10152 |
| bdg2 | xgboost | 0.95 | 13 | 11622 |
| rico | attention_lstm | 0.9 | 0 | 0 |
| rico | attention_lstm | 0.95 | 0 | 0 |
| rico | persistence | 0.9 | 0 | 0 |
| rico | persistence | 0.95 | 0 | 0 |
| rico | xgboost | 0.9 | 0 | 0 |
| rico | xgboost | 0.95 | 0 | 0 |


Point predictions are shared across levels; do not count the two repeated point diagnostics as different forecasts. Bounds and point predictions remain unclipped.
