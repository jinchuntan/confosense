import hashlib
import importlib.util
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REVIEW=ROOT/'review/pleia_energy_context005_multiseed_20260915'
sys.path.insert(0,str(REVIEW))
spec=importlib.util.spec_from_file_location('multiseed_pack',REVIEW/'pack_evidence.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)

def test_existing_archive_is_verified_and_reused(tmp_path):
    source=tmp_path/'source';source.mkdir();payload=source/'payload.txt';payload.write_text('immutable evidence',encoding='utf-8')
    complete={'files':{'payload.txt':hashlib.sha256(payload.read_bytes()).hexdigest()}}
    archive=tmp_path/'part.zip'
    members,part=pack.write_archive(archive,[payload],source,complete)
    again,reused=pack.verify_archive(archive,[payload],source,complete)
    assert members==again
    assert part==reused
