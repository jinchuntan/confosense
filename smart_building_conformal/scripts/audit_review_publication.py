"""Inspect the exact pending Git history, with secret matches reported by path only."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args()
lines=subprocess.check_output(['git','rev-list','--objects','HEAD','--not','--remotes=origin'],text=True).splitlines()
names=dict(line.split(' ',1) if ' ' in line else (line,'') for line in lines)
meta=subprocess.check_output(['git','cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)'],input='\n'.join(names)+'\n',text=True)
patterns={
    'private_key':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'github_token':re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
    'cloud_access_key':re.compile(rb'AKIA[0-9A-Z]{16}'),
    'openai_key':re.compile(rb'sk-(?:proj-)?[A-Za-z0-9_-]{35,}'),
    'assigned_secret':re.compile(rb'''(?i)(?:api[_-]?key|client[_-]?secret|password|access[_-]?token)\s*[:=]\s*["'][A-Za-z0-9_+/=-]{16,}["']'''),
}
records=[];findings=[]
def scan(stream,path):
    tail=b''
    while True:
        block=stream.read(2**20)
        if not block:break
        value=tail+block
        for kind,pattern in patterns.items():
            if pattern.search(value):findings.append(dict(path=path,kind=kind))
        tail=value[-512:]
for line in meta.splitlines():
    sha,kind,size=line.split()
    if kind!='blob':continue
    path=names[sha];size=int(size)
    if size>50*2**20:findings.append(dict(path=path,kind='oversized_blob'))
    if any(part in '/'+path.lower() for part in ['/data/raw/','/data/interim/','/data/processed/','/.venv/','/venv/','/.env','/id_rsa','/id_ed25519']):
        findings.append(dict(path=path,kind='excluded_path'))
    data=subprocess.check_output(['git','cat-file','blob',sha])
    if path.endswith('.gz'):
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:scan(f,path+' (decompressed)')
    elif path.endswith(('.zip','.pt')) and zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for member in z.namelist():
                with z.open(member) as f:scan(f,path+'!'+member)
    else:scan(io.BytesIO(data),path)
    records.append(dict(path=path,git_blob=sha,bytes=size,sha256=hashlib.sha256(data).hexdigest()))
result=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    comparison='HEAD excluding all fetched origin refs; includes reachable unpublished historical blobs',
    blobs=len(records),bytes=sum(r['bytes'] for r in records),findings=findings,
    secret_scan='Pattern scan including decompressed CSVs/source ZIPs/model archive members; manual scope/rights review also required, not a proof of absence.',records=records)
Path(a.out).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
if findings:raise SystemExit(1)
