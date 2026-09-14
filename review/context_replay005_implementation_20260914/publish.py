"""Publish bounded evidence and verify an incremental backup outside OneDrive."""
import csv as csvlib,json
from common import *

def index():
    out='../../smart_building_conformal/outputs/conditional_context005/'
    protocol='../../smart_building_conformal/protocols/conditional_context005/'
    lines=['# Conditional-context005 implementation evidence','',
        'No new real-data fit or real C replay occurred. Real completion remains 70/195 matched forecasting, 250/1950 interval cells and 9/27 unique seasonal computations. Full-study readiness is false.','',
        '[Completed implementation report](IMPLEMENTATION_REPORT.md), [support gate](SUPPORT_GATE_STATUS.md), [interval undercoverage diagnosis](INTERVAL_FAILURE_DIAGNOSTIC.md), [protocol-to-code crosswalk](PROTOCOL_TO_CODE_CROSSWALK.md), [energy sensitivity proposal](ENERGY_SENSITIVITY_SPEC.md), [panel response](PANEL_RESPONSE.md), [first real-run proposal](FIRST_CONDITIONAL_CONTEXT_RUN_PROPOSAL.md).','',
        '[Complete handoff](AUTHORIZING_HANDOFF.md), [authorization](USER_AUTHORIZATION.txt), [source code](../../smart_building_conformal/src/conditional_context005.py), [regression tests](../../smart_building_conformal/tests/test_context005.py), [inference tests](../../smart_building_conformal/tests/test_context005_inference_acceptance.py), [coordinator recovery tests](../../smart_building_conformal/tests/test_context005_coordinator.py).','',
        '## Actual verification and recovery','',
        '[Repository gate](repository_gate_v4.log.json): exit 0, 446 passed/one skipped. [Final numeric-reader regression](regression_numeric_columns_v6.log.json): exit 0, 38 passed. [Paired inference acceptance](inference_acceptance_v1.log.json): exit 0, two passed. Prior failed gates and validation attempts remain in this directory and the durable journal.','',
        '[Numeric-reader repair and original scientific hashes](VALIDATION_REPAIR_numeric_columns.json), [strict completed-only source compatibility]('+protocol+'synthetic_pleia_energy_v1/validation_source_compatibility.json), [coordinator progress]('+out+'synthetic_v1_coordinator/progress.json), [all attempt records]('+out+'synthetic_v1_coordinator/attempts.jsonl), [restart instructions](PROGRESS_AND_RESTART.md).','']
    for ds in ['pleia_energy','rico']:
        validation=ds+'_validation_numeric_columns' if ds=='pleia_energy' else ds+'_validation'
        lines.append(f'- {ds}: [frozen protocol]({protocol}synthetic_{ds}_v1/frozen_protocol.json), [readiness]({protocol}synthetic_{ds}_v1/readiness.json), [serialized owners and streams]({out}synthetic_{ds}_v1/stages), [operations]({out}synthetic_{ds}_v1/operations.jsonl), [independent validation]({out}synthetic_v1_coordinator/{validation}/validation.json), [zero-fit resume]({out}synthetic_v1_coordinator/{ds}_resume.json), [event records]({out}synthetic_{ds}_v1/stages/tables/events.csv.gz), [original workload]({out}synthetic_{ds}_v1/stages/tables/fullstream_workload.csv).')
    lines+=['','## Recomputable tables','']
    for path,purpose in [
        ('implementation_support_v1/scope_crosswalk.csv','all 1,950 method/horizon/fold/seed/level cells and explicit owner dependencies'),
        ('implementation_support_v1/joint_support.csv','all 36 joint role sets'),
        ('implementation_support_v1/context_role_support.csv','all nine C dataset/fold role checks and tails'),
        ('implementation_support_v1/boundary_checks.csv','24 strict chronological/group boundary checks'),
        ('interval_diagnostic_extension_v1/all_method_diagnostic.csv','all 130 preserved seed-42 interval cells; native/common support, errors and miss directions'),
        ('implementation_support_v1/interval_owner_diagnostic.csv','native CQR and static-EnbPI owner corrections/distributions'),
        ('implementation_support_v1/score_distributions.csv','calibration and held-out score distributions'),
        ('implementation_analysis_v1/synthetic_operation_counts.csv','actual synthetic CLI wrapper/sub-estimator/calibrator calls'),
        ('implementation_analysis_v1/synthetic_stage_costs.csv','per-stage wall time, CPU and sampled RSS/private memory'),
        ('implementation_analysis_v1/cli_all_attempt_costs_and_exits.csv','all attempts including failed validation costs'),
        ('implementation_analysis_v1/synthetic_validation_summary.csv','independent reconstruction outcomes'),
        ('implementation_analysis_v1/zero_fit_resume_summary.csv','zero fits/updates and unchanged scientific artifacts'),
        ('implementation_analysis_v1/seasonal_completion_crosswalk.csv','9/27 unique deterministic seasonal computations'),
        ('implementation_analysis_v1/first_run_stratum_support.csv','proposed real context/slot/effective/null denominators'),
        ('aggregate_validation_v2/validation.json','independent interval-diagnostic and aggregate check result; initial numeric-delay reader attempt preserved'),
        ('aggregate_validation_v2/issued_consumed_hash_crosswalk.csv.gz','each rule input/issued/consumed identity'),
        ('operation_audit_v1/call_counts_by_ledger.csv','separate recorded test/debug/CLI operation counts; nested timings are not additive'),
        ('energy_sensitivity_proposal_v1/mask_reason_provenance.csv','synthetic proposed mask and row-level reasons'),
        ('energy_sensitivity_proposal_v1/denominators.json','synthetic primary versus retrospective subset denominator example')]:
        lines.append(f'- [{path}]({out}{path}): {purpose}.')
    lines+=['',f'[Coverage figure PNG]({out}implementation_analysis_v1/interval_undercoverage.png), [PDF]({out}implementation_analysis_v1/interval_undercoverage.pdf), and [source manifest]({out}implementation_analysis_v1/interval_undercoverage.sources.json).','',
        '## Exact next unit; not launched','',
        '[Machine proposal](first_real_run_proposal_manifest.json), [68 contexts](first_run_published_contexts.csv), [2,856 schedules](first_run_published_schedules.csv.gz), [68 identity schedules](first_run_zero_controls.csv), [owner role compatibility](owner_role_compatibility.csv), [no-fit causal feature readiness](FIRST_RUN_NO_FIT_READINESS.json), [current-source frozen proposal]('+protocol+'pleia_energy_first_proposal_v3/frozen_protocol.json), [current-source readiness]('+protocol+'pleia_energy_first_proposal_v3/readiness.json), [future durable coordinator](first_real_coordinator.py), [inert helper guard test](FUTURE_REAL_HELPER_GUARD.json). Earlier proposal freezes remain preserved and superseded by v3.','',
        '[Preservation baseline](PRESERVATION_BASELINE.json), [completion/preservation verification](COMPLETION_VERIFICATION.json), [exact publication byte manifest](EVIDENCE_MANIFEST.csv). Verified incremental Git backup is stored outside OneDrive under `C:/Users/nigel/ConfoSenseBackups/context_replay005_implementation_20260914/`; its receipt is published separately.']
    atomic(REVIEW/'EVIDENCE_INDEX.md','\n'.join(lines)+'\n')

