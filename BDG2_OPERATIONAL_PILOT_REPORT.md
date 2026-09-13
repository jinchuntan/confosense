# Completed BDG2 operational pilot report

**Explicit abstention: no feasible configuration.** No operational pipeline was selected from the frozen nine candidates. The fixed CQR .95/static/immediate reference and controlled components are diagnostics, not substitutes for feasibility.

The canonical version-2 command completed with **exit status 0**. Its complete output matrix passed the production validator and independent reconstruction from saved observations, intervals, event schedules, original-row contributions and paired bootstrap draws. Completed-unit resume returned **zero new fits**, with all 30 unit files byte-identical and fitting/computation functions forbidden. These are engineering and calculation checks; full-study readiness remains **false**.

## Identity and bounded scope

- Entry implementation: `2243c167804690ad1ec9b8aebc369e5596d392aa`; evaluated implementation: `ef9a8a9525bafea00a12b5c1327aadec071eab91`. This is a descendant review branch, not the older source beneath the instruction branch.
- Source SHA-256: `8218d9f461811fa9075c2966c394cae2344ae61f073887ff356af82025c8f4e4`. The [exact evaluated ZIP](smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2_execution/evaluated_source.zip) preserves original bytes.
- Frozen configuration SHA-256: `b49eb9b3802e715b150c5cf3ed7681f0da85b913425c29c6460b74ef8c19a5fb`; data/features hash: `151ff7d0472fe0e98861746af98697f0fbca1b874451a973b4006366278c0ec9`; outcome hash: `d49161f5acd161aaba6218bc30d76f5daca0182ad0ab3c9d778f5235300c76ad`. Full identity, seed ledger, nine candidates and expected keys are in the [pre-fit record](smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2_execution/prefit_identity.json).
- BDG2 only, outer fold 2, model seed 42, all ten retained buildings, horizon one hour, catalogue seeds 42–46. All nine reduced-grid candidates use .95; CQR/uncalibrated static plus CQR rolling every 12 origins with window 200; immediate, 180-minute 3-of-3 and 360-minute 4-of-6 rules. Candidate IDs, incidence .5 events/asset-day, recall floor .60 and workload ceiling 1 episode/asset-day are unchanged.
- The original proposal remains marked as a historical proposal. This report records its execution. No additional real-data unit or full experiment was launched.

## Membership, exposure and event support

Fresh preparation passed all 13 role-hash comparisons against the published preflight before fitting. The five catalogue repetitions do not multiply exposure or independent building count. Asset-day exposure is eligible hourly observations divided by 24; target observations define the evaluation clock.

| role | n | groups | asset_days |
| --- | --- | --- | --- |
| final_fit | 52025 | 10 | 2167.71 |
| final_calibration | 17380 | 10 | 724.167 |
| outer_test | 34732 | 10 | 1447.17 |
| inner0_train | 12993 | 10 | 541.375 |
| inner0_calibration | 13000 | 10 | 541.667 |
| inner0_selection | 13002 | 10 | 541.75 |
| inner1_train | 25993 | 10 | 1083.04 |
| inner1_calibration | 13002 | 10 | 541.75 |
| inner1_selection | 13030 | 10 | 542.917 |

The 15 actual inner/outer catalogue files match the frozen preflight schedules exactly, including null realizations and failed requests. Event totals below pool the five catalogues; distinct support deduplicates building/onset pairs within each of the 21 strata.

| role | requested | placed | effective | null | rejected | minimum_distinct_effective_onsets |
| --- | --- | --- | --- | --- | --- | --- |
| inner0_selection | 1355 | 1355 | 1268 | 87 | 0 | 16 |
| inner1_selection | 1355 | 1355 | 1271 | 84 | 0 | 21 |
| outer_test | 3620 | 3620 | 3389 | 231 | 0 | 53 |

The four-task preflight limitations still apply: PLEIA temperature, PLEIA energy and RICO lack inner structural support at the unchanged incidence. RICO outer banks have zero events. This BDG2 pilot does not resolve those limitations or supply results for those tasks.

## Inner selection

