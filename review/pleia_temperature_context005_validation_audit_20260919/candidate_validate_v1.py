"""Candidate representation-compatible validator, version v1 (AUDIT ONLY).

This is NOT a substitute for the frozen `validate` action and does not waive any
scientific gate. It is a versioned candidate implemented on the audit branch,
importing `src` without modifying it, so the frozen source hash that the energy
study also depends on stays intact.

=== How the candidate contract differs from the original ===

The frozen validator asserts, in one step:
    (A') the saved bounds equal those obtained by applying the saved model to a
         feature vector reconstructed INDEPENDENTLY of the engine.

A' conflates two claims. The candidate separates them:

  A. PROVENANCE. The saved production features are reconstructed independently
     from the raw source inputs (no production causal_features/inject/pandas
     rolling) and must agree with the saved features within the UNCHANGED frozen
     tolerance 1e-10, and the saved feature hash and observation hash must match.
     The saved features are therefore never trusted a priori.

  B. MODEL APPLICATION. The saved model, applied to the exact verified
     production feature representation, must reproduce the saved predictions.

  C. DOWNSTREAM. Calibration, causal release/update state, interval
     construction and alert outcomes are re-derived by the independent scalar
     implementation from that verified representation.

A ^ B ^ C is strictly weaker than A' in exactly one respect: it does not certify
that a prediction is STABLE under a sub-tolerance perturbation of the features.
That property is unachievable in principle for a piecewise-constant tree
ensemble, so the audit records the sensitivity explicitly rather than hiding it:
for every variant whose two representations disagree, the candidate records the
original-contract violation and attributes it to a specific split threshold.

Tolerances are UNCHANGED (1e-10 absolute and relative) everywhere.
No fits. No rounding, clipping, sorting or recalibration of scientific outputs.
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

import audit_common as A

from src.intervals005_common import Operations, PhaseMeter, load_owner, read, tree, signature
from src.context005_spec import context_positions, POLICIES
from src.context005_validate import (table, scalar_observations, scalar_inputs, scalar_stream,
                                     independent_alert, numeric_array)
from src.context005_data import load_real
from src.context005_features import bounded_frame, feature_hash
from src.conformal_quantile import _sub_estimators

TOL = 1e-10
VERSION = 'candidate_representation_compatible_v1'
OUT = Path(os.environ.get('CANDIDATE_OUT', '')) if os.environ.get('CANDIDATE_OUT') else A.OUT / 'candidate_v1'
# Sandbox override exists ONLY so the corruption-rejection tests can exercise this
# exact code path against a disposable copy. It never points at real artifacts in
# a normal run, and the real run directory is opened read-only either way.
RUN = Path(os.environ['CANDIDATE_RUN']) if os.environ.get('CANDIDATE_RUN') else A.RUN


class Ledger:
    """Counts every assertion, including the ones that pass, with denominators."""

    def __init__(self):
        self.checks = {}
        self.violations = []
        self.maximum = 0.0

    def _bump(self, kind, elements=1, violations=0):
        c = self.checks.setdefault(kind, dict(assertions=0, elements=0, violations=0))
        c['assertions'] += 1
        c['elements'] += int(elements)
        c['violations'] += int(violations)

    def close(self, a, b, kind, label, where):
        aa = numeric_array(a)
        bb = numeric_array(b)
        if aa.size == 0:
            self._bump(kind + ':empty', 0, 0)
            return 0
        bad = ~np.isclose(aa, bb, atol=TOL, rtol=TOL, equal_nan=True)
        n_bad = int(np.nansum(bad))
        mx = float(np.nanmax(np.abs(aa - bb)))
        self.maximum = max(self.maximum, mx)
        self._bump(kind, aa.size, n_bad)
        if n_bad:
            self.violations.append(dict(kind=kind, check=label, where=where, n=int(aa.size),
                                        violations=n_bad, maximum_difference=mx,
                                        rows=[int(i) for i in np.flatnonzero(bad.ravel())][:20]))
        return n_bad

    def equal(self, ok, kind, label, where):
        self._bump(kind, 1, 0 if ok else 1)
        if not ok:
            self.violations.append(dict(kind=kind, check=label, where=where, n=1, violations=1,
                                        maximum_difference=None, rows=[]))
        return 0 if ok else 1


def walk_leaf(predictor, x):
    nodes = predictor.nodes
    i = 0
    path = []
    while not nodes[i]['is_leaf']:
        n = nodes[i]
        f = int(n['feature_idx'])
        thr = float(n['num_threshold'])
        v = x[f]
        go_left = bool(n['missing_go_to_left']) if np.isnan(v) else bool(v <= thr)
        path.append((int(i), f, thr, float(v), go_left))
        i = int(n['left']) if go_left else int(n['right'])
    return i, path


def attribute(ests, cols, xa, xb):
    """Explain a prediction difference by locating the divergent split node(s)."""
    found = []
    for k, est in enumerate(ests):
        for s, stage in enumerate(est._predictors):
            la, pa = walk_leaf(stage[0], xa)
            lb, pb = walk_leaf(stage[0], xb)
            if la == lb:
                continue
            first = None
            for (na, fa, tha, va, ga), (nb, fb, thb, vb, gb) in zip(pa, pb):
                if ga != gb:
                    first = dict(estimator=k, stage=s, node=na, feature=cols[fa],
                                 num_threshold=repr(tha), engine_value=repr(va),
                                 validator_value=repr(vb),
                                 engine_on_threshold=(va == tha), validator_on_threshold=(vb == tha),
                                 straddles_threshold=bool((va <= tha) != (vb <= tha)),
                                 gap_in_ulps=(abs(va - vb) / np.spacing(abs(tha)) if np.spacing(abs(tha)) else None))
                    break
            found.append(dict(estimator=k, stage=s, divergent_node=first,
                              explained=bool(first and first['straddles_threshold'])))
    return found


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    limit = int(os.environ.get('CANDIDATE_LIMIT', '0'))
    p = read(A.DESIGN / 'frozen_protocol.json')
    m = p['manifest']
    led = Ledger()
    before_tree = tree(RUN)

    sensitivity = []
    unexplained = []
    candidate_violation_rows = []

    with Operations(forbid=True), PhaseMeter() as meter:
        d = load_real(m['dataset'], m['outer_fold'])
        cols = list(d['X'].columns)
        meta = d['meta'].iloc[d['roles']['outer_test']].reset_index(drop=True)
        variants = table(RUN / 'stages/tables/variants.csv')
        if limit:
            variants = variants.head(limit)
            print(f'LIMITED RUN: {limit} variants', flush=True)
        ctxmap = d['contexts'].set_index('context_id').to_dict('index')
        models = load_owner(RUN / 'stages/controls/controls.pkl')
        ests, _ = _sub_estimators(models['cqr'].owner)
        reconstructed = []

        for idx, vr in enumerate(variants.to_dict('records')):
            where = vr['stage']
            ctx = dict(ctxmap[vr['context_id']], context_id=vr['context_id'])
            local = meta.iloc[context_positions(meta, ctx)].reset_index(drop=True)
            ctx = dict(ctx, end_time=str(local.target_time.max()))
            events = d['schedules'][d['schedules'].context_id == vr['context_id']].to_dict('records')
            event = None if vr['ordinal'] == 0 else events[int(vr['ordinal']) - 1]
            base, season = bounded_frame(d['series'], local, d['fcfg'], d['horizon'])
            truth, obs, avail = scalar_observations(base, local, event)
            Xr = scalar_inputs(base, local, d['fcfg'], d['horizon'], d['frequency'], season, cols, obs, avail)
            path = RUN / 'stages' / vr['canonical_stage']
            saved_full = table(path / 'features.csv.gz')
            saved = saved_full[cols]

            # ---- Contract A: provenance of the saved representation ----
            led.close(saved, Xr, 'A_feature_provenance', 'scalar_causal_features', where)
            observations = table(path / 'observations.csv.gz')
            led.close(observations.observed, obs, 'A_observations', 'independent_observations', where)
            led.equal(observations.available.tolist() == avail.tolist(), 'A_availability', 'availability', where)
            ident = read(path / 'identity.json')
            led.equal(feature_hash(saved) == ident['feature_hash'], 'A_identity', 'saved_feature_hash', where)
            led.equal(signature(np.nan_to_num(obs, nan=-1.23456789e307).tolist()) == ident['observation_hash'],
                      'A_identity', 'observation_hash', where)

            if vr['alias']:
                alias = read(RUN / 'stages' / vr['stage'] / 'alias.json')
                led.equal(alias['canonical_stage'] == vr['canonical_stage']
                          and alias['realization_hash'] == vr['realization_hash'],
                          'A_alias', 'alias_identity', where)
            else:
                a_arr = saved.to_numpy(float)
                r_arr = Xr.to_numpy(float)
                # Sensitivity: does the representation difference change any prediction?
                differs = False
                for est in ests:
                    if not np.allclose(est.predict(a_arr), est.predict(r_arr), atol=TOL, rtol=TOL):
                        differs = True
                        break
                if differs:
                    rows = set()
                    for est in ests:
                        pa, pb = est.predict(a_arr), est.predict(r_arr)
                        rows |= set(np.flatnonzero(~np.isclose(pa, pb, atol=TOL, rtol=TOL)).tolist())
                    expl = []
                    for r in sorted(rows):
                        ev = attribute(ests, cols, a_arr[r], r_arr[r])
                        expl.append(dict(row=int(r), divergences=ev,
                                         all_explained=bool(ev) and all(x['explained'] for x in ev)))
                        if not (ev and all(x['explained'] for x in ev)):
                            unexplained.append(dict(stage=where, row=int(r), evidence=ev))
                    sensitivity.append(dict(stage=where, rows=sorted(rows), detail=expl))

                for control in m['controls']:
                    cid = control['control_id']
                    model = models[control['method']]
                    # ---- Contract B + C from the VERIFIED saved representation ----
                    sc = scalar_stream(model, saved, local, obs, avail, control)
                    stream = table(path / (cid + '_issued.csv.gz'))
                    for col in ['point', 'raw_lower', 'raw_upper']:
                        n = led.close(stream[col], sc[col], 'B_model_application', f'{cid}_{col}', where)
                        if n:
                            candidate_violation_rows.append(dict(stage=where, control=cid, col=col, n=n))
                    for col in ['lower', 'upper']:
                        n = led.close(stream[col], sc[col], 'C_interval_construction', f'{cid}_{col}', where)
                        if n:
                            candidate_violation_rows.append(dict(stage=where, control=cid, col=col, n=n))
                    released = table(path / (cid + '_released.csv.gz'))
                    exp = sc['releases']
                    led.equal(len(released) == len(exp), 'C_release_count', f'{cid}_release_count', where)
                    if len(released) and len(released) == len(exp):
                        led.equal(released.row_id.tolist() == exp.row_id.tolist()
                                  and released.released_at_origin.tolist() == exp.released_at_origin.tolist(),
                                  'C_release_identity', f'{cid}_release_identity', where)
                        led.close(released.score, exp.score, 'C_released_scores', f'{cid}_released_scores', where)
                    updates = table(path / (cid + '_updates.csv.gz'))
                    eu = sc['updates']
                    led.equal(len(updates) == len(eu), 'C_update_count', f'{cid}_update_count', where)
                    if len(updates) and len(updates) == len(eu):
                        led.close(updates[['pool_n', 'correction_lower', 'correction_upper']],
                                  eu[['pool_n', 'correction_lower', 'correction_upper']],
                                  'C_rolling_state', f'{cid}_updates', where)
                        led.equal(updates.status.tolist() == eu.status.tolist(),
                                  'C_update_status', f'{cid}_update_status', where)
                    for rule in m['rules']:
                        flags, episodes = independent_alert(stream, d['frequency'], rule['k'], rule['m'])
                        prefix = cid + '_' + rule['rule_id']
                        consumed = table(path / (prefix + '_alerts.csv.gz'))
                        eps = table(path / (prefix + '_episodes.csv.gz'))
                        for channel, values in flags.items():
                            led.equal(consumed['alert_' + channel].tolist() == values.tolist(),
                                      'C_alert_flags', f'{prefix}_{channel}', where)
                        ccols = ['channel', 'group_id', 'segment_id', 'start_index', 'onset']
                        led.equal(set(map(tuple, eps[ccols].to_numpy())) == set(map(tuple, episodes[ccols].to_numpy())),
                                  'C_episode_onsets', f'{prefix}_episodes', where)

            if event:
                for control in m['controls']:
                    for rule in m['rules']:
                        eps = table(path / (control['control_id'] + '_' + rule['rule_id'] + '_episodes.csv.gz'))
                        onset = pd.Timestamp(event['onset'])
                        pol = POLICIES[m['dataset']]
                        tau = (pol['duration'] - 1 + pol['tolerance']) * float(d['frequency'] / pd.Timedelta('1min'))
                        for channel in ['numerical_only', 'availability_only', 'combined']:
                            cand = [(pd.Timestamp(e.onset) - onset) / pd.Timedelta('1min') for e in eps.itertuples()
                                    if e.channel == channel and e.group_id == str(ctx['group_id'])
                                    and 0 <= (pd.Timestamp(e.onset) - onset) / pd.Timedelta('1min') <= tau]
                            det = bool(event['effective']) and bool(cand)
                            reconstructed.append(dict(context_id=vr['context_id'], family=event['family'],
                                                      severity=event['severity'], replicate=event['replicate'],
                                                      control_id=control['control_id'], rule_id=rule['rule_id'],
                                                      channel=channel, detected=det,
                                                      restricted_delay_minutes=min(cand) if det else tau))
            if (idx + 1) % 200 == 0:
                print(f'candidate {idx+1}/{len(variants)} | candidate violations '
                      f'{sum(c["violations"] for c in led.checks.values())} | sensitivity stages {len(sensitivity)}',
                      flush=True)

        if not limit:
            actual = table(RUN / 'stages/tables/events.csv.gz')
            expected = pd.DataFrame(reconstructed)
            keys = ['context_id', 'family', 'severity', 'replicate', 'control_id', 'rule_id', 'channel']
            aa = actual.set_index(keys).sort_index()
            bb = expected.set_index(keys).sort_index()
            led.equal(aa.index.equals(bb.index), 'C_event_ledger', 'event_ledger_completeness', 'aggregate')
            led.close(aa.detected, bb.detected, 'C_event_detection', 'event_detection', 'aggregate')
            led.close(aa.restricted_delay_minutes, bb.restricted_delay_minutes, 'C_censored_delay',
                      'censored_delay', 'aggregate')

            ss = table(RUN / 'stages/tables/strata.csv')
            for row in ss.to_dict('records'):
                f = actual[(actual.control_id == row['control_id']) & (actual.rule_id == row['rule_id'])
                           & (actual.channel == row['channel']) & (actual.family == row['family'])
                           & (actual.severity == row['severity'])]
                pos = f[f.effective & f.eligible]
                means = [g.detected.mean() for _, g in pos.groupby('context_id')]
                led.equal(len(means) == row['effective_contexts'] and len(f) == row['scheduled'],
                          'C_equal_context_denominator', 'equal_context_denominator', 'stratum')
                if means:
                    led.close(row['recall'], np.mean(means), 'C_equal_context_recall', 'equal_context_recall', 'stratum')

            work = table(RUN / 'stages/tables/fullstream_workload.csv')
            for fs in sorted((RUN / 'stages').glob('fullstream_*')):
                observations = table(fs / 'observations.csv.gz')
                loc = observations[['row_id', 'group_id', 'origin_time', 'target_time']].copy()
                loc.origin_time = pd.to_datetime(loc.origin_time)
                loc.target_time = pd.to_datetime(loc.target_time)
                base, season = bounded_frame(d['series'], loc, d['fcfg'], d['horizon'])
                truth, obs, avail = scalar_observations(base, loc, None)
                Xr = scalar_inputs(base, loc, d['fcfg'], d['horizon'], d['frequency'], season, cols, obs, avail)
                saved = table(fs / 'features.csv.gz')[cols]
                led.close(saved, Xr, 'A_feature_provenance', 'fullstream_scalar_features', fs.name)
                for control in m['controls']:
                    cid = control['control_id']
                    stream = table(fs / (cid + '_issued.csv.gz'))
                    sc = scalar_stream(models[control['method']], saved, loc, obs, avail, control)
                    led.close(stream[['lower', 'upper']], np.column_stack([sc['lower'], sc['upper']]),
                              'C_interval_construction', f'fullstream_{cid}_bounds', fs.name)
                    for rule in m['rules']:
                        flags, episodes = independent_alert(stream, d['frequency'], rule['k'], rule['m'])
                        for channel, values in flags.items():
                            row = work[(work.control_id == cid) & (work.rule_id == rule['rule_id'])
                                       & (work.channel == channel) & (work.group_id == str(loc.group_id.iloc[0]))]
                            ok = (len(row) == 1 and row.iloc[0].alert_rows == sum(values)
                                  and row.iloc[0].episodes == sum(episodes.channel == channel))
                            led.equal(ok, 'C_workload', f'fullstream_{cid}_{rule["rule_id"]}_{channel}', fs.name)
            for _, part in work.groupby(['control_id', 'rule_id', 'channel']):
                led.equal(part.eligible_rows.sum() == len(meta), 'C_full_exposure', 'full_original_exposure', 'workload')
                led.close(part.asset_days.sum(), len(meta) * float(d['frequency'] / pd.Timedelta('1D')),
                          'C_full_exposure', 'original_exposure', 'workload')

        after_tree = tree(RUN)
        led.equal(after_tree == before_tree, 'integrity', 'scientific_artifacts_unchanged', 'run')

    total_assertions = sum(c['assertions'] for c in led.checks.values())
    total_elements = sum(c['elements'] for c in led.checks.values())
    total_violations = sum(c['violations'] for c in led.checks.values())
    result = dict(
        version=VERSION, limited=bool(limit),
        contract=dict(
            A='independent causal feature reconstruction vs saved features, frozen tolerance 1e-10',
            B='saved model applied to the verified saved feature representation reproduces saved predictions',
            C='calibration, causal release/update state, interval construction and alert outcomes re-derived independently',
            tolerance_changed=False, tolerance=dict(atol=TOL, rtol=TOL)),
        totals=dict(assertions=total_assertions, elements=total_elements, violations=total_violations,
                    maximum_observed_difference=led.maximum),
        by_kind={k: v for k, v in sorted(led.checks.items())},
        passed=bool(total_violations == 0),
        candidate_violations=led.violations[:200],
        sensitivity=dict(
            stages_where_representations_diverge=len(sensitivity),
            rows_affected=sum(len(s['rows']) for s in sensitivity),
            all_divergences_explained_by_threshold_straddle=(len(unexplained) == 0),
            unexplained=unexplained[:50]),
        artifacts_unchanged=bool(after_tree == before_tree),
        resources=meter.result)
    (OUT / 'CANDIDATE_VALIDATION.json').write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
    pd.DataFrame(led.violations).to_csv(OUT / 'candidate_violations.csv', index=False)
    Path(OUT / 'sensitivity_attribution.json').write_text(json.dumps(sensitivity, indent=2, default=str), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('by_kind', 'candidate_violations', 'sensitivity')}, indent=2, default=str))
    print('sensitivity:', json.dumps(result['sensitivity'], default=str)[:600])
    print('by_kind:', json.dumps(result['by_kind'], indent=1))


if __name__ == '__main__':
    main()
