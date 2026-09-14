"""Load verified published C roles; synthetic fixtures never share real settings."""
import hashlib,pickle
from types import SimpleNamespace
import numpy as np
import pandas as pd
from .context005_spec import *
from .context005_features import causal_features
from .operational004_design import seed_for,STRATA
from .operational004_events import corruption
from .split_integrity import membership_hash

def load_real(dataset,fold):
    path=CACHE/(dataset+'_prepared.pkl');identity=read(BASE/'validation.json')
    expected=next(x['sha256'] for x in identity['input_caches'] if Path(x['path']).name==path.name)
    if digest(path)!=expected:raise ValueError('prepared cache checksum differs from published source')
    with path.open('rb') as f:c=pickle.load(f)
    m=table(BASE/(dataset+'_operational_membership_observations.csv.gz'))
    meta=c['w']['meta'].copy().reset_index(drop=True)
    if meta.row_id.tolist()!=m.row_id.tolist():raise ValueError('operational membership differs from cache')
    np.testing.assert_array_equal(c['w']['y'],m.y.to_numpy(float))
    roles={r:role_rows(m,fold,r) for r in ['final_fit','final_calibration','outer_test']}
    role_summary=table(BASE/'proposal_roles.csv')
    for r,idx in roles.items():
        expected_role=role_summary[(role_summary.dataset==dataset)&(role_summary.outer_fold==fold)&(role_summary.role==r)].iloc[0]
        if membership_hash(meta,idx)!=expected_role.membership_hash:raise ValueError('published role hash mismatch')
    for a,b in [('final_fit','final_calibration'),('final_calibration','outer_test')]:
        if meta.iloc[roles[a]].target_time.max()>=meta.iloc[roles[b]].origin_time.min():raise ValueError('role temporal boundary')
        if dataset=='rico' and set(meta.iloc[roles[a]].group_id)&set(meta.iloc[roles[b]].group_id):raise ValueError('RICO split run')
    ctx=table(BASE/'challenge_contexts.csv');sch=table(BASE/'challenge_schedules.csv.gz')
    filt=lambda f:f[(f.dataset==dataset)&(f.outer_fold==fold)&(f.role=='outer_test')].copy().reset_index(drop=True)
    ctx,sch=filt(ctx),filt(sch)
    freq=pd.Timedelta(POLICIES[dataset]['frequency'])
    if c['prepared'].freq!=freq:raise ValueError('wrong source cadence')
    return dict(dataset=dataset,fold=fold,synthetic=False,meta=meta,X=c['w']['X'].reset_index(drop=True),
        y=np.asarray(c['w']['y'],float),roles=roles,contexts=ctx,schedules=sch,
        series=c['segmented'].series,fcfg=c['fcfg'],frequency=freq,horizon=POLICIES[dataset]['horizon'],
        cache_sha256=expected,source_inputs=source_inputs(dataset))

