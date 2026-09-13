# ConfoSense recovery assessment

Assessed 13 September 2026, Asia/Kuala_Lumpur. Scope: state recovery and panel-gap assessment; no implementation, fitting, experiment restart, dependency installation, Git-history change or push.

**Resume position:** the corrected core run is complete and preserved; its statistical reporting was subsequently corrected. The Amendment-003 full extension has no saved results and is not running locally. Attention-LSTM versus XGBoost interval-quality and computational-cost evidence is still missing. Several generated reports overstate completion, and source inspection identifies additional integration discrepancies that need validation before further fitting.

Paths below are relative to `smart_building_conformal/` unless stated otherwise. `F` means `outputs/final_dissertation_v2/`. The companion [panel matrix](PANEL_RESPONSE_MATRIX.md) maps the nine supplied feedback topics to evidence and actions. These files supersede the stale resume instructions for purposes of deciding the next task; existing project files were left unchanged.

## A. Git, environment, and backup/push readiness

### Verified Git state

| Item | Observed value |
|---|---|
| Root | `C:/Users/nigel/OneDrive/Desktop/GitHub/confosense` |
| Branch | `fix/final-dissertation-study` |
| HEAD | `35a5bade8a728edaa3e20753c5fba939426a43cc` |
| Upstream | `origin/fix/final-dissertation-study` |
| Upstream SHA | `041714a18e89173eb47da9c5fb2bb27efd2b93cd` |
| Ahead / behind | **25 / 0** |
| Tracked changes at entry | None |
| Nonignored untracked files at entry | None |
| Remote verification | Read-only `git ls-remote` returned the same upstream SHA; no fetch or pull performed |
| Repository instructions | No `AGENTS.md` or `CLAUDE.md` found in the project; no `AGENTS.md` found in the checked ancestor directories |
| Files added by this assessment | Only repository-root `PROJECT_RECOVERY_STATUS.md` and `PANEL_RESPONSE_MATRIX.md` |

The outgoing commits, oldest to newest, are:

| Commit | Change |
|---|---|
| `4c19ad6` | Executable, strictly validated frozen protocol |
| `69037dd` | Causal, group-safe updated recentred EnbPI |
| `20fbeb8` | Corrected group-safe alert primitives |
| `e8f445b` | Feature schema, weather checks, run-aware subsplit, robust scaling |
| `3d3b8a7` | Final-study validator and audit status |
| `46ef086` | Session-2 correction changelog |
| `bc2f3fd` | Status/resume document |
| `c286623` | Corrected smoke evidence and ignored run directory |
| `ef97905` | Nested corrected study engine |
| `5b75d53` | Amendment 002, four-level ablation |
| `7e7b385` | Engine wiring audit and readiness validator |
| `5877e06` | Shared interval fits |
| `e0f9341` | Exposure allocation and short-run viability floor |
| `d55f836` | Operating-level selection and readiness evidence |
| `9942156` | Per-group coverage and per-event detail; evaluated core code |
| `2850d2e` | Original bootstrap analysis |
| `e54dd3f` | Original corrected-run figure generator |
| `d1a73df` | Original report-suite generator |
| `ca78248` | Core results, CIs, reports, publication marker |
| `93231df` | Deliverable lineage in marker/report |
| `60b1397` | Post-run statistical audit and reporting corrections |
| `cb5927f` | Amendment 003 predeclaration |
| `3249e83` | Robustness extension and extension validator |
| `aa98c87` | Paired extension statistics and ten-figure generator |
| `35a5bad` | Tiered report generator v2 |

All 25 commits date from 31 August–2 September. The latest HEAD is a reporting-generator commit, not evidence that an extension finished.

### Existing environment and resources

Both `C:/cfs_venv/` and `smart_building_conformal/.venv/` exist, use Python **3.11.3**, and have the scientific packages installed. The shell's default `python` is **C:/Python314/python.exe**; it is not the recorded experiment interpreter.

