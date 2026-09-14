# Next task: close support gates and implement amendment-005 conditional-context replay

## Model, objective and authorization

Use **Astra / Extra High**. This package involves causal feature reconstruction, immutable interval ownership, contextual state resets, endpoint definitions and statistical support. It is a substantive integration task.

Start from experiment branch review/matched-intervals005-four-settings-20260914, publication commit **236180a953f2a268f37e1a6d68a4ccd2eb7954b5**, preserving valid local descendants.

Read only this instruction document from the instruction branch. Its application code is older; do not merge or check out that code.

The user authorizes:
- Necessary implementation and repairs within the scope below.
- Read-only real-data/support and saved-artifact diagnostics.
- Bounded, explicitly logged synthetic fitting and full synthetic integration/recovery tests.
- Reports, a concrete first real-data execution proposal, external backup and publication to a new non-main review branch.

This is an implementation package. Do not launch new real-data learned-model/calibrator fits or the remaining experiment queues. Existing models may be loaded for read-only diagnostics; no hidden refitting in validation. Complete all independent implementation/test/reporting work without requesting repeated permission.

Suggested output branch: review/context-replay005-implementation-20260914. Preserve main (06fe967be2be8d7898812c0c2d6e464d4e942351), existing review heads, historical results, untracked historical files and backups. Publish relevant evidence so the user need not upload it manually.

## Current state and scope correction

The 100-cell remaining-settings batch is complete. Matched forecasting is 70/195; interval methods are 250/1950; unique seasonal computations should reconcile to 9/27. Completion/validation does not establish nominal coverage.

All five methods in the frozen interval matrix already exist: uncalibrated quantiles, CQR, static EnbPI, updated EnbPI and DSCP. The remaining 1,700 cells are outstanding scope execution, not evidence that additional algorithm families must be invented. Correct the vague "remaining declared conformal variants" wording in current status documents using an explicit matrix crosswalk.

The next major missing component is event-backed **conditional-context challenge C**. Its estimand and controls are different from matched interval quality and from natural-frequency operational selection A. Do not turn all five matched methods into new C controls or apply C scores to amendment-004 feasibility gates.

Before implementing, read:
- AMENDMENT005_PROPOSAL.md and REMAINING_STUDY_EXECUTION_PLAN.md.
- MATCHED_METHOD_READINESS_MAP.md and OPERATIONAL_EVALUATION_PLAN.md.
- MATCHED_INTERVAL_METHODS_REMAINING_SETTINGS_REPORT.md and its evidence index.
- MATCHED_FAILURE_DIAGNOSIS.md and the current native/common interval CSVs.
- Existing operational004 design/events/stream/metrics/inference/checkpoint modules and applicable tests.
- The amendment-005 proposal_spec.json, proposal_roles.csv, challenge_contexts.csv, challenge schedules, rule applicability, aliases, exact role memberships and scales indexed by review/support_design_20260913/EVIDENCE_INDEX.md.
- support_final_checks_v1/challenge_zero_controls.csv, challenge_inference_support.csv and exact DSCP support tables.

Resolve paths through the evidence index and inspect actual schemas. Historical markdown statuses are not current readiness evidence.

## Stage 1 — concrete support and scientific-status gate

Do this with no real-data fitting. Keep it focused; do not repeat all historical audits.

