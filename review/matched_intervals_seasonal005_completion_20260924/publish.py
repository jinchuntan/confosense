"""Explicit-allowlist branch publication and commit-pinned HTTPS readback."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import msvcrt
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
BRANCH_REF = f"refs/heads/{BRANCH}"
EXTERNAL_RECOVERY_REPO = Path(
    "C:/Users/nigel/AppData/Local/Temp/confosense-external-recovery-be8487668e82"
)
SUPERVISOR_STATUS = SMART / "outputs/matched_intervals005/completion_52_v1_supervisor/status.json"
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


def staged_publication_delta(allowed: list[str]) -> list[str]:
    """Return the exact staged delta while accepting clean files in ancestry."""
    staged = git("diff", "--cached", "--name-only").splitlines()
    if not staged or not set(staged).issubset(set(allowed)):
        raise ValueError("staged paths are empty or exceed the publication allowlist")
    for path in set(allowed) - set(staged):
        git("ls-files", "--error-unmatch", "--", path)
        clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", path], cwd=REPO)
        if clean.returncode != 0:
            raise ValueError(f"allowed path was not staged or clean in ancestry: {path}")
    return staged


def checked_git(args: list[str], cwd: Path = REPO) -> subprocess.CompletedProcess:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if result.returncode:
        raise RuntimeError(json.dumps({
            "argv": ["git", *args], "cwd": str(cwd), "exit_code": result.returncode,
            "stdout": result.stdout.decode(errors="replace"),
            "stderr": result.stderr.decode(errors="replace"),
        }, indent=2))
    return result


def bundle(commit: str, name: str, positive_ref: str) -> dict:
    previous = read(PARENT_BACKUP)
    if not previous["passed"] or previous["commit"] != BASE or not previous["external_only_restore_verified"]:
        raise ValueError("verified base prerequisite unavailable")
    if git("rev-parse", positive_ref) != commit:
        raise ValueError(f"named positive ref does not pin intended commit: {positive_ref}")
    selection = [positive_ref, f"^{BASE}"]
    count = int(git("rev-list", "--count", *selection))
    if count < 1:
        raise ValueError("publication bundle revision set is empty")
    destination = BACKUP / name
    if destination.exists():
        raise ValueError("publication backup destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    argv = ["bundle", "create", str(destination), *selection]
    checked_git(argv)
    if destination.stat().st_size >= 95 * 2**20:
        raise ValueError("publication bundle exceeds 95 MiB part limit")
    heads = checked_git(["bundle", "list-heads", str(destination)]).stdout.decode().splitlines()
    if heads != [f"{commit} {positive_ref}"]:
        raise ValueError(f"bundle advertised unexpected heads: {heads}")
    verified = checked_git(["bundle", "verify", str(destination)])
    return dict(path=str(destination), sha256=digest(destination), bytes=destination.stat().st_size,
                prerequisite_commit=BASE, prerequisite_bundle=previous["bundle"],
                prerequisite_bundle_sha256=previous["sha256"], positive_ref=positive_ref,
                selected_commit=commit, selected_commit_count=count,
                create_argv=["git", *argv], advertised_heads=heads,
                verify_output=(verified.stdout + verified.stderr).decode(errors="replace").strip())


def external_restore(bundle_record: dict, commit: str, label: str) -> dict:
    repo = EXTERNAL_RECOVERY_REPO
    if not (repo / ".git").is_dir():
        raise ValueError("established external-only recovery repository is unavailable")
    alternates = repo / ".git/objects/info/alternates"
    if alternates.exists() or checked_git(["remote"], repo).stdout.strip():
        raise ValueError("recovery repository has alternates or remotes")
    checked_git(["cat-file", "-e", f"{BASE}^{{commit}}"], repo)
    verification = checked_git(["bundle", "verify", bundle_record["path"]], repo)
    restored_ref = f"refs/heads/interval-publication-{label}-{commit[:12]}"
    existing = checked_git(["show-ref", "--verify", "--hash", restored_ref], repo) \
        if subprocess.run(["git", "show-ref", "--verify", "--quiet", restored_ref], cwd=repo).returncode == 0 else None
    if existing is not None:
        if existing.stdout.decode().strip() != commit:
            raise ValueError("existing recovery ref points to a different commit")
    else:
        checked_git(["fetch", "--no-tags", bundle_record["path"],
                     f"{bundle_record['positive_ref']}:{restored_ref}"], repo)
    restored_commit = checked_git(["rev-parse", restored_ref], repo).stdout.decode().strip()
    if restored_commit != commit:
        raise ValueError("external bundle recovery restored the wrong commit")
    restored_tree = checked_git(["rev-parse", f"{commit}^{{tree}}"], repo).stdout.decode().strip()
    expected_tree = git("rev-parse", f"{commit}^{{tree}}")
    if restored_tree != expected_tree:
        raise ValueError("external recovery tree differs")
    return {
        "passed": True, "repository": str(repo), "alternates": False, "remotes": [],
        "prerequisite_commit": BASE, "bundle": bundle_record["path"],
        "bundle_sha256": bundle_record["sha256"], "restored_ref": restored_ref,
        "restored_commit": restored_commit, "restored_tree": restored_tree,
        "verify_output": (verification.stdout + verification.stderr).decode(errors="replace").strip(),
    }


def remote_head() -> str | None:
    output = git("ls-remote", "--heads", "origin", BRANCH_REF)
    if not output:
        return None
    rows = output.splitlines()
    if len(rows) != 1 or rows[0].split()[1] != BRANCH_REF:
        raise ValueError("unexpected remote branch query result")
    return rows[0].split()[0]


def push_without_overwrite(commit: str, expected_remote: str | None) -> dict:
    before = remote_head()
    if before != expected_remote:
        raise ValueError(f"unexpected remote divergence: {before} != {expected_remote}")
    if git("rev-parse", BRANCH_REF) != commit:
        raise ValueError("local review branch does not point to intended push commit")
    checked_git(["push", "origin", f"{BRANCH_REF}:{BRANCH_REF}"])
    after = remote_head()
    if after != commit:
        raise ValueError("remote review branch did not reach intended commit")
    return {"ref": BRANCH_REF, "before": before, "after": after, "forced": False}


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def await_supervisor_receipt_window() -> dict:
    """Start the short receipt-commit window just after a live heartbeat."""
    deadline = time.monotonic() + 150
    while True:
        status = read(SUPERVISOR_STATUS)
        checked = datetime.fromisoformat(status["checked_utc"])
        age = (datetime.now(timezone.utc) - checked).total_seconds()
        if status.get("state") != "blocked_needs_attention":
            raise ValueError("supervisor left the expected publication-blocked state")
        if 0 <= age <= 20:
            return {"checked_utc": status["checked_utc"], "age_seconds": age,
                    "pid": status["processes"]["supervisor"]["pid"]}
        if time.monotonic() >= deadline:
            raise TimeoutError("no fresh supervisor heartbeat for guarded receipt commit")
        time.sleep(2)


def recovery_lock():
    path = BACKUP / "publication_recovery.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    try:
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        handle.close()
        raise RuntimeError("another publication recovery holds the lock") from exc
    return handle


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


READBACK_SCOPE = [
    "review/matched_intervals_seasonal005_completion_20260924/adapter.py",
    "review/matched_intervals_seasonal005_completion_20260924/AUTHORIZATION.json",
    "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/CUMULATIVE_REPORT.md",
    "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/analysis_validation.json",
    "smart_building_conformal/outputs/matched_intervals005/completion_52_v1_packages/external_backup_validation.json",
    "smart_building_conformal/outputs/matched_intervals005/bdg2_f0_s42_method_completion_v1/COMPLETE.json",
]


def recover_publication(substantive: str) -> None:
    lock = recovery_lock()
    try:
        if git("branch", "--show-current") != BRANCH or git("symbolic-ref", "HEAD") != BRANCH_REF:
            raise ValueError("wrong review branch")
        if git("rev-parse", "HEAD") != substantive or git("rev-parse", BRANCH_REF) != substantive:
            raise ValueError("review branch no longer pins the intended substantive commit")
        if git("diff", "--cached", "--name-only"):
            raise ValueError("index already staged; preserve unrelated work")
        progress = read(COORDINATOR / "progress.json")
        analysis = read(OUTPUT / "analysis_validation.json")
        backup = read(PACKAGES / "external_backup_validation.json")
        if (progress.get("status") != "science_validated" or progress.get("completed_bundles") != 52
                or not analysis.get("passed") or analysis.get("total_method_cells") != 1950
                or analysis.get("unique_seasonal_computations") != 27
                or not backup.get("passed") or backup.get("bundles") != 52):
            raise ValueError("existing science/analysis/raw-backup gates are incomplete")
        if (HERE / "PUBLICATION_RECEIPT.json").exists():
            raise ValueError("publication receipt already exists")
        if remote_head() not in (None, substantive):
            raise ValueError("unexpected remote review-branch divergence")

        failed_log = BACKUP / "supervisor_finalizer.stderr.log"
        failed_argv = [
            "git", "bundle", "create",
            str(BACKUP / "publication_substantive_from_0c57f736.bundle"),
            f"{BASE}..{substantive}",
        ]
        substantive_bundle = bundle(
            substantive, "publication_substantive_recovery_v1_from_0c57f736.bundle", BRANCH_REF)
        substantive_restore = external_restore(substantive_bundle, substantive, "substantive")
        first_push = push_without_overwrite(substantive, remote_head())
        remote = readback(substantive, READBACK_SCOPE)
        receipt_window = await_supervisor_receipt_window()

        recovery_path = HERE / "PUBLICATION_RECOVERY_V1.json"
        receipt = HERE / "PUBLICATION_RECEIPT.json"
        if recovery_path.exists():
            raise ValueError("publication recovery record already exists")
        recovery_record = {
            "passed": True,
            "version": "matched_intervals_seasonal005_publication_recovery_v1",
            "utc": utc(),
            "scope": "publication-only; no experiment, validation, aggregation, raw package, or raw backup repeated",
            "established_failure": "raw object IDs supplied no named positive ref; Git returned 'fatal: Refusing to create empty bundle.'",
            "failed_finisher_log": str(failed_log),
            "failed_finisher_log_sha256": digest(failed_log),
            "failed_bundle_argv": failed_argv,
            "failed_bundle_exit_code": 128,
            "substantive_commit": substantive,
            "substantive_commit_subject": git("show", "-s", "--format=%s", substantive),
            "named_positive_ref": BRANCH_REF,
            "selected_commit_count": substantive_bundle["selected_commit_count"],
            "analysis_receipt_sha256": digest(OUTPUT / "analysis_validation.json"),
            "raw_backup_receipt_sha256": digest(PACKAGES / "external_backup_validation.json"),
            "corrected_substantive_bundle": substantive_bundle,
            "external_only_substantive_restore": substantive_restore,
            "initial_push": first_push,
            "https_readback_scope": remote,
            "https_readback_scope_statement": "These six exact substantive-commit paths only",
            "supervisor_receipt_commit_window": receipt_window,
            "full_study_ready": False,
        }
        atomic(recovery_path, recovery_record)
        atomic(receipt, {
            "substantive_commit": substantive,
            "branch": BRANCH,
            "publication_recovery": recovery_path.relative_to(REPO).as_posix(),
            "external_substantive_bundle": substantive_bundle,
            "external_only_substantive_restore": substantive_restore,
            "readback_commit": substantive,
            "readback_scope": remote,
            "readback_scope_statement": "These six exact paths only; not every published file or the receipt itself",
            "failed_attempt_preserved": {"path": str(failed_log), "sha256": digest(failed_log)},
            "full_study_ready": False,
        })

        staged_paths = [
            "review/matched_intervals_seasonal005_completion_20260924/publish.py",
            recovery_path.relative_to(REPO).as_posix(),
            receipt.relative_to(REPO).as_posix(),
        ]
        git("add", "--", *staged_paths)
        audit = staged_audit(staged_paths)
        print(json.dumps({key: audit[key] for key in ("count", "bytes", "maximum_bytes")}), flush=True)
        git("commit", "-m", "Recover interval completion publication backup")
        final_commit = git("rev-parse", "HEAD")
        receipt_payload = read(receipt)
        receipt.unlink()

        final_bundle = bundle(
            final_commit, "publication_final_recovery_v1_from_0c57f736.bundle", BRANCH_REF)
        final_restore = external_restore(final_bundle, final_commit, "final")
        final_push = push_without_overwrite(final_commit, substantive)
        atomic(receipt, receipt_payload)
        final_record = {
            "passed": True,
            "utc": utc(),
            "branch": BRANCH,
            "substantive_commit": substantive,
            "containing_receipt_commit": final_commit,
            "substantive_bundle": substantive_bundle,
            "final_bundle": final_bundle,
            "substantive_restore": substantive_restore,
            "final_restore": final_restore,
            "substantive_push": first_push,
            "final_push": final_push,
            "https_readback_commit": substantive,
            "https_readback_scope": remote,
        }
        atomic(BACKUP / "FINAL_DELIVERY_RECOVERY_V1.json", final_record)
        print(json.dumps(final_record, indent=2), flush=True)
    finally:
        lock.close()


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
    audit = staged_audit(staged_publication_delta(paths))
    print(json.dumps({key: audit[key] for key in ("count", "bytes", "maximum_bytes")}), flush=True)
    substantive = git("commit", "-m", "Deliver validated matched interval and seasonal completion")
    substantive_sha = git("rev-parse", "HEAD")
    backing = bundle(substantive_sha, "publication_substantive_from_0c57f736.bundle", BRANCH_REF)
    git("push", "origin", f"HEAD:refs/heads/{BRANCH}")
    remote = readback(substantive_sha, READBACK_SCOPE)
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
    receipt_payload = read(receipt)
    git("add", "--", receipt.relative_to(REPO).as_posix())
    second = staged_audit([receipt.relative_to(REPO).as_posix()])
    print(json.dumps({key: second[key] for key in ("count", "bytes", "maximum_bytes")}), flush=True)
    git("commit", "-m", "Record commit-pinned scoped delivery readback")
    final_sha = git("rev-parse", "HEAD")
    # The live supervisor treats this working-tree path as the delivery marker.
    # Keep it absent between the receipt commit and successful final bundle/push
    # so a partial final publication cannot be reported as delivered.
    receipt.unlink()
    final_bundle = bundle(final_sha, "publication_final_from_0c57f736.bundle", BRANCH_REF)
    git("push", "origin", f"HEAD:refs/heads/{BRANCH}")
    atomic(receipt, receipt_payload)
    print(json.dumps(dict(branch=BRANCH, substantive_commit=substantive_sha,
                          receipt_commit=final_sha, final_external_bundle=final_bundle,
                          readback_paths=len(remote)), indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--recover-substantive")
    args = parser.parse_args()
    if args.recover_substantive:
        recover_publication(args.recover_substantive)
    else:
        main()
