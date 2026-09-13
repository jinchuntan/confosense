"""Windows process/host memory measurements using the existing standard library."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import os
import platform
import threading
import time


class _MemoryStatus(ctypes.Structure):
    _fields_ = [("length", wintypes.DWORD), ("load", wintypes.DWORD)] + [
        (name, ctypes.c_ulonglong) for name in
        ("total_physical", "available_physical", "total_page", "available_page",
         "total_virtual", "available_virtual", "available_extended")]


class _ProcessMemory(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in ("peak_rss", "rss", "peak_pool_paged",
        "pool_paged", "peak_pool_nonpaged", "pool_nonpaged", "pagefile",
        "peak_pagefile", "private_bytes")]


def memory_snapshot():
    if os.name != "nt":
        raise RuntimeError("pilot memory instrumentation requires the declared Windows host")
    status = _MemoryStatus(); status.length = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError()
    mem = _ProcessMemory(); mem.cb = ctypes.sizeof(mem)
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    api = ctypes.windll.psapi.GetProcessMemoryInfo
    api.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessMemory), wintypes.DWORD]
    if not api(kernel.GetCurrentProcess(), ctypes.byref(mem), mem.cb):
        raise ctypes.WinError()
    return dict(rss_bytes=int(mem.rss), private_bytes=int(mem.private_bytes),
        lifetime_peak_rss_bytes=int(mem.peak_rss), available_ram_bytes=int(status.available_physical),
        physical_ram_bytes=int(status.total_physical))


def hardware():
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
        cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    return dict(cpu=cpu, logical_processors=os.cpu_count(), os=platform.platform(),
                python=platform.python_version(), memory=memory_snapshot(),
                environment_threads={k: os.environ.get(k) for k in
                    ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")})


class ResourceMeter:
    """50 ms sampled phase peaks plus Windows' process-lifetime RSS high water."""
    def __init__(self, interval=.05):
        self.interval = interval

    def sample(self):
        s = memory_snapshot()
        self.peak_rss = max(self.peak_rss, s["rss_bytes"])
        self.peak_private = max(self.peak_private, s["private_bytes"])
        self.min_available = min(self.min_available, s["available_ram_bytes"])
        self.last = s

    def __enter__(self):
        self.baseline = memory_snapshot()
        self.peak_rss = self.baseline["rss_bytes"]
        self.peak_private = self.baseline["private_bytes"]
        self.min_available = self.baseline["available_ram_bytes"]
        self.stop = threading.Event(); self.start = time.perf_counter()
        def poll():
            while not self.stop.wait(self.interval):
                self.sample()
        self.thread = threading.Thread(target=poll, daemon=True); self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set(); self.thread.join(); self.sample()
        self.result = dict(seconds=time.perf_counter()-self.start,
            baseline_rss_bytes=self.baseline["rss_bytes"], peak_rss_bytes=self.peak_rss,
            baseline_private_bytes=self.baseline["private_bytes"], peak_private_bytes=self.peak_private,
            incremental_peak_rss_bytes=self.peak_rss-self.baseline["rss_bytes"],
            lifetime_peak_rss_bytes=self.last["lifetime_peak_rss_bytes"],
            min_available_ram_bytes=self.min_available, sample_interval_seconds=self.interval)


def require_ram(minimum_bytes):
    snapshot = memory_snapshot()
    if snapshot["available_ram_bytes"] < minimum_bytes:
        raise MemoryError(f"available RAM {snapshot['available_ram_bytes']} < frozen minimum {minimum_bytes}")
    return snapshot
