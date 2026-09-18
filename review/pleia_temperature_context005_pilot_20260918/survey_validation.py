"""Full-extent independent validation survey for the temperature pilot.

This reproduces the frozen validator's independent reconstruction over every
variant, but COLLECTS discrepancies instead of aborting at the first one. It
changes nothing in ``src`` and loosens no tolerance: the frozen 1e-10 comparison
is applied unchanged and every violation is recorded.

Its purpose is to establish the exact extent of the bin-boundary discrepancy
found in attempt 1, and in particular whether any *scientific outcome* --
alert flags, episode onsets, event detection, restricted delay, equal-context
recall, full clean workload -- differs from the saved artifacts.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

for _n in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    os.environ[_n] = '1'

import numpy as np
import pandas as pd

import common
from common import read

sys.path.insert(0, str(common.SMART))
from src.intervals005_common import Operations, load_owner, tree, signature, PhaseMeter
from src.context005_spec import context_positions, POLICIES
# Use the validator's own reader: it coerces blank numeric stream cells to NaN.
# context005_spec.table keeps them as '' (object dtype), which breaks comparisons.
from src.context005_validate import table
from src.context005_data import load_real
from src.context005_features import bounded_frame, feature_hash
from src.context005_validate import scalar_observations, scalar_inputs, scalar_stream, independent_alert, numeric_array

RUN = common.run()
DESIGN = common.design()
MODELS = None
OUT = common.BATCH / 'validation_survey'
TOL = 1e-10


class Collector:
    def __init__(self):
        self.rows = []
        self.maximum = 0.0
        self.violations = 0
        self.checks = 0

    def close(self, a, b, label, kind):
        aa = numeric_array(a)
        bb = numeric_array(b)
        if aa.size == 0:
            return
        diff = np.abs(aa - bb)
        with np.errstate(invalid='ignore'):
            bad = ~np.isclose(aa, bb, atol=TOL, rtol=TOL, equal_nan=True)
        mx = float(np.nanmax(diff)) if diff.size else 0.0
        self.maximum = max(self.maximum, mx)
        self.checks += 1
        n_bad = int(np.nansum(bad))
        if n_bad:
            self.violations += n_bad
            self.rows.append(dict(check=label, kind=kind, n=int(aa.size), violations=n_bad,
                                  maximum_difference=mx))

    def equal(self, ok, label, kind):
        self.checks += 1
        if not ok:
            self.violations += 1
            self.rows.append(dict(check=label, kind=kind, n=1, violations=1, maximum_difference=float('nan')))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p = read(DESIGN / 'frozen_protocol.json')
    m = p['manifest']
    c = Collector()
    outcome_mismatch = dict(alert_flags=0, episode_onsets=0, release_identity=0, update_status=0,
                            update_counts=0, release_counts=0)
    with Operations(forbid=True), PhaseMeter() as meter:
        d = load_real(m['dataset'], m['outer_fold'])
        meta = d['meta'].iloc[d['roles']['outer_test']].reset_index(drop=True)
        variants = table(RUN / 'stages/tables/variants.csv')
        limit = int(os.environ.get('SURVEY_LIMIT', '0'))
        if limit:
            variants = variants.head(limit)
            print(f'SMOKE TEST: limited to {limit} variants', flush=True)
        ctxmap = d['contexts'].set_index('context_id').to_dict('index')
        reconstructed = []
        unique = 0
        for idx, vr in enumerate(variants.to_dict('records')):
            ctx = dict(ctxmap[vr['context_id']], context_id=vr['context_id'])
            ix = context_positions(meta, ctx)
            local = meta.iloc[ix].reset_index(drop=True)
            ctx = dict(ctx, end_time=str(local.target_time.max()))
            events = d['schedules'][d['schedules'].context_id == vr['context_id']].to_dict('records')
            event = None if vr['ordinal'] == 0 else events[int(vr['ordinal']) - 1]
            base, season = bounded_frame(d['series'], local, d['fcfg'], d['horizon'])
            truth, obs, avail = scalar_observations(base, local, event)
            X = scalar_inputs(base, local, d['fcfg'], d['horizon'], d['frequency'], season,
                              d['X'].columns, obs, avail)
            path = RUN / 'stages' / vr['canonical_stage']
            saved = table(path / 'features.csv.gz')
            c.close(saved[d['X'].columns], X, 'scalar_causal_features', 'features')
            observations = table(path / 'observations.csv.gz')
            c.close(observations.observed, obs, 'independent_observations', 'observations')
            c.equal(observations.available.tolist() == avail.tolist(), 'availability', 'observations')
            ident = read(path / 'identity.json')
            c.equal(feature_hash(saved[d['X'].columns]) == ident['feature_hash'], 'saved_feature_hash', 'identity')
            c.equal(signature(np.nan_to_num(obs, nan=-1.23456789e307).tolist()) == ident['observation_hash'],
                    'observation_hash', 'identity')
            if not vr['alias']:
                unique += 1
                for control in m['controls']:
                    cid = control['control_id']
                    model = MODELS[control['method']]
                    scalar = scalar_stream(model, X, local, obs, avail, control)
                    stream = table(path / (cid + '_issued.csv.gz'))
                    for col in ['lower', 'upper', 'point', 'raw_lower', 'raw_upper']:
                        c.close(stream[col], scalar[col], f'{cid}_{col}', 'bounds')
                    released = table(path / (cid + '_released.csv.gz'))
                    expected = scalar['releases']
                    if len(released) != len(expected):
                        outcome_mismatch['release_counts'] += 1
                        c.equal(False, f'{cid}_release_count', 'release')
                    elif len(released):
                        ok = (released.row_id.tolist() == expected.row_id.tolist()
                              and released.released_at_origin.tolist() == expected.released_at_origin.tolist())
                        if not ok:
                            outcome_mismatch['release_identity'] += 1
                        c.equal(ok, f'{cid}_release_identity', 'release')
                        c.close(released.score, expected.score, f'{cid}_released_scores', 'release')
                    updates = table(path / (cid + '_updates.csv.gz'))
                    eu = scalar['updates']
                    if len(updates) != len(eu):
                        outcome_mismatch['update_counts'] += 1
                        c.equal(False, f'{cid}_update_count', 'update')
                    elif len(updates):
                        c.close(updates[['pool_n', 'correction_lower', 'correction_upper']],
                                eu[['pool_n', 'correction_lower', 'correction_upper']], f'{cid}_updates', 'update')
                        if updates.status.tolist() != eu.status.tolist():
                            outcome_mismatch['update_status'] += 1
                        c.equal(updates.status.tolist() == eu.status.tolist(), f'{cid}_update_status', 'update')
                    for rule in m['rules']:
                        flags, episodes = independent_alert(stream, d['frequency'], rule['k'], rule['m'])
                        prefix = cid + '_' + rule['rule_id']
                        consumed = table(path / (prefix + '_alerts.csv.gz'))
                        eps = table(path / (prefix + '_episodes.csv.gz'))
                        for channel, values in flags.items():
                            ok = consumed['alert_' + channel].tolist() == values.tolist()
                            if not ok:
                                outcome_mismatch['alert_flags'] += 1
                            c.equal(ok, f'{prefix}_{channel}_alert_flags', 'alert_outcome')
                        cols = ['channel', 'group_id', 'segment_id', 'start_index', 'onset']
                        ok = set(map(tuple, eps[cols].to_numpy())) == set(map(tuple, episodes[cols].to_numpy()))
                        if not ok:
                            outcome_mismatch['episode_onsets'] += 1
                        c.equal(ok, f'{prefix}_episode_onsets', 'alert_outcome')
            if event:
                for control in m['controls']:
                    for rule in m['rules']:
                        eps = table(path / (control['control_id'] + '_' + rule['rule_id'] + '_episodes.csv.gz'))
                        onset = pd.Timestamp(event['onset'])
                        policy = POLICIES[m['dataset']]
                        tau = (policy['duration'] - 1 + policy['tolerance']) * float(d['frequency'] / pd.Timedelta('1min'))
                        for channel in ['numerical_only', 'availability_only', 'combined']:
                            cand = [(pd.Timestamp(e.onset) - onset) / pd.Timedelta('1min') for e in eps.itertuples()
                                    if e.channel == channel and e.group_id == str(ctx['group_id'])
                                    and 0 <= (pd.Timestamp(e.onset) - onset) / pd.Timedelta('1min') <= tau]
                            detected = bool(event['effective']) and bool(cand)
                            reconstructed.append(dict(context_id=vr['context_id'], family=event['family'],
                                                      severity=event['severity'], replicate=event['replicate'],
                                                      control_id=control['control_id'], rule_id=rule['rule_id'],
                                                      channel=channel, detected=detected,
                                                      restricted_delay_minutes=min(cand) if detected else tau))
            if (idx + 1) % 200 == 0:
                print(f'surveyed {idx + 1}/{len(variants)} variants; violations so far {c.violations}', flush=True)

        actual = table(RUN / 'stages/tables/events.csv.gz')
        expected = pd.DataFrame(reconstructed)
        if limit:
            print('SMOKE TEST: per-variant loop completed; skipping whole-study aggregates', flush=True)
            print(json.dumps(dict(checks=c.checks, violating_elements=c.violations,
                                  maximum_difference=c.maximum, outcome=outcome_mismatch), indent=2))
            return
        keys = ['context_id', 'family', 'severity', 'replicate', 'control_id', 'rule_id', 'channel']
        a = actual.set_index(keys).sort_index()
        b = expected.set_index(keys).sort_index()
        c.equal(a.index.equals(b.index), 'event_ledger_completeness', 'event_outcome')
        c.close(a.detected, b.detected, 'event_detection', 'event_outcome')
        c.close(a.restricted_delay_minutes, b.restricted_delay_minutes, 'censored_delay', 'event_outcome')

        ss = table(RUN / 'stages/tables/strata.csv')
        for row in ss.to_dict('records'):
            f = actual[(actual.control_id == row['control_id']) & (actual.rule_id == row['rule_id'])
                       & (actual.channel == row['channel']) & (actual.family == row['family'])
                       & (actual.severity == row['severity'])]
            positive = f[f.effective & f.eligible]
            means = [g.detected.mean() for _, g in positive.groupby('context_id')]
            c.equal(len(means) == row['effective_contexts'] and len(f) == row['scheduled'],
                    'equal_context_denominator', 'estimand')
            if means:
                c.close(row['recall'], np.mean(means), 'equal_context_recall', 'estimand')

        work = table(RUN / 'stages/tables/fullstream_workload.csv')
        for path in sorted((RUN / 'stages').glob('fullstream_*')):
            observations = table(path / 'observations.csv.gz')
            local = observations[['row_id', 'group_id', 'origin_time', 'target_time']].copy()
            local.origin_time = pd.to_datetime(local.origin_time)
            local.target_time = pd.to_datetime(local.target_time)
            base, season = bounded_frame(d['series'], local, d['fcfg'], d['horizon'])
            truth, obs, avail = scalar_observations(base, local, None)
            X = scalar_inputs(base, local, d['fcfg'], d['horizon'], d['frequency'], season, d['X'].columns, obs, avail)
            saved = table(path / 'features.csv.gz')
            c.close(saved[d['X'].columns], X, 'fullstream_scalar_features', 'features')
            for control in m['controls']:
                cid = control['control_id']
                stream = table(path / (cid + '_issued.csv.gz'))
                scalar = scalar_stream(MODELS[control['method']], X, local, obs, avail, control)
                c.close(stream[['lower', 'upper']], np.column_stack([scalar['lower'], scalar['upper']]),
                        f'fullstream_{cid}_bounds', 'bounds')
                for rule in m['rules']:
                    flags, episodes = independent_alert(stream, d['frequency'], rule['k'], rule['m'])
                    for channel, values in flags.items():
                        row = work[(work.control_id == cid) & (work.rule_id == rule['rule_id'])
                                   & (work.channel == channel) & (work.group_id == str(local.group_id.iloc[0]))]
                        ok = len(row) == 1 and row.iloc[0].alert_rows == sum(values) \
                            and row.iloc[0].episodes == sum(episodes.channel == channel)
                        if not ok:
                            outcome_mismatch['alert_flags'] += 1
                        c.equal(ok, f'fullstream_{cid}_{rule["rule_id"]}_{channel}_workload', 'workload_outcome')
        for _, part in work.groupby(['control_id', 'rule_id', 'channel']):
            c.equal(part.eligible_rows.sum() == len(meta), 'full_original_exposure', 'workload_outcome')
            c.close(part.asset_days.sum(), len(meta) * float(d['frequency'] / pd.Timedelta('1D')),
                    'original_exposure', 'workload_outcome')

    detail = pd.DataFrame(c.rows)
    detail.to_csv(OUT / 'validation_survey_violations.csv', index=False)
    expected.to_csv(OUT / 'independently_reconstructed_events.csv.gz', index=False)
    by_kind = detail.groupby('kind').agg(checks_with_violations=('check', 'size'),
                                         violations=('violations', 'sum'),
                                         maximum_difference=('maximum_difference', 'max')
                                         ).reset_index().to_dict('records') if len(detail) else []
    outcome_kinds = {'alert_outcome', 'event_outcome', 'estimand', 'workload_outcome', 'release', 'update'}
    outcome_violations = int(detail[detail.kind.isin(outcome_kinds)].violations.sum()) if len(detail) else 0
    result = dict(
        purpose='full_extent_independent_validation_survey_frozen_tolerance_unchanged',
        tolerance=dict(atol=TOL, rtol=TOL, note='frozen tolerance applied unchanged; nothing loosened'),
        total_checks=c.checks, total_violating_elements=c.violations,
        maximum_observed_difference=c.maximum,
        unique_canonical_variants=unique, variants=len(variants),
        violations_by_kind=by_kind,
        scientific_outcome_violations=outcome_violations,
        scientific_outcome_breakdown=outcome_mismatch,
        conclusion=('no scientific outcome differs; discrepancies confined to numeric bound values'
                    if outcome_violations == 0 else 'SCIENTIFIC OUTCOME DIFFERS - investigate'),
        resources=meter.result)
    name = 'SMOKE_VALIDATION_SURVEY.json' if os.environ.get('SURVEY_LIMIT') else 'VALIDATION_SURVEY.json'
    (OUT / name).write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'violations_by_kind'}, indent=2, default=str))
    print('violations by kind:', json.dumps(by_kind, indent=2, default=str))


if __name__ == '__main__':
    MODELS = load_owner(RUN / 'stages/controls/controls.pkl')
    main()
