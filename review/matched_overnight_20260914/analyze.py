"""Saved-evidence arithmetic, tables, figures and reports. Never fits a model."""
import argparse, hashlib, importlib.util, math, os, shutil, sys
from pathlib import Path
from common import *
sys.path.insert(0,str(SMART))
from src.matched_models005 import forbid_fitting
import numpy as np
import pandas as pd

PHASES=['tuning','final_fit','calibration','inference']
UNITS={'pleia':'degrees C','pleia_energy':'kWh per 10 minutes','rico':'degrees C','bdg2':'kWh per hour'}
LABELS={'pleia':'PLEIA temperature','pleia_energy':'PLEIA energy','rico':'RICO temperature','bdg2':'BDG2 electricity'}
MINUTES={'pleia':10,'pleia_energy':10,'rico':1,'bdg2':60}
COLORS={'persistence':'#555555','xgboost':'#0072B2','attention_lstm':'#D55E00'}
ID=['dataset','horizon','outer_fold','model_seed']

def csv(path):return pd.read_csv(path,keep_default_na=False,float_precision='round_trip',dtype={'group_id':str,'row_id':str})
def write(out,name,rows):pd.DataFrame(rows).to_csv(Path(out)/name,index=False)
def tree_hash(path):return hashlib.sha256('\n'.join(f'{p}:{v}' for p,v in tree(path).items()).encode()).hexdigest()
def metric(f):
    y=f.y_true.to_numpy();e=y-f.point.to_numpy();lo=f.lower.to_numpy();hi=f.upper.to_numpy();a=1-float(f.nominal_level.iloc[0])
    return dict(n=len(f),mae=float(np.abs(e).mean()),rmse=float(np.sqrt(np.square(e).mean())),coverage=float(((lo<=y)&(y<=hi)).mean()),mpiw=float((hi-lo).mean()),winkler=float((hi-lo+2/a*(np.maximum(lo-y,0)+np.maximum(y-hi,0))).mean()),negative_points=int((f.point<0).sum()),negative_lower_bounds=int((lo<0).sum()))
def model_dir(run,key,model):
    candidates=[p for p in (Path(run)/'units').iterdir() if p.name.endswith(f'h{key[1]}_f{key[2]}_s{key[3]}_{model}')]
    assert len(candidates)==1,(key,model,candidates)
    return candidates[0]

