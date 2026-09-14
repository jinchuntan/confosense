"""Durable serial run, independent validation, and forbidden-fit resume by seed."""
import importlib.util,subprocess,traceback
from pathlib import Path
from common import *

_spec=importlib.util.spec_from_file_location('interval_pilot_coordinator',ROOT/'review/matched_intervals005_bdg2_20260914/coordinator.py')
_legacy=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_legacy)
Engine,exclusive_lock=_legacy.Engine,_legacy.exclusive_lock

def command(seed,action,receipt=None):
    argv=[PYTHON,'-B',str(REVIEW/'measured_action.py'),'--measurement',str(BATCH/f'seed{seed}_{action}_worker_resources.json'),'--',action,'--design-dir',str(design(seed)),'--out',str(run(seed)),'--readiness',str(design(seed)/'readiness.json')]
    if receipt:argv+=['--receipt',str(receipt)]
    if action=='resume' and receipt:argv+=['--forbid-fits']
    return argv

def save_progress(engine):
    units={}
    for seed in SEEDS:
        root=run(seed);complete=root/'COMPLETE.json'
        units[str(seed)]=dict(run=str(root),complete=complete.exists(),completed_stages=sum((p/'COMPLETE.json').exists() for p in (root/'stages').glob('*')) if root.exists() else 0,validation=(BATCH/f'seed{seed}_validation/validation.json').exists(),zero_fit_resume=(BATCH/f'seed{seed}_completed_resume.json').exists())
    engine.state.update(units=units,restart_argv=[PYTHON,'-B',str(REVIEW/'coordinator.py')],full_study_ready=False)
    engine.save();BACKUP.mkdir(parents=True,exist_ok=True);atomic(BACKUP/'latest_progress.json',engine.state)
    lines=['# BDG2 interval multiseed progress','',f'Updated UTC: {now()}. Status: **{engine.state["status"]}**.','',f'Restart: `{PYTHON} -B {REVIEW/"coordinator.py"}`.','']
    for seed,row in units.items():lines.append(f'- Seed {seed}: stages {row["completed_stages"]}; run complete {row["complete"]}; validation {row["validation"]}; zero-fit resume {row["zero_fit_resume"]}.')
    atomic(REVIEW/'PROGRESS_AND_RESTART.md','\n'.join(lines)+'\n')

def main():
    BACKUP.mkdir(parents=True,exist_ok=True)
    with exclusive_lock(BACKUP/'coordinator.lock'):
        engine=Engine(BATCH)
        try:
            assert git('branch','--show-current')==BRANCH
            freeze=read(REVIEW/'PRE_FIT_FREEZE.json');assert freeze['passed'] and freeze['source_hash']==source_digest()
            subprocess.run(['git','merge-base','--is-ancestor',freeze['source_commit'],'HEAD'],cwd=ROOT,check=True)
            engine.reconcile();engine.state['status']='running';save_progress(engine)
            for seed in SEEDS:
                d=design(seed);r=run(seed);validation=BATCH/f'seed{seed}_validation';resume=BATCH/f'seed{seed}_completed_resume.json'
                assert sha(d/'frozen_protocol.json')==freeze['protocols'][str(seed)]['sha256']
                action='resume' if (r/'checkpoint_manifest.json').exists() else 'run'
                engine.phase(f'seed{seed}/run',lambda folder,s=seed,a=action:command(s,a));save_progress(engine)
                engine.phase(f'seed{seed}/validate',lambda folder,s=seed,v=validation:command(s,'validate',v));save_progress(engine)
                engine.phase(f'seed{seed}/completed_resume',lambda folder,s=seed,x=resume:command(s,'resume',x));save_progress(engine)
                checked=read(validation/'validation.json');resumed=read(resume)
                assert checked['passed'] and checked['method_cells']==30 and checked['alert_stream_checks']==30
                assert checked['models_fitted']==checked['calibrators_fitted']==0 and checked['source_artifacts_unchanged']
                assert resumed['models_fitted']==resumed['calibrators_fitted']==0 and resumed['all_run_files_unchanged']
                engine.state['status']=f'seed{seed}_validated';save_progress(engine)
            engine.state['status']='science_complete';save_progress(engine)
            print('ALL FOUR AUTHORIZED SEEDS COMPLETED, VALIDATED, AND ZERO-FIT RESUMED',flush=True)
        except BaseException as exc:
            engine.state.update(status='blocked',failure=str(exc),traceback=traceback.format_exc());save_progress(engine);raise

if __name__=='__main__':main()