1. Reconcile all four datasets, three folds, declared horizons/levels/seeds and five interval methods against the frozen matrix. Distinguish an implemented adapter from an available fitted owner, a passed no-fit membership check, and a completed experiment. Make any remaining fold-0/1 scope support data-driven and regression-tested. Missing future forecast artifacts should be recorded as dependencies, not fabricated, newly fitted or hidden.
2. Retain correct 10-minute PLEIA, 1-minute RICO and 1-hour BDG2 cadences; whole-run RICO roles; all seasonal applicability rules. Check role construction without requiring all future learned artifacts. Preserve explicit readiness failures for real runs whose prerequisites are absent.
3. Reconcile the current interval failures with saved evidence: native/common support, original units and availability, own-model prediction bias, calibration score distributions, frozen correction/rank, and test miss direction. Reuse existing point-model diagnosis and add only the missing interval-owner diagnostic. Separate demonstrated arithmetic/ownership defects, observed distribution changes and unproven causal explanations.
4. In particular, inspect severe static-EnbPI PLEIA undercoverage and negative CQR corrections, where applicable. Negative valid CQR scores or non-nested intervals from separately fitted confidence levels are not automatically defects. Do not clip corrections, widen intervals, change ranks, retune models or remove observations to meet nominal coverage.
5. If an actual correctness defect is found, document exact affected outputs, repair with a regression test, preserve original outputs and mark their status honestly. Do not silently rerun them or let affected artifacts enter the new endpoint. Continue independent safe implementation work.
6. Close the PLEIA-energy sensitivity specification gap explicitly. The prior plan requires separate keep/mask analyses of possible stalled/zero/catch-up periods but does not, by that phrase alone, define exact numerical rules. Locate any existing authoritative rules before claiming they are frozen. Keep primary meter values untouched. Implement a separately versioned sensitivity interface, synthetic tests, mask/reason provenance and evaluation-denominator accounting. Distinguish retrospective evaluation stratification from a causal online feature/treatment policy and from a retraining sensitivity. Zero demand is not automatically a faulty meter.
7. Where exact sensitivity thresholds or catch-up semantics are genuinely unspecified, produce a concrete proposed protocol based on source semantics and permitted training information, with the unresolved choice clearly identified. Do not invent a historical preregistration or run a favorable mask search on outer outcomes. This unresolved independent sensitivity choice must not prevent implementation of the already specified C endpoint; it must remain visible in the readiness map.

Produce SUPPORT_GATE_STATUS.md with exact remaining dependencies and an INTERVAL_FAILURE_DIAGNOSTIC table/report. No nominal-coverage pass criterion is introduced.

## Stage 2 — implement the actual conditional-context engine

Implement a versioned entrypoint, suggested **src.conditional_context005**, with freeze, readiness, run, validate and resume. Use small modules where useful and reuse correct existing primitives. The run action must enforce an explicit execution manifest so future real-data scope is reviewable.

### Frozen endpoint and support

C applies to PLEIA temperature, PLEIA energy and RICO at their primary alert horizons:
- pleia / pleia_energy: h1, ten minutes.
- rico: h5, five minutes.

Keep amendment-004 natural-frequency A as a separate endpoint. Its unsupported PLEIA/RICO primary selection and BDG2's reduced-grid abstentions remain intact. The full 264-candidate BDG2 wrapper and full execution remain separate outstanding work.

Consume the exact published C context and role hashes, not newly sampled or convenient windows. PLEIA contexts have 144 observations, six-hour warm-up, the fixed one-hour fault envelope and one-hour follow-up. RICO contexts are whole eligible runs with one-hour warm-up/envelope/follow-up. Preserve unused PLEIA tails for full-stream clean workload.

Each context has the published fixed onset, seven fault families, three severities and two slots with seeds 42/43 and signs -/+. Do not confuse slot seeds with model seeds. Preserve random-mask RNG keys, deterministic aliases, effective/null classification, attempted schedules and unchanged incidence semantics. Do not redraw null events until support improves.

Single-series group identity requires particular care: the matched-origin repair normalized a null group to an empty CSV field, while the published C context table contains a "None" representation. Use an explicit, versioned identity crosswalk where necessary; preserve all original context/group IDs and source hashes. Do not apply a global string replacement that merges genuinely distinct groups.

### Exactly the declared C controls

At confidence level .95:
1. Quantile-uncalibrated, static.
2. CQR, static.
3. CQR with the first declared rolling policy.
4. Persistence with its own fixed absolute-error split-conformal interval.

Raw/CQR/rolling controls share the legitimate quantile predictor when their fit/calibration identities match. Persistence uses available target_lag_0 and its own permitted calibration errors. Do not relabel HistGradientBoosting bounds as XGBoost or Attention-LSTM.

