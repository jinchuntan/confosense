"""Recompute diagnostic scores from saved development predictions; no fitting."""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
args = ap.parse_args()
root = Path(__file__).resolve().parents[2]
project = root / 'smart_building_conformal'
base = project / 'outputs/pilot_diagnostics_v1'
diag = base / 'inner_reproduction'
pilot = project / 'outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913'
scores = pd.read_csv(diag / 'matched_inner_metrics.csv')
assert len(scores) == 30
assert not scores.duplicated(['horizon', 'inner_fold', 'model', 'candidate_id']).any()
references = {}
checked = []
for row in scores.itertuples(index=False):
    folder = diag / f'h{row.horizon}_{row.model}_c{row.candidate_id}_inner{row.inner_fold}'
    data = pd.read_csv(folder / 'development_predictions.csv.gz')
    assert set(data.role) == {'train', 'validation'}
    assert not data.duplicated(['role', 'row_id']).any()
    for role in ['train', 'validation']:
        frame = data[data.role == role]
        keys = frame[['row_id', 'group_id', 'origin_time', 'target_time', 'truth']].reset_index(drop=True)
        key = (row.horizon, row.inner_fold, role)
        if key in references:
            pd.testing.assert_frame_equal(keys, references[key])
        else:
            references[key] = keys
        assert len(frame) == getattr(row, 'n_' + role)
        assert np.isfinite(frame[['truth', 'prediction']].to_numpy()).all()
        error = frame.prediction.to_numpy() - frame.truth.to_numpy()
        measured = dict(mae=np.abs(error).mean(), rmse=np.sqrt(np.mean(error**2)),
                        prediction_minus_truth_bias=error.mean())
        for metric, value in measured.items():
            np.testing.assert_allclose(value, getattr(row, role + '_' + metric), atol=1e-12, rtol=1e-12)
        origin = pd.to_datetime(frame.origin_time)
        target = pd.to_datetime(frame.target_time)
        assert (target - origin == pd.Timedelta(minutes=10 * row.horizon)).all()
    if row.model != 'persistence':
        original = pd.read_csv(pilot / f'units/h{row.horizon}_f0_s42_{row.model}/tuning.csv.gz')
        saved = original[(original.candidate_id == row.candidate_id) & (original.inner_fold == row.inner_fold)].iloc[0]
        np.testing.assert_allclose(row.validation_mae, saved.mae, rtol=1e-10, atol=1e-10)
        if row.model == 'attention_lstm':
            assert row.best_epoch == saved.best_epoch
            history = pd.read_csv(folder / 'history.csv')
            old_history = pd.read_csv(pilot / f'units/h{row.horizon}_f0_s42_attention_lstm/training_history.csv.gz')
            old_history = old_history[(old_history.candidate_id == row.candidate_id)
                                      & (old_history.inner_fold == row.inner_fold)]
            np.testing.assert_allclose(history[['epoch', 'train_mse', 'validation_mae']],
                old_history[['epoch', 'train_mse', 'validation_mae']], atol=1e-10, rtol=1e-10)
            best, best_epoch, stale = float('inf'), None, 0
            for epoch in history.itertuples(index=False):
                if epoch.validation_mae < best - 1e-6:
                    best, best_epoch, stale = epoch.validation_mae, epoch.epoch, 0
                else:
                    stale += 1
            assert best_epoch == row.best_epoch
            np.testing.assert_allclose(best, row.validation_mae, atol=1e-10, rtol=1e-10)
            assert len(history) == 30 or stale == 5
    checked.append(dict(horizon=row.horizon, inner_fold=row.inner_fold, model=row.model,
                        candidate_id=row.candidate_id, passed=True))

final_epochs = {}
for h in [1, 3, 6]:
    payload = json.loads((pilot / f'units/h{h}_f0_s42_attention_lstm/payload.json').read_text())
    lstm = scores[(scores.horizon == h) & (scores.model == 'attention_lstm')]
    selected = min((float(group.validation_mae.mean()), int(candidate))
                   for candidate, group in lstm.groupby('candidate_id'))[1]
    epochs = int(np.ceil(lstm[lstm.candidate_id == selected].best_epoch.mean()))
    assert selected == payload['selected_candidate'] and epochs == payload['final_epochs']
    final_epochs[h] = epochs

before = json.loads((base / 'memory_before/preparation.json').read_text())
after = json.loads((base / 'memory_after/preparation.json').read_text())
equal_keys = ['prepared_frame_hash', 'selection_audit_hash', 'selected_target', 'support']
for key in equal_keys:
    assert before[key] == after[key], key
assert before['models_fitted'] == after['models_fitted'] == 0
memory = []
for label, result in [('before', before), ('after', after)]:
    for stage in [dict(stage='total', **result['total_resources']), *result['stages']]:
        memory.append(dict(version=label, **{k: v for k, v in stage.items() if k != 'columns'}))
pd.DataFrame(memory).to_csv(base / 'memory_comparison.csv', index=False)

# Compare immutable pilot bytes with the task-entry commit, not the altered
# current source tree. These paths have -text attributes, preserving Git bytes.
paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only',
    'a5b32b81266efc107ad0bfdf74f95139ee99ba77', '--',
    'smart_building_conformal/outputs/model_comparison_pilot_v1',
    'smart_building_conformal/protocols/model_comparison_pilot_v1',
    'smart_building_conformal/configs/model_comparison_pilot_v1.json'], cwd=root, text=True).splitlines()
for path in paths:
    old = subprocess.check_output(['git', 'show', 'a5b32b81266efc107ad0bfdf74f95139ee99ba77:' + path], cwd=root)
    assert (root / path).read_bytes() == old, path

result = dict(status='passed', recomputed_development_cells=len(checked),
    matched_supports=len(references), unchanged_learned_fits_reproduced=24,
    complete_lstm_learning_histories_reproduced=12,
    final_epoch_choices=final_epochs, memory_identity_checks=equal_keys,
    memory_peak_reduction_fraction=1-after['total_resources']['peak_rss_bytes']/before['total_resources']['peak_rss_bytes'],
    original_pilot_files_byte_identical=len(paths), new_outer_or_final_fits=0,
    global_study_ready=False, checks=checked)
Path(args.out).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'checks'}, indent=2))
