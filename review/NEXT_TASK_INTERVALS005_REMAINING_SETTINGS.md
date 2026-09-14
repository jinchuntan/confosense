# Next task: interval-method support for the remaining three settings

## Model and purpose

Recommended assistant: **Sol / High**. This is a bounded extension of validated methods to declared dataset adapters and an explicitly authorized batch. Astra / Extra High is reserved for a genuinely unresolved scientific-design or causality question; do not interrupt routine execution to request a model upgrade.

Continue the agreed codebase-completion stage: make the matched interval engine work across all four study settings before scaling the remaining experiment queues. BDG2 is now demonstrated across five training seeds. The PLEIA-energy fold-1 forecasting triplet proposed by the last report remains valid queued work, but is not a prerequisite for this package: all ten required fold-2/seed-42 XGBoost owners already exist.

This instruction authorizes implementation, necessary bounded synthetic fitting tests, the three real-data task units below, independent validation, completed resume, reporting, backup and publication. Proceed automatically through those stages. Do not stop at "implementation ready" when the authorized runs can proceed.

## Starting point and preservation

- Repository: https://github.com/jinchuntan/confosense
- Experiment branch: review/matched-intervals005-bdg2-multiseed-20260914
- Published experiment commit: 95c9e35bc81d65f08492306cb716f4c9ca7d00a6
- Main at handoff creation: 06fe967be2be8d7898812c0c2d6e464d4e942351.
- Retrieve only this instruction document from its instruction branch. Do not merge or check out that branch's older application code.
- Preserve valid local descendants, existing backups, historical results and the four pre-existing untracked historical files. Inspect local state before choosing a new review branch; do not reset, clean, force-push or overwrite them.
- Publish on a new non-main review branch, suggested name review/matched-intervals005-four-settings-20260914. Preserve earlier review heads.

Read the current evidence index and BDG2_MATCHED_INTERVAL_METHODS_MULTISEED_REPORT.md. Then inspect:
- smart_building_conformal/src/matched_intervals005.py
- smart_building_conformal/src/intervals005_data.py
- smart_building_conformal/src/intervals005_owners.py
- smart_building_conformal/src/intervals005_stream.py
- smart_building_conformal/src/intervals005_validate.py
- The existing interval coordinator, relevant tests and native-method erratum.
- AMENDMENT005_PROPOSAL.md and REMAINING_STUDY_EXECUTION_PLAN.md, interpreting their historical status statements against the current completion ledger.
- outputs/amendment005/study_plan_v1/interval_method_matrix.csv
- outputs/amendment005/support_final_checks_v1/dscp_joint_origin_support.csv
- outputs/amendment005/support_final_checks_v1/dscp_joint_origin_membership.csv.gz
- outputs/matched_forecasting005/fold2_multiseed_batch_v1/analysis_v1/evidence_reuse_ledger.csv

All outputs paths above are relative to smart_building_conformal. Locate existing files from the evidence index rather than inventing replacement datasets or owners.

## Authorized real-data scope

Execute sequentially in this order, outer fold 2 and model seed 42 throughout:

| Task | Horizon steps | Sampling frequency | Physical horizons | Method cells |
| --- | --- | --- | --- | --- |
| PLEIA energy (pleia_energy) | 1, 3, 6 | 10 minutes | 10, 30, 60 minutes | 30 |
| PLEIA temperature (pleia) | 1, 3, 6 | 10 minutes | 10, 30, 60 minutes | 30 |
| RICO (rico) | 5, 15, 30, 60 | 1 minute | 5, 15, 30, 60 minutes | 40 |

Each task unit includes all its horizons, confidence levels 90% and 95%, and the five existing methods: uncalibrated quantiles, CQR, recentred EnbPI static, recentred EnbPI updated and DSCP. Use exact machine-readable method identifiers.

Total: **100 new native interval-method cells**, their common-support comparison views and **100 issued/consumed clean-stream checks**. Common-support views are not additional unique experiment cells.

Complete daily seasonal baselines for both PLEIA tasks on the declared support: six unique deterministic point computations and twelve own-seasonal interval cells. RICO daily seasonal remains explicitly inapplicable; never borrow observations across independent runs to manufacture a daily cycle.

No new matched forecasting, Attention-LSTM or standalone XGBoost owner fits are authorized or needed. No other folds/seeds, operational fault catalogues, full experiment queue or robustness study are launched by this package.

Under unchanged current factories, plan for:
- Twenty CQR wrappers, sixty quantile-estimator fits.
- Ten shared EnbPI wrappers, one hundred and ten XGBoost sub-estimator fits.
- Three DSCP calibrators, with up to fifteen KMeans candidates under the current candidate rule; record actual counts and data-dependent eligibility.
- **170 learned-estimator fits**, separate from DSCP/KMeans and conformalization operations.
- Zero historical matched-forecast refits; zero learned seasonal fits.
Record actual operations independently. Investigate unexpected extra fits before continuing, rather than adjusting the accounting to hide them. Tiny synthetic operations must be logged separately.

## Existing forecast ownership and fixed support

