"""Losslessly package each new raw run into deterministic GitHub-sized parts."""
from __future__ import annotations

import csv as csv_module
import gzip
import hashlib
import io
import json
import zipfile

from common import *


LIMIT = 95 * 2**20


def sha_data(data):
    return hashlib.sha256(data).hexdigest()


def csv_read(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv_module.DictReader(handle))


def verify_archive(archive, paths, source, complete):
    expected_names = [path.relative_to(source).as_posix() for path in paths]
    with zipfile.ZipFile(archive) as packed:
        if packed.namelist() != expected_names:
            raise ValueError("archive member order mismatch: " + str(archive))
        members = []
        for relative in expected_names:
            data = packed.read(relative); actual = sha_data(data)
            expected = digest(source / "COMPLETE.json") if relative == "COMPLETE.json" else complete["files"][relative]
            if actual != expected:
                raise ValueError("archive member hash mismatch: " + relative)
            members.append({"part": archive.name, "path": relative, "bytes": len(data), "sha256": actual})
    if archive.stat().st_size >= LIMIT:
        raise ValueError("archive part exceeds GitHub size bound")
    return members, {"part": archive.name, "bytes": archive.stat().st_size, "sha256": digest(archive),
                     "members": len(paths), "uncompressed_bytes": sum(path.stat().st_size for path in paths)}


def write_archive(archive, paths, source, complete):
    fixed = (2026, 9, 23, 0, 0, 0)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as packed:
        for path in paths:
            relative = path.relative_to(source).as_posix(); data = path.read_bytes(); actual = sha_data(data)
            expected = digest(source / "COMPLETE.json") if relative == "COMPLETE.json" else complete["files"][relative]
            if actual != expected:
                raise ValueError("raw source hash mismatch: " + relative)
            info = zipfile.ZipInfo(relative, fixed); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            packed.writestr(info, data, compresslevel=6)
    return verify_archive(archive, paths, source, complete)


def pack(seed):
    source = run(seed); destination = publication(seed)
    if (destination / "validation.json").exists():
        receipt = read(destination / "validation.json")
        for row in csv_read(destination / "parts_manifest.csv"):
            path = destination / row["part"]
            if path.stat().st_size != int(row["bytes"]) or digest(path) != row["sha256"]:
                raise ValueError("existing package part mismatch")
        return receipt
    complete = read(source / "COMPLETE.json"); current = tree(source); current.pop("COMPLETE.json")
    if current != complete["files"]:
        raise ValueError(f"seed {seed} raw tree differs from COMPLETE")
    files = sorted(path for path in source.rglob("*") if path.is_file()); groups = {"core": []}; contexts = []
    for path in files:
        relative = path.relative_to(source); stage = relative.parts[1] if len(relative.parts) > 1 and relative.parts[0] == "stages" else ""
        if stage.startswith("context_"):
            context = stage.rsplit("_v", 1)[0]
            if context not in contexts:
                contexts.append(context)
        else:
            groups["core"].append(path)
    for index in range(0, len(contexts), 8):
        selected = set(contexts[index:index + 8])
        groups[f"contexts_{index + 1:02d}_{min(index + 8, len(contexts)):02d}"] = [path for path in files
            if len(path.relative_to(source).parts) > 1 and path.relative_to(source).parts[1].rsplit("_v", 1)[0] in selected]
    if len(contexts) != 68 or sorted(path for group in groups.values() for path in group) != files:
        raise ValueError("raw package partition mismatch")
    destination.mkdir(parents=True, exist_ok=True); members = []; parts = []
    for label, paths in groups.items():
        archive = destination / (label + ".zip")
        current_members, part = verify_archive(archive, paths, source, complete) if archive.exists() else write_archive(archive, paths, source, complete)
        members.extend(current_members); parts.append(part)
    with gzip.GzipFile(filename="", mode="wb", fileobj=(destination / "raw_file_manifest.csv.gz").open("wb"), mtime=0) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", newline=""); writer = csv_module.DictWriter(text, fieldnames=["part", "path", "bytes", "sha256"])
        writer.writeheader(); writer.writerows(members); text.flush()
    with (destination / "parts_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv_module.DictWriter(handle, fieldnames=["part", "bytes", "sha256", "members", "uncompressed_bytes"])
        writer.writeheader(); writer.writerows(parts)
    receipt = {"passed": True, "model_seed": seed, "parts": len(parts), "members": len(members),
               "raw_files": len(files), "contexts": 68, "complete_tree_verified": True,
               "maximum_part_bytes": max(row["bytes"] for row in parts), "total_part_bytes": sum(row["bytes"] for row in parts),
               "github_part_limit_bytes": LIMIT, "source_complete_sha256": digest(source / "COMPLETE.json"),
               "reconstruction": "Extract every part into one empty directory and verify every byte with raw_file_manifest.csv.gz."}
    atomic(destination / "validation.json", receipt); return receipt


def main():
    results = [pack(seed) for seed in SEEDS]
    receipt = {"passed": True, "utc": now(), "seeds": list(SEEDS), "parts": sum(row["parts"] for row in results),
               "members": sum(row["members"] for row in results),
               "total_part_bytes": sum(row["total_part_bytes"] for row in results), "results": results}
    atomic(REVIEW / "RAW_PACKAGE_VALIDATION.json", receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
