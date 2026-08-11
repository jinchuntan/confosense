# ConfoSense Full Study — Results

_Every value in this document is read back from a CSV written by the pipeline under `outputs/full_study/`. No number is entered by hand._

## 1. Dataset Profiles

- **bdg2** — 10 series, 175440 observations at 0 days 01:00:00 sampling, target units `kWh`, span 2016-01-01 to 2017-12-31 23:00:00, mean target missingness 0.0000. Seasonal-naive baseline applicable: yes.
- **pleia** — 1 series, 50543 observations at 0 days 00:10:00 sampling, target units `degC`, span 2021-01-01 00:10:00 to 2021-12-17 23:50:00, mean target missingness 0.0000. Seasonal-naive baseline applicable: yes.
- **pleia_energy** — 1 series, 50545 observations at 0 days 00:10:00 sampling, target units `kWh per interval`, span 2021-01-01 to 2021-12-18, mean target missingness 0.0000. Seasonal-naive baseline applicable: yes.
- **rico** — 207 series, 49680 observations at 0 days 00:01:00 sampling, target units `degC`, span 2023-07-26 15:01:00 to 2024-05-18 07:00:00, mean target missingness 0.0000. Seasonal-naive baseline applicable: no.

## 2. Point Forecasting

- **bdg2**, horizon 1 (60 min): lowest MAE from **persistence** at 18.917 kWh (0.0% versus persistence), RMSE 37.842, over 1 seed(s).
- **bdg2**, horizon 3 (180 min): lowest MAE from **xgboost** at 28.142 kWh (21.8% versus persistence), RMSE 52.650, over 5 seed(s).
- **bdg2**, horizon 6 (360 min): lowest MAE from **xgboost** at 31.677 kWh (48.0% versus persistence), RMSE 60.063, over 5 seed(s).
- **pleia**, horizon 1 (10 min): lowest MAE from **persistence** at 0.203 degC (0.0% versus persistence), RMSE 0.325, over 1 seed(s).
- **pleia**, horizon 3 (30 min): lowest MAE from **persistence** at 0.375 degC (0.0% versus persistence), RMSE 0.606, over 1 seed(s).
- **pleia**, horizon 6 (60 min): lowest MAE from **persistence** at 0.546 degC (0.0% versus persistence), RMSE 0.872, over 1 seed(s).
- **pleia_energy**, horizon 1 (10 min): lowest MAE from **xgboost** at 0.098 kWh per interval (31.0% versus persistence), RMSE 2.451, over 5 seed(s).
- **pleia_energy**, horizon 3 (30 min): lowest MAE from **xgboost** at 0.104 kWh per interval (20.1% versus persistence), RMSE 2.452, over 5 seed(s).
- **pleia_energy**, horizon 6 (60 min): lowest MAE from **xgboost** at 0.112 kWh per interval (21.1% versus persistence), RMSE 2.452, over 5 seed(s).
- **rico**, horizon 5 (5 min): lowest MAE from **xgboost** at 0.093 degC (23.7% versus persistence), RMSE 0.126, over 5 seed(s).
- **rico**, horizon 15 (15 min): lowest MAE from **xgboost** at 0.220 degC (37.1% versus persistence), RMSE 0.320, over 5 seed(s).
- **rico**, horizon 30 (30 min): lowest MAE from **xgboost** at 0.353 degC (46.3% versus persistence), RMSE 0.515, over 5 seed(s).
- **rico**, horizon 60 (60 min): lowest MAE from **xgboost** at 0.616 degC (48.8% versus persistence), RMSE 0.904, over 5 seed(s).
- _rico, horizon 5: seasonal_naive not applicable — not applicable: no series contains a full seasonal cycle._
- _rico, horizon 15: seasonal_naive not applicable — not applicable: no series contains a full seasonal cycle._
- _rico, horizon 30: seasonal_naive not applicable — not applicable: no series contains a full seasonal cycle._
- _rico, horizon 60: seasonal_naive not applicable — not applicable: no series contains a full seasonal cycle._

## 3. Prediction Intervals

Methods are reported under their exact names: `quantile_uncalibrated` is the raw quantile band before any conformal correction, `cqr` is that band conformalized, the EnbPI variants are the documented **recentred** adaptation, and `dscp` is the dual-splitting procedure.

