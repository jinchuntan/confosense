# Recovery status: PLEIA-energy conditional-context multiseed batch

**Status: IN_PROGRESS — final analysis recovery.** Updated on 17 September 2026 UTC. The branch is `review/pleia-energy-context005-multiseed-20260915`; `main` remains unchanged.

| Unit | Verified state |
| --- | --- |
| Seed 42 | Preserved historical evidence; reused without rerun. |
| Seeds 43–46 | Each run, independent validation, and completed zero-fit resume passed. Every validation recorded 61,200 checks, 2,856 scheduled fault slots, 68 contexts, zero validation fits, and maximum reconstruction difference `1.0547118733938987e-15`. Every completed resume recorded zero model fits, calibrator fits, and replay updates. |

The historical seed-44 Windows interruption was recovered through the verified checkpoint path and is distinct from the current analysis-only repair.

`final/analyze` exited 1 on 16 September after 240.883 s. Its receipt and command log identify a deterministic `KeyError: 'control_id'`: the PLEIA contribution table has a nullable `group_id`, and pandas default grouping dropped all rows before macro construction. The failed aggregate directory contained no files and will be retained under a dated failure path. A focused no-fit repair retains null groups, passes five regression checks, and produces 84,360 seed/context averages, 1,260 stratum rows, and all 60 required macro cells from the saved five-seed evidence. No scientific source, protocol, model output, or completed receipt changed.

The sole coordinator will rerun only `final/analyze`, then aggregate validation, packaging, documents, backup, and publication. This status will be superseded by final completion evidence.

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/pleia_energy_context005_multiseed_20260915/coordinator.py
```
