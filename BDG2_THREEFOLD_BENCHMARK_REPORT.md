# Three-fold BDG2 reduced-grid benchmark, model seed 42

**Primary operational feasibility: 0 of 3 outer units selected a configuration; 3 abstained.** These decisions come only from the two inner folds. All three original study commands completed with **exit status 0**. Both new units passed independent saved-stream reconstruction and normal completed-unit resume with **zero new fits**. Full-study readiness remains **false**.

This benchmark combines preserved fold 2 with the explicitly authorized fold-1 then fold-0 runs. It evaluates ten known BDG2 buildings, one-hour forecasts, model seed 42, five synthetic catalogue seeds and the identical nine reduced-grid candidates. It is not the full candidate/method, multi-task or five-model-seed study. The [evidence index](review/bdg2_threefold_20260913/EVIDENCE_INDEX.md) links the complete code, CSVs, source archives, commands and reconstruction instructions.

## Identity, freeze and preservation

Entry/publication ancestor: `d63251b75f5c70c4d51c19456fbec6724e712516`. The repair, compatibility evidence, both-unit manifest and paired-analysis code were committed before either new fit at **`18e5db5f2d81ed641ae90c5e257e512cf7ebbcc7`**. Both new units evaluated source SHA-256 **`203f3babf66c98ac072ad450abec5ea7ce3d60473f02708fa64ac2102ea3f7c9`**. Fold 2 retains historical evaluated commit `ef9a8a9525bafea00a12b5c1327aadec071eab91` and source `8218d9f461811fa9075c2966c394cae2344ae61f073887ff356af82025c8f4e4`. Exact archived bytes avoid line-ending ambiguity.

The [joint manifest](smart_building_conformal/outputs/amendment004/bdg2_threefold_frozen_v2/execution_analysis_manifest.json) froze both new units and the combined estimands before either fit. Configuration hash: `b49eb9b3802e715b150c5cf3ed7681f0da85b913425c29c6460b74ef8c19a5fb`. Feature/data hash: `151ff7d0472fe0e98861746af98697f0fbca1b874451a973b4006366278c0ec9`. Outcome hash: `d49161f5acd161aaba6218bc30d76f5daca0182ad0ab3c9d778f5235300c76ad`. All **39 role memberships, 18 boundaries, 45 catalogues and 189 stratum-support cells** were checked against the published preflight without fitting. Every new launch also regenerated and verified its 15 catalogues. The initial no-fit freeze attempt exited at the unchanged 3 GiB RAM guard; after unused applications were closed, the successful freeze passed. No model had been fitted in that failed attempt.

The [memory repair report](CHECKPOINT_MEMORY_REPAIR_REPORT.md) records unchanged fold-2 values, 30 byte-identical unit files, zero fits, 28 required CSV parses and zero parses during completeness checking. The repaired comparable scope peaked at **2.817 GiB RSS**, versus historical resume's **4.422 GiB**; current-machine host availability differs and no universal reduction is promised. Production training resume continues to reject a changed source identity. No old manifest was rewritten, and fold 2 was not refitted. Main, historical results, the forecasting pilot and backups remain preserved; the old [fold-2 report](BDG2_OPERATIONAL_PILOT_REPORT.md) is unchanged.

## Per-fold dates, support and decisions

Fold IDs run backward in time: fold 2 is earliest, fold 0 latest. The ten buildings recur across periods. Asset-days use eligible observed hourly rows, not five times those rows for five catalogues. Event counts pool the five actual catalogues; distinct-onset minima deduplicate building/onset within each of 21 strata.

| outer_fold | target_min | target_max | n | groups | asset_days | effective_events | minimum_distinct_onsets | decision | candidate_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 2016-10-23 14:00:00 | 2017-03-17 08:00:00 | 34732 | 10 | 1447.17 | 3389 | 53 | no_feasible_configuration | unavailable |
| 1 | 2017-03-17 09:00:00 | 2017-08-09 03:00:00 | 34645 | 10 | 1443.54 | 3300 | 58 | no_feasible_configuration | unavailable |
| 0 | 2017-08-09 04:00:00 | 2017-12-31 23:00:00 | 34520 | 10 | 1438.33 | 3248 | 50 | no_feasible_configuration | unavailable |


