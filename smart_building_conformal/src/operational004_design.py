"""Versioned amendment-004 support and candidate contracts (no fitting)."""
from __future__ import annotations
from dataclasses import replace
import hashlib
import itertools
import math
import numpy as np
import pandas as pd
from . import split_integrity as SI, windowing
from .corrected_study import make_outer_folds
from .datasets.base import ChronologicalPartitioner
from .unit_checkpoint import signature

FAMILIES = ('random_missing', 'block_missing', 'stuck', 'dropout', 'bias', 'level_shift', 'drift')
SEVERITIES = (.5, 1., 2.)
STRATA = tuple(itertools.product(FAMILIES, SEVERITIES))
RULES = ((5, 2), (15, 3), (30, 3), (60, 4), (180, 3), (360, 4))
DESIGN = dict(amendment=4, evidence_status='post_inspection_design',
    tasks=['pleia', 'pleia_energy', 'rico', 'bdg2'], outer_folds=3,
    model_seeds=[42, 43, 44, 45, 46], catalogue_seeds=[42, 43, 44, 45, 46],
    bootstrap_seed=20240601, bootstrap_replicates=2000, minimum_valid_replicates=1900,
    min_train=400, min_calibration=400, min_selection=200, min_online_scores=50,
    min_events_per_stratum=5, min_resampling_units=5,
    incidence=.5, min_recall=.6, workload_max=1., beta=1.,
    levels=[.95, .975, .99, .995], quality_levels=[.9, .95],
    families=list(FAMILIES), severities=list(SEVERITIES), max_placement_attempts=1000,
    final_calibration_fraction=.25, inner_block_fractions=[.25]*4,
    availability_alarm=True, custom_utility='equal_stratum_synthetic_f1',
    fold_weight=[.5, .5], diagnostic_fallback='fixed_cqr_095_static_single_sample',
    full_study_ready=False)


def seed_for(*parts):
    return int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:16], 16)


def physical_rules(freq):
    minutes = float(pd.Timedelta(freq) / pd.Timedelta(minutes=1))
    out = [dict(rule_id='single_sample', window_minutes=minutes, k=1, m=1, applicable=True)]
    for duration, k in RULES:
        m = math.floor(duration/minutes)
        out.append(dict(rule_id=f'{duration}min_{k}of{m}', window_minutes=duration,
                        k=k, m=m, applicable=m >= k and m >= 1))
    return out


def rank_support(n, level, kind):
    if kind == 'quantile_uncalibrated':
        return dict(supported=True, lower_rank=None, upper_rank=None)
    if kind == 'cqr':
        lo = hi = math.ceil((n+1)*level)
    else:
        lo = math.floor((n+1)*(1-level)/2 + 1e-12)
        hi = math.ceil((n+1)*(1-(1-level)/2) - 1e-12)
    return dict(supported=1 <= lo <= hi <= n, lower_rank=lo, upper_rank=hi)


def candidates(cfg, freq, *, smoke=False):
    grid = cfg['recalibration']['grid']
    levels = [.95] if smoke else DESIGN['levels']
    rules = [r for r in physical_rules(freq) if r['applicable']]
    if smoke:
        rules = [rules[0], next(r for r in rules[1:] if r['k'] > 1)]
    policies = [dict(strategy='static', every=0, window=None)]
    if not smoke:
        policies += [dict(strategy='periodic', every=e, window=None) for e in grid['update_every']]
    policies += [dict(strategy='rolling', every=e, window=w)
                 for e in (grid['update_every'][:1] if smoke else grid['update_every'])
                 for w in (grid['window'][:1] if smoke else grid['window'])]
    rows = []
    for method in (['quantile_uncalibrated', 'cqr'] if smoke else
                   ['quantile_uncalibrated', 'cqr', 'recentred_enbpi']):
        ps = policies[:1] if method == 'quantile_uncalibrated' else list(policies)
        if method == 'recentred_enbpi':
            ps += [dict(strategy='native_updated', every=1, window=None)]
        for level, policy, rule in itertools.product(levels, ps, rules):
            spec = dict(method=method, level=level, **policy, **rule,
                        min_samples=DESIGN['min_online_scores'])
            spec['candidate_id'] = f"c{len(rows):04d}_{signature(spec)[:12]}"
            rows.append(spec)
    assert len({signature({k:v for k,v in r.items() if k != 'candidate_id'}) for r in rows}) == len(rows)
    return rows


