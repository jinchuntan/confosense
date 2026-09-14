"""Frozen native factories and shared checkpointed owners, with bounded inference."""
from __future__ import annotations
import copy
import inspect
import numpy as np
import pandas as pd
from mapie.regression import ConformalizedQuantileRegressor,TimeSeriesRegressor
from mapie.subsample import BlockBootstrap
from .conformal_cqr import _quantile_estimator
from .conformal_quantile import _sub_estimators
from .conformal_enbpi import _build_base,_recentered_intervals
from .intervals005_common import *


def method_spec(seed=42):
    base,name=_build_base(seed,{'base_n_estimators':60})
    if name!='XGBRegressor':raise RuntimeError('requested installed XGBoost unavailable; no silent fallback')
    return dict(version='matched_intervals005_native_and_causal_v1',seed=seed,
        cqr=dict(factory='src.conformal_cqr._quantile_estimator + MAPIE ConformalizedQuantileRegressor',estimator_parameters=_quantile_estimator(seed).get_params(),wrapper_parameters=dict(confidence_levels=LEVELS,prefit=False),objects_per_horizon=2,estimators_per_object=3,sharing='uncalibrated/CQR share exact raw lower/upper/median owner; levels have distinct objects',score='native static: separate raw_lower-y and y-raw_upper tail scores; method-preserving online replay: max(raw_lower-y,y-raw_upper)',native_quantile='asymmetric native tails: numpy.quantile(each tail score, (1-(1-level)/2)*(1+1/n), method=higher); MAPIE 1.4.1',native_predict_parameters=dict(symmetric_correction=False),crossing='retain raw pair; order only emitted pair'),
        enbpi=dict(factory='src.interval_stream.IntervalEstimator resolved MAPIE TimeSeriesRegressor',base_class=type(base).__module__+'.'+type(base).__name__,base_parameters=base.get_params(),bootstrap=dict(n_resamplings=5,length=24,overlapping=True,random_state=seed),wrapper=dict(method='enbpi',agg_function='mean',random_state=seed,n_jobs=1),sharing='static/updated and both nominal levels share exact final calibrated owner; updates never mutate it',operations='fit: full-data estimator plus five training bootstraps; explicit conformalize: five calibration bootstraps; verify synthetic actual ledger before real freeze',native_score='installed MAPIE conformity score with OOB predictions; retain nonfinite OOB score counts explicitly',native_interval='original _recentered_intervals; native offsets shifted from ensemble to full-fit point; no test-truth fitting',updated_policy=dict(version='amendment004_method_preserving_native_updated_v1',score='signed observed-minus-own-full-fit-point',every=1,window=None,min_samples=50,initialization='fixed pre-test same-group calibration history, otherwise fixed whole historical pool; global supported quantiles as initial hold',quantile='lower floor((n+1)*(1-level)/2+1e-12), upper ceil((n+1)*(1-(1-level)/2)-1e-12), one-indexed; no interpolation',group_policy='isolated original group and contiguous segment; reset to fixed historical calibration',legacy_difference='legacy updated EnbPI used interpolated numpy quantiles/min_samples1; this named adapter preserves amendment004 ranks/min_samples50; no bit-identity claim')),
        dscp=dict(factory='src.conformal_dscp.fit_dscp',max_clusters=6,ks_threshold=.05,neighbours=None,gamma=1.,seed=seed,silhouette_sample=2000,n_init=10,score='signed y-yhat',quantile='numpy.quantile default linear on fixed cluster/merged-step error pool',assignment='soft-DTW to all calibration predicted sequences; smallest-cluster-size neighbours; argpartition then majority/lowest-index tie',assignment_batch_size=64,minimum_calibration=400,owner='verified historical matched XGBoost direct horizon artifacts',labels=['direct_horizon_adaptation','from_paper_implementation'],test_truth_used_for_fit=False),
        replay=dict(calibration_minimum=400,update_minimum=50,release='compare matured observation to its immutable issued bounds before release; target_time <= current origin; available readings only',static='uncalibrated/CQR/static EnbPI/DSCP keep native static construction',availability='original target_was_missing and finite source observation; imputed does not imply observed'),
        alert=dict(rule='immediate_single_sample',k=1,m=1,sampling_frequency='1 hour for BDG2',events='empty; background workload only; no recall/F1/delay/primary feasibility'),
        references=dict(cqr='https://arxiv.org/abs/1905.03222',enbpi='https://proceedings.mlr.press/v139/xu21h.html',dscp='https://arxiv.org/abs/2503.21251',mapie='https://mapie.readthedocs.io/en/stable/'))


