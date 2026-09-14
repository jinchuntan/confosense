# Conditional-context replay implemented and synthetically validated

The amendment-005 C engine now executes observation-time faults through actual causal features and serialized predictors, with four fixed .95 controls, five rules, independent context state and original-stream workload. Both synthetic cadence workflows and zero-fit completed resumes passed. Real C fitting/replay was not launched.

Current totals remain **70/195 matched forecasting units, 250/1950 interval cells, and 9/27 unique seasonal computations**. All five declared interval methods are implemented; the 1,700 remaining interval cells require scope execution and their recorded owner prerequisites, not additional method families. Full-study readiness remains false.

The next bounded execution proposal is **PLEIA energy, fold 2, seed 42, h1: 68 published contexts, 2,856 fault slots, 68 clean identities, four controls and five rules, plus original clean workload**. Its C role masks require three new shared quantile estimators and one CQR conformalization; matched owners cannot be reused. This proposal awaits a new execution instruction. The separately versioned retrospective energy mask is proposed and unapproved; it does not block primary C execution.

Links: [evidence index](review/context_replay005_implementation_20260914/EVIDENCE_INDEX.md), [implementation report](review/context_replay005_implementation_20260914/IMPLEMENTATION_REPORT.md), [support and exact dependencies](review/context_replay005_implementation_20260914/SUPPORT_GATE_STATUS.md), [interval diagnosis](review/context_replay005_implementation_20260914/INTERVAL_FAILURE_DIAGNOSTIC.md), [protocol crosswalk](review/context_replay005_implementation_20260914/PROTOCOL_TO_CODE_CROSSWALK.md), [energy sensitivity proposal](review/context_replay005_implementation_20260914/ENERGY_SENSITIVITY_SPEC.md), [exact first-run proposal](review/context_replay005_implementation_20260914/FIRST_CONDITIONAL_CONTEXT_RUN_PROPOSAL.md).

<!-- context-replay005-implementation-20260914: historical status follows; current status is above -->

# Remaining study execution plan: matched models, methods and operational endpoints

13 September 2026. **Plan and no-fit inventory complete; no new fitting authorized or executed.** [Amendment-005](AMENDMENT005_PROPOSAL.md) resolves the support design; the matched forecasting comparison proceeds independently of event support. The existing PLEIA pilot and BDG2 benchmark remain preserved rather than rerun for this report.

## Exact completion matrix and prerequisites

The [machine-readable experiment matrix](smart_building_conformal/outputs/amendment005/support_design_v1/experiment_matrix.csv) has **1,560 task/horizon/fold/model-seed/model/level rows**, including explicit seasonal inapplicability. It binds data/role hashes, sample counts, expected fitting calls and evidence paths. [273 role records](smart_building_conformal/outputs/amendment005/support_design_v1/forecast_roles.csv) and thirteen compressed membership tables provide actual dates and row IDs for every horizon and all three folds. All 156 train/calibration/test/tuning boundaries passed no-fit validation. RICO uses the separately versioned 41/41/43-run outer batches, never a row cut through a run. Existing PLEIA pilot hashes match exactly.

| Task | Horizon steps | Physical horizons | Primary matched models | Seasonal applicability |
|---|---|---|---|---|
| PLEIA temperature | 1,3,6 | 10,30,60 min | Persistence, XGBoost, Attention-LSTM | Daily 144-step baseline; actual common calibration/test rows all supported |
| PLEIA energy | 1,3,6 | 10,30,60 min | Same | Daily 144-step baseline; all common rows supported |
| RICO | 5,15,30,60 | 5,15,30,60 min | Same | Inapplicable: no daily cycle inside an independent four-hour run; never reach across runs |
| BDG2 | 1,3,6 | 1,3,6 hours | Same | Daily 24-step baseline; all common rows supported |

All tasks retain outer IDs 0/1/2 and model seeds 42–46. Forecast levels are 90/95%. The primary three-model comparison comprises **195 paired task/horizon/fold/seed units, 585 point cells and 1,170 interval cells**. Three paired units are reusable from the completed PLEIA pilot: 9 point /18 interval cells. Required new evidence is **192 paired units /576 point /1,152 interval cells**. Every learned model/unit has four inner candidate-fold fits plus one final fit; the remaining work is **1,536 tuning +384 final =1,920 learned fit invocations**. The two interval levels share each model fit and are not counted twice.

