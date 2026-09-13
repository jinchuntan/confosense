# Execute and publish the twelve-unit matched overnight batch

## Authorization and outcome

The user authorizes the complete batch below, its necessary orchestration, validation, descriptive analysis, backups and publication to a new review branch. Continue autonomously through all twelve units and the final deliverables. This replaces the proposal-only status for these twelve keys; it does not authorize the entire remaining study queue.

Do not stop after a plan, readiness report, first successful unit or a request to approve the next listed unit. The user will be asleep. Continue while the work remains technically sound. A poor ranking, undercoverage or a longer runtime than estimated is a result to record, not a reason to change the experiment or end the batch.

The milestone is the first complete **13 task/horizon combinations at outer fold 2 and model seed 42**, using the two existing RICO h5 and BDG2 h1 units plus eleven of the new units. The twelfth new unit adds BDG2 h1/fold1. Including the existing three PLEIA-temperature fold0 units and PLEIA-energy h1/fold0, completion should reach **18/195 paired units, 54/585 point cells, 108/1170 interval cells**, with 177 paired units remaining. Independently reconcile these counts against identities; never count duplicate exports as additional experiments.

## Starting point and preservation

- Code base: `review/matched-rico-bdg2-20260914`, publication `d95405a005851dd7ffc3635a51034cb883b98671`.
- Read `RICO_BDG2_MATCHED_FIRST_UNITS_REPORT.md`, `MATCHED_NEXT_BATCH_PROPOSAL.md`, `review/matched_rico_bdg2_20260914/EVIDENCE_INDEX.md`, `review/CURRENT_EVIDENCE.md` and applicable repository instructions.
- Canonical proposed list: `smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/next_batch_units.csv`.
- Canonical scientific matrix: `smart_building_conformal/outputs/amendment005/support_design_v1/experiment_matrix.csv`.
- This handoff is distributed on the separate instruction branch `review/pilot-evidence-20260913`. Read its document with `git show` or a raw download. **Do not check out or merge that branch's old application code.**
- Inspect actual local HEAD, status and active study processes first. Preserve legitimate newer local work and existing partial runs. Use the verified code lineage, not a destructive reset. Create `review/matched-overnight-20260914` from the current verified experiment branch; if that name exists, inspect and resume it when appropriate rather than overwrite it.
- Keep main, previous review heads, completed runs, old protocols, original matrices and verified backups unchanged. Create fresh versioned authorization, protocols, analysis outputs and receipts.
- Use the installed environment and existing local datasets from the correct project working directory. Do not start unrelated downloads or install/upgrade packages.

## Exact authorized fitting scope

Read and verify the CSV against this table, retaining this order. All rows use model seed 42 and persistence, XGBoost and Attention-LSTM.

| Order | Dataset | Horizon steps | Physical horizon | Outer fold |
|---|---|---:|---|---:|
| 1 | pleia_energy | 1 | 10 minutes | 2 |
| 2 | pleia_energy | 3 | 30 minutes | 2 |
| 3 | pleia_energy | 6 | 60 minutes | 2 |
| 4 | rico | 15 | 15 minutes | 2 |
| 5 | rico | 30 | 30 minutes | 2 |
| 6 | rico | 60 | 60 minutes | 2 |
| 7 | bdg2 | 3 | 3 hours | 2 |
| 8 | bdg2 | 6 | 6 hours | 2 |
| 9 | bdg2 | 1 | 1 hour | 1 |
| 10 | pleia | 1 | 10 minutes | 2 |
| 11 | pleia | 3 | 30 minutes | 2 |
| 12 | pleia | 6 | 60 minutes | 2 |

Expected newly completed work: **12 paired units, 96 tuning fits, 24 final learned fits, 36 point cells and 72 interval cells**. These are 120 planned learned fits; persistence has no learned fit and the two interval levels share each fitted model. Log interrupted/failed attempts and any repeated incomplete fits separately from these planned completed fits.

These keys were selected from the previously published queue, not by whether their outer results favor a model. Do not substitute tasks, horizons, folds, seeds or easier subsets.

## Scientific procedure: retain the established matched design

Use `src.matched_forecasting005` and its existing model, support, checkpoint and independent-validation modules. There is no need for a new estimator implementation or a second scientific runner.

Preserve:
- Two frozen candidates per learned model and two purged inner validation folds; select by the existing equally weighted inner-fold MAE in original units and exact tie rule.
- XGBoost's existing depth-3/depth-5, 400-tree candidate grid and every pinned fixed parameter.
- Attention-LSTM's existing 64-unit attention architecture, dropout .2, batch256, learning rates .001/.0005, 24-step sequences, 30-epoch ceiling, patience5, training-only normalization, early-stopping rule and selected final epoch calculation.
- Persistence using actual `target_lag_0`.
- Final calibration excluded from tuning; unchanged split memberships, causal target-time boundaries and common target IDs across models within each unit.
- RICO's published whole-run chronological memberships and sequence boundaries; BDG2's same ten known buildings. Do not conflate old operational-support counts with matched sequence-support counts.
- Each fitted model's own absolute calibration residuals and symmetric 90%/95% split-conformal intervals, using the exact finite-sample order statistic. Preserve the explicit unsupported-rank behavior.
- Original PLEIA-energy values, zero/stall/catch-up behavior and all unclipped predictions/intervals. Do not silently remove outliers, change targets, pool residuals across models or truncate negative energy bounds.
- Actual estimator identity and representation/schema records. Equal target support does not imply identical flat-feature and sequence representations.

