from pathlib import Path
import subprocess,sys
REPO=Path(__file__).resolve().parents[2]; SMART=REPO/'smart_building_conformal'; REVIEW=Path(__file__).resolve().parent
PYTHON='C:/cfs_venv/Scripts/python.exe'; BRANCH='review/pleia-temperature-context005-pilot-20260918'; MAIN='06fe967be2be8d7898812c0c2d6e464d4e942351'
SOURCE_HASH='a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f'; BASE=SMART/'outputs/conditional_context005'; PROTOCOLS=SMART/'protocols/conditional_context005'
KEY='pleia_f2_s42_C_v1'; BATCH=BASE/'pleia_temperature_f2_context005_pilot_v1_coordinator'; BACKUP=Path('C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_pilot_20260918')
sys.path.insert(0,str(SMART))
from src.intervals005_common import atomic,append,read,now,tree,digest,source_digest,csv
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO,text=True).strip()
def manifest():return REVIEW/(KEY+'_execution_manifest.json')
def design():return PROTOCOLS/KEY
def run():return BASE/KEY
def validation():return BATCH/'validation'
def resume():return BATCH/'completed_resume.json'
def publication():return BASE/(KEY+'_publication_v1')
