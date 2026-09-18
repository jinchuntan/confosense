"""Seal, back up, push and independently verify the temperature pilot evidence.

Two stages produce two distinct commits:
  --stage primary   : the primary-results commit (evidence + analysis + archives)
  --stage delivery  : the final-delivery commit (settled receipt referring to primary)

Publication uses an EXPLICIT allowlist. This review directory was seeded by
copying the energy batch, so 37 byte-identical energy files sit beside the
temperature work; none of them may be republished as temperature evidence.

GitHub verification downloads bytes over HTTPS from raw.githubusercontent.com
pinned to the commit SHA. ``git show origin/...`` is NOT accepted as evidence of
a GitHub download.
"""
from __future__ import annotations

import argparse
import csv as csv_module
import hashlib
import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import common
from common import REPO, REVIEW, SMART, KEY, BRANCH, MAIN, BACKUP, read, digest, source_digest, now, atomic

RAW = 'https://raw.githubusercontent.com/jinchuntan/confosense/{sha}/{path}'
API = 'https://api.github.com/repos/jinchuntan/confosense/commits/{sha}'
ANALYSIS = common.BASE / (KEY + '_analysis')
PUBLICATION = common.publication()
ENTRY = 'c143fa16eaf9bfc6354b4cb1f8861915cb00f388'

