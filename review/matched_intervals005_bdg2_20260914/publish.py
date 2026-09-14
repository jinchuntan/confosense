"""Bounded exact-byte publication and verified incremental external backup."""
import argparse
from common import *


def index():
    text='# Matched intervals005 / BDG2 pilot evidence index\n\n'
    text+='[User authorization](USER_AUTHORIZATION.txt), [complete pinned handoff](AUTHORIZING_HANDOFF.md), [entry preservation](entry_preservation.json), [method/reference attribution](METHOD_REFERENCES.md), [synthetic acceptance](SYNTHETIC_ACCEPTANCE.json), [retained fixture recovery](SYNTHETIC_RECOVERY.md), and [durable progress/restart](PROGRESS_AND_RESTART.md).\n\n'
    if (REVIEW/'joint_pre_fit_manifest.json').exists():text+='[Exact pre-fit commands and identities](joint_pre_fit_manifest.json). '
    if (REVIEW/'evaluated_commit.json').exists():text+='[Evaluated commit](evaluated_commit.json). '
    text+='[Evaluated source archive](evaluated_source.zip).\n\n'
    if (ROOT/'MATCHED_INTERVALS005_IMPLEMENTATION_REPORT.md').exists():text+='[Implementation report](../../MATCHED_INTERVALS005_IMPLEMENTATION_REPORT.md), [completed numerical report](../../BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md), [panel response](PANEL_RESPONSE.md), and [current evidence](../CURRENT_EVIDENCE.md).\n\n'
    text+='## Protocol and scientific results\n\n'
    d='../../'+DESIGN.relative_to(ROOT).as_posix()+'/'
    for name in ['frozen_protocol.json','method_specification.json','scope.csv','native_membership.csv.gz','joint_fit.csv.gz','joint_calibration.csv.gz','joint_test.csv.gz','readiness.json']:
        if (DESIGN/name).exists():text+=f'- [{name}]({d}{name})\n'
    if RUN.exists():
        r='../../'+RUN.relative_to(ROOT).as_posix()+'/'
        text+=f'\n[Scientific checkpoints, serialized owners/calibrators, exact raw and issued/consumed streams]({r}stages), [actual operation journal]({r}operations.jsonl), [stage journal]({r}stage_journal.jsonl).\n\n'
    analysis=BATCH/'analysis_v1'
    if (analysis/'COMPLETE.json').exists():
        prefix='../../'+analysis.relative_to(ROOT).as_posix()+'/'
        for name,purpose in [('native_support_metrics.csv','30 native-support method cells'),('common_support_metrics.csv','30 views on the identical DSCP-supported rows'),('per_building_metrics.csv','original-building counts and metrics'),('shared_owner_contrasts.csv','CQR minus uncalibrated and updated minus static'),('background_workload.csv','numerical/availability/combined hourly immediate episodes and exposure'),('seasonal_point_metrics.csv','three deterministic point computations'),('seasonal_interval_metrics.csv','six seasonal own-residual interval cells'),('worker_costs.csv','whole CLI worker wall/CPU/memory'),('stage_costs.csv','nonoverlapping scientific stage wall/CPU/memory'),('preparation_costs.csv','full preparation costs, excluded from stage no-op bookkeeping'),('operations.csv','nested wrapper, learned estimator and calibrator calls; not additive runtime'),('interval_completion_overlay.csv','30/1950 completed method keys'),('next_proposed_method_keys.csv','120 explicit unlaunched next keys'),('next_proposed_costs.json','measured pilot scaling and sharing counts'),('analysis_validation.json','reconciled completion counts')]:text+=f'- [{name}]({prefix}{name}): {purpose}.\n'
        for figure in ('native_interval_quality','common_interval_quality','stage_costs'):text+=f'- {figure}: [PNG]({prefix}figures/{figure}.png), [PDF]({prefix}figures/{figure}.pdf), [source hashes]({prefix}figures/{figure}.sources.json).\n'
        text+='\nRecompute reports without fitting from the original repository layout, using an unused output directory beneath the repository:\n\n```powershell\n& C:/cfs_venv/Scripts/python.exe -B review/matched_intervals005_bdg2_20260914/report.py --out smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/recomputed_analysis_v1\n```\n\nThis creates a new analysis directory and refreshes current report prefixes. It does not modify the scientific run or historical results. Original absolute command paths remain in receipts.\n'
    b='../../'+BATCH.relative_to(ROOT).as_posix()+'/'
    if (BATCH/'validation_v1/validation.json').exists():text+=f'\n[Independent validation]({b}validation_v1/validation.json), [all arithmetic/model/quantile checks]({b}validation_v1/reconstruction_checks.csv), [alert checks]({b}validation_v1/alert_checks.csv), [zero-fit/calibrator-fit completed resume]({b}completed_resume_v1.json).\n'
    if (REVIEW/'delivery_v1').exists():text+='\n[Final delivery and publication receipts](delivery_v1).\n'
    text+='\n[Exact byte manifest](EVIDENCE_MANIFEST.csv) covers the bounded task files except itself; the Git commit binds the manifest. All previous review heads/main and the entry backup chain remain preserved.\n'
    atomic(REVIEW/'EVIDENCE_INDEX.md',text)


