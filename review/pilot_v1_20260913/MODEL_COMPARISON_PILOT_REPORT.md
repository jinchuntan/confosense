# PLEIA temperature model-comparison pilot

13 September 2026. **Pilot completed: completion exit status 0; output validation passed for all 9 point-summary and 18 interval-quality cells.** The original interrupted launch has no recorded exit status; its checkpoints were preserved and resumed. Paths are relative to `smart_building_conformal/` unless stated otherwise. This report concerns the authorised pilot only; it does not mark the full study or dissertation ready.

## Preservation and design

Work resumed on `fix/final-dissertation-study` at `3cb343d2c61a2ea0f3997b86d42f9d8db98f14c3`, with a clean working tree. Existing repair commits, external backups and historical outputs were retained. No dependencies were installed, no history was reset, and no commits were pushed. Execution uses `C:/cfs_venv/Scripts/python.exe`, Python 3.11.3 and PyTorch 2.13.0+cpu.

The frozen design and implementation were committed **before research fitting** as `d4bc1bc4af7b20d990618df09064ac310809a8ab`. The frozen protocol was written at **2026-09-13 04:17:02 UTC**; execution started after **04:20 UTC**. The versioned inputs are:

- `configs/model_comparison_pilot_v1.json`: explicit pilot scope, models, candidate budgets, thread/memory controls and interval construction.
- `protocols/model_comparison_pilot_v1/frozen_protocol.json`: resolved dataset configuration, actual row counts/endpoints, schemas, source-data fingerprints and membership hashes.
- `protocols/model_comparison_pilot_v1/PILOT_PROTOCOL.md`: readable design and complete role/date table.
- `protocols/model_comparison_pilot_v1/membership.csv.gz` and `boundaries.csv`: individual row IDs/roles and all checked temporal boundaries.
- `protocols/model_comparison_pilot_v1/readiness.json`: pilot-specific readiness, explicitly separate from global study/publication readiness.

Pilot protocol SHA-256: `af29d2340427f043c605f777e54389bc86ccbb44c9630aba57964536d0845ce3`. Evaluated source hash: `965ff02d8cb67183210632bfbc3a2251c430a2b027b8b44d87df356fd19e3d71`.

Only the existing PLEIA temperature task is fitted. The three horizons are **1/3/6 steps**, or **10/30/60 minutes**. Models are **persistence, XGBoost and Attention-LSTM**, with model seed **42** and nominal levels **90%/95%**. No synthetic faults, alerts, rule selection or adaptive recalibration are used.

The first fold in the existing declared order is **outer fold ID 0**. All horizons evaluate the same 9,907 target timestamps from **2021-10-10 04:50** to **2021-12-17 23:50**. Times are the dataset timestamps as stored, not newly assigned UTC timestamps. Their origin ranges differ by horizon:

| Horizon | First test origin | Last test origin | Fitting rows | Final calibration rows | Test rows |
|---|---|---|---:|---:|---:|
| 10 minutes | 2021-10-10 04:40 | 2021-12-17 23:40 | 29,719 | 9,907 | 9,907 |
| 30 minutes | 2021-10-10 04:20 | 2021-12-17 23:20 | 29,715 | 9,906 | 9,907 |
| 60 minutes | 2021-10-10 03:50 | 2021-12-17 22:50 | 29,710 | 9,904 | 9,907 |

Common eligibility is established **before fitting**, by intersecting complete flat features, finite outcomes and valid 24-step LSTM sequences. Every model uses the identical fitting, calibration and evaluation rows within its horizon. Sequences cannot cross a series boundary. Repaired marked-missing-value forward filling and repaired strict target-before-next-origin purging are reused. The retained cohort and previously inspected target choice are unchanged; upstream unflagged imputation remains a provenance limitation.

Final calibration is reserved first. Only the fitting pool supplies the **two expanding, purged inner validation folds**. Both learned models have two explicitly frozen candidates and use equally weighted mean inner-fold MAE in original temperature units. Exact score ties choose the earlier candidate ID. This is **model-comparison tuning**, and does not resolve the separate two-inner-fold operational alert-selection design.

