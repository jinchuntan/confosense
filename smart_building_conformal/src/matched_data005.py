"""Versioned matched roles; compatibility with pilot and whole-run RICO batches."""
import numpy as np
from . import split_integrity as SI
from .pilot_data import pilot_roles

ROLE_PAIRS = [('fit', 'calibration'), ('calibration', 'test'),
              ('inner0_train', 'inner0_validation'), ('inner1_train', 'inner1_validation')]


def export_identifiers(frame):
    """Keep Python None and literal 'None' visible in the canonical CSV schema.

    Row identities already stringify groups when constructed. Do the same only
    at export; never change prepared metadata, feature values or role hashes.
    """
    result = frame.copy()
    if 'group_id' in result:
        result['group_id'] = result.group_id.map(str)
    return result


def grouped_batch_folds(meta):
    groups = sorted(meta.group_id.unique(),
                    key=lambda g: (meta.loc[meta.group_id.eq(g), 'origin_time'].min(), str(g)))
    if len(groups) < 10:
        raise ValueError('insufficient whole runs for five chronological blocks')
    step = len(groups) // 5
    positions = np.arange(len(meta))
    folds = []
    for fold in range(3):
        a = step * (4 - fold)
        b = len(groups) if fold == 0 else a + step
        pool = positions[meta.group_id.isin(groups[:a])]
        test = positions[meta.group_id.isin(groups[a:b])]
        fit, calibration = SI.refit_split(meta, pool, SI.GROUPED)
        SI.assert_boundary(meta, np.r_[fit, calibration], test, SI.GROUPED)
        folds.append(dict(train=fit, calibration=calibration, test=test))
    return folds


def validate_roles(meta, roles, grouped=False):
    required = {'fit', 'calibration', 'test', 'inner0_train', 'inner0_validation',
                'inner1_train', 'inner1_validation'}
    if set(roles) != required:
        raise ValueError('incomplete role set')
    for name, rows in roles.items():
        if not len(rows) or len(set(rows)) != len(rows) or min(rows) < 0 or max(rows) >= len(meta):
            raise ValueError('empty, duplicate or invalid role rows: ' + name)
    scheme = SI.GROUPED if grouped else 'chronological'
    for left, right in ROLE_PAIRS:
        SI.assert_boundary(meta, roles[left], roles[right], scheme)
    if set(roles['fit']) & set(roles['test']):
        raise ValueError('fit/test overlap')
    for fold in range(2):
        if not set(roles[f'inner{fold}_train']).union(roles[f'inner{fold}_validation']) <= set(roles['fit']):
            raise ValueError('tuning escaped final fitting pool')


def forecast_roles(meta, horizon, freq, fold, grouped=False):
    if fold not in range(3):
        raise ValueError('unknown outer fold')
    if not grouped:
        roles = pilot_roles(meta, horizon, freq, fold, 3)
    else:
        f = grouped_batch_folds(meta)[fold]
        blocks = SI.ordered_blocks(meta, f['train'], [1/3] * 3, SI.GROUPED)
        roles = dict(fit=f['train'], calibration=f['calibration'], test=f['test'],
                     inner0_train=blocks[0], inner0_validation=blocks[1],
                     inner1_train=np.r_[blocks[0], blocks[1]], inner1_validation=blocks[2])
    validate_roles(meta, roles, grouped)
    return roles
