"""Paths and immutable scope for the authorized PLEIA-energy C multiseed batch."""
from __future__ import annotations
import subprocess,sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
SMART=REPO/'smart_building_conformal'
REVIEW=Path(__file__).resolve().parent
PYTHON='C:/cfs_venv/Scripts/python.exe'
BRANCH='review/pleia-energy-context005-multiseed-20260915'
ENTRY='35ae9cc7f2809d1bb2dce19d4d9b6a65490100da'
MAIN='06fe967be2be8d7898812c0c2d6e464d4e942351'
SEEDS=(43,44,45,46)
ALL_SEEDS=(42,43,44,45,46)
SOURCE_HASH='a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f'
BASE=SMART/'outputs/conditional_context005'
PROTOCOLS=SMART/'protocols/conditional_context005'
BATCH=BASE/'pleia_energy_f2_context005_multiseed_v1_coordinator'
ANALYSIS=BASE/'pleia_energy_f2_context005_five_seed_analysis_v1'
BACKUP=Path('C:/Users/nigel/ConfoSenseBackups/pleia_energy_context005_multiseed_20260915')
SEED42_RUN=BASE/'pleia_energy_f2_s42_C_v1'
SEED42_DESIGN=PROTOCOLS/'pleia_energy_f2_s42_C_v1'
SEED42_BATCH=BASE/'first_real_C_v1_coordinator'

sys.path.insert(0,str(SMART))
from src.intervals005_common import atomic,append,read,now,tree,digest,source_digest,csv

def git(*args):
    return subprocess.check_output(['git',*args],cwd=REPO,text=True).strip()

def key(seed):return f'pleia_energy_f2_s{seed}_C_v1'
def manifest(seed):return REVIEW/f'{key(seed)}_execution_manifest.json'
def design(seed):return PROTOCOLS/key(seed)
def run(seed):return BASE/key(seed)
def validation(seed):return BATCH/f'seed_{seed}_validation'
def resume(seed):return BATCH/f'seed_{seed}_completed_resume.json'
def publication(seed):return BASE/f'{key(seed)}_publication_v1'
