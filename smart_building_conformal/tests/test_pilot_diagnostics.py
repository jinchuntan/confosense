"""Allocation changes must preserve scientific data; verify native byte fields."""
import ctypes
import numpy as np
import pandas as pd
import pytest
from src import prepare_data as P
from src.pilot_resources import _MemoryStatus, _ProcessMemory, memory_snapshot


@pytest.mark.parametrize('optional_covariate', [True, False])
def test_projected_room_load_preserves_selection_and_processed_values(tmp_path, optional_covariate):
    cfg=dict(paths={'interim_dir':str(tmp_path)},
        dataset=dict(room_all_file='room.csv',csv_sep=';',timestamp_col='Date',block_col='block',room_col='room',target_var='V2'),
        covariates=dict(outdoor_temp='tmed',humidity='hrmed',radiation='radmed',setpoint='V12',hvac_state='V4',hvac_mode_onehot=['V5_0']),
        resample=dict(freq='10min'),target_selection=dict(min_std=.1,min_valid_obs=5),
        outliers=dict(target_min=0,target_max=50),missing=dict(max_short_gap_steps=3))
    data=pd.DataFrame(dict(Date=list(pd.date_range('2021-01-01',periods=20,freq='10min'))*2,
        block=['B']*20+['C']*20,room=[11]*20+[12]*20,V2=[20.,21.,22.,23.,24.]*8,
        tmed=np.arange(40,dtype=float),V4=[1]*40,cons_total=np.arange(40),unused=['x'*300]*40))
    data.loc[4,'V2']=np.nan
    data.loc[5,'Date']=data.loc[4,'Date']  # duplicate-time policy stays unchanged
    if optional_covariate:data['V12']=22.
    data.to_csv(tmp_path/'room.csv',sep=';',index=False)
    full=P.load_room_table(cfg)
    projected=P.load_room_table(cfg,model_columns_only=True)
    assert 'unused' not in projected and 'cons_total' not in projected
    pd.testing.assert_frame_equal(projected,full[projected.columns])
    choice, audit=P.select_target(full,cfg)
    projected_choice,projected_audit=P.select_target(projected,cfg)
    assert choice==projected_choice
    pd.testing.assert_frame_equal(audit,projected_audit)
    pd.testing.assert_frame_equal(P.build_dataset(full,choice,cfg),P.build_dataset(projected,choice,cfg))


def test_windows_memory_structures_use_documented_byte_fields():
    assert ctypes.sizeof(_MemoryStatus)==64
    assert _MemoryStatus.total_physical.offset==8
    assert _MemoryStatus.available_physical.offset==16
    assert ctypes.sizeof(ctypes.c_void_p)==8  # declared pilot host
    assert ctypes.sizeof(_ProcessMemory)==80
    assert _ProcessMemory.peak_rss.offset==8 and _ProcessMemory.rss.offset==16
    assert _ProcessMemory.private_bytes.offset==72
    s=memory_snapshot()
    assert 0<s['rss_bytes']<=s['lifetime_peak_rss_bytes']
    assert 0<s['available_ram_bytes']<=s['physical_ram_bytes']
