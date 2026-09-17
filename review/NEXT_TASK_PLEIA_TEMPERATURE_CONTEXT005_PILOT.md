# Next task: PLEIA-temperature conditional-context pilot

## Entry point and authorization

Continue from `review/pleia-energy-context005-multiseed-20260915`, final delivery commit `80df3579dfe68ccf2c0d406c21c0fec967ff2b41`. Preserve valid local descendants and existing untracked historical files. Fetch this instruction document only from its instruction branch; do not merge or check out that branch's older experiment tree.

This is a handoff for the user's next local Codex execution. When accompanied by the user's launch authorization, it authorizes bounded activation/coordinator work, necessary synthetic checks, and exactly ONE real conditional-context C pilot: PLEIA temperature (`dataset=pleia`), outer fold 2, horizon 1 (10 minutes), model seed 42. It also authorizes independent validation, completed resume, reporting, backup and publication. It does not itself launch a process.

The previous batch's `REMAINING_WORK.md` proposed readiness before separate real-fit authorization. The accompanying user launch prompt supplies that authorization conditionally on successful no-fitting freeze/readiness. Complete those gates first, then proceed without another approval. An unresolved scientific discrepancy is a blocker; a readiness result is not permission to change the study design.

Recommended execution model: GPT-5.6 Terra, High reasoning. This task reuses an implemented scientific engine and a frozen design. New scientific design choices remain outside scope.

## Why this is next

The five-seed PLEIA-energy C study is complete and delivered. Its accepted outputs and delivery receipt are inputs to this task, not work to repeat. The next pilot tests the same causal replay and alert contract on temperature, where existing forecasting/interval evidence showed substantial undercoverage.

All five matched interval families are already implemented. This four-control C pilot is a separate endpoint; do not rebuild the matched interval engine or confuse its scope with the 1,950-cell queue.

Read these current files selectively:
- `review/pleia_energy_context005_multiseed_20260915/DELIVERY_READBACK_RECEIPT.json`, `REMAINING_WORK.md`, and the completed report.
- `review/context_replay005_implementation_20260914/SUPPORT_GATE_STATUS.md`.
- `src/context005_spec.py`, `context005_data.py`, `context005_features.py`, `context005_owner.py`, `context005_metrics.py`, `context005_validate.py`, and `conditional_context005.py` under `smart_building_conformal`.
- The existing generic process-adoption engine and the latest multiseed coordinator, analysis, packaging and delivery repairs. Energy-specific paths, seed loops, recovery receipts and aggregation assumptions must not leak into this temperature unit.

## Frozen scientific scope

| Item | Required value |
| --- | --- |
| Dataset | PLEIA temperature, internal identifier `pleia` |
| Endpoint | `C_effective_fault_conditional_context`; selection `none` |
| Outer fold / model seed | 2 / 42 |
| Horizon / cadence | 1 / 10 minutes |
| Confidence | 95% |
| Published role support | 14,855 final-fit rows; 4,954 calibration rows; 9,907 outer rows |
| Original outer group | One published single-series group; preserve literal identifiers |
| Contexts / scheduled fault slots | 68 / 2,856 (42 per context) |
| Fault design | Seven families, three severities, two declared slots; fault-slot seeds 42/43 remain fixed |
| Full clean exposure | All 9,907 outer rows, including 115 untiled tail rows; 68.79861111111111 asset-days |
| Controls | Raw quantiles, static CQR, rolling CQR, static persistence |
| Rules | Immediate; 30-minute 3-of-3; 60-minute 4-of-6; 180-minute 3-of-18; 360-minute 4-of-36 |
| Channels | Numerical-only, availability-only, combined |
| Rolling CQR | Existing declared every=24, window=250, minimum=50 policy |
| Energy sensitivity | Inactive; no proposal adoption or retrospective cleaning |

Reconstruct these identities from the published PLEIA temperature cache, roles, contexts and schedules. Do not copy energy context hashes, realized-stream counts, features, outcomes, null flags, or fitted owners. Identical row counts do not establish interchangeable data.

