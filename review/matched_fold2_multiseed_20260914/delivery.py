"""Package actual completed-batch receipts and costs; never runs an estimator."""
import shutil
from common import *

def main():
    state=read(BATCH/'progress.json')
    assert state['status']=='complete' and state['completed_units']==52
    summary=read(BATCH/'analysis_v1/analysis_validation.json')
    assert summary['passed'] and summary['status']=='complete'
    assert summary['new_tuning_fits']==416 and summary['new_final_fits']==104
    assert summary['new_point_cells']==156 and summary['new_interval_cells']==312
    assert summary['saved_model_checks']==312 and summary['completed_zero_fit_resumes']==52
    assert summary['historical_refits']==summary['repeated_learned_fits']==0
    assert len(summary['new_run_exit_codes'])==52 and set(summary['new_run_exit_codes'])=={0}
    bootstrap=BACKUP/'bootstrap_v2.log.json';assert read(bootstrap)['exit_status']==0
    coordinator=list(BACKUP.glob('coordinator_*.log.json'));assert len(coordinator)==1
    assert read(coordinator[0])['exit_status']==0
    out=REVIEW/'delivery_v1';out.mkdir(exist_ok=False)
    copied=[]
    patterns=['bootstrap_v*.launch.json','bootstrap_v*.log','bootstrap_v*.log.json',
              'bootstrap_v*.log.started.json','coordinator_*.log','coordinator_*.log.json',
              'coordinator_*.log.started.json','*_publication.json','*_remote_verification.json',
              'verify_seed_checkpoint.py','atomic_replace_retries.jsonl','bootstrap_preparation_watch*.json']
    for p in sorted(set(p for pattern in patterns for p in BACKUP.glob(pattern))):
        target=out/p.name;shutil.copyfile(p,target);assert sha(target)==sha(p)
        copied.append(dict(source=str(p),published_path=target.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    with (out/'external_receipt_manifest.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['source','published_path','bytes','sha256']);w.writeheader();w.writerows(copied)
    logs=[('diagnosis_initial_boundary_tie_check',BATCH/'diagnosis_command_v1.log.json'),
          ('diagnosis_corrected_no_fitting',BATCH/'diagnosis_command_v2.log.json'),
          ('all_52_freeze_and_fresh_readiness',BATCH/'prepare_command_v1.log.json'),
          ('30_no_fit_regression_checks',BATCH/'regression_v1.log.json'),
          ('bootstrap_initial_summary_parser',BACKUP/'bootstrap_v1.log.json'),
          ('bootstrap_completed',bootstrap),('coordinator_completed',coordinator[0])]
    rows=[]
    for stage,path in logs:
        actual=read(path)
        rows.append(dict(stage=stage,source_receipt=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else (out/path.name).relative_to(ROOT).as_posix(),started_utc=actual['started_utc'],ended_utc=actual['ended_utc'],wall_seconds=actual['seconds'],actual_exit_status=actual['exit_status'],cost_scope='nested orchestration timings overlap; do not sum all rows'))
    with (out/'actual_outer_command_receipts.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    assert [r['actual_exit_status'] for r in rows]==[1,0,0,0,1,0,0]
    processes=[v for k,v in state['tasks'].items() if k.endswith('/run')]
    assert len(processes)==52 and all(v['exit_code']==0 for v in processes)
    first=min(v['started_utc'] for v in processes)
    completed=read(coordinator[0])['ended_utc']
    wall=(datetime.fromisoformat(completed)-datetime.fromisoformat(first)).total_seconds()
    retries=BACKUP/'atomic_replace_retries.jsonl'
    retry_events=[json.loads(line) for line in retries.read_text().splitlines()] if retries.exists() else []
    verification=dict(passed=True,utc=now(),evaluated_commit=read(REVIEW/'evaluated_commit.json')['commit'],
                      source_hash=read(REVIEW/'joint_pre_fit_manifest.json')['source_hash'],
                      bootstrap_actual_exit=0,coordinator_actual_exit=0,new_run_actual_exits=summary['new_run_exit_codes'],
                      first_model_command_utc=first,coordinator_completed_utc=completed,
                      first_run_to_coordinator_completion_wall_seconds=wall,
                      new_learned_fits=520,regression_checks=30,tiny_learned_fits=0,
                      failed_model_fits=0,repeated_model_fits=0,models_fitted_by_delivery=0,
                      completion=summary,external_files_copied=len(copied),atomic_rename_denials=len(retry_events))
    atomic(out/'validation.json',verification)
    body='# Actual completion and delivery verification\n\n'
    body+='All **52/52** new fold-2 units at seeds 43–46 passed with actual run exit **0**. The durable coordinator and final bootstrap also exited **0**. These are completed-process receipts, not inferred status from a running worker.\n\n'
    body+='Acceptance reconciles **416 tuning +104 final =520 learned fits**, **156 point cells**, **312 interval cells**, **312 saved-model calibration/test checks**, **52 zero-fit completed resumes**, and **30 pre-fit regression checks**. There were zero tiny integration fits, historical refits, failed learned fits or repeated learned fits. All saved run files survived validation/resume unchanged. Maximum saved-model prediction discrepancy: '+str(summary['observed_max_prediction_difference'])+'.\n\n'
    body+='[Actual outer command timings/exits](actual_outer_command_receipts.csv), [machine-readable completion](validation.json), and [external receipt byte manifest](external_receipt_manifest.csv) retain the evidence. Each copied log has its actual argv, working directory, PIDs and timestamps in the accompanying receipt. The main analysis directory contains the complete per-unit command and fit journals.\n\n'
    body+=f'From the first new model command to coordinator completion: **{wall/3600:.4f} elapsed hours**. Summed model-command wall time: **{summary["actual_run_wall_seconds"]/3600:.4f} hours**; summed model-command process CPU: **{summary["actual_run_cpu_seconds"]/3600:.4f} hours**. Independent validation wall time: **{summary["validation_wall_seconds"]/60:.3f} minutes**; completed resume wall time: **{summary["resume_wall_seconds"]/60:.3f} minutes**. Maximum model-command lifetime peak RSS: **{summary["maximum_lifetime_peak_rss_MiB"]:.3f} MiB**. Parent bootstrap/coordinator elapsed times contain child commands and must not be added again. Model-phase CPU/wall, preparation, action peaks and validation CPU remain separately measured in the analysis CSVs.\n\n'
    body+='Two pre-fitting bookkeeping/diagnostic failures remain visible: the first diagnosis rejected floating-point endpoint ties, and bootstrap v1 rejected a successful quiet pytest log because it expected a prose count. Each initial command exited 1; the documented correction preserved the logs and completed without changing science or repeating fits. Subsequent independent unit checks all passed. CLI publication receipts may record authentication exit 128; separate GitHub Desktop remote-verification receipts distinguish a pending CLI attempt from a successfully published checkpoint.\n\n'
    body+=f'The existing bounded atomic-write recovery recorded **{len(retry_events)} Windows rename denial(s)**. The copied retry journal retains exact timestamps, target paths and attempts; no completed fit was repeated for this bookkeeping recovery. Runtime/cost variation includes execution conditions as well as seed-dependent selected training budgets. Persistence prediction rows are deterministic aliases; differences in their measured costs are execution variability, not independent model-training evidence.\n\n'
    body+='This finishes the **65-unit five-seed fold-2 slice**, with **70/195** cumulative paired units, **210/585** point cells and **420/1170** interval cells. Five completed additional-fold units remain separate. **125 paired units /1250 learned fits** remain in the core matched queue, alongside the broader interval-method, seasonal, operational and robustness obligations. The next bounded implementation package is the versioned `src.matched_intervals005` owner/checkpoint/joint-origin/causal-replay adapter described in [the readiness map](../../../MATCHED_METHOD_READINESS_MAP.md); its proposed real-data execution still needs separate authorization. Full-study readiness remains false.\n'
    atomic(out/'COMPLETION_VERIFICATION.md',body)
    atomic(out/'COMPLETE.json',dict(passed=True,models_fitted=0,files=tree(out)))
    print(json.dumps({k:v for k,v in verification.items() if k!='completion'},indent=2))

if __name__=='__main__':main()
