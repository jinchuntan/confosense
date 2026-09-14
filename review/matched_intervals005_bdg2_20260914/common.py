"""Isolated task paths and the established Windows durable logging helpers."""
import csv,hashlib,json,os,subprocess,sys,time,uuid
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SMART=ROOT/'smart_building_conformal'
REVIEW=Path(__file__).resolve().parent
BACKUP=Path('C:/Users/nigel/ConfoSenseBackups/matched_intervals005_bdg2_20260914')
BATCH=SMART/'outputs/matched_intervals005/bdg2_pilot_v1_coordinator'
RUN=SMART/'outputs/matched_intervals005/bdg2_f2_s42_v1'
DESIGN=SMART/'protocols/matched_intervals005/bdg2_f2_s42_v1'
AUTH=SMART/'configs/matched_intervals005_bdg2_authorization_v1.json'
PYTHON='C:/cfs_venv/Scripts/python.exe'
BRANCH='review/matched-intervals005-bdg2-20260914'
ENTRY='c143fa16eaf9bfc6354b4cb1f8861915cb00f388'
sys.path.insert(0,str(SMART))
from src.intervals005_common import atomic as _atomic,append,read,tree,now
from src.unit_checkpoint import digest as sha

def atomic(path,value):return _atomic(path,value,BACKUP/'atomic_replace_retries.jsonl')


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def logged(command,log):
    log=Path(log);log.parent.mkdir(parents=True,exist_ok=True)
    result=subprocess.run([PYTHON,'-B',str(SMART/'scripts/log_pilot_command.py'),'--log',str(log),'--',*command],cwd=SMART)
    receipt=read(str(log)+'.json')
    if result.returncode or receipt['exit_status']:raise RuntimeError('actual command failure: '+str(log))
    return receipt


def command(action,receipt=None):
    result=[PYTHON,'-B',str(REVIEW/'measured_action.py'),'--measurement',str(BATCH/(action+'_worker_resources_v1.json')),'--',action,'--design-dir',str(DESIGN),'--out',str(RUN),'--readiness',str(DESIGN/'readiness.json')]
    if receipt:result+=['--receipt',str(receipt)]
    if action=='resume':result+=['--forbid-fits']
    return result
