"""Final no-fitting workload ratios, compatibility and safe replay restart evidence."""
from common import *
import numpy as np,pandas as pd
from src.context005_spec import table
from src.intervals005_common import Operations,csv
batch=SMART/'outputs/conditional_context005/synthetic_v1_coordinator';state=read(batch/'progress.json');assert state['status']=='completed'
with Operations(forbid=True):
    checked=0;summary=[]
    for ds,minutes in [('pleia_energy',10),('rico',1)]:
        run=SMART/f'outputs/conditional_context005/synthetic_{ds}_v1'
        f=table(run/'stages/tables/fullstream_workload.csv')
        np.testing.assert_allclose(f.asset_days,f.eligible_rows*minutes/1440,atol=1e-12,rtol=1e-12)
        np.testing.assert_allclose(f.episodes_per_asset_day,f.episodes/f.asset_days,atol=1e-12,rtol=1e-12)
        np.testing.assert_allclose(f.time_in_alert_days,f.alert_rows*minutes/1440,atol=1e-12,rtol=1e-12)
        checked+=len(f)*3
        v=table(run/'stages/tables/variants.csv');events=table(run/'stages/tables/events.csv.gz')
        summary.append(dict(dataset=ds,contexts=v.context_id.nunique(),fault_slots=int((v.ordinal>0).sum()),zero_controls=int((v.ordinal==0).sum()),unique_context_streams=int((~v.alias).sum()),alias_slots=int(v.alias.sum()),null_fault_slots=int(((v.ordinal>0)&v['null']).sum()),effective_fault_slots=int(((v.ordinal>0)&v.effective).sum()),event_control_rule_channel_rows=len(events)))
    # The completed original PLEIA run must match the pre-repair scientific tree.
    assert tree(SMART/'outputs/conditional_context005/synthetic_pleia_energy_v1')==read(REVIEW/'VALIDATION_REPAIR_numeric_columns.json')['old_run_scientific_tree']
    assert not (REVIEW/'first_real_execution_manifest_v1.json').exists()
    assert not (SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1').exists()
csv(REVIEW/'SYNTHETIC_SCOPE_COUNTS.csv',pd.DataFrame(summary))
atomic(REVIEW/'FINAL_NO_FIT_AUDIT.json',dict(passed=True,independently_checked_workload_values=checked,preserved_pre_repair_scientific_tree=True,actual_final_cli_passes=10,failed_validation_attempts=2,models_fitted=0,real_execution_absent=True,figure_review='PNG visually inspected; four distinct settings, five method labels, axes and nominal reference legible.'))
text='''# Completed progress and exact restart

Both synthetic freeze/readiness/run/validate/resume workflows completed. All ten final action receipts have actual exit 0. Two failed numeric-reader validation attempts are retained; they caused no extra fitting. The sequential coordinator is complete and has no active worker.

To reconcile an interrupted copy or verify completed coordinator state on this branch, run from the repository root:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/context_replay005_implementation_20260914/coordinator.py --version v1
```

The coordinator adopts exact surviving worker identities, skips passed stages and refuses a known unresolved failure. Scientific COMPLETE trees are preserved. The explicit numeric-reader compatibility applies only to completed PLEIA validation/resume and cannot authorize execution under changed source. Current RICO and real-proposal v3 freezes bind the final source.

To verify either completed unit independently again, run from `smart_building_conformal`; omit a receipt path to print the zero-fit result without overwriting evidence:

```powershell
& C:/cfs_venv/Scripts/python.exe -B -m src.conditional_context005 resume --design protocols/conditional_context005/synthetic_pleia_energy_v1 --out outputs/conditional_context005/synthetic_pleia_energy_v1 --readiness protocols/conditional_context005/synthetic_pleia_energy_v1/readiness.json
& C:/cfs_venv/Scripts/python.exe -B -m src.conditional_context005 resume --design protocols/conditional_context005/synthetic_rico_v1 --out outputs/conditional_context005/synthetic_rico_v1 --readiness protocols/conditional_context005/synthetic_rico_v1/readiness.json
```

No execution blocker remains for this implementation package. The separately proposed energy mask still needs scientific adoption. The single next execution proposal is the exact PLEIA-energy fold-2/seed-42/h1 C unit in FIRST_CONDITIONAL_CONTEXT_RUN_PROPOSAL.md. It is not launched; its future coordinator requires a new user execution instruction.
'''
atomic(REVIEW/'PROGRESS_AND_RESTART.md',text)
print('FINAL ORIGINAL-WORKLOAD AND PRESERVATION AUDIT PASSED')
