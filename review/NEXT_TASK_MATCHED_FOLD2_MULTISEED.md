# Complete the five-seed fold-2 comparison and explain the observed failures

## Outcome and authorization

Continue the ConfoSense study from `review/matched-overnight-20260914`, publication commit `3df9cbd480ffbfeac640580829e88c274fba2083`. The completed twelve-unit batch and its original evidence remain preserved.

The user authorizes **all 52 remaining outer-fold-2 matched units at model seeds 43, 44, 45 and 46**, their necessary orchestration, independent validation, analysis, verified backup and publication to a new review branch. Proceed through the four seed blocks without requesting permission between blocks. These are existing cells in the frozen study matrix, not additional model designs.

This completes five training seeds for all thirteen task/horizon combinations in fold 2. It measures sensitivity to model-training randomness on the same evaluation periods. It does not replace the remaining outer folds or the interval-method and operational experiments.

Alongside this execution, produce a **bounded no-fitting diagnosis** of the observed point-error and interval-coverage failures from existing artifacts. Do not interpret another seed as a repair for distribution change or poor calibration.

## Read and preserve the current state

Read the current `MATCHED_OVERNIGHT_BATCH_REPORT.md`, `review/matched_overnight_20260914/EVIDENCE_INDEX.md`, its `PANEL2_NUMERICAL_RESPONSE.md`, `PILOT_DIAGNOSTICS.md`, `review/CURRENT_EVIDENCE.md` and applicable repository instructions.

The handoff branch `review/pilot-evidence-20260913` carries instructions on an old application tree. Retrieve **this document only** using its pinned commit/raw URL or `git show`; do not merge or check out that branch's code.

Verify actual local HEAD, working changes, existing partial runs and active processes. Preserve legitimate local progress. Start or resume a new branch such as `review/matched-fold2-multiseed-20260914` from the verified current experiment lineage. Do not reset, force-push, merge into main, change previous review heads or overwrite completed scientific artifacts.

Retain the installed CPU environment and local source datasets. Use the correct `smart_building_conformal` working directory; no package upgrades, unrelated data downloads or paid compute.

## Exact execution scope

Canonical sources at the entry commit:

- `smart_building_conformal/outputs/amendment005/support_design_v1/experiment_matrix.csv`
- `smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/analysis_v1/remaining_queue_updated.csv`
- `review/matched_overnight_20260914/delivery_v1/proposed_seed43_replication.csv`

Select all rows from the remaining paired-unit queue satisfying **outer_fold=2 and model_seed in [43,44,45,46]**. Require exactly 52 unique dataset/horizon/fold/seed keys. Freeze a new scope file without editing the original matrix, proposal or queue.

Execute seed43 first, then 44, 45, 46. Within each seed preserve the published queue order:

| Dataset | Horizon steps | Physical horizons |
|---|---|---|
| pleia_energy | 1, 3, 6 | 10, 30, 60 minutes |
| rico | 5, 15, 30, 60 | 5, 15, 30, 60 minutes |
| bdg2 | 1, 3, 6 | 1, 3, 6 hours |
| pleia | 1, 3, 6 | 10, 30, 60 minutes |

Every unit uses persistence, XGBoost and Attention-LSTM with own-model 90%/95% absolute split-conformal intervals.

Per seed: **13 units, 104 tuning +26 final learned fits, 39 point cells, 78 interval cells, 78 saved-model calibration/test prediction checks**.

For this task: **52 units, 416 tuning +104 final =520 planned learned fits, 156 point cells, 312 interval cells, 312 saved-model checks and 52 completed zero-fit resumes**. Failed/interrupted attempts must be reported separately. Do not repeat the existing seed42 models.

If all keys validate, cumulative completion becomes **70/195 paired units, 210/585 point cells and 420/1170 interval cells; 125 paired units remain**. The fold2 subset is then complete at **65 paired units /195 point /390 interval cells**, with the five existing additional-fold units kept separate.

## Brief diagnosis before expansion

Use already saved seed42 predictions, calibration residuals, learning histories, protocols and raw development data where needed. **No new fitting and no repeated historical tuning reproduction.** Reuse the previous verified audit and inner-prediction files.

Address three concrete questions:

