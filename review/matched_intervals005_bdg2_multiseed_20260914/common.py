"""Paths and helpers for the bounded BDG2 interval multiseed extension."""
import json, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SMART=ROOT/'smart_building_conformal'
REVIEW=Path(__file__).resolve().parent
BACKUP=Path('C:/Users/nigel/ConfoSenseBackups/matched_intervals005_bdg2_multiseed_20260914')
BATCH=SMART/'outputs/matched_intervals005/bdg2_fold2_multiseed_v2_coordinator'
PYTHON='C:/cfs_venv/Scripts/python.exe'
BRANCH='review/matched-intervals005-bdg2-multiseed-20260914'
ENTRY='4853f634134a77b347ee29f781e3e81fe0b207cf'
SEEDS=[43,44,45,46]
sys.path.insert(0,str(SMART))
from src.intervals005_common import atomic as _atomic, append, read as _read, tree, now
from src.unit_checkpoint import digest as sha, source_digest

def design(seed):return SMART/f'protocols/matched_intervals005/bdg2_f2_s{seed}_v2'
def run(seed):return SMART/f'outputs/matched_intervals005/bdg2_f2_s{seed}_v2'
def auth(seed):return SMART/f'configs/matched_intervals005_bdg2_multiseed_s{seed}_v2.json'
def atomic(path,value):return _atomic(path,value,BACKUP/'atomic_replace_retries.jsonl')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def read(path):
    for attempt in range(100):
        try:return _read(path)
        except (json.JSONDecodeError,PermissionError):
            if attempt==99:raise
            time.sleep(.01)
