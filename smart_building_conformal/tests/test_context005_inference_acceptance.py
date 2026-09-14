"""No-fitting acceptance of paired original-unit inference and unavailable cases."""
import numpy as np
import pandas as pd
from src.context005_metrics import inference
from src.operational004_design import STRATA

def fixture(dataset,n):
    ctx=pd.DataFrame(dict(context_id=[str(i) for i in range(n)],outer_fold=2,segment_id='segment',context_start_row_id=[str(i) for i in range(n)],onset=pd.date_range('2020',periods=n,freq='1D'),phase=[i%2 for i in range(n)]))
    rows=[dict(context_id=str(i),control_id=control,rule_id='fixed',channel='combined',family=f,severity=s,model_seed=seed,recall=float((i+seed)%3==0)) for i in range(n) for control in ['a','paired_equal'] for f,s in STRATA for seed in range(42,47)]
    return pd.DataFrame(rows),ctx

def test_pleia_paired_week_blocks_and_original_seed_pooling():
    f,c=fixture('pleia_energy',35);a,r=inference(f,c,'pleia_energy')
    draws=np.asarray(r['draws']);assert draws.shape==(2000,35) and r['seed']==20240601
    assert set(a.status)=={'supported'} and a.valid_draws.eq(2000).all()
    np.testing.assert_array_equal(a[['lower','upper']].iloc[0],a[['lower','upper']].iloc[1])
    # Each full block carries adjacent contexts; repeats are bootstrap weights.
    assert (np.diff(draws.reshape(2000,5,7),axis=2)==1).all()
    short=f[f.context_id.isin(c.context_id.iloc[:28])]
    _,bad=inference(short,c.iloc[:28],'pleia_energy');assert bad['status']=='unavailable_complete_week_blocks'

def test_rico_phase_weights_and_degenerate_bounds():
    f,c=fixture('rico',6);a,r=inference(f,c,'rico')
    draws=np.asarray(r['draws']);assert draws.shape==(2000,6)
    assert ((draws[:,:3]%2)==0).all() and ((draws[:,3:]%2)==1).all()
    assert a.valid_draws.eq(2000).all()
    f.recall=0;flat,_=inference(f,c,'rico')
    assert set(flat.status)=={'unavailable_valid_draw_or_degenerate'} and flat.lower.isna().all()
