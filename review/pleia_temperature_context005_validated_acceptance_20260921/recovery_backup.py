"""Create scoped external recovery bundles and prove an isolated restore.

The restore action deliberately initializes a brand-new repository and fetches
only local bundle files.  It removes Git environment variables that could
otherwise point at this working repository; it neither accesses GitHub nor
borrows objects from the source repository while restoring.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BACKUP_ROOT = Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_validated_acceptance_20260921")
TEST_ROOT = Path("C:/Users/nigel/ConfoSenseRecoveryTests")
MAIN = "06fe967be2be8d7898812c0c2d6e464d4e942351"
BASE = "c143fa16eaf9bfc6354b4cb1f8861915cb00f388"
BASE_REF = "review/matched-fold2-multiseed-20260914"
AUDIT = "e52a3ba6b94996f51300af523f898207162cac79"
AUDIT_BASE = "ec9bed703db3d6bcb87a2acb7140d84a2a86c078"
PRIMARY = "affc006e64075558415d7fe038460ba560ee6dc6"
DELIVERY = "47595bfd7081f125e1f65a01971d5a82b2d2c40c"
FINAL = "18d8dd15d06459b3b54ba629e9948b78494f4c8f"
BRANCH = "review/pleia-temperature-context005-validated-acceptance-20260921"
EXISTING_PRIMARY_BUNDLE = BACKUP_ROOT / f"primary_{PRIMARY}_v3" / f"acceptance_primary_{PRIMARY}.bundle"
EXISTING_AUDIT_BUNDLE = Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_validation_audit_20260919/audit_v1_ec9bed70.bundle")
DEST = BACKUP_ROOT / "recovery_18d8_v6"
RECEIPT = HERE / "EXTERNAL_BACKUP_RECOVERY_RECEIPT.json"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(args: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, check=True, text=True, capture_output=True)


def clean_git_environment() -> dict[str, str]:
    env = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_OBJECT_DIRECTORY"):
        env.pop(name, None)
    return env


def bundle_metadata(path: Path) -> dict[str, object]:
    verified = run(["git", "bundle", "verify", str(path)], REPO)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path), "verify_stdout": verified.stdout, "verify_stderr": verified.stderr}


def create_bundle(path: Path, revisions: list[str]) -> dict[str, object]:
    run(["git", "bundle", "create", str(path), *revisions], REPO)
    return bundle_metadata(path)


def advertised_ref(path: Path, commit: str) -> str:
    lines = run(["git", "bundle", "list-heads", str(path)], REPO).stdout.splitlines()
    for line in lines:
        oid, ref = line.split(maxsplit=1)
        if oid == commit:
            return ref
    raise SystemExit(f"bundle does not advertise expected commit {commit}: {path}")


def main() -> int:
    if RECEIPT.exists():
        raise SystemExit(f"preserve existing recovery receipt: {RECEIPT}")
    if DEST.exists():
        raise SystemExit(f"preserve existing prerequisite backup: {DEST}")
    for required in (EXISTING_AUDIT_BUNDLE, EXISTING_PRIMARY_BUNDLE):
        if not required.exists():
            raise SystemExit(f"required external bundle is absent: {required}")
    DEST.mkdir(parents=True)
    base = DEST / "base_c143.bundle"
    audit = DEST / "audit_e52_from_ec9.bundle"
    delivery = DEST / "delivery_18_from_affc.bundle"
    bundles = {
        "base_c143": create_bundle(base, [BASE_REF]),
        "audit_full_existing": bundle_metadata(EXISTING_AUDIT_BUNDLE),
        "audit_receipt_delta": create_bundle(audit, [BRANCH.replace("validated-acceptance-20260921", "validation-audit-20260919"), "^" + AUDIT_BASE]),
        "primary_existing": bundle_metadata(EXISTING_PRIMARY_BUNDLE),
        "delivery_delta": create_bundle(delivery, [BRANCH, "^" + PRIMARY]),
    }

    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    restore = Path(tempfile.mkdtemp(prefix="acceptance_restore_", dir=TEST_ROOT))
    restore_env = clean_git_environment()
    run(["git", "init", "-q"], restore, env=restore_env)
    fetches = [
        (base, f"{advertised_ref(base, BASE)}:refs/heads/restored-base"),
        (EXISTING_AUDIT_BUNDLE, "refs/heads/review/pleia-temperature-context005-validation-audit-20260919:refs/heads/restored-audit-base"),
        (audit, "refs/heads/review/pleia-temperature-context005-validation-audit-20260919:refs/heads/restored-audit"),
        (EXISTING_PRIMARY_BUNDLE, f"refs/heads/{BRANCH}:refs/heads/restored-primary"),
        (delivery, f"refs/heads/{BRANCH}:refs/heads/restored-delivery"),
    ]
    fetch_outputs = []
    for source, refspec in fetches:
        fetched = run(["git", "fetch", "--no-tags", str(source), refspec], restore, env=restore_env)
        fetch_outputs.append({"source": str(source), "refspec": refspec, "stdout": fetched.stdout, "stderr": fetched.stderr})
    restored = run(["git", "rev-parse", "refs/heads/restored-delivery"], restore, env=restore_env).stdout.strip()
    required = [BASE, MAIN, AUDIT_BASE, AUDIT, PRIMARY, DELIVERY, FINAL]
    for commit in required:
        run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], restore, env=restore_env)
    fsck = run(["git", "fsck", "--full", "--no-dangling"], restore, env=restore_env)
    remotes = subprocess.run(["git", "config", "--get-regexp", r"^remote\."], cwd=restore, env=restore_env, text=True, capture_output=True)
    alternates = restore / ".git" / "objects" / "info" / "alternates"
    receipt = {
        "purpose": "external-backup-only recovery proof through validated-acceptance commit",
        "utc": utc(),
        "restored_commit": restored,
        "expected_restored_commit": FINAL,
        "restored_commit_matches_expected": restored == FINAL,
        "commits_present": required,
        "external_bundle_inputs": bundles,
        "isolated_repository": str(restore),
        "restore_method": "git init followed only by git fetch from the listed local external bundle paths",
        "network_or_working_repository_objects_used_during_restore": False,
        "remote_configuration_absent": remotes.returncode != 0 and not remotes.stdout.strip(),
        "object_alternates_absent": not alternates.exists(),
        "fsck_stdout": fsck.stdout,
        "fsck_stderr": fsck.stderr,
        "fetches": fetch_outputs,
        "superseded_incomplete_preflights": [str(BACKUP_ROOT / f"recovery_prerequisites_through_{FINAL}_v1"), str(BACKUP_ROOT / f"recovery_prerequisites_through_{FINAL}_v2"), str(BACKUP_ROOT / f"recovery_prerequisites_through_{FINAL}_v3"), str(BACKUP_ROOT / "recovery_18d8_v4"), str(BACKUP_ROOT / "recovery_18d8_v5")],
        "scope_note": "The new self-contained c143 base, existing full audit archive, and new audit-receipt and delivery deltas are the minimum lineage prerequisites for the pre-existing primary incremental bundle. This proof restores commits through 18d8dd15d only; it makes no claim about later commits containing this receipt.",
        "passed": restored == FINAL and remotes.returncode != 0 and not alternates.exists(),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("passed", "restored_commit", "isolated_repository")}, indent=2))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
