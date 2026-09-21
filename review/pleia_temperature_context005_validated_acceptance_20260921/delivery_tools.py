"""Backup and GitHub readback for the validated-acceptance primary commit.

The ``backup`` action copies exact Git blobs, not CRLF-normalized working-tree
files.  The ``readback`` action downloads bytes over HTTPS from GitHub pinned
to the named *earlier* primary commit.  Its receipt deliberately makes no
claim to verify the later commit that contains that receipt.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = REPO / "smart_building_conformal" / "outputs" / "conditional_context005" / "pleia_f2_s42_C_v1_validated_acceptance_v1"
ENTRY = "e52a3ba6b94996f51300af523f898207162cac79"
MAIN = "06fe967be2be8d7898812c0c2d6e464d4e942351"
OWNER_REPO = "jinchuntan/confosense"
BACKUP_ROOT = Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_validated_acceptance_20260921")
PREFIXES = [
    "review/pleia_temperature_context005_validated_acceptance_20260921",
    "smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1",
]


def utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def git(*args: str, binary: bool = False) -> str | bytes:
    value = subprocess.check_output(["git", *args], cwd=REPO, text=not binary)
    return value if binary else value.strip()  # type: ignore[union-attr,return-value]


def blob(commit: str, path: str) -> bytes:
    return git("cat-file", "blob", f"{commit}:{path}", binary=True)  # type: ignore[return-value]


def paths_at(commit: str) -> list[str]:
    found = []
    for prefix in PREFIXES:
        raw = str(git("ls-tree", "-r", "--name-only", commit, "--", prefix))
        found.extend(p for p in raw.splitlines() if p)
    return sorted(set(found))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def backup(primary: str) -> int:
    if str(git("rev-parse", "HEAD")) != primary:
        raise SystemExit("backup must run while HEAD equals the named primary commit")
    paths = paths_at(primary)
    if not paths:
        raise SystemExit("primary commit does not contain acceptance paths")
    # V1/V2 preserved copied blobs but used revision spellings Git interpreted
    # as empty bundles.  Keep both intact and write the ref-based V3 bundle to
    # a distinct location.
    dest = BACKUP_ROOT / f"primary_{primary}_v3"
    if dest.exists():
        raise SystemExit("preserve existing backup; destination already exists: " + str(dest))
    dest.mkdir(parents=True)
    evidence = dest / "exact_committed_blobs"
    rows = []
    for path in paths:
        data = blob(primary, path)
        target = evidence / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        rows.append({"path": path, "bytes": len(data), "sha256": sha(data), "backup_path": str(target.relative_to(dest)).replace("\\", "/")})
    with (dest / "blob_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256", "backup_path"])
        writer.writeheader(); writer.writerows(rows)
    bundle = dest / f"acceptance_primary_{primary}.bundle"
    branch = "review/pleia-temperature-context005-validated-acceptance-20260921"
    create = subprocess.run(["git", "bundle", "create", str(bundle), branch, "^" + ENTRY], cwd=REPO, capture_output=True, text=True)
    verify = subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=REPO, capture_output=True, text=True) if create.returncode == 0 else None
    verified_rows = []
    for row in rows:
        backup_bytes = (dest / row["backup_path"]).read_bytes()
        expected = blob(primary, row["path"])
        verified_rows.append(bool(backup_bytes == expected and sha(backup_bytes) == row["sha256"]))
    receipt = {
        "purpose": "incremental backup of validated-acceptance primary commit",
        "utc": utc(), "primary_commit": primary, "base_commit_not_in_incremental_bundle": ENTRY,
        "backup_root": str(dest), "exact_blob_files": len(rows), "all_exact_blobs_verified": all(verified_rows),
        "bundle": {"path": str(bundle), "bytes": bundle.stat().st_size if bundle.exists() else None, "sha256": file_sha(bundle) if bundle.exists() else None,
                   "create_returncode": create.returncode, "verify_returncode": verify.returncode if verify else None,
                   "verify_stdout": verify.stdout if verify else None, "verify_stderr": verify.stderr if verify else create.stderr},
        "previous_full_backup": "C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_validation_audit_20260919/audit_v1_ec9bed70.bundle",
        "previous_full_backup_status": "verified by the audit receipt; this backup adds the exact primary acceptance commit blobs",
        "passed": bool(create.returncode == 0 and verify and verify.returncode == 0 and all(verified_rows)),
    }
    write_json(dest / "BACKUP_VERIFICATION.json", receipt)
    current = OUT / "BACKUP_VERIFICATION.json"
    if current.exists():
        failed = OUT / "BACKUP_VERIFICATION_FAILED_V1.json"
        if failed.exists():
            failed = OUT / "BACKUP_VERIFICATION_FAILED_V2.json"
        if not failed.exists():
            failed.write_bytes(current.read_bytes())
    write_json(current, receipt)
    print(json.dumps({k: receipt[k] for k in ["passed", "primary_commit", "exact_blob_files", "backup_root", "bundle"]}, indent=2))
    return 0 if receipt["passed"] else 1


def https(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "confosense-validated-acceptance"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return int(response.status), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()


def readback(primary: str) -> int:
    backup_receipt = json.loads((OUT / "BACKUP_VERIFICATION.json").read_text(encoding="utf-8"))
    api_status, api_bytes = https(f"https://api.github.com/repos/{OWNER_REPO}/commits/{primary}")
    api_sha = None
    if api_status == 200:
        api_sha = json.loads(api_bytes.decode("utf-8"))["sha"]
    targets = paths_at(primary)
    downloads = []
    for path in targets:
        status, downloaded = https(f"https://raw.githubusercontent.com/{OWNER_REPO}/{primary}/{path}")
        committed = blob(primary, path)
        downloads.append({"path": path, "http_status": status, "committed_blob_bytes": len(committed), "downloaded_bytes": len(downloaded),
                          "committed_blob_sha256": sha(committed), "downloaded_sha256": sha(downloaded), "identical": downloaded == committed})
    receipt = {
        "purpose": "settled GitHub HTTPS delivery receipt",
        "utc": utc(), "branch": "review/pleia-temperature-context005-validated-acceptance-20260921",
        "verified_primary_commit": primary, "primary_url": f"https://github.com/{OWNER_REPO}/tree/{primary}",
        "api_status": api_status, "api_commit_sha": api_sha, "api_matches_primary": api_sha == primary,
        "downloads": downloads, "all_downloads_identical_to_committed_blobs": all(x["identical"] for x in downloads),
        "backup": {"passed": backup_receipt["passed"], "backup_root": backup_receipt["backup_root"], "bundle": backup_receipt["bundle"]},
        "main_expected": MAIN, "main_actual_at_receipt": str(git("rev-parse", "main")),
        "passed": bool(api_sha == primary and all(x["identical"] for x in downloads) and backup_receipt["passed"] and str(git("rev-parse", "main")) == MAIN),
        "scope_note": "This receipt verifies the earlier primary commit named above, by direct HTTPS downloads compared to committed Git blobs. It does not claim to verify the later commit that contains this receipt.",
    }
    output = HERE / "VALIDATED_ACCEPTANCE_DELIVERY_RECEIPT.json"
    if output.exists():
        raise SystemExit("preserve existing delivery receipt: " + str(output))
    write_json(output, receipt)
    print(json.dumps({"passed": receipt["passed"], "primary": primary, "downloads": len(downloads), "backup": receipt["backup"]}, indent=2))
    return 0 if receipt["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["backup", "readback"])
    parser.add_argument("primary")
    args = parser.parse_args()
    return backup(args.primary) if args.action == "backup" else readback(args.primary)


if __name__ == "__main__":
    raise SystemExit(main())
