from common import *
import zipfile,shutil
from src.unit_checkpoint import source_digest


def main():
    path=REVIEW/'VALIDATION_RECOVERY_COMMANDS.json';assert not path.exists()
    audit=REVIEW/'VALIDATION_ERRATUM.json';old=read(REVIEW/'joint_pre_fit_manifest.json')
    commands={}
    for action in ('validate','resume'):
        argv=old['commands'][action].copy()
        if action=='validate':
            argv[argv.index('--measurement')+1]=str(BATCH/'validate_worker_resources_v2.json')
            argv[argv.index('--receipt')+1]=str(BATCH/'validation_v2')
        argv+=['--audit-manifest',str(audit)];commands[action]=argv
    assert not (BATCH/'validation_v2').exists() and not (BATCH/'validate_worker_resources_v2.json').exists()
    test=SMART/'outputs/matched_intervals005/validation_erratum_tests_v1_command.log.json'
    assert read(test)['exit_status']==0
    atomic(path,dict(source_hash=source_digest(),audit_manifest_sha256=sha(audit),commands=commands,regression_receipt=str(test),regression_receipt_sha256=sha(test),resolved_acceptance_checks=46,no_new_fitting=True,failed_validation_preserved=str(BATCH/'validation_v1'),utc=now()))
    changes=['smart_building_conformal/src/'+name for name in ('matched_intervals005.py','intervals005_validate.py','intervals005_owners.py')]
    (REVIEW/'validation_source_erratum.diff').write_bytes(subprocess.check_output(['git','diff','--',*changes],cwd=ROOT))
    with zipfile.ZipFile(REVIEW/'corrected_validation_source.zip','x',zipfile.ZIP_DEFLATED) as z:
        for file in sorted((SMART/'src').rglob('*.py')):z.write(file,'src/'+file.relative_to(SMART/'src').as_posix())
    receipts=REVIEW/'erratum_receipts';receipts.mkdir()
    for file in BACKUP.glob('cqr_diagnosis_v1.log*'):shutil.copyfile(file,receipts/file.name)
    print('Read-only validation recovery commands and source archive frozen.',flush=True)


if __name__=='__main__':main()