Read-only package inspection of `C:/cfs_venv`: NumPy 2.1.3, pandas 2.2.3, SciPy 1.17.1, scikit-learn 1.5.2, XGBoost 3.2.0, MAPIE 1.4.1, PyTorch 2.13.0+cpu, pytest 9.1.1, PyYAML 6.0.3, tables 3.11.1. The local `.venv` agrees for the checked principal packages. Versions recorded in the core manifest agree for NumPy, pandas, sklearn, MAPIE and XGBoost; the manifest is not a complete environment lock.

Hardware: Intel i7-12700H, **14 cores / 20 logical processors**, approximately **15.73 GiB RAM**, with approximately **1.26 GiB free** at inspection. NVIDIA RTX 3050 Laptop GPU, **4096 MiB VRAM**, approximately 3836 MiB free, driver 546.30. PyTorch reports no CUDA build and `cuda.is_available() == False`; `src/attention_lstm.py:103` explicitly selects CPU. GPU hardware availability therefore does not imply the existing training path uses it.

No local Python/Jupyter/Conda experiment process was present. WSL Ubuntu was stopped. Windows last booted **2026-09-13 03:50:51 +08:00**; an August/September-2 process cannot still be alive across that boot. Remote execution elsewhere was not investigated.

### Backup and outgoing-file review

The scan covered **all 136 outgoing Git blobs**, including earlier versions within the 25 commits, totalling approximately **1.72 MiB uncompressed**. Largest outgoing blob: `F/metrics/run_artifacts/bdg2/outer_per_event.csv`, approximately **0.597 MiB**. None exceeded 10 MiB. Text scans found no private-key blocks, recognizable token formats, credential-bearing URLs, quoted credential assignments, or suspicious credential filenames. This is a bounded pattern scan, not a guarantee that no sensitive material exists. Reports contain local filesystem/user paths; those are provenance, not detected credentials.

Important ignored material actually present:

| Location | Files / size | Preservation priority |
|---|---|---|
| `data/raw/` | 14 files / 530.81 MiB | Essential input archives, RICO acquisitions, BDG2 electricity/metadata/weather |
| `data/interim/` | 33 files / 2028.32 MiB | Preserve processed PLEIA source tables and extraction state; avoids reconstruction ambiguity |
| `data/processed/` | 1 file / 0.68 MiB | Preserve with provenance |
| `F/runs/` | 123 files / 45.18 MiB | Core, engine/smoke runs, extension smoke and empty extension directory |
| `outputs/models/` | 3 ignored binaries / 1.78 MiB | Preliminary XGBoost models; diagnostic provenance |
| `.venv/` | 35142 files / 1237.81 MiB | Reconstructible environment, lower priority than inputs/results |

The core run contributes 29 files / approximately 0.76 MiB within `runs/`; **all 29 have byte-identical tracked copies** in `F/metrics/run_artifacts/`. The ignored extension smoke has no equivalent committed result set. Core point predictions, interval bounds and fitted models were not persisted. Older `outputs/full_study/<dataset>/predictions/` directories are **absent locally for all four datasets**; ignore rules and older comments about prediction dumps do not establish that those files are still available. Preliminary and laptop-verification prediction CSVs do exist.

**Recommended backup, not executed:** preserve all Git refs/history in a verified Git bundle or full repository copy, plus a separate checksummed archive of the inputs, entire output tree and these two recovery reports. Include empty run directories and a package/version inventory for both environments; optionally preserve `C:/cfs_venv/` for machine recovery. Keep an independent copy outside the working OneDrive folder and verify hashes/restore readability. The important ignored data/artifacts alone occupy approximately **2.55 GiB**, excluding environments/caches. A Git push or bundle alone does not cover them; OneDrive location alone does not prove a verified backup.

**Push readiness:** history is ahead cleanly and the bounded outgoing scan found no obvious blocker. Backup has not been made or verified. A future push could preserve history, but would also publish the misleading report text identified below; it should not be described as a publication-ready release. No push was performed.

## B. Verified completed work

### Core execution and artifact integrity