Primary feasibility requires supported bounds, recall LCB >=0.60 and workload UCB <=1.0 in **both** inner folds, using the unchanged 2,000 shared whole-building bootstrap draws, seed 20240601 and minimum 1,900 valid replicates. Utility is equal-fold custom synthetic F1, with the original delay/workload/ID ties. That custom utility allocates unmatched episodes uniformly across 21 strata and is distinct from ordinary matched-event/episode precision. No outer result changes a threshold, grid, catalogue or decision. Every candidate's failed gates follow; exact numerical bounds and rejection strings remain in each saved surface and the [combined rejection CSV](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/rejections.csv).

| outer_fold | candidate_id | failed_gates |
| --- | --- | --- |
| 2 | c0000_f5146f1247fa | inner0:workload; inner1:workload |
| 2 | c0001_ee0570e08213 | inner0:recall; inner1:recall |
| 2 | c0002_fa76e087b17d | inner0:recall; inner1:recall |
| 2 | c0012_23099bed3753 | inner0:recall; inner0:workload; inner1:recall; inner1:workload |
| 2 | c0013_a21278d4e492 | inner0:recall; inner1:recall |
| 2 | c0014_54a0e1ef5720 | inner0:recall; inner1:recall |
| 2 | c0024_ba16b82adffd | inner0:workload |
| 2 | c0025_63dd1cc1601e | inner0:recall; inner1:recall |
| 2 | c0026_47d9fe7d15ba | inner0:recall; inner1:recall |
| 1 | c0000_f5146f1247fa | inner0:workload; inner1:workload |
| 1 | c0001_ee0570e08213 | inner0:recall; inner1:recall |
| 1 | c0002_fa76e087b17d | inner0:recall; inner1:recall |
| 1 | c0012_23099bed3753 | inner0:recall; inner0:workload; inner1:workload |
| 1 | c0013_a21278d4e492 | inner0:recall; inner1:recall |
| 1 | c0014_54a0e1ef5720 | inner0:recall; inner1:recall |
| 1 | c0024_ba16b82adffd | inner1:workload |
| 1 | c0025_63dd1cc1601e | inner0:recall; inner1:recall |
| 1 | c0026_47d9fe7d15ba | inner0:recall; inner1:recall |
| 0 | c0000_f5146f1247fa | inner0:workload; inner1:workload |
| 0 | c0001_ee0570e08213 | inner0:recall; inner1:recall |
| 0 | c0002_fa76e087b17d | inner0:recall; inner1:recall |
| 0 | c0012_23099bed3753 | inner0:recall; inner0:workload; inner1:workload |
| 0 | c0013_a21278d4e492 | inner0:recall; inner1:recall |
| 0 | c0014_54a0e1ef5720 | inner0:recall; inner1:recall |
| 0 | c0024_ba16b82adffd | inner1:workload |
| 0 | c0025_63dd1cc1601e | inner0:recall; inner1:recall |
| 0 | c0026_47d9fe7d15ba | inner0:recall; inner1:recall |


The secondary inverse recall-floor selector is separate and removes the workload ceiling only for its own declared objective. Its `operational_feasible` flag does not establish primary feasibility. Independently selected components, shared-fit controlled components and persistence remain separately identified in the [actual comparison ledger](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/outer_comparisons.csv).

| outer_fold | decision | candidate_id |
| --- | --- | --- |
| 2 | selected | c0024_ba16b82adffd |
| 1 | selected | c0024_ba16b82adffd |
| 0 | selected | c0024_ba16b82adffd |


## Per-fold outer operational and interval results

All frozen candidates use .95 intervals. Candidate `c0000_f5146f1247fa` is static immediate uncalibrated; `c0012_23099bed3753` is static immediate CQR; `c0013_a21278d4e492` is static CQR, 180-minute 3-of-3; `c0024_ba16b82adffd` is immediate CQR rolling every 12 origins with window 200. Other evaluated IDs retain their exact settings in the ledger. Persistence is the fixed .95 split-conformal lag-0 diagnostic, with zero learned fits. The 360-minute 4-of-6 candidate remains in inner selection even where it is not requested for outer evaluation.

The operational predictor is the CQR-owned HistGradientBoosting quantile model. Uncalibrated controls share its fit. It is not the separate Attention-LSTM or point XGBoost comparison. Recall is the equal-weight mean across 21 family/severity strata; workload W is clean-background episodes per original asset-day, not adjudicated real-world false-alarm rate. Coverage is a fraction; MPIW and Winkler95 are in kWh per hourly observation. Clean interval metrics weight observed rows. The full CSV also retains point MAE/RMSE, ordinary matched-event/episode precision, custom synthetic F1, misses and censored-delay accounting.

