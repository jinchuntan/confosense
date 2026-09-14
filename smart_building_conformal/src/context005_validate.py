"""Independent C validator: scalar inputs, direct estimators, releases and episodes."""
import math
import numpy as np
import pandas as pd
from .intervals005_common import Operations,PhaseMeter,atomic,tree,load_owner,read,csv,signature,digest
from .context005_spec import table,POLICIES,context_positions
from .context005_data import load_real,synthetic
from .context005_features import bounded_frame
from .intervals005_validate import independent_alert

def scalar_inputs(frame,meta,cfg,horizon,freq,season,columns,observed,available):
    """Direct scalar features without production causal_features/inject/pandas rolling."""
    sensor={pd.Timestamp(t):float(v) if flag else None for t,v,flag in zip(meta.target_time,observed,available)}
    values=[];filled=[];last=None
    for t,row in frame.iterrows():
        value=sensor.get(pd.Timestamp(t),float(row.target))
        if value is not None and np.isfinite(value):last=value
        filled.append(last)
    index={pd.Timestamp(t):i for i,t in enumerate(frame.index)}
    for r in meta.itertuples():
        i=index[pd.Timestamp(r.origin_time)];target=pd.Timestamp(r.target_time);row={}
        for k in cfg['target_lags']:row[f'target_lag_{k}']=filled[i-k] if i>=k else np.nan
        if season is not None:
            row['target_daily_lag']=filled[i-(season-horizon)]
            if cfg.get('include_weekly'):row['target_weekly_lag']=filled[i-(7*season-horizon)]
        for w in cfg['rolling_windows']:
            v=np.asarray(filled[max(0,i-w+1):i+1],float);v=v[np.isfinite(v)]
            row[f'target_rollmean_{w}']=float(sum(v)/len(v)) if len(v)>=max(2,w//2) else np.nan
            row[f'target_rollstd_{w}']=math.sqrt(sum((v-v.mean())**2)/(len(v)-1)) if len(v)>=max(2,w//2) else np.nan
        for name,value,period in [('hour',target.hour+target.minute/60,24),('dow',target.dayofweek,7)]:
            row[name+'_sin']=math.sin(2*math.pi*value/period);row[name+'_cos']=math.cos(2*math.pi*value/period)
        for col in cfg.get('covariates',[]):
            if col in frame:row[col]=frame.iloc[i][col]
        for col in frame:
            if col.endswith('_was_missing'):row[col]=float(frame.iloc[i][col])
        if pd.Timestamp(r.origin_time) in sensor and 'target_was_missing' in columns:row['target_was_missing']=float(sensor[pd.Timestamp(r.origin_time)] is None)
        values.append([row[c] for c in columns])
    return pd.DataFrame(values,columns=columns)

def scalar_observations(frame,meta,event):
    """Independent fault algebra and RNG; never uses operational corruption()."""
    truth=frame.loc[pd.DatetimeIndex(meta.target_time),'target'].to_numpy(float);v=truth.copy();flags=np.ones(len(v),bool)
    if event is None:return truth,v,flags
    ids=list(meta.row_id);a=ids.index(event['onset_row_id']);b=ids.index(event['end_row_id'])+1;n=b-a;s=float(event['severity']);family=event['family']
    fraction={.5:.25,1.:.5,2.:1.}[s];length=math.ceil(n*fraction);start=(n-length)//2
    if family=='random_missing':flags[a:b]=np.random.default_rng(int(event['mask_seed'])).random(n)>=.2*s
    elif family=='block_missing':flags[a+start:a+start+length]=False
    elif family=='dropout':v[a+start:a+start+length]=0
    elif family=='stuck':v[a+start:a+start+length]=v[a+start-1] if a+start else float(frame.loc[frame.index<meta.target_time.iloc[0],'target'].dropna().iloc[-1])
    else:
        grid=np.linspace(0.,1.,n)
        for j in range(n):
            u=grid[j];shape=min(4*u,1,4*(1-u)) if family=='bias' else u if family=='drift' else 1
            v[a+j]+=int(event['sign'])*s*float(event['sigma'])*shape
    v[~flags]=np.nan;return truth,v,flags

def scalar_stream(model,X,meta,observed,available,control):
    """Independent chronological array state, native tails versus online max-score."""
    y=np.asarray(observed);n=len(y);method=control['method'];level=.95
    if method=='persistence_split':point=X.target_lag_0.to_numpy();lower=point;upper=point;native_lo=point-model.radius;native_hi=point+model.radius
    else:
        sub=model.owner._mapie_quantile_regressor.estimators_;pred=[e.predict(X.to_numpy()) for e in sub]
        lower,upper,point=pred;scores=model.owner._mapie_quantile_regressor.conformity_scores_
        q=np.quantile(scores[:2],.975*(1+1/scores.shape[1]),axis=1,method='higher')
        native_lo=np.minimum(lower-q[0],upper+q[1]);native_hi=np.maximum(lower-q[0],upper+q[1])
    lo=np.zeros(n);hi=np.zeros(n);release=[];updates=[];cal=model.calibration.copy();cal.target_time=pd.to_datetime(cal.target_time)
    def quantile(v):
        rank=math.ceil((len(v)+1)*level)
        return sorted(v)[rank-1] if 1<=rank<=len(v) else None
    base=quantile(cal.score.tolist());times=pd.DatetimeIndex(meta.target_time);origins=pd.DatetimeIndex(meta.origin_time)
    # Individual variant is always one original uninterrupted segment.
    if meta.group_id.nunique()!=1 or not times.to_series().diff().dropna().eq(times[1]-times[0]).all():raise ValueError('scalar validator requires one original segment')
    group=str(meta.group_id.iloc[0]);local=cal[cal.group_id.astype(str)==group]
    if local.empty:local=cal
    history=local.sort_values('target_time',kind='stable').score.tolist();q=base;cursor=0
    for i in range(n):
        while cursor<i and times[cursor]<=origins[i]:
            j=cursor;cursor+=1
            if available[j]:
                value=max(lower[j]-y[j],y[j]-upper[j]) if method!='persistence_split' else abs(y[j]-point[j]);history.append(float(value))
                release.append(dict(row_id=meta.row_id.iloc[j],score=value,released_at_origin=str(origins[i])))
        if control['strategy']=='rolling' and i%control['every']==0:
            pool=history[-control['window']:];proposed=quantile(pool) if len(pool)>=50 else None
            status='updated' if proposed is not None else 'held_insufficient_score_or_rank_support'
            if proposed is not None:q=proposed
            updates.append(dict(origin_time=str(origins[i]),pool_n=len(pool),correction_lower=q,correction_upper=q,status=status))
        if method=='quantile_uncalibrated':lo[i],hi[i]=sorted((lower[i],upper[i]))
        elif control['strategy']=='static':lo[i],hi[i]=native_lo[i],native_hi[i]
        else:lo[i],hi[i]=sorted((lower[i]-q,upper[i]+q))
    return dict(lower=lo,upper=hi,point=point,raw_lower=lower,raw_upper=upper,releases=pd.DataFrame(release),updates=pd.DataFrame(updates))

def validate(design,out,receipt):
    from pathlib import Path
    from .conditional_context005 import verify_complete,data_identity
    root=Path(out);before=tree(root);p=verify_complete(design,root);m=p['manifest'];dest=Path(receipt)
    if dest.exists():raise ValueError('preserve validation evidence')
    dest.mkdir(parents=True);checks=[];maximum=0.;reconstructed_events=[]
    def close(a,b,label,tol=1e-10):
        nonlocal maximum
        aa=np.asarray(a,float);bb=np.asarray(b,float)
        diff=float(np.nanmax(np.abs(aa-bb))) if aa.size else 0.;maximum=max(maximum,diff)
        np.testing.assert_allclose(aa,bb,atol=tol,rtol=1e-10,equal_nan=True,err_msg=label);checks.append(dict(check=label,n=aa.size,maximum_difference=diff))
    with Operations(forbid=True),PhaseMeter() as meter:
        d=synthetic(m['dataset']) if m['synthetic'] else load_real(m['dataset'],m['outer_fold'])
        if signature(data_identity(d))!=signature(p['data_identity']):raise ValueError('independent source identity')
        models=load_owner(root/'stages/controls/controls.pkl');meta=d['meta'].iloc[d['roles']['outer_test']].reset_index(drop=True)
        variants=table(root/'stages/tables/variants.csv');ctxmap=d['contexts'].set_index('context_id').to_dict('index')
        independent_hashes={};unique=0
        for vr in variants.to_dict('records'):
            ctx=dict(ctxmap[vr['context_id']],context_id=vr['context_id']);ix=context_positions(meta,ctx);local=meta.iloc[ix].reset_index(drop=True)
            events=d['schedules'][d['schedules'].context_id==vr['context_id']].to_dict('records');event=None if vr['ordinal']==0 else events[int(vr['ordinal'])-1]
            base,season=bounded_frame(d['series'],local,d['fcfg'],d['horizon']);truth,obs,avail=scalar_observations(base,local,event)
            X=scalar_inputs(base,local,d['fcfg'],d['horizon'],d['frequency'],season,d['X'].columns,obs,avail)
            path=root/'stages'/vr['canonical_stage'];saved=table(path/'features.csv.gz')
            close(saved[d['X'].columns],X,'scalar_causal_features_'+vr['stage'])
            observations=table(path/'observations.csv.gz');close(observations.observed,obs,'independent_observations')
            if observations.available.tolist()!=avail.tolist():raise ValueError('independent availability mismatch')
            ident=read(path/'identity.json')
            # Exact saved-input/observation hashes as well as scalar numeric reconstruction.
            from .context005_features import feature_hash
            if feature_hash(saved[d['X'].columns])!=ident['feature_hash']:raise ValueError('saved feature hash mismatch')
            if signature(np.nan_to_num(obs,nan=-1.23456789e307).tolist())!=ident['observation_hash']:raise ValueError('independent observation hash mismatch')
            if vr['alias']:
                alias=read(root/'stages'/vr['stage']/'alias.json')
                if alias['canonical_stage']!=vr['canonical_stage'] or alias['realization_hash']!=vr['realization_hash']:raise ValueError('alias identity mismatch')
            else:
                unique+=1
                for control in m['controls']:
                    cid=control['control_id'];model=models[control['method']];scalar=scalar_stream(model,X,local,obs,avail,control)
                    stream=table(path/(cid+'_issued.csv.gz'))
                    for col in ['lower','upper','point','raw_lower','raw_upper']:close(stream[col],scalar[col],col+'_'+vr['stage'])
                    released=table(path/(cid+'_released.csv.gz'));expected=scalar['releases']
                    if len(released)!=len(expected):raise ValueError('scalar release count')
                    if len(released):
                        if released.row_id.tolist()!=expected.row_id.tolist() or released.released_at_origin.tolist()!=expected.released_at_origin.tolist():raise ValueError('release order/identity')
                        close(released.score,expected.score,'scalar_released_scores')
                    updates=table(path/(cid+'_updates.csv.gz'));eu=scalar['updates']
                    if len(updates)!=len(eu):raise ValueError('scalar update count')
                    if len(updates):
                        close(updates[['pool_n','correction_lower','correction_upper']],eu[['pool_n','correction_lower','correction_upper']],'scalar_updates')
                        if updates.status.tolist()!=eu.status.tolist():raise ValueError('held update status')
                    for rule in m['rules']:
                        flags,episodes=independent_alert(stream,d['frequency'],rule['k'],rule['m']);prefix=cid+'_'+rule['rule_id']
                        consumed=table(path/(prefix+'_alerts.csv.gz'));eps=table(path/(prefix+'_episodes.csv.gz'))
                        for channel,values in flags.items():
                            if consumed['alert_'+channel].tolist()!=values.tolist():raise ValueError('independent alert flags')
                        cols=['channel','group_id','segment_id','start_index','onset']
                        if set(map(tuple,eps[cols].to_numpy()))!=set(map(tuple,episodes[cols].to_numpy())):raise ValueError('independent episode onsets')
            if event:
                # Each variant has only one event; earliest new onset, never pre-active.
                for control in m['controls']:
                    for rule in m['rules']:
                        eps=table(path/(control['control_id']+'_'+rule['rule_id']+'_episodes.csv.gz'))
                        onset=pd.Timestamp(event['onset']);policy=POLICIES[m['dataset']];tau=(policy['duration']-1+policy['tolerance'])*float(d['frequency']/pd.Timedelta('1min'))
                        for channel in ['numerical_only','availability_only','combined']:
                            candidates=[(pd.Timestamp(e.onset)-onset)/pd.Timedelta('1min') for e in eps.itertuples() if e.channel==channel and e.group_id==str(ctx['group_id']) and 0<=(pd.Timestamp(e.onset)-onset)/pd.Timedelta('1min')<=tau]
                            detected=bool(event['effective']) and bool(candidates);delay=min(candidates) if detected else np.nan
                            reconstructed_events.append(dict(context_id=vr['context_id'],family=event['family'],severity=event['severity'],replicate=event['replicate'],control_id=control['control_id'],rule_id=rule['rule_id'],channel=channel,detected=detected,restricted_delay_minutes=delay if detected else tau))
        actual=table(root/'stages/tables/events.csv.gz');expected=pd.DataFrame(reconstructed_events);keys=['context_id','family','severity','replicate','control_id','rule_id','channel']
        a=actual.set_index(keys).sort_index();b=expected.set_index(keys).sort_index()
        if not a.index.equals(b.index):raise ValueError('event ledger completeness')
        close(a.detected,b.detected,'event_detection');close(a.restricted_delay_minutes,b.restricted_delay_minutes,'censored_delay')
        # Independent equal-context aggregation, including aliases in fixed slots.
        ss=table(root/'stages/tables/strata.csv')
        for row in ss.to_dict('records'):
            f=actual[(actual.control_id==row['control_id'])&(actual.rule_id==row['rule_id'])&(actual.channel==row['channel'])&(actual.family==row['family'])&(actual.severity==row['severity'])]
            positive=f[f.effective&f.eligible];means=[g.detected.mean() for _,g in positive.groupby('context_id')]
            if len(means)!=row['effective_contexts'] or len(f)!=row['scheduled']:raise ValueError('equal-context denominator')
            if means:close(row['recall'],np.mean(means),'equal_context_recall')
        work=table(root/'stages/tables/fullstream_workload.csv')
        fullchecks=0
        for path in sorted((root/'stages').glob('fullstream_*')):
            observations=table(path/'observations.csv.gz');local=observations[['row_id','group_id','origin_time','target_time']].copy()
            local.origin_time=pd.to_datetime(local.origin_time);local.target_time=pd.to_datetime(local.target_time)
            base,season=bounded_frame(d['series'],local,d['fcfg'],d['horizon']);truth,obs,avail=scalar_observations(base,local,None)
            X=scalar_inputs(base,local,d['fcfg'],d['horizon'],d['frequency'],season,d['X'].columns,obs,avail)
            saved=table(path/'features.csv.gz');close(saved[d['X'].columns],X,'fullstream_scalar_features')
            for control in m['controls']:
                cid=control['control_id'];stream=table(path/(cid+'_issued.csv.gz'));scalar=scalar_stream(models[control['method']],X,local,obs,avail,control)
                close(stream[['lower','upper']],np.column_stack([scalar['lower'],scalar['upper']]),'fullstream_scalar_bounds')
                for rule in m['rules']:
                    flags,episodes=independent_alert(stream,d['frequency'],rule['k'],rule['m'])
                    for channel,values in flags.items():
                        row=work[(work.control_id==cid)&(work.rule_id==rule['rule_id'])&(work.channel==channel)&(work.group_id==str(local.group_id.iloc[0]))]
                        if len(row)!=1:raise ValueError('fullstream workload missing or duplicate group')
                        row=row.iloc[0]
                        if row.alert_rows!=sum(values) or row.episodes!=sum(episodes.channel==channel):raise ValueError('fullstream workload independent reconstruction')
                        fullchecks+=1
        for _,part in work.groupby(['control_id','rule_id','channel']):
            if part.eligible_rows.sum()!=len(meta):raise ValueError('full original exposure multiplied or tails lost')
            close(part.asset_days.sum(),len(meta)*float(d['frequency']/pd.Timedelta('1D')),'original_exposure')
        if tree(root)!=before:raise ValueError('validation mutated scientific artifacts')
    csv(dest/'independent_checks.csv',pd.DataFrame(checks));csv(dest/'independently_reconstructed_events.csv.gz',expected)
    result=dict(passed=True,models_fitted=0,calibrators_fitted=0,contexts=len(d['contexts']),scheduled_fault_slots=len(d['schedules']),unique_context_streams=unique,
        independently_reconstructed_event_rows=len(expected),fullstream_workload_checks=fullchecks,maximum_absolute_difference=maximum,checks=len(checks),source_artifacts_unchanged=True,resources=meter.result,actual_exit_status=0)
    atomic(dest/'validation.json',result);return result
