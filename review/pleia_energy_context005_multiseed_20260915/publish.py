"""Seal, back up, push and verify the completed multiseed evidence."""
from __future__ import annotations
import argparse,csv as csvmod,hashlib,json,subprocess
from common import *

def main(label):
    if git('branch','--show-current')!=BRANCH or git('rev-parse','main')!=MAIN:raise ValueError('branch/main preservation failure')
    base=read(REVIEW/'PRESERVATION_BASELINE.json')
    for ref,value in base['prior_heads'].items():
        if ref==f'refs/heads/{BRANCH}':continue
        if git('rev-parse',ref)!=value:raise ValueError('prior head moved: '+ref)
    for path in base['historical_untracked_files']:
        if not (REPO/path).is_file():raise ValueError('historical local file missing: '+path)
    assert digest(SEED42_RUN/'COMPLETE.json')==base['seed42_complete_sha256']
    a=read(ANALYSIS/'validation.json');v=read(ANALYSIS/'independent_validation.json');p=read(REVIEW/'RAW_PACKAGE_VALIDATION.json')
    assert a['passed'] and v['passed'] and p['passed'] and source_digest()==SOURCE_HASH
    for seed in SEEDS:
        assert read(validation(seed)/'validation.json')['passed'] and read(resume(seed))['passed'] and read(publication(seed)/'validation.json')['passed']
    atomic(REVIEW/'COMPLETION_VERIFICATION.json',dict(passed=True,branch=BRANCH,main=MAIN,source_hash=source_digest(),seed42_reused_without_rerun=True,
        completed_new_seeds=list(SEEDS),all_five_seeds=list(ALL_SEEDS),contexts=68,schedules_per_seed=2856,new_event_records=685440,total_event_records=856800,
        seed_specific_macro_cells=300,five_seed_comparison_cells=60,independent_validation_passed=True,completed_resume_zero_fit_all_new_seeds=True,
        raw_archive_parts=p['parts'],raw_archive_members=p['members'],energy_sensitivity_applied=False,matched_forecasting_complete=70,interval_quality_complete=250,seasonal_unique_complete=9,full_study_ready=False))
    roots=[REVIEW,BATCH,ANALYSIS,REPO/'review/CURRENT_EVIDENCE.md']
    for seed in SEEDS:roots += [manifest(seed),design(seed),publication(seed)]
    files={q for root in roots for q in (root.rglob('*') if root.is_dir() else [root]) if q.is_file()}
    # Direct core scientific records; the complete many-file trees are in verified ZIP parts.
    for seed in SEEDS:
        files|={run(seed)/'COMPLETE.json',run(seed)/'operations.jsonl'}
        for stage in ['owner_fit_cqr','owner_cal_cqr','controls','tables']:
            files|={q for q in (run(seed)/'stages'/stage).rglob('*') if q.is_file()}
    files=sorted(q for q in files if '__pycache__' not in q.parts and q.suffix not in ['.pyc','.tmp'] and q.name!='EVIDENCE_MANIFEST.csv')
    BACKUP.mkdir(parents=True,exist_ok=True);pathfile=BACKUP/(label+'_paths.txt');rels=[q.relative_to(REPO).as_posix() for q in files];atomic(pathfile,'\n'.join(rels)+'\n')
    subprocess.run(['git','add','--pathspec-from-file='+str(pathfile)],cwd=REPO,check=True)
    rows=[]
    for rel in rels:
        blob=subprocess.check_output(['git','show',':'+rel],cwd=REPO)
        if len(blob)>=100*2**20:raise ValueError('blob exceeds GitHub limit: '+rel)
        rows.append(dict(path=rel,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest()))
    manifest_path=REVIEW/'EVIDENCE_MANIFEST.csv'
    with manifest_path.open('w',encoding='utf-8',newline='') as f:
        w=csvmod.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(rows)
    subprocess.run(['git','add',str(manifest_path.relative_to(REPO))],cwd=REPO,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=REPO,check=True)
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=REPO).returncode:
        subprocess.run(['git','commit','-m','Publish PLEIA-energy context005 five-seed evidence'],cwd=REPO,check=True)
    head=git('rev-parse','HEAD');bundle=BACKUP/(label+'_'+head[:8]+'.bundle')
    subprocess.run(['git','bundle','create',str(bundle),BRANCH,'^'+ENTRY],cwd=REPO,check=True);subprocess.run(['git','bundle','verify',str(bundle)],cwd=REPO,check=True)
    subprocess.run(['git','push','-u','origin',BRANCH],cwd=REPO,check=True)
    subprocess.run(['git','fetch','origin',BRANCH],cwd=REPO,check=True)
    remote=git('rev-parse','origin/'+BRANCH)
    if remote!=head:raise ValueError('remote head mismatch')
    representative=[REVIEW/'EVIDENCE_INDEX.md',ANALYSIS/'five_seed_control_rule_channel.csv',ANALYSIS/'independent_validation.json',publication(46)/'parts_manifest.csv']
    remote_checks=[]
    for path in representative:
        rel=path.relative_to(REPO).as_posix();blob=subprocess.check_output(['git','show','origin/'+BRANCH+':'+rel],cwd=REPO)
        remote_checks.append(dict(path=rel,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest()))
    receipt=dict(passed=True,branch=BRANCH,commit=head,remote_commit=remote,url=f'https://github.com/jinchuntan/confosense/tree/{head}',
        backup=str(bundle),backup_bytes=bundle.stat().st_size,backup_sha256=digest(bundle),evidence_files=len(rows),evidence_bytes=sum(r['bytes'] for r in rows),
        representative_remote_checks=remote_checks,main_unchanged=git('rev-parse','main')==MAIN,utc=now())
    atomic(BACKUP/(label+'_publication_receipt.json'),receipt);atomic(REVIEW/'PUBLICATION_RECEIPT.json',receipt)
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);main(p.parse_args().label)