| dataset | model | status | point_cells | tuning_fits | final_fits |
| --- | --- | --- | --- | --- | --- |
| bdg2 | attention_lstm | required_new | 45 | 180 | 45 |
| bdg2 | persistence | required_new | 45 | 0 | 0 |
| bdg2 | seasonal_naive | required_new | 45 | 0 | 0 |
| bdg2 | xgboost | required_new | 45 | 180 | 45 |
| pleia | attention_lstm | completed_reusable | 3 | 12 | 3 |
| pleia | attention_lstm | required_new | 42 | 168 | 42 |
| pleia | persistence | completed_reusable | 3 | 0 | 0 |
| pleia | persistence | required_new | 42 | 0 | 0 |
| pleia | seasonal_naive | required_new | 45 | 0 | 0 |
| pleia | xgboost | completed_reusable | 3 | 12 | 3 |
| pleia | xgboost | required_new | 42 | 168 | 42 |
| pleia_energy | attention_lstm | required_new | 45 | 180 | 45 |
| pleia_energy | persistence | required_new | 45 | 0 | 0 |
| pleia_energy | seasonal_naive | required_new | 45 | 0 | 0 |
| pleia_energy | xgboost | required_new | 45 | 180 | 45 |
| rico | attention_lstm | required_new | 60 | 240 | 60 |
| rico | persistence | required_new | 60 | 0 | 0 |
| rico | seasonal_naive | inapplicable | 60 | 0 | 0 |
| rico | xgboost | required_new | 60 | 240 | 60 |


Seasonal adds **135 point /270 interval cells** across nine applicable task/horizons, implemented as **27 unique deterministic horizon/fold computations with five paired seed aliases**, zero learned fits. The matrix explicitly records 60 RICO seasonal point /120 level cells as inapplicable. Persistence also has no stochastic fitting; any reuse across seed aliases must retain complete identities and exact paired targets. Do not describe repeated baseline aliases as independent training replicates.

The historical operational CQR quality rows have different owners/masks/protocols and do not fill the matched own-model rows. The broader [five-method interval matrix](smart_building_conformal/outputs/amendment005/study_plan_v1/interval_method_matrix.csv) retains **1,950** level/horizon rows for quantile-uncalibrated, CQR, recentred-EnbPI static/updated and DSCP. This is additional required method evidence, not an assertion that 1,950 independent fits are needed. Share CQR/uncalibrated owners; share static/updated EnbPI where the same trained owner and calibration contract permit. DSCP consumes joint-origin multi-horizon predictions from the declared owner, not a fake single-horizon substitute. Record actual MAPIE bootstrap sub-estimator counts from the executed owner; no GPU or unmeasured fit-count shortcut is assumed.

## Smallest next implementation/run package

**Implement `src.matched_forecasting005`, then request/receive authorization for one PLEIA-energy horizon 1/fold 0/seed 42 matched unit containing persistence, XGBoost and Attention-LSTM.** No fitting authorization is implied by this document. The exact proposed [unit specification](smart_building_conformal/outputs/amendment005/study_plan_v1/next_forecast_unit.json) fixes all candidates and identities. It has **29,719 fitting, 9,907 final-calibration and 9,909 test rows**, three point cells, six interval cells, eight tuning and two learned final fits. This measures the next task's cost and matched errors without requiring operational event support.

The current `src.model_comparison_pilot` entrypoint exists but explicitly rejects another dataset/fold/seed. `pilot_data.pilot_roles` also hard-codes chronological splitting, so it must not be applied blindly to RICO. The proposed generalized command **does not exist yet**; this was checked rather than assumed. The [dry-run checker](smart_building_conformal/scripts/check_remaining_study005.py) is executable now and never fits models.

Required entrypoint work is concrete:

