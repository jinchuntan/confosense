"""Future authorized first C run. This module is inert until explicitly invoked."""
import argparse,traceback
from common import *
from coordinator import Engine,_legacy

def main(acknowledged):
    if not acknowledged:raise SystemExit('No real execution: obtain a new user authorization for the exact published proposal, then pass --acknowledge-new-user-authorization.')
    proposal=REVIEW/'first_real_run_proposal_manifest.json'
    manifest=REVIEW/'first_real_execution_manifest_v1.json'
    expected=read(proposal)
    expected.update(execution_authorized=True,authorization_kind='explicit_real_C_run')
    if manifest.exists():
        if read(manifest)!=expected:raise ValueError('preserve existing execution manifest; scope differs')
    else:atomic(manifest,expected)
    design=SMART/'protocols/conditional_context005/pleia_energy_f2_s42_C_v1'
    run=SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1'
    batch=SMART/'outputs/conditional_context005/first_real_C_v1_coordinator'
    BACKUP.mkdir(parents=True,exist_ok=True)
    with _legacy.exclusive_lock(BACKUP/'first_real_coordinator.lock'):
        engine=Engine(batch)
        try:
            if git('branch','--show-current')=='main':raise ValueError('real execution must retain a review branch')
            engine.reconcile()
            for action in ['freeze','readiness','run','validate','resume']:
                receipt=batch/'validation' if action=='validate' else batch/'resume.json' if action=='resume' else design/'readiness.json'
                argv=[PYTHON,'-B','-m','src.conditional_context005',action,'--manifest',str(manifest),'--design',str(design),'--out',str(run),'--readiness',str(design/'readiness.json'),'--receipt',str(receipt)]
                if action=='run' and (run/'checkpoint_manifest.json').exists():argv+=['--resume-incomplete']
                engine.phase('pleia_energy/'+action,lambda folder,a=argv:a)
                atomic(BACKUP/'first_real_progress.json',engine.state)
            if not read(batch/'validation/validation.json')['passed'] or not read(batch/'resume.json')['passed']:raise ValueError('first real C acceptance failed')
            engine.state.update(status='completed',active=None);engine.save()
        except BaseException as exc:
            engine.state.update(status='failed',failure=str(exc),traceback=traceback.format_exc());engine.save();raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--acknowledge-new-user-authorization',action='store_true')
    main(p.parse_args().acknowledge_new_user_authorization)
