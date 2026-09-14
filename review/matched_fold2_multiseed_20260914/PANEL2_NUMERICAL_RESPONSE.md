# Panel 2: training-seed sensitivity of Attention-LSTM versus XGBoost

| dataset | horizon | physical_minutes | target_units | seeds | mae_difference_mean | mae_difference_min | mae_difference_max | lstm_lower_mae_seeds | winkler95_difference_mean | lstm_lower_winkler95_seeds | lstm_coverage95_mean | xgboost_coverage95_mean | mpiw95_difference_mean | cpu_ratio_mean | cpu_ratio_min | cpu_ratio_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | 60 | kWh per hour | 2 | 1.65708 | 1.45398 | 1.86018 | 0 | 9.35897 | 0 | 0.950678 | 0.948427 | 7.57859 | 109.563 | 75.2636 | 143.863 |
| bdg2 | 3 | 180 | kWh per hour | 2 | 5.40108 | 4.87192 | 5.93024 | 0 | 83.9443 | 0 | 0.949581 | 0.949249 | 32.2121 | 51.7368 | 49.558 | 53.9156 |
| bdg2 | 6 | 360 | kWh per hour | 2 | 5.85229 | 5.80442 | 5.90016 | 0 | 67.1949 | 0 | 0.951703 | 0.949148 | 34.1383 | 35.5062 | 27.9135 | 43.099 |
| pleia | 1 | 10 | degrees C | 2 | 0.790913 | 0.769482 | 0.812343 | 0 | 6.36147 | 0 | 0.285657 | 0.330675 | 1.42749 | 55.0483 | 52.788 | 57.3087 |
| pleia | 3 | 30 | degrees C | 2 | 0.2464 | 0.237183 | 0.255618 | 0 | -1.82254 | 2 | 0.276572 | 0.297466 | 0.656816 | 42.7097 | 42.0287 | 43.3908 |
| pleia | 6 | 60 | degrees C | 2 | 0.155095 | 0.126363 | 0.183827 | 0 | -6.67871 | 2 | 0.27203 | 0.31826 | 0.559109 | 27.2267 | 26.5844 | 27.869 |
| pleia_energy | 1 | 10 | kWh per 10 minutes | 2 | -0.0128716 | -0.0224386 | -0.00330454 | 2 | 0.912773 | 0 | 0.620723 | 0.787019 | -0.276511 | 26.5043 | 25.683 | 27.3256 |
| pleia_energy | 3 | 30 | kWh per 10 minutes | 2 | 0.0229239 | 0.00805599 | 0.0377919 | 0 | 0.431303 | 0 | 0.659887 | 0.7366 | -0.0425115 | 20.4671 | 20.2966 | 20.6376 |
| pleia_energy | 6 | 60 | kWh per 10 minutes | 2 | 0.0276107 | 0.0271564 | 0.028065 | 0 | 0.0621661 | 0 | 0.665994 | 0.70758 | 0.0286874 | 16.0326 | 15.9198 | 16.1454 |
| rico | 5 | 5 | degrees C | 2 | 2.14272 | 1.97957 | 2.30588 | 0 | 62.2374 | 0 | 0.174356 | 0.704671 | 1.134 | 20.7142 | 13.716 | 27.7123 |
| rico | 15 | 15 | degrees C | 2 | 2.19159 | 1.95815 | 2.42503 | 0 | 69.6794 | 0 | 0.144772 | 0.794675 | 0.34303 | 19.2636 | 15.3419 | 23.1853 |
| rico | 30 | 30 | degrees C | 2 | 2.24665 | 2.00205 | 2.49124 | 0 | 75.836 | 0 | 0.113539 | 0.81916 | -0.398114 | 22.9816 | 20.8793 | 25.0839 |
| rico | 60 | 60 | degrees C | 2 | 1.68145 | 1.44077 | 1.92213 | 0 | 66.0907 | 0 | 0.170343 | 0.842939 | -2.23155 | 15.0473 | 13.0042 | 17.0905 |

All seed contributions remain in the paired table. These means/ranges concern training randomness on the same support, not population uncertainty. Consistent width or score differences do not imply adequate coverage, statistical superiority or equivalence. The remaining outer folds and broader interval methods are still required.
