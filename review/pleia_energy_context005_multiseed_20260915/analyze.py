"""Five-seed C analysis with frozen original-context aggregation and inference."""
from __future__ import annotations
import itertools,json,os,sys
from pathlib import Path
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[name]='1'
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import *
from src.context005_metrics import inference
from src.operational004_design import STRATA
from src.intervals005_common import Operations,load_owner
from src.conformal_quantile import _sub_estimators
from src.unit_checkpoint import signature

CONTROLS=['quantile_static','cqr_static','cqr_rolling','persistence_static']
RULES=['single_sample','30min_3of3','60min_4of6','180min_3of18','360min_4of36']
CHANNELS=['numerical_only','availability_only','combined']
KEYS=['dataset','outer_fold','control_id','rule_id','channel','context_id','original_segment_id','group_id','family','severity']

def frame(path):
    try:return pd.read_csv(path,float_precision='round_trip',dtype={'row_id':str,'context_id':str,'group_id':str,'original_segment_id':str,'segment_id':str})
    except pd.errors.EmptyDataError:return pd.DataFrame()

def validate_contribution_keys(df,expected_seeds=ALL_SEEDS):
    full=KEYS+['model_seed']
    if df.duplicated(full).any():raise ValueError('duplicate model-seed contribution key')
    sets=df.groupby(KEYS,dropna=False).model_seed.agg(lambda x:tuple(sorted(x)))
    expected=tuple(expected_seeds)
    if not sets.map(lambda x:x==expected).all():raise ValueError('seed completeness mismatch')
    invariant=df.groupby(KEYS,dropna=False).effective_slots.nunique()
    if not invariant.eq(1).all():raise ValueError('support mismatch across model seeds')
    return dict(passed=True,rows=len(df),keys=len(sets),seeds=list(expected),minimum_effective_slots=int(df.effective_slots.min()),maximum_effective_slots=int(df.effective_slots.max()))

def weighted(part):
    n=part.n.sum()
    return pd.Series(dict(n=int(n),unavailable_n=int(part.unavailable_n.sum()),coverage=float((part.coverage*part.n).sum()/n),
        mpiw=float((part.mpiw*part.n).sum()/n),winkler=float((part.winkler*part.n).sum()/n)))

def macro_from_contributions(contrib):
    # ``group_id`` is an explicitly nullable provenance field for this PLEIA
    # design.  Retain its null group when pooling; pandas otherwise drops all
    # contributions before the control/rule/channel macro rows are formed.
    seedavg=contrib.groupby([k for k in KEYS if k not in ['dataset','outer_fold','original_segment_id','group_id']]+['original_segment_id','group_id'],as_index=False,dropna=False).agg(
        recall=('recall','mean'),restricted_delay=('restricted_delay','mean'),effective_slots=('effective_slots','first'))
    # Average original contexts equally within stratum, then 21 strata equally.
    strata=seedavg.groupby(['control_id','rule_id','channel','family','severity'],as_index=False).agg(
        recall=('recall','mean'),restricted_ttd_minutes=('restricted_delay','mean'),original_contexts=('context_id','nunique'))
    rows=[]
    for key,g in strata.groupby(['control_id','rule_id','channel'],sort=True):
        supported=len(g)==21 and g.original_contexts.min()>=5
        rows.append(dict(zip(['control_id','rule_id','channel'],key),conditional_context_detection=float(g.recall.mean()) if supported else np.nan,
            restricted_ttd_equal_stratum_minutes=float(g.restricted_ttd_minutes.mean()) if supported else np.nan,
            supported_strata=int((g.original_contexts>=5).sum()),minimum_original_contexts=int(g.original_contexts.min()),status='supported_point_estimate' if supported else 'unavailable_support'))
    return seedavg,strata,pd.DataFrame(rows)

def estimator_seeds(seed):
    owner=load_owner(run(seed)/'stages/owner_fit_cqr/owner.pkl');estimators,_=_sub_estimators(owner)
    return [e.get_params()['random_state'] for e in estimators]

