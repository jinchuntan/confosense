"""Seal the C pilot evidence, commit it, and make a verified external Git backup."""
import argparse,csv,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SMART=ROOT/'smart_building_conformal';REVIEW=Path(__file__).resolve().parent
sys.path.insert(0,str(SMART))
from src.intervals005_common import atomic,read,digest,source_digest,tree
BRANCH='review/pleia-energy-context005-pilot-20260915';ENTRY='6e57bf4350012e3265ea2416f2e6b0bfcc12f8c3'
RUN=SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1';ANALYSIS=SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1_analysis'
PACK=SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1_publication_v1';BATCH=SMART/'outputs/conditional_context005/first_real_C_v1_coordinator'
DESIGN=SMART/'protocols/conditional_context005/pleia_energy_f2_s42_C_v1';BACKUP=Path('C:/Users/nigel/ConfoSenseBackups/pleia_energy_context005_pilot_20260915')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def evidence_index():
    out='../../smart_building_conformal/outputs/conditional_context005/';protocol='../../smart_building_conformal/protocols/conditional_context005/'
    lines=['# PLEIA-energy context005 pilot evidence index','',
        'Exact scope: outer fold 2, model seed 42, h1, 68 contexts, 2,856 scheduled fault slots, 68 clean identities, four fixed 95% controls, five rules, three channels and 9,907-row original clean workload. Energy sensitivity was inactive. No result-driven selection occurred.','',
        '[Pilot report](PLEIA_ENERGY_CONTEXT005_PILOT_REPORT.md), [panel response](PANEL_RESPONSE.md), [remaining work](REMAINING_WORK.md), [next bounded proposal](NEXT_BOUNDED_PROPOSAL.md), [authorization](USER_AUTHORIZATION.txt), [pinned handoff reference](AUTHORIZING_HANDOFF_REFERENCE.md), [progress/restart](PROGRESS_AND_RESTART.md).','',
        '## Frozen execution and fitted ownership','',
        '[Authorized execution manifest](../context_replay005_implementation_20260914/first_real_execution_manifest_v1.json), [frozen protocol]('+protocol+'pleia_energy_f2_s42_C_v1/frozen_protocol.json), [roles]('+protocol+'pleia_energy_f2_s42_C_v1/roles.csv.gz), [schedules]('+protocol+'pleia_energy_f2_s42_C_v1/schedules.csv.gz), [readiness]('+protocol+'pleia_energy_f2_s42_C_v1/readiness.json).','',
        '[Owner fit stage]('+out+'pleia_energy_f2_s42_C_v1/stages/owner_fit_cqr), [CQR calibration stage]('+out+'pleia_energy_f2_s42_C_v1/stages/owner_cal_cqr), [shared control owner]('+out+'pleia_energy_f2_s42_C_v1/stages/controls), [operation ledger]('+out+'pleia_energy_f2_s42_C_v1/operations.jsonl), [scientific completion tree]('+out+'pleia_energy_f2_s42_C_v1/COMPLETE.json).','',
        '## Results and validation','']
    for name,purpose in [
        ('control_rule_channel_summary.csv','all 60 fixed control/rule/channel comparisons, including detection, delays and clean workload'),
        ('stratum_metrics.csv','all 1,260 control/rule/channel/fault-stratum summaries and effective-context denominators'),
        ('event_records.csv.gz','all 171,360 scheduled event/control/rule/channel records including nulls'),
        ('fault_schedule_support.csv','21-stratum scheduled/effective/null/alias and context support'),
        ('original_context_contributions.csv.gz','paired original-context contributions for future seed aggregation'),
        ('paired_control_differences.csv','all descriptive within-context control contrasts; no significance or selection claim'),
        ('background_workload.csv','original full-stream workload contributions'),
        ('background_workload_summary.csv','60 original-exposure workload summaries'),
        ('context_interval_diagnostics.csv.gz','identity and scheduled-slot clean-truth/corrupted-observation interval diagnostics'),
        ('interval_summary.csv','weighted identity/all-slot/effective-slot interval summaries'),
        ('interval_by_fault_stratum.csv','interval metrics by fault family/severity/control/truth definition'),
        ('fullstream_clean_interval_diagnostics.csv','untouched original full-stream interval quality'),
        ('zero_control_identities.csv','all 68 clean context identities and owner/input hashes'),
        ('issued_consumed_hashes.csv.gz','every unique stream/control/rule issued-to-consumed row identity and file hash'),
        ('stream_bound_integrity_summary.csv','ordered emitted bounds and observed raw quantile crossings'),
        ('operation_counts.csv','actual real fit/conformalization call counts'),
        ('operations.csv','full returned-operation records and parameters'),
        ('owner_operation_reconciliation.json','shared owner, logical/nested call and persistence-radius accounting'),
        ('worker_costs_and_exits.csv','all five CLI action exits and elapsed costs'),
        ('stage_cost_summary.csv','stage wall/CPU/peak-memory aggregation'),
        ('stage_costs.csv','per-stage wall/CPU/RSS/private-memory measurements'),
        ('validation.json','aggregate analysis acceptance and unchanged matrix counts')]:lines.append(f'- [{name}]({out}pleia_energy_f2_s42_C_v1_analysis/{name}): {purpose}.')
    lines+=['', '[Compact comparison PNG]('+out+'pleia_energy_f2_s42_C_v1_analysis/control_rule_comparison.png), [PDF]('+out+'pleia_energy_f2_s42_C_v1_analysis/control_rule_comparison.pdf), [figure source manifest]('+out+'pleia_energy_f2_s42_C_v1_analysis/control_rule_comparison.sources.json).','',
        '[Independent validation]('+out+'first_real_C_v1_coordinator/validation/validation.json), [independent reconstructed events]('+out+'first_real_C_v1_coordinator/validation/independently_reconstructed_events.csv.gz), [all independent scalar/identity checks]('+out+'first_real_C_v1_coordinator/validation/independent_checks.csv), [zero-fit completed resume]('+out+'first_real_C_v1_coordinator/resume.json), [durable progress]('+out+'first_real_C_v1_coordinator/progress.json), [attempt journal]('+out+'first_real_C_v1_coordinator/attempts.jsonl).','',
        '## Lossless raw stream publication','',
        '[Archive validation]('+out+'pleia_energy_f2_s42_C_v1_publication_v1/validation.json), [archive parts and hashes]('+out+'pleia_energy_f2_s42_C_v1_publication_v1/parts_manifest.csv), and [every raw member path/byte/hash]('+out+'pleia_energy_f2_s42_C_v1_publication_v1/raw_file_manifest.csv.gz). Extract every ZIP part into one empty directory to reconstruct the complete local scientific run; paths are disjoint and every member was read back and hash-verified. Core fitted owners and aggregate tables are also linked directly above.','',
        '[Preservation baseline](PRESERVATION_BASELINE.json), [completion verification](COMPLETION_VERIFICATION.json), [publication file manifest](EVIDENCE_MANIFEST.csv). External verified bundle details are emitted under `C:/Users/nigel/ConfoSenseBackups/pleia_energy_context005_pilot_20260915/`.']
    atomic(REVIEW/'EVIDENCE_INDEX.md','\n'.join(lines)+'\n')

