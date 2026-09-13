# Next Astra task: amendment 004 operational implementation

13 September 2026. The current implementation is published on review/current-dissertation-20260913 at 3354393290d2afaef4361a9a7a1a43336a14c21d. The earlier sign-in blocker is resolved.

Continue from that implementation or a verified newer local descendant. This instruction file lives on the separate evidence-review branch, whose base source is older. Read this file without checking out that older source.

## Objective and boundaries

Implement the operational selection and causal replay described in OPERATIONAL_EVALUATION_PLAN.md as amendment 004, verify actual data support without fitting, and complete the specified synthetic two-inner-fold integration smoke.

The user authorizes relevant code and research review evidence to be published on a non-main review branch. Preserve current commits, backups, original pilot artifacts, protocol hashes and historical outputs. Do not push or merge into main, reset history, force-push or overwrite completed runs. Do not repeat the completed LSTM diagnostic experiment. No full four-dataset fitting, multi-seed study or 900-cell robustness run is authorized in this task.

Read repository instructions, review/CURRENT_EVIDENCE.md, PILOT_DIAGNOSTICS.md, OPERATIONAL_EVALUATION_PLAN.md, PROJECT_RECOVERY_STATUS.md and the current executable protocol. Use the existing working Python environment and dependencies. Check the local/remote state and preserve any newer work rather than assuming the quoted SHA is the latest local commit.

## Review findings to carry forward

The published diagnostic validation records 24 unchanged learned inner fits reproduced, 125 original pilot/config/protocol files unchanged and no new outer/final fit. The published regression log records 308 passed, 1 skipped and three existing warnings. These are existing results, not tests newly run by the reviewer.

The measured paired preparation peak fell from 2,183,290,880 to 1,045,798,912 bytes: 52.0999%. The before/after records agree on prepared-frame hash, selection-audit hash, selected target and all support records. Preserve this allocation-only fix and the original pilot timings.

No LSTM alignment/scaling/epoch defect was demonstrated. Warmer development validation data and negative prediction bias are measured; architectural explanations remain hypotheses. Do not spend this task trying to make LSTM win.

One operational-plan statement needs correction against the actual source:
- In corrected_study.select_on_inner, evaluate_outer and evaluate_ablation, the static branch already uses the method's original lower/upper bounds. The checked source does not route static CQR through _recalibrated_stream('static', ...).
- The demonstrated semantic gap is periodic/rolling recalibration: recalibrated_bounds uses generic signed point residuals without method-specific CQR scores.
- The core selects/evaluates forecasts and recalibration on clean arrays, then passes a perturbed observation array into alert_on_stream. This is not the causal corrupted-input/residual replay required by the operational plan.
Correct the documentation precisely and add regressions that protect the working static behavior while repairing those genuine gaps.

## 1. Run the planned no-fitting support preflight first

Before finalizing the amendment and launching any fitting, generate the proposed outer/final-calibration/B0-B3 memberships for all four tasks and all three outer folds at their primary operational horizons. Record both inner folds, their purged counts, groups, chronological endpoints, monitored exposure, physical-rule applicability and method/policy calibration-rank support.

Generate the five fixed catalogue schedules per role using the proposed incidence and placement rules without fitting a predictor or measuring forecast/alert performance. Record attempted, placed, effective, null and rejected events by family/severity and the available original time blocks/groups.

The proposed support rule requires 21 family/severity strata with at least five effective onsets each, across the five-catalogue bank, in each inner fold. That is at least 105 effective events per inner fold before other support checks. Counts alone are not sufficient for valid bootstrap bounds. Include placement guards, null realizations, missing strata, group counts and the planned block length. Identify tasks/folds that cannot meet those structural requirements.

Do not increase incidence, manufacture events, discard difficult strata, shorten the test, or weaken support thresholds to make preflight pass. Separate insufficient design support from measured poor model performance. Report any necessary design/scope decision explicitly. This does not block implementing and verifying correct insufficient-support behavior.

Write a concise support CSV/JSON and an explanation of actual limits. Outer-data use here is structural/exposure/placement checking only; do not choose policies from outer performance. Retain the plan's explicit post-inspection status.

## 2. Implement and version the operational contracts

Use the plan's declared values and definitions. Record amendment 004, resolved configuration, hash, data/membership identity, candidate IDs and a new output location. Document clarifications with reasons; do not silently change the protocol or claim it predates inspected results.

