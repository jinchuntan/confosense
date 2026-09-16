"""Narrow, auditable recovery of a Windows-interrupted checkpointed run."""
from __future__ import annotations
from pathlib import Path
import ctypes,datetime
from common import atomic,append,now,read,digest

# The logger recorded this exact Windows forced-termination exit during the
# 2026-09-15 reboot. It is not accepted generally as a scientific failure.
WINDOWS_INTERRUPTED_EXIT=1073807364

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