1. Add `freeze`, `readiness`, `run`, `validate` and `resume` actions to the new module; do not relax the old pilot's guard or modify its files. Consume matrix keys and exact data/role hashes, the frozen two-candidate configuration and the appropriate group-aware role constructor already exercised by the no-fit generator. Refuse absent keys, changed source/config/data, duplicate/missing cells and unsafe boundaries.
2. Generalize the existing measured `model_comparison_pilot.run_unit` logic without hard-coded `pleia/f0/s42` output fields. Use `pilot_data.build_support`, bounded LazyLSTM sequences and matching flat features. Preserve target_lag0 availability, input schemas, training-only normalization, own-model predictions/calibration residuals, inner-only candidate/epoch selection and separate phase resource meters. `pilot_roles` compatibility is required for the completed PLEIA cells; current-source production resume may not impersonate their old source.
3. Use one immutable checkpoint per dataset/horizon/fold/seed/model with serialized fitted artifacts and COMPLETE hashes; reuse the repaired hash-only completeness path. Verify shared-level fitting once. Add a read-only compatibility/reuse ledger for historical pilot units instead of rewriting their identities.
4. Check actual RAM/disk, persist command/source/config/data/PID/timestamps/exit through `scripts/log_pilot_command.py`, and serialize all real fits. Keep existing CPU environment, one numerical/Torch thread, `n_jobs=1`, batch 256, 3 GiB launch RAM and 8 GiB disk guard; retain the existing epoch memory guard. Do not reduce cohorts, model size, thresholds or candidates due to performance. Preserve incomplete attempts and support completed-unit resume only, with zero new fits when complete.
5. Before the real unit, pass focused train/cal/test sentinel, run-boundary, candidate-selection/epoch, own-model-radius, common-target, checkpoint corruption and forbidden-fit-resume tests. A tiny integration fixture, if fitting is required, belongs in the next explicitly authorized package. The present task used no learned fits, including tests.

Future command, executable only after that implementation and authorization:

```powershell
& C:/cfs_venv/Scripts/python.exe -B scripts/log_pilot_command.py --log outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1.log -- C:/cfs_venv/Scripts/python.exe -B -m src.matched_forecasting005 run --matrix outputs/amendment005/support_design_v1/experiment_matrix.csv --dataset pleia_energy --horizon 1 --outer-fold 0 --model-seed 42 --out outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1
```

Acceptance: actual exit 0; exactly 3 point/6 interval cells; all models share fitting/calibration/test target IDs; eight tuning/two final learned fits and zero persistence fits; independently recomputed saved MAE/RMSE, coverage/MPIW/Winkler and phase costs; unchanged historical hashes; completed-unit resume invokes zero fitting routes. Low coverage or disappointing LSTM accuracy is an outcome, not grounds to retune. Publish that bounded unit and measured expansion estimate before continuing the queue.

## Prioritized execution queue and costs

The [192-unit queue](smart_building_conformal/outputs/amendment005/study_plan_v1/forecast_execution_queue.csv) specifies exact dataset/horizon/fold/seed, argv, fresh output path, prerequisite, fit count and labelled planning range. It contains each required core unit exactly once and excludes all three reusable pilot units. Priority 1 is the package above; priority 2 is RICO h5/f2/s42, priority 3 BDG2 h1/f2/s42, then remaining units in the published order. Do not launch the whole queue automatically. Each first-task measurement is a resource gate before authorizing a larger chunk; a failed integrity/resource check stops execution without changing settings.

| priority | dataset | horizon | outer_fold | model_seed | learned_fit_invocations | scenario_low_model_seconds | scenario_high_model_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | pleia_energy | 1 | 0 | 42 | 10 | 111.888 | 1026.13 |
| 2 | rico | 5 | 2 | 42 | 10 | 48.6874 | 446.513 |
| 3 | bdg2 | 1 | 2 | 42 | 10 | 194.509 | 1783.84 |


These are scheduling scenarios: the minimum/maximum **measured PLEIA three-model per-horizon phase totals**, scaled by fitting-row count and factors 0.5/3. They exclude preparation, I/O, validation, channel-dimension differences and model-dependent epochs; they are not statistical intervals or four-task ETAs. The first energy unit has the same fitting-row count as the PLEIA reference; allow roughly **2–20 minutes** as an initial wall-time planning allowance, then replace it with measurements. RICO and BDG2 learned-model costs remain unmeasured. Historical operational CQR runtimes cannot be substituted for Attention-LSTM/XGBoost costs.

Measured reference: the completed PLEIA pilot has three-horizon phase totals 864.317 s for LSTM and 18.009 s for XGBoost; persistence 0.030 s. The current three-fold operational benchmark's 3,491.322 s uses CQR-owned HistGradientBoosting and is a different task. The measured preparation-copy repair and lazy batches are already in place; do not repeat those investigations. Record separate tuning, final fitting, calibration and inference seconds, sample throughput, peak/baseline/incremental RSS, process CPU, available RAM and actual command wall time. Nested phases must not be added to their enclosing totals. This environment is CPU-only; no GPU saving is claimed.

After core matched cells, execute the [27-job seasonal queue](smart_building_conformal/outputs/amendment005/study_plan_v1/seasonal_execution_queue.csv) with exact same calibration/test targets and own seasonal residuals; then complete the full-method adapter/quality matrix. For DSCP, intersect `(original group, origin_time)` across all declared horizons separately within calibration/test roles, check strict boundaries, retain direct-horizon adaptation labels, and use only historical calibration predictions/errors for clustering/merging. Its clustering/neighbor costs require a bounded measurement before a full multi-horizon launch; an imported module is not experimental evidence.