Every candidate retained both inner folds. Bounds used 2,000 shared whole-building bootstrap draws per fold, with a minimum of 1,900 valid replicates. Feasibility requires both folds' recall LCB ≥.60 and workload UCB ≤1.0; unavailable or degenerate bounds cannot be replaced with point estimates. Selection utility is the equal-fold mean of the custom 21-stratum synthetic F1, followed by the frozen delay/workload/ID tie-breaks.

| inner_fold | candidate_id | macro_event_recall | recall_lcb | background_episodes_per_asset_day | workload_ucb | custom_synthetic_f1 | bound_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | c0000_f5146f1247fa | 0.727312 | 0.645173 | 1.22012 | 1.60826 | 0.333079 | supported |
| 0 | c0001_ee0570e08213 | 0.22567 | 0.189079 | 0.0978311 | 0.182629 | 0.265967 | supported |
| 0 | c0002_fa76e087b17d | 0.185985 | 0.15293 | 0.0812183 | 0.160493 | 0.228013 | supported |
| 0 | c0012_23099bed3753 | 0.687057 | 0.594613 | 0.854638 | 1.22865 | 0.373612 | supported |
| 0 | c0013_a21278d4e492 | 0.175976 | 0.133796 | 0.0756807 | 0.145779 | 0.223691 | supported |
| 0 | c0014_54a0e1ef5720 | 0.140815 | 0.106396 | 0.0609137 | 0.123636 | 0.182873 | supported |
| 0 | c0024_ba16b82adffd | 0.679528 | 0.649176 | 0.889709 | 1.00016 | 0.405964 | supported |
| 0 | c0025_63dd1cc1601e | 0.149263 | 0.129409 | 0.0664513 | 0.106995 | 0.203611 | supported |
| 0 | c0026_47d9fe7d15ba | 0.113471 | 0.093601 | 0.042455 | 0.0664723 | 0.155797 | supported |
| 1 | c0000_f5146f1247fa | 0.747474 | 0.679748 | 1.45142 | 2.0225 | 0.313223 | supported |
| 1 | c0001_ee0570e08213 | 0.23604 | 0.189681 | 0.209977 | 0.368427 | 0.259643 | supported |
| 1 | c0002_fa76e087b17d | 0.1999 | 0.154269 | 0.176823 | 0.303914 | 0.231408 | supported |
| 1 | c0012_23099bed3753 | 0.678767 | 0.596763 | 0.968841 | 1.50129 | 0.3543 | supported |
| 1 | c0013_a21278d4e492 | 0.176984 | 0.123903 | 0.138143 | 0.276285 | 0.214879 | supported |
| 1 | c0014_54a0e1ef5720 | 0.146223 | 0.100732 | 0.121566 | 0.241289 | 0.183018 | supported |
| 1 | c0024_ba16b82adffd | 0.689423 | 0.659248 | 0.849117 | 0.981734 | 0.417861 | supported |
| 1 | c0025_63dd1cc1601e | 0.144721 | 0.122377 | 0.0976209 | 0.147352 | 0.189608 | supported |
| 1 | c0026_47d9fe7d15ba | 0.112823 | 0.0945433 | 0.0736761 | 0.117882 | 0.148509 | supported |

All rejection reasons, independently selected component decisions and the secondary inverse recall-floor decision are retained in the [checkpoint payload](smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2/units/outer2_model42/payload.json) and [independently recalculated rejections](smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/rejections.csv). The inverse selector also returned `selected`. No outer outcome selected or revised a pipeline.

The immediate rolling CQR candidate `c0024_ba16b82adffd` passes both recall lower-bound gates and the second fold's workload gate, but its first-fold workload UCB is **1.000161467488**, strictly above 1.0. Rounding that value to 1.000 would conceal its rejection. Its selection under the separate inverse objective removes the workload ceiling only for that declared secondary comparison; it is not primary operational feasibility. This near-boundary result also warrants caution about Monte Carlo and ten-building sampling uncertainty. Neither bootstrap settings nor thresholds were changed to change the decision.

## Outer results

The 5 distinct outer configurations and 25 catalogue pairs were derived from the actual frozen decision/comparators. Multiple comparison labels can refer to one evaluated configuration; they are not extra fits. Controlled components share the final quantile fit. The fixed persistence split-conformal reference requires zero learned fits.

