"""Build/check a manifest of staged published bytes and review-document links."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser()
ap.add_argument('--check', action='store_true')
ap.add_argument('--record', default='review/manifest_validation.json')
args = ap.parse_args()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)

paths = git('ls-files', '-z').decode().split('\0')[:-1]
root_files = {'.gitattributes', 'MODEL_COMPARISON_PILOT_REPORT.md', 'PILOT_DIAGNOSTICS.md',
              'OPERATIONAL_EVALUATION_PLAN.md', 'PROJECT_RECOVERY_STATUS.md',
              'PANEL_RESPONSE_MATRIX.md', 'INTEGRATION_REPAIR_REPORT.md'}
prefixes = ['review/', 'smart_building_conformal/src/', 'smart_building_conformal/tests/',
            'smart_building_conformal/scripts/', 'smart_building_conformal/configs/',
            'smart_building_conformal/protocols/model_comparison_pilot_v1/',
            'smart_building_conformal/outputs/model_comparison_pilot_v1/',
            'smart_building_conformal/outputs/pilot_diagnostics_v1/',
            'smart_building_conformal/outputs/integration_repair_20260913/',
            'smart_building_conformal/outputs/final_dissertation_v2/']
exclusions = {'review/EVIDENCE_MANIFEST.csv', 'review/publication_scan_final.json',
              'review/manifest_validation.json'}
selected = sorted(p for p in paths if p not in exclusions and
    (p in root_files or any(p.startswith(prefix) for prefix in prefixes)
     or p.startswith('smart_building_conformal/requirements')))
rows = []
for path in selected:
    data = git('show', ':' + path)
    rows.append(dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                     byte_basis='published_git_blob'))
manifest = root / 'review/EVIDENCE_MANIFEST.csv'
if not args.check:
    with manifest.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['path', 'bytes', 'sha256', 'byte_basis'])
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps(dict(manifest=str(manifest), files=len(rows), bytes=sum(r['bytes'] for r in rows))))
else:
    with manifest.open(encoding='utf-8', newline='') as f:
        expected = list(csv.DictReader(f))
    for item in expected:
        item['bytes'] = int(item['bytes'])
    assert expected == rows, 'Manifest does not match staged published bytes'
    docs = ['review/CURRENT_EVIDENCE.md', 'review/DATA_NOTICE.md', 'review/PUBLICATION_AUDIT.md',
            'PILOT_DIAGNOSTICS.md', 'OPERATIONAL_EVALUATION_PLAN.md']
    count = 0
    missing = []
    for doc in docs:
        for link in re.findall(r'\]\(([^\s)]+)\)', (root / doc).read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'):
                continue
            count += 1
            target = (root / doc).parent / link.split('#')[0]
            # The check's own record is created immediately below.
            if not target.exists() and target.resolve() != (root / args.record).resolve():
                missing.append(dict(document=doc, target=link))
    assert not missing, missing
    result = dict(status='passed', input_head=git('rev-parse', 'HEAD').decode().strip(),
                  byte_basis='staged published Git blobs', files=len(rows),
                  bytes=sum(r['bytes'] for r in rows), relative_links_checked=count,
                  missing_links=missing, excluded_circular_records=sorted(exclusions))
    (root / args.record).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
