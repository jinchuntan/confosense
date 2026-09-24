"""Explicit-allowlist branch publication and commit-pinned HTTPS readback."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from adapter import HERE, REPO, SMART, bundle_paths, digest, frame, read
from aggregate import COORDINATOR, OUTPUT, new_receipts, verify_new
from backup import BACKUP, PACKAGES
from src.intervals005_common import atomic

BRANCH = "review/matched-intervals-seasonal005-completion-20260924"
BASE = "0c57f73618552514d41c6b78c631bd575beeebbc"
PARENT_BACKUP = Path("C:/Users/nigel/ConfoSenseBackups/matched_forecasting005_completion_20260923/FINAL_DELIVERY_BUNDLE.json")
REMOTE = "https://raw.githubusercontent.com/jinchuntan/confosense"
ANALYSIS_FILES = (
    "native_metrics.csv", "common_metrics.csv", "seasonal_point_metrics.csv",
    "seasonal_interval_metrics.csv", "seasonal_unique_point_metrics.csv",
    "seasonal_unique_interval_metrics.csv", "shared_owner_contrasts.csv",
    "background_workload_pooled.csv", "descriptive_common_summary.csv",
    "new_bundle_costs.csv",
    "common_support_descriptive.png", "figure_sources.json",
    "CUMULATIVE_REPORT.md", "analysis_validation.json",
)
VALIDATION_FILES = ("validation.json", "COMPLETE.json", "independent_metrics.csv", "alert_checks.csv")


def git(*args: str, raw: bool = False) -> str | bytes:
    result = subprocess.run(["git", *args], cwd=REPO, capture_output=True, check=True,
                            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    return result.stdout if raw else result.stdout.decode().strip()


def allowed_paths() -> list[str]:
    scope = frame(HERE / "remaining_scope.csv")
    if len(scope) != 52:
        raise ValueError("scope changed")
    paths = [
        "review/matched_intervals_seasonal005_completion_20260924/aggregate.py",
        "review/matched_intervals_seasonal005_completion_20260924/backup.py",
        "review/matched_intervals_seasonal005_completion_20260924/finalize.py",
        "review/matched_intervals_seasonal005_completion_20260924/publish.py",
        "review/matched_intervals_seasonal005_completion_20260924/EVIDENCE_INDEX.md",
        "PROJECT_RECOVERY_STATUS.md",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_coordinator/progress.json",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_coordinator/attempts.jsonl",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_supervisor/status.json",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_supervisor/events.jsonl",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/external_file_manifest.csv",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/external_archive_manifest.csv",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/forecasting_owner_prerequisites.csv",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/external_backup_validation.json",
    ]
    for name in ANALYSIS_FILES:
        paths.append(f"smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/{name}")
    for row in scope.itertuples(index=False):
        dataset, fold, seed = str(row.dataset), int(row.outer_fold), int(row.model_seed)
        name = f"{dataset}_f{fold}_s{seed}"
        design, output = bundle_paths(dataset, fold, seed)
        verify_new(dataset, fold, seed)
        if seed != 42 and fold < 2 and dataset != "rico":
            base = design.relative_to(REPO).as_posix()
            paths += [f"{base}/{field}" for field in
                      ("frozen_protocol.json", "readiness.json", "scope.csv", "method_specification.json")]
        runbase = output.relative_to(REPO).as_posix()
        paths += [f"{runbase}/COMPLETE.json", f"{runbase}/operations.jsonl"]
        validation, resume = new_receipts(name)
        valbase = validation.relative_to(REPO).as_posix()
        paths += [f"{valbase}/{field}" for field in VALIDATION_FILES]
        paths.append(resume.relative_to(REPO).as_posix())
    if len(paths) != len(set(paths)):
        raise ValueError("publication allowlist contains duplicate paths")
    for name in paths:
        if not (REPO / name).is_file():
            raise ValueError(f"allowed publication file missing: {name}")
    return paths


def staged_audit(expected: list[str]) -> dict:
    staged = git("diff", "--cached", "--name-only").splitlines()
    if set(staged) != set(expected) or len(staged) != len(expected):
        raise ValueError("staged paths differ from exact publication allowlist")
    sizes = {name: (REPO / name).stat().st_size for name in staged}
    bulk = {name: size for name, size in sizes.items()
            if size > (15 * 2**20 if name.endswith("/external_file_manifest.csv") else 5 * 2**20)}
    if bulk or sum(sizes.values()) > 80 * 2**20:
        raise ValueError("unexpected bulk staged file")
    git("diff", "--cached", "--check")
    return dict(count=len(staged), bytes=sum(sizes.values()), maximum_bytes=max(sizes.values()), paths=staged)


def bundle(commit: str, name: str) -> dict:
    previous = read(PARENT_BACKUP)
    if not previous["passed"] or previous["commit"] != BASE or not previous["external_only_restore_verified"]:
        raise ValueError("verified base prerequisite unavailable")
    destination = BACKUP / name
    if destination.exists():
        raise ValueError("publication backup destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    git("bundle", "create", str(destination), f"{BASE}..{commit}")
    if destination.stat().st_size >= 95 * 2**20:
        raise ValueError("publication bundle exceeds 95 MiB part limit")
    git("bundle", "verify", str(destination))
    return dict(path=str(destination), sha256=digest(destination), bytes=destination.stat().st_size,
                prerequisite_commit=BASE, prerequisite_bundle=previous["bundle"],
                prerequisite_bundle_sha256=previous["sha256"])


def readback(commit: str, paths: list[str]) -> list[dict]:
    rows = []
    for path in paths:
        expected = git("show", f"{commit}:{path}", raw=True)
        url = f"{REMOTE}/{commit}/{path}"
        request = urllib.request.Request(url, headers={"User-Agent": "ConfoSense-commit-pinned-readback"})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    if response.status != 200:
                        raise ValueError(f"HTTPS readback failed: {path}")
                    actual = response.read()
                break
            except urllib.error.HTTPError as exc:
                if exc.code != 404 or attempt == 4:
                    raise
                time.sleep(6)
        if actual != expected:
            raise ValueError(f"HTTPS readback bytes differ: {path}")
        rows.append(dict(path=path, url=url, bytes=len(actual), sha256=hashlib.sha256(actual).hexdigest()))
    return rows


def main() -> None:
    if git("branch", "--show-current") != BRANCH:
        raise ValueError("wrong branch")
    if git("diff", "--cached", "--name-only"):
        raise ValueError("index already staged; preserve unrelated work")
    if not read(OUTPUT / "analysis_validation.json")["passed"] or not read(PACKAGES / "external_backup_validation.json")["passed"]:
        raise ValueError("analysis or external backup incomplete")
    paths = allowed_paths()
    for start in range(0, len(paths), 40):
        git("add", "--", *paths[start:start+40])
    audit = staged_audit(paths)
    print(json.dumps({key: audit[key] for key in ("count", "bytes", "maximum_bytes")}), flush=True)
    substantive = git("commit", "-m", "Deliver validated matched interval and seasonal completion")
    substantive_sha = git("rev-parse", "HEAD")
    backing = bundle(substantive_sha, "publication_substantive_from_0c57f736.bundle")
    git("push", "origin", f"HEAD:refs/heads/{BRANCH}")
    scope = [
        "review/matched_intervals_seasonal005_completion_20260924/adapter.py",
        "review/matched_intervals_seasonal005_completion_20260924/AUTHORIZATION.json",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/CUMULATIVE_REPORT.md",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/analysis_validation.json",
        "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/external_backup_validation.json",
        "smart_building_conformal/outputs/matched_intervals005/bdg2_f0_s42_method_completion_v1/COMPLETE.json",
    ]
    remote = readback(substantive_sha, scope)
    receipt = HERE / "PUBLICATION_RECEIPT.json"
    if receipt.exists():
        raise ValueError("publication receipt already exists")
    atomic(receipt, dict(substantive_commit=substantive_sha, branch=BRANCH,
                         staged_count=audit["count"], staged_bytes=audit["bytes"],
                         staged_maximum_bytes=audit["maximum_bytes"],
                         external_substantive_bundle=backing,
                         readback_commit=substantive_sha, readback_scope=remote,
                         readback_scope_statement="These six exact paths only; not every published file or the receipt itself",
                         full_study_ready=False))
    git("add", "--", receipt.relative_to(REPO).as_posix())
    second = staged_audit([receipt.relative_to(REPO).as_posix()])
    print(json.dumps({key: second[key] for key in ("count", "bytes", "maximum_bytes")}), flush=True)
    git("commit", "-m", "Record commit-pinned scoped delivery readback")
    final_sha = git("rev-parse", "HEAD")
    final_bundle = bundle(final_sha, "publication_final_from_0c57f736.bundle")
    git("push", "origin", f"HEAD:refs/heads/{BRANCH}")
    print(json.dumps(dict(branch=BRANCH, substantive_commit=substantive_sha,
                          receipt_commit=final_sha, final_external_bundle=final_bundle,
                          readback_paths=len(remote)), indent=2), flush=True)


if __name__ == "__main__":
    main()
