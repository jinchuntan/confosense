"""Freeze, check, execute, validate and explicitly resume one matched matrix unit."""
from __future__ import annotations
import os
for _variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_variable] = '1'
import argparse
import gc
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

import numpy as np
import pandas as pd

from . import split_integrity as SI
from .matched_data005 import forecast_roles, ROLE_PAIRS, validate_roles, export_identifiers
from .matched_models005 import PhaseMeter, forbid_fitting, run_model, unit_key
from .model_comparison_pilot import prepare
from .pilot_data import build_support, role_records
from .pilot_resources import hardware, memory_snapshot
from .unit_checkpoint import UnitCheckpoint, digest, signature, source_digest, require_cells

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'f1a71a19b4e227a9894a8e2c74686a642dca962a'
INSTRUCTION = 'f44d4d1bd784254237bd643b9389fc9ce8c380a3'
PROPOSAL = ROOT / 'outputs/amendment005/study_plan_v1/next_forecast_unit.json'
MODELS = ['persistence', 'xgboost', 'attention_lstm']
LEVELS = [.9, .95]
KEY_COLUMNS = ['dataset', 'horizon', 'outer_fold', 'model_seed']


def write_json(path, value, *, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, default=str)
        stream.write('\n')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def versions():
    return {name: importlib.metadata.version(name) for name in
            ['numpy', 'pandas', 'scikit-learn', 'xgboost', 'torch']}


def setup_threads():
    import torch
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    if torch.get_default_dtype() != torch.float32:
        raise ValueError('unexpected Torch default dtype')


def select_matrix(matrix, key, authorization):
    if list(key) not in authorization['allowed_units'] or not authorization['real_fitting_authorized']:
        raise ValueError('unit outside explicitly authorized scope')
    frame = pd.read_csv(matrix, keep_default_na=False)
    selected = frame
    for column, value in zip(KEY_COLUMNS, key):
        selected = selected[selected[column] == value]
    selected = selected[selected.model.isin(MODELS)]
    require_cells(selected, ['model', 'level'], [(m, l) for m in MODELS for l in LEVELS])
    for column in ['data_hash', 'role_bank_hash', 'fit_n', 'calibration_n', 'test_n']:
        if selected[column].nunique() != 1:
            raise ValueError('inconsistent matched matrix ' + column)
    return selected


def fresh_data(protocol):
    cfg, config = protocol['resolved_dataset_config'], protocol['config']
    prepared = prepare(cfg)
    data = build_support(prepared, cfg, config['horizon'], config['sequence_length'])
    roles = forecast_roles(data['meta'], config['horizon'], prepared.freq, config['outer_fold'], config['dataset']=='rico')
    verify_data(data, roles, protocol)
    return data, roles


def verify_data(data, roles, protocol):
    expected = protocol['support']
    validate_roles(data['meta'], roles, protocol['config']['dataset']=='rico')
    actual = role_records(data['meta'], roles)
    if data['data_hash'] != expected['data_hash'] or actual != expected['roles']:
        raise ValueError('fresh data/roles differ from frozen identity')
    if signature(actual) != expected['role_bank_hash']:
        raise ValueError('role-bank identity mismatch')
    if data['feature_names'] != expected['feature_names'] or data['sequence_channels'] != expected['sequence_channels']:
        raise ValueError('feature/channel schema mismatch')


def check_identity(protocol_path, matrix, key):
    protocol = read_json(protocol_path)
    config = protocol['config']
    if tuple(config[k] for k in KEY_COLUMNS) != tuple(key):
        raise ValueError('protocol/unit key mismatch')
    if source_digest() != protocol['source_hash'] or versions() != protocol['packages']:
        raise ValueError('source or package mismatch')
    for path, expected in protocol['input_hashes'].items():
        if digest(ROOT / path) != expected:
            raise ValueError('frozen input/config mismatch: ' + path)
    if digest(matrix) != protocol['matrix_hash']:
        raise ValueError('matrix mismatch')
    for filename, field in [('membership.csv.gz','membership_hash'),('boundaries.csv','boundaries_hash')]:
        if field in protocol and digest(Path(protocol_path).parent/filename)!=protocol[field]:
            raise ValueError('frozen support-file mismatch: '+filename)
    select_matrix(matrix, key, protocol['authorization'])
    return protocol


