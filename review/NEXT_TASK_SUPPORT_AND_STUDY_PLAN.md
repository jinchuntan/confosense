# Next task: resolve operational support and freeze the remaining study plan

13 September 2026. Source publication: `9b5acb49531ce12706285c3f040310c0ab6053dd`, branch `review/bdg2-threefold-20260913`.

## Outcome required

Complete one **no-fitting support-design and scope task**. Produce a quantified explanation of the unsupported PLEIA temperature, PLEIA energy and RICO evaluations, a recommended versioned evaluation design with actual memberships/schedules where applicable, and an executable plan for the remaining dissertation experiments. Do not finish by repeating that support is insufficient without resolving what can be estimated and what to run next.

The BDG2 three-fold reduced-grid benchmark is complete. Preserve its results and abstentions. Its static-CQR versus shared-fit uncalibrated contrast is useful exploratory evidence: about 28.1% lower pooled clean workload and coverage 94.68% versus 84.66%, with a recall change of -0.353 percentage points and uncertainty spanning zero. This is not recall equivalence or successful primary deployment selection.

When the user provides this handoff, the no-fit calculations, scripts, focused verification, concrete design documents and review-branch publication below are authorized. Model fitting, a new performance search and a full-study launch are outside this task.

## Starting state

Continue from the latest local descendant of `review/bdg2-threefold-20260913`, recording its relationship to the publication SHA. Preserve later local changes. Read the current evidence index, three-fold report, operational plan, amendment-004 design/events code and existing preflight evidence.

Read this handoff with git show. Do not check out or merge the old implementation beneath `review/pilot-evidence-20260913` into the current code.

Preserve main, all completed pilots/benchmarks, historical sources/configuration/manifest hashes and external backups. Work on a new `review/support-design-20260913` branch or a clearly named unused equivalent. Relevant code and reproducible research evidence may be pushed there; never to main, never with a force push.

## 1. Establish the actual constraints once

Reuse the published no-fit tables; only recompute to verify identity or obtain missing information. Do not repeat model, preparation-memory or checkpoint investigations already completed.

For every unsupported task and inner/outer role, publish:
- actual dates, frequency, horizon, eligible observed rows, original groups/runs, contiguous segments, original asset-days and training/calibration sizes;
- requested, hostable, placed, effective, null and rejected events;
- all 21 family/severity counts, distinct effective onsets and original resampling units;
- exact reasons for count insufficiency, placement limits, unbalanced stratum allocation, null changes, finite-rank limits and insufficient independent units, distinguishing these mechanisms.

Reconstruct the current request formula exactly:
`requested_per_catalogue = floor(0.5 * eligible_asset_days + 0.5)`.
Five catalogues do not multiply real observation exposure. The support gate needs at least five distinct effective onsets in each of 21 strata: at least 105 effective event instances in the bank is a necessary, not sufficient, count condition.

The published evidence already shows:
- PLEIA temperature and energy earliest inner blocks have approximately 25.8 asset-days: 13 requests per catalogue, 65 across five, below 105 before any null or failed placement.
- Their middle inner blocks have approximately 38.7 asset-days: 19 per catalogue, 95 total, also insufficient.
- Their later inner blocks have approximately 51.6 asset-days: 26 per catalogue, 130 total. Inspect distribution across strata, nulls and distinctness rather than declaring these impossible from total count alone.
- RICO inner blocks have approximately 5.83–5.99 asset-days over 38–39 runs: three requests per catalogue, at most 15 total.
- Each current RICO outer test has 221 eligible minute observations, approximately 0.1535 asset-days, and rounds to zero event requests. No injected-event recall can be estimated there.
- RICO uses only one whole run per outer fold under `make_outer_folds`. Verify the current retained-run inventory (historical recovery report lists 207 runs/49,680 raw observations). Compute an all-eligible-data optimistic request bound first: if even that is insufficient, no rearrangement into smaller train/calibration/test blocks can fix the unchanged count design.

Separate arithmetic impossibility from a lack of statistical precision. The 21-stratum/five-onset gate is a declared study rule, not a universal conformal-prediction theorem. Passing structural support does not demonstrate operational feasibility or adequate confidence-bound precision.

Inspect the deterministic stratum assignment:
`STRATA[(event_number + rotation) % 21]` with five rotations 0–4. Determine which strata short banks can never request and how repeated allocations behave. Label this a design limitation unless an implementation/specification mismatch is demonstrated. Do not alter the historical schedule or silently treat null realizations as effective.

## 2. Compare a small, explicit set of design choices

Evaluate these three choices using structure/support calculations only, without fitting models or reading prediction-performance values to choose the design:

A. **Keep amendment 004 unchanged.** Give exact estimable endpoints and structural non-estimability per task. Forecast accuracy, interval quality and measured clean-stream workload may still be estimable when 21-stratum injected-event recall or its gate is not.

B. **Revise the sampling plan while retaining the same estimand and incidence.** Quantify the minimum exposure, original runs/blocks and catalogue budget needed. Consider larger chronological validation blocks and batches of whole RICO runs where defensible. Show the effect on training/calibration support and independent evaluation units. If adding independent simulation catalogues is considered, derive a fixed count from a declared support/precision criterion before generating them, with a stopping rule; never keep drawing until a preferred model passes. More catalogues add simulation precision, not new independent buildings, runs or time periods. Distinguish an optimistic event-count bound from demonstrated support and precision.

