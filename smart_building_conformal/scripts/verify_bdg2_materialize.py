"""Restore byte-identical oversized checkpoint CSVs from published binary parts.

Small review tables remain directly readable. No dataset download or fitting.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def materialize(manifest):
    records=json.loads(Path(manifest).read_text())
    checked=[]
    for record in records['files']:
        target=(ROOT/record['repository_path']).resolve()
        if not target.is_relative_to(ROOT):raise ValueError('target outside repository')
        if target.exists():
            if target.stat().st_size!=record['bytes'] or sha(target)!=record['sha256']:
                raise ValueError(f'existing file mismatch; never overwrite: {target}')
            checked.append(dict(path=record['repository_path'],status='already_exact'));continue
        parts=[]
        for part in record['parts']:
            p=(ROOT/part['repository_path']).resolve()
            if not p.is_relative_to(ROOT) or sha(p)!=part['sha256'] or p.stat().st_size!=part['bytes']:
                raise ValueError('published part mismatch')
            parts.append(p)
        temp=target.with_name(target.name+'.assembling')
        if temp.exists():raise FileExistsError(temp)
        target.parent.mkdir(parents=True,exist_ok=True)
        with temp.open('xb') as f:
            for p in parts:
                with p.open('rb') as source:
                    for chunk in iter(lambda:source.read(2**20),b''):f.write(chunk)
        if sha(temp)!=record['sha256'] or temp.stat().st_size!=record['bytes']:
            raise ValueError('reassembled file mismatch; preserved partial file')
        temp.rename(target);checked.append(dict(path=record['repository_path'],status='restored_exact'))
    print(json.dumps(dict(passed=True,files=checked),indent=2))
    return checked

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);materialize(p.parse_args().manifest)
