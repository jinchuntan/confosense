# Preliminary Experiment: Report-Ready Results

_All values below are read directly from the CSV files in `outputs/metrics` and `outputs/data_profiles`._

## 1. Dataset and Preprocessing

The preliminary target is the indoor-temperature series (variable `V2`) of room 11 in block B of the PLEIAData dataset, resampled to a regular 10min grid over 2021-01-01 00:10:00 to 2021-12-17 23:50:00 (50543 steps). Physically implausible readings outside [15.0, 40.0] °C were removed (0 values); short gaps up to 3 steps were interpolated. The series was partitioned chronologically into 30325 training, 10109 calibration and 10109 test steps (60/20/20), with train ending 2021-07-30 14:10:00, calibration 2021-07-30 14:20:00–2021-10-08 19:00:00, and test beginning 2021-10-08 19:10:00.

## 2. Preliminary Point-Forecasting Results

At horizon 1 the lowest test MAE was achieved by **persistence** (MAE 0.203 °C, 0.0% better than persistence); the lowest RMSE by **persistence** (RMSE 0.325 °C, 0.0% better than persistence).
At horizon 3 the lowest test MAE was achieved by **persistence** (MAE 0.375 °C, 0.0% better than persistence); the lowest RMSE by **persistence** (RMSE 0.606 °C, 0.0% better than persistence).
At horizon 6 the lowest test MAE was achieved by **persistence** (MAE 0.546 °C, 0.0% better than persistence); the lowest RMSE by **persistence** (RMSE 0.872 °C, 0.0% better than persistence).

- Horizon 1 point:xgboost: MAE 0.351 (95% CI 0.334–0.370), RMSE 0.507 (95% CI 0.475–0.541).
- Horizon 3 point:xgboost: MAE 0.532 (95% CI 0.506–0.559), RMSE 0.728 (95% CI 0.682–0.778).
- Horizon 6 point:xgboost: MAE 0.700 (95% CI 0.661–0.740), RMSE 0.953 (95% CI 0.891–1.024).

## 3. Preliminary Prediction-Interval Results

**CQR**
- h1, nominal 90%: empirical coverage 0.890 (deviation 0.010), mean width 1.330 °C, Winkler 1.988.
- h1, nominal 95%: empirical coverage 0.937 (deviation 0.013), mean width 1.648 °C, Winkler 2.510.
- h3, nominal 90%: empirical coverage 0.888 (deviation 0.012), mean width 2.007 °C, Winkler 3.114.
- h3, nominal 95%: empirical coverage 0.948 (deviation 0.002), mean width 2.576 °C, Winkler 3.861.
- h6, nominal 90%: empirical coverage 0.901 (deviation 0.001), mean width 2.714 °C, Winkler 3.987.
- h6, nominal 95%: empirical coverage 0.940 (deviation 0.010), mean width 3.308 °C, Winkler 5.019.

**EnbPI-static**
- h1, nominal 90%: empirical coverage 0.845 (deviation 0.055), mean width 1.307 °C, Winkler 2.421.
- h1, nominal 95%: empirical coverage 0.914 (deviation 0.036), mean width 1.723 °C, Winkler 3.059.
- h3, nominal 90%: empirical coverage 0.801 (deviation 0.099), mean width 1.760 °C, Winkler 3.678.
- h3, nominal 95%: empirical coverage 0.880 (deviation 0.070), mean width 2.298 °C, Winkler 4.671.
- h6, nominal 90%: empirical coverage 0.795 (deviation 0.105), mean width 2.153 °C, Winkler 4.619.
- h6, nominal 95%: empirical coverage 0.877 (deviation 0.073), mean width 2.773 °C, Winkler 5.878.

**EnbPI-updated**
- h1, nominal 90%: empirical coverage 0.883 (deviation 0.017), mean width 1.499 °C, Winkler 2.368.
- h1, nominal 95%: empirical coverage 0.940 (deviation 0.010), mean width 1.961 °C, Winkler 2.965.
- h3, nominal 90%: empirical coverage 0.871 (deviation 0.029), mean width 2.139 °C, Winkler 3.491.
- h3, nominal 95%: empirical coverage 0.928 (deviation 0.022), mean width 2.785 °C, Winkler 4.352.
- h6, nominal 90%: empirical coverage 0.866 (deviation 0.034), mean width 2.666 °C, Winkler 4.371.
- h6, nominal 95%: empirical coverage 0.926 (deviation 0.024), mean width 3.395 °C, Winkler 5.450.

## 4. Preliminary Alert Results

The aggregation rule selected on the calibration set (with its own injected events) was **3-of-5**, using CQR 95% intervals at horizon 1.
On unmodified test data the rule produced 67 false-alert clusters (0.954 per day).
On test data with 21 injected events it detected 17 (recall 0.810, precision 0.212, F1 0.337), with 63 false-alert clusters (0.898/day) and mean/median detection delay 42.4/20.0 min.

## 5. Preliminary Robustness Results

_Preliminary probe only; not the full dissertation robustness study._

| Scenario | MAE | RMSE | Coverage | Width | Alert recall | False/day |
| --- | --- | --- | --- | --- | --- | --- |
| clean | 0.314 | 0.476 | 0.937 | 1.648 | n/a | 0.955 |
| missing_5pct | 0.311 | 0.471 | 0.937 | 1.642 | n/a | 1.026 |
| missing_10pct | 0.308 | 0.466 | 0.938 | 1.634 | n/a | 1.054 |
| level_shift_1sd | 0.413 | 0.557 | 0.804 | 1.694 | 1.000 | 3.320 |
| drift | 0.353 | 0.502 | 0.883 | 1.595 | 1.000 | 2.208 |

## 6. Limitations of the Preliminary Experiment

- A single room from one dataset is used; results are not yet generalised across sensors or buildings.
- The authors' processed file is already gap-filled, so the series shows no residual missingness; missing-data handling is exercised mainly through the synthetic robustness scenarios.
- Prediction intervals are held fixed when synthetic events are injected, so feedback of a perturbation into the model features is not modelled.
- EnbPI residual updating is applied per direct-horizon step and, for horizons greater than one, anticipates ground-truth availability; this is an approximation.
- Alert-rule selection optimises a simple recall / false-alert trade-off on one calibration injection; a broader operating-point study is future work.
- Seed counts for the LSTM and EnbPI are reduced relative to the ideal five because of CPU runtime (see `random_seed_log.json`).