| outer_fold | candidate_id | strategy | rule_id | macro_event_recall | background_episodes_per_asset_day | empirical_coverage | mpiw_kWh | winkler95_kWh |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | c0000_f5146f1247fa | static | single_sample | 0.840723 | 1.60382 | 0.882385 | 88.4156 | 155.434 |
| 2 | c0012_23099bed3753 | static | single_sample | 0.791943 | 1.03236 | 0.951111 | 98.7475 | 152.71 |
| 2 | c0013_a21278d4e492 | static | 180min_3of3 | 0.154322 | 0.0124381 | 0.951111 | 98.7475 | 152.71 |
| 2 | c0024_ba16b82adffd | rolling | single_sample | 0.785704 | 1.03305 | 0.9459 | 109.224 | 143.042 |
| 2 | diagnostic_persistence_split_095_single_sample | static | single_sample | 0.643014 | 1.06 | 0.946879 | 165.224 | 273.415 |
| 1 | c0000_f5146f1247fa | static | single_sample | 0.787844 | 1.44159 | 0.822023 | 92.4308 | 150.147 |
| 1 | c0012_23099bed3753 | static | single_sample | 0.81065 | 1.08068 | 0.944436 | 95.8342 | 146.823 |
| 1 | c0013_a21278d4e492 | static | 180min_3of3 | 0.16879 | 0.0408717 | 0.944436 | 95.8342 | 146.823 |
| 1 | c0024_ba16b82adffd | rolling | single_sample | 0.76816 | 0.926887 | 0.94409 | 103.459 | 142.989 |
| 1 | diagnostic_persistence_split_095_single_sample | static | single_sample | 0.622192 | 0.75578 | 0.959648 | 169.764 | 249.473 |
| 0 | c0000_f5146f1247fa | static | single_sample | 0.804697 | 1.48992 | 0.835342 | 85.6036 | 134.893 |
| 0 | c0012_23099bed3753 | static | single_sample | 0.821013 | 1.14994 | 0.944873 | 91.476 | 134.085 |
| 0 | c0013_a21278d4e492 | static | 180min_3of3 | 0.148301 | 0.0236385 | 0.944873 | 91.476 | 134.085 |
| 0 | c0024_ba16b82adffd | rolling | single_sample | 0.788392 | 0.915643 | 0.954519 | 97.6921 | 128.545 |
| 0 | diagnostic_persistence_split_095_single_sample | static | single_sample | 0.634616 | 0.980997 | 0.945684 | 152.106 | 251.552 |


No diagnostic substitutes for an abstained primary pipeline. Outer workload violations remain outcomes. Logged ill-sorted quantile notices are handled by the pre-existing CQR interval-order repair; the independently checked metrics use the actual issued bounds. No new interval sorting or calibration change was introduced. Temporal aggregation's changes in workload and detection are properties of these frozen physical rules and event envelopes; they did not trigger a software fix or retuning.

## Pooled results and frozen paired contrast

All **103,897 outer rows are disjoint** across the three test periods. Pooled W sums original clean episode counts and divides by original eligible asset-days. Pooled macro recall first sums N and TP separately within each of the 21 strata across folds/catalogues, then averages the 21 recalls equally. These are not unlabelled averages of fold percentages. Only identical candidate settings are pooled; the CSV explicitly flags any candidate not evaluated in all three folds. Interval quality below weights original observed rows; pooled RMSE is the square root of weighted squared RMSE.

| candidate_id | outer_folds | all_three_folds | asset_days | n_events | macro_event_recall | background_episodes_per_asset_day | empirical_coverage | mpiw_kWh | winkler95_kWh |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c0000_f5146f1247fa | [0, 1, 2] | True | 4329.04 | 9937 | 0.811191 | 1.51188 | 0.846627 | 88.8202 | 146.846 |
| c0012_23099bed3753 | [0, 1, 2] | True | 4329.04 | 9937 | 0.807658 | 1.08754 | 0.946813 | 95.3601 | 144.559 |
| c0013_a21278d4e492 | [0, 1, 2] | True | 4329.04 | 9937 | 0.15755 | 0.0256408 | 0.946813 | 95.3601 | 144.559 |
| c0024_ba16b82adffd | [0, 1, 2] | True | 4329.04 | 9937 | 0.780681 | 0.958642 | 0.94816 | 103.47 | 138.208 |
| diagnostic_persistence_split_095_single_sample | [0, 1, 2] | True | 4329.04 | 9937 | 0.633452 | 0.932308 | 0.95074 | 162.379 | 258.167 |