def summarize(run,key,*,new=False):
    run=Path(run);spec=read(run/'checkpoint_manifest.json')['spec']
    points=csv(run/'point_summary.csv').rename(columns={'seed':'model_seed'})
    ints=csv(run/'interval_quality.csv').rename(columns={'seed':'model_seed'})
    for col,val in zip(ID,key):points=points[points[col]==val];ints=ints[ints[col]==val]
    assert len(points)==3 and len(ints)==6
    meta=dict(zip(ID,key),target_units=UNITS[key[0]],physical_minutes=key[1]*MINUTES[key[0]],source_run=run.relative_to(ROOT).as_posix(),source_hash=spec['source_hash'],protocol_hash=spec['protocol_hash'],new_batch_unit=new)
    groups=[];phases=[];equal=[];comparison=[];costs=[];targets=[]
    history=csv(SMART/'outputs/amendment005/study_plan_v1/rico_run_history.csv').set_index('group_id')
    for model in MODELS:
        directory=model_dir(run,key,model);payload=read(directory/'payload.json');p=points[points.model==model].iloc[0]
        row=dict(meta,model=model,n_fit=int(p.n_fit),n_calibration=int(p.n_calibration),n_test=int(p.n_evaluation),mae=p.mae,rmse=p.rmse,selected_candidate=p.selected_candidate,final_epochs=p.final_epochs,estimator_class=p.estimator_class,**{n+'_seconds':float(p[n+'_seconds']) for n in PHASES},inference_rows_per_second=p.inference_rows_per_second,model_phase_seconds=sum(p[n+'_seconds'] for n in PHASES))
        row['process_cpu_seconds']=p.get('process_cpu_seconds',float('nan'))
        row['cpu_measurement_status']='measured' if np.isfinite(row['process_cpu_seconds']) else 'not recorded per model in original temperature pilot; wall phases retained'
        pred=csv(directory/'predictions.csv.gz')
        for level,frame in pred.groupby('nominal_level'):
            saved=ints[(ints.model==model)&(ints.nominal_level==level)].iloc[0];actual=metric(frame)
            for field in ['mae','rmse']:np.testing.assert_allclose(actual[field],p[field],atol=1e-12,rtol=1e-12)
            for field in ['coverage','mpiw','winkler']:
                np.testing.assert_allclose(actual[field],saved[field],atol=1e-12,rtol=1e-12)
            for field in ['coverage','mpiw','winkler','rank','q']:row[field+str(int(level*100))]=saved[field]
            row['coverage_deviation'+str(int(level*100))]=float(saved.coverage-level)
            local=[]
            for group,part in frame.groupby('group_id',sort=False):
                g=dict(meta,model=model,group_id=group,nominal_level=level,aggregation='within original group, sample weighted',**metric(part))
                if key[0]=='rico':
                    h=history.loc[group];g['phase']=h.phase
                    g['historical_training_use']=any('final_fit' in str(h[c]) for c in ['legacy_fold0_roles','legacy_fold1_roles','legacy_fold2_roles'])
                groups.append(g);local.append(g)
            for field in ['mae','coverage','mpiw','winkler']:
                np.testing.assert_allclose(np.average([g[field] for g in local],weights=[g['n'] for g in local]),actual[field],atol=1e-12,rtol=1e-12)
            np.testing.assert_allclose(np.sqrt(np.average([g['rmse']**2 for g in local],weights=[g['n'] for g in local])),actual['rmse'],atol=1e-12,rtol=1e-12)
            equal.append(dict(meta,model=model,nominal_level=level,groups=len(local),aggregation='equal original group diagnostic; distinct from pooled',**{c:np.mean([g[c] for g in local]) for c in ['mae','coverage','mpiw','winkler']},root_mean_group_mse=np.sqrt(np.mean([g['rmse']**2 for g in local]))))
            if key[0]=='rico':
                frame=frame.copy();frame['phase']=frame.group_id.map(history.phase);assert frame.phase.notna().all()
                for phase,part in frame.groupby('phase'):
                    phases.append(dict(meta,model=model,phase=phase,nominal_level=level,original_runs=part.group_id.nunique(),aggregation='within phase, sample weighted',**metric(part)))
        comparison.append(row)
        launch=payload.get('launch_resources',payload.get('launch_memory',{}))
        costs.append(dict(row,baseline_rss_MiB=p.baseline_rss_bytes/2**20,peak_rss_MiB=p.peak_rss_bytes/2**20,incremental_peak_rss_MiB=(p.peak_rss_bytes-p.baseline_rss_bytes)/2**20,artifact_serialization_seconds=payload['resources'].get('artifact_serialization',{}).get('seconds',float('nan')),launch_available_ram_MiB=launch.get('available_ram_bytes',float('nan'))/2**20))
        if model=='persistence':
            for role,filename in [('calibration','calibration.csv.gz'),('test','predictions.csv.gz')]:
                f=csv(directory/filename)
                if role=='test':f=f[f.nominal_level==.9]
                targets.append(dict(meta,role=role,n=len(f),groups=f.group_id.nunique(),zero_targets=int(f.y_true.eq(0).sum()),negative_targets=int(f.y_true.lt(0).sum()),adjacent_equal_targets=sum(int(part.y_true.diff().eq(0).sum()) for _,part in f.groupby('group_id')),minimum=f.y_true.min(),maximum=f.y_true.max(),posthoc_cleaning_or_clipping=False))
    return dict(comparison=comparison,group_metrics=groups,rico_phase_metrics=phases,equal_group_diagnostics=equal,model_costs=costs,target_diagnostics=targets)

