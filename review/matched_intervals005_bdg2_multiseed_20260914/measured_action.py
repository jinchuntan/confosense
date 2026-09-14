"""Measure one complete CLI worker while retaining its actual exit."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
import argparse,runpy,sys,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'smart_building_conformal'))
from src.intervals005_common import PhaseMeter,atomic,now

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--measurement',required=True);args,command=parser.parse_known_args()
    if command[:1]==['--']:command=command[1:]
    if Path(args.measurement).exists():raise ValueError('measurement receipt exists; preserve it')
    started=now();status=0;error=None
    try:
        with PhaseMeter() as meter:
            sys.argv=['src.matched_intervals005',*command]
            runpy.run_module('src.matched_intervals005',run_name='__main__')
    except SystemExit as exc:status=exc.code if isinstance(exc.code,int) else (0 if exc.code is None else 1)
    except BaseException:
        status=1;error=traceback.format_exc();print(error,flush=True)
    atomic(args.measurement,dict(started_utc=started,ended_utc=now(),pid=os.getpid(),action_argv=command,actual_exit=status,resources=meter.result,error=error,interpretation='whole Python CLI worker'))
    raise SystemExit(status)

if __name__=='__main__':main()

