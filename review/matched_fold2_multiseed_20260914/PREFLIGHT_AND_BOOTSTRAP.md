# Preflight and continuous execution

The no-fitting diagnosis is complete with no unresolved scientific correctness defect. All 52 protocols and fresh readiness checks must complete before fitting. The detached preparation and bootstrap use the installed interpreter and existing durable command logger.

Inspect the live [preflight ledger](../../smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/preflight_progress.json) and [preparation command log](../../smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/prepare_command_v1.log). The external bootstrap log is `C:/Users/nigel/ConfoSenseBackups/matched_fold2_multiseed_20260914/bootstrap_v1.log`; its `.json` receipt contains the actual exit only after completion.

The bootstrap waits on the exact live preparation process identities, requires its actual exit 0, runs thirty focused no-fit regression checks, publishes the evaluated pre-fit commit, records that commit before fitting, and invokes the durable coordinator. Preparation or test failure stops before any new model fitting; the failed logs and partial outputs remain intact.

After successful preparation, restarting the bootstrap from the repository root is:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/matched_fold2_multiseed_20260914/bootstrap.py
```

It refuses another bootstrap lock, reuses successful preflight/test receipts, and invokes the coordinator's checkpoint reconciliation. It does not automatically retry a recorded failed scientific command. If preparation itself was interrupted, inspect the frozen design and its command receipts before using `prepare.py`; never delete or overwrite a partial protocol to force progress.

Once the evaluated commit exists, [the coordinator's progress/restart record](PROGRESS_AND_RESTART.md) is authoritative for completed and remaining units. The existing `launch.ps1` launches that coordinator detached through the logger, using a fresh timestamped external log. No new chat message is required for seed-to-seed progression.
