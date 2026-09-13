"""Record exact command, complete output, wall time and exit status without extra packages."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ap=argparse.ArgumentParser()
ap.add_argument("--log",required=True)
ap.add_argument("command",nargs=argparse.REMAINDER)
a=ap.parse_args()
command=a.command[1:] if a.command and a.command[0]=="--" else a.command
if not command:
    ap.error("command required")
path=Path(a.log);path.parent.mkdir(parents=True,exist_ok=True)
if path.exists():
    raise FileExistsError(f"preserve prior command log: {path}")
start=time.perf_counter(); stamp=datetime.now(timezone.utc).isoformat()
with path.open("w",encoding="utf-8") as log:
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        text=True,encoding="utf-8",errors="replace",bufsize=1)
    identity=dict(command=command,cwd=str(Path.cwd()),started_utc=stamp,
                  logger_pid=os.getpid(),child_pid=process.pid,status='started',exit_status=None)
    with path.with_suffix(path.suffix+'.started.json').open('x',encoding='utf-8') as f:
        json.dump(identity,f,indent=2);f.flush();os.fsync(f.fileno())
    for line in process.stdout:
        log.write(line);log.flush();print(line,end="",flush=True)
    code=process.wait()
result=dict(command=command,cwd=str(Path.cwd()),started_utc=stamp,
            logger_pid=os.getpid(),child_pid=process.pid,
            ended_utc=datetime.now(timezone.utc).isoformat(),seconds=time.perf_counter()-start,exit_status=code)
path.with_suffix(path.suffix+".json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result),flush=True)
sys.exit(code)
