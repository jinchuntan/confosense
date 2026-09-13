"""Publish new completed units' oversized files as lossless original-byte parts."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'smart_building_conformal/outputs/amendment004'


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    for fold in [1,0]:
        run=BASE/f'bdg2_threefold_f{fold}_s42_v1'
        assert (run/f'units/outer{fold}_model42/COMPLETE.json').is_file()
        out=BASE/f'bdg2_threefold_f{fold}_publication_v1';out.mkdir(exist_ok=True)
        records=[]
        for source in sorted(run.rglob('*')):
            if not source.is_file() or source.stat().st_size<100*1024**2:continue
            parts=[];whole=hashlib.sha256()
            with source.open('rb') as f:
                i=0
                while block:=f.read(40*1024**2):
                    part=out/(source.name+f'.part{i:03d}')
                    if part.exists():assert part.read_bytes()==block
                    else:part.write_bytes(block)
                    whole.update(block)
                    parts.append(dict(repository_path=part.relative_to(ROOT).as_posix(),bytes=len(block),sha256=sha(part)));i+=1
            assert whole.hexdigest()==sha(source)
            records.append(dict(repository_path=source.relative_to(ROOT).as_posix(),bytes=source.stat().st_size,sha256=sha(source),parts=parts))
        manifest=dict(passed=True,format='ordered_binary_parts_of_original_gzip_bytes',files=records)
        path=out/'large_files.json'
        if path.exists():assert json.loads(path.read_text())==manifest
        else:path.write_text(json.dumps(manifest,indent=2)+'\n')
        ignore=ROOT/'.gitignore';old=ignore.read_text(encoding='utf-8')
        missing=['/'+r['repository_path'] for r in records if '/'+r['repository_path'] not in old.splitlines()]
        if missing:ignore.write_text(old+'\n# Exact oversized three-fold files have lossless publication parts.\n'+'\n'.join(missing)+'\n',encoding='utf-8')
        print(json.dumps(dict(fold=fold,files=len(records),parts=sum(len(r['parts']) for r in records))))


if __name__=='__main__':main()
