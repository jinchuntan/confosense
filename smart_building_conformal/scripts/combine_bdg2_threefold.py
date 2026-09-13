"""Frozen exploratory count pooling and paired original-building contrasts.

Consumes independently audited saved evidence; performs no fitting, selection,
threshold search, hypothesis testing or model-seed pseudo-replication.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

N=[f'n{i}' for i in range(21)];TP=[f'tp{i}' for i in range(21)]
COUNTS=['exposure_days','clean_episodes','unmatched_episodes','corrupted_episodes','time_in_alert_days']+N+TP


def rates(totals):
    n=np.asarray(totals[N],float);tp=np.asarray(totals[TP],float)
    return dict(macro_event_recall=float(np.mean(tp/n)) if (n>0).all() else np.nan,
                background_episodes_per_asset_day=float(totals['clean_episodes']/totals['exposure_days']),
                asset_days=float(totals['exposure_days']),clean_episodes=float(totals['clean_episodes']),
                n_events=float(n.sum()),n_detected=float(tp.sum()))


def paired_buildings(inputs,a,b,groups,seed=20240601,reps=2000,min_valid=1900):
    # Every input row already pools all five catalogues' event contributions;
    # exposure/clean episodes still represent each original row exactly once.
    sums=inputs.groupby(['candidate_id','group_id'])[COUNTS].sum()
    aa=sums.loc[a].reindex(groups);bb=sums.loc[b].reindex(groups)
    assert len(groups)==len(set(groups)) and not aa.isna().any().any() and not bb.isna().any().any()
    np.testing.assert_allclose(aa.exposure_days,bb.exposure_days,rtol=0,atol=1e-10)
    draws=np.random.default_rng(seed).integers(0,len(groups),size=(reps,len(groups)))
    multiplicity=np.array([np.bincount(d,minlength=len(groups)) for d in draws])
    reps_out=[]
    for table in (aa,bb):
        totals=pd.DataFrame(multiplicity@table[COUNTS].to_numpy(),columns=COUNTS)
        n=totals[N].to_numpy();tp=totals[TP].to_numpy();valid=(n>0).all(axis=1)
        with np.errstate(divide='ignore',invalid='ignore'): recall=np.mean(tp/n,axis=1)
        work=totals.clean_episodes.to_numpy()/totals.exposure_days.to_numpy()
        reps_out.append((recall,work,valid))
    valid=reps_out[0][2]&reps_out[1][2]
    data=pd.DataFrame(dict(replicate=np.arange(reps),valid=valid,
        delta_macro_event_recall=reps_out[0][0]-reps_out[1][0],
        delta_background_episodes_per_asset_day=reps_out[0][1]-reps_out[1][1]))
    point_a=rates(aa.sum());point_b=rates(bb.sum());result=[]
    for metric in ['macro_event_recall','background_episodes_per_asset_day']:
        v=data.loc[valid,'delta_'+metric].to_numpy();available=len(v)>=min_valid and np.ptp(v)>0
        lo,hi=np.quantile(v,[.025,.975]) if available else (np.nan,np.nan)
        result.append(dict(metric=metric,candidate_a=a,candidate_b=b,
            estimate_a=point_a[metric],estimate_b=point_b[metric],difference_a_minus_b=point_a[metric]-point_b[metric],
            ci_lower=lo,ci_upper=hi,valid_replicates=int(valid.sum()),requested_replicates=reps,
            interval_status='approximate_conditional_percentile' if available else 'unavailable_insufficient_or_degenerate',
            original_buildings=len(groups),model_seeds='[42]',bootstrap_seed=seed))
    return pd.DataFrame(result),data,draws


def combine(manifest,out):
    manifest=Path(manifest);plan=json.loads(manifest.read_text());out=Path(out);out.mkdir(parents=True,exist_ok=False)
    analysis=plan['combined_analysis'];assert plan['model_seeds']==[42] and plan['execution_order']==[1,0]
    a,b=analysis['candidate_a'],analysis['candidate_b'];assert a=='c0012_23099bed3753' and b=='c0000_f5146f1247fa'
    decisions=[];metrics=[];comparisons=[];inputs=[];support=[];channels=[];recoveries=[];rejections=[];fits=[];outer_sets={};checks=[]
    for fold in [2,1,0]:
        run=Path(plan['units'][str(fold)]['out']);unit=run/f'units/outer{fold}_model42'
        audit=run.parent/('bdg2_pilot_independent_validation_v1' if fold==2 else f'bdg2_threefold_f{fold}_audit_v{2 if fold==1 else 1}')
        validation=json.loads((audit/'validation.json').read_text());assert validation['passed'] and validation['learned_fits']==0
        payload=json.loads((unit/'payload.json').read_text());spec=json.loads((run/'checkpoint_manifest.json').read_text())['spec']
        assert spec['candidate_grid']==plan['candidate_grid'] and spec['data_hash']==plan['data_hash']
        assert spec['catalogue_seeds']==[42,43,44,45,46] and spec['model_seed']==42
        entries=dict(primary=dict(decision=payload['decision'],pipeline=payload['pipeline'],operational_feasible=payload['operational_feasible']),
                     inverse=payload['inverse_recall_floor'],**payload['independent_operating_points'])
        for kind,value in entries.items():
            pipeline=value['pipeline']
            decisions.append(dict(outer_fold=fold,selection=kind,decision=value['decision'],
                candidate_id=pipeline['candidate_id'] if pipeline else None,operational_feasible=value['operational_feasible'],
                settings=json.dumps(pipeline,sort_keys=True),source_hash=spec['source_hash']))
        comparisons.extend(dict(outer_fold=fold,**c) for c in payload['outer_comparisons'])
        for f in payload['fit_records']:
            fits.append(dict(outer_fold=fold,role=f['role'],method=f['method'],fit_objects=f['fit_invocations'],
                sub_estimators=f['identity'].get('sub_estimators',0)*f['fit_invocations'],
                estimator_class=f['identity']['estimator_class'],fit_identity=f['fit_identity']))
        m=pd.read_csv(audit/'recomputed_metrics.csv',float_precision='round_trip');q=pd.read_csv(audit/'clean_interval_quality.csv',float_precision='round_trip')
        m=m[m.role=='outer_test'].merge(q[q.role=='outer_test'],on=['role','candidate_id'],validate='one_to_one')
        metrics.append(m.assign(outer_fold=fold))
        support.append(pd.read_csv(audit/'event_support.csv').assign(outer_fold=fold))
        channels.append(pd.read_csv(audit/'stratum_channel_metrics.csv').assign(outer_fold=fold))
        recoveries.append(pd.read_csv(audit/'recovery.csv').assign(outer_fold=fold))
        for name in ['rejections','inverse_rejections']:
            rejections.append(pd.read_csv(audit/(name+'.csv')).assign(outer_fold=fold,selection='primary' if name=='rejections' else 'inverse'))
        seen={};parts=[]
        for chunk in pd.read_csv(unit/'outer_contributions.csv.gz',chunksize=50000,float_precision='round_trip',converters={'group_id':str,'row_id':str}):
            for cid,frame in chunk.groupby('candidate_id',sort=False):
                ids=seen.setdefault(cid,set());new=set(frame.row_id)
                assert len(new)==len(frame) and not ids&new;ids.update(new)
            parts.append(chunk.groupby(['candidate_id','group_id'])[COUNTS].sum())
        bank=pd.concat(parts).groupby(level=[0,1]).sum().reset_index().assign(outer_fold=fold)
        assert set(seen)==set(m.candidate_id) and all(ids==seen[a] for ids in seen.values())
        outer_sets[fold]=seen[a];inputs.append(bank)
        for cid,group in bank.groupby('candidate_id'):
            calc=rates(group[COUNTS].sum());saved=m[m.candidate_id==cid].iloc[0]
            for key in ['macro_event_recall','background_episodes_per_asset_day','n_events','n_detected']:
                np.testing.assert_allclose(calc[key],saved[key],rtol=2e-10,atol=2e-10)
        checks.append(dict(outer_fold=fold,rows=len(seen[a]),candidate_cells=len(seen),count_pool_reproduces_independent_metrics=True))
    overlaps=[dict(fold_a=x,fold_b=y,overlap=len(outer_sets[x]&outer_sets[y])) for x,y in [(2,1),(2,0),(1,0)]]
    assert all(v['overlap']==0 for v in overlaps)
    inputs=pd.concat(inputs,ignore_index=True);metrics=pd.concat(metrics,ignore_index=True)
    pooled=[]
    for cid,group in inputs.groupby('candidate_id'):
        folds=sorted(group.outer_fold.unique());row=dict(candidate_id=cid,outer_folds=json.dumps(list(map(int,folds))),
            all_three_folds=len(folds)==3,**rates(group[COUNTS].sum()))
        quality=metrics[metrics.candidate_id==cid];weights=quality.observed_rows
        for name in ['empirical_coverage','mpiw_kWh','winkler95_kWh','mae_kWh']:
            row[name]=np.average(quality[name],weights=weights)
        row['rmse_kWh']=np.sqrt(np.average(quality.rmse_kWh**2,weights=weights));row['observed_rows']=weights.sum()
        pooled.append(row)
    paired,reps,draws=paired_buildings(inputs,a,b,plan['original_buildings'],analysis['bootstrap_seed'],
        analysis['bootstrap_replicates'],analysis['minimum_valid_replicates'])
    pairfold=[]
    for fold in [2,1,0]:
        ma=metrics[(metrics.outer_fold==fold)&(metrics.candidate_id==a)].iloc[0]
        mb=metrics[(metrics.outer_fold==fold)&(metrics.candidate_id==b)].iloc[0]
        pairfold.append(dict(outer_fold=fold,**{'delta_'+k:ma[k]-mb[k] for k in
            ['macro_event_recall','background_episodes_per_asset_day','empirical_coverage','mpiw_kWh','winkler95_kWh']}))
    channel=pd.concat(channels,ignore_index=True);pooledchannel=channel[channel.role=='outer_test'].groupby(
        ['candidate_id','family','severity','channel'])[['n_events','n_detected']].sum().reset_index()
    pooledchannel['recall']=pooledchannel.n_detected/pooledchannel.n_events
    groupwork=inputs[['outer_fold','candidate_id','group_id','exposure_days','clean_episodes']].copy()
    groupwork['episodes_per_asset_day']=groupwork.clean_episodes/groupwork.exposure_days
    groupwork['above_workload_ceiling']=groupwork.episodes_per_asset_day>1.
    for name,table in [('fold_decisions',pd.DataFrame(decisions)),('outer_comparisons',pd.DataFrame(comparisons)),
        ('per_fold_operational_interval_metrics',metrics),('pooled_metrics',pd.DataFrame(pooled)),
        ('original_building_contributions',inputs),('paired_contrasts',paired),('paired_per_fold',pd.DataFrame(pairfold)),
        ('paired_replicates',reps),('paired_draws',pd.DataFrame(draws)),('event_support',pd.concat(support)),
        ('stratum_channel_metrics',channel),('pooled_stratum_channels',pooledchannel),('recovery',pd.concat(recoveries)),
        ('rejections',pd.concat(rejections)),('group_workload',groupwork),('fit_measurements',pd.DataFrame(fits)),('outer_disjointness',pd.DataFrame(overlaps))]:
        table.to_csv(out/(name+('.csv.gz' if name in ['paired_replicates','paired_draws','recovery'] else '.csv')),index=False)
    result=dict(passed=True,scope=plan['label'],manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        learned_fits=0,model_seeds=[42],original_buildings=10,catalogue_repetitions=5,outer_rows=sum(map(len,outer_sets.values())),
        all_outer_rows_disjoint=True,per_fold_count_checks=checks,paired_contrast=analysis,full_study_ready=False)
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();combine(a.manifest,a.out)
