import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('materializer',Path(__file__).parents[1]/'scripts/verify_bdg2_materialize.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_lossless_parts_restore_and_preserve_existing_file(tmp_path,monkeypatch):
    monkeypatch.setattr(module,'ROOT',tmp_path)
    pieces=[b'first\x00bytes',b'last\xffbytes'];parts=[]
    for i,data in enumerate(pieces):
        p=tmp_path/f'part{i}';p.write_bytes(data)
        parts.append(dict(repository_path=p.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    data=b''.join(pieces)
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps(dict(files=[dict(repository_path='unit/stream.csv.gz',
        bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=parts)])))
    assert module.materialize(manifest)[0]['status']=='restored_exact'
    assert (tmp_path/'unit/stream.csv.gz').read_bytes()==data
    assert module.materialize(manifest)[0]['status']=='already_exact'
    (tmp_path/'unit/stream.csv.gz').write_bytes(b'changed')
    with pytest.raises(ValueError,match='never overwrite'):module.materialize(manifest)
    assert (tmp_path/'unit/stream.csv.gz').read_bytes()==b'changed'
