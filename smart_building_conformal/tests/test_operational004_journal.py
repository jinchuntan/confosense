import json
from pathlib import Path
import subprocess
import sys
import pytest
from src.operational004_journal import RunJournal


def test_phase_failure_record_and_no_overwrite(tmp_path):
    j=RunJournal(tmp_path/'unit')
    with pytest.raises(ValueError,match='intentional'):
        with j.phase('failed_test'): raise ValueError('intentional')
    rows=[json.loads(x) for x in j.path.read_text().splitlines()]
    assert rows[-1]['status']=='failed' and rows[-1]['seconds']>=0
    with pytest.raises(FileExistsError): RunJournal(tmp_path/'unit')


def test_frozen_configuration_mismatch_stops_before_fit(tmp_path):
    j=RunJournal(tmp_path/'unit')
    with pytest.raises(ValueError,match='resolved configuration'):
        j.freeze({'dataset':'bdg2','resolved_config':{'changed':True}},
                 {'resolved_datasets':[{'dataset':'bdg2','resolved_dataset_config':{}}]},None,None,None)
    assert not (j.root/'prefit_identity.json').exists()


def test_logger_retains_process_identity_actual_exit_and_output(tmp_path):
    log=tmp_path/'command.log'
    logger=Path(__file__).parents[1]/'scripts/log_pilot_command.py'
    cmd=[sys.executable,'-B',str(logger),'--log',str(log),'--',sys.executable,'-B','-c',
         "import sys; print('durable stdout'); print('durable stderr',file=sys.stderr); sys.exit(7)"]
    r=subprocess.run(cmd,capture_output=True,text=True)
    assert r.returncode==7
    final=json.loads(Path(str(log)+'.json').read_text())
    started=json.loads(Path(str(log)+'.started.json').read_text())
    assert final['child_pid']==started['child_pid'] and final['exit_status']==7
    assert 'durable stdout' in log.read_text() and 'durable stderr' in log.read_text()
    before=log.read_bytes()
    assert subprocess.run(cmd,capture_output=True).returncode!=0
    assert log.read_bytes()==before
