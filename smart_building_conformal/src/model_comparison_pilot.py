"""Freeze, validate and execute the bounded model-specific interval pilot."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import gc
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
import numpy as np
import pandas as pd
from . import split_integrity as SI, metrics as M
from .pilot_data import build_support, pilot_roles, role_records
from .pilot_resources import ResourceMeter, hardware, require_ram
from .pilot_conformal import calibrate_absolute, fixed_bounds
from .unit_checkpoint import UnitCheckpoint, digest, signature, source_digest, require_cells


def write_json(path,data):
    Path(path).write_text(json.dumps(data,indent=2,default=str)+"\n",encoding="utf-8")


def prepare(cfg):
    from .datasets import get_adapter
    return SI.causal_prepared(get_adapter(cfg.get("adapter","pleia")).prepare(cfg),
                              cfg.get("missing",{}).get("max_short_gap_steps",3))


def freeze(config_path,design_dir):
    from .run_study import load_config,resolve_dataset_config
    config=json.loads(Path(config_path).read_text(encoding="utf-8"))
    if (config["dataset"] != "pleia" or config["horizons"] != [1,3,6] or
        config["models"] != ["persistence","xgboost","attention_lstm"] or
        config["nominal_levels"] != [.9,.95] or config["outer_fold_id"] != 0 or
        config["model_seed"] != 42 or any(config[k] for k in
        ("synthetic_fault_injection","alert_rule_selection","adaptive_recalibration"))):
        raise ValueError("configuration exceeds the authorised pilot scope")
    out=Path(design_dir)
    if out.exists() and any(out.iterdir()):
        raise ValueError("frozen design already exists; use a new version")
    out.mkdir(parents=True,exist_ok=True)
    cfg=resolve_dataset_config(load_config(config["study_config"]),"pleia")
    with ResourceMeter() as preparation:
        prepared=prepare(cfg)
        horizons={}; frames=[]; boundaries=[]
        for h in config["horizons"]:
            data=build_support(prepared,cfg,h,config["sequence_length"])
            roles=pilot_roles(data["meta"],h,prepared.freq,config["outer_fold_id"],3)
            records=role_records(data["meta"],roles)
            horizons[str(h)]=dict(data_hash=data["data_hash"], roles=records,
                eligible_rows=data["eligible_rows"], flat_rows=data["flat_rows"],
                excluded_rows=data["excluded_rows"], feature_names=data["feature_names"],
                sequence_channels=data["sequence_channels"], physical_minutes=h*prepared.freq/pd.Timedelta("1min"))
            for name,rows in roles.items():
                frame=data["meta"].iloc[rows][["row_id","group_id","origin_time","target_time"]].copy()
                frame["role"]=name; frame["horizon"]=h; frames.append(frame)
            for a,b in [("fit","calibration"),("calibration","test"),
                        ("inner0_train","inner0_validation"),("inner1_train","inner1_validation")]:
                boundaries.append(dict(horizon=h,left_role=a,right_role=b,
                    **SI.boundary_record(data["meta"],roles[a],roles[b])))
            del data; gc.collect()
    pd.concat(frames,ignore_index=True).to_csv(out/"membership.csv.gz",index=False,compression="gzip")
    pd.DataFrame(boundaries).to_csv(out/"boundaries.csv",index=False)
    protocol=dict(config=config,resolved_dataset_config=cfg,horizons=horizons,
        frozen_at_utc=datetime.now(timezone.utc).isoformat(),models_fitted=0,
        config_file_sha256=digest(config_path), membership_sha256=digest(out/"membership.csv.gz"),
        boundaries_sha256=digest(out/"boundaries.csv"),preparation_resources=preparation.result)
    write_json(out/"frozen_protocol.json",protocol)
    print(json.dumps({h:v["roles"] for h,v in horizons.items()},indent=2),flush=True)
    return protocol


def verify_support(data,roles,frozen):
    if data["data_hash"] != frozen["data_hash"] or role_records(data["meta"],roles) != frozen["roles"]:
        raise ValueError("data/support/role endpoints differ from frozen pilot design")
    if set(roles["fit"]) & set(roles["calibration"]) or set(roles["calibration"]) & set(roles["test"]):
        raise ValueError("overlapping final roles")
    for fold in (0,1):
        tr,va=roles[f"inner{fold}_train"],roles[f"inner{fold}_validation"]
        if not set(tr).union(va) <= set(roles["fit"]):
            raise ValueError("tuning/calibration/test role leakage")


def readiness(protocol_path,out_path):
    protocol=json.loads(Path(protocol_path).read_text(encoding="utf-8")); cfg=protocol["config"]
    base=Path(protocol_path).parent
    checks={"scope":cfg["dataset"]=="pleia" and cfg["horizons"]==[1,3,6] and cfg["model_seed"]==42,
        "fixed_absolute_split_conformal":cfg["interval_construction"]=="ordinary_split_conformal_absolute_error",
        "two_tuning_folds":cfg["inner_validation_folds"]==2,
        "membership_unchanged":digest(base/"membership.csv.gz")==protocol["membership_sha256"],
        "boundaries_unchanged":digest(base/"boundaries.csv")==protocol["boundaries_sha256"]}
    boundaries=pd.read_csv(base/"boundaries.csv")
    checks["zero_overlap"]=(boundaries[["target_overlap_count","row_overlap_count","run_intersections"]]==0).all().all().item()
    prepared=prepare(protocol["resolved_dataset_config"])
    for h in cfg["horizons"]:
        data=build_support(prepared,protocol["resolved_dataset_config"],h,cfg["sequence_length"])
        roles=pilot_roles(data["meta"],h,prepared.freq,cfg["outer_fold_id"],3)
        verify_support(data,roles,protocol["horizons"][str(h)])
        checks[f"h{h}_support_roles_verified"]=True
        checks[f"h{h}_rank_support"]=all(calibrate_absolute(np.zeros(len(roles["calibration"])),
            np.zeros(len(roles["calibration"])),lv)["status"]=="ok" for lv in cfg["nominal_levels"])
    require_ram(cfg["minimum_launch_available_ram_bytes"])
    result=dict(pilot_ready=all(checks.values()),global_study_ready=False,publication_ready=False,
        checks=checks,source_hash=source_digest(),protocol_hash=digest(protocol_path),
        expected_point_cells=9,expected_interval_cells=18,hardware=hardware(),models_fitted=0)
    write_json(out_path,result)
    if not result["pilot_ready"]:
        raise ValueError("pilot readiness failed")
    return result


def run_unit(name,horizon,data,roles,config):
    from . import pilot_forecasters as F
    seed=config["model_seed"]; batch=config["inference_batch_size"]
    tune_records=[]; histories=[]
    with ResourceMeter() as tuning:
        if name == "persistence":
            selected,final_epochs=0,None
        else:
            for candidate_id,params in enumerate(config["candidates"][name]):
                for fold in range(2):
                    tr,va=roles[f"inner{fold}_train"],roles[f"inner{fold}_validation"]
                    start=time.perf_counter()
                    print(f"h{horizon} {name}: candidate {candidate_id}, inner fold {fold}",flush=True)
                    model=F.fit(name,data,tr,params,seed,validation=va,
                        memory_floor=config["minimum_epoch_available_ram_bytes"],
                        progress=lambda row: print(f"  epoch {row['epoch']}, inner MAE {row.get('validation_mae',float('nan')):.5f}",flush=True))
                    prediction=F.predict(model,name,data,va,batch)
                    tune_records.append(dict(candidate_id=candidate_id,inner_fold=fold,
                        mae=M.mae(data["y"][va],prediction),best_epoch=getattr(model,"best_epoch",None),
                        seconds=time.perf_counter()-start,n_train=len(tr),n_validation=len(va),
                        estimator_class=F.actual_identity(model)))
                    for row in getattr(model,"history",[]):
                        histories.append(dict(candidate_id=candidate_id,inner_fold=fold,**row))
                    del model; gc.collect()
            selected,final_epochs,_=F.select_candidate(tune_records)
    params=config["candidates"][name][selected]
    print(f"h{horizon} {name}: refit candidate {selected}, epochs={final_epochs}",flush=True)
    with ResourceMeter() as final_fit:
        model=F.fit(name,data,roles["fit"],params,seed,final_epochs=final_epochs,
            memory_floor=config["minimum_epoch_available_ram_bytes"],
            progress=lambda row: print(f"  final epoch {row['epoch']}",flush=True))
    with ResourceMeter() as calibration:
        calibration_point=F.predict(model,name,data,roles["calibration"],batch)
        calibrations=[calibrate_absolute(data["y"][roles["calibration"]],calibration_point,lv)
                      for lv in config["nominal_levels"]]
    with ResourceMeter() as inference:
        point=F.predict(model,name,data,roles["test"],batch)
    identity=F.actual_identity(model)
    if not np.isfinite(point).all() or not np.isfinite(calibration_point).all():
        raise ValueError("nonfinite model predictions")
    tag=dict(dataset="pleia",horizon=horizon,outer_fold=config["outer_fold_id"],seed=seed,
             model=name,estimator_class=identity,evidence_status="pilot")
    row={**tag,"mae":M.mae(data["y"][roles["test"]],point),
        "rmse":M.rmse(data["y"][roles["test"]],point),"n_fit":len(roles["fit"]),
        "n_calibration":len(roles["calibration"]),"n_evaluation":len(point),
        "tuning_seconds":tuning.result["seconds"] if name != "persistence" else 0.,
        "final_fit_seconds":final_fit.result["seconds"],"calibration_seconds":calibration.result["seconds"],
        "inference_seconds":inference.result["seconds"],"inference_batch_size":batch,
        "inference_rows_per_second":len(point)/inference.result["seconds"],
        "selected_candidate":selected,"final_epochs":final_epochs,"status":"complete"}
    intervals=[]; predictions=[]
    base=data["meta"].iloc[roles["test"]][["row_id","group_id","origin_time","target_time"]].copy()
    base["y_true"]=data["y"][roles["test"]]; base["point"]=point
    for c in calibrations:
        lower,upper=fixed_bounds(point,c)
        good=c["status"]=="ok"
        intervals.append({**tag,**c,"n_evaluation":len(point),"construction":config["interval_construction"],
            "coverage":M.empirical_coverage(base.y_true,lower,upper) if good else None,
            "mpiw":M.mean_interval_width(lower,upper) if good else None,
            "winkler":M.winkler_score(base.y_true,lower,upper,1-c["nominal_level"]) if good else None})
        predictions.append(base.assign(nominal_level=c["nominal_level"],lower=lower,upper=upper,model=name,horizon=horizon))
    cal=data["meta"].iloc[roles["calibration"]][["row_id","group_id","origin_time","target_time"]].copy()
    cal["y_true"]=data["y"][roles["calibration"]]; cal["point"]=calibration_point
    cal["absolute_error"]=np.abs(cal.y_true-cal.point)
    resources={k:v.result for k,v in (("tuning",tuning),("final_fit",final_fit),("calibration",calibration),("inference",inference))}
    row.update(baseline_rss_bytes=tuning.result["baseline_rss_bytes"],
        peak_rss_bytes=max(v["peak_rss_bytes"] for v in resources.values()),
        peak_private_bytes=max(v["peak_private_bytes"] for v in resources.values()))
    if name == "attention_lstm":
        artifact={"model.pt":model.artifact()}
    elif name == "xgboost":
        artifact={"model.ubj":bytes(model.save_raw(raw_format="ubj"))} if hasattr(model,"save_raw") else {"model.ubj":bytes(model.get_booster().save_raw(raw_format="ubj"))}
    else:
        artifact={"model.json":json.dumps({"estimator_class":identity,"column":model.column}).encode()}
    payload=dict(point=row,intervals=intervals,parameters=params,resources=resources,
        model_seed=seed,seed_affects_fitting=name!="persistence",fallback=None,
        final_epochs=final_epochs,selected_candidate=selected,roles=role_records(data["meta"],roles),
        calibration_construction=config["interval_construction"],fixed_calibration=True)
    frames=dict(predictions=pd.concat(predictions,ignore_index=True),calibration=cal,
                tuning=pd.DataFrame(tune_records),training_history=pd.DataFrame(histories))
    del model; gc.collect()
    return payload,frames,artifact


def run(protocol_path,ready_path,out_root,*,resume=False):
    import torch
    protocol=json.loads(Path(protocol_path).read_text(encoding="utf-8")); config=protocol["config"]
    ready=json.loads(Path(ready_path).read_text(encoding="utf-8"))
    if not ready.get("pilot_ready") or ready["protocol_hash"] != digest(protocol_path) or ready["source_hash"] != source_digest():
        raise ValueError("pilot readiness does not match code/protocol")
    torch.set_num_threads(config["threads"])
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    spec=dict(protocol_hash=digest(protocol_path),source_hash=source_digest(),
        data_hashes={h:v["data_hash"] for h,v in protocol["horizons"].items()},
        config=config,packages={n:importlib.metadata.version(n) for n in
            ("numpy","pandas","scikit-learn","xgboost","torch")})
    store=UnitCheckpoint(out_root,spec,resume=resume); out=Path(out_root)
    if not (out/"execution_environment.json").exists():
        write_json(out/"execution_environment.json",dict(hardware=hardware(),torch_version=torch.__version__,
            torch_threads=torch.get_num_threads(),torch_interop_threads=torch.get_num_interop_threads(),
            command=sys.argv,code_commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            start_utc=datetime.now(timezone.utc).isoformat()))
    prepared=prepare(protocol["resolved_dataset_config"])
    expected=[f"h{h}_f0_s42_{name}" for h in config["horizons"] for name in config["models"]]
    points=[]; intervals=[]; failures=[]
    try:
        for h in config["horizons"]:
            with ResourceMeter() as preparation:
                data=build_support(prepared,protocol["resolved_dataset_config"],h,config["sequence_length"])
                roles=pilot_roles(data["meta"],h,prepared.freq,config["outer_fold_id"],3)
                verify_support(data,roles,protocol["horizons"][str(h)])
            write_json(out/f"preparation_h{h}.json",preparation.result)
            for name in config["models"]:
                key=f"h{h}_f0_s42_{name}"
                loaded=store.load(key) if resume else None
                if loaded is None:
                    launch=require_ram(config["minimum_launch_available_ram_bytes"])
                    print(f"START {key}; free RAM {launch['available_ram_bytes']/2**30:.2f} GiB",flush=True)
                    payload,frames,artifacts=run_unit(name,h,data,roles,config)
                    payload["launch_memory"]=launch
                    store.save(key,payload,frames,artifacts=artifacts)
                else:
                    payload,frames=loaded
                    print(f"RESUMED {key}",flush=True)
                points.append(payload["point"]); intervals.extend(payload["intervals"])
                pd.DataFrame(points).to_csv(out/"point_summary.csv",index=False)
                pd.DataFrame(intervals).to_csv(out/"interval_quality.csv",index=False)
                print(f"COMPLETE {key}",flush=True)
            del data; gc.collect()
        store.require_complete(expected)
        require_cells(pd.DataFrame(points),["horizon","model"],[(h,m) for h in config["horizons"] for m in config["models"]])
        require_cells(pd.DataFrame(intervals),["horizon","model","nominal_level"],
            [(h,m,l) for h in config["horizons"] for m in config["models"] for l in config["nominal_levels"]])
        write_json(out/"pilot_summary.json",dict(status="complete",evidence_status="pilot",point_cells=len(points),
            interval_cells=len(intervals),missing_cells=[],failed_cells=[],source_hash=source_digest(),
            protocol_hash=digest(protocol_path),global_study_ready=False,publication_ready=False))
    except BaseException as exc:
        complete={p.name for p in (out/"units").iterdir() if p.is_dir()}
        failures.append(dict(unit=locals().get("key"),error=f"{type(exc).__name__}: {exc}",traceback=traceback.format_exc()))
        write_json(out/f"failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",dict(failures=failures,missing_units=sorted(set(expected)-complete)))
        raise


def measure_bdg2(out_path):
    from .run_study import load_config,resolve_dataset_config
    cfg=resolve_dataset_config(load_config("configs/study_final_dissertation_v2.yaml"),"bdg2")
    require_ram(768*2**20)
    with ResourceMeter() as total:
        with ResourceMeter() as adapter:
            prepared=prepare(cfg)
        rows=[]
        for h in cfg["horizons"]:
            with ResourceMeter() as stage:
                data=build_support(prepared,cfg,h,cfg["models"]["lstm"]["seq_len"])
                # Traverse all eligible sequence windows in bounded batches;
                # no full tensor or fitted model is constructed.
                checksum=0.
                for start in range(0,len(data["meta"]),256):
                    batch=data["lazy"].take(data["sequence_rows"][start:start+256])
                    checksum+=float(batch.sum(dtype=np.float64))
                rows.append(dict(horizon=h,rows=len(data["meta"]),flat_feature_bytes=int(data["X"].memory_usage(deep=True).sum()),
                    lazy_stored_bytes=data["lazy"].stored_bytes,n_channels=data["lazy"].n_features,
                    sequence_length=data["lazy"].seq_len,
                    equivalent_full_tensor_bytes=len(data["meta"])*data["lazy"].seq_len*data["lazy"].n_features*4,
                    traversal_checksum=checksum,models_fitted=0))
            rows[-1]["resources"]=stage.result
            del data; gc.collect()
    result=dict(dataset="bdg2",hardware=hardware(),adapter_resources=adapter.result,
        total_resources=total.result,horizons=rows,models_fitted=0,method="lazy channels; every eligible sequence traversed in batches of 256")
    write_json(out_path,result); print(json.dumps(result,indent=2),flush=True)
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("action",choices=["freeze","readiness","run","bdg2-memory"])
    ap.add_argument("--config",default="configs/model_comparison_pilot_v1.json")
    ap.add_argument("--protocol",default="protocols/model_comparison_pilot_v1/frozen_protocol.json")
    ap.add_argument("--readiness",default="protocols/model_comparison_pilot_v1/readiness.json")
    ap.add_argument("--out",required=True); ap.add_argument("--resume",action="store_true")
    a=ap.parse_args()
    if a.action=="freeze": freeze(a.config,a.out)
    elif a.action=="readiness": readiness(a.protocol,a.out)
    elif a.action=="run": run(a.protocol,a.readiness,a.out,resume=a.resume)
    else: measure_bdg2(a.out)


if __name__=="__main__": main()
