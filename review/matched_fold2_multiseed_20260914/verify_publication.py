"""Read-only GitHub blob/download verification; receipts and bundles stay external."""
import concurrent.futures, urllib.request
from common import *

def get(url):
    request=urllib.request.Request(url,headers={'User-Agent':'ConfoSense-multiseed-evidence-verification'})
    with urllib.request.urlopen(request,timeout=60) as response:return response.read()

def main():
    commit=git('rev-parse','HEAD');assert git('branch','--show-current')==BRANCH
    state=read(BATCH/'progress.json');assert state['status']=='complete' and state['completed_units']==52
    assert not git('status','--porcelain'),'final delivery must be committed before remote verification'
    refs=git('-c','credential.helper=','ls-remote','origin','refs/heads/'+BRANCH,'refs/heads/main','refs/heads/review/matched-overnight-20260914')
    assert commit+'\trefs/heads/'+BRANCH in refs
    assert ENTRY+'\trefs/heads/review/matched-overnight-20260914' in refs
    assert '06fe967be2be8d7898812c0c2d6e464d4e942351\trefs/heads/main' in refs
    current=dict(line.split(' ',1) for line in git('for-each-ref','--format=%(refname) %(objectname)','refs/heads').splitlines())
    for line in read(REVIEW/'entry_preservation.json')['refs'].splitlines():
        ref,old=line.split(' ',1)
        if ref.startswith('refs/heads/') and ref!='refs/heads/'+BRANCH:assert current[ref]==old,ref
    remote=json.loads(get(f'https://api.github.com/repos/jinchuntan/confosense/git/trees/{commit}?recursive=1'))
    assert not remote.get('truncated');blobs={r['path']:r for r in remote['tree'] if r['type']=='blob'}
    manifest=list(csv.DictReader((REVIEW/'EVIDENCE_MANIFEST.csv').open(encoding='utf-8')))
    checked=[]
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    try:
        for row in manifest:
            path=row['path'];process.stdin.write((commit+':'+path+'\n').encode());process.stdin.flush()
            header=process.stdout.readline().split();assert len(header)==3 and header[1]==b'blob',path
            size=int(header[2]);data=process.stdout.read(size);assert len(data)==size and process.stdout.read(1)==b'\n'
            digest=hashlib.sha256(data).hexdigest();assert digest==row['sha256']==sha(ROOT/path),path
            blob=header[0].decode();assert blobs[path]['sha']==blob and blobs[path]['size']==size,path
            checked.append(dict(path=path,sha256=digest,git_blob=blob,bytes=size))
    finally:
        process.stdin.close();process.wait()
    prefix=BATCH.relative_to(ROOT).as_posix()+'/analysis_v1/'
    samples=['MATCHED_FOLD2_MULTISEED_REPORT.md','MATCHED_FAILURE_DIAGNOSIS.md','MATCHED_METHOD_READINESS_MAP.md','review/CURRENT_EVIDENCE.md']
    samples += [REVIEW.relative_to(ROOT).as_posix()+'/'+p for p in ['EVIDENCE_INDEX.md','EVIDENCE_MANIFEST.csv','PROGRESS_AND_RESTART.md','PANEL2_NUMERICAL_RESPONSE.md','evaluated_source.zip','joint_pre_fit_manifest.json','cross_seed_support.csv']]
    samples += [REVIEW.relative_to(ROOT).as_posix()+'/delivery_v1/'+p for p in ['COMPLETION_VERIFICATION.md','validation.json','actual_outer_command_receipts.csv','final_checks_v1/panel2_both_levels.csv','final_checks_v1/validation.json','cost_figure_v3/cost_and_error.png','cost_figure_v3/cost_and_error.pdf','cost_figure_v3/sources.json']]
    samples += [prefix+p for p in ['combined_comparison.csv','new_only_comparison.csv','fold2_five_seed_comparison.csv','interval_quality.csv','training_seed_summary.csv','paired_model_contrasts.csv','actual_seed_metadata.csv','group_metrics.csv','rico_phase_metrics.csv','model_costs.csv','run_costs.csv','seed_block_costs.csv','analysis_validation.json','completion_overlay.csv','remaining_queue_updated.csv','figures/forecast_error.png','figures/coverage.png','figures/interval_width.png','figures/winkler.png','figures/cost_and_error.png']]
    samples += [BATCH.relative_to(ROOT).as_posix()+'/diagnosis_v2/'+p for p in ['validation.json','role_target_ranges.csv','permitted_feature_ranges.csv','point_bias_by_role.csv','rico_phase_bias.csv','frozen_radius_residual_shift.csv','timeblock_group_coverage.csv','input_manifest.csv']]
    first={'pleia_energy':1,'rico':5,'bdg2':1,'pleia':1}
    for u in read(REVIEW/'joint_pre_fit_manifest.json')['units']:
        done=state['units'][u['stem']];run=Path(u['run']).relative_to(ROOT).as_posix();design=Path(u['design']).relative_to(ROOT).as_posix()
        samples += [design+'/frozen_protocol.json',run+'/point_summary.csv',run+'/interval_quality.csv',Path(done['audit']).relative_to(ROOT).as_posix()+'/validation.json',Path(done['audit']).relative_to(ROOT).as_posix()+'/saved_model_verification.csv',Path(done['resume']).relative_to(ROOT).as_posix()]
        if u['key'][1]==first[u['key'][0]]:
            for model,artifact in [('persistence','model.json'),('xgboost','model.ubj'),('attention_lstm','model.pt')]:
                part=run+'/units/'+u['stem'].removesuffix('_v1')+'_'+model+'/'
                samples += [part+artifact,part+'predictions.csv.gz',part+'calibration.csv.gz']
    def verify(path):
        data=get(f'https://raw.githubusercontent.com/jinchuntan/confosense/{commit}/{path}')
        digest=hashlib.sha256(data).hexdigest();assert digest==sha(ROOT/path),path
        return dict(path=path,sha256=digest,bytes=len(data))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:downloads=list(pool.map(verify,samples))
    bundles=list(BACKUP.glob('*_'+commit[:7]+'.bundle'));assert bundles
    bundle=bundles[-1];subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    old=BACKUP.parent/'matched_overnight_20260914/delivery_verified_3df9cbd.bundle'
    assert sha(old)=='0d55271b1d26718ee0dd6448b9102734f9d5372d923325546b0409ea1d0250da'
    subprocess.run(['git','-c','credential.helper=','fetch','origin'],cwd=ROOT,check=True)
    assert git('rev-parse','origin/'+BRANCH)==commit and not git('status','--porcelain')
    result=dict(passed=True,utc=now(),branch=BRANCH,commit=commit,remote_tree_files=len(checked),raw_readbacks=len(downloads),main_unchanged=True,prior_local_review_heads_unchanged=True,entry_remote_head_unchanged=True,clean_worktree=True,backup=str(bundle),backup_sha256=sha(bundle),entry_backup_preserved=str(old),tree_checks=checked,download_checks=downloads)
    atomic(BACKUP/'remote_verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['tree_checks','download_checks']},indent=2))

if __name__=='__main__':main()
