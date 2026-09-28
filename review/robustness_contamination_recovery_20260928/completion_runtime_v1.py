"""Lightweight control-plane utilities; imports no scientific packages."""
from __future__ import annotations

import csv
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SMART = REPO / "smart_building_conformal"
OUTPUT_ROOT = SMART / "outputs" / "robustness_contamination_recovery005"
OWNER_ROOT = OUTPUT_ROOT / "constructed_owners_v1"
LEGACY_FULL_ROOT = OUTPUT_ROOT / "completion_59_v1"
FULL_ROOT = OUTPUT_ROOT / "completion_58_v2"
PROTOCOL = HERE / "COMPLETION_PROTOCOL.json"
REGISTRY = HERE / "CONSTRUCTED_OWNERS.json"
SCIENTIFIC_CONTRACT = HERE / "SCIENTIFIC_REPLAY_CONTRACT.json"
SCIENTIFIC_PYTHON = Path(r"C:\cfs_venv\Scripts\python.exe")
DISK_FLOOR = 8 * 2**30
UNIT_ALLOWANCE = 512 * 2**20
LAUNCH_HEADROOM = 3 * 2**30


def utc(): return datetime.now(timezone.utc).isoformat()


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(2**20), b""): value.update(chunk)
    return value.hexdigest()


def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, default=str); handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


def crosswalk_records():
    with (HERE / "CROSSWALK.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 60 or sum(int(x["historical_obligation_cells"]) for x in rows) != 900:
        raise ValueError("frozen crosswalk no longer represents 60 units / 900 cells")
    return rows


def unit_key(row):
    return f"{row['dataset']}_h{int(row['horizon'])}_f{int(row['outer_fold'])}_s{int(row['model_seed'])}"


def checkpoint_root(key):
    return LEGACY_FULL_ROOT if key == "bdg2_h1_f0_s42" else FULL_ROOT


def completion_protocol():
    value = read(PROTOCOL)
    expected = {
        "preparation_commit": "138c9d6d47b01953669d8d4b88e4e662ac5e2fc4",
        "preparation_crosswalk_sha256": digest(HERE / "CROSSWALK.csv"),
        "preparation_protocol_sha256": digest(HERE / "PROTOCOL.json"),
    }
    for name, actual in expected.items():
        if value[name] != actual: raise ValueError(f"completion protocol identity mismatch: {name}")
    for name, expected_hash in value["source_sha256"].items():
        if digest(HERE / name) != expected_hash: raise ValueError(f"completion source identity mismatch: {name}")
    return value


class _PerformanceInformation(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong), ("CommitTotal", ctypes.c_size_t), ("CommitLimit", ctypes.c_size_t),
        ("CommitPeak", ctypes.c_size_t), ("PhysicalTotal", ctypes.c_size_t),
        ("PhysicalAvailable", ctypes.c_size_t), ("SystemCache", ctypes.c_size_t),
        ("KernelTotal", ctypes.c_size_t), ("KernelPaged", ctypes.c_size_t),
        ("KernelNonpaged", ctypes.c_size_t), ("PageSize", ctypes.c_size_t),
        ("HandleCount", ctypes.c_ulong), ("ProcessCount", ctypes.c_ulong), ("ThreadCount", ctypes.c_ulong),
    ]


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def resources():
    ctypes.windll.psapi.GetPerformanceInfo.argtypes = [ctypes.POINTER(_PerformanceInformation), wintypes.DWORD]
    ctypes.windll.psapi.GetPerformanceInfo.restype = wintypes.BOOL
    ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessMemoryCounters), wintypes.DWORD]
    ctypes.windll.psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    info = _PerformanceInformation(); info.cb = ctypes.sizeof(info)
    if not ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(info), info.cb): raise OSError("GetPerformanceInfo failed")
    counters = _ProcessMemoryCounters(); counters.cb = ctypes.sizeof(counters)
    if not ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return {
        "physical_available_bytes": int(info.PhysicalAvailable * info.PageSize),
        "commit_headroom_bytes": int((info.CommitLimit - info.CommitTotal) * info.PageSize),
        "disk_free_bytes": int(shutil.disk_usage(REPO.anchor).free),
        "working_set_bytes": int(counters.WorkingSetSize),
        "peak_working_set_bytes": int(counters.PeakWorkingSetSize),
        "pagefile_usage_bytes": int(counters.PagefileUsage),
        "peak_pagefile_usage_bytes": int(counters.PeakPagefileUsage),
    }


def resource_gate(stage, allowance=UNIT_ALLOWANCE):
    value = resources(); value.update(stage=stage, utc=utc(), disk_allowance_bytes=int(allowance))
    if value["disk_free_bytes"] < DISK_FLOOR + allowance: raise RuntimeError("completion disk resource gate failed")
    if value["physical_available_bytes"] < LAUNCH_HEADROOM: raise RuntimeError("completion physical-RAM resource gate failed")
    if value["commit_headroom_bytes"] < LAUNCH_HEADROOM: raise RuntimeError("completion Windows-commit resource gate failed")
    return value
