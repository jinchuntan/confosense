"""Scoped backup and commit-pinned HTTPS readback for the preflight commit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from common import BACKUP, BRANCH, REPO, REVIEW, utc


OWNER_REPO = "jinchuntan/confosense"
LINEAGE = "03ca62f2f0704725a13b93929b5ba5797f06e20f"
LINEAGE_BUNDLE = Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_validated_acceptance_20260921/followup_03ca62f2f0704725a13b93929b5ba5797f06e20f_v1/followup_03ca62f2f0704725a13b93929b5ba5797f06e20f.bundle")
PREFIX = "review/pleia_temperature_context005_seeds43_46_preflight_20260922/"


def git(*args: str, binary: bool = False) -> str | bytes:
    value = subprocess.check_output(["git", *args], cwd=REPO, text=not binary)
    return value if binary else value.strip()  # type: ignore[union-attr,return-value]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def changed_paths(commit: str) -> list[str]:
    paths = str(git("diff-tree", "--no-commit-id", "--name-only", "-r", commit)).splitlines()
    if not paths or any(not path.startswith(PREFIX) for path in paths):
        raise SystemExit("primary commit is not confined to the preflight review directory")
    return paths


def write_json(path: Path, value: object) -> None:
    if path.exists():
        raise SystemExit(f"preserve existing delivery receipt: {path}")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def backup(commit: str) -> int:
    if str(git("rev-parse", "HEAD")) != commit:
        raise SystemExit("backup must run while HEAD is the named substantive commit")
    if not LINEAGE_BUNDLE.is_file():
        raise SystemExit(f"verified lineage bundle missing: {LINEAGE_BUNDLE}")
    destination = BACKUP / f"primary_{commit}_v1"
    if destination.exists():
        raise SystemExit(f"preserve existing backup: {destination}")
    destination.mkdir(parents=True)
    rows = []
    for path in changed_paths(commit):
        data = git("cat-file", "blob", f"{commit}:{path}", binary=True)  # type: ignore[assignment]
        target = destination / "exact_committed_blobs" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        rows.append({"path": path, "bytes": len(data), "sha256": sha(data), "backup_path": target.relative_to(destination).as_posix()})
    with (destination / "blob_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    bundle = destination / f"preflight_{commit}.bundle"
    made = subprocess.run(["git", "bundle", "create", str(bundle), BRANCH, "^" + LINEAGE], cwd=REPO, capture_output=True, text=True)
    checked = subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=REPO, capture_output=True, text=True) if made.returncode == 0 else None
    exact = all((destination / row["backup_path"]).read_bytes() == git("cat-file", "blob", f"{commit}:{row['path']}", binary=True) for row in rows)
    receipt = {
        "purpose": "scoped external backup of substantive temperature preflight commit",
        "utc": utc(), "verified_commit": commit, "changed_paths": rows, "all_exact_blobs_verified": exact,
        "backup_root": str(destination), "lineage_prerequisite_commit": LINEAGE,
        "verified_existing_lineage_bundle": {"path": str(LINEAGE_BUNDLE), "bytes": LINEAGE_BUNDLE.stat().st_size, "sha256": sha(LINEAGE_BUNDLE.read_bytes())},
        "bundle": {"path": str(bundle), "bytes": bundle.stat().st_size if bundle.exists() else None, "sha256": sha(bundle.read_bytes()) if bundle.exists() else None,
                   "create_returncode": made.returncode, "verify_returncode": checked.returncode if checked else None, "verify_stdout": checked.stdout if checked else None, "verify_stderr": checked.stderr if checked else made.stderr},
        "scope_note": "Exact blobs cover the 44 files introduced by the named substantive preflight commit. The small bundle contains commits after the already-backed 03ca62f2f lineage prerequisite; it does not duplicate historical multi-gigabyte archives or verify a later receipt-containing commit.",
    }
    receipt["passed"] = bool(exact and made.returncode == 0 and checked and checked.returncode == 0)
    write_json(REVIEW / "PREFLIGHT_BACKUP_VERIFICATION.json", receipt)
    print(json.dumps({"passed": receipt["passed"], "commit": commit, "paths": len(rows), "bundle": receipt["bundle"]}, indent=2))
    return 0 if receipt["passed"] else 1


def fetch(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "confosense-temperature-preflight"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return int(response.status), response.read()
    except urllib.error.HTTPError as error:
        return int(error.code), error.read()


def readback(commit: str) -> int:
    backup_receipt = json.loads((REVIEW / "PREFLIGHT_BACKUP_VERIFICATION.json").read_text(encoding="utf-8"))
    if backup_receipt["verified_commit"] != commit or not backup_receipt["passed"]:
        raise SystemExit("backup receipt does not verify requested commit")
    api_status, api_data = fetch(f"https://api.github.com/repos/{OWNER_REPO}/commits/{commit}")
    api_sha = json.loads(api_data.decode("utf-8"))["sha"] if api_status == 200 else None
    downloads = []
    for row in backup_receipt["changed_paths"]:
        status, data = fetch(f"https://raw.githubusercontent.com/{OWNER_REPO}/{commit}/{row['path']}")
        downloads.append({"path": row["path"], "http_status": status, "committed_blob_bytes": row["bytes"], "downloaded_bytes": len(data), "committed_blob_sha256": row["sha256"], "downloaded_sha256": sha(data), "identical": len(data) == row["bytes"] and sha(data) == row["sha256"]})
    receipt = {
        "purpose": "commit-pinned GitHub HTTPS readback for substantive temperature preflight commit",
        "utc": utc(), "verified_commit": commit, "api_status": api_status, "api_commit_sha": api_sha, "api_matches_verified_commit": api_sha == commit,
        "downloads": downloads, "all_downloads_identical_to_committed_blobs": all(row["identical"] for row in downloads),
        "backup": {"passed": backup_receipt["passed"], "backup_root": backup_receipt["backup_root"], "bundle": backup_receipt["bundle"]},
        "scope_note": "This receipt verifies only the earlier substantive commit named above by HTTPS downloads pinned to that commit and compared with its committed Git blobs. It does not claim to verify the later commit that contains this receipt.",
    }
    receipt["passed"] = bool(api_sha == commit and receipt["all_downloads_identical_to_committed_blobs"] and backup_receipt["passed"])
    write_json(REVIEW / "PREFLIGHT_HTTPS_READBACK_RECEIPT.json", receipt)
    print(json.dumps({"passed": receipt["passed"], "commit": commit, "downloads": len(downloads)}, indent=2))
    return 0 if receipt["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("backup", "readback"))
    parser.add_argument("commit")
    args = parser.parse_args()
    return backup(args.commit) if args.action == "backup" else readback(args.commit)


if __name__ == "__main__":
    raise SystemExit(main())
