# File-access correction 2.4

Block 1 completed replay and independent validation under protocol 2.3. While launching its
zero-fit resume, the coordinator encountered `WinError 5` when OneDrive temporarily denied the
atomic replacement of `coordinator/progress.json`. The child resume exited and no resume receipt
was written. The completed block, passing validation, failed temporary progress file, and logs are
preserved; replay and validation do not need to run again.

Revision 2.4 retries only `PermissionError` from atomic replacement, with at most two retries and a
short bounded delay. Each retry is appended to a local file-access retry ledger and exposed as a
count in progress/status. Other errors still fail immediately. No scientific code, artifacts,
metrics, identities, tolerances, or fit budgets change.
