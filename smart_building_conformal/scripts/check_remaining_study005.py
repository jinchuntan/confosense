"""No-fit verification and dry-run inspection; this command cannot launch fits."""
import argparse,json,math,sys
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from support_design005 import ROOT,BASE,STRATA,allocation_counts,digest,no_fitting

def check(base,plan,out):
 base,plan,out=map(Path,[base,plan,out]);out.mkdir(parents=True,exist_ok=False)
 banks=pd.read_csv(base/'current_banks.csv');strata=pd.read_csv(base/'current_strata.csv');corrections=[]
 for i,b in banks.iterrows():
  tables=[pd.read_csv(BASE/f'{b.dataset}_f{b.outer_fold}_{b.role}_e{s}_catalogue.csv.gz',keep_default_na=False) for s in range(42,47)]
  events=pd.concat(tables,ignore_index=True);eff=events[events.effective.astype(bool)]
  groups=eff.group_id.nunique()
  if groups!=b.faulted_original_groups:
   assert b.dataset in ['pleia','pleia_energy'] and b.faulted_original_groups==0 and groups==1
   corrections.append(dict(dataset=b.dataset,outer_fold=int(b.outer_fold),role=b.role,column='faulted_original_groups',before=0,after=1,
    reason='literal group ID None was parsed as NA by default pandas reader; preserve literal identifier'))
   banks.loc[i,'faulted_original_groups']=groups
  assert len(events)==b.requested and len(eff)==b.effective_events
  assert events.placed.sum()==b.placed and events.null.sum()==b['null'] and events.rejected.sum()==b.rejected
  for j,(f,v) in enumerate(STRATA):
   selected=events[(events.family==f)&(events.severity==v)];effective=selected[selected.effective.astype(bool)]
   s=strata[(strata.dataset==b.dataset)&(strata.outer_fold==b.outer_fold)&(strata.role==b.role)&(strata.family==f)&(strata.severity==v)].iloc[0]
   distinct=len(effective[['group_id','onset']].drop_duplicates())
   assert len(selected)==s.requested and len(effective)==s.effective and distinct==s.distinct_onsets
   assert len(selected)==allocation_counts(int(b.requested_per_catalogue),range(5))[j]
 banks.to_csv(out/'current_banks_verified.csv',index=False)
 pd.DataFrame(corrections).to_csv(out/'identifier_corrections.csv',index=False)
 matrix=pd.read_csv(base/'experiment_matrix.csv');q=pd.read_csv(plan/'forecast_execution_queue.csv')
 units=matrix[matrix.model=='xgboost'].drop_duplicates(['dataset','horizon','outer_fold','model_seed'])
 required=units[units.status=='required_new'];keys=['dataset','horizon','outer_fold','model_seed']
 assert set(map(tuple,q[keys].to_numpy()))==set(map(tuple,required[keys].to_numpy())) and len(q)==len(required)==192
 seasonal=pd.read_csv(plan/'seasonal_execution_queue.csv')
 assert len(seasonal)*5==len(matrix[(matrix.model=='seasonal_naive')&(matrix.status=='required_new')])//2==135
 methods=pd.read_csv(plan/'interval_method_matrix.csv');assert len(methods)==1950 and not methods.duplicated(keys+['method','level']).any()
 scope=pd.read_csv(plan/'scope_ledger.csv');scope.loc[scope.scope=='seasonal','exact_status']=scope.loc[scope.scope=='seasonal','exact_status'].str.replace('45 unique deterministic runs','27 unique deterministic runs',regex=False)
 scope.to_csv(out/'scope_ledger_verified.csv',index=False)
 first=json.loads(q.iloc[0].argv);assert first[3]=='src.matched_forecasting005'
 assert not (ROOT/'src/matched_forecasting005.py').exists()
 nextunit=json.loads((plan/'next_forecast_unit.json').read_text())
 assert nextunit['expected_point_cells']==3 and nextunit['expected_interval_cells']==6 and nextunit['tuning_fits']+nextunit['final_learned_fits']==10
 # Calculate necessary exposure; count-only lower bound, not a power guarantee.
 inv=pd.read_csv(base/'inventory.csv');r=inv[inv.dataset=='rico'].iloc[0]
 assert r.eligible_rows==45747 and r.original_rows==49680 and r.groups==207
 extra=math.ceil((41*1440-r.eligible_rows)/221)
 result=dict(passed=True,models_fitted=0,current_banks_recalculated=len(banks),current_strata_recalculated=len(strata),
  identifier_count_corrections=len(corrections),original_generator_source_hash=json.loads((base/'validation.json').read_text())['script_hash'],
  corrected_generator_source_hash=digest(ROOT/'scripts/support_design005.py'),
  remaining_paired_units=len(q),remaining_learned_fits=int(q.learned_fit_invocations.sum()),seasonal_unique_runs=len(seasonal),
  rico_additional_221minute_runs_count_lower_bound=extra,
  next_command=first,command_exists=False,execution_blocker='implement matched_forecasting005 entrypoint and obtain next-unit fitting authorization',
  full_study_ready=False,publication_ready=False)
 (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--plan',required=True);p.add_argument('--out',required=True);p.add_argument('--dry-run',action='store_true',required=True);a=p.parse_args()
 with no_fitting():check(a.base,a.plan,a.out)