def seed_summary(seed):
    root=run(seed);tables=root/'stages/tables'
    events=frame(tables/'events.csv.gz');strata=frame(tables/'strata.csv');macros=frame(tables/'conditional_macro.csv');work=frame(tables/'fullstream_workload.csv')
    assert len(events)==171360 and len(strata)==1260 and len(macros)==60 and len(work)==60
    workagg=work.groupby(['control_id','rule_id','channel'],as_index=False).agg(eligible_rows=('eligible_rows','sum'),asset_days=('asset_days','sum'),
        background_episodes=('episodes','sum'),alert_rows=('alert_rows','sum'),time_in_alert_days=('time_in_alert_days','sum'))
    workagg['background_episodes_per_asset_day']=workagg.background_episodes/workagg.asset_days
    workagg['fraction_time_in_alert']=workagg.time_in_alert_days/workagg.asset_days
    rows=[]
    for m in macros.itertuples():
        ss=strata[(strata.control_id==m.control_id)&(strata.rule_id==m.rule_id)&(strata.channel==m.channel)]
        ev=events[(events.control_id==m.control_id)&(events.rule_id==m.rule_id)&(events.channel==m.channel)]
        pos=ev[ev.effective&ev.eligible];found=pos[pos.detected];w=workagg[(workagg.control_id==m.control_id)&(workagg.rule_id==m.rule_id)&(workagg.channel==m.channel)].iloc[0]
        rows.append(dict(model_seed=seed,control_id=m.control_id,rule_id=m.rule_id,channel=m.channel,
            conditional_context_detection=m.conditional_context_macro,restricted_ttd_equal_stratum_minutes=float(ss.restricted_mean_detection_minutes.mean()),
            detected=int(pos.detected.sum()),misses=int((~pos.detected).sum()),detected_delay_median_minutes=float(found.delay_minutes.median()) if len(found) else np.nan,
            detected_delay_q90_minutes=float(found.delay_minutes.quantile(.9)) if len(found) else np.nan,supported_strata=int(m.supported_strata),
            original_eligible_rows=int(w.eligible_rows),original_asset_days=float(w.asset_days),background_episodes=int(w.background_episodes),
            background_episodes_per_asset_day=float(w.background_episodes_per_asset_day),alert_rows=int(w.alert_rows),
            time_in_alert_days=float(w.time_in_alert_days),fraction_time_in_alert=float(w.fraction_time_in_alert)))
    return pd.DataFrame(rows),events,strata,work

def interval_rows(seed):
    root=run(seed);variants=frame(root/'stages/tables/variants.csv');cache={};rows=[]
    for v in variants.itertuples():
        if v.canonical_stage not in cache:cache[v.canonical_stage]=frame(root/'stages'/v.canonical_stage/'interval_diagnostics.csv')
        for r in cache[v.canonical_stage].to_dict('records'):
            rows.append(dict(model_seed=seed,context_id=v.context_id,ordinal=v.ordinal,family=v.family,severity=v.severity,effective=v.effective,
                null=v.null,alias=v.alias,canonical_stage=v.canonical_stage,**r))
    detail=pd.DataFrame(rows);out=[]
    for scope,mask in [('identity',detail.ordinal==0),('all_scheduled_fault_slots',detail.ordinal>0),('effective_fault_slots',(detail.ordinal>0)&detail.effective)]:
        for key,g in detail[mask].groupby(['control_id','target']):out.append(dict(model_seed=seed,scope=scope,control_id=key[0],target=key[1],streams=g[['context_id','ordinal']].drop_duplicates().shape[0],**weighted(g)))
    full=[]
    for stage in sorted((root/'stages').glob('fullstream_*')):full.append(frame(stage/'interval_diagnostics.csv'))
    f=pd.concat(full,ignore_index=True)
    for key,g in f.groupby(['control_id','target']):out.append(dict(model_seed=seed,scope='fullstream_clean',control_id=key[0],target=key[1],streams=len(g),**weighted(g)))
    return pd.DataFrame(out)

