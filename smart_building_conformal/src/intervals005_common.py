"""Durable stages, operation accounting and identities for matched intervals005."""
from __future__ import annotations
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import pickle
import shutil
import sys
import time
import uuid

import numpy as np
import pandas as pd

from .matched_models005 import PhaseMeter
from .pilot_resources import memory_snapshot
from .unit_checkpoint import digest, signature, source_digest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
METHODS = ['quantile_uncalibrated','cqr','recentred_enbpi_static','recentred_enbpi_updated','dscp']
LEVELS = [.9,.95]
ENTRY = 'c143fa16eaf9bfc6354b4cb1f8861915cb00f388'
OLD_SOURCE = 'cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e'


def now(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def tree(path): return {p.relative_to(path).as_posix():digest(p) for p in sorted(Path(path).rglob('*')) if p.is_file()}
def frame(path): return pd.read_csv(path,float_precision='round_trip',converters={'row_id':str,'group_id':str,'segment_id':str})
def packages(): return {n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','mapie','xgboost','torch']}
def append(path,value):
    if path is None:return
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as f:
        f.write(json.dumps(value,default=str)+'\n');f.flush();os.fsync(f.fileno())


def replace_retry(source,target,journal=None):
    delays=(.02,.05,.1,.2,.5,1,1,1,2,2)
    for attempt in range(len(delays)+1):
        try:os.replace(source,target);return
        except PermissionError as exc:
            append(journal,dict(utc=now(),event='atomic_rename_denial',source=str(source),target=str(target),attempt=attempt,error=str(exc)))
            if attempt==len(delays):raise
            time.sleep(delays[attempt])


def atomic(path,value,journal=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    with temp.open('w',encoding='utf-8',newline='\n') as f:
        f.write(value if isinstance(value,str) else json.dumps(value,indent=2,default=str)+'\n')
        f.flush();os.fsync(f.fileno())
    replace_retry(temp,path,journal)


def csv(path,data):
    path=Path(path)
    data.to_csv(path,index=False,compression={'method':'gzip','mtime':0} if path.suffix=='.gz' else None)


def resources(path):
    r=memory_snapshot();r['free_disk_bytes']=shutil.disk_usage(path).free
    r['launch_ram_reference_bytes']=3*2**30;r['launch_ram_reference_met']=r['available_ram_bytes']>=3*2**30
    r['launch_ram_reference_nonblocking']=True
    if r['free_disk_bytes']<8*2**30:raise OSError('below unchanged 8 GiB free-disk floor')
    return r


class Operations:
    """Count executed wrappers, base learners and calibrators, not labels.

    A MAPIE EnbPI conformalize call may fit bootstrap learners. Every nested
    learner call is recorded with its real row count and requested parameters.
    A forbidden context rejects calibrators as well as learned estimators.
    """
    def __init__(self,path=None,*,stage='',synthetic=False,forbid=False):
        self.path=path;self.stage=stage;self.synthetic=synthetic;self.forbid=forbid
        self.rows=[];self.live={}

    def __enter__(self):
        self.previous=sys.getprofile()
        def profile(f,event,arg):
            if event not in ('call','return'):return
            name=f.f_code.co_name;module=f.f_globals.get('__name__','');obj=f.f_locals.get('self')
            cls=type(obj).__name__ if obj is not None else ''
            kind=None
            if name=='fit' and cls=='HistGradientBoostingRegressor':kind='quantile_estimator_fit'
            elif name=='fit' and cls=='XGBRegressor':kind='xgboost_estimator_fit'
            elif name=='fit' and cls=='RandomForestRegressor':kind='random_forest_estimator_fit'
            elif name=='fit' and cls=='KMeans':kind='kmeans_candidate_fit'
            elif name=='fit' and cls=='ConformalizedQuantileRegressor':kind='cqr_wrapper_fit'
            elif name=='fit' and cls=='TimeSeriesRegressor':kind='enbpi_wrapper_fit'
            elif name=='conformalize' and cls in ('ConformalizedQuantileRegressor','TimeSeriesRegressor','_MapieQuantileRegressor'):kind='calibrator_conformalize'
            elif name=='fit_dscp' and module=='src.conformal_dscp':kind='dscp_calibrator_fit'
            if kind is None:
                # Also forbid unfamiliar learned/calibration routes.
                if self.forbid and event=='call' and name in ('fit','partial_fit','fit_predict','fit_transform','conformalize','fit_dscp') and module.startswith(('src.','sklearn.','mapie.','xgboost.')):
                    if cls!='GroupPartitioner':raise AssertionError('fitting/calibration forbidden: '+module+'.'+name)
                return
            if event=='call':
                if self.forbid:raise AssertionError('fitting/calibration forbidden: '+kind)
                operation=uuid.uuid4().hex;X=f.f_locals.get('X',f.f_locals.get('X_train',f.f_locals.get('X_conformalize',f.f_locals.get('calib_predictions'))))
                y=f.f_locals.get('y',f.f_locals.get('y_train',f.f_locals.get('y_conformalize',f.f_locals.get('calib_truth'))))
                r=dict(operation_id=operation,stage=self.stage,synthetic=self.synthetic,kind=kind,module=module,call=name,estimator_class=cls,pid=os.getpid(),utc=now(),n_rows=len(X) if X is not None else None,parameters=obj.get_params(deep=False) if hasattr(obj,'get_params') else {},target_hash=hashlib.sha256(np.asarray(y).tobytes()).hexdigest() if y is not None else None)
                self.live[id(f)]=(r,time.perf_counter(),time.process_time());append(self.path,dict(r,event='started'))
            elif id(f) in self.live:
                r,wall,cpu=self.live.pop(id(f));r.update(wall_seconds=time.perf_counter()-wall,process_cpu_seconds=time.process_time()-cpu,event='returned',return_is_none=arg is None)
                self.rows.append(r);append(self.path,r)
        sys.setprofile(profile)
        return self

    def __exit__(self,*exc):
        sys.setprofile(self.previous)
        if exc[0] is not None:append(self.path,dict(event='operation_context_failed',stage=self.stage,utc=now(),error=str(exc[1]),synthetic=self.synthetic))


class Stages:
    """Content-verified stages; preserve ready partials after rename failure."""
    def __init__(self,root,spec,*,resume=False):
        self.root=Path(root);self.identity=signature(spec);self.journal=self.root/'stage_journal.jsonl'
        manifest=self.root/'checkpoint_manifest.json'
        if manifest.exists():
            if not resume:raise ValueError('existing execution requires explicit resume')
            if read(manifest)['identity']!=self.identity:raise ValueError('checkpoint source/protocol identity mismatch')
        else:
            if self.root.exists() and any(self.root.iterdir()):raise ValueError('unrecognized nonempty output directory')
            atomic(manifest,dict(identity=self.identity,spec=spec))
        (self.root/'stages').mkdir(exist_ok=True)

    def verify_path(self,path,key):
        marker=path/'COMPLETE.json'
        if not marker.exists():raise ValueError('incomplete committed stage: '+key)
        record=read(marker)
        if record['identity']!=self.identity or record['key']!=key:raise ValueError('stage identity mismatch')
        actual=tree(path);actual.pop('COMPLETE.json')
        if actual!=record['files']:raise ValueError('corrupt stage: '+key)
        return record

    def get(self,key):
        if not key.replace('_','').isalnum():raise ValueError('invalid stage key')
        path=self.root/'stages'/key
        if path.exists():self.verify_path(path,key);return path
        partials=list(self.root.glob('.partial_'+key+'_*'))
        ready=[p for p in partials if (p/'COMPLETE.json').exists()]
        if len(ready)>1:raise ValueError('ambiguous recoverable stage')
        if ready:
            self.verify_path(ready[0],key);replace_retry(ready[0],path,self.journal)
            append(self.journal,dict(event='recovered_ready_stage',key=key,utc=now()));return path
        if partials and (key.startswith(('owner_fit_','owner_cal_')) or key=='dscp_fit'):
            raise ValueError('interrupted fit/calibrator stage requires evidence reconciliation; refusing automatic refit: '+key)
        return None

    def run(self,key,fn,*,forbid=False):
        path=self.get(key)
        if path is not None:return path
        if forbid:raise AssertionError('incomplete stage on completed forbidden-fit resume: '+key)
        partial=self.root/('.partial_'+key+'_'+uuid.uuid4().hex);partial.mkdir()
        append(self.journal,dict(event='started',key=key,pid=os.getpid(),utc=now(),partial=str(partial)))
        with PhaseMeter() as meter:
            payload=fn(partial) or {}
        atomic(partial/'stage.json',dict(key=key,payload=payload,resources=meter.result))
        atomic(partial/'COMPLETE.json',dict(identity=self.identity,key=key,files=tree(partial)))
        path=self.root/'stages'/key;replace_retry(partial,path,self.journal)
        append(self.journal,dict(event='complete',key=key,utc=now(),resources=meter.result))
        return path


def dump_owner(path,owner):
    with Path(path).open('wb') as f:pickle.dump(owner,f,protocol=5);f.flush();os.fsync(f.fileno())


def load_owner(path):
    # Only called after the containing content-verified stage passes.
    with Path(path).open('rb') as f:return pickle.load(f)
