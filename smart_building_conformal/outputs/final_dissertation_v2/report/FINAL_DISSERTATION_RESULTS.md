# Final dissertation results (corrected, three-tier)

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

**Tiers:** *confirmed* = paired/CI-supported on adequate independent units · *descriptive* = correct arithmetic, too few independent units for a CI · *exploratory* = post-hoc or endpoint differs from the frozen one · *unsupported/prohibited* = must not be claimed.

## Feasibility (all 60 units) — *confirmed accounting*
Source: `metrics/OUTER_UNIT_LEDGER.csv`.
- **pleia**: 10/15 units feasible under the frozen policy; abstentions are `no_feasible_configuration` (first-class outcome).
- **pleia_energy**: 2/15 units feasible under the frozen policy; abstentions are `no_feasible_configuration` (first-class outcome).
- **rico**: 0/15 units feasible under the frozen policy; abstentions are `no_feasible_configuration` (first-class outcome).
- **bdg2**: 0/15 units feasible under the frozen policy; abstentions are `no_feasible_configuration` (first-class outcome).

## Headline estimates (corrected inference) — *confirmed only where a CI exists*
Source: `metrics/final_cis_corrected.csv`; seeds aggregated before inference; resampling unit = run/building/fold.
### pleia
- feasible_only · empirical_coverage: 0.794 (NA — insufficient independent groups; n=2) — *descriptive*
- feasible_only · macro_event_recall_unitmean: 0.671 (NA — insufficient independent groups; n=2) — *descriptive*
- feasible_only · background_per_asset_day: 1.236 (NA — insufficient independent groups; n=2) — *descriptive*
- all_60_units · empirical_coverage: 0.846 (NA — insufficient independent groups; n=3) — *descriptive*
- all_60_units · macro_event_recall_unitmean: 0.698 (NA — insufficient independent groups; n=3) — *descriptive*
- all_60_units · background_per_asset_day: 1.685 (NA — insufficient independent groups; n=3) — *descriptive*

### pleia_energy
- feasible_only · empirical_coverage: 0.912 (NA — insufficient independent groups; n=2) — *descriptive*
- feasible_only · macro_event_recall_unitmean: 0.456 (NA — insufficient independent groups; n=2) — *descriptive*
- feasible_only · background_per_asset_day: 0.160 (NA — insufficient independent groups; n=2) — *descriptive*
- all_60_units · empirical_coverage: 0.786 (NA — insufficient independent groups; n=3) — *descriptive*
- all_60_units · macro_event_recall_unitmean: 0.745 (NA — insufficient independent groups; n=3) — *descriptive*
- all_60_units · background_per_asset_day: 10.441 (NA — insufficient independent groups; n=3) — *descriptive*

### rico
- feasible_only: no feasible units
- all_60_units · empirical_coverage: 1.000 (NA — insufficient independent groups; n=3) — *descriptive*
- all_60_units · macro_event_recall_unitmean: 0.417 (NA — insufficient independent groups; n=3) — *descriptive*
- all_60_units · background_per_asset_day: 0.000 (NA — insufficient independent groups; n=3) — *descriptive*

### bdg2
- feasible_only: no feasible units
- all_60_units · empirical_coverage: 0.891 [0.865, 0.915] (n=10) — *confirmed*
- all_60_units · macro_event_recall_unitmean: 0.375 [0.334, 0.416] (n=10) — *confirmed*
- all_60_units · background_per_asset_day: 1.433 (NA — insufficient independent groups; n=3) — *descriptive*

## Paired ablation (12 units, seed-aggregated) — *exploratory*
Source: `metrics/PAIRED_ABLATION_EFFECTS.csv` (frozen matched-budget endpoint was not computable from the single-rule core design).
- conformal_only - baseline: Δrecall 0.0044 [-0.0557, 0.0697], Δworkload -2.5099 [-4.7433, -0.7782]
- temporal - conformal_only: Δrecall -0.0729 [-0.1373, -0.0222], Δworkload -0.5655 [-1.0337, -0.1439]
- full - baseline: Δrecall -0.064 [-0.1691, 0.0378], Δworkload -2.0593 [-3.7405, -0.8189]
- full - temporal: Δrecall 0.0045 [-0.0272, 0.0339], Δworkload 1.0161 [0.2119, 2.1094]

## Robustness extension (amendment 003) — see ROBUSTNESS_RESULTS.md

## Prohibited claims
- real-world fault precision; unseen-building portability; distribution-free guarantees as achieved; RICO CIs; sharpness/point claims from the core run; measured SDG-11 impact.
