"""Build the completed-unit report/overlay from independently verified evidence."""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];SMART=ROOT/'smart_building_conformal'
BASE=SMART/'outputs/matched_forecasting005';RUN=BASE/'pleia_energy_h1_f0_s42_v1'
AUDIT=BASE/'energy_h1_audit_v2';OUT=BASE/'energy_h1_report_v1'
REVIEW=Path(__file__).resolve().parent
sys.path.insert(0,str(SMART))
from src.unit_checkpoint import digest,source_digest

def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def csv(path):return pd.read_csv(path,keep_default_na=False,float_precision='round_trip')
def table(frame,columns):
 def val(x):
  if x is None or pd.isna(x):return 'unavailable'
  return (f'{x:.6g}' if isinstance(x,(float,np.floating)) else str(x)).replace('|',' / ')
 return '| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'+''.join('| '+' | '.join(val(v) for v in row)+' |\n' for row in frame[columns].itertuples(index=False,name=None))

def main():
 OUT.mkdir(parents=True,exist_ok=False)
 run_command=load(str(RUN)+'.log.json');assert run_command['exit_status']==0
 audit=load(AUDIT/'validation.json');assert audit['passed']
 resume=load(BASE/'validation/energy_h1_resume_v1.json');assert resume['models_fitted']==0 and resume['all_run_files_unchanged']
 assert load(RUN/'execution_environment.json')['source_hash']==audit['source_hash']
 env=load(RUN/'execution_environment.json');process=load(str(RUN)+'.process.json')
 protocol=load(SMART/'protocols/matched_forecasting005/pleia_energy_h1_f0_s42_v1/frozen_protocol.json')
 cfg=protocol['config'];points=csv(RUN/'point_summary.csv');intervals=csv(RUN/'interval_quality.csv')
 costs=[];diagnostics=[];tunes=[];modelrows=[]
 for model in cfg['models']:
  unit=RUN/'units'/f'pleia_energy_h1_f0_s42_{model}'
  payload=load(unit/'payload.json');point=points[points.model==model].iloc[0]
  phase_seconds=sum(float(point[name+'_seconds']) for name in ['tuning','final_fit','calibration','inference'])
  costs.append(dict(model=model,tuning_seconds=point.tuning_seconds,final_fit_seconds=point.final_fit_seconds,
    calibration_seconds=point.calibration_seconds,inference_seconds=point.inference_seconds,
    model_phase_seconds=phase_seconds,process_cpu_seconds=point.process_cpu_seconds,
    inference_rows_per_second=point.inference_rows_per_second,baseline_rss_MiB=point.baseline_rss_bytes/2**20,
    peak_rss_MiB=point.peak_rss_bytes/2**20,incremental_peak_rss_MiB=(point.peak_rss_bytes-point.baseline_rss_bytes)/2**20,
    peak_private_MiB=point.peak_private_bytes/2**20,
    launch_available_ram_GiB=payload['launch_resources']['available_ram_bytes']/2**30,
    original_3GiB_reference_met=payload['launch_resources']['launch_ram_reference_met']))
  pred=csv(unit/'predictions.csv.gz');base=pred[pred.nominal_level==.9]
  record=dict(model=model,mae=point.mae,rmse=point.rmse,model_phase_seconds=phase_seconds,
              selected_candidate=point.selected_candidate,final_epochs=point.final_epochs)
  diagnostic=dict(model=model,negative_point_predictions=int((base.point<0).sum()),minimum_point=float(base.point.min()),
                  maximum_point=float(base.point.max()),clipped=False)
  for level in cfg['nominal_levels']:
   saved=intervals[(intervals.model==model)&(intervals.nominal_level==level)].iloc[0];part=pred[pred.nominal_level==level];suffix=str(int(level*100))
   for field in ['coverage','mpiw','winkler','q','rank']:record[field+suffix]=saved[field]
   diagnostic['negative_lower_'+suffix]=int((part.lower<0).sum());diagnostic['minimum_lower_'+suffix]=float(part.lower.min())
  modelrows.append(record);diagnostics.append(diagnostic)
  if model!='persistence':
   tune=csv(unit/'tuning.csv.gz');tune['model']=model;tunes.append(tune)
 modelcost=pd.DataFrame(costs);comparison=pd.DataFrame(modelrows);negative=pd.DataFrame(diagnostics)
 modelcost.to_csv(OUT/'model_computational_summary.csv',index=False)
 comparison.to_csv(OUT/'matched_model_comparison.csv',index=False)
 negative.to_csv(OUT/'negative_prediction_diagnostics.csv',index=False)
 pd.concat(tunes,ignore_index=True).to_csv(OUT/'inner_tuning_comparison.csv',index=False)
 # Original target observations, without classifying real zero use as a meter fault.
 quality=[]
 for role,file in [('calibration','calibration.csv.gz'),('test','predictions.csv.gz')]:
  frame=csv(RUN/'units/pleia_energy_h1_f0_s42_persistence'/file)
  if role=='test':frame=frame[frame.nominal_level==.9]
  values=frame.y_true.to_numpy();same=np.r_[False,values[1:]==values[:-1]]
  quality.append(dict(role=role,n=len(frame),original_groups=frame.group_id.nunique(),zeros=int((values==0).sum()),
      negative_targets=int((values<0).sum()),minimum=float(values.min()),maximum=float(values.max()),
      adjacent_equal_targets=int(same.sum()),p50=float(np.quantile(values,.5)),p95=float(np.quantile(values,.95)),
      cleaning='none beyond original frozen causal preparation; no clipping or meter-sensitivity filtering'))
 pd.DataFrame(quality).to_csv(OUT/'target_diagnostics.csv',index=False)
 # Keep the original matrix immutable: publish a completion overlay.
 matrix=csv(SMART/'outputs/amendment005/support_design_v1/experiment_matrix.csv')
 matrix['original_status']=matrix.status
 take=(matrix.dataset=='pleia_energy')&(matrix.horizon==1)&(matrix.outer_fold==0)&(matrix.model_seed==42)&matrix.model.isin(cfg['models'])
 assert int(take.sum())==6
 matrix.loc[take,'status']='completed_verified_energy_h1_v1'
 matrix.loc[take,'preserved_path']='outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1'
 matrix.loc[take,'reason']='independent 3-point/6-level audit and saved-model reproduction; explicit zero-fit resume'
 matrix.to_csv(OUT/'completion_overlay.csv',index=False)
 core=matrix[matrix.model.isin(cfg['models'])];done=core[core.status.str.startswith('completed')]
 assert len(done)==24 and len(done.drop_duplicates(['dataset','horizon','outer_fold','model_seed','model']))==12
 remaining=csv(SMART/'outputs/amendment005/study_plan_v1/forecast_execution_queue.csv')
 remaining=remaining[~((remaining.dataset=='pleia_energy')&(remaining.horizon==1)&(remaining.outer_fold==0)&(remaining.model_seed==42))].copy()
 assert len(remaining)==191
 refs=csv(SMART/'outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913/point_summary.csv')
 reference=list(refs.groupby('horizon')[['tuning_seconds','final_fit_seconds','calibration_seconds','inference_seconds']].sum().sum(axis=1))
 reference.append(float(modelcost.model_phase_seconds.sum()))
 fitrows=core[core.model=='xgboost'].drop_duplicates(['dataset','horizon','outer_fold','model_seed'])
 remaining=remaining.merge(fitrows[['dataset','horizon','outer_fold','model_seed','fit_n']],on=['dataset','horizon','outer_fold','model_seed'],validate='one_to_one')
 remaining['original_priority']=remaining.priority;remaining['priority']=np.arange(1,192)
 remaining['updated_low_model_seconds']=.5*min(reference)*remaining.fit_n/29719
 remaining['updated_high_model_seconds']=3*max(reference)*remaining.fit_n/29719
 remaining['estimate_basis']='four measured matched units (3 temperature horizons + energy h1), min/max model-phase sum x fit-row ratio x [0.5,3]; excludes prep/I/O/audit'
 remaining['command_exists']=True
 remaining['prerequisite']='new scoped authorization, dataset-unit freeze and readiness; generalized runner exists; no further run authorized now'
 remaining.to_csv(OUT/'remaining_queue_updated.csv',index=False)
 summary=dict(completed_paired_units=4,total_paired_units=195,completed_core_point_cells=12,total_core_point_cells=585,
  completed_core_interval_cells=24,total_core_interval_cells=1170,remaining_paired_units=191,remaining_core_point_cells=573,
  remaining_core_interval_cells=1146,remaining_learned_fits=1910,remaining_queue_launched=False,
  planning_low_model_hours=float(remaining.updated_low_model_seconds.sum()/3600),
  planning_high_model_hours=float(remaining.updated_high_model_seconds.sum()/3600),planning_is_not_eta=True,
  next_unit=remaining.iloc[0][['dataset','horizon','outer_fold','model_seed','fit_n','updated_low_model_seconds','updated_high_model_seconds']].to_dict(),
  seasonal_and_broader_methods_excluded_from_core_counts=True,full_study_ready=False)
 (OUT/'completion_summary.json').write_text(json.dumps(summary,indent=2,default=lambda v:v.item())+'\n')
 commands=[]
 paths=list((BASE/'validation').glob('*.log.json'))+[Path(str(RUN)+'.log.json')]
 for file in sorted(paths):
  item=load(file);name=file.name
  category='real unit' if file==Path(str(RUN)+'.log.json') else 'tiny integration/regression' if name.startswith('regression_smoke') else 'no-fit verification/preparation'
  commands.append(dict(log=file.relative_to(ROOT).as_posix(),category=category,command=json.dumps(item['command']),
      started_utc=item['started_utc'],ended_utc=item['ended_utc'],seconds=item['seconds'],exit_status=item['exit_status'],
      learned_fits=10 if category in ['real unit','tiny integration/regression'] else 0))
 pd.DataFrame(commands).to_csv(OUT/'command_measurements.csv',index=False)
 preparation=env['preparation_resources'];io_records=[]
 for file in RUN.glob('checkpoint_io_*.json'):io_records.extend(load(file))
 pd.DataFrame(io_records).to_csv(OUT/'checkpoint_io_measurements.csv',index=False)
 role_table=pd.DataFrame([dict(role=k,**v) for k,v in protocol['support']['roles'].items()])
 role_table.to_csv(OUT/'role_dates_and_support.csv',index=False)
 p=points.set_index('model');delta=float(p.loc['attention_lstm','mae']-p.loc['xgboost','mae'])
 ratio=float(p.loc['attention_lstm','mae']/p.loc['xgboost','mae'])
 total=float(modelcost.model_phase_seconds.sum());resume_cost=load(BASE/'validation/energy_h1_resume_v1.log.json')['seconds']
 validate_cost=load(BASE/'validation/energy_h1_audit_v2.log.json')['seconds']
 text=f'''# PLEIA-energy matched horizon-1 report

14 September 2026 local time. **Completed: actual run exit 0; all three point and six interval cells independently verified.** This is the authorized block-B `dif_cons` energy target (kWh per ten-minute interval), horizon 1, outer fold 0, model seed 42. The run performed **eight tuning and two final learned fits**; persistence performed no learned fitting. No remaining queue or conditional challenge was launched.

The evaluated implementation and frozen execution evidence were committed before the real run at `{env['code_commit']}`. Source SHA-256: `{audit['source_hash']}`. Protocol SHA-256: `{audit['protocol_hash']}`. The [evidence index](review/matched_energy_h1_20260913/EVIDENCE_INDEX.md) links source, full fitted checkpoints, CSVs, exact commands and validation. The original forecasting pilot, all BDG2 results/abstentions, amendment-005 proposal and original completion matrix are preserved.

## Matched numerical results

{table(comparison,['model','mae','rmse','coverage90','mpiw90','winkler90','coverage95','mpiw95','winkler95','model_phase_seconds'])}

MAE/RMSE, MPIW and Winkler are in the target's original kWh units; coverage is a proportion. `model_phase_seconds` sums tuning, final fitting (or persistence initialization), calibration and inference. It excludes preparation, artifact serialization/writes, validation, resume and process startup; nested fitting timers must not be added again.

On this single held-out block, Attention-LSTM minus XGBoost MAE is **{delta:.6g} kWh** (LSTM/XGBoost ratio **{ratio:.6g}**). This is a descriptive comparison for one target/horizon/fold/seed, not a completed multi-horizon superiority test or an independent prospective trial. Compare interval width together with empirical coverage and Winkler; nominal 90%/95% levels are not promises of achieved temporal or conditional coverage. No equivalence claim or formal multi-task test is made here.

## Candidate selection and interval ownership

{table(csv(AUDIT/'independent_selection.csv'),['model','selected_candidate','final_epochs','independently_verified'])}

Candidate IDs are zero-based. XGBoost retains exactly 400 trees and depth 3 (candidate 0) or 5 (candidate 1), learning rate .05, subsample/column fraction .8 and the frozen remaining parameters. The actual estimator is `xgboost.sklearn.XGBRegressor`, histogram trees, squared-error objective, seed 42 and `n_jobs=1`; each checkpoint includes actual wrapper parameters and booster configuration. None-valued wrapper defaults remain bound to the recorded library version rather than silently introducing a fallback estimator.

Attention-LSTM retains hidden size 64, dropout .2, sequence length 24, batch 256, learning rate .001 (candidate 0) or .0005 (candidate 1), maximum 30 epochs and patience 5. It uses the existing attention architecture, Adam/MSE training, training-only channel/target normalization and deterministic seed convention. Early improvement must exceed the preserved literal 1e-6 convention. Candidate selection minimizes the equally weighted mean of two inner validation MAEs, with exact ties following candidate order. Final epochs are the ceiling of the selected candidate's mean best inner epoch. Calibration/test outcomes select neither candidates nor epochs. Saved inner predictions and complete inner training histories independently verify these choices.

All three models use the same fitting/calibration/test target IDs and permitted causal source variables. They retain different feature representations: {len(protocol['support']['feature_names'])} flat features versus {len(protocol['support']['sequence_channels'])} sequence channels over 24 steps; this is not a claim of identical tensor representations or effective history lengths. `target_lag_0` remains available to persistence and the flat models. Exact feature/channel names and preprocessing configuration are frozen in the protocol.

Each model's own {len(csv(RUN/'units/pleia_energy_h1_f0_s42_persistence/calibration.csv.gz')):,} calibration absolute residuals determine its own symmetric interval. The one-based finite-sample ranks are `ceil((n+1)*level)`; there is no interpolated quantile, shared residual pool across models, adaptive recalibration or clipping. Both levels share their model fit. Saved calibration predictions are reproduced from each corresponding fitted artifact without fitting.

{table(csv(AUDIT/'recomputed_interval_metrics.csv'),['model','nominal_level','n_calibration','rank','q','coverage','mpiw','winkler'])}

## Original support and data-quality diagnostics

Data hash `{protocol['support']['data_hash']}` and role-bank hash `{protocol['support']['role_bank_hash']}` match the published no-fit proposal exactly. Membership includes one original energy series; its source group is Python `None`, with canonical CSV identity `None`. The original completed v1 streams serialized this as an empty field. The independently checked canonical streams restore the visible identifier while leaving every other column and all original checkpoint files unchanged. Eligible observed rows are {protocol['support']['eligible_rows']:,}; final fitting/calibration/test counts are **29,719 / 9,907 / 9,909**. All inner rows are confined to final fitting data, with strict target-before-next-origin purges.

{table(role_table,['role','n','target_min','target_max'])}

{table(pd.DataFrame(quality),['role','n','original_groups','zeros','negative_targets','minimum','maximum','adjacent_equal_targets'])}

Zero or repeated meter values are observations, not automatically labelled sensor failures. Source preprocessing/imputation and possible stalled/catch-up meter behaviour limit interpretation. This first unit keeps the original target and eligibility; the separately proposed keep/mask sensitivity analysis remains pending. There was no post-hoc removal of difficult periods, negative prediction clipping or interval truncation at zero.

{table(negative,['model','negative_point_predictions','minimum_point','negative_lower_90','minimum_lower_90','negative_lower_95','minimum_lower_95'])}

## Actual computational measurements

{table(modelcost,['model','tuning_seconds','final_fit_seconds','calibration_seconds','inference_seconds','process_cpu_seconds','baseline_rss_MiB','peak_rss_MiB','incremental_peak_rss_MiB'])}

The durable real command took **{run_command['seconds']:.3f} seconds**. Its lifetime process CPU was **{process['process_lifetime_cpu_seconds']:.3f} seconds**; the action's sampled peak RSS was **{process['action_resources']['peak_rss_bytes']/2**20:.3f} MiB**, and Windows' lifetime RSS high-water mark was **{process['ending_memory']['lifetime_peak_rss_bytes']/2**20:.3f} MiB**. Fresh run preparation took **{preparation['seconds']:.3f} seconds**, separately from the **{total:.3f} seconds** summed model phases. Atomic checkpoint writes took **{sum(r['seconds'] for r in io_records):.3f} seconds**; per-model artifact serialization is a separate phase in the detailed table. These nested/enclosing measurements must not be added indiscriminately.

The hardware was {env['hardware']['cpu']}; the fitted models ran on CPU, one numerical/Torch thread and `n_jobs=1`, training/inference batches 256. Memory was sampled every 50 ms, so sampled phase peaks can miss short transients; lifetime RSS is reported separately. All three actual launches met the original 3 GiB reference: **{bool(modelcost.original_3GiB_reference_met.all())}**. The later user instruction made that launch reference nonblocking, recorded in the new authorization; actual launch readings are published. The 256 MiB epoch floor and 8 GiB disk check were retained. No GPU cost or benefit is claimed.

Independent real-data audit and full saved-model prediction verification took **{validate_cost:.3f} command seconds**; completed zero-fit resume took **{resume_cost:.3f} command seconds**. These are excluded from model fit costs. Two separately preserved tiny integration versions used **20 synthetic learned fits total**, with reduced test-only architectures/candidates; their durations and the no-fit preparation/support commands, including one corrected checker failure, are in `command_measurements.csv`. They are not part of the ten real learned fits.

## Verification, completion overlay and next bounded proposal

All eight pre-fit regression checks passed. Both tiny integrations completed; their final saved-model predictions matched exactly. Two further no-fit CSV round-trip checks passed after identifying the Python-None serialization issue during the first real audit. Future exports now explicitly stringify group identifiers before writing, without altering prepared metadata, data/role hashes or any learned computation. The first audit's failure is retained. The corrected read-only audit uses the exact evaluated source archive and a separately hashed schema adapter, checks the original group against fresh metadata, and publishes canonical CSVs. This repair does **not invalidate the completed numerical results**, and no real learned fit was repeated. The updated export code requires a fresh source identity for future runs; it does not rewrite this completed run's protocol.

The real audit independently recalculated all point errors, absolute residuals, one-based ranks, bounds, coverage, MPIW, Winkler, selection and epochs. It checked training-only normalization and all common target IDs. Six saved-model checks (three models times calibration/test) passed at the predeclared absolute/relative tolerance 1e-7; exact observed discrepancies are published. All complete model payloads, metrics and run files remained unchanged during validation and completed resume. Source/configuration/data and checkpoint corruption rejection were covered by focused tests. The historical pilot passed read-only validation with zero refits. A second archive-based resume verifies that the published compatibility reader also performs zero fits; both resume costs are retained separately.

The [versioned completion overlay](smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/completion_overlay.csv) now has **4/195 paired units, 12/585 core point cells and 24/1,170 core interval cells completed**. **191 paired units / 573 point / 1,146 interval cells / 1,910 learned fits remain.** Seasonal and the broader interval-method/DSCP/robustness obligations remain separate and uncompleted; the original matrix/proposal was not edited.

The [updated queue](smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/remaining_queue_updated.csv) retains the original order after removing this completed unit. The unchanged planning factors [.5,3], applied to the range of four measured matched-unit model-phase totals and fitting-row ratios, give **{summary['planning_low_model_hours']:.2f}–{summary['planning_high_model_hours']:.2f} model-hours** across the remaining core queue. This is a scheduling scenario, not a wall-time ETA or statistical interval; it excludes preparation, I/O, audit, differing channel counts/epochs and memory contention. RICO/BDG2 learned-model costs remain unmeasured.

**Single next bounded proposal:** obtain separate authorization and freeze/run **RICO horizon 5 / outer fold 2 / model seed 42**, all retained runs under the published whole-run memberships, with the same three models and frozen two-candidate grids. Its preliminary scenario is **{summary['next_unit']['updated_low_model_seconds']:.1f}–{summary['next_unit']['updated_high_model_seconds']:.1f} model seconds**, to be replaced by actual measurement. No RICO, BDG2 queue unit or conditional challenge was launched. Full-study and scientific publication readiness remain **false**.
'''
 (ROOT/'PLEIA_ENERGY_MATCHED_H1_REPORT.md').write_bytes(text.encode('utf-8'))
 result=dict(passed=True,real_exit=0,point_cells=3,interval_cells=6,source_hash=audit['source_hash'],current_source_hash=source_digest(),
             run_command_seconds=run_command['seconds'],model_phase_seconds=total,completion=summary)
 (OUT/'report_validation.json').write_text(json.dumps(result,indent=2,default=lambda v:v.item())+'\n')
 print(json.dumps(result,indent=2,default=lambda v:v.item()))

if __name__=='__main__':main()
