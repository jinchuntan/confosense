# Filled Result Placeholders

_Populated from the generated CSV outputs._

## Table 15 — Preliminary Dataset and Preprocessing Summary

| Item | Value |
| --- | --- |
| Dataset | PLEIAData |
| Target sensor | block B, room 11, variable V2 |
| Date range | 2021-01-01 00:10:00 – 2021-12-17 23:50:00 |
| Resample interval | 10min |
| Processed steps | 50543 |
| Outliers removed | 0 |
| Raw missing fraction | 0.0000 |
| Train steps | 30325 |
| Calibration steps | 10109 |
| Test steps | 10109 |

## Table 16 — Preliminary Point-Forecasting Performance

| Horizon | Model | MAE | RMSE | MAE std | RMSE std | MAE impr % | RMSE impr % | Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | persistence | 0.203 | 0.325 | n/a | n/a | 0.000 | 0.000 | 1 |
| 1 | seasonal_naive | 1.477 | 2.197 | n/a | n/a | -628.922 | -575.408 | 1 |
| 1 | xgboost | 0.351 | 0.507 | 0.007 | 0.008 | -73.324 | -55.760 | 5 |
| 1 | attention_lstm | 0.803 | 1.074 | 0.094 | 0.118 | -296.277 | -230.101 | 3 |
| 3 | persistence | 0.375 | 0.606 | n/a | n/a | 0.000 | 0.000 | 1 |
| 3 | seasonal_naive | 1.477 | 2.198 | n/a | n/a | -293.785 | -262.733 | 1 |
| 3 | xgboost | 0.532 | 0.728 | 0.000 | 0.000 | -41.745 | -20.217 | 5 |
| 3 | attention_lstm | 0.811 | 1.071 | 0.026 | 0.022 | -116.107 | -76.758 | 3 |
| 6 | persistence | 0.546 | 0.872 | n/a | n/a | 0.000 | 0.000 | 1 |
| 6 | seasonal_naive | 1.477 | 2.198 | n/a | n/a | -170.731 | -151.947 | 1 |
| 6 | xgboost | 0.700 | 0.953 | 0.011 | 0.009 | -28.259 | -9.284 | 5 |
| 6 | attention_lstm | 1.056 | 1.369 | 0.025 | 0.018 | -93.437 | -56.949 | 3 |

## Table 17 — Preliminary Prediction-Interval Performance

| Horizon | Method | Nominal | Empirical | Cov. dev. | Mean width | Median width | Winkler |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | CQR | 0.900 | 0.890 | 0.010 | 1.330 | 1.275 | 1.988 |
| 1 | CQR | 0.950 | 0.937 | 0.013 | 1.648 | 1.574 | 2.510 |
| 1 | EnbPI-static | 0.900 | 0.845 | 0.055 | 1.307 | 1.307 | 2.421 |
| 1 | EnbPI-static | 0.950 | 0.914 | 0.036 | 1.723 | 1.723 | 3.059 |
| 1 | EnbPI-updated | 0.900 | 0.883 | 0.017 | 1.499 | 1.550 | 2.368 |
| 1 | EnbPI-updated | 0.950 | 0.940 | 0.010 | 1.961 | 2.010 | 2.965 |
| 3 | CQR | 0.900 | 0.888 | 0.012 | 2.007 | 1.946 | 3.114 |
| 3 | CQR | 0.950 | 0.948 | 0.002 | 2.576 | 2.500 | 3.861 |
| 3 | EnbPI-static | 0.900 | 0.801 | 0.099 | 1.760 | 1.760 | 3.678 |
| 3 | EnbPI-static | 0.950 | 0.880 | 0.070 | 2.298 | 2.298 | 4.671 |
| 3 | EnbPI-updated | 0.900 | 0.871 | 0.029 | 2.139 | 2.294 | 3.491 |
| 3 | EnbPI-updated | 0.950 | 0.928 | 0.022 | 2.785 | 2.979 | 4.352 |
| 6 | CQR | 0.900 | 0.901 | 0.001 | 2.714 | 2.657 | 3.987 |
| 6 | CQR | 0.950 | 0.940 | 0.010 | 3.308 | 3.246 | 5.019 |
| 6 | EnbPI-static | 0.900 | 0.795 | 0.105 | 2.153 | 2.153 | 4.619 |
| 6 | EnbPI-static | 0.950 | 0.877 | 0.073 | 2.773 | 2.773 | 5.878 |
| 6 | EnbPI-updated | 0.900 | 0.866 | 0.034 | 2.666 | 2.867 | 4.371 |
| 6 | EnbPI-updated | 0.950 | 0.926 | 0.024 | 3.395 | 3.571 | 5.450 |

## Table 18 — Preliminary Interval-Based Alert Performance

| Scenario | Rule | TP | FP | FN | Precision | Recall | F1 | False/day | Mean delay | Median delay |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clean_test | 3-of-5 | n/a | 67 | n/a | n/a | n/a | n/a | 0.954 | n/a | n/a |
| injected_test | 3-of-5 | 17.000 | 63 | 4.000 | 0.212 | 0.810 | 0.337 | 0.898 | 42.353 | 20.000 |
