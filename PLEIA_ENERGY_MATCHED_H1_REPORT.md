# PLEIA-energy matched horizon-1 report

14 September 2026 local time. **Completed: actual run exit 0; all three point and six interval cells independently verified.** This is the authorized block-B `dif_cons` energy target (kWh per ten-minute interval), horizon 1, outer fold 0, model seed 42. The run performed **eight tuning and two final learned fits**; persistence performed no learned fitting. No remaining queue or conditional challenge was launched.

The evaluated implementation and frozen execution evidence were committed before the real run at `697d0e6e8a7de0a2fc55c98b8341117d789390ce`. Source SHA-256: `7335d436f6e4f8c2144de372e8817d036bae216426c157f5bbdc1eb921927955`. Protocol SHA-256: `4e6c91f9f835e0f37ebf21e4de23c4f65c9911d42d933912d0ce4fbf7500a4c3`. The [evidence index](review/matched_energy_h1_20260913/EVIDENCE_INDEX.md) links source, full fitted checkpoints, CSVs, exact commands and validation. The original forecasting pilot, all BDG2 results/abstentions, amendment-005 proposal and original completion matrix are preserved.

## Matched numerical results

| model | mae | rmse | coverage90 | mpiw90 | winkler90 | coverage95 | mpiw95 | winkler95 | model_phase_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence | 0.144251 | 3.49735 | 0.957009 | 1.01562 | 2.19487 | 0.975477 | 1.23438 | 3.45284 | 0.0099787 |
| xgboost | 0.101363 | 2.47409 | 0.959734 | 0.705199 | 1.38259 | 0.978908 | 0.926191 | 2.14996 | 5.92678 |
| attention_lstm | 0.101338 | 2.47552 | 0.961651 | 0.723483 | 1.38363 | 0.981936 | 0.975838 | 2.16099 | 420.6 |


MAE/RMSE, MPIW and Winkler are in the target's original kWh units; coverage is a proportion. `model_phase_seconds` sums tuning, final fitting (or persistence initialization), calibration and inference. It excludes preparation, artifact serialization/writes, validation, resume and process startup; nested fitting timers must not be added again.

On this single held-out block, Attention-LSTM minus XGBoost MAE is **-2.46737e-05 kWh** (LSTM/XGBoost ratio **0.999757**). This is a descriptive comparison for one target/horizon/fold/seed, not a completed multi-horizon superiority test or an independent prospective trial. Compare interval width together with empirical coverage and Winkler; nominal 90%/95% levels are not promises of achieved temporal or conditional coverage. No equivalence claim or formal multi-task test is made here.

## Candidate selection and interval ownership

| model | selected_candidate | final_epochs | independently_verified |
| --- | --- | --- | --- |
| persistence | 0 |  | True |
| xgboost | 0 |  | True |
| attention_lstm | 0 | 12.0 | True |


Candidate IDs are zero-based. XGBoost retains exactly 400 trees and depth 3 (candidate 0) or 5 (candidate 1), learning rate .05, subsample/column fraction .8 and the frozen remaining parameters. The actual estimator is `xgboost.sklearn.XGBRegressor`, histogram trees, squared-error objective, seed 42 and `n_jobs=1`; each checkpoint includes actual wrapper parameters and booster configuration. None-valued wrapper defaults remain bound to the recorded library version rather than silently introducing a fallback estimator.

Attention-LSTM retains hidden size 64, dropout .2, sequence length 24, batch 256, learning rate .001 (candidate 0) or .0005 (candidate 1), maximum 30 epochs and patience 5. It uses the existing attention architecture, Adam/MSE training, training-only channel/target normalization and deterministic seed convention. Early improvement must exceed the preserved literal 1e-6 convention. Candidate selection minimizes the equally weighted mean of two inner validation MAEs, with exact ties following candidate order. Final epochs are the ceiling of the selected candidate's mean best inner epoch. Calibration/test outcomes select neither candidates nor epochs. Saved inner predictions and complete inner training histories independently verify these choices.

All three models use the same fitting/calibration/test target IDs and permitted causal source variables. They retain different feature representations: 23 flat features versus 8 sequence channels over 24 steps; this is not a claim of identical tensor representations or effective history lengths. `target_lag_0` remains available to persistence and the flat models. Exact feature/channel names and preprocessing configuration are frozen in the protocol.

