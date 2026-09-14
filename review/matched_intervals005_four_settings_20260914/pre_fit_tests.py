"""Run the bounded synthetic/no-fit acceptance suite and seal its receipt."""
import json, subprocess, sys
from common import *

def main():
    out=REVIEW/'PRE_FIT_TEST_RECEIPT_V2.json'
    if out.exists():raise ValueError('preserve existing test receipt')
    command=[PYTHON,'-m','pytest','-q','tests/test_matched_intervals005.py','tests/test_matched_intervals005_remaining.py','tests/test_matched_intervals005_multiseed.py']
    result=subprocess.run(command,cwd=SMART,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (REVIEW/'PRE_FIT_TESTS.log').write_text(result.stdout,encoding='utf-8')
    receipt=dict(passed=result.returncode==0,actual_exit=result.returncode,command=command,source_commit=git('rev-parse','HEAD'),source_hash=source_digest(),tests='27 matched-interval synthetic, remaining-scope, and prior-multiseed checks',enbpi_base_fits_per_owner=11,models_fitted=0,calibrators_fitted=0,utc=now())
    atomic(out,receipt)
    if result.returncode:raise SystemExit(result.returncode)
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
