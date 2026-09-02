# Slide-ready values (corrected, three-tier)

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

- BDG2 empirical_coverage: 0.891 [0.865, 0.915] (n=10) — the only CI-supported dataset (10 buildings)
- BDG2 macro_event_recall_unitmean: 0.375 [0.334, 0.416] (n=10) — the only CI-supported dataset (10 buildings)
- BDG2 background_per_asset_day: 1.433 (NA — insufficient independent groups; n=3) — the only CI-supported dataset (10 buildings)
- pleia/pleia_energy/rico: descriptive only (3 independent units) — say 'numerically', never 'significantly'.
- Conformal vs baseline: workload -2.5099/day [-4.7433, -0.7782] at Δrecall 0.0044 [-0.0557, 0.0697] (exploratory, paired).
- Feasibility: 12/60 units; abstention reported, never hidden.
- Oral caveat for every slide: nested post-audit estimation, no pristine holdout; synthetic events, not real faults.
