"""Fresh-process bootstrap for the hash-bound corrected validator v1.

This entrypoint changes no validation logic.  It resolves the repository and
scientific roots from its own location before importing the preserved v1
validator, so script-mode launches do not depend on the caller's working
directory or a globally configured PYTHONPATH.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SMART = REPO / "smart_building_conformal"
if not (SMART / "src").is_dir():
    raise RuntimeError(f"scientific root is unavailable: {SMART}")
sys.path.insert(0, str(SMART))

import corrected_validator_v1 as validator
from src.intervals005_common import digest


VERSION = "matched_intervals005_corrected_validator_bootstrap_v2"


def import_identity() -> dict:
    import src

    src_root = Path(src.__file__).resolve().parent
    if src_root != (SMART / "src").resolve():
        raise RuntimeError(f"unexpected src import: {src_root}")
    return {
        "passed": True,
        "version": VERSION,
        "entrypoint": str(Path(__file__).resolve()),
        "entrypoint_sha256": digest(Path(__file__)),
        "preserved_validator": str(Path(validator.__file__).resolve()),
        "preserved_validator_sha256": digest(Path(validator.__file__)),
        "scientific_root": str(SMART.resolve()),
        "src_root": str(src_root),
        "interpreter": str(Path(sys.executable).resolve()),
        "cwd": os.getcwd(),
    }


def main() -> None:
    if sys.argv[1:] == ["--import-check"]:
        print(json.dumps(import_identity(), indent=2), flush=True)
        return
    validator.main()


if __name__ == "__main__":
    main()
