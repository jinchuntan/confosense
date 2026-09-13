# PLEIA pilot diagnostics and allocation repair

13 September 2026. Bounded follow-up to `pilot_v1_20260913`; all original pilot outputs, protocol and model checkpoints are preserved. **One preparation-allocation problem was confirmed and fixed. No forecasting alignment, scaling or epoch-selection defect was demonstrated.** Development distribution changes and prediction bias are measured below; their architectural cause remains unresolved. No outer-test retuning, replacement pilot, new candidate, GPU migration or full multi-dataset experiment was performed.

## Identities and scope

The [evidence index](review/CURRENT_EVIDENCE.md) links the completed [pilot report](MODEL_COMPARISON_PILOT_REPORT.md), source, protocol, nine canonical CSVs, row-level predictions, histories and checkpoints. The original evaluated implementation is `d4bc1bc4af7b20d990618df09064ac310809a8ab`, source SHA-256 `965ff02d8cb67183210632bfbc3a2251c430a2b027b8b44d87df356fd19e3d71`, protocol SHA-256 `af29d2340427f043c605f777e54389bc86ccbb44c9630aba57964536d0845ce3`. The branch starts at the latest local `a5b32b81266efc107ad0bfdf74f95139ee99ba77`; the allocation change and reproduction driver are committed in `70b875a5f9abe73bfe6c9a2fe3f72c2ff4b41ecb`. The older published aggregate-review branch supplied the questions, not replacement source code.

Original inner learned predictions were **not saved**. Original tuning scores and learning histories were available. The diagnosis therefore reproduced exactly the existing two candidates × two inner folds × three horizons for each learned family: **24 learned inner fits**, plus six matched persistence supports, with seed 42 and unchanged epoch/patience budgets. No final/outer model was fitted. Saved development predictions now allow independent recomputation without the raw dataset. Diagnostic timings are separate and do not revise the original pilot's computational measurements.

## Matched inner-validation evidence

All entries are MAE in degrees Celsius on identical rows within each horizon/fold. Candidate 0/1 retain their frozen order. XGBoost uses depth 3/5; LSTM uses learning rate 0.001/0.0005, with the other frozen settings unchanged.

| Horizon | Inner fold | Persistence | XGB c0 | XGB c1 | LSTM c0 | LSTM c1 |
|---|---:|---:|---:|---:|---:|---:|
| 10 min | 0 | 0.270369 | 0.464341 | 0.483458 | 0.500975 | 0.564414 |
| 10 min | 1 | 0.239376 | 0.813644 | 0.815117 | 1.741837 | 1.844038 |
| 30 min | 0 | 0.455150 | 0.788961 | 0.930525 | 0.745112 | 0.806293 |
| 30 min | 1 | 0.391489 | 0.959988 | 1.114302 | 1.924060 | 2.044381 |
| 60 min | 0 | 0.645883 | 1.173682 | 1.296383 | 1.151718 | 1.169799 |
| 60 min | 1 | 0.547839 | 1.137805 | 1.216654 | 2.282438 | 2.255648 |

The [30-row matched table](smart_building_conformal/outputs/pilot_diagnostics_v1/inner_reproduction/matched_inner_metrics.csv) includes train/validation MAE, RMSE, prediction-minus-truth bias, ranges, original score differences and best epochs. [Development predictions and reproduced histories](smart_building_conformal/outputs/pilot_diagnostics_v1/inner_reproduction) retain role, row ID, group, origin, target time, truth and prediction. All 24 original learned MAEs reproduced within 1e-10; all 12 LSTM best-epoch choices reproduced exactly. Persistence has the lowest MAE on all six matched development supports. This comparison does not establish statistical superiority across tasks or future conditions.

### Target ranges and bias

For all three horizons, fold 0 trains approximately January 8–March 17 and validates March 17–May 25; fold 1 trains January 8–May 25 and validates May 25–August 2, 2021. Exact purged timestamps and counts are in [development_ranges.csv](smart_building_conformal/outputs/pilot_diagnostics_v1/inner_reproduction/development_ranges.csv). These are development folds, not the pilot's October–December outer evaluation.

