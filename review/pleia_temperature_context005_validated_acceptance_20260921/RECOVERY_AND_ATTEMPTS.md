# Recovery and runner attempts

This file preserves acceptance-runner failures separately from scientific validation results.

1. `preflight` attempt 001 exited before opening the repository because the new runner resolved its root one parent too high (`fatal: not a git repository`). It did not create an output receipt or access the pilot.
2. `PRESERVATION_BASELINE.json` completed the exact 127,161-file integrity pass but marked validator identity false because it compared CRLF checkout bytes directly with the LF Git blob. This was a source-representation check defect, not a candidate or scientific failure.
3. `PRESERVATION_BASELINE_V2.json` correctly attempted that reconciliation but a runner helper stripped the final newline from a binary Git blob before hashing. It is retained as an invalid tooling attempt.
4. `PRESERVATION_BASELINE_V3.json` fixes the binary handling, pins the audited Git blob SHA-256, confirms the only working-tree difference is CRLF representation, and passes. It reuses the exact successful manifest hash pass rather than repeating destructive or unnecessary work.

No attempt changed `src`, a frozen protocol, the completed pilot, a model, or any fit/calibration state.
