"""No-fit additional native-formula and unseen-group checks on saved tiny owners."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'smart_building_conformal'))
import numpy as np
import pandas as pd
from src.intervals005_common import *
from src.intervals005_owners import raw_predictions
from src.intervals005_stream import emit
from src.intervals005_validate import scalar_replay
from src.operational004_fixtures import fixture_data


def test_native_enbpi_formula_and_unseen_group_initialization():
    out=ROOT/'outputs/matched_intervals005/synthetic_v1/run';before=tree(out)
    store=Stages(out,read(out/'checkpoint_manifest.json')['spec'],resume=True)
    with Operations(forbid=True):
        for h in (1,3):
            _,s,w,_,_=fixture_data(n=1100,groups=2,horizon=h)
            per=[np.flatnonzero(w['meta'].group_id.eq(g)) for g in ('asset0','asset1')]
            ca=np.concatenate([r[356:606] for r in per]);te=np.concatenate([r[612:642] for r in per])
            def meta(ix):
                f=w['meta'].iloc[ix][['row_id','group_id','origin_time','target_time']].reset_index(drop=True).copy();f['y_true']=w['y'][ix];f['available']=True;return f
            cal=meta(ca);test=meta(te);test.group_id=['unseen_A']*30+['unseen_B']*30
            path=store.get(f'owner_cal_h{h}_enbpi');owner=load_owner(path/'owner.pkl');X=w['X'].iloc[te].reset_index(drop=True)
            raw=raw_predictions(owner,'enbpi',X.to_numpy());rawcal=raw_predictions(owner,'enbpi',w['X'].iloc[ca].to_numpy())
            scores=owner.conformity_scores_;values=scores[np.isfinite(scores)];n=len(values)
            for level in LEVELS:
                def q(alpha,reverse=False):
                    sign=-1 if reverse else 1;ref=1-alpha if reverse else alpha;cor=min(1,max(0,math.ceil(ref*(n+1))/n))
                    return sign*np.quantile(sign*values,cor,method='lower')
                lo=-q(level) if owner.conformity_score_function_.sym else q((1-level)/2,True)
                hi=q(level) if owner.conformity_score_function_.sym else q(1-(1-level)/2)
                np.testing.assert_allclose(raw[level].static_lower,raw[level].point+lo,atol=1e-7)
                np.testing.assert_allclose(raw[level].static_upper,raw[level].point+hi,atol=1e-7)
                result=emit('recentred_enbpi_updated',level,digest(path/'owner.pkl'),X,test,raw[level],cal,rawcal[level],s.freq)
                scalar=scalar_replay(test,raw[level],cal,rawcal[level],level,'recentred_enbpi','native_updated',freq=s.freq)
                np.testing.assert_array_equal(result['stream'].lower,scalar['lower'])
                assert result['stream'].update_pool_n.iloc[0]==len(cal)
                assert result['stream'].update_pool_n.iloc[30]==len(cal)
    assert tree(out)==before
