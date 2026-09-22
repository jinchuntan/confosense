"""Explicitly stage and commit the fully frozen batch before the first fit."""
from __future__ import annotations

import json
import subprocess

from common import *


def main() -> None:
    if git("branch", "--show-current") != BRANCH:
        raise ValueError("wrong branch")
    pre = read(REVIEW / "PREFIT_VALIDATION.json")
    if not pre["passed"] or pre["models_fitted"] != 0:
        raise ValueError("pre-fit validation missing")
    frozen = {"version": "pleia_temperature_context005_multiseed_frozen_v1", "utc": now(),
              "source_hash": source_digest(), "model_seeds": list(SEEDS), "seed42_reused": True,
              "manifests": {str(seed): digest(manifest(seed)) for seed in SEEDS},
              "protocols": {str(seed): digest(design(seed) / "frozen_protocol.json") for seed in SEEDS},
              "readiness": {str(seed): digest(design(seed) / "readiness.json") for seed in SEEDS},
              "exact_commands": read(REVIEW / "BATCH_SCOPE.json")["commands"],
              "preflight_sha256": digest(REVIEW / "PREFIT_VALIDATION.json"), "models_fitted": 0}
    atomic(REVIEW / "FROZEN_BATCH_MANIFEST.json", frozen)
    roots = [REVIEW, *(design(seed) for seed in SEEDS)]
    files = sorted({path for root in roots for path in root.rglob("*") if path.is_file()
                    and "__pycache__" not in path.parts and path.suffix != ".pyc"})
    rels = [path.relative_to(REPO).as_posix() for path in files]
    BACKUP.mkdir(parents=True, exist_ok=True)
    pathfile = BACKUP / "pre_fit_paths.txt"
    atomic(pathfile, "\n".join(rels) + "\n")
    subprocess.run(["git", "add", "--pathspec-from-file=" + str(pathfile)], cwd=REPO, check=True)
    subprocess.run(["git", "diff", "--cached", "--check"], cwd=REPO, check=True)
    staged = git("diff", "--cached", "--name-only").splitlines()
    if sorted(staged) != sorted(rels):
        raise ValueError("explicit staged list differs from pre-fit file list")
    subprocess.run(["git", "commit", "-m", "Freeze authorized PLEIA-temperature multiseed batch"], cwd=REPO, check=True)
    frozen["evaluated_commit"] = git("rev-parse", "HEAD")
    atomic(REVIEW / "EVALUATED_COMMIT.json", frozen)
    subprocess.run(["git", "add", "--", str((REVIEW / "EVALUATED_COMMIT.json").relative_to(REPO))], cwd=REPO, check=True)
    subprocess.run(["git", "commit", "-m", "Record temperature multiseed evaluated commit"], cwd=REPO, check=True)
    print(json.dumps({"sealed": True, "head": git("rev-parse", "HEAD"),
                      "evaluated_commit": frozen["evaluated_commit"], "files": len(rels)}, indent=2))


if __name__ == "__main__":
    main()
