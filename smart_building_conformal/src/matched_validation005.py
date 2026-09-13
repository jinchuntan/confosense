"""Independent saved-stream arithmetic and no-fit serialized-model verification."""
import gc
import json
import math
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
import numpy as np
import pandas as pd

from . import pilot_forecasters as F
from .matched_models005 import PhaseMeter, forbid_fitting, restore, unit_key
from .unit_checkpoint import UnitCheckpoint, digest, require_cells, signature


def close(actual, expected, atol=1e-12, rtol=1e-12):
    np.testing.assert_allclose(actual, expected, atol=atol, rtol=rtol)


def independent_selection(scores, history, predictions, config, name, data, roles):
    if name == 'persistence':
        if len(scores) or len(history) or len(predictions):
            raise ValueError('persistence must not be tuned')
        return 0, None
    require_cells(scores, ['candidate_id','inner_fold'], [(c,f) for c in range(2) for f in range(2)])
    means = []
    for candidate in range(2):
        errors = []
        for fold in range(2):
            records = predictions[(predictions.candidate_id==candidate)&(predictions.inner_fold==fold)]
            saved = scores[(scores.candidate_id==candidate)&(scores.inner_fold==fold)].iloc[0]
            rows = roles[f'inner{fold}_validation']
            assert records.row_id.tolist() == data['meta'].iloc[rows].row_id.tolist()
            close(records.y_true, data['y'][rows], atol=0, rtol=0)
            score = float(np.abs(records.y_true.to_numpy()-records.point.to_numpy()).mean())
            close(saved.mae, score)
            errors.append(score)
            assert int(saved.n_train)==len(roles[f'inner{fold}_train']) and int(saved.n_validation)==len(rows)
            if name == 'attention_lstm':
                h = history[(history.candidate_id==candidate)&(history.inner_fold==fold)].sort_values('epoch')
                assert h.epoch.tolist() == list(range(1,len(h)+1))
                best, best_epoch, stale = float('inf'), None, 0
                params = config['candidates'][name][candidate]
                for item in h.itertuples(index=False):
                    assert stale < params['patience']
                    if item.validation_mae < best-1e-6:
                        best, best_epoch, stale = item.validation_mae, item.epoch, 0
                    else:
                        stale += 1
                assert len(h)==params['max_epochs'] or stale==params['patience']
                assert int(saved.best_epoch)==best_epoch
                close(best, score, atol=1e-7, rtol=1e-7)
        means.append((float(np.mean(errors)), candidate))
    selected = min(means)[1]
    epochs = None if name != 'attention_lstm' else int(math.ceil(scores[scores.candidate_id==selected].best_epoch.mean()))
    return selected, epochs


