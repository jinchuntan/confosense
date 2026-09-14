"""Capture the immutable preservation and source-lineage baseline."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SMART=ROOT/'smart_building_conformal';REVIEW=Path(__file__).resolve().parent
sys.path.insert(0,str(SMART))
from src.intervals005_common import atomic,read,digest,source_digest
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
prior={line.split()[0]:line.split()[1] for line in git('for-each-ref','--format=%(refname) %(objectname)','refs/heads').splitlines() if not line.startswith('refs/heads/review/pleia-energy-context005-pilot-20260915 ')}
historical=git('ls-files','smart_building_conformal/outputs','smart_building_conformal/protocols').splitlines()
untracked=git('ls-files','--others','--exclude-standard','smart_building_conformal/outputs/amendment004').splitlines()
assert len(untracked)==4
proposal=read(SMART/'protocols/conditional_context005/pleia_energy_first_proposal_v3/frozen_protocol.json')
assert proposal['source_hash']==source_digest()
atomic(REVIEW/'PRESERVATION_BASELINE.json',dict(starting_commit='6e57bf4350012e3265ea2416f2e6b0bfcc12f8c3',main=git('rev-parse','main'),prior_heads=prior,
    evaluated_source_hash=source_digest(),quoted_pre_repair_readiness_hash='83243b4bfb70f56831c7e092fed2a120f67bffc11880d54665c11607c4087841',
    final_published_proposal_v3_source_hash=proposal['source_hash'],proposal_v3_sha256=digest(SMART/'protocols/conditional_context005/pleia_energy_first_proposal_v3/frozen_protocol.json'),
    historical_tracked_paths=historical,historical_untracked_paths=untracked,energy_sensitivity_status='inactive_unapproved',preexisting_real_execution_paths=False))
print('PRESERVATION AND EVALUATED-SOURCE BASELINE CAPTURED')
