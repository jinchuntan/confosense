import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from support_design005 import allocation_counts, request_count, binomial_minimum, grouped_batch_folds, contexts, schedule, no_fitting

def metadata(groups=1,n=240,freq='1min'):
    rows=[]
    for g in range(groups):
        times=pd.date_range('2024-01-01',periods=n,freq=freq)+pd.Timedelta(days=g)
        rows.extend(dict(group_id=f'g{g}',origin_time=t,target_time=t+pd.Timedelta(freq),row_id=f'{g}:{i}') for i,t in enumerate(times))
    return pd.DataFrame(rows)

def test_complete_rotations_balance_every_request_budget():
    for q in range(100):
        np.testing.assert_array_equal(allocation_counts(q,range(21)),np.full(21,q))
        assert allocation_counts(q,range(5)).sum()==5*q
    assert (allocation_counts(13,range(5))==0).sum()==4
    assert request_count(np.nextafter(41.,0))<21 and request_count(41.)==21

def test_fixed_replication_criterion_is_minimal():
    import math
    for p in [1-.9**6,1-.9**60]:
        n=binomial_minimum(p)
        def success(m):return 1-sum(math.comb(m,j)*p**j*(1-p)**(m-j) for j in range(min(m,4)+1))
        assert success(n)>=.95 and success(n-1)<.95

def test_whole_run_batches_have_disjoint_tests_and_prior_training():
    m=metadata(30)
    folds=grouped_batch_folds(m);seen=set()
    for f in folds:
        sets=[set(m.iloc[f[r]].group_id) for r in ['train','calibration','test']]
        assert not (sets[0]&sets[1] or sets[1]&sets[2] or sets[0]&sets[2])
        assert not seen&sets[2];seen|=sets[2]
        assert m.iloc[f['calibration']].target_time.max()<m.iloc[f['test']].origin_time.min()
        assert all(len(m.iloc[f[r]])==len(sets[i])*240 for i,r in enumerate(['train','calibration','test']))
    assert len(seen)==18

def test_contexts_deterministic_and_do_not_cross_gaps():
    m=metadata(1,600,'10min');m=m.drop(index=250).reset_index(drop=True)
    a=contexts(m,'pleia',pd.Timedelta('10min'),0,'outer_test')
    b=contexts(m,'pleia',pd.Timedelta('10min'),0,'outer_test')
    assert [(c['context_id'],c['onset_offset']) for c in a]==[(c['context_id'],c['onset_offset']) for c in b]
    for c in a:
        times=m.iloc[c['context_rows']].target_time
        assert times.diff().dropna().eq(pd.Timedelta('10min')).all()
        assert c['onset_offset']>=c['warmup']
        assert c['onset_offset']+c['duration']+c['followup']<=len(c['context_rows'])

def test_nulls_kept_and_repeated_variants_do_not_create_contexts():
    m=metadata(1,221);y=np.zeros(len(m));_,e=schedule(m,y,'rico',pd.Timedelta('1min'),0,'outer_test',{'__pooled__':0.})
    assert len(e)==42 and e.context_id.nunique()==1
    numeric=e[~e.family.isin(['random_missing','block_missing'])]
    assert numeric.null.all() and not numeric.effective.any()
    assert e.onset.nunique()==1 and e.placed.all()

def test_fitting_guard_stops_route_before_execution():
    ns={'__name__':'src.fake_forbidden'}
    exec('def fit():\n    raise RuntimeError("body must not execute")',ns)
    with pytest.raises(AssertionError,match='Fitting forbidden'):
        with no_fitting():ns['fit']()
