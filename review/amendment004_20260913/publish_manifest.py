"""Build and verify a publication manifest from staged Git objects."""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]
BASE='3354393290d2afaef4361a9a7a1a43336a14c21d'
HERE='review/amendment004_20260913/'
EXCLUDED={HERE+'EVIDENCE_MANIFEST.csv',HERE+'publication_validation.json'}


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def sha(data):return hashlib.sha256(data).hexdigest()


def purpose(path):
    if '/preflight_' in path:return 'no-fitting support or independent validation'
    if '/smoke_20260913_v1/' in path:return 'preserved first smoke checkpoint; command exit 1 reporting error'
    if '/smoke_20260913_v2/' in path:return 'canonical SMOKE ONLY replay, fixtures, resources and resume'
    if '/validation/' in path:return 'execution, verification, preservation or exact source archive'
    if '/src/' in path or '/tests/' in path:return 'implementation or regression tests'
    if '/protocols/' in path or '/configs/' in path:return 'frozen amendment and resolved configuration'
    return 'review report, index, publication audit or reproducible review helper'


def main():
    changed=git('diff','--cached','--name-only',BASE).decode().splitlines()
    rows=[];links=0;pending_links=[];pattern=re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{36,}|AKIA[A-Z0-9]{16}')
    allowed_root={'.gitattributes','OPERATIONAL_EVALUATION_PLAN.md','PILOT_DIAGNOSTICS.md',
        'AMENDMENT004_IMPLEMENTATION_REPORT.md','PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md',
        'review/CURRENT_EVIDENCE.md','review/DATA_NOTICE.md'}
    allowed_prefixes=(HERE,'smart_building_conformal/outputs/amendment004/',
        'smart_building_conformal/src/operational004','smart_building_conformal/src/validate_operational004',
        'smart_building_conformal/protocols/amendment004/')
    allowed_files={'smart_building_conformal/src/unit_checkpoint.py','smart_building_conformal/tests/test_operational004.py',
        'smart_building_conformal/configs/operational_amendment004.json'}
    for path in changed:
        if path in EXCLUDED:continue
        assert path in allowed_root or path in allowed_files or path.startswith(allowed_prefixes),path
        data=git('show',':'+path);assert len(data)<100*1024**2,path
        assert not pattern.search(data),f'possible credential in {path}'
        if path.endswith('.md'):
            for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',data.decode('utf-8')):
                if '://' in target or target.startswith('#'):continue
                target=target.split('#',1)[0].strip('<>')
                resolved=((ROOT/path).parent/target).resolve()
                assert resolved.exists() or resolved in {ROOT/x for x in EXCLUDED},(path,target)
                pending_links.append(resolved)
                links+=1
        oid=git('rev-parse',':'+path).decode().strip()
        rows.append(dict(path=path,bytes=len(data),git_blob=oid,sha256=sha(data),purpose=purpose(path)))
    # Verify the code/config snapshots and saved completed units as published.
    sources=0;unit_files=0
    base='smart_building_conformal/outputs/amendment004/'
    for archive,identity in [('preflight_source.zip','preflight_source.json'),('evaluated_source.zip','evaluated_source.json'),
        ('evaluated_source_v2.zip','evaluated_source_v2.json'),('evaluated_source_v3.zip','evaluated_source_v3.json')]:
        data=git('show',':'+base+'validation/'+archive)
        meta=json.loads(git('show',':'+base+'validation/'+identity))
        assert sha(data)==meta['archive_sha256']
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names=sorted(z.namelist())
            assert all(n.startswith('src/') and n.endswith('.py') for n in names)
            lines=[n.removeprefix('src/')+':'+sha(z.read(n)) for n in names]
            assert sha('\n'.join(lines).encode())==meta['source_hash']
        sources+=1
    for run in ['smoke_20260913_v1','smoke_20260913_v2']:
        prefix=base+run+'/units/outer0_model42/'
        marker=json.loads(git('show',':'+prefix+'COMPLETE.json'))
        for name,expected in marker['hashes'].items():
            assert sha(git('show',':'+prefix+name))==expected;unit_files+=1
    frozen=json.loads(git('show',':smart_building_conformal/configs/operational_amendment004.json'))
    assert sha(git('show',':OPERATIONAL_EVALUATION_PLAN.md'))==frozen['operational_plan_sha256']
    assert sha(git('show',':smart_building_conformal/protocols/amendment004/AMENDMENT004.md'))==frozen['readable_amendment_sha256']
    output=ROOT/HERE/'EVIDENCE_MANIFEST.csv'
    with output.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['path','bytes','git_blob','sha256','purpose']);writer.writeheader();writer.writerows(rows)
    result=dict(status='passed',entry_commit=BASE,evaluated_commit='917d6eb2d634a457f3fba0fc16133463fe05b9b4',
        branch=git('branch','--show-current').decode().strip(),manifest_files=len(rows),manifest_bytes=sum(x['bytes'] for x in rows),
        largest_file=max(rows,key=lambda x:x['bytes']),internal_links_checked=links,source_archives_verified=sources,
        checkpoint_files_verified=unit_files,publication_scope_checked=True,key_pattern_scan_passed=True,
        excluded_self_hashes=sorted(EXCLUDED),raw_data_published=False,global_study_ready=False)
    (ROOT/HERE/'publication_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    assert all(p.exists() for p in pending_links)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