XGBoost candidates have 400 trees and maximum depths 3 or 5; other parameters are frozen in the JSON. Attention-LSTM retains the existing architecture: 64 hidden units, dropout 0.2, batch size 256, at most 30 epochs and patience 5; candidates differ only in learning rate (0.001 or 0.0005). Inner validation controls early stopping. The final LSTM uses `ceil(mean(selected-candidate best epoch across the two inner folds))` and refits all permitted fitting rows, with normalisation learned only there. The final calibration and test data cannot select candidates or epochs.

The planned workload is **24 tuning fits** (12 per learned model), **six learned final fits**, and three no-learning persistence streams. These extra tuning fits do not inflate the nine point-summary cells or eighteen interval-quality cells. Persistence carries seed 42 as the paired experimental-unit identifier; it has no stochastic model training.

## Intervals and computational measurements

Each final predictor supplies its **own** calibration predictions. Its conformity scores are `abs(y_calibration - model_prediction)`. At nominal level `L`, the radius is the calibration order statistic at rank `ceil((n_cal+1)*L)`, computed without quantile interpolation. Intervals are `prediction - q` to `prediction + q`, fixed throughout outer evaluation. An unsupported rank produces `q=infinity` with an explicit insufficient-calibration status; it cannot be reported as a finite interval-quality result.

This is **ordinary split conformal**, not CQR, EnbPI or DSCP. Temporal dependence and distribution changes limit the usual exchangeability-based guarantee. Width must be interpreted alongside achieved coverage; a narrower interval is not automatically better.

Models run serially with numerical threads, Torch intra/inter-op threads and `n_jobs` set to one. Training and validation sequences are materialised in bounded batches instead of full tensors. Inference batch size is 256. No cohort, horizon or model-size reduction is triggered by memory pressure.

Every unit records tuning, final fitting, calibration and inference seconds separately, plus throughput. Calibration time includes prediction on calibration rows and computing both fixed radii. Final inference time covers test point predictions; constructing/writing CSVs and plotting are outside that field. End-to-end command time includes data preparation and checkpoint I/O.

Native Windows APIs measure working set (RSS), private committed memory, available system RAM and the OS process-lifetime RSS high-water mark. Phase baseline and peak working sets/private bytes are sampled every **50 ms**; very short peaks may be missed by the sampler. The OS lifetime high-water mark is also saved and can include earlier data preparation. Absolute RSS is affected by the serial process's retained allocations, so compare phase baselines/increments as well as maxima. These are CPU process measurements; no GPU timing or VRAM claim is made.

## Validation and execution

The focused preflight run passed **20 tests** (pilot plus integration-delivery checks) in **18.47 seconds**. The full preflight suite passed **305 tests, with one skip and three warnings**, in **30.30 seconds**. The skip is the pre-existing check for interval predictions on disk; pilot predictions have their own validator. Warnings originate from the existing deliberately small MAPIE fixture, not the pilot's split-conformal construction.

Tests cover exact finite-sample ranks and insufficient support; training/calibration/test isolation; two expanding tuning folds; lazy/eager sequence equality; common row support; actual fitted estimator identity; model-specific calibration errors; saved LSTM weight reproduction; deterministic candidate tie handling; interruption/resume; corrupted model artifacts; and recomputation of saved pilot outputs.

Preflight/readiness commands (working directory `smart_building_conformal/`) were:

```powershell
$env:OMP_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'; $env:NUMEXPR_NUM_THREADS='1'
& 'C:\cfs_venv\Scripts\python.exe' -B -m pytest -o addopts="" -p no:cacheprovider -q tests/test_model_comparison_pilot.py tests/test_integration_delivery.py
& 'C:\cfs_venv\Scripts\python.exe' -B -m src.model_comparison_pilot freeze --out protocols/model_comparison_pilot_v1
& 'C:\cfs_venv\Scripts\python.exe' -B -m pytest -o addopts="" -p no:cacheprovider -q -ra
& 'C:\cfs_venv\Scripts\python.exe' -B -m src.model_comparison_pilot readiness --out protocols/model_comparison_pilot_v1/readiness.json
```

All returned exit status **0**. The full-suite output is retained in `outputs/model_comparison_pilot_v1/validation/preflight_full_tests.txt`. Pilot readiness passed all checks; global study and publication readiness remained false.

The pilot command is:

```powershell
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/log_pilot_command.py --log outputs/model_comparison_pilot_v1/validation/pilot_run_v1.log -- 'C:\cfs_venv\Scripts\python.exe' -u -B -m src.model_comparison_pilot run --out outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913
```