1. **Where does learned point forecasting fail?** For PLEIA temperature and RICO, tabulate exact fit/inner-validation/final-calibration/test periods, target and permitted-covariate ranges, prediction-minus-truth bias and MAE/RMSE. Compare persistence on the identical support. Use original RICO runs/phases and distinguish sample-weighted from equal-run summaries. Quantify observed range shifts and error patterns; do not claim that correlation identifies a cause.
2. **Why do the fixed intervals miss?** For each model/task/horizon, compare the frozen calibration radius with the empirical calibration and test absolute-error distributions, actual exceedance rate and time-block/run coverage. Include PLEIA energy, where persistence also undercovers, and BDG2 as the contrasting better-calibrated case. Any test-residual quantile is a labelled retrospective diagnostic only; it must never set a prediction interval, hyperparameter or decision threshold.
3. **Is any new correctness defect demonstrated?** Check targeted evidence for alignment, current-observation availability, schema/channel order, train-only normalization/inversion and saved-model identity only where the new evidence raises a concrete unresolved question. Reuse checks that already resolve these questions. Separate a confirmed implementation defect, a measured distribution change and an untested modeling hypothesis.

Write `MATCHED_FAILURE_DIAGNOSIS.md` and supporting CSVs with exact source identities. Clearly distinguish the older pilot's inner folds from the current outer-fold-2 fit/calibration/test roles. Overlapping calendar periods across experiments do not make their model fits identical.

This diagnosis is not a new open-ended audit or a prerequisite that depends on favorable findings. If it finds no unresolved correctness defect, continue immediately through all authorized fits. Undercoverage, a persistence win or a descriptive distribution shift is not a stopping condition. If it demonstrates a scientific defect that invalidates evaluation, preserve evidence, stop affected expansion and report the precise affected scope; never hide it behind more runs.

## Fixed scientific design and seed verification

Preserve the existing `src.matched_forecasting005` scientific source, whose current digest is `cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e`, unless an actual correctness defect requires documented repair.

Keep the existing two candidates per learned model, two purged inner folds, MAE selection/tie rule, final epoch calculation, train-only scaling, common support, exact conformal order statistics, unclipped predictions and unchanged raw meter values.

Retain XGBoost depth3/depth5 with 400 trees and all other frozen parameters. Retain Attention-LSTM hidden64/dropout.2/batch256, learning rates .001/.0005, 24-step sequences, 30-epoch ceiling and patience5. Do not add residual targets, new features, extra epochs, phase filtering or model-selection changes within this replication.

For each key, verify that the requested model seed reaches the actual XGBoost estimator and all existing NumPy/Torch/training-shuffle seed paths; export actual seed/estimator metadata. A different seed label with the same hard-coded training seed is not a new replicate. Do not require predictions to differ as a correctness test: deterministic outcomes can legitimately match.

Verify that data, target IDs, roles and preprocessing support for each task/horizon are unchanged across seeds. Preserve historical authorization identities; create a new explicit authorization for this scope. Freeze all 52 protocols and their exact run/validation/resume argv, source/config/package/data/membership identities, then pass fresh no-fit readiness and commit the evaluated code plus joint manifest before fitting.

Persistence has no learned fitting or seed variability on identical data. Retain valid per-unit pairing and explicitly label repeated seed rows as deterministic aliases, even if they are recomputed for compatibility. Do not count baseline aliases as independent evidence or invent missing resource measurements.

## Reuse the durable coordinator

The last batch's coordinator and Windows atomic-write recovery worked. Reuse or minimally parameterize them in a **new batch directory**; do not overwrite `review/matched_overnight_20260914/common.py`, its authorization, progress files or historical helper code. The old helper contains hard-coded keys and paths and must not accidentally launch seed42 again.

Before fitting, verify new scope/count guards, distinct output/receipt paths, seed propagation and restart bookkeeping. Use focused existing tests and dummy subprocess fixtures for orchestration changes; do not replay completed real experiments or add unrelated test suites.

Run one process at a time through the installed interpreter and `scripts/log_pilot_command.py`. Preserve:

- Detached continuous progression independent of a new chat turn.
- Locking and live-process identity checks, an atomic progress ledger, immutable attempt logs, actual PID/argv/start/end/exit receipts and surviving-worker adoption.
- Per-model checkpoints, explicit partial resume, independent validation and completed resume with fitting forbidden.
- External validation/resume receipts and byte-preservation checks for completed run directories.
- The proven bounded retry for a Windows bookkeeping rename denial. Do not repeat a learned fit because a progress update failed.
- Automatic report/progress updates and backup/publication checkpoints after each completed seed. Continue to the next seed on integrity/resource checks, never on a preferred numerical result.
- Final automatic aggregation after seed46. Do not end with only a promise to await a background notification.

