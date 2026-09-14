"""Capture authorized source text and explicit preservation baselines."""
from common import *
import hashlib
HANDOFF='5481a295714d5e84451bf1651f60cd52ec3732e1:review/NEXT_TASK_CONTEXT_REPLAY005_IMPLEMENTATION.md'
path=REVIEW/'AUTHORIZING_HANDOFF.md'
if not path.exists():path.write_bytes(subprocess.check_output(['git','show',HANDOFF],cwd=ROOT))
authorization='User authorizes implementation, read-only real-data diagnostics, bounded synthetic fitting/integration tests, reporting, backup and publication. No new real-data fitting/replay is authorized in this package. Preserve all existing results and review heads; leave main unchanged.'
if not (REVIEW/'USER_AUTHORIZATION.txt').exists():atomic(REVIEW/'USER_AUTHORIZATION.txt',authorization+'\n')
prior=git('for-each-ref','--format=%(refname) %(objectname)','refs/heads/').splitlines()
if not (REVIEW/'PRESERVATION_BASELINE.json').exists():
    historical=git('ls-files','smart_building_conformal/outputs','smart_building_conformal/protocols').splitlines()
    # Git entry blobs bind all history; only this package's files will be staged.
    atomic(REVIEW/'PRESERVATION_BASELINE.json',dict(main=git('rev-parse','main'),prior_heads={x.split()[0]:x.split()[1] for x in prior if x.split()[0]!='refs/heads/'+BRANCH},
        entry=ENTRY,tracked_historical_paths=historical,untracked_historical_paths=git('ls-files','--others','--exclude-standard','smart_building_conformal/outputs/amendment004').splitlines()))
print('PRESERVATION AND HANDOFF CAPTURED')
