"""Meaningful boundary, ownership, resume and one persisted tiny-fit integration."""
import copy
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src import matched_forecasting005 as R, matched_models005 as U
from src.matched_data005 import forecast_roles, validate_roles
from src.matched_validation005 import validate
from src.pilot_data import build_support, role_records
from src.pilot_conformal import calibrate_absolute
from src.unit_checkpoint import digest, signature, source_digest
from test_integration_repairs import fixture_data


def fixture():
    prepared,cfg,_,_=fixture_data(900,3)
    prepared.series[0].group_id='None'
    data=build_support(prepared,cfg,3,24)
    roles=forecast_roles(data['meta'],3,prepared.freq,1)
    return prepared,cfg,data,roles


def test_future_observations_do_not_change_training_inputs():
    prepared,cfg,data,roles=fixture()
    altered=copy.deepcopy(prepared)
    cutoff=data['meta'].iloc[roles['calibration']].origin_time.min()
    altered.series[0].frame.loc[lambda f:f.index>=cutoff,'target']=987654.
    revised=build_support(altered,cfg,3,24)
    tr=roles['fit']
    np.testing.assert_array_equal(data['X'].iloc[tr],revised['X'].iloc[tr])
    np.testing.assert_array_equal(data['y'][tr],revised['y'][tr])
    np.testing.assert_array_equal(data['lazy'].take(data['sequence_rows'][tr]),revised['lazy'].take(revised['sequence_rows'][tr]))


def test_tuning_rejects_calibration_test_contamination_and_future_targets():
    _,_,data,roles=fixture()
    bad={k:v.copy() for k,v in roles.items()};bad['inner0_train']=np.r_[bad['inner0_train'],bad['test'][0]]
    with pytest.raises(ValueError):validate_roles(data['meta'],bad)
    meta=data['meta'].copy();meta.loc[roles['fit'][-1],'target_time']=meta.iloc[roles['test'][-1]].target_time
    with pytest.raises(ValueError):validate_roles(meta,roles)


def test_whole_run_batches_and_boundary_rejection():
    rows=[]
    for group in range(30):
        times=pd.date_range('2023-01-01',periods=20,freq='min')+pd.Timedelta(days=group)
        rows.extend(dict(group_id=f'run{group}',origin_time=t,target_time=t+pd.Timedelta('1min'),row_id=f'{group}:{i}') for i,t in enumerate(times))
    meta=pd.DataFrame(rows)
    for fold in range(3):
        roles=forecast_roles(meta,1,pd.Timedelta('1min'),fold,True)
        for name,idx in roles.items():
            for group in meta.iloc[idx].group_id.unique():
                assert set(meta.index[meta.group_id.eq(group)])<=set(idx)
        assert set(meta.iloc[roles['fit']].group_id).isdisjoint(meta.iloc[roles['calibration']].group_id)


def test_matrix_missing_duplicate_and_unauthorized_keys(tmp_path):
    key=('some_task',7,2,46);rows=[dict(zip(R.KEY_COLUMNS,key),model=m,level=l,data_hash='d',role_bank_hash='r',fit_n=30,calibration_n=20,test_n=10) for m in R.MODELS for l in R.LEVELS]
    file=tmp_path/'matrix.csv';pd.DataFrame(rows).to_csv(file,index=False)
    auth=dict(allowed_units=[list(key)],real_fitting_authorized=True)
    assert len(R.select_matrix(file,key,auth))==6
    with pytest.raises(ValueError,match='authorized'):R.select_matrix(file,('other',7,2,46),auth)
    pd.DataFrame(rows[:-1]).to_csv(file,index=False)
    with pytest.raises(ValueError):R.select_matrix(file,key,auth)
    pd.DataFrame(rows+[rows[0]]).to_csv(file,index=False)
    with pytest.raises(ValueError):R.select_matrix(file,key,auth)


def test_exact_equal_fold_selection_and_own_ranks():
    rows=[dict(candidate_id=c,inner_fold=f,mae=v,best_epoch=e) for c,f,v,e in [(0,0,1,2),(0,1,3,3),(1,0,2,7),(1,1,2,9)]]
    chosen,epochs,_=U.F.select_candidate(rows)
    assert chosen==0 and epochs==3
    a=calibrate_absolute(np.arange(20),np.zeros(20),.95)
    b=calibrate_absolute(np.arange(20),np.arange(20)-.25,.95)
    assert a['rank']==20 and a['q']==19 and b['q']==.25
    assert calibrate_absolute(np.arange(18),np.zeros(18),.95)['status']=='insufficient_calibration'


def test_forbidden_fit_guard_stops_before_model_body():
    entered=[]
    scope={'__name__':'src.test_fake','entered':entered}
    exec('def fit():\n entered.append(True)',scope)
    with pytest.raises(AssertionError,match='forbidden'):
        with U.forbid_fitting():scope['fit']()
    assert not entered


def test_changed_frozen_configuration_is_rejected_before_preparation(tmp_path):
    key=('another_task',6,2,46)
    matrix=tmp_path/'matrix.csv'
    pd.DataFrame([dict(zip(R.KEY_COLUMNS,key),model=m,level=l,data_hash='data',role_bank_hash='roles',
                      fit_n=100,calibration_n=40,test_n=40) for m in R.MODELS for l in R.LEVELS]).to_csv(matrix,index=False)
    config_file=tmp_path/'frozen_config.json';config_file.write_text('{"batch":256}')
    protocol=dict(config=dict(zip(R.KEY_COLUMNS,key)),source_hash=source_digest(),packages=R.versions(),
                  input_hashes={str(config_file):digest(config_file)},matrix_hash=digest(matrix),
                  authorization=dict(allowed_units=[list(key)],real_fitting_authorized=True))
    path=tmp_path/'protocol.json';R.write_json(path,protocol)
    assert R.check_identity(path,matrix,key)['matrix_hash']==digest(matrix)
    config_file.write_text('{"batch":128}')
    with pytest.raises(ValueError,match='frozen input/config'):R.check_identity(path,matrix,key)