The main exploratory paired contrast was frozen as **static immediate CQR minus static immediate uncalibrated quantiles**. Recall and workload changes must be interpreted together; a workload decrease is not a same-recall improvement. The [per-fold differences](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/paired_per_fold.csv) accompany the pooled contrast.

| metric | estimate_a | estimate_b | difference_a_minus_b | ci_lower | ci_upper | valid_replicates | interval_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| macro_event_recall | 0.807658 | 0.811191 | -0.00353283 | -0.0368021 | 0.0309934 | 2000 | approximate_conditional_percentile |
| background_episodes_per_asset_day | 1.08754 | 1.51188 | -0.424343 | -0.574584 | -0.278645 | 2000 | approximate_conditional_percentile |


Static CQR's pooled recall changed by **-0.353 percentage points**, with an approximate interval of **[-3.680, 3.099] points**, while clean workload changed by **-0.424 episodes/asset-day**, interval **[-0.575, -0.279]**. The recall change was negative in fold 2 and positive in folds 1 and 0. The interval spanning zero does not establish equal recall. The static CQR workload remains above 1.0 in every outer fold, and all primary inner-selection decisions remain abstentions.

These optional intervals use 2,000 paired draws of **ten original buildings**, with all each building's fold/catalogue contributions kept together. Seed 42 is the only model seed. The saved [count inputs](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/original_building_contributions.csv), draws and replicate differences permit exact recomputation. Three periods do not create 30 independent buildings, and five catalogues do not create five model seeds. Intervals are approximate, conditional and exploratory; no confirmatory significance, equivalence or population-wide superiority claim is made.

## Channel attribution, misses, recovery and local workload

The table reports every pooled family/severity stratum for the main controlled pair. Availability-only detection is exactly shared by the two immediate baselines; it must not be credited to conformal calibration. Numerical and combined channels are separate. The [full channel CSV](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/stratum_channel_metrics.csv) retains each fold, inner role and every actually evaluated comparison, including temporal and persistence.

| family | severity | shared_availability_recall | uncal_numerical_recall | cqr_numerical_recall | uncal_combined_recall | cqr_combined_recall |
| --- | --- | --- | --- | --- | --- | --- |
| bias | 0.5 | 0 | 0.751953 | 0.703125 | 0.751953 | 0.703125 |
| bias | 1 | 0 | 0.886497 | 0.861057 | 0.886497 | 0.861057 |
| bias | 2 | 0 | 0.947059 | 0.97451 | 0.947059 | 0.97451 |
| block_missing | 0.5 | 1 | 0.444444 | 0.264368 | 0.909962 | 0.994253 |
| block_missing | 1 | 1 | 0.472381 | 0.312381 | 0.912381 | 0.998095 |
| block_missing | 2 | 1 | 0.509542 | 0.364504 | 0.874046 | 0.967557 |
| drift | 0.5 | 0 | 0.666667 | 0.552941 | 0.666667 | 0.552941 |
| drift | 1 | 0 | 0.85098 | 0.807843 | 0.85098 | 0.807843 |
| drift | 2 | 0 | 0.919608 | 0.931373 | 0.919608 | 0.931373 |
| dropout | 0.5 | 0 | 0.936 | 0.904 | 0.936 | 0.904 |
| dropout | 1 | 0 | 0.938124 | 0.894212 | 0.938124 | 0.894212 |
| dropout | 2 | 0 | 0.915832 | 0.88978 | 0.915832 | 0.88978 |
| level_shift | 0.5 | 0 | 0.733333 | 0.672549 | 0.733333 | 0.672549 |
| level_shift | 1 | 0 | 0.878431 | 0.876471 | 0.878431 | 0.876471 |
| level_shift | 2 | 0 | 0.92549 | 0.954902 | 0.92549 | 0.954902 |
| random_missing | 0.5 | 1 | 0.444444 | 0.259259 | 0.919753 | 1 |
| random_missing | 1 | 1 | 0.417219 | 0.261589 | 0.903974 | 0.996689 |
| random_missing | 2 | 1 | 0.446903 | 0.25885 | 0.887168 | 0.984513 |
| stuck | 0.5 | 0 | 0.389522 | 0.29385 | 0.389522 | 0.29385 |
| stuck | 1 | 0 | 0.422566 | 0.331858 | 0.422566 | 0.331858 |
| stuck | 2 | 0 | 0.465665 | 0.371245 | 0.465665 | 0.371245 |


