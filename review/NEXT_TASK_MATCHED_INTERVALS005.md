# Implement the matched interval adapter, verify it, and run the first BDG2 method comparison

## Authorized outcome

Continue from `review/matched-fold2-multiseed-20260914`, publication **c143fa16eaf9bfc6354b4cb1f8861915cb00f388**.

The next stage is the conformal-method implementation and its actual consumption by alerting. The user authorizes:
1. Implementing `src.matched_intervals005` and necessary supporting code.
2. Running bounded synthetic integration/regression checks, including small explicitly labelled synthetic estimator fits.
3. Once those checks and fresh real-data readiness pass, running **BDG2 / outer fold 2 / model seed 42 / horizons 1,3,6 / levels .90,.95 / all five declared interval methods**, plus the specified deterministic seasonal baseline and clean-stream alert-consumption checks.
4. Independent validation, checkpoints/resume, reports, backup and publication to a new non-main review branch.

Continue through these stages without asking for another approval after implementation or synthetic checks. Do not stop at a proposal when the authorized next stage is ready. Keep execution sequential and durable. Genuine unresolved correctness/resource blockers require an accurate checkpoint, not invalid numbers.

No remaining forecasting-seed queue, full operational candidate search, real-data fault catalogue, conditional-challenge study or full robustness study is authorized in this package. Those remain explicit outstanding obligations.

## Starting evidence and preservation

Read:
- `MATCHED_METHOD_READINESS_MAP.md`
- `MATCHED_FOLD2_MULTISEED_REPORT.md`
- `MATCHED_FAILURE_DIAGNOSIS.md`
- `REMAINING_STUDY_EXECUTION_PLAN.md`, using current completion overlays instead of its historical counts
- `review/CURRENT_EVIDENCE.md`
- `smart_building_conformal/outputs/amendment005/study_plan_v1/interval_method_matrix.csv`
- `smart_building_conformal/outputs/amendment005/support_final_checks_v1/dscp_joint_origin_support.csv` and its membership file
- Applicable repository instructions.

Retrieve this handoff document from the instruction branch only. Do not check out or merge the old application code on `review/pilot-evidence-20260913`.

Verify local HEAD, working changes, active processes and the backup chain. Create or resume a new branch such as `review/matched-intervals005-bdg2-20260914` from the verified current code lineage. Preserve main, previous review heads, all 70 completed matched units, original protocols/matrices and historical outputs. Use new output versions. No reset, force push, package upgrades, unrelated downloads or paid compute.

Existing forecast artifacts retain their original source hash `cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e`. Adding a module may change a repository-wide source digest. Record the new digest honestly and use verified historical read-only loaders for old owners; never rewrite old protocols or relax source identity checks to make reuse pass.

## Adapter and method contracts

Provide an actual executable `freeze/readiness/run/validate/resume` interface consuming matrix identities and the published matched roles. Keep the completed forecasting runner unchanged. Reuse established implementations where their contracts apply.

Freeze a machine-readable method specification before real fitting. It must record factory, parameters, estimator class/seed, score definition, interval construction, rank/quantile convention, initialization, update schedule, group policy, crossing handling and source references. Method names alone do not resolve differences between legacy drivers.

### Owners and sharing

- **quantile_uncalibrated and cqr:** share the exact CQR quantile owner and its raw lower/upper/median predictions. The current factory is MAPIE ConformalizedQuantileRegressor with HistGradientBoostingRegressor, max_iter300, learning_rate .05 and min_samples_leaf50, plus all pinned defaults. Separate nominal levels currently have distinct quantile contracts: with the existing factory, the pilot requires six CQR wrapper objects / eighteen quantile estimator fits. Do not promise sharing across levels unless all affected fitted objects and quantiles are demonstrably identical. No extra predictor fit for the uncalibrated comparison.
- **recentred_enbpi_static and recentred_enbpi_updated:** share the exact trained MAPIE ensemble and actual base predictor. The readiness-map factory uses XGBoost with 60 trees and five length24 block-bootstrap resamplings, not the matched 400-tree forecasting model. Record actual base/sub-estimator fit calls, including any full-data estimator; a wrapper count is not a learner count. Share across nominal levels only when their fitted-owner contract permits it. Verify the requested installed base estimator; a fallback must be explicit and separately identified, never reported as XGBoost.
- **dscp:** use the three already fitted matched **XGBoost** direct-horizon owners for BDG2 fold2/seed42. Reuse their verified artifacts/predictions with no new XGBoost or LSTM fits. The legacy StudyRunner's CQR-median inputs are not this matrix's declared owner.

