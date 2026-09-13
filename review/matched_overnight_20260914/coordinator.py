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

def current_source():
    sys.path.insert(0,str(SMART))
    from src.unit_checkpoint import source_digest
    return source_digest()

def run_action(unit):
    return 'resume' if (Path(unit['run'])/'checkpoint_manifest.json').exists() else 'run'

def verify_frozen(manifest):
    assert current_source()==manifest['source_hash'], 'scientific source changed'
    assert sha(AUTH)==manifest['authorization_hash'] and sha(MATRIX)==manifest['matrix_hash'] and sha(QUEUE)==manifest['queue_hash']
    for u in manifest['units']:
        assert sha(Path(u['design'])/'frozen_protocol.json')==u['protocol_hash']
        assert sha(Path(u['design'])/'readiness.json')==u['readiness_hash']
        p=read(Path(u['design'])/'frozen_protocol.json')
        for name,value in p['input_hashes'].items():assert sha(SMART/name)==value

def progress(engine,manifest):
    done=[u['key'] for u in manifest['units'] if engine.state['units'].get(u['stem'],{}).get('validated')]
    pending=[u['key'] for u in manifest['units'] if u['key'] not in done]
    engine.state.update(completed_units=len(done),planned_units=12,completed_keys=done,pending_keys=pending,
       new_point_cells=3*len(done),new_interval_cells=6*len(done),saved_model_checks=6*len(done),zero_fit_resumes=len(done),
       restart_argv=[PYTHON,'-B',str(REVIEW/'coordinator.py')],full_study_ready=False)
    engine.save()
    body='# Matched overnight batch progress and restart\n\n'+f'Updated UTC: {now()}. Status: **{engine.state["status"]}**. Validated **{len(done)}/12 new paired units**; {3*len(done)} point / {6*len(done)} interval cells.\n\n'
    body+='The atomic [progress ledger](../../smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/progress.json) and [append-only attempts](../../smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/attempts.jsonl) retain exact commands, process identities, actual exits and receipt paths. A running process is not a successful exit.\n\n'
    body+='Restart from the repository with the existing environment:\n\n```powershell\n& C:/cfs_venv/Scripts/python.exe -B review/matched_overnight_20260914/coordinator.py\n```\n\n'
    body+='The coordinator refuses a concurrent launch, adopts an exact surviving logger, checks frozen identities, reuses completed model checkpoints and skips verified phases. A known failed integrity command requires investigation; this command does not bypass it. An interrupted unfinished fit has no mid-fit recovery; repeated attempts remain in the fit journal and must reconcile with the independent validator. Completed evidence is never deleted.\n\n'
    body+='| Order | Key: dataset / horizon / fold / seed | Status |\n|---|---|---|\n'
    for u in manifest['units']:body+=f'| {u["order"]} | '+ ' / '.join(map(str,u['key']))+' | '+('validated' if u['key'] in done else 'pending or active; see ledger')+' |\n'
    if engine.state.get('failure'):body+='\nFailure: `'+engine.state['failure'].replace('`','')+'`\n'
    atomic(REVIEW/'PROGRESS_AND_RESTART.md',body)
    BACKUP.mkdir(parents=True,exist_ok=True)
    atomic(BACKUP/'latest_progress.json',engine.state)

def accept(unit,engine):
    s=unit['stem'];v=engine.state['tasks'][s+'/validate'];z=engine.state['tasks'][s+'/resume']
    audit=Path(v['argv'][v['argv'].index('--receipt')+1]);rp=Path(z['argv'][z['argv'].index('--receipt')+1])
    a=read(audit/'validation.json');r=read(rp)
    for k,n in [('point_cells',3),('interval_cells',6),('real_tuning_fits_verified',8),('real_final_fits_verified',2),('saved_model_prediction_checks',6)]:assert a[k]==n
    assert a['passed'] and a['models_fitted']==0 and a['all_run_files_unchanged']
    assert r['models_fitted']==0 and r['reused_model_units']==3 and r['all_run_files_unchanged']
    assert a['protocol_hash']==unit['protocol_hash']==r['protocol_hash']
    journal=[json.loads(line) for line in (Path(unit['run'])/'fit_calls.jsonl').read_text().splitlines()]
    starts=[j for j in journal if j['event']=='started'];ends=[j for j in journal if j['event']=='complete']
    assert len(starts)==len(ends)==10, 'interrupted/repeated learned fits need explicit accounting; do not conceal them'
    return dict(validated=True,completed_utc=now(),audit=str(audit),resume=str(rp),run_files=tree(unit['run']),tuning_fits=8,final_fits=2,point_cells=3,interval_cells=6,saved_model_checks=6,zero_fit_resume=True)

