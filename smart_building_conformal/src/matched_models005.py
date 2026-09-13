"""Measured matched model unit using the preserved pilot fitting routines."""
import contextlib
import gc
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import metrics as M
from . import pilot_forecasters as F
from .matched_data005 import validate_roles
from .pilot_conformal import calibrate_absolute, fixed_bounds
from .pilot_data import role_records
from .pilot_resources import ResourceMeter
from .unit_checkpoint import signature


class PhaseMeter(ResourceMeter):
    def __enter__(self):
        self.cpu_start = time.process_time()
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.result['process_cpu_seconds'] = time.process_time() - self.cpu_start


@contextlib.contextmanager
def forbid_fitting():
    """Block learned fitting before its body; permit torch eval/train(False)."""
    calls = []
    old = sys.getprofile()
    def guard(frame, event, arg):
        module = frame.f_globals.get('__name__', '')
        name = frame.f_code.co_name
        if event == 'call' and ((name in {'fit', 'partial_fit', 'fit_once', 'run_model'} and
                                module.startswith(('src.', 'xgboost.', 'sklearn.', 'mapie.'))) or
                               (name == 'train' and module.startswith('xgboost.'))):
            calls.append(module + '.' + name)
            raise AssertionError('fitting forbidden: ' + calls[-1])
    sys.setprofile(guard)
    try:
        yield calls
    finally:
        sys.setprofile(old)


def unit_key(config, model):
    return f"{config['dataset']}_h{config['horizon']}_f{config['outer_fold']}_s{config['model_seed']}_{model}"


def append_record(path, record):
    if path is not None:
        with Path(path).open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record, default=str) + '\n')
            stream.flush()
            os.fsync(stream.fileno())


