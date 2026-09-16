"""Narrow, auditable recovery of a Windows-interrupted checkpointed run."""
from __future__ import annotations
from pathlib import Path
import ctypes,datetime
from common import atomic,append,now,read,digest

# The logger recorded this exact Windows forced-termination exit during the
# 2026-09-15 reboot. It is not accepted generally as a scientific failure.
WINDOWS_INTERRUPTED_EXIT=1073807364
ANALYSIS_NULL_GROUP_KEYERROR="KeyError: 'control_id'"
PACKAGE_CSV_SHADOW_ERROR="AttributeError: 'function' object has no attribute 'DictWriter'"

def windows_boot_utc():
    """Use the Windows monotonic boot clock; no optional package dependency."""
    ticks=ctypes.windll.kernel32.GetTickCount64()
    return datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(milliseconds=ticks)

def eligible_interruption(record, *, boot_after_attempt, checkpoint_exists, partial_exists):
    """Return a reason only for the single documented recoverable condition."""
    if record.get('status')!='failed': return None
    if not str(record.get('task','')).endswith('/run'): return None
    if record.get('exit_code')!=WINDOWS_INTERRUPTED_EXIT: return None
    if not boot_after_attempt or not checkpoint_exists or not partial_exists: return None
    return 'verified_nonzero_windows_interruption_with_checkpointed_run'

def reclassify(engine, *, task, boot_after_attempt, run_path):
    """Preserve the original nonzero receipt and let Engine.phase use --resume-incomplete."""
    record=engine.state['tasks'].get(task)
    reason=eligible_interruption(record or {},boot_after_attempt=boot_after_attempt,
        checkpoint_exists=(Path(run_path)/'checkpoint_manifest.json').exists(),
        partial_exists=any(Path(run_path).glob('.partial_*')))
    if not reason:return False
    receipt=Path(record['logger_receipt'])
    logged=read(receipt)
    if logged['exit_status']!=WINDOWS_INTERRUPTED_EXIT or logged['command']!=record['argv']:
        raise ValueError('interruption receipt mismatch')
    record.update(status='interrupted',reason=reason,reclassified_utc=now(),
        recovery_evidence=dict(exit_status=logged['exit_status'],receipt=str(receipt),
            checkpoint_manifest_sha256=digest(Path(run_path)/'checkpoint_manifest.json'),
            partial_directories=sorted(p.name for p in Path(run_path).glob('.partial_*'))))
    atomic(record['attempt_record'],record)
    append(engine.root/'attempts.jsonl',dict(event='reclassified_interrupted_after_verified_reboot',**record))
    engine.state['tasks'][task]=record;engine.save()
    return True

def eligible_analysis_null_group_recovery(record, *, receipt, log_text, analysis_dir):
    """Recognize only the observed empty-output aggregate-analysis defect.

    The failed command must be the fixed analysis entrypoint, its logger
    receipt must agree, the exact pandas KeyError must be present, and no
    completed or partial aggregate artifact may be overwritten.
    """
    if record.get('status')!='failed' or record.get('task')!='final/analyze':return None
    if record.get('exit_code')!=1 or receipt.get('exit_status')!=1:return None
    command=record.get('argv',[])
    if not command or Path(command[-1]).name!='analyze.py' or receipt.get('command')!=command:return None
    path=Path(analysis_dir)
    if path.exists() and any(path.iterdir()):return None
    if ANALYSIS_NULL_GROUP_KEYERROR not in log_text:return None
    return 'verified_nullable_group_id_analysis_keyerror_with_empty_output'

def eligible_package_csv_shadow_recovery(record, *, receipt, log_text, publication_root):
    """Recognize only the observed package-module shadowing failure."""
    if record.get('status')!='failed' or record.get('task')!='final/package_raw':return None
    if record.get('exit_code')!=1 or receipt.get('exit_status')!=1:return None
    command=record.get('argv',[])
    if not command or Path(command[-1]).name!='pack_evidence.py' or receipt.get('command')!=command:return None
    root=Path(publication_root)
    if not (root/'pleia_energy_f2_s43_C_v1_publication_v1').exists():return None
    if PACKAGE_CSV_SHADOW_ERROR not in log_text:return None
    return 'verified_package_csv_module_shadow_with_partial_archives'
