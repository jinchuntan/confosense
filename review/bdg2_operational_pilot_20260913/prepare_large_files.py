"""Lossless publication of checkpoint files over GitHub's ordinary blob limit."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2'
OUT=ROOT/'smart_building_conformal/outputs/amendment004/bdg2_pilot_publication_v1'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    assert (RUN/'units/outer2_model42/COMPLETE.json').exists()
    OUT.mkdir(exist_ok=True)
    records=[]
    for source in sorted(RUN.rglob('*')):
        if not source.is_file() or source.stat().st_size<100*1024**2:continue
        parts=[]
        with source.open('rb') as f:
            i=0
            while chunk:=f.read(40*1024**2):
                part=OUT/(source.name+f'.part{i:03d}')
                if part.exists():assert part.read_bytes()==chunk,'preserve different existing part'
                else:part.write_bytes(chunk)
                parts.append(dict(repository_path=part.relative_to(ROOT).as_posix(),bytes=len(chunk),sha256=sha(part)));i+=1
        # Verify concatenation against the original without modifying its bytes.
        h=hashlib.sha256()
        for part in parts:
            with (ROOT/part['repository_path']).open('rb') as f:
                for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
        assert h.hexdigest()==sha(source)
        records.append(dict(repository_path=source.relative_to(ROOT).as_posix(),bytes=source.stat().st_size,
            sha256=sha(source),parts=parts))
    manifest=dict(passed=True,format='ordered_binary_parts_of_original_gzip_bytes',
        reason='GitHub ordinary Git files must remain below 100 MiB; original checkpoint files remain unchanged locally',
        files=records)
    record_path=OUT/'large_files.json'
    if record_path.exists():assert json.loads(record_path.read_text())==manifest
    else:record_path.write_text(json.dumps(manifest,indent=2)+'\n')
    if records:
        ignore=ROOT/'.gitignore';old=ignore.read_text(encoding='utf-8') if ignore.exists() else ''
        additions='\n# Exact oversized BDG2 pilot files are published as lossless binary parts.\n'
        missing=['/'+r['repository_path'] for r in records if '/'+r['repository_path'] not in old.splitlines()]
        if missing:ignore.write_text(old+additions+'\n'.join(missing)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
