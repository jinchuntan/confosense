# ConfoSense candidature results index

This is the authoritative starting point for the completed candidature
evidence. It consolidates the scientific deliveries that were originally
published on separate review branches, including the bounded completed BDG2
one-hour operational replay.

## Integrated provenance

The submission branch `review/candidature-publication-20261002` descends from
all of the following delivery commits. Therefore the named code, compact result
artifacts, validation records, and delivery receipts are reachable from one Git
history; the earlier branches remain provenance records rather than prerequisites
for browsing the submission.

| Delivery | Integrated commit |
|---|---|
| Matched forecasting | `0c57f73618552514d41c6b78c631bd575beeebbc` |
| Interval methods and seasonal benchmark | `7544e6aba3f6a8125711f0c7e38a69ca2369bf63` |
| PLEIA energy conditional context | `80df3579dfe68ccf2c0d406c21c0fec967ff2b41` |
| PLEIA temperature conditional context | `640aa76d0c4ff47d5fea09d160bfacf488b7c5e7` |
| Robustness, contamination, and recovery | `1b94d7dc027fe2a15049c82ba3c9a721df329ece` |
| BDG2 one-hour operational replay (substantive) | `477151c0df4834fa1e26d6fbed260e0155bf5ff6` |
| BDG2 one-hour operational replay (final receipt) | `cb93a32a9e753295e313cae45ace1602e23eacb5` |

For report writing, start with the versioned
[`candidature_evidence_package_20261002_v1`](review/candidature_evidence_package_20261002_v1/),
which contains a commit-pinned evidence map, methodology facts, supported
findings, readiness assessment, and 11 consolidated CSV tables.

## Results at a glance

| Workstream | Accepted scope | Validation and delivery | Start here |
|---|---|---|---|
| Matched forecasting | 195/195 task-horizon-fold-seed units; 585/585 point cells; 1,170/1,170 own-model 90%/95% interval cells | All saved arithmetic, target identities, model reloads, independent aggregation, and zero-fit completed resumes passed; raw evidence and scoped HTTPS readback were verified | [report](review/matched_forecasting005_completion_20260923/MATCHED_FORECASTING005_CUMULATIVE_REPORT.md), [evidence index](review/matched_forecasting005_completion_20260923/EVIDENCE_INDEX.md) |
| Interval methods | 1,950/1,950 method cells; 52 completion bundles contributed the final 1,700 cells | Full corrected validation and zero-fit resume passed for every new bundle; the MAPIE 1.4.1 rank-boundary correction is retained as a separately versioned independent validator | [cumulative report](smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/CUMULATIVE_REPORT.md), [evidence index](review/matched_intervals_seasonal005_completion_20260924/EVIDENCE_INDEX.md) |
| Seasonal benchmark | 27/27 unique seasonal computations | Seed-labelled views are aliases of 27 unique computations, not extra experiments; aggregation and consistency checks passed | [point metrics](smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/seasonal_unique_point_metrics.csv), [interval metrics](smart_building_conformal/outputs/matched_intervals005/completion_52_v1_analysis/seasonal_unique_interval_metrics.csv) |
| PLEIA energy conditional context | Seeds 42–46; 68 original contexts; 2,856 fixed fault slots per seed; 856,800 event records; 60 aggregate control/rule/channel cells | Four new seeds plus reused seed 42 passed independent validation and zero-fit resume; 56 inference bounds are supported and 4 remain explicitly unavailable/degenerate | [report](review/pleia_energy_context005_multiseed_20260915/PLEIA_ENERGY_CONTEXT005_MULTISEED_REPORT.md), [60-cell table](smart_building_conformal/outputs/conditional_context005/pleia_energy_f2_context005_five_seed_analysis_v1/five_seed_control_rule_channel.csv), [completion](review/pleia_energy_context005_multiseed_20260915/COMPLETION_VERIFICATION.json) |
| PLEIA temperature conditional context | Seeds 42–46; 68 original contexts; 2,856 fixed fault slots per seed; 856,800 event records; 60 aggregate control/rule/channel cells | Four new seeds plus reused seed 42 passed independent validation and zero-fit resume; 56 inference bounds are supported and 4 remain explicitly unavailable/degenerate | [report](review/pleia_temperature_context005_multiseed_20260923/PLEIA_TEMPERATURE_CONTEXT005_FIVE_SEED_REPORT.md), [60-cell table](smart_building_conformal/outputs/conditional_context005/pleia_temperature_f2_context005_five_seed_analysis_v1/five_seed_control_rule_channel.csv), [completion](review/pleia_temperature_context005_multiseed_20260923/COMPLETION_VERIFICATION.json) |
| Robustness, contamination, and recovery | 60/60 frozen units; 900/900 cells; accepted pilot reused; 59 units newly executed | 60 independent validations and 60 zero-fit resumes passed; exact missing owners used the authorized 24 quantile-estimator fits and 8 conformalizations; raw backup and scoped publication/readback passed | [completion report](review/robustness_contamination_recovery_20260928/COMPLETION_REPORT.md), [cell metrics](review/robustness_contamination_recovery_20260928/AGGREGATE_CELL_METRICS.csv), [recovery by group](review/robustness_contamination_recovery_20260928/AGGREGATE_RECOVERY_BY_GROUP.csv), [delivery receipt](review/robustness_contamination_recovery_20260928/DELIVERY_RECEIPT.json) |
| BDG2 one-hour operational replay | 825/825 exact-owner-supported blocks; 2,475/2,475 unique evaluation rows across 165 candidate definitions | Every block passed independent validation and zero-fit resume; aggregation, D: backup, non-force publication, and commit-pinned readback passed | [operational report](review/operational005_causal_replay_20260925/OPERATIONAL_REPORT.md), [evidence index](review/operational005_causal_replay_20260925/EVIDENCE_INDEX.md), [compact metrics](smart_building_conformal/outputs/operational005_causal_replay_v2/analysis_v1/operational_metrics.csv), [delivery receipt](review/operational005_causal_replay_20260925/DELIVERY_RECEIPT.json) |

