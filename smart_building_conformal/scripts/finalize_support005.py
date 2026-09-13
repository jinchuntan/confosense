"""No-fit supplementary verification: rank IDs, phase support and joint horizons.

Consumes published row tables; does not open learned predictions or raw caches.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from support_design005 import BASE, ROOT, digest, no_fitting, signature


def main(base, plan, out):
    base, plan, out = map(Path, (base, plan, out))
    out.mkdir(parents=True, exist_ok=False)
    rank = pd.read_csv(BASE / 'calibration_rank_support.csv', keep_default_na=False,
                       na_values={'window': ['']})
    rank = rank[rank.dataset.ne('bdg2')]
    keys = ['dataset', 'outer_fold', 'role', 'method', 'level', 'strategy', 'window']
    corrected = rank.groupby(keys, dropna=False).agg(
        groups=('group_id', 'nunique'), initial_n_min=('initial_calibration_n', 'min'),
        initial_rank_all=('initial_rank_supported', 'all'),
        online_n_min=('update_pool_n', 'min'), online_rank_all=('online_rank_supported', 'all')
    ).reset_index()
    original = pd.read_csv(base / 'rank_support.csv')
    pd.testing.assert_frame_equal(corrected.drop(columns='groups'), original.drop(columns='groups'))
    changed = corrected.groups.ne(original.groups)
    assert corrected.loc[changed, 'dataset'].isin(['pleia', 'pleia_energy']).all()
    assert corrected.loc[changed, 'groups'].eq(1).all() and original.loc[changed, 'groups'].eq(0).all()
    corrected.to_csv(out / 'rank_support_verified.csv', index=False)
    correction = corrected.loc[changed, keys + ['groups']].copy()
    correction['old_groups'] = original.loc[changed, 'groups']
    correction['reason'] = 'Preserve literal group ID None; no rank/support value changes'
    correction.to_csv(out / 'rank_identifier_corrections.csv', index=False)

    contexts = pd.read_csv(base / 'challenge_contexts.csv', keep_default_na=False)
    history = pd.read_csv(plan / 'rico_run_history.csv', keep_default_na=False)
    phases = history.set_index('group_id').phase.astype(float).astype(int).to_dict()
    precision = pd.read_csv(plan / 'challenge_precision_support.csv')
    rows = []
    for p in precision.itertuples(index=False):
        ctx = contexts[(contexts.dataset == p.dataset) & (contexts.outer_fold == p.outer_fold)
                       & (contexts.role == p.role)]
        assert len(ctx) == p.contexts
        phase_counts = ctx.group_id.map(phases).value_counts().to_dict() if p.dataset == 'rico' else {}
        if p.dataset == 'rico':
            assert ctx.group_id.is_unique and sum(phase_counts.values()) == len(ctx)
        phase_ok = not phase_counts or min(phase_counts.values()) >= 2
        eligible = bool(p.minimum_five_blocks_met and phase_ok)
        reason = ('fewer than five complete original blocks' if not p.minimum_five_blocks_met
                  else 'represented acquisition phase has fewer than two original runs' if not phase_ok
                  else 'structural screen passes; actual precision and valid bootstrap draws unmeasured')
        rows.append(dict(dataset=p.dataset, outer_fold=p.outer_fold, role=p.role, contexts=len(ctx),
                         complete_original_blocks=p.complete_original_inference_blocks,
                         phase_counts=json.dumps({str(k): int(v) for k, v in phase_counts.items()}, sort_keys=True),
                         minimum_two_runs_per_phase=phase_ok, structural_ci_screen=eligible, reason=reason,
                         bootstrap_draws=2000, bootstrap_seed=20240601, required_valid_draws=1900,
                         measured_precision=False))
    pd.DataFrame(rows).to_csv(out / 'challenge_inference_support.csv', index=False)

    # Exactly one identity schedule per context, with no synthetic positive label.
    controls = contexts[['dataset', 'outer_fold', 'role', 'context_id', 'group_id',
                         'context_start_row_id', 'context_end_row_id', 'context_row_hash']].copy()
    controls['control_id'] = controls.context_id + ':clean_identity'
    controls['transformation'] = 'identity: original y and availability unchanged'
    controls['effective_positive'] = False
    controls['state'] = 'independent historical-calibration reset and causal clean warm-up'
    controls['future_acceptance'] = 'exact identity of inputs, bounds, alerts and released scores'
    controls['stream_identity_executed'] = False
    assert controls.control_id.is_unique
    controls.to_csv(out / 'challenge_zero_controls.csv', index=False)

    # DSCP requires common origins, not equality of horizon-dependent row IDs.
    joint, joint_membership = [], []
    matrix = pd.read_csv(base / 'experiment_matrix.csv')
    for ds, group in matrix.groupby('dataset'):
        horizons = sorted(group.horizon.unique())
        memberships = {int(h): pd.read_csv(base / f'{ds}_h{h}_forecast_membership.csv.gz',
                         keep_default_na=False) for h in horizons}
        for fi in range(3):
            role_sets = {}
            for role in ['fit', 'calibration', 'test']:
                parts = {h: m[m[f'fold{fi}_roles'].str.split('|').apply(lambda r: role in r)]
                         for h, m in memberships.items()}
                ids = [set(zip(p.group_id, p.origin_time)) for p in parts.values()]
                common = set.intersection(*ids)
                assert common
                role_sets[role] = common
                selected = []
                for h, p in parts.items():
                    pick = p[[key in common for key in zip(p.group_id, p.origin_time)]]
                    assert len(pick) == len(common)
                    selected.append(pick)
                max_target = max(pd.to_datetime(p.target_time).max() for p in selected)
                min_origin = min(pd.to_datetime(p.origin_time).min() for p in selected)
                joint.append(dict(dataset=ds, outer_fold=fi, role=role,
                                  horizons='|'.join(map(str, horizons)), common_origins=len(common),
                                  original_groups=len({g for g, _ in common}),
                                  origin_min=str(min_origin), target_max=str(max_target),
                                  common_origin_hash=signature(sorted(common)),
                                  calibration_minimum_400_met=len(common) >= 400,
                                  evaluated=False))
                joint_membership.extend(dict(dataset=ds, outer_fold=fi, role=role,
                                             group_id=g, origin_time=t) for g, t in sorted(common))
            assert not (role_sets['fit'] & role_sets['calibration'] or role_sets['calibration'] & role_sets['test'])
            own = joint[-3:]
            assert pd.Timestamp(own[0]['target_max']) < pd.Timestamp(own[1]['origin_min'])
            assert pd.Timestamp(own[1]['target_max']) < pd.Timestamp(own[2]['origin_min'])
            if ds == 'rico':
                assert not ({g for g, _ in role_sets['fit']} & {g for g, _ in role_sets['calibration']})
                assert not ({g for g, _ in role_sets['calibration']} & {g for g, _ in role_sets['test']})
    pd.DataFrame(joint).to_csv(out / 'dscp_joint_origin_support.csv', index=False)
    pd.DataFrame(joint_membership).to_csv(out / 'dscp_joint_origin_membership.csv.gz', index=False,
                                         compression={'method': 'gzip', 'mtime': 0})
    result = dict(passed=True, models_fitted=0, rank_summary_rows=len(corrected),
                  rank_identifier_corrections=int(changed.sum()), rank_values_unchanged=True,
                  inference_roles=len(rows), structural_ci_screens_unavailable=sum(not r['structural_ci_screen'] for r in rows),
                  identity_control_schedules=len(controls), fitted_stream_identity_executed=False,
                  dscp_joint_roles=len(joint), dscp_boundaries=24,
                  all_joint_calibrations_at_least_400=all(r['calibration_minimum_400_met'] for r in joint if r['role'] == 'calibration'),
                  current_generator_sha256=digest(ROOT / 'scripts/support_design005.py'),
                  script_sha256=digest(Path(__file__)), full_study_ready=False, publication_ready=False)
    (out / 'validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    with no_fitting():
        main(args.base, args.plan, args.out)
