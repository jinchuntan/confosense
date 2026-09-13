"""One causal, method-owned amendment-004 interval and observation replay."""
from __future__ import annotations
from dataclasses import replace
import hashlib
import numpy as np
import pandas as pd
from . import features, conformal_cqr, conformal_quantile
from .interval_stream import IntervalEstimator
from .operational004_design import DESIGN, rank_support, segments
from .unit_checkpoint import signature


def score_quantiles(scores, level, method):
    scores = np.asarray(scores,float)
    scores = np.sort(scores[np.isfinite(scores)])
    rank = rank_support(len(scores),level,method)
    if not rank['supported']:
        return None
    if method == 'cqr':
        return (float(scores[rank['upper_rank']-1]),)*2
    return float(scores[rank['lower_rank']-1]),float(scores[rank['upper_rank']-1])


class OwnedInterval:
    """Actual interval-owned predictor; optional shared quantile fit for ablations."""
    def __init__(self, method, level, X_train, y_train, X_cal, y_cal, meta_cal, horizon,
                 seed=42, *, shared_quantile=None):
        if len(X_train)<400 or len(X_cal)<400:
            raise ValueError('below declared fitting/initial-calibration minimum')
        if not rank_support(len(X_cal),level,method)['supported']:
            raise ValueError('initial calibration rank unsupported')
        self.method,self.level,self.columns=method,float(level),list(X_train.columns)
        if list(X_cal.columns)!=self.columns:
            raise ValueError('calibration feature schema mismatch')
        self.fitted_models = 0
        y_train=np.asarray(y_train,float);y_cal=np.asarray(y_cal,float)
        if not np.isfinite(y_train).all() or not np.isfinite(y_cal).all():
            raise ValueError('fitting/calibration outcomes must be finite observed values')
        if method in ('cqr','quantile_uncalibrated'):
            self.m = shared_quantile
            if self.m is None:
                self.m=conformal_cqr.fit_cqr(X_train,pd.Series(y_train),X_cal,pd.Series(y_cal),level,seed=seed)
                self.fitted_models=1 # one CQR object, containing three fitted quantile estimators
            self.identity=dict(estimator_class='sklearn.ensemble.HistGradientBoostingRegressor',
                method=method,seed=seed,fallback=None,parameters=conformal_cqr._quantile_estimator(seed).get_params(),
                calibration_score='max(raw_lower-observed, observed-raw_upper)',sub_estimators=3)
        elif method=='recentred_enbpi':
            self.wrapper=IntervalEstimator('recentred_enbpi_static',level,X_train,y_train,X_cal,y_cal,meta_cal,horizon,seed)
            self.m=self.wrapper.m;self.fitted_models=1
            self.identity=dict(self.wrapper.identity,method=method,
                calibration_score='signed observed-minus-own-point for online policies',
                native_static_construction='original recentred MAPIE EnbPI bounds')
        elif method=='persistence_split':
            self.fitted_models=0
            self.identity=dict(estimator_class='persistence.target_lag_0',method=method,seed=seed,
                fallback=None,calibration_score='absolute observed-minus-persistence, fixed split conformal')
            self.radius=0.
        else:
            raise ValueError('unsupported operational interval owner')
        raw=self.raw(X_cal)
        score=(np.maximum(raw['raw_lower']-y_cal,y_cal-raw['raw_upper'])
               if method in ('cqr','quantile_uncalibrated') else y_cal-raw['point'])
        if method=='persistence_split':
            score=np.abs(score)
            self.radius=score_quantiles(score,level,'cqr')[0]
        self.calibration=meta_cal[['group_id','target_time']].reset_index(drop=True).copy()
        self.calibration['score']=score
        self.fit_identity=signature(dict(identity=self.identity,columns=self.columns,
            train_hash=hashlib.sha256(pd.util.hash_pandas_object(X_train,index=False).values.tobytes()+np.asarray(y_train).tobytes()).hexdigest(),
            calibration_hash=hashlib.sha256(pd.util.hash_pandas_object(self.calibration,index=False).values.tobytes()).hexdigest()))

    def raw(self,X):
        if list(X.columns)!=self.columns:
            raise ValueError('prediction feature schema mismatch')
        if self.method=='persistence_split':
            point=X.target_lag_0.to_numpy(float)
            return dict(point=point,raw_lower=point,raw_upper=point,
                        static_lower=point-self.radius,static_upper=point+self.radius)
        if self.method in ('cqr','quantile_uncalibrated'):
            estimators,_=conformal_quantile._sub_estimators(self.m)
            a=X.to_numpy()
            lo=np.asarray(estimators[0].predict(a));hi=np.asarray(estimators[1].predict(a))
            point=np.asarray(estimators[2].predict(a))
            # Protect the existing static API, including its crossing repair.
            static=conformal_cqr.cqr_interval(self.m,X)
            return dict(point=point,raw_lower=lo,raw_upper=hi,
                        static_lower=static['lower'],static_upper=static['upper'])
        from .conformal_enbpi import _recentered_intervals
        result=_recentered_intervals(self.m,X.to_numpy(),[self.level])[self.level]
        return dict(point=result['point'],raw_lower=result['lower'],raw_upper=result['upper'],
                    static_lower=result['lower'],static_upper=result['upper'])