If a chat session ends, leave a genuinely live durable process or an accurately recorded failure, with exact restart commands. Do not assume notifications or detached sessions work without checking the environment.

## Resource policy and acceptance

Keep CPU-only, one numerical/Torch thread, `n_jobs=1`, lazy sequences and batch256. The 3 GiB available-RAM reference remains **nonblocking**; log it. Retain the 256 MiB epoch floor and 8 GiB free-disk check before each unit. Record actual model-phase CPU and wall time separately, preparation, validation/resume overhead and action/lifetime peak memory.

The current queue's 52-unit scenario sums to approximately **1.11–21.62 model-hours**, excluding preparation/I/O/verification. This broad scenario is not a statistical interval, deadline or guarantee. Recalculate and report it from the frozen scope; use observed seed-block times to improve planning without changing scope. Continue healthy progress beyond an estimate. Do not authorize cloud charges or change machine-wide settings.

For every unit require actual exit0, fit-journal reconciliation, independent 3-point/6-interval arithmetic, exact own-model ranks and support, reconstructed inner candidate/epoch choices, six saved-model prediction checks under existing tolerances, and a zero-fit resume preserving every run file. Summaries must reconcile with per-original-group counts and sums of squared errors.

Stop affected work for an unresolved scientific identity/metric/model mismatch, corrupt checkpoint, nonfinite prediction or hard resource failure. A reporting-only defect may be corrected separately and validated without refitting. An authentication/publication issue must not prevent already authorized local execution and backup.

## Analysis and dissertation evidence

After each seed block, update provisional summaries; after all four, create:

- `MATCHED_FOLD2_MULTISEED_REPORT.md` and `MATCHED_FAILURE_DIAGNOSIS.md`.
- A complete fold2 seed42–46 comparison, separate new-only/cumulative tables and an evidence-reuse ledger. Preserve all five seed values, not just the best seed.
- Per task/horizon/model/level mean, sample standard deviation, minimum and maximum across training seeds, clearly labelled **training-seed variability on the same evaluation support**. These are not population confidence intervals.
- Paired LSTM-minus-XGBoost and learned-minus-persistence contrasts within the same seed and target support. Include MAE/RMSE, coverage, both explicitly named signed and absolute deviations from nominal, MPIW, Winkler and actual CPU/wall costs. Never label a signed difference as an absolute calibration error.
- Per-run/per-building and RICO phase summaries with support counts. Repeated seeds or dependent horizons must not create extra independent buildings, runs or time periods.
- Source-linked figures for point errors, achieved coverage, width/Winkler and computational benefit by physical horizon, with source-CSV hashes. Do not average Celsius and kWh into a global model ranking.
- An updated quantitative Panel-2 response: whether any observed interval-score benefit for LSTM is consistent across seeds, what coverage accompanies it and what extra measured CPU cost it requires. Do not use width alone, a favorable individual seed, a nonsignificant difference or a five-seed sample to claim general superiority/equivalence.
- A completion overlay, remaining exact queue and updated measured timing references. Preserve original matrices and previous overlays.

Use these results to explain that the implemented static absolute-error interval benchmark is only one part of the dissertation methodology. Do not present it as the completed CQR/EnbPI/DSCP or alerting evaluation.

Finally produce a concise **implementation readiness map** for the remaining interval-method and alert stages, using the existing execution plan: exact available entrypoints, actual estimator owners, shared-fit opportunities, causal delayed-residual/group constraints, supported versus unavailable endpoints and the smallest next executable package. This is a bounded inventory from existing code, not another protocol redesign. Keep the remaining outer folds visible as necessary evidence. Do not launch unlisted fits, silently drop methods, revise amendment-004 feasibility rules, or replace unsupported deployment claims with conditional-challenge claims.

## Publish and deliver

Publication to a **non-main review branch is authorized**. Update `review/CURRENT_EVIDENCE.md`, recovery notes and the panel-response matrix. Publish the complete new code/protocol manifests, numerical CSVs, distributable fitted artifacts, verification receipts, reports and reproducible figures using existing notices and lossless large-file handling.

Preserve main, all prior review heads, historical scientific artifacts and the backup chain outside OneDrive. Verify remote commit and file hashes plus representative exact downloads. If authentication alone blocks publication, retain a complete local commit and backup and state the actual blocker.

Report the published branch/SHA, evaluated source SHA(s), actual fit/unit/metric/check counts, elapsed and CPU cost, peak memory, concise numerical findings, limitations and the next executable stage. A complete five-seed fold2 slice is a milestone; full-study readiness remains false until its remaining required evidence is complete.
