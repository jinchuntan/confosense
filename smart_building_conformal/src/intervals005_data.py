"""Read-only historical owners and exact native/joint matched support."""
from __future__ import annotations
import gc
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from .intervals005_common import *
from . import matched_forecasting005 as forecasting
from .matched_data005 import forecast_roles
from .matched_models005 import restore
from .model_comparison_pilot import prepare
from .pilot_data import build_support
from .pilot_forecasters import predict

LEDGER=ROOT/'outputs/matched_forecasting005/fold2_multiseed_batch_v1/analysis_v1/evidence_reuse_ledger.csv'
JOINT=ROOT/'outputs/amendment005/support_final_checks_v1/dscp_joint_origin_membership.csv.gz'
JOINT_SUPPORT=JOINT.with_name('dscp_joint_origin_support.csv')
MATRIX=ROOT/'outputs/amendment005/study_plan_v1/interval_method_matrix.csv'


def historical_references(dataset,fold,seed,horizons):
    ledger=frame(LEDGER)
    chosen=ledger[(ledger.dataset==dataset)&(ledger.outer_fold==fold)&(ledger.model_seed==seed)]
    protocols={digest(p):p for p in (ROOT/'protocols/matched_forecasting005').glob('*/frozen_protocol.json')}
    result={}
    for h in horizons:
        rows=chosen[chosen.horizon==h]
        if len(rows)!=1:raise ValueError('historical owner reference missing/ambiguous')
        r=rows.iloc[0];run=REPO/r.run_path;files=tree(run)
        actual=hashlib.sha256('\n'.join(f'{p}:{v}' for p,v in files.items()).encode()).hexdigest()
        if actual!=r.run_file_tree_hash or r.source_hash!=OLD_SOURCE:raise ValueError('historical run source/byte identity mismatch')
        protocol=protocols[r.protocol_hash]
        directory=run/'units'/f'{dataset}_h{h}_f{fold}_s{seed}_xgboost'
        record=read(directory/'COMPLETE.json')
        for name,value in record['hashes'].items():
            if digest(directory/name)!=value:raise ValueError('corrupt historical owner')
        result[str(h)]=dict(protocol=str(protocol.relative_to(REPO)),protocol_hash=digest(protocol),run=str(run.relative_to(REPO)),run_file_tree_hash=actual,source_hash=r.source_hash,owner_directory=str(directory.relative_to(REPO)),owner_hashes={p.name:digest(p) for p in directory.iterdir() if p.is_file()},evaluated_commit=r.evaluated_commit)
    return result


def check_historical(reference):
    protocol=REPO/reference['protocol'];directory=REPO/reference['owner_directory']
    if digest(protocol)!=reference['protocol_hash']:raise ValueError('historical protocol changed')
    for name,d in reference['owner_hashes'].items():
        if digest(directory/name)!=d:raise ValueError('historical owner/stream changed')
    old=read(protocol)
    if old['source_hash']!=reference['source_hash']:raise ValueError('historical source mismatch')
    for name,d in old['input_hashes'].items():
        if digest(ROOT/name)!=d:raise ValueError('historical input/config changed: '+name)
    return old


def _prepared_identity(cfg,c):
    """Identity carried with the in-memory preparation cache.

    A prepared object contains the target series.  Reusing it for a different
    target, dataset, outer membership, or sampling grid would silently cross
    the frozen owner boundary, so cache reuse is deliberately narrower than
    the caller's convenience API.
    """
    return signature(dict(dataset=c['dataset'],outer_fold=c['outer_fold'],
        target=cfg.get('target'),adapter=cfg.get('adapter'),
        resample=cfg.get('resample'),missing=cfg.get('missing')))