C. **Separate natural-frequency replay from a balanced fault challenge.** Assess this as an explicitly different estimand, not an invisible replacement for A. Keep clean-stream workload per original asset-day and fixed-incidence replay separate. A balanced challenge may assess detection conditional on declared fault family/severity using predetermined eligible contexts and schedules, with shared contexts across methods and causal replay. It does not estimate real deployment fault prevalence, operational precision or real-world false-alarm probability.

For C, specify original run/time support, context/onset selection, warm-up, guard/follow-up requirements, independent replay resets, finite fixed replication, null-realization handling and pairing. Reusing a context across 21 injected variants does not create 21 independent observations. Do not duplicate rows to manufacture effective support, force zero-amplitude/no-change events into positives, or select easy onsets/severities after observing detection.

Any broadened RICO evaluation must preserve whole-run grouping and chronology, describe the run/phase distribution being evaluated and identify earlier training/calibration use of those runs. The other retained runs are not globally untouched holdouts. If broader memberships are proposed, version them separately; do not relabel old results.

Use verified primary sources where a methodological claim needs support. Distinguish literature-backed principles from this project's design choices. Do not invent a citation that supposedly requires the exact ratios, thresholds or event counts.

## 3. Make one recommendation and make it executable

Choose one recommended approach per endpoint/task and explain the trade-off concisely. Prefer retaining the unchanged operational benchmark plus a separately labelled controlled fault challenge if the current exposure cannot support the original operational question; confirm the choice from the no-fit evidence rather than assuming it works.

Produce a **post-inspection amendment-005 proposal**, separate from amendment 004. It must state:
- the research question and estimand for each endpoint;
- datasets/tasks retained and the exact target/cohort/physical horizons;
- original sampling/inference unit, chronology, memberships, calibration and tuning boundaries;
- event scheduling, fixed replication, missing/null behavior and support criteria;
- controlled baselines, estimator ownership, policies, selection rules, deployment constraints if applicable, and separate evaluation-only diagnostics;
- the handling of unsupported results and the precise claims that remain unavailable.

Do not loosen the historical 0.60 recall/1.0 workload gates to reverse BDG2 abstentions. Do not use pooled outer rolling-CQR metrics to promote it as primary feasible. Do not redefine the 21-stratum macro without naming a different endpoint. No narrowing of dissertation scope should be hidden.

For the recommended design, generate and verify concrete no-fit memberships, support tables and schedule manifests in a new directory. If count-only evidence cannot resolve a precision question, state the remaining assumption and specify the smallest diagnostic needed instead of claiming readiness. Keep feasibility/publication readiness false pending actual evaluation.

If no defensible plan can estimate a claimed endpoint from the existing data, record explicit non-estimability and the additional data/exposure needed. That decision must not block evaluation of unrelated supported forecasting/interval endpoints.

## 4. Close the gap to the panel's model-comparison requirement

As part of the execution plan, inventory the matched forecasting/interval/compute experiment independently of operational fault support. The completed PLEIA temperature pilot already exists; do not rerun it merely to create a new report.

Keep the declared 13 task/horizon combinations visible, along with all intended models, nominal 90%/95% levels and fold/model-seed scope. Record seasonal-naive or other method inapplicability with its actual reason. For the panel's Attention-LSTM versus XGBoost comparison, retain persistence, common evaluation targets, own-model calibration, inner-only tuning and matched information sets. Report MAE/RMSE, coverage, MPIW, Winkler, tuning/fitting/calibration/inference times and memory; an interval-width benefit requires coverage context. Existing environment is CPU-only unless measurements establish otherwise; do not invent GPU costs or gains.

Emit an exact experiment matrix showing completed reusable cells, required new cells, blocked/inapplicable cells, prerequisites and estimator-fit counts. Retain full method/DSCP/seasonal and robustness/contamination/recovery obligations in a separate scope ledger; an implemented module is not completed experimental evidence. Distinguish required evidence for existing claims from optional extensions, with a stated rationale for any scope change.

Give one prioritized execution queue with concrete commands and measured-cost-based planning ranges. Separate real measurements from extrapolations. Nominate the next single run or minimal implementation/run package, its expected artifacts and acceptance criteria. Check whether the command actually exists; if it does not, specify the exact entrypoint work needed. Do not conclude vaguely with “full study later.”

## Deliverables, verification and publication

Create:
1. `SUPPORT_DESIGN_AUDIT.md` plus machine-readable exposure/count/stratum/support and design-comparison tables.
2. `AMENDMENT005_PROPOSAL.md` plus concrete no-fit membership/schedule specifications for the recommended design, marked proposal and post-inspection.
3. `REMAINING_STUDY_EXECUTION_PLAN.md` plus an exact task/model/horizon/fold/seed/level completion matrix and resource assumptions.
4. Updated `review/CURRENT_EVIDENCE.md`, `PROJECT_RECOVERY_STATUS.md` and `PANEL_RESPONSE_MATRIX.md`. The recovery file's current top still says the BDG2 pilot has not launched: correct that stale resume summary, preserving historical sections clearly labelled as such.
5. A brief source/assumption register for methodological justifications and missing evidence.

Use focused meaningful checks for arithmetic, complete-bank stratum allocation, group integrity, deterministic membership/schedules and zero fitting; do not add tests that merely restate output constants. Preserve actual commands/exits and source/input hashes. Publish the report, relevant code and recomputable tables on the new review branch, verify the remote URL/SHA and keep main unchanged. The user should not need to upload CSVs manually.

The final response must give the diagnosed mechanisms, recommended estimands/design, what remains supported on each task, the precise next execution step, and the publication SHA. No model fits are authorized here. This is a decision-completing task to unblock the remaining experiments, not another repeated status audit.
