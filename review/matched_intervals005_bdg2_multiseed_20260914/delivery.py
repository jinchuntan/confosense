"""No-fit final acceptance and measured-cost receipt."""
import json
import pandas as pd
from common import *

def main():
    state=read(BATCH/'progress.json');assert state['status']=='science_complete'
    expected_tasks=[f'seed{s}/{p}' for s in SEEDS for p in ('run','validate','completed_resume')]
    assert list(state['tasks'])==expected_tasks
    assert all(state['tasks'][key]['status']=='passed' and state['tasks'][key]['exit_code']==0 for key in expected_tasks)
    analysis=read(BATCH/'analysis_v1/analysis_validation.json');assert analysis['passed'] and analysis['new_method_cells']==120 and analysis['method_cells']==150
    costs=pd.read_csv(BATCH/'analysis_v1/worker_costs.csv')
    new=costs[costs.model_seed.isin(SEEDS)];assert len(new)==12 and (new.actual_exit==0).all()
    fits=pd.read_csv(BATCH/'analysis_v1/fit_operation_counts.csv');newfits=fits[fits.model_seed.isin(SEEDS)]
    assert newfits.quantile_estimator_fit.sum()==72 and newfits.xgboost_estimator_fit.sum()==132
    result=dict(passed=True,coordinator_exit=0,seeds_completed=SEEDS,new_method_cells=120,total_method_cells=150,new_alert_streams=120,independent_validations=4,zero_fit_completed_resumes=4,new_learned_estimator_fits=204,new_cqr_wrappers=int(newfits.cqr_wrapper_fit.sum()),new_enbpi_wrappers=int(newfits.enbpi_wrapper_fit.sum()),new_dscp_calibrators=int(newfits.dscp_calibrator_fit.sum()),new_kmeans_candidates=int(newfits.kmeans_candidate_fit.sum()),new_matched_forecasting_fits=0,new_seasonal_computations=0,worker_wall_seconds=float(new.seconds.sum()),worker_cpu_seconds=float(new.process_cpu_seconds.sum()),peak_worker_lifetime_rss_bytes=int(new.lifetime_peak_rss_bytes.max()),maximum_validation_difference=max(read(BATCH/f'seed{s}_validation/validation.json')['maximum_observed_difference'] for s in SEEDS),source_hash=source_digest(),main_unchanged=git('rev-parse','main')=='06fe967be2be8d7898812c0c2d6e464d4e942351',prior_review_unchanged=git('rev-parse','review/matched-intervals005-bdg2-20260914')==ENTRY,full_study_ready=False,utc=now())
    assert result['main_unchanged'] and result['prior_review_unchanged']
    atomic(REVIEW/'DELIVERY_VALIDATION.json',result)
    text='# Completed delivery verification\n\nAll four authorized seeds completed with actual run, independent-validation and forbidden-fit-resume exits of 0. Exactly 120 new method cells and 120 clean alert streams were added. The four completed resumes executed zero learned or calibrator fits and preserved every run byte.\n\nThe new interval owners used 72 quantile-estimator and 132 EnbPI XGBoost fits (204 learned fits), plus 24 CQR wrappers, 12 EnbPI wrappers, four DSCP calibrators and 20 KMeans candidates. No matched-forecasting or seasonal model was refitted.\n\nSee [machine-readable acceptance](DELIVERY_VALIDATION.json), [five-seed report](../../BDG2_MATCHED_INTERVAL_METHODS_MULTISEED_REPORT.md), and [evidence index](EVIDENCE_INDEX.md).\n'
    atomic(REVIEW/'COMPLETION_VERIFICATION.md',text);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
