# ConfoSense Full Study — Results

_Every value in this document is read back from a CSV written by the pipeline under `outputs/full_study/`. No number is entered by hand._

> **Fast mode.** This run used `--fast` smoke-test settings (reduced horizons, seeds, search iterations, epochs and bootstrap replicates). The values below verify that the pipeline executes end to end; they are not the full-study results.

## 1. Dataset Profiles

- **pleia** — 1 series, 50543 observations at 0 days 00:10:00 sampling, target units `degC`, span 2021-01-01 00:10:00 to 2021-12-17 23:50:00, mean target missingness 0.0000. Seasonal-naive baseline applicable: yes.

## 2. Point Forecasting

- **pleia**, horizon 1 (10 min): lowest MAE from **persistence** at 0.203 degC (0.0% versus persistence), RMSE 0.325, over 1 seed(s).
- **pleia**, horizon 3 (30 min): lowest MAE from **persistence** at 0.375 degC (0.0% versus persistence), RMSE 0.606, over 1 seed(s).

## 3. Prediction Intervals

Methods are reported under their exact names: `quantile_uncalibrated` is the raw quantile band before any conformal correction, `cqr` is that band conformalized, the EnbPI variants are the documented **recentred** adaptation, and `dscp` is the dual-splitting procedure.

**pleia**
- nominal 90%, `cqr`: mean empirical coverage 0.889 (deviation 0.011), mean width 1.669, Winkler 2.551.
- nominal 90%, `dscp`: mean empirical coverage 0.926 (deviation 0.026), mean width 1.957, Winkler 2.755.
- nominal 90%, `quantile_uncalibrated`: mean empirical coverage 0.815 (deviation 0.085), mean width 1.391, Winkler 2.696.
- nominal 90%, `recentred_enbpi_static`: mean empirical coverage 0.834 (deviation 0.066), mean width 1.588, Winkler 2.975.
- nominal 90%, `recentred_enbpi_updated`: mean empirical coverage 0.885 (deviation 0.015), mean width 1.843, Winkler 2.885.
- nominal 95%, `cqr`: mean empirical coverage 0.943 (deviation 0.007), mean width 2.112, Winkler 3.186.
- nominal 95%, `dscp`: mean empirical coverage 0.962 (deviation 0.012), mean width 2.539, Winkler 3.520.
- nominal 95%, `quantile_uncalibrated`: mean empirical coverage 0.894 (deviation 0.056), mean width 1.739, Winkler 3.383.
- nominal 95%, `recentred_enbpi_static`: mean empirical coverage 0.906 (deviation 0.044), mean width 2.059, Winkler 3.781.
- nominal 95%, `recentred_enbpi_updated`: mean empirical coverage 0.938 (deviation 0.012), mean width 2.384, Winkler 3.621.

## 4. Interval-Based Alerting

- **pleia** — operating rule **4-of-7**, frozen on calibration data. selected on calibration data only: highest event recall among rules within the budget of 1.0 false alerts/day; ties broken by median detection delay then false-alert frequency. No test observation influenced this choice.
  On calibration: recall 0.821, precision 0.451, F1 0.582, 0.997 false alert events/day, point-level FAR 0.0349.
  On test with 28 injected events: detected 23 (recall 0.821, precision 0.479, F1 0.605), 0.356 false alert events/day, point-level FAR 0.0137, mean/median detection delay 41.7/30.0 min.
  On unmodified test data: 0.413 false alert events/day.

_False Alarm Rate (FAR, point-level FP/(FP+TN)) and false alert events per day are distinct quantities and are reported separately throughout._

## 5. Robustness

`legacy_fixed_intervals` reproduces the preliminary behaviour (intervals frozen after injection); `closed_loop` is the primary realistic evaluation, in which the perturbation propagates into the lagged features and the model re-forecasts from the corrupted history.

- **pleia** clean baseline: coverage 0.937, MAE 0.314, 0.413 false alerts/day.
  - `calibration_contamination`: largest coverage deviation 0.047 under `calib_contam_5pct` (empirical coverage 0.997).
  - `closed_loop`: largest coverage deviation 0.118 under `bias_1.0sd` (empirical coverage 0.832).
  - `legacy_fixed_intervals`: largest coverage deviation 0.947 under `bias_1.0sd` (empirical coverage 0.003).

