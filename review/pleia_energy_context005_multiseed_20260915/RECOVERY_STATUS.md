# Recovery status: PLEIA-energy conditional-context multiseed batch

**Status: IN_PROGRESS.** Updated on 16 September 2026 UTC. The branch is `review/pleia-energy-context005-multiseed-20260915`; `main` remains unchanged.

| Unit | Verified state |
| --- | --- |
| Seed 43 | Run, independent validation, and completed zero-fit resume passed. Validation recorded 61,200 checks, maximum numerical difference `1.0547118733938987e-15`, and zero validation fits. |
| Seed 44 | Recovered run, independent validation, and completed zero-fit resume passed. The resumed run exit was 0 after 3,151.076 s. Validation recorded 61,200 checks, zero fits, and the same maximum reconstruction difference. The completed resume recorded zero model fits, calibrator fits, and replay updates. |
| Seed 45 | Frozen run is active under the sole coordinator worker; no duplicate worker or recovery action is present. |
| Seed 46 | Frozen and ready; no fit started. |

The original seed-44 logger recorded exit `1073807364` (`0x40010004`) at 2026-09-15 03:24:24 UTC. Windows boot records confirm a reboot at 03:28:40 UTC; the exact preceding termination mechanism is not available. The preserved checkpoint and completed stages supported the existing `--resume-incomplete` recovery path.

The sole coordinator records worker identities, preserves original receipts, performs independent validation and completed zero-fit resume for each unit, then continues the authorized sequential seeds 45–46, five-seed analysis, aggregate validation, packaging, backup, and final publication. This document will be superseded by final completion evidence.

Restart only if the coordinator is absent:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/pleia_energy_context005_multiseed_20260915/coordinator.py
```
