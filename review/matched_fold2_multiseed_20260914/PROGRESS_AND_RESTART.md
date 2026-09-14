# Matched fold-2 multiseed batch progress and restart

Updated UTC: 2026-09-14T03:06:31.303301+00:00. Status: **complete**. Validated **52/52 new paired units**; 156 point / 312 interval cells.

The atomic [progress ledger](../../smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/progress.json) and [append-only attempts](../../smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/attempts.jsonl) retain exact commands, process identities, actual exits and receipt paths. A running process is not a successful exit.

Restart from the repository with the existing environment:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/matched_fold2_multiseed_20260914/coordinator.py
```

The coordinator refuses a concurrent launch, adopts an exact surviving logger, checks frozen identities, reuses completed model checkpoints and skips verified phases. A known failed integrity command requires investigation; this command does not bypass it. An interrupted unfinished fit has no mid-fit recovery; repeated attempts remain in the fit journal and must reconcile with the independent validator. Completed evidence is never deleted.

| Order | Key: dataset / horizon / fold / seed | Status |
|---|---|---|
| 1 | pleia_energy / 1 / 2 / 43 | validated |
| 2 | pleia_energy / 3 / 2 / 43 | validated |
| 3 | pleia_energy / 6 / 2 / 43 | validated |
| 4 | rico / 5 / 2 / 43 | validated |
| 5 | rico / 15 / 2 / 43 | validated |
| 6 | rico / 30 / 2 / 43 | validated |
| 7 | rico / 60 / 2 / 43 | validated |
| 8 | bdg2 / 1 / 2 / 43 | validated |
| 9 | bdg2 / 3 / 2 / 43 | validated |
| 10 | bdg2 / 6 / 2 / 43 | validated |
| 11 | pleia / 1 / 2 / 43 | validated |
| 12 | pleia / 3 / 2 / 43 | validated |
| 13 | pleia / 6 / 2 / 43 | validated |
| 14 | pleia_energy / 1 / 2 / 44 | validated |
| 15 | pleia_energy / 3 / 2 / 44 | validated |
| 16 | pleia_energy / 6 / 2 / 44 | validated |
| 17 | rico / 5 / 2 / 44 | validated |
| 18 | rico / 15 / 2 / 44 | validated |
| 19 | rico / 30 / 2 / 44 | validated |
| 20 | rico / 60 / 2 / 44 | validated |
| 21 | bdg2 / 1 / 2 / 44 | validated |
| 22 | bdg2 / 3 / 2 / 44 | validated |
| 23 | bdg2 / 6 / 2 / 44 | validated |
| 24 | pleia / 1 / 2 / 44 | validated |
| 25 | pleia / 3 / 2 / 44 | validated |
| 26 | pleia / 6 / 2 / 44 | validated |
| 27 | pleia_energy / 1 / 2 / 45 | validated |
| 28 | pleia_energy / 3 / 2 / 45 | validated |
| 29 | pleia_energy / 6 / 2 / 45 | validated |
| 30 | rico / 5 / 2 / 45 | validated |
| 31 | rico / 15 / 2 / 45 | validated |
| 32 | rico / 30 / 2 / 45 | validated |
| 33 | rico / 60 / 2 / 45 | validated |
| 34 | bdg2 / 1 / 2 / 45 | validated |
| 35 | bdg2 / 3 / 2 / 45 | validated |
| 36 | bdg2 / 6 / 2 / 45 | validated |
| 37 | pleia / 1 / 2 / 45 | validated |
| 38 | pleia / 3 / 2 / 45 | validated |
| 39 | pleia / 6 / 2 / 45 | validated |
| 40 | pleia_energy / 1 / 2 / 46 | validated |
| 41 | pleia_energy / 3 / 2 / 46 | validated |
| 42 | pleia_energy / 6 / 2 / 46 | validated |
| 43 | rico / 5 / 2 / 46 | validated |
| 44 | rico / 15 / 2 / 46 | validated |
| 45 | rico / 30 / 2 / 46 | validated |
| 46 | rico / 60 / 2 / 46 | validated |
| 47 | bdg2 / 1 / 2 / 46 | validated |
| 48 | bdg2 / 3 / 2 / 46 | validated |
| 49 | bdg2 / 6 / 2 / 46 | validated |
| 50 | pleia / 1 / 2 / 46 | validated |
| 51 | pleia / 3 / 2 / 46 | validated |
| 52 | pleia / 6 / 2 / 46 | validated |
