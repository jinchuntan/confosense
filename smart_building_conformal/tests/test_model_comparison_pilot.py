"""Pilot-specific ranks, role isolation, matched support and real model provenance."""
from dataclasses import replace
import io
import json
import numpy as np
import pandas as pd
import pytest
import torch
from src import model_comparison_pilot as P, pilot_forecasters as F
from src.pilot_conformal import calibrate_absolute, fixed_bounds
from src.pilot_data import build_support,pilot_roles,role_records,LazySequences
from src.unit_checkpoint import UnitCheckpoint,source_digest,digest
from test_integration_repairs import fixture_data


@pytest.mark.parametrize("n,level,rank,q",[(19,.95,19,18.),(99,.9,90,89.),(9,.9,9,8.),(18,.95,19,np.inf),(0,.9,1,np.inf)])
def test_exact_conformal_order_statistic_and_insufficient_rank(n,level,rank,q):
    c=calibrate_absolute(np.arange(n),np.zeros(n),level)
    assert c["rank"]==rank and c["q"]==q
    assert (c["status"]=="ok")==np.isfinite(q)
    lo,hi=fixed_bounds(np.array([2.,4.]),c)
    assert np.array_equal(lo,np.array([2.,4.])-q)


def tiny_config():
    return dict(dataset="pleia",horizons=[1],outer_fold_id=0,model_seed=42,
        models=["persistence","xgboost","attention_lstm"],nominal_levels=[.9,.95],
        sequence_length=24,inference_batch_size=32,threads=1,
        minimum_launch_available_ram_bytes=0,minimum_epoch_available_ram_bytes=0,
        interval_construction="ordinary_split_conformal_absolute_error",
        candidates={"persistence":[{}],"xgboost":[{"n_estimators":2,"max_depth":2},{"n_estimators":3,"max_depth":2}],
          "attention_lstm":[dict(hidden_size=2,dropout=0.,batch_size=32,learning_rate=.001,max_epochs=2,patience=1),
                            dict(hidden_size=2,dropout=0.,batch_size=32,learning_rate=.002,max_epochs=2,patience=1)]})


def setup_data():
    prepared,cfg,_,_=fixture_data(900,1)
    data=build_support(prepared,cfg,1,24)
    roles=pilot_roles(data["meta"],1,prepared.freq)
    return prepared,cfg,data,roles


def test_common_support_drops_sequence_gaps_for_every_model():
    prepared,cfg,_,_=fixture_data(900,1)
    series=prepared.series[0]; series.frame.iloc[500,0]=np.nan
    data=build_support(prepared,cfg,1,24)
    assert data["excluded_rows"]>0
    assert len(data["X"])==len(data["y"])==len(data["sequence_rows"])
    assert data["lazy"].valid[data["sequence_rows"]].all()
    t=series.frame.index[501]
    assert t not in set(data["meta"].origin_time)


def test_lazy_batches_match_existing_sequence_values_and_order():
    from src import windowing
    prepared,cfg,data,_=setup_data()
    actual,valid,names=windowing.build_dataset_sequences(prepared,1,24,data["meta"])
    assert valid.all() and names==data["sequence_channels"]
    order=np.array([10,1,70,20])
    assert np.array_equal(data["lazy"].take(data["sequence_rows"][order]),actual[order])


def test_final_calibration_reserved_before_two_expanding_tuning_folds():
    _,_,data,roles=setup_data()
    assert set(roles["fit"]).isdisjoint(roles["calibration"])
    assert set(roles["fit"]).isdisjoint(roles["test"])
    for i in [0,1]:
        tr,va=roles[f"inner{i}_train"],roles[f"inner{i}_validation"]
        assert set(tr).union(va)<=set(roles["fit"])
        assert data["meta"].iloc[tr].target_time.max()<data["meta"].iloc[va].origin_time.min()
    assert set(roles["inner0_train"])<set(roles["inner1_train"])


def test_tuning_averages_folds_equally_and_breaks_ties_by_candidate_id():
    rows=[dict(candidate_id=c,inner_fold=f,mae=v,best_epoch=e)
          for c,f,v,e in [(0,0,1.,2),(0,1,3.,3),(1,0,2.,5),(1,1,2.,6)]]
    chosen,epochs,scores=F.select_candidate(rows)
    assert chosen==0 and epochs==3
    with pytest.raises(ValueError,match="exactly two"):
        F.select_candidate(rows[:-1])


