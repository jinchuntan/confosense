"""Hash, archive and check completed review evidence. This command fits no model."""
import csv
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMART = ROOT / 'smart_building_conformal'
REVIEW = Path(__file__).resolve().parent
OUT = SMART / 'outputs/matched_forecasting005'
RUN = OUT / 'pleia_energy_h1_f0_s42_v1'
ENTRY = 'f1a71a19b4e227a9894a8e2c74686a642dca962a'
EVALUATED = '697d0e6e8a7de0a2fc55c98b8341117d789390ce'
MAIN = '06fe967be2be8d7898812c0c2d6e464d4e942351'
EVAL_SOURCE = '7335d436f6e4f8c2144de372e8817d036bae216426c157f5bbdc1eb921927955'
CURRENT_SOURCE = '14b3f329a5bbdc268d5b330cf8a94a045d7de34dd3cee2d4fd0db29659589866'
sys.path.insert(0, str(SMART))
from src.unit_checkpoint import digest, source_digest, UnitCheckpoint
from src.matched_models005 import forbid_fitting
import pandas as pd


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def ledger(paths):
    return [dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size, sha256=digest(p))
            for p in sorted(set(paths))]


def archive(name, paths):
    rows = ledger(paths)
    with zipfile.ZipFile(REVIEW / name, 'w', zipfile.ZIP_DEFLATED) as z:
        for row in rows:
            z.writestr(row['path'], (ROOT / row['path']).read_bytes())
    with zipfile.ZipFile(REVIEW / name) as z:
        for row in rows:
            assert hashlib.sha256(z.read(row['path'])).hexdigest() == row['sha256']
    return rows


