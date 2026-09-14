"""Pin the cleanup import repair without changing any scientific output."""
from common import *
import zipfile
from src.unit_checkpoint import source_digest
from src.matched_intervals005 import check_protocol


def main():
    path=REVIEW/'VALIDATION_ERRATUM_V5.json';assert not path.exists()
    audit=read(REVIEW/'VALIDATION_ERRATUM_V4.json')
    audit.update(revision=5,validator_source_hash=source_digest(),validator_files={p.relative_to(SMART/'src').as_posix():sha(p) for p in sorted((SMART/'src').rglob('*.py'))},preceding_erratum_sha256=sha(REVIEW/'VALIDATION_ERRATUM_V4.json'),reason=audit['reason']+' Add missing gc import for between-horizon cleanup.',utc=now())
    atomic(path,audit);check_protocol(DESIGN/'frozen_protocol.json',path)
    recovery=read(REVIEW/'VALIDATION_RECOVERY_COMMANDS_V4.json')
    for action,argv in recovery['commands'].items():
        argv[argv.index('--audit-manifest')+1]=str(path)
        if action=='validate':
            argv[argv.index('--measurement')+1]=str(BATCH/'validate_worker_resources_v5.json')
            argv[argv.index('--receipt')+1]=str(BATCH/'validation_v5')
    recovery.update(source_hash=source_digest(),audit_manifest_sha256=sha(path),audit_manifest=str(path),validation_task='pilot/validate_v5',validation_directory=str(BATCH/'validation_v5'),regression_receipt=str(SMART/'outputs/matched_intervals005/validation_erratum_tests_v4_command.log.json'),resolved_acceptance_checks=49,previous_validation_attempts_preserved=['validation_v1','validation_v2','validation_v3','validation_v4'],utc=now())
    atomic(REVIEW/'VALIDATION_RECOVERY_COMMANDS_V5.json',recovery)
    with zipfile.ZipFile(REVIEW/'corrected_validation_source_v5.zip','x',zipfile.ZIP_DEFLATED) as z:
        for file in sorted((SMART/'src').rglob('*.py')):z.write(file,'src/'+file.relative_to(SMART/'src').as_posix())
    print(json.dumps(dict(source_hash=source_digest(),audit_manifest_sha256=sha(path)),indent=2),flush=True)


if __name__=='__main__':main()