def run_model(name, data, roles, config, journal=None):
    validate_roles(data['meta'], roles, config['dataset'] == 'rico')
    seed, batch = config['model_seed'], config['inference_batch_size']
    key = unit_key(config, name)
    tag = {k: config[k] for k in ['dataset', 'horizon', 'outer_fold', 'model_seed']}
    tag.update(model=name, evidence_status='matched_forecasting005')
    scores, histories, tuning_predictions, fits = [], [], [], []

    def fit_once(params, rows, phase, candidate, fold=None, validation=None, epochs=None):
        record = dict(unit=key, phase=phase, candidate_id=candidate, inner_fold=fold,
                      n_train=len(rows), train_row_id_hash=signature(data['meta'].iloc[rows].row_id.tolist()),
                      validation_row_id_hash=signature(data['meta'].iloc[validation].row_id.tolist()) if validation is not None else None,
                      parameters=params, seed=seed, final_epochs=epochs)
        append_record(journal, dict(record, event='started', pid=os.getpid()))
        with PhaseMeter() as meter:
            model = F.fit(name, data, rows, params, seed, validation=validation, final_epochs=epochs,
                          memory_floor=config['minimum_epoch_available_ram_bytes'],
                          progress=lambda row: print(f"{key} {phase} c{candidate} i{fold}: {row}", flush=True))
        record.update(estimator_class=F.actual_identity(model), **meter.result)
        fits.append(record)
        append_record(journal, dict(record, event='complete', pid=os.getpid()))
        return model

    with PhaseMeter() as tuning:
        if name == 'persistence':
            selected, final_epochs = 0, None
        else:
            for candidate, params in enumerate(config['candidates'][name]):
                for fold in range(2):
                    train, val = roles[f'inner{fold}_train'], roles[f'inner{fold}_validation']
                    print(f'START {key} tuning candidate={candidate} inner={fold}', flush=True)
                    start = time.perf_counter()
                    model = fit_once(params, train, 'tuning', candidate, fold, val)
                    pred = F.predict(model, name, data, val, batch)
                    scores.append(dict(candidate_id=candidate, inner_fold=fold,
                                       mae=M.mae(data['y'][val], pred), best_epoch=getattr(model, 'best_epoch', None),
                                       seconds=time.perf_counter()-start, n_train=len(train), n_validation=len(val),
                                       estimator_class=F.actual_identity(model)))
                    frame = data['meta'].iloc[val][['row_id', 'group_id', 'origin_time', 'target_time']].copy()
                    frame = frame.assign(y_true=data['y'][val], point=pred, candidate_id=candidate, inner_fold=fold)
                    tuning_predictions.append(frame)
                    histories.extend(dict(candidate_id=candidate, inner_fold=fold, **row) for row in getattr(model, 'history', []))
                    del model
                    gc.collect()
            selected, final_epochs, _ = F.select_candidate(scores)
    params = config['candidates'][name][selected]
    print(f'START {key} final candidate={selected} epochs={final_epochs}', flush=True)
    with PhaseMeter() as final_fit:
        model = F.Persistence(data['X'].columns) if name == 'persistence' else fit_once(
            params, roles['fit'], 'final_fit', selected, epochs=final_epochs)
    with PhaseMeter() as calibration:
        cal_point = F.predict(model, name, data, roles['calibration'], batch)
        calibrations = [calibrate_absolute(data['y'][roles['calibration']], cal_point, level)
                        for level in config['nominal_levels']]
    with PhaseMeter() as inference:
        point = F.predict(model, name, data, roles['test'], batch)
    if not np.isfinite(point).all() or not np.isfinite(cal_point).all():
        raise ValueError('nonfinite prediction')
    tag['estimator_class'] = F.actual_identity(model)
    base = data['meta'].iloc[roles['test']][['row_id', 'group_id', 'origin_time', 'target_time']].copy()
    base['y_true'], base['point'] = data['y'][roles['test']], point
    intervals, predictions = [], []
    for c in calibrations:
        lower, upper = fixed_bounds(point, c)
        good = c['status'] == 'ok'
        intervals.append(dict(tag, **c, n_evaluation=len(point), construction=config['interval_construction'],
                              coverage=M.empirical_coverage(base.y_true, lower, upper) if good else None,
                              mpiw=M.mean_interval_width(lower, upper) if good else None,
                              winkler=M.winkler_score(base.y_true, lower, upper, 1-c['nominal_level']) if good else None,
                              negative_lower_bounds=int((lower < 0).sum())))
        predictions.append(base.assign(nominal_level=c['nominal_level'], lower=lower, upper=upper, **tag))
    cal = data['meta'].iloc[roles['calibration']][['row_id', 'group_id', 'origin_time', 'target_time']].copy()
    cal = cal.assign(y_true=data['y'][roles['calibration']], point=cal_point)
    cal['absolute_error'] = np.abs(cal.y_true-cal.point)
    resources = {k: v.result for k, v in [('tuning', tuning), ('final_fit', final_fit), ('calibration', calibration), ('inference', inference)]}
    row = dict(tag, mae=M.mae(base.y_true, point), rmse=M.rmse(base.y_true, point),
               n_fit=len(roles['fit']), n_calibration=len(cal), n_evaluation=len(point),
               selected_candidate=selected, final_epochs=final_epochs,
               tuning_seconds=resources['tuning']['seconds'] if name != 'persistence' else 0.,
               final_fit_seconds=resources['final_fit']['seconds'], calibration_seconds=resources['calibration']['seconds'],
               inference_seconds=resources['inference']['seconds'], inference_batch_size=batch,
               inference_rows_per_second=len(point)/resources['inference']['seconds'],
               baseline_rss_bytes=tuning.result['baseline_rss_bytes'],
               peak_rss_bytes=max(r['peak_rss_bytes'] for r in resources.values()),
               peak_private_bytes=max(r['peak_private_bytes'] for r in resources.values()),
               process_cpu_seconds=sum(r['process_cpu_seconds'] for r in resources.values()),
               learned_tuning_fits=sum(r['phase']=='tuning' for r in fits),
               learned_final_fits=sum(r['phase']=='final_fit' for r in fits),
               negative_predictions=int((point < 0).sum()), status='complete')
    with PhaseMeter() as serialization:
        if name == 'attention_lstm':
            artifact = {'model.pt': model.artifact()}
            actual_params = dict(model.params, final_epochs=final_epochs, optimizer='torch.optim.Adam',
                                 optimizer_defaults=dict(betas=[.9,.999], eps=1e-8, weight_decay=0, amsgrad=False),
                                 loss='MSELoss', device=str(next(model.model.parameters()).device),
                                 dtype=str(next(model.model.parameters()).dtype))
        elif name == 'xgboost':
            artifact = {'model.ubj': bytes(model.get_booster().save_raw(raw_format='ubj')),
                        'booster_config.json': model.get_booster().save_config().encode()}
            actual_params = model.get_params(deep=True)
        else:
            artifact = {'model.json': json.dumps(dict(estimator_class=F.actual_identity(model), column=model.column)).encode()}
            actual_params = dict(column=model.column, learned_fits=0)
    resources['artifact_serialization'] = serialization.result
    payload = dict(point=row, intervals=intervals, parameters=params, actual_parameters=actual_params,
                   resources=resources, model_seed=seed, selected_candidate=selected, final_epochs=final_epochs,
                   roles=role_records(data['meta'], roles), feature_names=data['feature_names'],
                   sequence_channels=data['sequence_channels'], data_hash=data['data_hash'],
                   calibration_construction=config['interval_construction'], fixed_calibration=True,
                   fallback=None, clipping=False, learned_fits=len(fits), fitting_records=fits)
    frames = dict(predictions=pd.concat(predictions, ignore_index=True), calibration=cal,
                  tuning=pd.DataFrame(scores), training_history=pd.DataFrame(histories),
                  tuning_predictions=pd.concat(tuning_predictions, ignore_index=True) if tuning_predictions else pd.DataFrame(),
                  fitting_membership=data['meta'].iloc[roles['fit']][['row_id', 'group_id', 'origin_time', 'target_time']].copy())
    del model
    gc.collect()
    return payload, frames, artifact


def restore(name, directory, data):
    directory = Path(directory)
    if name == 'attention_lstm':
        state = F.torch.load(directory / 'model.pt', map_location='cpu', weights_only=True)
        model = F.LazyLSTM()
        model.model = F.AttentionLSTM(state['input_features'], state['parameters']['hidden_size'], state['parameters']['dropout'])
        model.model.load_state_dict(state['state_dict'])
        model.mean, model.std = np.asarray(state['x_mean']), np.asarray(state['x_std'])
        model.y_mean, model.y_std = state['y_mean'], state['y_std']
        model.params, model.seed = state['parameters'], state['seed']
        return model
    if name == 'xgboost':
        from xgboost import XGBRegressor
        model = XGBRegressor(n_jobs=1, device='cpu')
        model.load_model(directory / 'model.ubj')
        return model
    state = json.loads((directory / 'model.json').read_text())
    model = F.Persistence(data['X'].columns)
    if state['column'] != model.column:
        raise ValueError('persistence schema mismatch')
    return model
