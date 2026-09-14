"""Refresh the publication manifest from canonical staged Git blobs."""
import csv,hashlib,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REVIEW=Path(__file__).resolve().parent
MANIFEST=REVIEW/'EVIDENCE_MANIFEST.csv'

def main():
    prior=[row['path'] for row in csv.DictReader(MANIFEST.open(encoding='utf-8'))]
    review_files=[p.relative_to(ROOT).as_posix() for p in REVIEW.rglob('*')
                  if p.is_file() and p!=MANIFEST and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.tmp'}]
    paths=sorted(set(prior+review_files))
    subprocess.run(['git','add',*[str(p.relative_to(ROOT)) for p in REVIEW.rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.tmp'}]],cwd=ROOT,check=True)
    rows=[]
    for path in paths:
        blob=subprocess.check_output(['git','show',':'+path],cwd=ROOT)
        if len(blob)>=100*2**20:raise ValueError('GitHub file limit: '+path)
        rows.append(dict(path=path,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest()))
    with MANIFEST.open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['path','bytes','sha256']);writer.writeheader();writer.writerows(rows)
    subprocess.run(['git','add',str(MANIFEST.relative_to(ROOT))],cwd=ROOT,check=True)
    print(f'CANONICAL INDEX-BLOB MANIFEST REFRESHED: {len(rows)} files')

if __name__=='__main__':main()
