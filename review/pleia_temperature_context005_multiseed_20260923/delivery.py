"""Create the scoped delta backup and commit-pinned HTTPS readback receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from common import *


BACKUP_BASE = "f28eb4c6edc3362ad930ec949fd4363a2ce759fb"
PREFLIGHT_BUNDLE = Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_seeds43_46_preflight_20260922/primary_f28eb4c6edc3362ad930ec949fd4363a2ce759fb_v1/preflight_f28eb4c6edc3362ad930ec949fd4363a2ce759fb.bundle")
PREFLIGHT_BUNDLE_SHA256 = "6b1837773e846df132342262ba1e83c360038807e4f242327b1f1df4c6f5a5f6"
LINEAGE_BUNDLE = Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_validated_acceptance_20260921/followup_03ca62f2f0704725a13b93929b5ba5797f06e20f_v1/followup_03ca62f2f0704725a13b93929b5ba5797f06e20f.bundle")
LINEAGE_BUNDLE_SHA256 = "654ee36a1cd1879f665bbe55356b010b7d3b4496fe10d05752ae8cb10fa15767"


def http_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "ConfoSense-delivery-verifier"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.status, json.loads(response.read())


def http_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": "ConfoSense-delivery-verifier"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.status, response.read()


def main(commit):
    if git("branch", "--show-current") != BRANCH or git("rev-parse", "HEAD") != commit:
        raise ValueError("delivery must run at the named substantive commit")
    for path, expected in ((PREFLIGHT_BUNDLE, PREFLIGHT_BUNDLE_SHA256), (LINEAGE_BUNDLE, LINEAGE_BUNDLE_SHA256)):
        if not path.is_file() or digest(path) != expected:
            raise ValueError("verified external prerequisite changed: " + str(path))
        subprocess.run(["git", "bundle", "verify", str(path)], cwd=REPO, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    destination = BACKUP / ("substantive_" + commit + "_v1"); destination.mkdir(parents=True, exist_ok=False)
    bundle = destination / ("temperature_multiseed_" + commit + ".bundle")
    created = subprocess.run(["git", "bundle", "create", str(bundle), BRANCH, "^" + BACKUP_BASE],
                             cwd=REPO, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    verified = subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=REPO, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    backup_receipt = {"passed": True, "utc": now(), "purpose": "scoped external delta backup of substantive temperature five-seed delivery",
        "verified_commit": commit, "bundle": {"path": str(bundle), "bytes": bundle.stat().st_size,
        "sha256": digest(bundle), "create_stdout": created.stdout, "create_stderr": created.stderr,
        "verify_stdout": verified.stdout, "verify_stderr": verified.stderr},
        "prerequisite_commit": BACKUP_BASE,
        "verified_prerequisites": [{"path": str(PREFLIGHT_BUNDLE), "sha256": PREFLIGHT_BUNDLE_SHA256},
                                   {"path": str(LINEAGE_BUNDLE), "sha256": LINEAGE_BUNDLE_SHA256}],
        "scope_note": "The bundle contains commits after the externally backed f28eb4c prerequisite through the named substantive delivery. It does not claim to contain or duplicate the prerequisite's historical multi-gigabyte objects, nor a later receipt-containing commit."}
    atomic(REVIEW / "BACKUP_VERIFICATION.json", backup_receipt)
    subprocess.run(["git", "push", "-u", "origin", BRANCH], cwd=REPO, check=True)
    api_status, api = http_json(f"https://api.github.com/repos/jinchuntan/confosense/commits/{commit}")
    if api_status != 200 or api["sha"] != commit:
        raise ValueError("GitHub commit API mismatch")
    paths = [
        REVIEW / "PLEIA_TEMPERATURE_CONTEXT005_FIVE_SEED_REPORT.md", REVIEW / "EVIDENCE_INDEX.md",
        REVIEW / "BATCH_COMPLETION_RECORD.json", REVIEW / "COMPLETION_VERIFICATION.json",
        REVIEW / "EVIDENCE_MANIFEST.csv", ANALYSIS / "validation.json", ANALYSIS / "independent_validation.json",
        ANALYSIS / "five_seed_control_rule_channel.csv", ANALYSIS / "inference_bounds.csv",
        ANALYSIS / "five_seed_interval_diagnostics.csv", ANALYSIS / "operation_reconciliation.csv",
        ANALYSIS / "worker_costs_and_resources.csv", ANALYSIS / "five_seed_detection.sources.json",
    ]
    for seed in SEEDS:
        paths += [manifest(seed), design(seed) / "frozen_protocol.json", run(seed) / "COMPLETE.json",
                  run(seed) / "operations.jsonl", acceptance(seed), validation(seed) / "ADAPTER_VALIDATION_RECEIPT.json",
                  resume(seed), publication(seed) / "validation.json", publication(seed) / "parts_manifest.csv"]
    downloads = []
    for path in paths:
        relative = path.relative_to(REPO).as_posix()
        committed = subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=REPO)
        url = "https://raw.githubusercontent.com/jinchuntan/confosense/" + commit + "/" + urllib.parse.quote(relative)
        status, downloaded = http_bytes(url)
        row = {"path": relative, "url": url, "status": status, "bytes": len(downloaded),
               "committed_sha256": hashlib.sha256(committed).hexdigest(),
               "downloaded_sha256": hashlib.sha256(downloaded).hexdigest(),
               "identical": downloaded == committed}
        if status != 200 or not row["identical"]:
            raise ValueError("HTTPS readback mismatch: " + relative)
        downloads.append(row)
    readback = {"passed": True, "utc": now(), "verified_commit": commit, "api_status": api_status,
        "api_commit_sha": api["sha"], "api_matches_verified_commit": api["sha"] == commit,
        "downloads": downloads, "downloads_verified": len(downloads),
        "all_downloads_identical_to_committed_blobs": all(row["identical"] for row in downloads),
        "scope_note": "This receipt verifies only the earlier substantive commit named above: the GitHub commit API plus the explicitly listed report, index, completion, analysis, per-seed identity/acceptance, and package-manifest files downloaded over HTTPS and compared with committed Git blobs. It does not claim HTTPS readback of every raw ZIP part or of the later commit containing this receipt."}
    atomic(REVIEW / "HTTPS_READBACK_RECEIPT.json", readback)
    print(json.dumps({"backup": backup_receipt, "https_passed": True, "downloads": len(downloads)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--commit", required=True)
    main(parser.parse_args().commit)
