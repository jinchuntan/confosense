"""Aggregate the paired replay counts without treating injections as independent sites."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

COUNTS = ["events","hits","before_first_change","during_change_span","after_last_change",
          "after_slot","history_only","history_only_after_slot","history_only_no_cf_hit","post_existing_flag"]
BASE = ["cohort","method","budget","channel"]


def aggregate(data, dimensions):
    summary = data.groupby(BASE + dimensions)[COUNTS].sum().reset_index()
    summary["history_share_of_hits"] = summary.history_only / summary.hits.replace(0, np.nan)
    summary["history_share_of_events"] = summary.history_only / summary.events
    return summary


def summarize(pilot, replication, out):
    data = pd.concat([pd.read_csv(pilot), pd.read_csv(replication)], ignore_index=True)
    for label, table in data.groupby("cohort"):
        assert set(table.fold) == {0,1,2}, label
        assert set(table.catalogue) == {42,43,44,45,46}, label
        assert table.building.nunique() == 10, label
    assert len(set(data[data.cohort.eq("pilot")].site) & set(data[data.cohort.eq("replication")].site)) == 0
    assert (data.hits == data.before_first_change + data.during_change_span + data.after_last_change).all()
    assert (data.after_last_change == data.history_only + data.post_existing_flag).all()
    out.mkdir(parents=True, exist_ok=True)
    for name, dimensions in [("operating_points",[]), ("sites",["site"]), ("buildings",["building"]),
                             ("disturbances",["family","severity"]), ("periods",["fold"])]:
        aggregate(data, dimensions).to_csv(out / (name + ".csv"), index=False)
    primary = data.query("method == 'asymmetric_cqr' and budget == 0.5 and channel == 'numerical'").copy()
    summary = aggregate(primary, [])
    sites = aggregate(primary, ["site"])
    for i,row in summary.iterrows():
        group = sites[sites.cohort.eq(row.cohort)]
        summary.loc[i, "sites_with_history_only"] = group.history_only.gt(0).sum()
        summary.loc[i, "sites"] = len(group)
        summary.loc[i, "mean_site_history_share_of_hits"] = group.history_share_of_hits.mean()
        summary.loc[i, "min_site_history_share_of_hits"] = group.history_share_of_hits.min()
        summary.loc[i, "max_site_history_share_of_hits"] = group.history_share_of_hits.max()
    summary.to_csv(out / "primary.csv", index=False)
    primary["family_group"] = np.where(primary.family.isin(["random_missing","block_missing"]),
                                        "missing readings", "other five families")
    aggregate(primary, ["family_group"]).to_csv(out / "primary_families.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for key in ["pilot","replication","output"]:
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    summarize(args.pilot,args.replication,args.output)
