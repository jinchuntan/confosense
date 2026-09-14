# Next task: BDG2 matched interval methods, remaining fold-2 seeds

Recommended coding model: GPT-5.6 Sol.
Reasoning effort: High.
Reserve Astra / Extra High for a concrete unresolved statistical-design, causal-correctness or architecture problem. A long-running experiment alone does not call for a stronger model. Continue routine repairs and execution autonomously.

## Starting point and authorization

Continue from `review/matched-intervals005-bdg2-20260914`, published commit `4853f634134a77b347ee29f781e3e81fe0b207cf`. Preserve valid local descendants if present; inspect ancestry and unfinished processes before changing branches. Never reset or overwrite existing work.

The user authorizes the necessary bounded implementation, meaningful regression/synthetic checks, all four real-data units below, independent validation, reporting, backup and publication on a new non-main review branch. Proceed automatically between these stages. This supersedes the earlier proposal's `authorized: false` for exactly these units. Main, earlier review heads, historical results and frozen scientific inputs must remain unchanged.

Suggested result branch: `review/matched-intervals005-bdg2-multiseed-20260914`. If that branch already contains progress, resume its verified work. Do not merge or check out application code from the separate instruction branch; retrieve this instruction file only.

The goal is to finish this four-seed extension, producing a five-seed BDG2 fold-2 interval-method comparison. It is not authorization to launch the rest of the study.

## Read the existing evidence first

At the starting commit:
- `BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md`
- `MATCHED_INTERVALS005_IMPLEMENTATION_REPORT.md`
- `review/matched_intervals005_bdg2_20260914/EVIDENCE_INDEX.md`
- The five validation errata and `method_specification_resolved_v2.json` in that review directory.
- `review/CURRENT_EVIDENCE.md` and `MATCHED_METHOD_READINESS_MAP.md`.
- Under `smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/`:
  `next_proposed_method_keys.csv`, `next_proposed_costs.json`, `interval_completion_overlay.csv`, and `additional_integrity_validation.json`.
- Existing runner, owner, data, stream, validation and checkpoint modules; the pilot coordinator and acceptance tests.

Read what is needed for the implementation and evidence contracts. Do not repeat completed historical studies or broad audits without a concrete new risk.

## Exact real-data scope

Dataset BDG2, outer fold 2, model seeds 43, 44, 45, 46.
Each seed is one joint triplet with horizons 1, 3, 6 hours and confidence levels 0.90 and 0.95.
All five methods:
1. `quantile_uncalibrated`
2. `cqr`
3. `recentred_enbpi_static`
4. `recentred_enbpi_updated`
5. `dscp`

Execute sequentially in seed order 43, 44, 45, 46. Require exact equality with the 120 published proposed keys; reject missing, duplicate or additional keys.

Expected new work under the unchanged installed factories:
- 24 CQR wrappers, containing 72 quantile-estimator fits.
- 12 EnbPI wrappers, containing 132 XGBoost-estimator fits.
- Total 204 new learned-estimator fits in these two families.
- Four DSCP calibrators and up to the declared five KMeans candidate fits per calibrator, expected 20 calls under the pilot's supported path. Log actual candidate attempts and degenerate cases explicitly.
- Zero new matched forecasting XGBoost, LSTM or persistence fits.
- Reuse all twelve corresponding saved matched XGBoost horizon/seed owners for DSCP.
- 120 newly emitted and independently checked clean alert streams.
- Zero new seasonal-baseline computations when source/role/target identities match the completed seed-42 baseline. Use explicit read-only aliases.

Nested wrapper/calibrator calls are separate ledger categories; do not add them again to learned-estimator counts or runtime totals. Do not fit extra models to make a count match. Reconcile any unexpected factory behavior before continuing.

## Bounded implementation

