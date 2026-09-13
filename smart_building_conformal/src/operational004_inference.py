"""Paired outer contrasts: seeds stay within original time/building units.

Input is the catalogue-pooled contribution table from the operational engine,
with frozen comparison names attached using outer_comparisons. This interface
does not execute experiments or turn unsupported smoke into scientific evidence.
"""
import math
import numpy as np
import pandas as pd
from .operational004_design import DESIGN, segments, resampling_support
from .operational004_metrics import totals_metrics
from .unit_checkpoint import signature

METRICS=['exposure_days','clean_episodes','unmatched_episodes','corrupted_episodes','time_in_alert_days']+[
    f'{kind}{j}' for kind in ('n','tp') for j in range(21)]


def aggregate_seeds(frame,expected_seeds=(42,43,44,45,46)):
    keys=['comparison','outer_fold','row_id','group_id','origin_time','target_time']
    if frame.duplicated(keys+['model_seed']).any():raise ValueError('duplicate original row/model seed')
    sets=frame.groupby(keys,dropna=False).model_seed.agg(lambda x: tuple(sorted(x)))
    if not sets.map(lambda x:x==tuple(sorted(expected_seeds))).all():
        raise ValueError('missing model seed contributions; cannot pool incomplete crossings')
    # Catalogue pooling already averages clean exposure and workload. Model
    # seeds are now averaged within the identical original monitored row.
    return frame.groupby(keys,as_index=False,dropna=False)[METRICS].mean()


def paired_contrasts(frame,pairs,freq,dataset,*,expected_seeds=(42,43,44,45,46)):
    pooled=aggregate_seeds(frame,expected_seeds)
    keys=['outer_fold','row_id','group_id','origin_time','target_time']
    names=sorted(pooled.comparison.unique());arrays={};meta=None
    for name in names:
        part=pooled[pooled.comparison.eq(name)].sort_values(keys).reset_index(drop=True)
        if meta is None:meta=part[keys]
        else:pd.testing.assert_frame_equal(meta,part[keys])
        arrays[name]=part[METRICS].to_numpy(float)
    rng=np.random.default_rng(DESIGN['bootstrap_seed']);draws={};clustered={}
    if dataset in ('bdg2','rico'):
        groups=sorted(meta.group_id.astype(str).unique());units=len(groups)
        if units>=5:
            draws['groups']=groups;draws['indices']=rng.integers(units,size=(2000,units)).tolist()
            for name,a in arrays.items():
                by_group=np.stack([a[meta.group_id.astype(str).eq(g)].sum(axis=0) for g in groups])
                clustered[name]=by_group[np.array(draws['indices'])].sum(axis=1)
    else:
        units=0;fold_draws=[];okay=True
        for fold,part in meta.groupby('outer_fold',sort=True):
            # A block never crosses an outer-fold or actual acquisition boundary.
            local=part.reset_index(drop=True);support=resampling_support(local,freq,dataset)
            length=support['block_length_steps'];units+=support['original_resampling_units']
            segs=segments(local,freq)
            if any(len(rows)<length for _,_,rows in segs):okay=False;break
            order=np.concatenate([rows for _,_,rows in segs]);offset=0;starts=[]
            for _,_,rows in segs:starts.extend(range(offset,offset+len(rows)-length+1));offset+=len(rows)
            count=math.ceil(len(local)/length);sizes=np.full(count,length);sizes[-1]=len(local)-length*(count-1)
            idx=np.asarray(starts)[rng.integers(len(starts),size=(2000,count))]
            fold_draws.append(dict(fold=int(fold),indices=idx.tolist(),lengths=sizes.tolist(),original_positions=part.index[order].tolist()))
            for name,a in arrays.items():
                values=a[part.index[order]];cum=np.vstack([np.zeros(len(METRICS)),values.cumsum(axis=0)])
                totals=(cum[idx+sizes]-cum[idx]).sum(axis=1)
                clustered[name]=clustered.get(name,0)+totals
        draws['folds']=fold_draws
        if not okay:clustered={}
    rows=[]
    for left,right in pairs:
        if left not in arrays or right not in arrays:raise ValueError('missing frozen comparison')
        point={n:totals_metrics(dict(zip(METRICS,arrays[n].sum(axis=0)))) for n in (left,right)}
        for metric in ['macro_event_recall','background_episodes_per_asset_day']:
            row=dict(left=left,right=right,metric=metric,estimate=point[left][metric]-point[right][metric],
                original_units=units,status='insufficient_original_units',lower=np.nan,upper=np.nan,p_value=np.nan,valid_replicates=0)
            if units>=5 and clustered:
                def values(name):
                    a=clustered[name]
                    if metric=='background_episodes_per_asset_day':return a[:,1]/a[:,0]
                    return np.divide(a[:,26:47],a[:,5:26],out=np.full((len(a),21),np.nan),where=a[:,5:26]>0).mean(axis=1)
                diff=values(left)-values(right);valid=diff[np.isfinite(diff)]
                row['valid_replicates']=len(valid)
                row['status']='insufficient_bound_support'
                if len(valid)>=1900 and np.ptp(valid)>0:
                    row.update(status='supported',lower=float(np.quantile(valid,.025)),upper=float(np.quantile(valid,.975)),
                        p_value=float((1+np.sum(np.abs(valid-row['estimate'])>=abs(row['estimate'])))/(len(valid)+1)))
            rows.append(row)
    result=pd.DataFrame(rows);result['p_holm']=np.nan
    # One declared primary family per dataset; unavailable tests remain members
    # of its multiplicity count, not removed to make correction less stringent.
    order=result.index[result.p_value.notna()].tolist();order.sort(key=lambda i:result.loc[i,'p_value'])
    previous=0.
    for rank,i in enumerate(order):
        previous=max(previous,min(1.,(len(result)-rank)*result.loc[i,'p_value']))
        result.loc[i,'p_holm']=previous
    return result,dict(draws=draws,draws_hash=signature(draws),original_units=units,
        inference_unit='original groups/time; model/catalogue seeds averaged within units',
        multiplicity_family_size=len(result),claim='approximate paired percentile intervals; no equivalence claim')