def resource_reading(config, authorization, disk_path):
    snapshot = memory_snapshot()
    snapshot['free_disk_bytes'] = shutil.disk_usage(disk_path).free
    snapshot['launch_ram_reference_bytes'] = config['minimum_launch_available_ram_bytes']
    snapshot['launch_ram_reference_met'] = snapshot['available_ram_bytes'] >= config['minimum_launch_available_ram_bytes']
    snapshot['later_user_nonblocking_ram_instruction'] = authorization.get('nonblocking_launch_ram', False)
    if not snapshot['launch_ram_reference_met'] and not snapshot['later_user_nonblocking_ram_instruction']:
        raise MemoryError('launch RAM below execution policy')
    if snapshot['free_disk_bytes'] < config['minimum_free_disk_bytes']:
        raise OSError('insufficient free disk for fitted checkpoints')
    return snapshot


def freeze(matrix, key, design_dir, authorization_path):
    authorization = read_json(authorization_path)
    chosen = select_matrix(matrix, key, authorization).iloc[0]
    parent = read_json(PROPOSAL)
    if tuple(parent[k] for k in KEY_COLUMNS) == tuple(key):
        for name in ['data_hash', 'role_bank_hash', 'fit_n', 'calibration_n', 'test_n']:
            if chosen[name] != parent[name]:
                raise ValueError('matrix/proposal mismatch: ' + name)
    out = Path(design_dir)
    if out.exists() and any(p.resolve()!=Path(authorization_path).resolve() for p in out.iterdir()):
        raise ValueError('design already exists; preserve it and use a new version')
    out.mkdir(parents=True, exist_ok=True)
    from .run_study import load_config, resolve_dataset_config
    study = ROOT / 'configs/study_final_dissertation_v2.yaml'
    dataset_cfg = resolve_dataset_config(load_config(study), key[0])
    inherited = read_json(ROOT / 'configs/model_comparison_pilot_v1.json')
    config = {k: parent[k] for k in [*KEY_COLUMNS, 'models', 'nominal_levels', 'candidates', 'sequence_length',
                                   'interval_construction', 'inner_validation_folds', 'selection_metric', 'tie_rule',
                                   'final_lstm_epochs', 'minimum_launch_available_ram_bytes', 'minimum_free_disk_bytes']}
    config.update(dict(zip(KEY_COLUMNS, key)))
    config.update(inference_batch_size=inherited['inference_batch_size'], threads=1, n_jobs=1,
                  minimum_epoch_available_ram_bytes=parent['epoch_guard_bytes'], memory_sampling_seconds=.05,
                  clipping=False, missing_policy='unchanged existing causal preprocessing and common support',
                  device='cpu', fallback=None, prediction_reload_atol=1e-7, prediction_reload_rtol=1e-7,
                  metric_atol=1e-12, metric_rtol=1e-12, numeric_input='flat original dtype; lazy float32, normalization float64',
                  lstm_early_improvement=1e-6, lstm_loss='MSELoss', optimizer='Adam',
                  optimizer_defaults=dict(betas=[.9,.999], eps=1e-8, weight_decay=0, amsgrad=False),
                  xgboost_fixed=dict(objective='reg:squarederror', tree_method='hist', random_state=key[3], n_jobs=1),
                  xgboost_default_policy='None wrapper values delegate to the pinned library; full wrapper params frozen and actual booster config saved',
                  inference_clipping=False, test_selection=False)
    setup_threads()
    from xgboost import XGBRegressor
    config['xgboost_wrapper_parameters'] = [XGBRegressor(**p, **config['xgboost_fixed']).get_params(deep=True)
                                            for p in config['candidates']['xgboost']]
    with PhaseMeter() as meter:
        prepared = prepare(dataset_cfg)
        data = build_support(prepared, dataset_cfg, key[1], config['sequence_length'])
        roles = forecast_roles(data['meta'], key[1], prepared.freq, key[2], key[0]=='rico')
        records = role_records(data['meta'], roles)
    if data['data_hash'] != chosen['data_hash'] or signature(records) != chosen['role_bank_hash']:
        raise ValueError('fresh source data/roles do not match proposal; no fitting permitted')
    published = Path(matrix).parent / f'{key[0]}_h{key[1]}_forecast_membership.csv.gz'
    membership = pd.read_csv(published, keep_default_na=False)
    for name, rows in roles.items():
        expected = membership[membership[f'fold{key[2]}_roles'].str.split('|').apply(lambda names: name in names)]
        if len(rows)!=len(expected) or set(data['meta'].iloc[rows].row_id) != set(expected.row_id):
            raise ValueError('published membership mismatch: ' + name)
    frames = [data['meta'].iloc[rows][['row_id','group_id','origin_time','target_time']].assign(role=name)
              for name, rows in roles.items()]
    export_identifiers(pd.concat(frames, ignore_index=True)).to_csv(out/'membership.csv.gz', index=False, compression={'method':'gzip','mtime':0})
    boundary = [dict(left=left, right=right, **SI.boundary_record(data['meta'], roles[left], roles[right],
                SI.GROUPED if key[0]=='rico' else 'chronological')) for left, right in ROLE_PAIRS]
    pd.DataFrame(boundary).to_csv(out/'boundaries.csv', index=False)
    inputs = [PROPOSAL, Path(matrix).resolve(), published.resolve(), Path(matrix).parent.resolve()/'forecast_roles.csv',
              study, ROOT/'configs/model_comparison_pilot_v1.json', Path(authorization_path).resolve()]
    support = dict(data_hash=data['data_hash'], role_bank_hash=signature(records), roles=records,
                   feature_names=data['feature_names'], sequence_channels=data['sequence_channels'],
                   eligible_rows=len(data['meta']), excluded_rows=data['excluded_rows'],
                   frequency=str(prepared.freq), target=dataset_cfg.get('target'))
    protocol = dict(version=f'matched_forecasting005_{key[0]}_h{key[1]}_f{key[2]}_s{key[3]}_execution_v1', config=config, support=support,
                    resolved_dataset_config=dataset_cfg, authorization=authorization, parent_review_commit=PARENT,
                    instruction_commit=INSTRUCTION, frozen_utc=datetime.now(timezone.utc).isoformat(),
                    source_hash=source_digest(), packages=versions(), matrix_hash=digest(matrix),
                    input_hashes={p.relative_to(ROOT).as_posix(): digest(p) for p in inputs},
                    membership_hash=digest(out/'membership.csv.gz'), boundaries_hash=digest(out/'boundaries.csv'),
                    preparation_resources=meter.result, models_fitted=0, full_study_ready=False)
    write_json(out/'frozen_protocol.json', protocol, exclusive=True)
    return dict(frozen=True, models_fitted=0, data_hash=support['data_hash'], role_bank_hash=support['role_bank_hash'], roles=records)


