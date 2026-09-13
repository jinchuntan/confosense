"""Observe an existing Windows pilot process through exit; never launches a fit."""
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import sys

pid=int(sys.argv[1]);out=Path(sys.argv[2])
if out.exists():raise FileExistsError(out)
k=C.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];k.WaitForSingleObject.restype=W.DWORD
k.GetProcessTimes.argtypes=[W.HANDLE,C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME)]
k.GetExitCodeProcess.argtypes=[W.HANDLE,C.POINTER(W.DWORD)]
k.CloseHandle.argtypes=[W.HANDLE]
handle=k.OpenProcess(0x1000|0x100000,False,pid)
if not handle:raise C.WinError(C.get_last_error())
started=datetime.now(timezone.utc).isoformat()
def number(ft):return (ft.dwHighDateTime<<32)+ft.dwLowDateTime
try:
    while k.WaitForSingleObject(handle,1000)==0x102:pass
    creation,exit_time,kernel,user=(W.FILETIME() for _ in range(4))
    if not k.GetProcessTimes(handle,C.byref(creation),C.byref(exit_time),C.byref(kernel),C.byref(user)):
        raise C.WinError(C.get_last_error())
    status=W.DWORD()
    if not k.GetExitCodeProcess(handle,C.byref(status)):raise C.WinError(C.get_last_error())
    epoch=datetime(1601,1,1,tzinfo=timezone.utc)
    record=dict(pid=pid,observer_started_utc=started,
        process_created_utc=(epoch+timedelta(microseconds=number(creation)/10)).isoformat(),
        process_exited_utc=(epoch+timedelta(microseconds=number(exit_time)/10)).isoformat(),
        process_lifetime_wall_seconds=(number(exit_time)-number(creation))/1e7,
        kernel_cpu_seconds=number(kernel)/1e7,user_cpu_seconds=number(user)/1e7,
        total_cpu_seconds=(number(kernel)+number(user))/1e7,exit_status=int(status.value),
        measurement='Windows GetProcessTimes over the retained actual pilot process handle; complete lifetime CPU, including time before observer attached')
    out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
finally:k.CloseHandle(handle)
