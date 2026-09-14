"""Method-preserving causal replay, immutable issued streams and alert evidence."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import numpy as np
import pandas as pd
from .intervals005_common import signature,csv,atomic
from .operational004_design import segments
from .operational004_stream import replay,stream_hash
from .operational004_metrics import alert_on_stream


@dataclass
class FrozenStreamOwner:
    method: str
    level: float
    calibration: pd.DataFrame
    values: dict
    fit_identity: str
    identity: dict

    def raw(self,X):return self.values


def emit(method,level,owner_hash,X,meta,raw,calibration,calibration_raw,freq,*,strategy=None,window=None,every=1):
    """Use amendment004 replay unchanged; new names identify the actual policy."""
    alias='recentred_enbpi' if method.startswith('recentred_enbpi') else method
    strategy=strategy or ('native_updated' if method=='recentred_enbpi_updated' else 'static')
    observed=meta.y_true.to_numpy(float);available=meta.available.to_numpy(bool)
    ycal=calibration.y_true.to_numpy(float)
    scores=np.maximum(calibration_raw.raw_lower.to_numpy()-ycal,ycal-calibration_raw.raw_upper.to_numpy()) if alias in ('cqr','quantile_uncalibrated') else ycal-calibration_raw.point.to_numpy()
    cal=calibration[['group_id','target_time']].copy();cal['score']=scores
    values={k:raw[k].to_numpy(float) for k in ('point','raw_lower','raw_upper','static_lower','static_upper')}
    state_id=signature(dict(owner=owner_hash,method=method,level=level,calibration_hash=hashlib.sha256(pd.util.hash_pandas_object(cal,index=False).values.tobytes()).hexdigest(),strategy=strategy,window=window,every=every))
    identity=dict(owner_sha256=owner_hash,method=method,level=level,mutable_state_identity=state_id,score='CQR max(raw_lower-y,y-raw_upper)' if alias=='cqr' else 'signed y-own-point; unused by static methods')
    owner=FrozenStreamOwner(alias,level,cal,values,owner_hash,identity)
    candidate=dict(method=alias,level=level,strategy=strategy,every=every if strategy!='static' else 0,window=window,min_samples=50)
    result=replay(owner,X,meta,observed,available,candidate,freq)
    out=result['stream'];out['method']=method;out['level']=level;out['owner_id']=owner_hash
    out['calibration_state_id']=state_id;out['segment_id']=''
    for _,sid,rows in segments(out,freq):out.loc[rows,'segment_id']=sid
    out['raw_crossed']=out.raw_lower>out.raw_upper
    out['static_raw_crossed']=raw.static_raw_lower.to_numpy()>raw.static_raw_upper.to_numpy()
    out['static_lower']=raw.static_lower.to_numpy();out['static_upper']=raw.static_upper.to_numpy()
    out['observation_available_at']=out.target_time
    out.rename(columns={'released_rows':'matured_rows','latest_released_target':'latest_matured_target'},inplace=True)
    released=result['released_scores'];out['score_released_at_origin']=pd.NaT;out['released_score']=np.nan
    if len(released):
        releases=released.set_index('row_id');out['score_released_at_origin']=pd.to_datetime(out.row_id.map(releases.released_at_origin))
        out['released_score']=out.row_id.map(releases.score)
    out['issued_state_id']=state_id
    if len(result['updates']):
        updates=result['updates'].copy()
        updates['issued_state_id']=[signature(dict(calibration_state_id=state_id,**r)) for r in updates.to_dict('records')]
        ids={(str(r.group_id),str(pd.Timestamp(r.origin_time))):r.issued_state_id for r in updates.itertuples()}
        for _,sid,rows in segments(out,freq):
            current=state_id
            for i in rows:
                current=ids.get((str(out.at[i,'group_id']),str(pd.Timestamp(out.at[i,'origin_time']))),current)
                out.at[i,'issued_state_id']=current
        result['updates']=updates
    result['candidate']=candidate;result['emitted_hash']=stream_hash(out)
    return result


def consume(result,freq,*,k=1,m=1):
    rule=dict(applicable=True,k=k,m=m,rule='immediate_single_sample' if m==1 else 'synthetic_temporal')
    consumed=alert_on_stream(result,rule,pd.DataFrame(),freq)
    f=consumed['stream'];episodes=consumed['episodes'];exposure=len(f)*float(pd.Timedelta(freq)/pd.Timedelta(days=1))
    available=int(f.available.sum())
    rows=[]
    for group,part in [('__pooled__',f),*list(f.groupby('group_id',sort=True))]:
        e=episodes if group=='__pooled__' else episodes[episodes.group_id.astype(str)==str(group)]
        days=len(part)*float(pd.Timedelta(freq)/pd.Timedelta(days=1))
        for channel in ('numerical_only','availability_only','combined'):
            rows.append(dict(group_id=str(group),channel=channel,n_rows=len(part),n_available=int(part.available.sum()),n_unavailable=int((~part.available).sum()),exposure_asset_days=days,observed_asset_days=int(part.available.sum())*float(pd.Timedelta(freq)/pd.Timedelta(days=1)),episodes=int((e.channel==channel).sum()),background_episodes_per_asset_day=float((e.channel==channel).sum()/days) if days else np.nan,time_in_alert_fraction=float(part['alert_'+channel].mean()),event_count=0,event_recall_status='not_estimable_empty_event_catalogue',interpretation='background episodes, not confirmed false alarms; no primary selection'))
    return consumed,pd.DataFrame(rows)


def save_stream(out,result,freq,tag):
    consumed,workload=consume(result,freq)
    csv(out/'issued.csv.gz',result['stream']);csv(out/'updates.csv.gz',result['updates']);csv(out/'released_scores.csv.gz',result['released_scores'])
    csv(out/'consumed.csv.gz',consumed['stream']);csv(out/'episodes.csv.gz',consumed['episodes'])
    for k,v in tag.items():workload[k]=v
    csv(out/'background_workload.csv',workload)
    atomic(out/'stream_identity.json',dict(emitted_hash=result['emitted_hash'],consumed_hash=consumed['consumed_hash'],identity=result['identity'],candidate=result['candidate'],alert_rule=dict(k=1,m=1,frequency=str(freq)),event_count=0,**tag))
    return dict(n=len(result['stream']),emitted_hash=result['emitted_hash'],consumed_hash=consumed['consumed_hash'],updated_rows=int(result['stream'].updated.sum()),raw_crossed=int(result['stream'].raw_crossed.sum()),held_insufficient=int(result['stream'].update_status.eq('held_insufficient_score_or_rank_support').sum()),**tag)


def interval_metrics(f,level):
    y=f.observed.to_numpy(float);lo=f.lower.to_numpy(float);hi=f.upper.to_numpy(float)
    valid=np.isfinite(y)&np.isfinite(lo)&np.isfinite(hi)
    if not valid.all() or np.any(lo>hi):raise ValueError('unsupported/nonfinite rows must be explicit, not dropped')
    width=hi-lo;coverage=float(((y>=lo)&(y<=hi)).mean());alpha=1-level
    score=width+2/alpha*np.maximum(lo-y,0)+2/alpha*np.maximum(y-hi,0)
    error=f.point.to_numpy(float)-y
    return dict(n=len(f),coverage=coverage,signed_coverage_deviation=coverage-level,absolute_coverage_deviation=abs(coverage-level),mpiw=float(width.mean()),winkler=float(score.mean()),mae=float(np.abs(error).mean()),rmse=float(np.sqrt(np.mean(error**2))),sum_absolute_error=float(np.abs(error).sum()),sum_squared_error=float(np.sum(error**2)),sum_width=float(width.sum()),sum_winkler=float(score.sum()),covered_count=int(((y>=lo)&(y<=hi)).sum()),available_count=int(f.available.sum()),unavailable_count=int((~f.available).sum()),raw_crossed=int(f.raw_crossed.sum()),status='complete')
