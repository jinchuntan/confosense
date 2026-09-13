"""Derive alternative memberships, scope ledgers and a non-launching execution queue."""
import itertools,json,math,pickle,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];SMART=ROOT/'smart_building_conformal';sys.path.insert(0,str(SMART/'scripts'))
from support_design005 import SI,BASE,request_count,binomial_minimum,grouped_batch_folds,make_outer_folds,nested_roles,no_fitting,digest
OUT=SMART/'outputs/amendment005/study_plan_v1';AUDIT=SMART/'outputs/amendment005/support_design_v1'

def main():
 OUT.mkdir(parents=True,exist_ok=False);B=[]
 for ds in ['pleia','pleia_energy','rico']:
  with (Path('C:/Users/nigel/ConfoSenseBackups/amendment004_20260913/preflight_v1')/(ds+'_prepared.pkl')).open('rb') as f:c=pickle.load(f)
  m=c['w']['meta'];freq=c['prepared'].freq;scheme=SI.GROUPED if ds=='rico' else 'chronological'
  folds=grouped_batch_folds(m) if ds=='rico' else make_outer_folds(m,scheme,3,1,freq)
  for fi,f in enumerate(folds):
   blocks=SI.ordered_blocks(m,f['train'],[.25]*4 if ds=='rico' else [.1,.1,.4,.4],scheme)
   for inner in [0,1]:
    tr=blocks[0] if inner==0 else np.r_[blocks[0],blocks[1]];cal=blocks[1+inner];sel=blocks[2+inner]
    days=len(sel)*freq/pd.Timedelta('1D');q=request_count(days);duration=60 if ds=='rico' else 6
    target=binomial_minimum(1-.9**duration)
    B.append(dict(dataset=ds,outer_fold=fi,inner_fold=inner,train_n=len(tr),calibration_n=len(cal),selection_n=len(sel),
     selection_groups=m.iloc[sel].group_id.nunique(),selection_days=days,requests_per_catalogue=q,five_catalogue_count_bound=5*q,
     final_calibration_n=len(f['calibration']),train_cal_minimum_met=min(len(tr),len(cal))>=400,
     count_condition_met=5*q>=105,fixed_complete_rotation_catalogues=21*math.ceil(target/q) if q else None,
     selection_target_min=str(m.iloc[sel].target_time.min()),selection_target_max=str(m.iloc[sel].target_time.max()),
     selection_membership_hash=SI.membership_hash(m,sel),actual_event_support_verified=False))
 pd.DataFrame(B).to_csv(OUT/'alternative_B_larger_blocks.csv',index=False)
 contexts=pd.read_csv(AUDIT/'challenge_contexts.csv',keep_default_na=False);events=pd.read_csv(AUDIT/'challenge_schedules.csv.gz',keep_default_na=False)
 aliases=events.groupby(['dataset','outer_fold','role','family','severity']).apply(lambda x:pd.Series(dict(
  variant_rows=len(x),unique_context_realisations=len(x.drop_duplicates(['context_id','mask_hash','observed_hash'])),
  alias_rows=len(x)-len(x.drop_duplicates(['context_id','mask_hash','observed_hash'])))),include_groups=False).reset_index()
 aliases.to_csv(OUT/'challenge_aliases.csv',index=False)
 units=[];prec=[]
 for keys,ctx in contexts.groupby(['dataset','outer_fold','role'],sort=False):
  ds,fi,role=keys;ctx=ctx.sort_values(['segment_id','onset']);unit_count=0
  for sid,part in ctx.groupby('segment_id',sort=False):
   for j,c in enumerate(part.to_dict('records')):
    unit=str(c['group_id']) if ds=='rico' else sid+':week'+str(j//7)
    units.append(dict(dataset=ds,outer_fold=fi,role=role,context_id=c['context_id'],resampling_unit=unit,
      complete_unit=True if ds=='rico' else (j//7+1)*7<=len(part)))
   unit_count+=len(part) if ds=='rico' else len(part)//7
  prec.append(dict(dataset=ds,outer_fold=fi,role=role,contexts=len(ctx),complete_original_inference_blocks=unit_count,
    minimum_five_blocks_met=unit_count>=5,precision_measured=False,
    iid_bernoulli_n_for_10pp_95_halfwidth_heuristic=math.ceil(1.96**2/(4*.1**2))))
 pd.DataFrame(units).to_csv(OUT/'challenge_inference_units.csv',index=False);pd.DataFrame(prec).to_csv(OUT/'challenge_precision_support.csv',index=False)
 groups=pd.read_csv(AUDIT/'original_groups.csv');rg=groups[groups.dataset=='rico'].copy()
 old=pd.read_csv(BASE/'rico_membership.csv.gz');new=pd.read_csv(AUDIT/'rico_operational_membership_observations.csv.gz')
 for fi in range(3):
  prior=old[old.outer_fold==fi].groupby('group_id').roles.first().to_dict();now=new.groupby('group_id')[f'fold{fi}_roles'].first().to_dict()
  rg[f'legacy_fold{fi}_roles']=rg.group_id.map(prior);rg[f'proposal_fold{fi}_roles']=rg.group_id.map(now)
 rg.to_csv(OUT/'rico_run_history.csv',index=False)
 phases=[]
 for fi in range(3):
  for role in ['final_fit','final_calibration','inner0_selection','inner1_selection','outer_test']:
   part=rg[rg[f'proposal_fold{fi}_roles'].fillna('').str.split('|').apply(lambda x:role in x)]
   for phase,g in part.groupby('phase'):
    phases.append(dict(outer_fold=fi,role=role,phase=phase,runs=len(g),raw_rows=g.raw_rows.sum(),start=g.start.min(),end=g.end.max(),
     ever_legacy_final_fit=int(g[[f'legacy_fold{j}_roles' for j in range(3)]].fillna('').apply(lambda r:any('final_fit' in s.split('|') for s in r),axis=1).sum()),
     ever_legacy_final_calibration=int(g[[f'legacy_fold{j}_roles' for j in range(3)]].fillna('').apply(lambda r:any('final_calibration' in s.split('|') for s in r),axis=1).sum())))
 pd.DataFrame(phases).to_csv(OUT/'rico_phase_distribution.csv',index=False)
 matrix=pd.read_csv(AUDIT/'experiment_matrix.csv');points=matrix.drop_duplicates(['dataset','horizon','outer_fold','model_seed','model'])
 points.groupby(['dataset','model','status']).agg(point_cells=('horizon','size'),tuning_fits=('tuning_fits','sum'),final_fits=('final_fits','sum')).reset_index().to_csv(OUT/'completion_counts.csv',index=False)
 config=json.loads((SMART/'configs/model_comparison_pilot_v1.json').read_text())
 nextrow=matrix[(matrix.dataset=='pleia_energy')&(matrix.horizon==1)&(matrix.outer_fold==0)&(matrix.model_seed==42)].iloc[0]
 nextconfig=dict(version='matched_forecasting005_first_unit_proposal',dataset='pleia_energy',horizon=1,outer_fold=0,model_seed=42,
   models=['persistence','xgboost','attention_lstm'],nominal_levels=[.9,.95],candidates=config['candidates'],
   sequence_length=24,batch_size=256,threads=1,n_jobs=1,interval_construction=config['interval_construction'],
   inner_validation_folds=2,selection_metric=config['selection_metric'],tie_rule=config['tie_rule'],final_lstm_epochs=config['final_lstm_epochs'],
   role_bank_hash=nextrow.role_bank_hash,data_hash=nextrow.data_hash,fit_n=int(nextrow.fit_n),calibration_n=int(nextrow.calibration_n),test_n=int(nextrow.test_n),
   expected_point_cells=3,expected_interval_cells=6,tuning_fits=8,final_learned_fits=2,
   generic_entrypoint='src.matched_forecasting005',entrypoint_exists=(SMART/'src/matched_forecasting005.py').exists(),
   minimum_launch_available_ram_bytes=3*2**30,minimum_free_disk_bytes=8*2**30,
   epoch_guard_bytes=config['minimum_epoch_available_ram_bytes'],future_fitting_authorized=False)
 (OUT/'next_forecast_unit.json').write_text(json.dumps(nextconfig,indent=2)+'\n')
 costs=pd.read_csv(SMART/'outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913/point_summary.csv')
 cs=costs.groupby('horizon')[['tuning_seconds','final_fit_seconds','calibration_seconds','inference_seconds']].sum().sum(axis=1)
 queue=[];units=points[(points.model=='xgboost')&(points.status=='required_new')].copy()
 def order(r):
  priority=0 if (r.dataset,r.horizon,r.outer_fold,r.model_seed)==('pleia_energy',1,0,42) else 1 if (r.dataset,r.horizon,r.outer_fold,r.model_seed)==('rico',5,2,42) else 2 if (r.dataset,r.horizon,r.outer_fold,r.model_seed)==('bdg2',1,2,42) else 3
  return priority,['pleia_energy','rico','bdg2','pleia'].index(r.dataset),r.model_seed,-r.outer_fold,r.horizon
 for pos,r in enumerate(sorted(units.itertuples(index=False),key=order),1):
  out=f'outputs/matched_forecasting005/{r.dataset}_h{r.horizon}_f{r.outer_fold}_s{r.model_seed}_v1'
  argv=['C:/cfs_venv/Scripts/python.exe','-B','-m','src.matched_forecasting005','run','--matrix','outputs/amendment005/support_design_v1/experiment_matrix.csv',
    '--dataset',r.dataset,'--horizon',str(r.horizon),'--outer-fold',str(r.outer_fold),'--model-seed',str(r.model_seed),'--out',out]
  ratio=r.fit_n/29719
  queue.append(dict(priority=pos,dataset=r.dataset,horizon=r.horizon,outer_fold=r.outer_fold,model_seed=r.model_seed,
    models='persistence|xgboost|attention_lstm',argv=json.dumps(argv),output=out,command_exists=False,
    prerequisite='implement and verify matched_forecasting005; explicit fitting authorization; per-unit resource guard',
    learned_fit_invocations=10,scenario_low_model_seconds=float(cs.min()*.5*ratio),scenario_high_model_seconds=float(cs.max()*3*ratio),
    estimate_basis='PLEIA measured 3-model phase min/max times x fitting-row ratio x [0.5,3]; excludes preparation/I/O; not an ETA'))
 pd.DataFrame(queue).to_csv(OUT/'forecast_execution_queue.csv',index=False)
 seasonal=points[(points.model=='seasonal_naive')&(points.status=='required_new')].drop_duplicates(['dataset','horizon','outer_fold'])
 seasonal[['dataset','horizon','outer_fold','calibration_n','test_n']].assign(model_seed_aliases='42|43|44|45|46',learned_fits=0).to_csv(OUT/'seasonal_execution_queue.csv',index=False)
 methods=[]
 for ds,h,fi,seed,level,method in itertools.product(['pleia','pleia_energy','rico','bdg2'],[1],range(3),range(42,47),[.9,.95],['quantile_uncalibrated','cqr','recentred_enbpi_static','recentred_enbpi_updated','dscp']):
  for hz in sorted(matrix[matrix.dataset==ds].horizon.unique()):
   methods.append(dict(dataset=ds,horizon=int(hz),outer_fold=fi,model_seed=seed,level=level,method=method,status='required_new_versioned_evidence',
    owner='shared CQR quantile fit' if method in ['quantile_uncalibrated','cqr'] else 'shared static/updated EnbPI fit' if method.startswith('recentred') else 'matched XGBoost predictions plus joint-horizon DSCP calibrator',
    prerequisite='joint-origin adapter for all declared horizons' if method=='dscp' else 'method-comparison runner with own-model streams and owner/sub-estimator ledger'))
 pd.DataFrame(methods).to_csv(OUT/'interval_method_matrix.csv',index=False)
 scope=[
  ('matched_forecasting','required','195 paired units; 585 core point/1170 level cells; 18 levels reused, 1152 pending; 1920 new learned fits','panel LSTM versus XGBoost and own-model intervals'),
  ('seasonal','required','135 point/270 level cells on nine applicable task/horizons; 27 unique deterministic runs with five seed aliases; RICO60 point/120 levels inapplicable','daily history unavailable inside four-hour runs'),
  ('interval_methods','required','1950 level/horizon cells; shared estimator ownership; DSCP joint horizon adapter; no existing operational cell substituted','full declared method scope'),
  ('operational_BDG2','required_for_full_grid_claim','three seed42 reduced-grid units complete; full264-candidate five-seed scope unexecuted','abstentions preserved; no rolling diagnostic promoted'),
  ('operational_PLEIA_RICO','original_question_not_estimable_under_A','A retained as support-limited replay; proposed C conditional challenge separately evaluated','explicit question change, not evidence of four-task deployment feasibility'),
  ('robustness_contamination_recovery','required_for_existing_claims','60 legacy units x15 cells=900 remain historical/unexecuted under current valid design; requires005crosswalk and serialized owners','retain zero controls, calibration-only contamination, closed-loop cascades and censored recovery; no automatic launch'),
  ('inference','required','original-unit paired metrics, five seed contributions aggregated; no IID rows/catalogues; unavailable CIs preserved','post-inspection historic-period evidence'),
  ('PLEIA_energy_meter_sensitivity','required_sensitivity','keep primary meter values; separately version keep/mask stalled/zero/catch-up periods','do not silently clean'),
  ('unseen_building_portability','optional_unless_claimed','separate held-building design and resources; not supported by ten recurring buildings','no current portability claim'),
  ('additional_model_seeds','optional_beyond42to46','not in authorized scope','five declared model seeds remain required; no best-seed selection')]
 pd.DataFrame(scope,columns=['scope','obligation','exact_status','rationale']).to_csv(OUT/'scope_ledger.csv',index=False)
 result=dict(passed=True,models_fitted=0,remaining_core_paired_units=len(queue),remaining_core_learned_fits=10*len(queue),
   seasonal_unique_runs=len(seasonal),method_level_cells=len(methods),entrypoint_exists=nextconfig['entrypoint_exists'],
   next_run_authorized=False,full_study_ready=False,publication_ready=False)
 (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
 with no_fitting():main()