`F/runs/full_20260831_220811/` contains the expected four datasets, **60 outer rows** (4 datasets × 3 folds × 5 seed labels), **240 ablation rows**, selection records, provenance, event allocation, per-event detail and per-group coverage. Each dataset has 15 outer and 60 ablation rows. `engine_summary.json` says `fast: false`; row counts and files independently support completion.

Verified now: all **29 raw hashes**, all **8 derived hashes** in `F/provenance/artifact_manifest.json`, all 29 committed/raw copy pairs, and **181/181** historical `outputs/full_study/` baseline checksums match. This verifies preservation, not scientific correctness. The audit's independent regeneration of the original CIs is historical evidence, not a regeneration performed in this session.

The core manifest identifies evaluated code `99421566e7493a67fba47de21a4b2f231796aa0c`, analysis code `ca782487bdd4334f3699436b16dd98e1d584e558`, and reporting head `93231df...`. Its protocol hash is Amendment 002, `07bf304aceeafc7411b570f21c26a48a8d33515cdd3badad35c4f1a61a932c7b`. Current config/frozen-protocol records identify Amendment 003, `10437ab054199d64c74edb5e62a4011f707fedb96b7d6440d6047f42ea500a8d`. Different hashes here represent documented stages, not evidence of a corrupted core run.

### What the statistical audit resolved

Read together: `F/report/POST_RUN_STATISTICAL_AUDIT.md`, `SCIENTIFIC_VALIDITY_AUDIT.md`, `FEASIBILITY_AUDIT.md`, `CLAIMS_DISPOSITION.md`, `F/audit/post_run_statistical_audit.json`, and the audit CSVs.

| Earlier concern | Verified current disposition | Remaining limitation |
|---|---|---|
| 48/60 `no_feasible_configuration` outcomes | All 60 executed; 12 feasible, 48 explicitly abstained. No evidence that these were execution failures. Feasible counts: PLEIA 10/15, energy 2/15, RICO 0/15, BDG2 0/15. | This is poor feasibility under the frozen policy, not something to hide or fix by relaxing thresholds. |
| RICO described as only three runs | 49,680 observations across 207 runs were loaded. Three distinct outer tests are P5S59/P5S58/P5S57, 221 windows each, approximately 0.46 asset-days total. | Only three independent evaluated runs. The other 204 were not outer tests; they were used in training/calibration pools and must not be called globally untouched data. |
| Inclusion/abstention | `final_cis_corrected.csv` separates feasible-only estimates from all-unit diagnostic estimates. Abstentions retain diagnostic evaluations; they were not replaced with zero workload. | `final_cis.csv` pooled these scopes and is superseded. The literal scope label `all_60_units` means each dataset's 15 rows within the 60-row study. |
| Nominal coverage and widths | `NOMINAL_COVERAGE_AUDIT.csv` compares each row to its own selected nominal. Undercoverage: PLEIA 14/15, energy 15/15, BDG2 15/15; RICO 0/15. | Widths/Winkler remain absent from the core. RICO's 100% coverage does not prove useful calibration; actual width magnitude cannot be asserted without bounds. |
| Independence of CIs | Corrected reporting aggregates seed-labelled replicates before independent-unit inference. PLEIA/energy/RICO CIs are NA; BDG2 coverage and recall use 10 buildings. | BDG2 workload still has only three fold aggregates and **no CI**. Building independence remains a modelling assumption; the correction does not prove it. |
| Paired ablations | All four levels have common fold/seed support. Paired effects are persisted in `PAIRED_ABLATION_EFFECTS.csv`. | Frozen matched-workload/matched-recall endpoints were not evaluated; heterogeneous pooled contrasts remain exploratory. |

Corrected descriptive/diagnostic estimates are retained as evidence of what this implementation produced. For example, BDG2 diagnostic coverage is **0.8908 [0.8649, 0.9147]** and recall **0.3746 [0.3338, 0.4165]**, with no feasible operating units. PLEIA feasible-only outer workload is **1.2355/day**, exceeding the inner selection budget; energy feasible-only outer recall is **0.4559**, below the inner recall floor. Passing inner feasibility is not a guarantee of meeting the policy on outer data.

