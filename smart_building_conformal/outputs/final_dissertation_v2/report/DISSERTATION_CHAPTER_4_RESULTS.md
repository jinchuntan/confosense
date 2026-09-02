# Chapter 4 — Results (dissertation draft)

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

**Tiers:** *confirmed* = paired/CI-supported on adequate independent units · *descriptive* = correct arithmetic, too few independent units for a CI · *exploratory* = post-hoc or endpoint differs from the frozen one · *unsupported/prohibited* = must not be claimed.

Structure: 4.1 data inventory (`FULL_RUN_INVENTORY.csv`); 4.2 point forecasting (fig01); 4.3 interval validity vs own nominal (fig02, `NOMINAL_COVERAGE_AUDIT.csv`) — undercoverage in 44/60 units is a central result; 4.4 method selection & feasibility (fig03, fig10) — 12/60 feasible, abstention as a scientific outcome; 4.5 alert reliability three-tier (fig06); 4.6 paired ablation (fig04, fig05); 4.7 robustness/contamination/recovery (fig07–fig09).
Every number in the chapter must be copied from the CSVs cited above; this draft intentionally contains structure plus the tiered numbers in FINAL_DISSERTATION_RESULTS.md rather than duplicating them.
