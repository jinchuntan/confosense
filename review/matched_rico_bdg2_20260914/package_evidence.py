"""Verify preserved history and package the completed two-unit review. No fitting."""
import csv,hashlib,json,re,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SMART=ROOT/'smart_building_conformal';REVIEW=Path(__file__).resolve().parent
BASE=SMART/'outputs/matched_forecasting005';OUT=BASE/'rico_bdg2_report_v2';CHECKS=BASE/'rico_bdg2_validation_v1'
ENTRY='b26ee5b6a2cfb322b392e017e627bf3c96339c78';PREFIT='350ef4fd1c92c12a982df2b8366023937515b65b'
MAIN='06fe967be2be8d7898812c0c2d6e464d4e942351';SOURCE='cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e'
sys.path.insert(0,str(SMART))
from src.unit_checkpoint import UnitCheckpoint,digest,source_digest
from src.matched_models005 import forbid_fitting
import pandas as pd

def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf-8').strip()
def ledger(paths):return [dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(set(paths))]
def write_csv(path,rows):
 with path.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
 assert git('branch','--show-current')=='review/matched-rico-bdg2-20260914'
 assert git('rev-parse','main')==git('rev-parse','origin/main')==MAIN
 assert git('rev-parse','review/matched-energy-h1-20260913')==ENTRY
 subprocess.run(['git','merge-base','--is-ancestor',PREFIT,'HEAD'],cwd=ROOT,check=True)
 assert source_digest()==SOURCE
 preserved=load(REVIEW/'entry_preservation.json');changed='smart_building_conformal/src/matched_models005.py'
 for row in preserved['files']:
  if row['path']==changed:continue
  assert digest(ROOT/row['path'])==row['sha256'],row['path']
 assert digest(REVIEW/'evaluated_source.zip')==load(REVIEW/'joint_pre_fit_manifest.json')['source_archive_hash']
 with zipfile.ZipFile(REVIEW/'evaluated_source.zip') as z:
  names=sorted(z.namelist());raw='\n'.join(f"{n.split('/src/',1)[1]}:{hashlib.sha256(z.read(n)).hexdigest()}" for n in names)
  assert hashlib.sha256(raw.encode()).hexdigest()==SOURCE
  for n in names:assert z.read(n)==(ROOT/n).read_bytes()
 # Bind the one intentional source change separately from immutable history.
 diff=subprocess.check_output(['git','diff',ENTRY,'--',changed],cwd=ROOT)
 (REVIEW/'guard_repair.diff').write_bytes(diff)
 statuses=['PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']
 marker='<!-- matched-rico-bdg2-20260914: historical content -->'
 for name in statuses:
  old=subprocess.check_output(['git','show',ENTRY+':'+name],cwd=ROOT).decode('utf-8')
  assert (ROOT/name).read_text(encoding='utf-8').split(marker,1)[1].strip()==old.strip()
  assert (ROOT/name).read_bytes().endswith(old.encode('utf-8'))
 analysis=load(OUT/'analysis_validation.json');assert analysis['passed'] and analysis['models_fitted']==0
 assert analysis['summary']['completed_paired_units']==6 and analysis['summary']['remaining_paired_units']==189
 run_records=[]
 for ds,h in [('rico',5),('bdg2',1)]:
  s=f'{ds}_h{h}_f2_s42_v2';run=BASE/s
  cp=UnitCheckpoint(run,load(run/'checkpoint_manifest.json')['spec'],resume=True)
  for m in ['persistence','xgboost','attention_lstm']:assert cp.verify(f'{ds}_h{h}_f2_s42_{m}')
  env=load(run/'execution_environment.json');assert env['code_commit']==PREFIT and env['source_hash']==SOURCE
  audit=load(BASE/(s+'_audit')/'validation.json');resume=load(CHECKS/(s+'_resume.json'));log=load(str(run)+'.log.json')
  assert audit['passed'] and audit['models_fitted']==0 and audit['all_run_files_unchanged']
  assert audit['point_cells']==3 and audit['interval_cells']==6 and audit['saved_model_prediction_checks']==6
  assert audit['real_tuning_fits_verified']==8 and audit['real_final_fits_verified']==2
  assert resume['models_fitted']==0 and resume['all_run_files_unchanged'] and resume['reused_model_units']==3
  assert log['exit_status']==0
  reloads=pd.read_csv(BASE/(s+'_audit')/'saved_model_verification.csv');assert len(reloads)==6 and reloads.verified.all()
  run_records.append(dict(dataset=ds,horizon=h,fold=2,seed=42,actual_exit=log['exit_status'],seconds=log['seconds'],point_cells=3,interval_cells=6,tuning_fits=8,final_fits=2,reload_checks=6,max_absolute_prediction_difference=float(reloads.max_absolute_difference.max()),zero_fit_resume=True))
 # Verify frozen input bytes remain exact under both active protocols.
 for u in load(REVIEW/'joint_pre_fit_manifest.json')['units']:
  p=ROOT/u['protocol'];assert digest(p)==u['protocol_hash'];protocol=load(p)
  for rel,expected in protocol['input_hashes'].items():assert digest(SMART/rel)==expected
  for filename,key in [('membership.csv.gz','membership_hash'),('boundaries.csv','boundaries_hash')]:assert digest(p.parent/filename)==protocol[key]
 scripts=list(REVIEW.glob('*.py'))+[SMART/'tests/test_matched005_partition_guard.py']
 rows=ledger(scripts)
 with zipfile.ZipFile(REVIEW/'review_helpers.zip','w',zipfile.ZIP_DEFLATED) as z:
  for row in rows:z.writestr(row['path'],(ROOT/row['path']).read_bytes())
 write_csv(REVIEW/'review_helpers_manifest.csv',rows)
 roots=[ROOT/n for n in statuses+['.gitattributes','RICO_BDG2_MATCHED_FIRST_UNITS_REPORT.md','MATCHED_NEXT_BATCH_PROPOSAL.md',changed]]
 roots += [SMART/'tests/test_matched005_partition_guard.py',SMART/'configs/matched_forecasting005_rico_bdg2_authorization.json']
 dirs=[REVIEW,OUT,CHECKS,BASE/'rico_bdg2_report_v1']  # Preserve the failed reporting attempt.
 for ds,h in [('rico',5),('bdg2',1)]:
  s=f'{ds}_h{h}_f2_s42_v2'
  dirs += [BASE/s,BASE/(s+'_audit')]
  roots += [BASE/(s+suffix) for suffix in ['.log','.log.json','.log.started.json','.process.json']]
  for version in ['v1','v2']:dirs.append(SMART/f'protocols/matched_forecasting005/{ds}_h{h}_f2_s42_{version}')
 for directory in dirs:roots += [p for p in directory.rglob('*') if p.is_file()]
 excluded={'EVIDENCE_MANIFEST.csv','publication_validation.json'}
 paths=sorted(set(p for p in roots if not(p.parent==REVIEW and p.name in excluded)))
 assert all(p.stat().st_size<100*2**20 and p.suffix not in ['.pyc','.pkl','.hdf'] for p in paths)
 links=0
 # Handoff text is a verbatim historical document; validate new document links.
 for p in [p for p in paths if p.suffix=='.md' and p.name!='AUTHORIZING_HANDOFF.md']:
  text=p.read_text(encoding='utf-8').split(marker)[0]
  for target in re.findall(r'\]\(([^)]+)\)',text):
   if '://' in target or target.startswith('#'):continue
   dest=(p.parent/target.split('#')[0]).resolve()
   assert dest.exists() or dest.parent==REVIEW and dest.name in excluded,(p,target)
   links+=1
 manifest=ledger(paths);write_csv(REVIEW/'EVIDENCE_MANIFEST.csv',manifest)
 commands=pd.read_csv(OUT/'command_measurements.csv',keep_default_na=False);failed=commands[commands.exit_status!=0]
 assert len(failed)==2,failed[['log','exit_status']]
 reporting=load(REVIEW/'reporting_attempts.json')
 assert [r['actual_exit'] for r in reporting]==[1,0] and all(r['models_fitted']==0 for r in reporting)
 assert digest(REVIEW/'failed_analysis_v1_source.txt')==reporting[0]['source_sha256']
 assert digest(REVIEW/'analyze.py')==reporting[1]['source_sha256']
 result=dict(passed=True,packaging_fits=0,entry_commit=ENTRY,evaluated_commit=PREFIT,source_hash=SOURCE,
  branch=git('branch','--show-current'),main_commit=MAIN,historical_files_unchanged=len(preserved['files'])-1,
  intentional_source_repair=changed,historical_results_invalidated=False,historical_status_documents_preserved=statuses,
  units=run_records,total_real_tuning_fits=16,total_real_final_fits=4,tiny_fits=0,
  no_fit_regression_checks=15,failed_attempts_preserved=failed[['log','exit_status','seconds']].to_dict('records'),
  reporting_attempt_exits=[r['actual_exit'] for r in reporting],reporting_failures_do_not_invalidate_models=True,
  local_links_checked=links,manifest_files=len(manifest),manifest_bytes=sum(r['bytes'] for r in manifest),max_file_bytes=max(r['bytes'] for r in manifest),
  manifest_sha256=digest(REVIEW/'EVIDENCE_MANIFEST.csv'),manifest_excludes=sorted(excluded),
  full_study_ready=False,proposed_batch_launched=False,review_artifacts_ready=True,
  remote_verification='performed after final commit; external receipt and delivery')
 (REVIEW/'publication_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':
 with forbid_fitting():main()
