"""Verify the published Git tree and representative exact downloads."""
import concurrent.futures,csv,hashlib,json,subprocess,time,urllib.request
from common import *

def get(url):
    request=urllib.request.Request(url,headers={'User-Agent':'ConfoSense-interval-multiseed-verifier'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request,timeout=60) as response:return response.read()
        except Exception:
            if attempt==2:raise
            time.sleep(1+attempt)

def main():
    commit=git('rev-parse','HEAD');assert git('branch','--show-current')==BRANCH
    refs=git('-c','credential.helper=','ls-remote','origin','refs/heads/'+BRANCH,'refs/heads/main','refs/heads/review/matched-intervals005-bdg2-20260914')
    assert commit+'\trefs/heads/'+BRANCH in refs and ENTRY+'\trefs/heads/review/matched-intervals005-bdg2-20260914' in refs
    assert git('rev-parse','main')+'\trefs/heads/main' in refs
    remote=json.loads(get(f'https://api.github.com/repos/jinchuntan/confosense/git/trees/{commit}?recursive=1'));assert not remote.get('truncated')
    blobs={r['path']:r for r in remote['tree'] if r['type']=='blob'}
    manifest=list(csv.DictReader((REVIEW/'EVIDENCE_MANIFEST.csv').open(encoding='utf-8')))
    for row in manifest:
        data=(ROOT/row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert blobs[row['path']]['sha']==blob and blobs[row['path']]['size']==len(data)
    samples=['BDG2_MATCHED_INTERVAL_METHODS_MULTISEED_REPORT.md','review/CURRENT_EVIDENCE.md',REVIEW.relative_to(ROOT).as_posix()+'/EVIDENCE_INDEX.md',REVIEW.relative_to(ROOT).as_posix()+'/EVIDENCE_MANIFEST.csv']
    for seed in SEEDS:
        samples += [(design(seed)/name).relative_to(ROOT).as_posix() for name in ('frozen_protocol.json','scope.csv','readiness.json')]
        samples += [(BATCH/f'seed{seed}_validation/validation.json').relative_to(ROOT).as_posix(),(BATCH/f'seed{seed}_completed_resume.json').relative_to(ROOT).as_posix()]
        for h in (1,3,6):
            for level in (90,95):
                for method in ('quantile_uncalibrated','cqr','recentred_enbpi_static','recentred_enbpi_updated','dscp'):
                    samples.append((run(seed)/f'stages/stream_h{h}_l{level}_{method}/issued.csv.gz').relative_to(ROOT).as_posix())
            samples.append((run(seed)/f'stages/owner_cal_h{h}_enbpi/owner.pkl').relative_to(ROOT).as_posix())
        samples.append((run(seed)/'stages/dscp_fit/calibrator.pkl').relative_to(ROOT).as_posix())
    for name in ('common_support_metrics.csv','five_seed_summary.csv','background_workload.csv','worker_costs.csv','fit_operation_counts.csv','analysis_validation.json'):
        samples.append((BATCH/'analysis_v1'/name).relative_to(ROOT).as_posix())
    def verify(path):
        data=get(f'https://raw.githubusercontent.com/jinchuntan/confosense/{commit}/{path}');assert hashlib.sha256(data).hexdigest()==sha(ROOT/path),path
        return path
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:downloads=list(pool.map(verify,samples))
    bundle=list(BACKUP.glob('*_'+commit[:7]+'.bundle'))[-1];subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    result=dict(passed=True,commit=commit,branch=BRANCH,utc=now(),manifest_remote_blob_checks=len(manifest),exact_downloads=len(downloads),main_and_previous_review_heads_unchanged=True,backup=str(bundle),backup_sha256=sha(bundle))
    atomic(BACKUP/'REMOTE_VERIFICATION.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
