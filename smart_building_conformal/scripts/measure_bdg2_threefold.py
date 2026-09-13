"""Collect actual costs with nonoverlapping command and nested phase scopes."""
import json
from pathlib import Path
import sys
import pandas as pd


def main(manifest,out):
    plan=json.loads(Path(manifest).read_text());out=Path(out);out.mkdir(parents=True,exist_ok=False)
    base=Path('outputs/amendment004');new=base/'bdg2_threefold_validation_v1';old=base/'bdg2_pilot_validation_v1'
    commands=[];phases=[];sizes=[];process=[]
    logs=[old/'pilot_v2.log.json',old/'resume.log.json',old/'independent_audit.log.json']+sorted(new.glob('*.log.json'))
    for p in logs:
        r=json.loads(p.read_text());label=p.name.removesuffix('.log.json')
        commands.append(dict(path=p.as_posix(),historical=p.parent==old,command_label=label,
            scope='study_execution' if label in ['pilot_v2','fold1_run','fold0_run'] else 'verification_or_freezing',
            **{k:r[k] for k in ['seconds','exit_status','started_utc','ended_utc','logger_pid','child_pid']},
            command=json.dumps(r['command'])))
    for fold in [2,1,0]:
        root=Path(plan['units'][str(fold)]['out']);execution=Path(str(root)+'_execution')
        for mode in ['run','resume']:
            for line in (execution/(mode+'_phases.jsonl')).read_text().splitlines():
                r=json.loads(line)
                if r['event']=='phase_end':
                    phases.append(dict(outer_fold=fold,invocation=mode,nested_in_checkpoint=r['phase'] in
                        ['inner0_fit_replay_score','inner1_fit_replay_score','outer_fit_replay_score'],**r))
        for label,p in [('canonical_checkpoint',root),('execution_identity_and_journals',execution)]:
            files=[f for f in p.rglob('*') if f.is_file()]
            sizes.append(dict(outer_fold=fold,scope=label,path=p.as_posix(),files=len(files),bytes=sum(f.stat().st_size for f in files),
                largest_file=max(files,key=lambda f:f.stat().st_size).name,largest_file_bytes=max(f.stat().st_size for f in files)))
    historical=pd.read_csv(old/'process_measurements.csv').to_dict('records')
    process.extend(dict(outer_fold=2,**r) for r in historical)
    for fold in [1,0]:
        r=json.loads((new/f'fold{fold}_process_cost.json').read_text());assert r['exit_status']==0
        process.append(dict(outer_fold=fold,**r))
    cmd=pd.DataFrame(commands);study=cmd[cmd.scope=='study_execution']
    assert len(study)==3 and study.exit_status.eq(0).all()
    for name,rows in [('command_measurements',commands),('phase_measurements',phases),
                      ('process_measurements',process),('artifact_measurements',sizes)]:
        pd.DataFrame(rows).to_csv(out/(name+'.csv'),index=False)
    result=dict(passed=True,study_command_seconds=float(study.seconds.sum()),study_commands=3,
        new_execution_seconds=float(study[~study.historical].seconds.sum()),
        scope='sum of three nonoverlapping original successful study commands, including historical fold 2 exactly once',
        phase_warning='inner and outer phases are nested inside checkpoint computation; never add them to parent phases or sum memory peaks',
        validation_costs='resume, compatibility, regression, preflight and independent audits are separate command rows; no fitting except tiny regression fixtures',
        process_cpu='actual Windows process lifetime accounting for each study process; launcher PIDs differ from the numerical process',
        estimator_accounting='see combined fit_measurements.csv: 3 CQR objects / 9 quantile sub-estimators per fold, shared uncalibrated controls, persistence zero fits',
        historical_scope='completed forecasting pilot costs and previous investigations are not part of this operational benchmark',
        planning_estimates_are_not_measurements=True,full_study_ready=False)
    (out/'cost_scope.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
