"""Check replay counts against the frozen scorer and report achieved workloads."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
STRATA = ["fold", "catalogue", "building", "family", "severity", "method", "budget", "channel"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(count_file, runs, cohort):
    replay = pd.read_csv(count_file)
    assert replay.cohort.eq(cohort).all()
    registered = []
    workloads = []
    receipt = {"fold_receipts_sha256": {}}
    for fold in range(3):
        unit = runs / f"f{fold}_s42"
        receipt["fold_receipts_sha256"][unit.name] = digest(unit / "COMPLETE.json")
        events = pd.read_csv(unit / "events.csv.gz", usecols=(
            ["catalogue_seed" if key == "catalogue" else key for key in STRATA] + ["detected"]
        )).rename(columns={"catalogue_seed": "catalogue"})
        events = events[events.channel.isin(["numerical", "combined"]) & events.budget.gt(0)]
        baseline = events.groupby(STRATA).detected.agg(events="size", hits="sum")
        registered.append(baseline)
        workloads.append(pd.read_csv(unit / "workload.csv"))
    expected = pd.concat(registered).sort_index()
    reproduced = replay.set_index(STRATA)[["events", "hits"]].sort_index()
    pd.testing.assert_frame_equal(expected, reproduced, check_dtype=False)
    receipt.update(counts_sha256=digest(count_file), verified_strata=len(expected),
                   verified_event_policy_channel_rows=int(expected.events.sum()),
                   registered_hits_across_rows=int(expected.hits.sum()))
    operating = replay.groupby(["method", "budget", "channel"])[
        ["events", "hits", "during_change_span", "history_only"]].sum().reset_index()
    background = pd.concat(workloads).groupby(["method", "budget"])[
        ["background_episodes", "exposure_days"]].sum()
    background["test_background_episodes_per_meter_day"] = (
        background.background_episodes / background.exposure_days)
    operating = operating.merge(background.reset_index(), on=["method", "budget"], validate="many_to_one")
    operating["matched_recall"] = operating.hits / operating.events
    operating["first_during_recall"] = operating.during_change_span / operating.events
    return receipt, operating.assign(cohort=cohort)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ["pilot_counts", "pilot_runs", "replication_counts", "replication_runs", "out"]:
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    audit, comparisons = {}, []
    for label in ["pilot", "replication"]:
        audit[label], table = compare(getattr(args, label + "_counts"),
                                      getattr(args, label + "_runs"), label)
        comparisons.append(table)
    args.out.mkdir(parents=True, exist_ok=True)
    pd.concat(comparisons, ignore_index=True).to_csv(args.out / "policy_comparison.csv", index=False)
    (args.out / "validation.json").write_text(json.dumps(audit, indent=2) + "\n")
