"""Diagnose the validator/run mismatch on context_3c2ed441cb78fe67ef35_v0.

Read-only. Fits are forbidden. Determines whether the discrepancy is a defect in
the replay science or a reconstruction-precision artifact at a gradient-boosting
bin boundary, and reports the exact row, feature and magnitudes.
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
from src.intervals005_common import Operations, load_owner
from src.context005_spec import table, context_positions
from src.context005_data import load_real
from src.context005_features import bounded_frame
from src.context005_validate import scalar_observations, scalar_inputs, scalar_stream

STAGE = 'context_3c2ed441cb78fe67ef35_v0'
RUN = common.run()
DESIGN = common.design()


def main():
    p = read(DESIGN / 'frozen_protocol.json')
    m = p['manifest']
    with Operations(forbid=True):
        d = load_real(m['dataset'], m['outer_fold'])
        meta = d['meta'].iloc[d['roles']['outer_test']].reset_index(drop=True)
        variants = table(RUN / 'stages/tables/variants.csv')
        vr = variants[variants.stage == STAGE].to_dict('records')[0]
        ctxmap = d['contexts'].set_index('context_id').to_dict('index')
        ctx = dict(ctxmap[vr['context_id']], context_id=vr['context_id'])
        ix = context_positions(meta, ctx)
        local = meta.iloc[ix].reset_index(drop=True)
        base, season = bounded_frame(d['series'], local, d['fcfg'], d['horizon'])
        truth, obs, avail = scalar_observations(base, local, None)
        Xs = scalar_inputs(base, local, d['fcfg'], d['horizon'], d['frequency'], season,
                           d['X'].columns, obs, avail)

        path = RUN / 'stages' / vr['canonical_stage']
        saved_feat = table(path / 'features.csv.gz')[list(d['X'].columns)]
        models = load_owner(RUN / 'stages/controls/controls.pkl')

        print('=== feature reconstruction difference (validator X vs saved features) ===')
        diffs = {}
        for c in d['X'].columns:
            a = Xs[c].to_numpy(float)
            b = saved_feat[c].to_numpy(float)
            diffs[c] = float(np.nanmax(np.abs(a - b))) if len(a) else 0.0
        worst = sorted(diffs.items(), key=lambda kv: -kv[1])[:6]
        for c, v in worst:
            print(f'  {c:24s} max|diff| = {v:.3e}')
        print(f'  overall max feature difference = {max(diffs.values()):.3e} (validator tolerance 1e-10)')
        print()

        for control in m['controls']:
            cid = control['control_id']
            model = models[control['method']]
            scalar = scalar_stream(model, Xs, local, obs, avail, control)
            stream = table(path / (cid + '_issued.csv.gz'))
            for col in ['lower', 'upper', 'point', 'raw_lower', 'raw_upper']:
                a = np.asarray(stream[col], float)
                b = np.asarray(scalar[col], float)
                bad = np.where(~np.isclose(a, b, atol=1e-10, rtol=1e-10, equal_nan=True))[0]
                if len(bad):
                    print(f'=== MISMATCH {cid} / {col}: {len(bad)} of {len(a)} rows ===')
                    for i in bad:
                        print(f'  row {i}: saved={a[i]!r} scalar={b[i]!r} absdiff={abs(a[i]-b[i]):.6e}')
                        fd = {c: abs(float(Xs[c].iloc[i]) - float(saved_feat[c].iloc[i])) for c in d['X'].columns}
                        nz = {c: v for c, v in fd.items() if v > 0}
                        print(f'    nonzero feature input differences at this row: '
                              f'{ {c: f"{v:.3e}" for c, v in sorted(nz.items(), key=lambda kv: -kv[1])[:6]} }')
                        # Feed BOTH feature vectors through the same estimators.
                        if control['method'] != 'persistence_split':
                            sub = model.owner._mapie_quantile_regressor.estimators_
                            xs = Xs.to_numpy()[i:i + 1]
                            xv = saved_feat.to_numpy()[i:i + 1]
                            ps = [float(e.predict(xs)[0]) for e in sub]
                            pv = [float(e.predict(xv)[0]) for e in sub]
                            print(f'    estimator preds from validator X : {ps}')
                            print(f'    estimator preds from saved    X : {pv}')
                            print(f'    identical given saved X? {np.allclose(ps, pv, atol=0, rtol=0)}')
                    print()


if __name__ == '__main__':
    main()
