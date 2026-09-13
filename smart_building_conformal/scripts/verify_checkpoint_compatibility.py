"""Explicit read-only historical evaluation/current-reader compatibility audit.

This is NOT a production training resume: the historical manifest is never
rewritten and a current-source training identity must still be rejected.
"""
import gc
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src import operational004 as runner, operational004_engine as engine, operational004_stream as stream
from src.unit_checkpoint import UnitCheckpoint, digest, signature, source_digest
from src.pilot_resources import ResourceMeter, hardware, require_ram
from src.operational004_design import build_windows, make_outer_folds, nested_roles
from src import split_integrity as SI


def fingerprint(frame):
    h=hashlib.sha256()
    for start in range(0,len(frame),50000):
        h.update(pd.util.hash_pandas_object(frame.iloc[start:start+50000],index=True).values.tobytes())
    return dict(rows=len(frame),columns=list(frame.columns),dtypes=list(map(str,frame.dtypes)),
                all_values_and_index_sha256=h.hexdigest())


def main(run, out):
    run=Path(run);out=Path(out);out.mkdir(exist_ok=False,parents=True)
    unit=run/'units/outer2_model42';manifest=json.loads((run/'checkpoint_manifest.json').read_text())
    spec=manifest['spec'];before={str(p.relative_to(run)):digest(p) for p in run.rglob('*') if p.is_file()}
    attempts=[]
    def forbidden(*a,**k):
        attempts.append('forbidden');raise AssertionError('no fitting/computation allowed')
    runner.evaluate_unit=engine.evaluate_unit=forbidden
    stream.OwnedInterval.__init__=stream.conformal_cqr.fit_cqr=forbidden
    current_hash=source_digest()
    try: UnitCheckpoint(run,dict(spec,source_hash=current_hash),resume=True)
    except ValueError as e:
        assert 'signature mismatch' in str(e); guard=str(e)
    else: raise AssertionError('production source guard was bypassed')
    phases=[]
    def phase(name, fn):
        with ResourceMeter() as m: value=fn()
        phases.append(dict(phase=name,**m.result));return value
    real=pd.read_csv;calls=[]
    def counted(*a,**k): calls.append(str(a[0]));return real(*a,**k)
    require_ram(3*2**30)
    with ResourceMeter() as total:
        cfg=runner.resolve_dataset_config(runner.load_config('configs/study_final_dissertation_v2.yaml'),'bdg2')
        prepared=phase('preparation',lambda:runner.prepare(cfg))
        s,w,_=phase('windows',lambda:build_windows(prepared,cfg,cfg['alerts']['primary_horizon']))
        def identity():
            scheme='chronological' if isinstance(prepared.partitioner,runner.ChronologicalPartitioner) else SI.GROUPED
            fold=make_outer_folds(w['meta'],scheme,3,w['horizon'],s.freq)[2]
            roles=nested_roles(w['meta'],fold,scheme)
            assert cfg==spec['resolved_config'] and w['data_hash']==spec['data_hash']
            assert hashlib.sha256(np.asarray(w['y'],float).tobytes()).hexdigest()==spec['outcomes_hash']
            assert runner.pilot_grid(cfg,s.freq)==spec['candidate_grid']
            assert {k:SI.membership_hash(w['meta'],v) for k,v in roles.items()}==spec['membership_hashes']
        phase('prefit_identity_read_only',identity)
        store=UnitCheckpoint(run,spec,resume=True,string_columns=('group_id','row_id'))
        def read():
            pd.read_csv=counted
            try:
                value=store.load('outer2_model42'); n=len(calls)
                store.require_complete(['outer2_model42'])
                assert len(calls)==n
                return value
            finally: pd.read_csv=real
        payload,frames=phase('checkpoint_load_verify',read)
        validation=phase('output_validation',lambda:engine.validate_unit(payload,frames,expected_scope='bounded_operational_pilot'))
    # Same preparation/window/identity/read/validation scope as historical resume.
    # Exhaustive value fingerprints are a separate audit cost after that scope.
    new_values={k:fingerprint(v) for k,v in frames.items()}
    saved_payload=json.loads((unit/'payload.json').read_text())
    assert payload==saved_payload
    del frames,prepared,s,w;gc.collect()
    archive=Path(str(run)+'_execution')/'evaluated_source.zip'
    with zipfile.ZipFile(archive) as z:
        raw=z.read('src/unit_checkpoint.py')
        source_entries={n:z.read(n) for n in z.namelist() if n.endswith('.py')}
    old_source=hashlib.sha256('\n'.join(f"{n[4:]}:{hashlib.sha256(b).hexdigest()}" for n,b in sorted(source_entries.items())).encode()).hexdigest()
    assert old_source==spec['source_hash']
    # Execute the archived parser body in isolation, one required frame at a
    # time. This preserves exact legacy dtype/converter behavior without the
    # unsafe second all-frame allocation. Its load implementation is unchanged.
    legacy={};exec(compile(raw,'archived/unit_checkpoint.py','exec'),legacy)
    record=json.loads((unit/'COMPLETE.json').read_text())
    old_values={}
    for name, filename in record['frames'].items():
        try: frame=legacy['pd'].read_csv(unit/filename,float_precision='round_trip',converters={'group_id':str,'row_id':str})
        except pd.errors.EmptyDataError: frame=pd.DataFrame()
        old_values[name]=fingerprint(frame);del frame;gc.collect()
    assert new_values==old_values
    after={str(p.relative_to(run)):digest(p) for p in run.rglob('*') if p.is_file()}
    assert before==after and not attempts
    assert len(calls)==len(record['frames']) and len(set(calls))==len(calls)
    result=dict(passed=True,mode='read_only_historical_checkpoint_compatibility_not_training_resume',
        historical_evaluated_commit='ef9a8a9525bafea00a12b5c1327aadec071eab91',historical_source_hash=old_source,
        current_reader_source_hash=current_hash,reader_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        historical_source_archive_sha256=digest(archive),production_source_guard=guard,manifest_rewritten=False,
        learned_fits=0,forbidden_fit_or_compute_calls=0,required_frames=len(calls),csv_parses_in_completed_read=len(calls),
        csv_parses_in_completeness_check=0,all_payload_values_equal=True,all_frame_value_fingerprints_equal=True,
        primary_decision=payload['decision'],inverse_decision=payload['inverse_recall_floor'],
        scientific_output_validation=validation,unit_files_byte_identical=len(before)-1,
        original_file_hashes=before,frames=new_values,phases=phases,comparable_resume_scope=total.result,
        comparable_scope_note='Fresh preparation, windows, read-only identity checks, single load + completeness + output validation; excludes subsequent value audit and imports. Historical command time additionally includes imports/journal writes.',
        hardware=hardware())
    (out/'validation.json').write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')
    pd.DataFrame(phases).to_csv(out/'phase_measurements.csv',index=False)
    print(json.dumps({k:v for k,v in result.items() if k not in ('original_file_hashes','frames','phases','hardware')},indent=2,default=str),flush=True)


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