| candidate_id | method | rule_id | macro_event_recall | recall_lcb | recall_ucb | background_episodes_per_asset_day | workload_ucb | custom_synthetic_f1 | ordinary_matched_event_episode_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c0000_f5146f1247fa | quantile_uncalibrated | single_sample | 0.840723 | 0.795137 | 0.876172 | 1.60382 | 2.15538 | 0.326105 | 0.206402 |
| c0012_23099bed3753 | cqr | single_sample | 0.791943 | 0.714826 | 0.850665 | 1.03236 | 1.6251 | 0.393054 | 0.271407 |
| c0013_a21278d4e492 | cqr | 180min_3of3 | 0.154322 | 0.119402 | 0.190464 | 0.0124381 | 0.0221007 | 0.220328 | 0.876006 |
| c0024_ba16b82adffd | cqr | single_sample | 0.785704 | 0.75922 | 0.8127 | 1.03305 | 1.07741 | 0.450585 | 0.331319 |
| diagnostic_persistence_split_095_single_sample | persistence_split | single_sample | 0.643014 | 0.490962 | 0.780212 | 1.06 | 1.79734 | 0.315987 | 0.218418 |

The recall columns are equal-weight means over all 21 family/severity strata. The custom synthetic F1 allocates unmatched episodes uniformly across those strata and is **not conventional precision**. Ordinary matched-event/episode precision is shown separately. Workload is clean-background episodes per original asset-day, not a proven real-world false-alarm rate: the source has no adjudicated natural-fault labels.

Observed outer point-workload violations of the declared ceiling: **`c0000_f5146f1247fa`, `c0012_23099bed3753`, `c0024_ba16b82adffd`, `diagnostic_persistence_split_095_single_sample`**. No violation triggered reselection or threshold changes. Per-building workload shows whether an aggregate rate conceals local burden:

| candidate_id | min_group_workload | max_group_workload | groups_above_1_per_day |
| --- | --- | --- | --- |
| c0000_f5146f1247fa | 0.511079 | 3.59827 | 7 |
| c0012_23099bed3753 | 0.0345324 | 3.12173 | 4 |
| c0013_a21278d4e492 | 0 | 0.0345324 | 0 |
| c0024_ba16b82adffd | 0.895574 | 1.14647 | 6 |
| diagnostic_persistence_split_095_single_sample | 0 | 3.15626 | 4 |

Event matches use one-to-one episode starts at target-observation time. An episode already active before onset receives no credit. Complete scheduled tolerance is required for eligibility. Misses remain in recall and the restricted mean; median and 90th-percentile delays describe detected events only.

| candidate_id | n_events | n_detected | corrupted_episode_count | unmatched_episode_count | detected_delay_median_minutes | detected_delay_q90_minutes | undetected_fraction | restricted_mean_detection_minutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c0000_f5146f1247fa | 3389 | 2837 | 13745 | 10908 | 60 | 240 | 0.16288 | 119.611 |
| c0012_23099bed3753 | 3389 | 2653 | 9775 | 7122 | 60 | 180 | 0.217173 | 130.392 |
| c0013_a21278d4e492 | 3389 | 544 | 621 | 77 | 120 | 180 | 0.839481 | 326.167 |
| c0024_ba16b82adffd | 3389 | 2632 | 7944 | 5312 | 60 | 180 | 0.22337 | 134.057 |
| diagnostic_persistence_split_095_single_sample | 3389 | 2118 | 9697 | 7579 | 60 | 240 | 0.375037 | 182.656 |

All three channel attributions (availability-only, numerical-only, combined), 21 strata, buildings, misses, delays and recovery censoring are independently checked and available in the [audit directory](smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1). Recovery is a descriptive return toward each building's pre-injection coverage, not a guaranteed restoration of nominal coverage.

## Clean interval and point quality

The following is independently recomputed from **unmodified-stream** observed targets and issued bounds. Coverage is a fraction; MPIW, Winkler95, MAE and RMSE use the adapter's **kWh per hourly observation**. All 34732 outer rows contribute to each configuration; aggregation weights observations, not buildings equally. Winkler95 uses alpha=.05 and a penalty multiplier of 40 beyond either bound. It includes CQR's existing interval-order repair. The .95 uncalibrated quantiles do not acquire conformal guarantees from their label.