| Horizon/fold | Train mean | Validation mean | Train range | Validation range | Validation above train maximum |
|---|---:|---:|---|---|---:|
| 10 min / 0 | 20.0252 | 22.2029 | 15–26.6 | 15–29.6 | 7.8445% |
| 10 min / 1 | 21.1140 | 28.9384 | 15–29.6 | 21.8–33.4 | 43.5147% |
| 30 min / 0 | 20.0246 | 22.2012 | 15–26.6 | 15–29.6 | 7.8469% |
| 30 min / 1 | 21.1129 | 28.9376 | 15–29.6 | 21.8–33.4 | 43.5033% |
| 60 min / 0 | 20.0239 | 22.1984 | 15–26.6 | 15–29.6 | 7.8408% |
| 60 min / 1 | 21.1111 | 28.9360 | 15–29.6 | 21.8–33.4 | 43.4572% |

The selected LSTM candidates are c0/c0/c1 at 10/30/60 minutes. Their fold-1 train MAEs are **0.269460/0.408697/0.542221**, compared with validation MAEs **1.741837/1.924060/2.255648**. Validation prediction-minus-truth biases are **−1.608535/−1.710241/−2.029226 °C**. Matched persistence biases are approximately **−0.000353/−0.001121/−0.002686 °C**. Thus substantial learned underprediction accompanies a warmer validation distribution; it is not an error created by mixing unmatched supports.

The [normalization table](smart_building_conformal/outputs/pilot_diagnostics_v1/inner_reproduction/normalization.csv) also shows covariate distribution changes. At 10 minutes/fold 1, training-window `V12` mean/std are 26.955250/0.206755; validation-origin standardized values range from −28.803440 to 5.053087, with 28.1518% having absolute z-score above 5. `V4` and `V5_0` each have 12.3145% above that threshold. These origin summaries diagnose covariate ranges; they are not activation measurements or proof of a defective scaler.

## Correctness audit

The [reproduction driver](smart_building_conformal/scripts/diagnose_pilot_inner.py) first verifies that model, sequence, feature and split source bytes match the exact evaluated-source ZIP. Its [completion record](smart_building_conformal/outputs/pilot_diagnostics_v1/inner_reproduction/summary.json) records the following checks at each horizon.

| Question | Evidence and outcome |
|---|---|
| Origin/target alignment | All 49,535 common eligible rows per horizon have truth from their exact target timestamp and target time = origin + h × 10 minutes. Metadata are monotone. Outer rows are inspected only for structural alignment here, not used for new selection. |
| Current observation and sequence order | Every 24-step sequence is compared in bounded batches against raw target indices in oldest-to-newest order. Its last target equals `target_lag_0`; y_t is available to both persistence and LSTM. |
| Schema | Each feature schema equals its frozen protocol entry. Sequence channels and order are recorded separately from flattened tabular features. The representations differ as declared; neither silently loses the current target. |
| Input normalization | Independent weighted raw-channel moments, using overlapping training-window multiplicities, match every reproduced LSTM's statistics and all three saved final artifacts. Only fit rows contribute. Near-zero standard deviations use the declared unit fallback. |
| Target scaling/inverse | The implementation standardizes training targets only, then returns predictions using `prediction * y_std + y_mean`. Saved final target mean/std match the final fit support; reproduced validation MAEs are in original units. |
| Early stopping | Validation MAE in original units, 1e-6 improvement threshold, patience 5 and at most 30 epochs. Saved best weights are cloned and restored. Recomputed history choices match the frozen records. |
| Selection and final refit | Equal mean of the two inner MAEs, exact ties by candidate order. Selected LSTM best epochs (30,10), (16,11), (10,12) imply ceil means **20,14,11**, equal to saved final settings. Final refitting has no calibration/test early stopping. |
| Model mechanics | Source uses linear projection with tanh, batch-first LSTM, attention normalized across time, dropout and linear output. Prediction disables dropout and uses batched inference. No demonstrated shape/order defect was found. |

**Confirmed observations:** temporal changes in targets/covariates, large negative learned-model bias on the second validation fold, and limited performance under this frozen budget. **Unresolved hypotheses:** sensitivity to rare HVAC states or out-of-range inputs, tanh projection saturation, insufficient capacity/training budget, and MSE training versus MAE selection. We did not measure hidden activations or isolate these causes with controlled ablations. The observed distribution change is consistent with the degradation, but the relative causal contributions are not identified. No architecture, loss, scaler, epoch budget or candidate change is justified as a demonstrated bug fix by these results alone.

