"""Freeze and readiness-check all three authorized real-data designs without fitting."""
import json, subprocess
from common import *

def worker(unit,action,receipt=None):
    command=[PYTHON,'-B',str(REVIEW/'measured_action.py'),'--measurement',str(BATCH/f'{unit["name"]}_{action}_worker_resources.json'),'--',action,'--design-dir',str(design(unit))]
    if action=='freeze':command += ['--authorization',str(auth(unit)),'--synthetic-receipt',str(REVIEW/'PRE_FIT_TEST_RECEIPT_V2.json')]
    else:command += ['--receipt',str(receipt)]
    result=subprocess.run(command,cwd=SMART)
    if result.returncode:raise SystemExit(result.returncode)
    return command

def main():
    if git('branch','--show-current')!=BRANCH:raise ValueError('wrong review branch')
    tests=read(REVIEW/'PRE_FIT_TEST_RECEIPT_V2.json')
    if not tests['passed'] or tests['source_hash']!=source_digest():raise ValueError('pre-fit synthetic receipt mismatch')
    if BATCH.exists() and any(BATCH.iterdir()):raise ValueError('preserve existing batch freeze artifacts')
    BATCH.mkdir(parents=True)
    records=[];protocols={}
    for unit in UNITS:
        if design(unit).exists():raise ValueError('preserve existing frozen design')
        records.append(dict(unit=unit['name'],action='freeze',argv=worker(unit,'freeze')))
        ready=design(unit)/'readiness.json'
        records.append(dict(unit=unit['name'],action='readiness',argv=worker(unit,'readiness',ready)))
        protocol=read(design(unit)/'frozen_protocol.json')
        assert protocol['scope']['dataset']==unit['dataset'] and protocol['joint_support']=={'fit':(14845 if unit['dataset']!='rico' else 9577),'calibration':(4943 if unit['dataset']!='rico' else 3297),'test':(9902 if unit['dataset']!='rico' else 6437)}
        assert protocol['expected_cells']['interval_method']==unit['cells'] and protocol['expected_operations']['quantile_estimator_fit']+protocol['expected_operations']['xgboost_estimator_fit']==unit['learned_fits']
        protocols[unit['name']]=dict(path=str(design(unit)/'frozen_protocol.json'),sha256=sha(design(unit)/'frozen_protocol.json'),readiness_sha256=sha(ready),joint_support=protocol['joint_support'])
    result=dict(passed=True,source_commit=git('rev-parse','HEAD'),source_hash=source_digest(),authorized_units=[u['name'] for u in UNITS],new_method_cells=sum(u['cells'] for u in UNITS),new_learned_estimator_fits=sum(u['learned_fits'] for u in UNITS),commands=records,protocols=protocols,models_fitted=0,calibrators_fitted=0,utc=now())
    atomic(REVIEW/'PRE_FIT_FREEZE.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