# Byte-identical energy copies that live in this directory; never published here.
ENERGY_COPIES = {
    'analyze.py', 'AUTHORIZING_HANDOFF_REFERENCE.md', 'COMPLETION_VERIFICATION.json',
    'coordinator.stderr.log', 'coordinator.stdout.log', 'DELIVERY_READBACK_RECEIPT.json',
    'EVALUATED_COMMIT.json', 'EVIDENCE_INDEX.md', 'EVIDENCE_MANIFEST.csv',
    'FINAL_ANALYSIS_RECOVERY.md', 'FROZEN_BATCH_MANIFEST.json', 'GITHUB_REMOTE_READBACK.json',
    'pack_evidence.py', 'PANEL_RESPONSE.md', 'PLEIA_ENERGY_CONTEXT005_MULTISEED_REPORT.md',
    'pleia_energy_f2_s43_C_v1_execution_manifest.json', 'pleia_energy_f2_s44_C_v1_execution_manifest.json',
    'pleia_energy_f2_s45_C_v1_execution_manifest.json', 'pleia_energy_f2_s46_C_v1_execution_manifest.json',
    'preflight.py', 'PREFLIGHT_VALIDATION.json', 'prepare.py', 'PRESERVATION_BASELINE.json',
    'PROGRESS_AND_RESTART.md', 'PUBLICATION_RECEIPT.json', 'publish.py', 'RAW_PACKAGE_RECOVERY.md',
    'RAW_PACKAGE_VALIDATION.json', 'recovery.py', 'recovery_coordinator.stderr.log',
    'recovery_coordinator.stdout.log', 'RECOVERY_STATUS.md', 'REMAINING_WORK.md', 'seal_freeze.py',
    'update_documents.py', 'validate_aggregate.py',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def download(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'confosense-delivery-verification'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read(), r.status


def check_preservation():
    if git('branch', '--show-current') != BRANCH:
        raise ValueError('not on the temperature review branch')
    if git('rev-parse', 'main') != MAIN:
        raise ValueError('main moved')
    base = read(REVIEW / 'TEMPERATURE_PRESERVATION_BASELINE.json')
    for ref, value in base['prior_heads'].items():
        if ref == f'refs/heads/{BRANCH}':
            continue
        if git('rev-parse', ref) != value:
            raise ValueError('prior review head moved: ' + ref)
    if source_digest() != common.SOURCE_HASH:
        raise ValueError('source drift since the frozen design')
    return base


def allowlist():
    """Exactly the temperature artifacts, never the copied energy files."""
    files = set()
    for p in REVIEW.iterdir():
        if not p.is_file() or p.name in ENERGY_COPIES:
            continue
        if '__pycache__' in p.parts or p.suffix in ('.pyc', '.tmp'):
            continue
        files.add(p)
    # Frozen design, execution manifest, coordinator records, analysis, archives.
    for root in [common.design(), common.BATCH, ANALYSIS, PUBLICATION, common.validation()]:
        if root.exists():
            files |= {q for q in root.rglob('*') if q.is_file()}
    resume_receipt = common.resume()
    if resume_receipt.exists():
        files.add(resume_receipt)
    # Core scientific records direct; the full many-file tree ships as verified ZIP parts.
    run = common.run()
    files |= {run / 'COMPLETE.json', run / 'operations.jsonl', run / 'checkpoint_manifest.json',
              run / 'stage_journal.jsonl'}
    for stage in ['owner_fit_cqr', 'owner_cal_cqr', 'controls', 'tables']:
        files |= {q for q in (run / 'stages' / stage).rglob('*') if q.is_file()}
    files.add(REPO / 'review/CURRENT_EVIDENCE.md')
    return sorted(q for q in files
                  if q.is_file() and '__pycache__' not in q.parts and q.suffix not in ('.pyc', '.tmp'))


def stage_and_commit(message, label):
    files = allowlist()
    rels = [q.relative_to(REPO).as_posix() for q in files]
    BACKUP.mkdir(parents=True, exist_ok=True)
    pathfile = BACKUP / (label + '_paths.txt')
    pathfile.write_text('\n'.join(rels) + '\n', encoding='utf-8')
    subprocess.run(['git', 'add', '--pathspec-from-file=' + str(pathfile)], cwd=REPO, check=True)
    rows = []
    for rel in rels:
        blob = subprocess.check_output(['git', 'show', ':' + rel], cwd=REPO)
        if len(blob) >= 100 * 2 ** 20:
            raise ValueError('blob exceeds GitHub limit: ' + rel)
        rows.append(dict(path=rel, bytes=len(blob), sha256=sha_bytes(blob)))
    manifest_path = REVIEW / 'TEMPERATURE_EVIDENCE_MANIFEST.csv'
    with manifest_path.open('w', encoding='utf-8', newline='') as f:
        w = csv_module.DictWriter(f, fieldnames=['path', 'bytes', 'sha256'])
        w.writeheader()
        w.writerows(rows)
    subprocess.run(['git', 'add', str(manifest_path.relative_to(REPO))], cwd=REPO, check=True)
    # Whitespace gate. A preserved artifact from the superseded coordinator ends with a
    # blank line; that file must not be edited, so only that class is tolerated and it is
    # reported. Any other whitespace error still fails the publication.
    check = subprocess.run(['git', 'diff', '--cached', '--check'], cwd=REPO,
                           capture_output=True, text=True)
    whitespace_notes = []
    if check.returncode:
        for line in check.stdout.splitlines():
            if line.strip():
                whitespace_notes.append(line)
        hard = [l for l in whitespace_notes if 'new blank line at EOF' not in l]
        if hard:
            raise ValueError('whitespace errors block publication: ' + ' | '.join(hard))
    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=REPO).returncode:
        subprocess.run(['git', 'commit', '-m', message], cwd=REPO, check=True)
    return git('rev-parse', 'HEAD'), rows, whitespace_notes


def backup_and_push(label, head):
    bundle = BACKUP / (label + '_' + head[:8] + '.bundle')
    if not bundle.exists():
        subprocess.run(['git', 'bundle', 'create', str(bundle), BRANCH, '^' + ENTRY], cwd=REPO, check=True)
    subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=REPO, check=True)
    subprocess.run(['git', 'push', '-u', 'origin', BRANCH], cwd=REPO, check=True)
    subprocess.run(['git', 'fetch', 'origin', BRANCH], cwd=REPO, check=True)
    remote = git('rev-parse', 'origin/' + BRANCH)
    if remote != head:
        raise ValueError(f'remote head mismatch {remote} != {head}')
    return bundle, remote


