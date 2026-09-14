"""No-fit scope, frequency, seasonal and causal-boundary acceptance."""
import json
import numpy as np
import pandas as pd
import pytest

from src.intervals005_common import LEVELS, METHODS, ROOT
from src.intervals005_data import MATRIX, joint_join
from src.intervals005_stream import emit
from src.matched_intervals005 import config_scope, expected_cells, expected_operations, scope_policy


def authorization(name):
    return json.loads((ROOT/'configs'/f'matched_intervals005_remaining_{name}_f2_s42_v1.json').read_text())


def test_authorized_remaining_scope_and_exact_cell_manifest():
    expected={
        'pleia_energy':([1,3,6],30,51,True),
        'pleia':([1,3,6],30,51,True),
        'rico':([5,15,30,60],40,68,False),
    }
    for dataset,(horizons,cells,fits,seasonal) in expected.items():
        scope,selected=config_scope(authorization(dataset),MATRIX)
        assert scope['horizons']==horizons and len(selected)==cells
        assert expected_cells(scope)['interval_method']==cells
        assert expected_operations(scope)['quantile_estimator_fit']+expected_operations(scope)['xgboost_estimator_fit']==fits
        assert scope_policy(dataset)['seasonal'] is seasonal
        assert scope_policy(dataset)['frequency']==('1min' if dataset=='rico' else '10min')
    wrong=authorization('rico');wrong['scope']['horizons']=[1,3,6]
    with pytest.raises(ValueError,match='authorization'):config_scope(wrong,MATRIX)


@pytest.mark.parametrize('frequency,horizons',[(pd.Timedelta(minutes=10),[1,3,6]),(pd.Timedelta(minutes=1),[5,15,30,60])])
def test_joint_frequency_is_explicit_and_rejects_wrong_default(frequency,horizons):
    origin=pd.date_range('2024-01-01',periods=4,freq=frequency)
    frames={h:pd.DataFrame(dict(row_id=[f'{h}:{i}' for i in range(4)],group_id='g',origin_time=origin,target_time=origin+h*frequency,y_true=np.arange(4.))) for h in horizons}
    assert len(joint_join(frames,horizons,frequency=frequency)[horizons[0]])==4
    with pytest.raises(ValueError,match='explicit'):joint_join(frames,horizons)
    with pytest.raises(ValueError,match='target mismatch'):joint_join(frames,horizons,frequency=pd.Timedelta(hours=1))


def test_rico_causal_replay_resets_at_run_gap_and_cannot_use_future_truth():
    freq=pd.Timedelta(minutes=1)
    targets=pd.DatetimeIndex(['2024-01-01 00:01','2024-01-01 00:02','2024-01-01 00:03','2024-01-01 02:01','2024-01-01 02:02','2024-01-01 02:03'])
    meta=pd.DataFrame(dict(row_id=[f'r{i}' for i in range(len(targets))],group_id='run-group',origin_time=targets-freq,target_time=targets,y_true=np.arange(len(targets),dtype=float),available=True))
    cal_times=pd.date_range(end='2023-12-31 23:59',periods=400,freq=freq)
    calibration=pd.DataFrame(dict(group_id='run-group',target_time=cal_times,y_true=np.linspace(-1,1,400)))
    raw=pd.DataFrame(dict(point=np.zeros(len(meta)),raw_lower=-np.ones(len(meta)),raw_upper=np.ones(len(meta)),static_lower=-np.ones(len(meta)),static_upper=np.ones(len(meta)),static_raw_lower=-np.ones(len(meta)),static_raw_upper=np.ones(len(meta))))
    rawcal=pd.DataFrame(dict(point=np.zeros(len(calibration)),raw_lower=-np.ones(len(calibration)),raw_upper=np.ones(len(calibration))))
    clean=emit('recentred_enbpi_updated',.9,'owner',pd.DataFrame({'x':np.arange(len(meta))}),meta,raw,calibration,rawcal,freq)
    changed=meta.copy();changed.loc[3:,'y_true']+=10_000
    altered=emit('recentred_enbpi_updated',.9,'owner',pd.DataFrame({'x':np.arange(len(meta))}),changed,raw,calibration,rawcal,freq)
    np.testing.assert_array_equal(clean['stream'].lower.iloc[:3],altered['stream'].lower.iloc[:3])
    assert clean['stream'].segment_id.nunique()==2
    assert 'r2' not in set(clean['released_scores'].row_id), 'a completed run must not release into a later run'
