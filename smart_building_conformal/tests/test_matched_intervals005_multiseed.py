"""No-fit acceptance for the bounded fold-2 seed extension."""
from pathlib import Path
import json
import pandas as pd
import pytest

from src.intervals005_common import LEVELS, METHODS, ROOT, digest
from src.intervals005_data import MATRIX, historical_references
from src.intervals005_owners import method_spec
from src.matched_intervals005 import config_scope


REPO=ROOT.parent
SEEDS=[43,44,45,46]


def authorization(seed):
    return json.loads((ROOT/f'configs/matched_intervals005_bdg2_multiseed_s{seed}_v2.json').read_text())


def test_exact_120_published_keys_and_narrow_scope():
    proposed=pd.read_csv(ROOT/'outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/next_proposed_method_keys.csv')
    expected={(s,h,l,m) for s in SEEDS for h in (1,3,6) for l in LEVELS for m in METHODS}
    actual=set(proposed[['model_seed','horizon','level','method']].itertuples(index=False,name=None))
    assert actual==expected and len(proposed)==120
    for seed in SEEDS:
        scope,cells=config_scope(authorization(seed),MATRIX)
        assert scope['model_seed']==seed and len(cells)==30
    bad=authorization(43);bad['scope']['outer_fold']=1
    with pytest.raises(ValueError,match='authorization'):config_scope(bad,MATRIX)
    legacy=json.loads((ROOT/'configs/matched_intervals005_bdg2_authorization_v1.json').read_text())
    scope,cells=config_scope(legacy,MATRIX)
    assert scope['model_seed']==42 and len(cells)==30
    bad=authorization(43);bad['scope']['model_seed']=42
    with pytest.raises(ValueError,match='authorization'):config_scope(bad,MATRIX)


@pytest.mark.parametrize('seed',SEEDS)
def test_seed_propagation_and_historical_dscp_owners(seed):
    spec=method_spec(seed)
    assert spec['seed']==seed
    assert spec['cqr']['estimator_parameters']['random_state']==seed
    assert spec['enbpi']['base_parameters']['random_state']==seed
    assert spec['enbpi']['bootstrap']['random_state']==seed
    assert spec['enbpi']['wrapper']['random_state']==seed
    assert spec['dscp']['seed']==seed
    refs=historical_references('bdg2',2,seed,[1,3,6])
    assert set(refs)=={'1','3','6'}
    for h,reference in refs.items():
        owner=REPO/reference['owner_directory']
        assert f'_h{h}_f2_s{seed}_xgboost' in str(owner)
        assert digest(REPO/owner/'model.ubj')==reference['owner_hashes']['model.ubj']


def test_seed42_seasonal_alias_sources_are_complete_and_distinct_from_method_cells():
    root=ROOT/'outputs/matched_intervals005/bdg2_f2_s42_v1/stages'
    for h in (1,3,6):
        stage=root/f'seasonal_h{h}'
        assert {p.name for p in stage.iterdir()}>={'calibration.csv.gz','interval_90.csv.gz','interval_95.csv.gz','point.json','calibration.json','COMPLETE.json'}
        point=json.loads((stage/'point.json').read_text())
        assert point['model_seed']==42 and point['learned_fits']==0
