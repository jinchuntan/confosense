# ConfoSense integration repair report

13 September 2026. Paths below are relative to `smart_building_conformal/` unless stated otherwise.

**Outcome:** confirmed temporal/group split, event-scaling, prediction-attribution and recalibration defects have been repaired and exercised through engine paths. Future core and extension units retain predictions/bounds and support verified resume. Report generation now distinguishes missing, smoke and historical evidence. **No research-scale fit, full experiment, dependency change, push, merge or history reset was performed.** The remaining methodology decisions below must be resolved before the next research run. No new publication-ready marker was issued.

## Preservation and environment

- Entry branch: `fix/final-dissertation-study`; HEAD `35a5bade8a728edaa3e20753c5fba939426a43cc`, 25 commits ahead / 0 behind its recorded upstream. Only the two recovery documents were untracked. No intervening source changes were discarded.
- Verified backup: `C:/Users/nigel/ConfoSenseBackups/integration_20260913_102403`. Available space before copying: **49,945,255,936 bytes**. Snapshot: **670 files, 2,790,842,412 bytes**, including raw/interim/processed data, existing outputs, ignored runs and the two recovery documents. Every copied file was SHA-256 checked against its source.
- `history.bundle` contains all Git refs and passed `git bundle verify`. Its SHA-256 is `788396c678b4561c97d1883f6e17b9015fbcbc2f0ad050b53d90eadba2230823`. The backup includes `BACKUP_MANIFEST.json`, `bundle_verification.txt`, `environment_freeze.txt` and `snapshot/`. Git internals are represented by the bundle; virtual environments, caches and notebook checkpoints were excluded. Existing `C:/cfs_venv` was not changed.
- Recovery documents were first preserved in local commit `55109ca`. Subsequent repair commits are listed in Git history. The backup represents the entry state, not an assertion that it contains later repairs.
- Execution used **`C:/cfs_venv/Scripts/python.exe`**. Laptop: Intel i7-12700H, 14 cores / 20 logical processors; about **15.73 GiB physical RAM**. Free RAM was about **2.38 GiB** during initial inspection and **1.67 GiB** during later work. These are snapshots, not measured model peaks. The RTX 3050 has 4 GB VRAM, but installed PyTorch is **2.13.0+cpu** and the LSTM selects CPU. GPU acceleration was neither installed nor assumed. Disk free after backup was about 43.5 GiB.

## Confirmed defects and repairs

