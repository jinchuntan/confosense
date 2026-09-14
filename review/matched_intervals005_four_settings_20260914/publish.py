"""Seal a byte manifest, commit, and make a verified external backup."""
import argparse,csv,os,subprocess
from common import *

def index():
    base='../../smart_building_conformal/outputs/matched_intervals005/four_settings_f2_s42_v2_coordinator/analysis_v1/'
    lines=['# Remaining settings interval-method evidence index','', '[User authorization](USER_AUTHORIZATION.txt), [pinned handoff](AUTHORIZING_HANDOFF.md), [pre-fit test receipt](PRE_FIT_TEST_RECEIPT_V2.json), [pre-fit freeze](PRE_FIT_FREEZE.json), [durable progress](PROGRESS_AND_RESTART.md), [no-fit repair record](NO_FIT_REPAIR.md), and [current evidence](../CURRENT_EVIDENCE.md).','', '[Combined report](../../MATCHED_INTERVAL_METHODS_REMAINING_SETTINGS_REPORT.md), [panel response](PANEL_RESPONSE.md), and [delivery verification](COMPLETION_VERIFICATION.md).','', '## Frozen units, owner artifacts and checks','']
    for unit in UNITS:
        d='../../'+str(design(unit).relative_to(ROOT)).replace('\\','/')+'/';r='../../'+str(run(unit).relative_to(ROOT)).replace('\\','/')+'/';b='../../'+str(BATCH.relative_to(ROOT)).replace('\\','/')+'/'
        lines.append(f'- {unit["dataset"]}: [protocol]({d}frozen_protocol.json), [scope]({d}scope.csv), [readiness]({d}readiness.json), [owners and streams]({r}stages), [operation journal]({r}operations.jsonl), [validation]({b}{unit["name"]}_validation/validation.json), and [zero-fit resume]({b}{unit["name"]}_completed_resume.json).')
    lines += ['', '## Recomputable tables and figures','']
    for name,purpose in [('native_support_metrics.csv','100 native-support method rows'),('common_support_metrics.csv','100 matched joint-support method rows'),('all_seed42_common_support_metrics.csv','130-cell BDG2/PLEIA/RICO seed-42 descriptive table'),('per_building_metrics.csv','group-level contributions'),('background_workload.csv','clean-stream background workload'),('joint_support_and_availability.csv','membership, availability, and sampling support'),('seasonal_point_metrics.csv','six PLEIA daily-lag baseline point cells'),('seasonal_interval_metrics.csv','twelve PLEIA baseline interval cells'),('seasonal_applicability.csv','including four RICO no-daily-cycle markers'),('operations.csv','full nested operation ledger'),('fit_operation_counts.csv','170 new learned fits and calibrator counts'),('worker_costs.csv','all nine measured worker costs'),('validation_summary.csv','independent reconstruction and resume summary'),('interval_completion_overlay.csv','250/1950 completed-cell overlay'),('analysis_validation.json','aggregate no-fit acceptance')]:lines.append(f'- [{name}]({base}{name}): {purpose}.')
    lines += ['', f'Figures: [coverage PNG]({base}figures/remaining_settings_coverage.png), [MPIW PNG]({base}figures/remaining_settings_mpiw.png), and [Winkler PNG]({base}figures/remaining_settings_winkler.png); each has a source manifest and PDF version.', '', '[Exact byte manifest](EVIDENCE_MANIFEST.csv) covers this bounded-task evidence except itself.']
    atomic(REVIEW/'EVIDENCE_INDEX.md','\n'.join(lines)+'\n')

def main(label):
    if git('branch','--show-current')!=BRANCH:raise ValueError('wrong branch')
    if git('rev-parse','main')!='06fe967be2be8d7898812c0c2d6e464d4e942351':raise ValueError('main changed')
    index()
    paths=[REVIEW,BATCH,*[design(u) for u in UNITS],*[run(u) for u in UNITS],*[auth(u) for u in UNITS],SMART/'src/matched_intervals005.py',SMART/'src/intervals005_data.py',SMART/'src/intervals005_owners.py',SMART/'src/intervals005_stream.py',SMART/'src/intervals005_validate.py',SMART/'tests/test_matched_intervals005_remaining.py',ROOT/'MATCHED_INTERVAL_METHODS_REMAINING_SETTINGS_REPORT.md',ROOT/'review/CURRENT_EVIDENCE.md',ROOT/'PROJECT_RECOVERY_STATUS.md',ROOT/'MATCHED_METHOD_READINESS_MAP.md',ROOT/'.gitattributes',ROOT/'.gitignore']
    failed=SMART/'outputs/matched_intervals005/four_settings_f2_s42_v1_coordinator'
    if failed.exists():paths.append(failed)
    files=sorted(set(p for path in paths for p in (path.rglob('*') if path.is_dir() else [path]) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.tmp') and p.name!='EVIDENCE_MANIFEST.csv'))
    rows=[]
    for path in files:
        if path.stat().st_size>=100*2**20:raise ValueError('unexpected oversized evidence file: '+str(path))
        rows.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
    manifest=REVIEW/'EVIDENCE_MANIFEST.csv'
    with manifest.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(rows)
    BACKUP.mkdir(parents=True,exist_ok=True);stage=BACKUP/f'{label}_stage_paths.txt';atomic(stage,'\n'.join([r['path'] for r in rows]+[manifest.relative_to(ROOT).as_posix()])+'\n')
    subprocess.run(['git','add','--pathspec-from-file='+str(stage)],cwd=ROOT,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:subprocess.run(['git','commit','-m','Publish remaining interval settings: '+label],cwd=ROOT,check=True)
    commit=git('rev-parse','HEAD');bundle=BACKUP/f'{label}_{commit[:7]}.bundle';subprocess.run(['git','bundle','create',str(bundle),BRANCH,'^'+ENTRY],cwd=ROOT,check=True);subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    result=dict(commit=commit,branch=BRANCH,backup=str(bundle),backup_sha256=sha(bundle),main_unchanged=True,publication_status='pending',utc=now())
    atomic(BACKUP/f'{label}_{commit[:7]}_publication.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);main(parser.parse_args().label)
