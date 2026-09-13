"""Read-only entry-file, completed-unit, source and Git-lineage preservation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'smart_building_conformal/outputs/amendment004'


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def main(out):
    entry=json.loads((BASE/'bdg2_threefold_validation_v1/entry_preservation.json').read_text())
    for path,h in entry['files'].items():assert sha(ROOT/path)==h,path
    assert git('rev-parse','main')==entry['main']
    assert git('rev-parse','review/bdg2-operational-pilot-20260913')==entry['entry_commit']
    subprocess.run(['git','merge-base','--is-ancestor',entry['entry_commit'],'HEAD'],cwd=ROOT,check=True)
    source=ROOT/'smart_building_conformal/src'
    source_hash=hashlib.sha256('\n'.join(f'{p.relative_to(source).as_posix()}:{sha(p)}' for p in sorted(source.rglob('*.py'))).encode()).hexdigest()
    planpath=BASE/'bdg2_threefold_frozen_v2/execution_analysis_manifest.json'
    plan=json.loads(planpath.read_text());assert source_hash==plan['source_hash']
    units=[]
    for fold in [2,1,0]:
        run=ROOT/'smart_building_conformal'/plan['units'][str(fold)]['out']
        spec=json.loads((run/'checkpoint_manifest.json').read_text())['spec']
        unit=run/f'units/outer{fold}_model42';marker=json.loads((unit/'COMPLETE.json').read_text())
        for name,h in marker['hashes'].items():assert sha(unit/name)==h,(fold,name)
        assert spec['candidate_grid']==plan['candidate_grid'] and spec['config_hash']==plan['config_hash']
        assert spec['data_hash']==plan['data_hash'] and spec['outcomes_hash']==plan['outcomes_hash']
        if fold!=2:
            assert spec['source_hash']==source_hash and spec['execution_manifest_hash']==sha(planpath)
            identity=json.loads((Path(str(run)+'_execution')/'prefit_identity.json').read_text())
            assert identity['git_commit']=='18e5db5f2d81ed641ae90c5e257e512cf7ebbcc7'
        with zipfile.ZipFile(Path(str(run)+'_execution')/'evaluated_source.zip') as z:
            lines=[n.removeprefix('src/')+':'+hashlib.sha256(z.read(n)).hexdigest() for n in sorted(z.namelist())]
            assert hashlib.sha256('\n'.join(lines).encode()).hexdigest()==spec['source_hash']
        units.append(dict(outer_fold=fold,files=len(list(unit.iterdir())),source_hash=spec['source_hash'],all_file_hashes_match=True))
    backup=Path('C:/Users/nigel/ConfoSenseBackups/bdg2_operational_pilot_20260913/review_d63251b75f5c.bundle')
    expected='3efea48461e50d72c943de54ed390f3b55358d3504fc08369358bf64be8a627b'
    assert sha(backup)==expected
    record=dict(passed=True,learned_fits=0,entry_commit=entry['entry_commit'],current_head=git('rev-parse','HEAD'),
        preserved_entry_files=len(entry['files']),main_unchanged=entry['main'],prior_review_branch_unchanged=True,
        unchanged_scientific_source_hash=source_hash,frozen_manifest_sha256=sha(planpath),units=units,
        prior_backup=dict(path=str(backup),sha256=expected,unchanged=True),full_study_ready=False)
    with Path(out).open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
    print(json.dumps(record,indent=2))


if __name__=='__main__':main(sys.argv[1])
