import numpy as np
import pandas as pd
from scripts.independent_bdg2_operational_audit import binary_window_means,recovery_rows


def test_binary_prefix_means_match_exact_counts_and_rolling_for_all_hourly_windows():
    rng=np.random.default_rng(42)
    for values in [np.ones(100,bool),rng.random(100)>.2]:
        for window in range(1,25):
            expected=np.array([sum(values[i:i+window])/window for i in range(len(values)-window+1)])
            np.testing.assert_array_equal(binary_window_means(values,window),expected)
            np.testing.assert_array_equal(binary_window_means(values,window),
                pd.Series(values.astype(float)).rolling(window).mean().to_numpy()[window-1:])


def test_exact_saved_recovery_boundary_is_not_relaxed_by_convolution_rounding():
    times=pd.date_range('2020',periods=62,freq='h')
    stream=pd.DataFrame(dict(group_id='g',target_time=times,observed=0.,lower=-1.,upper=1.))
    stream.loc[19,'upper']=-.1  # 19/20 pre-event observations covered.
    events=pd.DataFrame([dict(group_id='g',effective=True,onset=times[20],end=times[21])])
    old_mean=np.convolve(np.ones(40),np.ones(10)/10,mode='valid')[0]
    assert abs(old_mean-.95)<=.05 and abs(1.-.95)>.05
    result=recovery_rows(stream,stream.copy(),events).iloc[0]
    assert result.pre_coverage==.95 and result.window_steps==10
    assert result.status=='right_censored' and result.recovery_censored
    assert np.isnan(result.recovery_minutes) and result.followup_minutes==2400.
