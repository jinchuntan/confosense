"""Run one command and record wall/CPU/RSS/I/O/disk measurements on Windows."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes as W
from datetime import datetime, timezone
from pathlib import Path


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class Entry(ctypes.Structure):
    _fields_ = [("size", W.DWORD), ("usage", W.DWORD), ("pid", W.DWORD),
                ("heap", ctypes.c_size_t), ("module", W.DWORD), ("threads", W.DWORD),
                ("parent", W.DWORD), ("priority", W.LONG), ("flags", W.DWORD), ("exe", W.WCHAR * 260)]


class Memory(ctypes.Structure):
    _fields_ = [("cb", W.DWORD), ("PageFaultCount", W.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t)]


class IO(ctypes.Structure):
    _fields_ = [("ReadOperationCount", ctypes.c_ulonglong), ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong), ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong), ("OtherTransferCount", ctypes.c_ulonglong)]


K = ctypes.WinDLL("kernel32", use_last_error=True)
P = ctypes.WinDLL("psapi", use_last_error=True)
K.CreateToolhelp32Snapshot.argtypes = [W.DWORD, W.DWORD]
K.CreateToolhelp32Snapshot.restype = W.HANDLE
K.Process32FirstW.argtypes = [W.HANDLE, ctypes.POINTER(Entry)]
K.Process32NextW.argtypes = [W.HANDLE, ctypes.POINTER(Entry)]
K.CloseHandle.argtypes = [W.HANDLE]
K.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
K.OpenProcess.restype = W.HANDLE
K.GetProcessTimes.argtypes = [W.HANDLE, *([ctypes.POINTER(W.FILETIME)] * 4)]
K.GetProcessIoCounters.argtypes = [W.HANDLE, ctypes.POINTER(IO)]
P.GetProcessMemoryInfo.argtypes = [W.HANDLE, ctypes.POINTER(Memory), W.DWORD]


def pids(root: int) -> set[int]:
    handle = K.CreateToolhelp32Snapshot(2, 0)
    rows = []
    item = Entry(); item.size = ctypes.sizeof(item)
    try:
        more = K.Process32FirstW(handle, ctypes.byref(item))
        while more:
            rows.append((int(item.pid), int(item.parent)))
            more = K.Process32NextW(handle, ctypes.byref(item))
    finally:
        K.CloseHandle(handle)
    found = {root}
    for _ in rows:
        added = {child for child, parent in rows if parent in found}
        if added <= found:
            break
        found |= added
    return found


def sample(root: int) -> dict[str, int]:
    working = private = cpu_100ns = read_bytes = write_bytes = 0
    live = 0
    for pid in pids(root):
        handle = K.OpenProcess(0x1000 | 0x0400, False, pid)
        if not handle:
            continue
        try:
            live += 1
            mem = Memory(); mem.cb = ctypes.sizeof(mem)
            if P.GetProcessMemoryInfo(handle, ctypes.byref(mem), mem.cb):
                working += int(mem.WorkingSetSize); private += int(mem.PrivateUsage)
            times = [W.FILETIME() for _ in range(4)]
            if K.GetProcessTimes(handle, *[ctypes.byref(value) for value in times]):
                for value in times[2:]:
                    cpu_100ns += (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)
            io = IO()
            if K.GetProcessIoCounters(handle, ctypes.byref(io)):
                read_bytes += int(io.ReadTransferCount); write_bytes += int(io.WriteTransferCount)
        finally:
            K.CloseHandle(handle)
    return {"live_processes": live, "working_set_bytes": working, "private_bytes": private,
            "cpu_100ns": cpu_100ns, "read_bytes": read_bytes, "write_bytes": write_bytes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        parser.error("command required")
    path = Path(args.log)
    if path.exists():
        raise FileExistsError(f"preserve prior command log: {path}")
    env = os.environ.copy()
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[key] = "1"
    started = stamp(); start = time.perf_counter(); initial_free = shutil.disk_usage(Path.cwd()).free
    with path.open("x", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        identity = {"command": command, "cwd": str(Path.cwd()), "started_utc": started,
                    "logger_pid": os.getpid(), "child_pid": process.pid, "status": "started", "exit_status": None}
        path.with_suffix(path.suffix + ".started.json").write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
        peak_working = peak_private = peak_family = peak_cpu = peak_read = peak_write = 0
        minimum_free = initial_free; samples = 0
        while process.poll() is None:
            row = sample(process.pid); samples += 1
            peak_working = max(peak_working, row["working_set_bytes"])
            peak_private = max(peak_private, row["private_bytes"])
            peak_family = max(peak_family, row["live_processes"])
            peak_cpu = max(peak_cpu, row["cpu_100ns"])
            peak_read = max(peak_read, row["read_bytes"]); peak_write = max(peak_write, row["write_bytes"])
            minimum_free = min(minimum_free, shutil.disk_usage(Path.cwd()).free)
            time.sleep(2)
        code = process.wait()
    result = {"command": command, "cwd": str(Path.cwd()), "started_utc": started,
              "logger_pid": os.getpid(), "child_pid": process.pid, "ended_utc": stamp(),
              "seconds": time.perf_counter() - start, "exit_status": code, "samples": samples,
              "peak_family_processes": peak_family, "peak_family_working_set_bytes": peak_working,
              "peak_family_private_bytes": peak_private, "family_cpu_seconds": peak_cpu / 10_000_000,
              "family_read_bytes": peak_read, "family_write_bytes": peak_write,
              "initial_disk_free_bytes": initial_free, "minimum_disk_free_bytes": minimum_free,
              "final_disk_free_bytes": shutil.disk_usage(Path.cwd()).free}
    path.with_suffix(path.suffix + ".json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
