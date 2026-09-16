# Recovery status: PLEIA-energy conditional-context multiseed batch

**Status: IN_PROGRESS — lossless raw-evidence packaging.** Updated on 17 September 2026 UTC. The branch is `review/pleia-energy-context005-multiseed-20260915`; `main` remains unchanged.

| Unit | Verified state |
| --- | --- |
| Seed 42 | Preserved historical evidence; reused without rerun. |
| Seeds 43–46 | Each run, independent validation, and completed zero-fit resume passed. Every validation recorded 61,200 checks, 2,856 scheduled fault slots, 68 contexts, zero validation fits, and maximum reconstruction difference `1.0547118733938987e-15`. Every completed resume recorded zero model fits, calibrator fits, and replay updates. |

The historical seed-44 Windows interruption was recovered through the verified checkpoint path and is distinct from the completed analysis-only repair.

The original `final/analyze` attempt failed with the receipt-bound nullable-`group_id` aggregation defect recorded in [FINAL_ANALYSIS_RECOVERY.md](FINAL_ANALYSIS_RECOVERY.md). The empty failed analysis directory was retained under a dated failure path. The repaired five-seed analysis passed without fitting: it produced 84,360 seed/context averages, 1,260 stratum rows, 60 macro comparisons, and the predeclared 2,000-draw original-context inference. Independent aggregate validation then passed.

Lossless raw packaging is active under the sole coordinator worker. It verifies every archive member before documents, backup, and final publication. This status will be superseded by final completion evidence.

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/pleia_energy_context005_multiseed_20260915/coordinator.py
```