def operation_and_cost(seed):
    ops=[json.loads(line) for line in (run(seed)/'operations.jsonl').read_text(encoding='utf-8').splitlines()]
    returned=pd.DataFrame([r for r in ops if r.get('event')=='returned'])
    counts=returned.groupby('kind').size().to_dict()
    if counts!={'calibrator_conformalize':2,'cqr_wrapper_fit':1,'quantile_estimator_fit':3}:raise ValueError(f'operation mismatch seed {seed}: {counts}')
    seeds=estimator_seeds(seed)
    if seeds!=[seed,seed,seed]:raise ValueError(f'native estimator seed mismatch {seed}: {seeds}')
    owner=read(run(seed)/'stages/controls/identity.json')
    if not owner['quantile_shared'] or owner['new_learned_fits']!=0 or owner['persistence_calibrations']!=1:raise ValueError('owner sharing mismatch')
    return dict(model_seed=seed,cqr_wrapper_fit=1,quantile_estimator_fit=3,nested_calibrator_conformalize=2,logical_conformalizations=1,
        persistence_radius_computations=1,persistence_learned_fits=0,estimator_random_states=';'.join(map(str,seeds)),owner_sha256=owner['owner_sha256'])

def make_draw_estimates(pooled,contexts,draws):
    lookup={c:i for i,c in enumerate(contexts.context_id)};rows=[]
    for key,part in pooled.groupby(['control_id','rule_id','channel']):
        a=np.full((len(contexts),21),np.nan)
        for r in part.itertuples():a[lookup[r.context_id],STRATA.index((r.family,r.severity))]=r.recall
        values=np.nanmean(a[draws],axis=1).mean(axis=1)
        rows.extend(dict(control_id=key[0],rule_id=key[1],channel=key[2],draw=i,value=float(v)) for i,v in enumerate(values))
    return pd.DataFrame(rows)