| candidate_id | observed_rows | empirical_coverage | mpiw_kWh | winkler95_kWh | mae_kWh | rmse_kWh |
| --- | --- | --- | --- | --- | --- | --- |
| c0000_f5146f1247fa | 34732 | 0.882385 | 88.4156 | 155.434 | 17.103 | 35.7736 |
| c0012_23099bed3753 | 34732 | 0.951111 | 98.7475 | 152.71 | 17.103 | 35.7736 |
| c0013_a21278d4e492 | 34732 | 0.951111 | 98.7475 | 152.71 | 17.103 | 35.7736 |
| c0024_ba16b82adffd | 34732 | 0.9459 | 109.224 | 143.042 | 17.103 | 35.7736 |
| diagnostic_persistence_split_095_single_sample | 34732 | 0.946879 | 165.224 | 273.415 | 20.9588 | 41.6246 |

## Uncertainty and applicability limits

| role | bound_status | cells | minimum_valid_replicates | maximum_valid_replicates |
| --- | --- | --- | --- | --- |
| inner0_selection | supported | 9 | 2000 | 2000 |
| inner1_selection | supported | 9 | 2000 | 2000 |
| outer_test | supported | 5 | 2000 | 2000 |

These are approximate percentile, whole-building, conditional pilot bounds. Ten selected buildings are ten original resampling units; five synthetic catalogues are not five independent datasets. Only one model seed and one outer fold were run. Selection uncertainty, variation across other model seeds/folds, possible dependence between buildings at the same site and generalization to a broader building population are not established. Paired full-study tests, Holm-adjusted claims, equivalence and superiority claims are not produced by this pilot. Any unavailable bound retains its explicit reason rather than receiving an invented interval.

Synthetic scheduled fault envelopes and coarse hourly duration/missingness realizations limit interpretation. Bias/drift can begin at zero amplitude; null realizations stay null. Results describe the declared injection distribution and frozen horizon, not verified detection of naturally occurring faults. Inspection of this pilot does not authorize retuning.

## Actual computational cost

The successful command took **987.382 seconds (16.46 minutes)** and **962.938 CPU seconds** in the actual pilot process. Its evaluate-unit region took **785.984 seconds**. Peak Windows process RSS was **3,901,652,992 bytes (3.634 GiB)**; minimum sampled available physical RAM was **1,498,148,864 bytes (1.395 GiB)**. Launch required 3 GiB available RAM and passed. Numerical thread variables were all 1; real fits were sequential in the existing Python environment. [Process lifetime CPU measurements](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/process_measurements.csv) come from Windows process accounting and include the interval before the observer attached.

There were **3 CQR fit objects containing 9 quantile sub-estimators**: two inner fits and one final fit. Uncalibrated controls shared those fits; persistence used zero learned fits. The failed version-1 attempt used zero fits and took 25.807 seconds. The canonical run directory contains **31 files, 397,730,260 bytes (379.31 MiB)**, excluding raw data, environments and external backups.

| phase | seconds | peak_rss_bytes | lifetime_peak_rss_bytes | min_available_ram_bytes |
| --- | --- | --- | --- | --- |
| preparation | 4.87728 | 1024704512 | 1036832768 | 3680841728 |
| windows | 1.82924 | 507240448 | 1036832768 | 4190052352 |
| prefit_identity | 5.70381 | 490172416 | 1036832768 | 4209623040 |
| inner0_fit_replay_score | 170.894 | 1111388160 | 1112596480 | 3595997184 |
| inner1_fit_replay_score | 171.216 | 1400573952 | 1423626240 | 3343097856 |
| outer_fit_replay_score | 441.318 | 2720698368 | 2754732032 | 1994489856 |
| checkpoint_compute_save_verify | 961.439 | 3839774720 | 3901652992 | 1498148864 |
| output_validation | 5.59968 | 2166538240 | 3901652992 | 3471953920 |

