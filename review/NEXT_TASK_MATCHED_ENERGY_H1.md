# Next task: implement the matched runner and complete the first PLEIA-energy unit

13 September 2026. Reviewed source: `f1a71a19b4e227a9894a8e2c74686a642dca962a` on `review/support-design-20260913`.

## Goal and scoped authorization

When the user supplies this handoff, implement `src.matched_forecasting005` and **run the specified PLEIA-energy horizon-1 / outer-fold-0 / model-seed-42 matched experiment to completion**. This includes the necessary small integration-test fits and the real unit's eight tuning plus two final learned fits. Finish validation, the report and review-branch publication; do not stop after implementation to request fitting authorization again.

The historical audit and proposal correctly said no fits were authorized at that time. Preserve those documents and the old `future_fitting_authorized:false` proposal as historical evidence; record this later, explicitly scoped instruction in a new execution authorization/manifest. Do not misrepresent this as authorization to run the remaining queue, conditional-context challenge, full method grid or robustness study.

Continue from the latest local descendant of the source publication, preserving later work. Read this instruction with git show: the `review/pilot-evidence-20260913` branch has old implementation code beneath its handoffs. Do not check out or merge that old code over the current branch.

Create `review/matched-energy-h1-20260913` or a clearly named unused review branch. Preserve main, completed PLEIA temperature and BDG2 evidence, amendment-004 results/abstentions, original protocols and backups. No force push or main update.

## Read these current sources

- `REMAINING_STUDY_EXECUTION_PLAN.md`, especially the smallest implementation/run package.
- The matched-forecasting portions of `AMENDMENT005_PROPOSAL.md`.
- `smart_building_conformal/outputs/amendment005/study_plan_v1/next_forecast_unit.json`.
- `outputs/amendment005/support_design_v1/experiment_matrix.csv`, `forecast_roles.csv` and the exact forecast membership files, relative to `smart_building_conformal`.
- Existing `src/model_comparison_pilot.py`, `pilot_data.py`, `pilot_forecasters.py`, `pilot_conformal.py`, `unit_checkpoint.py`, and the group-aware no-fit `forecast_roles` implementation in `scripts/support_design005.py`.

The existing pilot entrypoint and its tags/keys hard-code PLEIA/fold 0/seed 42; `pilot_roles` is chronological only. The new runner must generalize those contracts rather than weakening the historical pilot's scope guard. The old no-fit checker explicitly asserts that the new entrypoint is absent; preserve its historical report and provide an appropriate current readiness check instead of rerunning that obsolete absence assertion as if it were a required scientific condition.

## Exact real-data scope

| Item | Fixed value |
|---|---|
| Dataset/target | PLEIA energy, existing block-B `dif_cons`, kWh per 10-minute interval |
| Horizon | 1 step / 10 minutes |
| Outer fold/model seed | 0 / 42 |
| Models | Persistence, XGBoost, Attention-LSTM |
| Intervals | 90% and 95%, each model's ordinary absolute-error split conformal |
| Expected final-fit/calibration/test rows | 29,719 / 9,907 / 9,909 |
| Role-bank hash | `2c01da7ec94037d9b88d36fa91b52f5ec841f85bc648406f8796c190ac7c4c92` |
| Data hash | `8bfbf2d874682c3d69016a5b2b5cd9586d83211bbc7d08f2d1563f696869362b` |
| Real learned fits | 8 tuning + 2 final, excluding separately identified tiny test fits |
| Completed metric cells | 3 point and 6 interval |

Retain exactly the two XGBoost and two LSTM candidates in `next_forecast_unit.json`: XGBoost 400 trees/depth 3 or 5 with all other recorded parameters unchanged; LSTM hidden size64/dropout0.2/batch256, learning rate0.001 or0.0005, maximum30 epochs/patience5. Sequence length24. Preserve the existing early-stopping convention and deterministic seeds.

Choose candidates by equally weighted mean MAE over the two purged inner validation folds in original units, with frozen exact-tie candidate order. Final LSTM epochs are the ceiling of the mean selected-candidate best epochs across the two folds. Do not use final calibration/test outcomes to choose candidates, epochs, features, preprocessing or parameters.

Keep the original energy observations and eligibility rules. Do not silently remove stalled/zero/catch-up periods, clip predictions, truncate intervals at zero or otherwise clean the target to improve metrics. The separately proposed meter-sensitivity analysis remains outside this first run.

## Implementation and pre-fit verification

1. Implement `freeze`, `readiness`, `run`, `validate` and explicit `resume` actions for one matrix unit. Support real dataset/horizon/fold/seed/model keys throughout filenames, checkpoint keys, payloads, CSVs and figures; no leftover hard-coded PLEIA labels. Validate matrix keys and scope before preparation/fitting.
2. Reuse the measured model/normalization/calibration routines and lazy sequence batches where appropriate. Extract reusable group-aware role construction into production code if necessary, verifying against the published roles. Do not import a reporting generator with data-generation side effects as the experiment engine.
3. Preserve common target IDs, target-time purges, target_lag_0 and permitted features, training-only input/target normalization and identical final fit/calibration/test membership across models. Verify two tuning folds lie entirely within final fitting data. Preserve original identifiers, including a literal group ID `None`, through CSV serialization.
4. Resolve and freeze every executable parameter, including inherited inference batch size, numeric/thread settings, feature/channel schemas and fallback behavior. Record the actual class/parameters/library versions. XGBoost must be identified as the estimator actually fitted, and intervals must use that model's own errors.
5. Recompute fresh data/role identities and actual dates against the published no-fit proposal. If they differ, diagnose before fitting; never rewrite the proposal hashes to make a mismatch pass.
6. Save a new immutable protocol/execution manifest and commit the evaluated implementation before the real run. Retain the frozen proposal as its parent. Full-study readiness remains false; use an explicit first-unit readiness status.
7. Use focused tests for chronology/whole-run role handling, future-target and calibration/test exclusion from fitting/selection, exact candidate/epoch selection, common support, own-model conformal radii, generic unit identities, checkpoint corruption and zero-fit resume. Tiny synthetic learned fits are allowed here and counted separately. Include a group-safe RICO fixture/no-fit membership check so the generalized interface does not claim unsupported grouped behavior. Do not train RICO or BDG2 in this task.
8. Preserve the original PLEIA pilot through read-only reuse/compatibility evidence, without rerunning its learned fits or impersonating its old source hash. Keep a reuse ledger for its three completed paired units.

