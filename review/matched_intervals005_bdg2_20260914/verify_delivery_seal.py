"""Verify the final delivery commit after publishing the full remote-proof receipt."""
from common import *
from verify_publication import get


def main():
    commit=git('rev-parse','HEAD')
    assert git('branch','--show-current')==BRANCH and not git('status','--porcelain')
    prior=read(REVIEW/'delivery_v1/REMOTE_VERIFICATION.json')
    assert prior['passed']
    subprocess.run(['git','merge-base','--is-ancestor',prior['commit'],commit],cwd=ROOT,check=True)
    refs=git('-c','credential.helper=','ls-remote','origin','refs/heads/'+BRANCH,'refs/heads/main','refs/heads/review/matched-fold2-multiseed-20260914')
    assert commit+'\trefs/heads/'+BRANCH in refs
    assert ENTRY+'\trefs/heads/review/matched-fold2-multiseed-20260914' in refs
    assert git('rev-parse','main')+'\trefs/heads/main' in refs
    remote=json.loads(get(f'https://api.github.com/repos/jinchuntan/confosense/git/trees/{commit}?recursive=1'))
    assert not remote.get('truncated')
    blobs={r['path']:r for r in remote['tree'] if r['type']=='blob'}
    manifest=list(csv.DictReader((REVIEW/'EVIDENCE_MANIFEST.csv').open(encoding='utf-8')))
    for row in manifest:
        data=(ROOT/row['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['sha256']
        assert blobs[row['path']]['size']==len(data)
        assert blobs[row['path']]['sha']==hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    changed=git('diff','--name-only',prior['commit'],commit).splitlines()
    readbacks=[]
    for path in changed:
        remote_data=get(f'https://raw.githubusercontent.com/jinchuntan/confosense/{commit}/{path}')
        assert hashlib.sha256(remote_data).hexdigest()==sha(ROOT/path),path
        readbacks.append(dict(path=path,bytes=len(remote_data),sha256=sha(ROOT/path)))
    preserved=read(REVIEW/'entry_preservation.json')
    assert sha(preserved['prior_bundle'])==preserved['prior_bundle_sha256']
    local=dict(line.split(' ',1) for line in git('for-each-ref','--format=%(refname) %(objectname)','refs/heads').splitlines())
    for line in preserved['refs'].splitlines():
        name,value=line.split(' ',1)
        if name.startswith('refs/heads/') and name!='refs/heads/'+BRANCH:assert local[name]==value
    bundle=list(BACKUP.glob('*_'+commit[:7]+'.bundle'))[-1]
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    assert not git('status','--porcelain')
    result=dict(passed=True,commit=commit,branch=BRANCH,utc=now(),manifest_remote_blob_checks=len(manifest),prior_full_remote_proof_commit=prior['commit'],prior_exact_downloads=prior['raw_readbacks'],changed_file_exact_readbacks=readbacks,main_and_prior_review_heads_unchanged=True,clean_worktree=True,backup=str(bundle),backup_sha256=sha(bundle))
    atomic(BACKUP/'FINAL_DELIVERY_SEAL.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
