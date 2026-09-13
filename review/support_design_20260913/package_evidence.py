"""Package and check the completed no-fit evidence; never invokes a model runner."""
import csv
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMART = ROOT / 'smart_building_conformal'
REVIEW = Path(__file__).resolve().parent
OUT = SMART / 'outputs/amendment005'
ENTRY = '9b5acb49531ce12706285c3f040310c0ab6053dd'
MAIN = '06fe967be2be8d7898812c0c2d6e464d4e942351'
sys.path.insert(0, str(SMART / 'scripts'))
from support_design005 import digest, no_fitting, source_digest


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def write_csv(path, rows, fields=None):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    assert git('branch', '--show-current') == 'review/support-design-20260913'
    subprocess.run(['git', 'merge-base', '--is-ancestor', ENTRY, 'HEAD'], cwd=ROOT, check=True)
    assert git('rev-parse', 'main') == git('rev-parse', 'origin/main') == MAIN
    preservation = json.loads((OUT / 'support_design_v1/entry_preservation.json').read_text())
    for row in preservation['files']:
        assert digest(SMART / row['path']) == row['sha256'], row['path']
    assert source_digest() == '203f3babf66c98ac072ad450abec5ea7ce3d60473f02708fa64ac2102ea3f7c9'
    generated = json.loads((OUT / 'support_design_v1/validation.json').read_text())
    for row in generated['input_caches']:
        assert digest(row['path']) == row['sha256']
    assert digest(OUT / 'support_design_v1/proposal_spec.json') == generated['proposal_spec_hash']
    assert digest(SMART / 'outputs/amendment004/preflight_20260913_v1/summary.json') == generated['published_preflight_hash']
    commands = []
    for path in sorted((OUT / 'validation').glob('*.log.json')):
        record = json.loads(path.read_text())
        assert record['exit_status'] == 0
        commands.append(dict(log=path.relative_to(ROOT).as_posix(),
                             command=json.dumps(record['command']), started_utc=record['started_utc'],
                             ended_utc=record['ended_utc'], seconds=record['seconds'],
                             exit_status=record['exit_status'], models_fitted=0))
    write_csv(REVIEW / 'command_measurements.csv', commands)
    for folder in ['support_design_v1', 'independent_verification_v1', 'study_plan_v1',
                   'plan_check_v1', 'support_final_checks_v1']:
        record = json.loads((OUT / folder / 'validation.json').read_text())
        assert record['passed'] and record['models_fitted'] == 0
    environment = dict(python=sys.version, executable=sys.executable,
                       versions={p: importlib.metadata.version(p) for p in
                                 ['numpy', 'pandas', 'scipy', 'scikit-learn', 'xgboost', 'torch', 'mapie', 'pytest']})
    (REVIEW / 'environment.json').write_text(json.dumps(environment, indent=2) + '\n', encoding='utf-8')

    # Preserve exact pre-cleanup command sources, including both reporting-reader stages.
    original_archives = [('generator_original_source.zip', generated['script_hash']),
                         ('generator_bank_reader_source.zip',
                          '6a9bd16a694dc502b330b093fc584b65e19c7b31553fc970047a78ea537c6ef4')]
    for name, expected in original_archives:
        with zipfile.ZipFile(OUT / 'validation' / name) as archive:
            assert hashlib.sha256(archive.read('smart_building_conformal/scripts/support_design005.py')).hexdigest() == expected
    scripts = ['support_design005.py', 'verify_support_design005.py', 'check_remaining_study005.py', 'finalize_support005.py']
    source_paths = sorted(set(list((SMART / 'src').rglob('*.py')) +
                              [SMART / 'scripts' / name for name in scripts] +
                              [SMART / 'tests/test_support_design005.py'] + list(REVIEW.glob('*.py'))))
    archive_rows = []
    with zipfile.ZipFile(REVIEW / 'source_archive.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in source_paths:
            rel = path.relative_to(ROOT).as_posix()
            archive.write(path, rel)
            archive_rows.append(dict(path=rel, bytes=path.stat().st_size, sha256=digest(path)))
    write_csv(REVIEW / 'source_archive_manifest.csv', archive_rows)

    roots = ['SUPPORT_DESIGN_AUDIT.md', 'AMENDMENT005_PROPOSAL.md', 'REMAINING_STUDY_EXECUTION_PLAN.md',
             'PROJECT_RECOVERY_STATUS.md', 'PANEL_RESPONSE_MATRIX.md', 'review/CURRENT_EVIDENCE.md', '.gitattributes']
    files = sorted(set([ROOT / name for name in roots] + [p for p in OUT.rglob('*') if p.is_file()] +
                       [p for p in REVIEW.rglob('*') if p.is_file()] +
                       [SMART / 'scripts' / name for name in scripts] + [SMART / 'tests/test_support_design005.py']))
    files = [p for p in files if p.name not in ['EVIDENCE_MANIFEST.csv', 'publication_validation.json']]
    assert all(p.stat().st_size < 100 * 2**20 and p.suffix not in ['.pkl', '.pyc'] for p in files)
    # Check new prose and preserved historical content separately.
    history_checked = []
    for name in ['PROJECT_RECOVERY_STATUS.md', 'PANEL_RESPONSE_MATRIX.md', 'review/CURRENT_EVIDENCE.md']:
        old = subprocess.check_output(['git', 'show', f'{ENTRY}:{name}'], cwd=ROOT).decode('utf-8')
        now = (ROOT / name).read_text(encoding='utf-8').split('<!-- support-design-20260913: historical content -->', 1)[1]
        assert now.strip() == old.strip()
        history_checked.append(name)
    links = 0
    future_outputs = {'EVIDENCE_MANIFEST.csv', 'publication_validation.json'}
    for path in [p for p in files if p.suffix == '.md']:
        content = path.read_text(encoding='utf-8').split('<!-- support-design-20260913: historical content -->')[0]
        for target in re.findall(r'\]\(([^)]+)\)', content):
            if '://' in target or target.startswith('#'):
                continue
            target = target.split('#')[0]
            resolved = (path.parent / target).resolve()
            assert resolved.exists() or resolved.parent == REVIEW and resolved.name in future_outputs, (path.name, target)
            links += 1
    manifest = [dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size, sha256=digest(p)) for p in files]
    write_csv(REVIEW / 'EVIDENCE_MANIFEST.csv', manifest)
    result = dict(passed=True, entry_commit=ENTRY, branch=git('branch', '--show-current'), main_commit=MAIN,
                  instruction_commit='46d057cba3e56386b5d3e0f277ecf003851d9536',
                  production_source_sha256=source_digest(), preserved_files=len(preservation['files']),
                  preserved_input_caches=4, historical_status_documents_preserved=history_checked,
                  no_fit_commands=len(commands), command_exits=[r['exit_status'] for r in commands], models_fitted=0,
                  local_document_links_checked=links, source_files_archived=len(archive_rows),
                  published_files_in_manifest=len(manifest), manifest_bytes=sum(r['bytes'] for r in manifest),
                  max_file_bytes=max(r['bytes'] for r in manifest),
                  manifest_sha256=digest(REVIEW / 'EVIDENCE_MANIFEST.csv'),
                  manifest_excludes=['EVIDENCE_MANIFEST.csv', 'publication_validation.json'],
                  source_archive_sha256=digest(REVIEW / 'source_archive.zip'),
                  no_new_performance_results=True, full_study_ready=False, publication_ready=False,
                  review_artifacts_ready=True, remote_verification='performed after commit; recorded externally and in delivery')
    (REVIEW / 'publication_validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    with no_fitting():
        main()