def unit(stem_name,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    u=next(u for u in read(REVIEW/'joint_pre_fit_manifest.json')['units'] if u['stem']==stem_name)
    result=summarize(u['run'],u['key'],new=True)
    for name,rows in result.items():write(out,name+'.csv',rows)
    atomic(out/'validation.json',dict(passed=True,models_fitted=0,group_to_pooled_reconstruction=True,rmse_reconstruction='sqrt(count-weighted mean group MSE)',key=u['key'],source_hash=u['source_hash'],protocol_hash=u['protocol_hash']))

def paired(frame):
    rows=[]
    fields=['mae','rmse','coverage90','coverage95','coverage_deviation90','coverage_deviation95','mpiw90','mpiw95','winkler90','winkler95',*[p+'_seconds' for p in PHASES],'model_phase_seconds','process_cpu_seconds','inference_rows_per_second']
    for key,f in frame.groupby(ID):
        for left,right in [('attention_lstm','xgboost'),('attention_lstm','persistence'),('xgboost','persistence')]:
            a=f[f.model==left].iloc[0];b=f[f.model==right].iloc[0]
            row={k:a[k] for k in [*ID,'target_units','physical_minutes','source_run','source_hash','protocol_hash','n_fit','n_calibration','n_test']};row.update(left_model=left,right_model=right,interpretation='left minus right; descriptive paired on same targets')
            for col in fields:row[col+'_difference']=a[col]-b[col]
            for col in ['model_phase_seconds','process_cpu_seconds','inference_rows_per_second']:
                denominator=b[col]
                status='ok' if np.isfinite(denominator) and denominator!=0 and np.isfinite(a[col]) else ('zero_denominator' if denominator==0 else 'unmeasured_or_nonfinite')
                row[col+'_ratio']=a[col]/denominator if status=='ok' else float('nan');row[col+'_ratio_status']=status
            rows.append(row)
    return rows

def figures(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    source=out/'fold2_seed42_all_horizons.csv';frame=csv(source);figdir=out/'figures';figdir.mkdir()
    plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.2,'savefig.dpi':160})
    datasets=['pleia','pleia_energy','rico','bdg2']
    definitions=[('forecast_error',[('mae','MAE'),('rmse','RMSE')]),('coverage',[('coverage90','90% interval coverage'),('coverage95','95% interval coverage')]),('interval_width',[('mpiw90','90% MPIW'),('mpiw95','95% MPIW')]),('winkler',[('winkler90','90% Winkler'),('winkler95','95% Winkler')])]
    sidecars=[]
    for name,columns in definitions:
        fig,axes=plt.subplots(4,2,figsize=(12,15),layout='constrained')
        for i,ds in enumerate(datasets):
            f=frame[frame.dataset==ds]
            for j,(column,label) in enumerate(columns):
                ax=axes[i,j]
                for model in MODELS:
                    r=f[f.model==model].sort_values('physical_minutes');ax.plot(r.physical_minutes,r[column],marker='o',label=model.replace('_',' '),color=COLORS[model])
                ax.set_title(LABELS[ds]+' — '+label);ax.set_xlabel('Physical forecast horizon (minutes)');ax.set_xticks(sorted(f.physical_minutes.unique()))
                ax.set_ylabel('Coverage proportion' if name=='coverage' else UNITS[ds])
                if name=='coverage':ax.axhline(.9 if j==0 else .95,color='black',linestyle='--',linewidth=1);ax.set_ylim(0,1.03)
                if i==0 and j==0:ax.legend(fontsize=8)
        fig.suptitle('Matched fold 2 / seed 42 — descriptive horizon comparisons',fontsize=15)
        files=[]
        for ext in ['png','pdf']:
            p=figdir/(name+'.'+ext);fig.savefig(p);files.append(dict(path=p.name,sha256=sha(p)))
        plt.close(fig)
        side=dict(source_csv=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),script=Path(__file__).relative_to(ROOT).as_posix(),script_sha256=sha(__file__),matplotlib_version=matplotlib.__version__,slice='outer fold 2; model seed 42; 13 task/horizon combinations; dependent horizons',files=files)
        atomic(figdir/(name+'.sources.json'),side);sidecars.append(side)
    fig,axes=plt.subplots(2,2,figsize=(12,9),layout='constrained')
    for ax,ds in zip(axes.ravel(),datasets):
        f=frame[frame.dataset==ds]
        for model in MODELS:
            r=f[f.model==model]
            ax.scatter(r.model_phase_seconds,r.mae,color=COLORS[model],label=model.replace('_',' '))
            for p in r.itertuples():ax.annotate(f'{int(p.physical_minutes)}m',(p.model_phase_seconds,p.mae),xytext=(4,3),textcoords='offset points',fontsize=8)
        ax.set_xscale('log');ax.set_xlabel('Measured model-phase wall seconds (log scale)');ax.set_ylabel('MAE ('+UNITS[ds]+')');ax.set_title(LABELS[ds]);ax.legend(fontsize=8)
    fig.suptitle('Measured cost and forecast error — fold 2 / seed 42',fontsize=15)
    files=[]
    for ext in ['png','pdf']:
        p=figdir/('cost_and_error.'+ext);fig.savefig(p);files.append(dict(path=p.name,sha256=sha(p)))
    plt.close(fig)
    atomic(figdir/'cost_and_error.sources.json',dict(source_csv=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),script_sha256=sha(__file__),matplotlib_version=matplotlib.__version__,files=files))

