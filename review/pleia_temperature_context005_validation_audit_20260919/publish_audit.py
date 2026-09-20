"""Publish the validation audit on its own review branch, with real GitHub readback.

Preserves main, the delivered pilot branch and every prior review head. Uses an
explicit allowlist. Verification downloads bytes over HTTPS from
raw.githubusercontent.com pinned to the commit and compares them against the
committed git blob; a local `git show origin/...` is not accepted as evidence.
"""
from __future__ import annotations

import argparse
import csv as csv_module
import hashlib
import json
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import audit_common as A

RAW = 'https://raw.githubusercontent.com/jinchuntan/confosense/{sha}/{path}'
API = 'https://api.github.com/repos/jinchuntan/confosense/commits/{sha}'
ENTRY = 'c143fa16eaf9bfc6354b4cb1f8861915cb00f388'
RECEIPT = A.AUDIT_REVIEW / 'AUDIT_DELIVERY_RECEIPT.json'


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def download(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'confosense-audit-verification'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read(), r.status


def preservation():
    heads = {}
    for line in A.git('for-each-ref', '--format=%(refname) %(objectname)', 'refs/heads').splitlines():
        r, o = line.split()
        heads[r] = o
    return heads


def allowlist():
    files = set()
    for p in A.AUDIT_REVIEW.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.tmp'):
            files.add(p)
    for p in A.OUT.rglob('*'):
        if p.is_file() and p.suffix not in ('.pyc', '.tmp'):
            files.add(p)
    files.add(A.COORD / 'AUDIT_GITHUB_READBACK.json')
    files.add(A.PILOT_REVIEW / 'PLEIA_TEMPERATURE_CONTEXT005_PILOT_REPORT.md')
    return sorted(files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', required=True)
    a = ap.parse_args()

    if A.git('branch', '--show-current') != A.AUDIT_BRANCH:
        raise ValueError('not on the audit branch')
    if A.git('rev-parse', 'main') != A.MAIN:
        raise ValueError('main moved')
    if A.git('rev-parse', A.PILOT_BRANCH) != A.DELIVERY:
        raise ValueError('delivered pilot branch moved')
    before_heads = preservation()

    files = allowlist()
    rels = [f.relative_to(A.REPO).as_posix() for f in files]
    A.BACKUP.mkdir(parents=True, exist_ok=True)
    pathfile = A.BACKUP / (a.label + '_paths.txt')
    pathfile.write_text('\n'.join(rels) + '\n', encoding='utf-8')
    subprocess.run(['git', 'add', '--pathspec-from-file=' + str(pathfile)], cwd=A.REPO, check=True)

    rows = []
    for rel in rels:
        blob = subprocess.check_output(['git', 'show', ':' + rel], cwd=A.REPO)
        if len(blob) >= 100 * 2 ** 20:
            raise ValueError('blob exceeds GitHub limit: ' + rel)
        rows.append(dict(path=rel, bytes=len(blob), sha256=sha_bytes(blob)))
    manifest = A.AUDIT_REVIEW / 'AUDIT_EVIDENCE_MANIFEST.csv'
    with manifest.open('w', encoding='utf-8', newline='') as f:
        wr = csv_module.DictWriter(f, fieldnames=['path', 'bytes', 'sha256'])
        wr.writeheader()
        wr.writerows(rows)
    subprocess.run(['git', 'add', str(manifest.relative_to(A.REPO))], cwd=A.REPO, check=True)

    check = subprocess.run(['git', 'diff', '--cached', '--check'], cwd=A.REPO,
                           capture_output=True, text=True)
    notes = [l for l in check.stdout.splitlines() if l.strip()] if check.returncode else []
    hard = [l for l in notes if 'new blank line at EOF' not in l]
    if hard:
        raise ValueError('whitespace errors block publication: ' + ' | '.join(hard))

    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=A.REPO).returncode:
        subprocess.run(['git', 'commit', '-m',
                        'Publish PLEIA-temperature context005 validation audit'], cwd=A.REPO, check=True)
    head = A.git('rev-parse', 'HEAD')

    bundle = A.BACKUP / (a.label + '_' + head[:8] + '.bundle')
    if not bundle.exists():
        subprocess.run(['git', 'bundle', 'create', str(bundle), A.AUDIT_BRANCH, '^' + ENTRY],
                       cwd=A.REPO, check=True)
    subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=A.REPO, check=True)

    subprocess.run(['git', 'push', '-u', 'origin', A.AUDIT_BRANCH], cwd=A.REPO, check=True)
    subprocess.run(['git', 'fetch', 'origin', A.AUDIT_BRANCH], cwd=A.REPO, check=True)
    remote = A.git('rev-parse', 'origin/' + A.AUDIT_BRANCH)
    if remote != head:
        raise ValueError(f'remote head mismatch {remote} != {head}')

    representative = [A.AUDIT_REVIEW / 'VALIDATION_AUDIT_REPORT.md',
                      A.AUDIT_REVIEW / 'CANDIDATE_VALIDATION_CONTRACT.md',
                      A.AUDIT_REVIEW / 'REPORT_CORRECTIONS.md',
                      A.OUT / 'candidate_v1/CANDIDATE_VALIDATION.json',
                      A.OUT / 'MECHANISM_PROOF.json',
                      A.PILOT_REVIEW / 'PLEIA_TEMPERATURE_CONTEXT005_PILOT_REPORT.md']
    checks = []
    for path in [p for p in representative if p.exists()]:
        rel = path.relative_to(A.REPO).as_posix()
        blob = subprocess.check_output(['git', 'cat-file', 'blob', f'{head}:{rel}'], cwd=A.REPO)
        data, status = download(RAW.format(sha=head, path=urllib.parse.quote(rel)))
        checks.append(dict(path=rel, http_status=status, committed_blob_bytes=len(blob),
                           downloaded_bytes=len(data), committed_blob_sha256=sha_bytes(blob),
                           downloaded_sha256=sha_bytes(data), identical=sha_bytes(blob) == sha_bytes(data)))
    bad = [c for c in checks if not c['identical']]
    if bad:
        raise ValueError('GitHub downloaded bytes differ: ' + json.dumps(bad, indent=2))
    api, api_status = download(API.format(sha=head))

    # external backup of the audit evidence
    dest = A.BACKUP / 'audit_evidence'
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for src in [p for p in representative if p.exists()] + [
            A.OUT / 'contract_tests/CONTRACT_TESTS.json', A.OUT / 'LATTICE_EVIDENCE.json',
            A.OUT / 'SURVEY_COVERAGE_AUDIT.json', A.OUT / 'COUNT_RECONCILIATION.json',
            A.OUT / 'POST_AUDIT_INTEGRITY.json', A.AUDIT_REVIEW / 'AUDIT_EVIDENCE_INDEX.md']:
        if not src.exists():
            continue
        tgt = dest / src.name
        shutil.copy2(src, tgt)
        ok = sha_bytes(src.read_bytes()) == sha_bytes(tgt.read_bytes())
        copied.append(dict(name=src.name, bytes=tgt.stat().st_size, verified=ok))
        if not ok:
            raise ValueError('backup copy mismatch: ' + src.name)

    after_heads = preservation()
    moved = [r for r, o in before_heads.items() if r != f'refs/heads/{A.AUDIT_BRANCH}'
             and after_heads.get(r) != o]

    receipt = dict(
        purpose='validation_audit_delivery', branch=A.AUDIT_BRANCH, audit_commit=head,
        remote_commit=remote, url=f'https://github.com/jinchuntan/confosense/tree/{head}',
        pilot_branch=A.PILOT_BRANCH, pilot_primary=A.PRIMARY, pilot_final_delivery=A.DELIVERY,
        main=A.MAIN, main_unchanged=A.git('rev-parse', 'main') == A.MAIN,
        pilot_branch_unchanged=A.git('rev-parse', A.PILOT_BRANCH) == A.DELIVERY,
        prior_heads_moved=moved, evidence_files=len(rows),
        evidence_bytes=sum(r['bytes'] for r in rows),
        github_readback=dict(passed=True, api_status=api_status,
                             api_commit_sha=json.loads(api).get('sha'), downloads=checks,
                             method='https download from raw.githubusercontent.com pinned to commit, '
                                    'compared against git cat-file blob'),
        backup=dict(bundle=str(bundle), bundle_bytes=bundle.stat().st_size,
                    bundle_sha256=sha_bytes(bundle.read_bytes()) if bundle.stat().st_size < 2**31 else None,
                    evidence_directory=str(dest), evidence_files=len(copied),
                    all_verified=all(c['verified'] for c in copied)),
        tolerated_whitespace_notes=notes,
        acceptance_status='execution and publication complete; scientific acceptance pending validation',
        candidate_adopted=False)
    RECEIPT.write_text(json.dumps(receipt, indent=2, default=str), encoding='utf-8')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'github_readback'}, indent=2, default=str))
    print('readback:', json.dumps([{c['path'].split('/')[-1]: c['identical']} for c in checks]))


if __name__ == '__main__':
    main()
