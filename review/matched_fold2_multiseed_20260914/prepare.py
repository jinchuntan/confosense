"""Freeze the exact 52-key scope and no-fit readiness before any expansion fit."""
import gc, sys, zipfile
from common import *
sys.path.insert(0,str(SMART))
from src import matched_forecasting005 as R
from src.matched_models005 import forbid_fitting
from src.unit_checkpoint import source_digest
import pandas as pd
from seed_checks import preflight

def main():
    os.chdir(SMART);assert git('branch','--show-current')==BRANCH
    assert read(BATCH/'diagnosis_v2/validation.json')['expansion_may_proceed']
    subprocess.run(['git','merge-base','--is-ancestor',ENTRY,'HEAD'],cwd=ROOT,check=True)
    BATCH.mkdir(parents=True,exist_ok=True);BACKUP.mkdir(parents=True,exist_ok=True)
    q=pd.read_csv(QUEUE,keep_default_na=False)
    scope=pd.concat([q[(q.outer_fold==2)&(q.model_seed==s)] for s in (43,44,45,46)],ignore_index=True)
    assert len(scope)==52 and not scope.duplicated(KEYCOLS).any()
    assert list(scope[KEYCOLS].itertuples(index=False,name=None))==KEYS
    scope['batch_order']=range(1,53);scope['new_authorization']=INSTRUCTION
    scope_path=REVIEW/'frozen_scope.csv'
    if scope_path.exists():pd.testing.assert_frame_equal(pd.read_csv(scope_path,keep_default_na=False),scope,check_dtype=False)
    else:scope.to_csv(scope_path,index=False)
    auth=dict(version='matched_fold2_multiseed_authorization_v1',instruction_commit=INSTRUCTION,instruction_path='review/NEXT_TASK_MATCHED_FOLD2_MULTISEED.md',entry_commit=ENTRY,real_fitting_authorized=True,allowed_units=KEYS,models=MODELS,nominal_levels=[.9,.95],real_tuning_fits=416,real_final_learned_fits=104,nonblocking_launch_ram=True,remaining_queue_authorized=False,conditional_challenge_authorized=False,resource_policy='CPU only; one numerical/Torch thread; n_jobs=1; lazy batch256; nonblocking 3 GiB launch reference; 256 MiB epoch floor; 8 GiB disk check',execution_order='seeds 43 then 44 then 45 then 46; frozen queue order within seed; advance after validation and zero-fit resume regardless of model rankings',provenance_note='Historical runner-provenance fields retained; current authorization separate.')
    if not AUTH.exists():atomic(AUTH,auth)
    auth=read(AUTH);assert auth['allowed_units']==[list(k) for k in KEYS]
    if not (REVIEW/'entry_preservation.json').exists():
        oldpaths=git('ls-tree','-r','--name-only',ENTRY).splitlines()
        atomic(REVIEW/'entry_preservation.json',dict(entry_commit=ENTRY,refs=git('for-each-ref','--format=%(refname) %(objectname)','refs/heads','refs/remotes/origin'),files=[dict(path=p,sha256=sha(ROOT/p)) for p in oldpaths]))
    probes=preflight();atomic(REVIEW/'seed_path_preflight.json',probes)
    oldledger=pd.read_csv(OLD_ANALYSIS/'evidence_reuse_ledger.csv',keep_default_na=False)
    oldledger=oldledger[oldledger.outer_fold==2]
    oldprotocols={sha(p):p for p in (SMART/'protocols/matched_forecasting005').glob('*/frozen_protocol.json')}
    baselines={(r.dataset,int(r.horizon)):read(oldprotocols[r.protocol_hash]) for r in oldledger.itertuples()}
    units=[];roles=[];same_support=[]
    for order,key in enumerate(KEYS,1):
        u=paths(key);design=Path(u['design']);assert not Path(u['run']).exists(),f'existing fit requires reconciliation: {key}'
        for action in ('freeze','readiness'):
            log=BATCH/'preflight'/f'{order:02d}_{action}.log'
            atomic(BATCH/'preflight_progress.json',dict(unit=order,key=key,phase=action,updated_utc=now(),models_fitted=0))
            if Path(str(log)+'.json').exists():
                receipt=read(str(log)+'.json');assert receipt['exit_status']==0 and receipt['command']==argv(u,action)
            else:
                assert not log.exists(),'incomplete preflight requires inspection'
                logged(argv(u,action),log)
        p=read(design/'frozen_protocol.json');ready=read(design/'readiness.json');old=baselines[key[:2]]
        assert ready['first_unit_ready'] and ready['models_fitted']==0
        assert p['support']==old['support'] and p['packages']==old['packages']
        assert p['membership_hash']==old['membership_hash'] and p['boundaries_hash']==old['boundaries_hash']
        c=json.loads(json.dumps(p['config']));c['model_seed']=42;c['xgboost_fixed']['random_state']=42
        for candidate in c['xgboost_wrapper_parameters']:candidate['random_state']=42
        assert json.dumps(c,sort_keys=True)==json.dumps(old['config'],sort_keys=True),'non-seed scientific configuration changed'
        assert p['config']['model_seed']==key[3] and all(v['random_state']==key[3] for v in p['config']['xgboost_wrapper_parameters'])
        for role,v in p['support']['roles'].items():roles.append(dict(zip(KEYCOLS,key),role=role,frequency=p['support']['frequency'],**v))
        same_support.append(dict(zip(KEYCOLS,key),baseline_model_seed=42,data_hash=p['support']['data_hash'],role_bank_hash=p['support']['role_bank_hash'],membership_hash=p['membership_hash'],boundaries_hash=p['boundaries_hash'],same_support=True,same_nonseed_config=True))
        u.update(order=order,protocol_hash=sha(design/'frozen_protocol.json'),readiness_hash=sha(design/'readiness.json'),source_hash=p['source_hash'],data_hash=p['support']['data_hash'],role_bank_hash=p['support']['role_bank_hash'],support=p['support']['roles'],commands=dict(run=argv(u,'run'),validate=argv(u,'validate',BATCH/'receipts'/u['stem']/'audit_v1'),resume=argv(u,'resume',BATCH/'receipts'/u['stem']/'resume_v1.json')+['--forbid-fits']))
        units.append(u);print(f'PREFLIGHT {order}/52 {u["stem"]}',flush=True);gc.collect()
    archive=REVIEW/'evaluated_source.zip'
    if not archive.exists():
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
            for p in sorted((SMART/'src').rglob('*.py')):z.writestr(p.relative_to(ROOT).as_posix(),p.read_bytes())
    pd.DataFrame(roles).to_csv(REVIEW/'fresh_role_support.csv',index=False)
    pd.DataFrame(same_support).to_csv(REVIEW/'cross_seed_support.csv',index=False)
    manifest=dict(passed=True,models_fitted=0,entry_commit=ENTRY,authorizing_instruction_commit=INSTRUCTION,authorizing_instruction_path='review/NEXT_TASK_MATCHED_FOLD2_MULTISEED.md',source_hash=source_digest(),source_archive_hash=sha(archive),authorization_hash=sha(AUTH),queue_hash=sha(QUEUE),matrix_hash=sha(MATRIX),scope_hash=sha(scope_path),diagnosis_hash=sha(BATCH/'diagnosis_v2/validation.json'),units=units,all_frozen_before_any_fit=True,planned_tuning_fits=416,planned_final_fits=104,scenario_low_model_hours=scope.updated_low_model_seconds.sum()/3600,scenario_high_model_hours=scope.updated_high_model_seconds.sum()/3600,nonblocking_launch_ram=True,full_study_ready=False)
    atomic(REVIEW/'joint_pre_fit_manifest.json',manifest)
    atomic(BATCH/'preflight_progress.json',dict(status='all_52_ready',models_fitted=0,updated_utc=now()))
    print('ALL 52 FROZEN AND READY; ZERO FITS',flush=True)

if __name__=='__main__':
    with forbid_fitting():main()
