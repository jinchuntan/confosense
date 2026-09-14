"""Freeze exact evaluated/current trees for read-only native-CQR validation repair."""
from common import *
from src.intervals005_common import source_digest
from src.intervals005_owners import method_spec
from src.matched_intervals005 import check_protocol


def main():
    path=REVIEW/'VALIDATION_ERRATUM.json'
    assert not path.exists()
    diagnosis=read(REVIEW/'cqr_native_diagnosis.json')
    assert diagnosis['passed'] and all(r['max_bound_difference']==0 for r in diagnosis['rows'])
    protocol=read(DESIGN/'frozen_protocol.json')
    archive=REVIEW/'evaluated_source.zip'
    files={p.relative_to(SMART/'src').as_posix():sha(p) for p in sorted((SMART/'src').rglob('*.py'))}
    atomic(path,dict(version='cqr_native_validation_erratum_v2',completed_readonly_only=True,evaluated_source_hash=protocol['source_hash'],validator_source_hash=source_digest(),protocol_sha256=sha(DESIGN/'frozen_protocol.json'),evaluated_archive=archive.relative_to(ROOT).as_posix(),evaluated_archive_sha256=sha(archive),validator_files=files,resolved_method_specification=method_spec(),scientific_run_complete_sha256=sha(RUN/'COMPLETE.json'),diagnosis_sha256=sha(REVIEW/'cqr_native_diagnosis.json'),new_learned_or_calibrator_fits_authorized=False,reason='Installed native CQR defaults to asymmetric tail corrections; preserve all generated bounds and correct only validator/specification description.',utc=now()))
    check_protocol(DESIGN/'frozen_protocol.json',path)
    atomic(REVIEW/'method_specification_resolved_v2.json',method_spec())
    print(json.dumps(dict(evaluated_source_hash=protocol['source_hash'],validator_source_hash=source_digest(),audit_manifest_sha256=sha(path)),indent=2),flush=True)


if __name__=='__main__':main()