def synthetic(dataset):
    """Two original evaluation groups, all 21 strata and two slots, fixed minima.

    520 fitting and 420 calibration observations; PLEIA two 144-row contexts
    per group plus nine tail readings, RICO one 221-row context per whole run.
    One PLEIA context is constant zero to retain numerical null realizations.
    """
    p=POLICIES[dataset];freq=pd.Timedelta(p['frequency']);h=p['horizon'];season=144 if dataset!='rico' else None
    cfg=dict(target_lags=[0,1,2,5],rolling_windows=[6,24],include_weekly=False,covariates=['ambient'])
    rows=[];xs=[];ys=[];series=[];roles={r:[] for r in ['final_fit','final_calibration','outer_test']};count=0
    for g,(role,n) in enumerate([('final_fit',520),('final_calibration',420),('outer_test',297 if dataset!='rico' else 221),('outer_test',297 if dataset!='rico' else 221)]):
        group=f'synthetic_g{g}';start=pd.Timestamp('2020-01-01')+pd.Timedelta(days=g*40)
        hist=150;times=pd.date_range(start,periods=hist+n+h,freq=freq);x=np.arange(len(times),dtype=float)
        # An autoregressive fixture makes the observation-to-predictor path
        # identifiable even with three tiny boosting iterations. Seasonal and
        # calendar covariates cannot reconstruct its innovations.
        values=np.empty(len(x));values[0]=5.;rng=np.random.default_rng(100+g)
        for i in range(1,len(x)):values[i]=5+.98*(values[i-1]-5)+rng.normal(0,.2)
        if g==3:values[hist+h:hist+h+144]=0
        f=pd.DataFrame(dict(target=values,target_was_missing=np.zeros(len(x)),ambient=np.cos(x/30)),index=times)
        s=SimpleNamespace(group_id=group,frame=f,freq=freq,season_steps=season,metadata={'phase':g%2+1});series.append(s)
        meta=pd.DataFrame(dict(row_id=[signature([dataset,group,i]) for i in range(n)],group_id=group,
            origin_time=times[hist:hist+n],target_time=times[hist+h:hist+n+h]))
        columns=['target_lag_0','target_lag_1','target_lag_2','target_lag_5']+(['target_daily_lag'] if season else [])
        columns+=['target_rollmean_6','target_rollstd_6','target_rollmean_24','target_rollstd_24','hour_sin','hour_cos','dow_sin','dow_cos','ambient','target_was_missing']
        X=causal_features(f,meta,h,freq,season,cfg,columns);xs.append(X);ys.append(values[hist+h:hist+n+h]);rows.append(meta)
        roles[role].extend(range(count,count+n));count+=n
    meta=pd.concat(rows,ignore_index=True);y=np.concatenate(ys);roles={k:np.array(v) for k,v in roles.items()}
    test=meta.iloc[roles['outer_test']].reset_index(drop=True);truth=y[roles['outer_test']];contexts=[];schedules=[]
    for group,part in test.groupby('group_id',sort=True):
        ix=part.index.to_numpy();size=144 if dataset!='rico' else len(ix)
        for a in range(0,len(ix)-size+1,size):
            rr=ix[a:a+size];j=p['warmup']+2;pick=rr[j:j+p['duration']];cid=signature([VERSION,'synthetic',dataset,group,a])[:20]
            ctx=dict(dataset=dataset,outer_fold=2,role='outer_test',context_id=cid,group_id=group,segment_id=group+':segment:0',
                onset_offset=j,duration=p['duration'],warmup=p['warmup'],followup=p['followup'],context_rows=size,sigma=1.,
                context_start_row_id=test.iloc[rr[0]].row_id,context_end_row_id=test.iloc[rr[-1]].row_id,
                onset_row_id=test.iloc[pick[0]].row_id,onset=str(test.iloc[pick[0]].target_time),context_row_hash=signature(test.iloc[rr].row_id.tolist()))
            contexts.append(ctx)
            for family,severity in STRATA:
                for rep,sign in [(42,-1),(43,1)]:
                    seed=seed_for('amendment005',cid,family,severity,rep)
                    v,flags=corruption(truth[pick],family,severity,1.,sign,np.random.default_rng(seed),truth[rr[j-1]])
                    effective=bool((~flags).any() or np.any(v[flags]!=truth[pick][flags]))
                    schedules.append(dict(dataset=dataset,outer_fold=2,role='outer_test',context_id=cid,group_id=group,family=family,
                        severity=severity,replicate=rep,sign=sign,mask_seed=str(seed),sigma=1.,onset=ctx['onset'],onset_row_id=ctx['onset_row_id'],
                        end_row_id=test.iloc[pick[-1]].row_id,requested=True,hostable=True,placed=True,effective=effective,null=not effective,rejected=False,
                        changed_values=int(np.sum(flags&(np.nan_to_num(v)!=truth[pick]))),unavailable_readings=int((~flags).sum()),
                        mask_hash=signature(flags.tolist()),observed_hash=signature(np.nan_to_num(v,nan=-1.23456789e307).tolist())))
    return dict(dataset=dataset,fold=2,synthetic=True,meta=meta,X=pd.concat(xs,ignore_index=True),y=y,roles=roles,
        contexts=pd.DataFrame(contexts),schedules=pd.DataFrame(schedules),series=series,fcfg=cfg,frequency=freq,horizon=h,
        cache_sha256=None,source_inputs={})