Each model's own 9,907 calibration absolute residuals determine its own symmetric interval. The one-based finite-sample ranks are `ceil((n+1)*level)`; there is no interpolated quantile, shared residual pool across models, adaptive recalibration or clipping. Both levels share their model fit. Saved calibration predictions are reproduced from each corresponding fitted artifact without fitting.

| model | nominal_level | n_calibration | rank | q | coverage | mpiw | winkler |
| --- | --- | --- | --- | --- | --- | --- | --- |
| persistence | 0.9 | 9907 | 8918 | 0.507812 | 0.957009 | 1.01562 | 2.19487 |
| persistence | 0.95 | 9907 | 9413 | 0.617188 | 0.975477 | 1.23438 | 3.45284 |
| xgboost | 0.9 | 9907 | 8918 | 0.3526 | 0.959734 | 0.705199 | 1.38259 |
| xgboost | 0.95 | 9907 | 9413 | 0.463095 | 0.978908 | 0.926191 | 2.14996 |
| attention_lstm | 0.9 | 9907 | 8918 | 0.361742 | 0.961651 | 0.723483 | 1.38363 |
| attention_lstm | 0.95 | 9907 | 9413 | 0.487919 | 0.981936 | 0.975838 | 2.16099 |


## Original support and data-quality diagnostics

Data hash `8bfbf2d874682c3d69016a5b2b5cd9586d83211bbc7d08f2d1563f696869362b` and role-bank hash `2c01da7ec94037d9b88d36fa91b52f5ec841f85bc648406f8796c190ac7c4c92` match the published no-fit proposal exactly. Membership includes one original energy series; its source group is Python `None`, with canonical CSV identity `None`. The original completed v1 streams serialized this as an empty field. The independently checked canonical streams restore the visible identifier while leaving every other column and all original checkpoint files unchanged. Eligible observed rows are 49,537; final fitting/calibration/test counts are **29,719 / 9,907 / 9,909**. All inner rows are confined to final fitting data, with strict target-before-next-origin purges.

| role | n | target_min | target_max |
| --- | --- | --- | --- |
| fit | 29719 | 2021-01-08 00:00:00 | 2021-08-02 09:00:00 |
| calibration | 9907 | 2021-08-02 09:20:00 | 2021-10-10 04:20:00 |
| test | 9909 | 2021-10-10 04:40:00 | 2021-12-18 00:00:00 |
| inner0_train | 9905 | 2021-01-08 00:00:00 | 2021-03-17 18:40:00 |
| inner0_validation | 9905 | 2021-03-17 19:00:00 | 2021-05-25 13:40:00 |
| inner1_train | 19810 | 2021-01-08 00:00:00 | 2021-05-25 13:40:00 |
| inner1_validation | 9907 | 2021-05-25 14:00:00 | 2021-08-02 09:00:00 |


| role | n | original_groups | zeros | negative_targets | minimum | maximum | adjacent_equal_targets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| calibration | 9907 | 1 | 557 | 0 | 0 | 326.531 | 996 |
| test | 9909 | 1 | 442 | 0 | 0 | 246.008 | 1619 |


Zero or repeated meter values are observations, not automatically labelled sensor failures. Source preprocessing/imputation and possible stalled/catch-up meter behaviour limit interpretation. This first unit keeps the original target and eligibility; the separately proposed keep/mask sensitivity analysis remains pending. There was no post-hoc removal of difficult periods, negative prediction clipping or interval truncation at zero.

| model | negative_point_predictions | minimum_point | negative_lower_90 | minimum_lower_90 | negative_lower_95 | minimum_lower_95 |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | 0 | 0 | 6965 | -0.507812 | 8229 | -0.617188 |
| xgboost | 0 | 0.0459724 | 4832 | -0.306627 | 5124 | -0.417123 |
| attention_lstm | 0 | 0.0352685 | 4835 | -0.326473 | 6064 | -0.45265 |


## Actual computational measurements

| model | tuning_seconds | final_fit_seconds | calibration_seconds | inference_seconds | process_cpu_seconds | baseline_rss_MiB | peak_rss_MiB | incremental_peak_rss_MiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence | 0 | 0.0006204 | 0.0052474 | 0.0041109 | 0.015625 | 367.621 | 367.719 | 0.0976562 |
| xgboost | 4.55873 | 1.18634 | 0.0904966 | 0.0912167 | 5.78125 | 368.32 | 482.891 | 114.57 |
| attention_lstm | 356.451 | 63.1565 | 0.405594 | 0.586597 | 394.531 | 473.773 | 594.023 | 120.25 |


