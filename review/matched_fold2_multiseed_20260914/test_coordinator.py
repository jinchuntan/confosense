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


def test_new_scope_excludes_seed42_and_keeps_all_seed_blocks():
    from common import KEYS,HORIZONS,paths,argv
    assert len(KEYS)==len(set(KEYS))==52
    for seed in (43,44,45,46):
        keys=[k for k in KEYS if k[3]==seed]
        assert [(k[0],k[1]) for k in keys]==HORIZONS and all(k[2]==2 for k in keys)
        for key in keys:
            command=argv(paths(key),'run')
            assert command[command.index('--model-seed')+1]==str(seed)
            assert f'_s{seed}_' in paths(key)['run']
    assert all(k[3]!=42 for k in KEYS)


def test_seed_path_probes_reach_numpy_torch_and_shuffle():
    from seed_checks import preflight
    result=preflight();assert result['passed'] and result['models_fitted']==0
    for row in result['rng_probes']:
        assert row['requested_seed']==row['numpy_seed']==row['torch_seed']==row['shuffle_generator_seed']


def test_wrong_actual_fit_seed_is_rejected(tmp_path):
    from seed_checks import unit
    rows=[dict(event='complete',seed=42,unit='pleia_h1_f2_s43_xgboost') for _ in range(10)]
    (tmp_path/'fit_calls.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
    with pytest.raises(AssertionError):unit(dict(key=['pleia',1,2,43],run=str(tmp_path)))


def test_signed_and_absolute_calibration_deviations_are_distinct():
    import pandas as pd
    from analyze import add_deviations,paired,FIELDS,variability
    rows=[]
    for seed in (43,44):
        for model,coverage in [('attention_lstm',.8),('xgboost',.85),('persistence',.9)]:
            row=dict(dataset='pleia',horizon=1,outer_fold=2,model_seed=seed,model=model,physical_minutes=10,target_units='degrees C',source_run='dummy',source_hash='dummy',protocol_hash='dummy',n_fit=3,n_calibration=3,n_test=3)
            row.update({field:1. for field in FIELDS});row.update(coverage90=coverage,coverage95=coverage,process_cpu_seconds=0. if model=='persistence' else 1.,mae=1. if seed==43 else 3.)
            rows.append(row)
    frame=add_deviations(pd.DataFrame(rows));pairs=paired(frame)
    r=pairs[(pairs.left_model=='attention_lstm')&(pairs.right_model=='xgboost')].iloc[0]
    assert r.signed_coverage_deviation90_difference==pytest.approx(-.05)
    assert r.absolute_coverage_deviation90_difference==pytest.approx(.05)
    p=pairs[pairs.right_model=='persistence'].iloc[0];assert p.process_cpu_seconds_ratio_status=='zero_denominator'
    v=variability(frame);r=v[(v.model=='attention_lstm')&(v.metric=='mae')].iloc[0]
    assert r['mean']==2 and r['sample_std']==pytest.approx(2**.5) and r['minimum']==1 and r['maximum']==3
