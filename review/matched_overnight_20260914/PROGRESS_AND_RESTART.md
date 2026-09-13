# Matched overnight batch progress and restart

Updated UTC: 2026-09-13T18:48:01.630088+00:00. Status: **unit_validated**. Validated **9/12 new paired units**; 27 point / 54 interval cells.

The atomic [progress ledger](../../smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/progress.json) and [append-only attempts](../../smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/attempts.jsonl) retain exact commands, process identities, actual exits and receipt paths. A running process is not a successful exit.

Restart from the repository with the existing environment:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/matched_overnight_20260914/coordinator.py
```

The coordinator refuses a concurrent launch, adopts an exact surviving logger, checks frozen identities, reuses completed model checkpoints and skips verified phases. A known failed integrity command requires investigation; this command does not bypass it. An interrupted unfinished fit has no mid-fit recovery; repeated attempts remain in the fit journal and must reconcile with the independent validator. Completed evidence is never deleted.

| Order | Key: dataset / horizon / fold / seed | Status |
|---|---|---|
| 1 | pleia_energy / 1 / 2 / 42 | validated |
| 2 | pleia_energy / 3 / 2 / 42 | validated |
| 3 | pleia_energy / 6 / 2 / 42 | validated |
| 4 | rico / 15 / 2 / 42 | validated |
| 5 | rico / 30 / 2 / 42 | validated |
| 6 | rico / 60 / 2 / 42 | validated |
| 7 | bdg2 / 3 / 2 / 42 | validated |
| 8 | bdg2 / 6 / 2 / 42 | validated |
| 9 | bdg2 / 1 / 1 / 42 | validated |
| 10 | pleia / 1 / 2 / 42 | pending or active; see ledger |
| 11 | pleia / 3 / 2 / 42 | pending or active; see ledger |
| 12 | pleia / 6 / 2 / 42 | pending or active; see ledger |
