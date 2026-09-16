"""No-fit guard for the one documented Windows interruption recovery path."""
import importlib.util,sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
REVIEW=ROOT/'review/pleia_energy_context005_multiseed_20260915'
sys.path.insert(0,str(REVIEW))
spec=importlib.util.spec_from_file_location('multiseed_recovery',REVIEW/'recovery.py')
recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)

def record(**updates):
    value=dict(status='failed',task='seed_44/run',exit_code=recovery.WINDOWS_INTERRUPTED_EXIT)
    value.update(updates);return value

def test_only_exact_documented_interruption_is_recoverable():
    assert recovery.eligible_interruption(record(),boot_after_attempt=True,checkpoint_exists=True,partial_exists=True)
    assert recovery.eligible_interruption(record(exit_code=1),boot_after_attempt=True,checkpoint_exists=True,partial_exists=True) is None
    assert recovery.eligible_interruption(record(task='seed_44/validate'),boot_after_attempt=True,checkpoint_exists=True,partial_exists=True) is None
    assert recovery.eligible_interruption(record(),boot_after_attempt=False,checkpoint_exists=True,partial_exists=True) is None
    assert recovery.eligible_interruption(record(),boot_after_attempt=True,checkpoint_exists=False,partial_exists=True) is None

def test_only_empty_nullable_group_analysis_keyerror_is_recoverable(tmp_path):
    analysis=tmp_path/'analysis'
    receipt={'exit_status':1,'command':['python','-B','analyze.py']}
    failed=dict(status='failed',task='final/analyze',exit_code=1,argv=receipt['command'])
    assert recovery.eligible_analysis_null_group_recovery(failed,receipt=receipt,log_text="KeyError: 'control_id'",analysis_dir=analysis)
    analysis.mkdir();(analysis/'partial.csv').write_text('preserve')
    assert recovery.eligible_analysis_null_group_recovery(failed,receipt=receipt,log_text="KeyError: 'control_id'",analysis_dir=analysis) is None

def test_only_recorded_partial_package_shadow_is_recoverable(tmp_path):
    root=tmp_path/'publication';(root/'pleia_energy_f2_s43_C_v1_publication_v1').mkdir(parents=True)
    receipt={'exit_status':1,'command':['python','-B','pack_evidence.py']}
    failed=dict(status='failed',task='final/package_raw',exit_code=1,argv=receipt['command'])
    assert recovery.eligible_package_csv_shadow_recovery(failed,receipt=receipt,log_text="AttributeError: 'function' object has no attribute 'DictWriter'",publication_root=root)
    assert recovery.eligible_package_csv_shadow_recovery(failed,receipt=receipt,log_text='different',publication_root=root) is None
    assert recovery.eligible_package_csv_shadow_recovery(failed,receipt=receipt,log_text='FileExistsError: [WinError 183] Cannot create a file when that file already exists\ndest.mkdir(parents=True)',publication_root=root)
    assert recovery.eligible_package_csv_shadow_recovery(failed,receipt=receipt,log_text="KeyError: 'COMPLETE.json'\nverify_archive",publication_root=root)
