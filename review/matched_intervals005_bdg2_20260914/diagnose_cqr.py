"""No-fit diagnosis of native MAPIE's default asymmetric correction."""
from common import *
import inspect
import numpy as np
import pandas as pd
from mapie.regression import ConformalizedQuantileRegressor
from src.intervals005_common import Operations,frame


def main():
    before=tree(RUN);rows=[]
    assert inspect.signature(ConformalizedQuantileRegressor.predict_interval).parameters['symmetric_correction'].default is False
    with Operations(forbid=True):
        for h in (1,3,6):
            for level in (.9,.95):
                folder=RUN/f'stages/raw_h{h}_cqr_l{int(100*level)}'
                cal=frame(folder/f'calibration_{int(100*level)}.csv.gz')
                y=frame(folder/'calibration_metadata.csv.gz').y_true.to_numpy()
                raw=frame(folder/f'test_{int(100*level)}.csv.gz')
                scores=np.vstack([cal.raw_lower-y,y-cal.raw_upper])
                q=(1-(1-level)/2)*(1+1/len(y))
                lo,hi=np.quantile(scores,q,axis=1,method='higher')
                expected_lo=np.minimum(raw.raw_lower-lo,raw.raw_upper+hi)
                expected_hi=np.maximum(raw.raw_lower-lo,raw.raw_upper+hi)
                d=max(float(np.max(np.abs(raw.static_lower-expected_lo))),float(np.max(np.abs(raw.static_upper-expected_hi))))
                np.testing.assert_allclose(raw.static_lower,expected_lo,atol=1e-7,rtol=1e-7)
                np.testing.assert_allclose(raw.static_upper,expected_hi,atol=1e-7,rtol=1e-7)
                rows.append(dict(horizon=h,level=level,n_calibration=len(y),lower_correction=float(lo),upper_correction=float(hi),quantile_probability=q,max_bound_difference=d,n_test=len(raw),passed=True))
    assert tree(RUN)==before
    pd.DataFrame(rows).to_csv(REVIEW/'cqr_native_diagnosis.csv',index=False)
    atomic(REVIEW/'cqr_native_diagnosis.json',dict(passed=True,rows=rows,native_default_symmetric_correction=False,models_fitted=0,calibrators_fitted=0,scientific_run_unchanged=True,classification='validator assumed symmetric max-score correction; native generator used installed default asymmetric tail corrections'))
    print(json.dumps(rows,indent=2),flush=True)


if __name__=='__main__':main()
