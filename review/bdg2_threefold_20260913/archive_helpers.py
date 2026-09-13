"""Preserve exact helper/test bytes in addition to Git's normalized source."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]


def main(out):
    out=Path(out)
    names=['independent_bdg2_operational_audit.py','verify_bdg2_completed_resume.py',
        'verify_checkpoint_compatibility.py','freeze_bdg2_threefold.py','combine_bdg2_threefold.py',
        'measure_bdg2_threefold.py','diagnose_bdg2_recovery.py','log_pilot_command.py',
        'verify_bdg2_process_cost.py','verify_bdg2_materialize.py']
    files=[ROOT/'smart_building_conformal/scripts'/n for n in names]
    files+=list((ROOT/'review/bdg2_threefold_20260913').glob('*.py'))
    files+=list((ROOT/'smart_building_conformal/tests').glob('test_threefold_*.py'))
    files+=[ROOT/'smart_building_conformal/tests'/n for n in ['test_checkpoint_memory.py','test_independent_bdg2_audit.py']]
    rows=[]
    with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            name=p.relative_to(ROOT).as_posix();data=p.read_bytes();z.writestr(name,data)
            rows.append(dict(repository_path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    record=dict(format='exact_working_helper_source_bytes',files=rows,archive_sha256=hashlib.sha256(out.read_bytes()).hexdigest())
    with out.with_suffix('.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
    print(json.dumps(dict(files=len(rows),archive_sha256=record['archive_sha256'])))


if __name__=='__main__':main(sys.argv[1])
