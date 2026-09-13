"""No-fitting fresh support, group-safe sequences and joint execution evidence."""
import argparse, hashlib, json, os, subprocess, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SMART=ROOT/'smart_building_conformal'
REVIEW=Path(__file__).resolve().parent
sys.path.insert(0,str(SMART))
from src import matched_forecasting005 as R
from src.matched_models005 import forbid_fitting
from src.unit_checkpoint import digest,source_digest
import numpy as np
import pandas as pd
ENTRY='b26ee5b6a2cfb322b392e017e627bf3c96339c78'
KEYS=[('rico',5,2,42),('bdg2',1,2,42)]

def main(action):
 os.chdir(SMART)  # Dataset config paths are relative to the existing project.
 if action=='entry':
  excluded={'.gitattributes','PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md'}
  paths=subprocess.check_output(['git','ls-tree','-r','--name-only',ENTRY],cwd=ROOT).decode().splitlines()
  rows=[dict(path=p,bytes=(ROOT/p).stat().st_size,sha256=digest(ROOT/p)) for p in paths if p not in excluded]
  R.write_json(REVIEW/'entry_preservation.json',dict(entry_commit=ENTRY,files=rows),exclusive=True)
  print('Recorded preserved files',len(rows));return
 matrix=SMART/'outputs/amendment005/support_design_v1/experiment_matrix.csv'
 records=[];groups=[];sequences=[];units=[]
 history=pd.read_csv(SMART/'outputs/amendment005/study_plan_v1/rico_run_history.csv',keep_default_na=False).set_index('group_id')
 for key in KEYS:
  stem=f'{key[0]}_h{key[1]}_f{key[2]}_s{key[3]}_v2'
  p=SMART/'protocols/matched_forecasting005'/stem/'frozen_protocol.json'
  protocol=R.check_identity(p,matrix,key);data,roles=R.fresh_data(protocol)
  expected=(12932,4452,8692) if key[0]=='rico' else (51664,17370,34640)
  assert tuple(len(roles[n]) for n in ['fit','calibration','test'])==expected
  # All eligible windows, not just role samples: a single original series index
  # owns each entire 24-step input; no run/building can enter another's window.
  lazy=data['lazy']; idx=data['sequence_rows']
  assert (lazy.positions[idx]>=23).all() and lazy.valid[idx].all()
  mapping={}
  for group,part in data['meta'].groupby('group_id',dropna=False):
   serial=np.unique(lazy.series_index[idx[part.index]])
   assert len(serial)==1
   mapping[str(group)]=int(serial[0])
  assert len(set(mapping.values()))==len(mapping)
  for start in range(0,len(idx),256):
   rows=idx[start:start+256]; batch=lazy.take(rows)
   for j,row in enumerate(rows):
    pos=lazy.positions[row];serial=lazy.series_index[row]
    np.testing.assert_array_equal(batch[j],lazy.channels[serial][pos-23:pos+1])
  sequences.append(dict(dataset=key[0],horizon=key[1],eligible_sequences=len(idx),groups=len(mapping),sequence_length=24,all_windows_within_original_series=True))
  for name,rows in roles.items():
   meta=data['meta'].iloc[rows]
   if key[0]=='rico':
    for group in meta.group_id.unique():
     assert set(data['meta'].index[data['meta'].group_id.eq(group)])<=set(rows)
   records.append(dict(dataset=key[0],horizon=key[1],outer_fold=key[2],role=name,groups=meta.group_id.nunique(),**protocol['support']['roles'][name]))
   for group,part in meta.groupby('group_id'):
    row=dict(dataset=key[0],horizon=key[1],role=name,group_id=str(group),n=len(part),origin_min=str(part.origin_time.min()),origin_max=str(part.origin_time.max()),target_min=str(part.target_time.min()),target_max=str(part.target_time.max()))
    if key[0]=='rico':row.update(history.loc[group].to_dict())
    groups.append(row)
  assert [data['meta'].iloc[roles[r]].group_id.nunique() for r in ['fit','calibration','test']]==([61,21,41] if key[0]=='rico' else [10,10,10])
  frozen=pd.read_csv(p.parent/'membership.csv.gz',keep_default_na=False)
  for role,rows in roles.items():
   part=frozen[frozen.role.eq(role)]
   assert part.row_id.tolist()==data['meta'].iloc[rows].row_id.tolist()
   assert part.group_id.tolist()==data['meta'].iloc[rows].group_id.astype(str).tolist()
  ready=R.read_json(p.parent/'readiness.json');assert ready['first_unit_ready'] and ready['models_fitted']==0
  units.append(dict(key=list(key),protocol=p.relative_to(ROOT).as_posix(),protocol_hash=digest(p),source_hash=protocol['source_hash'],data_hash=protocol['support']['data_hash'],role_bank_hash=protocol['support']['role_bank_hash'],frequency=protocol['support']['frequency'],target=protocol['support']['target'],feature_names=protocol['support']['feature_names'],sequence_channels=protocol['support']['sequence_channels']))
 pd.DataFrame(records).to_csv(REVIEW/'fresh_role_support.csv',index=False)
 pd.DataFrame(groups).to_csv(REVIEW/'role_group_history.csv',index=False)
 pd.DataFrame(sequences).to_csv(REVIEW/'sequence_group_verification.csv',index=False)
 with zipfile.ZipFile(REVIEW/'evaluated_source.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for path in sorted((SMART/'src').rglob('*.py')):archive.writestr(path.relative_to(ROOT).as_posix(),path.read_bytes())
 manifest=dict(passed=True,models_fitted=0,entry_commit=ENTRY,
  authorizing_instruction_commit='d334f2b36144b58434725d81c7de20c9324954b8',authorizing_instruction_path='review/NEXT_TASK_MATCHED_RICO_BDG2.md',
  historical_runner_design_parent_commit=R.PARENT,historical_runner_design_instruction_commit=R.INSTRUCTION,
  authorization_hash=digest(SMART/'configs/matched_forecasting005_rico_bdg2_authorization.json'),
  source_hash=source_digest(),source_archive_hash=digest(REVIEW/'evaluated_source.zip'),units=units,
  both_frozen_before_either_fit=True,planned_real_tuning_fits=16,planned_real_final_fits=4,
  synthetic_fits_this_task=0,current_ram_policy_preserved=True,full_study_ready=False)
 R.write_json(REVIEW/'joint_pre_fit_manifest.json',manifest,exclusive=True)
 print(json.dumps(manifest,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['entry','verify']);args=parser.parse_args()
 with forbid_fitting():main(args.action)