def test_tiny_matched_checkpoint_integration(tmp_path,monkeypatch):
    base=Path(os.environ.get('CONFOSENSE_SMOKE_OUT',str(tmp_path/'smoke')))
    base.mkdir(parents=True,exist_ok=False)
    prepared,dcfg,data,roles=fixture();key=('fixture_energy',3,1,43)
    cfg=dict(zip(R.KEY_COLUMNS,key),models=R.MODELS,nominal_levels=R.LEVELS,sequence_length=24,
             inference_batch_size=32,threads=1,n_jobs=1,minimum_launch_available_ram_bytes=0,
             minimum_free_disk_bytes=0,minimum_epoch_available_ram_bytes=0,
             prediction_reload_atol=1e-7,prediction_reload_rtol=1e-7,
             interval_construction='ordinary_split_conformal_absolute_error',
             candidates=dict(persistence=[{}],xgboost=[dict(n_estimators=2,max_depth=2),dict(n_estimators=3,max_depth=2)],
                 attention_lstm=[dict(hidden_size=2,dropout=0.,batch_size=32,learning_rate=lr,max_epochs=2,patience=1) for lr in [.001,.002]]))
    bank=role_records(data['meta'],roles)
    matrix=base/'matrix.csv'
    pd.DataFrame([dict(zip(R.KEY_COLUMNS,key),model=m,level=l,data_hash=data['data_hash'],role_bank_hash=signature(bank),
                      fit_n=len(roles['fit']),calibration_n=len(roles['calibration']),test_n=len(roles['test'])) for m in R.MODELS for l in R.LEVELS]).to_csv(matrix,index=False)
    auth=dict(allowed_units=[list(key)],real_fitting_authorized=True,nonblocking_launch_ram=False,scope='authorized tiny synthetic integration only')
    protocol=dict(config=cfg,resolved_dataset_config=dcfg,authorization=auth,source_hash=source_digest(),packages=R.versions(),
                  matrix_hash=digest(matrix),input_hashes={},support=dict(data_hash=data['data_hash'],roles=bank,role_bank_hash=signature(bank),
                  feature_names=data['feature_names'],sequence_channels=data['sequence_channels']))
    p=base/'protocol.json';R.write_json(p,protocol)
    ready=base/'readiness.json';R.write_json(ready,dict(first_unit_ready=True,source_hash=source_digest(),protocol_hash=digest(p)))
    monkeypatch.setattr(R,'prepare',lambda _:prepared)
    original_fit=U.F.fit;seen=[]
    def traced(name,data_arg,train,params,seed,**kw):
        assert set(train)<=set(roles['fit'])
        np.testing.assert_array_equal(data_arg['y'][train],data['y'][train])
        if kw.get('validation') is not None:
            assert set(kw['validation'])<=set(roles['fit'])
        seen.append(name)
        return original_fit(name,data_arg,train,params,seed,**kw)
    monkeypatch.setattr(U.F,'fit',traced)
    original_run=R.run_model
    def interrupted(name,*args,**kw):
        if name=='xgboost':raise RuntimeError('intentional pre-fit interruption')
        return original_run(name,*args,**kw)
    monkeypatch.setattr(R,'run_model',interrupted)
    run=base/'run'
    with pytest.raises(RuntimeError,match='intentional'):R.execute(p,matrix,key,run,ready)
    persistence=run/'units'/U.unit_key(cfg,'persistence')
    preserved={f.name:digest(f) for f in persistence.iterdir()}
    assert seen==[]
    monkeypatch.setattr(R,'run_model',original_run)
    R.execute(p,matrix,key,run,ready,resume=True)
    assert preserved=={f.name:digest(f) for f in persistence.iterdir()}
    assert seen.count('xgboost')==seen.count('attention_lstm')==5
    result=validate(run,p,matrix,key,base/'audit')
    assert result['passed'] and result['saved_model_prediction_checks']==6
    with U.forbid_fitting():
        resumed=R.execute(p,matrix,key,run,ready,resume=True,forbid_fits=True,receipt=base/'resume.json')
    assert resumed['all_run_files_unchanged'] and resumed['models_fitted']==0
    # Corruption of artifacts, source/config, and current data must all fail.
    artifact=run/'units'/U.unit_key(cfg,'xgboost')/'model.ubj'
    raw=artifact.read_bytes();artifact.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='corrupt'):R.execute(p,matrix,key,run,ready,resume=True,forbid_fits=True)
    artifact.write_bytes(raw)
    old=p.read_bytes();bad=copy.deepcopy(protocol);bad['source_hash']='changed';R.write_json(p,bad)
    with pytest.raises(ValueError,match='source'):R.execute(p,matrix,key,run,ready,resume=True,forbid_fits=True)
    p.write_bytes(old)
    changed=copy.deepcopy(prepared);changed.series[0].frame.iloc[40,0]+=1
    monkeypatch.setattr(R,'prepare',lambda _:changed)
    with pytest.raises(ValueError,match='fresh data'):R.execute(p,matrix,key,run,ready,resume=True,forbid_fits=True)
    R.write_json(base/'smoke_summary.json',dict(passed=True,synthetic_learned_fits=len(seen),tuning_fits=8,final_fits=2,
                  real_data_fits=0,point_cells=3,interval_cells=6,completed_resume_fits=0,
                  interrupted_before_any_learned_fit=True,corruption_source_data_rejected=True,
                  generic_key=key,synthetic_candidates=cfg['candidates']))
