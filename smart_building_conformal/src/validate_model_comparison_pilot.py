"""Validate saved pilot predictions, ranks, summaries and full cell coverage."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .unit_checkpoint import UnitCheckpoint,digest,require_cells
from .pilot_conformal import calibrate_absolute,fixed_bounds
from . import metrics as M


def validate(run_dir,protocol_path):
    root=Path(run_dir)
    protocol=json.loads(Path(protocol_path).read_text(encoding="utf-8")); cfg=protocol["config"]
    manifest=json.loads((root/"checkpoint_manifest.json").read_text(encoding="utf-8"))
    if manifest["spec"]["protocol_hash"] != digest(protocol_path):
        raise ValueError("protocol identity mismatch")
    store=UnitCheckpoint(root,manifest["spec"],resume=True)
    keys=[f"h{h}_f0_s42_{name}" for h in cfg["horizons"] for name in cfg["models"]]
    store.require_complete(keys)
    points=pd.read_csv(root/"point_summary.csv",float_precision="round_trip")
    intervals=pd.read_csv(root/"interval_quality.csv",float_precision="round_trip")
    require_cells(points,["horizon","model"],[(h,m) for h in cfg["horizons"] for m in cfg["models"]])
    require_cells(intervals,["horizon","model","nominal_level"],
        [(h,m,l) for h in cfg["horizons"] for m in cfg["models"] for l in cfg["nominal_levels"]])
    support={}; checked=0
    for h in cfg["horizons"]:
        for name in cfg["models"]:
            payload,frames=store.load(f"h{h}_f0_s42_{name}")
            expected_class={"persistence":"src.pilot_forecasters.Persistence",
                "xgboost":"xgboost.sklearn.XGBRegressor","attention_lstm":"src.attention_lstm.AttentionLSTM"}[name]
            if payload["point"]["estimator_class"] != expected_class:
                raise ValueError("estimator attribution mismatch")
            if payload["roles"] != protocol["horizons"][str(h)]["roles"]:
                raise ValueError("unit membership differs from frozen design")
            cal=frames["calibration"]
            np.testing.assert_allclose(cal.absolute_error,np.abs(cal.y_true-cal.point),rtol=0,atol=1e-12)
            for lv in cfg["nominal_levels"]:
                pred=frames["predictions"].loc[lambda d:d.nominal_level.eq(lv)]
                if pred.row_id.duplicated().any() or set(pred.row_id)&set(cal.row_id):
                    raise ValueError("duplicate predictions or calibration/test overlap")
                identity=(tuple(pred.row_id),tuple(cal.row_id),tuple(pred.y_true),tuple(cal.y_true))
                if h in support and identity != support[h]:
                    raise ValueError("models or levels evaluated on different support")
                support[h]=identity
                c=calibrate_absolute(cal.y_true,cal.point,lv)
                if c["status"]!="ok":
                    raise ValueError("pilot calibration support insufficient")
                lo,hi=fixed_bounds(pred.point,c)
                np.testing.assert_allclose(pred.lower,lo,rtol=0,atol=1e-12)
                np.testing.assert_allclose(pred.upper,hi,rtol=0,atol=1e-12)
                p=points[(points.horizon==h)&(points.model==name)].iloc[0]
                v=intervals[(intervals.horizon==h)&(intervals.model==name)&(intervals.nominal_level==lv)].iloc[0]
                for label,actual in [("mae",M.mae(pred.y_true,pred.point)),("rmse",M.rmse(pred.y_true,pred.point))]:
                    np.testing.assert_allclose(p[label],actual,rtol=1e-12,atol=1e-12)
                for label,actual in [("coverage",M.empirical_coverage(pred.y_true,lo,hi)),
                    ("mpiw",M.mean_interval_width(lo,hi)),("winkler",M.winkler_score(pred.y_true,lo,hi,1-lv)),("q",c["q"]),("rank",c["rank"])]:
                    np.testing.assert_allclose(v[label],actual,rtol=1e-12,atol=1e-12)
                if int(v.n_evaluation)!=len(pred) or int(v.n_calibration)!=len(cal):
                    raise ValueError("summary denominators differ from saved rows")
                checked+=1
    return dict(pilot_outputs_valid=True,evidence_status="pilot",units=len(keys),point_cells=len(points),
        interval_cells=len(intervals),recomputed_interval_cells=checked,missing_cells=[],duplicate_cells=[],
        model_support_equal=True,checkpoint_hashes_verified=True,global_study_ready=False,publication_ready=False,
        source_hash=manifest["spec"]["source_hash"],protocol_hash=digest(protocol_path))


if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--run",required=True);ap.add_argument("--protocol",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args(); result=validate(a.run,a.protocol)
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