def test_actual_models_own_calibration_errors_and_share_evaluation_rows(monkeypatch):
    torch.set_num_threads(1)
    _,_,data,roles=setup_data(); cfg=tiny_config()
    original=F.fit; seen=[]
    def traced(name,data,tr,params,seed,**kwargs):
        seen.append((name,set(tr),set(kwargs.get("validation") or []) if isinstance(kwargs.get("validation"),list) else kwargs.get("validation")))
        assert set(tr)<=set(roles["fit"])
        if kwargs.get("validation") is not None:
            assert set(kwargs["validation"])<=set(roles["fit"])
        return original(name,data,tr,params,seed,**kwargs)
    monkeypatch.setattr(F,"fit",traced)
    ids=[]; error_sets=[]
    for name in cfg["models"]:
        payload,frames,artifacts=P.run_unit(name,1,data,roles,cfg)
        ids.append(frames["predictions"].row_id.tolist())
        cal=frames["calibration"]
        assert np.array_equal(cal.absolute_error.to_numpy(),np.abs(cal.y_true-cal.point))
        error_sets.append(cal.absolute_error.to_numpy())
        expected={"persistence":"Persistence","xgboost":"XGBRegressor","attention_lstm":"AttentionLSTM"}[name]
        assert payload["point"]["estimator_class"].endswith(expected)
        assert len(artifacts)==1 and payload["fallback"] is None
        if name=="attention_lstm":
            state=torch.load(io.BytesIO(artifacts["model.pt"]),weights_only=True)
            assert state["estimator_class"]=="src.attention_lstm.AttentionLSTM"
            restored=F.LazyLSTM(); restored.model=F.AttentionLSTM(state["input_features"],state["parameters"]["hidden_size"],state["parameters"]["dropout"])
            restored.model.load_state_dict(state["state_dict"])
            restored.mean=np.array(state["x_mean"]); restored.std=np.array(state["x_std"])
            restored.y_mean=state["y_mean"]; restored.y_std=state["y_std"]
            pred=restored.predict(data,roles["test"],cfg["inference_batch_size"])
            saved=frames["predictions"].query("nominal_level==0.9").point.to_numpy()
            assert np.array_equal(pred,saved)
    assert ids[0]==ids[1]==ids[2]
    assert not np.array_equal(error_sets[0],error_sets[1])
    assert not np.array_equal(error_sets[1],error_sets[2])


def test_pilot_driver_interruption_resume_and_hash_integrity(tmp_path,monkeypatch):
    prepared,cfg,data,roles=setup_data(); config=tiny_config()
    protocol=dict(config=config,resolved_dataset_config=cfg,
        horizons={"1":dict(data_hash=data["data_hash"],roles=role_records(data["meta"],roles))})
    p=tmp_path/"protocol.json"; P.write_json(p,protocol)
    ready=tmp_path/"ready.json"; P.write_json(ready,dict(pilot_ready=True,source_hash=source_digest(),protocol_hash=digest(p)))
    monkeypatch.setattr(P,"prepare",lambda _: prepared)
    actual=P.run_unit; calls=[]
    def interrupted(name,*args,**kw):
        calls.append(name)
        if name=="xgboost": raise RuntimeError("test interruption")
        return actual(name,*args,**kw)
    monkeypatch.setattr(P,"run_unit",interrupted)
    run=tmp_path/"run"
    with pytest.raises(RuntimeError,match="interruption"):
        P.run(p,ready,run)
    saved=(run/"units"/"h1_f0_s42_persistence"/"predictions.csv.gz").read_bytes()
    def resumed(name,*args,**kw):
        assert name!="persistence"
        return actual(name,*args,**kw)
    monkeypatch.setattr(P,"run_unit",resumed)
    P.run(p,ready,run,resume=True)
    assert (run/"units"/"h1_f0_s42_persistence"/"predictions.csv.gz").read_bytes()==saved
    assert json.loads((run/"pilot_summary.json").read_text())["point_cells"]==3
    from src.validate_model_comparison_pilot import validate
    assert validate(run,p)["pilot_outputs_valid"]
    model=run/"units"/"h1_f0_s42_xgboost"/"model.ubj"; model.write_bytes(b"corrupt")
    with pytest.raises(ValueError,match="corrupt"):
        P.run(p,ready,run,resume=True)