Implement the C context replay only after matched-runner correctness is established. Its first bounded fitting/replay proposal must name the dataset/fold/seed and fixed .95 controls, use the published context hashes, and include zero-control, causal-input, released-score, method-identity, alias/null and original-unit contribution validation. Do not run unsupported amendment-004 primary selection and label a C result as a replacement. BDG2 full-grid operational execution remains a separate authorization; preserve its reduced-grid evidence.

## Required evidence and optional scope

| scope | obligation | exact_status | rationale |
| --- | --- | --- | --- |
| matched_forecasting | required | 195 paired units; 585 core point/1170 level cells; 18 levels reused, 1152 pending; 1920 new learned fits | panel LSTM versus XGBoost and own-model intervals |
| seasonal | required | 135 point/270 level cells on nine applicable task/horizons; 27 unique deterministic runs with five seed aliases; RICO 60 point/120 levels inapplicable | daily history unavailable inside four-hour runs |
| interval_methods | required | 1950 level/horizon cells; shared estimator ownership; DSCP joint horizon adapter; no existing operational cell substituted | full declared method scope |
| operational_BDG2 | required_for_full_grid_claim | three seed 42 reduced-grid units complete; full 264-candidate five-seed scope unexecuted | abstentions preserved; no rolling diagnostic promoted |
| operational_PLEIA_RICO | original_question_not_estimable_under_A | A retained as support-limited replay; proposed C conditional challenge separately evaluated | explicit question change, not evidence of four-task deployment feasibility |
| robustness_contamination_recovery | required_for_existing_claims | 60 legacy units x15 cells=900 remain historical/unexecuted under current valid design; requires an amendment-005 crosswalk and serialized owners | retain zero controls, calibration-only contamination, closed-loop cascades and censored recovery; no automatic launch |
| inference | required | original-unit paired metrics, five seed contributions aggregated; no IID rows/catalogues; unavailable CIs preserved | post-inspection historic-period evidence |
| PLEIA_energy_meter_sensitivity | required_sensitivity | keep primary meter values; separately version keep/mask stalled/zero/catch-up periods | do not silently clean |
| unseen_building_portability | optional_unless_claimed | separate held-building design and resources; not supported by ten recurring buildings | no current portability claim |
| additional_model_seeds | optional_beyond42to46 | not in authorized scope | five declared model seeds remain required; no best-seed selection |


The amended execution crosswalk must retain the legacy robustness/contamination/recovery obligations: 900 intended cells across 60 legacy core unit keys; fixed zero controls; actual closed-loop features/residuals; calibration-only contamination; group-specific coverage/workload shifts, cascades, restricted recovery time and censoring. Original amendment003 fault definitions and frequency must not be silently equated with C's 21 strata. Unsupported primary pipelines retain abstention; any fixed diagnostic recovery is labelled diagnostic. RICO membership changes require new IDs and an explicit row-count crosswalk, not relabelling old cells. No full-method, robustness or full operational result is newly claimed.

Report paired LSTM-minus-XGBoost MAE as the primary forecasting contrast for each of 13 task/horizon combinations, with RMSE, interval quality and computational trade-offs alongside it. Average model-seed contributions within original groups/time blocks before paired inference; do not resample five seeds as independent test populations. Keep original folds and phase/building dependence. If formal tests are reported, treat the 13 MAE contrasts as the declared Holm family; width, coverage, Winkler and timing contrasts are secondary and must remain jointly contextualized. No equivalence claim follows from a CI spanning zero and no width benefit is claimed without coverage context.

The no-fit plan checker exited 0, confirmed all 192 queued keys and 1,920 required learned fits, and explicitly reported the missing generalized entrypoint. This is a concrete implementation prerequisite, not an unresolved design question. Scientific/full-study readiness stays **false** pending implementation, authorized execution, output verification and correctly scoped inference.

The DSCP intersection is now concretely enumerated: [36 joint-origin role support rows](smart_building_conformal/outputs/amendment005/support_final_checks_v1/dscp_joint_origin_support.csv) and [exact common-origin memberships](smart_building_conformal/outputs/amendment005/support_final_checks_v1/dscp_joint_origin_membership.csv.gz). All 24 fit/calibration/test boundaries and whole-run constraints passed; each of 12 joint calibration sets has at least 400 rows. Fitted predictions, joint calibrators and their measured costs remain required.
