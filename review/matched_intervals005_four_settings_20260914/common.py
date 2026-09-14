"""Paths and immutable scope for the remaining-settings interval batch."""
import json, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SMART=ROOT/'smart_building_conformal'
REVIEW=Path(__file__).resolve().parent
BACKUP=Path('C:/Users/nigel/ConfoSenseBackups/matched_intervals005_four_settings_20260914')
# v1 is retained as a no-fit rejected attempt: it exposed the published
# empty-group CSV representation mismatch before any owner was fitted.
BATCH=SMART/'outputs/matched_intervals005/four_settings_f2_s42_v2_coordinator'
PYTHON='C:/cfs_venv/Scripts/python.exe'
BRANCH='review/matched-intervals005-four-settings-20260914'
ENTRY='95c9e35bc81d65f08492306cb716f4c9ca7d00a6'
UNITS=(
    dict(name='pleia_energy',dataset='pleia_energy',horizons=[1,3,6],cells=30,learned_fits=51,seasonal=True),
    dict(name='pleia',dataset='pleia',horizons=[1,3,6],cells=30,learned_fits=51,seasonal=True),
    dict(name='rico',dataset='rico',horizons=[5,15,30,60],cells=40,learned_fits=68,seasonal=False),
)
sys.path.insert(0,str(SMART))
from src.intervals005_common import atomic as _atomic,append,read as _read,now,tree
from src.unit_checkpoint import digest as sha,source_digest

def design(unit):return SMART/f'protocols/matched_intervals005/{unit["name"]}_f2_s42_v{2 if unit["name"]=="pleia_energy" else 1}'
def run(unit):return SMART/f'outputs/matched_intervals005/{unit["name"]}_f2_s42_v{2 if unit["name"]=="pleia_energy" else 1}'
def auth(unit):return SMART/f'configs/matched_intervals005_remaining_{unit["name"]}_f2_s42_v1.json'
def atomic(path,value):return _atomic(path,value,BACKUP/'atomic_replace_retries.jsonl')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def read(path):
    for attempt in range(100):
        try:return _read(path)
        except (json.JSONDecodeError,PermissionError):
            if attempt==99:raise
            time.sleep(.01)
