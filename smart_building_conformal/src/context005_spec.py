"""Amendment-005 C controls and immutable published inputs; no A selection."""
from pathlib import Path
import numpy as np
import pandas as pd
from .intervals005_common import ROOT,REPO,read,digest,signature
from .operational004_design import physical_rules

VERSION='conditional_context005_v1'
BASE=ROOT/'outputs/amendment005/support_design_v1'
FINAL=ROOT/'outputs/amendment005/support_final_checks_v1'
PLAN=ROOT/'outputs/amendment005/study_plan_v1'
CACHE=Path('C:/Users/nigel/ConfoSenseBackups/amendment004_20260913/preflight_v1')
POLICIES={
    'pleia':dict(frequency='10min',horizon=1,every=24,window=250,warmup=36,duration=6,followup=6,tolerance=6),
    'pleia_energy':dict(frequency='10min',horizon=1,every=24,window=250,warmup=36,duration=6,followup=6,tolerance=6),
    'rico':dict(frequency='1min',horizon=5,every=15,window=200,warmup=60,duration=60,followup=60,tolerance=10)}

def table(path):
    return pd.read_csv(path,keep_default_na=False,float_precision='round_trip',dtype={'row_id':str,'group_id':str,'mask_seed':str})

def controls(dataset):
    p=POLICIES[dataset]
    return [dict(control_id=name,method=method,level=.95,strategy=strategy,
                 every=p['every'] if strategy=='rolling' else 0,
                 window=p['window'] if strategy=='rolling' else None,min_samples=50)
            for name,method,strategy in [('quantile_static','quantile_uncalibrated','static'),
                ('cqr_static','cqr','static'),('cqr_rolling','cqr','rolling'),
                ('persistence_static','persistence_split','static')]]

def rules(dataset):
    return [r for r in physical_rules(POLICIES[dataset]['frequency'])
            if r['applicable'] and (dataset!='rico' or r['window_minutes']<=60)]

def source_inputs(dataset):
    paths=[BASE/n for n in ('proposal_spec.json','proposal_roles.csv','challenge_contexts.csv',
        'challenge_schedules.csv.gz','challenge_rule_applicability.csv','original_groups.csv',
        dataset+'_operational_membership_observations.csv.gz','validation.json')]
    paths += [FINAL/'challenge_zero_controls.csv',FINAL/'challenge_inference_support.csv',PLAN/'challenge_aliases.csv']
    return {p.relative_to(REPO).as_posix():digest(p) for p in paths}

def role_rows(membership,fold,role):
    return np.flatnonzero(membership[f'fold{fold}_roles'].map(lambda s: role in s.split('|')))

def identity_crosswalk(dataset,source_groups,matched_groups):
    """One explicit representation map for the verified single-series adapter.

    Never globally rewrite a real named group called 'None', 'nan', or ''.
    """
    a=set(map(str,source_groups));b=set(map(str,matched_groups))
    if dataset in ('pleia','pleia_energy') and a=={'None'} and b=={''}:
        return dict(version='pleia_single_series_identity_v1',dataset=dataset,
            source_group='None',matched_group='',preserve_source_ids=True)
    if a==b:return dict(version='literal_identity_v1',dataset=dataset,preserve_source_ids=True)
    raise ValueError('unverified group identity crosswalk')

def context_positions(meta,context):
    ids=list(meta.row_id);a=ids.index(context['context_start_row_id']);b=ids.index(context['context_end_row_id'])+1
    part=meta.iloc[a:b]
    if len(part)!=int(context['context_rows']) or signature(part.row_id.tolist())!=context['context_row_hash']:
        raise ValueError('published context row identity mismatch')
    if set(part.group_id.astype(str))!={str(context['group_id'])}:raise ValueError('context crosses original group')
    return np.arange(a,b)
