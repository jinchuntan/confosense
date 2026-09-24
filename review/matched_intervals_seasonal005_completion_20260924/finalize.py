"""Wait for sequential science, then close only the authorized delivery scope."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from adapter import HERE, REPO, SMART, read
from aggregate import COORDINATOR, OUTPUT
from backup import PACKAGES
from src.intervals005_common import atomic

PYTHON = "C:/cfs_venv/Scripts/python.exe"
STATUS = REPO / "PROJECT_RECOVERY_STATUS.md"


def child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    current = [part for part in environment.get("PYTHONPATH", "").split(os.pathsep) if part]
    smart = str(SMART.resolve())
    environment["PYTHONPATH"] = os.pathsep.join(
        [smart, *[part for part in current if Path(part).resolve() != SMART.resolve()]]
    )
    return environment


def run(script: str) -> None:
    subprocess.run([PYTHON, "-B", str(HERE / script)], cwd=SMART,
                   env=child_environment(), check=True)


def wait_science() -> None:
    started = time.monotonic()
    while True:
        progress = read(COORDINATOR / "progress.json")
        if progress.get("status") == "blocked":
            raise ValueError(f"scientific coordinator stopped: {progress.get('failure')}")
        if progress.get("status") == "science_validated" and progress.get("completed_bundles") == 52 and not progress.get("active"):
            return
        if time.monotonic() - started > 72 * 3600:
            raise TimeoutError("sequential science did not complete within 72 hours")
        time.sleep(120)


def documents() -> None:
    analysis = read(OUTPUT / "analysis_validation.json")
    backup = read(PACKAGES / "external_backup_validation.json")
    if (not analysis["passed"] or analysis["total_method_cells"] != 1950 or
        analysis["unique_seasonal_computations"] != 27 or not backup["passed"] or
        backup["bundles"] != 52):
        raise ValueError("final analysis or backup gate failed")
    index = HERE / "EVIDENCE_INDEX.md"
    if index.exists():
        raise ValueError("evidence index already exists; preserve it")
    atomic(index, """# Bounded interval-method and seasonal completion evidence

The [scope and pre-fit gate](PREFIT_GATE.md) identify exactly 52 new bundles, 1,700 new method cells and 18 new unique seasonal computations. The [cumulative report](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/CUMULATIVE_REPORT.md) and [analysis validation](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/analysis_validation.json) cover all 1,950 cells and 27 unique seasonal computations without population inference.

[Native metrics](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/native_metrics.csv), [common-support metrics](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/common_metrics.csv), [shared-owner contrasts](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/shared_owner_contrasts.csv), [seasonal unique point and interval metrics](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/seasonal_unique_point_metrics.csv), and [background workload](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/background_workload_pooled.csv) retain exact results and availability context. Native/common views and seed aliases are not extra experiments.

The [durable coordinator](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_coordinator/progress.json) records each sequential run, scoped validation and zero-fit resume. The [external backup validation](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/external_backup_validation.json), [archive manifest](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/external_archive_manifest.csv), [file manifest](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/external_file_manifest.csv), and [170 exact forecasting-owner prerequisites](../../smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/forecasting_owner_prerequisites.csv) cover the new raw evidence and the verified forecasting-base lineage.

The [publication receipt](PUBLICATION_RECEIPT.json) pins the earlier substantive commit and names exactly six HTTPS-readback paths. It does not claim readback of every file or self-verification of the receipt. Full-study readiness remains false pending separate operational and robustness/contamination/recovery work.
""")
    changed = subprocess.check_output(["git", "diff", "--name-only", "--", "PROJECT_RECOVERY_STATUS.md"], cwd=REPO, text=True).strip()
    if changed:
        raise ValueError("top-level status has unrelated uncommitted changes")
    before = STATUS.read_text(encoding="utf-8")
    marker = "<!-- matched-intervals-seasonal005-completion-20260924: historical status follows -->"
    if marker in before:
        raise ValueError("top-level status already contains this completion")
    latest = """# Matched interval-method and seasonal completion validated

The bounded 52-bundle extension is complete: 1,700 new cells plus 250 preserved accepted cells cover all **1,950/1,950** declared interval-method cells. The three applicable datasets have **27/27 unique seasonal dataset/fold/horizon computations**, 18 new, with 135 point and 270 interval seed-alias rows. RICO seasonal remains inapplicable. Every new bundle passed scoped independent validation, exact operation-ledger reconciliation and an unchanged-artifact zero-fit resume. The scientific source digest stayed `a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f`.

The native/common evaluation views are separate views of the same cells. Fold/seed results are descriptive; overlapping observations and aliases do not support population intervals. Clean-stream workload is not labelled-event detection performance. Verified external backup packages preserve the new raw runs, protocols and exact forecasting-owner prerequisites; the published review branch has a scoped, commit-pinned HTTPS readback receipt.

Full-study readiness remains **false**. The separate operational grid and robustness, contamination and recovery obligations remain unresolved; no such runs were launched here.

[Cumulative report](smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/CUMULATIVE_REPORT.md), [evidence index](review/matched_intervals_seasonal005_completion_20260924/EVIDENCE_INDEX.md), [analysis validation](smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/analysis_validation.json), [external backup validation](smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/external_backup_validation.json).

"""
    atomic(STATUS, latest + marker + "\n\n" + before)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--import-check", action="store_true")
    args = parser.parse_args()
    if args.run == args.import_check:
        parser.error("choose exactly one of --run or --import-check")
    if args.import_check:
        import src
        print(json.dumps({"passed": Path(src.__file__).resolve().parent == (SMART / "src").resolve(),
                          "interpreter": sys.executable, "cwd": os.getcwd(),
                          "src_root": str(Path(src.__file__).resolve().parent)}, indent=2), flush=True)
        return
    wait_science()
    if OUTPUT.exists() or (PACKAGES / "external_backup_validation.json").exists():
        raise ValueError("post-science output already exists; preserve and investigate")
    run("aggregate.py")
    run("backup.py")
    documents()
    run("publish.py")
    print("SCOPED SCIENCE, ANALYSIS, EXTERNAL BACKUP AND PUBLICATION COMPLETE", flush=True)


if __name__ == "__main__":
    main()
