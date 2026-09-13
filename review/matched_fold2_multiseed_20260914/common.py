"""Orchestration utilities; no estimator or scientific-design implementation."""
import csv, hashlib, json, os, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMART = ROOT / 'smart_building_conformal'
REVIEW = Path(__file__).resolve().parent
BASE = SMART / 'outputs/matched_forecasting005'
BATCH = BASE / 'fold2_multiseed_batch_v1'
BACKUP = Path('C:/Users/nigel/ConfoSenseBackups/matched_fold2_multiseed_20260914')
PYTHON = 'C:/cfs_venv/Scripts/python.exe'
ENTRY = '3df9cbd480ffbfeac640580829e88c274fba2083'
INSTRUCTION = '1312510b8549ef9467ee63597cf3e634412044a9'
BRANCH = 'review/matched-fold2-multiseed-20260914'
MATRIX = SMART / 'outputs/amendment005/support_design_v1/experiment_matrix.csv'
QUEUE = BASE / 'overnight_batch_v1/analysis_v1/remaining_queue_updated.csv'
AUTH = SMART / 'configs/matched_forecasting005_fold2_multiseed_authorization_v1.json'
HORIZONS = [('pleia_energy',h) for h in (1,3,6)] + [('rico',h) for h in (5,15,30,60)] + [('bdg2',h) for h in (1,3,6)] + [('pleia',h) for h in (1,3,6)]
KEYS = [(ds,h,2,s) for s in (43,44,45,46) for ds,h in HORIZONS]
OLD_REVIEW = ROOT / 'review/matched_overnight_20260914'
OLD_ANALYSIS = BASE / 'overnight_batch_v1/analysis_v1'
MODELS = ['persistence','xgboost','attention_lstm']
KEYCOLS = ['dataset','horizon','outer_fold','model_seed']

def now(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(2**20),b''): h.update(part)
    return h.hexdigest()
def tree(path): return {p.relative_to(path).as_posix():sha(p) for p in sorted(Path(path).rglob('*')) if p.is_file()}
def atomic(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+f'.{os.getpid()}.{uuid.uuid4().hex}.tmp')
    with temp.open('w',encoding='utf-8',newline='\n') as f:
        if isinstance(value,str): f.write(value)
        else: json.dump(value,f,indent=2,default=str);f.write('\n')
        f.flush();os.fsync(f.fileno())
    delays=[.02,.05,.1,.2,.5,1,1,1,2,2]
    for attempt in range(len(delays)+1):
        try:
            os.replace(temp,path);break
        except PermissionError as exc:
            # Windows readers/sync/indexing can briefly deny replacement. Keep
            # the old atomic file intact, preserve the new temporary file, and
            # retry only this bookkeeping rename with a finite wait budget.
            append(BACKUP/'atomic_replace_retries.jsonl',dict(utc=now(),path=str(path),temporary=str(temp),attempt=attempt,error=str(exc)))
            if attempt==len(delays):raise
            time.sleep(delays[attempt])
def append(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open('a',encoding='utf-8') as f:
        f.write(json.dumps(value,default=str)+'\n');f.flush();os.fsync(f.fileno())
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def stem(key): return f'{key[0]}_h{key[1]}_f{key[2]}_s{key[3]}_v1'
def paths(key):
    s=stem(key)
    return dict(key=list(key),stem=s,design=str(SMART/'protocols/matched_forecasting005'/s),run=str(BASE/s))
def argv(unit,action,receipt=None):
    ds,h,f,s=unit['key']
    a=[PYTHON,'-B','-m','src.matched_forecasting005',action,'--matrix',str(MATRIX),'--dataset',ds,'--horizon',str(h),'--outer-fold',str(f),'--model-seed',str(s),'--design-dir',unit['design']]
    if action=='freeze':a+=['--authorization',str(AUTH)]
    elif action in ('run','resume','validate'):a+=['--out',unit['run'],'--readiness',str(Path(unit['design'])/'readiness.json')]
    if receipt:a+=['--receipt',str(receipt)]
    return a
def logged(command,log,*,stdout=None):
    log=Path(log);log.parent.mkdir(parents=True,exist_ok=True)
    wrapped=[PYTHON,'-B',str(SMART/'scripts/log_pilot_command.py'),'--log',str(log),'--',*command]
    result=subprocess.run(wrapped,cwd=SMART,stdout=stdout,stderr=subprocess.STDOUT)
    receipt=read(str(log)+'.json')
    if result.returncode or receipt['exit_status']:
        raise RuntimeError(f'Command failed, exit {receipt["exit_status"]}: {log}')
    return receipt