| Finding | Evidence and repair | Limit of the conclusion |
|---|---|---|
| Inner selection did not purge targets reaching later blocks | Shared `split_integrity.ordered_blocks` enforces `max(earlier target_time) < min(later origin_time)` at train/calibration and calibration/selection boundaries. Engine selection asserts these boundaries. | The existing one inner holdout is now safe; it is not two inner folds. |
| Refit split used raw row fractions, including inside RICO runs | Shared refit split cuts whole RICO runs; all temporal datasets cut unique origin timestamps. Refit-to-test availability is checked too. | Purging changes membership and therefore invalidates old fitted estimates. |
| BDG2 boundaries could split simultaneous building observations | Common origin-time cuts keep all buildings on the same temporal boundary. | This is within-building temporal assessment, not leave-building-out evaluation. |
| Event scales were taken from original partition labels, including data unavailable to earlier folds | Inner scales now use only `inner_train`; outer/extension scales use only refit training. Membership hashes and actual scale maps are saved in per-unit provenance. | Frozen cohort/target choices were previously inspected and remain so. |
| Local interpolation could use future neighbours | Corrected core/extension remask adapter-marked missing values and use bounded forward filling before rebuilding windows. XGBoost tuning and LSTM early stopping accept purged, run-safe training metadata; LSTM normalisation uses the resulting training subset only. | Unflagged upstream-imputed PLEIA values cannot be reversed locally. Legacy diagnostic entry points retain their historical behaviour; they are not repaired dissertation runners. |
| `point_model` labelled a disconnected persistence/XGBoost fit | Removed unrelated point selection from the interval-owned alert core. `IntervalEstimator` supplies its own point and calibration predictions, class, seed and fallback. CQR/uncalibrated quantiles own HistGradientBoosting; EnbPI owns its fitted base estimator. Outer evaluation rejects a conflicting class/model/fallback label. | This repairs attribution. It does not create LSTM-CQR or generic XGBoost-CQR comparisons. |
| Model labels varied seeds while fits used seed zero | Fitted estimators and EnbPI bootstrap now consume the recorded model seed. Event seed is a separate field and follows the existing explicit one-to-one seed pairing. Event RNG no longer uses process-randomised Python string hashes. | Five paired model/event seeds are not 25 combinations or five independent datasets. |
| Recalibration consumed zero test residuals and CQR calibration points for other methods | Shared core/extension stream receives observed `y - own_point_prediction`, with own-model calibration errors. Updates require target time at or before forecast origin; test residual state is isolated by group. | For an unseen RICO run, initial calibration uses the fixed historical pool; only that run's subsequent residuals update its state. This explicit cross-run calibration assumption is not an exchangeability guarantee. |
| Inner selection was also affected by incorrect residual streams | Corrected residuals flow through every periodic/rolling candidate before selection, as well as outer evaluation and ablations. | Rerun **all 60 core units**, not only the 18 historical rows selecting periodic recalibration. |
| Core and extension could evaluate different clean streams | Both use the same `IntervalEstimator`, refit splitter and recalibration implementation. Deterministic engine tests compare clean and zero-control consumed bounds under static, periodic and rolling policies. | Faulted extension streams intentionally use corrupted, delayed observations. Core synthetic-event scoring remains a different, open-loop experiment; see design decisions. |
| Physical 360-minute rule and minimum-support settings were omitted | Rules are read from compiled protocol, including 4 violations / 360 minutes; declared minimum train/calibration/selection counts and interval calibration minimum are now compiled and enforced in core execution. | Unsupported physical rules remain inapplicable at a dataset's frequency. The instantaneous 1-of-1 reference retains the existing interpretation. |
| Extension pooled fault positions/recovery across assets | Fault detection now checks each group's local positions. Recovery is calculated and saved per group, including censoring. Ambiguous multi-group pooled delay/recovery scalars are missing instead of treating concatenated buildings as one timeline. | A multi-group recovery estimand and matching inference must still be declared. Single-group scalar meaning is retained. |
| In-memory-only runs and permissive completeness checks | Atomic per-unit checkpoints contain payloads, predictions, calibration predictions and hashes. Resume checks code/config/data identity, never overwrites a historical directory, skips complete units and rejects corruption, missing or duplicate cells. Full extension requires repaired core provenance and an explicit core path. | Checkpoints store complete experimental units, not partial estimator training. An interrupted unit is recomputed. |
| Report generators asserted missing/unsupported achievements | Both report entry points now generate evidence-status reports. Missing full extension inputs remain missing; explicitly supplied smoke timings are labelled **SMOKE ONLY**, with path/count. Historical CIs cannot become current findings merely by existing on disk. Publication validation also requires repaired lineage, design resolution and recomputed evidence. | Scientific validation is deliberately not automatic. Existing publication markers and metrics remain historical records. |

No evidence was found that the **48 abstentions were 48 software failures**, or that RICO loaded only three runs: the retained dataset has **207 runs**, with only three selected as outer tests. The earlier statistical audit's corrections to accounting and seed aggregation remain historical corrections; they did not test the integration defects found here. The other 204 RICO runs must not be called untouched tests, since many contributed to fitting/calibration.

## Actual-data membership audit

No models were fitted by `scripts/audit_integration_membership.py`. It used the current four-task data and every declared horizon:

| Task | Horizons in steps | Physical horizons | Windows by horizon |
|---|---|---|---|
| PLEIA temperature | 1, 3, 6 | 10, 30, 60 minutes | 49,535 at each horizon |
| PLEIA energy | 1, 3, 6 | 10, 30, 60 minutes | 49,537 at each horizon |
| RICO temperature | 5, 15, 30, 60 | 5, 15, 30, 60 minutes | 45,747; 43,677; 40,572; 34,362 |
| BDG2 electricity | 1, 3, 6 | 1, 3, 6 hours | 173,352 at each horizon |

