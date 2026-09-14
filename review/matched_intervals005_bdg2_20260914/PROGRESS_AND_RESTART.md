# Matched intervals005 durable progress and restart

Updated UTC: 2026-09-14T04:48:15.237561+00:00. Status: **blocked**. 138 scientific stages checkpointed; acceptance requires the completed independent validation and forbidden-fit resume receipts.

The [atomic progress ledger](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/progress.json), [immutable command attempts](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/attempts.jsonl), and [scientific stage journal](../../smart_building_conformal/outputs/matched_intervals005/bdg2_f2_s42_v1/stage_journal.jsonl) retain owner/calibrator/stream and live process identities.

Restart the sole coordinator from the repository using:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/matched_intervals005_bdg2_20260914/coordinator.py
```

The exclusive OS lock prevents duplicate coordinators. A surviving exact logger/worker is adopted. Known failed commands require investigation, not a blind retry. Completed fitted stages are hash-verified and reused; incomplete fit stages require explicit reconciliation. An unavailable chat callback does not interrupt the detached coordinator.

- pilot/run: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\matched_intervals005\bdg2_pilot_v1_coordinator\attempts\2026-09-14T042810811050+0000_7545aa5c\command.log.json`.
- pilot/validate: failed; actual exit 1; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\matched_intervals005\bdg2_pilot_v1_coordinator\attempts\2026-09-14T044714663329+0000_ba3bf09f\command.log.json`.

Failure: phase pilot/validate failed; actual exit 1; C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\matched_intervals005\bdg2_pilot_v1_coordinator\attempts\2026-09-14T044714663329+0000_ba3bf09f\command.log
