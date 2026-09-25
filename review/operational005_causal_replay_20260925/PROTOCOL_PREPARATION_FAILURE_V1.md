# Preserved protocol-preparation failure

The first generated protocol draft was not used for scientific work. A pre-execution review found
that the independent validator did not add the scientific package root to its import path when
launched as its own process. That draft is preserved as `PROTOCOL_PREPARATION_FAILED_V1.json`.

No replay, conformalization, validation, checkpoint, or scientific output was created under that
draft.

A second preserved draft, `PROTOCOL_PREPARATION_FAILED_V2.json`, added the import and hash checks
but still relied on `psutil`, which is absent from the populated scientific environment. It too was
rejected before scientific work. The final preparation pins `C:\cfs_venv\Scripts\python.exe` and
uses read-only Windows process queries, avoiding package installation or upgrade. Both corrections
precede the executable `PROTOCOL.json` freeze.
