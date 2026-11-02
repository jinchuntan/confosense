"""Materialize the pinned manuscript inputs from this repository's git history."""

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBMISSION = "2db2ac6a1cd708c100e1a3da7ac8ff454d54945e"
EXTENSION = "55e74b51eeea917ebbec9a213d7054b968f53a8b"
ORIGINAL = "d65147ff22e6c079603eda1337630254796c8990"
PROJ = "smart_building_conformal"


def prepare(directory):
    files = {}
    for fold, version in [(1, 1), (2, 2)]:
        unit = f"bdg2_h1_f{fold}_s42"
        base = f"{PROJ}/outputs/matched_forecasting005/{unit}_v{version}/units/{unit}_xgboost"
        for name in [
            "model.ubj",
            "COMPLETE.json",
            "predictions.csv.gz",
            "fitting_membership.csv.gz",
            "payload.json",
        ]:
            files[f"f{fold}/{name}"] = (SUBMISSION, f"{base}/{name}")
    base = f"{PROJ}/outputs/matched_intervals005/bdg2_f2_s42_v1/stages"
    for name in ["owner.pkl", "COMPLETE.json"]:
        files[f"cqr/{name}"] = (SUBMISSION, f"{base}/owner_cal_h1_cqr_l95/{name}")
    files["cqr/common.csv.gz"] = (SUBMISSION, f"{base}/dscp_joint/test_h1.csv.gz")
    files["f0/protocol.json"] = (
        SUBMISSION,
        f"{PROJ}/protocols/matched_forecasting005/bdg2_h1_f0_s42_v1_core_completion_v1/frozen_protocol.json",
    )
    for name in ["point_summary.csv", "interval_quality.csv"]:
        files[f"f0/{name}"] = (
            SUBMISSION,
            f"{PROJ}/outputs/matched_forecasting005/bdg2_h1_f0_s42_v1/{name}",
        )
    files["source/combined_candidate_summary.csv"] = (
        EXTENSION,
        "review/operational005_high_coverage_extension_20261003/results/combined_candidate_summary.csv",
    )
    files["source/op_metrics.csv"] = (
        ORIGINAL,
        f"{PROJ}/outputs/operational005_causal_replay_v2/analysis_v1/operational_metrics.csv",
    )
    for local, (commit, path) in files.items():
        target = directory / local
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(
            subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    prepare(parser.parse_args().directory)
