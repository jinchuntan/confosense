"""Immutable paths and helpers for the authorized PLEIA-temperature batch."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SMART = REPO / "smart_building_conformal"
REVIEW = Path(__file__).resolve().parent
PREFLIGHT = REPO / "review" / "pleia_temperature_context005_seeds43_46_preflight_20260922"
PYTHON = "C:/cfs_venv/Scripts/python.exe"
BRANCH = "review/pleia-temperature-context005-seeds43-46-execution-20260923"
ENTRY = "59b842b5ee4485553c8509d526159b2a7e46a00d"
MAIN = "06fe967be2be8d7898812c0c2d6e464d4e942351"
SOURCE_HASH = "a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f"
REQUIRED_FREE_BYTES = 16854663172
DISK_FLOOR_BYTES = 8 * 2**30
SEEDS = (43, 44, 45, 46)
ALL_SEEDS = (42, 43, 44, 45, 46)
BASE = SMART / "outputs" / "conditional_context005"
PROTOCOLS = SMART / "protocols" / "conditional_context005"
BATCH = BASE / "pleia_temperature_f2_context005_multiseed_v1_coordinator"
ANALYSIS = BASE / "pleia_temperature_f2_context005_five_seed_analysis_v1"
BACKUP = Path("C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_multiseed_20260923")
SEED42_RUN = BASE / "pleia_f2_s42_C_v1"
SEED42_DESIGN = PROTOCOLS / "pleia_f2_s42_C_v1"
SEED42_MANIFEST = REPO / "review" / "pleia_temperature_context005_pilot_20260918" / "pleia_f2_s42_C_v1_execution_manifest.json"
SEED42_ACCEPTANCE = BASE / "pleia_f2_s42_C_v1_validated_acceptance_v1"
VALIDATOR = PREFLIGHT / "candidate_validate_v2.py"

sys.path.insert(0, str(SMART))
from src.intervals005_common import atomic, append, csv, digest, now, read, source_digest, tree


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def key(seed: int) -> str:
    return f"pleia_f2_s{seed}_C_v1"


def manifest(seed: int) -> Path:
    return REVIEW / f"{key(seed)}_execution_manifest.json"


def draft_manifest(seed: int) -> Path:
    return PREFLIGHT / f"{key(seed)}_draft_manifest.json"


def design(seed: int) -> Path:
    return PROTOCOLS / key(seed)


def run(seed: int) -> Path:
    return BASE / key(seed)


def validation(seed: int) -> Path:
    return BATCH / f"seed_{seed}_validation"


def resume(seed: int) -> Path:
    return BATCH / f"seed_{seed}_completed_resume.json"


def acceptance(seed: int) -> Path:
    return BATCH / f"seed_{seed}_acceptance.json"


def publication(seed: int) -> Path:
    return BASE / f"{key(seed)}_publication_v1"
