> **Historical document ? status changed 13 September 2026.** This retained account predates the integration repairs. Its performance/achievement statements do not establish current findings. See `INTEGRATION_REPAIR_REPORT.md` at the repository root and `audit/integration_repair_status.json`. Historical metrics and publication markers are preserved, not revalidated.

# Limitations and validity

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is therefore estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

- No untouched holdout remains; performance is nested post-audit estimation.
- Several datasets show interval **undercoverage** under the evaluated conditions (see final_cis.csv validity flags).
- RICO high-coverage operating levels yield very wide intervals that rarely alert, so its recall/workload CIs are degenerate and low-power (only a few runs).
- Closed-loop robustness, calibration contamination and recalibration-recovery are not part of this nested run; the corresponding figures are therefore not produced.
- Point-forecast skill is used for selection but not exported per outer fold, so a point-skill figure is not built here.
- Synthetic-event incidence is a modelling choice; RICO uses a viability floor (realised > requested), recorded in event_allocation.csv.