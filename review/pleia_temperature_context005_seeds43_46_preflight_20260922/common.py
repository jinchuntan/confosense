"""Shared constants for the bounded PLEIA-temperature seeds 43--46 preflight."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SMART = REPO / "smart_building_conformal"
REVIEW = Path(__file__).resolve().parent
PYTHON = "C:/cfs_venv/Scripts/python.exe"
BRANCH = "review/pleia-temperature-context005-seeds43-46-preflight-20260922"
ENTRY = "ed560464e8fecc3462d068e87ae019eae5b11300"
MAIN = "06fe967be2be8d7898812c0c2d6e464d4e942351"
SOURCE_HASH = "a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f"
SEEDS = (43, 44, 45, 46)
ALL_SEEDS = (42, 43, 44, 45, 46)
BASE = SMART / "outputs" / "conditional_context005"
SEED42_RUN = BASE / "pleia_f2_s42_C_v1"
SEED42_DESIGN = SMART / "protocols" / "conditional_context005" / "pleia_f2_s42_C_v1"
SEED42_MANIFEST = REPO / "review" / "pleia_temperature_context005_pilot_20260918" / "pleia_f2_s42_C_v1_execution_manifest.json"
AUDIT = REPO / "review" / "pleia_temperature_context005_validation_audit_20260919"
ACCEPTANCE = REPO / "review" / "pleia_temperature_context005_validated_acceptance_20260921"
DESIGNS = REVIEW / "draft_designs"
BACKUP = Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_seeds43_46_preflight_20260922")

sys.path.insert(0, str(SMART))


def utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def key(seed: int) -> str:
    return f"pleia_f2_s{seed}_C_v1"


def manifest(seed: int) -> Path:
    return REVIEW / f"{key(seed)}_draft_manifest.json"


def design(seed: int) -> Path:
    return DESIGNS / key(seed)


def proposed_run(seed: int) -> Path:
    return BASE / key(seed)


def read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, sort_keys=True, default=str) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise ValueError(f"preserve differing existing evidence: {path}")
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()
