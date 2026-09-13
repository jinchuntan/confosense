"""Local byte audit; compares history, never modifies datasets or backups."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BASE='3354393290d2afaef4361a9a7a1a43336a14c21d'
SNAPSHOT=Path(r'C:\Users\nigel\ConfoSenseBackups\integration_20260913_102403\snapshot')


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def main():
    entries=[]
    for line in git('ls-tree','-rz',BASE).split(b'\0'):
        if not line:continue
        info,name=line.split(b'\t');name=name.decode()
        if (name.startswith('smart_building_conformal/outputs/model_comparison_pilot_v1/') or
            name.startswith('smart_building_conformal/protocols/model_comparison_pilot_v1/') or
            name=='smart_building_conformal/configs/model_comparison_pilot_v1.json'):
            blob=info.split()[2].decode();raw=(ROOT/name).read_bytes()
            assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob,name
            entries.append(dict(path=name,sha256=hashlib.sha256(raw).hexdigest()))
    changed=git('diff','--name-only',BASE,'--','smart_building_conformal/outputs','smart_building_conformal/data').decode().splitlines()
    assert all('/outputs/amendment004/' in p for p in changed),changed
    historical=[];prior_reports=[]
    for sub in ['smart_building_conformal/data','smart_building_conformal/outputs']:
        for old in (SNAPSHOT/sub).rglob('*'):
            if not old.is_file():continue
            rel=old.relative_to(SNAPSHOT);now=ROOT/rel;assert now.is_file(),str(rel)
            if sha(now)!=sha(old):
                # The prior repair added historical-status notices to these
                # reports. The Git comparison above proves no new changes here.
                assert rel.as_posix().startswith('smart_building_conformal/outputs/final_dissertation_v2/report/')
                assert rel.suffix=='.md'
                prior_reports.append(rel.as_posix())
            else:historical.append(rel.as_posix())
    bundle=Path(r'C:\Users\nigel\ConfoSenseBackups\pilot_followup_20260913\review_3354393290d2.bundle')
    assert sha(bundle)=='2b80a4be8b33fd2762078bd0b5204eb7efe1425bc1e546d50b6ce05aeebaef40'
    assert len(entries)==125 and len(historical)==554 and len(prior_reports)==19
    result=dict(status='passed',baseline_commit=BASE,original_pilot_protocol_config_files_unchanged=len(entries),
        historical_snapshot_files_byte_identical=len(historical),historical_snapshot=str(SNAPSHOT),
        pre_existing_report_annotations_unchanged_since_entry=prior_reports,
        previous_review_bundle_sha256=sha(bundle),previous_review_bundle_unchanged=True,
        original_main=git('rev-parse','main').decode().strip(),
        original_review_branch=git('rev-parse','review/current-dissertation-20260913').decode().strip(),
        pilot_files=entries,historical_files=historical,
        completed_pilot_validity='preserved; amendment affects only future operational runs')
    path=ROOT/'smart_building_conformal/outputs/amendment004/validation/preservation.json'
    assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('pilot_files','historical_files','pre_existing_report_annotations_unchanged_since_entry')},indent=2))


if __name__=='__main__':main()
