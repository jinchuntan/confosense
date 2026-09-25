# Bounded matched interval-method and seasonal completion

All 1,950 declared method cells are present once in each native/common evaluation view: 250 accepted historical cells and 1,700 newly validated cells. All 27 unique applicable seasonal dataset/fold/horizon computations are present; 18 are new. The 135 seasonal point and 270 interval seed rows are aliases, not independent repetitions. RICO seasonal remains inapplicable.

The analyses are descriptive across fixed folds and model seeds. Overlapping observations, folds and seed aliases are not independent population replicates. No population interval, significance claim, or cross-target numerical ranking is made. Full-study readiness is false; operational-grid and robustness/contamination/recovery obligations remain.

Widths, Winkler scores, MAE and RMSE use target units: BDG2 and PLEIA energy kWh; PLEIA temperature and RICO °C. Coverage is a fraction. Native and common rows are two views of the same cells, not 3,900 experiments. Availability counts and original masks are retained in the full CSVs.

## Descriptive common-support results

| Dataset | Level | Method | Cells | Median coverage | Median width | Median Winkler | Unit |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| bdg2 | 0.90 | cqr | 45 | 0.885 | 104.758 | 159.873 | kWh |
| bdg2 | 0.90 | dscp | 45 | 0.896 | 120.611 | 203.393 | kWh |
| bdg2 | 0.90 | quantile_uncalibrated | 45 | 0.789 | 97.912 | 172.656 | kWh |
| bdg2 | 0.90 | recentred_enbpi_static | 45 | 0.902 | 147.277 | 252.795 | kWh |
| bdg2 | 0.90 | recentred_enbpi_updated | 45 | 0.888 | 124.982 | 195.536 | kWh |
| bdg2 | 0.95 | cqr | 45 | 0.950 | 135.576 | 205.166 | kWh |
| bdg2 | 0.95 | dscp | 45 | 0.946 | 164.606 | 272.202 | kWh |
| bdg2 | 0.95 | quantile_uncalibrated | 45 | 0.824 | 122.985 | 220.617 | kWh |
| bdg2 | 0.95 | recentred_enbpi_static | 45 | 0.950 | 215.874 | 333.441 | kWh |
| bdg2 | 0.95 | recentred_enbpi_updated | 45 | 0.940 | 166.247 | 244.951 | kWh |
| pleia | 0.90 | cqr | 45 | 0.807 | 3.214 | 5.419 | °C |
| pleia | 0.90 | dscp | 45 | 0.822 | 2.600 | 4.926 | °C |
| pleia | 0.90 | quantile_uncalibrated | 45 | 0.233 | 1.538 | 23.086 | °C |
| pleia | 0.90 | recentred_enbpi_static | 45 | 0.213 | 1.667 | 25.888 | °C |
| pleia | 0.90 | recentred_enbpi_updated | 45 | 0.848 | 3.655 | 5.215 | °C |
| pleia | 0.95 | cqr | 45 | 0.893 | 3.788 | 6.551 | °C |
| pleia | 0.95 | dscp | 45 | 0.897 | 3.218 | 5.750 | °C |
| pleia | 0.95 | quantile_uncalibrated | 45 | 0.264 | 2.205 | 43.811 | °C |
| pleia | 0.95 | recentred_enbpi_static | 45 | 0.262 | 2.181 | 44.378 | °C |
| pleia | 0.95 | recentred_enbpi_updated | 45 | 0.922 | 4.418 | 5.839 | °C |
| pleia_energy | 0.90 | cqr | 45 | 0.842 | 0.364 | 1.015 | kWh |
| pleia_energy | 0.90 | dscp | 45 | 0.819 | 0.702 | 1.448 | kWh |
| pleia_energy | 0.90 | quantile_uncalibrated | 45 | 0.743 | 0.341 | 1.041 | kWh |
| pleia_energy | 0.90 | recentred_enbpi_static | 45 | 0.872 | 0.693 | 1.819 | kWh |
| pleia_energy | 0.90 | recentred_enbpi_updated | 45 | 0.893 | 0.674 | 1.436 | kWh |
| pleia_energy | 0.95 | cqr | 45 | 0.946 | 0.443 | 1.727 | kWh |
| pleia_energy | 0.95 | dscp | 45 | 0.887 | 0.883 | 2.262 | kWh |
| pleia_energy | 0.95 | quantile_uncalibrated | 45 | 0.830 | 0.496 | 1.746 | kWh |
| pleia_energy | 0.95 | recentred_enbpi_static | 45 | 0.942 | 0.898 | 2.732 | kWh |
| pleia_energy | 0.95 | recentred_enbpi_updated | 45 | 0.952 | 0.885 | 2.202 | kWh |
| rico | 0.90 | cqr | 60 | 0.818 | 2.690 | 4.579 | °C |
| rico | 0.90 | dscp | 60 | 0.825 | 1.164 | 3.547 | °C |
| rico | 0.90 | quantile_uncalibrated | 60 | 0.552 | 1.852 | 6.672 | °C |
| rico | 0.90 | recentred_enbpi_static | 60 | 0.477 | 1.146 | 6.124 | °C |
| rico | 0.90 | recentred_enbpi_updated | 60 | 0.852 | 1.624 | 4.085 | °C |
| rico | 0.95 | cqr | 60 | 0.874 | 3.650 | 5.744 | °C |
| rico | 0.95 | dscp | 60 | 0.886 | 1.448 | 4.861 | °C |
| rico | 0.95 | quantile_uncalibrated | 60 | 0.647 | 2.688 | 8.748 | °C |
| rico | 0.95 | recentred_enbpi_static | 60 | 0.694 | 1.612 | 8.440 | °C |
| rico | 0.95 | recentred_enbpi_updated | 60 | 0.903 | 2.148 | 5.187 | °C |