Implement:
- Two operational inner folds, final-calibration reservation, strict target-time purging and whole-group boundaries.
- Explicit actual estimator ownership, and a model-seed by catalogue-seed crossing rather than the current one-to-one pairing.
- Shared exposure-based catalogues, seven distinct corruption definitions, null/zero controls, physical rules, target-observation-time alarms and deterministic one-to-one episode matching.
- Both-fold feasibility, declared selection utility and deterministic ties, all candidate rejection reasons and no_feasible_configuration without a hidden point-estimate fallback.
- Independent clean-counterfactual workload and corrupted-stream performance. Retain denominators and distinguish unsupported design, scientific infeasibility and software failure.
- The controlled baseline/ablation wiring and separate independently selected operating points specified by the plan.

Keep the plan's constructed stratum-level F1 explicitly labeled as a custom synthetic selection utility. Also export ordinary matched-event/episode precision, event recall and background episodes per asset-day; do not present the custom utility as conventional real-fault precision.

## 3. Wire a single causal, method-preserving stream

Preserve static CQR's quantile curves and correction. Periodic/rolling CQR must update its own stored nonconformity scores; signed-residual methods retain their own construction. Use declared grids and finite-sample support rules. Do not adapt native-updated EnbPI twice or count equivalent method/policy combinations as distinct.

At each origin, use only available observations and matured forecast outcomes. Corruptions must causally affect subsequent features and observable residuals. Evaluate each reading against the bounds actually issued for that target before incorporating its residual into later forecasts. Keep clean and corrupted states separate, and reset correctly at group boundaries and genuine observation gaps.

Pass the actual selected bounds and availability flags into alerting and record hashes of those consumed arrays. Preserve issued forecasts; a later recalibration cannot rewrite a past interval.

Apply the same availability-alarm convention to all compared pipelines. Export availability-only, numerical-only and combined causes, plus per-family results, so directly detecting a missing reading is not attributed solely to conformal calibration. This is attribution/accounting within the existing missingness rule, not an extra model search.

## 4. Complete meaningful tests and the bounded smoke

Use the existing regression foundations and the plan's section-8 acceptance matrix. Tests must exercise real interfaces rather than only restating helper formulas.

Cover final-calibration/test sentinels leaving selection unchanged, both required inner folds, unequal fold sizes and declared aggregation, unsupported/degenerate bounds, exact ties, no-feasible fallback separation, target-time alarm causality, group/gap resets, zero-severity identity, clean versus corrupted replay, static CQR preservation, method-specific online scores, no double adaptation and emitted/consumed-bound equality.

Complete the specified synthetic smoke with two operational folds, group resets, model seed 42, the five catalogue seeds, CQR/uncalibrated bounds, static plus one declared rolling setting, and immediate plus an applicable temporal rule. Use deterministic sufficient-support fixtures to test feasible selection, a separate insufficient/all-infeasible fixture, and one tiny actual CQR fit for interface verification.

Keep reduced smoke grids and fixtures marked SMOKE ONLY. Never relax the scientific validator to accept them as full results. Verify checkpoint corruption rejection and zero-refit resume. Save exact commands, exit statuses, expected/observed row keys, resource measurements and the emitted/consumed stream hashes.

Run the relevant regression suite after implementation; broaden checks only for a concrete dependency risk or existing project gate. Do not stop after producing another planning document: complete the implementation and bounded smoke unless a real blocker prevents it.

## 5. Publish the reviewable result

Commit and push relevant code, tests, amendment/configuration, no-fitting support tables, smoke evidence and a concise AMENDMENT004_IMPLEMENTATION_REPORT.md on review/current-dissertation-20260913, or a clearly named descendant review branch if needed.

Update review/CURRENT_EVIDENCE.md with exact paths, run IDs, evaluated code/config hashes and the new remote head. Keep small CSV/JSON evidence, execution logs and the report accessible from GitHub. Preserve earlier evidence and avoid raw datasets, secrets, environment directories or unnecessary bulky artifacts.

Report these separately:
1. Software contracts implemented and tests actually passed.
2. Dataset/fold support established by the no-fitting preflight.
3. Synthetic smoke completion and limitations.
4. Readiness for a bounded real-data operational pilot; this is not full-study or dissertation readiness.

Return the branch URL, exact commit SHA, links to the implementation report and support tables, remaining concrete blockers, and the single next bounded real-data execution proposal with estimated work. Do not call files existing, test success or a smoke result proof of reliable alerts.
