"""Dummy-command orchestration checks: no learned fits or scientific inputs."""
import json, subprocess, sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import PYTHON, read
from coordinator import Engine, exclusive_lock, identity, alive, run_action

def factory(events,name,exit_code=0):
    code='from pathlib import Path; import sys; p=Path(sys.argv[1]); f=p.open("a"); f.write(sys.argv[2]+"\\n"); f.close(); sys.exit(int(sys.argv[3]))'
    return lambda folder:[PYTHON,'-B','-c',code,str(events),name,str(exit_code)]

def test_ordering_and_completed_restart_zero_new_commands(tmp_path):
    events=tmp_path/'events';engine=Engine(tmp_path/'batch',cwd=tmp_path,poll_seconds=.01)
    for u in (1,2):
        for phase in ('run','validate','resume'):engine.phase(f'{u}/{phase}',factory(events,f'{u}/{phase}'))
    expected=events.read_text();again=Engine(tmp_path/'batch',cwd=tmp_path,poll_seconds=.01)
    for u in (1,2):
        for phase in ('run','validate','resume'):again.phase(f'{u}/{phase}',factory(events,'MUST_NOT_RUN'))
    assert events.read_text()==expected=='1/run\n1/validate\n1/resume\n2/run\n2/validate\n2/resume\n'

def test_failure_stops_and_is_not_silently_retried(tmp_path):
    events=tmp_path/'events';engine=Engine(tmp_path/'batch',cwd=tmp_path,poll_seconds=.01)
    engine.phase('run',factory(events,'run'))
    with pytest.raises(RuntimeError,match='actual exit 7'):engine.phase('validate',factory(events,'validate',7))
    again=Engine(tmp_path/'batch',cwd=tmp_path,poll_seconds=.01)
    with pytest.raises(RuntimeError,match='Known command failure'):again.phase('validate',factory(events,'retry'))
    assert events.read_text()=='run\nvalidate\n'
    assert again.state['tasks']['validate']['exit_code']==7

def test_restart_after_run_advances_to_validation(tmp_path):
    events=tmp_path/'events';engine=Engine(tmp_path/'batch',cwd=tmp_path,poll_seconds=.01)
    engine.phase('run',factory(events,'run'))
    again=Engine(tmp_path/'batch',cwd=tmp_path,poll_seconds=.01)
    again.phase('run',factory(events,'duplicate'));again.phase('validate',factory(events,'validate'));again.phase('resume',factory(events,'resume'))
    assert events.read_text()=='run\nvalidate\nresume\n'

def test_lock_refuses_concurrent_coordinator(tmp_path):
    with exclusive_lock(tmp_path/'lock'):
        with pytest.raises(RuntimeError,match='another coordinator'):
            with exclusive_lock(tmp_path/'lock'):pass
    with exclusive_lock(tmp_path/'lock'):pass

def test_exact_process_identity_rejects_pid_reuse():
    import os
    record=identity(os.getpid());assert alive(record)
    record['created']-=1;assert not alive(record)

def test_partial_checkpoint_chooses_supported_resume(tmp_path):
    u={'run':str(tmp_path)};assert run_action(u)=='run'
    (tmp_path/'checkpoint_manifest.json').write_text('{}');assert run_action(u)=='resume'

def test_lost_coordinator_adopts_exit_receipt_without_repeating(tmp_path):
    events=tmp_path/'events';engine=Engine(tmp_path/'batch',cwd=tmp_path,poll_seconds=.01)
    done=engine.phase('run',factory(events,'run'))
    # Simulate death after the logger wrote its actual receipt, before adoption.
    engine.state['active']=dict(done,status='running');engine.state['tasks']={};engine.save()
    again=Engine(tmp_path/'batch',cwd=tmp_path,poll_seconds=.01);again.reconcile()
    again.phase('run',factory(events,'duplicate'))
    assert events.read_text()=='run\n' and again.state['tasks']['run']['exit_code']==0

def test_missing_exit_receipt_is_interrupted_not_success(tmp_path):
    from common import atomic
    engine=Engine(tmp_path/'batch',cwd=tmp_path,poll_seconds=.01);record=dict(task='run',argv=['dummy'],log=str(tmp_path/'missing'),attempt_record=str(tmp_path/'attempt.json'),logger_identity=None,worker_identity=None,status='running')
    atomic(record['attempt_record'],record);engine.state['active']=record;engine.save();engine.reconcile()
    assert engine.state['tasks']['run']['status']=='interrupted' and engine.state['tasks']['run']['exit_code'] is None

def test_adopts_live_logger_then_uses_actual_exit(tmp_path):
    from common import atomic, SMART, now
    import time
    engine=Engine(tmp_path/'batch',cwd=tmp_path,poll_seconds=.01)
    folder=tmp_path/'attempt';folder.mkdir();log=folder/'command.log'
    command=[PYTHON,'-B','-c','import time; time.sleep(0.3); print("dummy complete")']
    process=subprocess.Popen([PYTHON,'-B',str(SMART/'scripts/log_pilot_command.py'),'--log',str(log),'--',*command],cwd=tmp_path,stdout=subprocess.DEVNULL)
    record=dict(task='live',argv=command,log=str(log),attempt_record=str(folder/'attempt.json'),logger_identity=identity(process.pid),status='running',started_utc=now())
    atomic(record['attempt_record'],record);engine.state['active']=record;engine.save()
    engine.reconcile();process.wait()
    assert engine.state['tasks']['live']['exit_code']==0 and engine.state['tasks']['live']['status']=='passed'

def test_atomic_replace_retries_transient_denial_without_changing_old_data(tmp_path,monkeypatch):
    import common
    target=tmp_path/'progress.json';target.write_text('{"old":true}')
    original=common.os.replace;calls=[]
    monkeypatch.setattr(common,'BACKUP',tmp_path/'trace')
    monkeypatch.setattr(common.time,'sleep',lambda _:None)
    def denied_twice(src,dst):
        calls.append(1)
        if len(calls)<=2:
            assert target.read_text()=='{"old":true}'
            raise PermissionError('injected transient sharing denial')
        original(src,dst)
    monkeypatch.setattr(common.os,'replace',denied_twice)
    common.atomic(target,{'new':True})
    assert read(target)=={'new':True} and len(calls)==3
    assert len((tmp_path/'trace/atomic_replace_retries.jsonl').read_text().splitlines())==2

def test_atomic_replace_persistent_denial_stops_and_preserves_both_versions(tmp_path,monkeypatch):
    import common
    target=tmp_path/'progress.json';target.write_text('{"old":true}');calls=[]
    monkeypatch.setattr(common,'BACKUP',tmp_path/'trace');monkeypatch.setattr(common.time,'sleep',lambda _:None)
    def denied(src,dst):calls.append(1);raise PermissionError('injected persistent denial')
    monkeypatch.setattr(common.os,'replace',denied)
    with pytest.raises(PermissionError):common.atomic(target,{'new':True})
    assert len(calls)==11 and read(target)=={'old':True}
    retained=list(tmp_path.glob('progress.json.*.tmp'));assert len(retained)==1 and read(retained[0])=={'new':True}