The exploratory conformal-only versus baseline effect is workload **−2.5099/day**, CI **[−4.7433, −0.7782]**, with recall difference **+0.0044**, CI **[−0.0557, +0.0697]**. A recall CI containing zero does **not** establish equivalence or noninferiority. Prefer “lower observed workload; uncertain recall difference” to “equal recall.” Full versus temporal increases workload by **+1.0161/day [0.2119, 2.1094]** with uncertain recall benefit. No requirement exists for the full pipeline or LSTM to win.

## C. Incomplete, failed, or unverified work

### Amendment-003 extension

`F/runs/robx_full_20260902_080752/` exists but is **empty**, last modified 2 September around 08:07:56. There is no extension summary, per-dataset output, point-accuracy CSV, timing CSV or full-run checkpoint. No repository log identifies its exit reason. No local experiment is active. Classification: **unfinished and no longer active locally; crash versus cancellation/termination is unknown**.

The driver accumulates all 15 units of a dataset in memory before writing that dataset (`src/robustness_extension.py:483–503`). An empty directory therefore cannot tell us how much unpersisted computation happened. There is no unit-level resume/checkpoint mechanism in that loop. Do not reuse an old background-task ID or infer resumability.

`robx_smoke` has `fast: true`, 13 files, one fold/seed per dataset and ten cells per unit. The saved clean/zero-control coverage, width and Winkler values agree in all four smoke units. This is limited integration evidence, not full robustness results.

Current non-fast code expects **15 cells per unit**: clean + zero control + seven fault cells + three contamination cells + three recovery cells. Across 60 units this is **900 cell rows**, **120 point rows** and **60 timing rows**, plus a non-fast summary. This is the executed-code expectation; protocol/code discrepancies still require reconciliation. All these full-extension artifacts are absent. `metrics/robustness_effects.csv` and `point_accuracy_summary.csv` are also absent.

### Reports and validation markers are not uniformly current

| File | Problem / interpretation |
|---|---|
| `F/STATUS_AND_RESUME.md` | Stale pre-engine status, 224-test history and branch-checkout instructions. Do not execute its resume recipe. |
| `F/PUBLICATION_READY.json`, `report/VALIDATION_REPORT.md` | Historical core publication gate; predates Amendment 003 and later reporting corrections. Not validation of today's complete claim set. |
| `F/report/FINAL_CLAIMS_REGISTER.md` | Older, broader claim wording. Read the later `CLAIMS_DISPOSITION.md` and this assessment for restrictions. |
| `F/report/COMPUTATIONAL_EFFICIENCY.md` | Reported 4.5/6.7/4.8/8.8 s values exactly match rounded **smoke** interval-fit timings (4.45/6.74/4.83/8.77), not full-extension or LSTM/XGBoost timings. |
| `F/report/RQ_RO_ACHIEVEMENT.md` | Claims point summary exported and robustness achieved, although referenced summary/full-extension results are absent. |
| `F/report/ROBUSTNESS_RESULTS.md` | Correctly says effects not yet computed, but then asserts absorption as a finding without completed corrected-extension evidence. Treat as draft interpretation. |
| `F/figures/fig_coverage_with_cis.png` | `figure_index.csv` traces it to superseded `final_cis.csv`; unsuitable for corrected inferential claims. |
| `F/report/FINAL_FIGURES_INDEX.md` | Heading only. Ten-figure v2 output set, SVGs and hash sidecars are absent. Four older figures exist. |
| `F/report/SLIDE_READY_VALUES.md` | Generic “only CI-supported dataset” wording also appears on BDG2 workload, which has NA CI. Read the metric-specific CSV. |

The extension validator checks dataset/family presence and some clean/zero-control values, but does not enforce the exact 60-unit × cell matrix or require every unit to have a control (`src/validate_final_study.py:218–257`). Missing control pairs are skipped. A future marker alone would still not establish completeness.

