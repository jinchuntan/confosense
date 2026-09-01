# Research questions and objectives — achievement

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is therefore estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

- **RQ (interval validity):** empirical coverage is estimated with group-appropriate CIs per dataset (see final_cis.csv). Where the upper CI is below the nominal level the finding is **undercoverage**, reported as such — *partially achieved*, not asserted as guaranteed.
- **RQ (temporal alerting value):** the ablation isolates k-of-m aggregation on the same folds/catalogues; recall and background workload are reported per level. Conclusions are drawn only from the ablation table, *among the evaluated methods*.
- **RO (leakage-controlled, reproducible pipeline):** *achieved* — nested selection on inner data only, horizon embargo, group-safe state, exposure-based events, and fail-closed integrity gates, all under a hashed frozen protocol; PUBLICATION_READY.json records the lineage.
- **RO (fault-absorption / robustness):** *not evaluated in the nested engine* — the closed-loop robustness stage is not part of this end-to-end run; stated as a limitation, not a result.