def readiness(protocol_path, matrix, key, receipt):
    setup_threads()
    protocol = check_identity(protocol_path, matrix, key)
    with forbid_fitting(), PhaseMeter() as meter:
        data, roles = fresh_data(protocol)
    from .pilot_conformal import calibrate_absolute
    rank_checks = [calibrate_absolute(data['y'][roles['calibration']], np.zeros(len(roles['calibration'])), l)['status']
                   for l in protocol['config']['nominal_levels']]
    folder = Path(protocol_path).parent
    if digest(folder/'membership.csv.gz') != protocol['membership_hash'] or digest(folder/'boundaries.csv') != protocol['boundaries_hash']:
        raise ValueError('frozen support file mismatch')
    resources = resource_reading(protocol['config'], protocol['authorization'], ROOT)
    result = dict(first_unit_ready=all(v=='ok' for v in rank_checks), full_study_ready=False, models_fitted=0,
                  source_hash=source_digest(), protocol_hash=digest(protocol_path), fresh_support_verified=True,
                  resources=resources, preparation_resources=meter.result, expected_point_cells=3, expected_interval_cells=6)
    write_json(receipt, result, exclusive=True)
    if not result['first_unit_ready']:
        raise ValueError('first-unit readiness failed')
    return result


def checkpoint_spec(protocol_path, protocol):
    return dict(protocol_hash=digest(protocol_path), source_hash=protocol['source_hash'],
                config=protocol['config'], data_hash=protocol['support']['data_hash'],
                role_bank_hash=protocol['support']['role_bank_hash'], packages=protocol['packages'])