def main():
    assert git('branch', '--show-current') == 'review/matched-energy-h1-20260913'
    for parent in [ENTRY, EVALUATED]:
        subprocess.run(['git', 'merge-base', '--is-ancestor', parent, 'HEAD'], cwd=ROOT, check=True)
    assert git('rev-parse', 'main') == git('rev-parse', 'origin/main') == MAIN
    assert git('rev-parse', 'review/support-design-20260913') == ENTRY
    preserved = read(OUT / 'preflight_v2/entry_preservation.json')
    assert preserved['entry_commit'] == ENTRY
    for row in preserved['files']:
        assert digest(ROOT / row['path']) == row['sha256'], row['path']
    statuses = ['PROJECT_RECOVERY_STATUS.md', 'PANEL_RESPONSE_MATRIX.md', 'review/CURRENT_EVIDENCE.md']
    marker = '<!-- matched-energy-h1-20260913: historical content -->'
    for name in statuses:
        old = subprocess.check_output(['git', 'show', f'{ENTRY}:{name}'], cwd=ROOT).decode('utf-8')
        assert (ROOT / name).read_text(encoding='utf-8').split(marker, 1)[1].strip() == old.strip()
    assert source_digest() == CURRENT_SOURCE
    protocol = read(SMART / 'protocols/matched_forecasting005/pleia_energy_h1_f0_s42_v1/frozen_protocol.json')
    assert protocol['source_hash'] == EVAL_SOURCE
    assert digest(REVIEW / 'evaluated_source.zip') == '8e353355ed6bf4b32ffc691463537eef3001f888b036a0a2b87650d06fd32e5a'
    with zipfile.ZipFile(REVIEW / 'evaluated_source.zip') as z:
        names = sorted(z.namelist())
        raw = '\n'.join(f"{name.split('/src/', 1)[1]}:{hashlib.sha256(z.read(name)).hexdigest()}" for name in names)
        assert hashlib.sha256(raw.encode()).hexdigest() == EVAL_SOURCE
    archive_rows = archive('current_source.zip', (SMART / 'src').rglob('*.py'))
    write_csv(REVIEW / 'current_source_manifest.csv', archive_rows)
    scripts = [SMART / 'scripts/check_matched005_preflight.py', SMART / 'scripts/read_matched_energy005.py']
    tests = [SMART / 'tests/test_matched_forecasting005.py', SMART / 'tests/test_matched005_identifier_export.py']
    helper_rows = archive('review_helpers.zip', list(REVIEW.glob('*.py')) + scripts + tests)
    write_csv(REVIEW / 'review_helpers_manifest.csv', helper_rows)

    cp = UnitCheckpoint(RUN, read(RUN / 'checkpoint_manifest.json')['spec'], resume=True)
    for model in ['persistence', 'xgboost', 'attention_lstm']:
        assert cp.verify('pleia_energy_h1_f0_s42_' + model)
    audit = read(OUT / 'energy_h1_audit_v2/validation.json')
    assert audit['passed'] and audit['models_fitted'] == 0 and audit['all_run_files_unchanged']
    for key, expected in [('point_cells', 3), ('interval_cells', 6), ('real_tuning_fits_verified', 8),
                          ('real_final_fits_verified', 2), ('saved_model_prediction_checks', 6)]:
        assert audit[key] == expected
    reloads = pd.read_csv(OUT / 'energy_h1_audit_v2/saved_model_verification.csv')
    assert len(reloads) == 6 and reloads.verified.all() and reloads.max_absolute_difference.eq(0).all()
    mapping = pd.read_csv(OUT / 'energy_h1_audit_v2/identifier_schema_mapping.csv')
    assert mapping.other_columns_unchanged.all() and mapping.original_checkpoint_unchanged.all()
    for row in mapping.itertuples(index=False):
        original = pd.read_csv(RUN / 'units' / row.unit / (row.frame + '.csv.gz'), keep_default_na=False, float_precision='round_trip')
        canonical = pd.read_csv(OUT / 'energy_h1_audit_v2/canonical_streams' / row.unit / (row.frame + '.csv.gz'), keep_default_na=False, float_precision='round_trip')
        assert len(original) == row.rows and original.group_id.eq('').all() and canonical.group_id.eq('None').all()
        pd.testing.assert_frame_equal(original.drop(columns='group_id'), canonical.drop(columns='group_id'), check_exact=True)
    resume_paths = ['energy_h1_resume_v1.json', 'energy_h1_archive_resume_v1.json']
    for name in resume_paths:
        resume = read(OUT / 'validation' / name)
        assert resume['models_fitted'] == 0 and resume['reused_model_units'] == 3
        assert resume['all_run_files_unchanged'] and resume['fresh_data_identity_verified']
    for version in ['v1', 'v2']:
        smoke = read(OUT / f'synthetic_smoke_{version}/smoke_summary.json')
        assert smoke['passed'] and smoke['synthetic_learned_fits'] == 10
    preflight = read(OUT / 'preflight_v2/validation.json')
    assert preflight['passed'] and preflight['models_fitted'] == preflight['historical_pilot_learned_refits'] == 0
    report = read(OUT / 'energy_h1_report_v1/report_validation.json')
    assert report['passed'] and report['completion']['remaining_paired_units'] == 191
    commands = [dict(path=p.relative_to(ROOT).as_posix(), exit_status=read(p)['exit_status'], seconds=read(p)['seconds'])
                for p in sorted(OUT.rglob('*.log.json'))]
    failed = [r for r in commands if r['exit_status'] != 0]
    assert len(failed) == 2 and all(any(s in r['path'] for s in ['published_roles_v1.log.json', 'energy_h1_audit_v1.log.json']) for r in failed), failed
    real_log = read(OUT / 'pleia_energy_h1_f0_s42_v1.log.json')
    assert real_log['exit_status'] == 0

    roots = [ROOT / n for n in statuses + ['.gitattributes', 'PLEIA_ENERGY_MATCHED_H1_REPORT.md']]
    roots += list((SMART / 'src').glob('matched*005.py')) + scripts + tests
    roots += [SMART / 'configs/matched_forecasting005_energy_h1_authorization.json']
    for directory in [REVIEW, OUT, SMART / 'protocols/matched_forecasting005']:
        roots += [p for p in directory.rglob('*') if p.is_file()]
    exclusions = {'EVIDENCE_MANIFEST.csv', 'publication_validation.json'}
    paths = sorted(set(p for p in roots if not (p.parent == REVIEW and p.name in exclusions)))
    assert all(p.stat().st_size < 100 * 2**20 and p.suffix not in ['.pkl', '.pyc'] for p in paths)
    links = 0
    for path in [p for p in paths if p.suffix == '.md']:
        content = path.read_text(encoding='utf-8').split(marker)[0]
        for target in re.findall(r'\]\(([^)]+)\)', content):
            if '://' in target or target.startswith('#'):
                continue
            resolved = (path.parent / target.split('#')[0]).resolve()
            assert resolved.exists() or resolved.parent == REVIEW and resolved.name in exclusions, (path, target)
            links += 1
    manifest = ledger(paths)
    write_csv(REVIEW / 'EVIDENCE_MANIFEST.csv', manifest)
    result = dict(passed=True, models_fitted_by_packaging=0, branch=git('branch', '--show-current'),
                  entry_commit=ENTRY, evaluated_pre_fit_commit=EVALUATED, main_commit=MAIN,
                  instruction_commit='f44d4d1bd784254237bd643b9389fc9ce8c380a3',
                  evaluated_source_hash=EVAL_SOURCE, current_source_hash=CURRENT_SOURCE,
                  future_export_only_repair_invalidates_completed_results=False,
                  preserved_historical_files=len(preserved['files']), historical_status_documents_preserved=statuses,
                  actual_run_exit=0, real_tuning_fits=8, real_final_fits=2, synthetic_learned_fits=20,
                  point_cells_passed=3, interval_cells_passed=6, saved_model_checks=6,
                  maximum_saved_prediction_difference=float(reloads.max_absolute_difference.max()),
                  zero_fit_completed_resumes=2, all_complete_run_files_unchanged=True,
                  canonical_identifier_frames_verified=len(mapping), other_columns_exactly_unchanged=True,
                  successful_command_count=len(commands)-len(failed), preserved_failed_commands=failed,
                  published_role_banks_verified=39, historical_pilot_point_cells=9, historical_pilot_interval_cells=18,
                  historical_pilot_refits=0, local_document_links_checked=links,
                  current_source_files_archived=len(archive_rows), helper_files_archived=len(helper_rows),
                  published_files_in_manifest=len(manifest), manifest_bytes=sum(r['bytes'] for r in manifest),
                  max_file_bytes=max(r['bytes'] for r in manifest), manifest_sha256=digest(REVIEW / 'EVIDENCE_MANIFEST.csv'),
                  manifest_excludes=sorted(exclusions), full_study_ready=False, remaining_queue_launched=False,
                  review_artifacts_ready=True, remote_verification='after final commit; recorded externally and in delivery')
    (REVIEW / 'publication_validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    with forbid_fitting():
        main()
