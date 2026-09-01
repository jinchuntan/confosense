# Final dissertation results (corrected study)

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is therefore estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

Terminology: *synthetic-event recall* and *background alert episodes per monitored asset-day*; coverage is *empirical coverage under the evaluated time-series conditions*; BDG2 is *within-building temporal generalisation* only.

## Headline estimates with 95% CIs
### bdg2
- **macro_event_recall**: 0.373 (95% CI 0.336–0.414; n_units=10, boot=2000) [source: metrics/final_cis.csv]
- **empirical_coverage**: 0.891 (95% CI 0.865–0.915; n_units=10, boot=2000) [source: metrics/final_cis.csv]
- **background_episodes_per_asset_day**: 1.433 (95% CI 1.379–1.494; n_units=4, boot=2000) [source: metrics/final_cis.csv]

### pleia
- **macro_event_recall**: 0.663 (95% CI 0.616–0.707; n_units=23, boot=2000) [source: metrics/final_cis.csv]
- **empirical_coverage**: 0.846 (95% CI 0.743–0.934; n_units=4, boot=2000) [source: metrics/final_cis.csv]
- **background_episodes_per_asset_day**: 1.685 (95% CI 1.355–2.159; n_units=4, boot=2000) [source: metrics/final_cis.csv]

### pleia_energy
- **macro_event_recall**: 0.726 (95% CI 0.657–0.785; n_units=23, boot=2000) [source: metrics/final_cis.csv]
- **empirical_coverage**: 0.786 (95% CI 0.755–0.811; n_units=4, boot=2000) [source: metrics/final_cis.csv]
- **background_episodes_per_asset_day**: 10.441 (95% CI 7.075–13.697; n_units=4, boot=2000) [source: metrics/final_cis.csv]

### rico
- **macro_event_recall**: 0.333 (95% CI 0.333–0.333; n_units=3, boot=2000) [source: metrics/final_cis.csv]
- **empirical_coverage**: 1.000 (95% CI 1.000–1.000; n_units=3, boot=2000) [source: metrics/final_cis.csv]
- **background_episodes_per_asset_day**: 0.000 (95% CI 0.000–0.000; n_units=4, boot=2000) [source: metrics/final_cis.csv]

## Operational selection outcomes
Across outer folds: {'no_feasible_configuration': 48, 'selected': 12}. `no_feasible_configuration` is an honest abstention, not a failure — it means no candidate met the frozen recall/workload policy on inner data.

## Ablation (same outer folds and event catalogues)
- **baseline**: recall 0.613, background 5.449/asset-day
- **conformal_only**: recall 0.617, background 2.939/asset-day
- **temporal**: recall 0.544, background 2.374/asset-day
- **full**: recall 0.549, background 3.390/asset-day

## Validity flags (auto-detected)
- pleia: interval coverage upper CI 0.934 < 0.95 nominal — undercoverage under the evaluated conditions.
- pleia_energy: interval coverage upper CI 0.811 < 0.95 nominal — undercoverage under the evaluated conditions.
- rico macro_event_recall: zero-width CI over only 3 unit(s) — a degenerate, low-power estimate, not a precise one.
- rico empirical_coverage: zero-width CI over only 3 unit(s) — a degenerate, low-power estimate, not a precise one.
- rico: coverage ~1.0 — intervals so wide they rarely alert (see near-zero recall/workload).
- rico background_episodes_per_asset_day: zero-width CI over only 4 unit(s) — a degenerate, low-power estimate, not a precise one.
- bdg2: interval coverage upper CI 0.915 < 0.95 nominal — undercoverage under the evaluated conditions.

## Do-not-claim
- No universal superiority; comparisons are *among the evaluated methods*.
- No real-world fault-detection precision; the datasets carry no comprehensive fault labels.
- No unseen-building generalisation (within-building analysis only).
- SDG 11 is described only as conceptual alignment, not measured impact.