Record exact feature columns, source/package hashes, role membership hashes, chronology, context/schedule identities, null/effective classifications and full clean exposure before fitting. The existing single-series identity crosswalk is narrowly scoped; never globally normalize a real group named `None`, `nan`, or an empty string.

The expected operation budget is one NEW logical CQR owner containing three HistGradientBoosting quantile-estimator fits; one logical conformalization represented by the existing two nested profiler calls; one persistence-radius calculation. Raw/static/rolling controls share that owner's fitted estimators. There are no XGBoost, Attention-LSTM, EnbPI, DSCP, tuning, or matched-forecast fits in this pilot. Record separately any tiny synthetic fits.

Preserve original causal observation delays, group/context state isolation, native CQR conventions, source features, model parameters, support minima, tolerances and alert/event definitions. Corrupted observations must enter causal features and actual serialized-model predictions. Counterfactual clean truth is only for evaluation. Keep aliases and null realizations in the accounting. Restricted time to detection retains the declared 110-minute restriction and misses.

## Execution and recovery

1. Inspect local branch/HEAD, changes, processes and receipts. Preserve the completed energy study and all previous review heads. Create a new branch such as `review/pleia-temperature-context005-pilot-20260917` from the valid current experiment descendant. Main must remain `06fe967be2be8d7898812c0c2d6e464d4e942351`.
2. Create temperature-specific manifest, protocol, output, coordinator, review and backup paths. A suitable unit key is `pleia_f2_s42_C_v1`; if a path already exists, inspect its identity and accepted progress rather than overwrite it or choose a fresh path to duplicate work.
3. Reuse the tested replay engine and durable process-adoption/locking code. Keep implementation changes to the necessary adapter/coordinator/reporting layer. Before worker launch, check helper imports and module isolation, dataset/seed scope, receipt paths and command construction. The prior `common.py`/CSV shadowing defects must not recur. Do not import an energy script with top-level execution side effects.
4. Run meaningful bounded tests for any changed contracts and existing relevant causality/ownership/resume checks. Do not rerun the full repository suite without a concrete regression risk. Failed tests remain recorded; never adjust tolerances or observations to obtain a pass.
5. Freeze and run no-fitting readiness. Independently reconcile published memberships, 68 contexts, 2,856 slots, source/cache identities and operation budget. Commit the pre-fit design and evaluated source identity. If a scientific mismatch remains, stop before fitting and report its exact cause. A confirmed serialization/orchestration defect may be narrowly repaired, tested and re-frozen in a new version with the failed attempt preserved.
6. Once readiness passes, run the one authorized pilot, independent reconstruction, and zero-fit completed resume sequentially. Use the recorded Python environment, one CPU worker and the existing single-thread/resource policy. Preserve the 8 GiB disk floor; estimate peak live storage including validation temporaries, raw outputs, archives and backup. The historical 3 GiB launch-RAM reference is nonblocking in the existing protocol; report actual memory rather than silently invent a new resource policy.
7. Reconcile exact process identity (PID plus creation time, command and process family) before launch/adoption. A surviving worker must be adopted, not duplicated. An interrupted run may reuse hash-valid committed stages and fitted owner/calibration. Do not blindly refit an incomplete owner or classify an unexplained nonzero exit as success. Preserve failed attempts and log any narrowly justified recovery.
8. Use a durable logger and externally saved restart instructions so computation does not depend on repeated chat polling. Publish concise milestone progress. Diagnose a slow stage using worker CPU/I/O/checkpoints, not elapsed time alone. Do not alter system-wide power settings or terminate unrelated processes.

Existing CLI actions are `freeze`, `readiness`, `run`, `validate`, `resume` in `src.conditional_context005`. Generate and persist exact local commands from the temperature manifest. `--resume-incomplete` is only for the verified interrupted unit; it is not a shortcut past failed checks.

## Acceptance and reporting

Independently validate actual serialized predictions, reconstructed causal features, emitted bounds, delayed releases/updates, emitted-versus-consumed stream identities, episode matching, full clean workload and aggregate arithmetic. Preserve the frozen numerical tolerances and report the maximum observed difference. Warnings are assessed against saved artifacts; do not suppress them or treat informational text alone as failure.

