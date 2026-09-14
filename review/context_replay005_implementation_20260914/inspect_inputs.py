import json,pickle,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SMART=ROOT/'smart_building_conformal'
sys.path.insert(0,str(SMART))
import pandas as pd
base=SMART/'outputs/amendment005/support_design_v1'
for name in ['pleia_energy_operational_membership_observations.csv.gz','pleia_energy_h1_forecast_membership.csv.gz','challenge_schedules.csv.gz']:
    f=pd.read_csv(base/name,nrows=2,keep_default_na=False);print(name, f.columns.tolist());print(f.to_string(index=False))
f=pd.read_csv(base/'proposal_roles.csv');print(f[(f.dataset=='pleia_energy')&(f.outer_fold==2)].to_string(index=False))
print(json.loads((base/'validation.json').read_text()).keys())
for ds in ['pleia_energy','rico']:
    p=Path('C:/Users/nigel/ConfoSenseBackups/amendment004_20260913/preflight_v1')/(ds+'_prepared.pkl')
    with p.open('rb') as file:c=pickle.load(file)
    print(ds, list(c),c['fcfg'],c['w']['X'].columns.tolist(),c['w']['meta'].head(1).to_dict('records'))
    print('segment',c['segmented'].series[0].frame.head(2).to_string(),c['segmented'].series[0].season_steps)
    print('cfg',json.dumps(c['cfg'],default=str))
