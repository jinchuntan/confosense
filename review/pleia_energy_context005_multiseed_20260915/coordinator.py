"""Durable sequential coordinator for the four authorized real C units."""
from __future__ import annotations
import argparse,importlib.util,json,os,shutil,subprocess,sys,traceback
from common import *
from recovery import reclassify,windows_boot_utc,eligible_analysis_null_group_recovery,eligible_package_csv_shadow_recovery

# Reuse the already reviewed adoption/identity engine without copying it.
LEGACY_DIR=REPO/'review/context_replay005_implementation_20260914'
sys.path.insert(0,str(LEGACY_DIR))
current_common=sys.modules.get('common')
common_spec=importlib.util.spec_from_file_location('context005_reviewed_common',LEGACY_DIR/'common.py')
legacy_common=importlib.util.module_from_spec(common_spec);common_spec.loader.exec_module(legacy_common)
sys.modules['common']=legacy_common
spec=importlib.util.spec_from_file_location('context005_reviewed_coordinator',LEGACY_DIR/'coordinator.py')
reviewed=importlib.util.module_from_spec(spec);spec.loader.exec_module(reviewed)
if current_common is not None:sys.modules['common']=current_common
else:sys.modules.pop('common',None)
Engine=reviewed.Engine;exclusive_lock=reviewed._legacy.exclusive_lock

def save_external(engine):
    BACKUP.mkdir(parents=True,exist_ok=True)
    atomic(BACKUP/'latest_progress.json',engine.state)
    lines=['# Durable progress and restart','',f'Updated UTC: {now()}. Status: **{engine.state.get("status")}**.','',
        'Restart the sole coordinator from the repository root:','',
        '```powershell','& C:/cfs_venv/Scripts/python.exe -B review/pleia_energy_context005_multiseed_20260915/coordinator.py','```','',
        'The exclusive lock prevents duplicate coordinators. An exact surviving logger or worker is adopted. Passed tasks are reused; known failed commands require investigation.','']
    for task,row in engine.state.get('tasks',{}).items():lines.append(f'- {task}: {row.get("status")}; actual exit {row.get("exit_code")}; receipt `{row.get("logger_receipt",row.get("log"))}`.')
    if engine.state.get('failure'):lines+=['',f'Failure: {engine.state["failure"]}']
    atomic(REVIEW/'PROGRESS_AND_RESTART.md','\n'.join(lines)+'\n')

def argv(seed,action):
    receipt=validation(seed) if action=='validate' else resume(seed) if action=='resume' else design(seed)/'readiness.json'
    out=[PYTHON,'-B','-m','src.conditional_context005',action,'--manifest',str(manifest(seed)),'--design',str(design(seed)),
         '--out',str(run(seed)),'--readiness',str(design(seed)/'readiness.json'),'--receipt',str(receipt)]
    if action=='run' and (run(seed)/'checkpoint_manifest.json').exists():out+=['--resume-incomplete']
    return out

def disk_gate():
    free=shutil.disk_usage(REPO).free
    if free<8*2**30:raise RuntimeError(f'disk floor failed: {free} bytes free')
    return free

def recover_empty_analysis_keyerror(engine):
    """Archive and retry only the receipt-bound aggregate-analysis defect."""
    task='final/analyze';record=engine.state['tasks'].get(task)
    if not record or record.get('status')!='failed':return False
    receipt=read(record['logger_receipt']);log_text=Path(record['log']).read_text(encoding='utf-8',errors='replace')
    reason=eligible_analysis_null_group_recovery(record,receipt=receipt,log_text=log_text,analysis_dir=ANALYSIS)
    if not reason:return False
    archived=ANALYSIS.with_name(ANALYSIS.name+'_failed_nullable_group_20260916')
    if ANALYSIS.exists():
        if archived.exists():raise ValueError('failed analysis archive already exists')
        shutil.move(str(ANALYSIS),str(archived))
    prior=dict(task=task,reason=reason,failed_record=record,archived_empty_analysis_directory=str(archived),recovered_utc=now())
    if engine.state.get('failure'):prior['failure']=engine.state.pop('failure')
    if engine.state.get('traceback'):prior['traceback']=engine.state.pop('traceback')
    engine.state.setdefault('prior_failures',[]).append(prior)
    engine.state['tasks'].pop(task)
    engine.state.update(status='analysis_recovery',active=None)
    append(engine.root/'attempts.jsonl',dict(event='reclassified_analysis_failure_after_verified_empty_output',**prior))
    engine.save()
    return True

def recover_partial_package_csv_shadow(engine):
    """Retry packaging only after validating its exact exited receipt."""
    task='final/package_raw';record=engine.state['tasks'].get(task)
    if not record or record.get('status')!='failed':return False
    receipt=read(record['logger_receipt']);log_text=Path(record['log']).read_text(encoding='utf-8',errors='replace')
    reason=eligible_package_csv_shadow_recovery(record,receipt=receipt,log_text=log_text,publication_root=BASE)
    if not reason:return False
    prior=dict(task=task,reason=reason,failed_record=record,reused_partial_archives=str(publication(43)),recovered_utc=now())
    if engine.state.get('failure'):prior['failure']=engine.state.pop('failure')
    if engine.state.get('traceback'):prior['traceback']=engine.state.pop('traceback')
    engine.state.setdefault('prior_failures',[]).append(prior)
    engine.state['tasks'].pop(task)
    engine.state.update(status='package_recovery',active=None)
    append(engine.root/'attempts.jsonl',dict(event='reclassified_package_failure_after_verified_partial_archives',**prior))
    engine.save()
    return True

