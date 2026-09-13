import json
import pytest
from src.operational004_authorization import authorize


@pytest.mark.parametrize('changed', ['source_hash','config_hash','candidate_grid','catalogue_seeds','horizon','membership'])
def test_frozen_two_unit_identity_cannot_drift(tmp_path, changed):
    spec=dict(dataset='bdg2',outer_fold=1,model_seed=42,source_hash='source',config_hash='config',
              design_hash='design',data_hash='data',outcomes_hash='outcomes',candidate_grid=[{'id':'frozen'}],
              catalogue_seeds=[42,43,44,45,46],horizon=1)
    members={'final_fit':'frozen'}
    plan=dict(spec,execution_order=[1,0],model_seeds=[42],units={'1':dict(membership_hashes=members)})
    path=tmp_path/'plan.json';path.write_text(json.dumps(plan))
    assert authorize(dict(spec),path,members)==plan['units']['1']
    current=dict(spec)
    if changed=='membership': members={'final_fit':'changed'}
    else: current[changed]='changed'
    with pytest.raises(ValueError,match='mismatch'): authorize(current,path,members)


def test_other_units_and_sequence_rejected(tmp_path):
    path=tmp_path/'plan.json';path.write_text(json.dumps(dict(execution_order=[0,1],model_seeds=[42])))
    with pytest.raises(ValueError,match='sequence'): authorize({},path,{})
    path.write_text(json.dumps(dict(execution_order=[1,0],model_seeds=[42])))
    with pytest.raises(ValueError,match='outside'):
        authorize(dict(dataset='bdg2',outer_fold=2,model_seed=42),path,{})
