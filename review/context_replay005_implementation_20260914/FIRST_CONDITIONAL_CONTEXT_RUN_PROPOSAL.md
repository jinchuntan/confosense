# First conditional-context real-run proposal

PLEIA energy / outer fold 2 / model seed 42 / h1 (10 minutes), fixed .95, no inner or outer challenge selection. This is a concrete execution proposal and does not authorize a real run.

The exact [68 published outer contexts](first_run_published_contexts.csv), [2,856 fault schedules](first_run_published_schedules.csv.gz) and [68 clean identities](first_run_zero_controls.csv) are included. All 21 strata, both slot seeds42/43 with signs-/+, all four controls and all five rules are retained. Rules consume shared streams; 171,360 event/control/rule/channel rows are expected before any aggregate, with null rows retained. These rows and aliases are not independent observations or model fits.

| role | matched_rows | context_rows | common_rows | matched_only | context_only | exact_row_identity |
| --- | --- | --- | --- | --- | --- | --- |
| final_fit | 14858 | 14855 | 14855 | 3 | 0 | False |
| final_calibration | 4953 | 4954 | 4953 | 0 | 1 | False |
| outer_test | 9907 | 9907 | 9907 | 0 | 0 | True |

Required computation: one new HistGradientBoosting quantile CQR wrapper containing three native estimators, each with max_iter=300; one public conformalization (two nested calls in the profiler); one fixed persistence absolute-error radius. No tuning, XGBoost, LSTM, EnbPI or DSCP fit belongs to C. Raw/CQR/rolling share this owner; persistence uses its own calibration errors. Exact role/features/source compatibility rules rule out reusing the matched owner.

Full-stream workload uses all 9,907 original eligible readings, 68.798611 asset-days, including 115 readings outside challenge tiles. It is counted once for each control/rule/channel. Contexts reset to the permitted 4,954-row historical calibration pool and their clean causal warm-up. Fitting uses 14,855 rows and 23 features. Primary meter values remain untouched.

The synthetic PLEIA context-stage extrapolation is 1665.1 seconds for at most 2,924 separately reset replay executions, based on 124 actually executed synthetic streams. These share original contexts and are not independent statistical observations. This is a scheduling calculation with substantial uncertainty from aliases, I/O and different feature count/model size. It excludes real owner fitting, final validation, preparation and publication; no real C fit cost has been measured. The synthetic cost CSV records actual phase/RSS/CPU values.

Resources: existing `C:/cfs_venv`, CPU, one OMP/OpenBLAS/MKL/NumExpr thread, sequential workers, unchanged nonblocking 3 GiB RAM reference and 8 GiB disk floor. Retain the prepared-cache hash and published context/role/input hashes. A source or dependency change requires a fresh reviewed freeze; do not reuse a changed-source readiness receipt.

After a new user instruction authorizes this exact real run, execute the activation helper and durable coordinator below. The helper refuses activation without its explicit acknowledgment flag; it copies the reviewed proposal to a separate execution manifest and preserves the proposal.

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/context_replay005_implementation_20260914/first_real_coordinator.py --acknowledge-new-user-authorization
```

The [machine manifest](first_real_run_proposal_manifest.json), [no-fit readiness](FIRST_RUN_NO_FIT_READINESS.json) and [executable coordinator](first_real_coordinator.py) fix freeze/readiness/run/validate/resume argv and unused output paths. An interrupted coordinator adopts its surviving worker; a known failed worker stops for diagnosis. Completed stages and owners are reused; an incomplete fit stage is never blindly repeated. The energy sensitivity proposal remains a separate choice and does not block this unchanged primary C endpoint.

A fresh [proposal-only freeze](../../smart_building_conformal/protocols/conditional_context005/pleia_energy_first_proposal_v3/frozen_protocol.json) and [readiness receipt](../../smart_building_conformal/protocols/conditional_context005/pleia_energy_first_proposal_v3/readiness.json) passed on the final repaired source with execution disabled. Earlier v1/v2 proposal freezes are preserved as superseded source snapshots. After authorization the coordinator creates distinct `pleia_energy_f2_s42_C_v1` protocol/output paths and `first_real_C_v1_coordinator` logs; it never activates the proposal artifact in place.