| Audit | Boundary records | Unsafe boundaries | Scale scopes | Scopes outside allowed training |
|---|---:|---:|---:|---:|
| Before repair | 195 | **89** | 78 | **57** |
| After repair | 273 | **0** | 78 | **0** |

The after audit additionally includes 78 training/validation tuning boundaries. Therefore its larger denominator is not a changed definition of safety. Both audits include origin/target endpoints, row overlap, target overlap, RICO run intersections, per-role/group membership and SHA-256 membership fingerprints. Full records are in `outputs/integration_repair_20260913/{before,after}/`: `boundaries.csv`, `membership.csv`, `event_scale_membership.csv`, `summary.json`. The original membership audit was executed before editing the engine; rerunning `--phase before` against repaired source is not a historical reconstruction.

```powershell
# Work directory: smart_building_conformal
$env:OMP_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'; $env:PYTHONPATH='.'
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/audit_integration_membership.py --phase before --out outputs/integration_repair_20260913/before
& 'C:\cfs_venv\Scripts\python.exe' -B scripts/audit_integration_membership.py --phase after --out outputs/integration_repair_20260913/after
```

## Declared versus executed

| Dimension | Declaration | Historical core | Repaired code and remaining decision |
|---|---|---|---|
| Point models | Persistence, seasonal naive, XGBoost, Attention-LSTM | Persistence/XGBoost scored separately; their labels did not identify interval predictions | Actual interval-owned predictor is recorded. LSTM/seasonal/model-specific interval benchmark still needs a dedicated runner. |
| Interval methods | Uncalibrated quantiles, CQR, static/updated recentred EnbPI, DSCP | Four single-horizon methods; DSCP marked inapplicable | Attribution and stream handling fixed. DSCP requires a multi-horizon implementation path and a declared common support. |
| Horizons | All 13 task/horizon combinations above | Primary only: 1, 1, 5, 1 | All 13 audited; current alert driver still runs the four primary horizons. Audit coverage is not experimental coverage. |
| Nominal levels | Quality 90%/95%; operating 95/97.5/99/99.5% | Operational selection; smoke includes quality levels | Operating selection retained. Full model-specific quality grid remains absent. |
| Physical rules | Immediate reference plus 5/15/30/60/180/360 minutes | 360 omitted | Compiled declaration now drives candidates; inapplicable conversions remain explicit. |
| Inner evaluation | Two inner folds; minimum support | One 50/25/25 holdout; minima incompletely bound | Both boundaries/minima repaired. Decide and implement two-fold aggregation before claiming full protocol execution. |
| Seed roles | Model/event lists 42–46; bootstrap 20240601 | Model fits hard-coded zero; event placement varied | Actual model seed applied, event seed separate, one-to-one pairing retained. Bootstrap seed remains for inference only. |
| Alert selection | Confidence-bound recall/workload, F-beta and delay tie-break | Point-estimate bounds, precision fallback to recall, delay missing | Requires a precise inner resampling/precision/delay policy; do not silently alter it based on test outcomes. |
| Events/endpoints | Seven fault types, dataset-level type/severity balance, paired clean counterfactual workload, matched-budget comparison | Core uses four types; repeated per-group allocation; nonmatched episode workload on injected stream | Exact fault mappings and clean/corrupted endpoint definitions must be reconciled. Existing historical contrasts cannot establish equal-recall benefit. |

The compiled protocol is still Amendment 003 (`10437ab0…`). Its settings were not rewritten to agree with observed results. New engine summaries explicitly record `execution_scope=interval_owned_alert_core` and `full_declared_methodology_complete=false`.

## Decisions required before research fitting

