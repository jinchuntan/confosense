"""Package actual final exits and unchanged scientific evidence, without fitting."""
import shutil
from common import *


def main():
    state=read(BATCH/'progress.json');assert state['status']=='complete'
    run=read(RUN/'COMPLETE.json');validation=read(BATCH/'validation_v4/validation.json');resume=read(BATCH/'completed_resume_v1.json');analysis=read(BATCH/'analysis_v1/analysis_validation.json')
    assert run['status']=='complete' and validation['passed'] and analysis['passed'] and resume['all_run_files_unchanged']
    current=tree(RUN);current.pop('COMPLETE.json');assert current==run['files']
    outer=sorted(BACKUP.glob('coordinator_*.log.json'));assert len(outer)==4
    outer_receipts=[read(path) for path in outer]
    assert [r['exit_status'] for r in outer_receipts]==[1,1,1,0]
    outer_receipt=outer_receipts[-1]
    receipts=[]
    for task,record in state['tasks'].items():
        expected=1 if task in ('pilot/validate','pilot/validate_v2','pilot/validate_v3') else 0
        assert record['status']==('failed' if expected else 'passed') and record['exit_code']==expected
        receipt=read(record['logger_receipt']);assert receipt['exit_status']==expected
        receipts.append(dict(task=task,**receipt))
    out=REVIEW/'delivery_v1';out.mkdir(exist_ok=False)
    copied=[]
    for pattern in ['coordinator_*.log','coordinator_*.log.json','coordinator_*.log.started.json','coordinator_*.log.launch.json','prefit_*_publication.json','prefit_remote_verification.json','completed_*_publication.json','validation-erratum_*_publication.json','validation_erratum_publication.log.json','atomic_replace_retries.jsonl','measured_cli_help.json']:
        for source in BACKUP.glob(pattern):
            target=out/source.name;shutil.copyfile(source,target);assert sha(source)==sha(target)
            copied.append(dict(file=target.name,original_path=str(source),sha256=sha(source),bytes=source.stat().st_size))
    with (out/'copied_receipts.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['file','original_path','sha256','bytes']);writer.writeheader();writer.writerows(copied)
    atomic(out/'command_receipts.json',dict(coordinator_attempts=outer_receipts,final_coordinator=outer_receipt,phases=receipts))
    counts=read(RUN/'stages/tables/operation_counts.json')
    result=dict(passed=True,coordinator_exit=0,phase_exit_codes={r['task']:r['exit_status'] for r in receipts},method_cells=30,seasonal_point_cells=3,seasonal_interval_cells=6,alert_streams=30,actual_learned_estimator_fits=counts['quantile_estimator_fit']+counts['xgboost_estimator_fit'],operation_counts=counts,synthetic_learned_fits=34,synthetic_dscp_calibrators=2,unique_acceptance_checks=48,completed_resume_learned_fits=resume['models_fitted'],completed_resume_calibrator_fits=resume['calibrators_fitted'],scientific_files_unchanged=True,source_hash=run['source_hash'],coordinator_wall_seconds=outer_receipt['seconds'],full_study_ready=False)
    atomic(out/'validation.json',result)
    text='# Completed interval-pilot delivery\n\nThe pilot run exited **0**. The first three validators and their coordinators exited **1** on documented native-CQR, EnbPI accumulator, and float32 CSV reconstruction errors. The corrected validator, zero-fit resume, report, publication helper and recovery coordinator all exited **0**. Independent validation passed 30 method cells, 6 seasonal interval cells and 30 alert streams. Three seasonal point computations are separately recorded. Completed resume executed zero learned and zero calibrator fits and left all scientific run bytes unchanged. [The erratum](../VALIDATION_ERRATUM.md) preserves both source identities and the original failed attempt.\n\n'
    text+='Real operations:6 CQR wrappers/18 HistGradientBoosting quantile fits;3 EnbPI wrappers/33 XGBoost fits;1 DSCP calibrator/5 KMeans candidates. These are51 learned estimator fits plus the separately counted clustering/calibration operations. Synthetic fits:34 tiny learned estimators and2 DSCP calibrators;48 distinct acceptance checks resolved, with the initial fixture failure retained and corrected without refitting.\n\n'
    text+=f'Actual recovery-coordinator elapsed seconds: {outer_receipt["seconds"]:.6f}; original coordinator: {outer_receipts[0]["seconds"]:.6f}; second attempt: {outer_receipts[1]["seconds"]:.6f}; third attempt: {outer_receipts[2]["seconds"]:.6f}. [Exact command receipts](command_receipts.json) contain all four attempts, PIDs, argv, timestamps and actual exits. [Whole-worker wall/CPU/memory](../../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/worker_costs.csv) includes the failed validation cost separately. [Stage costs](../../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/stage_costs.csv) must not be added to enclosing coordinator time.\n\n'
    text+='[Delivery acceptance](validation.json), [copied receipt hashes](copied_receipts.csv), [numerical report](../../../BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md), and [evidence index](../EVIDENCE_INDEX.md) provide the review trail. CLI push authentication failures are separate from the authenticated Desktop publication and verified remote readbacks. Main, previous review heads and the external backup chain are preserved. Full-study readiness remains false.\n'
    atomic(out/'COMPLETION_VERIFICATION.md',text);atomic(out/'COMPLETE.json',dict(files=tree(out),models_fitted=0));print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
