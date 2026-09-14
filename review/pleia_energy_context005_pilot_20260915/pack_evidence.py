"""Create deterministic, lossless <95 MiB publication parts for the raw replay tree."""
from __future__ import annotations
import csv,gzip,hashlib,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'smart_building_conformal'))
from src.intervals005_common import ROOT,atomic,digest,read,tree

RUN=ROOT/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1'
DEST=ROOT/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1_publication_v1'
LIMIT=95*2**20

def file_hash(data):return hashlib.sha256(data).hexdigest()

def main():
    if DEST.exists():raise ValueError('preserve publication archives; choose a new version')
    complete=read(RUN/'COMPLETE.json');current=tree(RUN);current.pop('COMPLETE.json')
    if current!=complete['files']:raise ValueError('raw scientific run differs from COMPLETE manifest')
    files=sorted(p for p in RUN.rglob('*') if p.is_file())
    groups={'core':[]};context_ids=[]
    for path in files:
        first=path.relative_to(RUN).parts[1] if path.relative_to(RUN).parts[0]=='stages' and len(path.relative_to(RUN).parts)>1 else ''
        if first.startswith('context_'):
            context=first.rsplit('_v',1)[0]
            if context not in context_ids:context_ids.append(context)
        else:groups['core'].append(path)
    for i in range(0,len(context_ids),8):
        selected=set(context_ids[i:i+8]);groups[f'contexts_{i+1:02d}_{min(i+8,len(context_ids)):02d}']=[p for p in files if len(p.relative_to(RUN).parts)>1 and p.relative_to(RUN).parts[1].rsplit('_v',1)[0] in selected]
    assert len(context_ids)==68
    assert sorted(p for values in groups.values() for p in values)==files
    DEST.mkdir(parents=True)
    member_rows=[];part_rows=[]
    fixed=(2026,9,15,0,0,0)
    for label,paths in groups.items():
        archive=DEST/(label+'.zip')
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for path in paths:
                relative=path.relative_to(RUN).as_posix();data=path.read_bytes();actual=file_hash(data)
                if relative!='COMPLETE.json' and complete['files'][relative]!=actual:raise ValueError('source hash mismatch: '+relative)
                info=zipfile.ZipInfo(relative,fixed);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                z.writestr(info,data,compresslevel=6)
                member_rows.append(dict(part=archive.name,path=relative,bytes=len(data),sha256=actual))
        if archive.stat().st_size>=LIMIT:raise ValueError('GitHub part too large: '+str(archive))
        part_rows.append(dict(part=archive.name,bytes=archive.stat().st_size,sha256=digest(archive),members=len(paths),uncompressed_bytes=sum(p.stat().st_size for p in paths)))
    with gzip.GzipFile(filename='',mode='wb',fileobj=(DEST/'raw_file_manifest.csv.gz').open('wb'),mtime=0) as raw:
        import io
        text=io.TextIOWrapper(raw,encoding='utf-8',newline='');writer=csv.DictWriter(text,fieldnames=['part','path','bytes','sha256']);writer.writeheader();writer.writerows(member_rows);text.flush()
    with (DEST/'parts_manifest.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['part','bytes','sha256','members','uncompressed_bytes']);writer.writeheader();writer.writerows(part_rows)
    # Read every archived member back and verify exact content hashes without
    # relying on the source tree or archive CRC alone.
    checked=0;lookup={(r['part'],r['path']):r for r in member_rows}
    for row in part_rows:
        with zipfile.ZipFile(DEST/row['part']) as z:
            for info in z.infolist():
                expected=lookup[(row['part'],info.filename)]
                data=z.read(info.filename);assert len(data)==int(expected['bytes']) and file_hash(data)==expected['sha256'];checked+=1
    atomic(DEST/'validation.json',dict(passed=True,format='ZIP_DEFLATED lossless deterministic member ordering/timestamps',parts=len(part_rows),members=checked,
        raw_files=len(files),contexts=68,complete_tree_verified=True,maximum_part_bytes=max(r['bytes'] for r in part_rows),github_part_limit_bytes=LIMIT,
        reconstruction='Extract every part into one empty directory. Duplicate member paths are forbidden by this partition. Verify each byte against raw_file_manifest.csv.gz.',
        source_complete_sha256=digest(RUN/'COMPLETE.json')))
    print(json.dumps(dict(passed=True,parts=len(part_rows),members=checked,total_part_bytes=sum(r['bytes'] for r in part_rows),maximum_part_bytes=max(r['bytes'] for r in part_rows)),indent=2))

if __name__=='__main__':main()
