"""Losslessly package each new raw run in deterministic GitHub-sized parts."""
from __future__ import annotations
import csv,gzip,hashlib,io,json,zipfile
from common import *
LIMIT=95*2**20

def sha_data(data):return hashlib.sha256(data).hexdigest()

def verify_existing(seed):
    dest=publication(seed);v=read(dest/'validation.json')
    for row in csv_read(dest/'parts_manifest.csv'):
        p=dest/row['part'];assert p.stat().st_size==int(row['bytes']) and digest(p)==row['sha256']
    return v

def csv_read(path):
    import csv as c
    with Path(path).open(encoding='utf-8',newline='') as f:return list(c.DictReader(f))

def pack(seed):
    src=run(seed);dest=publication(seed)
    if dest.exists():return verify_existing(seed)
    complete=read(src/'COMPLETE.json');current=tree(src);current.pop('COMPLETE.json')
    if current!=complete['files']:raise ValueError(f'raw scientific run {seed} differs from COMPLETE')
    files=sorted(p for p in src.rglob('*') if p.is_file());groups={'core':[]};contexts=[]
    for path in files:
        rel=path.relative_to(src);stage=rel.parts[1] if len(rel.parts)>1 and rel.parts[0]=='stages' else ''
        if stage.startswith('context_'):
            context=stage.rsplit('_v',1)[0]
            if context not in contexts:contexts.append(context)
        else:groups['core'].append(path)
    for i in range(0,len(contexts),8):
        selected=set(contexts[i:i+8]);groups[f'contexts_{i+1:02d}_{min(i+8,len(contexts)):02d}']=[p for p in files if len(p.relative_to(src).parts)>1 and p.relative_to(src).parts[1].rsplit('_v',1)[0] in selected]
    assert len(contexts)==68 and sorted(p for g in groups.values() for p in g)==files
    dest.mkdir(parents=True);members=[];parts=[];fixed=(2026,9,15,0,0,0)
    for label,paths in groups.items():
        archive=dest/(label+'.zip')
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for path in paths:
                relative=path.relative_to(src).as_posix();data=path.read_bytes();actual=sha_data(data)
                if relative!='COMPLETE.json' and complete['files'][relative]!=actual:raise ValueError('source hash mismatch '+relative)
                info=zipfile.ZipInfo(relative,fixed);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data,compresslevel=6)
                members.append(dict(part=archive.name,path=relative,bytes=len(data),sha256=actual))
        if archive.stat().st_size>=LIMIT:raise ValueError('GitHub part too large '+str(archive))
        parts.append(dict(part=archive.name,bytes=archive.stat().st_size,sha256=digest(archive),members=len(paths),uncompressed_bytes=sum(p.stat().st_size for p in paths)))
    with gzip.GzipFile(filename='',mode='wb',fileobj=(dest/'raw_file_manifest.csv.gz').open('wb'),mtime=0) as raw:
        text=io.TextIOWrapper(raw,encoding='utf-8',newline='');w=csv.DictWriter(text,fieldnames=['part','path','bytes','sha256']);w.writeheader();w.writerows(members);text.flush()
    with (dest/'parts_manifest.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['part','bytes','sha256','members','uncompressed_bytes']);w.writeheader();w.writerows(parts)
    lookup={(r['part'],r['path']):r for r in members};checked=0
    for row in parts:
        with zipfile.ZipFile(dest/row['part']) as z:
            for info in z.infolist():
                expected=lookup[(row['part'],info.filename)];data=z.read(info.filename);assert len(data)==expected['bytes'] and sha_data(data)==expected['sha256'];checked+=1
    result=dict(passed=True,model_seed=seed,parts=len(parts),members=checked,raw_files=len(files),contexts=68,complete_tree_verified=True,
        maximum_part_bytes=max(r['bytes'] for r in parts),total_part_bytes=sum(r['bytes'] for r in parts),github_part_limit_bytes=LIMIT,
        reconstruction='Extract every part into one empty directory; verify every byte with raw_file_manifest.csv.gz.',source_complete_sha256=digest(src/'COMPLETE.json'))
    atomic(dest/'validation.json',result);return result

def main():
    results=[pack(seed) for seed in SEEDS]
    atomic(REVIEW/'RAW_PACKAGE_VALIDATION.json',dict(passed=True,seeds=list(SEEDS),parts=sum(x['parts'] for x in results),members=sum(x['members'] for x in results),total_part_bytes=sum(x['total_part_bytes'] for x in results),results=results))
    print(json.dumps(read(REVIEW/'RAW_PACKAGE_VALIDATION.json'),indent=2))

if __name__=='__main__':main()
