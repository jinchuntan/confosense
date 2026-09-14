"""Shared fitted quantile owner; each C control has an immutable score contract."""
import numpy as np
import pandas as pd
from .operational004_stream import score_quantiles
from .intervals005_owners import quantile_raw
from .unit_checkpoint import signature
from .context005_features import feature_hash

class ContextOwner:
    def __init__(self,owner,method,Xcal,ycal,metacal,identity):
        self.owner=owner;self.method=method;self.level=.95;self.columns=list(Xcal.columns)
        self.radius=0.;self.identity=dict(identity,method=method,static_convention='native asymmetric CQR tails' if method=='cqr' else method)
        self.fit_identity=signature(dict(owner=identity,method=method,columns=self.columns))
        raw=self.raw(Xcal);y=np.asarray(ycal,float)
        score=np.maximum(raw['raw_lower']-y,y-raw['raw_upper']) if method!='persistence_split' else np.abs(y-raw['point'])
        if method=='persistence_split':self.radius=score_quantiles(score,.95,'cqr')[0]
        self.calibration=metacal[['group_id','target_time']].reset_index(drop=True).copy();self.calibration['score']=score

    def raw(self,X):
        if list(X.columns)!=self.columns:raise ValueError('owner feature schema differs')
        if self.method=='persistence_split':
            p=X.target_lag_0.to_numpy(float)
            return dict(point=p,raw_lower=p,raw_upper=p,static_lower=p-self.radius,static_upper=p+self.radius)
        result=quantile_raw(self.owner,X.to_numpy());_,bounds=self.owner.predict_interval(X.to_numpy())
        a,b=bounds[:,0,0],bounds[:,1,0]
        return dict(result,static_lower=np.minimum(a,b),static_upper=np.maximum(a,b))

def prediction_cache(model,X,variant_identity):
    return dict(feature_hash=feature_hash(X),fit_identity=model.fit_identity,variant_identity=variant_identity,values=model.raw(X))
