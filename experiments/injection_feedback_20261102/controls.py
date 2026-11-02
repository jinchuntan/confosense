"""Specialist flatline baseline and a different building-temperature dataset."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from compare import RELATIVE, align_inputs, first_state, load_runner, transitions


def repeated(y):
    x = np.asarray(y, dtype=float)
    equal = np.r_[False, np.isfinite(x[1:]) & (x[1:] == x[:-1])]
    i = np.arange(len(x))
    return i - np.maximum.accumulate(np.where(equal, 0, i))


def workload(flag, boundaries, steps_per_day):
    onsets = flag & (boundaries | ~np.r_[False, flag[:-1]])
    return int(onsets.sum()), float(onsets.sum()*steps_per_day/len(flag)), float(flag.mean())


def select_score(score, values, boundary, steps_per_day, over=False):
    candidates = []
    for t in values:
        flag = score > t if over else score >= t
        _, rate, active = workload(flag, boundary, steps_per_day)
        if rate <= .5 and active <= .2:
            candidates.append((.5-rate,active,t))
    if not candidates:
        raise ValueError("No admissible threshold")
    return min(candidates)[2]


def bnd(meta):
    return np.r_[True,(np.diff(meta.time.to_numpy()) != np.timedelta64(1,'h')) |
                 (meta.building.to_numpy()[1:] != meta.building.to_numpy()[:-1])]


def meter_run(frames, meta, observed=None):
    parts = []
    for b,g in meta.groupby("building",sort=False):
        series = frames[b].y.copy()
        if observed is not None:
            series.loc[g.time] = observed[g.index]
        parts.append(pd.Series(repeated(series),index=series.index).loc[g.time])
    return np.concatenate(parts)


def bdg(args):
    study = load_runner(args.runner)
    unit, frames, sites, meta, masks = align_inputs(study,args.raw,args.runs,args.fold)
    clean = meter_run(frames,meta)
    sel = meta[masks["selection"]]
    limit = select_score(clean[masks["selection"]],range(1,97),bnd(sel),24)
    test = meta[masks["test"]].reset_index(drop=True)
    y = test.y.to_numpy()
    episode_count, rate, active = workload(clean[masks["test"]]>=limit,bnd(test),24)
    stats = dict(min_repeats=int(limit),test_rows=len(y),background_episodes=episode_count,
                 background_rate=rate,time_in_alert=active)
    study.write_json(args.out/f"{args.cohort}_f{args.fold}_flat_policy.json",stats)
    fit=meta[masks["fit"]]
    scales={b:max(float(1.4826*(g.y-g.y.median()).abs().median()),1e-6) for b,g in fit.groupby("building")}
    policies=json.loads((unit/"selected.json").read_text())
    k=next(i for i,p in enumerate(policies) if p["method"]=="asymmetric_cqr" and p["budget"]==.5)
    tables=[]
    with np.load(unit/"alert_flags.npz") as saved:
        for seed in study.PROTOCOL["event_catalogue_seeds"]:
            obs,cat=study.inject(test,y,scales,args.fold,seed)
            pd.testing.assert_frame_equal(cat,pd.read_csv(unit/f"catalogue_{seed}.csv.gz"),check_dtype=False)
            events=cat[cat.effective].sort_values(["building","start"]).reset_index(drop=True)
            ix=events.start.to_numpy()[:,None]+RELATIVE
            change=obs[ix[:,1:5]]!=y[ix[:,1:5]]
            live=np.unpackbits(saved[f"c{seed}_p{k}_numerical"])[:len(y)].astype(bool)
            flat=meter_run(frames,test,obs)>=limit
            counts=transitions(events,first_state(live,ix,change),first_state(flat,ix,change),sites)
            tables.append(counts.assign(catalogue=seed,cohort=args.cohort,fold=args.fold))
    pd.concat(tables,ignore_index=True).to_csv(args.out/f"{args.cohort}_f{args.fold}_flat.csv.gz",index=False)


def design(series, delay):
    clock=series.index
    X=pd.DataFrame(index=clock)
    for lag in [1,2,3,6,12]:
        X[f"lag{lag}"]=series.shift(lag+delay)
    X["previous_day"]=series.shift(144)
    phase=2*np.pi*(clock.hour*60+clock.minute)/1440
    X["sin"]=np.sin(phase)
    X["cos"]=np.cos(phase)
    return X


def external(args):
    sha=hashlib.sha256(args.source.read_bytes()).hexdigest()
    if sha!="b31cc2b9e1c928fc7914dc616cdf60ca19c42608e7371862e9e00cf2ac5b0b9f":
        raise ValueError("Unexpected archived temperature stream")
    data=pd.read_csv(args.source,usecols=["target_time","y_true"],parse_dates=["target_time"]).drop_duplicates()
    y=data.set_index("target_time").sort_index().y_true.asfreq("10min")
    assert y.index.is_unique and len(data)==9907
    design_by_delay={k:design(y,k) for k in [0,4]}
    support=y.notna() & design_by_delay[0].notna().all(axis=1) & design_by_delay[4].notna().all(axis=1)
    i=np.arange(len(y)); n=len(y)
    fit=support&(i<int(n*.5)); cal=support&(i>=int(n*.5))&(i<int(n*.65))
    sel=support&(i>=int(n*.65))&(i<int(n*.8)); test=support&(i>=int(n*.8))
    def boundaries(mask):
        return np.r_[True, np.diff(i[mask])!=1]
    models={}; records=[]; policies=[]
    for delay,X in design_by_delay.items():
        estimator=make_pipeline(StandardScaler(),Ridge(alpha=1)).fit(X[fit],y[fit])
        pred=np.full(n,np.nan); pred[support]=estimator.predict(X[support])
        error=np.abs(y.to_numpy()-pred)
        calibration=np.sort(error[cal])
        levels=np.linspace(.5,.999,500)
        thresholds=np.unique(calibration[np.minimum(len(calibration)-1,
                np.ceil((len(calibration)+1)*levels).astype(int)-1)])
        limit=select_score(error[sel],thresholds,boundaries(sel),144,over=True)
        models[delay]=(estimator,pred,limit)
        episodes,rate,active=workload(error[test]>limit,boundaries(test),144)
        policies.append(dict(rule=f"ridge_delay_{delay}",threshold=limit,episodes=episodes,
                             background_rate=rate,time_in_alert=active,test_rows=int(test.sum())))
    run=repeated(y)
    limit=select_score(run[sel],range(1,97),boundaries(sel),144)
    episodes,rate,active=workload(run[test]>=limit,boundaries(test),144)
    policies.append(dict(rule="flatline",threshold=limit,episodes=episodes,background_rate=rate,
                         time_in_alert=active,test_rows=int(test.sum())))
    for seed in range(42,47):
        rng=np.random.default_rng(seed)
        # The complete eight-sample maximum slot and its matching window must be observed.
        candidates=[j for j in np.flatnonzero(test) if j>=1 and j+12<=n and test.iloc[j-1:j+12].all()]
        rng.shuffle(candidates)
        occupied=np.zeros(n,bool); events=[]; measured=y.copy()
        for j in candidates:
            if len(events)==30:
                break
            if occupied[j-1:j+12].any():
                continue
            duration=[2,4,8][len(events)%3]
            occupied[j-1:j+12]=True
            measured.iloc[j:j+duration]=y.iloc[j-1]
            changed=measured.iloc[j:j+duration].to_numpy()!=y.iloc[j:j+duration].to_numpy()
            events.append((j,duration,changed))
        assert len(events)==30
        flags={"flatline":repeated(measured)>=limit}
        for delay,(model,detached,t) in models.items():
            x=design(measured,delay)
            updated=np.full(n,np.nan)
            updated[support]=model.predict(x[support])
            flags[f"ridge_delay_{delay}_fixed"]=np.abs(measured.to_numpy()-detached)>t
            flags[f"ridge_delay_{delay}_live"]=np.abs(measured.to_numpy()-updated)>t
        for j,duration,changed in events:
            if not changed.any():
                continue
            a,b=np.flatnonzero(changed)[[0,-1]]
            for name,flag in flags.items():
                local=flag[j-1:j+duration+3]
                onset=np.flatnonzero(local[1:] & ~local[:-1])
                state="miss" if not len(onset) else "before" if onset[0]<a else "during" if onset[0]<=b else "after"
                records.append(dict(catalogue=seed,start=str(y.index[j]),duration=duration,rule=name,state=state))
    detail=pd.DataFrame(records)
    detail.to_csv(args.out/"pleia_events.csv.gz",index=False)
    detail.groupby(["rule","duration","state"]).size().rename("events").reset_index().to_csv(
        args.out/"pleia_transitions.csv",index=False)
    pd.DataFrame(policies).to_csv(args.out/"pleia_policies.csv",index=False)


if __name__=="__main__":
    p=argparse.ArgumentParser(); modes=p.add_subparsers(dest="command",required=True)
    b=modes.add_parser("bdg")
    for k in ["raw","runner","runs","out"]:
        b.add_argument(k,type=Path)
    b.add_argument("cohort");b.add_argument("fold",type=int)
    e=modes.add_parser("pleia");e.add_argument("source",type=Path);e.add_argument("out",type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    if args.command=="bdg":
        bdg(args)
    else:
        external(args)
