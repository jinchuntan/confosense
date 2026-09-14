"""Durable serial execution of the three frozen remaining-settings units."""
import importlib.util,subprocess,traceback
from common import *

_spec=importlib.util.spec_from_file_location('interval_engine',ROOT/'review/matched_intervals005_bdg2_20260914/coordinator.py')
_legacy=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_legacy)
Engine,exclusive_lock=_legacy.Engine,_legacy.exclusive_lock

def command(unit,action,receipt=None):
    argv=[PYTHON,'-B',str(REVIEW/'measured_action.py'),'--measurement',str(BATCH/f'{unit["name"]}_{action}_worker_resources.json'),'--',action,'--design-dir',str(design(unit)),'--out',str(run(unit)),'--readiness',str(design(unit)/'readiness.json')]
    if receipt:argv+=['--receipt',str(receipt)]
    if action=='resume':argv+=['--forbid-fits']
    return argv

def progress(engine):
    units={}
    for unit in UNITS:
        root=run(unit);stage=root/'stages'
        units[unit['name']]=dict(run=str(root),complete=(root/'COMPLETE.json').exists(),completed_stages=sum((p/'COMPLETE.json').exists() for p in stage.glob('*')) if stage.exists() else 0,validation=(BATCH/f'{unit["name"]}_validation/validation.json').exists(),zero_fit_resume=(BATCH/f'{unit["name"]}_completed_resume.json').exists())
    engine.state.update(units=units,restart_argv=[PYTHON,'-B',str(REVIEW/'coordinator.py')],full_study_ready=False)
    engine.save();BACKUP.mkdir(parents=True,exist_ok=True);atomic(BACKUP/'latest_progress.json',engine.state)
    lines=['# Remaining settings interval batch progress','',f'Updated UTC: {now()}. Status: **{engine.state["status"]}**.','',f'Restart: `{PYTHON} -B {REVIEW/"coordinator.py"}`.','']
    for name,row in units.items():lines.append(f'- {name}: {row["completed_stages"]} stages; complete {row["complete"]}; validation {row["validation"]}; zero-fit resume {row["zero_fit_resume"]}.')
    atomic(REVIEW/'PROGRESS_AND_RESTART.md','\n'.join(lines)+'\n')

def main():
    BACKUP.mkdir(parents=True,exist_ok=True)
    with exclusive_lock(BACKUP/'coordinator.lock'):
        engine=Engine(BATCH)
        try:
            if git('branch','--show-current')!=BRANCH:raise ValueError('wrong review branch')
            freeze=read(REVIEW/'PRE_FIT_FREEZE.json')
            if not freeze['passed'] or freeze['source_hash']!=source_digest():raise ValueError('frozen source identity mismatch')
            subprocess.run(['git','merge-base','--is-ancestor',freeze['source_commit'],'HEAD'],cwd=ROOT,check=True)
            engine.reconcile();engine.state['status']='running';progress(engine)
            for unit in UNITS:
                name=unit['name'];root=run(unit);validation=BATCH/f'{name}_validation';resume=BATCH/f'{name}_completed_resume.json'
                if sha(design(unit)/'frozen_protocol.json')!=freeze['protocols'][name]['sha256']:raise ValueError('frozen protocol changed: '+name)
                action='resume' if (root/'checkpoint_manifest.json').exists() else 'run'
                engine.phase(f'{name}/run',lambda folder,u=unit,a=action:command(u,a));progress(engine)
                engine.phase(f'{name}/validate',lambda folder,u=unit,r=validation:command(u,'validate',r));progress(engine)
                engine.phase(f'{name}/completed_resume',lambda folder,u=unit,r=resume:command(u,'resume',r));progress(engine)
                checked=read(validation/'validation.json');resumed=read(resume)
                if not checked['passed'] or checked['method_cells']!=unit['cells'] or checked['alert_stream_checks']!=unit['cells']:raise ValueError('validation count mismatch: '+name)
                if checked['models_fitted'] or checked['calibrators_fitted'] or not checked['source_artifacts_unchanged']:raise ValueError('validation mutated or fit: '+name)
                if resumed['models_fitted'] or resumed['calibrators_fitted'] or not resumed['all_run_files_unchanged']:raise ValueError('completed resume refit or changed bytes: '+name)
                engine.state['status']=name+'_validated';progress(engine)
            engine.state['status']='science_complete';progress(engine)
            print('ALL THREE AUTHORIZED SETTINGS COMPLETED, VALIDATED, AND ZERO-FIT RESUMED',flush=True)
        except BaseException as exc:
            engine.state.update(status='blocked',failure=str(exc),traceback=traceback.format_exc());progress(engine);raise

if __name__=='__main__':main()
