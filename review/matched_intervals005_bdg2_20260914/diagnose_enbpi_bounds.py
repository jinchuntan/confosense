"""Reconstruct all native EnbPI bounds from actual reloaded float32 points."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','MKL_NUM_THREADS'):os.environ[name]='1'
from common import *
import math,numpy as np,pandas as pd
from src.intervals005_common import Operations,frame,load_owner
from src.intervals005_data import load_data


def main():
    os.chdir(SMART);before=tree(RUN);p=read(DESIGN/'frozen_protocol.json');prepared=None;rows=[]
    with Operations(forbid=True):
        for h in (1,3,6):
            data,roles,prepared=load_data(p['references'][str(h)],prepared)
            owner=load_owner(RUN/f'stages/owner_cal_h{h}_enbpi/owner.pkl')
            point=owner.estimator_.single_estimator_.predict(data['X'].iloc[roles['test']].to_numpy()).astype(np.float64)
            scores=owner.conformity_scores_;values=scores[np.isfinite(scores)];n=len(values)
            def q(alpha,reverse=False):
                sign=-1 if reverse else 1;ref=1-alpha if reverse else alpha
                probability=min(1,max(0,math.ceil(ref*(n+1))/n))
                return sign*np.quantile(sign*values,probability,method='lower')
            for level in (.9,.95):
                raw=frame(RUN/f'stages/raw_h{h}_enbpi/test_{int(100*level)}.csv.gz')
                np.testing.assert_array_equal(raw.point.to_numpy(np.float32).astype(np.float64),point)
                lo=-q(level) if owner.conformity_score_function_.sym else q((1-level)/2,True)
                hi=q(level) if owner.conformity_score_function_.sym else q(1-(1-level)/2)
                np.testing.assert_allclose(raw.static_lower,point+lo,atol=1e-7,rtol=1e-7)
                np.testing.assert_allclose(raw.static_upper,point+hi,atol=1e-7,rtol=1e-7)
                delta=max(float(np.max(np.abs(raw.static_lower-point-lo))),float(np.max(np.abs(raw.static_upper-point-hi))))
                rows.append(dict(horizon=h,level=level,n_test=len(point),native_point_dtype='float32',csv_point_read_as='float64 decimal',float32_roundtrip_exact=True,maximum_point_decimal_difference=float(np.max(np.abs(raw.point-point))),maximum_native_bound_difference=delta,passed=True))
                print(json.dumps(rows[-1]),flush=True)
            del data,point
    assert tree(RUN)==before
    pd.DataFrame(rows).to_csv(REVIEW/'enbpi_bounds_diagnosis.csv',index=False)
    atomic(REVIEW/'enbpi_bounds_diagnosis.json',dict(passed=True,rows=rows,models_fitted=0,calibrators_fitted=0,tolerances_unchanged=True,scientific_run_unchanged=True))


if __name__=='__main__':main()
