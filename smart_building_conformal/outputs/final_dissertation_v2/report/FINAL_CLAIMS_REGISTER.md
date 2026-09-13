> **Historical document ? status changed 13 September 2026.** This retained account predates the integration repairs. Its performance/achievement statements do not establish current findings. See `INTEGRATION_REPAIR_REPORT.md` at the repository root and `audit/integration_repair_status.json`. Historical metrics and publication markers are preserved, not revalidated.

# Final claims register

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is therefore estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

| claim | status | evidence | required caveat |
|---|---|---|---|
| Conformal calibration lowers background alert workload at comparable recall | retained (among evaluated methods) | ablation baseline vs conformal_only | not a real-FP-rate; synthetic events |
| Updated recentred EnbPI is now causal & group-safe | retained | test_enbpi_causal; wired in engine | interval-quality claim only |
| Distribution-free coverage guarantee | withdrawn | observed undercoverage on several datasets | report empirical coverage only |
| Real-world fault-detection precision | withdrawn | no fault labels | use background-workload framing |
| Unseen-building portability (BDG2) | withdrawn | within-building design | within-building temporal generalisation only |