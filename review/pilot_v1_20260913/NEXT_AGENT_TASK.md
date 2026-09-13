# Next local Astra task: publish current code and resolve pilot follow-ups

Work in the existing local ConfoSense repository. The completed PLEIA pilot is pilot_v1_20260913. Continue from the actual latest local state; do not check out an old SHA from conversation history.

The owner explicitly approved public publication of the pilot evidence package on 13 September 2026 and requested future relevant code and review evidence on separate branches. This supersedes the earlier no-push instruction for this bounded task; do not ask again for that same authorization. Do not push to main, merge into main, force-push, reset history, or overwrite historical results.

## 1. Publish the current implementation and evidence

Inspect git status, branches, remotes, local instructions and current recovery/pilot reports. Preserve all existing work and verified backups. Inspect the pending commit range and explicit file list for credentials, raw/restricted datasets, virtual environments and bulky run artifacts before pushing.

Fetch origin and create a new branch review/current-dissertation-20260913 from the latest local dissertation work. If it already exists, inspect its ancestry and continue safely or use a unique suffix. Keep main unchanged.

The chat reviewer published the approved evidence package on origin/review/pilot-evidence-20260913 under review/pilot_v1_20260913/. This contains the four CSVs, completed pilot report and review. That branch was created from the older published repair commit 041714a; its base source tree is NOT the current evaluated implementation. Read its review files without replacing your current local code with that older tree.

Publish the current code, required dependency specifications, focused tests, pilot configuration, frozen protocol, validation summaries, updated recovery/panel/repair reports and a small evidence index. Include the nine listed pilot CSVs and readable figure/source index. Preserve the existing canonical paths, rather than making multiple inconsistent copies.

Include enough permitted evidence to reproduce the pilot metrics: saved point/calibration predictions, interval bounds, membership/boundary records, checkpoint manifests and training histories when reasonably sized and redistributable. Keep raw source datasets, environment folders and oversized model weights outside normal Git. If necessary, publish derived diagnostic summaries and a manifest explicitly identifying what remains local; do not claim that hashes alone let a reviewer recompute the metrics. Do not install a new sharing service for this task.

Create review/CURRENT_EVIDENCE.md linking the exact source commit used for the pilot, protocol hash, run ID, current implementation commit and canonical relative paths. Clearly distinguish evaluated code from subsequent reporting/diagnostic changes. Add a small manifest with paths, byte sizes and SHA-256 hashes. Use exact path allowlists when staging. Push the named review branch and verify its remote head. Return its GitHub URL and SHA so future sessions can fetch it directly; do not ask the user to upload CSVs again.

If authentication blocks the push, finish the local preparation and report the actual blocker. Do not claim the branch is published.

## 2. Investigate the specific pilot findings without retuning its test set

The independent aggregate review reconciled the four provided CSVs, candidate selection, epoch selection, interval ranks/widths, throughput and resource totals. It did not inspect the current implementation or raw predictions.

Confirmed findings:
- Persistence has the lowest MAE/RMSE at 10, 30 and 60 minutes.
- LSTM takes 864.3173 seconds across the recorded phases versus XGBoost's 18.0087 seconds (47.99 times), on CPU. These totals exclude preparation, I/O and abandoned partial work.
- LSTM has wider intervals and worse Winkler scores than both comparators in every pilot interval cell. At 60 minutes its 95% interval covers 80.73%.
- The selected LSTM candidate's inner-fold MAE changes from 0.5010 to 1.7418 at 10 minutes, 0.7451 to 1.9241 at 30 minutes, and 1.1698 to 2.2556 at 60 minutes.
- The preparation record reports a 2.2857 GiB process peak and just 794,624 bytes (0.758 MiB) minimum available system RAM during protocol freezing. Later stages have more headroom. The reason for the historical interruption is unknown.
- Persistence has zero tuning work in comparison.csv; its raw resource rows retain approximately 0.0005–0.0006 seconds of empty-branch overhead. The report documents this. Preserve that distinction; it is not a model-performance defect.

Use saved artifacts first. Compute persistence MAE on the same two inner validation supports and export a matched table alongside both learned candidates. Reuse predictions/histories; if the inner learned predictions were never saved, report that and only reproduce the unchanged inner fits needed for diagnosis, within the existing two-candidate budgets.

Audit origin/target/sequence alignment, availability of y_t, feature schemas, sequence ordering, model and target scaling/inverse transforms, final refit epoch handling, and train-only normalization. Summarize fit-versus-validation target ranges and residual bias on these development folds. Distinguish a demonstrated implementation error from plausible temporal distribution change or limited model capacity. The CSVs alone do not identify a root cause.

Inspect the memory sampler and the protocol-freeze path for temporary full tensors/copies. Verify the byte units and Windows memory-API fields. A preparation-only measurement may be repeated after checking available RAM; do not retrain models for a memory check. Reduce demonstrably unnecessary allocations without changing rows, timestamps, features or frozen protocol identity.

Write PILOT_DIAGNOSTICS.md with evidence paths, confirmed findings, unresolved hypotheses and exact recommended next actions. Implement only confirmed correctness or preparation-memory fixes, with focused regression checks. Preserve the completed pilot artifacts. If a fix affects evaluated predictions or data membership, identify affected cells and version the replacement experiment before any rerun; do not silently overwrite or continue calling the original results corrected.

Do not add candidates, tune calibration radii on test coverage, change horizons/cohorts, switch to GPU, or discard LSTM solely to improve the displayed score. Any later model-development experiment must be explicitly distinguished from this completed pilot and its previously inspected evaluation data.

## 3. Prepare the next operational evaluation task

Using the current executable protocol and recovery/panel matrix, produce one concrete OPERATIONAL_EVALUATION_PLAN.md. The pilot's two inner folds tune point models; they do not resolve the separate nested alert-selection protocol.

Resolve the exact two-inner-fold aggregation, event-family weighting, physical-time alert rules, feasibility confidence bounds and insufficient-support behavior, deterministic selection/ties and no-feasible-configuration behavior. Define event incidence and severity by group and physical exposure, onset-aware one-to-one matching, event recall, background alerts per asset-day and detection-delay estimands. Mark precision/F-beta based on synthetic labels appropriately.

Specify paired baselines and ablations on the same event schedules, recalibration feeding the actual alert stage, and comparable workload-budget comparisons. Do not treat a nonsignificant recall difference as equivalence. Keep grouped resampling, seeds, repeated folds, censored recovery and the previously observed outer data explicit. Preserve existing declared values where scientifically valid. Explain any proposed amendment and its reason; do not invent a budget from the desired test result.

Map each decision to the implementation function, relevant existing tests, missing regression checks and the smallest integration smoke needed. Identify the remaining literature/report explanations from the panel matrix without expanding this task into rewriting the slide deck.

Commit and push these diagnostics and the plan to the same review/current-dissertation-20260913 branch (or the uniquely named replacement). Re-run only checks needed for the changes. No full multi-dataset fit or robustness study is authorized in this task.

At completion return: review branch URL and exact head; paths to CURRENT_EVIDENCE.md, PILOT_DIAGNOSTICS.md and OPERATIONAL_EVALUATION_PLAN.md; confirmed defects versus hypotheses; any changed-code effect on existing results; commands actually run and outcomes; one concrete next implementation/run step. A reporting validator must not declare scientific readiness or successful coverage merely because files exist.
