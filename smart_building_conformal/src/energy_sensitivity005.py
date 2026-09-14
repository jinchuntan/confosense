"""Proposed retrospective evaluation stratification; never alters sensor input.

Version is a proposal, not a historical preregistration. The authoritative
record defines no numerical stalled/catch-up rules. Training parameters are
required explicitly and carry provenance; the primary keep analysis is intact.
"""
import numpy as np
import pandas as pd
from .unit_checkpoint import signature

PROPOSAL=dict(version='energy_sensitivity005_proposed_v1',status='scientific_choice_unapproved',
    frequency='10min',kind='retrospective_evaluation_only',minimum_zero_run_steps=6,
    training_positive_quantile=.99,catchup_lookahead_steps=1,
    zero_alone_means_fault=False,mask_policy='zero_run_and_immediate_large_successor',
    primary_values='untouched',online_treatment=False,retraining=False)

def parameters(train,train_ids):
    y=np.asarray(train,float);positive=y[np.isfinite(y)&(y>0)]
    if len(positive)<400:raise ValueError('insufficient positive training support for proposed sensitivity threshold')
    return dict(PROPOSAL,threshold=float(np.quantile(positive,.99,method='higher')),
        threshold_source='permitted fitting outcomes only',training_ids_hash=signature(list(train_ids)),
        training_values_hash=signature(y.tolist()),positive_training_rows=len(positive))

def stratify(frame,spec):
    if spec.get('version')!=PROPOSAL['version'] or spec.get('online_treatment') or spec.get('retraining'):
        raise ValueError('not the proposed retrospective interface')
    f=frame.copy().reset_index(drop=True);out=f[['row_id','group_id','target_time']].copy()
    out['primary_keep']=True;out['zero_candidate']=False;out['catchup_candidate']=False;out['sensitivity_mask']=False;out['reason']='kept'
    for _,group in f.groupby('group_id',sort=False):
        ix=group.index.to_numpy();t=pd.to_datetime(group.target_time).astype('int64').to_numpy()
        cuts=np.r_[0,np.flatnonzero(np.diff(t)!=pd.Timedelta(spec['frequency']).value)+1,len(ix)]
        for a,b in zip(cuts,cuts[1:]):
            rows=ix[a:b];y=f.loc[rows,'observed'].to_numpy(float);i=0
            while i<len(rows):
                if y[i]!=0:i+=1;continue
                j=i+1
                while j<len(rows) and y[j]==0:j+=1
                if j-i>=spec['minimum_zero_run_steps']:
                    out.loc[rows[i:j],'zero_candidate']=True
                    out.loc[rows[i:j],'reason']='zero_run_only_kept_not_adjudicated_fault'
                    if j<len(rows) and np.isfinite(y[j]) and y[j]>spec['threshold']:
                        out.loc[rows[i:j+1],'sensitivity_mask']=True
                        out.loc[rows[i:j+1],'reason']='proposed_zero_run_plus_large_immediate_successor'
                        out.loc[rows[j],'catchup_candidate']=True
                i=j
    out['spec_hash']=signature(spec)
    accounting=dict(primary_n=len(out),masked_n=int(out.sensitivity_mask.sum()),retained_n=int((~out.sensitivity_mask).sum()),
        original_asset_days=len(out)*pd.Timedelta(spec['frequency'])/pd.Timedelta('1D'),
        sensitivity_asset_days=int((~out.sensitivity_mask).sum())*pd.Timedelta(spec['frequency'])/pd.Timedelta('1D'),
        primary_workload_denominator_unchanged=True,status='proposed_no_real_mask_applied')
    return out,accounting