Rolling schedules remain every 24/window 250 observations for PLEIA and every 15/window 200 for RICO; minimum online pool 50. Preserve declared score/rank, native static conventions and released-observation ordering. Name differences between asymmetric native static CQR and symmetric max-score online replay accurately; do not silently redesign them.

Use immediate and the exact context-supported temporal rules:
- PLEIA: immediate, 30-minute 3/3, 60-minute 4/6, 180-minute 3/18, 360-minute 4/36.
- RICO: immediate, 5-minute 2/5, 15-minute 3/15, 30-minute 3/30, 60-minute 4/60.
No latching/cooldown. Keep other declared rules explicitly inapplicable for C.

C is fixed evaluation, with no challenge-score model/rule selection. The matched-forecast role masks and operational/C masks differ. Reuse a fitted owner only after exact role, features, calibration, parameters and source compatibility are demonstrated. Otherwise record the required future fit. Matching dataset/fold/seed alone is insufficient.

### Actual closed-loop causal execution

Do not feed archived clean forecasts into corrupted variants. intervals005_stream.FrozenStreamOwner returns fixed saved predictions and is not, by itself, a predictor for corrupted features.

For each context/variant:
- Initialize from that role's permitted historical calibration pool.
- Reset adaptive, residual-release and alert state independently.
- Use clean observed warm-up and permitted preceding history from the same original segment.
- Inject corruption at sensor-observation time before constructing future lags, rolling features, target_lag_0 and missingness flags.
- Predict with the actual serialized owner on those causal feature rows.
- Compare a matured reading to the interval that was actually issued for it before releasing its score for an eligible later/current origin under the frozen ordering.
- Missing observations release no numerical score. Missingness and numeric dropout are different cases. Clean counterfactual truth never fills or updates the corrupted stream.
- No window, forward fill, event episode or adaptive state may cross an original run/segment boundary.

Reuse raw predictions across controls/rules only when predictor, feature, variant and support identities match. A corrupted variant must never hit a clean-feature cache. Restrict feature rebuilding to sufficient causal history/context where this preserves exact behavior; do not rebuild the entire dataset thousands of times unnecessarily.

One clean identity replay per context uses the SAME initialization and context-history contract as its fault variants. Prove zero corruption reproduces its inputs, predictions, issued bounds, released scores, updates and alerts. Do not require an independently reset context stream to equal a full-stream adaptive trajectory with a different preceding history.

Also evaluate clean workload once on the full original held-out stream per control/rule. Keep that full-stream trajectory separate from context-reset zero controls. Challenge variants and aliases do not multiply clean exposure.

## Stage 3 — metrics and independent synthetic acceptance

Keep numerical-only, availability-only and combined channels separate. Reuse and independently check one-to-one onset-aware episode matching; pre-active episodes earn no new-onset credit.

Implement:
- Scheduled, effective, null and alias counts by original context/stratum/slot.
- Equal-context within-stratum detection means; equal weighting across all 21 strata only when every stratum meets the frozen distinct-context support.
- Missing/unsupported full macro as unavailable, not a favorable mean over remaining strata.
- Full-stream background episodes per original eligible asset-day and time in alert.
- Misses, detected-only delay and restricted time-to-detection with misses censored at the declared envelope-plus-tolerance horizon.
- Separate clean counterfactual and corrupted-observation interval diagnostics.
- Original context/run contributions sufficient for later paired inference.

Preserve the amendment's inference requirements: model seeds averaged within original units; no IID resampling of rows, fault slots, catalogues or seed aliases; PLEIA seven-adjacent-context blocks and RICO phase-aware original-run support; 2,000 fixed draws/seed 20240601 and the existing valid-draw/support rules. Single-model-seed pilot summaries remain descriptive. Known unavailable inference must remain unavailable. C estimates do not establish deployment precision/F1 or primary A feasibility.

Use bounded synthetic fixtures covering both cadences, independent groups/runs and enough fitting/calibration rows for declared minima. Tiny estimator settings must be explicitly synthetic, never leak into real protocols. Log actual tiny fits/calibrators separately.

