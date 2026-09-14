"""Durable serial CLI coordinator, with immutable attempts and restart reconciliation.

The scientific runner is unchanged. A failed integrity command halts; there is no
automatic retry of a known failure. A killed coordinator can adopt its surviving
logger and recover the logger's actual exit receipt before advancing.
"""
import argparse, contextlib, json, os, subprocess, sys, time, traceback, uuid
from pathlib import Path
from common import *

def identity(pid):
    # Standard-library Windows APIs: no new environment dependencies.
    import ctypes
    from ctypes import wintypes as W
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.CloseHandle.argtypes=[W.HANDLE]
    k.GetProcessTimes.argtypes=[W.HANDLE,*([ctypes.POINTER(W.FILETIME)]*4)]
    k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
    k.GetExitCodeProcess.argtypes=[W.HANDLE,ctypes.POINTER(W.DWORD)]
    handle=k.OpenProcess(0x1000,False,pid)
    if not handle:return None
    try:
        code=W.DWORD();assert k.GetExitCodeProcess(handle,ctypes.byref(code))
        if code.value!=259:return None
        times=[W.FILETIME() for _ in range(4)]
        assert k.GetProcessTimes(handle,*[ctypes.byref(t) for t in times])
        size=W.DWORD(32768);name=ctypes.create_unicode_buffer(size.value)
        assert k.QueryFullProcessImageNameW(handle,0,name,ctypes.byref(size))
        return dict(pid=pid,created=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime,executable=name.value)
    finally:k.CloseHandle(handle)

def alive(record):
    current=identity(record['pid']) if record else None
    return bool(current and current['created']==record['created'] and current['executable']==record['executable'])

def family(pid):
    """Include Windows venv shims and their real Python worker descendants."""
    import ctypes
    from ctypes import wintypes as W
    class Entry(ctypes.Structure):
        _fields_=[('size',W.DWORD),('usage',W.DWORD),('pid',W.DWORD),('heap',ctypes.c_size_t),('module',W.DWORD),('threads',W.DWORD),('parent',W.DWORD),('priority',W.LONG),('flags',W.DWORD),('exe',W.WCHAR*260)]
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];k.CreateToolhelp32Snapshot.restype=W.HANDLE
    k.Process32FirstW.argtypes=[W.HANDLE,ctypes.POINTER(Entry)];k.Process32NextW.argtypes=k.Process32FirstW.argtypes;k.CloseHandle.argtypes=[W.HANDLE]
    handle=k.CreateToolhelp32Snapshot(2,0);assert handle!=ctypes.c_void_p(-1).value
    rows=[];entry=Entry();entry.size=ctypes.sizeof(entry)
    try:
        more=k.Process32FirstW(handle,ctypes.byref(entry))
        while more:
            rows.append((entry.pid,entry.parent));more=k.Process32NextW(handle,ctypes.byref(entry))
    finally:k.CloseHandle(handle)
    pids={pid}
    for _ in range(len(rows)):
        more={child for child,parent in rows if parent in pids}
        if more<=pids:break
        pids|=more
    return [record for child in pids if (record:=identity(child))]

@contextlib.contextmanager
def exclusive_lock(path):
    import msvcrt
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    f=path.open('a+b')
    if os.fstat(f.fileno()).st_size==0:f.write(b'0');f.flush()
    f.seek(0)
    try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:
        f.close();raise RuntimeError('another coordinator holds this batch lock')
    try:yield
    finally:
        f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1);f.close()

