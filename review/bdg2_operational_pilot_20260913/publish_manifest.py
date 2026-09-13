"""Manifest the new review scope from staged objects and check evidence bytes."""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]
BASE='2243c167804690ad1ec9b8aebc369e5596d392aa'
HERE='review/bdg2_operational_pilot_20260913/'
EXCLUDED={HERE+'EVIDENCE_MANIFEST.csv',HERE+'publication_validation.json'}
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    changed=git('diff','--cached','--name-only',BASE).decode().splitlines()
    rows=[];links=[]
    allowed={'.gitattributes','.gitignore','BDG2_OPERATIONAL_PILOT_REPORT.md','review/CURRENT_EVIDENCE.md','review/DATA_NOTICE.md'}
    prefixes=(HERE,'smart_building_conformal/outputs/amendment004/bdg2_',
        'smart_building_conformal/src/operational004','smart_building_conformal/tests/test_operational004_',
        'smart_building_conformal/tests/test_independent_bdg2_',
        'smart_building_conformal/scripts/verify_bdg2_','smart_building_conformal/scripts/independent_bdg2_')
    allowed.add('smart_building_conformal/scripts/log_pilot_command.py')
    pattern=re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{36,}|AKIA[A-Z0-9]{16}')
    for path in changed:
        if path in EXCLUDED:continue
        assert path in allowed or path.startswith(prefixes),path
        data=git('show',':'+path);assert len(data)<100*1024**2,(path,len(data))
        assert not pattern.search(data),path
        if path.endswith('.md'):
            for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',data.decode('utf-8')):
                if '://' in target or target.startswith('#'):continue
                target=target.split('#')[0].strip('<>');p=((ROOT/path).parent/target).resolve()
                assert p.exists() or p in {ROOT/x for x in EXCLUDED},(path,target)
                links.append(p)
        purpose=('canonical completed BDG2 pilot unit' if '/bdg2_operational_pilot_f2_s42_v2/' in path else
                 'preserved failed pre-fit attempt' if '/bdg2_operational_pilot_f2_s42_v1/' in path else
                 'execution identity, exact source or measured phases' if '_execution/' in path else
                 'independent validation, regression or command evidence' if '/outputs/' in path else
                 'review report, reproducible helper or implementation')
        rows.append(dict(path=path,bytes=len(data),git_blob=git('rev-parse',':'+path).decode().strip(),sha256=sha(data),purpose=purpose))
    base='smart_building_conformal/outputs/amendment004/'
    archives=0
    for version in ['v1','v2']:
        prefix=base+f'bdg2_operational_pilot_f2_s42_{version}_execution/'
        ident=json.loads(git('show',':'+prefix+'prefit_identity.json'))
        archive=git('show',':'+prefix+'evaluated_source.zip')
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            lines=[n.removeprefix('src/')+':'+sha(z.read(n)) for n in sorted(z.namelist())]
            assert sha('\n'.join(lines).encode())==ident['spec']['source_hash']
        archives+=1
    prefix=base+'bdg2_operational_pilot_f2_s42_v2/units/outer2_model42/'
    complete=json.loads(git('show',':'+prefix+'COMPLETE.json'))
    large=json.loads(git('show',':'+base+'bdg2_pilot_publication_v1/large_files.json'))
    split={r['repository_path']:r for r in large['files']}
    for name,h in complete['hashes'].items():
        path=prefix+name
        if path in split:
            digest=hashlib.sha256();size=0
            for part in split[path]['parts']:
                data=git('show',':'+part['repository_path'])
                assert sha(data)==part['sha256'] and len(data)==part['bytes']
                digest.update(data);size+=len(data)
            assert digest.hexdigest()==h==split[path]['sha256'] and size==split[path]['bytes']
        else:assert sha(git('show',':'+path))==h,name
    manifest=ROOT/HERE/'EVIDENCE_MANIFEST.csv'
    with manifest.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['path','bytes','git_blob','sha256','purpose']);w.writeheader();w.writerows(rows)
    result=dict(passed=True,entry_commit=BASE,manifest_files=len(rows),manifest_bytes=sum(r['bytes'] for r in rows),
        largest_file=max(rows,key=lambda x:x['bytes']),local_links_checked=len(links),source_archives_verified=archives,
        completed_unit_files_verified=len(complete['hashes']),oversized_files_verified_via_lossless_parts=len(split),
        scope_checked=True,credential_pattern_scan_passed=True,
        excluded_self_hashes=sorted(EXCLUDED),global_study_ready=False)
    (ROOT/HERE/'publication_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
