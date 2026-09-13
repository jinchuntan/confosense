# Support design and remaining-study evidence

13 September 2026. Branch: [review/support-design-20260913](https://github.com/jinchuntan/confosense/tree/review/support-design-20260913), descended from `9b5acb49531ce12706285c3f040310c0ab6053dd`. The final delivery and branch history give the published commit SHA. Main, production code, completed experiments and backups are preserved. **No model fits were performed.** This is a completed structural design task, not completed amendment-005 performance evidence.

- [Quantified support audit](../../SUPPORT_DESIGN_AUDIT.md)
- [Post-inspection amendment-005 proposal](../../AMENDMENT005_PROPOSAL.md)
- [Exact remaining-study execution plan](../../REMAINING_STUDY_EXECUTION_PLAN.md)
- [Current evidence](../CURRENT_EVIDENCE.md), [recovery status](../../PROJECT_RECOVERY_STATUS.md), [panel response](../../PANEL_RESPONSE_MATRIX.md)
- [Sources and assumptions](SOURCE_ASSUMPTION_REGISTER.md), [derived-data attribution](DATA_NOTICE.md)
- [File/hash manifest](EVIDENCE_MANIFEST.csv), [publication validation](publication_validation.json), [exact current helper/production source bytes](source_archive.zip), [source hash ledger](source_archive_manifest.csv)

## Canonical tables and their purposes

All paths are relative to the repository root. GitHub's download/raw button retrieves compressed CSVs; read them with `pandas.read_csv(path, keep_default_na=False, float_precision='round_trip')`. Preserve the literal PLEIA group ID `None`. For large integer mask seeds, use `dtype={'mask_seed': str}`. Empty numeric cells mean unavailable, not zero. No private cache upload is required to inspect the support evidence.

| File | Purpose |
|---|---|
| [inventory.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/inventory.csv) | Four-task raw/eligible observations, original groups, physical frequency/horizon, exposure and all-data event-count bounds. |
| [current_roles.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/current_roles.csv) | 117 original role records: dates, rows, groups, segments, exposure, training/calibration sizes, onset/guarded placement capacities and original membership hashes. |
| [current_banks_verified.csv](../../smart_building_conformal/outputs/amendment005/plan_check_v1/current_banks_verified.csv) | **Canonical 27 current event banks:** requested, hostable, placed, effective, null, rejected, distinct-onset support and original-unit limits. |
| [current_strata.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/current_strata.csv) | All 567 original family/severity cells, including absent strata and under-supported denominators. |
| [current_events.csv.gz](../../smart_building_conformal/outputs/amendment005/support_design_v1/current_events.csv.gz) | Existing published current-bank event records; no new historical events or altered thresholds. |
| [rank_support_verified.csv](../../smart_building_conformal/outputs/amendment005/support_final_checks_v1/rank_support_verified.csv) | **Canonical 1,224 rank summaries:** original groups, initial calibration ranks and method/level/window-specific online ranks. |
| [alternatives.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/alternatives.csv) | A/B/C support arithmetic, complete-rotation budgets and declared random-mask probability criterion. |
| [alternative_B_larger_blocks.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/alternative_B_larger_blocks.csv) | Concrete larger PLEIA selection blocks and grouped RICO alternative: fitting/calibration trade-offs, dates, membership hashes, fixed B catalogue budget. |
| [original_groups.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/original_groups.csv) | Original series/run/cohort inventory, target, dates, phase and seasonal applicability. |
| [rico_source_run_audit.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/rico_source_run_audit.csv) | 287 source scheduler candidates, including the 80 excluded and 207 retained runs. |
| [rico_run_history.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/rico_run_history.csv) | Every retained run's old and proposed role assignments; documents earlier training/calibration use. |
| [rico_phase_distribution.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/rico_phase_distribution.csv) | Acquisition-phase distribution and prior use for the broader proposed RICO evaluation. |
| [proposal_roles.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/proposal_roles.csv) | Exact proposed challenge fitting, calibration, inner and outer boundaries; separately versioned RICO batches. |
| [challenge_contexts.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/challenge_contexts.csv) | 1,128 predetermined role-specific contexts, onset, warm-up/follow-up, training-only sigma and row hashes. |
| [challenge_schedules.csv.gz](../../smart_building_conformal/outputs/amendment005/support_design_v1/challenge_schedules.csv.gz) | 47,376 fixed family/severity/slot variants, masks, signs, effective/null flags and realization hashes. |
| [challenge_support.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/challenge_support.csv) | All 567 proposed role/stratum support cells; distinct effective contexts/onsets, not duplicated variant counts. |
| [challenge_summary.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/challenge_summary.csv) | Compact role-level context/effective/null/support counts for the audit. |
| [challenge_aliases.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/challenge_aliases.csv) | Deterministic duplicate realizations across slots; not additional independent observations. |
| [challenge_rule_applicability.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/challenge_rule_applicability.csv) | Sampling-frequency and context-length applicability of each physical temporal rule. |
| [challenge_inference_units.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/challenge_inference_units.csv) | Context-to-original-run or seven-day block mapping; incomplete tail blocks retained and flagged. |
| [challenge_precision_support.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/challenge_precision_support.csv) | Complete-block count screen and explicitly heuristic independent-Bernoulli planning count. |
| [challenge_inference_support.csv](../../smart_building_conformal/outputs/amendment005/support_final_checks_v1/challenge_inference_support.csv) | **Complete CI screen**, adding per-phase RICO support; five unavailable role-level screens and unmeasured precision remain explicit. |
| [challenge_zero_controls.csv](../../smart_building_conformal/outputs/amendment005/support_final_checks_v1/challenge_zero_controls.csv) | One clean identity control specification per context; future fitted-stream identity checks are not claimed executed. |
| [experiment_matrix.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/experiment_matrix.csv) | Exact 1,560 model/task/horizon/fold/seed/level cells: completed, required or inapplicable, hashes, sample/fit counts and prerequisites. |
| [forecast_roles.csv](../../smart_building_conformal/outputs/amendment005/support_design_v1/forecast_roles.csv) | 273 forecast role records across all 13 horizons and three folds. |
| [completion_counts.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/completion_counts.csv) | Point-cell status and learned tuning/final-fit accounting without double-counting interval levels. |
| [forecast_execution_queue.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/forecast_execution_queue.csv) | All 192 remaining matched units, priority, exact future argv/output paths and measured-reference planning scenarios. |
| [seasonal_execution_queue.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/seasonal_execution_queue.csv) | 27 unique deterministic computations, each with five model-seed aliases; zero learned fits. |
| [interval_method_matrix.csv](../../smart_building_conformal/outputs/amendment005/study_plan_v1/interval_method_matrix.csv) | 1,950 broader-method level cells; shared estimator ownership and DSCP joint-origin prerequisites. |
| [dscp_joint_origin_support.csv](../../smart_building_conformal/outputs/amendment005/support_final_checks_v1/dscp_joint_origin_support.csv) | 36 actual joint-horizon role sets, calibration counts, boundaries and origin hashes. |
| [dscp_joint_origin_membership.csv.gz](../../smart_building_conformal/outputs/amendment005/support_final_checks_v1/dscp_joint_origin_membership.csv.gz) | Recomputable common original-group/origin identities for each task/fold/role. |
| [scope_ledger_verified.csv](../../smart_building_conformal/outputs/amendment005/plan_check_v1/scope_ledger_verified.csv) | **Canonical full scope:** methods, seasonal, robustness, contamination, recovery, full-grid operational claims and optional extensions. |
| [command_measurements.csv](command_measurements.csv) | Actual no-fit command argv, UTC times, wall seconds and exits. Not learned-model computational costs. |

The three compressed operational observation files in [support_design_v1](../../smart_building_conformal/outputs/amendment005/support_design_v1) are `pleia_operational_membership_observations.csv.gz`, `pleia_energy_operational_membership_observations.csv.gz` and `rico_operational_membership_observations.csv.gz`. They retain row IDs, groups, original/target time, observed target values and all three fold memberships, sufficient for independent signal-change/null reconstruction.

That same directory contains exactly thirteen forecast membership files: `pleia_h{1,3,6}_forecast_membership.csv.gz`, `pleia_energy_h{1,3,6}_forecast_membership.csv.gz`, `rico_h{5,15,30,60}_forecast_membership.csv.gz` and `bdg2_h{1,3,6}_forecast_membership.csv.gz`. Each binds common flat/sequence target eligibility and all fitting/calibration/test/tuning roles. They do not contain fitted predictions. Every exact expanded path and SHA-256 is in the file manifest.

The frozen no-fit [proposal specification](../../smart_building_conformal/outputs/amendment005/support_design_v1/proposal_spec.json) and [next forecasting unit](../../smart_building_conformal/outputs/amendment005/study_plan_v1/next_forecast_unit.json) distinguish completed design from future fitting authorization.

## Verification and reporting corrections

- [Generator validation](../../smart_building_conformal/outputs/amendment005/support_design_v1/validation.json): four cache/data identities, 117 original role hashes, 1,267 preserved historical files, zero fits.
- [Six focused no-fit tests and actual log](../../smart_building_conformal/outputs/amendment005/validation/support_tests_v1.log): arithmetic boundaries, complete rotations, whole-run chronology, deterministic contexts, null/duplicate support, forbidden-fit guard.
- [Independent reconstruction](../../smart_building_conformal/outputs/amendment005/independent_verification_v1/validation.json): all 47,376 variants, 1,128 contexts, training-only scales and 210 operational/forecast boundaries.
- [Current-bank and plan verification](../../smart_building_conformal/outputs/amendment005/plan_check_v1/validation.json): 27 banks, 567 strata, 192 queued units, 1,920 future learned fits; missing generalized command explicitly detected.
- [Supplementary checks](../../smart_building_conformal/outputs/amendment005/support_final_checks_v1/validation.json): rank identities, phase precision screens, zero-control specifications and joint-origin support.

The original generated `support_design_v1/current_banks.csv` and `rank_support.csv` are preserved intermediate artifacts. Default CSV NA parsing turned the literal PLEIA group `None` into missing data in two reporting aggregates. Use the **canonical verified** files above. The [18 bank corrections](../../smart_building_conformal/outputs/amendment005/plan_check_v1/identifier_corrections.csv) and [864 rank corrections](../../smart_building_conformal/outputs/amendment005/support_final_checks_v1/rank_identifier_corrections.csv) affect group counts only; all rank/support/event values are unchanged. The initial `study_plan_v1/scope_ledger.csv` contained a prose typo of 45 unique seasonal computations; the canonical ledger and actual 27-row queue correct it. All are current-task reporting corrections, not changes to historical experiments.

The [original executed generator](../../smart_building_conformal/outputs/amendment005/validation/generator_original_source.zip) has SHA `9a7ed7b2e517d3cec7f60bfd233d2b2d25d8895db361a0ee6806be8d25cb0cd7`. The [intermediate bank-reader repair](../../smart_building_conformal/outputs/amendment005/validation/generator_bank_reader_source.zip) has SHA `6a9bd16a694dc502b330b093fc584b65e19c7b31553fc970047a78ea537c6ef4`. The final generator fixes both literal-ID readers; the final source archive/ledger records its actual bytes. The initial validation identifies the source actually executed, not the later corrected reader. Independent correction checks make a full regeneration unnecessary.

## Reproduction without fitting

Use the existing `C:/cfs_venv` environment from `smart_building_conformal`; retain one OMP/OpenBLAS/MKL/NumExpr thread. These commands only verify published data and create **fresh** outputs. Never overwrite the preserved evidence directories.

```powershell
& C:/cfs_venv/Scripts/python.exe -B -m pytest tests/test_support_design005.py -q
& C:/cfs_venv/Scripts/python.exe -B scripts/verify_support_design005.py --base outputs/amendment005/support_design_v1 --out outputs/amendment005/independent_verification_recheck
& C:/cfs_venv/Scripts/python.exe -B scripts/check_remaining_study005.py --base outputs/amendment005/support_design_v1 --plan outputs/amendment005/study_plan_v1 --out outputs/amendment005/plan_recheck --dry-run
& C:/cfs_venv/Scripts/python.exe -B scripts/finalize_support005.py --base outputs/amendment005/support_design_v1 --plan outputs/amendment005/study_plan_v1 --out outputs/amendment005/final_support_recheck
```

The [generator](../../smart_building_conformal/scripts/support_design005.py) can rebuild the structural design in a fresh `--out` directory using `--cache-dir C:/Users/nigel/ConfoSenseBackups/amendment004_20260913/preflight_v1`; its four local cache SHA-256 values and published preflight hash are in the generator validation. These trusted local pickle caches and raw archives are not published. `build_plan.py` requires those caches and its original output path to be absent; use an isolated checkout for a full rebuild. The observed-row verification above does not require pickle caches. Fitted predictions are not needed for any support decision here. The final source archive preserves production source hash `203f3babf66c98ac072ad450abec5ea7ce3d60473f02708fa64ac2102ea3f7c9`.

The next fitting command deliberately remains unavailable until `src.matched_forecasting005` is implemented and the single PLEIA-energy h1/fold0/seed42 unit is authorized. The [execution plan](../../REMAINING_STUDY_EXECUTION_PLAN.md) specifies its exact command, candidates, 3 point/6 interval cells, 8 tuning/2 final learned fits, resource guards, saved artifacts and zero-fit resume acceptance. No queue command was launched.

## Preserved completed evidence

- [PLEIA temperature forecasting pilot](../../MODEL_COMPARISON_PILOT_REPORT.md): nine point and eighteen interval cells retained unchanged; actual model cost measurements are in its linked CSVs.
- [Completed BDG2 three-fold benchmark](../../BDG2_THREEFOLD_BENCHMARK_REPORT.md), [all code/CSV/stream evidence](../bdg2_threefold_20260913/EVIDENCE_INDEX.md): three primary abstentions preserved, no historical retuning.
- [Entry file hashes](../../smart_building_conformal/outputs/amendment005/support_design_v1/entry_preservation.json): all 1,267 historical output/configuration/protocol files remain byte-identical.

The publication manifest excludes itself and `publication_validation.json` to avoid recursive hashes. Git commit identity binds those two files; final remote verification is retained in the external publication record. Structural completion does not imply scientific/full-study readiness, which remains **false**.
