"""Summarise measured command/phase costs without adding overlapping phases."""
import json
from pathlib import Path
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'smart_building_conformal/outputs/amendment004'
OUT=BASE/'bdg2_pilot_validation_v1'

def main():
    commands=[];phases=[]
    for p in sorted(OUT.glob('*.log.json')):
        d=json.loads(p.read_text());commands.append(dict(log=p.name.removesuffix('.json'),
            seconds=d['seconds'],exit_status=d['exit_status'],started_utc=d['started_utc'],ended_utc=d['ended_utc'],
            logger_pid=d.get('logger_pid'),child_pid=d.get('child_pid'),command=json.dumps(d['command'])))
    for p in sorted(BASE.glob('bdg2_operational_pilot_f2_s42_v*_execution/*_phases.jsonl')):
        for line in p.read_text().splitlines():
            d=json.loads(line)
            if d['event']=='phase_end':phases.append(dict(run=p.parent.name,invocation=p.name,**d))
    run=BASE/'bdg2_operational_pilot_f2_s42_v2';payload=json.loads((run/'units/outer2_model42/payload.json').read_text())
    cpu=json.loads((OUT/'process_cpu.json').read_text())
    process=json.loads((Path(str(run)+'_execution')/'run_phases.jsonl').read_text().splitlines()[0])
    assert cpu['pid']==process['pid'] and cpu['exit_status']==0
    pd.DataFrame([cpu]).to_csv(OUT/'process_measurements.csv',index=False)
    fits=[]
    for r in payload['fit_records']:
        fits.append(dict(role=r['role'],method=r['method'],model_seed=r['model_seed'],level=r['level'],
            learned_fit_objects=r['fit_invocations'],quantile_sub_estimators=r['fit_invocations']*r['identity'].get('sub_estimators',0),
            estimator_class=r['identity']['estimator_class'],fit_identity=r['fit_identity']))
    sizes=[]
    for p in sorted(BASE.glob('bdg2_*')):
        if not p.is_dir():continue
        files=[x for x in p.rglob('*') if x.is_file()]
        sizes.append(dict(directory=p.name,files=len(files),bytes=sum(x.stat().st_size for x in files),
            largest_file=max(files,key=lambda x:x.stat().st_size).relative_to(p).as_posix() if files else '',
            largest_file_bytes=max([x.stat().st_size for x in files],default=0)))
    for name,rows in [('command_measurements.csv',commands),('phase_measurements.csv',phases),
                      ('fit_measurements.csv',fits),('artifact_measurements.csv',sizes)]:
        pd.DataFrame(rows).to_csv(OUT/name,index=False)
    meta=dict(note='Command wall times are disjoint invocations. Phase windows overlap; do not sum nested measurements.',
        run_compute_scope='evaluate_unit including two inner blocks, selection, final block and frame assembly; excludes preparation/checkpoint writing/validation',
        process_peak_scope='Windows process lifetime peak (includes preparation and I/O); phase RSS sampled every 50 ms',
        artifact_scope='Existing evidence directories at table-generation time; excludes local raw data, caches and environments',
        actual_learned_fit_objects=sum(x['learned_fit_objects'] for x in fits),
        actual_quantile_sub_estimators=sum(x['quantile_sub_estimators'] for x in fits),
        first_attempt_learned_fits=0,completed_resume_learned_fits=0,
        process_cpu=cpu,compute_resources=payload['compute_resources'],hardware=payload['hardware'])
    (OUT/'cost_scope.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(meta,indent=2))

if __name__=='__main__':main()
