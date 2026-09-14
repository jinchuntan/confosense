"""Bounded two-group/two-horizon actual-owner integration; synthetic fits only."""
import os
from pathlib import Path
import copy
import hashlib
import numpy as np
import pandas as pd
import pytest
from src.intervals005_common import *
from src.intervals005_owners import fit_owner,conformalize_owner,raw_predictions
from src.intervals005_data import joint_join
from src.intervals005_stream import emit,consume,save_stream
from src.intervals005_validate import scalar_replay,independent_alert,independent_metrics,quantile_pair
from src.operational004_fixtures import fixture_data
from src.operational004_design import segments
from src.operational004_stream import corrupted_features,stream_hash
from src.conformal_dscp import fit_dscp,soft_dtw,soft_dtw_to_bank


@pytest.fixture(scope='module')
def integration(tmp_path_factory):
    out=Path(os.environ.get('INTERVALS005_SYNTHETIC_OUT',str(tmp_path_factory.mktemp('synthetic005'))))
    out.mkdir(parents=True,exist_ok=True)
    stages=Stages(out/'run',dict(synthetic=True,source_hash=source_digest(),horizons=[1,3],tiny_max_iter=3))
    all_data={};results={};owners={}
    for h in (1,3):
        prepared,s,w,cfg,fc=fixture_data(n=1100,groups=2,horizon=h)
        per=[np.flatnonzero(w['meta'].group_id.eq(g)) for g in ('asset0','asset1')]
        tr=np.concatenate([r[:350] for r in per]);ca=np.concatenate([r[356:606] for r in per]);te=np.concatenate([np.r_[r[612:672],r[710:770]] for r in per])
        def metadata(rows):
            f=w['meta'].iloc[rows][['row_id','group_id','origin_time','target_time']].reset_index(drop=True).copy();f['y_true']=w['y'][rows];f['available']=True;return f
        cal=metadata(ca);test=metadata(te);test.loc[[4,17,81],'available']=False
        X=w['X'].iloc[te].reset_index(drop=True)
        all_data[h]=dict(prepared=prepared,segmented=s,w=w,cfg=cfg,fc=fc,tr=tr,ca=ca,te=te,cal=cal,test=test,X=X)
        for kind,levels in [('cqr',LEVELS),('enbpi',[None])]:
            for level in levels:
                suffix=f'h{h}_{kind}'+(f'_l{int(level*100)}' if level else '')
                fitted=fit_owner(stages,'owner_fit_'+suffix,kind,level,42,w['X'].iloc[tr],w['y'][tr],synthetic=True)
                calibrated=conformalize_owner(stages,'owner_cal_'+suffix,fitted,w['X'].iloc[ca],w['y'][ca],synthetic=True)
                model=load_owner(calibrated/'owner.pkl');levels_actual=[level] if level else LEVELS
                raw=raw_predictions(model,kind,X.to_numpy(),levels_actual);rawcal=raw_predictions(model,kind,w['X'].iloc[ca].to_numpy(),levels_actual)
                owners[h,kind,level]=(model,calibrated,raw,rawcal)
                for l in levels_actual:
                    methods=['quantile_uncalibrated','cqr'] if kind=='cqr' else ['recentred_enbpi_static','recentred_enbpi_updated']
                    for method in methods:
                        result=emit(method,l,digest(calibrated/'owner.pkl'),X,test,raw[l],cal,rawcal[l],s.freq)
                        path=stages.run(f'stream_h{h}_l{int(l*100)}_{method}',lambda dest,result=result,h=h,l=l,method=method:save_stream(dest,result,s.freq,dict(horizon=h,level=l,method=method)))
                        results[h,l,method]=(result,path)
    # Joint calibration/test prediction sequences from separately trained owners.
    cf={};tf={}
    for h in (1,3):
        model,_,raw,rawcal=owners[h,'enbpi',None]
        cf[h]=all_data[h]['cal'].assign(point=rawcal[.9].point.to_numpy())
        tf[h]=all_data[h]['test'].assign(point=raw[.9].point.to_numpy())
    jc=joint_join(cf,[1,3],frequency=pd.Timedelta(minutes=10));jt=joint_join(tf,[1,3],frequency=pd.Timedelta(minutes=10))
    P=np.column_stack([jc[h].point for h in (1,3)]);Y=np.column_stack([jc[h].y_true for h in (1,3)]);T=np.column_stack([jt[h].point for h in (1,3)])
    with Operations(stages.root/'operations.jsonl',stage='synthetic_dscp',synthetic=True):multi=fit_dscp(P,Y,[1,3],max_clusters=2,seed=42)
    with Operations(stages.root/'operations.jsonl',stage='synthetic_dscp_one_cluster',synthetic=True):one=fit_dscp(np.ones_like(P),Y,[1,3],max_clusters=1,seed=42)
    assert multi.n_clusters==2 and one.n_clusters==1
    dscp_path=stages.run('dscp_fit',lambda dest:(dump_owner(dest/'calibrator.pkl',multi) or dict(n=len(P),synthetic=True)))
    assigned=multi.assign(T)
    for l in LEVELS:
        b=multi.predict_interval(T,l,assignments=assigned)
        for j,h in enumerate((1,3)):
            raw=pd.DataFrame(dict(point=T[:,j],raw_lower=b['lower'][:,j],raw_upper=b['upper'][:,j],static_raw_lower=b['lower'][:,j],static_raw_upper=b['upper'][:,j],static_lower=b['lower'][:,j],static_upper=b['upper'][:,j]));calraw=pd.DataFrame(dict(point=P[:,j]))
            result=emit('dscp',l,digest(dscp_path/'calibrator.pkl'),pd.DataFrame(T),jt[h],raw,jc[h],calraw,pd.Timedelta(minutes=10))
            result['stream']['dscp_cluster']=assigned
            path=stages.run(f'stream_h{h}_l{int(l*100)}_dscp',lambda dest,result=result,h=h,l=l:save_stream(dest,result,pd.Timedelta(minutes=10),dict(horizon=h,level=l,method='dscp')))
            results[h,l,'dscp']=(result,path)
    ledger=[json.loads(s) for s in (stages.root/'operations.jsonl').read_text().splitlines()]
    counts={k:sum(r.get('kind')==k and r['event']=='returned' for r in ledger) for k in set(r.get('kind') for r in ledger) if k}
    atomic(out/'actual_synthetic_fit_counts.json',dict(counts=counts,learned_estimator_fits=counts.get('quantile_estimator_fit',0)+counts.get('xgboost_estimator_fit',0),dscp_calibrator_fits=counts.get('dscp_calibrator_fit',0),enbpi_base_fits_per_owner=counts.get('xgboost_estimator_fit',0)//2,method_stream_cells=len(results),source_hash=source_digest()))
    return dict(out=out,stages=stages,data=all_data,results=results,owners=owners,multi=multi,one=one,P=P,Y=Y,T=T,assigned=assigned,calframes=cf,testframes=tf,counts=counts)


def test_actual_shared_owner_counts(integration):
    c=integration['counts'];assert c['cqr_wrapper_fit']==4 and c['quantile_estimator_fit']==12
    assert c['enbpi_wrapper_fit']==2 and c['xgboost_estimator_fit']==22
    for h in (1,3):
        for l in LEVELS:
            a=integration['results'][h,l,'cqr'][0];b=integration['results'][h,l,'quantile_uncalibrated'][0]
            assert a['fit_identity']==b['fit_identity']
            np.testing.assert_array_equal(a['stream'].point,b['stream'].point)
        ids=[integration['results'][h,l,m][0]['fit_identity'] for l in LEVELS for m in ('recentred_enbpi_static','recentred_enbpi_updated')]
        assert len(set(ids))==1


@pytest.mark.parametrize('h',[1,3])
@pytest.mark.parametrize('l',LEVELS)
def test_scalar_matches_batch_all_methods(integration,h,l):
    d=integration['data'][h]
    for method in METHODS[:-1]:
        kind='cqr' if method in ('cqr','quantile_uncalibrated') else 'enbpi'
        _,_,raw,rawcal=integration['owners'][h,kind,l if kind=='cqr' else None]
        expected=scalar_replay(d['test'],raw[l],d['cal'],rawcal[l],l,method if kind=='cqr' else 'recentred_enbpi',strategy='native_updated' if method.endswith('_updated') else 'static',freq=d['segmented'].freq)
        actual=integration['results'][h,l,method][0]['stream']
        np.testing.assert_array_equal(actual.lower,expected['lower']);np.testing.assert_array_equal(actual.upper,expected['upper']);np.testing.assert_array_equal(actual.numerical_violation,expected['numerical'])


def test_serialized_owner_predictions_and_forbidden_completed_stage_resume(integration):
    s=integration['stages'];before=tree(s.root)
    with Operations(forbid=True):
        resumed=Stages(s.root,dict(synthetic=True,source_hash=source_digest(),horizons=[1,3],tiny_max_iter=3),resume=True)
        for key in sorted(p.name for p in (s.root/'stages').iterdir()):resumed.run(key,lambda _:pytest.fail('completed stage invoked work'),forbid=True)
        for (h,kind,l),(original,path,raw,_) in integration['owners'].items():
            restored=load_owner(path/'owner.pkl');pred=raw_predictions(restored,kind,integration['data'][h]['X'].to_numpy(),[l] if l else LEVELS)
            for level,f in pred.items():pd.testing.assert_frame_equal(f,raw[level],check_exact=True)
        restored=load_owner(s.get('dscp_fit')/'calibrator.pkl');np.testing.assert_array_equal(restored.assign(integration['T']),integration['assigned'])
    assert tree(s.root)==before


def test_fit_and_calibrator_routes_forbidden(integration):
    from src.intervals005_owners import new_cqr
    with pytest.raises(AssertionError,match='forbidden'),Operations(forbid=True):new_cqr(.9,42,True).fit(np.ones((500,2)),np.arange(500.))
    with pytest.raises(AssertionError,match='forbidden'),Operations(forbid=True):fit_dscp(integration['P'],integration['Y'],[1,3])
    owner=copy.deepcopy(integration['owners'][1,'enbpi',None][0])
    with pytest.raises(AssertionError,match='forbidden'),Operations(forbid=True):owner.conformalize(np.ones((500,2)),np.arange(500.))


def test_joint_rejects_permutation_duplicate_missing_and_wrong_target(integration):
    frames=integration['calframes'];expected=joint_join(frames,[1,3],frequency=pd.Timedelta(minutes=10))[1][['group_id','origin_time']]
    with pytest.raises(ValueError,match='order'):joint_join({3:frames[3],1:frames[1]},[1,3])
    for defect in ('duplicate','missing','target'):
        bad={h:f.copy() for h,f in frames.items()}
        if defect=='duplicate':bad[1]=pd.concat([bad[1],bad[1].iloc[:1]])
        if defect=='missing':bad[1]=bad[1].iloc[1:]
        if defect=='target':bad[1].loc[0,'target_time']=pd.Timestamp('2100')
        with pytest.raises(ValueError):joint_join(bad,[1,3],expected=expected,frequency=pd.Timedelta(minutes=10))


def test_dscp_assignments_truth_independent_shared_levels_and_scalar_dtw(integration):
    m=integration['multi'];before=signature(m.metadata);a=m.assign(integration['T'])
    changed=integration['Y']+1e6 # deliberately never supplied to frozen calibrator
    assert changed.shape==integration['Y'].shape
    for l in LEVELS:np.testing.assert_array_equal(m.predict_interval(integration['T'],l,assignments=a)['cluster'],a)
    np.testing.assert_array_equal(m.assign(integration['T']),a);assert signature(m.metadata)==before
    np.testing.assert_array_equal(integration['one'].assign(integration['T']),np.zeros(len(a),int))
    bank=integration['P'][:15];query=integration['T'][0]
    np.testing.assert_allclose(soft_dtw_to_bank(query,bank),[soft_dtw(query,row) for row in bank],atol=1e-12)


def test_inclusive_maturity_missingness_and_group_segment_isolation(integration):
    d=integration['data'][3];_,path,raw,rawcal=integration['owners'][3,'enbpi',None]
    clean=integration['results'][3,.95,'recentred_enbpi_updated'][0]
    records=clean['released_scores'];lookup=d['test'].set_index('row_id')
    assert (pd.to_datetime(records.released_at_origin)>=pd.to_datetime(lookup.loc[records.row_id].target_time).to_numpy()).all()
    assert (pd.to_datetime(records.released_at_origin)==pd.to_datetime(lookup.loc[records.row_id].target_time).to_numpy()).any()
    assert not set(d['test'].loc[~d['test'].available,'row_id'])&set(records.row_id)
    changed=d['test'].copy();changed.loc[:59,'y_true']+=1000
    other=emit('recentred_enbpi_updated',.95,digest(path/'owner.pkl'),d['X'],changed,raw[.95],d['cal'],rawcal[.95],d['segmented'].freq)
    np.testing.assert_array_equal(clean['stream'].lower.iloc[60:],other['stream'].lower.iloc[60:])
    at=d['test'].iloc[20].target_time
    altered=d['test'].copy();altered.loc[20:,'y_true']+=1e4
    future=emit('recentred_enbpi_updated',.95,digest(path/'owner.pkl'),d['X'],altered,raw[.95],d['cal'],rawcal[.95],d['segmented'].freq)
    prior=d['test'].origin_time<at;np.testing.assert_array_equal(clean['stream'].lower[prior],future['stream'].lower[prior])


def test_cqr_scores_static_crossing_and_insufficient_rank_hold(integration):
    d=integration['data'][3];_,path,raw,rawcal=integration['owners'][3,'cqr',.95]
    crossed=raw[.95].copy();crossed.loc[0,['raw_lower','raw_upper']]=[30.,20.]
    result=emit('cqr',.95,digest(path/'owner.pkl'),d['X'],d['test'],crossed,d['cal'],rawcal[.95],d['segmented'].freq,strategy='rolling',window=20)
    assert result['stream'].raw_crossed.iloc[0]
    assert result['stream'].update_status.eq('held_insufficient_score_or_rank_support').all()
    scalar=scalar_replay(d['test'],crossed,d['cal'],rawcal[.95],.95,'cqr','rolling',window=20,freq=d['segmented'].freq)
    np.testing.assert_array_equal(result['stream'].lower,scalar['lower'])
    prior=result['stream'].set_index('row_id').loc[result['released_scores'].row_id]
    np.testing.assert_array_equal(result['released_scores'].score,np.maximum(prior.raw_lower-prior.observed,prior.observed-prior.raw_upper))
    assert quantile_pair(list(range(50)),.995,'recentred_enbpi') is None
    static=integration['results'][3,.95,'cqr'][0]['stream'];np.testing.assert_array_equal(static.lower,raw[.95].static_lower)


@pytest.mark.parametrize('k,m',[(1,1),(2,3)])
def test_emitted_consumed_identity_and_independent_episodes(integration,k,m):
    for result,_ in integration['results'].values():
        consumed,_=consume(result,pd.Timedelta(minutes=10),k=k,m=m)
        expected,episodes=independent_alert(result['stream'],pd.Timedelta(minutes=10),k,m)
        for channel,values in expected.items():np.testing.assert_array_equal(consumed['stream']['alert_'+channel],values)
        assert len(episodes)==len(consumed['episodes'])
        assert consumed['consumed_hash']==result['emitted_hash']
    altered=copy.deepcopy(result);altered['stream'].loc[0,'upper']+=1
    with pytest.raises(ValueError,match='differ'):consume(altered,pd.Timedelta(minutes=10))


def test_corrupted_features_zero_control_scalar_replay_and_future_inputs(integration):
    d=integration['data'][3];w=d['w'];meta=d['test'];s=d['segmented'];columns=list(w['X'])
    clean=corrupted_features(s,meta,meta.y_true,np.ones(len(meta),bool),3,d['fc'],columns)
    np.testing.assert_array_equal(clean,d['X'])
    obs=meta.y_true.to_numpy().copy();flags=np.ones(len(meta),bool);obs[20:25]+=5;flags[30]=False;obs[30]=np.nan
    altered=corrupted_features(s,meta,obs,flags,3,d['fc'],columns)
    before=meta.origin_time<meta.target_time.iloc[20];np.testing.assert_array_equal(clean[before],altered[before])
    owner,path,_,rawcal=integration['owners'][3,'cqr',.95]
    raw=raw_predictions(owner,'cqr',altered.to_numpy(),[.95])[.95]
    modified=meta.copy();modified['y_true']=np.where(flags,obs,meta.y_true);modified['available']=flags
    result=emit('cqr',.95,digest(path/'owner.pkl'),altered,modified,raw,d['cal'],rawcal[.95],s.freq,strategy='periodic')
    scalar=scalar_replay(modified,raw,d['cal'],rawcal[.95],.95,'cqr','periodic',freq=s.freq)
    np.testing.assert_array_equal(result['stream'].lower,scalar['lower'])
    # Build the feature at each selected origin using a source truncated at that
    # origin: a separate scalar causality check of batch corrupted features.
    from dataclasses import replace
    from src import features
    for i in (19,23,32,90,150):
        group=meta.group_id.iloc[i];origin=meta.origin_time.iloc[i];series=next(z for z in s.series if z.group_id==group);source=series.frame.loc[:origin].copy()
        for j in range(len(meta)):
            t=meta.target_time.iloc[j]
            if meta.group_id.iloc[j]==group and t in source.index:source.loc[t,'target']=obs[j] if flags[j] else np.nan
        source.target=source.target.ffill()
        # Extend only the row index for deterministic target-calendar features;
        # feature extraction uses no later target values.
        extended=source.reindex(source.index.append(pd.date_range(origin+s.freq,periods=3,freq=s.freq)))
        # build_supervised filters rows with a missing target label. These
        # arbitrary future labels retain the queried feature row only; no label
        # enters its lags/rolling statistics and no fitting uses this frame.
        extended.loc[extended.index>origin,'target']=-1e9
        built=features.build_supervised(extended,3,s.freq,None,d['fc'])['X']
        np.testing.assert_allclose(built.loc[origin,columns],altered.iloc[i],atol=1e-12)


def test_corrupt_checkpoint_and_ready_partial_recovery(tmp_path):
    s=Stages(tmp_path/'store',dict(test=True))
    p=s.run('owner_fit_demo',lambda dest:(atomic(dest/'owner.json',dict(value=1)) or {}))
    partial=s.root/'.partial_owner_fit_demo_interrupted';p.rename(partial)
    recovered=Stages(s.root,dict(test=True),resume=True).run('owner_fit_demo',lambda _:pytest.fail('refit after ready checkpoint'))
    assert recovered.exists() and not partial.exists()
    (recovered/'owner.json').write_text('corrupt')
    with pytest.raises(ValueError,match='corrupt'):s.get('owner_fit_demo')
    with pytest.raises(ValueError,match='identity'):Stages(s.root,dict(test=False),resume=True)


def test_incomplete_fit_not_automatically_repeated(tmp_path):
    s=Stages(tmp_path/'store',dict(test=True));(s.root/'.partial_owner_fit_broken_123').mkdir()
    with pytest.raises(ValueError,match='refit'):s.run('owner_fit_broken',lambda _:pytest.fail('unsafe refit'))


def test_metric_reconstruction_and_native_common_subset_history(integration):
    from src.intervals005_stream import interval_metrics
    for result,_ in integration['results'].values():
        f=result['stream'];a=interval_metrics(f,float(f.level.iloc[0]));b=independent_metrics(f,float(f.level.iloc[0]))
        for k,v in b.items():np.testing.assert_allclose(a[k],v,atol=1e-10)
        subset=f.iloc[::3];same=independent_metrics(subset,float(f.level.iloc[0]));assert same['n']==len(subset)
        # Subsetting consumes already-issued bounds and does not restart replay.
        np.testing.assert_array_equal(subset.lower,f.lower.iloc[::3])