1. Generalize the seed-42-only scope and naming in `src.matched_intervals005` and necessary supporting orchestration. Use an explicit, versioned authorization manifest for the four new seeds and exact matrix keys. Retain rejection of other datasets, folds, horizons, levels and methods. This is a narrow extension of the permitted scope, not removal of the guard.
2. Give every seed its own frozen design, protocol identity, owner/calibrator checkpoints, emitted streams, operation ledger and validation directory. Remove stale seed-42 labels from newly generated identities without changing original identities.
3. Verify actual seed propagation through HistGradientBoostingRegressor, MAPIE wrapper, BlockBootstrap, EnbPI base-estimator construction and DSCP clustering. Inspect resolved estimator parameters and native seed conventions; a filename alone is insufficient. Native bootstrap-derived child seeds need not all equal the top-level seed, but their derivation must be traceable.
4. Never share fitted/calibrated owners or adaptive histories across model seeds. Within a seed, retain the intended CQR/raw-quantile and static/updated EnbPI sharing and level-specific state isolation.
5. DSCP must resolve each horizon to that seed's historical matched XGBoost artifact, with source, feature, row, role, target and owner hashes checked. Do not substitute the seed-42 forecasts or a CQR median.
6. Implement seasonal aliases with source and target-support hashes. A verified alias points to the original deterministic values and own-residual intervals; it is not a newly completed computation. Keep this distinct from the 120 method cells.
7. Adapt the existing durable coordinator rather than adding an unrelated execution system. Maintain exact process identities, exclusive locking, per-stage checkpoints, actual exit receipts and atomic progress recovery.

The previous independent validator is already repaired. New protocols must freeze the resolved native asymmetric CQR convention explicitly. Do not recreate the erroneous symmetric specification. Preserve native EnbPI float64 OOB accumulation, float32 prediction roundtrip handling, unchanged numeric tolerances and raw-crossing records. Keep the observed nonfinite OOB-score limitation visible; do not change bootstrap count, remove evaluation rows or silently alter quantiles.

The existing source-identity exception applies only to exact historical, read-only validation/completed resume. Do not expand it into permission to fit against an old protocol after changing source. Freeze fresh source/protocol identities for new runs. Preserve old evidence and, if an old validation is necessary, use its pinned source or a fully specified read-only compatibility check.

## Pre-fit verification and freeze

Run meaningful focused checks for the changed scope, seed propagation, per-seed owner resolution, state isolation, seasonal aliases, operation accounting and interrupted/completed resume.

Reuse existing acceptance evidence for unchanged scientific algorithms. Tiny synthetic fits are authorized only where needed to prove a changed behavior, separately logged from research fitting. Use no-fit spies, saved fixtures and direct parameter checks where adequate; do not repeat all historical fits for reassurance.

Keep the native-versus-causal method definitions unchanged:
- CQR and uncalibrated methods share the exact native quantile owner.
- Static EnbPI retains the native recentering convention.
- Updated EnbPI retains amendment-004 causal signed-residual ranks and initialization, including its documented difference from the legacy interpolated policy.
- DSCP retains its declared clustering, assignment, scoring and direct-horizon adaptation.
- Release only available observations with target time no later than the current origin. Compare each matured observation with its immutable previously issued interval before admitting its residual.
- Isolate original buildings and contiguous segments. No future truth or other-seed/group adaptive state may enter an earlier prediction.

Freeze all four units before real fitting and verify readiness:
- Unchanged production settings, package versions, candidates, split dates, features and data.
- Same ten known buildings and native per-horizon support.
- Joint origins joined on original group and origin time, with the ordered target timestamps verified.
- Expected joint role counts remain 51,534 fit, 17,270 calibration and 34,590 test origins per horizon; verify memberships and hashes, not only counts.
- Original direct-model training supports stay intact; do not refit them on the joint intersection.
- Complete historical forecasting owner availability for every seed.
- Adequate disk and the existing resource policy.

Proceed directly to the real batch after these checks. Do not stop at “ready” or ask for permission again.

## Execution and validation

For seed 43, run the complete triplet, independently validate it and verify completed resume before proceeding automatically to seed 44, then 45 and 46. This is a gate against repeating an implementation defect, not a new approval step.

Use the repaired independent reconstruction to check:
- 30 method cells per seed on native support and a separate 30-row common-support view.
- Coverage, MPIW, Winkler, point-owner predictions and per-building contributions.
- Reloaded fitted-owner predictions, native score/rank arrays, emitted bounds and complete DSCP assignments.
- Immutable issued versus consumed interval/availability hashes for all 30 streams.
- Exact operation counts, owning seeds and sharing relationships.
- Completed resume with both learned fitting and calibrator fitting forbidden, preserving all scientific run files.

