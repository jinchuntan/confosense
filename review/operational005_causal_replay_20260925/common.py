"""Shared identities for the separately versioned operational005 replay."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[2]
SMART = REPO / "smart_building_conformal"
HERE = Path(__file__).resolve().parent
CONFIG = SMART / "configs" / "operational_amendment004.json"
INTERVAL_PROTOCOLS = SMART / "protocols" / "matched_intervals005"
INTERVAL_OUTPUTS = SMART / "outputs" / "matched_intervals005"
OUTPUTS = SMART / "outputs" / "operational005_causal_replay_v2"
UNITS = OUTPUTS / "units"
SUPERVISOR = OUTPUTS / "supervisor"
SOURCE_HASH = "a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f"
VERSION = "operational005_causal_replay_v2.3"
ENTRY_COMMIT = "bc9b30a93497b06f9cd7cb91f1c91b9092b51ead"
SCIENTIFIC_PYTHON = Path(r"C:\cfs_venv\Scripts\python.exe")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def signature(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def csv_write(path: Path, rows: Iterable[dict[str, Any]], fields: list[str] | None = None) -> None:
    rows = list(rows)
    if fields is None:
        fields = list(rows[0]) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def bundle_name(fold: int, seed: int) -> str:
    if fold == 2:
        return f"bdg2_f2_s{seed}_{'v1' if seed == 42 else 'v2'}"
    return f"bdg2_f{fold}_s{seed}_method_completion_v1"


def bundle_paths(fold: int, seed: int) -> tuple[Path, Path]:
    name = bundle_name(fold, seed)
    protocol = INTERVAL_PROTOCOLS / name
    output = INTERVAL_OUTPUTS / name
    if not protocol.is_dir() or not output.is_dir():
        raise ValueError(f"missing completed interval bundle: {name}")
    return protocol, output


def stage_file_identity(stage: Path, name: str) -> dict[str, Any]:
    marker = read(stage / "COMPLETE.json")
    expected = marker["files"].get(name)
    path = stage / name
    actual = digest(path)
    if expected != actual:
        raise ValueError(f"saved owner artifact changed: {path}")
    return {"path": path.relative_to(REPO).as_posix(), "sha256": actual, "bytes": path.stat().st_size}


def owner_reference(fold: int, seed: int, method: str, level: float) -> dict[str, Any]:
    protocol, output = bundle_paths(fold, seed)
    if method in {"quantile_uncalibrated", "cqr"}:
        if level != 0.95:
            return {
                "available": False,
                "reason": "no exact saved CQR/quantile owner at this frozen operational level",
                "owner_kind": "cqr",
            }
        owner_kind = "cqr"
        stage = output / "stages" / "owner_cal_h1_cqr_l95"
        raw = output / "stages" / "raw_h1_cqr_l95"
    elif method == "recentred_enbpi":
        owner_kind = "enbpi"
        stage = output / "stages" / "owner_cal_h1_enbpi"
        raw = output / "stages" / "raw_h1_enbpi"
    else:
        return {"available": False, "reason": "method absent from saved operational owner contract", "owner_kind": ""}
    frozen = protocol / "frozen_protocol.json"
    owner = stage_file_identity(stage, "owner.pkl")
    cal_meta = stage_file_identity(raw, "calibration_metadata.csv.gz")
    cal_values = stage_file_identity(raw, "calibration_95.csv.gz")
    common = output / "stages" / "dscp_joint" / "test_h1.csv.gz"
    if not common.exists():
        raise ValueError(f"missing frozen common-support membership: {common}")
    return {
        "available": True,
        "reason": "",
        "owner_kind": owner_kind,
        "owner": owner,
        "calibration_metadata": cal_meta,
        "calibration_values": cal_values,
        "interval_protocol": frozen.relative_to(REPO).as_posix(),
        "interval_protocol_sha256": digest(frozen),
        "common_support": common.relative_to(REPO).as_posix(),
        "common_support_sha256": digest(common),
        "evaluated_source_hash": read(output / "COMPLETE.json")["source_hash"],
    }


def code_hashes(names: Iterable[str]) -> dict[str, str]:
    return {name: digest(HERE / name) for name in names}


def process_identity(pid: int) -> dict[str, Any] | None:
    """Read a Windows process identity without adding a package to the scientific environment."""
    pid = int(pid)
    script = (
        f'$launchPid={pid}; $p=Get-CimInstance Win32_Process -Filter "ProcessId = {pid}"; '
        'for($depth=0; $depth -lt 8 -and $null -ne $p; $depth++) {'
        '$child=Get-CimInstance Win32_Process -Filter ("ParentProcessId = " + $p.ProcessId) '
        '|Sort-Object CreationDate|Select-Object -Last 1; if($null -eq $child){break}; $p=$child}; '
        '$g=if($null -ne $p){Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue}; '
        'if ($null -ne $p -and $null -ne $g) {'
        '[pscustomobject]@{launch_pid=[int]$launchPid;pid=[int]$p.ProcessId;'
        'creation_time=$g.StartTime.ToUniversalTime().ToString("o");'
        'executable=$p.ExecutablePath;command=$p.CommandLine;'
        'cpu_seconds=[double]$g.CPU;rss_bytes=[int64]$g.WorkingSet64}'
        '|ConvertTo-Json -Compress}'
    )
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", script],
                            capture_output=True, text=True, check=False)
    if result.returncode or not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def verify_protocol() -> dict[str, Any]:
    """Fail closed if any frozen code, queue, configuration, or fault definition changed."""
    path = HERE / "PROTOCOL.json"
    if not path.exists():
        raise ValueError("missing frozen causal-replay protocol")
    protocol = read(path)
    if protocol.get("version") != VERSION or protocol.get("entry_commit") != ENTRY_COMMIT:
        raise ValueError("causal-replay protocol identity mismatch")
    runtime = protocol.get("runtime", {})
    if Path(sys.executable).resolve() != SCIENTIFIC_PYTHON.resolve():
        raise ValueError(f"wrong causal-replay interpreter: {sys.executable}")
    if digest(SCIENTIFIC_PYTHON) != runtime.get("python_sha256"):
        raise ValueError("frozen causal-replay interpreter changed")
    from importlib.metadata import version
    for package, expected in runtime.get("packages", {}).items():
        if version(package) != expected:
            raise ValueError(f"frozen causal-replay package changed: {package}")
    for name, expected in protocol.get("code_hashes", {}).items():
        actual = digest(HERE / name)
        if actual != expected:
            raise ValueError(f"frozen causal-replay code changed: {name}")
    artifacts = {
        "candidate_queue_sha256": HERE / "evaluation_queue.csv",
        "candidate_definitions_sha256": HERE / "candidate_definitions.csv",
        "metric_view_queue_sha256": HERE / "metric_view_queue.csv",
        "owner_inventory_sha256": HERE / "owner_inventory.csv",
        "queue_summary_sha256": HERE / "QUEUE_SUMMARY.json",
        "preflight_sha256": HERE / "PREFLIGHT.json",
        "operational_configuration_sha256": CONFIG,
    }
    for field, artifact in artifacts.items():
        if digest(artifact) != protocol.get(field):
            raise ValueError(f"frozen causal-replay artifact changed: {artifact}")
    for name, expected in protocol.get("fault_specification_hashes", {}).items():
        artifact = SMART / "src" / name
        if digest(artifact) != expected:
            raise ValueError(f"frozen fault implementation changed: {name}")
    return protocol
