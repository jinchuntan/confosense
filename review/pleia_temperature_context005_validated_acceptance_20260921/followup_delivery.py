"""Backup and HTTPS-readback an earlier, additive follow-up evidence commit.

Each receipt names the earlier commit it verifies.  It never claims to verify
the later commit that contains the receipt itself.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BACKUP_ROOT = Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_validated_acceptance_20260921")
ENTRY = "18d8dd15d06459b3b54ba629e9948b78494f4c8f"
BRANCH = "review/pleia-temperature-context005-validated-acceptance-20260921"
OWNER_REPO = "jinchuntan/confosense"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str, binary: bool = False) -> str | bytes:
    value = subprocess.check_output(["git", *args], cwd=REPO, text=not binary)
    return value if binary else value.strip()  # type: ignore[union-attr,return-value]


def changed_paths(commit: str) -> list[str]:
    names = str(git("diff-tree", "--no-commit-id", "--name-only", "-r", commit)).splitlines()
    prefixes = ("review/pleia_temperature_context005_validated_acceptance_20260921/", "smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/")
    if not names or any(not name.startswith(prefixes) for name in names):
        raise SystemExit("follow-up commit must change only acceptance evidence paths")
    return names


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def backup(commit: str) -> int:
    if str(git("rev-parse", "HEAD")) != commit:
        raise SystemExit("backup must run while HEAD equals the named earlier follow-up commit")
    dest = BACKUP_ROOT / f"followup_{commit}_v1"
    if dest.exists():
        raise SystemExit(f"preserve existing follow-up backup: {dest}")
    dest.mkdir(parents=True)
    rows = []
    for name in changed_paths(commit):
        data = git("cat-file", "blob", f"{commit}:{name}", binary=True)  # type: ignore[assignment]
        target = dest / "exact_committed_blobs" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        rows.append({"path": name, "bytes": len(data), "sha256": sha(data), "backup_path": str(target.relative_to(dest)).replace("\\", "/")})
    with (dest / "blob_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256", "backup_path"], lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    bundle = dest / f"followup_{commit}.bundle"
    made = subprocess.run(["git", "bundle", "create", str(bundle), BRANCH, "^" + ENTRY], cwd=REPO, text=True, capture_output=True)
    checked = subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=REPO, text=True, capture_output=True) if made.returncode == 0 else None
    receipt = {
        "purpose": "exact committed-blob and incremental-bundle backup for earlier additive acceptance follow-up",
        "utc": utc(), "verified_commit": commit, "base_commit_not_in_incremental_bundle": ENTRY,
        "changed_paths": rows, "all_exact_blobs_verified": all((dest / row["backup_path"]).read_bytes() == git("cat-file", "blob", f"{commit}:{row['path']}", binary=True) for row in rows),
        "bundle": {"path": str(bundle), "bytes": bundle.stat().st_size if bundle.exists() else None, "sha256": sha(bundle.read_bytes()) if bundle.exists() else None,
                   "create_returncode": made.returncode, "verify_returncode": checked.returncode if checked else None, "verify_stdout": checked.stdout if checked else None, "verify_stderr": checked.stderr if checked else made.stderr},
        "backup_root": str(dest),
        "scope_note": "This backup contains the named earlier additive evidence commit and its changed acceptance-evidence paths. It does not claim to verify a later receipt-containing commit.",
    }
    receipt["passed"] = bool(receipt["all_exact_blobs_verified"] and made.returncode == 0 and checked and checked.returncode == 0)
    output = HERE / "FOLLOWUP_BACKUP_VERIFICATION.json"
    if output.exists():
        raise SystemExit(f"preserve existing follow-up backup receipt: {output}")
    write_json(output, receipt)
    print(json.dumps({"passed": receipt["passed"], "commit": commit, "paths": len(rows)}, indent=2))
    return 0 if receipt["passed"] else 1


def fetch(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "confosense-acceptance-followup"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return int(response.status), response.read()
    except urllib.error.HTTPError as error:
        return int(error.code), error.read()


def readback(commit: str) -> int:
    backup_receipt = json.loads((HERE / "FOLLOWUP_BACKUP_VERIFICATION.json").read_text(encoding="utf-8"))
    api_status, api_data = fetch(f"https://api.github.com/repos/{OWNER_REPO}/commits/{commit}")
    api_sha = json.loads(api_data.decode("utf-8"))["sha"] if api_status == 200 else None
    downloads = []
    for row in backup_receipt["changed_paths"]:
        status, data = fetch(f"https://raw.githubusercontent.com/{OWNER_REPO}/{commit}/{row['path']}")
        downloads.append({"path": row["path"], "http_status": status, "committed_blob_bytes": row["bytes"], "downloaded_bytes": len(data), "committed_blob_sha256": row["sha256"], "downloaded_sha256": sha(data), "identical": len(data) == row["bytes"] and sha(data) == row["sha256"]})
    receipt = {
        "purpose": "commit-pinned GitHub HTTPS readback for earlier additive acceptance follow-up",
        "utc": utc(), "verified_commit": commit, "api_status": api_status, "api_commit_sha": api_sha, "api_matches_verified_commit": api_sha == commit,
        "downloads": downloads, "all_downloads_identical_to_committed_blobs": all(row["identical"] for row in downloads),
        "backup": {"passed": backup_receipt["passed"], "backup_root": backup_receipt["backup_root"], "bundle": backup_receipt["bundle"]},
        "scope_note": "This receipt verifies only the earlier commit named above, by GitHub HTTPS downloads pinned to that commit and compared with its committed blobs. It does not claim to verify the later commit that contains this receipt.",
    }
    receipt["passed"] = bool(backup_receipt["passed"] and api_sha == commit and receipt["all_downloads_identical_to_committed_blobs"])
    output = HERE / "FOLLOWUP_HTTPS_READBACK_RECEIPT.json"
    if output.exists():
        raise SystemExit(f"preserve existing follow-up HTTPS receipt: {output}")
    write_json(output, receipt)
    print(json.dumps({"passed": receipt["passed"], "commit": commit, "downloads": len(downloads)}, indent=2))
    return 0 if receipt["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("backup", "readback"))
    parser.add_argument("commit")
    arguments = parser.parse_args()
    return backup(arguments.commit) if arguments.action == "backup" else readback(arguments.commit)


if __name__ == "__main__":
    raise SystemExit(main())
