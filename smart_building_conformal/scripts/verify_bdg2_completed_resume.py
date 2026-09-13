"""Run the normal completed-unit resume with every fitting route forbidden."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.unit_checkpoint import digest
from src import operational004 as runner
from src import operational004_engine as engine
from src import operational004_stream as stream

run=Path(sys.argv[1]);out=Path(sys.argv[2])
if out.exists():raise FileExistsError(out)
unit=run/'units/outer2_model42'
before={p.name:digest(p) for p in unit.iterdir() if p.is_file()}
assert 'COMPLETE.json' in before
attempts=[]
def forbidden(*args,**kwargs):
    attempts.append('fit_or_compute_attempt');raise AssertionError('completed-unit resume attempted fitting/computation')
runner.evaluate_unit=forbidden
engine.evaluate_unit=forbidden
stream.OwnedInterval.__init__=forbidden
stream.conformal_cqr.fit_cqr=forbidden
result=runner.run('bdg2',2,42,str(run),'configs/operational_amendment004.json',resume=True)
after={p.name:digest(p) for p in unit.iterdir() if p.is_file()}
assert before==after and not attempts and result['new_fit_invocations']==0 and result['reused_units']==1
record=dict(passed=True,normal_completed_resume=result,forbidden_fit_or_compute_calls=len(attempts),
    unit_files_byte_identical=len(before),unit_hashes=after,partial_stage_recovery_claimed=False)
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='unit_hashes'},indent=2),flush=True)