The logger records its exact child command, start/end times, duration and exit status beside the log. Each model/horizon checkpoint saves fitted weights/model files, parameters, class and seed, role/membership identifiers, calibration truth/predictions/errors, test truth/predictions/bounds, tuning scores/history and resource measurements. Code/configuration/data/package hashes bind resume identity. A partial or corrupt unit cannot count as complete.

The original launch stopped during the 30-minute LSTM tuning unit, with **five committed units** and no process exit record. Its cause and exit code are unknown. The original log, aggregate CSVs, preparation records and hashes of all 35 files in those five units were preserved in `validation/interrupted_launch_snapshot/` under the pilot output directory. This was an execution interruption, with no observed software exception and no code or design change. The unchanged frozen run was resumed with:

```powershell
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/log_pilot_command.py --log outputs/model_comparison_pilot_v1/validation/pilot_completion_resume.log -- 'C:\cfs_venv\Scripts\python.exe' -u -B -m src.model_comparison_pilot run --out outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913 --resume
```

The interrupted unit's partial training is not a saved scientific cell; it is recomputed from its start. Its abandoned computation has no complete phase timing record. Consequently, the sum of saved unit timings measures the work represented by the delivered checkpoints, and **does not include all interruption overhead**. The original launch's exact total wall time cannot be recovered from its incomplete logger output.

Post-fit commands use the same Python environment and single-thread environment variables shown above:

```powershell
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/log_pilot_command.py --log outputs/model_comparison_pilot_v1/validation/pilot_verification_resume.log -- 'C:\cfs_venv\Scripts\python.exe' -B -m src.model_comparison_pilot run --out outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913 --resume
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/log_pilot_command.py --log outputs/model_comparison_pilot_v1/validation/output_validation.log -- 'C:\cfs_venv\Scripts\python.exe' -B -m src.validate_model_comparison_pilot --run outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913 --protocol protocols/model_comparison_pilot_v1/frozen_protocol.json --out outputs/model_comparison_pilot_v1/validation/output_validation.json
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/log_pilot_command.py --log outputs/model_comparison_pilot_v1/validation/bdg2_preparation.log -- 'C:\cfs_venv\Scripts\python.exe' -B -m src.model_comparison_pilot bdg2-memory --out outputs/model_comparison_pilot_v1/validation/bdg2_preparation_memory.json
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/log_pilot_command.py --log outputs/model_comparison_pilot_v1/validation/summary_tables.log -- 'C:\cfs_venv\Scripts\python.exe' -B scripts/summarise_pilot.py --run outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913 --out outputs/model_comparison_pilot_v1/tables
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/log_pilot_command.py --log outputs/model_comparison_pilot_v1/validation/comparison_figure.log -- 'C:\cfs_venv\Scripts\python.exe' -B -m src.pilot_figure --run outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913 --out outputs/model_comparison_pilot_v1/figures
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/collect_pilot_measurements.py --base outputs/model_comparison_pilot_v1 --protocol protocols/model_comparison_pilot_v1/frozen_protocol.json
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/write_pilot_report_results.py --base outputs/model_comparison_pilot_v1 --report ../MODEL_COMPARISON_PILOT_REPORT.md
```

`scripts/finalise_pilot_artifacts.py --base outputs/model_comparison_pilot_v1 --wait-for-completion` sequences these commands after confirming successful completion. It checks all nine existing checkpoints before the verification resume, ensuring that this verification cannot fit a missing unit. It preserves completion-launch preparation records before the verification resume rewrites those per-invocation measurements. The finalisation command's duration includes its wait for fitting; it is **not an additional model-runtime measurement**.

## Artifact locations and CSV definitions

The absolute output root is:

```text
C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\model_comparison_pilot_v1
```

All paths in this table are relative to that root. Temperature errors and widths are in degrees Celsius; coverage is a fraction; time is in seconds; memory is in bytes unless a column explicitly says otherwise.

