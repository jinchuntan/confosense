"""Export recorded preparation and command measurements without fitting models."""
import argparse
import json
from pathlib import Path

import pandas as pd


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--protocol", required=True)
args = ap.parse_args()
base = Path(args.base)
validation = base / "validation"
out = base / "tables"
out.mkdir(parents=True, exist_ok=True)
protocol_path = Path(args.protocol)
protocol = read(protocol_path)

preparation = [dict(dataset="pleia", launch="protocol_freeze", phase="complete_preparation",
                    source=str(protocol_path), **protocol["preparation_resources"])]
for launch, folder in [
    ("interrupted_initial_launch", validation / "interrupted_launch_snapshot"),
    ("completion_launch", validation / "completed_launch_snapshot"),
    ("verification_resume", base / "runs/pilot_v1_20260913"),
]:
    for path in sorted(folder.glob("preparation_h*.json")):
        preparation.append(dict(dataset="pleia", launch=launch,
                                phase="features_sequences_and_role_validation",
                                horizon=int(path.stem.split("_h")[1]),
                                source=str(path), **read(path)))
pd.DataFrame(preparation).to_csv(out / "pleia_preparation_memory.csv", index=False)

bdg_path = validation / "bdg2_preparation_memory.json"
bdg = read(bdg_path)
assert bdg["models_fitted"] == 0
bdg_rows = [dict(dataset="bdg2", phase=phase, models_fitted=0,
                 source=str(bdg_path), **bdg[key])
            for phase, key in [("adapter", "adapter_resources"), ("total", "total_resources")]]
for row in bdg["horizons"]:
    bdg_rows.append(dict(dataset="bdg2", phase="features_sequences_and_full_batch_traversal",
                         source=str(bdg_path), **{k: v for k, v in row.items() if k != "resources"},
                         **row["resources"]))
pd.DataFrame(bdg_rows).to_csv(out / "bdg2_preparation_memory.csv", index=False)

commands = []
for path in sorted(validation.glob("*.log.json")):
    record = read(path)
    commands.append(dict(log=path.name.removesuffix(".json"), status="exited",
                         command=json.dumps(record.pop("command")), **record))
interruption_path = validation / "interrupted_launch_snapshot/interruption_record.json"
interruption = read(interruption_path)
commands.append(dict(log="pilot_run_v1.log", status=interruption["status"],
                     exit_status=None, seconds=None,
                     observation_utc=interruption["observed_utc"],
                     note="Original launch ended without a recorded exit code or duration; completed checkpoints reused."))
pd.DataFrame(commands).to_csv(out / "execution_measurements.csv", index=False)

print(json.dumps(dict(preparation_rows=len(preparation), bdg2_rows=len(bdg_rows),
                      command_rows=len(commands), models_fitted=0, output=str(out)), indent=2))