def main():
    if ANALYSIS.exists():raise ValueError('preserve completed aggregate analysis')
    ANALYSIS.mkdir(parents=True)
    with Operations(forbid=True):
        baseline=read(REVIEW/'PRESERVATION_BASELINE.json')
        assert source_digest()==SOURCE_HASH and digest(SEED42_RUN/'COMPLETE.json')==baseline['seed42_complete_sha256']
        summaries=[];events=[];strata=[];work=[];contrib=[];interval=[];operations=[]
        for seed in ALL_SEEDS:
            complete=read(run(seed)/'COMPLETE.json');assert complete['actual_exit_status']==0
            s,e,st,w=seed_summary(seed);summaries.append(s);events.append(e.assign(model_seed=seed));strata.append(st.assign(model_seed=seed));work.append(w.assign(model_seed=seed))
            contrib.append(frame(run(seed)/'stages/tables/original_context_contributions.csv.gz'))
            interval.append(interval_rows(seed));operations.append(operation_and_cost(seed))
        summaries=pd.concat(summaries,ignore_index=True);events=pd.concat(events,ignore_index=True);strata=pd.concat(strata,ignore_index=True);work=pd.concat(work,ignore_index=True)
        contributions=pd.concat(contrib,ignore_index=True);interval=pd.concat(interval,ignore_index=True);operations=pd.DataFrame(operations)
        assert len(summaries)==300 and len(events)==856800 and set(summaries.model_seed)==set(ALL_SEEDS)
        keycheck=validate_contribution_keys(contributions)
        # Null/effective/alias/eligibility and slot identities must be seed-invariant.
        event_key=['context_id','family','severity','replicate','slot_sign','mask_seed','control_id','rule_id','channel']
        inv=events.groupby(event_key,dropna=False).agg(seeds=('model_seed','nunique'),effective=('effective','nunique'),null=('null','nunique'),alias=('alias','nunique'),eligible=('eligible','nunique'))
        if not (inv.seeds.eq(5)&inv[['effective','null','alias','eligible']].eq(1).all(axis=1)).all():raise ValueError('event support/null masks differ across model seeds')
        contexts=frame(SEED42_DESIGN/'contexts.csv')
        bounds,drawmeta=inference(contributions,contexts,'pleia_energy',expected_seeds=ALL_SEEDS)
        if drawmeta['status']!='draws_generated' or len(drawmeta['draws'])!=2000:raise ValueError('original-context inference unavailable before cell gates')
        draws=np.asarray(drawmeta['draws'],dtype=int)
        seedavg,stratum_avg,macro=macro_from_contributions(contributions)
        comparison=macro.merge(bounds,on=['control_id','rule_id','channel'],suffixes=('','_inference'),validate='one_to_one')
        seed_stats=summaries.groupby(['control_id','rule_id','channel'],as_index=False).agg(
            seed_mean_detection=('conditional_context_detection','mean'),seed_sd_detection=('conditional_context_detection','std'),seed_min_detection=('conditional_context_detection','min'),seed_max_detection=('conditional_context_detection','max'),
            mean_restricted_ttd_minutes=('restricted_ttd_equal_stratum_minutes','mean'),mean_detected=('detected','mean'),mean_misses=('misses','mean'),
            mean_background_episodes_per_asset_day=('background_episodes_per_asset_day','mean'),mean_fraction_time_in_alert=('fraction_time_in_alert','mean'),
            mean_original_asset_days=('original_asset_days','mean'))
        comparison=comparison.merge(seed_stats,on=['control_id','rule_id','channel'],validate='one_to_one')
        if not np.allclose(comparison.conditional_context_detection,comparison.seed_mean_detection,atol=1e-14):raise ValueError('seed pooling order disagreement')
        pooled=contributions.groupby(['context_id','control_id','rule_id','channel','family','severity'],as_index=False).recall.mean()
        draw_values=make_draw_estimates(pooled,contexts,draws)
        # Predeclared six control contrasts, all rules/channels, using the exact shared draws.
        pairs=[]
        for a,b in itertools.combinations(CONTROLS,2):
            p=draw_values[draw_values.control_id.isin([a,b])].pivot(index=['rule_id','channel','draw'],columns='control_id',values='value').reset_index()
            p['difference']=p[a]-p[b]
            for key,g in p.groupby(['rule_id','channel']):
                vals=g.difference.to_numpy();good=len(vals)>=1900 and np.ptp(vals)>0
                point=float(comparison[(comparison.control_id==a)&(comparison.rule_id==key[0])&(comparison.channel==key[1])].conditional_context_detection.iloc[0]-comparison[(comparison.control_id==b)&(comparison.rule_id==key[0])&(comparison.channel==key[1])].conditional_context_detection.iloc[0])
                pairs.append(dict(control_a=a,control_b=b,definition='A minus B',rule_id=key[0],channel=key[1],point_difference=point,
                    status='supported' if good else 'unavailable_valid_draw_or_degenerate',valid_draws=len(vals),lower=float(np.quantile(vals,.025)) if good else np.nan,upper=float(np.quantile(vals,.975)) if good else np.nan,draw_hash=drawmeta['draw_hash']))
        pairs=pd.DataFrame(pairs);assert len(pairs)==90
        interval_five=interval.groupby(['scope','control_id','target'],as_index=False).agg(seeds=('model_seed','nunique'),mean_streams=('streams','mean'),
            total_n=('n','sum'),total_unavailable_n=('unavailable_n','sum'),mean_coverage=('coverage','mean'),seed_sd_coverage=('coverage','std'),mean_mpiw=('mpiw','mean'),mean_winkler=('winkler','mean'))
        csv(ANALYSIS/'per_seed_control_rule_channel.csv',summaries);csv(ANALYSIS/'five_seed_control_rule_channel.csv',comparison)
        csv(ANALYSIS/'per_seed_stratum_metrics.csv',strata);csv(ANALYSIS/'original_context_seed_contributions.csv.gz',contributions)
        csv(ANALYSIS/'original_context_seed_averages.csv.gz',seedavg);csv(ANALYSIS/'five_seed_stratum_averages.csv',stratum_avg)
        csv(ANALYSIS/'inference_bounds.csv',bounds);csv(ANALYSIS/'bootstrap_draw_estimates.csv.gz',draw_values);atomic(ANALYSIS/'bootstrap_design.json',drawmeta)
        csv(ANALYSIS/'paired_control_detection_contrasts.csv',pairs);csv(ANALYSIS/'per_seed_background_workload.csv',work)
        csv(ANALYSIS/'per_seed_interval_diagnostics.csv',interval);csv(ANALYSIS/'five_seed_interval_diagnostics.csv',interval_five)
        csv(ANALYSIS/'operation_reconciliation.csv',operations)
        # Actual command costs: seed 42 plus new four-seed coordinator.
        costs=[]
        old=read(SEED42_BATCH/'progress.json');new=read(BATCH/'progress.json')
        for seed,progress,prefix in [(42,old,'pleia_energy/')]:
            for action in ['freeze','readiness','run','validate','resume']:
                r=progress['tasks'][prefix+action];costs.append(dict(model_seed=seed,action=action,actual_exit_status=r['exit_code'],wall_seconds=r['seconds'],started_utc=r['started_utc'],ended_utc=r['ended_utc'],logger_receipt=r['logger_receipt']))
        for seed in SEEDS:
            for action in ['freeze','readiness','run','validate','resume']:
                r=new['tasks'][f'seed_{seed}/{action}'];costs.append(dict(model_seed=seed,action=action,actual_exit_status=r['exit_code'],wall_seconds=r['seconds'],started_utc=r['started_utc'],ended_utc=r['ended_utc'],logger_receipt=r['logger_receipt']))
        costs=pd.DataFrame(costs);csv(ANALYSIS/'worker_costs_and_exits.csv',costs)
        cost_summary=costs.groupby('action',as_index=False).agg(units=('model_seed','size'),total_wall_seconds=('wall_seconds','sum'),mean_wall_seconds=('wall_seconds','mean'),max_wall_seconds=('wall_seconds','max'))
        csv(ANALYSIS/'worker_cost_summary.csv',cost_summary)
        # Compact, source-bound combined-channel figure.
        plot=comparison[comparison.channel=='combined'].copy();fig,axes=plt.subplots(2,2,figsize=(13,8),sharey=True);colors=plt.cm.tab10(np.linspace(0,1,5))
        for ax,control in zip(axes.flat,CONTROLS):
            p=plot[plot.control_id==control].set_index('rule_id').loc[RULES].reset_index();x=np.arange(5)
            ax.bar(x,p.conditional_context_detection,color=colors);ax.errorbar(x,p.conditional_context_detection,
                yerr=np.vstack([p.conditional_context_detection-p.lower,p.upper-p.conditional_context_detection]),fmt='none',ecolor='black',capsize=3)
            ax.set_title(control);ax.set_xticks(x,RULES,rotation=30,ha='right');ax.set_ylim(0,1);ax.grid(axis='y',alpha=.25)
        fig.supylabel('Conditional detection');fig.suptitle('PLEIA-energy C: five-seed mean and original-context block-bootstrap interval');fig.tight_layout()
        fig.savefig(ANALYSIS/'five_seed_detection.png',dpi=170);fig.savefig(ANALYSIS/'five_seed_detection.pdf');plt.close(fig)
        atomic(ANALYSIS/'five_seed_detection.sources.json',dict(source_files={n:digest(ANALYSIS/n) for n in ['five_seed_control_rule_channel.csv','inference_bounds.csv']},draw_hash=drawmeta['draw_hash']))
        result=dict(passed=True,source_hash=source_digest(),model_seeds=list(ALL_SEEDS),new_model_seeds=list(SEEDS),seed42_reused_without_rerun=True,
            contexts=68,contexts_not_pseudoreplicated=68,schedules_per_seed=2856,event_records=len(events),seed_specific_macro_cells=len(summaries),aggregate_cells=len(comparison),
            contribution_validation=keycheck,event_support_invariant=True,inference_status_counts=bounds.status.value_counts().to_dict(),draw_hash=drawmeta['draw_hash'],draws=2000,
            operation_totals={c:int(operations[c].sum()) for c in ['cqr_wrapper_fit','quantile_estimator_fit','nested_calibrator_conformalize','logical_conformalizations','persistence_radius_computations','persistence_learned_fits']},
            energy_sensitivity_applied=False,matched_forecasting_complete=70,interval_quality_complete=250,seasonal_unique_complete=9,full_study_ready=False)
        atomic(ANALYSIS/'validation.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
