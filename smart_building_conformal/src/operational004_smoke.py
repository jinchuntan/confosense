"""The bounded amendment-004 synthetic integration smoke; never a study result."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import numpy as np
import pandas as pd
from .operational004_design import DESIGN,make_outer_folds,candidates
from .operational004_fixtures import fixture_data,DeterministicOwnedInterval
from .operational004_engine import evaluate_unit,checkpointed_unit,validate_unit
from .operational004_verification import selection_probes,actual_cqr_probe,zero_probe
from .pilot_resources import ResourceMeter,hardware
from .unit_checkpoint import UnitCheckpoint,signature,source_digest,digest


def run(out,config,resume=False):
    out=Path(out);configuration=json.loads(Path(config).read_text(encoding='utf-8'))
    if configuration['design']!=DESIGN:raise ValueError('frozen amendment/design mismatch')
    _,segmented,w,cfg,_=fixture_data()
    fold=make_outer_folds(w['meta'],'chronological',3,1,segmented.freq)[0]
    spec=dict(scope='SMOKE ONLY',outer_fold=0,model_seed=42,config_hash=digest(config),
        design_hash=signature(DESIGN),source_hash=source_digest(),data_hash=w['data_hash'],
        outcomes_hash=signature(w['y'].tolist()),candidate_grid=candidates(cfg,segmented.freq,smoke=True),
        catalogue_seeds=DESIGN['catalogue_seeds'],fixture='two 3600-sample groups at 10 minutes',
        actual_cqr_probe=dict(train=400,calibration=400,evaluate=300,seed=42,quantile_max_iter=300))
    def compute():
        start=datetime.now(timezone.utc).isoformat()
        with ResourceMeter() as meter:
            payload,frames=evaluate_unit('synthetic004',0,42,segmented,w,cfg,fold,smoke=True,
                model_factory=DeterministicOwnedInterval,force_diagnostic=True,save_streams=True,evaluate_outer=True)
            selection,selection_frames=selection_probes();frames.update(selection_frames)
            actual,actual_frames=actual_cqr_probe();frames.update(actual_frames)
            frames['zero_controls']=zero_probe(segmented,w,cfg,fold)
            payload.update(selection_acceptance=selection,actual_cqr_acceptance=actual,
                fit_accounting=dict(main_fixture_objects=3,zero_control_fixture_objects=1,
                    actual_cqr_objects=1,actual_quantile_sub_estimators=3,persistence_learned_fits=0),
                total_fit_invocations=5,configuration=configuration,
                evaluated_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                started_utc=start,hardware=hardware(),global_study_ready=False)
        payload['compute_resources']=meter.result
        payload['completed_utc']=datetime.now(timezone.utc).isoformat()
        return payload,frames
    payload,frames,status=checkpointed_unit(out,spec,compute,resume=resume)
    # Reload the serialized bytes even on the initial execution; validating only
    # in-memory frames would not verify the reviewer's actual saved evidence.
    stored=UnitCheckpoint(out,spec,resume=True,string_columns=('group_id','row_id'))
    payload,frames=stored.load('outer0_model42')
    validation=validate_unit(payload,frames,expected_scope='SMOKE ONLY')
    rejects_full=False
    try:validate_unit(payload,frames,expected_scope='full_study')
    except ValueError:rejects_full=True
    assert rejects_full
    with tempfile.TemporaryDirectory(prefix='confosense004_corruption_') as temp:
        copied=Path(temp)/'checkpoint';shutil.copytree(out,copied)
        target=copied/'units/outer0_model42/streams.csv.gz'
        with target.open('ab') as f:f.write(b'INTENTIONAL CORRUPTION TEST ON TEMPORARY COPY')
        rejected=False
        try:UnitCheckpoint(copied,spec,resume=True).load('outer0_model42')
        except ValueError as e:rejected='corrupt checkpoint' in str(e)
        assert rejected
    expected=pd.DataFrame([(c['candidate_id'],i) for c in spec['candidate_grid'] for i in [0,1]],
        columns=['candidate_id','inner_fold']).sort_values(['candidate_id','inner_fold']).reset_index(drop=True)
    actual=frames['surface'][['candidate_id','inner_fold']].sort_values(['candidate_id','inner_fold']).reset_index(drop=True)
    pd.testing.assert_frame_equal(expected,actual)
    result=dict(status='complete',**validation,**status,
        expected_inner_cells=12,expected_inner_catalogue_pairs=60,expected_outer_catalogue_pairs=20,
        checkpoint_corruption_rejected_on_temporary_copy=rejected,full_study_validator_rejects_smoke=rejects_full,
        decision=payload['decision'],operational_feasible=payload['operational_feasible'],
        fixture_feasible_selection=payload['selection_acceptance']['feasible_selection'],
        source_hash=spec['source_hash'],config_hash=spec['config_hash'],design_hash=spec['design_hash'],
        evaluated_commit=payload['evaluated_commit'],run_id=out.name)
    # Validation reports are separate from the immutable completed unit.
    filename='resume_validation.json' if resume else 'output_validation.json'
    path=out/filename
    if path.exists():raise ValueError('validation report already exists; do not overwrite completed evidence')
    if not resume:
        expected.to_csv(out/'expected_inner_keys.csv',index=False);actual.to_csv(out/'actual_inner_keys.csv',index=False)
        pd.DataFrame([dict(phase='smoke_compute',**payload['compute_resources'])]).to_csv(out/'resources.csv',index=False)
    path.write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True)
    parser.add_argument('--config',default='configs/operational_amendment004.json');parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();run(args.out,args.config,args.resume)