class Engine:
    def __init__(self,directory,cwd=SMART,logger=None,poll_seconds=2):
        self.root=Path(directory);self.cwd=Path(cwd);self.poll_seconds=poll_seconds
        self.logger=Path(logger or SMART/'scripts/log_pilot_command.py')
        self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'progress.json'
        self.state=read(self.path) if self.path.exists() else dict(version=1,started_utc=now(),tasks={},units={},status='prepared',active=None)
    def save(self):
        self.state['updated_utc']=now();atomic(self.path,self.state)
    def finish(self,record):
        receipt=Path(record['log']+'.json')
        if not receipt.exists():
            record.update(status='interrupted',ended_utc=now(),exit_code=None,reason='logger is no longer live and no actual exit receipt exists')
        else:
            actual=read(receipt)
            assert actual['command']==record['argv'] and Path(actual['cwd']).resolve()==self.cwd.resolve()
            record.update(status='passed' if actual['exit_status']==0 else 'failed',ended_utc=actual['ended_utc'],exit_code=actual['exit_status'],logger_receipt=str(receipt),seconds=actual['seconds'],child_pid=actual['child_pid'])
        atomic(record['attempt_record'],record)
        append(self.root/'attempts.jsonl',dict(event='finished',**record))
        self.state['tasks'][record['task']]=record
        self.state['active']=None;self.save()
        return record
    def reconcile(self):
        record=self.state.get('active')
        if not record:return
        while alive(record.get('logger_identity')) or any(alive(p) for p in record.get('process_family',[])):
            self.state['status']='adopting_surviving_logger';self.save();time.sleep(self.poll_seconds)
        # On Windows the launcher can exit while its worker still survives. Do not
        # create a duplicate while any exact recorded worker identity is alive.
        while alive(record.get('worker_identity')):
            self.state['status']='waiting_for_surviving_worker';self.save();time.sleep(self.poll_seconds)
        self.finish(record)
    def phase(self,task,command_factory):
        self.reconcile()
        previous=self.state['tasks'].get(task)
        if previous and previous['status']=='passed':return previous
        if previous and previous['status']=='failed':
            raise RuntimeError(f'Known command failure requires investigation; no automatic retry: {task}; {previous["log"]}')
        aid=now().replace(':','').replace('.','')+'_'+uuid.uuid4().hex[:8]
        folder=self.root/'attempts'/aid;folder.mkdir(parents=True)
        command=command_factory(folder)
        record=dict(task=task,attempt_id=aid,argv=command,cwd=str(self.cwd),started_utc=now(),ended_utc=None,exit_code=None,status='launching',log=str(folder/'command.log'),attempt_record=str(folder/'attempt.json'),previous_attempt=previous.get('attempt_id') if previous else None)
        atomic(record['attempt_record'],record)
        self.state.update(active=record,status='running');self.save()
        wrapped=[PYTHON,'-B',str(self.logger),'--log',record['log'],'--',*command]
        with (folder/'logger.stdout.log').open('x',encoding='utf-8') as out:
            process=subprocess.Popen(wrapped,cwd=self.cwd,stdout=out,stderr=subprocess.STDOUT)
            record.update(status='running',logger_identity=identity(process.pid),logger_pid=process.pid,process_family=family(process.pid))
            append(self.root/'attempts.jsonl',dict(event='started',**record))
            self.state['active']=record;self.save();atomic(record['attempt_record'],record)
            while process.poll() is None:
                if task.startswith('publication/') or task=='final/publication':
                    # Keep the published progress snapshot stable while git stages it.
                    time.sleep(self.poll_seconds);continue
                started=Path(record['log']+'.started.json')
                if started.exists() and not record.get('worker_identity'):
                    child=read(started);record['worker_identity']=identity(child['child_pid'])
                    atomic(record['attempt_record'],record)
                record['process_family']=family(process.pid)
                self.state['active']=record;self.save();time.sleep(self.poll_seconds)
        result=self.finish(record)
        if result['status']!='passed':raise RuntimeError(f'phase {task} {result["status"]}; actual exit {result["exit_code"]}; {result["log"]}')
        return result


def run_action(unit):
    return 'resume' if (Path(unit['run'])/'checkpoint_manifest.json').exists() else 'run'


def progress(engine):
    stages=sorted(p.name for p in (RUN/'stages').glob('*') if (p/'COMPLETE.json').exists())
    engine.state.update(completed_scientific_stages=stages,run_directory=str(RUN),restart_argv=[PYTHON,'-B',str(REVIEW/'coordinator.py')],full_study_ready=False)
    engine.save();atomic(BACKUP/'latest_progress.json',engine.state)
    text='# Matched intervals005 durable progress and restart\n\n'
    text+=f'Updated UTC: {now()}. Status: **{engine.state["status"]}**. {len(stages)} scientific stages checkpointed; acceptance requires the completed independent validation and forbidden-fit resume receipts.\n\n'
    text+='The [atomic progress ledger](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/progress.json), [immutable command attempts](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/attempts.jsonl), and [scientific stage journal](../../smart_building_conformal/outputs/matched_intervals005/bdg2_f2_s42_v1/stage_journal.jsonl) retain owner/calibrator/stream and live process identities.\n\n'
    text+='Restart the sole coordinator from the repository using:\n\n```powershell\n& C:/cfs_venv/Scripts/python.exe -B review/matched_intervals005_bdg2_20260914/coordinator.py\n```\n\nThe exclusive OS lock prevents duplicate coordinators. A surviving exact logger/worker is adopted. Known failed commands require investigation, not a blind retry. Completed fitted stages are hash-verified and reused; incomplete fit stages require explicit reconciliation. An unavailable chat callback does not interrupt the detached coordinator.\n\n'
    for name,record in engine.state['tasks'].items():text+=f'- {name}: {record["status"]}; actual exit {record.get("exit_code")}; receipt `{record.get("logger_receipt",record["log"])}`.\n'
    if engine.state.get('failure'):text+='\nFailure: '+engine.state['failure']+'\n'
    atomic(REVIEW/'PROGRESS_AND_RESTART.md',text)


