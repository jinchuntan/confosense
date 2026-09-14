"""Freeze and check all four no-fit designs before any real fitting."""
import argparse,csv,json,subprocess
from common import *

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-commit',required=True);args=parser.parse_args()
    assert git('branch','--show-current')==BRANCH and git('rev-parse','HEAD')==args.source_commit
    proposed=list(csv.DictReader((SMART/'outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/next_proposed_method_keys.csv').open()))
    keys={(int(r['model_seed']),int(r['horizon']),float(r['level']),r['method']) for r in proposed}
    expected={(s,h,l,m) for s in SEEDS for h in (1,3,6) for l in (.9,.95) for m in ['quantile_uncalibrated','cqr','recentred_enbpi_static','recentred_enbpi_updated','dscp']}
    assert keys==expected and len(proposed)==120
    commands=[]
    for seed in SEEDS:
        d=design(seed);ready=d/'readiness.json'
        freeze=[PYTHON,'-B','-m','src.matched_intervals005','freeze','--authorization',str(auth(seed)),'--synthetic-receipt',str(ROOT/'review/matched_intervals005_bdg2_20260914/SYNTHETIC_ACCEPTANCE.json'),'--design-dir',str(d)]
        check=[PYTHON,'-B','-m','src.matched_intervals005','readiness','--design-dir',str(d),'--receipt',str(ready)]
        for action,command in [('freeze',freeze),('readiness',check)]:
            if action=='freeze' and d.exists():raise ValueError(f'preserve existing design {d}')
            if action=='readiness' and ready.exists():raise ValueError(f'preserve existing readiness {ready}')
            result=subprocess.run(command,cwd=SMART)
            commands.append(dict(seed=seed,action=action,argv=command,exit_code=result.returncode))
            if result.returncode:raise SystemExit(result.returncode)
        protocol=read(d/'frozen_protocol.json')
        assert protocol['source_hash']==source_digest() and protocol['scope']['model_seed']==seed
        assert protocol['joint_support']=={'fit':51534,'calibration':17270,'test':34590}
        assert protocol['seasonal_alias_source']['model_seed']==42
    record=dict(passed=True,source_commit=args.source_commit,source_hash=source_digest(),exact_new_keys=120,seeds=SEEDS,commands=commands,protocols={str(s):dict(path=str(design(s)/'frozen_protocol.json'),sha256=sha(design(s)/'frozen_protocol.json'),readiness_sha256=sha(design(s)/'readiness.json')) for s in SEEDS},models_fitted=0,calibrators_fitted=0,utc=now())
    atomic(REVIEW/'PRE_FIT_FREEZE.json',record);print(json.dumps(record,indent=2))

if __name__=='__main__':main()

