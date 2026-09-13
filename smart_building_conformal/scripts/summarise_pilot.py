"""Export compact, traceable comparison/resource tables from a complete pilot."""
import argparse
import json
from pathlib import Path
import pandas as pd

ap=argparse.ArgumentParser();ap.add_argument("--run",required=True);ap.add_argument("--out",required=True)
a=ap.parse_args();run=Path(a.run);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
points=pd.read_csv(run/"point_summary.csv")
intervals=pd.read_csv(run/"interval_quality.csv")
summary=json.loads((run/"pilot_summary.json").read_text(encoding="utf-8"))
assert summary["status"]=="complete" and len(points)==9 and len(intervals)==18
wide=points.copy()
for level in [.9,.95]:
    sub=intervals[intervals.nominal_level==level][["horizon","model","coverage","mpiw","winkler","q","rank"]]
    sub=sub.rename(columns={k:k+f"_{int(level*100)}" for k in ["coverage","mpiw","winkler","q","rank"]})
    wide=wide.merge(sub,on=["horizon","model"],validate="one_to_one")
wide["horizon_minutes"]=wide.horizon*10
wide.to_csv(out/"comparison.csv",index=False)
resources=[];tuning=[]
for folder in sorted((run/"units").iterdir()):
    p=json.loads((folder/"payload.json").read_text(encoding="utf-8"))
    tag={k:p["point"][k] for k in ["horizon","model","seed","outer_fold","estimator_class"]}
    for phase,r in p["resources"].items():
        resources.append(dict(**tag,phase=phase,**r,source=str(folder/"payload.json")))
    try:
        frame=pd.read_csv(folder/"tuning.csv.gz")
    except pd.errors.EmptyDataError:
        continue
    for k,v in tag.items():frame[k]=v
    frame["selected_candidate"]=p["selected_candidate"]
    frame["final_epochs"]=p["final_epochs"]
    tuning.append(frame)
pd.DataFrame(resources).to_csv(out/"resource_measurements.csv",index=False)
pd.concat(tuning,ignore_index=True).to_csv(out/"tuning_results.csv",index=False)
by=points.groupby("model").agg(tuning_seconds=("tuning_seconds","sum"),
    final_fit_seconds=("final_fit_seconds","sum"),calibration_seconds=("calibration_seconds","sum"),
    inference_seconds=("inference_seconds","sum"),max_sampled_rss_bytes=("peak_rss_bytes","max"))
by["model_compute_seconds"]=by[["tuning_seconds","final_fit_seconds","calibration_seconds","inference_seconds"]].sum(axis=1)
by["same_cost_15_repetitions_seconds"]=15*by.model_compute_seconds
by.to_csv(out/"measured_cost_and_expansion_scenario.csv")
print(wide[["horizon_minutes","model","mae","rmse","coverage_90","mpiw_90","winkler_90", "coverage_95","mpiw_95","winkler_95","tuning_seconds","final_fit_seconds"]].to_string(index=False))
print('\nCost totals and same-cost 15-repetition scenario (not an ETA):\n'+by.to_string())