| File | Purpose |
|---|---|
| `runs/pilot_v1_20260913/point_summary.csv` | Nine model/horizon cells: MAE, RMSE, fitting/calibration/evaluation counts, four timing phases, batch size, throughput and baseline/peak process memory. |
| `runs/pilot_v1_20260913/interval_quality.csv` | Eighteen model/horizon/nominal-level cells: empirical coverage, MPIW, Winkler score, calibration radius/order-statistic rank and sample counts. |
| `tables/resource_measurements.csv` | Thirty-six phase measurements: tuning, final fitting, calibration and inference for each of nine units; wall time, baseline/peak/incremental RSS, private bytes, minimum available RAM and lifetime RSS peak. Persistence tuning is explicitly zero-work. |
| `tables/tuning_results.csv` | Twenty-four completed candidate/inner-fold results for the two learned models, with inner MAE, timing, sample counts, epoch information and selected candidate. Excludes abandoned partial tuning from the interrupted launch. |
| `tables/pleia_preparation_memory.csv` | PLEIA protocol-freeze preparation and per-horizon preparation measurements from the original launch, completion launch and verification resume. Separates startup/preparation peaks from model-phase memory. |
| `tables/bdg2_preparation_memory.csv` | Separate no-fitting BDG2 measurement: adapter, complete preparation, and each configured horizon's flat features/lazy sequences/full batched traversal; stored bytes and equivalent full-tensor bytes. Total includes its component stages and must not be added to them. |
| `tables/execution_measurements.csv` | Recorded command start/end times, duration and exit status. Original interrupted launch has an explicitly unknown exit/duration. Distinguishes completion, resume verification and postprocessing costs; overlapping/nested command durations must not be summed. |
| `tables/measured_cost_and_expansion_scenario.csv` | Measured per-model totals over three horizons and a labelled same-cost 15-repetition scenario; this is not a forecast for all four tasks. |
| `tables/comparison.csv` | Convenience join of the nine point rows with both interval levels and horizon minutes. The original point/interval CSVs remain the metric sources. |

Per-observation evidence is in `runs/pilot_v1_20260913/units/h{1,3,6}_f0_s42_{persistence,xgboost,attention_lstm}/`: `predictions.csv.gz` (truth, points and both interval levels), `calibration.csv.gz` (own-model calibration predictions/errors), `tuning.csv.gz`, and `training_history.csv.gz`. `payload.json` records fitted parameters, estimator identity, resources and membership. `model.json`, `model.ubj` or `model.pt` retains the actual final predictor; `COMPLETE.json` verifies each artifact's content hash. Empty persistence tuning/history files represent no model learning.

`figures/pilot_comparison.png` and `.svg` contain the readable comparison figure; `figure_sources.json` binds it to the two source metric CSVs by SHA-256. `validation/output_validation.json` is the metric/membership/checkpoint validation result; `validation/resume_integrity.json` records actual unchanged-checkpoint reuse. Hardware and thread settings are retained in `runs/pilot_v1_20260913/execution_environment.json` and the BDG2 preparation JSON.

## Completion evidence and measured results

**Completed and output-validated.** The completion run returned **exit status 0**. All **9/9 point-summary cells** and **18/18 interval-quality cells** passed validation, with **zero missing, duplicate or failed cells**. All eighteen interval cells have sufficient finite calibration support. The validator recomputed point errors, coverage, MPIW, Winkler scores, radii, ranks and bounds from saved predictions/calibration errors, checked identical support across models and levels, matched membership to the frozen design, and verified all checkpoint artifact hashes.

The original five completed units were reused with all 35 files unchanged. A subsequent complete-run resume reused **all nine units with zero refits**, preserving all 63 unit files byte-for-byte. Its exit status and the output validator's exit status were both **0**. The interrupted original launch has **unknown exit status**, not a claimed success. The bounded pilot is complete; **global study readiness and publication readiness remain false**.

### Point metrics

| Horizon (min) | Model | MAE (°C) | RMSE (°C) |
|---|---|---|---|
| 10 | Persistence | 0.2038 | 0.3275 |
| 10 | XGBoost | 0.2445 | 0.3533 |
| 10 | Attention-LSTM | 0.3611 | 0.4866 |
| 30 | Persistence | 0.3773 | 0.6099 |
| 30 | XGBoost | 0.5613 | 0.7299 |
| 30 | Attention-LSTM | 0.6531 | 0.8792 |
| 60 | Persistence | 0.5481 | 0.8776 |
| 60 | XGBoost | 0.7590 | 0.9858 |
| 60 | Attention-LSTM | 1.2464 | 1.5677 |

### Interval quality

Coverage percentages below are empirical. Every cell evaluates 9,907 rows; horizon-specific calibration counts are given in the design table. MPIW and Winkler scores are in °C.