def corrupted_features(segmented, meta, observed, available, horizon, fcfg, columns):
    """Vectorized causal lags are equivalent to origin-by-origin construction.

    Only the target sensor and its supplied missingness flag are corrupted.
    Forward fill is within an original continuous acquisition segment. No clean
    future target is used to fill a missing synthetic reading. The fixed common
    row mask is established before injection, never selected from model scores.
    """
    meta=meta.reset_index(drop=True)
    lookup={}
    for g,o,t,value,flag in zip(meta.group_id,meta.origin_time,meta.target_time,observed,available):
        lookup[(str(g),pd.Timestamp(t))]=(float(value),bool(flag))
    pieces=[]
    for series in segmented.series:
        frame=series.frame.copy()
        # Adapters encode this binary covariate as int, float or bool. Assigning
        # bool into BDG2's integer column coerces it to object in pandas, which
        # makes the otherwise numeric feature matrix fail np.isfinite. Preserve
        # its exact 0/1 meaning in an explicitly numeric column before injection.
        if 'target_was_missing' in frame:
            frame['target_was_missing']=frame['target_was_missing'].astype(float)
        for time in frame.index:
            item=lookup.get((str(series.group_id),pd.Timestamp(time)))
            if item is not None:
                value,flag=item;frame.loc[time,'target']=value if flag else np.nan
                if 'target_was_missing' in frame:
                    frame.loc[time,'target_was_missing']=float(not flag)
        frame['target']=frame.target.ffill()
        if series.season_steps is not None and series.season_steps < horizon:
            raise ValueError('seasonal feature would use a future reading')
        built=features.build_supervised(frame,horizon,series.freq,series.season_steps,fcfg)
        part=built['X'].copy();part['group_id']=str(series.group_id)
        part['origin_time']=part.index;pieces.append(part.reset_index(drop=True))
    whole=pd.concat(pieces,ignore_index=True)
    selected=meta[['group_id','origin_time']].merge(whole,on=['group_id','origin_time'],how='left',validate='one_to_one')
    X=selected[columns]
    if not np.isfinite(X.to_numpy()).all():
        raise ValueError('corrupted replay lost common eligible features')
    return X


def stream_hash(frame):
    fields=['row_id','group_id','origin_time','target_time','lower','upper','available']
    canonical=frame[fields].copy()
    for name in ['row_id','group_id']:canonical[name]=canonical[name].astype(str)
    for name in ['origin_time','target_time']:canonical[name]=pd.to_datetime(canonical[name])
    for name in ['lower','upper']:canonical[name]=canonical[name].astype(float)
    canonical['available']=canonical.available.astype(bool)
    return hashlib.sha256(pd.util.hash_pandas_object(canonical,index=False).values.tobytes()).hexdigest()


