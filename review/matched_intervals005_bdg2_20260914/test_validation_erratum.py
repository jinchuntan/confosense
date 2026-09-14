"""No-fit regression for native CQR and exact, read-only historical compatibility."""
from common import *
import copy
import numpy as np
import pytest
from src.intervals005_common import Operations,Stages,load_owner
from src.matched_intervals005 import check_protocol,execute
from src.operational004_fixtures import fixture_data


AUDIT=REVIEW/('VALIDATION_ERRATUM_V3.json' if (REVIEW/'VALIDATION_ERRATUM_V3.json').exists() else 'VALIDATION_ERRATUM.json')


def test_exact_audited_source_and_unchanged_factory_accepted():
    with Operations(forbid=True):
        assert check_protocol(DESIGN/'frozen_protocol.json',AUDIT)['source_hash']==read(AUDIT)['evaluated_source_hash']


@pytest.mark.parametrize('damage',['protocol_sha256','validator_source_hash','validator_files'])
def test_audit_identity_damage_refused(tmp_path,damage):
    value=read(AUDIT)
    if damage=='validator_files':value[damage]['alerts.py']='0'*64
    else:value[damage]='0'*64
    path=tmp_path/'bad.json';atomic(path,value)
    with Operations(forbid=True),pytest.raises(ValueError,match='identity mismatch'):
        check_protocol(DESIGN/'frozen_protocol.json',path)


@pytest.mark.parametrize('mode',['new_fit','incomplete_resume'])
def test_audit_never_allows_new_or_incomplete_fitting(tmp_path,mode):
    with Operations(forbid=True),pytest.raises(ValueError,match='completed forbidden-fit resume only'):
        execute(DESIGN/'frozen_protocol.json',DESIGN/'readiness.json',RUN if mode=='new_fit' else tmp_path,resume=mode!='new_fit',forbid=mode!='new_fit',audit_manifest=AUDIT)


def test_unreviewed_old_source_reuse_still_refused():
    with Operations(forbid=True),pytest.raises(ValueError,match='source identity mismatch'):
        check_protocol(DESIGN/'frozen_protocol.json')


def test_native_asymmetric_cqr_formula_on_reloaded_synthetic_owners():
    saved=SMART/'outputs/matched_intervals005/synthetic_v1/run';before=tree(saved)
    store=Stages(saved,read(saved/'checkpoint_manifest.json')['spec'],resume=True)
    with Operations(forbid=True):
        for h in (1,3):
            _,_,w,_,_=fixture_data(n=1100,groups=2,horizon=h)
            X=w['X'].iloc[:64].to_numpy()
            for level in (.9,.95):
                owner=load_owner(store.get(f'owner_cal_h{h}_cqr_l{int(level*100)}')/'owner.pkl')
                inner=owner._mapie_quantile_regressor
                rawlo,rawhi=[e.predict(X) for e in inner.estimators_[:2]]
                score=inner.conformity_scores_
                q=(1-(1-level)/2)*(1+1/score.shape[1])
                correction=np.quantile(score[:2],q,axis=1,method='higher')
                _,actual=owner.predict_interval(X)
                np.testing.assert_array_equal(actual[:,0,0],rawlo-correction[0])
                np.testing.assert_array_equal(actual[:,1,0],rawhi+correction[1])
    assert tree(saved)==before


def test_native_enbpi_float64_oob_accumulator_on_saved_tiny_owners():
    import warnings
    saved=SMART/'outputs/matched_intervals005/synthetic_v1/run';before=tree(saved)
    store=Stages(saved,read(saved/'checkpoint_manifest.json')['spec'],resume=True)
    with Operations(forbid=True):
        for h in (1,3):
            _,_,w,_,_=fixture_data(n=1100,groups=2,horizon=h)
            per=[np.flatnonzero(w['meta'].group_id.eq(g)) for g in ('asset0','asset1')]
            ca=np.concatenate([r[356:606] for r in per])
            owner=load_owner(store.get(f'owner_cal_h{h}_enbpi')/'owner.pkl')
            preds=np.column_stack([e.predict(w['X'].iloc[ca].to_numpy()) for e in owner.estimator_.estimators_])
            assert preds.dtype==np.float32
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',RuntimeWarning)
                oob=np.nanmean(np.where(owner.estimator_.k_==1,preds.astype(np.float64),np.nan),axis=1)
            expected=w['y'][ca]-oob
            if owner.conformity_score_function_.sym:expected=np.abs(expected)
            np.testing.assert_allclose(owner.conformity_scores_,expected,atol=1e-12,rtol=0,equal_nan=True)
    assert tree(saved)==before
