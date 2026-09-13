import numpy as np
import pandas as pd
import pytest
from src.operational004_fixtures import fixture_data
from src.operational004_design import build_windows
from src.operational004_stream import corrupted_features


@pytest.mark.parametrize('dtype',[np.int64,np.float64,bool])
def test_numeric_missingness_covariate_zero_identity_and_causal_missing(dtype):
    prepared,_,_,cfg,_=fixture_data(n=150,groups=1)
    prepared.series[0].frame['target_was_missing']=np.zeros(150,dtype=dtype)
    s,w,fc=build_windows(prepared,cfg,1)
    original=s.series[0].frame.copy(deep=True)
    clean=corrupted_features(s,w['meta'],w['y'],np.ones(len(w['y']),bool),1,fc,list(w['X']))
    np.testing.assert_array_equal(clean.to_numpy(float),w['X'].to_numpy(float))
    flags=np.ones(len(w['y']),bool);flags[50]=False
    obs=w['y'].copy();obs[50]=np.nan
    changed=corrupted_features(s,w['meta'],obs,flags,1,fc,list(w['X']))
    assert np.isfinite(changed.to_numpy()).all()
    at=w['meta'].iloc[50].target_time
    before=w['meta'].origin_time<at
    np.testing.assert_array_equal(changed.loc[before].to_numpy(),clean.loc[before].to_numpy())
    row=np.flatnonzero(w['meta'].origin_time.eq(at))[0]
    assert changed.iloc[row].target_was_missing==1.
    assert changed.iloc[row].target_lag_0==clean.iloc[row-1].target_lag_0
    pd.testing.assert_frame_equal(s.series[0].frame,original)