def main(freeze_only=False):
    os.chdir(SMART);BACKUP.mkdir(parents=True,exist_ok=True)
    with exclusive_lock(BACKUP/'coordinator.lock'):
        engine=Engine(BATCH,poll_seconds=2)
        try:
            if git('branch','--show-current')!=BRANCH:raise ValueError('wrong review branch')
            if git('rev-parse','main')!=MAIN:raise ValueError('main changed')
            if source_digest()!=SOURCE_HASH:raise ValueError('scientific source changed')
            for name in ['append','atomic','read','now','identity','family','alive']:
                if not callable(reviewed._legacy.__dict__.get(name)):raise RuntimeError('prelaunch missing coordinator helper: '+name)
            subprocess.run([PYTHON,'-B','-c','import src.conditional_context005,src.context005_validate,src.context005_metrics'],cwd=SMART,check=True)
            engine.reconcile()
            # A reboot produced a logged nonzero Windows interruption for the
            # seed-44 run. Only the hash-bound recovery helper can turn that
            # exact receipt into a resumable checkpoint; all other failures
            # remain terminal and require investigation.
            if engine.state['tasks'].get('seed_44/run',{}).get('status')=='failed':
                attempt=engine.state['tasks']['seed_44/run']
                ended=__import__('datetime').datetime.fromisoformat(attempt['ended_utc'])
                boot=windows_boot_utc()
                reclassify(engine,task='seed_44/run',boot_after_attempt=boot>ended,run_path=run(44))
            recover_empty_analysis_keyerror(engine)
            recover_partial_package_csv_shadow(engine)
            save_external(engine)
            # Freeze every seed before any fit.
            for seed in SEEDS:
                if not design(seed).exists():engine.phase(f'seed_{seed}/freeze',lambda folder,s=seed:argv(s,'freeze'))
                if not (design(seed)/'readiness.json').exists():engine.phase(f'seed_{seed}/readiness',lambda folder,s=seed:argv(s,'readiness'))
                save_external(engine)
            engine.phase('batch/preflight',lambda folder:[PYTHON,'-B',str(REVIEW/'preflight.py')]);save_external(engine)
            if freeze_only:
                engine.state.update(status='frozen_no_fits',active=None,disk_free_bytes=disk_gate());save_external(engine)
                print('FOUR-SEED BATCH FROZEN; NO FITS',flush=True);return
            frozen=read(REVIEW/'FROZEN_BATCH_MANIFEST.json');evaluated=read(REVIEW/'EVALUATED_COMMIT.json')
            assert frozen['models_fitted']==0 and frozen['source_hash']==source_digest()==evaluated['source_hash']
            subprocess.run(['git','merge-base','--is-ancestor',evaluated['evaluated_commit'],'HEAD'],cwd=REPO,check=True)
            for seed in SEEDS:
                engine.state.update(status=f'seed_{seed}_running',current_seed=seed,disk_free_bytes=disk_gate());save_external(engine)
                engine.phase(f'seed_{seed}/run',lambda folder,s=seed:argv(s,'run'));save_external(engine)
                engine.phase(f'seed_{seed}/validate',lambda folder,s=seed:argv(s,'validate'));save_external(engine)
                engine.phase(f'seed_{seed}/resume',lambda folder,s=seed:argv(s,'resume'));save_external(engine)
                v=read(validation(seed)/'validation.json');r=read(resume(seed))
                if not v['passed'] or v['actual_exit_status']!=0:raise ValueError(f'seed {seed} validation failed')
                if not r['passed'] or any(r[x] for x in ['models_fitted','calibrators_fitted','replay_updates']) or not r['scientific_artifacts_unchanged']:
                    raise ValueError(f'seed {seed} completed resume failed')
                engine.state.setdefault('units',{})[str(seed)]=dict(status='validated_and_resumed',run=str(run(seed)),validation=str(validation(seed)),resume=str(resume(seed)))
                save_external(engine)
            engine.phase('final/analyze',lambda folder:[PYTHON,'-B',str(REVIEW/'analyze.py')]);save_external(engine)
            engine.phase('final/validate_aggregate',lambda folder:[PYTHON,'-B',str(REVIEW/'validate_aggregate.py')]);save_external(engine)
            engine.phase('final/package_raw',lambda folder:[PYTHON,'-B',str(REVIEW/'pack_evidence.py')]);save_external(engine)
            engine.phase('final/update_documents',lambda folder:[PYTHON,'-B',str(REVIEW/'update_documents.py')]);save_external(engine)
            engine.state.update(status='science_and_evidence_complete',active=None,disk_free_bytes=disk_gate());save_external(engine)
            engine.phase('final/publication',lambda folder:[PYTHON,'-B',str(REVIEW/'publish.py'),'--label','completed']);
            engine.state.update(status='completed',active=None);save_external(engine)
            print('ALL FOUR AUTHORIZED SEEDS, VALIDATION, ANALYSIS, PACKAGING AND PUBLICATION COMPLETE',flush=True)
        except BaseException as exc:
            engine.state.update(status='failed',failure=str(exc),traceback=traceback.format_exc());save_external(engine);raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--freeze-only',action='store_true');main(p.parse_args().freeze_only)
