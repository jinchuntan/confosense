"""Bounded observation-time injection and causal features, without outcome filtering."""
import hashlib
import numpy as np
import pandas as pd
from .operational004_events import corruption
from .unit_checkpoint import signature

def feature_hash(X):
    return hashlib.sha256(pd.util.hash_pandas_object(X,index=False).values.tobytes()).hexdigest()

def history_length(cfg,season_steps,horizon):
    lags=list(cfg['target_lags'])+[max(cfg['rolling_windows'])-1]
    if season_steps is not None:
        if season_steps<horizon:raise ValueError('future seasonal feature')
        lags += [season_steps-horizon]
        if cfg.get('include_weekly'):lags += [7*season_steps-horizon]
    return max(lags)

def bounded_frame(series,meta,cfg,horizon):
    """Locate exactly one original segment and retain sufficient preceding history."""
    group=str(meta.group_id.iloc[0]);start=pd.Timestamp(meta.origin_time.min());end=pd.Timestamp(meta.target_time.max())
    candidates=[s for s in series if str(s.group_id)==group and s.frame.index.min()<=start and s.frame.index.max()>=end]
    if len(candidates)!=1:raise ValueError('context not contained in one original source segment')
    s=candidates[0];at=s.frame.index.get_indexer([start])[0]
    if at<0:raise ValueError('origin absent from source')
    before=max(0,at-history_length(cfg,s.season_steps,horizon))
    frame=s.frame.iloc[before:s.frame.index.get_indexer([end])[0]+1].copy()
    if not frame.index.to_series().diff().dropna().eq(s.freq).all():raise ValueError('causal history crosses acquisition gap')
    return frame,s.season_steps

def inject(frame,meta,event=None):
    frame=frame.copy();times=pd.DatetimeIndex(meta.target_time)
    truth=frame.loc[times,'target'].to_numpy(float)
    available=np.isfinite(truth)
    if 'target_was_missing' in frame:available &= ~frame.loc[times,'target_was_missing'].to_numpy(bool)
    observed=truth.copy()
    if event is not None:
        ids=list(meta.row_id);a=ids.index(event['onset_row_id']);b=ids.index(event['end_row_id'])+1
        prior=frame.loc[frame.index<times[a],'target'].dropna()
        if not len(prior):raise ValueError('fault lacks observable predecessor')
        values,flags=corruption(truth[a:b],event['family'],float(event['severity']),float(event['sigma']),
            int(event['sign']),np.random.default_rng(int(event['mask_seed'])),float(prior.iloc[-1]))
        if not available[a:b].all():raise ValueError('published event overlaps unavailable original readings')
        observed[a:b]=values;available[a:b]=flags
        if float(event['severity'])>0:
            effective=bool((~flags).any() or np.any(values[flags]!=truth[a:b][flags]))
            if effective!=bool(event['effective']):raise ValueError('published effective/null realization changed')
            if signature(flags.tolist())!=event['mask_hash'] or signature(np.nan_to_num(values,nan=-1.23456789e307).tolist())!=event['observed_hash']:
                raise ValueError('published RNG mask/observations changed')
    frame.loc[times,'target']=np.where(available,observed,np.nan)
    if 'target_was_missing' in frame:
        frame['target_was_missing']=frame.target_was_missing.astype(float)
        frame.loc[times,'target_was_missing']=(~available).astype(float)
    return frame,truth,observed,available

def causal_features(frame,meta,horizon,freq,season_steps,cfg,columns):
    """Features depend on readings through origin only; original mask is retained."""
    target=frame.target.astype(float).ffill();values={}
    for k in cfg['target_lags']:values[f'target_lag_{k}']=target.shift(k)
    if season_steps is not None:
        if season_steps<horizon:raise ValueError('future seasonal feature')
        values['target_daily_lag']=target.shift(season_steps-horizon)
        if cfg.get('include_weekly'):values['target_weekly_lag']=target.shift(7*season_steps-horizon)
    for w in cfg['rolling_windows']:
        r=target.rolling(w,min_periods=max(2,w//2));values[f'target_rollmean_{w}']=r.mean()
        # Evaluate each finite window directly. Incremental variance drift in
        # pandas was measurable (~1.24e-12) when a bounded history was rebuilt.
        # This keeps the same sample-standard-deviation definition and removes
        # accumulated cancellation; the independent scalar check stays strict.
        values[f'target_rollstd_{w}']=r.apply(lambda v:np.std(v,ddof=1),raw=True)
    t=frame.index+horizon*pd.Timedelta(freq)
    for label,v,period in [('hour',t.hour+t.minute/60,24),('dow',t.dayofweek,7)]:
        values[label+'_sin']=np.sin(2*np.pi*np.asarray(v)/period);values[label+'_cos']=np.cos(2*np.pi*np.asarray(v)/period)
    for name in cfg.get('covariates',[]):
        if name in frame:values[name]=frame[name]
    for name in frame:
        if name.endswith('_was_missing'):values[name]=frame[name]
    X=pd.DataFrame(values,index=frame.index).loc[pd.DatetimeIndex(meta.origin_time),columns].reset_index(drop=True)
    if not np.isfinite(X.to_numpy(float)).all():raise ValueError('unforecastable input; original common eligibility cannot be silently reduced')
    return X