## 6. Recalibration

Adaptive strategies consume a residual only once its ground truth has been observed, enforced by a delayed-availability queue; for horizon *h* a residual becomes usable *h* steps after its forecast origin.

- **pleia** `static`: coverage 0.932 (deviation 0.018), mean width 1.707, Winkler 2.894, 0 updates, residual delay 1 steps.
- **pleia** `periodic`: coverage 0.939 (deviation 0.011), mean width 1.784, Winkler 2.877, 422 updates, residual delay 1 steps.
- **pleia** `rolling`: coverage 0.948 (deviation 0.002), mean width 1.891, Winkler 2.869, 422 updates, residual delay 1 steps.

## 7. Statistical Analysis

Diebold–Mariano comparisons: 8 pairwise tests, 8 significant at the 5% level after Holm adjustment.

- pleia h1: xgboost vs persistence — DM 50.25, p 0.0000, Holm p 0.0000 (significant).
- pleia h1: attention_lstm vs persistence — DM 102.51, p 0.0000, Holm p 0.0000 (significant).
- pleia h1: xgboost vs attention_lstm — DM -88.91, p 0.0000, Holm p 0.0000 (significant).
- pleia h1: seasonal_naive vs persistence — DM 79.25, p 0.0000, Holm p 0.0000 (significant).
- pleia h3: xgboost vs persistence — DM 29.38, p 0.0000, Holm p 0.0000 (significant).
- pleia h3: attention_lstm vs persistence — DM 51.04, p 0.0000, Holm p 0.0000 (significant).
- pleia h3: xgboost vs attention_lstm — DM -39.63, p 0.0000, Holm p 0.0000 (significant).
- pleia h3: seasonal_naive vs persistence — DM 40.44, p 0.0000, Holm p 0.0000 (significant).

Effect sizes (practical significance):

- pleia h1: xgboost vs persistence — MAE improvement -75.7%, median paired |error| difference 0.107, mean difference 95% CI [0.140, 0.165].
- pleia h1: attention_lstm vs persistence — MAE improvement -411.7%, median paired |error| difference 0.669, mean difference 95% CI [0.784, 0.890].
- pleia h1: xgboost vs attention_lstm — MAE improvement 65.7%, median paired |error| difference -0.533, mean difference 95% CI [-0.736, -0.634].
- pleia h1: seasonal_naive vs persistence — MAE improvement -628.9%, median paired |error| difference 0.700, mean difference 95% CI [1.143, 1.387].
- pleia h3: xgboost vs persistence — MAE improvement -52.0%, median paired |error| difference 0.159, mean difference 95% CI [0.172, 0.216].
- pleia h3: attention_lstm vs persistence — MAE improvement -193.2%, median paired |error| difference 0.596, mean difference 95% CI [0.672, 0.792].
- pleia h3: xgboost vs attention_lstm — MAE improvement 48.2%, median paired |error| difference -0.385, mean difference 95% CI [-0.594, -0.485].
- pleia h3: seasonal_naive vs persistence — MAE improvement -293.8%, median paired |error| difference 0.500, mean difference 95% CI [0.975, 1.209].

- Friedman test not run: Friedman needs at least 3 methods and 3 complete blocks; got 4 methods over 2 blocks.

## 8. Cross-Dataset Findings

Raw MAE is not comparable across targets measured in degrees Celsius and kilowatt-hours, so cross-dataset statements use within-dataset rankings, percentage improvement over persistence, normalised interval width and coverage deviation.

- **pleia** mean MAE rank: persistence (1.00), xgboost (2.00), attention_lstm (3.00), seasonal_naive (4.00).

## 9. Figures

- `report\figures\fig_01_point_forecasting_comparison.png`
- `report\figures\fig_02_coverage_vs_width.png`
- `report\figures\fig_03_coverage_deviation_by_horizon.png`
- `report\figures\fig_04_winkler_comparison.png`
- `report\figures\fig_05_alert_rule_sensitivity.png`
- `report\figures\fig_06_alert_tradeoff.png`
- `report\figures\fig_07_robustness_degradation.png`
- `report\figures\fig_08_recalibration_recovery.png`
- `report\figures\fig_09_cross_dataset_rankings.png`
- `report\figures\fig_12_pleia_interval_timeline.png`
- `report\figures\fig_13_closed_loop_absorption.png`
