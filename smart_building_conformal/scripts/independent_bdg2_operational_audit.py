"""Read-only BDG2 pilot recomputation, independent of production metric code.

Uses saved observations, issued bounds, event schedules and actual bootstrap
draws. No source dataset, model fit, production scorer or selector is imported.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd

FAMILIES=['random_missing','block_missing','stuck','dropout','bias','level_shift','drift']
STRATA=list(itertools.product(FAMILIES,[.5,1.,2.]))
CHANNELS=['availability_only','numerical_only','combined']
NAMES=['exposure_days','clean_episodes','unmatched_episodes','corrupted_episodes','time_in_alert_days']+[
    name for j in range(21) for name in [f'n{j}',f'tp{j}']]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()


def read(path):
    try:return pd.read_csv(path,float_precision='round_trip',converters={'row_id':str,'group_id':str})
    except pd.errors.EmptyDataError:return pd.DataFrame()


def ordered_blocks(path,keys):
    """Bounded-memory reader for contiguous candidate blocks in checkpoint CSVs."""
    pending=[];last=None;seen=set()
    for chunk in pd.read_csv(path,chunksize=50000,float_precision='round_trip',
                             converters={'row_id':str,'group_id':str}):
        for key,part in chunk.groupby(keys,sort=False,dropna=False):
            key=key if isinstance(key,tuple) else (key,)
            if last is not None and key!=last:
                assert last not in seen,'noncontiguous checkpoint block'
                seen.add(last);yield last,pd.concat(pending,ignore_index=True);pending=[]
            pending.append(part);last=key
    if pending:
        assert last not in seen
        yield last,pd.concat(pending,ignore_index=True)


def episodes_and_matches(stream,candidate,events):
    s=stream.reset_index(drop=True)
    times=pd.to_datetime(s.target_time);groups=s.group_id.to_numpy()
    observed=s.observed.to_numpy(float);lo=s.lower.to_numpy(float);hi=s.upper.to_numpy(float)
    av=s.available.to_numpy(bool)
    violations={'availability_only':~av,'numerical_only':av&((observed<lo)|(observed>hi))}
    violations['combined']=violations['availability_only']|violations['numerical_only']
    segments=[];ends={}
    for group in sorted(set(groups)):
        ix=np.flatnonzero(groups==group);ix=ix[np.argsort(times.iloc[ix].to_numpy(),kind='stable')]
        cuts=np.flatnonzero(np.diff(times.iloc[ix].to_numpy())!=np.timedelta64(1,'h'))+1
        for j,rows in enumerate(np.split(ix,cuts)):
            sid=f'{group}:segment:{j}';segments.append((group,sid,rows));ends[sid]=times.iloc[rows[-1]]
    eps=[];flags={};matches=[]
    for channel,violate in violations.items():
        active=np.zeros(len(s),bool);channel_eps=[]
        for group,sid,rows in segments:
            # Independent rolling-window implementation, retaining partial starts.
            a=pd.Series(violate[rows].astype(int)).rolling(int(candidate['m']),min_periods=1).sum().to_numpy()>=candidate['k']
            active[rows]=a
            start=np.flatnonzero(a & ~np.roll(a,1));end=np.flatnonzero(a & ~np.roll(a,-1))
            if a[0] and 0 not in start:start=np.r_[0,start]
            if a[-1] and len(a)-1 not in end:end=np.r_[end,len(a)-1]
            for left,right in zip(start,end):
                i,k=int(rows[left]),int(rows[right])
                channel_eps.append(dict(channel=channel,group_id=group,segment_id=sid,
                    episode_id=f'{channel}:{sid}:{i}',start_index=i,end_index=k,onset=times.iloc[i],end=times.iloc[k]))
        flags[channel]=active
        saved='alert_'+channel
        if saved in s:np.testing.assert_array_equal(active,s[saved].to_numpy(bool),err_msg=saved)
        used=set()
        for event in events[events.effective.astype(bool)].sort_values(['group_id','onset','event_id']).to_dict('records'):
            onset=pd.Timestamp(event['onset']);limit=pd.Timestamp(event['tolerance_end'])
            full=event['segment_id'] in ends and limit<=ends[event['segment_id']]
            choices=[e for e in channel_eps if e['group_id']==str(event['group_id']) and
                     e['segment_id']==event['segment_id'] and onset<=e['onset']<=limit and e['episode_id'] not in used] if full else []
            found=min(choices,key=lambda e:(e['onset'],e['episode_id'])) if choices else None
            if found:used.add(found['episode_id'])
            follow=max(0.,(min(limit,ends.get(event['segment_id'],onset))-onset).total_seconds()/60)
            matches.append(dict(event_id=event['event_id'],family=event['family'],severity=float(event['severity']),
                group_id=str(event['group_id']),start_index=int(event['start_index']),channel=channel,
                eligible=full,detected=found is not None,episode_id=found['episode_id'] if found else '',
                delay_minutes=(found['onset']-onset).total_seconds()/60 if found else np.nan,
                followup_minutes=follow,detection_censored=found is None,incomplete_followup=not full))
        for e in channel_eps:e['matched']=e['episode_id'] in used
        eps.extend(channel_eps)
    return pd.DataFrame(eps),pd.DataFrame(matches),flags


def contributions(clean,clean_eps,corrupt_eps,matched,active):
    bank=pd.DataFrame(0.,index=np.arange(len(clean)),columns=NAMES)
    bank['exposure_days']=1/24
    bank['time_in_alert_days']=active/24
    for eps,name in [(clean_eps,'clean_episodes'),(corrupt_eps,'corrupted_episodes')]:
        if not len(eps):continue
        for e in eps[eps.channel=='combined'].to_dict('records'):
            bank.loc[e['start_index'],name]+=1
            if name=='corrupted_episodes' and not e['matched']:bank.loc[e['start_index'],'unmatched_episodes']+=1
    for e in matched[(matched.channel=='combined')&matched.eligible].to_dict('records'):
        j=STRATA.index((e['family'],e['severity']));bank.loc[e['start_index'],f'n{j}']+=1
        bank.loc[e['start_index'],f'tp{j}']+=e['detected']
    return bank


def summarise(bank,events):
    total=bank.sum();n=total[[f'n{j}' for j in range(21)]].to_numpy(float);tp=total[[f'tp{j}' for j in range(21)]].to_numpy(float)
    macro=np.mean(tp/n) if (n>0).all() else np.nan
    custom=np.mean(2*tp/(n+tp+total.unmatched_episodes/21)) if (n>0).all() else np.nan
    pe=events[(events.channel=='combined')&events.eligible];det=pe[pe.detected]
    tau=pe.followup_minutes.min();micro=tp.sum()/n.sum() if n.sum() else np.nan
    return dict(macro_event_recall=macro,observed_strata_recall=np.mean(tp[n>0]/n[n>0]),
        custom_synthetic_f1=custom,event_recall_micro=micro,
        ordinary_matched_event_episode_precision=tp.sum()/total.corrupted_episodes if total.corrupted_episodes else np.nan,
        background_episodes_per_asset_day=total.clean_episodes/total.exposure_days,
        exposure_asset_days=total.exposure_days,n_events=int(n.sum()),n_detected=int(tp.sum()),
        corrupted_episode_count=int(total.corrupted_episodes),unmatched_episode_count=int(total.unmatched_episodes),
        time_in_alert_fraction=total.time_in_alert_days/total.exposure_days,observed_strata=int((n>0).sum()),
        detected_delay_median_minutes=det.delay_minutes.median(),detected_delay_q90_minutes=det.delay_minutes.quantile(.9),
        undetected_fraction=1-micro,delay_restriction_minutes=tau,
        restricted_mean_detection_minutes=np.minimum(np.where(pe.detected,pe.delay_minutes,pe.followup_minutes),tau).mean())


def bounds(bank,groups,catalogues,draws):
    supported=sum(len(catalogues[(catalogues.family==f)&(catalogues.severity==v)&catalogues.effective]
        [['group_id','onset']].drop_duplicates())>=5 for f,v in STRATA)
    result=dict(bound_status='insufficient_design_support',valid_replicates=0,supported_strata=supported,
                recall_lcb=np.nan,recall_ucb=np.nan,workload_lcb=np.nan,workload_ucb=np.nan)
    if supported<21 or len(set(groups))<5:return result,pd.DataFrame()
    assert draws['kind']=='whole_group' and draws['groups']==sorted(set(groups))
    indices=np.asarray(draws['indices']);assert indices.shape==(2000,len(set(groups)))
    np.testing.assert_array_equal(indices,np.random.default_rng(20240601).integers(len(set(groups)),size=indices.shape))
    names=['exposure_days','clean_episodes']+[f'n{j}' for j in range(21)]+[f'tp{j}' for j in range(21)]
    cluster=np.array([bank.loc[np.asarray(groups)==g,names].sum().to_numpy() for g in draws['groups']])
    # Bootstrap via cluster multiplicities, independent of production indexing.
    weights=np.stack([np.bincount(row,minlength=len(cluster)) for row in indices])
    total=weights@cluster;n=total[:,2:23];tp=total[:,23:44]
    valid=(n>0).all(axis=1)&(total[:,0]>0)&np.isfinite(total).all(axis=1)
    r=(tp[valid]/n[valid]).mean(axis=1);w=total[valid,1]/total[valid,0]
    result['valid_replicates']=int(valid.sum())
    replicas=pd.DataFrame(dict(replicate=np.flatnonzero(valid),macro_event_recall=r,background_episodes_per_asset_day=w))
    if len(r)<1900 or np.ptp(r)==0 or np.ptp(w)==0:
        result['bound_status']='insufficient_bound_support';return result,replicas
    result.update(bound_status='supported',recall_lcb=np.quantile(r,.025),recall_ucb=np.quantile(r,.975),
                  workload_lcb=np.quantile(w,.025),workload_ucb=np.quantile(w,.975))
    return result,replicas


def selection(surface,candidates,inverse=False):
    accepted=[];records=[]
    for c in candidates:
        rows=surface[surface.candidate_id==c['candidate_id']];reasons=[]
        assert sorted(rows.inner_fold)==[0,1]
        for r in rows.to_dict('records'):
            if r['bound_status']!='supported':reasons.append(f"fold{int(r['inner_fold'])}:{r['bound_status']}")
            elif not np.isfinite([r['recall_lcb'],r['workload_ucb'],r['custom_synthetic_f1']]).all():
                reasons.append(f"fold{int(r['inner_fold'])}:nonfinite_bounds_or_utility")
            else:
                if r['recall_lcb']<.6:reasons.append(f"fold{int(r['inner_fold'])}:recall_below_floor")
                if not inverse and r['workload_ucb']>1:reasons.append(f"fold{int(r['inner_fold'])}:workload_above_ceiling")
        utility=rows.custom_synthetic_f1.mean();work=rows.background_episodes_per_asset_day.mean()
        delay=rows.detected_delay_median_minutes.mean() if rows.detected_delay_median_minutes.notna().all() else np.inf
        records.append(dict(candidate_id=c['candidate_id'],feasible=not reasons,reasons=';'.join(reasons),
            equal_fold_custom_synthetic_f1=utility,equal_fold_workload=work,equal_fold_detected_delay=delay))
        if not reasons:accepted.append(((work,-utility,delay,c['candidate_id']) if inverse else
                                        (-utility,delay,work,c['candidate_id']),c))
    return (min(accepted,key=lambda v:v[0])[1] if accepted else None),pd.DataFrame(records)


def compare_values(actual,expected,label):
    for key,value in actual.items():
        if key not in expected:continue
        other=expected[key]
        if isinstance(value,(str,bool)):assert value==other,(label,key,value,other)
        else:np.testing.assert_allclose(value,other,rtol=2e-10,atol=2e-10,equal_nan=True,err_msg=f'{label}: {key}')


def interval_quality(stream):
    y=stream.observed.to_numpy(float);lo=stream.lower.to_numpy(float);hi=stream.upper.to_numpy(float)
    point=stream.point.to_numpy(float);valid=stream.available.to_numpy(bool)&np.isfinite(y)&np.isfinite(lo)&np.isfinite(hi)
    assert valid.all() and (lo<=hi).all()
    score=hi-lo+40*np.maximum(lo-y,0)+40*np.maximum(y-hi,0)
    return dict(observed_rows=len(y),empirical_coverage=np.mean((y>=lo)&(y<=hi)),
        mpiw_kWh=np.mean(hi-lo),winkler95_kWh=np.mean(score),mae_kWh=np.mean(abs(y-point)),
        rmse_kWh=np.sqrt(np.mean((y-point)**2)),nominal_level=.95,target_units='kWh')


def compare_matches(computed,saved,label):
    keys=['event_id','channel'];cols=['eligible','detected','episode_id','delay_minutes','followup_minutes',
                                      'detection_censored','incomplete_followup']
    a=computed.set_index(keys).sort_index()[cols].copy();b=saved.set_index(keys).sort_index()[cols].copy()
    assert not a.index.duplicated().any() and not b.index.duplicated().any()
    a.episode_id=a.episode_id.fillna('');b.episode_id=b.episode_id.fillna('')
    pd.testing.assert_frame_equal(a,b,check_dtype=False,rtol=2e-10,atol=2e-10,obj=label)


def recovery_rows(stream,clean,events):
    result=[]
    for group,part in stream.groupby('group_id',sort=True):
        fs=events[(events.group_id==group)&events.effective]
        if not len(fs):continue
        start=pd.to_datetime(fs.onset).min();end=pd.to_datetime(fs.end).max()
        times=pd.to_datetime(part.target_time);before=times<start;after=times>end
        truth=clean.observed.to_numpy()[part.index];covered=(truth>=part.lower)&(truth<=part.upper)
        if not before.any() or not after.any():
            result.append(dict(group_id=group,status='insufficient_recovery_support',recovery_minutes=np.nan,
                recovery_censored=True,followup_minutes=0.));continue
        baseline=covered[before].mean();window=max(1,min(24,int(after.sum())//4))
        tail=covered[after].to_numpy(float)
        means=np.convolve(tail,np.ones(window)/window,mode='valid')
        # pandas rolling uses compensated summation; compare with a small
        # rounding tolerance only for its exact frozen inclusive boundary.
        success=np.flatnonzero(abs(means-baseline)<=.05)
        at=(times[after].iloc[success[0]+window-1]-end).total_seconds()/60 if len(success) else np.nan
        result.append(dict(group_id=group,status='observed' if len(success) else 'right_censored',
            pre_coverage=baseline,window_steps=window,recovery_minutes=at,recovery_censored=not len(success),
            followup_minutes=(times[after].iloc[-1]-end).total_seconds()/60))
    return pd.DataFrame(result)


def audit(run,out):
    run=Path(run);out=Path(out)
    out.mkdir(parents=True,exist_ok=False)
    unit=run/'units/outer2_model42'
    manifest=json.loads((run/'checkpoint_manifest.json').read_text());spec=manifest['spec']
    complete=json.loads((unit/'COMPLETE.json').read_text());payload=json.loads((unit/'payload.json').read_text())
    assert spec['dataset']=='bdg2' and spec['outer_fold']==2 and spec['model_seed']==42
    assert spec['catalogue_seeds']==[42,43,44,45,46] and spec['horizon']==1
    assert sorted(p.name for p in (run/'units').iterdir())==['outer2_model42']
    for name,h in complete['hashes'].items():assert sha(unit/name)==h,(name,'hash mismatch')
    grid=spec['candidate_grid'];assert len(grid)==9
    surface=read(unit/'surface.csv.gz');outer=read(unit/'outer_metrics.csv.gz')
    assert len(surface)==18 and set(zip(surface.candidate_id,surface.inner_fold))=={
        (c['candidate_id'],i) for c in grid for i in [0,1]}
    primary,rejections=selection(surface,grid);inverse,inverse_rejections=selection(surface,grid,True)
    assert primary==payload['pipeline'];assert inverse==payload['inverse_recall_floor']['pipeline']
    assert payload['decision']==('selected' if primary else 'no_feasible_configuration')
    for table,name in [(rejections,'rejections'),(inverse_rejections,'inverse_rejections')]:
        saved=read(unit/(name+'.csv.gz')).fillna({'reasons':''})
        pd.testing.assert_frame_equal(table.set_index('candidate_id').sort_index(),
            saved.set_index('candidate_id').sort_index(),check_dtype=False,rtol=2e-10,atol=2e-10)
        table.to_csv(out/(name+'.csv'),index=False)
    subsets=dict(baseline=[c for c in grid if c['method']=='quantile_uncalibrated' and c['rule_id']=='single_sample'],
        conformal_only=[c for c in grid if c['method']=='cqr' and c['strategy']=='static' and c['rule_id']=='single_sample'],
        temporal=[c for c in grid if c['method']=='cqr' and c['strategy']=='static' and c['rule_id']!='single_sample'],full=grid)
    selected={k:selection(surface,cs)[0] for k,cs in subsets.items()}
    for k,c in selected.items():assert c==payload['independent_operating_points'][k]['pipeline']
    reference=primary or next(c for c in grid if c['method']=='cqr' and c['strategy']=='static' and c['rule_id']=='single_sample')
    rule=reference['rule_id'] if reference['rule_id']!='single_sample' else next(c['rule_id'] for c in grid if c['method']=='cqr' and c['strategy']=='static' and c['rule_id']!='single_sample')
    controls=[next(c for c in grid if c['method']==method and c['strategy']=='static' and c['rule_id']==r)
        for method,r in [('quantile_uncalibrated','single_sample'),('cqr','single_sample'),('cqr',rule)]]
    expected={c['candidate_id'] for c in controls+[reference]+[c for c in list(selected.values())+[inverse] if c]}
    expected.add('diagnostic_persistence_split_095_single_sample')
    assert set(outer.candidate_id)==expected and len(outer)==len(expected)
    assert {c['candidate_id'] for c in payload['outer_comparisons'] if c['candidate_id']}==expected
    assert payload['fits']==3 and sum(r['fit_invocations'] for r in payload['fit_records'])==3
    assert sum(r['identity'].get('sub_estimators',0)*r['fit_invocations'] for r in payload['fit_records'])==9
    fit_map={(r['role'],r['method']):r['fit_invocations'] for r in payload['fit_records']}
    assert len(fit_map)==len(payload['fit_records'])==4
    assert fit_map=={('inner0_selection','cqr'):1,('inner1_selection','cqr'):1,
                     ('outer_test','cqr'):1,('outer_test','persistence_split'):0}
    assert surface.groupby('role').fit_identity.nunique().eq(1).all()
    assert outer[outer.method.isin(['cqr','quantile_uncalibrated'])].fit_identity.nunique()==1
    summary=[];quality=[];groups_out=[];families_out=[];replicas_out=[];support_out=[];recovery_out=[]
    checked=dict(candidate_fold_cells=18,inner_catalogue_pairs=90,outer_catalogue_pairs=len(outer)*5,
        persisted_streams=0,contribution_rows=0,event_channel_records=0,bootstrap_cells=0,preflight_catalogues=0)
    preflight=run.parent/'preflight_20260913_v1'
    for prefix,table in [('',surface),('outer_',outer)]:
        cat=read(unit/(prefix+'catalogues.csv.gz'))
        scores=read(unit/(prefix+'event_scores.csv.gz'));saved_family=read(unit/(prefix+'family_attribution.csv.gz'))
        saved_groups=read(unit/(prefix+'group_workload.csv.gz'));saved_recovery=read(unit/(prefix+'recovery.csv.gz'))
        banks=dict(ordered_blocks(unit/(prefix+'contributions.csv.gz'),['role','candidate_id']))
        # Immutable preflight schedules independently verify unchanged event incidence.
        roles=table.role.unique()
        for role in roles:
            events=cat[cat.inner_fold==int(role[5])] if not prefix else cat
            for seed in [42,43,44,45,46]:
                saved=read(preflight/f'bdg2_f2_{role}_e{seed}_catalogue.csv.gz')
                actual=events[events.catalogue_seed==seed][saved.columns].reset_index(drop=True)
                pd.testing.assert_frame_equal(actual,saved,check_dtype=False,rtol=0,atol=0)
                checked['preflight_catalogues']+=1
            for f,v in STRATA:
                e=events[(events.family==f)&(events.severity==v)]
                support_out.append(dict(role=role,family=f,severity=v,requested=len(e),effective=int(e.effective.sum()),
                    distinct_effective_onsets=len(e[e.effective][['group_id','onset']].drop_duplicates()),
                    placed=int(e.placed.sum()),null=int(e.null.sum()),rejected=int(e.rejected.sum())))
        for (role,cid),block in ordered_blocks(unit/(prefix+'streams.csv.gz'),['role','candidate_id']):
            row=table[(table.role==role)&(table.candidate_id==cid)].iloc[0].to_dict()
            events=cat[cat.inner_fold==int(role[5])] if not prefix else cat
            streams={int(seed):part.reset_index(drop=True) for seed,part in block.groupby('catalogue_seed',sort=False)}
            assert set(streams)=={-1,42,43,44,45,46};clean=streams[-1]
            for stream in streams.values():
                latest=pd.to_datetime(stream.latest_released_target,errors='coerce')
                origins=pd.to_datetime(stream.origin_time)
                assert (latest.isna()|(latest<=origins)).all(),'future score released before observation'
                assert np.isfinite(stream.loc[stream.available,'observed']).all()
                assert stream.loc[~stream.available,'observed'].isna().all()
            assert clean.stream_role.eq('clean').all() and clean.group_id.nunique()==10
            ce,_,_=episodes_and_matches(clean,row,events.iloc[:0]);parts=[];per_events=[]
            for seed in [42,43,44,45,46]:
                stream=streams[seed];assert stream.stream_role.eq('corrupted').all()
                pd.testing.assert_frame_equal(clean[['row_id','group_id','origin_time','target_time']],
                    stream[['row_id','group_id','origin_time','target_time']])
                e=events[events.catalogue_seed==seed]
                ep,pe,flags=episodes_and_matches(stream,row,e)
                saved=scores[(scores.role==role)&(scores.candidate_id==cid)&(scores.catalogue_seed==seed)]
                compare_matches(pe,saved,f'{role}/{cid}/{seed}')
                checked['event_channel_records']+=len(pe)
                parts.append(contributions(clean,ce,ep,pe,flags['combined']));per_events.append(pe)
                rec=recovery_rows(stream,clean,e)
                oldrec=saved_recovery[(saved_recovery.role==role)&(saved_recovery.candidate_id==cid)&(saved_recovery.catalogue_seed==seed)]
                for r in rec.to_dict('records'):
                    compare_values(r,oldrec[oldrec.group_id==r['group_id']].iloc[0].to_dict(),'recovery')
                recovery_out.append(rec.assign(role=role,candidate_id=cid,catalogue_seed=seed))
            bank=sum(parts[1:],parts[0].copy())
            bank[['exposure_days','clean_episodes','time_in_alert_days']]/=5
            savedbank=banks.pop((role,cid))
            np.testing.assert_array_equal(clean.row_id.to_numpy(),savedbank.row_id.to_numpy())
            np.testing.assert_allclose(bank[NAMES],savedbank[NAMES],rtol=2e-10,atol=2e-10)
            checked['contribution_rows']+=len(bank);checked['persisted_streams']+=6
            pe=pd.concat(per_events,ignore_index=True);metrics=summarise(bank,pe)
            draws=payload['outer_resampling_draws'] if prefix else payload['resampling_draws'][role[5]]
            ci,replicas=bounds(bank,clean.group_id.to_numpy(),events,draws)
            compare_values(ci,row,'confidence bounds');checked['bootstrap_cells']+=1
            if 'resampling_hash' in row and pd.notna(row['resampling_hash']):
                assert hashlib.sha256(json.dumps(draws,sort_keys=True).encode()).hexdigest()==row['resampling_hash']
            replicas_out.append(replicas.assign(role=role,candidate_id=cid))
            gr=[]
            for group in sorted(clean.group_id.unique()):
                b=bank[clean.group_id==group];t=b.sum();n=sum(t[f'n{j}'] for j in range(21));tp=sum(t[f'tp{j}'] for j in range(21))
                g=dict(group_id=group,asset_days=t.exposure_days,clean_episodes=t.clean_episodes,
                    episodes_per_asset_day=t.clean_episodes/t.exposure_days,event_recall_micro=tp/n if n else np.nan,
                    n_events=int(n),n_detected=int(tp))
                old=saved_groups[(saved_groups.role==role)&(saved_groups.candidate_id==cid)&(saved_groups.group_id==group)].iloc[0]
                compare_values(g,old.to_dict(),'group workload');gr.append(g)
                groups_out.append(dict(role=role,candidate_id=cid,**g))
            gr=pd.DataFrame(gr);calendar=clean.target_time.nunique()/24
            metrics.update(equal_group_episode_rate=gr.episodes_per_asset_day.mean(),equal_group_event_recall=gr.event_recall_micro.mean(),
                portfolio_calendar_days=calendar,portfolio_episodes_per_calendar_day=gr.clean_episodes.sum()/calendar)
            compare_values(metrics,row,'surface metrics')
            for f,v in STRATA:
                for channel in CHANNELS:
                    sub=pe[(pe.family==f)&(pe.severity==v)&(pe.channel==channel)&pe.eligible]
                    vals=dict(n_events=len(sub),n_detected=int(sub.detected.sum()),recall=sub.detected.mean())
                    old=saved_family[(saved_family.role==role)&(saved_family.candidate_id==cid)&(saved_family.family==f)&
                        (saved_family.severity==v)&(saved_family.channel==channel)].iloc[0]
                    compare_values(vals,old.to_dict(),'family attribution')
                    families_out.append(dict(role=role,candidate_id=cid,family=f,severity=v,channel=channel,**vals))
            summary.append(dict(role=role,candidate_id=cid,method=row['method'],rule_id=row['rule_id'],strategy=row['strategy'],
                inner_fold=int(role[5]) if not prefix else -1,**metrics,**ci))
            quality.append(dict(role=role,candidate_id=cid,**interval_quality(clean)))
            print(json.dumps(dict(recomputed=role,candidate_id=cid,streams=6,events=metrics['n_events'])),flush=True)
        assert not banks,'extra contribution cells'
    recalculated=pd.DataFrame(summary)
    assert selection(recalculated[recalculated.inner_fold>=0],grid)[0]==primary
    assert selection(recalculated[recalculated.inner_fold>=0],grid,True)[0]==inverse
    assert checked['persisted_streams']==6*(18+len(outer))
    pd.DataFrame(summary).to_csv(out/'recomputed_metrics.csv',index=False)
    pd.DataFrame(quality).to_csv(out/'clean_interval_quality.csv',index=False)
    pd.DataFrame(groups_out).to_csv(out/'group_metrics.csv',index=False)
    pd.DataFrame(families_out).to_csv(out/'stratum_channel_metrics.csv',index=False)
    pd.DataFrame(support_out).to_csv(out/'event_support.csv',index=False)
    pd.concat(recovery_out,ignore_index=True).to_csv(out/'recovery.csv',index=False)
    pd.concat(replicas_out,ignore_index=True).to_csv(out/'bootstrap_replicates.csv.gz',index=False)
    result=dict(passed=True,scope='independent_saved_stream_event_contribution_draw_recomputation',
        learned_fits=0,decision=payload['decision'],selected_candidate=primary['candidate_id'] if primary else None,
        inverse_selected_candidate=inverse['candidate_id'] if inverse else None,
        **checked,outer_metric_cells=len(outer),fit_objects=3,quantile_sub_estimators=9,
        unchanged_preflight_catalogues=True,unit_file_hashes_checked=len(complete['hashes']),
        source_sha256=sha(__file__),global_study_ready=False)
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args();audit(args.run,args.out)
