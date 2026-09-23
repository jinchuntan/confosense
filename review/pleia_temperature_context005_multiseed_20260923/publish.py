"""Explicitly stage and commit the bounded substantive delivery."""
from __future__ import annotations

import csv as csv_module
import hashlib
import json
import subprocess

from common import *


def main():
    if git("branch", "--show-current") != BRANCH or git("rev-parse", "main") != MAIN:
        raise ValueError("branch/main preservation failure")
    baseline = read(REVIEW / "PRESERVATION_BASELINE.json")
    if source_digest() != SOURCE_HASH or digest(SEED42_RUN / "COMPLETE.json") != baseline["seed42_complete_sha256"]:
        raise ValueError("source or accepted seed 42 changed")
    aggregate = read(ANALYSIS / "validation.json"); independent = read(ANALYSIS / "independent_validation.json")
    packages = read(REVIEW / "RAW_PACKAGE_VALIDATION.json"); completion = read(REVIEW / "BATCH_COMPLETION_RECORD.json")
    if not all(row["passed"] for row in (aggregate, independent, packages, completion)):
        raise ValueError("completion evidence is not ready")
    for seed in SEEDS:
        if not read(acceptance(seed))["passed"] or not read(publication(seed) / "validation.json")["passed"]:
            raise ValueError(f"seed {seed} evidence incomplete")
    verification = {"passed": True, "utc": now(), "branch": BRANCH, "main": MAIN,
                    "source_hash": source_digest(), "completed_new_seeds": list(SEEDS),
                    "accepted_all_seeds": list(ALL_SEEDS), "seed42_reused_without_rerun": True,
                    "full_validation_all_new_seeds": True, "completed_resume_zero_fit_all_new_seeds": True,
                    "independent_aggregate_validation": True, "raw_packages_verified": True,
                    "scientific_source_changed": False, "historical_heads_rewritten": False}
    atomic(REVIEW / "COMPLETION_VERIFICATION.json", verification)
    roots = [REVIEW, BATCH, ANALYSIS]
    for seed in SEEDS:
        roots += [manifest(seed), design(seed), publication(seed)]
    files = {path for root in roots for path in (root.rglob("*") if root.is_dir() else [root]) if path.is_file()}
    for seed in SEEDS:
        files |= {run(seed) / "COMPLETE.json", run(seed) / "operations.jsonl"}
        for stage in ("owner_fit_cqr", "owner_cal_cqr", "controls", "tables"):
            files |= {path for path in (run(seed) / "stages" / stage).rglob("*") if path.is_file()}
    files = sorted(path for path in files if "__pycache__" not in path.parts and path.suffix not in (".pyc", ".tmp")
                   and path.name != "EVIDENCE_MANIFEST.csv")
    rels = [path.relative_to(REPO).as_posix() for path in files]
    pathfile = BACKUP / "substantive_paths.txt"; BACKUP.mkdir(parents=True, exist_ok=True)
    atomic(pathfile, "\n".join(rels) + "\n")
    subprocess.run(["git", "add", "-f", "--pathspec-from-file=" + str(pathfile)], cwd=REPO, check=True)
    rows = []
    for relative in rels:
        blob = subprocess.check_output(["git", "show", ":" + relative], cwd=REPO)
        if len(blob) >= 100 * 2**20:
            raise ValueError("blob exceeds GitHub limit: " + relative)
        rows.append({"path": relative, "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()})
    evidence = REVIEW / "EVIDENCE_MANIFEST.csv"
    with evidence.open("w", encoding="utf-8", newline="") as handle:
        writer = csv_module.DictWriter(handle, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader(); writer.writerows(rows)
    subprocess.run(["git", "add", "--", str(evidence.relative_to(REPO))], cwd=REPO, check=True)
    subprocess.run(["git", "diff", "--cached", "--check"], cwd=REPO, check=True)
    staged = set(git("diff", "--cached", "--name-only").splitlines())
    expected_staged = set()
    for relative in rels:
        index_blob = git("rev-parse", ":" + relative)
        head_blob = subprocess.run(
            ["git", "rev-parse", "HEAD:" + relative], cwd=REPO, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        if head_blob.returncode or head_blob.stdout.strip() != index_blob:
            expected_staged.add(relative)
    if staged != expected_staged | {evidence.relative_to(REPO).as_posix()}:
        raise ValueError("explicit substantive staging scope mismatch")
    subprocess.run(["git", "commit", "-m", "Publish PLEIA-temperature five-seed evidence"], cwd=REPO, check=True)
    print(json.dumps({"committed": True, "commit": git("rev-parse", "HEAD"),
                      "evidence_files": len(rows), "evidence_bytes": sum(row["bytes"] for row in rows)}, indent=2))


if __name__ == "__main__":
    main()