def main(label):
    assert git('branch','--show-current')==BRANCH
    baseline=read(REVIEW/'PRESERVATION_BASELINE.json')
    for ref,head in baseline['prior_heads'].items():assert git('rev-parse',ref)==head,(ref,head)
    historical=[p for p in git('diff',ENTRY,'--name-only','--','smart_building_conformal/outputs','smart_building_conformal/protocols').splitlines() if '/conditional_context005/' not in p]
    assert not historical,historical
    for path in baseline['untracked_historical_paths']:assert (ROOT/path).is_file()
    analysis=read(SMART/'outputs/conditional_context005/implementation_analysis_v1/validation.json');assert analysis['passed']
    assert read(SMART/'outputs/conditional_context005/aggregate_validation_v2/validation.json')['passed']
    atomic(REVIEW/'COMPLETION_VERIFICATION.json',dict(analysis,main=git('rev-parse','main'),prior_review_heads_unchanged=True,tracked_historical_changes=historical,
        untracked_historical_files_left_unstaged=baseline['untracked_historical_paths'],current_source_hash=source_digest(),publication_branch=BRANCH))
    index()
    paths=[REVIEW,SMART/'outputs/conditional_context005',SMART/'protocols/conditional_context005',ROOT/'.gitattributes',SMART/'src/matched_intervals005.py',SMART/'src/conditional_context005.py',SMART/'src/energy_sensitivity005.py',*list((SMART/'src').glob('context005_*.py')),*list((SMART/'tests').glob('test_context005*.py')),
        *[ROOT/n for n in ['MATCHED_METHOD_READINESS_MAP.md','PROJECT_RECOVERY_STATUS.md','REMAINING_STUDY_EXECUTION_PLAN.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']]]
    files=sorted(set(p for path in paths for p in (path.rglob('*') if path.is_dir() else [path]) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.tmp','.pyc') and p.name!='EVIDENCE_MANIFEST.csv'))
    rows=[]
    for p in files:
        assert p.stat().st_size<100*2**20,p
        rows.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    manifest=REVIEW/'EVIDENCE_MANIFEST.csv'
    with manifest.open('w',newline='',encoding='utf-8') as f:
        writer=csvlib.DictWriter(f,fieldnames=['path','bytes','sha256']);writer.writeheader();writer.writerows(rows)
    BACKUP.mkdir(parents=True,exist_ok=True);stage=BACKUP/(label+'_stage_paths.txt');atomic(stage,'\n'.join([r['path'] for r in rows]+[manifest.relative_to(ROOT).as_posix()])+'\n')
    subprocess.run(['git','add','--pathspec-from-file='+str(stage)],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:subprocess.run(['git','commit','-m','Publish conditional-context implementation evidence: '+label],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    head=git('rev-parse','HEAD');bundle=BACKUP/(label+'_'+head[:8]+'.bundle')
    subprocess.run(['git','bundle','create',str(bundle),BRANCH,'^'+ENTRY],cwd=ROOT,check=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    result=dict(commit=head,branch=BRANCH,backup=str(bundle),backup_sha256=sha(bundle),backup_bytes=bundle.stat().st_size,evidence_files=len(rows),evidence_bytes=sum(r['bytes'] for r in rows),main_unchanged=True,utc=now())
    atomic(BACKUP/(label+'_backup_receipt.json'),result);print(json.dumps(result,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);main(p.parse_args().label)
