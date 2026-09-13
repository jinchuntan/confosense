"""Explicit SMOKE ONLY fixtures, never accepted as empirical operating results."""
import numpy as np
import pandas as pd
from .datasets.base import PreparedSeries, PreparedDataset, ChronologicalPartitioner, Provenance
from .operational004_design import STRATA, build_windows
from .operational004_stream import score_quantiles
from .unit_checkpoint import signature


def fixture_data(n=3600,groups=2,horizon=1):
    series=[];freq=pd.Timedelta('10min');t=pd.date_range('2022',periods=n,freq=freq)
    for g in range(groups):
        j=np.arange(n)
        y=23+g+np.sin(j/27)+.03*np.cos(j/4)+.0005*j
        frame=pd.DataFrame({'target':y},index=t)
        series.append(PreparedSeries('synthetic004','temperature',frame,freq,group_id=f'asset{g}',season_steps=None))
    prepared=PreparedDataset('synthetic004',series,ChronologicalPartitioner(),Provenance('synthetic004','SMOKE ONLY deterministic fixture'))
    cfg=dict(features={'target_lags':[0,1,3],'rolling_windows':[4]},
        alerts={'primary_horizon':horizon,'detection_tolerance_steps':6},horizons=[horizon],
        recalibration={'grid':{'update_every':[24,48,144],'window':[250,500,1000],'min_samples':50}})
    segmented,w,fcfg=build_windows(prepared,cfg,horizon)
    return prepared,segmented,w,cfg,fcfg


class DeterministicOwnedInterval:
    """Training-mean fixture with distinct quantile curves and own CQR scores."""
    def __init__(self,method,level,X_train,y_train,X_cal,y_cal,meta_cal,horizon,seed=42):
        if len(X_train)<400 or len(X_cal)<400:raise ValueError('fixture still enforces fitting minima')
        self.method,self.level,self.columns=method,float(level),list(X_train.columns)
        self.mean=float(np.mean(y_train));self.fitted_models=1
        self.identity=dict(estimator_class='smoke.DeterministicOwnedInterval',method=method,seed=seed,fixture=True,fallback=None)
        self.q=(0.,0.)
        raw=self.raw(X_cal)
        scores=np.maximum(raw['raw_lower']-y_cal,y_cal-raw['raw_upper']) if method=='cqr' else y_cal-raw['point']
        self.calibration=meta_cal[['group_id','target_time']].reset_index(drop=True).copy()
        self.calibration['score']=scores
        self.q=score_quantiles(scores,level,method)
        self.fit_identity=signature(dict(method=method,level=level,mean=self.mean,seed=seed,
            scores=np.asarray(scores).tolist(),calibration_ids=self.calibration.astype(str).to_dict('records')))

    def raw(self,X):
        if list(X.columns)!=self.columns:raise ValueError('fixture schema mismatch')
        point=.8*X.target_lag_0.to_numpy()+.2*self.mean
        lo=point-.2-.1*np.abs(X.hour_sin.to_numpy())
        hi=point+.35+.15*np.abs(X.hour_cos.to_numpy())
        if self.method in ('cqr','quantile_uncalibrated'):
            a,b=lo-self.q[0],hi+self.q[1]
        else:a,b=point+self.q[0],point+self.q[1]
        return dict(point=point,raw_lower=lo,raw_upper=hi,static_lower=np.minimum(a,b),static_upper=np.maximum(a,b))


def sufficient_bank(groups=20,*,perfect=False,workload_multiplier=1):
    """Synthetic count fixture for the real bootstrap/selection interface.

    This is deliberately NOT an exposure-generated scientific catalogue. Each
    original group has all strata so support and degenerate-bound paths can be
    tested without altering incidence or the scientific support thresholds.
    """
    records=[];events=[]
    for g in range(groups):
        for j,(family,severity) in enumerate(STRATA):
            time=pd.Timestamp('2021')+pd.Timedelta(hours=j)
            good=perfect or g not in (0,1)
            row=dict(row_id=f'g{g}_t{j}',group_id=f'g{g:02d}',origin_time=time-pd.Timedelta(hours=1),target_time=time,
                exposure_days=1/24,clean_episodes=float(j==0 and g in (0,9))*workload_multiplier,
                unmatched_episodes=float(j==0 and g in (0,9))*5,
                corrupted_episodes=5*float(good)+float(j==0 and g in (0,9))*5,time_in_alert_days=0.)
            for k in range(21):row[f'n{k}']=5. if j==k else 0.;row[f'tp{k}']=5. if j==k and good else 0.
            records.append(row)
            for seed in range(42,47):
                events.append(dict(event_id=f'g{g}_s{j}_e{seed}',group_id=row['group_id'],family=family,severity=severity,
                    onset=str(time),effective=True,placed=True,null=False,rejected=False,catalogue_seed=seed))
    bank=pd.DataFrame(records);all_events=pd.DataFrame(events)
    tables=[all_events[all_events.catalogue_seed.eq(seed)].reset_index(drop=True) for seed in range(42,47)]
    return bank,bank[['row_id','group_id','origin_time','target_time']].copy(),tables
