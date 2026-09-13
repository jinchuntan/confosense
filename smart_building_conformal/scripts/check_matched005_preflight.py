"""No fitting: all published roles, historical pilot compatibility and preservation."""
import argparse,json,subprocess,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.matched_data005 import forecast_roles
from src.pilot_data import role_records
from src.matched_models005 import forbid_fitting
from src.unit_checkpoint import digest,signature
from src.validate_model_comparison_pilot import validate as old_validate

def main(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=False)
 matrix=pd.read_csv(ROOT/'outputs/amendment005/support_design_v1/experiment_matrix.csv')
 checked=[]
 for (ds,h),part in matrix.groupby(['dataset','horizon']):
  m=pd.read_csv(ROOT/f'outputs/amendment005/support_design_v1/{ds}_h{h}_forecast_membership.csv.gz',keep_default_na=False)
  m.origin_time=pd.to_datetime(m.origin_time);m.target_time=pd.to_datetime(m.target_time)
  freq=pd.Timedelta(minutes={'pleia':10,'pleia_energy':10,'rico':1,'bdg2':60}[ds])
  for fold in range(3):
   roles=forecast_roles(m,int(h),freq,fold,ds=='rico');record=role_records(m,roles)
   expected=part[part.outer_fold==fold].role_bank_hash.unique();assert len(expected)==1 and signature(record)==expected[0]
   differing_orders=[]
   for role,rows in roles.items():
    chosen=m[m[f'fold{fold}_roles'].str.split('|').apply(lambda r:role in r)]
    actual=m.iloc[rows].row_id.tolist();exported=chosen.row_id.tolist()
    assert len(actual)==len(exported) and set(actual)==set(exported)
    if actual!=exported:differing_orders.append(role)
   if differing_orders:print(json.dumps(dict(dataset=ds,horizon=int(h),outer_fold=fold,export_order_differs=differing_orders,sets_identical=True,ordered_role_hashes_match=True)),flush=True)
   checked.append(dict(dataset=ds,horizon=int(h),outer_fold=fold,role_bank_hash=signature(record),roles=7,
                       exported_source_order_differs_for='|'.join(differing_orders),ordered_role_hashes_match=True,passed=True,models_fitted=0))
 pd.DataFrame(checked).to_csv(out/'published_role_compatibility.csv',index=False)
 old_run=ROOT/'outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913'
 protocol=ROOT/'protocols/model_comparison_pilot_v1/frozen_protocol.json'
 old=old_validate(old_run,protocol)
 (out/'historical_pilot_validation.json').write_text(json.dumps(old,indent=2)+'\n')
 reuse=[]
 for h in [1,3,6]:
  rows=matrix[(matrix.dataset=='pleia')&(matrix.horizon==h)&(matrix.outer_fold==0)&(matrix.model_seed==42)&matrix.model.isin(['persistence','xgboost','attention_lstm'])]
  assert len(rows)==6 and rows.status.eq('completed_reusable').all()
  reuse.append(dict(dataset='pleia',horizon=h,outer_fold=0,model_seed=42,point_cells=3,interval_cells=6,
                    old_source_hash=old['source_hash'],old_protocol_hash=old['protocol_hash'],
                    current_role_bank_hash=rows.role_bank_hash.iloc[0],models_refitted=0,
                    compatibility='read-only historical validator and exact new-role equality; old source identity retained'))
 pd.DataFrame(reuse).to_csv(out/'historical_pilot_reuse.csv',index=False)
 repo=ROOT.parent;files=[]
 for name in subprocess.check_output(['git','ls-tree','-r','--name-only','f1a71a19b4e227a9894a8e2c74686a642dca962a'],cwd=repo).decode().splitlines():
  if name in ['.gitattributes','PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']:continue
  path=repo/name
  if path.is_file():files.append(dict(path=name,bytes=path.stat().st_size,sha256=digest(path)))
 (out/'entry_preservation.json').write_text(json.dumps(dict(entry_commit='f1a71a19b4e227a9894a8e2c74686a642dca962a',files=files),indent=2)+'\n')
 result=dict(passed=True,models_fitted=0,published_role_banks=len(checked),published_roles=7*len(checked),
             grouped_rico_role_banks=12,historical_pilot_point_cells=9,historical_pilot_interval_cells=18,
             historical_pilot_learned_refits=0,preserved_files_recorded=len(files),full_study_ready=False)
 (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
 with forbid_fitting():main(a.out)
