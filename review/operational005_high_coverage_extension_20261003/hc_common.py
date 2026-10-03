"""Shared identities for the separately versioned operational005 high-coverage extension.

The extension completes only the 99 BDG2 one-hour candidates that the frozen
operational005 replay recorded as unavailable (CQR and uncalibrated quantiles at
nominal 0.975, 0.99 and 0.995).  It never edits the frozen replay, its queues or
its accepted outputs.  Scientific code runs from an isolated, hash-pinned copy of
the frozen inputs (the "science root") outside OneDrive.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parents[1]
PRIMARY = Path(r"C:\Users\nigel\OneDrive\Desktop\GitHub\confosense")
RUN_ROOT = Path(r"D:\ConfoSenseStorage\runs\op005_hicov_v1")
SCIENCE = RUN_ROOT / "science_root"
FROZEN_REL = "review/operational005_causal_replay_20260925"
FROZEN = SCIENCE / FROZEN_REL
OWNERS = RUN_ROOT / "owners"
UNITS = RUN_ROOT / "units"
SUPERVISOR = RUN_ROOT / "supervisor"
ANALYSIS = RUN_ROOT / "analysis_v1"
QUARANTINE = RUN_ROOT / "quarantine"
PROTOCOL_PATH = HERE / "EXTENSION_PROTOCOL.json"
MANIFEST_PATH = HERE / "SCIENCE_ROOT_MANIFEST.json"

VERSION = "operational005_high_coverage_extension_v1"
BRANCH = "review/operational005-high-coverage-extension-20261003"
BASE_COMMIT = "d65147ff22e6c079603eda1337630254796c8990"
FROZEN_TAG = "candidature-evidence-20261002-v1"
ENTRY_COMMIT = "bc9b30a93497b06f9cd7cb91f1c91b9092b51ead"
FROZEN_PROTOCOL_SHA256 = "4138a93b1b79120bcd2b837b1ffb7a31896f8511bd7a671a2b182d9a55ff2c6a"
# Byte digest recorded by every accepted 2026-09 run.  Its working-tree line-ending
# mix is not recoverable after the 2026-10-02 checkout; the extension pins the
# committed source content instead (see source_content_digest).
HISTORICAL_SOURCE_BYTE_DIGEST = "a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f"
SCIENTIFIC_PYTHON = Path(r"C:\cfs_venv\Scripts\python.exe")
LEVELS = (0.975, 0.99, 0.995)
FOLDS = (0, 1, 2)
SEEDS = (42, 43, 44, 45, 46)
PILOT_UNIT = (0, 42)
BLOCKS_PER_UNIT = 33
THREAD_VARIABLES = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
EXTENSION_CODE = (
    "hc_common.py", "hc_materialize.py", "hc_freeze.py", "hc_owner.py", "hc_adapter.py",
    "hc_validate.py", "hc_pilot_gate.py", "hc_aggregate.py", "test_hc_guards.py",
)


def single_thread_environment() -> None:
    for name in THREAD_VARIABLES:
        os.environ[name] = "1"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def lf_digest(path: Path) -> str:
    """Digest of text content with CRLF normalised to LF (checkout-independent)."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def signature(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def level_tag(level: float) -> str:
    """0.975 -> l0975; avoids the int(level*100) collision of 0.99 and 0.995."""
    tag = f"l{round(float(level) * 1000):04d}"
    if float(level) not in LEVELS or tag not in {"l0975", "l0990", "l0995"}:
        raise ValueError(f"level outside the extension scope: {level}")
    return tag


def unit_name(fold: int, seed: int) -> str:
    if fold not in FOLDS or seed not in SEEDS:
        raise ValueError("unit outside the extension scope")
    return f"bdg2_f{fold}_s{seed}"


def replace_retry(source: Path, target: Path, journal: Path | None = None) -> int:
    """Atomic rename with bounded retries for transient Windows sharing denials."""
    delays = (.05, .1, .25, .5, 1., 2.)
    for attempt in range(len(delays) + 1):
        try:
            os.replace(source, target)
            return attempt
        except PermissionError as exc:
            if journal is not None:
                append_ledger(journal, event="atomic_rename_denial", source=str(source), target=str(target),
                              attempt=attempt, error=repr(exc))
            if attempt == len(delays):
                raise
            time.sleep(delays[attempt])
    raise AssertionError("unreachable rename retry state")


