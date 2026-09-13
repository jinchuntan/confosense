"""A source-linked pilot comparison; no statistical-superiority annotations."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .unit_checkpoint import digest


def build(run_dir,out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    run,out=Path(run_dir),Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    points=pd.read_csv(run/"point_summary.csv"); intervals=pd.read_csv(run/"interval_quality.csv")
    models=["persistence","xgboost","attention_lstm"]
    names=["Persistence","XGBoost","Attention-LSTM"]; colours=["#777777","#0072B2","#D55E00"]
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for model,name,colour in zip(models,names,colours):
        p=points[points.model==model].sort_values("horizon")
        axes[0,0].plot(p.horizon*10,p.mae,"o-",label=name,color=colour)
        for lv,style in [(0.9,"--"),(0.95,"-")]:
            d=intervals[(intervals.model==model)&(intervals.nominal_level==lv)].sort_values("horizon")
            axes[0,1].plot(d.horizon*10,d.coverage*100,"o"+style,color=colour)
            axes[1,0].plot(d.horizon*10,d.mpiw,"o"+style,color=colour)
        axes[1,1].plot(p.horizon*10,p.tuning_seconds+p.final_fit_seconds,"o-",label=name,color=colour)
    axes[0,0].set(title="Point forecast error",ylabel="MAE (temperature units)")
    axes[0,1].set(title="Coverage: dashed 90%, solid 95%",ylabel="Observed coverage (%)")
    axes[0,1].axhline(90,color="black",ls="--",lw=.8,alpha=.5)
    axes[0,1].axhline(95,color="black",ls="-",lw=.8,alpha=.5)
    axes[1,0].set(title="Interval width: read alongside coverage",ylabel="MPIW (temperature units)")
    axes[1,1].set(title="Measured tuning + final fitting cost",ylabel="Wall time (seconds)",yscale="symlog")
    for ax in axes.flat:
        ax.set_xticks([10,30,60]); ax.set_xlabel("Forecast horizon (minutes)"); ax.grid(alpha=.2)
    axes[0,0].legend(frameon=False)
    fig.suptitle("PLEIA temperature pilot | outer fold 0 | seed 42",fontsize=16)
    fig.text(.5,.015,"Fixed model-specific split conformal. One fold/seed; previously inspected test data. No superiority claim.",ha="center",fontsize=9)
    fig.tight_layout(rect=(0,.035,1,.95))
    fig.savefig(out/"pilot_comparison.png",dpi=150)
    fig.savefig(out/"pilot_comparison.svg")
    plt.close(fig)
    (out/"figure_sources.json").write_text(json.dumps({str(p):digest(p) for p in
        [run/"point_summary.csv",run/"interval_quality.csv",out/"pilot_comparison.png",out/"pilot_comparison.svg"]},indent=2),encoding="utf-8")


if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--run",required=True); ap.add_argument("--out",required=True)
    args=ap.parse_args(); build(args.run,args.out)