1. **A common model-specific interval construction.** Recommended smallest comparison: ordinary split conformal around each fitted Attention-LSTM, XGBoost and persistence predictor, using its own calibration absolute errors. At level `1-alpha`, use the finite-sample order statistic at rank `ceil((n_cal+1)*(1-alpha))`, with an explicit infinite/inapplicable result if the rank exceeds `n_cal`; interval is `prediction ± q`. This is a proposed additional benchmark, not the existing HistGBR CQR and not an already-executed pairing. Freeze pooled-versus-group calibration and unseen-run fallback before fitting. Temporal/group dependence limits formal coverage claims.
2. **Two inner folds.** Recommended: two expanding, purged inner train/calibration/selection splits contained in the outer training pool; whole-run splits for RICO; fixed aggregation across both inner selections, never select the best inner fold. Freeze fold endpoints, weighting, feasibility CI construction and handling of inapplicable cells. The current safe single holdout must not be renamed two-fold nested validation.
3. **Operational endpoints and fault families.** Define the seven core fault operators at each frequency, balance across the dataset rather than restart the type list in each group, and compute workload on the paired clean stream. Freeze an inner-only operating curve/selection rule for a matched-budget comparison. Account for previously declared F-beta, confidence bounds and delay ties. Do not infer equal recall from an insignificant difference. These are necessary follow-up implementation work, not resolved by residual repair.
4. **DSCP and seasonal context.** Keep seasonal naive where valid, with explicit nonapplicability for short runs. Either implement the declared DSCP multi-horizon comparison on aligned targets or formally delimit the dissertation claim by amendment. Neither can silently count as completed.
5. **Robustness recovery across groups.** Per-group recovery is now retained with censoring. Choose a group-level estimand and inference that includes unrecovered groups; do not average only recovered buildings. Update extension statistics/figures to consume it before a full extension. Retain the declared contamination-family residual-offset adaptation separately from method-native intervals.

## Test evidence

Tests use deterministic fixtures and small actual fits only. Coverage includes actual engine inner/refit/outer calls across horizons, variable-length RICO groups, common BDG2 times, method-specific inner residuals, delayed/group-isolated static/periodic/rolling updates, clean/zero identity, fitted estimator identity/seeds/fallback, purged XGBoost CV, CPU LSTM normalisation, minimum support, group fault detection, interruption/resume, corrupt/missing/duplicate checkpoints and report gating.

```powershell
$env:OMP_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'
& 'C:\cfs_venv\Scripts\python.exe' -B -m pytest -o addopts="" -p no:cacheprovider -q tests/test_integration_repairs.py tests/test_integration_delivery.py tests/test_corrected_engine.py tests/test_robustness_extension.py tests/test_enbpi_causal.py tests/test_final_reports.py tests/test_validate_final_study.py
& 'C:\cfs_venv\Scripts\python.exe' -B -m pytest -o addopts="" -p no:cacheprovider -q -ra
```

Final focused result: **65 passed, 3 warnings in 27.82 seconds**. Final full suite: **294 passed, 1 skipped, 3 warnings in 46.12 seconds**. The skipped existing check is `tests/test_output_schema.py:119`, ?no interval predictions on disk?; it does not establish a missing experiment's output validity. MAPIE warnings came from the deliberately small bootstrap fixture (empty out-of-bag means/division); base-prediction identity assertions passed. Only fixture estimator sizes were reduced, not research settings.

The first full run was **293 passed, 1 failed, 1 skipped**. Its failure was the old test expecting historical artifacts to qualify as publication-ready. The replacement asserts that preserved historical evidence is rejected for repaired execution, while the validator accepts explicitly justified absent CIs as accounting. The failure and subsequent successful run are both retained. Earlier intermediate focused runs passed 49, 57 and 60 tests.

Logs: `outputs/integration_repair_20260913/focused_tests_final.txt` and `full_tests_final.txt`; earlier runs are retained as `focused_tests.txt` and `full_tests.txt`. Commands above were run from `smart_building_conformal`; output was redirected to the corresponding logs. `git diff --check` passed.

Read-only gate verification invoked `validate_final_study.run("outputs/final_dissertation_v2", run_tests=False, mode=...)` for `readiness`, `publication` and `extension`. All correctly returned **not ready**; `validation_gates.json` records every check. Publication fails on unresolved design, no recomputed evidence, historical execution lineage and incomplete declared methodology. Extension additionally lacks a completed full run. No marker-writing command was invoked.

