"""Prove or reject the proposed validator-failure mechanism from direct evidence.

Claim under test: the engine's vectorised causal features and the validator's
scalar reconstruction differ by ~1e-14 (float64 ULP), and that difference flips
a gradient-boosting split-threshold comparison, changing leaf routing and hence
the prediction, interval bound and released score.

This script proves or rejects that claim by:
  1. recomputing BOTH feature representations for a failing stage,
  2. recording feature identity, column order and dtype for each,
  3. walking the SERIALIZED trees node by node for both representations and
     locating every node whose routing differs, with its exact num_threshold,
  4. attributing the prediction delta to those nodes,
  5. propagating to interval bounds and released conformity scores.

Read-only. Fits are forbidden. Nothing is rounded, clipped or re-tolerance.
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

from src.intervals005_common import Operations, load_owner, read
from src.context005_spec import context_positions
from src.context005_data import load_real
from src.context005_features import bounded_frame
from src.context005_validate import (table, scalar_observations, scalar_inputs, scalar_stream)
from src.conformal_quantile import _sub_estimators

STAGE = os.environ.get('AUDIT_STAGE', 'context_3c2ed441cb78fe67ef35_v0')
QUANTILE_NAMES = {0.025: 'lower_q0.025', 0.975: 'upper_q0.975', 0.5: 'median_q0.5'}


def walk(predictor, x):
    """Replicate sklearn TreePredictor routing on raw (unbinned) input."""
    nodes = predictor.nodes
    i = 0
    path = []
    while not nodes[i]['is_leaf']:
        n = nodes[i]
        f = int(n['feature_idx'])
        thr = float(n['num_threshold'])
        v = x[f]
        if np.isnan(v):
            go_left = bool(n['missing_go_to_left'])
        else:
            go_left = v <= thr
        path.append((i, f, thr, float(v), go_left))
        i = int(n['left']) if go_left else int(n['right'])
    return float(nodes[i]['value']), path, i


def raw_predict(est, x):
    total = float(np.ravel(est._baseline_prediction)[0])
    contributions = []
    for s, stage in enumerate(est._predictors):
        val, path, leaf = walk(stage[0], x)
        total += val
        contributions.append((s, val, path, leaf))
    return total, contributions


def main():
    A.OUT.mkdir(parents=True, exist_ok=True)
    p = read(A.DESIGN / 'frozen_protocol.json')
    m = p['manifest']
    report = dict(stage=STAGE, purpose='mechanism_proof_or_rejection')

    with Operations(forbid=True):
        d = load_real(m['dataset'], m['outer_fold'])
        meta = d['meta'].iloc[d['roles']['outer_test']].reset_index(drop=True)
        variants = table(A.RUN / 'stages/tables/variants.csv')
        vr = variants[variants.stage == STAGE].to_dict('records')[0]
        ctxmap = d['contexts'].set_index('context_id').to_dict('index')
        ctx = dict(ctxmap[vr['context_id']], context_id=vr['context_id'])
        ix = context_positions(meta, ctx)
        local = meta.iloc[ix].reset_index(drop=True)
        events = d['schedules'][d['schedules'].context_id == vr['context_id']].to_dict('records')
        event = None if vr['ordinal'] == 0 else events[int(vr['ordinal']) - 1]
        base, season = bounded_frame(d['series'], local, d['fcfg'], d['horizon'])
        truth, obs, avail = scalar_observations(base, local, event)

        cols = list(d['X'].columns)
        X_scalar = scalar_inputs(base, local, d['fcfg'], d['horizon'], d['frequency'], season, cols, obs, avail)
        path = A.RUN / 'stages' / vr['canonical_stage']
        saved = table(path / 'features.csv.gz')[cols]

        # ---- 1. feature identity, order, dtype -------------------------
        report['feature_identity'] = dict(
            n_columns=len(cols), column_order_identical=list(X_scalar.columns) == cols,
            saved_column_order_identical=list(saved.columns) == cols,
            scalar_dtypes=sorted({str(t) for t in X_scalar.dtypes}),
            saved_dtypes=sorted({str(t) for t in saved.dtypes}),
            rows=len(saved))

        a = saved.to_numpy(float)
        b = X_scalar.to_numpy(float)
        diff = np.abs(a - b)
        per_col = {c: float(np.nanmax(diff[:, j])) for j, c in enumerate(cols)}
        report['feature_difference'] = dict(
            max_overall=float(np.nanmax(diff)),
            frozen_feature_tolerance=1e-10,
            within_frozen_tolerance=bool(np.nanmax(diff) <= 1e-10),
            nonzero_columns={c: v for c, v in sorted(per_col.items(), key=lambda kv: -kv[1]) if v > 0},
            max_relative=float(np.nanmax(np.where(np.abs(a) > 0, diff / np.maximum(np.abs(a), 1e-300), 0.0))),
            ulp_multiple_of_max={})
        # express the worst difference as a multiple of the value's ULP
        j, i = np.unravel_index(np.nanargmax(diff), diff.shape)
        worst_val = a[j, i]
        report['feature_difference']['ulp_multiple_of_max'] = dict(
            row=int(j), column=cols[i], engine_value=repr(float(a[j, i])),
            validator_value=repr(float(b[j, i])),
            absolute_difference=float(diff[j, i]),
            ulp_of_engine_value=float(np.spacing(abs(worst_val))),
            difference_in_ulps=float(diff[j, i] / np.spacing(abs(worst_val))) if np.spacing(abs(worst_val)) else None)

        # ---- 2. locate rows whose predictions differ -------------------
        models = load_owner(A.RUN / 'stages/controls/controls.pkl')
        owner = models['cqr'].owner
        ests, _ = _sub_estimators(owner)
        est_info = [dict(index=k, quantile=float(e.get_params()['quantile']),
                         random_state=e.get_params()['random_state'],
                         n_stages=len(e._predictors)) for k, e in enumerate(ests)]
        report['estimators'] = est_info

        rows_examined = []
        for k, est in enumerate(ests):
            pa = est.predict(a)
            pb = est.predict(b)
            bad = np.flatnonzero(~np.isclose(pa, pb, atol=1e-10, rtol=1e-10))
            for r in bad:
                rows_examined.append((k, int(r), float(pa[r]), float(pb[r])))
        report['rows_with_prediction_difference'] = [
            dict(estimator=k, quantile=est_info[k]['quantile'], row=r,
                 engine_prediction=pa_, validator_prediction=pb_, difference=abs(pa_ - pb_))
            for k, r, pa_, pb_ in rows_examined]

        # ---- 3. tree-level routing evidence ----------------------------
        evidence = []
        for k, r, pa_, pb_ in rows_examined:
            est = ests[k]
            xa = a[r]
            xb = b[r]
            ta, ca = raw_predict(est, xa)
            tb, cb = raw_predict(est, xb)
            # manual walk must reproduce sklearn exactly, else the evidence is worthless
            skl_a = float(est.predict(xa.reshape(1, -1))[0])
            skl_b = float(est.predict(xb.reshape(1, -1))[0])
            diverged = []
            for (s, va, patha, leafa), (_, vb, pathb, leafb) in zip(ca, cb):
                if leafa != leafb or va != vb:
                    # find the first node where the two paths disagree
                    first = None
                    for (na, fa, tha, vala, la), (nb, fb, thb, valb, lb) in zip(patha, pathb):
                        if la != lb:
                            first = dict(stage=s, node=int(na), feature_index=int(fa),
                                         feature_name=cols[fa], num_threshold=repr(tha),
                                         engine_value=repr(vala), validator_value=repr(valb),
                                         engine_goes_left=bool(la), validator_goes_left=bool(lb),
                                         engine_minus_threshold=vala - tha,
                                         validator_minus_threshold=valb - tha,
                                         threshold_straddled=bool((vala <= tha) != (valb <= tha)))
                            break
                    diverged.append(dict(stage=s, engine_leaf_value=va, validator_leaf_value=vb,
                                         leaf_index_engine=leafa, leaf_index_validator=leafb,
                                         first_divergent_node=first))
            evidence.append(dict(
                estimator=k, quantile=est_info[k]['quantile'], row=r,
                manual_walk_matches_sklearn=dict(
                    engine=bool(abs(ta - skl_a) < 1e-12), validator=bool(abs(tb - skl_b) < 1e-12),
                    manual_engine=ta, sklearn_engine=skl_a,
                    manual_validator=tb, sklearn_validator=skl_b),
                total_stages=len(est._predictors),
                stages_with_different_leaf=len(diverged),
                prediction_difference=abs(ta - tb),
                sum_of_leaf_value_differences=sum(x['engine_leaf_value'] - x['validator_leaf_value'] for x in diverged),
                divergences=diverged))
        report['tree_routing_evidence'] = evidence

        # ---- 4. propagation to bounds and released scores --------------
        prop = []
        for control in m['controls']:
            cid = control['control_id']
            model = models[control['method']]
            sc = scalar_stream(model, X_scalar, local, obs, avail, control)
            stream = table(path / (cid + '_issued.csv.gz'))
            cols_cmp = {}
            for col in ['point', 'raw_lower', 'raw_upper', 'lower', 'upper']:
                u = np.asarray(stream[col], float)
                v = np.asarray(sc[col], float)
                bad = np.flatnonzero(~np.isclose(u, v, atol=1e-10, rtol=1e-10, equal_nan=True))
                cols_cmp[col] = dict(violations=int(len(bad)), rows=[int(x) for x in bad],
                                     max_difference=float(np.nanmax(np.abs(u - v))) if len(u) else 0.0)
            rel = table(path / (cid + '_released.csv.gz'))
            exp = sc['releases']
            rel_cmp = dict(count_engine=len(rel), count_validator=len(exp),
                           counts_match=len(rel) == len(exp))
            if len(rel) and len(rel) == len(exp):
                ru = np.asarray(rel.score, float)
                rv = np.asarray(exp.score, float)
                badr = np.flatnonzero(~np.isclose(ru, rv, atol=1e-10, rtol=1e-10, equal_nan=True))
                rel_cmp.update(identity_match=bool(rel.row_id.tolist() == exp.row_id.tolist()),
                               release_order_match=bool(rel.released_at_origin.tolist() == exp.released_at_origin.tolist()),
                               score_violations=int(len(badr)), score_rows=[int(x) for x in badr],
                               max_score_difference=float(np.nanmax(np.abs(ru - rv))))
            prop.append(dict(control_id=cid, method=control['method'], strategy=control['strategy'],
                             columns=cols_cmp, released=rel_cmp))
        report['propagation'] = prop

    out = A.OUT / 'MECHANISM_PROOF.json'
    out.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print(json.dumps(dict(
        stage=STAGE,
        feature_max_difference=report['feature_difference']['max_overall'],
        within_frozen_feature_tolerance=report['feature_difference']['within_frozen_tolerance'],
        worst_feature=report['feature_difference']['ulp_multiple_of_max'],
        rows_with_prediction_difference=len(report['rows_with_prediction_difference']),
        routing_cases=[dict(estimator=e['estimator'], row=e['row'],
                            manual_matches_sklearn=e['manual_walk_matches_sklearn']['engine'] and e['manual_walk_matches_sklearn']['validator'],
                            stages_with_different_leaf=e['stages_with_different_leaf'],
                            prediction_difference=e['prediction_difference'])
                       for e in report['tree_routing_evidence']],
        written=str(out)), indent=2, default=str))


if __name__ == '__main__':
    main()