### Newly identified source discrepancies: separate from resolved audit findings

The historical audit verdict was **PASS WITH REPORTING CORRECTIONS**, and stated that no core rerun was required. Its arithmetic/inference corrections remain useful. The following current-source findings mean that verdict must not be extended to “the entire declared methodology is verified.” Relevant corrected-engine, interval, windowing and recalibration files have no changes between evaluated `9942156` and current HEAD in the checked diff.

1. **Selected point model is metadata, not the interval's input.** `select_on_inner` selects persistence/XGBoost at lines 472–482; `_all_intervals` independently fits CQR/EnbPI at lines 399–430. `evaluate_outer` uses `iv['point']` at lines 594–603 and writes `pipe.point_model` into the result row at line 621. Changing that label does not change the interval estimator. This is directly relevant to the panel's model comparison.
2. **Nested boundary handling does not fully implement the declared embargo.** `inner_split` uses 50/25/25 positional cuts without target-time purging (lines 153–182). The outer refit reconstructs a 75/25 positional split (lines 568–583), including for RICO. A no-fitting, in-memory probe of the extracted functions with 500 regular ten-minute observations and horizon one passed the pool-to-test embargo but failed both inner boundaries and the refit train/calibration boundary under the protocol's strict target-before-next-origin rule. This establishes a structural gap, not the numerical impact on the real dataset results. The positional RICO refit also needs checking for whole-run integrity.
3. **Additional recalibration receives zero residuals.** `_recalibrated_stream` builds the delayed test residual pool from `np.zeros(...)` (lines 444–447), not observed `y − prediction`; it also uses CQR calibration points for every interval family. Eighteen outer rows use periodic recalibration (PLEIA 1, energy 5, BDG2 12). The extension uses observed residuals and method-specific calibration predictions (`robustness_extension.py:171–178,299–312`), so “deterministic refit of exactly the same pipeline” needs a clean-stream equivalence check. This is distinct from the repaired updated-EnbPI helper, which does consume delayed observed residuals.
4. **Protocol execution is narrower than the declarations.** The corrected engine runs one alert horizon per dataset and only persistence/XGBoost point selection, although the protocol lists four point models and multi-horizon quality evaluation at 90/95%. DSCP is explicitly not applicable at one horizon; no corrected DSCP quality branch is run. The physical rule list omits the protocol's 360-minute candidate, and `inner_folds: 2` is not a two-fold inner selection loop. Point/interval fits use hard-coded seed 0, while seed labels mainly vary event catalogues/selections. Event scales are computed once from original train partition labels before outer folds (`corrected_study.py:722–727`); their membership relative to each earlier outer fold needs auditing before “fold-local train-only” is asserted.

These findings do not turn the 48 abstentions into software failures or undo corrected CI accounting. They restrict how confidently saved numbers can be attributed to the claimed pipeline. No scientific settings were changed and no numerical impact was estimated by refitting.

## D. Which artifacts can be used

| Artifact set | Current use |
|---|---|
| `F/metrics/run_artifacts/`, matching core `runs/full_*` | Preserved primary record of the executed implementation; suitable for accounting, diagnostic analysis and targeted audit. Scientific claims must disclose the source discrepancies above. |
| `OUTER_UNIT_LEDGER`, `FULL_RUN_INVENTORY`, `FOLD_MEMBERSHIP`, accounting/nominal audits | Usable execution/feasibility and exposure evidence. Historical report explanations are not all independently re-proven. |
| `final_cis_corrected.csv` | Preferred corrected statistical summary of that record, retaining feasible-only/diagnostic separation and metric-specific NA CIs; not proof of pipeline correctness. |
| `PAIRED_ABLATION_EFFECTS.csv` | Exploratory paired evidence only; no matched-budget or equivalent-recall claim. |
| `final_cis.csv`, original coverage-with-CIs figure | Superseded diagnostic material; do not use their uncertainty estimates as final. |
| `robx_smoke` and smoke timing values | Software integration diagnostics only. |
| Empty `robx_full_*` | No usable result evidence. |
| Older `outputs/full_study/` | Preserved pre-repair diagnostics, including model comparisons; do not substitute these for corrected-run validation. |
| Preliminary/laptop prediction CSVs and preliminary models | Permit limited labelled historical analysis; do not fill missing corrected calibration/test streams. |
| Latest report suite | Mixed: the main results table reflects corrected CSVs, while efficiency, achievement and robustness text contains unsupported statements. Review per claim. |

