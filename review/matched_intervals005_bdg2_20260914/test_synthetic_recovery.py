"""Recheck the corrected scalar fixture using already verified synthetic owners."""
import importlib.util
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'smart_building_conformal'))
from src.intervals005_common import *
from src.intervals005_owners import raw_predictions
from src.operational004_fixtures import fixture_data


def test_scalar_fixture_recovery_without_fitting():
    testpath=ROOT/'tests/test_matched_intervals005.py'
    spec=importlib.util.spec_from_file_location('bounded_tests',testpath);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    run=ROOT/'outputs/matched_intervals005/synthetic_v1/run';before=tree(run)
    stages=Stages(run,read(run/'checkpoint_manifest.json')['spec'],resume=True)
    with Operations(forbid=True):
        prepared,s,w,cfg,fc=fixture_data(n=1100,groups=2,horizon=3)
        per=[np.flatnonzero(w['meta'].group_id.eq(g)) for g in ('asset0','asset1')]
        tr=np.concatenate([r[:350] for r in per]);ca=np.concatenate([r[356:606] for r in per]);te=np.concatenate([np.r_[r[612:672],r[710:770]] for r in per])
        def metadata(rows):
            f=w['meta'].iloc[rows][['row_id','group_id','origin_time','target_time']].reset_index(drop=True).copy();f['y_true']=w['y'][rows];f['available']=True;return f
        cal=metadata(ca);test=metadata(te);test.loc[[4,17,81],'available']=False;X=w['X'].iloc[te].reset_index(drop=True)
        path=stages.get('owner_cal_h3_cqr_l95');owner=load_owner(path/'owner.pkl')
        raw=raw_predictions(owner,'cqr',X.to_numpy(),[.95]);rawcal=raw_predictions(owner,'cqr',w['X'].iloc[ca].to_numpy(),[.95])
        fixture=dict(data={3:dict(prepared=prepared,segmented=s,w=w,cfg=cfg,fc=fc,tr=tr,ca=ca,te=te,cal=cal,test=test,X=X)},owners={(3,'cqr',.95):(owner,path,raw,rawcal)})
        module.test_corrupted_features_zero_control_scalar_replay_and_future_inputs(fixture)
    assert tree(run)==before