**bdg2**
- nominal 90%, `cqr`: mean empirical coverage 0.899 (deviation 0.003), mean width 105.404, Winkler 157.575.
- nominal 90%, `dscp`: mean empirical coverage 0.869 (deviation 0.031), mean width 105.187, Winkler 215.237.
- nominal 90%, `quantile_uncalibrated`: mean empirical coverage 0.812 (deviation 0.088), mean width 101.325, Winkler 157.590.
- nominal 90%, `recentred_enbpi_static`: mean empirical coverage 0.892 (deviation 0.008), mean width 129.827, Winkler 246.046.
- nominal 90%, `recentred_enbpi_updated`: mean empirical coverage 0.904 (deviation 0.004), mean width 139.828, Winkler 247.014.
- nominal 95%, `cqr`: mean empirical coverage 0.948 (deviation 0.003), mean width 138.853, Winkler 200.252.
- nominal 95%, `dscp`: mean empirical coverage 0.927 (deviation 0.023), mean width 147.074, Winkler 287.461.
- nominal 95%, `quantile_uncalibrated`: mean empirical coverage 0.839 (deviation 0.111), mean width 127.017, Winkler 200.203.
- nominal 95%, `recentred_enbpi_static`: mean empirical coverage 0.942 (deviation 0.008), mean width 187.279, Winkler 329.704.
- nominal 95%, `recentred_enbpi_updated`: mean empirical coverage 0.950 (deviation 0.001), mean width 203.567, Winkler 332.963.

**pleia**
- nominal 90%, `cqr`: mean empirical coverage 0.893 (deviation 0.008), mean width 2.017, Winkler 3.030.
- nominal 90%, `dscp`: mean empirical coverage 0.912 (deviation 0.023), mean width 2.211, Winkler 3.274.
- nominal 90%, `quantile_uncalibrated`: mean empirical coverage 0.804 (deviation 0.096), mean width 1.600, Winkler 3.243.
- nominal 90%, `recentred_enbpi_static`: mean empirical coverage 0.814 (deviation 0.086), mean width 1.740, Winkler 3.573.
- nominal 90%, `recentred_enbpi_updated`: mean empirical coverage 0.873 (deviation 0.027), mean width 2.101, Winkler 3.410.
- nominal 95%, `cqr`: mean empirical coverage 0.942 (deviation 0.008), mean width 2.510, Winkler 3.797.
- nominal 95%, `dscp`: mean empirical coverage 0.953 (deviation 0.013), mean width 2.846, Winkler 4.153.
- nominal 95%, `quantile_uncalibrated`: mean empirical coverage 0.880 (deviation 0.070), mean width 1.972, Winkler 4.215.
- nominal 95%, `recentred_enbpi_static`: mean empirical coverage 0.890 (deviation 0.060), mean width 2.264, Winkler 4.536.
- nominal 95%, `recentred_enbpi_updated`: mean empirical coverage 0.931 (deviation 0.019), mean width 2.714, Winkler 4.255.

**pleia_energy**
- nominal 90%, `cqr`: mean empirical coverage 0.934 (deviation 0.034), mean width 0.327, Winkler 1.014.
- nominal 90%, `dscp`: mean empirical coverage 0.969 (deviation 0.069), mean width 0.728, Winkler 1.336.
- nominal 90%, `quantile_uncalibrated`: mean empirical coverage 0.775 (deviation 0.125), mean width 0.226, Winkler 1.038.
- nominal 90%, `recentred_enbpi_static`: mean empirical coverage 0.965 (deviation 0.065), mean width 0.860, Winkler 1.505.
- nominal 90%, `recentred_enbpi_updated`: mean empirical coverage 0.905 (deviation 0.005), mean width 0.597, Winkler 1.452.
- nominal 95%, `cqr`: mean empirical coverage 0.966 (deviation 0.016), mean width 0.436, Winkler 1.658.
- nominal 95%, `dscp`: mean empirical coverage 0.984 (deviation 0.034), mean width 0.903, Winkler 2.031.
- nominal 95%, `quantile_uncalibrated`: mean empirical coverage 0.848 (deviation 0.102), mean width 0.298, Winkler 1.707.
- nominal 95%, `recentred_enbpi_static`: mean empirical coverage 0.985 (deviation 0.035), mean width 1.404, Winkler 2.546.
- nominal 95%, `recentred_enbpi_updated`: mean empirical coverage 0.951 (deviation 0.003), mean width 0.891, Winkler 2.278.