def main(label):
    assert git('branch','--show-current')==BRANCH and git('rev-parse','main')=='06fe967be2be8d7898812c0c2d6e464d4e942351'
    baseline=read(REVIEW/'PRESERVATION_BASELINE.json')
    for ref,value in baseline['prior_heads'].items():assert git('rev-parse',ref)==value,(ref,value)
    for path in baseline['historical_untracked_paths']:assert (ROOT/path).is_file()
    changed=git('diff',ENTRY,'--name-only','--','smart_building_conformal/outputs','smart_building_conformal/protocols').splitlines()
    allowed=('smart_building_conformal/outputs/conditional_context005/pleia_energy_f2_s42_C_v1',
             'smart_building_conformal/outputs/conditional_context005/first_real_C_v1_coordinator',
             'smart_building_conformal/protocols/conditional_context005/pleia_energy_f2_s42_C_v1')
    unexpected=[p for p in changed if not p.startswith(allowed)];assert not unexpected,unexpected
    result=read(ANALYSIS/'validation.json');packed=read(PACK/'validation.json');resume=read(BATCH/'resume.json');independent=read(BATCH/'validation/validation.json')
    assert result['passed'] and packed['passed'] and resume['passed'] and independent['passed'] and source_digest()==baseline['evaluated_source_hash']
    assert not result['energy_sensitivity_applied'] and result['matched_forecasting_complete']==70 and result['interval_quality_complete']==250 and result['seasonal_unique_complete']==9
    atomic(REVIEW/'COMPLETION_VERIFICATION.json',dict(passed=True,source_hash=source_digest(),main=git('rev-parse','main'),prior_review_heads_unchanged=True,
        historical_output_protocol_changes=unexpected,historical_untracked_files_preserved=baseline['historical_untracked_paths'],contexts=68,scheduled_fault_slots=2856,
        zero_controls=68,event_records=171360,all_five_cli_actions_exit_zero=True,independent_validation_passed=True,zero_fit_resume=True,
        raw_archive_parts=packed['parts'],raw_archive_members=packed['members'],energy_sensitivity_applied=False,full_study_ready=False))
    evidence_index()
    run_core=[RUN/'COMPLETE.json',RUN/'operations.jsonl']
    for name in ['owner_fit_cqr','owner_cal_cqr','controls','tables']:
        run_core+=list((RUN/'stages'/name).rglob('*'))
    roots=[REVIEW,DESIGN,BATCH,ANALYSIS,PACK,ROOT/'review/context_replay005_implementation_20260914/first_real_execution_manifest_v1.json',
        *[ROOT/n for n in ['MATCHED_METHOD_READINESS_MAP.md','PROJECT_RECOVERY_STATUS.md','REMAINING_STUDY_EXECUTION_PLAN.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']]]
    files=set(p for root in roots for p in (root.rglob('*') if root.is_dir() else [root]) if p.is_file())|set(p for p in run_core if p.is_file())
    files=sorted(p for p in files if '__pycache__' not in p.parts and p.suffix not in ['.pyc','.tmp'] and p.name!='EVIDENCE_MANIFEST.csv')
    # Stage first, then hash the canonical index blobs. On Windows, hashing
    # working-tree text before staging can disagree with Git after autocrlf
    # normalization even though the committed content is correct.
    BACKUP.mkdir(parents=True,exist_ok=True);stage=BACKUP/(label+'_paths.txt')
    relative_files=[p.relative_to(ROOT).as_posix() for p in files]
    atomic(stage,'\n'.join(relative_files)+'\n')
    subprocess.run(['git','add','--pathspec-from-file='+str(stage)],cwd=ROOT,check=True)
    rows=[]
    for relative in relative_files:
        blob=subprocess.check_output(['git','show',':'+relative],cwd=ROOT)
        assert len(blob)<100*2**20,relative
        rows.append(dict(path=relative,bytes=len(blob),sha256=__import__('hashlib').sha256(blob).hexdigest()))
    manifest=REVIEW/'EVIDENCE_MANIFEST.csv'
    with manifest.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);writer.writeheader();writer.writerows(rows)
    subprocess.run(['git','add',str(manifest.relative_to(ROOT))],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    assert all(path not in git('diff','--cached','--name-only').splitlines() for path in baseline['historical_untracked_paths'])
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:
        subprocess.run(['git','commit','-m','Publish PLEIA-energy conditional-context pilot: '+label],cwd=ROOT,check=True)
    head=git('rev-parse','HEAD');bundle=BACKUP/(label+'_'+head[:8]+'.bundle')
    subprocess.run(['git','bundle','create',str(bundle),BRANCH,'^'+ENTRY],cwd=ROOT,check=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    receipt=dict(commit=head,branch=BRANCH,backup=str(bundle),backup_sha256=digest(bundle),backup_bytes=bundle.stat().st_size,
        evidence_files=len(rows),evidence_bytes=sum(r['bytes'] for r in rows),main_unchanged=True,utc=read(BATCH/'progress.json')['updated_utc'])
    atomic(BACKUP/(label+'_backup_receipt.json'),receipt);print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);main(p.parse_args().label)