def replay(model, X, meta, observed, available, candidate, freq, *, raw_prediction=None):
    """Issue immutable bounds, compare matured readings, then release scores.

    Fixed predictors can batch the causal feature rows. All outcome-dependent
    interval updates still execute in chronological observation/origin order.
    """
    meta=meta.reset_index(drop=True);observed=np.asarray(observed,float);available=np.asarray(available,bool)
    if len(X)!=len(meta) or len(observed)!=len(meta) or len(available)!=len(meta):
        raise ValueError('misaligned replay inputs')
    if np.any(available & ~np.isfinite(observed)):
        raise ValueError('available reading is nonfinite')
    method,strategy=candidate['method'],candidate['strategy']
    if method != model.method or candidate['level'] != model.level:
        raise ValueError('candidate/estimator ownership mismatch')
    if method=='quantile_uncalibrated' and strategy!='static':
        raise ValueError('uncalibrated quantiles cannot receive an adaptive wrapper')
    if method=='persistence_split' and strategy!='static':
        raise ValueError('persistence reference is fixed split conformal only')
    if strategy=='native_updated' and (method!='recentred_enbpi' or candidate['every']!=1):
        raise ValueError('native update must be the canonical single policy')
    if strategy not in ('static','periodic','rolling','native_updated'):
        raise ValueError('unknown recalibration policy')
    if strategy!='static' and (candidate['every']<1 or candidate['min_samples']!=50):
        raise ValueError('undeclared update schedule/support minimum')
    feature_hash=hashlib.sha256(pd.util.hash_pandas_object(X,index=False).values.tobytes()).hexdigest()
    if raw_prediction is not None:
        if raw_prediction['feature_hash']!=feature_hash or raw_prediction['fit_identity']!=model.fit_identity:
            raise ValueError('raw prediction cache provenance mismatch')
        raw=raw_prediction['values']
    else:raw=model.raw(X)
    if any(len(raw[k])!=len(meta) or not np.isfinite(raw[k]).all()
           for k in ('point','raw_lower','raw_upper','static_lower','static_upper')):
        raise ValueError('nonfinite or misaligned method predictions')
    out=meta[['row_id','group_id','origin_time','target_time']].copy()
    out['observed']=observed;out['available']=available
    for k in ['point','raw_lower','raw_upper']:out[k]=raw[k]
    n=len(meta);lo=np.full(n,np.nan);hi=lo.copy();numerical=np.zeros(n,bool)
    released=np.zeros(n,int);latest=np.full(n,np.datetime64('NaT'),dtype='datetime64[ns]')
    pool_size=np.zeros(n,int);updated=np.zeros(n,bool);age=np.zeros(n,int)
    status=np.full(n,'static',dtype=object);updates=[];score_records=[]
    cal=model.calibration.copy();cal['target_time']=pd.to_datetime(cal.target_time)
    if len(cal)<400 or not np.isfinite(cal.score).all() or cal.target_time.max()>=pd.Timestamp(meta.origin_time.min()):
        raise ValueError('calibration minimum/boundary violated')
    global_scores=cal.score.to_numpy(float)
    base=score_quantiles(global_scores,model.level,'cqr' if method in ('quantile_uncalibrated','persistence_split') else method)
    if base is None:raise ValueError('initial calibration rank unsupported')
    targets=pd.DatetimeIndex(meta.target_time).asi8;origins=pd.DatetimeIndex(meta.origin_time).asi8
    if np.any(targets<=origins):raise ValueError('forecast target must follow origin')
    for group,sid,rows in segments(meta,freq):
        local=cal[cal.group_id.astype(str).eq(group)]
        if local.empty:local=cal
        local=local.sort_values('target_time',kind='stable')
        history=list(local.score[np.isfinite(local.score)].astype(float))
        history_times=list(pd.DatetimeIndex(local.target_time[np.isfinite(local.score)]).asi8)
        q=base;pointer=0;last_update=-1
        for ordinal,i in enumerate(rows):
            # Compare each matured reading with its previously issued interval
            # before making its score eligible for this origin's update.
            while pointer<ordinal and targets[rows[pointer]]<=origins[i]:
                old=int(rows[pointer]);pointer+=1
                numerical[old]=bool(available[old] and (observed[old]<lo[old] or observed[old]>hi[old]))
                if available[old]:
                    score=float(max(raw['raw_lower'][old]-observed[old],observed[old]-raw['raw_upper'][old])
                                if method in ('cqr','quantile_uncalibrated') else observed[old]-raw['point'][old])
                    if method=='persistence_split':score=abs(score)
                    kind={'cqr':'cqr_nonconformity','quantile_uncalibrated':'uncalibrated_quantile_score_unused',
                          'persistence_split':'absolute_persistence_score_unused'}.get(method,'signed_residual')
                    history.append(score);history_times.append(int(targets[old]))
                    score_records.append(dict(row_id=meta.iloc[old].row_id,group_id=group,segment_id=sid,
                        target_time=str(meta.iloc[old].target_time),released_at_origin=str(meta.iloc[i].origin_time),
                        score=score,kind=kind,
                        prior_interval_compared=True))
            pool_size[i]=len(history);released[i]=pointer
            if pointer:latest[i]=np.datetime64(int(targets[rows[pointer-1]]),'ns')
            if strategy!='static' and ordinal%candidate['every']==0:
                scores=history[-candidate['window']:] if strategy=='rolling' else history
                proposed=score_quantiles(scores,model.level,method) if len(scores)>=50 else None
                status[i]='updated' if proposed is not None else 'held_insufficient_score_or_rank_support'
                if proposed is not None:q=proposed;updated[i]=True;last_update=ordinal
                pool_size[i]=len(scores)
                updates.append(dict(group_id=group,segment_id=sid,origin_time=str(meta.iloc[i].origin_time),
                    pool_n=len(scores),latest_score_target=str(pd.Timestamp(max(history_times))) if history_times else '',
                    status=status[i],correction_lower=q[0],correction_upper=q[1]))
            elif strategy!='static':status[i]='held_between_updates'
            age[i]=ordinal-last_update if last_update>=0 else ordinal
            if method=='quantile_uncalibrated':
                lo[i],hi[i]=sorted((raw['raw_lower'][i],raw['raw_upper'][i]))
            elif strategy=='static':
                lo[i],hi[i]=raw['static_lower'][i],raw['static_upper'][i]
            elif method=='cqr':
                lo[i],hi[i]=sorted((raw['raw_lower'][i]-q[0],raw['raw_upper'][i]+q[1]))
            else:
                lo[i],hi[i]=raw['point'][i]+q[0],raw['point'][i]+q[1]
        for i in rows[pointer:]:
            numerical[i]=bool(available[i] and (observed[i]<lo[i] or observed[i]>hi[i]))
    if not np.isfinite(lo).all() or not np.isfinite(hi).all() or np.any(lo>hi):
        raise ValueError('invalid issued interval')
    out['lower']=lo;out['upper']=hi;out['numerical_violation']=numerical
    out['availability_violation']=~available;out['combined_violation']=numerical|~available
    out['released_rows']=released;out['latest_released_target']=latest
    out['update_pool_n']=pool_size;out['updated']=updated;out['correction_age_steps']=age;out['update_status']=status
    return dict(stream=out,emitted_hash=stream_hash(out),updates=pd.DataFrame(updates),
        released_scores=pd.DataFrame(score_records),identity=model.identity,
        fit_identity=model.fit_identity,causal_features_hash=feature_hash)
