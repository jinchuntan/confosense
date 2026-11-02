"""Select a site-disjoint cohort from early history and run the frozen pilot design."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "matched_workload_20261102"


def prepare(raw, work):
    base = json.loads((PILOT / "protocol.json").read_text())
    metadata = pd.read_csv(raw / "metadata.csv").set_index("building_id")
    excluded = set(metadata.loc[base["buildings"], "site_id"])
    meter = raw / "electricity.csv"
    times = pd.read_csv(meter, usecols=["timestamp"]).timestamp
    if not times.is_monotonic_increasing or not times.is_unique:
        raise ValueError("Expected unique chronological meter timestamps")
    early = pd.read_csv(meter, nrows=int(len(times) * .35))
    selected = {}
    for name in sorted(set(early.columns).intersection(metadata.index)):
        site = metadata.loc[name, "site_id"]
        if site in excluded or site in selected:
            continue
        series = early[name].replace([np.inf, -np.inf], np.nan)
        if series.notna().mean() < .95 or series.nunique() < 2:
            continue
        pairs = series.notna() & series.shift().notna()
        if series.eq(series.shift())[pairs].mean() <= .5:
            selected[site] = name
    cohort = sorted(selected.values())
    profile = dict(base, buildings=cohort, seeds=[42])
    # The original runner reads the protocol beside its source and hashes both.
    work.mkdir(parents=True, exist_ok=True)
    protocol = work / "protocol.json"
    content = json.dumps(profile, indent=2) + "\n"
    if protocol.exists() and protocol.read_text() != content:
        raise ValueError("Existing cohort protocol differs")
    protocol.write_text(content)
    shutil.copyfile(PILOT / "study.py", work / "study.py")
    membership = dict(buildings_by_site=selected, excluded_pilot_sites=sorted(excluded),
                      screening_rows=len(early), last_screened_timestamp=early.timestamp.iloc[-1])
    (work / "membership.json").write_text(json.dumps(membership, indent=2) + "\n")
    print(json.dumps(membership), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("work", type=Path)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    prepare(args.raw, args.work)
    if not args.prepare_only:
        subprocess.run([sys.executable, str(args.work / "study.py"), "--raw", str(args.raw),
                        "--out", str(args.work / "runs"), "--workers", "2"], check=True)
