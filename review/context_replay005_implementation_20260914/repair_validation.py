"""Explicit diagnosed recovery, preserving the completed fit and all attempts."""
import hashlib
from common import *
from src.conditional_context005 import validation_source_compatible,check_protocol

original_commit='b7ab0fd'
current={p.relative_to(SMART/'src').as_posix():sha(p) for p in sorted((SMART/'src').rglob('*.py'))}
original=current.copy()
# Unchanged legacy files have Windows CRLF working bytes; these two new files
# are explicitly -text. Reconstruct the exact historical *working* digest.
diff=git('diff',original_commit,'--name-only','--','smart_building_conformal/src').splitlines()
assert set(diff)=={'smart_building_conformal/src/conditional_context005.py','smart_building_conformal/src/context005_validate.py'},diff
for name in ['conditional_context005.py','context005_validate.py']:
    data=subprocess.check_output(['git','show',original_commit+':smart_building_conformal/src/'+name],cwd=ROOT)
    original[name]=hashlib.sha256(data).hexdigest()
changed=[n for n in original if original[n]!=current[n]]
assert set(changed)=={'conditional_context005.py','context005_validate.py'},changed
design=SMART/'protocols/conditional_context005/synthetic_pleia_energy_v1'
receipt=dict(purpose='completed_validation_and_zero_fit_resume_only',original_commit=git('rev-parse',original_commit),original_files=original,current_files=current,
    changed_files=changed,reason='Numeric missing observations in CSV are empty cells; decode only numeric comparisons, preserve group IDs. Compatibility guard applies only to completed validation/resume.',models_fitted=0)
path=design/'validation_source_compatibility.json'
if path.exists() and read(path)!=receipt:
    archive=path.with_name('validation_source_compatibility_numeric_array_v1.json')
    if not archive.exists():atomic(archive,read(path))
atomic(path,receipt)
assert validation_source_compatible(design,read(design/'frozen_protocol.json')['source_hash'])
try:check_protocol(design)
except ValueError:pass
else:raise AssertionError('compatibility must never authorize execution under a different source')
batch=SMART/'outputs/conditional_context005/synthetic_v1_coordinator';state=read(batch/'progress.json')
record=state['tasks'].get('pleia_energy/validate')
if record and record['status']=='failed':
    assert record['exit_code']==1
    atomic(batch/('failure_before_numeric_csv_repair_'+record['attempt_id']+'.json'),state)
    state['tasks']['pleia_energy/validate_failed_original_'+record['attempt_id']]=record
    del state['tasks']['pleia_energy/validate']
    state.update(status='diagnosed_validation_recovery',active=None)
    atomic(batch/'progress.json',state)
atomic(REVIEW/'VALIDATION_REPAIR_numeric_columns.json',dict(passed=True,changed_files=changed,old_run_scientific_tree=tree(SMART/'outputs/conditional_context005/synthetic_pleia_energy_v1'),models_fitted=0,preserves_all_failed_attempts=True))
print('EXACT VALIDATOR-ONLY RECOVERY PREPARED; EXECUTION COMPATIBILITY REMAINS FORBIDDEN')