Separate immutable fitted-owner identity from method/level-specific mutable calibration state. Updating one consumer must not alter static intervals, another level, another group or the shared predictor. Cache raw predictions only with verified owner, feature and row identities.

The legacy `interval_stream.stream` generic signed-residual wrapper is not a method-preserving CQR recalibrator. Use the amendment-004 method-preserving replay contract for operational stream integration. Keep native static MAPIE/DSCP constructions distinguishable from versioned online policies. Document any adapter differences from legacy updated-EnbPI interpolation/rank/initialization behavior; do not silently claim bit-identical legacy results.

### DSCP joint origins and costs

Join horizons by **(original group, origin_time)** independently within fit/calibration/test roles. Verify horizon order, exact target timestamps, row uniqueness and strict role boundaries against frozen joint-origin memberships.

The published BDG2 fold2 joint supports are:
- fit: 51,534 common origins
- calibration: 17,270 common origins
- test: 34,590 common origins
- ten original buildings.

The learned direct-horizon owners retain their original fit supports; do not refit them on the intersection. The intersection defines the joint prediction/calibration/evaluation sequences.

Fit DSCP clustering/merging/neighbour rules using calibration predictions and calibration errors only. Freeze the existing resolved DSCP parameters before test inference. Test predicted sequences may be assigned to frozen calibration clusters; test truths cannot train clusters, merge pools, choose neighbours or set interval widths. Serialize the calibrator and cache assignments across levels.

Retain the published direct-horizon adaptation and from-paper implementation labels. Do not turn it into ordinary absolute-error split conformal or claim a simultaneous/conditional guarantee merely because it has multiple horizons.

Measure calibration clustering/merging and test assignment separately. Use bounded exact batches instead of an all-test by all-calibration distance matrix. A fixed first 64 joint predicted sequences may be timed after freezing to estimate inference cost; reuse those assignments and still evaluate the entire support. No subsampling the scientific cohort or changing neighbours to obtain a faster/favorable result.

### Comparable support

Export each method on its declared native support: single-horizon methods on the original matched rows and DSCP on the joint-origin intersection. Also export a clearly labelled **common-test-support comparison** restricting every method to the exact DSCP-supported rows at each horizon. Use this table for direct all-method comparisons.

Do not silently shrink original cohorts, refit on different rows, substitute old operational masks, or count native/common-support summaries as separate matrix completions. For an online method, preserve its genuine causal history when computing a diagnostic metric subset; do not recompute selected rows with a different residual history.

## Method-owned streams and alert integration

Export row/group/segment/origin/target identities, owner/method/level, own point and raw bounds, immutable issued bounds, observed value, observation availability, release time, update status and relevant calibration-state identity.

Use the current replay primitives or a narrowly extended interface:
- Corrupt observed input/missingness before rebuilding causal features in synthetic tests.
- At each origin, consume only outcomes already observable at that origin. First compare each matured observation to the bounds actually issued for it; only then release its score for future issuance.
- Preserve CQR nonconformity `max(raw_lower-observed, observed-raw_upper)`; preserve the declared signed own-predictor score for recentred EnbPI.
- Keep uncalibrated and native static methods static. Do not apply an adaptive wrapper by default.
- Isolate online state by original group/continuous segment. New runs may initialize from an explicitly declared fixed pre-test historical pool; never borrow another test run's updates.
- Preserve explicit hold/unsupported behavior for insufficient scores or ranks. Do not replace unsupported intervals with fabricated finite bounds.
- Retain raw crossing information and the existing declared bound-ordering policy; do not conceal repaired crossings.
- Feed exactly the emitted intervals/availability to `alert_on_stream`, with emitted/consumed hashes and an independent numerical-violation/episode check.

For the real pilot, consume all 30 method/horizon/level streams with the **fixed immediate single-sample rule**, using their correct hourly sampling frequency and empty synthetic-event catalogue. This is a stream-integration/background-workload diagnostic, not primary operational selection. Preserve original source availability flags; finite imputed values are not automatically observed readings.

