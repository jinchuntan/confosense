import json, pickle, sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'smart_building_conformal'))
BASE=ROOT/'smart_building_conformal/outputs/amendment004/preflight_20260913_v1'
summary=json.loads((BASE/'summary.json').read_text())
for d in summary['datasets']:
 c=d['resolved_dataset_config']
 print(json.dumps(dict(dataset=d['dataset'],horizon=d['horizon'],freq=d['freq'],raw=d['original_prepared_rows'],eligible=d['eligible_rows'],groups=d['groups'],horizons=c['horizons'],target=c.get('target'),adapter=c.get('adapter'),season=c.get('season_steps'),data_hash=d['data_hash'])))
print(pd.read_csv(BASE/'event_support.csv').to_string(index=False))
print(pd.read_csv(BASE/'catalogue_summary.csv').groupby(['dataset','outer_fold','role'])[['requested','placed','effective','null','rejected']].sum().to_string())
for ds in ['pleia','pleia_energy','rico']:
 p=Path('C:/Users/nigel/ConfoSenseBackups/amendment004_20260913/preflight_v1')/(ds+'_prepared.pkl')
 with p.open('rb') as f: c=pickle.load(f)
 print(ds,'CACHE',list(c),'SERIES',len(c['prepared'].series),'FREQ',c['prepared'].freq,'SERIES_METADATA',c['prepared'].series[0].__dict__.keys())
 print('first series', {k:v for k,v in c['prepared'].series[0].__dict__.items() if k!='frame'})
 print('meta columns',list(c['w']['meta']), 'datahash',c['w']['data_hash'])
 print('prepared metadata', {k:v for k,v in c['prepared'].__dict__.items() if k not in ('series','partitioner')})
