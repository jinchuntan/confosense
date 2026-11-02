# More alarm credit, fewer freezes caught in time

When a frozen meter reading entered the next forecast, the original ConfoSense interval model earned credit on **166 of 497** simulated freezes, up from **160** with forecasts computed on the undisturbed meter history. Yet its first alarm occurred during the changed readings on only **14** freezes, down from **76**. The reversal also appeared in both verified XGBoost test periods. The headline is a property of this evaluation on these models and disturbances. These are repeated placements on building-meter data, not independently observed breakdowns.

## Which model generated Table 6?

The submitted table compared two versions of the **same histogram gradient boosting quantile predictors**. One used their raw bounds and the other applied static MAPIE conformalized quantile regression (CQR). Both used a one-hour horizon, nominal 95% level and a single-reading alarm. The historical evaluator injected faults into the meter stream, rebuilt the lagged features and made new forecasts. The submitted workload reduction therefore stands. XGBoost was a separate point-forecast comparison with a calibrated absolute-error band. [Figure source manifest](https://github.com/jinchuntan/confosense/blob/2db2ac6a1cd708c100e1a3da7ac8ff454d54945e/report_figures/jbe_operational_20261018/SOURCE_MANIFEST.json) · [Historical evaluator](https://github.com/jinchuntan/confosense/blob/d65147ff22e6c079603eda1337630254796c8990/review/operational005_causal_replay_20260925/adapter.py) · [Quantile estimator](../../smart_building_conformal/src/conformal_cqr.py)

| Original Table 6 metric | Raw quantiles | Static CQR |
|---|---:|---:|
| Macro event recall | 0.8039 | 0.8082 |
| Episode precision | 0.2052 | 0.2577 |
| Synthetic F1 as defined in the manuscript | 0.3212 | 0.3811 |
| Background episodes per asset-day | 1.5023 | 1.1188 |
| Restricted mean detection time, minutes | 131.49 | 125.47 |

All ten entries match the submitted table after rounding. Each column averages the same 15 fold/seed cells, with 49,350 event records per method across replicates. Using unrounded rates reproduces the **25.53% reduction** in background episodes on the uninjected stream. The provenance chain runs from the submitted figure manifest through the candidate summary to the original unit metrics. [Exact reconstruction](results/table6.csv) · [Candidate summary](https://github.com/jinchuntan/confosense/blob/55e74b51eeea917ebbec9a213d7054b968f53a8b/review/operational005_high_coverage_extension_20261003/results/combined_candidate_summary.csv) · [Original 15-cell source](https://github.com/jinchuntan/confosense/blob/d65147ff22e6c079603eda1337630254796c8990/smart_building_conformal/outputs/operational005_causal_replay_v2/analysis_v1/operational_metrics.csv)

## Paired replay on the manuscript models

Each row compares identical targets, thresholds and event windows on all five original mixed-fault schedules. Only the history supplied for forecasting changes. “Credited” means a new alarm episode started between the beginning of the four-hour event slot and three hours beyond its end. At lower severities the freeze occupies only part of the slot. “During” means the first credited onset fell between the first and last readings the injection actually changed. It can be the same hour for a short event. Start times before that span, after it and misses are retained separately. Events can affect subsequent forecasts throughout the disturbed stream. All results below use numerical alarms and model seed 42.

| Model and test period | Effective freezes | Credited, clean → feedback | During, clean → feedback | Same during hits retained |
|---|---:|---:|---:|---:|
| Submitted static CQR, fold 2 on Table 6 common support | 497 | 160 → 166 | 76 → 14 | 13 of 76 |
| Archived XGBoost, fold 1 | 415 | 97 → 110 | 50 → 15 | 13 of 50 |
| Archived XGBoost, fold 2 | 497 | 118 → 132 | 59 → 16 | 15 of 59 |
| XGBoost, two folds pooled descriptively | 912 | 215 → 242 | 109 → 31 | 28 of 109 |

Of CQR's 76 previously timely hits, 38 first alerted after the altered readings and 25 missed the full window under feedback. One previously late hit became timely. For XGBoost, 65 moved later, 16 became misses and three previously missed events became timely. CQR and XGBoost share fold-2 events, so adding across model rows would double count. The earlier 23-of-343 result used different fitted policies and two BDG2 cohorts. Keep its denominators separate. [Per-event ledger](results/paired_events.csv.gz) · [Counts by fold](results/stuck_summary.csv) · [All family transitions](results/transitions.csv) · [Earlier study](../injection_feedback_20261102/README.md)

The original CQR checkpoint reproduced the archived combined-channel totals across **all seven fault families** on native support (2,672 credited of 3,378 effective events) and Table 6 common support (2,665 of 3,371). Its clean background workloads also matched (1.0718 and 1.0727 episodes per meter-day respectively). The XGBoost checkpoints matched all 69,172 archived clean test predictions exactly and both 95% bounds to numerical precision. Their background exposure was 1,015 episodes in 1,438.83 meter-days and 1,339 in 1,443.33 meter-days. Background scoring uses the same clean readings in both replay arms. With all injections disabled, the feedback pipeline reproduced every clean feature value exactly for both verified folds. Per-catalogue feature hashes identify each arm. [Model checks](results/model_checks.csv) · [Input matrix hashes](results/feature_hashes.csv)

Fold 0 had no recoverable public seed-42 booster in the archived unit. The refit matched the archived ordered fitting, calibration and test row hashes, but its test MAE was 17.0859 against 16.7126, and its calibration radius was 61.0846 against 60.7870. It contributed no replay counts. A full three-fold XGBoost claim would require the original fold-0 model or a verified reconstruction. The present test also covers one submitted CQR checkpoint among the 15 cells. [Backup inventory](https://github.com/jinchuntan/confosense/blob/2db2ac6a1cd708c100e1a3da7ac8ff454d54945e/smart_building_conformal/outputs/matched_forecasting005/core_completion_125_v1_packages/external_run_archive_manifest.csv)

## Field evidence

**A genuine reason for repeated readings.** At Harvard HouseZero, 87 of 365 candidate nights met the prespecified midnight-to-03:00 controls on the released minute series. Solar radiation stayed at or below 1 W/m², a separate PV meter stayed within 0.1 kW of zero, and both meters responded to daytime sun on the preceding and following dates. On **all 87 qualifying nights**, every one of PV meter 1's 180 reported readings was exactly 0 kW. That is 261 observed hours of physically corroborated steady output. A rule that labels any sufficiently long flatline as a fault would flag this operating regime. These windows measure a stationary PV regime at one site. They do not supply a maintenance-certified health label or a background rate for a building-consumption meter. HouseZero already describes repetition filters and nighttime exceptions. [Window definition](FIELD_CONTROLS.md) · [All candidate windows and exclusions](results/housezero_controls.csv) · [Study](https://doi.org/10.1038/s41597-026-07720-3) · [Data](https://doi.org/10.6084/m9.figshare.30260233.v1)

| Source | What the evidence establishes | What can be scored now |
|---|---|---|
| Harvard HouseZero | Table 2 links system events to maintenance or operational records. The published series replaces rejected readings with missing values. | The released power and radiation series support the steady-output controls above. The timing comparison on natural freezes requires the original readings before the filter. [Study](https://doi.org/10.1038/s41597-026-07720-3) |
| Honda Research Institute Europe | The authors document two mechanical failures of cooling-flow meter V.K21 and reconstruct flow from four downstream meters. | The public deposit lists raw measurements and issue records. This audit could access the manifest but could not retrieve the issue archive through the available download interface. Whether V.K21 repeatedly emitted a value or stopped transmitting during either failure is unverified. [Study](https://doi.org/10.1038/s41597-025-05186-3) · [Deposit](https://doi.org/10.5061/dryad.73n5tb363) |
| CSIRO Newcastle office | Seventeen experiment-log entries specify a fixed zone-temperature proxy. Eleven have overlapping telemetry, ten have complete observations, and no complete window holds any released physical zone-temperature channel within 0.05 °C of the commanded value throughout. | These are controlled BMS interventions. The logged override and the released physical channel answer different questions. No natural freeze scored. [Window results](results/csiro_incidents.csv) · [Dataset and authors' citation instructions](https://github.com/csiro-energy-systems/ahu-fault-detection-dataset) |
| South Korean office AHUs | The referenced v1 workbook contains 5,471 rows with only “Fan fault” or “Sensor fault” labels, repeated timestamps and no AHU identifier column. | This workbook supplies neither a normal class nor a verified freeze subtype with a unique equipment timeline. [Release label counts](results/korean_release_labels.csv) · [Data](https://doi.org/10.6084/m9.figshare.25909813.v1) |

**Next decisive test.** Obtain HouseZero's pre-filter minute readings for one documented server incident, spanning before failure through recovery, with the affected channel map and an independent incident start and restoration time. An alternative is Honda's manual issue record with timestamped raw V.K21 flow emissions and H1.K11, H1.K12, H1.K14 and H1.K16 during failure and healthy operation. Preserve acquisition flags to distinguish a retransmitted reading from a held display value or a stopped stream. Lock the labels and thresholds before scoring. Compare the first live alert with restoration time. A clean-history counterfactual on a natural incident additionally needs an independent reference signal. A real-electrical-load or flow control from the same system remains preferable for estimating a detector's false-alarm rate.

## Reproduction

Use the three BDG2 CSV files listed in the [matched-workload protocol](../matched_workload_20261102/protocol.json). The replay checks their SHA-256 digests and the archived model receipts. Use a checkout with the three commits in [the input preparation script](prepare_archive.py). Python 3.12 was used with pandas 2.2.3, NumPy 2.3.5, SciPy 1.17.0, scikit-learn 1.5.2, MAPIE 1.4.1, xgboost-cpu 3.2.0 and PyYAML. The original protocol records NumPy 2.1.3. The local refit exclusion above reflects the actual rerun in this environment.

```sh
d=experiments/manuscript_audit_20261102
python "$d/prepare_archive.py" "$AUDIT_WORK"
python "$d/table6.py" "$AUDIT_WORK/source" "$AUDIT_OUT/table6.csv"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python "$d/replay_models.py" "$AUDIT_WORK" "$BDG2_RAW" "$AUDIT_OUT"
python "$d/field_checks.py" "$FIELD_INPUTS" "$AUDIT_OUT"
```

Set the four path variables to local directories. For the field checks install pyarrow and xlrd. From HouseZero Figshare save Load.csv as house_load.csv and HZ_solar_radiation.csv as house_solar.csv. From the pinned [CSIRO repository](https://github.com/csiro-energy-systems/ahu-fault-detection-dataset/tree/3eb50a9ce1d4eeed778877cbfdbd259d2298d8e6) obtain the three actual Parquet files in data/ using Git LFS. Place them alongside the original combined_FDD.xls from the Korean deposit. The script checks publisher or Git LFS checksums before processing. The published folder contains derived tables. Credit the source teams and consult their data licenses for reuse, including CSIRO's CC BY-SA 4.0 terms for its data and derived incident table. [CSIRO license and attribution](https://github.com/csiro-energy-systems/ahu-fault-detection-dataset#referencing)