Phase intervals overlap: do not add nested phase durations or memory peaks. The checkpoint phase includes computation, frame assembly, compression and integrity reload. Full command time includes imports and final output checks. [Command measurements](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/command_measurements.csv), [phase measurements](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/phase_measurements.csv), [fit counts](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/fit_measurements.csv), [artifact sizes](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/artifact_measurements.csv) and [measurement scope](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/cost_scope.json) separately retain actual costs of resume, independent verification and regression. They are not full-study runtime estimates.

Completed-unit resume took **86.231 seconds**, with **4,748,304,384 bytes (4.422 GiB)** process peak RSS and **633,327,616 bytes (0.590 GiB)** minimum sampled available RAM. It performs no fits, but [the completed-unit path](smart_building_conformal/src/operational004_engine.py) calls `load` and then `require_complete`; [the latter calls `load` again](smart_building_conformal/src/unit_checkpoint.py) while the first loaded frames remain live. This confirmed duplicate materialization explains an avoidable allocation component; the exact peak reduction from fixing it has not been measured. It is a new checkpoint-read limitation, not a repeat of the earlier preparation-memory investigation. Independent metric recomputation took **139.705 seconds**, with zero fits.

## Demonstrated defect, verification and preservation

Version 1 exited **1**, before any model fit, because assigning Boolean flags to BDG2's integer `target_was_missing` column coerced it to an object-valued feature matrix and NumPy's finite-value check failed. The focused fix explicitly retains the binary flag as numeric 0/1 before causal injection. It changes representation, not values, memberships, events, models or settings.

Three integer/float/Boolean flag tests passed. A no-fitting real-data reproduction checked 13,002 rows × 22 features across ten buildings: the original TypeError reproduced, corrected values matched the original numeric view exactly, and zero corruption reproduced clean features. The earlier 27 operational/journal regression checks passed; all five final independent-audit/materialization tests passed. The failed logs, source identity and empty unit manifest remain under version 1; version 2 has a new source identity and directory. No previous completed pilot result is invalidated: the forecasting pipeline does not use this operational feature function, and the previous synthetic fixture did not contain this adapter covariate.

Production validation: 18/18 inner cells, 90/90 inner pairs, 25/25 outer pairs and 138 persisted streams passed. Independent validation recomputed 407,948 original-row contributions, 119,388 event/channel records and 23 confidence-bound cells, checked all declared surface metrics, per-building workloads, channel attribution, recovery, selection and paired draws, and verified all 15 preflight catalogues. Resume completed with fitting routes forbidden and 30 files unchanged. [Verification record](smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/validation.json), [resume proof](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/resume_validation.json).

All 942 entry evidence/protocol files and the previous publication bundle remain unchanged. The old snapshot's 554 data/result files remain byte-identical; its 19 earlier report annotations remain unchanged since entry. Main and the previous review branch retain their original heads. [Preservation proof](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/preservation.json). The original completed forecasting pilot is preserved.

## Single next justified step

**Remove the duplicate completed-checkpoint table materialization, then verify the same preserved BDG2 unit with zero fits.** Introduce a file/hash-only completeness check for the second verification pass, retain corruption/provenance checks, and measure the resulting resume peak against the observed 4.422 GiB. This is a bounded checkpoint implementation/verification follow-up and requires no additional real-data fitting or changes to the selected/abstained result. A new real-data unit or full study should not launch automatically. The current task leaves the evaluated source and completed checkpoint immutable for review.

The [evidence index](review/bdg2_operational_pilot_20260913/EVIDENCE_INDEX.md) links exact files and purposes, including the two canonical metric CSVs and their independently recomputed counterparts. [BDG2 attribution and derived-data notice](review/bdg2_operational_pilot_20260913/DATA_NOTICE.md).

The 150,246,039-byte inner `streams.csv.gz` exceeds [GitHub's ordinary 100 MiB file limit](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). All of its bytes are published as four ordered binary parts with a [SHA-256 manifest](smart_building_conformal/outputs/amendment004/bdg2_pilot_publication_v1/large_files.json). The index provides the reconstruction command, which preserves the original gzip bytes and completed-checkpoint hash. The original local file is unchanged; no manual CSV upload is needed. Other canonical files are published directly.