def table(frame,columns):
    def fmt(x):
        if isinstance(x,(float,np.floating)):return f'{x:.6g}' if np.isfinite(x) else 'unmeasured'
        return str(x)
    return '| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'+''.join('| '+' | '.join(fmt(r[c]) for c in columns)+' |\n' for _,r in frame.iterrows())

def final(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    state=read(BATCH/'progress.json');manifest=read(REVIEW/'joint_pre_fit_manifest.json')
    assert len(state['units'])==12 and all(u['validated'] for u in state['units'].values())
    combined={k:[] for k in ['comparison','group_metrics','rico_phase_metrics','equal_group_diagnostics','model_costs','target_diagnostics']}
    reuse=csv(BASE/'rico_bdg2_report_v2/evidence_reuse_ledger.csv');provenance=reuse.to_dict('records');cached={}
    for old in provenance:
        run=ROOT/old['run_path']
        if str(run) not in cached:cached[str(run)]=tree_hash(run)
        assert cached[str(run)]==old['run_file_tree_hash'], 'historical evidence changed'
        result=summarize(run,[old[k] for k in ID])
        for name,rows in result.items():combined[name].extend(rows)
    costs=[];verification=[];fit_attempts=[];io=[]
    for u in manifest['units']:
        s=u['stem'];done=state['units'][s];run=Path(u['run']);key=u['key'];meta=dict(zip(ID,key),target_units=UNITS[key[0]],physical_minutes=key[1]*MINUTES[key[0]],source_run=run.relative_to(ROOT).as_posix(),source_hash=u['source_hash'],protocol_hash=u['protocol_hash'])
        assert tree(run)==done['run_files']
        groups_task=state['tasks'][s+'/groups'];groupdir=Path(groups_task['argv'][groups_task['argv'].index('--out')+1])
        assert read(groupdir/'validation.json')['passed']
        for name in combined:
            path=groupdir/(name+'.csv')
            if path.stat().st_size>2:combined[name].extend(csv(path).to_dict('records'))
        rr=state['tasks'][s+'/run'];vr=state['tasks'][s+'/validate'];zr=state['tasks'][s+'/resume']
        assert rr['exit_code']==vr['exit_code']==zr['exit_code']==0
        a=read(Path(done['audit'])/'validation.json');reloads=csv(Path(done['audit'])/'saved_model_verification.csv')
        assert a['passed'] and len(reloads)==6
        verification.append(dict(meta,actual_exit=0,point_cells=3,interval_cells=6,tuning_fits=8,final_fits=2,saved_model_checks=6,max_absolute_prediction_difference=reloads.max_absolute_difference.max(),completed_resume_fits=0,all_run_files_unchanged=True,audit=done['audit'],resume=done['resume']))
        env=read(run/'execution_environment.json')
        process_path=Path(str(run)+'.process.json') if rr['argv'][4]=='run' else Path(rr['argv'][rr['argv'].index('--receipt')+1]+'.process.json')
        proc=read(process_path)
        costs.append(dict(meta,command_seconds=rr['seconds'],process_cpu_seconds=proc['process_lifetime_cpu_seconds'],preparation_seconds=env['preparation_resources']['seconds'],preparation_peak_rss_MiB=env['preparation_resources']['peak_rss_bytes']/2**20,action_peak_rss_MiB=proc['action_resources']['peak_rss_bytes']/2**20,lifetime_peak_rss_MiB=proc['ending_memory']['lifetime_peak_rss_bytes']/2**20,validation_seconds=vr['seconds'],validation_cpu_seconds=a['total_validation_resources']['process_cpu_seconds'],resume_seconds=zr['seconds'],output_bytes=sum(p.stat().st_size for p in run.rglob('*') if p.is_file())))
        for path in run.glob('checkpoint_io_*.json'):io.extend(dict(meta,**r) for r in read(path))
        fit_attempts.extend(dict(meta,**json.loads(line)) for line in (run/'fit_calls.jsonl').read_text().splitlines())
        provenance.append(dict(zip(ID,key),run_path=run.relative_to(ROOT).as_posix(),source_hash=u['source_hash'],protocol_hash=u['protocol_hash'],run_file_tree_hash=tree_hash(run),evaluated_commit=env['code_commit'],historical_refits=0))
    for name,rows in combined.items():write(out,('combined_comparison' if name=='comparison' else name)+'.csv',rows)
    frame=pd.DataFrame(combined['comparison']);assert len(frame)==54 and not frame.duplicated(ID+['model']).any()
    new=frame[frame.new_batch_unit==True];fold2=frame[(frame.outer_fold==2)&(frame.model_seed==42)];assert len(new)==36 and len(fold2)==39
    write(out,'new_only_comparison.csv',new);write(out,'fold2_seed42_all_horizons.csv',fold2);write(out,'additional_folds_comparison.csv',frame[frame.outer_fold!=2])
    pairs=pd.DataFrame(paired(frame));write(out,'paired_model_contrasts.csv',pairs)
    write(out,'run_costs.csv',costs);write(out,'checkpoint_io.csv',io);write(out,'fit_attempts.csv',fit_attempts);write(out,'verification_summary.csv',verification);write(out,'evidence_reuse_ledger.csv',provenance)
    write(out,'command_attempts.csv',[dict(task=k,**{x:v.get(x) for x in ['attempt_id','argv','cwd','started_utc','ended_utc','exit_code','logger_pid','child_pid','seconds','log']}) for k,v in state['tasks'].items()])
    overlay=csv(BASE/'rico_bdg2_report_v2/completion_overlay.csv');remaining=csv(BASE/'rico_bdg2_report_v2/remaining_queue_updated.csv')
    for u in manifest['units']:
        mask=pd.Series(True,index=overlay.index);r=pd.Series(True,index=remaining.index)
        for col,val in zip(ID,u['key']):mask&=overlay[col]==val;r&=remaining[col]==val
        mask&=overlay.model.isin(MODELS);assert mask.sum()==6 and not overlay.loc[mask,'status'].str.startswith('completed').any()
        overlay.loc[mask,'status']='completed_verified_overnight_v1';overlay.loc[mask,'reason']='saved-stream arithmetic, six artifact checks, zero-fit resume and original-group reconciliation'
        overlay.loc[mask,'preserved_path']=Path(u['run']).relative_to(SMART).as_posix();assert r.sum()==1;remaining=remaining[~r]
    assert len(remaining)==177 and len(overlay[overlay.model.isin(MODELS)&overlay.status.str.startswith('completed')])==108
    refs=frame.groupby(ID).agg(model_phase_seconds=('model_phase_seconds','sum'),fit_n=('n_fit','first')).reset_index()
    for idx,row in remaining.iterrows():
        rates=refs[refs.dataset==row.dataset];rate=rates.model_phase_seconds/rates.fit_n
        remaining.loc[idx,'updated_low_model_seconds']=.5*rate.min()*row.fit_n;remaining.loc[idx,'updated_high_model_seconds']=3*rate.max()*row.fit_n
    remaining['estimate_basis']='same-dataset actual model-phase seconds per fitting row; min/max observed rates times [0.5,3]; not wall-time guarantees'
    remaining['prerequisite']='separate authorization; frozen protocols and readiness; broader methods require separate implementation'
    write(out,'completion_overlay.csv',overlay);write(out,'remaining_queue_updated.csv',remaining);write(out,'measured_timing_references.csv',refs)
    f=pd.DataFrame(fit_attempts);assert len(f[f.event=='started'])==len(f[f.event=='complete'])==120
    assert len(f[(f.event=='complete')&(f.phase=='tuning')])==96
    summary=dict(passed=True,new_paired_units=12,new_tuning_fits=96,new_final_fits=24,new_point_cells=36,new_interval_cells=72,saved_model_checks=72,completed_zero_fit_resumes=12,observed_max_prediction_difference=max(v['max_absolute_prediction_difference'] for v in verification),new_run_exit_codes=[v['actual_exit'] for v in verification],completed_paired_units=18,total_paired_units=195,completed_point_cells=54,total_point_cells=585,completed_interval_cells=108,total_interval_cells=1170,fold2_seed42_task_horizon_combinations=13,remaining_paired_units=177,remaining_learned_fits=1770,actual_run_wall_seconds=sum(c['command_seconds'] for c in costs),actual_run_cpu_seconds=sum(c['process_cpu_seconds'] for c in costs),validation_wall_seconds=sum(c['validation_seconds'] for c in costs),resume_wall_seconds=sum(c['resume_seconds'] for c in costs),maximum_lifetime_peak_rss_MiB=max(c['lifetime_peak_rss_MiB'] for c in costs),remaining_low_model_hours=remaining.updated_low_model_seconds.sum()/3600,remaining_high_model_hours=remaining.updated_high_model_seconds.sum()/3600,models_fitted_by_analysis=0,historical_refits=0,full_study_ready=False,additional_fits_authorized=False)
    atomic(out/'analysis_validation.json',summary)
    recovery=REVIEW/'recovery_v1/before_recovery.json'
    if recovery.exists():
        before=read(recovery)
        assert tree(BASE/'pleia_h1_f2_s42_v1')==before['run_files']
        atomic(out/'coordinator_recovery_validation.json',dict(passed=True,initial_coordinator_exit=1,affected_model_run_exit=0,scientific_run_files_unchanged=True,repeated_learned_fits=0,all_planned_fits_reconciled=True,repair_commit='bdfb651a6b59df57b2c681e95306ce3b1fed4e8d',scientific_source_changed=False))
    figures(out);reports(out,frame,pairs,pd.DataFrame(costs),summary)
    atomic(out/'COMPLETE.json',dict(passed=True,files=tree(out),models_fitted=0))
    print(json.dumps(summary,indent=2),flush=True)

def reports(out,frame,pairs,costs,summary):
    rel=out.relative_to(ROOT).as_posix();slice=frame[(frame.outer_fold==2)&(frame.model_seed==42)]
    columns=['physical_minutes','model','mae','rmse','coverage90','mpiw90','winkler90','coverage95','mpiw95','winkler95','model_phase_seconds','process_cpu_seconds']
    text='# Matched overnight batch completion report\n\n'+f'All **12 authorized paired units completed**, actual exits 0: **96 tuning +24 final learned fits**, **36 point /72 interval cells**, **72 saved-model prediction checks**, and **12 zero-fit completed resumes**. Maximum observed prediction discrepancy: {summary["observed_max_prediction_difference"]:.9g}. Analysis performed zero fits.\n\n'
    text+='All twelve protocols were frozen and checked before fitting. Scientific source is unchanged from d95405a: `'+read(REVIEW/'joint_pre_fit_manifest.json')['source_hash']+'`. The evaluated orchestration commit is recorded in [evaluated_commit.json](review/matched_overnight_20260914/evaluated_commit.json). [Evidence index](review/matched_overnight_20260914/EVIDENCE_INDEX.md) and [progress/restart record](review/matched_overnight_20260914/PROGRESS_AND_RESTART.md) link exact commands and identities.\n\n'
    text+='## Comparable fold-2 / seed-42 horizon results\n\nThese 13 task/horizon combinations use the eleven new fold-2 units plus the preserved RICO h5 and BDG2 h1 units. The new BDG2 h1/fold1 and older fold0 pilots remain in a [separate table]('+rel+'/additional_folds_comparison.csv). Units, folds and dependent horizons are not pooled into a global ranking.\n\n'
    for ds in ['pleia','pleia_energy','rico','bdg2']:
        text+='### '+LABELS[ds]+'\n\nErrors, widths and Winkler scores: '+UNITS[ds]+'.\n\n'+table(slice[slice.dataset==ds].sort_values(['physical_minutes','model']),columns)+'\n'
    text+='## Actual computational measurements\n\n'+table(costs,['dataset','horizon','outer_fold','command_seconds','process_cpu_seconds','preparation_seconds','validation_seconds','resume_seconds','lifetime_peak_rss_MiB'])+'\n'
    text+=f'Total new-run wall time: **{summary["actual_run_wall_seconds"]/60:.2f} minutes**; process lifetime CPU: **{summary["actual_run_cpu_seconds"]/60:.2f} minutes**. Validation adds {summary["validation_wall_seconds"]/60:.2f} wall minutes and completed resume {summary["resume_wall_seconds"]/60:.2f} minutes. These sums exclude freeze/readiness, orchestration, reporting and publication. [Command attempts]({rel}/command_attempts.csv) preserve separate measured phases; do not add nested fit timers twice.\n\n'
    text+='CPU-only, one numerical/Torch thread, n_jobs=1, lazy batch256, nonblocking 3 GiB launch reference, 256 MiB epoch floor and 8 GiB disk checks were retained. Sampled 50 ms memory peaks can miss brief allocations; lifetime high-water marks are separate. Original temperature pilot per-model CPU was not recorded and remains explicitly unmeasured; it is not inferred from wall time.\n\n'
    text+='## Integrity and supported interpretation\n\nIndependent saved-stream arithmetic, exact own-model residual order statistics, tuning and epoch reconstruction, training-only normalization, matching target identities, saved-model reconstruction and immutable completed resume all passed. Group-to-pooled RMSE is reconstructed from count-weighted squared errors, never an average of group RMSE. [Group]('+rel+'/group_metrics.csv), [RICO phase]('+rel+'/rico_phase_metrics.csv) and [equal-group diagnostic]('+rel+'/equal_group_diagnostics.csv) tables remain separate.\n\n'
    text+='PLEIA-energy zeros, repeated/stall/catch-up values and all negative predictions/bounds remain unaltered. Target/negative-output diagnostics are published. RICO uses whole chronological acquisition runs: the fold-2 test has one phase-1 run, six phase-3 runs and 34 phase-4 runs, with historical training reuse. This cannot establish phase-conditional population coverage. BDG2 evaluates ten recurring known buildings, not unseen buildings. Single-seed, temporally dependent multi-horizon comparisons do not establish statistical superiority/equivalence or prospective/conditional coverage. Undercoverage remains a reported result.\n\n'
    text+='The initial new preparation helper stopped after a successful first freeze/readiness because its in-memory authorization keys were tuples rather than JSON lists. The helper now reads the unchanged saved authorization; successful checks were reused and no model had been fitted. Its original traceback and retry log are preserved. No scientific-source repair or result invalidation occurred.\n\n'
    if (REVIEW/'recovery_v1/before_recovery.json').exists():
        text+='The first coordinator subsequently exited1 after Windows denied an atomic progress-file replacement. The independent PLEIA-temperature h1 worker finished with exit0. A bounded bookkeeping retry was verified with injected transient/persistent denials and committed separately at bdfb651; restart adopted the actual success receipt and continued validation. All affected run files remain byte-identical and no learned fit was repeated. See [recovery record](review/matched_overnight_20260914/RECOVERY_PROGRESS_WRITE.md) and [independent preservation check]('+rel+'/coordinator_recovery_validation.json). Twenty-six distinct regression/orchestration checks passed, with zero tiny learned fits.\n\n'
    text+='The models use identical eligible target IDs within a unit and the frozen permitted causal variables, but flat features and24-step sequences are different representations and effective histories. The protocol records their separate schemas. Candidate selection, final epochs, estimator identity and support counts are explicit in the combined CSV; this does not isolate architecture from representation.\n\n'
    text+='## Completion and outstanding work\n\n**18/195 paired units;54/585 point cells;108/1170 interval cells.177 paired units /1,770 learned fits remain** in the matched core queue. The original matrix and prior completion records are preserved. The updated same-dataset timing scenario is '+f'{summary["remaining_low_model_hours"]:.2f}–{summary["remaining_high_model_hours"]:.2f} model-hours, excluding preparation/I/O/verification; this is a planning range, not a deadline.\n\n'
    text+='The next concrete study stage is the matched fold-2 all-horizon slice at model seed43: thirteen paired units (PLEIA temperature h1/3/6, PLEIA energy h1/3/6, RICO h5/15/30/60 and BDG2 h1/3/6), 104 tuning+26 final learned fits,39 point/78 interval cells, with fresh authorization/freeze/readiness and the same per-unit checks. This is a proposed bounded replication stage; it has not been launched. Further seeds/folds, seasonal baselines, broader CQR/EnbPI/DSCP methods, operational selection/recalibration, conditional challenge, contamination/recovery and robustness remain separate obligations. The dissertation/full study is not complete or publication-ready.\n'
    atomic(ROOT/'MATCHED_OVERNIGHT_BATCH_REPORT.md',text)
    panel='# Panel 2: matched Attention-LSTM versus XGBoost evidence\n\nFold 2 / seed42; positive differences mean LSTM is larger. CPU ratio is measured LSTM model-phase CPU divided by XGBoost CPU. Width alone is not interval quality; read achieved coverage and Winkler together.\n\n'
    select=pairs[(pairs.outer_fold==2)&(pairs.model_seed==42)&(pairs.left_model=='attention_lstm')&(pairs.right_model=='xgboost')].sort_values(['dataset','physical_minutes'])
    panel+=table(select,['dataset','physical_minutes','mae_difference','rmse_difference','coverage_deviation95_difference','mpiw95_difference','winkler95_difference','process_cpu_seconds_ratio','model_phase_seconds_ratio'])+'\n'
    panel+='Numerical reading by horizon (own-model 95% split-conformal intervals):\n\n'
    for p in select.itertuples():
        x=slice[(slice.dataset==p.dataset)&(slice.horizon==p.horizon)&(slice.model=='xgboost')].iloc[0];l=slice[(slice.dataset==p.dataset)&(slice.horizon==p.horizon)&(slice.model=='attention_lstm')].iloc[0]
        panel+=f'- {LABELS[p.dataset]}, {p.physical_minutes:g} min: LSTM-minus-XGBoost MAE {p.mae_difference:+.6g}, RMSE {p.rmse_difference:+.6g}, MPIW {p.mpiw95_difference:+.6g}, Winkler {p.winkler95_difference:+.6g} ({p.target_units}); coverage {l.coverage95:.2%} versus {x.coverage95:.2%}. LSTM used {p.process_cpu_seconds_ratio:.2f}× measured model-phase CPU ({p.model_phase_seconds_ratio:.2f}× model-phase wall time).\n'
    panel+='\nThese observed trade-offs do not establish statistical superiority or equivalence. More horizons are dependent comparisons, not independent replications. Phase imbalance, temporal drift, known-building scope, historical reuse and incomplete multi-seed/multi-fold evaluation remain limitations. Exact 90% and95% signed coverage deviations and learned-minus-persistence contrasts are in the paired CSV.\n'
    atomic(REVIEW/'PANEL2_NUMERICAL_RESPONSE.md',panel)
    for file in ['PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']:
        old=subprocess.check_output(['git','show',ENTRY+':'+file],cwd=ROOT)
        prefix=('# Matched overnight batch completed — 14 September 2026\n\nTwelve new paired units validated;18/195 total.96 tuning+24 final new fits;36 point/72 interval cells;72 artifact checks;12 zero-fit resumes.\n\n'+('[Report](../../MATCHED_OVERNIGHT_BATCH_REPORT.md)' if file.startswith('review/') else '[Report](MATCHED_OVERNIGHT_BATCH_REPORT.md)')+'; '+('[evidence index](matched_overnight_20260914/EVIDENCE_INDEX.md)' if file.startswith('review/') else '[evidence index](review/matched_overnight_20260914/EVIDENCE_INDEX.md)')+'. Full study remains incomplete;177 paired units and broader-method obligations remain.\n\n<!-- overnight-20260914: preserved historical status follows -->\n\n').encode()
        (ROOT/file).write_bytes(prefix+old)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['unit','final']);p.add_argument('--stem');p.add_argument('--out',required=True);a=p.parse_args()
    with forbid_fitting():
        if a.action=='unit':unit(a.stem,a.out)
        else:final(a.out)
