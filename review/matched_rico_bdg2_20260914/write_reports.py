"""Render reports and status links from the verified, immutable result tables."""
import json,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];SMART=ROOT/'smart_building_conformal'
REVIEW=Path(__file__).resolve().parent;BASE=SMART/'outputs/matched_forecasting005';OUT=BASE/'rico_bdg2_report_v2'
sys.path.insert(0,str(SMART))
from src.unit_checkpoint import source_digest
ENTRY='b26ee5b6a2cfb322b392e017e627bf3c96339c78'
PREFIT='350ef4fd1c92c12a982df2b8366023937515b65b'
BRANCH='review/matched-rico-bdg2-20260914'

def csv(name):return pd.read_csv(OUT/name,keep_default_na=False,float_precision='round_trip')
def table(frame,cols):
 def val(x):
  if isinstance(x,(float,np.floating)):return f'{x:.6g}'
  return str(x).replace('|',' / ')
 return '\n| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+''.join('| '+' | '.join(val(x) for x in row)+' |\n' for row in frame[cols].itertuples(index=False,name=None))+'\n'
def write(path,text):path.write_text(text,encoding='utf-8')

def main():
 check=json.loads((OUT/'analysis_validation.json').read_text());assert check['passed']
 summary=check['summary'];comparison=csv('pooled_comparison.csv');cost=csv('model_costs.csv');runtime=csv('run_costs.csv');contrasts=csv('paired_descriptive_contrasts.csv')
 fields=['model','mae','rmse','coverage90','mpiw90','winkler90','coverage95','mpiw95','winkler95','model_phase_seconds']
 report=f'''# First matched RICO and BDG2 units

14 September 2026. **Both authorized experiments completed with actual exit 0.** RICO h5/f2/seed42 ran first; after its independent validation and zero-fit resume, BDG2 h1/f2/seed42 ran. Total: **16 tuning + 4 final learned fits**, six point and twelve interval cells. No tiny learned fits or additional queue units were run in this task.

Evaluated pre-fit commit: `{PREFIT}`; source SHA-256 `{source_digest()}`. Both active protocols were frozen before either fit. The [joint manifest](review/matched_rico_bdg2_20260914/joint_pre_fit_manifest.json) binds the current handoff/authorization separately from the original runner/design provenance. The [evidence index](review/matched_rico_bdg2_20260914/EVIDENCE_INDEX.md) links all fitted artifacts, per-row streams, CSVs, resource logs and validation receipts.

## RICO: five-minute B.RTD3 temperature forecast

The values below are in degrees Celsius; coverage is a proportion. The pooled estimates weight target rows equally.
'''+table(comparison[comparison.dataset=='rico'],fields)+'''
Support: **12,932 fit / 4,452 calibration / 8,692 test rows**, respectively **61/21/41 complete original runs**. This is the first evaluation batch, outer fold 2, under amendment-005's five chronological run batches. It is not the old single-run test. Calibration residuals are pooled across earlier runs; new evaluation runs have no within-run calibration observations.

Persistence has the smallest observed errors on this test block. XGBoost and especially LSTM have substantial interval undercoverage: their 95% intervals cover approximately 73.47% and 18.81% of test targets, versus 97.24% for persistence. The much larger LSTM error is a validated outcome, not a reason to change candidates or rerun this unit. Phase differences and calibration-to-test shift limit transport of the pooled residual distribution; this descriptive result alone does not identify a causal explanation or a new implementation defect.

The test comprises one phase-1 run, six phase-3 runs and 34 phase-4 runs. All 41 were used in historical training under at least one legacy fold; they are not globally untouched holdouts. Within this new unit, fitting/calibration precede the evaluation runs. This post-inspection, phase-imbalanced evidence cannot establish prospective or phase-conditional coverage. A phase-stratified population interval is unavailable with only one phase-1 run; no phase is dropped to obtain one.

Phase summaries (sample-weighted within each phase):
'''+table(csv('rico_phase_metrics.csv'),['phase','model','nominal_level','original_runs','n','mae','rmse','coverage','mpiw','winkler'])+'''
Every original run also has a separate row in [group_metrics.csv](smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/group_metrics.csv). The distinctly labelled equal-run diagnostics are in [equal_group_diagnostics.csv](smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/equal_group_diagnostics.csv). Neither is relabelled as the pooled result.

## BDG2: one-hour energy forecast

Errors, widths and Winkler scores are in kWh for the hourly observations; coverage is a proportion.
'''+table(comparison[comparison.dataset=='bdg2'],fields)+'''
Support: **51,664 fit / 17,370 calibration / 34,640 test rows** across the same ten retained buildings. Chronological splits and all flat-feature histories/lazy sequences remain within buildings. This is forecasting in known buildings, not unseen-building generalization. Pooled errors are sample-weighted and can be dominated by larger loads. Each building's 90%/95% point and interval summaries are published separately in `group_metrics.csv`; equal-building diagnostics remain separate.

XGBoost has the smallest observed MAE/RMSE and Winkler scores on this unit. LSTM improves point errors over persistence but has larger errors, wider intervals and much higher measured cost than XGBoost. Both learned models are close to the nominal interval levels in the pooled test; this does not establish coverage for each building or for unseen buildings. These are descriptive one-fold/one-seed results, not a general model ranking.

## Frozen construction and selected configurations

Persistence reads the actual last-observation feature `target_lag_0` and has no learned fit. XGBoost is the fitted `xgboost.sklearn.XGBRegressor`, histogram trees, squared-error objective, 400 trees, depth 3 or 5, learning rate .05, subsample/column fraction .8, seed42 and `n_jobs=1`, with all remaining pinned parameters unchanged. Full wrapper and actual booster configurations are saved.

Attention-LSTM retains hidden64/dropout.2/batch256, 24-step sequences, candidate learning rates .001/.0005, maximum30 epochs/patience5, Adam/MSE and training-only channel/target normalization. Both learned models use two purged inner folds, equally weighted original-unit validation MAE and exact candidate-order ties. LSTM improvement must exceed 1e-6; final epochs equal the ceiling of the selected candidate's mean best inner epoch. Final calibration/test results select no hyperparameters, epochs or preprocessing.

Candidate IDs are zero-based (XGBoost 0=depth3, 1=depth5; LSTM 0=.001, 1=.0005):
'''+table(comparison,['dataset','model','selected_candidate','final_epochs'])+'''
Each fitted model supplies its own absolute calibration residuals. The symmetric radius is the one-based ordered residual at `ceil((n+1)*level)`. No interpolated/clipped rank, residual sharing, recalibration or interval truncation is used. The 90%/95% intervals share one model fit. Insufficient rank remains an explicit unavailable status; both actual units have sufficient calibration support.
'''+table(comparison,['dataset','model','n_calibration','rank90','q90','rank95','q95'])+'''
All models share exact target IDs and permitted causal variables. Flat features and 24-step sequence channels are different representations and effective histories. Their names, physical frequency and exact role dates are in the protocols and [fresh_role_support.csv](review/matched_rico_bdg2_20260914/fresh_role_support.csv). The generic support `target` field is null because these adapters store target selection in nested configuration/source; RICO explicitly resolves `rico.target_column=B.RTD3`, while BDG2's electricity loader and retained building IDs are bound by the source/configuration and data hashes.

## Actual costs and verification
'''+table(cost,['dataset','model','tuning_seconds','final_fit_seconds','calibration_seconds','inference_seconds','inference_rows_per_second','process_cpu_seconds','baseline_rss_MiB','peak_rss_MiB','incremental_peak_rss_MiB'])+table(runtime,['dataset','command_seconds','process_cpu_seconds','preparation_seconds','preparation_peak_rss_MiB','action_peak_rss_MiB','lifetime_peak_rss_MiB','validation_seconds','resume_seconds'])+'''
The environment is the existing CPU-only Intel i7-12700H setup, one numerical/Torch thread and `n_jobs=1`. The 3 GiB launch reference is nonblocking and actual readings are in `model_costs.csv`; the 256 MiB epoch floor and 8 GiB free-disk checks remain. Memory samples are 50 ms apart and can miss short peaks; lifetime high-water marks are separate. Model phases exclude preparation, serialization, checkpoint writing, validation/resume and interpreter startup. Nested per-fit timers must not be added again to enclosing tuning/final phases. Detailed CPU/memory/throughput and serialization/I/O records are published.

For **each unit**, independent arithmetic passed all three point and six interval cells, exact own-residual ranks/bounds, common targets, candidate and epoch selection, training-only normalization and six saved-model calibration/test prediction checks at the declared 1e-7 absolute/relative tolerance. Completed resume forbade all learned fitting routes, performed zero new fits and left every run file unchanged. Group-weighted recomputation independently reproduces the pooled metrics. Passing integrity checks does not certify nominal coverage.

The only production repair was a narrow no-fit guard exception for the exact deterministic `GroupPartitioner.fit` method, demonstrated necessary by failed RICO readiness. Fifteen no-fit regression checks passed; no synthetic fits were repeated. Initial protocols and the failed readiness remain preserved. A separate helper's wrong-working-directory attempt entered a download path and was stopped; its log and unused downloads are preserved, and the corrected helper uses existing project data. Both repairs preceded all real fitting, invalidated no completed numerical result and caused no real refit. See [pre-fit record](review/matched_rico_bdg2_20260914/PRE_FIT_EXECUTION.md) and the successful/failed command ledger.

The combined-report v1 attempt subsequently failed on the older temperature pilot's provenance layout: its executed source hash is stored in the checkpoint specification, not at the top of the protocol. The corrected v2 reader uses that original specification and verifies the original protocol digest. The failed partial report, exact failed helper source and [reporting attempt exits](review/matched_rico_bdg2_20260914/reporting_attempts.json) are preserved. This reporting-only repair changes no source identity or numerical result and triggers no fitting.

Negative points/lower bounds are counted per original group in `group_metrics.csv`. Original zero/repeated/negative targets are retained in `target_diagnostics.csv`; no post-hoc cleaning or clipping was applied. Frozen causal imputation, phase/load shifts and temporal dependence limit interpretation.

## Available evidence across four settings

The following descriptive contrasts preserve each target's units/horizon/fold/seed. LSTM-minus-XGBoost errors and interval scores are paired on the same rows. No Celsius/kWh errors are averaged into a global ranking. The uneven six-unit pilot set is not a completed four-task study or five-seed inference; no general superiority/equivalence conclusion follows.
'''+table(contrasts,['dataset','horizon','outer_fold','model_seed','target_units','mae_lstm_minus_xgboost','rmse_lstm_minus_xgboost','coverage95_lstm_minus_xgboost','mpiw95_lstm_minus_xgboost','winkler95_lstm_minus_xgboost','lstm_to_xgboost_model_seconds'])+'''
[all_four_settings.csv](smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/all_four_settings.csv) includes all 18 model rows and both interval levels, including the three historical temperature horizons and energy h1. [evidence_reuse_ledger.csv](smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/evidence_reuse_ledger.csv) retains their original source/protocol/run-tree hashes; no historical model was refitted. Interval width must be read with achieved coverage and Winkler, not in isolation.

The new completion overlay records **6/195 paired units, 18/585 point cells and 36/1,170 interval cells complete**, leaving **189 units / 1,890 learned fits**. Original matrices and earlier overlays are unchanged. Seasonal, broader interval methods, DSCP, operational/conditional challenge and robustness remain separate obligations.

The [concrete next-batch proposal](MATCHED_NEXT_BATCH_PROPOSAL.md) enumerates twelve units selected for coverage and feasibility. It is **not authorized or launched** by this task. Full-study readiness remains false.
'''
 roles=pd.read_csv(REVIEW/'fresh_role_support.csv',keep_default_na=False)
 report+='\n## Exact target-time support\n'+table(roles[roles.role.isin(['fit','calibration','test'])],['dataset','role','n','groups','target_min','target_max'])
 report+='\n## Verification and negative-output totals\n'+table(csv('verification_summary.csv'),['dataset','actual_exit','point_cells','interval_cells','saved_model_checks','maximum_prediction_difference','completed_resume_fits','all_run_files_unchanged'])
 negatives=csv('group_metrics.csv').groupby(['dataset','model','nominal_level'],as_index=False)[['negative_points','negative_lower_bounds']].sum()
 report+=table(negatives,['dataset','model','nominal_level','negative_points','negative_lower_bounds'])+'\nPoint predictions are shared across levels; do not count the two repeated point diagnostics as different forecasts. Bounds and point predictions remain unclipped.\n'
 write(ROOT/'RICO_BDG2_MATCHED_FIRST_UNITS_REPORT.md',report)
 batch=csv('next_batch_units.csv');refs=csv('measured_task_timing_references.csv')
 max_peak=float(runtime.lifetime_peak_rss_MiB.max());max_disk=int((runtime.output_bytes+runtime.audit_bytes).max())
 plan=f'''# Proposed next matched batch: twelve fixed units

14 September 2026. **Proposal only; no additional fitting authorization and no batch launch.** The two newly authorized units completed. The generalized runner has no demonstrated unresolved implementation blocker for these matched units. Pending execution is distinct from the unimplemented broader interval/operational obligations.

Select the earliest three still-pending keys for each dataset from the unchanged published queue, then retain their original queue order. This balances all four settings while broadening horizon/fold coverage, uses seed42 as declared in that queue, and does not use model rankings, error sizes or coverage to select work. Five-seed inference remains pending.
'''+table(batch,['batch_order','original_priority','dataset','horizon','outer_fold','model_seed','fit_n','updated_low_model_seconds','updated_high_model_seconds'])+f'''
Exact scope: **12 paired units, 96 tuning + 24 final =120 learned fits, 36 point and 72 interval cells**, with persistence/XGBoost/Attention-LSTM, both own-model 90%/95% split-conformal levels and unchanged candidates. Each row's exact planned output/argv and prerequisites are in [next_batch_units.csv](smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/next_batch_units.csv). These bare run argv require the prior freeze/readiness steps below.

## Measured timing and resource assumptions

Each proposed unit uses its own dataset's measured model-phase seconds per final-fitting row, scaled by that unit's fixed fit count. For temperature, use the min/max rates across its three measured horizons; other settings currently have one measured unit. Retain the explicit [.5,3] planning factors. This gives **{summary['next_batch_low_model_minutes']:.2f}–{summary['next_batch_high_model_minutes']:.2f} model-minutes** for this batch. These are scheduling scenarios, not statistical bounds, deadlines or wall-time promises; they exclude preparation, serialization/I/O, validation/resume, changing epochs and channel/history costs. No operational HistGradientBoosting/CQR timing is used.
'''+table(refs,['dataset','horizon','outer_fold','model_seed','fit_n','model_phase_seconds'])+f'''
The updated full remaining core queue scenario is **{summary['remaining_low_model_hours']:.2f}–{summary['remaining_high_model_hours']:.2f} model-hours**; broader methods are excluded. Preserve actual per-unit phase measurements instead of treating a row-scaled estimate as evidence.

For the two new units, measured preparation, validation/resume and lifetime peaks are:
'''+table(runtime,['dataset','command_seconds','preparation_seconds','validation_seconds','resume_seconds','lifetime_peak_rss_MiB','output_bytes','audit_bytes'])+f'''
The larger of these lifetime peaks is **{max_peak:.1f} MiB**. Budget approximately **{1.5*max_peak:.1f} MiB** per active process as a planning allowance, not a new blocking launch rule or a guarantee. Run one experiment at a time, with lazy batch256 and one numerical/Torch thread. Preserve the nonblocking 3 GiB available-RAM reference, 256 MiB epoch floor and 8 GiB free-disk check. Retain actual available RAM, disk and process peaks at every unit.

The largest new run plus audit occupies **{max_disk/2**20:.1f} MiB**. A conservative twelve-unit storage allowance of twice that size per unit is **{24*max_disk/2**30:.2f} GiB**, excluding source data and any backup/publication duplication; verify free disk before the batch and each unit. Allocation/I/O failures require preserved evidence and correction, never a smaller scientific cohort/grid.

## Exact execution package after separate authorization

1. Create a new authorization listing exactly the twelve CSV keys. Freeze all protocols with current source/config/package/data/role identities and the unchanged original memberships; select unused output versions. Pass fresh no-fit readiness and commit the evaluated code plus joint manifest before any fit. The authorization in this completed task continues to allow only RICO h5/f2/s42 and BDG2 h1/f2/s42.
2. For each row in CSV order, run `src.matched_forecasting005 run` through `scripts/log_pilot_command.py`, passing its frozen `--design-dir` or explicit protocol/readiness. The CLI already exists; no second runner or model redesign is required.
3. Persist one atomic checkpoint per model. On interruption, explicitly resume under the same source/config/data identity and reuse complete models; mid-fit recovery is not available. Keep failed logs and incomplete attempts. Never rerun a valid complete fit for improved scores.
4. Before advancing, require actual exit0, 8 tuning/2 final learned fits, independent 3-point/6-interval arithmetic, six fitted-artifact prediction checks, original-group summaries and zero-fit completed resume with all run files unchanged. Publish incremental evidence at sensible completed-unit boundaries.
5. Stop for an unresolved source/config/data/role mismatch, checkpoint corruption, failed arithmetic/artifact check, nonfinite model output, actual allocation failure, epoch-floor failure or disk guard failure. Preserve completed checkpoints. Disappointing rankings, missed nominal coverage, an exceeded timing scenario or a sub-3-GiB launch reading alone are not stop conditions.

This proposal does not launch seasonal, full interval methods/DSCP, injected-fault selection, recalibration, conditional challenge or robustness experiments. Those remain separately scoped implementation/execution obligations.
'''
 write(ROOT/'MATCHED_NEXT_BATCH_PROPOSAL.md',plan)
 index=f'''# Matched RICO and BDG2 evidence index

Branch: [{BRANCH}](https://github.com/jinchuntan/confosense/tree/{BRANCH}). Evaluated pre-fit commit: `{PREFIT}`. Final publication SHA is supplied by the delivery and branch history. Both authorized units completed; no additional batch ran.

- [Combined completed report](../../RICO_BDG2_MATCHED_FIRST_UNITS_REPORT.md), [concrete twelve-unit proposal](../../MATCHED_NEXT_BATCH_PROPOSAL.md)
- [Current authorizing handoff](AUTHORIZING_HANDOFF.md), [authorization](../../smart_building_conformal/configs/matched_forecasting005_rico_bdg2_authorization.json), [pre-fit record](PRE_FIT_EXECUTION.md), [joint identity manifest](joint_pre_fit_manifest.json)
- [Exact evaluated source archive](evaluated_source.zip), [runner](../../smart_building_conformal/src/matched_forecasting005.py), [guard repair](../../smart_building_conformal/src/matched_models005.py), [independent validator](../../smart_building_conformal/src/matched_validation005.py)
- [Fresh roles/dates](fresh_role_support.csv), [original-group history](role_group_history.csv), [sequence boundary verification](sequence_group_verification.csv)
- [Publication manifest](EVIDENCE_MANIFEST.csv), [preservation/publication validation](publication_validation.json), [report-helper archive](review_helpers.zip), [data attribution](DATA_NOTICE.md)
- [Reporting attempts](reporting_attempts.json), [preserved failed analysis status](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v1/ATTEMPT_STATUS.json)

## Summary CSVs

All links below are repository-relative. Use `pandas.read_csv(path, keep_default_na=False, float_precision="round_trip")` to preserve string IDs and numeric round trips. Empty final-epoch fields are inapplicable to persistence/XGBoost, not zero-epoch fits. No CSV upload by the user is needed.

| File | Purpose |
|---|---|
'''
 purposes={'rico_comparison.csv':'Three RICO model rows, errors, both interval levels, selection and model-phase cost.',
 'bdg2_comparison.csv':'Three BDG2 model rows with the same complete fields.',
 'pooled_comparison.csv':'Both units pooled over target rows, clearly labelled units/horizons.',
 'group_metrics.csv':'Every original RICO run / BDG2 building: point and 90/95 interval metrics, support and negative-output counts.',
 'rico_phase_metrics.csv':'Separate sample-weighted acquisition-phase summaries.',
 'equal_group_diagnostics.csv':'Explicit equal-run/equal-building diagnostics, separate from pooled results.',
 'model_costs.csv':'Tuning/final/calibration/inference/serialization, CPU, throughput, memory and actual launch RAM.',
 'run_costs.csv':'Command wall/CPU, preparation, action/lifetime memory, audit/resume and storage costs.',
 'checkpoint_io.csv':'Atomic checkpoint writing measurements, separate from model phases.',
 'command_measurements.csv':'All successful/failed attempts with exact command, PID, start/end, exit and fit count.',
 'tuning_comparison.csv':'All sixteen tuning candidate/fold outcomes and best epochs.',
 'target_diagnostics.csv':'Unfiltered zeros, repeated values and target extrema by task/role.',
 'all_four_settings.csv':'Eighteen model rows across six completed paired units, all four settings.',
 'paired_descriptive_contrasts.csv':'Within-unit LSTM-minus-XGBoost errors/interval scores and cost ratios; no pooled cross-unit ranking.',
 'evidence_reuse_ledger.csv':'Original source, protocol and full run-file-tree identities, with zero historical refits.',
 'completion_overlay.csv':'Versioned 6/195 paired-unit completion; original and earlier overlays untouched.',
 'remaining_queue_updated.csv':'189 remaining units in preserved queue order with same-dataset measured timing scenarios.',
 'measured_task_timing_references.csv':'Actual six paired-unit model-phase measurements used for all four settings.',
 'next_batch_units.csv':'Twelve specifically enumerated proposed keys, counts, order and commands; not launched.',
 'analysis_validation.json':'Independent group-to-pooled reconciliation and complete analysis outcomes.',
 'verification_summary.csv':'Actual exits, metric/artifact cell counts, maximum reload discrepancies and zero-fit resume outcomes.'}
 for name,purpose in purposes.items():index+=f'| [{name}](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/{name}) | {purpose} |\n'
 index+='\n## Per-unit protocols, artifacts and independent checks\n\n'
 for ds,h in [('rico',5),('bdg2',1)]:
  s=f'{ds}_h{h}_f2_s42_v2';prefix='../../smart_building_conformal/outputs/matched_forecasting005/'+s
  index+=f'''### {ds}: h{h}/fold2/seed42

- [Frozen protocol](../../smart_building_conformal/protocols/matched_forecasting005/{s}/frozen_protocol.json), [all ordered memberships](../../smart_building_conformal/protocols/matched_forecasting005/{s}/membership.csv.gz), [readiness](../../smart_building_conformal/protocols/matched_forecasting005/{s}/readiness.json)
- [Point metrics]({prefix}/point_summary.csv), [interval metrics]({prefix}/interval_quality.csv), [actual exit]({prefix}.log.json), [process cost]({prefix}.process.json), [fit journal]({prefix}/fit_calls.jsonl), [execution environment]({prefix}/execution_environment.json)
- [Independent validation]({prefix}_audit/validation.json), [recomputed points]({prefix}_audit/recomputed_point_metrics.csv), [recomputed intervals]({prefix}_audit/recomputed_interval_metrics.csv), [saved-model verification]({prefix}_audit/saved_model_verification.csv), [selection]({prefix}_audit/independent_selection.csv), [phase resources]({prefix}_audit/phase_measurements.csv), [nested fit resources]({prefix}_audit/learned_fit_measurements.csv)
- [Zero-fit resume](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_validation_v1/{s}_resume.json), [resume command exit](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_validation_v1/{s}_resume.log.json)

| Model | Fitted artifact and complete per-row evidence |
|---|---|
'''
  for m,file in [('persistence','model.json'),('xgboost','model.ubj'),('attention_lstm','model.pt')]:
   unit=prefix+'/units/'+f'{ds}_h{h}_f2_s42_{m}'
   index+=f'| {m} | [artifact]({unit}/{file}), [all unit files]({unit}) |\n'
 index+='''
Each model directory includes `predictions.csv.gz` (both levels), `calibration.csv.gz` (own residuals), `fitting_membership.csv.gz`, `tuning_predictions.csv.gz`, `tuning.csv.gz`, `training_history.csv.gz`, `payload.json` and `COMPLETE.json` hashes. Learned final artifacts include all required model/preprocessing state. XGBoost's actual booster configuration is separate; LSTM reload uses `weights_only=True`. Both levels share the same trained model.

## Reproduction and preserved evidence

From `smart_building_conformal`, with the recorded environment/data and exact evaluated source bytes, use fresh receipt directories:

```powershell
# Replace dataset/horizon/stem together for BDG2: bdg2 / 1 / bdg2_h1_f2_s42_v2.
& C:/cfs_venv/Scripts/python.exe -B -m src.matched_forecasting005 validate --matrix outputs/amendment005/support_design_v1/experiment_matrix.csv --dataset rico --horizon 5 --outer-fold 2 --model-seed 42 --design-dir protocols/matched_forecasting005/rico_h5_f2_s42_v2 --out outputs/matched_forecasting005/rico_h5_f2_s42_v2 --receipt outputs/matched_forecasting005/rico_recheck
& C:/cfs_venv/Scripts/python.exe -B -m src.matched_forecasting005 resume --forbid-fits --matrix outputs/amendment005/support_design_v1/experiment_matrix.csv --dataset rico --horizon 5 --outer-fold 2 --model-seed 42 --design-dir protocols/matched_forecasting005/rico_h5_f2_s42_v2 --out outputs/matched_forecasting005/rico_h5_f2_s42_v2 --receipt outputs/matched_forecasting005/rico_resume_recheck.json
```

Validation/resume never authorize new fitting. Source/config/package/data or checkpoint mismatch must fail. The archive preserves raw evaluated source bytes, including line endings; use an isolated copy if a checkout changes those bytes. Recomputing published group/pooled arithmetic requires only the saved CSVs and analysis helper; recreating features for fitted-model checks additionally requires the original data. The existing local source/data were used for the actual recorded checks.

[Fifteen regression checks](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_validation_v1/regression.log), [successful joint preflight](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_validation_v1/joint_preflight_v2.log.json), [entry preservation hashes](entry_preservation.json) and the exact failed attempts are retained. No historical output or original protocol was rewritten. The historical [energy report](../../PLEIA_ENERGY_MATCHED_H1_REPORT.md), [temperature pilot](../../MODEL_COMPARISON_PILOT_REPORT.md) and [BDG2 operational report](../../BDG2_THREEFOLD_BENCHMARK_REPORT.md) remain available with their original identities and abstentions.

The publication manifest excludes itself and publication_validation.json to avoid recursive hashes; final Git identity binds both. Remote SHA/content checks and the additional backup are recorded externally and confirmed in the delivery. Main and previous review branches remain unchanged.
'''
 write(REVIEW/'EVIDENCE_INDEX.md',index)
 for name in ['PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']:
  old=subprocess.check_output(['git','show',ENTRY+':'+name],cwd=ROOT).decode('utf-8')
  prefix='../' if name.startswith('review/') else ''
  front=f'''# Current status: RICO and BDG2 matched units completed

14 September 2026. Both authorized units (RICO h5/fold2/seed42 and BDG2 h1/fold2/seed42) completed, each with actual exit0, eight tuning/two final learned fits, independent 3-point/6-interval validation, six saved-model checks and zero-fit completed resume. No historical fits or new tiny fits were repeated. The documented nonblocking RAM reference remains in effect.

The core matched comparison is now **6/195 paired units, 18/585 point cells and 36/1,170 interval cells complete**; 189 units /1,890 learned fits remain. Historical protocols/results, BDG2 operational abstentions and earlier completion overlays are preserved. Broader interval methods, seasonal, operational/conditional challenge and robustness remain separate; full-study readiness is false.

Read the [completed report]({prefix}RICO_BDG2_MATCHED_FIRST_UNITS_REPORT.md), [evidence index]({'' if prefix else 'review/'}matched_rico_bdg2_20260914/EVIDENCE_INDEX.md) and [twelve-unit next-batch proposal]({prefix}MATCHED_NEXT_BATCH_PROPOSAL.md). The larger batch is specified but not authorized or launched. It uses measured same-dataset costs from all four settings, preserves queue order and does not select units by model rankings.

Branch: [{BRANCH}](https://github.com/jinchuntan/confosense/tree/{BRANCH}); evaluated pre-fit commit `{PREFIT}`. The final delivery/branch history identifies the publication SHA.

<!-- matched-rico-bdg2-20260914: historical content -->

'''
  (ROOT/name).write_bytes(front.encode('utf-8')+old.encode('utf-8'))

if __name__=='__main__':main()
