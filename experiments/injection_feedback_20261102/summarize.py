"""Reconcile prior event counts, then publish the prespecified paired comparisons."""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent / "recovery_replay_20261102" / "results"
COHORTS = ["pilot", "replication"]
METHOD = "asymmetric_cqr"
PRIMARY = 'method == @METHOD and channel == "numerical" and budget == 0.5'
BASE = ["cohort", "method", "budget", "channel"]


def read_arm(work, arm):
    units = [pd.read_csv(work / f"{c}_f{fold}_{arm}.csv.gz")
             for c in COHORTS for fold in range(3)]
    data = pd.concat(units, ignore_index=True)
    assert data.catalogue.nunique() == 5 and (data["count"] > 0).all()
    return data


def indicators(data):
    pairs = data[["from_state","to_state"]]
    live, alt = (pairs.iloc[:,j] for j in [0,1])
    masks = dict(events=np.ones(len(data),bool), live_hit=live.ne("miss"), alt_hit=alt.ne("miss"),
                 live_during=live.eq("during"), alt_during=alt.eq("during"),
                 live_only_hit=live.ne("miss") & alt.eq("miss"), alt_only_hit=alt.ne("miss") & live.eq("miss"),
                 both_during=live.eq("during") & alt.eq("during"))
    return data.assign(**{name:data["count"] * mask for name, mask in masks.items()}), list(masks)


def summarize(work, out):
    out.mkdir(parents=True, exist_ok=True)
    placements = read_arm(work, "placement")
    counts, measures = indicators(placements)
    controls = []
    expected_names = {"events":"events", "hits":"live_hit", "during_change_span":"live_during"}
    for name, dims in [("operating_points", []), ("disturbances", ["family","severity"]), ("sites", ["site"])]:
        idx = BASE + dims
        measured = counts.groupby(idx)[measures].sum().sort_index()
        prior = pd.read_csv(ARCHIVE / (name + ".csv")).set_index(idx).sort_index()
        for saved, observed in expected_names.items():
            pd.testing.assert_series_equal(prior[saved], measured[observed], check_names=False)
        measured.to_csv(out / (name + ".csv"))
    primary = placements.query(PRIMARY)
    primary.groupby(["cohort","family","from_state","to_state"])["count"].sum().to_csv(
        out / "primary_transitions.csv")
    reference = pd.read_csv(ARCHIVE / "policy_comparison.csv").query(PRIMARY)
    policies = []
    for arm in ["placement", "delay", "flat"]:
        data = primary if arm == "placement" else read_arm(work, arm)
        if arm == "delay":
            data = data.query(PRIMARY)
        rows, columns = indicators(data)
        for cohort in COHORTS:
            table = rows[rows.cohort.eq(cohort)]
            workrate = reference.loc[reference.cohort.eq(cohort),"test_background_episodes_per_meter_day"].item()
            if arm != "placement":
                files = [json.loads((work / f"{cohort}_f{f}_{arm}_policy.json").read_text()) for f in range(3)]
                workrate = sum(x["background_episodes"] for x in files)*24/sum(x["test_rows"] for x in files)
                for fold, rec in enumerate(files):
                    policies.append(dict(cohort=cohort, fold=fold, arm=arm, **rec))
            for family, piece in [("all",table), *table.groupby("family")]:
                sums = piece[columns].sum().to_dict()
                controls.append(dict(cohort=cohort, arm=arm, family=family,
                                     background_episodes_per_day=workrate, **sums))
    control = pd.DataFrame(controls)
    keys = ["cohort","family"]
    for _, table in control.groupby("arm"):
        idx = table.set_index(keys).sort_index()
        ref = control[control.arm.eq("placement")].set_index(keys).sort_index()
        pd.testing.assert_frame_equal(idx[["events","live_during","live_hit"]],ref[["events","live_during","live_hit"]])
    control.to_csv(out / "practical_controls.csv",index=False)
    (out / "selected_controls.json").write_text(json.dumps(policies,indent=2)+"\n")
    for filename in ["pleia_policies.csv","pleia_transitions.csv"]:
        shutil.copyfile(work / filename, out / filename)
    traces = pd.read_csv(work / "pleia_events.csv.gz")
    wide = traces.pivot(index=["catalogue","start","duration"],columns="rule",values="state")
    assert wide.notna().all().all()
    wide.groupby(["duration","ridge_delay_0_fixed","ridge_delay_0_live"]).size().rename("count").to_csv(
        out / "pleia_paired.csv")


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("work",type=Path)
    parser.add_argument("out",type=Path)
    args=parser.parse_args()
    summarize(args.work,args.out)