Do not change the scientific design in response to outer metrics. In particular, the earlier RICO LSTM undercoverage does not authorize retuning, phase removal or new calibration methods. Diagnose descriptive patterns after the frozen run; do not promote an untested explanation to a confirmed code defect.

## Freeze and preflight once, then execute

1. Create a new joint authorization with the twelve exact keys, this handoff's published SHA/path, the actual starting code commit, fit counts and `nonblocking_launch_ram: true`. Preserve the historical runner-provenance fields; record current authorization separately as in the previous task.
2. Verify pending versus completed/partial output paths by identity. Reuse valid completed models through supported resume; never overwrite or refit them for different scores. Assign unused output/design versions when genuinely necessary.
3. Freeze all twelve protocols before real fitting, using fresh data, role, source, configuration, package, matrix, membership and boundary identities. Save exact unit command arrays and actual role dates/counts in the joint manifest.
4. Pass fresh no-fit readiness for each unit and the applicable existing integrity tests. Do not repeat the entire historical audit or create new real-data pilot fits. If adding orchestration, test its ordering, failure handling and restart behavior with dummy commands, not extra learned models.
5. Commit the evaluated source, coordinator and joint manifest before fitting. Record the pre-fit source commit/hash. Later evidence-only commits must remain distinguishable from the evaluated code. Do not alter scientific source or frozen inputs during the active batch.

An existing documented safety check is not a new permission request: carry out authorized routine implementation and execution without asking again. Stop only when a substantive unresolved correctness/resource/access blocker genuinely prevents safe continuation.

## Durable unattended execution

Use a **single sequential batch coordinator** around the existing CLI and `scripts/log_pilot_command.py`; if an equivalent reliable coordinator already exists, reuse it. Run it as a properly detached, logged process supported by the local environment, so progression to the next unit does not depend on a future chat callback.

The coordinator must:
- Operate in the correct `smart_building_conformal` working directory, with the verified interpreter and explicit protocol/readiness/output paths for every command.
- Persist an atomic progress ledger and append-only attempt log with unit identity, phase, exact argv, PID, start/end time, actual exit code and validation/receipt paths.
- Prevent two coordinators from running the same batch concurrently. On restart, reconcile live process identity and checkpoint state before launching anything.
- For each unit, execute run (or supported partial resume), independent validation, and completed `resume --forbid-fits`, in that order. Only then mark it validated and advance automatically.
- Place validation/resume receipts outside the immutable run directory; never replace existing logs or completed receipts.
- Capture stdout/stderr directly to durable logs. Record actual process completion; silence, a started PID or an empty queue is not evidence of exit 0.
- On interruption, reuse completed model checkpoints under the exact same identity. Mid-fit recovery is not implemented: an interrupted unfinished fit may need replay, which must be recorded rather than hidden.
- Automatically create/update a concise machine-readable and Markdown progress summary after each validated unit. Keep exact restart commands and the remaining keys available throughout.
- Execute final aggregation and reporting after the last validated unit without needing another user turn. Save all work even if the chat session ends.

If a routine logging/path problem is provably unrelated to scientific computation, preserve the failed attempt, correct it and continue without changing completed fits. Do not weaken identity checks, ignore corrupt evidence or silently switch configurations. A demonstrated scientific defect requires preserved evidence, an affected-scope assessment and explicit corrected lineage; do not publish invalid units as completed. An unresolved shared integrity defect stops further fitting.

## Resource policy and failure handling

Preserve CPU-only operation, one numerical/Torch thread, `n_jobs=1`, lazy sequences and batch256. One experiment or validation process at a time; no parallel learned fits.

The **3 GiB launch RAM reference is nonblocking** by the user's existing instruction. Log its value without reinstating a refusal threshold. Keep the **256 MiB epoch floor and 8 GiB free-disk check**. Record actual free memory/disk before each unit and actual preparation/model/action/lifetime memory measurements separately.

The published 56.56–348.22 model-minute range is a planning scenario, excluding preparation, I/O and verification. Do not treat it as a deadline or guarantee. The authorized batch may continue beyond it while making progress and respecting resource checks. There is no authorization for paid cloud compute or changing machine-wide settings.

Preserve artifacts and stop on an unresolved identity mismatch, corrupted checkpoint, nonfinite output, failed independent arithmetic/model reconstruction, actual allocation failure or hard resource-guard failure. Poor accuracy/coverage, slower-than-planned progress or a sub-3-GiB launch reading alone are not stop conditions. Avoid infinite retry loops.

If publication/authentication alone fails, complete the authorized local science, reports and backup. Preserve the exact pending branch/commit; do not let an unavailable sign-in strand the experiment queue.

## Acceptance checks for each unit