def atomic_json(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, default=str) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    replace_retry(temporary, path, path.parent / "file_access_retries.jsonl")


def atomic_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    replace_retry(temporary, path, path.parent / "file_access_retries.jsonl")


def csv_write(path: Path, rows: Iterable[dict[str, Any]], fields: list[str] | None = None) -> None:
    rows = list(rows)
    if fields is None:
        fields = list(rows[0]) if rows else []
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    replace_retry(temporary, path)


def append_ledger(path: Path, **record: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"utc": utc(), **record}, default=str, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def tree(path: Path) -> dict[str, str]:
    path = Path(path)
    return {p.relative_to(path).as_posix(): digest(p) for p in sorted(path.rglob("*")) if p.is_file()}


def source_content_digest(src: Path) -> str:
    """Digest of src/*.py content with CRLF normalised; equals the git-blob digest."""
    src = Path(src)
    return hashlib.sha256("\n".join(
        f"{p.relative_to(src).as_posix()}:{lf_digest(p)}" for p in sorted(src.rglob("*.py"))
    ).encode()).hexdigest()


def source_byte_digest(src: Path) -> str:
    """The frozen unit_checkpoint.source_digest formula over the files as they are on disk."""
    src = Path(src)
    return hashlib.sha256("\n".join(
        f"{p.relative_to(src).as_posix()}:{digest(p)}" for p in sorted(src.rglob("*.py"))
    ).encode()).hexdigest()


def extension_code_hashes() -> dict[str, str]:
    return {name: lf_digest(HERE / name) for name in EXTENSION_CODE}


def verify_science_files(paths: Iterable[str] | None = None) -> int:
    """Verify science-root bytes against the materialisation manifest."""
    manifest = read(MANIFEST_PATH)
    files = manifest["files"]
    selected = files if paths is None else {name: files[name] for name in paths}
    for name, record in selected.items():
        if digest(SCIENCE / name) != record["sha256"]:
            raise ValueError(f"science-root input changed: {name}")
    return len(selected)


def unit_science_paths(fold: int, seed: int) -> list[str]:
    """Shared inputs plus the inputs belonging to one fold/seed unit."""
    manifest = read(MANIFEST_PATH)
    owned = set(manifest["units"][unit_name(fold, seed)])
    return [name for name, record in manifest["files"].items()
            if record["scope"] == "shared" or name in owned]


def verify_extension_protocol(*, fold: int | None = None, seed: int | None = None,
                              check_frozen: bool = True) -> dict[str, Any]:
    """Fail closed if the extension protocol, its code, interpreter or inputs changed."""
    if not PROTOCOL_PATH.exists():
        raise ValueError("missing frozen extension protocol")
    protocol = read(PROTOCOL_PATH)
    if protocol.get("version") != VERSION:
        raise ValueError("extension protocol identity mismatch")
    if Path(sys.executable).resolve() != SCIENTIFIC_PYTHON.resolve():
        raise ValueError(f"wrong scientific interpreter: {sys.executable}")
    runtime = protocol["runtime"]
    if digest(SCIENTIFIC_PYTHON) != runtime["python_sha256"]:
        raise ValueError("scientific interpreter changed")
    from importlib.metadata import version
    for package, expected in runtime["packages"].items():
        if version(package) != expected:
            raise ValueError(f"scientific package changed: {package}")
    for name, expected in protocol["extension_code_lf_sha256"].items():
        if lf_digest(HERE / name) != expected:
            raise ValueError(f"extension code changed: {name}")
    for name, expected in protocol["extension_artifact_lf_sha256"].items():
        if lf_digest(HERE / name) != expected:
            raise ValueError(f"extension artifact changed: {name}")
    if lf_digest(MANIFEST_PATH) != protocol["science_root_manifest_lf_sha256"]:
        raise ValueError("science-root manifest changed")
    if fold is None:
        verify_science_files()
    else:
        verify_science_files(unit_science_paths(fold, seed))
    src = SCIENCE / "smart_building_conformal" / "src"
    if source_content_digest(src) != protocol["source_content_digest"]:
        raise ValueError("science-root source content changed")
    if check_frozen:
        sys.path.insert(0, str(FROZEN))
        import common as frozen_common  # frozen operational005 module, science-root copy
        if Path(frozen_common.__file__).resolve() != (FROZEN / "common.py").resolve():
            raise ValueError("frozen common module resolved outside the science root")
        frozen_common.verify_protocol()
    return protocol
