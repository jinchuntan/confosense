"""No-fit independent OOB reconstruction using the installed accumulator dtype."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
from common import *
import warnings,numpy as np,pandas as pd
from src.intervals005_common import Operations,load_owner
from src.intervals005_data import load_data


def main():
    os.chdir(SMART)
    before=tree(RUN);p=read(DESIGN/'frozen_protocol.json');prepared=None;rows=[]
    with Operations(forbid=True):
        for h in (1,3,6):
            data,roles,prepared=load_data(p['references'][str(h)],prepared)
            owner=load_owner(RUN/f'stages/owner_cal_h{h}_enbpi/owner.pkl')
            X=data['X'].iloc[roles['calibration']].to_numpy()
            prediction=np.column_stack([e.predict(X) for e in owner.estimator_.estimators_])
            mask=owner.estimator_.k_==1
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',RuntimeWarning)
                old=np.nanmean(np.where(mask,prediction,np.nan),axis=1)
                corrected=np.nanmean(np.where(mask,prediction.astype(np.float64),np.nan),axis=1)
            y=data['y'][roles['calibration']]
            expected=y-corrected
            if owner.conformity_score_function_.sym:expected=np.abs(expected)
            np.testing.assert_allclose(owner.conformity_scores_,expected,atol=1e-7,rtol=1e-7,equal_nan=True)
            d=float(np.nanmax(np.abs(owner.conformity_scores_-expected)))
            rows.append(dict(horizon=h,n_calibration=len(y),base_prediction_dtype=str(prediction.dtype),native_accumulator_dtype='float64',old_float32_difference=float(np.nanmax(np.abs(owner.conformity_scores_-(y-old)))),corrected_max_difference=d,nonfinite_scores=int((~np.isfinite(expected)).sum()),passed=True))
            print(json.dumps(rows[-1]),flush=True)
            del data,X,prediction
    assert tree(RUN)==before
    pd.DataFrame(rows).to_csv(REVIEW/'enbpi_precision_diagnosis.csv',index=False)
    atomic(REVIEW/'enbpi_precision_diagnosis.json',dict(passed=True,rows=rows,models_fitted=0,calibrators_fitted=0,scientific_run_unchanged=True,tolerances_unchanged=True))


if __name__=='__main__':main()
