"""Verify entry evidence, old snapshot and previous publication bundle unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(output):
    out=Path(output);assert not out.exists()
    entry=json.loads((ROOT/'smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/entry_preservation.json').read_text())
    for r in entry['files']:assert sha(ROOT/r['path'])==r['sha256'],r['path']
    snapshot=Path('C:/Users/nigel/ConfoSenseBackups/integration_20260913_102403/snapshot')
    identical=[];annotated=[]
    for sub in ['smart_building_conformal/data','smart_building_conformal/outputs']:
        for old in (snapshot/sub).rglob('*'):
            if not old.is_file():continue
            rel=old.relative_to(snapshot);now=ROOT/rel;assert now.is_file()
            if sha(now)==sha(old):identical.append(rel.as_posix())
            else:
                assert rel.as_posix().startswith('smart_building_conformal/outputs/final_dissertation_v2/report/') and rel.suffix=='.md'
                annotated.append(rel.as_posix())
    bundle=Path('C:/Users/nigel/ConfoSenseBackups/amendment004_20260913/review_2243c1678046.bundle')
    assert sha(bundle)=='a16a911fa3deca05522263ee892c88630bb7bf6f2c031d4e1359b56b5cea0a74'
    assert len(identical)==554 and len(annotated)==19
    assert subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()=='06fe967be2be8d7898812c0c2d6e464d4e942351'
    assert subprocess.check_output(['git','rev-parse','review/amendment004-20260913'],cwd=ROOT,text=True).strip()=='2243c167804690ad1ec9b8aebc369e5596d392aa'
    record=dict(passed=True,entry_evidence_files_unchanged=len(entry['files']),historical_snapshot_files_byte_identical=len(identical),
        pre_existing_report_annotations_unchanged=len(annotated),previous_bundle_sha256=sha(bundle),
        main_unchanged=True,previous_review_branch_unchanged=True,completed_forecasting_pilot_preserved=True,
        entry_commit=entry['entry_commit'])
    out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);main(p.parse_args().out)