## Preparation-memory finding and fix

The original protocol-freeze record remains **2.2857 GiB sampled process peak**, about **2.2895 GiB lifetime peak**, and **794,624 bytes (0.758 MiB)** minimum available system RAM. That last quantity is a system-wide reading, not the model's allocation. The historical interruption has no recorded cause or exit code; an out-of-memory termination is unconfirmed.

The Windows sampler was checked against the documented structures and byte units. `MEMORYSTATUSEX.ullAvailPhys` is available physical memory; `PROCESS_MEMORY_COUNTERS_EX.WorkingSetSize`, `PeakWorkingSetSize` and `PrivateUsage` measure current working set, lifetime peak working set and private commit respectively. Private commit must not be relabeled private working-set RAM. Field sizes/offsets are checked in the new tests. Sources: [Microsoft MEMORYSTATUSEX](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/ns-sysinfoapi-memorystatusex), [Microsoft PROCESS_MEMORY_COUNTERS_EX](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex).

The freeze path already hashes source files in chunks and uses lazy sequences; it does **not** require a full N × 24 × channels tensor. The confirmed avoidable allocations occur earlier: the loader reads a 2,527,150-row, 27-column room table, and target selection groups/sorts those full records although only four columns are needed for ranking. The selected-room processed frame is only 50,543 rows.

The [fix in prepare_data.py](smart_building_conformal/src/prepare_data.py) adds an explicit model-column projection to `load_room_table` and restricts target ranking to block/room/timestamp/target. The [PLEIA temperature adapter](smart_building_conformal/src/datasets/pleia.py) opts into 12 needed columns. The loader's default remains compatible with callers needing the full table. No data type, timestamp, gap treatment, feature calculation or target-selection criterion was changed.

Two separate preparation-only processes, each requiring at least 3 GiB available RAM before loading, followed the same prepare/common-support/membership-retention path. Neither trained a model.

| Measurement | Before | After |
|---|---:|---:|
| Sampled total peak working set | 2,183,290,880 bytes (2.03335 GiB) | 1,045,798,912 bytes (0.97398 GiB) |
| Lifetime peak working set | 2,301,026,304 bytes | 1,083,916,288 bytes |
| Minimum available system RAM | 3,450,773,504 bytes | 4,641,542,144 bytes |
| Loaded DataFrame size | 672,222,032 bytes / 27 columns | 368,964,032 bytes / 12 columns |
| Target-selection incremental peak | 647,229,440 bytes | 248,598,528 bytes |
| Measured total preparation | 17.67075 s | 14.97654 s |

The paired sampled peak fell **52.0999%**. This is one before/after pair, with 50 ms sampling and ordinary OS variation, not a runtime confidence interval. The historical freeze had a different imported-process baseline, so its 2.2857 GiB peak is not the denominator of that percentage. The near-zero historical free-RAM reading did not recur in these repeats. Avoidable copies were reduced; no change to the memory API was needed.

[memory_comparison.csv](smart_building_conformal/outputs/pilot_diagnostics_v1/memory_comparison.csv) combines the new per-stage measurements. The [before](smart_building_conformal/outputs/pilot_diagnostics_v1/memory_before/preparation.json) and [after](smart_building_conformal/outputs/pilot_diagnostics_v1/memory_after/preparation.json) records have **identical prepared-frame hash, selection-audit hash, chosen target, and all horizon data/membership/role records**, each checked against the original frozen protocol. The baseline prepared cache remains outside Git; it is not needed to recompute published metrics.

## Verification, commands and effect on results

Commands ran from `smart_building_conformal/` with the existing `C:\cfs_venv\Scripts\python.exe`; OMP/OpenBLAS/MKL/NumExpr threads were set to 1, and the diagnostic driver set Torch threads/inter-op threads to 1. `scripts/log_pilot_command.py` records each exact invocation, time and exit status. Paths below identify those durable records.

