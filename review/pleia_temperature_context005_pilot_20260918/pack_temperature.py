"""Losslessly package the single temperature raw run in GitHub-sized parts.

Reuses the corrected packaging contract from the energy study: explicit
``csv`` module handling (``common`` re-exports a ``csv`` writer that shadows the
standard library), COMPLETE.json verified against its own digest rather than
against its own file list, validated parts reused across retries, and every
archive member reopened and hashed once locally.

Single unit: no seed loop, no energy path.
"""
from __future__ import annotations

import csv as csv_module
import gzip
import hashlib
import io
import json
import zipfile
from pathlib import Path

import common
from common import REVIEW, read, digest, tree, atomic

LIMIT = 95 * 2 ** 20
CONTEXTS_PER_PART = 8
SRC = common.run()
DEST = common.publication()


def sha_data(data):
    return hashlib.sha256(data).hexdigest()


def csv_read(path):
    with Path(path).open(encoding='utf-8', newline='') as f:
        return list(csv_module.DictReader(f))


def verify_existing():
    v = read(DEST / 'validation.json')
    for row in csv_read(DEST / 'parts_manifest.csv'):
        p = DEST / row['part']
        if p.stat().st_size != int(row['bytes']) or digest(p) != row['sha256']:
            raise ValueError('existing part drifted: ' + row['part'])
    return v


def verify_archive(archive, paths, complete):
    expected_members = [path.relative_to(SRC).as_posix() for path in paths]
    with zipfile.ZipFile(archive) as z:
        if z.namelist() != expected_members:
            raise ValueError('existing archive members mismatch ' + str(archive))
        members = []
        for relative in expected_members:
            data = z.read(relative)
            actual = sha_data(data)
            want = digest(SRC / 'COMPLETE.json') if relative == 'COMPLETE.json' else complete['files'][relative]
            if actual != want:
                raise ValueError('existing archive hash mismatch ' + relative)
            members.append(dict(part=archive.name, path=relative, bytes=len(data), sha256=actual))
    if archive.stat().st_size >= LIMIT:
        raise ValueError('GitHub part too large ' + str(archive))
    return members, dict(part=archive.name, bytes=archive.stat().st_size, sha256=digest(archive),
                         members=len(paths), uncompressed_bytes=sum(p.stat().st_size for p in paths))


def write_archive(archive, paths, complete):
    fixed = (2026, 9, 19, 0, 0, 0)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for path in paths:
            relative = path.relative_to(SRC).as_posix()
            data = path.read_bytes()
            actual = sha_data(data)
            want = digest(SRC / 'COMPLETE.json') if relative == 'COMPLETE.json' else complete['files'][relative]
            if actual != want:
                raise ValueError('source hash mismatch ' + relative)
            info = zipfile.ZipInfo(relative, fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data, compresslevel=6)
    return verify_archive(archive, paths, complete)


def preserve_incomplete_metadata():
    """Retain any failed metadata stub instead of silently overwriting it."""
    for name in ['raw_file_manifest.csv.gz', 'parts_manifest.csv', 'validation.json']:
        path = DEST / name
        if path.exists():
            archived = DEST / (name + '.incomplete_preserved')
            if archived.exists():
                raise ValueError('incomplete metadata archive already exists ' + str(archived))
            path.rename(archived)


def pack():
    if (DEST / 'validation.json').exists():
        return verify_existing()
    complete = read(SRC / 'COMPLETE.json')
    current = tree(SRC)
    current.pop('COMPLETE.json')
    if current != complete['files']:
        raise ValueError('raw scientific run differs from its COMPLETE manifest')

    files = sorted(p for p in SRC.rglob('*') if p.is_file())
    groups = {'core': []}
    contexts = []
    for path in files:
        rel = path.relative_to(SRC)
        stage = rel.parts[1] if len(rel.parts) > 1 and rel.parts[0] == 'stages' else ''
        if stage.startswith('context_'):
            context = stage.rsplit('_v', 1)[0]
            if context not in contexts:
                contexts.append(context)
        else:
            groups['core'].append(path)
    for i in range(0, len(contexts), CONTEXTS_PER_PART):
        selected = set(contexts[i:i + CONTEXTS_PER_PART])
        label = f'contexts_{i + 1:02d}_{min(i + CONTEXTS_PER_PART, len(contexts)):02d}'
        groups[label] = [p for p in files if len(p.relative_to(SRC).parts) > 1
                         and p.relative_to(SRC).parts[1].rsplit('_v', 1)[0] in selected]
    if len(contexts) != 68:
        raise ValueError(f'expected 68 original contexts, found {len(contexts)}')
    if sorted(p for g in groups.values() for p in g) != files:
        raise ValueError('packaging partition is not a lossless cover of the raw tree')

    DEST.mkdir(parents=True, exist_ok=True)
    preserve_incomplete_metadata()
    expected_archives = {label + '.zip' for label in groups}
    existing = {p.name for p in DEST.glob('*.zip')}
    if existing - expected_archives:
        raise ValueError('unexpected existing archive part ' + str(existing - expected_archives))

    members, parts = [], []
    for label, paths in groups.items():
        archive = DEST / (label + '.zip')
        got, part = verify_archive(archive, paths, complete) if archive.exists() else write_archive(archive, paths, complete)
        members.extend(got)
        parts.append(part)

    with gzip.GzipFile(filename='', mode='wb', fileobj=(DEST / 'raw_file_manifest.csv.gz').open('wb'), mtime=0) as raw:
        text = io.TextIOWrapper(raw, encoding='utf-8', newline='')
        w = csv_module.DictWriter(text, fieldnames=['part', 'path', 'bytes', 'sha256'])
        w.writeheader()
        w.writerows(members)
        text.flush()
    with (DEST / 'parts_manifest.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv_module.DictWriter(f, fieldnames=['part', 'bytes', 'sha256', 'members', 'uncompressed_bytes'])
        w.writeheader()
        w.writerows(parts)

    lookup = {(r['part'], r['path']): r for r in members}
    checked = 0
    for row in parts:
        with zipfile.ZipFile(DEST / row['part']) as z:
            for info in z.infolist():
                want = lookup[(row['part'], info.filename)]
                data = z.read(info.filename)
                if len(data) != want['bytes'] or sha_data(data) != want['sha256']:
                    raise ValueError('reopened member mismatch ' + info.filename)
                checked += 1

    result = dict(passed=True, unit=common.KEY, dataset='pleia', target='temperature', model_seed=42,
                  parts=len(parts), members=checked, raw_files=len(files), contexts=68,
                  complete_tree_verified=True,
                  maximum_part_bytes=max(r['bytes'] for r in parts),
                  total_part_bytes=sum(r['bytes'] for r in parts),
                  github_part_limit_bytes=LIMIT,
                  reconstruction='Extract every part into one empty directory; verify every byte with '
                                 'raw_file_manifest.csv.gz.',
                  source_complete_sha256=digest(SRC / 'COMPLETE.json'))
    atomic(DEST / 'validation.json', result)
    return result


def main():
    result = pack()
    # Distinct name: RAW_PACKAGE_VALIDATION.json in this directory is a stale
    # energy copy that must not be overwritten or republished as temperature.
    atomic(REVIEW / 'TEMPERATURE_RAW_PACKAGE_VALIDATION.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