Expected accounting is 68 contexts, 2,856 requested slots and 68 clean context identities, with 171,360 event/control/rule/channel records if every scheduled slot is represented by the unchanged schema. Retain null/ineligible flags. Produce all 60 control/rule/channel summary rows; report actual support and unavailable metrics rather than assume all strata are effective. Independently derive expected check counts and unique realized-stream/alias counts from this temperature design, not energy's successful numbers.

Completed resume must record zero learned fits, zero calibrator fits, zero replay updates, and unchanged scientific output hashes. Reuse that successful receipt for delivery; do not repeat expensive completed validations/resumes merely to refresh publication timestamps.

Deliver directly accessible CSVs for control/rule/channel summaries, stratum support, full-stream workload, interval diagnostics, operation counts, timings/CPU/memory, and validation. Retain original-context contributions for later seed aggregation. Provide a concise report and figures for detection versus workload and restricted delay, with temperature units where applicable.

This is one model seed and one fold. The declared five-seed inference is not yet available for this temperature setting: preserve unavailable conditions and do not recycle energy bounds or treat slots/seeds as additional independent original contexts. Do not infer deployment prevalence, precision, F1, or operational feasibility from the conditional challenge. Any comparison with the energy study must retain its different target units and support; no pooled cross-dataset error average.

Forecasting remains 70/195, matched interval methods 250/1950, and unique seasonal computations 9/27. This C pilot adds separately identified conditional-context evidence; it does not fill those matrix cells. Full-study readiness remains false. List the next bounded proposal without launching it.

## Cost planning

Use measured timings, not model-generation speed, to plan the job. The five accepted energy units had run times approximately 52.5–103.2 minutes, validation 89.0–153.7 minutes, and completed resume 6.1–53.4 minutes. These are analogues, not a temperature guarantee; effective faults and alias counts can differ. A provisional end-to-end allowance is roughly 4–8 hours including preparation/reporting/packaging/upload, subject to local I/O, resource and network conditions. Re-estimate after no-fit inspection; record actual costs and failed-attempt costs separately.

The four new energy seeds produced about 2.094 GiB of packaged raw evidence across 40 parts. Do not assume temperature has exactly one quarter that size: inspect its scheduled realizations and measure the new unit. Preserve enough disk for the raw run, validation, archive and backup simultaneously. Keep the scientific checks intact.

## Finish publication in this same task

Reuse the corrected lossless packaging logic, including explicit CSV-module handling and archived COMPLETE.json verification. Preserve immutable scientific files and validated parts across retries. Publish compact reports/CSVs directly plus lossless raw archive parts with manifests. Hash and reopen every archive member locally once under the existing package contract.

Use an explicit staging allowlist. Commit and push only to the new review branch. Do not republish or repackage completed energy data, broaden ignore rules, or delete historical/untracked files.

Verify the new branch ref and all newly indexed remote blob identities. Perform actual GitHub raw-download SHA-256 checks for representative new artifacts, including a raw archive, final summary CSV and independent validation record. Distinguish API/blob identity checks from actual downloaded-byte checks. A local `git show origin/...` is not an independent GitHub download.

Write a settled delivery receipt describing exactly what was checked, commit and publish it, then confirm that final branch SHA. Separate primary-results and final-delivery SHAs. The receipt can refer to the primary commit; it need not embed its own unknowable future commit hash. Stop routine verification once these gates pass.

Create and verify the external backup of primary evidence and the final delivery records. Update CURRENT_EVIDENCE.md, the report, evidence index and concise remaining-work/restart notes. Do not leave successful work at “implementation ready”, “pilot running”, “packaging pending”, or an unpublished receipt when it can proceed.

Final response: branch URL; primary/final SHAs; report/index/CSV links; actual scientific/validation/resume counts and costs; measured findings and limitations; backup confirmation; preservation status; and the next unlaunched bounded proposal. If blocked, state the exact stage, error, live-worker status, accepted checkpoints and restart command. Do not claim completion of a pending phase.