Final preservation check: **554 historical data/output files checked against the entry backup, zero mismatches**, excluding the explicitly updated report documents. This includes historical metrics/provenance and publication markers. Details are in `outputs/integration_repair_20260913/preservation_verification.json`.

Local commits completed before this report: `55109ca` (recovered state), `467b38e` (split/interval execution and checkpoints), `7fd46b3` (evidence gating and interruption/delivery tests). This report, current recovery/panel status and final logs are committed separately. A supplementary `integration_repairs.bundle` in the same backup directory preserves the final committed repairs; its verification record is stored beside it. No commits were pushed.

## Affected artifacts and required reruns

| Artifact | Disposition | Required action |
|---|---|---|
| `outputs/full_study/`, preliminary runs | Preserve as previously inspected diagnostics | Never use to fill missing corrected LSTM interval/cost results. |
| Core `runs/full_20260831_220811`, matching `metrics/run_artifacts/` | Preserve all 60 outer and 240 ablation rows with original provenance | Recompute **all 60 units and all 240 ablations** after design reconciliation: boundaries, scales, seeds, rules and candidate residuals changed. |
| Core selections, per-event/per-group details and membership tables | Historical record only | Regenerate from new per-unit checkpoints; preserve abstention and diagnostic labels. |
| `final_cis.csv` | Statistically superseded | Do not present as current confidence intervals. |
| `final_cis_corrected.csv`, ledger, nominal/accounting audits, paired effects | Corrected summaries of old computation | Recompute from new raw results, with seeds aggregated before independent-unit inference and explicit NA CIs where justified. |
| `runs/robx_smoke` | Software/smoke evidence only | May retain for history; no full extension inference or runtime extrapolation. |
| Empty `runs/robx_full_20260902_080752` | No results | Start a **new** run after repaired core selection and recovery/statistical decisions. Current full grid: 60 units × 15 cells = **900 robustness cells**, 120 supplementary point rows and 60 timing rows. |
| Existing performance figures and old publication markers | Preserve; historical status | Rebuild figures from newly validated inference. Do not issue a replacement marker from test success. |
| Current report suite | Evidence-status text updated; remaining reports explicitly historical | Populate results only after source-linked experimental and statistical validation. Then revise slides and candidature report. |

## Smallest adequate next experiment and resource plan

**Next execution scope begins with code/design work, not a full launch:** freeze decisions 1–5; implement the common-support multi-horizon point/interval runner and measurements; adapt two-inner-fold selection, operational endpoints and per-group robustness inference; verify with small fixtures. Reuse the checkpoint store. Do not run the old legacy study runner as a shortcut.

Then run the following staged experiment, subject to that design being frozen:

1. **Resource pilot:** PLEIA temperature only; horizons **1, 3, 6**; one specified outer fold; model seed 42; Attention-LSTM, XGBoost and persistence; levels **90% and 95%**. This is six learned forecasting fits, plus their training-only tuning/early-stopping fits, three no-learning persistence streams, nine point summaries and eighteen interval-quality cells. Label it a pilot. No rows have been fitted for this pilot in this task. Separately measure largest-BDG2 feature/sequence construction memory without fitting.
2. **Required model comparison:** all four tasks and all **13 task/horizon combinations**, three frozen outer folds, five model seeds for learned models, the same seed set/support for paired summaries. There are **195 task/horizon/fold/seed units**, **585 point-summary cells** for three forecasters, and **1,170 interval-quality cells** at two levels. There are **390 learned final fits** before tuning costs; persistence needs only 39 unique task/horizon/fold prediction streams, reused for pairing without treating duplicate baselines as independent evidence. Add seasonal-naive context where valid; DSCP remains a separate declared multi-horizon analysis, not silently included in these counts.
3. **Core and robustness:** rerun all **60 primary-horizon core units** with all inner candidates and 240 ablations after the operational design is reconciled. Then run **60 extension units / 900 cells** using those new frozen selections and the same refit membership. Retain infeasible operational decisions with explicitly diagnostic evaluations. Supplementary XGBoost/persistence point rows in the extension do not substitute for the main LSTM comparison.

