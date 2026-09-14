"""Commit and incrementally back up the no-fit validation correction."""
from common import *


def main():
    base=git('rev-parse','HEAD');assert base=='ed2a17220168c5ac78d227c877926b825cc9e773'
    assert git('branch','--show-current')==BRANCH
    assert read(SMART/'outputs/matched_intervals005/validation_erratum_tests_v4_command.log.json')['exit_status']==0
    subprocess.run(['git','add','--',str(REVIEW),str(SMART/'src/intervals005_validate.py'),str(SMART/'outputs/matched_intervals005')],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m','Correct between-horizon validation cleanup import without changing pilot outputs'],cwd=ROOT,check=True)
    commit=git('rev-parse','HEAD');bundle=BACKUP/f'validation_v5_{commit[:7]}.bundle'
    subprocess.run(['git','bundle','create',str(bundle),BRANCH,'^'+base],cwd=ROOT,check=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    result=dict(commit=commit,base_commit=base,validator_source_hash=read(REVIEW/'VALIDATION_ERRATUM_V5.json')['validator_source_hash'],backup=str(bundle),backup_sha256=sha(bundle),requires_verified_base_bundle=str(BACKUP/'validation_v4_ed2a172.bundle'),new_learned_or_calibrator_fits=0)
    atomic(BACKUP/'validation_v5_commit.json',result);print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