**rico**
- nominal 90%, `cqr`: mean empirical coverage 0.828 (deviation 0.072), mean width 2.049, Winkler 3.965.
- nominal 90%, `dscp`: mean empirical coverage 0.829 (deviation 0.071), mean width 1.412, Winkler 2.684.
- nominal 90%, `quantile_uncalibrated`: mean empirical coverage 0.564 (deviation 0.336), mean width 1.200, Winkler 4.773.
- nominal 90%, `recentred_enbpi_static`: mean empirical coverage 0.791 (deviation 0.109), mean width 1.018, Winkler 3.231.
- nominal 90%, `recentred_enbpi_updated`: mean empirical coverage 0.824 (deviation 0.076), mean width 1.245, Winkler 2.787.
- nominal 95%, `cqr`: mean empirical coverage 0.772 (deviation 0.178), mean width 2.498, Winkler 11.260.
- nominal 95%, `dscp`: mean empirical coverage 0.897 (deviation 0.053), mean width 1.790, Winkler 3.373.
- nominal 95%, `quantile_uncalibrated`: mean empirical coverage 0.630 (deviation 0.320), mean width 1.809, Winkler 12.682.
- nominal 95%, `recentred_enbpi_static`: mean empirical coverage 0.872 (deviation 0.078), mean width 1.427, Winkler 4.318.
- nominal 95%, `recentred_enbpi_updated`: mean empirical coverage 0.904 (deviation 0.046), mean width 1.708, Winkler 3.322.

## 4. Interval-Based Alerting

- **bdg2** — operating rule **1-of-1**, frozen on calibration data. selected on calibration data only: highest event recall among rules within the budget of 1.0 false alerts/day; ties broken by median detection delay then false-alert frequency. No test observation influenced this choice.
  On calibration: recall 0.929, precision 0.065, F1 0.121, 0.967 false alert events/day, point-level FAR 0.0625.
  On test with 42 injected events: detected 37 (recall 0.881, precision 0.025, F1 0.049), 0.986 false alert events/day, point-level FAR 0.0575, mean/median detection delay 30.8/0.0 min.
  On unmodified test data: 1.002 false alert events/day.
- **pleia** — operating rule **4-of-7**, frozen on calibration data. selected on calibration data only: highest event recall among rules within the budget of 1.0 false alerts/day; ties broken by median detection delay then false-alert frequency. No test observation influenced this choice.
  On calibration: recall 0.833, precision 0.583, F1 0.686, 0.890 false alert events/day, point-level FAR 0.0351.
  On test with 42 injected events: detected 34 (recall 0.810, precision 0.576, F1 0.673), 0.356 false alert events/day, point-level FAR 0.0132, mean/median detection delay 38.8/30.0 min.
  On unmodified test data: 0.413 false alert events/day.
- **pleia_energy** — operating rule **2-of-3**, frozen on calibration data. selected on calibration data only: highest event recall among rules within the budget of 1.0 false alerts/day; ties broken by median detection delay then false-alert frequency. No test observation influenced this choice.
  On calibration: recall 0.619, precision 0.542, F1 0.578, 0.784 false alert events/day, point-level FAR 0.0148.
  On test with 42 injected events: detected 32 (recall 0.762, precision 0.438, F1 0.557), 0.584 false alert events/day, point-level FAR 0.0102, mean/median detection delay 32.8/10.0 min.
  On unmodified test data: 0.584 false alert events/day.
- **rico** — operating rule **2-of-3**, frozen on calibration data. selected on calibration data only: highest event recall among rules no candidate met the budget of 1.0 false alerts/day, so the rule with the lowest false-alert frequency was taken; ties broken by median detection delay then false-alert frequency. No test observation influenced this choice.
  On calibration: recall 0.771, precision 0.771, F1 0.771, 3.183 false alert events/day, point-level FAR 0.0175.
  On test with 40 injected events: detected 35 (recall 0.875, precision 0.312, F1 0.461), 11.946 false alert events/day, point-level FAR 0.2077, mean/median detection delay 2.3/1.0 min.
  On unmodified test data: 12.566 false alert events/day.

_False Alarm Rate (FAR, point-level FP/(FP+TN)) and false alert events per day are distinct quantities and are reported separately throughout._

## 5. Robustness

`legacy_fixed_intervals` reproduces the preliminary behaviour (intervals frozen after injection); `closed_loop` is the primary realistic evaluation, in which the perturbation propagates into the lagged features and the model re-forecasts from the corrupted history.