Resolve each owner from the reuse ledger and validate its protocol, source and full run-file identities. Required existing XGBoost run paths are:
- outputs/matched_forecasting005/pleia_energy_h1_f2_s42_v1, pleia_energy_h3_f2_s42_v1 and pleia_energy_h6_f2_s42_v1.
- outputs/matched_forecasting005/pleia_h1_f2_s42_v1, pleia_h3_f2_s42_v1 and pleia_h6_f2_s42_v1.
- outputs/matched_forecasting005/rico_h5_f2_s42_v2, rico_h15_f2_s42_v1, rico_h30_f2_s42_v1 and rico_h60_f2_s42_v1.

These owners use the historical scientific-source SHA-256 cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e. Validate rather than replacing that provenance with the new runner's hash.

The currently published fold-2 DSCP joint-origin support is:

| Task | Fitting origins | Calibration origins | Test origins | Fitting/calibration/test original groups |
| --- | --- | --- | --- | --- |
| pleia | 14,845 | 4,943 | 9,902 | 1 / 1 / 1 |
| pleia_energy | 14,845 | 4,943 | 9,902 | 1 / 1 / 1 |
| rico | 9,577 | 3,297 | 6,437 | 61 / 21 / 41 |

These counts are cross-checks, not a substitute for exact published memberships and hashes. A mismatch must be diagnosed; do not resplit data to achieve these counts. RICO uses whole-run memberships.

Use original native single-horizon fitting/calibration/test rows for the existing horizon owners. DSCP consumes the declared saved XGBoost forecasts joined on original group and forecast origin across all declared horizons. Do not refit owners on the intersection. Common-support comparisons must restrict emitted results after their legitimate native-history processing; do not replay adaptive methods on a shorter history merely to match DSCP rows.

## Necessary bounded implementation

The current source contains BDG2-specific assumptions beyond the top-level scope guard. Remove those assumptions through explicit protocol-driven fields, preserving BDG2 behavior:

1. Parameterize authorized dataset, fold, seed, horizon list, counts and dataset-specific output/alias identity. Verify keys against the frozen matrix. RICO has four horizons and forty method cells; it must not inherit three-horizon or thirty-cell success counters.
2. Use the declared sampling frequency from the dataset configuration throughout joint-origin joins, origin/target checks, replay, stream metadata, independent validation, alert consumption, exposure and time-in-alert calculations. Existing default/explicit one-hour arguments in joint_join, DSCP emission and independent alert validation must not survive for PLEIA or RICO. Do not infer cadence from gaps between independent runs.
3. Make seasonal applicability explicit in readiness, execution, validation, completion and reporting. Use the declared 144-step daily lag for PLEIA and retain BDG2's 24-step baseline. Missing RICO seasonal files are expected inapplicability, not missing mandatory evidence. Seasonal intervals use their own calibration errors. Never drop rows silently to obtain complete seasonal support.
4. Preserve correct dataset-specific preparation caches and feature schemas; a cache must never carry temperature data, energy targets, or run memberships into another task.
5. Preserve native asymmetric CQR conventions and shared raw/CQR ownership; static and updated EnbPI must share the legitimate fitted owner while maintaining separate state for each level/horizon/group. DSCP must use the saved XGBoost owner, not CQR's median estimator or newly fitted substitutes.
6. Preserve all frozen method parameters and installed-library numerical conventions. For example, do not silently convert a frozen bootstrap length in observation steps to a new physical-time hyperparameter. This is adapter work, not tuning based on the observed coverage.
7. Preserve original group isolation and causal score release at target observability, including exact-boundary ordering under the existing protocol. RICO online state must reset per original run; no residual, rolling window or alert episode can migrate from one test run to another. If the declared initialization uses historical calibration data, document it separately from test-stream updates.
8. Retain source-availability/imputation masks and original identities. Do not treat an imputed finite target as newly observed. Preserve the frozen scoring-support policy and make denominators explicit.
9. Version new protocols and source hashes before fitting. Existing narrow read-only compatibility rules must not become a general source-mismatch bypass. New fits run under the new frozen source; historical owners retain their historical identities.
10. Make coordinator, resource records, validators, completion counters and comparison reports derive scope from the frozen manifest. Include explicit physical units and supported/inapplicable status.

Preserve the original PLEIA energy meter values. Zero, stalled or catch-up periods must not be removed or transformed for better results. The separately versioned meter sensitivity remains a distinct remaining obligation; do not claim this package completes it.

## Pre-fit gates and tests

Record the exact task list, owner references, role/support hashes, frequencies, seasonal policy, method settings, resource policy, predicted operation counts, commands and fresh output paths before real fitting.

Add only necessary tests for the expanded risks:
- Ten-minute and one-minute origin/target checks, with a deliberately incorrect one-hour interpretation rejected.
- Four-horizon DSCP joins and exact whole-run support, including duplicate/missing origin rejection.
- Causal release and cross-run isolation for RICO, including an adversarial future-observation change that cannot affect earlier issued intervals.
- Seasonal inapplicability flowing cleanly through readiness/run/validation/reporting for RICO.
- Dynamic 30/30/40 cell manifests, units, clean-stream exposure and independent consumption.
- Wrong-owner/dataset cache rejection and corruption detection.
- Interrupted-stage recovery and completed resume with all fitting/calibration routes forbidden.