| Horizon (min) | Model | Nominal | Coverage | MPIW | Winkler |
|---|---|---|---|---|---|
| 10 | Persistence | 90% | 92.05% | 1.0000 | 1.5598 |
| 10 | Persistence | 95% | 95.96% | 1.4000 | 1.9842 |
| 10 | XGBoost | 90% | 88.72% | 0.9956 | 1.6335 |
| 10 | XGBoost | 95% | 93.63% | 1.2712 | 2.0766 |
| 10 | Attention-LSTM | 90% | 87.24% | 1.3804 | 2.1772 |
| 10 | Attention-LSTM | 95% | 92.28% | 1.6681 | 2.6857 |
| 30 | Persistence | 90% | 89.27% | 1.6000 | 2.9449 |
| 30 | Persistence | 95% | 94.18% | 2.2000 | 3.8255 |
| 30 | XGBoost | 90% | 76.57% | 1.5938 | 3.4327 |
| 30 | XGBoost | 95% | 88.03% | 2.0760 | 4.1208 |
| 30 | Attention-LSTM | 90% | 82.10% | 2.1020 | 4.0572 |
| 30 | Attention-LSTM | 95% | 89.70% | 2.6310 | 5.0885 |
| 60 | Persistence | 90% | 89.39% | 2.4000 | 4.2199 |
| 60 | Persistence | 95% | 94.02% | 3.2000 | 5.5474 |
| 60 | XGBoost | 90% | 77.53% | 2.2696 | 4.4371 |
| 60 | XGBoost | 95% | 88.19% | 2.7936 | 5.3711 |
| 60 | Attention-LSTM | 90% | 71.92% | 3.2909 | 7.8195 |
| 60 | Attention-LSTM | 95% | 80.73% | 3.9119 | 10.0489 |

### Model computation

Measured time is in seconds; RSS is in MiB (2²⁰ bytes). These are the delivered units' measurements, spanning the original and resumed processes. Persistence's tiny final-fit value measures constructor overhead. Its point-summary tuning time is zero; the raw resource CSV retains the timing of the empty tuning branch.

| Horizon (min) | Model | Tuning s | Final fit s | Calibration s | Inference s | Rows/s | Baseline RSS MiB | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| 10 | Persistence | 0.000 | 0.000 | 0.0054 | 0.0040 | 2,462,039 | 391.4 | 391.5 |
| 10 | XGBoost | 4.354 | 1.283 | 0.1058 | 0.1026 | 96,578 | 393.5 | 502.3 |
| 10 | Attention-LSTM | 252.916 | 82.528 | 0.3792 | 0.3654 | 27,115 | 485.4 | 681.4 |
| 30 | Persistence | 0.000 | 0.001 | 0.0052 | 0.0042 | 2,377,490 | 661.6 | 661.6 |
| 30 | XGBoost | 4.190 | 1.242 | 0.1014 | 0.1013 | 97,775 | 660.4 | 670.0 |
| 30 | Attention-LSTM | 241.381 | 68.477 | 0.5106 | 0.5226 | 18,958 | 403.1 | 518.5 |
| 60 | Persistence | 0.000 | 0.000 | 0.0053 | 0.0041 | 2,429,794 | 486.0 | 486.0 |
| 60 | XGBoost | 4.983 | 1.330 | 0.1094 | 0.1073 | 92,334 | 486.1 | 598.6 |
| 60 | Attention-LSTM | 164.952 | 51.453 | 0.3881 | 0.4451 | 22,258 | 592.5 | 639.6 |

The completion invocation ran from **2026-09-13T04:35:36.069147+00:00** to **2026-09-13T04:45:19.035244+00:00**, taking **582.96 seconds**. It reused five units and computed four; this is not a nine-unit fresh-run runtime. The delivered units' four measured phases sum to **882.36 seconds**. Data preparation, checkpoint I/O, validation and abandoned partial tuning are outside that phase sum.

Selected candidates are shown below; complete parameters remain in the frozen configuration and each unit's payload. Candidate choice and epoch counts came only from the frozen inner folds.