Misses remain in recall and restricted mean detection time; detected-only delay quantiles do not replace them. Episode starts are matched one-to-one at target-observation time, and pre-active episodes get no onset credit. Full scheduled tolerance is required. [Recovery records](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/recovery.csv.gz) retain right censoring and follow-up; return toward pre-injection coverage is descriptive, not guaranteed restoration of nominal coverage.

Building-specific burden remains visible:

| outer_fold | candidate_id | min_W | max_W | buildings_above_1 |
| --- | --- | --- | --- | --- |
| 0 | c0000_f5146f1247fa | 0.241657 | 2.70656 | 6 |
| 0 | c0012_23099bed3753 | 0.0414269 | 2.3061 | 6 |
| 0 | c0013_a21278d4e492 | 0 | 0.103567 | 0 |
| 0 | c0024_ba16b82adffd | 0.289988 | 1.20829 | 7 |
| 0 | diagnostic_persistence_split_095_single_sample | 0 | 3.25201 | 4 |
| 1 | c0000_f5146f1247fa | 0.614676 | 2.59683 | 8 |
| 1 | c0012_23099bed3753 | 0.0276339 | 2.07885 | 6 |
| 1 | c0013_a21278d4e492 | 0.00690647 | 0.207194 | 0 |
| 1 | c0024_ba16b82adffd | 0.428325 | 1.23626 | 4 |
| 1 | diagnostic_persistence_split_095_single_sample | 0 | 2.11338 | 4 |
| 2 | c0000_f5146f1247fa | 0.511079 | 3.59827 | 7 |
| 2 | c0012_23099bed3753 | 0.0345324 | 3.12173 | 4 |
| 2 | c0013_a21278d4e492 | 0 | 0.0345324 | 0 |
| 2 | c0024_ba16b82adffd | 0.895574 | 1.14647 | 6 |
| 2 | diagnostic_persistence_split_095_single_sample | 0 | 3.15626 | 4 |


## Actual verification and cost

| outer_fold | exit_status | inner_cells | inner_pairs | outer_cells | outer_pairs | streams | contribution_rows | event_channel_records | resume_new_fits | unchanged_unit_files |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | 18 | 90 | 5 | 25 | 138 | 407948 | 119388 | 0 | 30 |
| 1 | 0 | 18 | 90 | 5 | 25 | 138 | 524891 | 152910 | 0 | 30 |
| 0 | 0 | 18 | 90 | 5 | 25 | 138 | 641428 | 186285 | 0 | 30 |


The two new audits independently reconstruct metrics, bounds and selection from saved streams, events, original-row contributions and actual resampling draws. Outer counts are derived from each actual decision/ledger. The preserved fold-2 independent audit remains unchanged and its newly read values are compatible. Both new normal resumes forbid fitting/computation routes and preserve all 30 unit files. Focused/shared-consumer regression, authorization, paired-count and recovery-arithmetic tests passed **58 distinct checks** (62 executions including four focused repeats); three existing MAPIE warnings remain. None of these engineering checks alone establishes scientific readiness.

The first fold-1 independent audit exited **1** on recovery censoring, and its failed output/log remain preserved. The [no-fit diagnosis](smart_building_conformal/outputs/amendment004/bdg2_threefold_validation_v1/recovery_numerics.json) demonstrated fractional-convolution rounding in the independent checker: an all-covered window became 0.9999999999999999, while the saved compensated rolling mean was exactly 1.0. Against a pre-coverage value of .95, this crosses the literal floating-point `<=.05` comparison. Integer prefix counts divided once by window size exactly reproduce the saved rolling arithmetic and **all 250 outer recovery records**. Six candidate/catalogue/group cases had differing window decisions; four changed the erroneous audit censoring status. The checker was repaired and six focused checks passed, then the audit was rerun into a fresh version-2 directory. Production source, recovery threshold, primary feasibility gates and all 30 completed unit files stayed unchanged. This preserves the frozen floating-point boundary behavior; it does not introduce a favourable tolerance or invalidate the study result. Recovery at an exact mathematical boundary remains sensitive to the declared numerical convention.