- **bdg2** clean baseline: coverage 0.943, MAE 20.011, 1.002 false alerts/day.
  - `calibration_contamination`: largest coverage deviation 0.050 under `calib_contam_10pct` (empirical coverage 1.000).
  - `closed_loop`: largest coverage deviation 0.062 under `bias_2.0sd` (empirical coverage 0.888).
  - `legacy_fixed_intervals`: largest coverage deviation 0.949 under `bias_2.0sd` (empirical coverage 0.001).
- **pleia** clean baseline: coverage 0.937, MAE 0.314, 0.413 false alerts/day.
  - `calibration_contamination`: largest coverage deviation 0.050 under `calib_contam_10pct` (empirical coverage 1.000).
  - `closed_loop`: largest coverage deviation 0.692 under `bias_2.0sd` (empirical coverage 0.258).
  - `legacy_fixed_intervals`: largest coverage deviation 0.950 under `bias_2.0sd` (empirical coverage 0.000).
- **pleia_energy** clean baseline: coverage 0.973, MAE 0.093, 0.584 false alerts/day.
  - `calibration_contamination`: largest coverage deviation 0.047 under `calib_contam_10pct` (empirical coverage 0.997).
  - `closed_loop`: largest coverage deviation 0.029 under `drift_2.0sd` (empirical coverage 0.979).
  - `legacy_fixed_intervals`: largest coverage deviation 0.875 under `bias_2.0sd` (empirical coverage 0.075).
- **rico** clean baseline: coverage 0.781, MAE 0.111, 12.566 false alerts/day.
  - `calibration_contamination`: largest coverage deviation 0.050 under `calib_contam_10pct` (empirical coverage 1.000).
  - `closed_loop`: largest coverage deviation 0.501 under `drift_2.0sd` (empirical coverage 0.449).
  - `legacy_fixed_intervals`: largest coverage deviation 0.950 under `bias_1.0sd` (empirical coverage 0.000).

## 6. Recalibration

Adaptive strategies consume a residual only once its ground truth has been observed, enforced by a delayed-availability queue; for horizon *h* a residual becomes usable *h* steps after its forecast origin.

- **bdg2** `static`: coverage 0.843 (deviation 0.107), mean width 126.210, Winkler 202.331, 0 updates, residual delay 1 steps.
- **bdg2** `periodic`: coverage 0.859 (deviation 0.091), mean width 127.375, Winkler 194.025, 1460 updates, residual delay 1 steps.
- **bdg2** `rolling`: coverage 0.859 (deviation 0.091), mean width 127.375, Winkler 194.025, 1460 updates, residual delay 1 steps.
- **pleia** `static`: coverage 0.932 (deviation 0.018), mean width 1.707, Winkler 2.894, 0 updates, residual delay 1 steps.
- **pleia** `periodic`: coverage 0.939 (deviation 0.011), mean width 1.784, Winkler 2.877, 422 updates, residual delay 1 steps.
- **pleia** `rolling`: coverage 0.948 (deviation 0.002), mean width 1.891, Winkler 2.869, 422 updates, residual delay 1 steps.
- **pleia_energy** `static`: coverage 0.981 (deviation 0.031), mean width 0.941, Winkler 2.099, 0 updates, residual delay 1 steps.
- **pleia_energy** `periodic`: coverage 0.972 (deviation 0.022), mean width 0.847, Winkler 2.060, 71 updates, residual delay 1 steps.
- **pleia_energy** `rolling`: coverage 0.929 (deviation 0.021), mean width 0.458, Winkler 1.866, 71 updates, residual delay 1 steps.
- **rico** `static`: coverage 0.905 (deviation 0.045), mean width 0.536, Winkler 0.925, 0 updates, residual delay 5 steps.
- **rico** `periodic`: coverage 0.926 (deviation 0.024), mean width 0.571, Winkler 0.855, 619 updates, residual delay 5 steps.
- **rico** `rolling`: coverage 0.912 (deviation 0.038), mean width 0.529, Winkler 0.830, 619 updates, residual delay 5 steps.

## 7. Statistical Analysis

Diebold–Mariano comparisons: 48 pairwise tests, 36 significant at the 5% level after Holm adjustment.

