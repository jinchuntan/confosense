import numpy as np
import pandas as pd
from scripts.combine_bdg2_threefold import N,TP,COUNTS,rates,paired_buildings


def test_pool_sums_stratum_counts_and_original_exposure():
    a=pd.Series({**dict.fromkeys(COUNTS,0.),**dict.fromkeys(N,1.),**dict.fromkeys(TP,1.),
                 'clean_episodes':2.,'exposure_days':1.})
    b=pd.Series({**dict.fromkeys(COUNTS,0.),**dict.fromkeys(N,99.),**dict.fromkeys(TP,9.),
                 'clean_episodes':3.,'exposure_days':9.})
    pooled=rates(a+b)
    assert np.isclose(pooled['macro_event_recall'],.1)
    assert pooled['background_episodes_per_asset_day']==.5
    assert not np.isclose(pooled['macro_event_recall'],(rates(a)['macro_event_recall']+rates(b)['macro_event_recall'])/2)


def test_resample_original_building_keeps_all_folds_and_catalogues_together():
    rows=[];groups=[str(i) for i in range(10)]
    for fold in range(3):
        for g in range(10):
            for c in ['a','b']:
                rows.append({'candidate_id':c,'group_id':str(g),'outer_fold':fold,
                    **dict.fromkeys(COUNTS,0.),**dict.fromkeys(N,5.*(g+1)),
                    **dict.fromkeys(TP,float((g+1)*(1 if c=='a' else 2))),
                    'exposure_days':float(fold+1),'clean_episodes':float(g+(c=='a'))})
    inputs=pd.DataFrame(rows)
    result,reps,draws=paired_buildings(inputs,'a','b',groups,reps=25,min_valid=20)
    assert draws.shape==(25,10) and result.original_buildings.eq(10).all()
    for i,draw in enumerate(draws):
        weights=np.bincount(draw,minlength=10)
        totals={}
        for c in ['a','b']:
            sub=inputs[inputs.candidate_id==c]
            totals[c]=rates(sub[COUNTS].mul(sub.group_id.map(lambda x:weights[int(x)]),axis=0).sum())
        for metric in ['macro_event_recall','background_episodes_per_asset_day']:
            assert np.isclose(reps.loc[i,'delta_'+metric],totals['a'][metric]-totals['b'][metric])
    # Duplicating catalogue-event contributions must not duplicate original
    # exposure; unavailable strata must never receive an invented interval.
    inputs.loc[:,'n0']=0.;inputs.loc[:,'tp0']=0.
    result,reps,_=paired_buildings(inputs,'a','b',groups,reps=25,min_valid=20)
    assert not reps.valid.any() and result.ci_lower.isna().all()
