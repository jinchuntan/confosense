# Next task: run the first RICO and BDG2 matched-model units

Based on `review/matched-energy-h1-20260913` at `b26ee5b6a2cfb322b392e017e627bf3c96339c78`.

## Goal and authorization

When the user supplies this handoff, execute the next **two** published matched-forecasting units sequentially: RICO h5/f2/s42, then BDG2 h1/f2/s42. Complete their validation, zero-fit resumes, reports, cost update and review-branch publication. This is a two-unit batch that measures the remaining dataset paths before a larger batch; it is not authorization for the remaining 191-unit queue.

Each unit includes persistence, XGBoost and Attention-LSTM with the frozen two-candidate learned-model grids and own-model 90%/95% split-conformal intervals. Total authorized real work: **16 tuning + 4 final learned fits**, yielding **6 point and 12 interval cells** across the two units. Any necessary tiny fixture fits are separate and must be counted separately; do not repeat completed real experiments.

Proceed to BDG2 when RICO has completed and passed its integrity/metric checks and BDG2 meets the current resource policy. This continuation depends on correctness and resources, not on which model wins or whether nominal coverage is reached. Do not stop after RICO just to request fitting permission again. An unresolved shared-code defect or concrete resource blocker is a reason to pause and report evidence.

## Preserve and reuse the completed work

Continue from the latest local descendant of b26ee5b, preserving later local work. Read the handoff using git show; do not check out or merge the old implementation beneath `review/pilot-evidence-20260913`.

Use `review/matched-rico-bdg2-20260914` or an unused clearly named review branch. Preserve main, previous review heads, original protocols, completed temperature/energy/BDG2-operational results, all abstentions and backups. Never force push or update main.

Read:
- `PLEIA_ENERGY_MATCHED_H1_REPORT.md` and its evidence index;
- `REMAINING_STUDY_EXECUTION_PLAN.md` and matched/RICO-membership sections of `AMENDMENT005_PROPOSAL.md`;
- `outputs/matched_forecasting005/energy_h1_report_v1/remaining_queue_updated.csv`;
- `outputs/amendment005/support_design_v1/experiment_matrix.csv`, `forecast_roles.csv` and the RICO h5 / BDG2 h1 membership files;
- `src/matched_forecasting005.py`, `matched_data005.py`, `matched_models005.py` and `matched_validation005.py`.

The reusable runner already exists and all 39 role banks were checked. Do not restart the general support audit or rebuild a second matched runner. The current branch includes the identifier-export repair. Use that current source for fresh experiments and retain the earlier energy source identity for its historical evidence.

The energy result does not select the RICO/BDG2 models or alter their grids. XGBoost and LSTM's near-identical energy MAE, different interval widths/Winkler and approximately 71x model-phase cost are descriptive findings, not an instruction to remove LSTM.

## Freeze both units before either real fit

Create a new explicit authorization file containing exactly:
`[["rico",5,2,42],["bdg2",1,2,42]]`.

Record this later authorization separately from the historical energy-only authorization and the older no-fitting proposal. Bind the new handoff/publication identity and actual entry commit to the new execution manifest. The runner still contains the original design-parent and instruction constants: retain their legitimate historical meaning and record the current authorizing instruction separately, or make the minimal provenance-only generalization needed. Do not present the energy-only instruction as the authorization for these new fits.

Freeze fresh per-unit protocols and a joint two-unit manifest before fitting. Verify actual source/config/package/data/schema/role hashes against the published matrix and memberships, including all tuning roles. Do not update a stored expected hash to hide a mismatch.

| Unit | Physical forecast | Final fit | Calibration | Test | Original grouping |
|---|---|---:|---:|---:|---|
| RICO h5/f2/s42 | 5 minutes | 12,932 | 4,452 | 8,692 | 61 fit runs, 21 calibration runs, 41 test runs |
| BDG2 h1/f2/s42 | 1 hour | 51,664 | 17,370 | 34,640 | Same ten retained buildings across chronological roles |

These are **matched flat/24-step-sequence support counts**, not the different operational/challenge counts. Confirm them against the actual matrix; save exact dates, IDs, schemas and frequency. RICO's test block is the 41-run earliest evaluation batch, not the old single-run outer test. Historical training/calibration use and represented acquisition phases must remain disclosed.

Use the existing frozen settings:
- persistence from the actual last-observation feature;
- XGBoost 400 trees, depth3 or5, remaining recorded parameters unchanged;
- Attention-LSTM hidden64, dropout0.2, batch256, learning rate0.001 or0.0005, maximum30 epochs/patience5;
- sequence length24, original causal features, inner-training-only normalization;
- two purged inner validation folds, equal-inner-MAE candidate selection, existing exact candidate tie order and LSTM early-improvement convention;
- final LSTM epochs from the ceiling of the selected candidate's mean best inner epoch;
- final calibration reserved; each model's own absolute residuals, exact finite-sample ranks, symmetric 90/95% intervals;
- no clipping, recalibration, injected faults, rule selection or conditional challenge in these units.

Preserve whole RICO runs at every boundary and prevent sequences from crossing runs. BDG2 sequences/history must stay within buildings. Do not call differing flat features and sequence tensors identical representations. Calibration/test outcomes may not change hyperparameters, epochs, targets, cohort, normalization or masks.

## Readiness and execution

Use the existing freeze/readiness/run/validate/resume actions. Resolve their actual protocol, authorization, readiness and receipt arguments; do not assume a bare queue argv replaces pre-fit freezing.

