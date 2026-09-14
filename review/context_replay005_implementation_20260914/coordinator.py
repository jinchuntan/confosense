"""Sequential synthetic CLI gate with prelaunch checks and exact worker adoption."""
import importlib.util,subprocess,traceback,os
from common import *
_spec=importlib.util.spec_from_file_location('context_legacy_engine',ROOT/'review/matched_intervals005_bdg2_20260914/coordinator.py')
_legacy=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_legacy)

class Engine(_legacy.Engine):
    def phase(self,task,command_factory):
        # In the old failure, append was unresolved AFTER the worker launched.
        # Resolve every critical journal symbol and check imports before Popen.
        for name in ['append','atomic','read','now','identity','family','alive']:
            if not callable(_legacy.__dict__.get(name)):raise RuntimeError('prelaunch missing coordinator symbol: '+name)
        return super().phase(task,command_factory)

def main(version):
    batch=SMART/f'outputs/conditional_context005/synthetic_{version}_coordinator';BACKUP.mkdir(parents=True,exist_ok=True)
    with _legacy.exclusive_lock(BACKUP/'coordinator.lock'):
        engine=Engine(batch)
        try:
            if git('branch','--show-current')!=BRANCH:raise ValueError('wrong review branch')
            subprocess.run([PYTHON,'-B','-c','import src.conditional_context005,src.context005_validate'],cwd=SMART,check=True)
            engine.reconcile()
            for ds in ['pleia_energy','rico']:
                manifest=REVIEW/f'synthetic_{ds}_{version}.json';design=SMART/f'protocols/conditional_context005/synthetic_{ds}_{version}';run=SMART/f'outputs/conditional_context005/synthetic_{ds}_{version}'
                from src.context005_spec import VERSION,controls,rules,POLICIES
                from src.context005_data import synthetic
                d=synthetic(ds)
                if not manifest.exists():atomic(manifest,dict(version=VERSION,dataset=ds,outer_fold=2,model_seed=42,horizon=POLICIES[ds]['horizon'],synthetic=True,tiny_estimator=True,
                    controls=controls(ds),rules=rules(ds),expected_contexts=len(d['contexts']),expected_schedules=len(d['schedules']),
                    selection='none',endpoint='C_effective_fault_conditional_context',execution_authorized=True,authorization_kind='bounded_synthetic_integration'))
                del d
                for action in ['freeze','readiness','run','validate','resume']:
                    receipt=(batch/(ds+'_validation')) if action=='validate' else (batch/(ds+'_resume.json')) if action=='resume' else design/'readiness.json'
                    argv=[PYTHON,'-B','-m','src.conditional_context005',action,'--manifest',str(manifest),'--design',str(design),'--out',str(run),'--readiness',str(design/'readiness.json'),'--receipt',str(receipt)]
                    if action=='run' and (run/'checkpoint_manifest.json').exists():argv+=['--resume-incomplete']
                    engine.phase(ds+'/'+action,lambda folder,a=argv:a)
                    atomic(BACKUP/'latest_progress.json',engine.state)
                if not read(batch/(ds+'_validation')/'validation.json')['passed'] or not read(batch/(ds+'_resume.json'))['passed']:raise ValueError('synthetic acceptance failed')
            engine.state.update(status='completed',active=None);engine.save();print('BOTH CADENCE CLI WORKFLOWS PASSED',flush=True)
        except BaseException as exc:
            engine.state.update(status='failed',failure=str(exc),traceback=traceback.format_exc());engine.save();raise

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='v1');main(parser.parse_args().version)