Require:
- Actual successful exit and the eight tuning/two final learned fits expected for a newly executed complete unit, reconciled with the attempt log and any resumed work.
- Independent recalculation of all three MAE/RMSE point cells and all six coverage/MPIW/Winkler interval cells from saved streams, including actual sample counts.
- Correct own-model conformal ranks/radii; identical paired target IDs; strict temporal/group integrity; preserved tuning selection, epochs and training-only normalization.
- All six saved fitted-artifact calibration/test prediction checks under existing documented tolerances. Report observed discrepancies; do not assert exact equality unless observed.
- Completed resume with fitting routes forbidden, zero new fits and every run file unchanged.
- Per-original-run/building summaries where applicable and independent reconciliation back to the pooled metrics.
- An evidence manifest linking protocol, source, input identity, fitted objects, residuals, predictions, tuning histories, costs and verification receipts.

Keep raw identifiers as strings and preserve float round trips when reading CSVs. Do not average per-group RMSE to reconstruct pooled RMSE: reconstruct from squared errors and counts.

At batch completion reconcile **36 new point cells, 72 new interval cells and 72 saved-model prediction checks**, plus twelve completed zero-fit resumes. If interrupted or blocked, report actual completed counts and failed/pending identities instead of claiming these targets were met.

## Final analysis and panel-ready evidence

After successful units are validated, create a new analysis version from saved artifacts only. Reuse the six historical matched units through their existing validated evidence/identity ledger; do not force them through a newer incompatible source hash or refit them.

Produce:
1. `MATCHED_OVERNIGHT_BATCH_REPORT.md`: actual completion, result tables, costs, integrity status, supported claims, limitations and next outstanding work.
2. A complete combined comparison CSV, a new-only CSV and a clearly labelled **fold2/seed42 all-horizon slice**. Keep dataset, target units, physical horizon, fold, seed, support, source run and protocol identity in every table.
3. A paired LSTM-minus-XGBoost and learned-model-minus-persistence table: MAE, RMSE, coverage deviation at 90/95, MPIW, Winkler, phase timings, inference throughput and cost ratios with explicit zero-denominator handling. Keep raw units separate across datasets.
4. Per-run/per-building and RICO-phase summaries, and separate equal-group diagnostics. Preserve phase/run support limitations, historical reuse and known-building scope.
5. Reproducible figures with source-CSV/hash sidecars: forecast error by horizon, coverage with nominal reference, MPIW and Winkler by horizon, and measured model cost versus benefit. Use readable dataset-specific panels, correct physical horizon axes and no mixed-unit global ranking.
6. A concise numerical response to Panel 2: whether LSTM's extra measured CPU cost is accompanied by better point errors or interval scores at each horizon; whether apparent narrowness instead comes with undercoverage. Report trade-offs without claiming statistical superiority/equivalence from one seed and one fold. This batch broadens horizon evidence; multi-fold/multi-seed inference remains pending.
7. Updated completion overlay, remaining queue and revised runtime scenarios based on actual same-dataset measurements. Preserve original matrices/queues and distinguish estimates from observed times.
8. Updated `PANEL_RESPONSE_MATRIX.md`, `PROJECT_RECOVERY_STATUS.md` and `review/CURRENT_EVIDENCE.md` with precise links and statuses. No slide-deck rewrite is needed in this batch.

Use the comparable fold2 slice for the main horizon display; show the additional earlier/later folds separately. Do not call twelve dependent horizon/seed observations twelve independent replications, average Celsius with kWh, interpret a nonsignificant result as equality or claim nominal/conditional coverage merely because artifact validation passed.

Own-model absolute split conformal is not the same experiment as the broader CQR/EnbPI/DSCP comparison. Seasonal baselines, remaining seeds/folds, broader interval methods, operational selection, conditional challenge, contamination/recovery and robustness remain recorded obligations. Do not launch these unlisted fits or mark the full study/dissertation publication-ready.

## Publish and finish

Publication to a **new non-main review branch is already authorized**. Commit and push incremental evidence at sensible validated-unit boundaries, then publish the final report, index, CSVs, source/protocol/command manifests, validation receipts, reproducible figure sources and established distributable artifacts. Preserve dataset notices and existing handling for fitted objects and large files; provide lossless indexed parts where needed. Never include credentials or unrelated private files.

Keep the verified backup outside OneDrive current. Verify the remote branch SHA and downloadable evidence with file hashes and representative exact readbacks. Main and previous review heads must stay unchanged.

The final message must give:
- Published branch, publication SHA and evaluated source SHA(s).
- Actual unit/fit/metric/verification counts, exits, wall/CPU cost and memory.
- Main quantitative findings for all four tasks and longer horizons, including MPIW/Winkler and LSTM compute trade-offs.
- Direct links to the report, evidence index, comparison CSV and progress/restart record.
- Honest completed/blocked/pending scope and the next concrete study stage.

Do not finish with only "the background job is running." If the session ends before completion, leave a demonstrably live durable coordinator or an accurately recorded failure, with progress and restart instructions. Never promise a notification or continuation mechanism that the environment does not provide.