Example paths:
- `protocols/matched_forecasting005/rico_h5_f2_s42_v1/`
- `protocols/matched_forecasting005/bdg2_h1_f2_s42_v1/`
- `outputs/matched_forecasting005/rico_h5_f2_s42_v1/`
- `outputs/matched_forecasting005/bdg2_h1_f2_s42_v1/`

Use unused versions if those paths already contain work. Never overwrite an old directory or duplicate an active process.

Pass no-fit fresh-support/readiness checks for both datasets and focused checks covering any actual code changes. Existing group-aware role and identifier tests can be reused. Additional tiny integration fits are justified only by a concrete unverified path; do not rerun the previous 20 synthetic fits automatically. Commit the evaluated implementation and protocol evidence before real fits.

Preserve the current documented resource policy, including the later user instruction making the 3 GiB launch RAM reference **nonblocking**. Log actual available RAM and whether that reference is met; do not silently reinstate the old blocking rule. Retain the existing epoch floor and disk checks unless the user has separately changed them. Use lazy batches, one numerical/Torch thread, `n_jobs=1`, the existing compatible CPU environment and sequential real fitting. Respond to an actual allocation failure or unsafe resource state with preserved evidence, not by reducing the scientific cohort or model.

The current model-phase planning scenarios are approximately 49–557 seconds for RICO and 195–2,224 seconds for BDG2. They exclude preparation, I/O and validation and are not time limits. Replace them with measured task-specific costs. Do not use operational HistGradientBoosting/CQR timings as XGBoost/LSTM estimates.

Persist exact commands, PIDs, start/end/exit, stdout/stderr, code/config/data identities, actual fit journal and resource phases. Save each completed model atomically with fitted artifact, normalization state, calibration/test predictions, inner predictions/history and COMPLETE hashes. Both levels share the same trained model. Explicit partial-run resume may reuse complete model units under the same identity; do not promise mid-fit recovery.

If a genuine defect appears, preserve the failed attempt and determine its scope. Fix and verify it, using a fresh identity/version if required. Retain completed valid units; do not refit them merely because the result is disappointing or a reporting helper changed.

## Validation required for each unit

Use the independent saved-stream validator and saved-model checks already implemented, with actual generic unit identities. Require:
- actual run exit0 and exactly 3 point/6 interval cells;
- eight real tuning/two real final fits, persistence zero learned fits;
- identical final fitting/calibration/test target IDs and reference targets across models;
- independent MAE/RMSE, own residuals/order-statistic ranks, issued bounds, coverage/MPIW/Winkler and selection/epoch reconstruction;
- correct RICO phase/run IDs and BDG2 building IDs through CSV round trips;
- six saved-model checks, calibration/test for each model, at the already declared tolerances;
- completed-unit resume with all fitting routes forbidden, zero new fits and all original run files unchanged;
- preservation of existing provenance, source/config/data mismatch rejection and corruption detection.

Do not certify coverage just because validation passes. Report negative predictions/lower bounds without post-hoc clipping. Report per-run/phase RICO and per-building BDG2 point/interval summaries alongside pooled values; pooled sample-weighted results must not be relabelled equal-run/equal-building averages.

This remains one fold and one model seed for each new task. Provide descriptive paired errors/interval/cost differences; do not invent full five-seed or multi-horizon significance. RICO phase imbalance and earlier data reuse remain limitations. BDG2 is within known buildings, not unseen-building generalization.

## Reports, ledger and next batch plan

Produce `RICO_BDG2_MATCHED_FIRST_UNITS_REPORT.md` and readable per-dataset comparison tables covering:
- MAE/RMSE;
- coverage, MPIW and Winkler at both 90/95%;
- selected hyperparameters/epochs and estimator ownership;
- tuning/final fit/calibration/inference times and throughput;
- preparation, serialization/checkpoint, validation/resume, CPU and memory measured separately;
- successful and failed command attempts with actual exits;
- task/group-specific limitations and verification evidence.

Summarize the available matched evidence across all four settings using the preserved temperature and energy results plus these new units. Keep different targets/units/horizons/folds clearly labelled; do not average raw Celsius and kWh errors into one ranking or imply that the uneven pilot set is a completed four-task study. Use exact source/run hashes for reused evidence and no historical refits.

After both units complete, create a versioned completion overlay with **6/195 paired units, 18/585 point cells and 36/1,170 interval cells completed; 189 paired units remain**. Preserve the original proposal/matrix and earlier overlays. Seasonal, broader interval methods, conditional challenge and robustness are still separate obligations.

Now that each setting has measured matched-model execution, give a **concrete larger-batch proposal** from the unchanged remaining queue: enumerate its unit keys, fit/metric counts, checkpoint strategy, measured timing/RAM/disk assumptions and acceptable stop conditions. Choose the batch for coverage and resource feasibility, not favorable previous scores. Separate implementation blockers from mere pending executions. Do not stop at another generic “one unit next” recommendation if a larger fixed batch is supportable. Do not launch that additional batch in this task.

Publish relevant current code, protocols, actual fitted artifacts, per-row recalculation inputs, summaries, logs and validation evidence on the new review branch. Update CURRENT_EVIDENCE and recovery/panel status, verify remote SHA and key content, preserve main and historical branches, and provide the artifact URLs. The user should not need to upload CSVs manually.

Complete both authorized units and their reporting/publication without requesting a second fitting authorization. If a concrete blocker prevents completion, report the exact failed gate and saved partial results rather than claiming both were completed.
