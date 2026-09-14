import importlib.util,sys,json,subprocess,time
from pathlib import Path
import pytest

def module():
    root=Path(__file__).resolve().parents[2];review=root/'review/context_replay005_implementation_20260914'
    prior=sys.modules.pop('common',None);sys.path.insert(0,str(review))
    try:
        spec=importlib.util.spec_from_file_location('tested_context_coordinator',review/'coordinator.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    finally:
        sys.path.remove(str(review));sys.modules.pop('common',None)
        if prior:sys.modules['common']=prior
    return m

def test_prelaunch_rejects_missing_journal_import_before_worker(tmp_path,monkeypatch):
    m=module();e=m.Engine(tmp_path/'batch');monkeypatch.delitem(m._legacy.__dict__,'append')
    launched=[];monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:launched.append(a))
    with pytest.raises(RuntimeError,match='prelaunch missing'):e.phase('test',lambda folder:[sys.executable,'-c','print(1)'])
    assert not launched

@pytest.mark.skipif(sys.platform!='win32',reason='production coordinator Windows process identities')
def test_surviving_logger_is_adopted_once_and_passed_phase_does_not_relaunch(tmp_path):
    m=module();e=m.Engine(tmp_path/'batch',poll_seconds=.05)
    task='synthetic/adoption';folder=e.root/'attempt';folder.mkdir();log=folder/'command.log';marker=folder/'worker_count.txt'
    command=[sys.executable,'-B','-c',"from pathlib import Path; import time; p=Path(r'"+str(marker)+"'); p.write_text('one execution'); time.sleep(.6)"]
    record=dict(task=task,argv=command,log=str(log),attempt_record=str(folder/'attempt.json'),status='running')
    with (folder/'output.log').open('w') as f:
        p=subprocess.Popen([sys.executable,'-B',str(e.logger),'--log',str(log),'--',*command],cwd=e.cwd,stdout=f,stderr=subprocess.STDOUT)
        record.update(logger_identity=m._legacy.identity(p.pid),process_family=m._legacy.family(p.pid))
        e.state['active']=record;e.save()
        # A new coordinator adopts the exact existing process, as after a crash.
        adopted=m.Engine(e.root,poll_seconds=.05);adopted.reconcile();p.wait(timeout=10)
    assert adopted.state['tasks'][task]['exit_code']==0 and marker.read_text()=='one execution'
    adopted.phase(task,lambda folder:(_ for _ in ()).throw(AssertionError('duplicate launch')))