## Code and artifact accessibility

The integrated history includes the reusable implementations under
[`smart_building_conformal/src/`](smart_building_conformal/src/), frozen
protocols under [`smart_building_conformal/protocols/`](smart_building_conformal/protocols/),
and required dated adapters under the linked `review/` directories. In
particular:

- `src.matched_forecasting005`, `src.matched_intervals005`, and
  `src.conditional_context005` are available as maintained module entry points;
- the interval rank correction and import bootstrap are retained in
  `review/matched_intervals_seasonal005_completion_20260924/`;
- the exact saved-owner replay adapter, independent validator, frozen 60-unit
  crosswalk, and 900-cell protocol are retained in
  `review/robustness_contamination_recovery_20260928/`;
- the bounded operational replay adapters, candidate definitions, independent
  completion validation, and delivery receipts are retained in
  `review/operational005_causal_replay_20260925/`;
- compact reports, CSV tables, figures, manifests, and validation/delivery
  receipts linked above are tracked on the submission branch;
- bulk raw evidence remains outside the compact Git publication where specified,
  with verified backup manifests preserved by each completed delivery.

The final repository cleanup removed only verified misplaced duplicates and one
superseded stdout log; their hashes, D: preservation paths, and retained
locations are in the
[`cleanup manifest`](review/candidature_publication_20261002/CLEANUP_MANIFEST.csv).

The reviewer surface is compact, but the integrated branch history is not a
small Git diff: it contains 28,726 paths and approximately 11.61 GiB of blobs
relative to `main`, dominated by scientific streams, split archives, and other
evidence already committed by the historical review deliveries. Those objects
were retained to preserve provenance; this integration did not duplicate them,
delete them, or rewrite history. External-only evidence remains governed by the
linked backup manifests.

See the [package README](smart_building_conformal/README.md) for the maintained
module map, exact environment lock, lightweight inspection commands, and the
separate expensive reproduction entry points.

## Supported conclusions and limitations

- The evidence supports the declared, frozen experimental cells only. Completing
  the robustness extension does not establish universal robustness across all
  buildings, sensors, fault mechanisms, deployments, or distribution shifts.
- Attention-LSTM and XGBoost were compared on matched targets and supports with
  point, interval, time, and memory evidence. The results do not establish a
  general computational benefit for Attention-LSTM; any conclusion must remain
  task- and metric-specific.
- Population intervals are unavailable for the matched forecasting,
  interval-method, seasonal, and robustness summaries under the recorded
  design. Repeated seeds, overlapping folds, groups, and stream rows are not
  independent population replicates. Conditional-context bounds use the stated
  original-context block design and do not turn model seeds into new contexts.
- Conditional synthetic-fault outcomes do not estimate natural fault
  prevalence, deployment precision/F1, or universal operational feasibility.
  Unsupported and degenerate metrics remain unavailable rather than being
  imputed.
- The completed operational causal replay is limited to BDG2 at the one-hour
  horizon and the 165 candidate definitions supported by exact saved owners.
  It supplies direct alert evaluation under the recorded causal-fault design,
  not natural-fault prevalence, new-building portability, or universal
  deployment performance. The 99 definitions lacking exact higher-level owners
  remain explicitly unavailable and were not approximated.

## Inspection versus reproduction

Reading the linked Markdown, JSON, CSV, and figures is the normal reviewer path
and is zero-fit. Reproduction is a separate, expensive action governed by exact
frozen protocols and per-attempt command receipts. The generic historical
`src.run_study --all` command is not authoritative for these accepted results.
Do not restart completed coordinators or the operational replay simply to
inspect the evidence; all experimental execution remains inactive.