[Common-support descriptive figure](common_support_descriptive.png) and [source hashes](figure_sources.json).

## Shared-owner comparisons

bdg2, cqr versus quantile_uncalibrated: median coverage difference +0.1096 (fraction), median width difference +7.1719 kWh, and median Winkler difference -3.2872 kWh. These are descriptive cell summaries; see the per-cell CSV for unfavorable cases.

pleia, cqr versus quantile_uncalibrated: median coverage difference +0.2221 (fraction), median width difference +1.5494 °C, and median Winkler difference -17.9429 °C. These are descriptive cell summaries; see the per-cell CSV for unfavorable cases.

pleia_energy, cqr versus quantile_uncalibrated: median coverage difference +0.1185 (fraction), median width difference +0.1092 kWh, and median Winkler difference -0.0443 kWh. These are descriptive cell summaries; see the per-cell CSV for unfavorable cases.

rico, cqr versus quantile_uncalibrated: median coverage difference +0.1836 (fraction), median width difference +0.7519 °C, and median Winkler difference -1.2662 °C. These are descriptive cell summaries; see the per-cell CSV for unfavorable cases.

bdg2, recentred_enbpi_updated versus recentred_enbpi_static: median coverage difference -0.0161 (fraction), median width difference -26.3882 kWh, and median Winkler difference -74.0360 kWh. These are descriptive cell summaries; see the per-cell CSV for unfavorable cases.

pleia, recentred_enbpi_updated versus recentred_enbpi_static: median coverage difference +0.6412 (fraction), median width difference +2.1484 °C, and median Winkler difference -29.1330 °C. These are descriptive cell summaries; see the per-cell CSV for unfavorable cases.

pleia_energy, recentred_enbpi_updated versus recentred_enbpi_static: median coverage difference +0.0129 (fraction), median width difference +0.0816 kWh, and median Winkler difference -0.0273 kWh. These are descriptive cell summaries; see the per-cell CSV for unfavorable cases.

rico, recentred_enbpi_updated versus recentred_enbpi_static: median coverage difference +0.1866 (fraction), median width difference +0.5618 °C, and median Winkler difference -2.3099 °C. These are descriptive cell summaries; see the per-cell CSV for unfavorable cases.

CQR and raw quantiles share their frozen owner. Static and updated EnbPI share their frozen EnbPI owner. DSCP reuses each exact matched XGBoost forecasting owner, so method contrasts with DSCP also change predictor. [All native cells](native_metrics.csv), [all common cells](common_metrics.csv), [paired differences](shared_owner_contrasts.csv), [unique seasonal point](seasonal_unique_point_metrics.csv) and [seasonal interval](seasonal_unique_interval_metrics.csv) retain the full evidence, including unfavorable results.

Seasonal-naive predictions use the declared daily period, each dataset/fold/horizon's own rows and pre-test calibration. Compare their saved point and interval metrics on their declared support; an alias is not a second learned computation. [Pooled clean-stream workload](background_workload_pooled.csv) reports background episodes/exposure only. Its event catalogues are empty, so recall, F1 and confirmed false-alarm rates are not estimable.

## Actual new operation ledger totals

- cqr_wrapper_fit: 340
- quantile_estimator_fit: 1020
- enbpi_wrapper_fit: 170
- xgboost_estimator_fit: 1870
- random_forest_estimator_fit: 0
- dscp_calibrator_fit: 52
- kmeans_candidate_fit: 260
- calibrator_conformalize: 1020

CQR/EnbPI wrapper counts enclose nested estimator fits; they are not additional predictive fits. The 2,890 new predictive-estimator fits are 1,020 quantile plus 1,870 XGBoost; DSCP and KMeans are separate calibrator/candidate counts. No historical forecasting refit or random-forest fallback occurred.

## Measured resources

Across the 52 new bundles, recorded run/validation/resume worker wall time summed to 15.881 hours; resume duration is present for 50/52 bundles, while both manually recovered zero-fit resumes retain pass receipts without invented durations. Measured run-stage plus validation CPU time summed to 15.095 hours; this excludes preparation, resume and process-launch overhead, so it is not a whole-batch CPU total. Peak recorded lifetime RSS was 1.165 GiB. The minimum free disk recorded at post-bundle checkpoints was 49.197 GiB; transient between-checkpoint minima are not claimed. [Per-bundle costs](new_bundle_costs.csv) retain the exact components. External backup and publication times are separately scoped.
