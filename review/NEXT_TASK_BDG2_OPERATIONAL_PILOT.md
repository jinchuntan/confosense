# Next local Astra task: bounded BDG2 operational pilot

Reviewed source: review/amendment004-20260913 at 2243c167804690ad1ec9b8aebc369e5596d392aa. The branch, report, proposal, smoke records and runner are published. This file is the proposed next instruction for the user to give the local Astra session. It is not evidence that the pilot has already run.

## Purpose and scope

Execute the single proposed BDG2 operational pilot, then validate and publish its actual results. Keep it a reduced engineering pilot, separate from the full study.

Use BDG2, outer fold 2, model seed 42, all ten retained buildings, one-hour horizon and catalogue seeds 42–46. Match review/amendment004_20260913/next_bounded_proposal.json exactly: nine 95% candidates; shared uncalibrated/CQR quantile fits; static and rolling every 12 origins with 200 scores; immediate, 3-of-3 over 180 minutes and 4-of-6 over 360 minutes.

The expected inner surface has 18 candidate/fold rows and 90 candidate/fold/catalogue pairs. The proposed learned fitting work is two inner CQR objects and one final CQR object, each containing three quantile estimators. Persistence is a fixed reference with no learned fit. Derive expected outer rows/streams from the frozen selected/comparator requests; do not hardcode a favourable selection outcome.

This task authorizes that one pilot when the user gives these instructions to the coding session. It does not authorize additional folds, seeds, datasets, an expanded candidate grid, architecture tuning, the full robustness study or a full-study launch.

## Before the run

Read local repository instructions, AMENDMENT004_IMPLEMENTATION_REPORT.md, review/CURRENT_EVIDENCE.md, protocols/amendment004/AMENDMENT004.md and the frozen proposal/configuration. Continue from the current amendment implementation or a verified newer descendant. This handoff lives on an older evidence-branch source base; do not check out its source over the current implementation.

Inspect git status and preserve newer work, historical artifacts, backups and the completed forecasting pilot. Relevant code/results may be pushed to a non-main review branch. Do not push or merge into main, reset history, force-push or overwrite existing completed outputs.

Use the existing C:/cfs_venv/Scripts/python.exe environment. Confirm the generated candidate identities/settings, actual memberships and primary horizon match the proposal and published preflight. Use the existing 3 GiB available-RAM launch guard and one numerical thread. Do not run real fits in parallel. Record free disk capacity and phase/peak memory. The 1–3 hour figure is a planning allowance, not measured runtime or a promise.

Freeze the actual execution identity, resolved configuration, candidate list, seed ledger, source/config/data/membership hashes and expected output keys before fitting. If the output directory already exists, inspect its state and use the existing identity-checked resume only when it matches. Otherwise use a newly identified directory; never delete the old evidence to make a fresh run look clean.

## Execute the proposed command

From smart_building_conformal/, run through the existing durable command logger with captured stdout/stderr, start/end times, exit status and process identity:

C:/cfs_venv/Scripts/python.exe -B -m src.operational004 --dataset bdg2 --outer-fold 2 --model-seed 42 --config configs/operational_amendment004.json --out outputs/amendment004/bdg2_operational_pilot_f2_s42_v1

Set OMP_NUM_THREADS, OPENBLAS_NUM_THREADS, MKL_NUM_THREADS and NUMEXPR_NUM_THREADS to 1. Track the actual process and report meaningful progress. Do not describe a process as running merely because an old session said it was. Do not start a duplicate run while the original is alive.

Retain no_feasible_configuration if screening fails. Keep its fixed diagnostic/comparator results separate from a feasible selected operational result. Never widen the grid, raise event incidence, weaken support rules, change alert thresholds or retune from the outer output to obtain a favourable result.

If a real software failure occurs, preserve the failing logs/artifacts, isolate the cause and add the necessary focused regression. Record any source change and affected outputs, then use a new execution identity when required. Do not overwrite the failed attempt. Completed-unit resume is supported; do not claim recovery of partially fitted stages unless such checkpoints actually exist.

## Validate the evidence and report the measurements

Require the recorded command to finish and confirm its actual exit status. Save the existing output validator's results, but do not equate stream hashes with verification of every reported metric.

The current validate_unit checks candidate/fold completeness, catalogue/hash completeness, issued/consumed equality, persisted stream hashes and abstention consistency. Add a focused read-only result-recomputation step using saved streams, event records and frozen definitions. Recompute clean episode onsets/exposure by group, corrupted event matching, per-stratum counts/recall, the declared custom synthetic utility and ordinary precision. Reconcile these with the recorded surface. Recalculate recorded confidence bounds/selection from the saved contribution tables and paired resampling draws. Treat differences as errors to investigate, not values to silently replace.

Where saved clean truth and issued bounds allow, report clean empirical coverage, MPIW and Winkler score at 95%, with units and denominators. Keep these separate from coverage against corrupted readings or hidden clean truth. Do not imply that an alarm is a forecast made before its target became observable.

Save a concise comparison CSV and BDG2_OPERATIONAL_PILOT_REPORT.md containing:
- Both inner-fold results and rejection reasons for all nine candidates.
- Selected configuration or explicit abstention.
- Outer results for the full selection when present, controlled components, independent operating points and fixed CQR/persistence diagnostics, with unambiguous status labels.
- Event recall by family/severity, clean background episodes per asset-day, detected-event delay with detection denominators, missed-event fraction and availability/numerical attribution.
- Available uncertainty bounds with their original building-level resampling support, plus unavailable/degenerate reasons. One model seed and one fold do not establish the full study's uncertainty or generality.
- Actual fit-object/sub-estimator counts, phase timings, end-to-end duration, memory and artifact sizes.
- Outer workload violations without post-test threshold adjustment.

Validate saved-output completeness and hashes, then confirm a completed-unit resume performs zero new fits and preserves unit bytes. Use focused tests for any validation/reporting code changes; do not repeat unchanged expensive fits just to regenerate summaries.

## Publish and define the next decision

Commit and push the relevant implementation, run identity, recomputable evidence, small tables, logs, report and updated review/CURRENT_EVIDENCE.md to a non-main review branch. Publish derived prediction/event evidence and manifests at their canonical paths. Keep raw source datasets, secrets, environments and external backups out of the push. Verify the remote head and return direct evidence links so the user need not upload CSVs.

Return the branch URL and commit SHA, actual exit/validation/resume status, selection outcome, a compact numerical result table, measured resources and the single next justified step.

Preserve the distinction between software readiness, structural support and measured operational performance. Only BDG2 met the current 21-stratum support requirement in every inner bank. The absence of enough events for PLEIA/PLeia-energy/RICO is not proof that their forecasters fail and does not justify silently removing them from the dissertation. Their point/interval comparisons remain separate; the four-task operational scope still requires a documented design decision.

This pilot is a useful next real-data measurement, not a full-study result. Keep full-study/dissertation readiness false and do not launch the next experiment automatically.