Use bounded synthetic integration fixtures with logged tiny fits when required. Reuse existing meaningful tests rather than duplicating all native-method audits. Run the repository's required test gate. Resolve any failure that could affect the authorized results before fitting.

Verify existing BDG2 outputs and aliases read-only, with relevant compatibility checks. Do not repeat BDG2 scientific runs or the entire historical remote-download audit.

## Sequential execution and recovery

After readiness passes, run all three authorized task units without another fitting approval. Validate and perform a zero-fit completed resume for each before continuing.

Maintain the existing CPU/thread, launch-RAM, disk and memory guards; use separate worker processes and one real fitting task at a time. Measure task-specific preparation, fitting, calibration, inference, replay, validation and resume. Do not assume BDG2 timing scales directly with row count: cadence, number of horizons, groups and clustering can change costs.

Use durable atomic checkpoints and a coordinator with recorded PID, attempt, start/end timestamps, command and actual exit code. A launched process or a notification is not evidence of completion. After interruption, reuse valid completed owners/stages without repeating their fits; retain failed attempt logs. Repairs that change scientific outputs require a new protocol/run identity and an explicit affected-scope statement.

If one dataset has a genuine local blocker, preserve it with exact diagnostics and complete the other independent authorized datasets where safe. Do not invent settings or relax frozen acceptance tolerances to unblock a run. Report scientific design blockers precisely if the existing protocol cannot determine the correct behavior.

## Independent acceptance

For each task:
- Reconstruct point predictions/owner identities, native interval bounds and DSCP membership/assignment using saved artifacts and independent formulas, preserving the established dtype and numerical-tolerance rules.
- Recalculate every native and common-support coverage, MPIW and Winkler row from saved issued intervals.
- Independently check actual cadence, group membership, target observability and emitted/consumed stream identities; recalculate background episode counts, asset-day exposure, time in alert and availability alerts.
- Verify deterministic seasonal predictions, own-residual radii and metrics where applicable.
- Verify completed resume performs zero learned fits, zero DSCP/KMeans/calibrator fits and zero conformalization refits, preserving all scientific run files byte-for-byte.
- Reconcile measured operation counts, exact completed keys, failed attempts and resource totals. Distinguish nested phase measurements from enclosing wall/CPU totals.
- Show actual commands and exits for readiness, run, independent validation and completed resume.

Numerical validation is a correctness check; nominal coverage is an empirical outcome. Preserve low coverage, broad intervals, native warnings and disappointing comparisons honestly.

## Reporting, publication and completion

Deliver a concise completed report (suggested INTERVALS005_REMAINING_SETTINGS_REPORT.md), implementation notes, evidence index, exact machine-readable CSVs, matched comparison figures, validated fitted artifacts/streams, resource measurements and restart instructions. Publish the evidence needed for remote inspection through existing artifact/large-file conventions.

The seed-42 comparison across all four settings has 130 method cells: 30 existing BDG2 cells plus 100 new cells. Keep the separate five-seed BDG2 evidence intact. Do not pool tasks with different target units or interpret five training seeds on identical buildings/periods as population uncertainty.

In particular:
- Compare raw quantiles with their own CQR counterpart, and static EnbPI with its updated counterpart.
- Present coverage alongside width and Winkler; do not imply that narrow but severely undercovered intervals are better calibrated.
- Report cadence-specific background workload and group contributions. Empty catalogues support no recall, F1, detection-delay or deployment-feasibility claims.
- Keep RICO phase imbalance, historical data reuse and original-run scope explicit.
- Label mean/min/max summaries accurately. A range of seed means across horizons is not the full range of individual-seed outcomes.

If all authorized work passes, update the ledger to:
- Matched forecasting: **70/195**, unchanged.
- Interval methods: **250/1950**, with 1,700 remaining.
- Unique deterministic seasonal computations: **9/27**, with 18 remaining, subject to identity reconciliation against existing evidence.
Do not count native/common views or seed aliases as new fits or independent observations.

Update CURRENT_EVIDENCE.md, the panel-response matrix and remaining-work status. Preserve the queued PLEIA-energy fold-1 triplet. Clearly separate remaining adapter/fold gates and meter sensitivity, operational selection/conditional challenge, closed-loop robustness/recovery, bulk execution and final inference/reporting. Do not mark the whole codebase or dissertation publication-ready.

Verify the new branch's SHA and changed published artifact hashes with representative exact downloads, including metrics and every new stream or its documented lossless parts. Reuse recorded historical identities rather than re-downloading thousands of unchanged artifacts. Confirm main and prior review heads remain unchanged; complete the existing external-backup procedure.

Final response: published URL/SHA, evaluated source hash, exact completed counts, validation and resume outcomes, measured costs, main findings and the single next dependency from the updated readiness map. If blocked, give the affected task/stage, precise reason, preserved paths and exact restart command. Do not end with "shall I proceed?" for any work authorized above.
