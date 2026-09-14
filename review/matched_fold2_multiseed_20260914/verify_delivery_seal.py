"""Verify publication additions against a fully verified parent delivery; no fits."""
from common import *
from verify_publication import get


def main():
    commit=git('rev-parse','HEAD')
    assert git('branch','--show-current')==BRANCH
    assert not git('status','--porcelain')
    previous=read(REVIEW/'delivery_v1/REMOTE_VERIFICATION.json')
    assert previous['passed'] and previous['main_unchanged']
    assert previous['entry_remote_head_unchanged']
    subprocess.run(['git','merge-base','--is-ancestor',previous['commit'],commit],cwd=ROOT,check=True)
    refs=git('-c','credential.helper=','ls-remote','origin','refs/heads/'+BRANCH,'refs/heads/main','refs/heads/review/matched-overnight-20260914')
    assert commit+'\trefs/heads/'+BRANCH in refs
    assert ENTRY+'\trefs/heads/review/matched-overnight-20260914' in refs
    assert '06fe967be2be8d7898812c0c2d6e464d4e942351\trefs/heads/main' in refs
    prior={r['path']:r for r in previous['tree_checks']}
    remote=json.loads(get(f'https://api.github.com/repos/jinchuntan/confosense/git/trees/{commit}?recursive=1'))
    assert not remote.get('truncated')
    blobs={r['path']:r for r in remote['tree'] if r['type']=='blob'}
    manifest=list(csv.DictReader((REVIEW/'EVIDENCE_MANIFEST.csv').open(encoding='utf-8')))
    inherited=[];downloads=[]
    for row in manifest:
        name=row['path'];data=(ROOT/name).read_bytes()
        digest=hashlib.sha256(data).hexdigest()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert digest==row['sha256'] and len(data)==int(row['bytes'])
        assert blobs[name]['sha']==blob and blobs[name]['size']==len(data),name
        before=prior.get(name)
        if before and before['git_blob']==blob and before['sha256']==digest:
            inherited.append(name)
        else:
            downloaded=get(f'https://raw.githubusercontent.com/jinchuntan/confosense/{commit}/{name}')
            assert hashlib.sha256(downloaded).hexdigest()==digest,name
            downloads.append(dict(path=name,bytes=len(data),sha256=digest,git_blob=blob))
    # The manifest cannot include its own hash; independently download it.
    name=(REVIEW/'EVIDENCE_MANIFEST.csv').relative_to(ROOT).as_posix()
    assert hashlib.sha256(get(f'https://raw.githubusercontent.com/jinchuntan/confosense/{commit}/{name}')).hexdigest()==sha(ROOT/name)
    changed=git('diff','--name-only',previous['commit'],commit).splitlines()
    assert all(p.startswith(REVIEW.relative_to(ROOT).as_posix()+'/') for p in changed),changed
    current=dict(line.split(' ',1) for line in git('for-each-ref','--format=%(refname) %(objectname)','refs/heads').splitlines())
    for line in read(REVIEW/'entry_preservation.json')['refs'].splitlines():
        ref,old=line.split(' ',1)
        if ref.startswith('refs/heads/') and ref!='refs/heads/'+BRANCH:assert current[ref]==old,ref
    bundle=BACKUP/f'delivery_verified_{commit[:7]}.bundle'
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    assert sha(previous['backup'])==previous['backup_sha256']
    entry_backup=BACKUP.parent/'matched_overnight_20260914/delivery_verified_3df9cbd.bundle'
    assert sha(entry_backup)=='0d55271b1d26718ee0dd6448b9102734f9d5372d923325546b0409ea1d0250da'
    subprocess.run(['git','-c','credential.helper=','fetch','origin'],cwd=ROOT,check=True)
    assert git('rev-parse','origin/'+BRANCH)==commit
    assert not git('status','--porcelain')
    result=dict(passed=True,utc=now(),branch=BRANCH,commit=commit,prior_fully_verified_commit=previous['commit'],prior_raw_readbacks=previous['raw_readbacks'],current_tree_files=len(manifest),unchanged_verified_blobs=len(inherited),new_or_changed_raw_readbacks=len(downloads)+1,main_and_prior_review_heads_unchanged=True,clean_worktree=True,changed_paths=changed,download_checks=downloads,backup=str(bundle),backup_sha256=sha(bundle),prior_delivery_bundle_preserved=True,entry_bundle_preserved=True,models_fitted=0)
    atomic(BACKUP/'final_remote_verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('changed_paths','download_checks')},indent=2),flush=True)


if __name__=='__main__':main()