Report numerical, availability and combined background episodes per asset-day and exposure counts on the declared support. No recall/F1/detection-delay or primary feasibility claim is estimable from an empty injected-event catalogue. Do not call all background episodes confirmed false alarms.

Exercise temporal rules in synthetic checks as well. Do not convert a forecast horizon into an alert-rule window or tune the rule using this real test block.

## Bounded synthetic acceptance

Build a small deterministic fixture with two distinct original groups, multiple horizons including horizon>1, supported initial calibration and controlled delayed/missing observations. Tiny estimator settings may be used in clearly isolated test fixtures; they must not enter real protocols. Keep a separate actual synthetic-fit ledger.

Meaningful checks must cover:
1. Correct shared owner reuse and actual fit counts; no contamination of static/other-level state by updates.
2. Exact owner reload predictions and immutable completed resume with all learned fitting **and calibrator fitting** forbidden.
3. DSCP joins, horizon permutation/duplicate/missing-row rejection, calibration-only fitting and assignment independence from test truth. Test both one-cluster and multi-cluster paths and same assignments across levels.
4. Inclusive maturity boundary, no future residual consumption, no cross-group/segment updates and preserved new-run initialization.
5. CQR versus signed-residual scoring, static-bound preservation, insufficient-rank hold behavior and crossing counts.
6. Scalar chronological replay versus the batch implementation on clean, zero-control and corrupted-input paths; future-input perturbations must not change earlier issued forecasts.
7. Exact emitted/consumed interval identity, independently checked numerical flags and group-safe immediate/temporal episodes.
8. Corrupted owner/checkpoint refusal, interrupted-stage recovery and completed zero-fit resume.

Do not lower production support minima to make synthetic tests pass. Use sufficiently supported fixtures or explicitly isolated low-level tests. Record actual exits and test/fit counts; do not invent expected pass totals. Limit broader testing to regression risks introduced by the adapter.

## Real BDG2 pilot: proceed automatically after readiness

Create a fresh explicit authorization and pre-fit manifest for the thirty matrix keys:
**BDG2, fold2, seed42, h1/h3/h6, levels .90/.95, quantile_uncalibrated/cqr/recentred_enbpi_static/recentred_enbpi_updated/dscp.**

Also authorize three deterministic BDG2 seasonal computations on the same h1/h3/h6 matched targets, with own calibration residuals at both levels: **3 point /6 interval cells, zero learned fits**. Keep these separate from the thirty method cells. Reuse existing persistence/matched-XGBoost interval summaries only as explicitly identified references.

Freeze source/config/package/input/role/owner identities, method specifications, numerical tolerances, exact command arrays, all expected wrapper/sub-fit/calibrator counts and unused output paths before fitting. Determine concrete EnbPI sub-fit counts using the installed implementation and synthetic ledger, not guesses. Commit the evaluated source and protocol.

Use existing CPU-only, one numerical/Torch thread, n_jobs1, lazy/bounded data, the nonblocking 3 GiB launch reference, 256 MiB epoch floor where applicable and 8 GiB free-disk check. Record actual current resources, wall/CPU and memory by phase. Do not reintroduce the old operational CLI's blocking 3 GiB rule in this adapter.

Run through durable logged commands and checkpoints. Persist fitted owners, calibrators and completed streams separately, permitting resume without repeated fits. Expensive inference may be resumed/recomputed deterministically with its cost recorded; completed scientific outputs stay immutable. Keep failure evidence and exact restart instructions. A poor metric or an exceeded planning estimate is not a correctness failure.

Actual allocation/disk problems, identity violations, corrupt artifacts or failed independent validation require correction/checkpointing. Never silently reduce buildings, rows, parameters, horizons or methods. A reporting-only problem can be corrected without refitting valid owners.

## Independent validation and deliverables

Independently reconstruct every completed interval cell from saved issued streams:
- coverage, signed/absolute deviation, MPIW and Winkler at each level;
- exact IDs, counts, availability and support distinctions;
- method-specific score/quantile/correction rules, without substituting one universal formula;
- original-building contributions reconciling to pooled results;
- serialized owner/calibrator predictions and DSCP assignments;
- causal release/update logs and emitted/consumed alert streams;
- actual fits/calibrator operations and zero-fit completed resume.