def github_readback(head, representative):
    """Actual downloaded-byte verification, pinned to the immutable commit SHA."""
    checks = []
    for path in representative:
        rel = path.relative_to(REPO).as_posix()
        local = path.read_bytes()
        url = RAW.format(sha=head, path=urllib.parse.quote(rel))
        data, status = download(url)
        checks.append(dict(path=rel, url=url, http_status=status,
                           local_bytes=len(local), downloaded_bytes=len(data),
                           local_sha256=sha_bytes(local), downloaded_sha256=sha_bytes(data),
                           identical=sha_bytes(local) == sha_bytes(data),
                           method='https_download_from_raw_githubusercontent_pinned_to_commit'))
    api, api_status = download(API.format(sha=head))
    commit = json.loads(api)
    bad = [c for c in checks if not c['identical']]
    if bad:
        raise ValueError('GitHub downloaded bytes differ: ' + json.dumps(bad, indent=2))
    return dict(passed=True, commit=head, api_status=api_status,
                api_commit_sha=commit.get('sha'), downloads=checks,
                note='Byte-for-byte HTTPS downloads from GitHub; not a local remote-tracking read.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['primary', 'delivery'])
    ap.add_argument('--label', required=True)
    a = ap.parse_args()
    base = check_preservation()

    if a.stage == 'primary':
        run = common.run()
        if read(run / 'COMPLETE.json')['actual_exit_status'] != 0:
            raise ValueError('run has no clean recorded exit')
        survey = common.BATCH / 'validation_survey/VALIDATION_SURVEY.json'
        corrected = common.BATCH / 'validation_survey/VALIDATION_SURVEY_CORRECTED_READING.json'
        for receipt in [common.resume(), PUBLICATION / 'validation.json',
                        ANALYSIS / 'ANALYSIS_RECORD.json', survey, corrected]:
            if not receipt.exists():
                raise ValueError('missing required receipt: ' + str(receipt))
        # The frozen `validate` action did NOT pass; publication does not pretend it did.
        # The full-extent survey stands in its place and the receipt records that plainly.
        formal = common.validation() / 'validation.json'
        validation_state = dict(
            frozen_validate_passed=bool(formal.exists() and read(formal).get('passed')),
            frozen_validate_status=('passed' if formal.exists() else
                                    'FAILED at attempt 1; preserved, not retried unchanged, '
                                    'no tolerance loosened'),
            survey=read(survey), corrected_reading=read(corrected))
        s = validation_state['survey']
        if s['total_checks'] < 100000:
            raise ValueError('survey did not cover the study')
        r = read(common.resume())
        if not (r['passed'] and r['models_fitted'] == 0 and r['calibrators_fitted'] == 0
                and r['replay_updates'] == 0 and r['scientific_artifacts_unchanged']):
            raise ValueError('completed resume is not a clean zero-fit receipt')
        head, rows, ws = stage_and_commit('Publish PLEIA-temperature context005 seed-42 pilot evidence', a.label)
        bundle, remote = backup_and_push(a.label, head)
        representative = [PUBLICATION / 'parts_manifest.csv',
                          ANALYSIS / 'control_rule_channel_summary.csv',
                          common.validation() / 'validation.json',
                          REVIEW / 'PLEIA_TEMPERATURE_CONTEXT005_PILOT_REPORT.md']
        representative = [p for p in representative if p.exists()]
        readback = github_readback(head, representative)
        receipt = dict(passed=True, stage='primary_results', branch=BRANCH, primary_results_commit=head,
                       remote_commit=remote, url=f'https://github.com/jinchuntan/confosense/tree/{head}',
                       backup=str(bundle), backup_bytes=bundle.stat().st_size, backup_sha256=digest(bundle),
                       evidence_files=len(rows), evidence_bytes=sum(r['bytes'] for r in rows),
                       github_readback=readback, validation=validation_state, tolerated_whitespace_notes=ws,
                       main_unchanged=git('rev-parse', 'main') == MAIN, utc=now())
        atomic(REVIEW / 'TEMPERATURE_PUBLICATION_RECEIPT.json', receipt)
        atomic(BACKUP / (a.label + '_publication_receipt.json'), receipt)
        print(json.dumps(receipt, indent=2))
    else:
        pub = read(REVIEW / 'TEMPERATURE_PUBLICATION_RECEIPT.json')
        head, rows, ws = stage_and_commit('Record PLEIA-temperature context005 pilot final delivery', a.label)
        bundle, remote = backup_and_push(a.label, head)
        representative = [REVIEW / 'TEMPERATURE_DELIVERY_READBACK_RECEIPT.json',
                          REVIEW / 'TEMPERATURE_EVIDENCE_INDEX.md']
        representative = [p for p in representative if p.exists()]
        readback = github_readback(head, representative)
        receipt = dict(passed=True, stage='final_delivery', branch=BRANCH,
                       primary_results_commit=pub['primary_results_commit'],
                       final_delivery_commit=head, remote_commit=remote,
                       url=f'https://github.com/jinchuntan/confosense/tree/{head}',
                       backup=str(bundle), backup_sha256=digest(bundle),
                       github_readback=readback, main_unchanged=git('rev-parse', 'main') == MAIN,
                       note='This receipt describes checks performed up to and including the primary '
                            'results commit and this delivery commit push/readback. It does not assert '
                            'verification of any later commit.', utc=now())
        atomic(REVIEW / 'TEMPERATURE_FINAL_DELIVERY_RECEIPT.json', receipt)
        atomic(BACKUP / (a.label + '_final_delivery_receipt.json'), receipt)
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
