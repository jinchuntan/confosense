"""Create the exact four authorized manifests and preservation baseline."""
from __future__ import annotations
import copy,json
from common import *

def main():
    if git('branch','--show-current')!=BRANCH:raise ValueError('wrong review branch')
    if git('rev-parse','main')!=MAIN:raise ValueError('main moved before batch freeze')
    if source_digest()!=SOURCE_HASH:raise ValueError('evaluated scientific source changed')
    seed42_manifest=read(REPO/'review/context_replay005_implementation_20260914/first_real_execution_manifest_v1.json')
    assert seed42_manifest['model_seed']==42 and seed42_manifest['execution_authorized']
    for seed in SEEDS:
        m=copy.deepcopy(seed42_manifest);m['model_seed']=seed
        path=manifest(seed)
        if path.exists() and read(path)!=m:raise ValueError(f'preserve mismatching manifest {path}')
        if not path.exists():atomic(path,m)
        for unused in [design(seed),run(seed),validation(seed),resume(seed),publication(seed)]:
            if unused.exists():raise ValueError(f'new path already exists: {unused}')
    prior={line.split(' ',1)[0]:line.split(' ',1)[1] for line in git('for-each-ref','--format=%(refname) %(objectname)','refs/heads').splitlines()
           if not line.startswith('refs/heads/'+BRANCH+' ')}
    baseline=dict(version='pleia_energy_context005_multiseed_v1',entry_commit=ENTRY,branch=BRANCH,main=MAIN,
        source_hash=SOURCE_HASH,prior_heads=prior,seed42_commit=ENTRY,
        seed42_protocol_sha256=digest(SEED42_DESIGN/'frozen_protocol.json'),seed42_complete_sha256=digest(SEED42_RUN/'COMPLETE.json'),
        seed42_validation_sha256=digest(SEED42_BATCH/'validation/validation.json'),seed42_resume_sha256=digest(SEED42_BATCH/'resume.json'),
        seed42_publication_validation_sha256=digest(BASE/'pleia_energy_f2_s42_C_v1_publication_v1/validation.json'),
        historical_untracked_files=read(REPO/'review/pleia_energy_context005_pilot_20260915/COMPLETION_VERIFICATION.json')['historical_untracked_files_preserved'],
        authorized_model_seeds=list(SEEDS),fault_slot_seeds=[42,43],energy_sensitivity_status='inactive_unapproved')
    if (REVIEW/'PRESERVATION_BASELINE.json').exists() and read(REVIEW/'PRESERVATION_BASELINE.json')!=baseline:
        raise ValueError('preservation baseline changed')
    atomic(REVIEW/'PRESERVATION_BASELINE.json',baseline)
    atomic(REVIEW/'AUTHORIZING_HANDOFF_REFERENCE.md',
        '# Authorizing handoff\n\nThe complete task is pinned at commit `a78e77414a53c847ee091df2e2ca40eb94ab70dc`, path `review/NEXT_TASK_PLEIA_ENERGY_CONTEXT005_MULTISEED.md`. The user explicitly authorized model seeds 43–46 in the 15 September 2026 request. Only that document was read from the instruction branch; its older source was not checked out or merged.\n')
    atomic(REVIEW/'USER_AUTHORIZATION.txt','User authorized PLEIA-energy fold-2/h1 C model seeds 43, 44, 45 and 46, including coordination, validation, analysis, backup and non-main publication, on 2026-09-15.\n')
    scope=dict(version='pleia_energy_context005_multiseed_batch_v1',dataset='pleia_energy',outer_fold=2,horizon=1,
        model_seeds=list(SEEDS),reused_seed=42,fault_slot_seeds=[42,43],contexts=68,schedules_per_seed=2856,
        controls=['quantile_static','cqr_static','cqr_rolling','persistence_static'],
        rules=['single_sample','30min_3of3','60min_4of6','180min_3of18','360min_4of36'],channels=['numerical_only','availability_only','combined'],
        confidence_level=.95,expected_new_events=685440,expected_new_seed_macros=240,expected_five_seed_macros=300,
        expected_new_operations=dict(cqr_wrapper_fit=4,quantile_estimator_fit=12,calibrator_conformalize=8,logical_conformalizations=4,persistence_radius=4),
        selection='none',energy_sensitivity=False,source_hash=SOURCE_HASH,execution_authorized=True,authorization_kind='explicit_real_C_run',
        commands={str(s):{a:[PYTHON,'-B','-m','src.conditional_context005',a,'--manifest',str(manifest(s)),'--design',str(design(s)),'--out',str(run(s)),'--readiness',str(design(s)/'readiness.json'),'--receipt',str(validation(s) if a=='validate' else resume(s) if a=='resume' else design(s)/'readiness.json')]
                          for a in ['freeze','readiness','run','validate','resume']} for s in SEEDS})
    atomic(REVIEW/'BATCH_SCOPE.json',scope)
    print(json.dumps(dict(prepared=True,seeds=list(SEEDS),source_hash=source_digest()),indent=2))

if __name__=='__main__':main()