## Execute the authorized unit

Use the existing compatible Python environment, CPU-only unless actual hardware evidence says otherwise, one numerical/Torch thread and `n_jobs=1`. Keep batch256, the existing epoch guard, the 3 GiB launch-available-RAM guard and 8 GiB free-disk guard. Measure preparation separately; do not repeat already solved memory investigations. Serialize all real fits.

Use a fresh directory such as `outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1`. Adapt the published command to the implemented freeze/readiness interface and verify its actual argument names. The intended run invocation is:

```powershell
& C:/cfs_venv/Scripts/python.exe -B scripts/log_pilot_command.py --log outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1.log -- C:/cfs_venv/Scripts/python.exe -B -m src.matched_forecasting005 run --matrix outputs/amendment005/support_design_v1/experiment_matrix.csv --dataset pleia_energy --horizon 1 --outer-fold 0 --model-seed 42 --out outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1
```

Record durable command/PID/start/end/exit information, evaluated source hash/commit, config/data/role hashes and actual resource measurements. The earlier 2–20-minute allowance is only a planning scenario, not a deadline or a reason to kill a healthy fit. Never launch a duplicate while a process is running.

Write one atomic checkpoint per model immediately after completion, including fitted artifact, preprocessing state, calibration predictions/errors, both interval levels, test predictions, tuning/history, parameters and resources. Both interval levels share that one model fit. Persistence incurs no learned fitting; count its initialization/prediction cost separately.

Preserve incomplete attempts and errors in their own logs. Reuse valid completed model checkpoints on explicit resume under the same identity; do not promise mid-fit recovery. Fix demonstrated implementation faults if needed, documenting whether fresh execution identity/output versions are required. Do not repeat a correctly completed experiment to obtain better scores.

## Independent validation and reporting

The completed run must have an actual exit0 and exactly three point/six interval cells, with no missing or duplicate model/level/support identities.

Recompute from saved calibration/test evidence independently of the production metric wrappers:
- MAE and RMSE in kWh;
- calibration residuals belonging to the corresponding fitted model;
- one-based rank `ceil((n_calibration+1)*nominal_level)` and its selected ordered absolute residual;
- issued symmetric bounds, empirical coverage, mean width and Winkler score at each matching nominal level;
- candidate choice and final epoch choice from the saved inner scores/histories.

Verify all three models used the same target rows and reference targets. Preserve unsupported rank statuses; do not substitute interpolated/clipped ranks. Check saved fitted artifacts and preprocessing can be reloaded to reproduce predictions without fitting, using a declared numerical tolerance and separately measured verification cost.

Check resource accounting against actual phase records. Report tuning, final fitting, calibration, inference, throughput, process CPU, baseline/peak/incremental memory and complete command wall time. Separate tiny-test, preparation, I/O, validation and resume costs. Do not sum overlapping phases or claim a GPU benefit in a CPU run.

Run completed-unit resume with all fitting routes forbidden. Require zero new fits, unchanged scientific payloads, metrics and completed unit files. Source/config/data mismatch and checkpoint corruption must still fail.

Write `PLEIA_ENERGY_MATCHED_H1_REPORT.md` containing:
- the three model rows for point errors, both levels' coverage/MPIW/Winkler, and measured cost;
- exact model/interval construction and data dates/support;
- the selected candidates/epochs and actual fit counts;
- data-quality limitations and any negative predictions/bounds as diagnostics, with no post-hoc clipping;
- a restrained interpretation: this is one target/horizon/fold/model-seed experiment, not a completed multi-horizon LSTM superiority test. Narrower intervals alone are not a benefit if coverage is worse.

Publish readable comparison CSVs, per-row recalculation inputs, model/calibration artifacts, tuning histories, resource tables, validation and resume records. An optional compact plot must be generated from those real CSVs, not AI imagery.

Update CURRENT_EVIDENCE, recovery/panel status and the completion ledger. After successful completion, the primary matched comparison has 4/195 paired units completed, 12/585 point cells and 24/1170 interval cells; 191 paired units remain. These totals exclude separate seasonal and broader interval-method obligations. Keep the original experiment matrix/proposal immutable and create a versioned completion overlay instead of rewriting its historical status.

Publish on the new review branch and verify its remote SHA and key artifact contents; leave main and source review branches unchanged. End with actual results, validation/exit status, costs, publication links/SHA and a revised measured planning estimate for the remaining queue. The queue's next RICO/BDG2 units remain unlaunched.

If a concrete integrity/resource blocker persists, report its exact evidence and preserved checkpoints. Otherwise complete the implementation, this real unit, validation and publication in the authorized task. Do not stop at another plan or ask whether to begin fitting.