def validate(run, protocol_path, matrix, key, audit_out):
    from .matched_forecasting005 import check_identity, checkpoint_spec, fresh_data, setup_threads, write_json
    setup_threads()
    root, out = Path(run), Path(audit_out)
    if out.resolve().is_relative_to(root.resolve()):
        raise ValueError('validation evidence must be outside immutable completed run')
    out.mkdir(parents=True, exist_ok=False)
    before = {p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file()}
    with forbid_fitting() as attempts, PhaseMeter() as overall:
        protocol = check_identity(protocol_path, matrix, key)
        config = protocol['config']
        with PhaseMeter() as preparation:
            data, roles = fresh_data(protocol)
        store = UnitCheckpoint(root, checkpoint_spec(protocol_path, protocol), resume=True, string_columns=('row_id','group_id'))
        keys = [unit_key(config, name) for name in config['models']]
        store.require_complete(keys)
        points = pd.read_csv(root/'point_summary.csv', float_precision='round_trip')
        intervals = pd.read_csv(root/'interval_quality.csv', float_precision='round_trip')
        require_cells(points, ['dataset','horizon','outer_fold','model_seed','model'], [(*key,m) for m in config['models']])
        require_cells(intervals, ['dataset','horizon','outer_fold','model_seed','model','nominal_level'],
                      [(*key,m,l) for m in config['models'] for l in config['nominal_levels']])
        point_rows, interval_rows, artifacts, selections, costs, fits = [], [], [], [], [], []
        for name in config['models']:
            unit = unit_key(config, name)
            payload, frames = store.load(unit)
            assert payload['roles']==protocol['support']['roles'] and payload['data_hash']==data['data_hash']
            assert payload['feature_names']==data['feature_names'] and payload['sequence_channels']==data['sequence_channels']
            assert payload['fallback'] is None and payload['clipping'] is False
            expected_class = {'persistence':'src.pilot_forecasters.Persistence', 'xgboost':'xgboost.sklearn.XGBRegressor',
                              'attention_lstm':'src.attention_lstm.AttentionLSTM'}[name]
            assert payload['point']['estimator_class']==expected_class
            fitrows = frames['fitting_membership']
            assert fitrows.row_id.tolist()==data['meta'].iloc[roles['fit']].row_id.tolist()
            cal = frames['calibration']
            assert cal.row_id.tolist()==data['meta'].iloc[roles['calibration']].row_id.tolist()
            assert cal.group_id.tolist()==data['meta'].iloc[roles['calibration']].group_id.astype(str).tolist()
            close(cal.y_true, data['y'][roles['calibration']], atol=0, rtol=0)
            absolute = np.abs(cal.y_true.to_numpy()-cal.point.to_numpy())
            close(cal.absolute_error, absolute)
            selected, epochs = independent_selection(frames['tuning'], frames['training_history'], frames['tuning_predictions'], config, name, data, roles)
            assert payload['selected_candidate']==selected and payload['final_epochs']==epochs
            assert payload['parameters']==config['candidates'][name][selected]
            selections.append(dict(model=name, selected_candidate=selected, final_epochs=epochs, independently_verified=True))
            saved_point = points[points.model==name].iloc[0]
            assert int(saved_point.selected_candidate)==selected
            assert (pd.isna(saved_point.final_epochs) if epochs is None else int(saved_point.final_epochs)==epochs)
            first_prediction = None
            for level in config['nominal_levels']:
                pred = frames['predictions'][frames['predictions'].nominal_level==level]
                assert pred.row_id.tolist()==data['meta'].iloc[roles['test']].row_id.tolist() and pred.row_id.is_unique
                assert pred.group_id.tolist()==data['meta'].iloc[roles['test']].group_id.astype(str).tolist()
                for column, value in zip(['dataset','horizon','outer_fold','model_seed','model'], (*key,name)):
                    assert pred[column].eq(value).all()
                close(pred.y_true, data['y'][roles['test']], atol=0, rtol=0)
                if first_prediction is not None:
                    close(pred.point, first_prediction, atol=0, rtol=0)
                first_prediction = pred.point.to_numpy()
                error = pred.y_true.to_numpy()-first_prediction
                mae, rmse = float(np.abs(error).mean()), float(np.sqrt(np.square(error).mean()))
                close(saved_point.mae, mae); close(saved_point.rmse, rmse)
                assert int(saved_point.n_fit)==len(roles['fit']) and int(saved_point.n_calibration)==len(cal) and int(saved_point.n_evaluation)==len(pred)
                rank = int((Decimal(len(cal)+1)*Decimal(str(level))).to_integral_value(rounding=ROUND_CEILING))
                q = float(np.sort(absolute)[rank-1]) if rank<=len(cal) else float('inf')
                lower, upper = first_prediction-q, first_prediction+q
                close(pred.lower, lower); close(pred.upper, upper)
                saved = intervals[(intervals.model==name)&(intervals.nominal_level==level)].iloc[0]
                assert int(saved['rank'])==rank and int(saved.n_calibration)==len(cal) and int(saved.n_evaluation)==len(pred)
                close(saved.q, q)
                values = dict(model=name, nominal_level=level, n_calibration=len(cal), n_evaluation=len(pred), rank=rank, q=q)
                if np.isfinite(q):
                    coverage = float(np.mean((pred.y_true>=lower)&(pred.y_true<=upper)))
                    width = float(np.mean(upper-lower))
                    winkler = float(np.mean(upper-lower+2/(1-level)*(np.maximum(lower-pred.y_true,0)+np.maximum(pred.y_true-upper,0))))
                    for label, value in [('coverage',coverage),('mpiw',width),('winkler',winkler)]:
                        close(saved[label], value)
                        values[label] = value
                    assert saved.status=='ok'
                else:
                    assert saved.status=='insufficient_calibration' and saved[['coverage','mpiw','winkler']].isna().all()
                values.update(negative_lower_bounds=int((lower<0).sum()), verified=True)
                interval_rows.append(values)
            point_rows.append(dict(model=name, mae=mae, rmse=rmse, n=len(first_prediction),
                                   negative_predictions=int((first_prediction<0).sum()), verified=True))
            with PhaseMeter() as reloading:
                model = restore(name, root/'units'/unit, data)
                for role, saved_values in [('calibration',cal.point.to_numpy()),('test',first_prediction)]:
                    actual = F.predict(model, name, data, roles[role], config['inference_batch_size'])
                    close(actual, saved_values, atol=config['prediction_reload_atol'], rtol=config['prediction_reload_rtol'])
                    artifacts.append(dict(model=name, role=role, n=len(actual), max_absolute_difference=float(np.max(np.abs(actual-saved_values))),
                                          atol=config['prediction_reload_atol'], rtol=config['prediction_reload_rtol'], fits=0, verified=True))
                if name=='attention_lstm':
                    total = np.zeros(data['lazy'].n_features); squares = total.copy(); count = 0
                    for start in range(0,len(roles['fit']),config['inference_batch_size']):
                        rows = roles['fit'][start:start+config['inference_batch_size']]
                        a = data['lazy'].take(data['sequence_rows'][rows]).astype(np.float64)
                        total += a.sum(axis=(0,1)); squares += np.square(a).sum(axis=(0,1)); count += a.shape[0]*a.shape[1]
                    mean = total/count; std = np.sqrt(np.maximum(0,squares/count-mean**2)); std[std<1e-12]=1.
                    close(model.mean, mean); close(model.std, std)
                    close(model.y_mean, data['y'][roles['fit']].mean()); close(model.y_std, data['y'][roles['fit']].std() or 1.)
                if name=='xgboost':
                    assert model.get_booster().num_boosted_rounds()==config['candidates'][name][selected]['n_estimators']
                    assert model.get_booster().feature_names==data['feature_names']
                del model
                gc.collect()
            costs.append(dict(model=name, phase='artifact_reload_and_predict_verification', nested=False, **reloading.result))
            for phase, record in payload['resources'].items():
                assert record['seconds']>=0 and record['process_cpu_seconds']>=0
                assert record['peak_rss_bytes']>=record['baseline_rss_bytes']
                assert record['incremental_peak_rss_bytes']==record['peak_rss_bytes']-record['baseline_rss_bytes']
                if phase in ['tuning','final_fit','calibration','inference']:
                    expected_seconds=0 if name=='persistence' and phase=='tuning' else record['seconds']
                    close(saved_point[phase+'_seconds'], expected_seconds)
                costs.append(dict(model=name, phase=phase, nested=False, **record))
            close(saved_point.inference_rows_per_second, len(first_prediction)/payload['resources']['inference']['seconds'])
            close(saved_point.process_cpu_seconds, sum(payload['resources'][p]['process_cpu_seconds'] for p in ['tuning','final_fit','calibration','inference']))
            records = payload['fitting_records']
            assert len(records)==(0 if name=='persistence' else 5)
            for record in records:
                role = 'fit' if record['phase']=='final_fit' else f"inner{record['inner_fold']}_train"
                assert record['train_row_id_hash']==signature(data['meta'].iloc[roles[role]].row_id.tolist())
                assert record['n_train']==len(roles[role])
                if record['phase']=='tuning':
                    vr = roles[f"inner{record['inner_fold']}_validation"]
                    assert record['validation_row_id_hash']==signature(data['meta'].iloc[vr].row_id.tolist())
                fits.append(dict(model=name, **record))
            del frames
            gc.collect()
        journal=[json.loads(line) for line in (root/'fit_calls.jsonl').read_text().splitlines()]
        completed=[r for r in journal if r['event']=='complete']; started=[r for r in journal if r['event']=='started']
        assert len(started)==len(completed)==len(fits)==10
        assert sum(r['phase']=='tuning' for r in completed)==8 and sum(r['phase']=='final_fit' for r in completed)==2
        for row in fits:
            match=[r for r in completed if r['unit']==row['unit'] and r['phase']==row['phase'] and r['candidate_id']==row['candidate_id'] and r['inner_fold']==row['inner_fold']]
            assert len(match)==1 and match[0]['train_row_id_hash']==row['train_row_id_hash']
        summary=json.loads((root/'run_summary.json').read_text())
        assert summary['point_cells']==3 and summary['interval_cells']==6 and summary['learned_tuning_fits']==8 and summary['learned_final_fits']==2
        for filename, rows in [('recomputed_point_metrics.csv',point_rows),('recomputed_interval_metrics.csv',interval_rows),
                               ('saved_model_verification.csv',artifacts),('independent_selection.csv',selections),
                               ('phase_measurements.csv',costs),('learned_fit_measurements.csv',fits)]:
            pd.DataFrame(rows).to_csv(out/filename,index=False)
    assert not attempts
    after = {p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file()}
    assert before==after
    result=dict(passed=True, models_fitted=0, point_cells=3, interval_cells=6, real_tuning_fits_verified=8,
                real_final_fits_verified=2, saved_model_prediction_checks=len(artifacts), own_calibration_verified=True,
                common_target_ids_verified=True, training_only_normalization_verified=True,
                candidate_and_epoch_selection_verified=True, all_run_files_unchanged=True,
                preparation_resources=preparation.result, total_validation_resources=overall.result,
                source_hash=protocol['source_hash'], protocol_hash=digest(protocol_path), full_study_ready=False)
    write_json(out/'validation.json',result,exclusive=True)
    return result
