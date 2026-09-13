# Matched fold-2 multiseed batch progress and restart

Updated UTC: 2026-09-13T23:03:43.809189+00:00. Status: **prepared**. Validated **0/52 new paired units**; 0 point / 0 interval cells.

The atomic [progress ledger](../../smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/progress.json) and [append-only attempts](../../smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/attempts.jsonl) retain exact commands, process identities, actual exits and receipt paths. A running process is not a successful exit.

Restart from the repository with the existing environment:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/matched_fold2_multiseed_20260914/coordinator.py
```

The coordinator refuses a concurrent launch, adopts an exact surviving logger, checks frozen identities, reuses completed model checkpoints and skips verified phases. A known failed integrity command requires investigation; this command does not bypass it. An interrupted unfinished fit has no mid-fit recovery; repeated attempts remain in the fit journal and must reconcile with the independent validator. Completed evidence is never deleted.

| Order | Key: dataset / horizon / fold / seed | Status |
|---|---|---|
| 1 | pleia_energy / 1 / 2 / 43 | pending or active; see ledger |
| 2 | pleia_energy / 3 / 2 / 43 | pending or active; see ledger |
| 3 | pleia_energy / 6 / 2 / 43 | pending or active; see ledger |
| 4 | rico / 5 / 2 / 43 | pending or active; see ledger |
| 5 | rico / 15 / 2 / 43 | pending or active; see ledger |
| 6 | rico / 30 / 2 / 43 | pending or active; see ledger |
| 7 | rico / 60 / 2 / 43 | pending or active; see ledger |
| 8 | bdg2 / 1 / 2 / 43 | pending or active; see ledger |
| 9 | bdg2 / 3 / 2 / 43 | pending or active; see ledger |
| 10 | bdg2 / 6 / 2 / 43 | pending or active; see ledger |
| 11 | pleia / 1 / 2 / 43 | pending or active; see ledger |
| 12 | pleia / 3 / 2 / 43 | pending or active; see ledger |
| 13 | pleia / 6 / 2 / 43 | pending or active; see ledger |
| 14 | pleia_energy / 1 / 2 / 44 | pending or active; see ledger |
| 15 | pleia_energy / 3 / 2 / 44 | pending or active; see ledger |
| 16 | pleia_energy / 6 / 2 / 44 | pending or active; see ledger |
| 17 | rico / 5 / 2 / 44 | pending or active; see ledger |
| 18 | rico / 15 / 2 / 44 | pending or active; see ledger |
| 19 | rico / 30 / 2 / 44 | pending or active; see ledger |
| 20 | rico / 60 / 2 / 44 | pending or active; see ledger |
| 21 | bdg2 / 1 / 2 / 44 | pending or active; see ledger |
| 22 | bdg2 / 3 / 2 / 44 | pending or active; see ledger |
| 23 | bdg2 / 6 / 2 / 44 | pending or active; see ledger |
| 24 | pleia / 1 / 2 / 44 | pending or active; see ledger |
| 25 | pleia / 3 / 2 / 44 | pending or active; see ledger |
| 26 | pleia / 6 / 2 / 44 | pending or active; see ledger |
| 27 | pleia_energy / 1 / 2 / 45 | pending or active; see ledger |
| 28 | pleia_energy / 3 / 2 / 45 | pending or active; see ledger |
| 29 | pleia_energy / 6 / 2 / 45 | pending or active; see ledger |
| 30 | rico / 5 / 2 / 45 | pending or active; see ledger |
| 31 | rico / 15 / 2 / 45 | pending or active; see ledger |
| 32 | rico / 30 / 2 / 45 | pending or active; see ledger |
| 33 | rico / 60 / 2 / 45 | pending or active; see ledger |
| 34 | bdg2 / 1 / 2 / 45 | pending or active; see ledger |
| 35 | bdg2 / 3 / 2 / 45 | pending or active; see ledger |
| 36 | bdg2 / 6 / 2 / 45 | pending or active; see ledger |
| 37 | pleia / 1 / 2 / 45 | pending or active; see ledger |
| 38 | pleia / 3 / 2 / 45 | pending or active; see ledger |
| 39 | pleia / 6 / 2 / 45 | pending or active; see ledger |
| 40 | pleia_energy / 1 / 2 / 46 | pending or active; see ledger |
| 41 | pleia_energy / 3 / 2 / 46 | pending or active; see ledger |
| 42 | pleia_energy / 6 / 2 / 46 | pending or active; see ledger |
| 43 | rico / 5 / 2 / 46 | pending or active; see ledger |
| 44 | rico / 15 / 2 / 46 | pending or active; see ledger |
| 45 | rico / 30 / 2 / 46 | pending or active; see ledger |
| 46 | rico / 60 / 2 / 46 | pending or active; see ledger |
| 47 | bdg2 / 1 / 2 / 46 | pending or active; see ledger |
| 48 | bdg2 / 3 / 2 / 46 | pending or active; see ledger |
| 49 | bdg2 / 6 / 2 / 46 | pending or active; see ledger |
| 50 | pleia / 1 / 2 / 46 | pending or active; see ledger |
| 51 | pleia / 3 / 2 / 46 | pending or active; see ledger |
| 52 | pleia / 6 / 2 / 46 | pending or active; see ledger |