Existing scientific tolerances remain unchanged. An observed small nonzero difference within the declared tolerance must be reported as such; do not claim exact equality. Poor coverage or a losing method is a result, not an integrity failure or reason to alter settings.

Use an empty event catalogue and the frozen immediate single-sample alert rule at hourly frequency. Report numerical, availability and combined background episode rates with actual asset-day exposure. Do not manufacture recall, F1, detection delay, confirmed false-alarm rates or operational feasibility from this clean-stream exercise.

Use CPU/thread 1/n_jobs 1 and bounded inference/DSCP processing. The existing 3 GiB launch-RAM reference is nonblocking; preserve the 256 MiB epoch floor and 8 GiB disk guard. Run one real-data worker at a time. Measure preparation, fit, conformalization, assignment, validation and resume costs separately.

If a process fails, preserve the exact failure and completed artifacts. Fix a concrete orchestration/validation defect with an appropriate regression check; continue from valid checkpoints without refitting completed owners. A scientific change that invalidates already issued outputs requires a separately versioned affected-run record; never silently mix source identities. If a real scientific ambiguity cannot be resolved under the frozen method, checkpoint the affected work and state the precise blocker while completing independent authorized tasks.

Do not continuously spend model calls narrating or polling healthy numerical computation. Use the durable coordinator and supported background tracking, with useful status updates and restart information.

## Analysis and completion

Combine these 120 new method cells with the preserved 30 seed-42 cells into a five-seed table containing exactly 150 unique method keys.

Deliver:
- Per-seed native-support and common-support comparisons, plus all-five-seed summaries.
- Per-building contributions, actual coverage deviations, MPIW, Winkler, crossings and nonfinite OOB counts.
- Paired shared-owner contrasts: CQR minus raw quantiles, updated minus static EnbPI.
- Seed-level mean, standard deviation and range as descriptive training-variability summaries. The five seeds use the same buildings and test periods; they are not five independent population samples. Do not derive population confidence intervals, significance or equivalence from five seeds.
- Read-only deterministic seasonal aliases, with original source identities.
- All clean-stream checks and workload denominators; retain native versus common-support distinctions.
- Per-seed DSCP cluster sizes, selected neighbours, candidate outcomes, assignment cost and owner identities.
- Complete fit/calibrator ledgers, model artifacts, source snapshots, commands, actual exit statuses, validation receipts and zero-fit resumes.
- A concise completion report, source-linked figures and numerical panel-response update.
- Updated evidence index, current recovery status, readiness map and remaining-work counts.

After successful completion:
- Matched forecasting remains 70/195 paired units.
- Interval-method completion becomes 150/1950 cells, with 1,800 remaining.
- Native/common metric views do not double that completion count.
- The three seasonal computations already completed remain three; record new seed aliases separately.
- No full-study or dissertation-publication readiness claim is permitted on this batch alone.

Give a measured next execution proposal aligned with the remaining-study plan and method-readiness map. Do not automatically launch the remaining forecasting queue, new datasets/folds, injected fault catalogues, full operational selection or robustness/contamination/recovery work under this handoff.

## Backup, publication and final response

Use existing backups and artifact-sharing conventions, including lossless parts/manifests where necessary. Publish relevant code, protocols, CSVs, figures, fitted artifacts and evidence to the new review branch so the reviewer can fetch them directly. Preserve main and every previous review head. Verify the published head and key direct artifact readbacks. Do not publish ignored raw source datasets or credentials.

A GitHub authentication problem must not strand healthy authorized local work: finish and preserve it, then report the specific publication blocker if it persists.

Complete all four units and reporting without another approval request. The pilot's measured linear scaling estimates approximately 8,403 seconds (2 hours 20 minutes) for four runs, successful validation and resumes; this excludes new implementation, tests, freezes, failed attempts, reporting and publishing. It is a planning estimate, not a deadline. Finish early if complete; continue healthy authorized work if it takes longer.

Return the published URL and SHA; exact completed/pending counts; actual fit counts and exits; validation and preservation results; measured elapsed/CPU/memory costs; restrained five-seed findings; remaining limitations and next step. If interrupted, provide an accurate durable checkpoint and one exact resume command. Never report an active process or unfinished unit as complete.
