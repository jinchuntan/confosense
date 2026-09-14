import copy,json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.context005_spec import controls,rules,identity_crosswalk,POLICIES,context_positions,VERSION
from src.context005_data import synthetic
from src.context005_features import bounded_frame,inject,causal_features,feature_hash
from src.context005_validate import scalar_inputs,scalar_observations,scalar_stream
from src.context005_owner import ContextOwner,prediction_cache
from src.context005_metrics import conditional_summary,inference
from src.operational004_stream import replay
from src.operational004_metrics import alert_on_stream
from src.intervals005_owners import new_cqr
from src.intervals005_common import Stages,atomic,Operations
from src.energy_sensitivity005 import parameters,stratify
from src.matched_intervals005 import scope_policy

@pytest.fixture(scope='module')
def fitted():
    d=synthetic('pleia_energy');r=d['roles'];o=new_cqr(.95,42,tiny=True)
    o.fit(d['X'].iloc[r['final_fit']].to_numpy(),d['y'][r['final_fit']]);o.conformalize(d['X'].iloc[r['final_calibration']].to_numpy(),d['y'][r['final_calibration']])
    models={method:ContextOwner(o,method,d['X'].iloc[r['final_calibration']],d['y'][r['final_calibration']],d['meta'].iloc[r['final_calibration']],dict(owner_sha256='synthetic',model_seed=42)) for method in ['cqr','quantile_uncalibrated','persistence_split']}
    return d,models

def case(d,event=None,context=0):
    meta=d['meta'].iloc[d['roles']['outer_test']].reset_index(drop=True);ctx=d['contexts'].iloc[context].to_dict();meta=meta.iloc[context_positions(meta,ctx)].reset_index(drop=True)
    frame,season=bounded_frame(d['series'],meta,d['fcfg'],d['horizon']);changed,truth,obs,available=inject(frame,meta,event)
    X=causal_features(changed,meta,d['horizon'],d['frequency'],season,d['fcfg'],d['X'].columns)
    return ctx,meta,frame,season,changed,truth,obs,available,X

@pytest.mark.parametrize('dataset',['pleia','pleia_energy','rico'])
def test_declared_controls_and_physical_rules(dataset):
    cs=controls(dataset);rs=rules(dataset)
    assert len(cs)==4 and len(rs)==5 and all(c['level']==.95 for c in cs)
    assert [(r['k'],r['m']) for r in rs]==([(1,1),(3,3),(4,6),(3,18),(4,36)] if dataset!='rico' else [(1,1),(2,5),(3,15),(3,30),(4,60)])
    assert cs[2]['every']==(15 if dataset=='rico' else 24) and cs[2]['window']==(200 if dataset=='rico' else 250)

@pytest.mark.parametrize('ds',['bdg2','pleia','pleia_energy','rico'])
@pytest.mark.parametrize('fold',[0,1,2])
def test_all_fold_support_from_published_roles(ds,fold):
    policy=scope_policy(ds,fold)
    assert min(policy['joint_support'].values())>=400
    if fold!=2:assert policy['joint_support']['fit']>scope_policy(ds,2)['joint_support']['fit']

def test_identity_crosswalk_cannot_merge_named_groups():
    assert identity_crosswalk('pleia',['None'],[''])['version']=='pleia_single_series_identity_v1'
    with pytest.raises(ValueError):identity_crosswalk('rico',['None','P1S1'],['','P1S1'])
    with pytest.raises(ValueError):identity_crosswalk('pleia',['None','other'],['','other'])

@pytest.mark.parametrize('dataset',['pleia_energy','rico'])
def test_independent_scalar_features_and_future_perturbation(dataset):
    d=synthetic(dataset);ctx,meta,base,season,frame,truth,obs,available,X=case(d)
    expected=scalar_inputs(base,meta,d['fcfg'],d['horizon'],d['frequency'],season,X.columns,obs,available)
    np.testing.assert_allclose(X,expected,atol=1e-12,rtol=1e-12)
    future=frame.copy();cut=pd.Timestamp(meta.origin_time.iloc[60]);future.loc[future.index>cut,'target']+=10000
    other=causal_features(future,meta,d['horizon'],d['frequency'],season,d['fcfg'],X.columns)
    np.testing.assert_array_equal(other.iloc[:61],X.iloc[:61])
    assert not np.array_equal(other.iloc[70:],X.iloc[70:])

