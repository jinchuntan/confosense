"""Preparation-only allocation audit; compare every horizon with the frozen pilot."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import pickle
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src import prepare_data, model_comparison_pilot as P
from src.pilot_resources import ResourceMeter, hardware, require_ram
from src.unit_checkpoint import source_digest

ap=argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--cache')
a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=False)
protocol=json.loads(Path('protocols/model_comparison_pilot_v1/frozen_protocol.json').read_text())
cfg=protocol['resolved_dataset_config']; stages=[]; frames=[]
launch=require_ram(3*2**30)

def wrap(name):
    original=getattr(prepare_data,name)
    def measured(*args,**kwargs):
        with ResourceMeter() as meter:
            result=original(*args,**kwargs)
        detail={}
        if isinstance(result,pd.DataFrame):
            detail=dict(rows=len(result),columns=list(result.columns),dataframe_bytes=int(result.memory_usage(deep=True).sum()))
        stages.append(dict(stage=name,**meter.result,**detail))
        return result
    setattr(prepare_data,name,measured)

for name in ['load_room_table','select_target','build_dataset']:wrap(name)
with ResourceMeter() as total:
    prepared=P.prepare(cfg)
    support=[]
    for h in protocol['config']['horizons']:
        with ResourceMeter() as meter:
            data=P.build_support(prepared,cfg,h,24)
            roles=P.pilot_roles(data['meta'],h,prepared.freq)
            P.verify_support(data,roles,protocol['horizons'][str(h)])
            for name,rows in roles.items():
                f=data['meta'].iloc[rows][['row_id','group_id','origin_time','target_time']].copy()
                f['role']=name;f['horizon']=h;frames.append(f)
            support.append(dict(horizon=h,data_hash=data['data_hash'],rows=len(data['meta']),roles=P.role_records(data['meta'],roles)))
        stages.append(dict(stage=f'common_support_h{h}',**meter.result))
        del data;gc.collect()
result=dict(models_fitted=0,launch_memory=launch,hardware=hardware(),source_hash=source_digest(),
            total_resources=total.result,stages=stages,support=support,
            prepared_frame_hash=hashlib.sha256(pd.util.hash_pandas_object(prepared.series[0].frame,index=True).values.tobytes()).hexdigest(),
            selection_audit_hash=hashlib.sha256(prepared.metadata['selection_audit'].to_csv(index=False).encode()).hexdigest(),
            selected_target=prepared.metadata['choice'])
(out/'preparation.json').write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')
pd.DataFrame(stages).to_csv(out/'stages.csv',index=False)
if a.cache:
    cache=Path(a.cache);cache.parent.mkdir(parents=True,exist_ok=True)
    with cache.open('xb') as f:pickle.dump(prepared,f)
print(json.dumps(dict(models_fitted=0,total=total.result,stages=[{k:v for k,v in r.items() if k!='columns'} for r in stages],support_matches_frozen=True),indent=2))
