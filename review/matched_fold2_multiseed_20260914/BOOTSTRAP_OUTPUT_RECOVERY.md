# Bootstrap output-format recovery

All 52 fresh preflight checks completed before fitting; the preparation command exited 0. The thirty selected regression checks also exited 0, with thirty pass dots and `[100%]` in `regression_v1.log`.

The first bootstrap then exited 1 because it expected pytest's prose `30 passed` summary. The repository's quiet options suppressed that summary. This was a bootstrap output-parsing error, not a failed test or scientific defect. No new model had been fitted.

The bootstrap now accepts either the prose count or the complete thirty-dot progress line, always requiring the recorded actual exit 0 and exact command identity. Restart reuses the successful preparation and test receipts; it repeats neither preparation nor tests. The original bootstrap log and actual exit receipt remain outside OneDrive and are included in the final delivery records. Scientific source, protocols and all historical artifacts remain unchanged.
