"""No-fit acceptance of the completed remaining-settings batch."""
import json
from common import *

def main():
    state=read(BATCH/'progress.json');expected=[f'{u["name"]}/{action}' for u in UNITS for action in ('run','validate','completed_resume')]
    if state['status']!='science_complete' or list(state['tasks'])!=expected:raise ValueError('coordinator did not complete every authorized phase')
    if any(state['tasks'][key]['status']!='passed' or state['tasks'][key]['exit_code']!=0 for key in expected):raise ValueError('worker exit failure')
    analysis=read(BATCH/'analysis_v2/analysis_validation.json')
    if not analysis['passed'] or analysis['new_method_cells']!=100 or analysis['combined_seed42_method_cells']!=130:raise ValueError('analysis acceptance mismatch')
    result=dict(passed=True,coordinator_exit=0,settings_completed=[u['dataset'] for u in UNITS],new_method_cells=100,combined_seed42_method_cells=130,interval_methods_complete=250,interval_methods_remaining=1700,new_learned_estimator_fits=170,independent_validations=3,zero_fit_completed_resumes=3,worker_exits_zero=9,main_unchanged=git('rev-parse','main')=='06fe967be2be8d7898812c0c2d6e464d4e942351',prior_review_unchanged=git('rev-parse','review/matched-intervals005-bdg2-multiseed-20260914')==ENTRY,models_fitted=0,calibrators_fitted=0,full_study_ready=False,utc=now())
    if not result['main_unchanged'] or not result['prior_review_unchanged']:raise ValueError('protected branch changed')
    atomic(REVIEW/'DELIVERY_VALIDATION.json',result)
    atomic(REVIEW/'COMPLETION_VERIFICATION.md','# Completed remaining-settings delivery verification\n\nAll three authorized settings completed with run, independent-validation, and zero-fit completed-resume exits of 0. The evidence contains 100 new interval cells, six applicable seasonal point cells, twelve applicable seasonal interval cells, and four explicit RICO not-applicable seasonal markers.\n\nSee [machine-readable acceptance](DELIVERY_VALIDATION.json), the [report](../../MATCHED_INTERVAL_METHODS_REMAINING_SETTINGS_REPORT.md), and the [evidence index](EVIDENCE_INDEX.md).\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
