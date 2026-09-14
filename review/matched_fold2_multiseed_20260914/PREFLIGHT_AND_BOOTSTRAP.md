# Preflight and continuous execution

The no-fitting diagnosis, all 52 frozen protocols, fresh readiness checks, thirty regression checks, and all 52 model units are now complete. Coordinator and bootstrap v2 exited 0. [Actual completion receipts](delivery_v1/COMPLETION_VERIFICATION.md) are authoritative. The workflow below records how the detached preparation and bootstrap used the installed interpreter and durable command logger; it does not authorize another batch.

Inspect the completed [preflight ledger](../../smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/preflight_progress.json) and [preparation command log](../../smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/prepare_command_v1.log). [Bootstrap v1](delivery_v1/bootstrap_v1.log.json) exited 1 because its parser expected prose rather than pytest's successful quiet output. [Bootstrap v2](delivery_v1/bootstrap_v2.log.json) reused the successful preparation/tests and exited 0 after the batch. Both logs and the [parser recovery explanation](BOOTSTRAP_OUTPUT_RECOVERY.md) are preserved.

The bootstrap waits on the exact live preparation process identities, requires its actual exit 0, runs thirty focused no-fit regression checks, publishes the evaluated pre-fit commit, records that commit before fitting, and invokes the durable coordinator. Preparation or test failure stops before any new model fitting; the failed logs and partial outputs remain intact.

After successful preparation, restarting the bootstrap from the repository root is:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/matched_fold2_multiseed_20260914/bootstrap.py
```

It refuses another bootstrap lock, reuses successful preflight/test receipts, and invokes the coordinator's checkpoint reconciliation. It does not automatically retry a recorded failed scientific command. If preparation itself was interrupted, inspect the frozen design and its command receipts before using `prepare.py`; never delete or overwrite a partial protocol to force progress.

Once the evaluated commit exists, [the coordinator's progress/restart record](PROGRESS_AND_RESTART.md) is authoritative for completed and remaining units. The existing `launch.ps1` launches that coordinator detached through the logger, using a fresh timestamped external log. No new chat message is required for seed-to-seed progression.
