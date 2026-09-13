"""Validate a completed pilot and export its evidence; never start new model fits."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--wait-for-completion", action="store_true")
args = ap.parse_args()
base = Path(args.base)
run = base / "runs/pilot_v1_20260913"
validation = base / "validation"
protocol = Path("protocols/model_comparison_pilot_v1/frozen_protocol.json")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def hashes(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def logged(name, *command):
    subprocess.run([sys.executable, "-B", "scripts/log_pilot_command.py", "--log",
                    str(validation / f"{name}.log"), "--", sys.executable, "-B", *command],
                   check=True)


record_path = validation / "pilot_completion_resume.log.json"
deadline = time.monotonic() + 2700
while args.wait_for_completion and not record_path.exists():
    if time.monotonic() >= deadline:
        raise TimeoutError("Completion record still missing after 45 minutes; do not assume success")
    time.sleep(5)
assert read(record_path)["exit_status"] == 0
summary = read(run / "pilot_summary.json")
assert summary["status"] == "complete" and summary["point_cells"] == 9 and summary["interval_cells"] == 18

# Preserve preparation timings before the complete-run reuse check rewrites them.
snapshot = validation / "completed_launch_snapshot"
snapshot.mkdir(exist_ok=False)
for path in run.glob("preparation_h*.json"):
    shutil.copy2(path, snapshot / path.name)
initial = read(validation / "interrupted_launch_snapshot/interruption_record.json")
before = hashes(run / "units")
for path, expected in initial["unit_file_hashes"].items():
    assert hashlib.sha256((run / path).read_bytes()).hexdigest() == expected, path

# Verify all committed units before invoking resume, so no missing unit can fit.
manifest = read(run / "checkpoint_manifest.json")
keys = [f"h{h}_f0_s42_{m}" for h in [1, 3, 6]
        for m in ["persistence", "xgboost", "attention_lstm"]]
assert {p.name for p in (run / "units").iterdir() if p.is_dir()} == set(keys)
for key in keys:
    marker = read(run / "units" / key / "COMPLETE.json")
    assert marker["key"] == key and marker["spec_hash"] == manifest["spec_hash"]
    for name, expected in marker["hashes"].items():
        assert before[str(Path(key) / name)] == expected
logged("pilot_verification_resume", "-m", "src.model_comparison_pilot", "run",
       "--out", str(run), "--resume")
after = hashes(run / "units")
assert before == after
resume_log = (validation / "pilot_verification_resume.log").read_text(encoding="utf-8")
assert resume_log.count("RESUMED ") == 9 and "START " not in resume_log
(validation / "resume_integrity.json").write_text(json.dumps(dict(
    passed=True, original_completed_units_reused=5, original_unit_files_unchanged=len(initial["unit_file_hashes"]),
    verification_units_reused=9, refits=0, unchanged_unit_files=len(before),
    unit_file_hashes=after), indent=2) + "\n", encoding="utf-8")

logged("output_validation", "-m", "src.validate_model_comparison_pilot", "--run", str(run),
       "--protocol", str(protocol), "--out", str(validation / "output_validation.json"))
logged("bdg2_preparation", "-m", "src.model_comparison_pilot", "bdg2-memory",
       "--out", str(validation / "bdg2_preparation_memory.json"))
logged("summary_tables", "scripts/summarise_pilot.py", "--run", str(run), "--out", str(base / "tables"))
logged("comparison_figure", "-m", "src.pilot_figure", "--run", str(run), "--out", str(base / "figures"))
# Collect after all measured commands have their exit records.
subprocess.run([sys.executable, "-B", "scripts/collect_pilot_measurements.py", "--base", str(base),
                "--protocol", str(protocol)], check=True)
print("Completed: nine point cells, eighteen interval cells, checkpoint reuse, BDG2 memory and exports.", flush=True)
