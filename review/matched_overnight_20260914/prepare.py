"""Freeze and check all twelve units before any real fit; preserve source bytes."""
import gc, json, os, subprocess, sys, zipfile
from pathlib import Path
from common import *
sys.path.insert(0,str(SMART))
from src import matched_forecasting005 as R
from src.matched_models005 import forbid_fitting
from src.unit_checkpoint import source_digest
import pandas as pd

def main():
    os.chdir(SMART)
    assert git('branch','--show-current')==BRANCH
    subprocess.run(['git','merge-base','--is-ancestor',ENTRY,'HEAD'],cwd=ROOT,check=True)
    BATCH.mkdir(parents=True,exist_ok=True);BACKUP.mkdir(parents=True,exist_ok=True)
    q=pd.read_csv(QUEUE,keep_default_na=False)
    assert [tuple(row) for row in q[KEYCOLS].itertuples(index=False,name=None)]==KEYS
    auth=dict(version='matched_overnight_authorization_v1',instruction_commit=INSTRUCTION,instruction_path='review/NEXT_TASK_MATCHED_OVERNIGHT_BATCH.md',entry_commit=git('rev-parse','HEAD'),real_fitting_authorized=True,allowed_units=KEYS,models=MODELS,nominal_levels=[.9,.95],real_tuning_fits=96,real_final_learned_fits=24,nonblocking_launch_ram=True,remaining_queue_authorized=False,conditional_challenge_authorized=False,resource_policy='CPU only; one numerical/Torch thread; n_jobs=1; lazy batch256; nonblocking 3 GiB launch reference; 256 MiB epoch floor; 8 GiB disk check',execution_order='exact listed order; advance only after independent validation and zero-fit resume; never select by test metrics',provenance_note='Historical runner design constants retain their original meaning; this authorization binds the current instruction separately.')
    if not AUTH.exists():atomic(AUTH,auth)
    auth=read(AUTH)  # JSON lists are the runner's explicit authorization representation.
    assert auth['allowed_units']==[list(k) for k in KEYS]
    handed=subprocess.check_output(['git','show',INSTRUCTION+':review/NEXT_TASK_MATCHED_OVERNIGHT_BATCH.md'],cwd=ROOT)
    (REVIEW/'AUTHORIZING_HANDOFF.md').write_bytes(handed)
    oldpaths=git('ls-tree','-r','--name-only',ENTRY).splitlines()
    if not (REVIEW/'entry_preservation.json').exists():
        atomic(REVIEW/'entry_preservation.json',dict(entry_commit=ENTRY,files=[dict(path=p,sha256=sha(ROOT/p)) for p in oldpaths]))
    units=[];roles=[]
    for i,key in enumerate(KEYS,1):
        unit=paths(key);design=Path(unit['design']);run=Path(unit['run'])
        assert not run.exists(), f'existing fitting work requires reconciliation: {key}'
        for action in ('freeze','readiness'):
            log=BATCH/'preflight'/f'{i:02d}_{action}.log'
            atomic(BATCH/'preflight_progress.json',dict(unit=i,key=key,phase=action,updated_utc=now(),models_fitted=0))
            if Path(str(log)+'.json').exists():
                receipt=read(str(log)+'.json')
                assert receipt['exit_status']==0 and receipt['command']==argv(unit,action)
            else:
                assert not log.exists(), 'incomplete preflight command needs inspection'
                logged(argv(unit,action),log)
        p=read(design/'frozen_protocol.json');ready=read(design/'readiness.json')
        assert ready['first_unit_ready'] and ready['models_fitted']==0
        selected=R.select_matrix(MATRIX,key,auth).iloc[0]
        for role,column in [('fit','fit_n'),('calibration','calibration_n'),('test','test_n')]:
            assert p['support']['roles'][role]['n']==int(selected[column])
        # The frozen ordered memberships and integrity checks include both inner folds.
        member=pd.read_csv(design/'membership.csv.gz',dtype={'row_id':str,'group_id':str},keep_default_na=False,float_precision='round_trip')
        for role,part in member.groupby('role',sort=False):
            roles.append(dict(zip(KEYCOLS,key),role=role,groups=part.group_id.nunique(),frequency=p['support']['frequency'],**p['support']['roles'][role]))
        unit.update(order=i,protocol_hash=sha(design/'frozen_protocol.json'),readiness_hash=sha(design/'readiness.json'),source_hash=p['source_hash'],data_hash=p['support']['data_hash'],role_bank_hash=p['support']['role_bank_hash'],support=p['support']['roles'],commands=dict(run=argv(unit,'run'),validate=argv(unit,'validate',BATCH/'receipts'/unit['stem']/'audit_v1'),resume=argv(unit,'resume',BATCH/'receipts'/unit['stem']/'resume_v1.json')+['--forbid-fits']))
        units.append(unit);gc.collect()
    with zipfile.ZipFile(REVIEW/'evaluated_source.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((SMART/'src').rglob('*.py')):z.writestr(p.relative_to(ROOT).as_posix(),p.read_bytes())
    pd.DataFrame(roles).to_csv(REVIEW/'fresh_role_support.csv',index=False)
    manifest=dict(passed=True,models_fitted=0,entry_commit=ENTRY,authorizing_instruction_commit=INSTRUCTION,authorizing_instruction_path='review/NEXT_TASK_MATCHED_OVERNIGHT_BATCH.md',source_hash=source_digest(),source_archive_hash=sha(REVIEW/'evaluated_source.zip'),authorization_hash=sha(AUTH),queue_hash=sha(QUEUE),matrix_hash=sha(MATRIX),units=units,all_frozen_before_any_fit=True,planned_tuning_fits=96,planned_final_fits=24,nonblocking_launch_ram=True,full_study_ready=False)
    atomic(REVIEW/'joint_pre_fit_manifest.json',manifest)
    atomic(BATCH/'preflight_progress.json',dict(status='all_twelve_ready',models_fitted=0,updated_utc=now()))
    print('ALL TWELVE FROZEN AND READY; ZERO FITS',flush=True)

if __name__=='__main__':
    with forbid_fitting():main()