def main():
    os.chdir(SMART)
    with exclusive_lock(BACKUP/'coordinator.lock'):
        manifest=read(REVIEW/'joint_pre_fit_manifest.json');engine=Engine(BATCH)
        try:
            assert git('branch','--show-current')==BRANCH
            prefit=read(REVIEW/'evaluated_commit.json')
            subprocess.run(['git','merge-base','--is-ancestor',prefit['commit'],'HEAD'],cwd=ROOT,check=True)
            verify_frozen(manifest)
            if engine.state.get('failure'):
                # Retain the prior failure. A known failed command is still
                # rejected by phase(); an actual successful orphan receipt can
                # be adopted without repeating the completed scientific run.
                previous=dict(utc=now(),failure=engine.state.pop('failure'),traceback=engine.state.pop('traceback',None))
                engine.state.setdefault('previous_failures',[]).append(previous)
                append(BATCH/'attempts.jsonl',dict(event='coordinator_restart',**previous))
            engine.reconcile()
            for unit in manifest['units']:
                s=unit['stem'];prior=engine.state['units'].get(s)
                if prior and prior.get('validated'):
                    assert tree(unit['run'])==prior['run_files'], 'completed evidence changed';continue
                verify_frozen(manifest)
                from src.pilot_resources import memory_snapshot
                resources=dict(available_ram_bytes=memory_snapshot()['available_ram_bytes'],free_disk_bytes=__import__('shutil').disk_usage(SMART).free,launch_reference_bytes=3*2**30,launch_reference_nonblocking=True)
                assert resources['free_disk_bytes']>=8*2**30, '8 GiB free-disk guard'
                append(BATCH/'resources.jsonl',dict(utc=now(),key=unit['key'],**resources))
                progress(engine,manifest)
                def run(folder):
                    action=run_action(unit)
                    return argv(unit,action,folder/'partial_resume.json' if action=='resume' else None)
                engine.phase(s+'/run',run)
                def verification(phase,folder):
                    planned=unit['commands'][phase];receipt=Path(planned[planned.index('--receipt')+1])
                    # Preserve a partial prior receipt after interruption; use a new one.
                    if receipt.exists():return argv(unit,'validate',folder/'audit') if phase=='validate' else argv(unit,'resume',folder/'resume.json')+['--forbid-fits']
                    return planned
                engine.phase(s+'/validate',lambda folder:verification('validate',folder))
                engine.phase(s+'/resume',lambda folder:verification('resume',folder))
                # Saved-stream group arithmetic is also a prerequisite to advancing.
                engine.phase(s+'/groups',lambda folder:[PYTHON,'-B',str(REVIEW/'analyze.py'),'unit','--stem',s,'--out',str(folder/'groups')])
                engine.state['units'][s]=accept(unit,engine);engine.state['status']='unit_validated';progress(engine,manifest)
                print(f'VALIDATED {unit["order"]}/12 {s}',flush=True)
                if unit['order'] in (3,6,9):
                    engine.phase(f'publication/{unit["order"]}',lambda folder:[PYTHON,'-B',str(REVIEW/'publish.py'),'--label',f'unit{unit["order"]:02d}'])
            engine.state['status']='aggregating';progress(engine,manifest)
            engine.phase('final/analysis',lambda folder:[PYTHON,'-B',str(REVIEW/'analyze.py'),'final','--out',str(BATCH/'analysis_v1')])
            engine.state['status']='science_and_reports_complete';progress(engine,manifest)
            engine.phase('final/publication',lambda folder:[PYTHON,'-B',str(REVIEW/'publish.py'),'--label','final'])
            engine.state['status']='complete';progress(engine,manifest)
            print('TWELVE UNITS AND FINAL REPORTS COMPLETE',flush=True)
        except BaseException as exc:
            engine.state.update(status='blocked',failure=str(exc),traceback=traceback.format_exc())
            progress(engine,manifest);print(engine.state['traceback'],flush=True);raise

if __name__=='__main__':main()
