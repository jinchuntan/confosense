"""Run manifests, provenance records and resumable-execution bookkeeping.

Three jobs, all in service of being able to say later exactly how a number was
produced:

* **Provenance** — where each dataset came from (official source, DOI, URL,
  retrieval time, archive name, checksum, licence, preprocessing decisions),
  written to ``manifests/dataset_sources.json``.
* **Manifest** — the environment a run happened in: git SHA, whether the tree was
  dirty, config path and hash, package versions, seeds, machine, timings, and
  which stages completed, failed or were skipped *and why*. Written to
  ``manifests/experiment_manifest.json``.
* **Resume** — a per-stage ledger so an interrupted study restarts at the first
  incomplete stage instead of recomputing everything.

The resume ledger stores the configuration hash alongside each completed stage.
On ``--resume`` a stage is only reused when its hash still matches; otherwise it
is recomputed and the mismatch is recorded. Silently reusing results computed
under a different configuration would be the single easiest way to publish a
number that no run ever produced.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .datasets.base import config_hash


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except Exception:                                    # pragma: no cover
        return ""


def git_state() -> dict:
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(status),
        "n_modified_files": len([ln for ln in status.splitlines() if ln.strip()]),
    }


def package_versions() -> dict:
    versions = {"python": sys.version.split()[0]}
    for name, mod in [("numpy", "numpy"), ("pandas", "pandas"), ("scipy", "scipy"),
                      ("scikit_learn", "sklearn"), ("xgboost", "xgboost"),
                      ("torch", "torch"), ("mapie", "mapie"),
                      ("matplotlib", "matplotlib"), ("pyarrow", "pyarrow"),
                      ("h5py", "h5py"), ("tables", "tables")]:
        try:
            versions[name] = __import__(mod).__version__
        except Exception:
            versions[name] = "not installed"
    return versions


def machine_info() -> dict:
    """Machine identity plus everything that can change a numerical result.

    Thread counts are recorded because XGBoost's ``hist`` tree method reduces
    gradient histograms in thread-completion order: the same seed on the same
    data yields a different model at a different core count. A result is only
    reproducible alongside the thread configuration that produced it.
    """
    import os

    info = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "device": "cpu",
    }
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS"):
        info[var] = os.environ.get(var, "unset")
    try:
        import torch
        info["torch_num_threads"] = torch.get_num_threads()
    except Exception:
        info["torch_num_threads"] = "unavailable"
    return info


# --------------------------------------------------------------------------- #
@dataclass
class StageRecord:
    name: str
    status: str                 # completed | failed | skipped
    seconds: float = 0.0
    reason: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class RunManifest:
    """Accumulates everything about one study run and writes it out at the end."""

    config_path: str
    config: dict
    output_dir: Path
    fast: bool = False
    datasets: list[str] = field(default_factory=list)
    stages: list[StageRecord] = field(default_factory=list)
    provenance: dict = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)

    @property
    def manifest_dir(self) -> Path:
        d = self.output_dir / "manifests"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def record(self, name: str, status: str, seconds: float = 0.0,
               reason: str = "", **details) -> None:
        self.stages.append(StageRecord(name, status, seconds, reason, details))

    def note_limitation(self, text: str) -> None:
        if text not in self.limitations:
            self.limitations.append(text)

    def add_provenance(self, dataset_id: str, prov: dict) -> None:
        """Record a dataset's provenance, stamping the retrieval time.

        ``Provenance`` initialises ``retrieved_at`` to an empty string, so
        ``setdefault`` would leave it empty — the field has to be filled when it
        is absent *or* blank, otherwise every manifest records no retrieval time
        at all.
        """
        prov = dict(prov)
        if not str(prov.get("retrieved_at", "")).strip():
            prov["retrieved_at"] = pd.Timestamp.utcnow().isoformat()
        self.provenance[dataset_id] = prov

    def write(self) -> dict:
        payload = {
            "config_path": self.config_path,
            "config_hash": config_hash(self.config),
            "fast_mode": self.fast,
            "datasets": self.datasets,
            "git": git_state(),
            "packages": package_versions(),
            "machine": machine_info(),
            "seed": self.config.get("seed"),
            "started_at": pd.Timestamp.utcfromtimestamp(self.started_at).isoformat(),
            "ended_at": pd.Timestamp.utcnow().isoformat(),
            "runtime_seconds": round(time.time() - self.started_at, 2),
            "stages": [
                {"name": s.name, "status": s.status, "seconds": round(s.seconds, 2),
                 "reason": s.reason, **s.details}
                for s in self.stages
            ],
            "n_completed": sum(s.status == "completed" for s in self.stages),
            "n_failed": sum(s.status == "failed" for s in self.stages),
            "n_skipped": sum(s.status == "skipped" for s in self.stages),
            "limitations": self.limitations,
        }
        with open(self.manifest_dir / "experiment_manifest.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        # Provenance is *merged*, not overwritten. A study is normally executed
        # one dataset at a time so that failures stay isolated, and each of those
        # invocations only knows about its own dataset; overwriting would leave
        # the final manifest describing whichever dataset happened to run last,
        # losing the sources and checksums of all the others.
        prov_path = self.manifest_dir / "dataset_sources.json"
        merged = {}
        if prov_path.exists():
            try:
                merged = json.loads(prov_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                merged = {}
        merged.update(self.provenance)
        if merged:
            with open(prov_path, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2, default=str)

        # Likewise, append a one-line summary of every invocation so the stage
        # record of a multi-command study survives; experiment_manifest.json
        # describes only the most recent invocation.
        history = {k: payload[k] for k in
                   ("config_path", "config_hash", "fast_mode", "datasets",
                    "started_at", "ended_at", "runtime_seconds", "n_completed",
                    "n_failed", "n_skipped")}
        history["git_commit"] = payload["git"]["commit"]
        history["stages"] = [{"name": s["name"], "status": s["status"],
                              "seconds": s["seconds"]} for s in payload["stages"]]
        with open(self.manifest_dir / "run_history.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(history, default=str) + "\n")
        return payload


# --------------------------------------------------------------------------- #
class ResumeLedger:
    """Per-stage completion ledger guarded by a configuration hash."""

    def __init__(self, path: Path, cfg_hash: str, enabled: bool):
        """Load any compatible ledger, whether or not resume is requested.

        ``enabled`` governs only whether :meth:`done` reports a stage as
        reusable. The existing file is loaded regardless, because :meth:`mark`
        rewrites it: if a run started from an empty ledger it would erase every
        previously recorded stage the moment it marked its first one. That is
        how an ordinary ``--stage prepare`` invocation, which does not pass
        ``--resume``, silently destroyed the completion record of a finished
        multi-hour study.
        """
        self.path = path
        self.cfg_hash = cfg_hash
        self.enabled = enabled
        self.state: dict = {"config_hash": cfg_hash, "stages": {}}
        self.mismatches: list[str] = []
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                loaded = {}
            if loaded.get("config_hash") == cfg_hash:
                self.state = loaded
            elif enabled:
                # Different configuration: start clean rather than mixing runs.
                self.mismatches.append(
                    f"resume ledger at {path} was written under configuration hash "
                    f"{loaded.get('config_hash')!r}, but this run is "
                    f"{cfg_hash!r}; all stages will be recomputed"
                )

    def done(self, stage: str) -> bool:
        return self.enabled and stage in self.state.get("stages", {})

    def mark(self, stage: str, **details) -> None:
        self.state.setdefault("stages", {})[stage] = {
            "completed_at": pd.Timestamp.utcnow().isoformat(), **details
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, indent=2, default=str),
                             encoding="utf-8")