The durable real command took **446.597 seconds**. Its lifetime process CPU was **418.219 seconds**; the action's sampled peak RSS was **594.023 MiB**, and Windows' lifetime RSS high-water mark was **595.316 MiB**. Fresh run preparation took **5.100 seconds**, separately from the **426.537 seconds** summed model phases. Atomic checkpoint writes took **6.384 seconds**; per-model artifact serialization is a separate phase in the detailed table. These nested/enclosing measurements must not be added indiscriminately.

The hardware was 12th Gen Intel(R) Core(TM) i7-12700H; the fitted models ran on CPU, one numerical/Torch thread and `n_jobs=1`, training/inference batches 256. Memory was sampled every 50 ms, so sampled phase peaks can miss short transients; lifetime RSS is reported separately. All three actual launches met the original 3 GiB reference: **True**. The later user instruction made that launch reference nonblocking, recorded in the new authorization; actual launch readings are published. The 256 MiB epoch floor and 8 GiB disk check were retained. No GPU cost or benefit is claimed.

Independent real-data audit and full saved-model prediction verification took **24.479 command seconds**; completed zero-fit resume took **8.742 command seconds**. These are excluded from model fit costs. Two separately preserved tiny integration versions used **20 synthetic learned fits total**, with reduced test-only architectures/candidates; their durations and the no-fit preparation/support commands, including one corrected checker failure, are in `command_measurements.csv`. They are not part of the ten real learned fits.

## Verification, completion overlay and next bounded proposal

All eight pre-fit regression checks passed. Both tiny integrations completed; their final saved-model predictions matched exactly. Two further no-fit CSV round-trip checks passed after identifying the Python-None serialization issue during the first real audit. Future exports now explicitly stringify group identifiers before writing, without altering prepared metadata, data/role hashes or any learned computation. The first audit's failure is retained. The corrected read-only audit uses the exact evaluated source archive and a separately hashed schema adapter, checks the original group against fresh metadata, and publishes canonical CSVs. This repair does **not invalidate the completed numerical results**, and no real learned fit was repeated. The updated export code requires a fresh source identity for future runs; it does not rewrite this completed run's protocol.

The real audit independently recalculated all point errors, absolute residuals, one-based ranks, bounds, coverage, MPIW, Winkler, selection and epochs. It checked training-only normalization and all common target IDs. Six saved-model checks (three models times calibration/test) passed at the predeclared absolute/relative tolerance 1e-7; exact observed discrepancies are published. All complete model payloads, metrics and run files remained unchanged during validation and completed resume. Source/configuration/data and checkpoint corruption rejection were covered by focused tests. The historical pilot passed read-only validation with zero refits. A second archive-based resume verifies that the published compatibility reader also performs zero fits; both resume costs are retained separately.

The [versioned completion overlay](smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/completion_overlay.csv) now has **4/195 paired units, 12/585 core point cells and 24/1,170 core interval cells completed**. **191 paired units / 573 point / 1,146 interval cells / 1,910 learned fits remain.** Seasonal and the broader interval-method/DSCP/robustness obligations remain separate and uncompleted; the original matrix/proposal was not edited.

The [updated queue](smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/remaining_queue_updated.csv) retains the original order after removing this completed unit. The unchanged planning factors [.5,3], applied to the range of four measured matched-unit model-phase totals and fitting-row ratios, give **6.72–76.86 model-hours** across the remaining core queue. This is a scheduling scenario, not a wall-time ETA or statistical interval; it excludes preparation, I/O, audit, differing channel counts/epochs and memory contention. RICO/BDG2 learned-model costs remain unmeasured.

**Single next bounded proposal:** obtain separate authorization and freeze/run **RICO horizon 5 / outer fold 2 / model seed 42**, all retained runs under the published whole-run memberships, with the same three models and frozen two-candidate grids. Its preliminary scenario is **48.7–556.8 model seconds**, to be replaced by actual measurement. No RICO, BDG2 queue unit or conditional challenge was launched. Full-study and scientific publication readiness remain **false**.
