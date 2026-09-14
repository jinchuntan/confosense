"""Build the evidence index, exact manifest, commit and external backup."""
import argparse,csv,hashlib,os,subprocess
from common import *

def evidence_index():
    a='../../smart_building_conformal/outputs/matched_intervals005/bdg2_fold2_multiseed_v2_coordinator/analysis_v1/'
    lines=['# BDG2 interval-method multiseed evidence index','', '[Authorization](USER_AUTHORIZATION.txt), [pinned handoff identity](AUTHORIZING_HANDOFF.md), [evaluated source identity](evaluated_source.json), [source archive](evaluated_source.zip), [pre-fit tests](PRE_FIT_TESTS.md), [freeze receipt](PRE_FIT_FREEZE.json), [durable command receipts](command_receipts/README.md), and [durable progress](PROGRESS_AND_RESTART.md).','', '[Five-seed report](../../BDG2_MATCHED_INTERVAL_METHODS_MULTISEED_REPORT.md), [seed-42 pilot report](../../BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md), [panel response](PANEL_RESPONSE.md), and [current evidence](../CURRENT_EVIDENCE.md).','','## Protocols, runs and validation','']
    for seed in SEEDS:
        d=f'../../smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s{seed}_v2/'
        r=f'../../smart_building_conformal/outputs/matched_intervals005/bdg2_f2_s{seed}_v2/'
        b=f'../../smart_building_conformal/outputs/matched_intervals005/bdg2_fold2_multiseed_v2_coordinator/'
        lines.append(f'- Seed {seed}: [protocol]({d}frozen_protocol.json), [scope]({d}scope.csv), [readiness]({d}readiness.json), [fitted owners and streams]({r}stages), [operation journal]({r}operations.jsonl), [independent validation]({b}seed{seed}_validation/validation.json), [zero-fit resume]({b}seed{seed}_completed_resume.json).')
    lines += ['', '## Combined recomputable tables','']
    purposes=[('native_support_metrics.csv','150 native-support cells'),('common_support_metrics.csv','150 common-support views'),('five_seed_summary.csv','mean, sample standard deviation and range by method/horizon/level'),('per_building_metrics.csv','original-building contributions'),('shared_owner_contrasts.csv','per-seed CQR/raw and updated/static contrasts'),('shared_owner_contrast_summary.csv','five-seed contrast summaries'),('background_workload.csv','all per-seed clean-stream exposure and episodes'),('background_workload_summary.csv','descriptive five-seed workload summaries'),('worker_costs.csv','whole run/validation/resume worker costs'),('fit_operation_counts.csv','actual wrapper/learner/calibrator counts'),('operations.csv','complete nested operation journal'),('enbpi_oob_support.csv','finite/nonfinite native OOB scores'),('dscp_summary.csv','clusters, neighbours and matched-owner hashes'),('seasonal_aliases.csv','twelve explicit deterministic aliases'),('validation_summary.csv','per-seed validation and zero-fit resume'),('interval_completion_overlay.csv','150/1950 exact completed keys'),('next_proposed_forecasting_units.csv','exact next three-unit execution proposal; not authorized or launched'),('next_proposed_measured_costs.csv','measured fold-2 cost basis and fitting-row-scaled planning estimate'),('analysis_validation.json','aggregate acceptance')]
    for name,purpose in purposes:lines.append(f'- [{name}]({a}{name}): {purpose}.')
    lines += ['', 'Figures: [coverage PNG]('+a+'figures/five_seed_coverage.png) ([sources]('+a+'figures/five_seed_coverage.sources.json)), [MPIW PNG]('+a+'figures/five_seed_mpiw.png) ([sources]('+a+'figures/five_seed_mpiw.sources.json)), [Winkler PNG]('+a+'figures/five_seed_winkler.png) ([sources]('+a+'figures/five_seed_winkler.sources.json)); PDF versions are alongside them.','', '[Exact byte manifest](EVIDENCE_MANIFEST.csv) covers the bounded task artifacts except itself; the Git commit binds the manifest.']
    atomic(REVIEW/'EVIDENCE_INDEX.md','\n'.join(lines)+'\n')

def main(label):
    assert git('branch','--show-current')==BRANCH
    assert git('rev-parse','main')=='06fe967be2be8d7898812c0c2d6e464d4e942351'
    assert git('rev-parse','review/matched-intervals005-bdg2-20260914')==ENTRY
    evidence_index()
    paths=[REVIEW,SMART/'outputs/matched_intervals005/bdg2_fold2_multiseed_v2_coordinator',*[run(s) for s in SEEDS],*[design(s) for s in SEEDS],*[auth(s) for s in SEEDS],SMART/'src/matched_intervals005.py',SMART/'src/intervals005_common.py',SMART/'src/intervals005_data.py',SMART/'src/intervals005_owners.py',SMART/'src/intervals005_stream.py',SMART/'src/intervals005_validate.py',SMART/'tests/test_matched_intervals005_multiseed.py',ROOT/'.gitattributes',ROOT/'.gitignore']
    for name in ('BDG2_MATCHED_INTERVAL_METHODS_MULTISEED_REPORT.md','review/CURRENT_EVIDENCE.md','PROJECT_RECOVERY_STATUS.md','MATCHED_METHOD_READINESS_MAP.md'):
        if (ROOT/name).exists():paths.append(ROOT/name)
    files=sorted(set(p for path in paths for p in (path.rglob('*') if path.is_dir() else [path]) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.tmp') and p.name!='EVIDENCE_MANIFEST.csv'))
    rows=[]
    for path in files:
        assert path.stat().st_size<100*2**20,path
        rows.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
    manifest=REVIEW/'EVIDENCE_MANIFEST.csv'
    with manifest.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(rows)
    names=[r['path'] for r in rows]+[manifest.relative_to(ROOT).as_posix()]
    pathfile=BACKUP/f'{label}_stage_paths.txt';atomic(pathfile,'\n'.join(names)+'\n')
    subprocess.run(['git','add','--pathspec-from-file='+str(pathfile)],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:subprocess.run(['git','commit','-m','Publish BDG2 interval multiseed: '+label],cwd=ROOT,check=True)
    commit=git('rev-parse','HEAD');bundle=BACKUP/f'{label}_{commit[:7]}.bundle'
    if not bundle.exists():subprocess.run(['git','bundle','create',str(bundle),BRANCH,'^'+ENTRY],cwd=ROOT,check=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    receipt=dict(commit=commit,branch=BRANCH,utc=now(),backup=str(bundle),backup_sha256=sha(bundle),main_and_previous_review_heads_unchanged=True,publication_status='pending')
    env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    pushed=subprocess.run(['git','-c','credential.interactive=false','push','origin','HEAD:refs/heads/'+BRANCH],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    receipt.update(push_exit=pushed.returncode,push_output=pushed.stdout)
    if pushed.returncode==0:receipt['publication_status']='pushed_pending_readback'
    atomic(BACKUP/f'{label}_{commit[:7]}_publication.json',receipt);print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);args=parser.parse_args();main(args.label)