def segments(meta, freq, *, time_column='target_time'):
    """Position arrays for nonoverlapping, contiguous asset monitoring segments."""
    out = []
    for group, frame in meta.groupby('group_id', sort=True, dropna=False):
        rows = np.flatnonzero(meta.group_id.eq(group).to_numpy())
        rows = rows[np.argsort(pd.DatetimeIndex(meta.iloc[rows][time_column]).asi8, kind='stable')]
        times = pd.DatetimeIndex(meta.iloc[rows][time_column])
        if times.duplicated().any():
            raise ValueError('duplicate group/time monitoring row')
        cuts = np.r_[0, np.flatnonzero(np.diff(times.asi8) != pd.Timedelta(freq).value)+1, len(rows)]
        for i, (a,b) in enumerate(zip(cuts, cuts[1:])):
            if a < b:
                out.append((str(group), f'{group}:segment:{i}', rows[a:b]))
    return out


def build_windows(prepared, cfg, horizon):
    """Use existing features, resetting history across genuine acquisition gaps.

    Source-marked missing targets are not counted as observed exposure. Historical
    source-side imputations without flags remain an explicit provenance limit.
    """
    parts = []
    for series in prepared.series:
        frame = series.frame
        observed = np.isfinite(frame.target.to_numpy())
        if 'target_was_missing' in frame:
            observed &= ~frame.target_was_missing.astype(bool).to_numpy()
        good = np.flatnonzero(observed)
        cuts = np.r_[0, np.flatnonzero((np.diff(good) != 1) |
            (np.diff(frame.index[good].asi8) != series.freq.value))+1, len(good)]
        for a,b in zip(cuts,cuts[1:]):
            if b > a:
                parts.append(replace(series, group_id=str(series.group_id), frame=frame.iloc[good[a:b]].copy()))
    segmented = replace(prepared, series=parts)
    fcfg = windowing.feature_config(cfg, prepared.series[0].covariates)
    w = windowing.build_dataset_windows(segmented, horizon, fcfg)
    w['meta']['group_id'] = w['meta'].group_id.astype(str)
    w['meta']['row_id'] = [hashlib.sha256(f'{horizon}|{g}|{o}|{t}'.encode()).hexdigest()
        for g,o,t in w['meta'][['group_id','origin_time','target_time']].itertuples(index=False,name=None)]
    if w['meta'].row_id.duplicated().any():
        raise ValueError('duplicate eligible row')
    w['data_hash'] = signature(dict(meta=hashlib.sha256(pd.util.hash_pandas_object(w['meta'],index=False).values.tobytes()).hexdigest(),
        features=hashlib.sha256(pd.util.hash_pandas_object(w['X'],index=False).values.tobytes()).hexdigest()))
    return segmented, w, fcfg


def nested_roles(meta, fold, scheme):
    # make_outer_folds already reserves the final calibration once. Do not
    # concatenate and cut again after its purge, moving that frozen boundary.
    fit, ca, te = fold['train'], fold['calibration'], fold['test']
    blocks = SI.ordered_blocks(meta, fit, DESIGN['inner_block_fractions'], scheme)
    roles = {f'B{i}': b for i,b in enumerate(blocks)}
    roles.update(final_fit=np.concatenate(blocks), final_calibration=ca, outer_test=te,
        inner0_train=blocks[0], inner0_calibration=blocks[1], inner0_selection=blocks[2],
        inner1_train=np.concatenate(blocks[:2]), inner1_calibration=blocks[2], inner1_selection=blocks[3])
    for i in [0,1]:
        SI.assert_boundary(meta, roles[f'inner{i}_train'], roles[f'inner{i}_calibration'], scheme)
        SI.assert_boundary(meta, roles[f'inner{i}_calibration'], roles[f'inner{i}_selection'], scheme)
    SI.assert_boundary(meta, roles['final_fit'], ca, scheme)
    SI.assert_boundary(meta, ca, te, scheme)
    return roles


def resampling_support(meta, freq, dataset):
    applicable = [r['m'] for r in physical_rules(freq) if r['applicable']]
    dt = float(pd.Timedelta(freq)/pd.Timedelta(minutes=1))
    envelope = max(4, math.ceil(60/dt))
    tolerance = {'pleia':6, 'pleia_energy':6, 'rico':10, 'bdg2':3}.get(dataset,6)
    length = max(round(math.sqrt(len(meta))), max(applicable)+envelope+tolerance)
    n = (meta.group_id.nunique() if dataset in ('rico','bdg2') else
         sum(len(rows)//length for _,_,rows in segments(meta,freq)))
    return dict(block_length_steps=length, original_resampling_units=int(n),
                enough_original_units=n >= DESIGN['min_resampling_units'])