def load_data(reference,prepared=None):
    old=check_historical(reference);cfg=old['resolved_dataset_config'];c=old['config']
    identity=_prepared_identity(cfg,c)
    if prepared is None:
        prepared=(prepare(cfg),identity)
    if not isinstance(prepared,tuple) or len(prepared)!=2 or prepared[1]!=identity:
        raise ValueError('prepared cache dataset/target/membership identity mismatch')
    prepared_object=prepared[0]
    data=build_support(prepared_object,cfg,c['horizon'],c['sequence_length'])
    roles=forecast_roles(data['meta'],c['horizon'],prepared_object.freq,c['outer_fold'],c['dataset']=='rico')
    forecasting.verify_data(data,roles,old)
    meta=data['meta'];available=np.zeros(len(meta),bool);seasonal=np.full(len(meta),np.nan)
    from .baselines import seasonal_naive_prediction
    for series in prepared_object.series:
        idx=np.flatnonzero(meta.group_id.astype(str).eq(str(series.group_id)))
        times=pd.DatetimeIndex(meta.iloc[idx].target_time)
        source=series.frame.reindex(times)
        values=source.target.to_numpy(float)
        flags=np.isfinite(values)
        if 'target_was_missing' in source:flags &= ~source.target_was_missing.fillna(True).astype(bool).to_numpy()
        available[idx]=flags
        if series.season_steps is not None:
            if series.season_steps<c['horizon']:raise ValueError('seasonal prediction would use future reading')
            seasonal[idx]=seasonal_naive_prediction(series.frame.target,times,series.season_steps,series.freq)
    data['available']=available;data['seasonal']=seasonal;data['freq']=pd.Timedelta(prepared_object.freq)
    data['old_protocol']=old
    return data,roles,prepared


def role_frame(data,rows):
    out=data['meta'].iloc[rows][['row_id','group_id','origin_time','target_time']].reset_index(drop=True).copy()
    out.group_id=out.group_id.astype(str)
    out['y_true']=data['y'][rows];out['available']=data['available'][rows]
    return out


def historical_predictions(reference,data,roles):
    directory=REPO/reference['owner_directory'];model=restore('xgboost',directory,data);records={};checks=[]
    for role in ('fit','calibration','test'):
        rows=roles[role];out=role_frame(data,rows)
        out['point']=predict(model,'xgboost',data,rows,256)
        if role!='fit':
            saved=frame(directory/('calibration.csv.gz' if role=='calibration' else 'predictions.csv.gz'))
            if 'nominal_level' in saved:saved=saved[saved.nominal_level==.9].copy()
            if list(saved.row_id)!=list(out.row_id):raise ValueError('historical prediction row mismatch')
            np.testing.assert_allclose(saved.y_true,out.y_true,rtol=0,atol=1e-12)
            difference=float(np.max(np.abs(saved.point-out.point)))
            np.testing.assert_allclose(saved.point,out.point,rtol=1e-7,atol=1e-7)
            checks.append(dict(role=role,n=len(out),maximum_prediction_difference=difference,owner_sha256=reference['owner_hashes']['model.ubj']))
        records[role]=out
    return records,checks


def joint_join(frames,horizons,*,expected=None,frequency=None):
    if list(frames)!=list(horizons) or horizons!=sorted(set(horizons)):raise ValueError('joint horizons must have exact increasing order')
    if frequency is None:raise ValueError('joint frequency must be explicit')
    frequency=pd.Timedelta(frequency)
    if frequency <= pd.Timedelta(0):raise ValueError('joint frequency must be positive')
    sets=[]
    for h,f in frames.items():
        if f.row_id.duplicated().any() or f[['group_id','origin_time']].duplicated().any():raise ValueError('duplicate horizon row/origin')
        o=pd.to_datetime(f.origin_time);t=pd.to_datetime(f.target_time)
        if not ((t-o)==h*frequency).all():raise ValueError('joint horizon target mismatch')
        sets.append(set(zip(f.group_id.astype(str),o.astype(str))))
    common=set.intersection(*sets)
    if expected is not None:
        e=set(zip(expected.group_id.astype(str),pd.to_datetime(expected.origin_time).astype(str)))
        if e!=common or len(e)!=len(expected):raise ValueError('missing/unexpected joint origin versus frozen membership')
    order=sorted(common)
    if not order:raise ValueError('empty joint origin support')
    parts={}
    for h,f in frames.items():
        temp=f.copy();temp.group_id=temp.group_id.astype(str);temp.origin_time=pd.to_datetime(temp.origin_time).astype(str)
        parts[h]=temp.set_index(['group_id','origin_time']).loc[order].reset_index()
    return parts


def expected_joint(dataset,fold,role):
    f=frame(JOINT);return f[(f.dataset==dataset)&(f.outer_fold==fold)&(f.role==role)].copy()