@pytest.mark.parametrize('family',['random_missing','block_missing','stuck','dropout','bias','level_shift','drift'])
def test_independent_corruption_and_exact_envelope(family):
    d=synthetic('rico');event=d['schedules'][(d['schedules'].family==family)&(d['schedules'].severity==2)].iloc[0].to_dict()
    ctx,meta,base,season,frame,truth,obs,available,X=case(d,event)
    y,v,flags=scalar_observations(base,meta,event)
    np.testing.assert_allclose(obs,v,rtol=0,atol=1e-12,equal_nan=True);np.testing.assert_array_equal(available,flags)
    a=ctx['onset_offset'];b=a+ctx['duration'];np.testing.assert_array_equal(obs[:a],truth[:a]);np.testing.assert_array_equal(obs[b:],truth[b:])
    assert a>=60 and b+60<=len(obs)

def test_corruption_changes_actual_predictor_and_rejects_clean_cache(fitted):
    d,models=fitted;clean=case(d);event=d['schedules'][(d['schedules'].family=='level_shift')&(d['schedules'].severity==2)&(d['schedules'].sign==1)].iloc[0].to_dict();changed=case(d,event)
    model=models['cqr'];control=controls('pleia_energy')[2]
    clean_raw=model.raw(clean[-1]);changed_raw=model.raw(changed[-1]);onset=changed[0]['onset_offset']
    assert np.any(clean_raw['point'][onset+1:onset+6]!=changed_raw['point'][onset+1:onset+6])
    cache=prediction_cache(model,clean[-1],'clean')
    with pytest.raises(ValueError,match='provenance'):replay(model,changed[-1],changed[1],changed[6],changed[7],control,d['frequency'],raw_prediction=cache)

def test_missingness_no_score_method_static_bounds_and_held_state(fitted):
    d,models=fitted;event=d['schedules'][(d['schedules'].family=='block_missing')&(d['schedules'].severity==2)].iloc[0].to_dict();c=case(d,event)
    for control in controls('pleia_energy'):
        model=models[control['method']];r=replay(model,c[-1],c[1],c[6],c[7],control,d['frequency']);sc=scalar_stream(model,c[-1],c[1],c[6],c[7],control)
        np.testing.assert_allclose(r['stream'][['lower','upper']],np.column_stack([sc['lower'],sc['upper']]),rtol=0,atol=1e-12)
        assert not set(c[1].loc[~c[7],'row_id']) & set(r['released_scores'].row_id)
        assert r['stream'].availability_violation.sum()==6
    small=dict(controls('pleia_energy')[2],window=20)
    r=replay(models['cqr'],c[-1],c[1],c[6],c[7],small,d['frequency'])
    assert (r['updates'].status=='held_insufficient_score_or_rank_support').all()

def test_zero_control_and_independent_context_reset(fitted):
    d,models=fitted;c=case(d);event=d['schedules'].iloc[0].to_dict();event['severity']=0
    zero=case(d,event);np.testing.assert_array_equal(c[-1],zero[-1]);np.testing.assert_array_equal(c[6],zero[6])
    control=controls('pleia_energy')[2]
    a=replay(models['cqr'],c[-1],c[1],c[6],c[7],control,d['frequency']);b=replay(models['cqr'],zero[-1],zero[1],zero[6],zero[7],control,d['frequency'])
    for key in ['stream','updates','released_scores']:pd.testing.assert_frame_equal(a[key],b[key])
    assert a['updates'].iloc[0].pool_n==250
    other=case(d,context=2);r=replay(models['cqr'],other[-1],other[1],other[6],other[7],control,d['frequency'])
    assert r['updates'].iloc[0].pool_n==250 and r['stream'].released_rows.iloc[0]==0

def test_deterministic_alias_and_numeric_nulls():
    d=synthetic('pleia_energy');s=d['schedules'];sub=s[(s.context_id==d['contexts'].iloc[2].context_id)&(s.family=='dropout')]
    assert sub['null'].all() and not sub.effective.any()
    sub=s[(s.context_id==d['contexts'].iloc[0].context_id)&(s.family=='stuck')&(s.severity==1)]
    assert sub.observed_hash.nunique()==1 and sub.mask_hash.nunique()==1

