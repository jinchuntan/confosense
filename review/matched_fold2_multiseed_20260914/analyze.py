"""Seed-preserving saved-stream analysis; no fitting and no best-seed selection."""
import argparse, importlib.util, sys
from common import *
sys.path.insert(0,str(SMART))
from src.matched_models005 import forbid_fitting
import numpy as np
import pandas as pd
from seed_checks import unit as verify_seed

spec=importlib.util.spec_from_file_location('preserved_overnight_analysis',OLD_REVIEW/'analyze.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
csv=A.csv;write=A.write;ID=KEYCOLS;UNITS=A.UNITS;MINUTES=A.MINUTES;LABELS=A.LABELS;PHASES=A.PHASES

def baseline(key):
    ledger=csv(OLD_ANALYSIS/'evidence_reuse_ledger.csv')
    r=ledger[(ledger.dataset==key[0])&(ledger.horizon==key[1])&(ledger.outer_fold==2)&(ledger.model_seed==42)]
    assert len(r)==1
    return ROOT/r.iloc[0].run_path

def unit(stem_name,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    u=next(v for v in read(REVIEW/'joint_pre_fit_manifest.json')['units'] if v['stem']==stem_name)
    result=A.summarize(u['run'],u['key'],new=True)
    for name,rows in result.items():write(out,name+'.csv',rows)
    seeds=verify_seed(u);write(out,'actual_seed_metadata.csv',seeds)
    olddir=A.model_dir(baseline(u['key']),[*u['key'][:3],42],'persistence')
    newdir=A.model_dir(u['run'],u['key'],'persistence')
    for filename,columns in [('calibration.csv.gz',['row_id','group_id','origin_time','target_time','y_true','point','absolute_error']),('predictions.csv.gz',['row_id','group_id','origin_time','target_time','y_true','point','nominal_level','lower','upper'])]:
        pd.testing.assert_frame_equal(csv(olddir/filename)[columns],csv(newdir/filename)[columns],check_exact=True)
    atomic(out/'validation.json',dict(passed=True,models_fitted=0,group_to_pooled_reconstruction=True,rmse_reconstruction='sqrt(count-weighted mean group MSE)',actual_seed_verified=True,persistence_seed42_alias_exact=True,key=u['key'],source_hash=u['source_hash'],protocol_hash=u['protocol_hash']))

def add_deviations(frame):
    f=frame.copy()
    # Historical pilot CPU was unmeasured. CSV empty cells must remain NaN,
    # without coercing the measured values in that mixed column into strings.
    for column in FIELDS:
        if column in f:
            f[column]=pd.to_numeric(f[column],errors='coerce')
            if column!='process_cpu_seconds':assert np.isfinite(f[column]).all(),column
    for level in (90,95):
        f[f'signed_coverage_deviation{level}']=f[f'coverage{level}']-level/100
        f[f'absolute_coverage_deviation{level}']=f[f'signed_coverage_deviation{level}'].abs()
    f['deterministic_baseline_alias']=f.model.eq('persistence')
    return f

FIELDS=['mae','rmse',*[f'{metric}{level}' for level in (90,95) for metric in ('coverage','signed_coverage_deviation','absolute_coverage_deviation','mpiw','winkler')],*[p+'_seconds' for p in PHASES],'model_phase_seconds','process_cpu_seconds','inference_rows_per_second']

def paired(frame):
    rows=[]
    for key,f in frame.groupby(ID):
        for left,right in [('attention_lstm','xgboost'),('attention_lstm','persistence'),('xgboost','persistence')]:
            a=f[f.model==left].iloc[0];b=f[f.model==right].iloc[0]
            row={k:a[k] for k in [*ID,'physical_minutes','target_units','source_run','source_hash','protocol_hash','n_fit','n_calibration','n_test']}
            row.update(left_model=left,right_model=right,interpretation='left minus right within identical seed and target support')
            for field in FIELDS:row[field+'_difference']=a[field]-b[field]
            for field in ['model_phase_seconds','process_cpu_seconds','inference_rows_per_second']:
                valid=np.isfinite(a[field]) and np.isfinite(b[field]) and b[field]!=0
                row[field+'_ratio']=a[field]/b[field] if valid else np.nan
                row[field+'_ratio_status']='ok' if valid else 'zero_denominator' if b[field]==0 else 'unmeasured'
            rows.append(row)
    return pd.DataFrame(rows)

def variability(fold):
    rows=[]
    for key,f in fold.groupby(['dataset','horizon','outer_fold','model']):
        assert not f.model_seed.duplicated().any()
        r=f.iloc[0]
        for metric in FIELDS:
            a=pd.to_numeric(f[metric],errors='coerce').dropna()
            rows.append(dict(zip(['dataset','horizon','outer_fold','model'],key),physical_minutes=r.physical_minutes,target_units=r.target_units,metric=metric,nominal_level=.9 if metric.endswith('90') else .95 if metric.endswith('95') else None,source_runs='|'.join(f.sort_values('model_seed').source_run.astype(str)),protocol_hashes='|'.join(f.sort_values('model_seed').protocol_hash.astype(str)),n_fit=int(r.n_fit),n_calibration=int(r.n_calibration),n_test=int(r.n_test),model_seeds='|'.join(map(str,sorted(f.model_seed))),n_seed_rows=len(f),n_measured=len(a),mean=a.mean(),sample_std=a.std(ddof=1),minimum=a.min(),maximum=a.max(),interpretation='training-seed variability on same evaluation support; not a population confidence interval',deterministic_baseline_alias=key[3]=='persistence',independent_baseline_realizations=1 if key[3]=='persistence' else None))
    return pd.DataFrame(rows)

def figures(out,fold):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    dest=out/'figures';dest.mkdir();source=out/'fold2_five_seed_comparison.csv'
    plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.2,'savefig.dpi':160})
    definitions=[('forecast_error',[('mae','MAE'),('rmse','RMSE')]),('coverage',[('coverage90','90% coverage'),('coverage95','95% coverage')]),('interval_width',[('mpiw90','90% MPIW'),('mpiw95','95% MPIW')]),('winkler',[('winkler90','90% Winkler'),('winkler95','95% Winkler')])]
    def save(fig,name):
        files=[]
        for ext in ('png','pdf'):
            p=dest/f'{name}.{ext}';fig.savefig(p);files.append(dict(path=p.name,sha256=sha(p)))
        plt.close(fig)
        atomic(dest/f'{name}.sources.json',dict(source_csv=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),script=Path(__file__).relative_to(ROOT).as_posix(),script_sha256=sha(__file__),preserved_arithmetic_script_sha256=sha(OLD_REVIEW/'analyze.py'),matplotlib_version=matplotlib.__version__,meaning='thin lines are all individual training seeds; bold lines are means; same evaluation support, no population CI',files=files))
    for name,columns in definitions:
        fig,axes=plt.subplots(4,2,figsize=(12,15),layout='constrained')
        for i,ds in enumerate(['pleia','pleia_energy','rico','bdg2']):
            f=fold[fold.dataset==ds]
            for j,(metric,label) in enumerate(columns):
                ax=axes[i,j]
                for model in MODELS:
                    m=f[f.model==model]
                    for seed,s in m.groupby('model_seed'):
                        s=s.sort_values('physical_minutes');ax.plot(s.physical_minutes,s[metric],color=A.COLORS[model],alpha=.22,lw=1)
                    g=m.groupby('physical_minutes')[metric].mean();ax.plot(g.index,g.values,color=A.COLORS[model],marker='o',label=model.replace('_',' '),lw=2)
                ax.set_title(LABELS[ds]+' — '+label);ax.set_xlabel('Physical forecast horizon (minutes)');ax.set_xticks(sorted(f.physical_minutes.unique()));ax.set_ylabel('Coverage proportion' if name=='coverage' else UNITS[ds])
                if name=='coverage':ax.axhline(.9 if j==0 else .95,color='black',linestyle='--',lw=1);ax.set_ylim(0,1.03)
                if i==0 and j==0:ax.legend(fontsize=8)
        fig.suptitle('Fold 2: all training seeds and their mean on identical evaluation periods',fontsize=14);save(fig,name)
    fig,axes=plt.subplots(2,2,figsize=(12,9),layout='constrained')
    for ax,ds in zip(axes.ravel(),['pleia','pleia_energy','rico','bdg2']):
        f=fold[fold.dataset==ds]
        for model in MODELS:
            m=f[f.model==model];ax.scatter(m.model_phase_seconds,m.mae,color=A.COLORS[model],alpha=.4,s=18,label=model.replace('_',' '))
            for minutes,g in m.groupby('physical_minutes'):
                x=g.model_phase_seconds.mean();y=g.mae.mean();ax.scatter([x],[y],color=A.COLORS[model],marker='D',s=35);ax.annotate(f'{minutes:g}m',(x,y),xytext=(3,4),textcoords='offset points',fontsize=8)
        ax.set_xscale('log');ax.set_title(LABELS[ds]);ax.set_xlabel('Measured model-phase wall seconds (log scale)');ax.set_ylabel('MAE ('+UNITS[ds]+')');ax.legend(fontsize=8)
    fig.suptitle('Measured computation and forecast error: all seeds; diamonds are means');save(fig,'cost_and_error')

