"""Synthetic fit ledger and repository gate. No real data fits are authorized."""
import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[name]='1'
from common import *
import pytest
from src.intervals005_common import Operations

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='v2');parser.add_argument('--focused',action='store_true');parser.add_argument('--repository',action='store_true');args=parser.parse_args()
    tests=['tests/test_context005.py','tests/test_context005_coordinator.py','tests/test_support_design005.py','tests/test_matched_intervals005.py',
        'tests/test_matched_intervals005_remaining.py','tests/test_matched_intervals005_multiseed.py',
        'tests/test_operational004.py','tests/test_operational004_journal.py','tests/test_operational004_flag_dtype.py']
    if args.focused:tests=['tests/test_context005.py','tests/test_context005_coordinator.py']
    if args.repository:tests=['tests']
    os.environ['INTERVALS005_SYNTHETIC_OUT']=str(SMART/'outputs/conditional_context005'/('regression_fixture_'+args.version))
    start_source=source_digest()
    with Operations(REVIEW/f'synthetic_test_operations_{args.version}.jsonl',stage='bounded_regression_gate',synthetic=True) as ops:
        status=pytest.main(['-q',*tests])
    unchanged=start_source==source_digest()
    if not unchanged:status=1
    atomic(REVIEW/f'REGRESSION_RECEIPT_{args.version}.json',dict(exit_status=status,passed=status==0,source_hash=start_source,source_unchanged=unchanged,tests=tests,
        operations=ops.rows,real_data_fits=0,utc=now()))
    raise SystemExit(status)
if __name__=='__main__':main()
