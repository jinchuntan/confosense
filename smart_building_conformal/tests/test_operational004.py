"""Amendment 004 acceptance: real replay/selection/checkpoint interfaces."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src import corrected_study as old
from src.operational004_design import (DESIGN,FAMILIES,candidates,physical_rules,rank_support,
    make_outer_folds,nested_roles,build_windows)
from src.operational004_events import corruption,catalogue,bank_support
from src.operational004_stream import replay,corrupted_features,stream_hash
from src.operational004_metrics import alert_on_stream,group_recovery,resampling_draws
from src.operational004_engine import evaluate_unit,checkpointed_unit,validate_unit
from src.operational004_fixtures import fixture_data,DeterministicOwnedInterval,sufficient_bank
from src.operational004_verification import selection_probes,actual_cqr_probe,zero_probe
from src.operational004_inference import paired_contrasts,aggregate_seeds
from src.unit_checkpoint import UnitCheckpoint


@pytest.fixture(scope='module')
def data():
    p,s,w,c,fc=fixture_data()
    fold=make_outer_folds(w['meta'],'chronological',3,1,s.freq)[0]
    return p,s,w,c,fc,fold


@pytest.fixture(scope='module')
def unit(data):
    _,s,w,c,_,fold=data
    return evaluate_unit('synthetic004',0,42,s,w,c,fold,smoke=True,
        model_factory=DeterministicOwnedInterval,force_diagnostic=True,save_streams=True,evaluate_outer=True)


def test_actual_two_fold_matrix_and_owned_comparisons(unit):
    payload,frames=unit
    result=validate_unit(payload,frames,expected_scope='SMOKE ONLY')
    assert result['candidate_fold_cells']==12 and result['stream_hash_pairs']==60
    assert result['outer_stream_hash_pairs']==20 and result['persisted_streams_recomputed']==96
    assert payload['fits']==3 and payload['pipeline'] is None
    assert payload['independent_operating_points']['full']['pipeline'] is None
    for _,part in frames['hashes'].groupby(['role','catalogue_seed']):
        assert part.catalogue_hash.nunique()==1 and part.fit_identity.nunique()==1
    assert frames['outer_metrics'].query("method in ['cqr', 'quantile_uncalibrated']").fit_identity.nunique()==1
    assert payload['outer_comparisons'][-1]['name']=='persistence_split'
    assert not payload['outer_comparisons'][-1]['operational_feasible']
    assert set(frames['family_attribution'].channel)=={'availability_only','numerical_only','combined'}
    with pytest.raises(ValueError,match='full-study'):validate_unit(payload,frames,expected_scope='full_study')
    with pytest.raises(ValueError,match='real-data'):validate_unit(payload,frames,expected_scope='bounded_operational_pilot')


def test_final_calibration_and_test_sentinels_do_not_select(data,unit):
    _,s,w,c,_,fold=data
    roles=nested_roles(w['meta'],fold,'chronological');altered=deepcopy(w);ss=deepcopy(s)
    sentinel=np.concatenate([roles['final_calibration'],roles['outer_test']])
    altered['y'][sentinel]+=1e6
    cutoff=w['meta'].iloc[roles['final_calibration']].origin_time.min()
    altered['X'].loc[altered['meta'].origin_time>=cutoff,:]+=1e5
    for series in ss.series:series.frame.loc[series.frame.index>=cutoff,'target']+=1e6
    result,frames=evaluate_unit('synthetic004',0,42,ss,altered,c,fold,smoke=True,
        model_factory=DeterministicOwnedInterval,force_diagnostic=True)
    expected,old_frames=unit
    pd.testing.assert_frame_equal(frames['surface'],old_frames['surface'])
    assert result['pipeline']==expected['pipeline'] and result['fits']==2
    assert result['fit_records']==expected['fit_records'][:2]


def test_supported_bounds_ties_unequal_folds_and_abstention():
    result,_=selection_probes()
    assert result['feasible_selection']['candidate_id']=='fixture_a'


def test_actual_cqr_static_and_method_specific_causal_scores():
    result,_=actual_cqr_probe()
    assert result['actual_cqr_objects_fitted']==1


def test_zero_identity_all_families_and_five_catalogues(data):
    _,s,w,c,_,fold=data
    result=zero_probe(s,w,c,fold)
    assert len(result)==12


@pytest.mark.parametrize('family',FAMILIES)
def test_severity_semantics_and_null_realisation(family):
    source=np.arange(8.)+20
    outputs=[corruption(source,family,x,2.,1,np.random.default_rng(3),19.) for x in (.5,1.,2.)]
    if family=='block_missing':assert [int((~a).sum()) for _,a in outputs]==[2,4,8]
    elif family=='dropout':assert [int((x==0).sum()) for x,_ in outputs]==[2,4,8]
    elif family=='stuck':assert [int((x!=source).sum()) for x,_ in outputs]==[2,4,8]
    elif family in ('bias','level_shift','drift'):
        assert np.allclose(outputs[2][0]-source,4*(outputs[0][0]-source))
    elif family=='random_missing':
        assert all(np.isnan(x[~a]).all() for x,a in outputs)
    if family in ('bias','level_shift','drift'):
        curves=[corruption(source,f,1.,2.,1,np.random.default_rng(3),19.)[0] for f in ('bias','level_shift','drift')]
        assert len({x.tobytes() for x in curves})==3


def test_incidence_zero_unhostable_global_placement_and_nulls():
    times=pd.date_range('2020',periods=120,freq='min')
    meta=pd.DataFrame(dict(group_id='short',origin_time=times-pd.Timedelta('1min'),target_time=times))
    _,_,events,summary=catalogue(np.ones(120),meta,pd.Timedelta('1min'),{'__pooled__':1.},'rico','outer_test',0,42)
    assert summary['requested']==0 and events.empty
    # Many short disjoint assets have exposure, but cannot host even one event.
    fragmented=pd.concat([meta.assign(group_id=f'g{i}') for i in range(30)],ignore_index=True)
    fragmented['target_time']=pd.Timestamp('2020')+pd.to_timedelta(np.tile(np.arange(120)*2,30),unit='min')
    _,_,events,summary=catalogue(np.ones(len(fragmented)),fragmented,pd.Timedelta('1min'),{'__pooled__':1.},'rico','inner0_selection',0,42)
    assert summary['requested']==1 and summary['rejected']==1 and not events.placed.any()
    times=pd.date_range('2020',periods=15000,freq='10min')
    meta=pd.DataFrame(dict(group_id='constant',origin_time=times-pd.Timedelta('10min'),target_time=times))
    _,_,events,summary=catalogue(np.ones(len(meta)),meta,pd.Timedelta('10min'),{'__pooled__':1.},'pleia','inner0_selection',0,42)
    assert events.query("family=='stuck'").null.all()
    assert summary['requested']==52 and summary['effective']+summary['null']==summary['placed']
    assert events.groupby(['family','severity']).size().max()-events.groupby(['family','severity']).size().min()<=1


def test_physical_rules_ranks_and_no_double_adaptation(data):
    _,s,w,c,_,_=data
    assert sum(x['applicable'] for x in physical_rules(pd.Timedelta('1h')))==3
    assert not rank_support(50,.995,'cqr')['supported']
    assert not rank_support(200,.995,'recentred_enbpi')['supported']
    grid=candidates(c,s.freq)
    native=[x for x in grid if x['strategy']=='native_updated']
    assert native and all(x['every']==1 and x['method']=='recentred_enbpi' for x in native)
    assert len(native)==4*5
    assert not [x for x in grid if x['method']=='quantile_uncalibrated' and x['strategy']!='static']


def test_group_gap_reset_and_available_target_time(data):
    _,s,w,c,fc,_=data
    tr=np.arange(400);ca=np.arange(401,801)
    # Two separated segments in asset0 plus a second asset.
    ev=np.r_[np.arange(802,900),np.arange(950,1050),np.arange(4398,4498)]
    block=w['meta'].iloc[ev].reset_index(drop=True);X=w['X'].iloc[ev].reset_index(drop=True)
    model=DeterministicOwnedInterval('cqr',.95,w['X'].iloc[tr],w['y'][tr],w['X'].iloc[ca],w['y'][ca],w['meta'].iloc[ca],1)
    candidate=next(x for x in candidates(c,s.freq,smoke=True) if x['method']=='cqr' and x['strategy']=='rolling')
    obs=w['y'][ev].copy();flags=np.ones(len(ev),bool)
    clean=replay(model,X,block,obs,flags,candidate,s.freq)
    obs[:98]+=100
    corrupted=replay(model,X,block,obs,flags,candidate,s.freq)
    assert np.array_equal(clean['stream'].lower.iloc[98:],corrupted['stream'].lower.iloc[98:])
    assert list(corrupted['stream'].iloc[[0,98,198]].released_rows)==[0,0,0]
    altered=deepcopy(s);original=altered.series[0]
    altered.series[0]=replace(original,frame=original.frame.drop(original.frame.index[100:103]))
    _,gap,_=build_windows(altered,c,1)
    assert not gap['meta'].query("group_id=='asset0'").origin_time.isin(original.frame.index[100:106]).any()


def _alarm_frame():
    target=pd.to_datetime(['2020-01-01 00:10','2020-01-01 00:20','2020-01-01 00:40','2020-01-01 00:50'])
    return pd.DataFrame(dict(row_id=['a','b','c','d'],group_id='g',origin_time=target-pd.Timedelta('10min'),
        target_time=target,observed=[2.,2.,2.,2.],lower=0.,upper=1.,available=True))


def test_target_time_preexisting_episode_gap_and_censoring():
    frame=_alarm_frame();result=dict(stream=frame,emitted_hash=stream_hash(frame))
    rule=dict(applicable=True,k=2,m=3)
    out=alert_on_stream(result,rule,pd.DataFrame(),pd.Timedelta('10min'))
    assert out['episodes'].query("channel=='combined'").onset.tolist()==['2020-01-01 00:20:00','2020-01-01 00:50:00']
    rule=dict(applicable=True,k=1,m=1)
    events=pd.DataFrame([dict(event_id='fault',effective=True,group_id='g',segment_id='g:segment:0',
        onset='2020-01-01 00:20',end='2020-01-01 00:20',tolerance_end='2020-01-01 00:20')])
    scored=alert_on_stream(result,rule,events,pd.Timedelta('10min'))
    assert not scored['per_event'].detected.any() # Existing episode cannot get retrospective credit.
    events['tolerance_end']='2020-01-01 00:30'
    assert alert_on_stream(result,rule,events,pd.Timedelta('10min'))['per_event'].incomplete_followup.all()
    frame.loc[1,'available']=False
    with pytest.raises(ValueError,match='differ'):alert_on_stream(result,rule,events,pd.Timedelta('10min'))


def test_native_policy_single_update_and_signed_scores(data):
    _,s,w,c,_,_=data;tr=np.arange(400);ca=np.arange(401,801);ev=np.arange(802,902)
    model=DeterministicOwnedInterval('recentred_enbpi',.95,w['X'].iloc[tr],w['y'][tr],w['X'].iloc[ca],w['y'][ca],w['meta'].iloc[ca],1)
    candidate=next(x for x in candidates(c,s.freq) if x['strategy']=='native_updated' and x['level']==.95)
    out=replay(model,w['X'].iloc[ev],w['meta'].iloc[ev],w['y'][ev],np.ones(100,bool),candidate,s.freq)
    assert len(out['updates'])==100 and len(out['released_scores'])==99
    assert out['released_scores'].kind.eq('signed_residual').all()
    prior=out['stream'].set_index('row_id').loc[out['released_scores'].row_id]
    assert np.array_equal(out['released_scores'].score,prior.observed-prior.point)
    candidate=dict(candidate,every=2)
    with pytest.raises(ValueError,match='canonical'):replay(model,w['X'].iloc[ev],w['meta'].iloc[ev],w['y'][ev],np.ones(100,bool),candidate,s.freq)


def test_checkpoint_zero_refit_and_corruption_rejection(tmp_path,unit):
    payload,frames=unit;spec=dict(outer_fold=0,model_seed=42,scope='SMOKE ONLY',test='immutable')
    checkpointed_unit(tmp_path,spec,lambda:unit)
    def forbidden():raise AssertionError('completed resume must not fit')
    loaded,loaded_frames,status=checkpointed_unit(tmp_path,spec,forbidden,resume=True)
    assert status==dict(reused_units=1,new_fit_invocations=0)
    validate_unit(loaded,loaded_frames,expected_scope='SMOKE ONLY')
    file=tmp_path/'units/outer0_model42/streams.csv.gz'
    with file.open('ab') as out:out.write(b'corrupt')
    with pytest.raises(ValueError,match='corrupt checkpoint'):checkpointed_unit(tmp_path,spec,forbidden,resume=True)


def test_checkpoint_preserves_literal_none_asset_identifier(tmp_path):
    frame=_alarm_frame().assign(group_id='None')
    spec=dict(outer_fold=0,model_seed=42)
    checkpointed_unit(tmp_path,spec,lambda:(dict(fits=0),dict(stream=frame)))
    _,frames,status=checkpointed_unit(tmp_path,spec,lambda:pytest.fail('refit'),resume=True)
    assert frames['stream'].group_id.eq('None').all()
    assert stream_hash(frames['stream'])==stream_hash(frame)


def test_smoke_runner_persists_validation_and_resume(tmp_path,monkeypatch,unit):
    from src import operational004_smoke as smoke
    # The real CQR interface has its own test; reuse the completed two-fold
    # unit here to test the actual CLI runner's serialization and result schema.
    monkeypatch.setattr(smoke,'evaluate_unit',lambda *a,**kw:deepcopy(unit))
    monkeypatch.setattr(smoke,'actual_cqr_probe',lambda:(dict(test_stub=True),{}))
    configuration=Path(__file__).resolve().parents[1]/'configs/operational_amendment004.json'
    result=smoke.run(tmp_path,configuration)
    assert result['scope']=='SMOKE ONLY' and result['output_valid']
    assert (tmp_path/'output_validation.json').is_file()
    result=smoke.run(tmp_path,configuration,resume=True)
    assert result['reused_units']==1 and result['new_fit_invocations']==0
    assert (tmp_path/'resume_validation.json').is_file()


def test_unsupported_design_skips_fits(data):
    _,s,w,c,_,fold=data
    def forbidden(*args,**kwargs):pytest.fail('unsupported design must not trigger a learned fit')
    result,frames=evaluate_unit('synthetic004',0,43,s,w,c,fold,smoke=True,model_factory=forbidden)
    assert result['fits']==0 and result['pipeline'] is None
    assert frames['surface'].bound_status.eq('insufficient_design_support').all()
    assert sorted(frames['allocations'].catalogue_seed.unique())==DESIGN['catalogue_seeds']


def test_saved_output_validation_rejects_missing_cells_and_edited_bounds(unit):
    payload,frames=unit;changed=dict(frames)
    changed['surface']=frames['surface'].iloc[1:]
    with pytest.raises(ValueError,match='matrix'):validate_unit(payload,changed,expected_scope='SMOKE ONLY')
    changed=dict(frames);changed['streams']=frames['streams'].copy();changed['streams'].loc[0,'upper']+=1
    with pytest.raises(ValueError,match='persisted issued'):validate_unit(payload,changed,expected_scope='SMOKE ONLY')


def test_old_static_paths_keep_method_bounds(monkeypatch):
    from test_integration_repairs import fixture_data as old_data,install_estimators
    from src import split_integrity as SI
    install_estimators(monkeypatch)
    prepared,cfg,_,w=old_data(1600);m,X,y=w['meta'],w['X'],w['y']
    f=old.make_outer_folds(m,'chronological',3,5,prepared.freq)[0]
    trc=np.concatenate([f['train'],f['calibration']])
    inner=old.inner_split(m,trc,'chronological',5,prepared.freq)
    def forbidden(*a,**kw):raise AssertionError('static method bounds must bypass signed recalibration')
    monkeypatch.setattr(old,'_recalibrated_stream',forbidden)
    policy=dict(operating_levels=[.9],incidence=.5,min_recall=0.,workload_max=1e6,
        model_seeds=[7],event_seeds=[99],recalibration_strategies=['static'])
    selected=old.select_on_inner('fixture',5,7,0,m,X,y,inner,cfg,prepared.freq,SI.training_scale(y,m,inner['inner_train']),policy)
    pipe=selected['pipeline'];assert pipe.recalibration=='static'
    scales=SI.training_scale(y,m,inner['inner_train'])
    old.evaluate_outer(pipe,m,X,y,trc,f['test'],cfg,prepared.freq,scales,policy)
    old.evaluate_ablation(pipe,m,X,y,trc,f['test'],cfg,prepared.freq,scales,policy)


def test_paired_original_groups_not_seed_rows_and_censored_recovery():
    bank,meta,_=sufficient_bank(8);frames=[]
    for name in ('baseline','full'):
        for seed in DESIGN['model_seeds']:
            part=bank.copy();part['comparison']=name;part['outer_fold']=0;part['model_seed']=seed
            if name=='full':part.loc[part.group_id.eq('g00'),'clean_episodes']=0.
            frames.append(part)
    all_rows=pd.concat(frames,ignore_index=True)
    result,proof=paired_contrasts(all_rows,[('full','baseline')],pd.Timedelta('1h'),'bdg2')
    assert proof['original_units']==8 and result.original_units.eq(8).all()
    assert len(aggregate_seeds(all_rows))==2*len(bank)
    few=all_rows[all_rows.group_id.isin(['g00','g01','g02'])]
    out,_=paired_contrasts(few,[('full','baseline')],pd.Timedelta('1h'),'rico')
    assert out.status.eq('insufficient_original_units').all() and out.p_holm.isna().all()
    with pytest.raises(ValueError,match='missing model seed'):aggregate_seeds(all_rows[all_rows.model_seed.ne(46)])
    t=pd.date_range('2020',periods=30,freq='10min')
    stream=pd.DataFrame(dict(group_id=['a']*30,target_time=t,lower=-1.,upper=1.))
    truth=np.r_[np.zeros(10),np.full(20,10.)]
    faults=pd.DataFrame([dict(group_id='a',effective=True,onset=t[10],end=t[12])])
    rows,summary=group_recovery(stream,truth,faults,pd.Timedelta('10min'))
    assert rows.recovery_censored.all() and summary['median_recovery_minutes'] is None
    assert summary['restricted_mean_recovery_minutes']==summary['common_horizon_minutes']>0