def aggregate(out,final=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    state=read(BATCH/'progress.json');manifest=read(REVIEW/'joint_pre_fit_manifest.json')
    units=[u for u in manifest['units'] if state['units'].get(u['stem'],{}).get('validated')];n=len(units)
    assert n in (13,26,39,52) and (not final or n==52)
    combined={}
    for name,file in [('comparison','combined_comparison.csv'),('group_metrics','group_metrics.csv'),('rico_phase_metrics','rico_phase_metrics.csv'),('equal_group_diagnostics','equal_group_diagnostics.csv'),('model_costs','model_costs.csv'),('target_diagnostics','target_diagnostics.csv')]:
        f=csv(OLD_ANALYSIS/file);f['new_batch_unit']=False;combined[name]=f.to_dict('records')
    provenance=csv(OLD_ANALYSIS/'evidence_reuse_ledger.csv').to_dict('records')
    for old in provenance:assert A.tree_hash(ROOT/old['run_path'])==old['run_file_tree_hash']
    costs=[];verification=[];fits=[];io=[];seeds=[]
    for u in units:
        s=u['stem'];done=state['units'][s];run=Path(u['run']);key=u['key'];meta=dict(zip(ID,key),target_units=UNITS[key[0]],physical_minutes=key[1]*MINUTES[key[0]],source_run=run.relative_to(ROOT).as_posix(),source_hash=u['source_hash'],protocol_hash=u['protocol_hash'])
        assert tree(run)==done['run_files']
        task=state['tasks'][s+'/groups'];directory=Path(task['argv'][task['argv'].index('--out')+1]);check=read(directory/'validation.json')
        assert check['passed'] and check['actual_seed_verified'] and check['persistence_seed42_alias_exact']
        for name in combined:
            path=directory/(name+'.csv')
            if path.stat().st_size>2:combined[name].extend(csv(path).to_dict('records'))
        seeds.extend(csv(directory/'actual_seed_metadata.csv').to_dict('records'))
        rr=state['tasks'][s+'/run'];vr=state['tasks'][s+'/validate'];zr=state['tasks'][s+'/resume']
        assert rr['exit_code']==vr['exit_code']==zr['exit_code']==0
        audit=read(Path(done['audit'])/'validation.json');reloads=csv(Path(done['audit'])/'saved_model_verification.csv')
        verification.append(dict(meta,actual_exit=rr['exit_code'],point_cells=3,interval_cells=6,tuning_fits=8,final_fits=2,saved_model_checks=len(reloads),max_absolute_prediction_difference=reloads.max_absolute_difference.max(),completed_resume_fits=0,all_run_files_unchanged=True,actual_seed_verified=True,audit=done['audit'],resume=done['resume']))
        env=read(run/'execution_environment.json');proc=read(str(run)+'.process.json')
        costs.append(dict(meta,command_seconds=rr['seconds'],process_cpu_seconds=proc['process_lifetime_cpu_seconds'],preparation_seconds=env['preparation_resources']['seconds'],preparation_peak_rss_MiB=env['preparation_resources']['peak_rss_bytes']/2**20,action_peak_rss_MiB=proc['action_resources']['peak_rss_bytes']/2**20,lifetime_peak_rss_MiB=proc['ending_memory']['lifetime_peak_rss_bytes']/2**20,validation_seconds=vr['seconds'],validation_cpu_seconds=audit['total_validation_resources']['process_cpu_seconds'],resume_seconds=zr['seconds'],output_bytes=sum(p.stat().st_size for p in run.rglob('*') if p.is_file())))
        for path in run.glob('checkpoint_io_*.json'):io.extend(dict(meta,**r) for r in read(path))
        fits.extend(dict(meta,**json.loads(line)) for line in (run/'fit_calls.jsonl').read_text().splitlines())
        provenance.append(dict(zip(ID,key),run_path=run.relative_to(ROOT).as_posix(),source_hash=u['source_hash'],protocol_hash=u['protocol_hash'],run_file_tree_hash=A.tree_hash(run),evaluated_commit=env['code_commit'],historical_refits=0))
    frame=add_deviations(pd.DataFrame(combined['comparison']));assert len(frame)==3*(18+n) and not frame.duplicated(ID+['model']).any()
    fold=frame[frame.outer_fold==2].copy();assert len(fold)==3*(13+n)
    assert set(fold.model_seed)==set(range(42,43+n//13))
    for name,rows in combined.items():
        if name!='comparison':write(out,name+'.csv',rows)
    write(out,'combined_comparison.csv',frame);write(out,'new_only_comparison.csv',frame[frame.new_batch_unit==True]);write(out,'fold2_five_seed_comparison.csv',fold);write(out,'additional_folds_comparison.csv',frame[frame.outer_fold!=2])
    intervals=[]
    for row in frame.to_dict('records'):
        for level in (90,95):intervals.append({**{k:row[k] for k in [*ID,'model','physical_minutes','target_units','source_run','source_hash','protocol_hash','n_calibration','n_test','deterministic_baseline_alias']},'nominal_level':level/100,**{metric:row[f'{metric}{level}'] for metric in ['coverage','signed_coverage_deviation','absolute_coverage_deviation','mpiw','winkler','q','rank']}})
    write(out,'interval_quality.csv',intervals)
    pair=paired(frame);write(out,'paired_model_contrasts.csv',pair);write(out,'training_seed_summary.csv',variability(fold))
    write(out,'run_costs.csv',costs);write(out,'checkpoint_io.csv',io);write(out,'fit_attempts.csv',fits);write(out,'verification_summary.csv',verification);write(out,'actual_seed_metadata.csv',seeds);write(out,'evidence_reuse_ledger.csv',provenance)
    write(out,'command_attempts.csv',[dict(task=k,**{x:v.get(x) for x in ['attempt_id','argv','cwd','started_utc','ended_utc','exit_code','logger_pid','child_pid','seconds','log']}) for k,v in state['tasks'].items()])
    seedcost=pd.DataFrame(costs).groupby('model_seed').agg(units=('dataset','size'),run_wall_seconds=('command_seconds','sum'),run_cpu_seconds=('process_cpu_seconds','sum'),validation_wall_seconds=('validation_seconds','sum'),resume_wall_seconds=('resume_seconds','sum'),peak_lifetime_rss_MiB=('lifetime_peak_rss_MiB','max')).reset_index()
    write(out,'seed_block_costs.csv',seedcost)
    oldcost=csv(OLD_ANALYSIS/'run_costs.csv');oldcost=oldcost[oldcost.outer_fold==2]
    first=csv(BASE/'rico_bdg2_report_v2/run_costs.csv');first['model_seed']=42;first['outer_fold']=2;first['horizon']=first.dataset.map({'rico':5,'bdg2':1})
    allcost=pd.concat([oldcost,first,pd.DataFrame(costs)],ignore_index=True);assert len(allcost)==13+n
    write(out,'fold2_all_seed_run_costs.csv',allcost)
    overlay=csv(OLD_ANALYSIS/'completion_overlay.csv');remaining=csv(QUEUE)
    for u in units:
        mask=pd.Series(True,index=overlay.index);r=pd.Series(True,index=remaining.index)
        for column,value in zip(ID,u['key']):mask&=overlay[column]==value;r&=remaining[column]==value
        mask&=overlay.model.isin(MODELS);assert mask.sum()==6 and not overlay.loc[mask,'status'].str.startswith('completed').any()
        overlay.loc[mask,'status']='completed_verified_fold2_multiseed_v1';overlay.loc[mask,'reason']='actual seed paths; independent metrics/artifacts; zero-fit resume; group arithmetic';overlay.loc[mask,'preserved_path']=Path(u['run']).relative_to(SMART).as_posix();assert r.sum()==1;remaining=remaining[~r]
    refs=frame.groupby(ID).agg(model_phase_seconds=('model_phase_seconds','sum'),fit_n=('n_fit','first')).reset_index()
    for idx,row in remaining.iterrows():
        rates=refs[refs.dataset==row.dataset];rate=rates.model_phase_seconds/rates.fit_n
        remaining.loc[idx,'updated_low_model_seconds']=.5*rate.min()*row.fit_n;remaining.loc[idx,'updated_high_model_seconds']=3*rate.max()*row.fit_n
    remaining['estimate_basis']='same-dataset observed model-phase seconds per fit row; min/max rates times 0.5/3; planning scenario, not a confidence interval or deadline'
    remaining['prerequisite']='separate authorization and fresh freeze/readiness; broader methods need their own adapter implementation'
    assert len(remaining)==177-n
    write(out,'completion_overlay.csv',overlay);write(out,'remaining_queue_updated.csv',remaining);write(out,'measured_timing_references.csv',refs)
    f=pd.DataFrame(fits);assert len(f[f.event=='started'])==len(f[f.event=='complete'])==10*n
    assert len(f[(f.event=='complete')&(f.phase=='tuning')])==8*n
    summary=dict(passed=True,status='complete' if final else 'provisional_seed_block',new_paired_units=n,new_tuning_fits=8*n,new_final_fits=2*n,new_point_cells=3*n,new_interval_cells=6*n,saved_model_checks=6*n,completed_zero_fit_resumes=n,actual_seed_checks=3*n,observed_max_prediction_difference=max(v['max_absolute_prediction_difference'] for v in verification),new_run_exit_codes=[v['actual_exit'] for v in verification],completed_paired_units=18+n,total_paired_units=195,completed_point_cells=3*(18+n),completed_interval_cells=6*(18+n),fold2_paired_units=13+n,fold2_point_cells=3*(13+n),fold2_interval_cells=6*(13+n),remaining_paired_units=177-n,remaining_learned_fits=10*(177-n),actual_run_wall_seconds=sum(c['command_seconds'] for c in costs),actual_run_cpu_seconds=sum(c['process_cpu_seconds'] for c in costs),validation_wall_seconds=sum(c['validation_seconds'] for c in costs),resume_wall_seconds=sum(c['resume_seconds'] for c in costs),maximum_lifetime_peak_rss_MiB=max(c['lifetime_peak_rss_MiB'] for c in costs),remaining_low_model_hours=remaining.updated_low_model_seconds.sum()/3600,remaining_high_model_hours=remaining.updated_high_model_seconds.sum()/3600,models_fitted_by_analysis=0,historical_refits=0,repeated_learned_fits=0,full_study_ready=False,additional_fits_authorized=False)
    atomic(out/'analysis_validation.json',summary)
    # A compact panel table retains every seed's contribution and all signs.
    panels=[]
    for key,p in pair[(pair.outer_fold==2)&(pair.left_model=='attention_lstm')&(pair.right_model=='xgboost')].groupby(['dataset','horizon']):
        l=fold[(fold.dataset==key[0])&(fold.horizon==key[1])&(fold.model=='attention_lstm')];x=fold[(fold.dataset==key[0])&(fold.horizon==key[1])&(fold.model=='xgboost')]
        panels.append(dict(dataset=key[0],horizon=key[1],physical_minutes=key[1]*MINUTES[key[0]],target_units=UNITS[key[0]],seeds=len(p),mae_difference_mean=p.mae_difference.mean(),mae_difference_min=p.mae_difference.min(),mae_difference_max=p.mae_difference.max(),lstm_lower_mae_seeds=int((p.mae_difference<0).sum()),winkler95_difference_mean=p.winkler95_difference.mean(),lstm_lower_winkler95_seeds=int((p.winkler95_difference<0).sum()),lstm_coverage95_mean=l.coverage95.mean(),xgboost_coverage95_mean=x.coverage95.mean(),mpiw95_difference_mean=p.mpiw95_difference.mean(),cpu_ratio_mean=p.process_cpu_seconds_ratio.mean(),cpu_ratio_min=p.process_cpu_seconds_ratio.min(),cpu_ratio_max=p.process_cpu_seconds_ratio.max()))
    panel=pd.DataFrame(panels);write(out,'panel2_horizon_summary.csv',panel)
    reports(out,fold,panel,seedcost,summary)
    if final:figures(out,fold)
    atomic(out/'COMPLETE.json',dict(passed=True,files=tree(out),models_fitted=0));print(json.dumps(summary,indent=2),flush=True)

def reports(out,fold,panel,costs,summary):
    rel=out.relative_to(ROOT).as_posix();n=summary['new_paired_units'];last=42+n//13
    text='# Matched fold-2 multiseed comparison\n\n'+f'Validated **{n}/52 new paired units**, seeds 43–{last}. Actual run exits are all 0: **{8*n} tuning + {2*n} final learned fits**, **{3*n} point and {6*n} interval cells**, **{6*n} saved-model prediction checks**, and **{n} zero-fit resumes**. Observed maximum artifact prediction discrepancy: {summary["observed_max_prediction_difference"]:.9g}. Actual seed paths and deterministic persistence aliases passed verification. No historical model was refitted.\n\n'
    text+='[No-fitting failure diagnosis](MATCHED_FAILURE_DIAGNOSIS.md) found measured bias and distribution changes, without a new unresolved correctness defect. Scientific source stays `'+read(REVIEW/'joint_pre_fit_manifest.json')['source_hash']+'`. [Evaluated source](review/matched_fold2_multiseed_20260914/evaluated_commit.json), [evidence index](review/matched_fold2_multiseed_20260914/EVIDENCE_INDEX.md), and [progress/restart](review/matched_fold2_multiseed_20260914/PROGRESS_AND_RESTART.md) retain identities and actual commands.\n\n'
    text+='## Five-seed evidence and interpretation\n\n[Every seed, metric and measured model cost]('+rel+'/fold2_five_seed_comparison.csv) and [mean, sample standard deviation, minimum and maximum]('+rel+'/training_seed_summary.csv) describe training randomness on identical fold-2 evaluation support. They are not population confidence intervals. Persistence seed rows are deterministic aliases, not independent replicates. All seeds remain visible; none is selected as best for reporting.\n\n'
    text+=A.table(panel,['dataset','physical_minutes','seeds','mae_difference_mean','mae_difference_min','mae_difference_max','lstm_lower_mae_seeds','winkler95_difference_mean','lstm_lower_winkler95_seeds','lstm_coverage95_mean','xgboost_coverage95_mean','mpiw95_difference_mean','cpu_ratio_mean'])+'\n'
    text+='Differences are LSTM minus XGBoost. CPU ratio is LSTM/XGBoost measured model-phase CPU. Lower width is not a benefit without coverage context. The [paired table]('+rel+'/paired_model_contrasts.csv) explicitly distinguishes **signed deviation from nominal**, **absolute deviation from nominal**, and their paired differences at both 90% and 95%. Group and RICO-phase summaries retain original support; dependent horizons and seeds do not create independent buildings, acquisition runs or periods.\n\n'
    for ds in ['pleia','pleia_energy','rico','bdg2']:
        text+='### '+LABELS[ds]+'\n\nTarget units: '+UNITS[ds]+'. Values below are means across the reported training seeds; exact values, sample SD and ranges remain in CSVs.\n\n'
        mean=fold[fold.dataset==ds].groupby(['physical_minutes','model'],as_index=False)[['mae','rmse','coverage90','mpiw90','winkler90','coverage95','mpiw95','winkler95','process_cpu_seconds']].mean()
        text+=A.table(mean,list(mean.columns))+'\n'
    text+='## Measured cost and acceptance\n\n'+A.table(costs,list(costs.columns))+'\n'
    text+=f'New model commands used **{summary["actual_run_wall_seconds"]/3600:.4f} wall hours** and **{summary["actual_run_cpu_seconds"]/3600:.4f} process CPU hours**. Independent validation adds {summary["validation_wall_seconds"]/60:.2f} wall minutes; zero-fit resume adds {summary["resume_wall_seconds"]/60:.2f}. Maximum lifetime peak RSS: {summary["maximum_lifetime_peak_rss_MiB"]:.2f} MiB. These exclude preflight, diagnosis, orchestration, aggregation and publication. Separate actual command logs retain those costs. Nested phase timers must not be added twice.\n\n'
    text+='CPU-only, one numerical/Torch thread, n_jobs=1, lazy batch256, the nonblocking 3 GiB launch reference, 256 MiB epoch floor and 8 GiB disk guard were preserved. All per-unit saved-stream arithmetic, finite-sample ranks, inner selection/epochs, serialized-model reconstruction, group-to-pooled squared-error arithmetic and immutable zero-fit resumes passed. No clipping, outer-result retuning or model-ranking gate was used. Original phase timing measurements stay attached to their original executions.\n\n'
    text+=f'## Remaining work\n\nCumulative **{18+n}/195 paired units, {3*(18+n)}/585 point cells and {6*(18+n)}/1170 interval cells**. Fold 2 contains {13+n} paired units; five additional-fold units stay separate. **{177-n} paired units / {10*(177-n)} learned fits remain** in the matched core queue. Updated same-dataset planning scenario: {summary["remaining_low_model_hours"]:.2f}–{summary["remaining_high_model_hours"]:.2f} model-hours; this excludes preparation and verification and is not a confidence interval or deadline.\n\n'
    text+='The [implementation readiness map](MATCHED_METHOD_READINESS_MAP.md) identifies the smallest next adapter package for broader conformal methods and causal alerting. Static own-model absolute-error split conformal does not complete CQR, EnbPI, DSCP, seasonal, operational, conditional-challenge, contamination/recovery or robustness obligations. Remaining outer folds are still necessary. RICO historical use and phase imbalance, recurring known BDG2 buildings, and the inspected historical periods limit claims. Full-study readiness remains false; no unlisted fits are launched.\n'
    atomic(ROOT/'MATCHED_FOLD2_MULTISEED_REPORT.md',text)
    atomic(REVIEW/'PANEL2_NUMERICAL_RESPONSE.md','# Panel 2: training-seed sensitivity of Attention-LSTM versus XGBoost\n\n'+A.table(panel,list(panel.columns))+'\nAll seed contributions remain in the paired table. These means/ranges concern training randomness on the same support, not population uncertainty. Consistent width or score differences do not imply adequate coverage, statistical superiority or equivalence. The remaining outer folds and broader interval methods are still required.\n')
    for name in ['PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']:
        old=subprocess.check_output(['git','show',ENTRY+':'+name],cwd=ROOT)
        report='../MATCHED_FOLD2_MULTISEED_REPORT.md' if name.startswith('review/') else 'MATCHED_FOLD2_MULTISEED_REPORT.md'
        idx='matched_fold2_multiseed_20260914/EVIDENCE_INDEX.md' if name.startswith('review/') else 'review/matched_fold2_multiseed_20260914/EVIDENCE_INDEX.md'
        prefix=f'# Fold-2 multiseed progress — 14 September 2026\n\n{n}/52 new units validated; {18+n}/195 total. {8*n} tuning and {2*n} final fits; {3*n} point and {6*n} interval cells; {6*n} artifact checks; {n} zero-fit resumes. Seeds 43–{last} complete. Main and historical results preserved.\n\n[Report]({report}); [evidence index]({idx}). {177-n} matched units and broader-method obligations remain; full-study readiness is false.\n\n<!-- multiseed-20260914: preserved historical status follows -->\n\n'
        (ROOT/name).write_bytes(prefix.encode()+old)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['unit','seed','final']);p.add_argument('--stem');p.add_argument('--out',required=True);args=p.parse_args()
    with forbid_fitting():
        if args.action=='unit':unit(args.stem,args.out)
        else:aggregate(args.out,final=args.action=='final')