For each task/horizon/fold, intersect valid feature and sequence keys **before fitting and scoring**, including calibration support, so differences cannot be driven by LSTM history length or missingness. Preserve per-model `group_id`, origin, target time, clean truth, point prediction, lower/upper bounds, nominal level, calibration scores, fit parameters, all seed roles, membership hashes and interval construction. Report per-task/per-horizon coverage, **MPIW**, **Winkler**, **MAE/RMSE**, calibration size and evaluation exposure. Do not pool errors measured in incompatible temperature/energy units.

Measure training-only **tuning time**, final **fit time**, calibration time, **inference time** (batch size and per-row rate), per-unit wall-clock time, baseline and peak process RSS/private working set, and CPU/thread settings. Include descendants if a process-based tuner is used; preferably keep fitting serial. Aggregate paired model differences over independent runs/buildings/time blocks, with seeds aggregated first. Retain numerator/denominator and censoring information. A neutral or negative LSTM result is acceptable.

The laptop cannot safely use 20 parallel fitting jobs simply because it has 20 logical processors. Start with **one unit at a time, `n_jobs=1`, OMP/OpenBLAS/Torch threads=1**, and the existing declared batch sizes. LSTM test inference is now batched; training and validation tensors are still resident. For illustration, a float32 sequence array costs `N × sequence_length × channels × 4` bytes: 173,352 × 24 × 5 is about **79.4 MiB** before covariates, DataFrames, normalised copies, validation tensors, model state and activations. This arithmetic is not a measured peak. Avoid holding all horizons/models/datasets simultaneously; prepare, fit, checkpoint and release one unit. If pilot memory exceeds available headroom, first implement lazy/batched sequence loading and batched validation rather than silently downsample the research cohort.

No defensible full-run duration can be inferred from the old 4.5–8.8-second smoke interval fits. Estimate per-task/per-horizon total only from the measured pilot's tuning + refit + inference costs, with explicit scaling assumptions and an uncertainty range. Record current free RAM before each launch and abort/pause before fitting if the measured headroom requirement is not met. Available memory during this task was much lower than installed memory.

Core execution now supports `python -m src.corrected_study ... --out <new-run>` and `--resume`. Extension requires `python -m src.robustness_extension ... --core-artifacts <new-core-run> --out <new-extension-run>`, with `--resume` for recovery. Use the explicit existing Python path above. **These are interfaces for after the outstanding work, not instructions to start a full run now.** A code/config/data change requires a new directory; completed unit hashes, exact expected cell sets and frozen core provenance must match. Predictions and bounds survive interruption. No extra seed or repaired rerun makes previously inspected data newly unseen.


## Follow-up completed 13 September 2026

The resource pilot described above subsequently completed; the historical execution plan is retained as dated context. See [MODEL_COMPARISON_PILOT_REPORT.md](MODEL_COMPARISON_PILOT_REPORT.md) and the [current review index](review/CURRENT_EVIDENCE.md) for its source-linked evidence. Completion exit 0, all nine point and eighteen interval cells validated, and nine-unit resume required zero refits.

[PILOT_DIAGNOSTICS.md](PILOT_DIAGNOSTICS.md) records the bounded follow-up: 24 unchanged development fits reproduced; no demonstrated LSTM alignment/scaling/epoch defect; a preparation-allocation fix reduced sampled peak working set 52.1% in paired preparation-only checks with identical data/support. Revalidation preserved all 125 pilot/config/protocol files and 554 historical data/output files. Follow-up checks passed: 14 focused tests, 308 full tests with one skip and three existing warnings. Original pilot metrics and resource records were not rewritten.

[OPERATIONAL_EVALUATION_PLAN.md](OPERATIONAL_EVALUATION_PLAN.md) resolves the next specification as proposed amendment 004. Implement its selection/stream contracts and one synthetic two-inner-fold smoke next. All historical core/ablation reruns, DSCP/seasonal paths, group recovery and full robustness work remain pending; the global design/evidence readiness flags remain false until implementation and research validation. The separate review branch preserves the latest local history; main is unchanged.