| Horizon (min) | Model | Candidate ID | Parameters | Final epochs |
|---|---|---|---|---|
| 10 | XGBoost | 0 | depth=3; trees=400 | N/A |
| 10 | Attention-LSTM | 0 | learning rate=0.001; hidden size=64 | 20 |
| 30 | XGBoost | 0 | depth=3; trees=400 | N/A |
| 30 | Attention-LSTM | 0 | learning rate=0.001; hidden size=64 | 14 |
| 60 | XGBoost | 0 | depth=3; trees=400 | N/A |
| 60 | Attention-LSTM | 1 | learning rate=0.0005; hidden size=64 | 11 |

### Separate BDG2 preparation measurement

**No BDG2 models were fitted** (`models_fitted=0`). The full retained ten-building cohort was processed, and every eligible sequence was traversed in batches of 256 at every configured horizon. The separate preparation command returned exit status **0**. Its aggregate resource measurement was **11.28 seconds**, with sampled peak RSS **0.794 GiB** and minimum available system RAM **3.213 GiB**. The aggregate includes the adapter and horizon stages; do not add it to those components.

| Horizon (hours) | Eligible rows | Channels | Sequence length | Lazy stored MiB | Equivalent full tensor MiB | Stage peak RSS MiB | Stage seconds |
|---|---|---|---|---|---|---|---|
| 1 | 172662 | 7 | 24 | 7.5 | 110.7 | 519.2 | 1.95 |
| 3 | 172662 | 7 | 24 | 7.5 | 110.7 | 499.7 | 1.97 |
| 6 | 172662 | 7 | 24 | 7.5 | 110.7 | 519.6 | 2.00 |

The equivalent full-tensor figure is an arithmetic size estimate, not an allocated tensor or measured process peak. Lazy storage is only one component of memory: flat features, preprocessing copies, Python/library allocations and batching also consume RAM. This measurement establishes preparation feasibility for the retained cohort; it does not measure BDG2 tuning, fitting, calibration or inference cost.

### Expansion scenario

| Model | Measured three-horizon phases (s) | 15 equal-cost repetitions (s) | 15 equal-cost repetitions (min) |
|---|---|---|---|
| Attention-LSTM | 864.32 | 12964.76 | 216.08 |
| Persistence | 0.03 | 0.45 | 0.01 |
| XGBoost | 18.01 | 270.13 | 4.50 |

Repeating this PLEIA three-horizon workload at identical cost for **three folds × five seeds** gives a mechanical scenario of **220.59 minutes** of measured model phases. This is a total 15-repetition scenario, not fifteen additional runs, not a confidence interval and not an ETA. Other folds have different fitting/calibration sizes and selected epoch counts; memory pressure, I/O, system load and interruptions also affect cost. **PLEIA energy, RICO and BDG2 model-fitting costs remain unmeasured.** No four-task runtime estimate or GPU speed-up is inferred. The full comparison's 195 paired units / 585 point cells / 1,170 interval-quality cells remains separate work; this pilot does not authorise that launch.

## Interpretation and remaining work

Within this pilot, **Attention-LSTM incurred more computation and had higher MAE, RMSE and Winkler scores than both comparators at every horizon and both interval levels**. Its four measured phases totalled **864.32 seconds**, versus **18.01 seconds** for XGBoost, approximately **48 times** as much. This is a descriptive comparison under the frozen two-candidate budgets, one outer fold and seed 42; it does not establish statistical superiority, an architecture-wide ranking or final dissertation performance.

Persistence had the lowest observed point error at all three horizons. XGBoost's narrower intervals came with lower achieved coverage than persistence. At 60 minutes and nominal 95%, persistence achieved **94.02% coverage / 3.2000°C MPIW / 5.5474°C Winkler**, XGBoost **88.19% / 2.7936°C / 5.3711°C**, and Attention-LSTM **80.73% / 3.9119°C / 10.0489°C**. Thus even a slightly lower interval score or width should not be read as meeting the coverage target. At 30 minutes LSTM covered more observations than XGBoost, but used wider intervals and had a worse Winkler score.

**Output validation is not a coverage-target test:** 16 of the 18 empirical coverage estimates were below their nominal levels. Only persistence at 10 minutes exceeded both nominal levels. All eighteen outputs nevertheless passed recomputation, support and provenance checks. Fixed calibration under temporal dependence does not guarantee these held-out empirical proportions. The pilot does not identify the cause of the coverage gaps, and no candidates, intervals or study design were changed in response to outer-test performance. Previously inspected data remain previously inspected; no paired uncertainty or untouched-holdout claim is made.

