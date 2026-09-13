"""Explicit one-unit real-data operational entrypoint; no full-study launcher."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from .run_study import load_config,resolve_dataset_config
from .model_comparison_pilot import prepare
from .datasets.base import ChronologicalPartitioner
from . import split_integrity as SI
from .operational004_design import DESIGN,build_windows,make_outer_folds,candidates
from .operational004_engine import evaluate_unit,checkpointed_unit,validate_unit
from .pilot_resources import ResourceMeter,hardware,require_ram
from .unit_checkpoint import signature,source_digest,digest


def pilot_grid(cfg,freq):
    """Predeclared bounded engineering pilot subset; not a full-grid result."""
    all_candidates=candidates(cfg,freq)
    return [c for c in all_candidates if c['level']==.95 and c['method'] in ('cqr','quantile_uncalibrated')
        and (c['strategy']=='static' or (c['strategy']=='rolling' and
            c['every']==cfg['recalibration']['grid']['update_every'][0] and
            c['window']==cfg['recalibration']['grid']['window'][0]))]


def run(dataset,outer_fold,model_seed,out,config,resume=False):
    frozen=json.loads(Path(config).read_text(encoding='utf-8'))
    if frozen['design']!=DESIGN:raise ValueError('frozen amendment/design mismatch')
    if dataset not in DESIGN['tasks'] or outer_fold not in range(3) or model_seed not in DESIGN['model_seeds']:
        raise ValueError('unit outside declared design')
    require_ram(3*2**30)
    cfg=resolve_dataset_config(load_config('configs/study_final_dissertation_v2.yaml'),dataset)
    prepared=prepare(cfg);s,w,_=build_windows(prepared,cfg,cfg['alerts']['primary_horizon'])
    scheme='chronological' if isinstance(prepared.partitioner,ChronologicalPartitioner) else SI.GROUPED
    fold=make_outer_folds(w['meta'],scheme,3,w['horizon'],s.freq)[outer_fold];grid=pilot_grid(cfg,s.freq)
    spec=dict(scope='bounded_operational_pilot',grid_scope='reduced_engineering_pilot_not_full_study',
        dataset=dataset,outer_fold=outer_fold,model_seed=model_seed,config_hash=digest(config),
        resolved_config=cfg,design_hash=signature(DESIGN),source_hash=source_digest(),data_hash=w['data_hash'],
        outcomes_hash=hashlib.sha256(np.asarray(w['y'],float).tobytes()).hexdigest(),candidate_grid=grid,
        catalogue_seeds=DESIGN['catalogue_seeds'])
    def compute():
        with ResourceMeter() as meter:
            payload,frames=evaluate_unit(dataset,outer_fold,model_seed,s,w,cfg,fold,
                candidate_grid=grid,save_streams=True,evaluate_outer=True)
        payload.update(compute_resources=meter.result,hardware=hardware(),grid_scope=spec['grid_scope'])
        return payload,frames
    payload,frames,status=checkpointed_unit(out,spec,compute,resume=resume)
    result=dict(**validate_unit(payload,frames,expected_scope='bounded_operational_pilot'),**status,
                decision=payload['decision'],global_study_ready=False)
    print(json.dumps(result,indent=2),flush=True)
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',choices=DESIGN['tasks'],required=True)
    ap.add_argument('--outer-fold',type=int,choices=range(3),required=True)
    ap.add_argument('--model-seed',type=int,choices=DESIGN['model_seeds'],required=True)
    ap.add_argument('--out',required=True);ap.add_argument('--config',default='configs/operational_amendment004.json')
    ap.add_argument('--resume',action='store_true');args=ap.parse_args()
    run(args.dataset,args.outer_fold,args.model_seed,args.out,args.config,args.resume)
