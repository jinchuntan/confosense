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
    def __init__(self, root, spec, *, resume=False, string_columns=()):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.spec_hash = signature(spec)
        # Opt-in schema for new runners: e.g. an asset literally named "None"
        # must survive CSV loading. Historical readers retain their old default.
        self.string_columns = tuple(string_columns)
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

    def verify(self, key):
        """Verify committed bytes/provenance without materializing CSV frames.

        Scientific cell validation remains the consumer's responsibility after
        its single load (or on the original in-memory frames after save).
        """
        path = self._path(key)
        if not path.exists():
            return None
        marker = path / "COMPLETE.json"
        if not marker.exists():
            raise ValueError(f"incomplete committed unit {key}")
        record = json.loads(marker.read_text(encoding="utf-8"))
        if record["spec_hash"] != self.spec_hash or record["key"] != key:
            raise ValueError(f"unit provenance mismatch {key}")
        required = {"payload.json", *record["frames"].values()}
        if not required.issubset(record["hashes"]):
            raise ValueError(f"unhashed checkpoint payload/frame {key}")
        for name, expected in record["hashes"].items():
            if Path(name).name != name or name in (".", "..", "COMPLETE.json"):
                raise ValueError(f"invalid checkpoint filename {key}/{name}")
            if not (path / name).is_file() or digest(path / name) != expected:
                raise ValueError(f"corrupt checkpoint {key}/{name}")
        # Small JSON payload validation retains the former completeness contract.
        json.loads((path / "payload.json").read_text(encoding="utf-8"))
        return record

    def load(self, key):
        record = self.verify(key)
        if record is None:
            return None
        path = self._path(key)
        payload = json.loads((path / "payload.json").read_text(encoding="utf-8"))
        frames = {}
        for name, filename in record["frames"].items():
            try:
                frames[name] = pd.read_csv(path / filename, float_precision="round_trip",
                    converters={column: str for column in self.string_columns})
            except pd.errors.EmptyDataError:
                frames[name] = pd.DataFrame()
        return payload, frames

    def save(self, key, payload, frames, *, artifacts=None):
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
        for name, data in (artifacts or {}).items():
            if not re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9]+", name) or name in names.values() or name in ("payload.json", "COMPLETE.json"):
                raise ValueError("invalid artifact name")
            (staging / name).write_bytes(data)
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
            self.verify(key)


def require_cells(frame, columns, expected):
    """Exact scientific-cell coverage, not merely dataset/family presence."""
    keys = list(frame[columns].itertuples(index=False, name=None))
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate experimental cells")
    if set(keys) != set(expected):
        raise ValueError("missing or unexpected experimental cells")
