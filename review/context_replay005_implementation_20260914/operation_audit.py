"""Separate actual test/debug/CLI profiler calls; do not sum nested wall times."""
from common import *
import json,pandas as pd
from src.intervals005_common import csv,Operations
out=SMART/'outputs/conditional_context005/operation_audit_v1';out.mkdir(parents=True,exist_ok=False)
paths=list(REVIEW.glob('synthetic*operations*.jsonl'))+list((SMART/'outputs/conditional_context005').glob('synthetic_*_v1/operations.jsonl'))+list((SMART/'outputs/conditional_context005').glob('regression_fixture_*/run/operations.jsonl'))
rows=[];seen=set()
with Operations(forbid=True):
    for path in paths:
        for line in path.read_text().splitlines():
            row=json.loads(line)
            if row.get('event')!='returned':continue
            key=row['operation_id'];assert key not in seen;seen.add(key)
            rows.append(dict(ledger=path.relative_to(ROOT).as_posix(),**row))
    f=pd.DataFrame(rows);csv(out/'all_recorded_calls.csv',f)
    csv(out/'call_counts_by_ledger.csv',f.groupby(['ledger','kind']).size().rename('returned_calls').reset_index())
    atomic(out/'validation.json',dict(passed=True,recorded_returned_calls=len(f),ledgers=len(paths),unique_operation_ids=True,
        all_activity_synthetic=True,wall_times_nested_not_additive=True,scope='Instrumented calls in preserved test/debug/CLI ledgers; temporary ledgers from early failed/exploratory gates are not reconstructed or claimed complete. CLI fit counts are separately complete.'))
print('SYNTHETIC OPERATION LEDGERS AUDITED')