def test_equal_context_not_effective_slot_weight_and_unavailable_full_macro():
    base=dict(control_id='x',rule_id='r',channel='combined',family='bias',severity=.5,alias=False,effective=True,eligible=True,null=False,restricted_delay_minutes=20,delay_minutes=20)
    rows=[dict(base,context_id='a',detected=True),dict(base,context_id='a',detected=True),dict(base,context_id='b',detected=False,delay_minutes=np.nan,restricted_delay_minutes=110)]
    s,m=conditional_summary(pd.DataFrame(rows),min_contexts=2);r=s[(s.family=='bias')&(s.severity==.5)].iloc[0]
    assert r.recall==.5 and r.restricted_mean_detection_minutes==65 and r.misses==1
    assert m.conditional_context_macro.isna().all() and m.supported_strata.iloc[0]==1

def test_pre_active_and_one_to_one_episode_matching():
    from src.operational004_stream import stream_hash
    times=pd.date_range('2024-01-01',periods=12,freq='10min')
    f=pd.DataFrame(dict(row_id=[str(i) for i in range(12)],group_id='g',origin_time=times-pd.Timedelta('10min'),target_time=times,observed=[2,2,2,0,2,2,0,0,0,0,0,0],available=True,lower=-1.,upper=1.))
    events=pd.DataFrame([dict(event_id=str(i),group_id='g',segment_id='g:segment:0',effective=True,onset=str(times[a]),tolerance_end=str(times[b])) for i,(a,b) in enumerate([(1,5),(4,5)])])
    result=alert_on_stream(dict(stream=f,emitted_hash=stream_hash(f)),dict(k=1,m=1,applicable=True),events,'10min')
    matched=result['per_event'].query('channel=="combined"');assert matched.detected.tolist()==[True,False]
    assert matched.delay_minutes.iloc[0]==30 # episode at t0 is pre-active and not credited

def test_checkpoints_reject_corruption_and_uncommitted_fit_repetition(tmp_path):
    s=Stages(tmp_path/'run',{'id':1});s.run('owner_fit_cqr',lambda p:atomic(p/'payload.json',{'ok':True}))
    with Operations(forbid=True):assert s.get('owner_fit_cqr') is not None
    atomic(tmp_path/'run/stages/owner_fit_cqr/payload.json',{'changed':True})
    with pytest.raises(ValueError,match='corrupt'):s.get('owner_fit_cqr')
    other=Stages(tmp_path/'other',{'id':1});(tmp_path/'other/.partial_owner_fit_cqr_interrupted').mkdir()
    with pytest.raises(ValueError,match='refit'):other.get('owner_fit_cqr')

def test_sensitivity_zero_is_not_fault_and_never_changes_primary():
    spec=parameters(np.arange(1,501.),[str(i) for i in range(500)]);t=pd.date_range('2024-01-01',periods=16,freq='10min')
    f=pd.DataFrame(dict(row_id=list(map(str,range(16))),group_id='g',target_time=t,observed=[0]*6+[600,2]+[0]*6+[3,2]));before=f.copy()
    mask,account=stratify(f,spec);pd.testing.assert_frame_equal(f,before)
    assert mask.sensitivity_mask.sum()==7 and mask.zero_candidate.sum()==12 and account['retained_n']==9
    assert mask.primary_keep.all() and account['primary_workload_denominator_unchanged']
    other=f.copy();other.loc[6:,'group_id']='new'
    result,_=stratify(other,spec);assert not result.sensitivity_mask.any()

def test_inference_never_bootstraps_single_seed_or_singleton_phase():
    f=pd.DataFrame([dict(context_id=str(i),control_id='a',rule_id='r',channel='combined',family='bias',severity=.5,model_seed=42,recall=i%2) for i in range(6)])
    ctx=pd.DataFrame(dict(context_id=list(map(str,range(6))),phase=[1,2,2,2,2,2]))
    _,r=inference(f,ctx,'rico');assert r['status']=='unavailable_incomplete_model_seeds'
    allseeds=pd.concat([f.assign(model_seed=s) for s in range(42,47)])
    from src.operational004_design import STRATA
    allseeds=pd.concat([allseeds.assign(family=fam,severity=sev) for fam,sev in STRATA])
    _,r=inference(allseeds,ctx,'rico');assert r['status']=='unavailable_singleton_phase'