def execute(protocol_path, matrix, key, out, ready_path, *, resume=False, forbid_fits=False, receipt=None):
    setup_threads()
    protocol = check_identity(protocol_path, matrix, key)
    cfg = protocol['config']
    ready = read_json(ready_path)
    if not ready['first_unit_ready'] or ready['protocol_hash'] != digest(protocol_path) or ready['source_hash'] != source_digest():
        raise ValueError('readiness identity mismatch')
    root = Path(out)
    if resume and not (root/'checkpoint_manifest.json').exists():
        raise ValueError('resume requires an existing checkpoint manifest')
    store = UnitCheckpoint(root, checkpoint_spec(protocol_path, protocol), resume=resume,
                           string_columns=('row_id','group_id'))
    expected = [unit_key(cfg, name) for name in cfg['models']]
    complete = [name for name in expected if store.verify(name) is not None]
    if forbid_fits and len(complete) != len(expected):
        raise ValueError('forbidden-fit resume requires all model units complete')
    before = {p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file()} if resume else {}
    with PhaseMeter() as preparation:
        data, roles = fresh_data(protocol)
    if len(complete) == len(expected) and resume:
        store.require_complete(expected)
        for filename in ['point_summary.csv','interval_quality.csv','run_summary.json']:
            if not (root/filename).exists():
                raise ValueError('completed unit summaries missing')
        result = dict(status='complete', action='resume', models_fitted=0, reused_model_units=len(expected),
                      fresh_data_identity_verified=True, preparation_resources=preparation.result,
                      protocol_hash=digest(protocol_path), source_hash=source_digest())
        after = {p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file()}
        if before != after:
            raise ValueError('completed resume modified scientific evidence')
        result['all_run_files_unchanged'] = True
        if receipt:
            write_json(receipt, result, exclusive=True)
        return result
    if not (root/'execution_environment.json').exists():
        write_json(root/'execution_environment.json', dict(hardware=hardware(), packages=versions(),
                   code_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                   source_hash=source_digest(), protocol_hash=digest(protocol_path), command=sys.argv,
                   start_utc=datetime.now(timezone.utc).isoformat(), preparation_resources=preparation.result,
                   authorization=protocol['authorization'], cpu_only=True))
    points, intervals, io_records = [], [], []
    try:
        for name in cfg['models']:
            unit = unit_key(cfg, name)
            if unit in complete:
                payload = read_json(root/'units'/unit/'payload.json')
                print('REUSED ' + unit, flush=True)
            else:
                launch = resource_reading(cfg, protocol['authorization'], root)
                print(f"LAUNCH {unit}; available RAM={launch['available_ram_bytes']/2**30:.2f} GiB", flush=True)
                payload, frames, artifacts = run_model(name, data, roles, cfg, root/'fit_calls.jsonl')
                payload['launch_resources'] = launch
                with PhaseMeter() as write_meter:
                    store.save(unit, payload, frames, artifacts=artifacts)
                io_records.append(dict(unit=unit, **write_meter.result))
                del frames, artifacts
                gc.collect()
            points.append(payload['point'])
            intervals.extend(payload['intervals'])
            pd.DataFrame(points).to_csv(root/'point_summary.csv', index=False)
            pd.DataFrame(intervals).to_csv(root/'interval_quality.csv', index=False)
            print('COMPLETE ' + unit, flush=True)
        store.require_complete(expected)
        require_cells(pd.DataFrame(points), ['model'], [(m,) for m in cfg['models']])
        require_cells(pd.DataFrame(intervals), ['model','nominal_level'], [(m,l) for m in cfg['models'] for l in cfg['nominal_levels']])
        # Keep previous partial-resume I/O evidence under its original timestamp.
        write_json(root/f"checkpoint_io_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}.json", io_records, exclusive=True)
        result = dict(status='complete', point_cells=len(points), interval_cells=len(intervals),
                      learned_tuning_fits=sum(p['learned_tuning_fits'] for p in points),
                      learned_final_fits=sum(p['learned_final_fits'] for p in points),
                      models=cfg['models'], source_hash=source_digest(), protocol_hash=digest(protocol_path),
                      full_study_ready=False, publication_ready=False)
        write_json(root/'run_summary.json', result)
        return result
    except BaseException as exc:
        write_json(root/f"failure_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}.json",
                   dict(error=str(exc), traceback=traceback.format_exc()), exclusive=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze','readiness','run','validate','resume'])
    parser.add_argument('--matrix', required=True)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--horizon', type=int, required=True)
    parser.add_argument('--outer-fold', type=int, required=True)
    parser.add_argument('--model-seed', type=int, required=True)
    parser.add_argument('--out')
    parser.add_argument('--design-dir')
    parser.add_argument('--protocol')
    parser.add_argument('--authorization')
    parser.add_argument('--readiness')
    parser.add_argument('--receipt')
    parser.add_argument('--forbid-fits', action='store_true')
    args = parser.parse_args()
    key = (args.dataset,args.horizon,args.outer_fold,args.model_seed)
    stem = f'{key[0]}_h{key[1]}_f{key[2]}_s{key[3]}_v1'
    design = Path(args.design_dir or f'protocols/matched_forecasting005/{stem}')
    protocol = Path(args.protocol or design/'frozen_protocol.json')
    ready = Path(args.readiness or design/'readiness.json')
    if args.action == 'freeze':
        result = freeze(args.matrix, key, design, args.authorization or design/'authorization.json')
    elif args.action == 'readiness':
        result = readiness(protocol, args.matrix, key, args.receipt or ready)
    elif args.action == 'validate':
        from .matched_validation005 import validate
        if not args.out or not args.receipt:
            parser.error('validate requires --out run directory and --receipt fresh audit directory')
        result = validate(args.out, protocol, args.matrix, key, args.receipt)
    else:
        if not args.out:
            parser.error('run/resume requires --out')
        if args.action == 'resume' and args.forbid_fits:
            with forbid_fitting() as calls:
                result = execute(protocol, args.matrix, key, args.out, ready, resume=True, forbid_fits=True, receipt=args.receipt)
            if calls:
                raise AssertionError('forbidden fit route invoked')
        else:
            result = execute(protocol, args.matrix, key, args.out, ready, resume=args.action=='resume', receipt=args.receipt)
    return result, args


if __name__ == '__main__':
    with PhaseMeter() as command_action:
        result, args = main()
    if args.action in ['run','resume']:
        process = dict(action=args.action, action_resources=command_action.result,
                       process_lifetime_cpu_seconds=time.process_time(), ending_memory=memory_snapshot(),
                       timing_scope='action excludes interpreter/import startup; lifetime CPU includes it')
        target = str(args.receipt)+'.process.json' if args.action=='resume' and args.receipt else str(args.out)+'.process.json'
        write_json(target, process, exclusive=True)
    print(json.dumps(result, indent=2, default=str), flush=True)
