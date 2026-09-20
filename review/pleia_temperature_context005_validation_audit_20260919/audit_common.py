"""Shared paths for the temperature validation audit. No scientific side effects."""
from pathlib import Path
import subprocess, sys

REPO = Path(__file__).resolve().parents[2]
SMART = REPO / 'smart_building_conformal'
AUDIT_REVIEW = Path(__file__).resolve().parent
PILOT_REVIEW = REPO / 'review/pleia_temperature_context005_pilot_20260918'
PYTHON = 'C:/cfs_venv/Scripts/python.exe'
AUDIT_BRANCH = 'review/pleia-temperature-context005-validation-audit-20260919'
PILOT_BRANCH = 'review/pleia-temperature-context005-pilot-20260918'
MAIN = '06fe967be2be8d7898812c0c2d6e464d4e942351'
PRIMARY = '31fdacbb29ef70bbb297cfe52d9fbf91fb789038'
DELIVERY = '571408be0b51e81c6987306a292afc7fcae2ff94'
SOURCE_HASH = 'a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f'

KEY = 'pleia_f2_s42_C_v1'
BASE = SMART / 'outputs/conditional_context005'
RUN = BASE / KEY
DESIGN = SMART / 'protocols/conditional_context005' / KEY
COORD = BASE / 'pleia_temperature_f2_context005_pilot_v1_coordinator'
OUT = BASE / (KEY + '_validation_audit')
BACKUP = Path('C:/Users/nigel/ConfoSenseBackups/pleia_temperature_context005_validation_audit_20260919')

sys.path.insert(0, str(SMART))


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()
