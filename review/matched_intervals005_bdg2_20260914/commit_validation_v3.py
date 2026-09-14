"""Commit and incrementally back up the no-fit validation correction."""
from common import *


def main():
    base=git('rev-parse','HEAD');assert base=='1e084ee9f67a9f259a4d3a4d4b3d3ee399017ac8'
    assert git('branch','--show-current')==BRANCH
    assert read(SMART/'outputs/matched_intervals005/validation_erratum_tests_v2_command.log.json')['exit_status']==0
    subprocess.run(['git','add','--',str(REVIEW),str(SMART/'src/intervals005_validate.py'),str(SMART/'outputs/matched_intervals005')],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m','Correct native EnbPI validation accumulator without changing pilot outputs'],cwd=ROOT,check=True)
    commit=git('rev-parse','HEAD');bundle=BACKUP/f'validation_v3_{commit[:7]}.bundle'
    subprocess.run(['git','bundle','create',str(bundle),BRANCH,'^'+base],cwd=ROOT,check=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    result=dict(commit=commit,base_commit=base,validator_source_hash=read(REVIEW/'VALIDATION_ERRATUM_V3.json')['validator_source_hash'],backup=str(bundle),backup_sha256=sha(bundle),requires_verified_base_bundle=str(BACKUP/'validation-erratum_1e084ee.bundle'),new_learned_or_calibrator_fits=0)
    atomic(BACKUP/'validation_v3_commit.json',result);print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
