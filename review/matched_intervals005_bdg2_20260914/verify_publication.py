"""Read-only remote Git tree and representative exact artifact downloads."""
import concurrent.futures,urllib.request
from common import *


def get(url):
    request=urllib.request.Request(url,headers={'User-Agent':'ConfoSense-matched-intervals005-verification'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request,timeout=60) as response:return response.read()
        except Exception:
            if attempt==2:raise
            time.sleep(1+attempt)


def main():
    commit=git('rev-parse','HEAD');assert git('branch','--show-current')==BRANCH and not git('status','--porcelain')
    status=read(BATCH/'progress.json');assert status['status']=='complete'
    assert read(BATCH/'validation_v5/validation.json')['passed'] and read(BATCH/'completed_resume_v1.json')['all_run_files_unchanged']
    refs=git('-c','credential.helper=','ls-remote','origin','refs/heads/'+BRANCH,'refs/heads/main','refs/heads/review/matched-fold2-multiseed-20260914')
    assert commit+'\trefs/heads/'+BRANCH in refs
    assert ENTRY+'\trefs/heads/review/matched-fold2-multiseed-20260914' in refs
    preserved=read(REVIEW/'entry_preservation.json')
    local=dict(line.split(' ',1) for line in git('for-each-ref','--format=%(refname) %(objectname)','refs/heads').splitlines())
    for line in preserved['refs'].splitlines():
        name,old=line.split(' ',1)
        if name.startswith('refs/heads/') and name!='refs/heads/'+BRANCH:assert local[name]==old
    assert local['refs/heads/main']+'\trefs/heads/main' in refs
    remote=json.loads(get(f'https://api.github.com/repos/jinchuntan/confosense/git/trees/{commit}?recursive=1'));assert not remote.get('truncated')
    blobs={r['path']:r for r in remote['tree'] if r['type']=='blob'}
    manifest=list(csv.DictReader((REVIEW/'EVIDENCE_MANIFEST.csv').open(encoding='utf-8')));checked=[]
    for r in manifest:
        data=(ROOT/r['path']).read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==r['sha256']
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert blobs[r['path']]['sha']==blob and blobs[r['path']]['size']==len(data)
        checked.append(dict(path=r['path'],sha256=digest,git_blob=blob,bytes=len(data)))
    samples=['MATCHED_INTERVALS005_IMPLEMENTATION_REPORT.md','BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md','review/CURRENT_EVIDENCE.md','MATCHED_METHOD_READINESS_MAP.md']
    samples += [REVIEW.relative_to(ROOT).as_posix()+'/'+name for name in ['EVIDENCE_INDEX.md','EVIDENCE_MANIFEST.csv','PANEL_RESPONSE.md','METHOD_REFERENCES.md','joint_pre_fit_manifest.json','evaluated_commit.json','evaluated_source.zip','SYNTHETIC_ACCEPTANCE.json','VALIDATION_ERRATUM_V4.md','VALIDATION_ERRATUM_V4.json','VALIDATION_RECOVERY_COMMANDS_V4.json','corrected_validation_source_v4.zip','method_specification_resolved_v2.json','enbpi_bounds_diagnosis.csv','delivery_v1/validation.json']]
    samples += [DESIGN.relative_to(ROOT).as_posix()+'/'+name for name in ['frozen_protocol.json','method_specification.json','native_membership.csv.gz','joint_calibration.csv.gz','joint_test.csv.gz','readiness.json']]
    samples += [BATCH.relative_to(ROOT).as_posix()+'/'+name for name in ['validation_v5/validation.json','validation_v5/reconstruction_checks.csv','completed_resume_v1.json','run_worker_resources_v1.json','validate_worker_resources_v5.json','resume_worker_resources_v1.json','analysis_v1/native_support_metrics.csv','analysis_v1/common_support_metrics.csv','analysis_v1/per_building_metrics.csv','analysis_v1/background_workload.csv','analysis_v1/worker_costs.csv','analysis_v1/operations.csv','analysis_v1/seasonal_interval_metrics.csv','analysis_v1/shared_owner_contrasts.csv','analysis_v1/next_proposed_method_keys.csv','analysis_v1/background_and_crossing_checks.csv','analysis_v1/additional_integrity_validation.json','analysis_v1/enbpi_calibration_support.csv']]
    for h in (1,3,6):
        for l in (90,95):
            for method in ('quantile_uncalibrated','cqr','recentred_enbpi_static','recentred_enbpi_updated','dscp'):
                for name in ('issued.csv.gz','consumed.csv.gz','stream_identity.json'):
                    samples.append((RUN/f'stages/stream_h{h}_l{l}_{method}'/name).relative_to(ROOT).as_posix())
            samples.append((RUN/f'stages/owner_cal_h{h}_cqr_l{l}/owner.pkl').relative_to(ROOT).as_posix())
        samples.append((RUN/f'stages/owner_cal_h{h}_enbpi/owner.pkl').relative_to(ROOT).as_posix())
    samples.append((RUN/'stages/dscp_fit/calibrator.pkl').relative_to(ROOT).as_posix())
    for name in ('native_interval_quality','common_interval_quality','stage_costs'):
        for ext in ('png','pdf','sources.json'):samples.append((BATCH/f'analysis_v1/figures/{name}.{ext}').relative_to(ROOT).as_posix())
    def verify(path):
        data=get(f'https://raw.githubusercontent.com/jinchuntan/confosense/{commit}/{path}');d=hashlib.sha256(data).hexdigest();assert d==sha(ROOT/path),path
        return dict(path=path,sha256=d,bytes=len(data))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:downloads=list(pool.map(verify,samples))
    bundle=list(BACKUP.glob('*_'+commit[:7]+'.bundle'))[-1];subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    assert sha(preserved['prior_bundle'])==preserved['prior_bundle_sha256']
    subprocess.run(['git','-c','credential.helper=','fetch','origin'],cwd=ROOT,check=True)
    assert git('rev-parse','origin/'+BRANCH)==commit and not git('status','--porcelain')
    result=dict(passed=True,utc=now(),commit=commit,branch=BRANCH,remote_tree_files=len(checked),raw_readbacks=len(downloads),main_and_previous_review_heads_unchanged=True,entry_backup_preserved=True,clean_worktree=True,backup=str(bundle),backup_sha256=sha(bundle),tree_checks=checked,download_checks=downloads)
    atomic(BACKUP/'remote_verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('tree_checks','download_checks')},indent=2),flush=True)


if __name__=='__main__':main()