- bdg2 h1: xgboost vs persistence — DM 16.32, p 0.0000, Holm p 0.0000 (significant).
- bdg2 h1: attention_lstm vs persistence — DM 8.29, p 0.0000, Holm p 0.0000 (significant).
- bdg2 h1: xgboost vs attention_lstm — DM 11.53, p 0.0000, Holm p 0.0000 (significant).
- bdg2 h1: seasonal_naive vs persistence — DM 49.33, p 0.0000, Holm p 0.0000 (significant).
- bdg2 h3: xgboost vs persistence — DM -21.33, p 0.0000, Holm p 0.0000 (significant).
- bdg2 h3: attention_lstm vs persistence — DM -16.29, p 0.0000, Holm p 0.0000 (significant).
- bdg2 h3: xgboost vs attention_lstm — DM -6.83, p 0.0000, Holm p 0.0000 (significant).
- bdg2 h3: seasonal_naive vs persistence — DM 0.91, p 0.3648, Holm p 0.3648.
- bdg2 h6: xgboost vs persistence — DM -37.57, p 0.0000, Holm p 0.0000 (significant).
- bdg2 h6: attention_lstm vs persistence — DM -27.18, p 0.0000, Holm p 0.0000 (significant).
- bdg2 h6: xgboost vs attention_lstm — DM -16.99, p 0.0000, Holm p 0.0000 (significant).
- bdg2 h6: seasonal_naive vs persistence — DM -27.23, p 0.0000, Holm p 0.0000 (significant).

Effect sizes (practical significance):

- bdg2 h1: xgboost vs persistence — MAE improvement -12.9%, median paired |error| difference 2.262, mean difference 95% CI [1.890, 2.970].
- bdg2 h1: attention_lstm vs persistence — MAE improvement -4.7%, median paired |error| difference 2.859, mean difference 95% CI [0.490, 1.340].
- bdg2 h1: xgboost vs attention_lstm — MAE improvement -7.7%, median paired |error| difference -0.749, mean difference 95% CI [0.948, 2.155].
- bdg2 h1: seasonal_naive vs persistence — MAE improvement -93.1%, median paired |error| difference 0.400, mean difference 95% CI [15.463, 19.716].
- bdg2 h3: xgboost vs persistence — MAE improvement 21.8%, median paired |error| difference 1.071, mean difference 95% CI [-9.158, -6.568].
- bdg2 h3: attention_lstm vs persistence — MAE improvement 16.1%, median paired |error| difference 1.480, mean difference 95% CI [-6.767, -4.800].
- bdg2 h3: xgboost vs attention_lstm — MAE improvement 6.9%, median paired |error| difference -0.358, mean difference 95% CI [-3.354, -0.844].
- bdg2 h3: seasonal_naive vs persistence — MAE improvement -1.5%, median paired |error| difference 0.000, mean difference 95% CI [-1.218, 2.477].
- bdg2 h6: xgboost vs persistence — MAE improvement 48.0%, median paired |error| difference -3.514, mean difference 95% CI [-31.863, -26.763].
- bdg2 h6: attention_lstm vs persistence — MAE improvement 33.3%, median paired |error| difference 0.057, mean difference 95% CI [-22.594, -18.193].
- bdg2 h6: xgboost vs attention_lstm — MAE improvement 22.0%, median paired |error| difference -3.663, mean difference 95% CI [-10.748, -7.184].
- bdg2 h6: seasonal_naive vs persistence — MAE improvement 40.0%, median paired |error| difference -2.110, mean difference 95% CI [-26.750, -21.759].

- Friedman test over 9 blocks and 4 methods: statistic 14.07, p 0.0028.

## 8. Cross-Dataset Findings

Raw MAE is not comparable across targets measured in degrees Celsius and kilowatt-hours, so cross-dataset statements use within-dataset rankings, percentage improvement over persistence, normalised interval width and coverage deviation.

- **bdg2** mean MAE rank: xgboost (1.67), attention_lstm (2.33), persistence (2.67), seasonal_naive (3.33).
- **pleia** mean MAE rank: persistence (1.00), xgboost (2.00), attention_lstm (3.00), seasonal_naive (4.00).
- **pleia_energy** mean MAE rank: xgboost (1.00), attention_lstm (2.00), persistence (3.00), seasonal_naive (4.00).
- **rico** mean MAE rank: xgboost (1.00), persistence (2.25), attention_lstm (2.75).

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
- `report\figures\fig_10_rico_interval_timeline.png`
- `report\figures\fig_11_bdg2_interval_timeline.png`
- `report\figures\fig_12_pleia_interval_timeline.png`
- `report\figures\fig_13_closed_loop_absorption.png`
