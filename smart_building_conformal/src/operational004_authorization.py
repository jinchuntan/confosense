"""No-fitting identity checks for the two explicitly authorized BDG2 units."""
import json
from pathlib import Path
import pandas as pd
from . import split_integrity as SI
from .operational004_design import DESIGN
from .operational004_events import catalogue, bank_support
from .unit_checkpoint import digest


def verify_catalogues(w, roles, freq, fold, preflight):
    """Recreate all schedules from current inputs and compare published bytes/values."""
    preflight = Path(preflight)
    old = pd.read_csv(preflight/'catalogue_summary.csv', float_precision='round_trip')
    records, support = [], []
    for role, train in [('inner0_selection','inner0_train'),
                        ('inner1_selection','inner1_train'),('outer_test','final_fit')]:
        indices = roles[role]; block = w['meta'].iloc[indices].reset_index(drop=True)
        scale = SI.training_scale(w['y'], w['meta'], roles[train]); tables = []
        for seed in DESIGN['catalogue_seeds']:
            _, _, events, allocation = catalogue(w['y'][indices], block, freq, scale,
                                                 'bdg2', role, fold, seed)
            path = preflight/f'bdg2_f{fold}_{role}_e{seed}_catalogue.csv.gz'
            saved = pd.read_csv(path, float_precision='round_trip', converters={'group_id':str})
            pd.testing.assert_frame_equal(events, saved, check_exact=True)
            prior = old[(old.dataset=='bdg2') & (old.outer_fold==fold) &
                        (old.role==role) & (old.catalogue_seed==seed)].iloc[0]
            if allocation['catalogue_hash'] != prior.catalogue_hash:
                raise ValueError('current catalogue hash differs from published preflight')
            records.append(dict(outer_fold=fold, role=role, path=path.as_posix(),
                                preflight_file_sha256=digest(path), **allocation))
            tables.append(events)
        support.extend(dict(outer_fold=fold, role=role, **r) for r in bank_support(tables).to_dict('records'))
    return records, support


def authorize(spec, manifest_path, memberships):
    plan = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    if plan['execution_order'] != [1,0] or plan['model_seeds'] != [42]:
        raise ValueError('not the authorized two-unit sequence')
    if (spec['dataset'], spec['model_seed']) != ('bdg2',42) or spec['outer_fold'] not in [1,0]:
        raise ValueError('unit outside authorized manifest')
    for key in ['source_hash','config_hash','design_hash','data_hash','outcomes_hash','candidate_grid','catalogue_seeds','horizon']:
        if spec[key] != plan[key]: raise ValueError(f'frozen execution mismatch: {key}')
    unit = plan['units'][str(spec['outer_fold'])]
    if memberships != unit['membership_hashes']:
        raise ValueError('frozen execution membership mismatch')
    spec['execution_manifest_hash'] = digest(manifest_path)
    return unit