Report max observed reconstruction discrepancies under frozen tolerances. Preserve unsupported statuses explicitly; do not report success by dropping failed rows or methods.

Publish:
- `MATCHED_INTERVALS005_IMPLEMENTATION_REPORT.md`
- `BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md`
- Method specifications and source/primary-reference attribution table.
- Evidence index linking all source/protocol/owner/stream identities, matrices, metrics, resource logs, synthetic checks and real validation receipts.
- Native-support and common-support method tables/figures, per-building metrics, seasonal reference outputs and background alert-consumption results.
- A concise interpretation of whether calibration improves coverage/width/Winkler relative to shared-owner uncalibrated bounds, what updating changes, and what remains unsupported. Method owners differ, so this is not a pure calibrator-only comparison across all five methods.
- New completion overlays: matched forecasting remains **70/195**; the interval-method matrix gains only the verified pilot keys (target **30/1950**); seasonal and stream diagnostics have separate counts.
- Updated `review/CURRENT_EVIDENCE.md`, recovery notes, panel responses and the actual implementation readiness map.

Include the next scalable execution proposal with exact keys, dependencies, shared-fit counts and **measured** costs. Keep the 125 remaining matched forecasting units, seasonal remainder, full interval matrix, operational selection, conditional contexts and robustness/recalibration obligations visible. Do not mark the dissertation or full methodology complete based on this pilot.

## Publication and completion

Create/update only the new review branch. Publication and backup are authorized; no further user confirmation is needed. Preserve existing dataset notices, distributable artifacts and lossless handling of large files. Never publish credentials or unrelated private content.

Back up outside OneDrive, verify main/previous review heads unchanged, and verify remote hashes with representative exact downloads. An authentication-only block should not strand authorized local computation: complete reports/backup and retain the exact pending branch/commit.

Finish with actual exits, new method/seasonal/stream counts, wrapper/base-learner/calibrator operations, measured CPU/wall/memory, numerical findings, preservation/validation status and direct report/CSV/evidence links. Do not finish merely with "implementation ready" if the authorized real-data pilot can proceed.

## Unattended execution while the user is away

The user expects to be unavailable for approximately **6–7 hours**. This is an availability window, not a promise of completion or a hard runtime limit. The entire implementation, verification, defined BDG2 pilot, reporting and publication scope above is authorized.

- Begin the actual work after a brief state check. Do not return only a plan, another authorization request for an already listed stage, or a synthetic-test checkpoint when the real pilot is ready.
- Keep one durable task/status record with the current phase, completed owner/calibrator/stream identities, active process identity, latest actual exit, remaining work and exact restart commands. Reuse existing suitable mechanisms instead of creating a second competing coordinator.
- Checkpoint completed owners and phases promptly. Keep source/protocol/parameter identities fixed for an active scientific run, and distinguish later reporting-only commits.
- For long commands, establish and verify an environment-supported persistent process with logs and a real PID. Do not assume a chat callback or an ephemeral tool session will automatically advance the remaining stages.
- Continue automatically from implementation to bounded synthetic checks, no-fit real-data readiness, the authorized pilot, independent validation, reports, backup and publication. Poll/observe long jobs without launching duplicate processes.
- Fix routine implementation, path, serialization and reporting issues within this scope; retain the failed attempt and run the relevant checks again. Do not alter the scientific design to obtain better results or to conceal a failure.
- If a genuine scientific/identity/resource problem blocks a stage, preserve its evidence and address the concrete cause. If it remains unresolved, complete independent authorized documentation, backup and reporting work, then leave a precise blocked status. Do not bypass permissions, identity checks or resource guards.
- A GitHub sign-in or other publication-only block must not stop authorized local computation and backup. Use existing authenticated tools where available; otherwise retain the exact pending commit and state what action is actually needed.
- If all authorized work finishes early, publish and deliver it. Do not fill the remaining hours with additional cohorts, hyperparameter searches, remaining forecasting batches or unrelated changes.
- If valid computation is still running when the absence window ends, allow it to continue under the existing resource policy and leave a current progress record. Never truncate the cohort or label partial output complete to meet a guessed runtime.
- Completion requires actual exit/verification evidence and accessible saved results, not an unattended-process launch alone. If the session must end early, accurately state whether a verified persistent process remains live and how to resume; do not promise automatic continuation the environment cannot provide.
