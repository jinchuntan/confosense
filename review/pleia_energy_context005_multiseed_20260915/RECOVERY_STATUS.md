# Recovery status: PLEIA-energy conditional-context multiseed batch

Snapshot verified on 16 September 2026 UTC, before recovery was launched.

The current branch is `review/pleia-energy-context005-multiseed-20260915` at `9b8fba2ea59a8fc8731a2329a8bf9e90d9495718`; `main` remains unchanged. The four-seed freeze, readiness and no-fit preflight completed before fitting.

| Unit | Verified state |
| --- | --- |
| Seed 43 | Run, independent validation and completed zero-fit resume passed. The validation recorded 61,200 checks, maximum numerical difference `1.0547118733938987e-15`, and zero validation fits. |
| Seed 44 | Interrupted during the run after 691 committed stages. The seed-44 owner fit, calibration and controls are complete and bound to model seed 44. One uncommitted non-fit partial context stage remains. |
| Seeds 45–46 | Frozen and ready; no fit started. |

The seed-44 logger recorded exit `1073807364` (`0x40010004`) at 2026-09-15 03:24:24 UTC. Windows boot records confirm a reboot at 03:28:40 UTC; the exact termination mechanism in the preceding minutes is not available. No matching coordinator, logger or scientific worker survived, and the stage journal and progress file were unchanged during a bounded post-boot observation.

The supported restart command is:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/pleia_energy_context005_multiseed_20260915/coordinator.py
```

The coordinator records the original receipt, verifies the checkpoint, classifies only this documented Windows interruption as resumable, invokes the existing `--resume-incomplete` path for seed 44, then continues the approved sequential validation, completed-resume, seeds 45–46, five-seed analysis, packaging and publication. This document is **IN_PROGRESS** and must be superseded by final completion evidence.
