import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

spec=importlib.util.spec_from_file_location('independent_audit',Path(__file__).parents[1]/'scripts/independent_bdg2_operational_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def test_independent_episode_matching_preexisting_and_censoring():
    times=pd.date_range('2020',periods=8,freq='h')
    stream=pd.DataFrame(dict(target_time=times,group_id='g',observed=[2,2,0,2,2,0,np.nan,0],
                            lower=-1.,upper=1.,available=[True]*6+[False,True]))
    events=pd.DataFrame([dict(event_id=str(i),group_id='g',family='bias',severity=1.,effective=True,
        segment_id='g:segment:0',start_index=a,onset=times[a],tolerance_end=times[0]+pd.Timedelta(hours=b))
        for i,(a,b) in enumerate([(1,2),(3,4),(7,9)])])
    episodes,matches,flags=audit.episodes_and_matches(stream,dict(k=1,m=1),events)
    combined=episodes[episodes.channel=='combined']
    assert combined.start_index.tolist()==[0,3,6]
    pe=matches[matches.channel=='combined']
    assert pe.detected.tolist()==[False,True,False]
    assert pe.eligible.tolist()==[True,True,False]
    assert pe.followup_minutes.tolist()==[60.,60.,0.]
    assert flags['availability_only'].sum()==1


def test_independent_metrics_custom_f1_and_degenerate_bounds():
    bank=pd.DataFrame(0.,index=range(10),columns=audit.NAMES)
    bank.exposure_days=10.;bank.clean_episodes=np.arange(10,dtype=float)
    bank.corrupted_episodes=21.;bank.unmatched_episodes=0.
    for j in range(21):bank[f'n{j}']=1.;bank[f'tp{j}']=1.
    groups=np.array([f'g{i}' for i in range(10)])
    cats=pd.DataFrame([dict(group_id=g,family=f,severity=v,onset='2020',effective=True)
                       for g in groups for f,v in audit.STRATA])
    draws=dict(kind='whole_group',groups=sorted(groups),indices=np.random.default_rng(20240601).integers(10,size=(2000,10)).tolist())
    ci,reps=audit.bounds(bank,groups,cats,draws)
    assert ci['bound_status']=='insufficient_bound_support' and ci['valid_replicates']==2000
    assert np.isnan(ci['recall_lcb'])
    ci,_=audit.bounds(bank,groups,cats.iloc[:1],draws)
    assert ci['bound_status']=='insufficient_design_support'


def test_independent_selection_both_folds_and_exact_tie():
    rows=[]
    for cid in ['b','a']:
        for fold in [0,1]:rows.append(dict(candidate_id=cid,inner_fold=fold,bound_status='supported',
            recall_lcb=.6,workload_ucb=1.,custom_synthetic_f1=.7,background_episodes_per_asset_day=.5,
            detected_delay_median_minutes=60.))
    surface=pd.DataFrame(rows);grid=[dict(candidate_id='b'),dict(candidate_id='a')]
    assert audit.selection(surface,grid)[0]['candidate_id']=='a'
    surface.loc[surface.inner_fold==1,'workload_ucb']=1.00001
    assert audit.selection(surface,grid)[0] is None
    assert audit.selection(surface,grid,True)[0]['candidate_id']=='a'
    surface.loc[surface.inner_fold==1,'bound_status']='insufficient_bound_support'
    assert audit.selection(surface,grid,True)[0] is None


def test_clean_interval_quality_winkler_in_target_units():
    frame=pd.DataFrame(dict(observed=[0.,3.],lower=[-1.,-1.],upper=[1.,1.],point=[0.,0.],available=True))
    q=audit.interval_quality(frame)
    assert q['empirical_coverage']==.5 and q['mpiw_kWh']==2 and q['winkler95_kWh']==42.
