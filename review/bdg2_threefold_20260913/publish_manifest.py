"""Validate staged review scope, source archives and original checkpoint bytes."""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]
BASE='d63251b75f5c70c4d51c19456fbec6724e712516'
HERE='review/bdg2_threefold_20260913/'
EXCLUDED={HERE+'EVIDENCE_MANIFEST.csv',HERE+'publication_validation.json'}


def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()


def main():
    changed=git('diff','--cached','--name-only',BASE).decode().splitlines();rows=[];links=[]
    allowed={'.gitattributes','.gitignore','CHECKPOINT_MEMORY_REPAIR_REPORT.md','BDG2_THREEFOLD_BENCHMARK_REPORT.md',
             'PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md','smart_building_conformal/src/unit_checkpoint.py'}
    prefixes=(HERE,'smart_building_conformal/outputs/amendment004/bdg2_threefold_',
        'smart_building_conformal/outputs/amendment004/bdg2_checkpoint_compatibility_',
        'smart_building_conformal/src/operational004',
        'smart_building_conformal/scripts/verify_checkpoint_compatibility.py',
        'smart_building_conformal/scripts/verify_bdg2_completed_resume.py',
        'smart_building_conformal/scripts/independent_bdg2_operational_audit.py',
        'smart_building_conformal/scripts/freeze_bdg2_threefold.py',
        'smart_building_conformal/scripts/combine_bdg2_threefold.py',
        'smart_building_conformal/scripts/measure_bdg2_threefold.py',
        'smart_building_conformal/scripts/diagnose_bdg2_recovery.py',
        'smart_building_conformal/tests/test_checkpoint_memory.py','smart_building_conformal/tests/test_threefold_')
    pattern=re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{36,}|AKIA[A-Z0-9]{16}')
    for path in changed:
        if path in EXCLUDED:continue
        assert path in allowed or path.startswith(prefixes),path
        data=git('show',':'+path);assert len(data)<100*1024**2,(path,len(data));assert not pattern.search(data),path
        if path.endswith('.md'):
            for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',data.decode('utf-8')):
                if '://' in target or target.startswith('#'):continue
                p=((ROOT/path).parent/target.split('#')[0].strip('<>')).resolve()
                assert p.exists() or p in {ROOT/x for x in EXCLUDED},(path,target)
                links.append(str(p))
        purpose=('completed canonical checkpoint' if '/units/' in path else
            'exact source, execution identity or nested phase measurements' if '_execution/' in path else
            'lossless original CSV bytes' if '_publication_' in path else
            'frozen memberships, catalogues and combined analysis' if '_frozen_' in path else
            'independent validation or measured result' if '/outputs/' in path else 'implementation, report or reproducible helper')
        rows.append(dict(path=path,bytes=len(data),git_blob=git('rev-parse',':'+path).decode().strip(),sha256=sha(data),purpose=purpose))
    base='smart_building_conformal/outputs/amendment004/';archives=0;files_checked=0;split_count=0
    for fold in [1,0]:
        run=base+f'bdg2_threefold_f{fold}_s42_v1';execution=run+'_execution/'
        identity=json.loads(git('show',':'+execution+'prefit_identity.json'))
        with zipfile.ZipFile(io.BytesIO(git('show',':'+execution+'evaluated_source.zip'))) as z:
            lines=[n.removeprefix('src/')+':'+sha(z.read(n)) for n in sorted(z.namelist())]
            assert sha('\n'.join(lines).encode())==identity['spec']['source_hash']
        archives+=1
        complete=json.loads(git('show',':'+run+f'/units/outer{fold}_model42/COMPLETE.json'))
        large=json.loads(git('show',':'+base+f'bdg2_threefold_f{fold}_publication_v1/large_files.json'))
        split={r['repository_path']:r for r in large['files']};split_count+=len(split)
        for name,h in complete['hashes'].items():
            path=run+f'/units/outer{fold}_model42/'+name
            if path in split:
                total=hashlib.sha256();size=0
                for part in split[path]['parts']:
                    data=git('show',':'+part['repository_path'])
                    assert sha(data)==part['sha256'] and len(data)==part['bytes']
                    total.update(data);size+=len(data)
                assert total.hexdigest()==h==split[path]['sha256'] and size==split[path]['bytes']
            else:assert sha(git('show',':'+path))==h,path
            files_checked+=1
    prefix=base+'bdg2_checkpoint_compatibility_v1/'
    record=json.loads(git('show',':'+prefix+'validation.json'))
    with zipfile.ZipFile(io.BytesIO(git('show',':'+prefix+'current_reader_source.zip'))) as z:
        lines=[n.removeprefix('src/')+':'+sha(z.read(n)) for n in sorted(z.namelist())]
        assert sha('\n'.join(lines).encode())==record['current_reader_source_hash']
    archives+=1
    helper_prefix=base+'bdg2_threefold_validation_v1/review_helpers'
    helper_record=json.loads(git('show',':'+helper_prefix+'.json'))
    helper_archive=git('show',':'+helper_prefix+'.zip')
    assert sha(helper_archive)==helper_record['archive_sha256']
    with zipfile.ZipFile(io.BytesIO(helper_archive)) as z:
        for r in helper_record['files']:
            content=z.read(r['repository_path'])
            assert sha(content)==r['sha256'] and len(content)==r['bytes']
    helper_hashes={r['repository_path']:r['sha256'] for r in helper_record['files']}
    for fold,version in [(1,2),(0,1)]:
        audit=json.loads(git('show',':'+base+f'bdg2_threefold_f{fold}_audit_v{version}/validation.json'))
        assert audit['source_sha256']==helper_hashes['smart_building_conformal/scripts/independent_bdg2_operational_audit.py']
    with (ROOT/HERE/'EVIDENCE_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['path','bytes','git_blob','sha256','purpose']);writer.writeheader();writer.writerows(rows)
    result=dict(passed=True,entry_commit=BASE,manifest_files=len(rows),manifest_bytes=sum(r['bytes'] for r in rows),
        largest_file=max(rows,key=lambda r:r['bytes']),local_links_checked=len(links),source_archives_verified=archives,
        completed_unit_files_verified=files_checked,oversized_files_verified_via_lossless_parts=split_count,
        exact_helper_source_files_verified=len(helper_record['files']),
        scope_checked=True,credential_pattern_scan_passed=True,excluded_self_hashes=sorted(EXCLUDED),full_study_ready=False)
    (ROOT/HERE/'publication_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
