"""Atomic, content-verified per-unit experiment checkpoints.

Resume requires the same code/configuration/data identity. A partial directory
is never a completed unit; a completed but corrupt unit fails loudly. Historical
run directories without this manifest cannot be overwritten by a repaired run.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import uuid
import pandas as pd


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_digest():
    root = Path(__file__).parent
    return hashlib.sha256("\n".join(
        f"{p.relative_to(root).as_posix()}:{digest(p)}"
        for p in sorted(root.rglob("*.py"))).encode()).hexdigest()


def json_value(obj):
    if hasattr(obj, "item"):
        return obj.item()
    return str(obj)


def signature(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True, default=json_value).encode()).hexdigest()


class UnitCheckpoint:
    def __init__(self, root, spec, *, resume=False):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.spec_hash = signature(spec)
        manifest = self.root / "checkpoint_manifest.json"
        if manifest.exists():
            if not resume:
                raise ValueError("run already exists; explicit resume is required")
            saved = json.loads(manifest.read_text(encoding="utf-8"))
            if saved["spec_hash"] != self.spec_hash:
                raise ValueError("resume code/config/data signature mismatch; use a new run directory")
        else:
            if any(self.root.iterdir()):
                raise ValueError("refusing to overwrite a historical or unrecognised run directory")
            manifest.write_text(json.dumps({"spec": spec, "spec_hash": self.spec_hash},
                indent=2, default=json_value), encoding="utf-8")
        (self.root / "units").mkdir(exist_ok=True)

    def _path(self, key):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            raise ValueError("invalid unit key")
        return self.root / "units" / key

    def load(self, key):
        path = self._path(key)
        if not path.exists():
            return None
        marker = path / "COMPLETE.json"
        if not marker.exists():
            raise ValueError(f"incomplete committed unit {key}")
        record = json.loads(marker.read_text(encoding="utf-8"))
        if record["spec_hash"] != self.spec_hash or record["key"] != key:
            raise ValueError(f"unit provenance mismatch {key}")
        for name, expected in record["hashes"].items():
            if not (path / name).is_file() or digest(path / name) != expected:
                raise ValueError(f"corrupt checkpoint {key}/{name}")
        payload = json.loads((path / "payload.json").read_text(encoding="utf-8"))
        frames = {}
        for name, filename in record["frames"].items():
            try:
                frames[name] = pd.read_csv(path / filename, float_precision="round_trip")
            except pd.errors.EmptyDataError:
                frames[name] = pd.DataFrame()
        return payload, frames

    def save(self, key, payload, frames):
        destination = self._path(key)
        if destination.exists():
            raise ValueError(f"duplicate experimental unit {key}")
        staging = self.root / (".partial-" + key + "-" + uuid.uuid4().hex)
        staging.mkdir()
        (staging / "payload.json").write_text(json.dumps(payload, default=json_value), encoding="utf-8")
        names = {}
        for name, frame in frames.items():
            if not re.fullmatch(r"[A-Za-z0-9_]+", name):
                raise ValueError("invalid frame name")
            names[name] = name + ".csv.gz"
            frame.to_csv(staging / names[name], index=False, compression="gzip")
        hashes = {p.name: digest(p) for p in staging.iterdir() if p.is_file()}
        with (staging / "COMPLETE.json").open("w", encoding="utf-8") as f:
            json.dump({"key": key, "spec_hash": self.spec_hash, "frames": names,
                       "hashes": hashes}, f, indent=2)
            f.flush(); os.fsync(f.fileno())
        staging.rename(destination)

    def require_complete(self, expected_keys):
        expected = list(expected_keys)
        if len(expected) != len(set(expected)):
            raise ValueError("duplicate expected experimental cells")
        actual = {p.name for p in (self.root / "units").iterdir() if p.is_dir()}
        if actual != set(expected):
            raise ValueError(f"unit matrix mismatch: missing={sorted(set(expected)-actual)}, extra={sorted(actual-set(expected))}")
        for key in expected:
            self.load(key)


def require_cells(frame, columns, expected):
    """Exact scientific-cell coverage, not merely dataset/family presence."""
    keys = list(frame[columns].itertuples(index=False, name=None))
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate experimental cells")
    if set(keys) != set(expected):
        raise ValueError("missing or unexpected experimental cells")
