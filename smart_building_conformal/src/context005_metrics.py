"""Conditional equal-context endpoint and original-stream workload accounting."""
import numpy as np
import pandas as pd
from .operational004_design import STRATA
from .unit_checkpoint import signature

def conditional_summary(events,min_contexts=5):
    rows=[];macro=[]
    for key,group in events.groupby(['control_id','rule_id','channel'],sort=True):
        for family,severity in STRATA:
            sub=group[(group.family==family)&(group.severity==severity)]
            positive=sub[sub.effective & sub.eligible]
            context=positive.groupby('context_id',sort=True).agg(detected=('detected','mean'),delay=('restricted_delay_minutes','mean'))
            found=positive[positive.detected]
            rows.append(dict(zip(['control_id','rule_id','channel'],key),family=family,severity=severity,
                scheduled=len(sub),effective=int(sub.effective.sum()),null=int(sub['null'].sum()),aliases=int(sub.alias.sum()),
                effective_contexts=len(context),supported=len(context)>=min_contexts,
                recall=float(context.detected.mean()) if len(context) else np.nan,
                misses=int((~positive.detected).sum()),detected=int(positive.detected.sum()),
                detected_delay_median=float(found.delay_minutes.median()) if len(found) else np.nan,
                detected_delay_q90=float(found.delay_minutes.quantile(.9)) if len(found) else np.nan,
                restricted_mean_detection_minutes=float(context.delay.mean()) if len(context) else np.nan))
        r=rows[-21:];supported=all(x['supported'] for x in r)
        macro.append(dict(zip(['control_id','rule_id','channel'],key),conditional_context_macro=np.mean([x['recall'] for x in r]) if supported else np.nan,
            status='supported_point_estimate' if supported else 'unavailable_missing_distinct_context_support',supported_strata=sum(x['supported'] for x in r),
            inference_status='single_model_seed_descriptive',endpoint='C_effective_fault_conditional_context'))
    return pd.DataFrame(rows),pd.DataFrame(macro)

def original_contributions(events):
    pos=events[events.effective & events.eligible]
    keys=['dataset','outer_fold','model_seed','control_id','rule_id','channel','context_id','original_segment_id','group_id','family','severity']
    return pos.groupby(keys,as_index=False,dropna=False).agg(recall=('detected','mean'),restricted_delay=('restricted_delay_minutes','mean'),effective_slots=('detected','size'))

def interval_diagnostics(stream,truth):
    lo=stream.lower.to_numpy();hi=stream.upper.to_numpy();observed=stream.observed.to_numpy();available=stream.available.to_numpy(bool)
    result={}
    for label,y,mask in [('clean_counterfactual',np.asarray(truth),np.ones(len(truth),bool)),('corrupted_observation',observed,available)]:
        n=int(mask.sum());covered=(lo[mask]<=y[mask])&(y[mask]<=hi[mask]);width=hi[mask]-lo[mask]
        winkler=width+40*np.maximum(lo[mask]-y[mask],0)+40*np.maximum(y[mask]-hi[mask],0)
        result[label]=dict(n=n,unavailable_n=len(truth)-n,coverage=float(covered.mean()) if n else None,mpiw=float(width.mean()) if n else None,winkler=float(winkler.mean()) if n else None)
    return result

def inference(contributions,contexts,dataset,expected_seeds=(42,43,44,45,46)):
    """Paired draws carry all strata/controls, seeds averaged within contexts.

    Returns draw indices even when outcomes are degenerate. No row/slot bootstrap.
    Single-seed pilots are descriptive and never enter population intervals.
    """
    seedsets=contributions.groupby(['context_id','control_id','rule_id','channel','family','severity']).model_seed.agg(lambda v:tuple(sorted(set(v))))
    if not seedsets.map(lambda v:v==tuple(expected_seeds)).all():
        return pd.DataFrame(),dict(status='unavailable_incomplete_model_seeds',required_seeds=list(expected_seeds),draws=[])
    keys=['context_id','control_id','rule_id','channel','family','severity']
    pooled=contributions.groupby(keys,as_index=False).recall.mean()
    # Check the full original 21-stratum estimand before drawing anything.
    for _,part in pooled.groupby(['control_id','rule_id','channel']):
        support=part.groupby(['family','severity']).context_id.nunique()
        if len(support)!=21 or support.min()<5:
            return pd.DataFrame(),dict(status='unavailable_distinct_context_stratum_support',draws=[])
    ctx=contexts.drop_duplicates('context_id').reset_index(drop=True);n=len(ctx);rng=np.random.default_rng(20240601)
    if n<5:return pd.DataFrame(),dict(status='unavailable_original_units',draws=[])
    draws=[]
    if dataset=='rico':
        if 'phase' not in ctx:raise ValueError('RICO original phase identities required')
        groups=[p.index.to_numpy() for _,p in ctx.groupby('phase',sort=True)]
        if min(map(len,groups))<2:return pd.DataFrame(),dict(status='unavailable_singleton_phase',draws=[])
        draws=np.concatenate([g[rng.integers(len(g),size=(2000,len(g)))] for g in groups],axis=1)
    else:
        groups=[p.sort_values('context_start_row_id').index.to_numpy() for _,p in ctx.groupby(['outer_fold','segment_id'],sort=True)]
        # Sort using real chronological context onset, not opaque row hashes.
        groups=[ctx.loc[g].sort_values('onset').index.to_numpy() for g in groups]
        if sum(len(g)//7 for g in groups)<5 or any(len(g)<7 for g in groups):return pd.DataFrame(),dict(status='unavailable_complete_week_blocks',draws=[])
        parts=[]
        for g in groups:
            starts=rng.integers(len(g)-6,size=(2000,int(np.ceil(len(g)/7))))
            parts.append(g[(starts[:,:,None]+np.arange(7)).reshape(2000,-1)[:,:len(g)]])
        draws=np.concatenate(parts,axis=1)
    output=[]
    for key,part in pooled.groupby(['control_id','rule_id','channel']):
        a=np.full((n,21),np.nan);lookup={c:i for i,c in enumerate(ctx.context_id)}
        for r in part.itertuples():a[lookup[r.context_id],STRATA.index((r.family,r.severity))]=r.recall
        sampled=a[draws];counts=np.isfinite(sampled).sum(axis=1);sums=np.nansum(sampled,axis=1)
        means=np.divide(sums,counts,out=np.full_like(sums,np.nan),where=counts>0)
        vals=means.mean(axis=1);valid=vals[np.isfinite(vals)];good=len(valid)>=1900 and np.ptp(valid)>0
        output.append(dict(zip(['control_id','rule_id','channel'],key),status='supported' if good else 'unavailable_valid_draw_or_degenerate',valid_draws=len(valid),lower=float(np.quantile(valid,.025)) if good else np.nan,upper=float(np.quantile(valid,.975)) if good else np.nan))
    return pd.DataFrame(output),dict(status='draws_generated',seed=20240601,draws=draws.tolist(),draw_hash=signature(draws.tolist()),original_contexts=ctx.context_id.tolist())