def main():
    os.chdir(SMART)
    with exclusive_lock(BACKUP/'coordinator.lock'):
        engine=Engine(BATCH)
        try:
            assert git('branch','--show-current')==BRANCH
            frozen=read(REVIEW/'joint_pre_fit_manifest.json');evaluated=read(REVIEW/'evaluated_commit.json')
            subprocess.run(['git','merge-base','--is-ancestor',evaluated['commit'],'HEAD'],cwd=ROOT,check=True)
            from src.unit_checkpoint import source_digest
            recovery_path=REVIEW/('VALIDATION_RECOVERY_COMMANDS_V3.json' if (REVIEW/'VALIDATION_RECOVERY_COMMANDS_V3.json').exists() else 'VALIDATION_RECOVERY_COMMANDS.json')
            recovery=read(recovery_path) if recovery_path.exists() else None
            audit_path=Path(recovery.get('audit_manifest',str(REVIEW/'VALIDATION_ERRATUM.json'))) if recovery else None
            if recovery:
                from src.matched_intervals005 import check_protocol
                check_protocol(DESIGN/'frozen_protocol.json',audit_path)
                assert recovery['audit_manifest_sha256']==sha(audit_path)
                assert recovery['source_hash']==source_digest()
                assert engine.state['tasks']['pilot/run']['status']=='passed'
                assert read(RUN/'COMPLETE.json')['status']=='complete'
                assert read(recovery['regression_receipt'])['exit_status']==0
                if engine.state.get('failure'):
                    engine.state.setdefault('prior_failures',[]).append(dict(failure=engine.state.pop('failure'),traceback=engine.state.pop('traceback',None),recovery_manifest=str(recovery_path)))
                engine.state['status']='recovering_validation'
            else:assert source_digest()==frozen['source_hash']
            assert sha(DESIGN/'frozen_protocol.json')==frozen['protocol_hash']
            engine.reconcile();progress(engine)
            def real_run(folder):
                argv=frozen['commands']['run'].copy()
                if (RUN/'checkpoint_manifest.json').exists():argv[argv.index('run')]='resume'
                return argv
            engine.phase('pilot/run',real_run);progress(engine)
            engine.phase(recovery.get('validation_task','pilot/validate_v2') if recovery else 'pilot/validate',lambda folder:recovery['commands']['validate'] if recovery else frozen['commands']['validate']);progress(engine)
            engine.phase('pilot/resume',lambda folder:recovery['commands']['resume'] if recovery else frozen['commands']['resume']);progress(engine)
            validation=read(Path(recovery.get('validation_directory',str(BATCH/'validation_v2')))/'validation.json') if recovery else read(BATCH/'validation_v1/validation.json');resume=read(BATCH/'completed_resume_v1.json')
            assert validation['passed'] and validation['method_cells']==30 and validation['alert_stream_checks']==30
            assert validation['models_fitted']==validation['calibrators_fitted']==0
            assert resume['models_fitted']==resume['calibrators_fitted']==0 and resume['all_run_files_unchanged']
            engine.state['status']='science_validated';progress(engine)
            engine.phase('final/report',lambda folder:[PYTHON,'-B',str(REVIEW/'report.py'),'--out',str(BATCH/'analysis_v1')])
            engine.state['status']='reports_complete';progress(engine)
            engine.phase('final/publication',lambda folder:[PYTHON,'-B',str(REVIEW/'publish.py'),'--label','completed'])
            engine.state['status']='complete';progress(engine)
            print('ALL AUTHORIZED INTERVAL, SEASONAL, ALERT, VALIDATION AND REPORT STAGES COMPLETE',flush=True)
        except BaseException as exc:
            engine.state.update(status='blocked',failure=str(exc),traceback=traceback.format_exc());progress(engine);raise


if __name__=='__main__':main()