def main(label):
    assert git('branch','--show-current')==BRANCH
    preserved=read(REVIEW/'entry_preservation.json')
    allowed={'.gitattributes','review/CURRENT_EVIDENCE.md','PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','MATCHED_METHOD_READINESS_MAP.md'}
    for row in preserved['files']:
        if row['path'] not in allowed:assert sha(ROOT/row['path'])==row['sha256'],'historical file changed: '+row['path']
    refs=dict(line.split(' ',1) for line in git('for-each-ref','--format=%(refname) %(objectname)','refs/heads').splitlines())
    for line in preserved['refs'].splitlines():
        name,value=line.split(' ',1)
        if name.startswith('refs/heads/') and name!='refs/heads/'+BRANCH:assert refs[name]==value,name
    index()
    paths=[REVIEW,SMART/'outputs/matched_intervals005',SMART/'protocols/matched_intervals005',AUTH,ROOT/'.gitattributes',SMART/'tests/test_matched_intervals005.py']
    paths+=list((SMART/'src').glob('intervals005_*.py'))+[SMART/'src/matched_intervals005.py']
    paths+=[ROOT/p for p in ['MATCHED_INTERVALS005_IMPLEMENTATION_REPORT.md','BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md',*sorted(allowed- {'.gitattributes'})] if (ROOT/p).exists()]
    state=read(BATCH/'progress.json') if (BATCH/'progress.json').exists() else {};active=Path(state['active']['attempt_record']).parent if state.get('active') else None
    files=sorted(set(p for path in paths for p in (path.rglob('*') if path.is_dir() else [path]) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.tmp') and p.name!='EVIDENCE_MANIFEST.csv' and not (active and p.is_relative_to(active))))
    rows=[]
    for p in files:
        assert p.stat().st_size<100*2**20,'oversized artifact needs lossless parts: '+str(p)
        rows.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    manifest=REVIEW/'EVIDENCE_MANIFEST.csv'
    with manifest.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(rows)
    names=[r['path'] for r in rows]+[manifest.relative_to(ROOT).as_posix()];pathfile=BACKUP/(label+'_stage_paths.txt');atomic(pathfile,'\n'.join(names)+'\n')
    for extra in ([],['--renormalize']):subprocess.run(['git','add',*extra,'--pathspec-from-file='+str(pathfile)],cwd=ROOT,check=True)
    staged={}
    for entry in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).split(b'\0'):
        if entry:
            meta,name=entry.split(b'\t',1);staged[name.decode()]=meta.split()[1].decode()
    for name in names:
        data=(ROOT/name).read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert staged[name]==blob,name
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:subprocess.run(['git','commit','-m','Publish matched intervals005 BDG2: '+label],cwd=ROOT,check=True)
    commit=git('rev-parse','HEAD');bundle=BACKUP/f'{label}_{commit[:7]}.bundle'
    if not bundle.exists():subprocess.run(['git','bundle','create',str(bundle),BRANCH,'^'+ENTRY],cwd=ROOT,check=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    receipt=dict(commit=commit,branch=BRANCH,utc=now(),backup=str(bundle),backup_sha256=sha(bundle),historical_files_preserved=True,main_and_prior_review_heads_unchanged=True,publication_status='pending')
    env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    try:
        pushed=subprocess.run(['git','-c','credential.interactive=false','push','origin','HEAD:refs/heads/'+BRANCH],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60);receipt.update(push_exit=pushed.returncode,push_output=pushed.stdout)
        if pushed.returncode==0:receipt['publication_status']='push_succeeded_pending_remote_readback'
    except subprocess.TimeoutExpired:receipt['publication_status']='noninteractive_timeout_use_authenticated_desktop'
    atomic(BACKUP/f'{label}_{commit[:7]}_publication.json',receipt);print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);args=parser.parse_args();main(args.label)
