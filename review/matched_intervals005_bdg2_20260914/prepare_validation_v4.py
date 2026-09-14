"""Pin the independently diagnosed accumulator correction; no fitting."""
from common import *
import zipfile,shutil
from src.unit_checkpoint import source_digest
from src.matched_intervals005 import check_protocol


def main():
    path=REVIEW/'VALIDATION_ERRATUM_V4.json';assert not path.exists()
    diagnosis=read(REVIEW/'enbpi_bounds_diagnosis.json')
    assert diagnosis['passed'] and all(r['maximum_native_bound_difference']<1e-7 for r in diagnosis['rows'])
    audit=read(REVIEW/'VALIDATION_ERRATUM_V3.json')
    audit.update(revision=4,validator_source_hash=source_digest(),validator_files={p.relative_to(SMART/'src').as_posix():sha(p) for p in sorted((SMART/'src').rglob('*.py'))},preceding_erratum_sha256=sha(REVIEW/'VALIDATION_ERRATUM_V3.json'),enbpi_bounds_diagnosis_sha256=sha(REVIEW/'enbpi_bounds_diagnosis.json'),reason='Native CQR asymmetric reconstruction; native EnbPI float64 OOB accumulator and exact float32 point roundtrip; all outputs/settings/tolerances unchanged.',utc=now())
    atomic(path,audit);check_protocol(DESIGN/'frozen_protocol.json',path)
    recovery=read(REVIEW/'VALIDATION_RECOVERY_COMMANDS_V3.json')
    for action,argv in recovery['commands'].items():
        argv[argv.index('--audit-manifest')+1]=str(path)
        if action=='validate':
            argv[argv.index('--measurement')+1]=str(BATCH/'validate_worker_resources_v4.json')
            argv[argv.index('--receipt')+1]=str(BATCH/'validation_v4')
    recovery.update(source_hash=source_digest(),audit_manifest_sha256=sha(path),audit_manifest=str(path),validation_task='pilot/validate_v4',validation_directory=str(BATCH/'validation_v4'),regression_receipt=str(SMART/'outputs/matched_intervals005/validation_erratum_tests_v3_command.log.json'),resolved_acceptance_checks=48,previous_validation_attempts_preserved=['validation_v1','validation_v2','validation_v3'],utc=now())
    recovery.pop('regression_receipt_sha256',None)
    atomic(REVIEW/'VALIDATION_RECOVERY_COMMANDS_V4.json',recovery)
    with zipfile.ZipFile(REVIEW/'corrected_validation_source_v4.zip','x',zipfile.ZIP_DEFLATED) as z:
        for file in sorted((SMART/'src').rglob('*.py')):z.write(file,'src/'+file.relative_to(SMART/'src').as_posix())
    for file in BACKUP.glob('enbpi_bounds_diagnosis_v1.log*'):shutil.copyfile(file,REVIEW/'erratum_receipts'/file.name)
    print(json.dumps(dict(source_hash=source_digest(),audit_manifest_sha256=sha(path)),indent=2),flush=True)


if __name__=='__main__':main()