Meaningful acceptance must include:
- Independent scalar causal-feature/prediction/release reconstruction, not just calling the production replay twice.
- Future-observation perturbations cannot affect earlier features/issued intervals.
- Corruption demonstrably changes later predictors where the frozen fixture says it should; clean-prediction reuse is rejected.
- Missingness releases no score; held update state and insufficient support are explicit.
- Whole-run resets and group-isolated alerts; exact warm-up/onset/follow-up edges.
- Raw/CQR shared ownership, fixed persistence and method-specific static/rolling bounds.
- Identity controls, deterministic alias equality and null handling.
- Hand-calculated episode matching, equal-context weighting, unavailable macros and censored-delay examples.
- Full-stream exposure counted once, including eligible tails.
- Corrupt checkpoints rejected; completed resume invokes zero fits/calibrator updates and preserves scientific artifacts.
- Coordinator prelaunch/import checks, interrupted-worker adoption and no duplicate fits after the known missing-journal failure pattern.

Run the required repository test gate and a complete synthetic CLI freeze/readiness/run/validate/resume workflow, with actual exit codes. Validate method/variant/input/issued/consumed hashes independently. Avoid broad repeated testing once concrete acceptance risks are resolved.

## Stage 4 — concrete first real-data proposal, not another vague next step

Produce FIRST_CONDITIONAL_CONTEXT_RUN_PROPOSAL.md and a machine-readable manifest for:
- PLEIA energy, outer fold 2, model seed 42, h1.
- All published outer contexts, all 21 strata, both slots and four .95 controls.
- All five applicable rules.
- Original full-stream clean workload and per-context identity controls.
- No inner/outer challenge-score selection.

At the inspected commit, challenge_contexts.csv contains **68 PLEIA-energy fold-2 outer contexts**. Reconcile exact membership and role name locally. That implies **2,856 scheduled fault slots** (68 x 21 x 2) before null/alias accounting, plus 68 clean context identities; these are not independent observations or fit counts. Rules consume shared legitimate streams rather than causing new predictor fits.

Record exact fitting/calibration/test rows, permitted owner reuse versus genuinely required new fits, expected wrapper/sub-estimator counts, semantic control/rule counts, immutable paths, actual executable commands and resource prerequisites. Provide synthetic measurements and clearly labelled extrapolation uncertainty; do not recycle matched-forecast or BDG2 quality-run cost as if it measured C replay.

No new real-data fitting/replay is launched in this implementation package. The proposal must be concrete enough for the next execution prompt to authorize it without another design exercise.

## Delivery and exit criteria

Publish:
- Implementation source and regression/synthetic evidence.
- A protocol-to-code crosswalk with precise implemented/blocked/unexecuted distinctions.
- Support/fold status, the interval diagnostic, and the energy sensitivity specification/interface/tests with any unresolved scientific choice explicit.
- Frozen synthetic protocol, complete actual CLI logs, operation/resource ledger, independent validation and zero-fit resume evidence.
- The exact first real-data proposal and readiness manifest.
- Updated CURRENT_EVIDENCE.md, method readiness map, panel response and remaining-work plan.
- External backup and verified remote evidence index on the new non-main review branch.

Correct stale links/status text without rewriting historical reports. Keep completion totals at their actual values; synthetic execution and no-fit checks add no real-study cells. Full-study/publication readiness remains false.

Document how the same owner/replay interfaces will later support calibration contamination, cascades and recovery. Do not claim the separate legacy robustness obligations or full BDG2 operational grid are completed by C.

Verify changed published files and representative exact artifact downloads; preserve earlier branch heads and historical hashes. Do not spend the task repeating thousands of unchanged remote downloads.

Finish with the published SHA/URL, actual synthetic operations and verified exits, concrete implementation achievements, remaining genuine design choices, and the exact first-run proposal. Do not end at a plan without implementing the specified engine. If a dependency is genuinely blocked, complete independent authorized work and provide precise evidence and restart instructions.