def new_cqr(level,seed,tiny=False):
    estimator=_quantile_estimator(seed)
    if tiny:estimator.set_params(max_iter=3,max_leaf_nodes=7,min_samples_leaf=10,early_stopping=False)
    return ConformalizedQuantileRegressor(estimator=estimator,confidence_level=level)


def new_enbpi(seed,tiny=False):
    base,name=_build_base(seed,{'base_n_estimators':3 if tiny else 60})
    if name!='XGBRegressor':raise RuntimeError('XGBoost unavailable; fallback requires explicit separate identity')
    return TimeSeriesRegressor(estimator=base,method='enbpi',cv=BlockBootstrap(n_resamplings=5,length=24,overlapping=True,random_state=seed),agg_function='mean',random_state=seed,n_jobs=1)


def quantile_raw(owner,X):
    estimators,levels=_sub_estimators(owner)
    values=[np.asarray(e.predict(np.asarray(X)),float) for e in estimators]
    return dict(point=values[2],raw_lower=values[0],raw_upper=values[1])


def raw_predictions(owner,kind,X,levels=LEVELS,batch=256):
    outputs={l:[] for l in levels}
    for start in range(0,len(X),batch):
        part=np.asarray(X[start:start+batch])
        if kind=='cqr':
            raw=quantile_raw(owner,part);point,interval=owner.predict_interval(part)
            arr=np.asarray(interval);a=arr[:,0,0];b=arr[:,1,0]
            out=dict(raw,static_raw_lower=a,static_raw_upper=b,static_lower=np.minimum(a,b),static_upper=np.maximum(a,b))
            outputs[levels[0]].append(pd.DataFrame(out))
        else:
            result=_recentered_intervals(owner,part,levels)
            for l,r in result.items():
                outputs[l].append(pd.DataFrame(dict(point=r['point'],raw_lower=r['lower'],raw_upper=r['upper'],static_raw_lower=r['lower'],static_raw_upper=r['upper'],static_lower=np.minimum(r['lower'],r['upper']),static_upper=np.maximum(r['lower'],r['upper']))))
    return {l:pd.concat(parts,ignore_index=True) for l,parts in outputs.items() if parts}


def fit_owner(stages,key,kind,level,seed,X,y,*,synthetic=False):
    def work(out):
        owner=new_cqr(level,seed,synthetic) if kind=='cqr' else new_enbpi(seed,synthetic)
        with Operations(stages.root/'operations.jsonl',stage=key,synthetic=synthetic) as ops:owner.fit(np.asarray(X),np.asarray(y))
        dump_owner(out/'owner.pkl',owner)
        atomic(out/'operation_counts.json',dict(counts={k:sum(r['kind']==k for r in ops.rows) for k in sorted(set(r['kind'] for r in ops.rows))},operations=ops.rows))
        return dict(kind=kind,level=level,seed=seed,n_fit=len(y),synthetic=synthetic,owner_class=type(owner).__module__+'.'+type(owner).__name__)
    return stages.run(key,work)


def conformalize_owner(stages,key,fit_path,X,y,*,synthetic=False):
    def work(out):
        owner=load_owner(fit_path/'owner.pkl')
        with Operations(stages.root/'operations.jsonl',stage=key,synthetic=synthetic) as ops:owner.conformalize(np.asarray(X),np.asarray(y))
        dump_owner(out/'owner.pkl',owner)
        scores=owner._mapie_quantile_regressor.conformity_scores_ if isinstance(owner,ConformalizedQuantileRegressor) else owner.conformity_scores_
        np.save(out/'native_conformity_scores.npy',scores)
        atomic(out/'operation_counts.json',dict(counts={k:sum(r['kind']==k for r in ops.rows) for k in sorted(set(r['kind'] for r in ops.rows))},operations=ops.rows))
        return dict(source_fitted_owner_sha256=digest(fit_path/'owner.pkl'),n_calibration=len(y),nonfinite_native_scores=int((~np.isfinite(scores)).sum()),score_symmetry=getattr(getattr(owner,'conformity_score_function_',None),'sym',None),synthetic=synthetic)
    return stages.run(key,work)
