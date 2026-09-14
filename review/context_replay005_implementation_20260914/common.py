import sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SMART=ROOT/'smart_building_conformal';REVIEW=Path(__file__).resolve().parent
PYTHON='C:/cfs_venv/Scripts/python.exe'
BACKUP=Path('C:/Users/nigel/ConfoSenseBackups/context_replay005_implementation_20260914')
BRANCH='review/context-replay005-implementation-20260914'
ENTRY='236180a953f2a268f37e1a6d68a4ccd2eb7954b5'
sys.path.insert(0,str(SMART))
from src.intervals005_common import atomic,append,read,now,tree,source_digest,digest as sha,signature
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
