# Recovery status: PLEIA-energy conditional-context multiseed batch

**Status: IN_PROGRESS — lossless raw-evidence package recovery.** Updated on 17 September 2026 UTC. The branch is `review/pleia-energy-context005-multiseed-20260915`; `main` remains unchanged.

All five model-seed contributions are available: seed 42 is preserved historical evidence and seeds 43–46 each passed run, independent validation, and completed zero-fit resume. Every new-seed validation recorded 61,200 checks, 2,856 scheduled fault slots, 68 contexts, zero validation fits, and maximum reconstruction difference `1.0547118733938987e-15`; every completed resume recorded zero model/calibrator fits and replay updates.

The nullable-`group_id` analysis recovery passed, producing 84,360 seed/context averages, 1,260 stratum rows, 60 macro comparisons, and the predeclared 2,000-draw inference. Independent aggregate validation passed.

The first raw packaging attempt exited 1 after 1,562.536 s at metadata creation: `from common import *` shadowed the Python `csv` module after valid seed-43 ZIP parts had been written. The exited receipt, worker record, and all 11 seed-43 partial artifacts are retained. The repair aliases the standard-library module, verifies and reuses exact existing archive members, preserves incomplete metadata under a dated failure name, and permits only this receipt-bound packaging retry. No scientific output, protocol, model, or completed validation was changed.

The coordinator will now resume packaging, then documents, backup, and final publication.

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/pleia_energy_context005_multiseed_20260915/coordinator.py
```
