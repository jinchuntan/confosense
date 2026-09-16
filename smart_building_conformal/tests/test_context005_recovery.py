"""No-fit guard for the one documented Windows interruption recovery path."""
import importlib.util,sys
from pathlib import Path

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