![PLEIA pilot point errors, coverage, interval width and computational cost](smart_building_conformal/outputs/model_comparison_pilot_v1/figures/pilot_comparison.png)

The 1,800 × 1,200 PNG was visually inspected: titles, model legend, horizon labels, nominal-level line styles and the scope note are readable and unclipped. The SVG is also retained for reuse. Both figures are linked to the exact metric CSV hashes.

### Hardware and memory implications

Measurements used an **Intel Core i7-12700H, 20 logical processors, 15.73 GiB physical RAM**, Windows build 26200 and the existing CPU Python/PyTorch environment. Numerical libraries and Torch used one thread; XGBoost used `n_jobs=1`; batches were 256. There was no dependency change, GPU execution or concurrent research fit. Available RAM at the original launch snapshot was **2.67 GiB**.

The largest sampled model-phase RSS was **681.4 MiB**, and the smallest available-RAM sample during the delivered model phases was **2.24 GiB**. These phase values exclude earlier preprocessing peaks. PLEIA's protocol-freeze preparation measured **2.286 GiB peak RSS** and a **2.289 GiB OS lifetime peak**; the actual fitting processes also recorded roughly **2.289 GiB lifetime peaks** from startup/preparation. The initial freeze recorded an extreme transient minimum of **794,624 bytes (0.758 MiB) available RAM**. This sample should not be hidden behind the lower model-only peaks. Recheck RAM headroom for the approximately 2.3 GiB preprocessing peak before planning a broader run; serial fitting and lazy sequences do not remove adapter/preprocessing allocations.

BDG2's separately measured aggregate sampled peak was **0.794 GiB**, while its OS lifetime peak was **0.965 GiB**. The latter catches a higher transient than the 50 ms samples. This preparation measurement and the PLEIA measurements occurred in different process/system-memory states; their absolute RSS values are not isolated model memory requirements. The CSVs retain baselines, private memory, incremental peaks, available RAM and sampling intervals so those limits remain visible.

### Remaining work and next task

The next concrete task is to **freeze and reconcile the operational alert-selection design before a core research rerun**: define the two-inner-fold aggregation, confidence-bound feasibility, recall/workload endpoints, precision/F-beta and delay ties, matched-budget comparisons, synthetic fault families/severities and paired clean-counterfactual workload. Then implement and validate those choices against the repaired temporal/group split machinery. The pilot's inner-fold model tuning does not complete that operational requirement.

The completion plan also retains:

1. The full four-task model comparison, all 13 task/horizon combinations, multiple outer folds/seeds, matched own-model 90%/95% intervals and group-appropriate uncertainty; measure PLEIA energy, RICO and BDG2 fitting costs before claiming an overall runtime.
2. All **60 repaired core units**, their **240 ablation rows**, and **900 robustness cells**, after the unresolved methodology is reconciled. The empty historical extension remains untouched.
3. Explicit **DSCP and seasonal-baseline evaluation**, and the **group-recovery estimand/inference**, without substituting this fixed split-conformal pilot for those methods.
4. Dataset/method source verification, source-linked final figures, and then slide/candidature-report revisions grounded in validated broader evidence.

No full study was launched and no publication-ready marker was issued. The current recovery status and panel matrix point to this pilot while retaining those unresolved requirements.

Final preservation verification rechecked **554 historical source-data/output files against the existing entry backup, with zero mismatches**. The original repair backup and bundles are retained. The frozen implementation/protocol and completed pilot artifacts are recorded in local commits on the existing branch; nothing was pushed. `validation/preservation_verification.json` records the historical-file check.

Final delivery checks also passed: all **nine listed CSV files** have the expected row counts; all **36 model-phase resource rows** match the unit timing summaries; throughput agrees with recorded evaluation count/time; figure hashes match the metric sources; and the frozen source hash is unchanged. `validation/delivery_validation.json` contains the file hashes and visual-review record. Those presentation/export checks required no new fits or changes to the frozen design.

Git attributes preserve pilot configuration, protocol and output bytes without line-ending conversion. `validation/evaluated_source.zip` and `evaluated_source.json` additionally retain the exact evaluated Python source bytes and archive/source hashes. If reproducing in a separate checkout whose source hash differs solely because of Git line-ending conversion, use that exact source snapshot there before attempting resume. The evaluated working source was not altered after freezing.