| outer_fold | command_seconds | cpu_seconds | peak_RSS_GiB | minimum_available_RAM_GiB |
| --- | --- | --- | --- | --- |
| 2 | 987.382 | 962.938 | 3.6337 | 1.39526 |
| 1 | 1138.26 | 1112.8 | 3.08604 | 2.93714 |
| 0 | 1365.68 | 1334 | 3.61586 | 2.51584 |


The three nonoverlapping original study commands total **3491.322 s (58.19 minutes)**, including historical fold 2 exactly once. The two newly authorized commands total **2503.939 s**. Actual process CPU totals **3409.734 s**. There are **9 CQR fit objects / 27 quantile sub-estimators** across the three units; shared uncalibrated controls add no fits and persistence adds zero. This task added 6 objects / 18 sub-estimators and did not refit fold 2.

Separate command costs, including preserved failed verification attempts:

| command_label | historical | seconds | exit_status |
| --- | --- | --- | --- |
| resume | True | 86.2311 | 0 |
| independent_audit | True | 139.705 | 0 |
| authorization_tests | False | 2.91719 | 0 |
| combination_tests | False | 1.19053 | 0 |
| combined | False | 8.94811 | 0 |
| compatibility_v1 | False | 98.5587 | 0 |
| fold0_audit | False | 212.756 | 0 |
| fold0_resume | False | 83.8205 | 0 |
| fold1_audit | False | 105.453 | 1 |
| fold1_audit_v2 | False | 166.964 | 0 |
| fold1_resume | False | 70.0468 | 0 |
| freeze_v1 | False | 5.70056 | 1 |
| freeze_v2 | False | 43.0538 | 0 |
| publication_parts | False | 3.21212 | 0 |
| recovery_diagnosis | False | 11.3661 | 0 |
| recovery_tests | False | 1.24193 | 0 |
| regression_v1 | False | 101.621 | 0 |


Verification commands are separate scopes and may overlap each other; they are not added to the nonoverlapping study total or represented as end-to-end project elapsed time.

The prior 16.46-minute fold-2 measurement informed scheduling; the frozen 20-40-minute per-new-unit range was a planning estimate, not a substitute for these measurements. Numerical thread variables were all 1 in the existing environment, with sequential real fits and launch RAM/disk guards. Complete command/CPU/artifact tables and [nested phase measurements](smart_building_conformal/outputs/amendment004/bdg2_threefold_costs_v1/phase_measurements.csv) separate preparation, windows, identity, checkpoint and validation. Fit, calibration, replay and scoring are measured jointly per inner/outer block; their separate constituent times were not isolated. The checkpoint phase contains those blocks, so it must not be added to them. No memory peaks are added together. Resume, independent audits, compatibility, freezing and regression have separate actual command rows, including the failed no-fit guard attempt.

## Interpretation and remaining research scope

The design was declared after inspection of earlier evidence, and fold 2 was already inspected before this replication. The result assesses repeatability across historical periods for the same ten selected buildings. Later folds legitimately train on earlier historical observations; they are not independent prospective trials or unseen-building tests. Synthetic catalogue uncertainty, one model seed, selected buildings, possible within-site dependence, coarse hourly fault realizations and unadjudicated natural faults limit interpretation. Clean W measures monitoring workload, not established false-alarm truth. No disappointing result caused a change to incidence, thresholds, candidates, model parameters or rules.

The broader work still requires matched point/interval/computational comparisons across all declared tasks and horizons, including the panel's Attention-LSTM versus XGBoost question; the full candidate/method scope; and justified operational handling for PLEIA temperature, PLEIA energy and RICO. Their current six inner banks per task have zero structurally supported banks; BDG2 has six of six. They are not dropped, and incidence is not inflated to manufacture support. This benchmark does not authorize a full-grid, four-task, five-model-seed or 900-cell robustness launch.

The single next justified bounded step is a **no-fitting support-design audit for the three unsupported tasks**, using their existing data to determine whether defensible temporal memberships/exposure can support the unchanged scientific estimands, followed by a written amendment or explicit non-estimability decision before further operational fitting. The broader forecasting comparison remains required regardless of operational support. No next experiment was launched automatically.