| Check | Actual child command / evidence | Outcome |
|---|---|---|
| Before allocation repair | `-B scripts/profile_pilot_preparation.py --out outputs/pilot_diagnostics_v1/memory_before --cache C:\Users\nigel\ConfoSenseBackups\pilot_followup_20260913\prepared_baseline.pkl`; [command record](smart_building_conformal/outputs/pilot_diagnostics_v1/memory_before.log.json) | Exit 0; zero models. |
| After allocation repair | `-B scripts/profile_pilot_preparation.py --out outputs/pilot_diagnostics_v1/memory_after`; [command record](smart_building_conformal/outputs/pilot_diagnostics_v1/memory_after.log.json) | Exit 0; zero models; identical support. |
| Unchanged inner reproduction | `-u -B scripts/diagnose_pilot_inner.py --cache C:\Users\nigel\ConfoSenseBackups\pilot_followup_20260913\prepared_baseline.pkl --out outputs/pilot_diagnostics_v1/inner_reproduction`; [command record](smart_building_conformal/outputs/pilot_diagnostics_v1/inner_reproduction.log.json) | Exit 0; 24 learned inner fits; zero new final/outer fits. Wrapper duration 646.521 s, separate from original cost. |
| Focused tests | `-B -m pytest -o addopts= -p no:cacheprovider -q tests/test_pilot_diagnostics.py tests/test_model_comparison_pilot.py`; [log](smart_building_conformal/outputs/pilot_diagnostics_v1/focused_tests.log) | 14 passed, 12.06 s; exit 0. |
| Full regression | `-B -m pytest -o addopts= -p no:cacheprovider -q -ra`; [log](smart_building_conformal/outputs/pilot_diagnostics_v1/full_tests.log) | 308 passed, 1 skipped, 3 existing MAPIE warnings, 35.22 s; exit 0. The skip concerns absent legacy interval predictions, not the completed pilot. |
| Pilot recomputation | `-B -m src.validate_model_comparison_pilot --run outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913 --protocol protocols/model_comparison_pilot_v1/frozen_protocol.json --out outputs/pilot_diagnostics_v1/pilot_revalidation.json`; [result](smart_building_conformal/outputs/pilot_diagnostics_v1/pilot_revalidation.json) | Exit 0; all 9 point and 18 interval cells passed, checkpoint hashes verified; no missing/duplicate cells. |
| Independent diagnostic recomputation/preservation | `-B scripts/validate_pilot_diagnostics.py --out outputs/pilot_diagnostics_v1/diagnostic_validation_extended.json`; [result](smart_building_conformal/outputs/pilot_diagnostics_v1/diagnostic_validation_extended.json) | Exit 0; all 30 saved prediction files recomputed; matched support, 12 full learning histories, original tuning/epoch choices and memory identity verified; 125 pilot/config/protocol files byte-identical. |

**No original pilot result is invalidated by this allocation-only fix.** It preserves the actual prepared values and supports and does not change model logic. Original phase times and memory measurements remain observations of the original implementation. All original pilot/config/protocol files are compared byte-for-byte with task-entry commit a5b32b8. Changed source identity does mean a future execution needs a new version/output directory; do not bypass the original checkpoint source guard or overwrite its readiness record.

The completed pilot's recorded completion exit remains **0**; its initial interrupted invocation remains **unknown**, and the previously recorded nine-unit resume remains a zero-refit check. Passing output validation does not imply nominal coverage: the pilot still has 16/18 coverage estimates below nominal and the previously reported poor LSTM interval performance. Global dissertation readiness remains false.

## Exact follow-up

Implement the [operational plan](OPERATIONAL_EVALUATION_PLAN.md) as amendment 004 and pass its one synthetic two-inner-fold integration smoke. The plan records separate core integration gaps, including method-specific recalibration not always reaching the actual alert stream; repairing that causal pipeline requires its versioned selection/stream contracts. That core work does not use or revise the pilot's fixed own-model conformal calculation. No full core/robustness run is part of this task.

Keep any later LSTM development study separate, explicitly acknowledging previously inspected pilot data. Test the unresolved architectural hypotheses on a newly declared development experiment only if separately authorized; do not retune against these pilot test results or discard LSTM merely to improve the reported ranking.


### Operational source-review correction, amendment-004 handoff

The subsequent review at f14076cbeb894488ef83229e90242aaa32605174 correctly narrows the operational finding: the three current core static branches already preserve their method-owned bounds. Periodic/rolling CQR instead uses generic signed point residuals, and the old core injects alert observations after clean forecasts/recalibration. Those are the demonstrated gaps for amendment 004. The earlier plan's claim that static CQR was routed through generic recalibration was incorrect and is corrected in the plan. None of this changes the completed pilot or its LSTM diagnosis.
