"""Build the isolated, hash-pinned science root used by every extension worker.

The 2026-10-02 re-checkout of the primary repository rewrote line endings of
tracked text files, so several frozen hash pins no longer match the primary
working tree byte-for-byte although their content is unchanged.  This step copies
exactly the inputs the replay reads into D: storage.  For every pinned file it
writes the byte variant (as found, LF or CRLF) whose SHA-256 equals the frozen
pin, and refuses any file that matches no variant.  Source modules are written
from the committed git blobs of the frozen candidature commit.  Nothing in the
primary repository is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PureWindowsPath

from hc_common import (
    BASE_COMMIT, FOLDS, FROZEN_PROTOCOL_SHA256, FROZEN_REL, HERE, MANIFEST_PATH, PRIMARY,
    RUN_ROOT, SCIENCE, SEEDS, atomic_json, digest, read, source_byte_digest,
    source_content_digest, unit_name, utc,
)

SMART = "smart_building_conformal"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def variants(data: bytes) -> list[tuple[str, bytes]]:
    lf = data.replace(b"\r\n", b"\n")
    return [("as_found", data), ("lf", lf), ("crlf", lf.replace(b"\n", b"\r\n"))]


def posix(path: str) -> str:
    return PureWindowsPath(path).as_posix()


class Builder:
    def __init__(self) -> None:
        self.files: dict[str, dict] = {}
        self.units: dict[str, list[str]] = {}

    def add(self, rel: str, *, pin: str | None, authority: str, scope: str) -> None:
        rel = posix(rel)
        source = PRIMARY / rel
        data = source.read_bytes()
        chosen = None
        for name, candidate in variants(data):
            if pin is None or sha(candidate) == pin:
                chosen = (name, candidate)
                break
        if chosen is None:
            raise ValueError(f"no byte variant of {rel} matches its frozen pin ({authority})")
        self._write(rel, chosen[1], variant=chosen[0], pin=pin, authority=authority,
                    origin="primary_working_tree", scope=scope)

    def add_blob(self, rel: str, blob: bytes, blob_sha: str, *, scope: str) -> None:
        self._write(rel, blob, variant="git_blob", pin=None, authority=f"git blob {blob_sha} at {BASE_COMMIT}",
                    origin=f"git_blob:{blob_sha}", scope=scope)

    def _write(self, rel: str, data: bytes, **record) -> None:
        if rel in self.files:
            if self.files[rel]["sha256"] != sha(data):
                raise ValueError(f"conflicting materialisation for {rel}")
            if record["scope"] != "shared" and rel not in self.units.setdefault(record["scope"], []):
                self.units[record["scope"]].append(rel)
            return
        target = SCIENCE / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise ValueError(f"refusing to overwrite science-root file: {rel}")
        target.write_bytes(data)
        if digest(target) != sha(data):
            raise ValueError(f"science-root write verification failed: {rel}")
        self.files[rel] = {"sha256": sha(data), "bytes": len(data), **record}
        if record["scope"] != "shared":
            self.units.setdefault(record["scope"], []).append(rel)


def git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(PRIMARY), *args], capture_output=True, check=True).stdout


def bundle_name(fold: int, seed: int) -> str:
    if fold == 2:
        return f"bdg2_f2_s{seed}_{'v1' if seed == 42 else 'v2'}"
    return f"bdg2_f{fold}_s{seed}_method_completion_v1"


def build() -> dict:
    if SCIENCE.exists() and any(SCIENCE.iterdir()):
        raise ValueError("science root already exists; use verify")
    SCIENCE.mkdir(parents=True, exist_ok=True)
    b = Builder()

    # Source modules: committed content at the frozen candidature commit.
    listing = git("ls-tree", "-r", BASE_COMMIT, "--", f"{SMART}/src").decode().splitlines()
    for line in listing:
        meta, path = line.split("\t", 1)
        blob_sha = meta.split()[2]
        b.add_blob(path, git("cat-file", "blob", blob_sha), blob_sha, scope="shared")
    src = SCIENCE / SMART / "src"
    primary_src = PRIMARY / SMART / "src"
    if source_content_digest(src) != source_content_digest(primary_src):
        raise ValueError("primary source content differs from the frozen commit")

    # Frozen operational005 replay: code, queues, protocol and its BDG2 raw-data copy.
    frozen = read(PRIMARY / FROZEN_REL / "PROTOCOL.json")
    b.add(f"{FROZEN_REL}/PROTOCOL.json", pin=FROZEN_PROTOCOL_SHA256,
          authority="COMPLETION_VALIDATION.protocol_sha256", scope="shared")
    for name, pin in frozen["code_hashes"].items():
        b.add(f"{FROZEN_REL}/{name}", pin=pin, authority="PROTOCOL.code_hashes", scope="shared")
    artifacts = {
        "evaluation_queue.csv": "candidate_queue_sha256", "candidate_definitions.csv": "candidate_definitions_sha256",
        "metric_view_queue.csv": "metric_view_queue_sha256", "owner_inventory.csv": "owner_inventory_sha256",
        "QUEUE_SUMMARY.json": "queue_summary_sha256", "PREFLIGHT.json": "preflight_sha256",
    }
    for name, field in artifacts.items():
        b.add(f"{FROZEN_REL}/{name}", pin=frozen[field], authority=f"PROTOCOL.{field}", scope="shared")
    b.add(frozen["operational_configuration"], pin=frozen["operational_configuration_sha256"],
          authority="PROTOCOL.operational_configuration_sha256", scope="shared")
    for name, pin in frozen["fault_specification_hashes"].items():
        if b.files[f"{SMART}/src/{name}"]["sha256"] != pin:
            raise ValueError(f"fault specification content differs from its pin: {name}")
    for path in sorted((PRIMARY / FROZEN_REL / "data").rglob("*")):
        if path.is_file():
            b.add(path.relative_to(PRIMARY).as_posix(), pin=None,
                  authority="verified downstream by the frozen data_hash", scope="shared")

    queue = list(__import__("csv").DictReader((PRIMARY / FROZEN_REL / "evaluation_queue.csv").open(encoding="utf-8")))
    for fold in FOLDS:
        for seed in SEEDS:
            unit = unit_name(fold, seed)
            rows = [r for r in queue if int(r["outer_fold"]) == fold and int(r["model_seed"]) == seed
                    and r["execution_status"] == "ready" and r["method"] == "cqr"]
            protocol_rel = rows[0]["interval_protocol_path"]
            b.add(protocol_rel, pin=rows[0]["interval_protocol_sha256"], authority="evaluation_queue.interval_protocol_sha256",
                  scope=unit)
            interval = read(SCIENCE / protocol_rel)
            bundle = f"{SMART}/outputs/matched_intervals005/{bundle_name(fold, seed)}"
            if posix(protocol_rel) != f"{SMART}/protocols/matched_intervals005/{bundle_name(fold, seed)}/frozen_protocol.json":
                raise ValueError("unexpected interval bundle layout")
            complete = read(PRIMARY / bundle / "COMPLETE.json")
            b.add(f"{bundle}/COMPLETE.json", pin=None, authority="bundle completion marker", scope=unit)
            for stage in ("owner_fit_h1_cqr_l95", "owner_cal_h1_cqr_l95", "raw_h1_cqr_l95", "dscp_joint"):
                stage_root = PRIMARY / bundle / "stages" / stage
                for path in sorted(stage_root.rglob("*")):
                    if path.is_file():
                        rel_in_bundle = path.relative_to(PRIMARY / bundle).as_posix()
                        b.add(f"{bundle}/{rel_in_bundle}", pin=complete["files"][rel_in_bundle],
                              authority="interval bundle COMPLETE.files", scope=unit)
            if b.files[rows[0]["model_owner_path"]]["sha256"] != rows[0]["model_owner_sha256"]:
                raise ValueError("saved 95% owner differs from the frozen queue")
            if b.files[rows[0]["calibration_owner_path"]]["sha256"] != rows[0]["calibration_owner_sha256"]:
                raise ValueError("saved 95% calibration differs from the frozen queue")
            reference = interval["references"]["1"]
            b.add(reference["protocol"], pin=reference["protocol_hash"], authority="interval reference protocol_hash",
                  scope=unit)
            for name, pin in reference["owner_hashes"].items():
                b.add(f"{posix(reference['owner_directory'])}/{name}", pin=pin,
                      authority="interval reference owner_hashes", scope=unit)
            historical = read(SCIENCE / posix(reference["protocol"]))
            for name, pin in historical["input_hashes"].items():
                b.add(f"{SMART}/{name}", pin=pin, authority="historical protocol input_hashes", scope=unit)
            # Accepted 95% replay block of the same unit: the fault catalogue and
            # disturbed observations of a new block must equal these exactly.
            accepted = f"{SMART}/outputs/operational005_causal_replay_v2/units/{unit}/blocks/block_000"
            marker = read(PRIMARY / accepted / "COMPLETE.json")
            b.add(f"{accepted}/COMPLETE.json", pin=None, authority="accepted block completion marker", scope=unit)
            for name, pin in marker["files"].items():
                b.add(f"{accepted}/{name}", pin=pin, authority="accepted block COMPLETE.files", scope=unit)

    manifest = {
        "version": "operational005_high_coverage_science_root_v1",
        "created_utc": utc(),
        "science_root": str(SCIENCE),
        "primary_repository": str(PRIMARY),
        "base_commit": BASE_COMMIT,
        "primary_head": git("rev-parse", "HEAD").decode().strip(),
        "source_content_digest": source_content_digest(src),
        "source_byte_digest_science_root": source_byte_digest(src),
        "source_byte_digest_primary": source_byte_digest(primary_src),
        "variant_counts": {name: sum(r["variant"] == name for r in b.files.values())
                           for name in ("as_found", "lf", "crlf", "git_blob")},
        "file_count": len(b.files),
        "total_bytes": sum(r["bytes"] for r in b.files.values()),
        "files": dict(sorted(b.files.items())),
        "units": {name: sorted(paths) for name, paths in sorted(b.units.items())},
    }
    atomic_json(MANIFEST_PATH, manifest)
    atomic_json(RUN_ROOT / "SCIENCE_ROOT_MANIFEST.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("files", "units")}, indent=2))
    return manifest


def verify() -> dict:
    manifest = read(MANIFEST_PATH)
    for name, record in manifest["files"].items():
        if digest(SCIENCE / name) != record["sha256"]:
            raise ValueError(f"science-root input changed: {name}")
    extra = {p.relative_to(SCIENCE).as_posix() for p in SCIENCE.rglob("*") if p.is_file()} - set(manifest["files"])
    extra = {name for name in extra if "__pycache__" not in name}
    if extra:
        raise ValueError(f"unexpected science-root files: {sorted(extra)[:5]}")
    result = {"passed": True, "files": len(manifest["files"]), "utc": utc()}
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["build", "verify"])
    args = parser.parse_args()
    build() if args.action == "build" else verify()