**Software tests:** the user's 265 passed / 1 skipped screenshot is historical and was not supplied as a test log. Existing status documents record earlier counts. No full pytest run was performed here; this session's structural probe and hash checks are not a replacement for the suite.

**Experiment completion:** core complete; full extension incomplete. **Scientific validity:** accounting and inference improved, with the integration discrepancies above still unresolved. **Operational effectiveness:** limited feasibility, substantial undercoverage, and no demonstration of broad deployment effectiveness. These are separate conclusions.

## E. Panel-response gaps ranked by priority

1. **P0 — Validate the actual prediction and split path.** Resolve model attribution, nested boundaries, recalibration residuals and fold-local scaling before authorising more fitting or broad validity claims.
2. **P0 — Repair the evidence narrative.** Remove smoke-as-results timings, absent-result achievement claims and stale CIs from publication material in a separately authorised editing task.
3. **P1 — Attention-LSTM versus XGBoost comparison.** Corrected matched point/interval/cost evidence is absent; the existing extension cannot supply it.
4. **P1 — Complete or explicitly delimit Amendment 003.** First reconcile core/extension clean streams and completeness checks; then decide whether a new full run is warranted. Do not automatically relaunch the empty directory.
5. **P1 — State what the ablation actually answers.** Retain exploratory paired effects; acknowledge that the frozen matched-budget endpoint and full declared method/horizon grid were not completed.
6. **P2 — Dataset/bibliography/protocol explanation.** Provide an accurate source-purpose-selection table, method-level citations and the actual nested protocol, with separate dataset evaluation.
7. **P2 — Simplify presentation.** One mechanism example, one protocol diagram/table, one feasibility table, and only audited figures. The original panel sheet and current dissertation manuscript were not supplied, so exact wording/page-level completion cannot be certified.

## F. Smallest next task and acceptance criteria

**Proposed next task, not executed: a no-fitting audit of split membership and prediction-stream identity on the existing four-dataset configuration, followed by a narrowly scoped repair proposal.** This is smaller and more informative than resuming Amendment 003 or adding the LSTM comparison immediately.

Acceptance criteria:

1. Produce per-dataset/fold membership evidence for every inner and refit boundary: last eligible target, next origin, overlap count, and RICO run intersections. Verify event-scale inputs against each fold's permitted training rows. Use existing local data read-only, with no adapter output rewrites.
2. Trace the estimator behind point predictions, calibration residuals, bounds and alert-consumed bounds. Demonstrate whether changing the chosen point model changes the evaluated stream. Identify all impacted core unit IDs from provenance without altering results.
3. Validate periodic/rolling update inputs with a small deterministic fixture: observed residuals may influence bounds only once available; zero placeholders cannot stand in for observations. Check core/extension clean-stream compatibility, allowing documented method differences only.
4. Reconcile declared versus executed models, horizons, nominal levels, rules, seeds and inner folds. Distinguish code repairs from scientific-design changes; propose no new datasets/models or outcome-driven thresholds.
5. End with a concrete list of affected artifacts and the smallest required repair/refit scope for user review. Do not assume that all core artifacts must be rerun, or that none must be rerun.

After that gate, the smallest model-comparison work is described in the panel matrix: assess saved-prediction availability first; if corrected calibration/test streams are absent, fit only the existing Attention-LSTM and XGBoost on matched, validated splits using the same declared uncertainty construction, plus persistence context. Save predictions/bounds and measure costs separately. No requirement is imposed on which model wins.

Recovery work stops here. Only the two requested Markdown files were created; source/configuration, existing artifacts, branch and history remain unchanged.
