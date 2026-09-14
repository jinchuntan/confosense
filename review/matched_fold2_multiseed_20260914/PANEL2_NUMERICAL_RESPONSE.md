# Panel 2: training-seed sensitivity of Attention-LSTM versus XGBoost

| dataset | horizon | physical_minutes | target_units | seeds | mae_difference_mean | mae_difference_min | mae_difference_max | lstm_lower_mae_seeds | winkler95_difference_mean | lstm_lower_winkler95_seeds | lstm_coverage95_mean | xgboost_coverage95_mean | mpiw95_difference_mean | cpu_ratio_mean | cpu_ratio_min | cpu_ratio_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | 60 | kWh per hour | 4 | 1.56962 | 1.43653 | 1.86018 | 0 | 7.98268 | 0 | 0.949184 | 0.9486 | 4.98846 | 91.4391 | 66.8132 | 143.863 |
| bdg2 | 3 | 180 | kWh per hour | 4 | 5.63645 | 4.77752 | 6.9661 | 0 | 80.542 | 0 | 0.949776 | 0.949213 | 32.0776 | 51.5727 | 40.0923 | 62.7251 |
| bdg2 | 6 | 360 | kWh per hour | 4 | 6.81032 | 5.80442 | 8.08193 | 0 | 65.8721 | 0 | 0.951386 | 0.949365 | 33.7646 | 34.8247 | 27.9135 | 43.099 |
| pleia | 1 | 10 | degrees C | 4 | 1.01573 | 0.769482 | 1.37862 | 0 | 10.0946 | 0 | 0.285909 | 0.333274 | 1.7514 | 55.3765 | 52.788 | 57.3087 |
| pleia | 3 | 30 | degrees C | 4 | 0.238313 | 0.187038 | 0.273412 | 0 | -0.628778 | 3 | 0.280256 | 0.307636 | 0.56072 | 45.7943 | 42.0287 | 49.6875 |
| pleia | 6 | 60 | degrees C | 4 | 0.254395 | 0.126363 | 0.495218 | 0 | -3.46502 | 3 | 0.270945 | 0.316418 | 0.640784 | 27.6449 | 26.5844 | 28.952 |
| pleia_energy | 1 | 10 | kWh per 10 minutes | 4 | -0.00243225 | -0.0224386 | 0.0144587 | 2 | 0.988027 | 0 | 0.604194 | 0.782477 | -0.24046 | 26.0971 | 24.6059 | 27.3256 |
| pleia_energy | 3 | 30 | kWh per 10 minutes | 4 | 0.0259233 | 0.00805599 | 0.0377919 | 0 | 0.499007 | 0 | 0.645604 | 0.748133 | -0.0560162 | 19.6101 | 18.6947 | 20.6376 |
| pleia_energy | 6 | 60 | kWh per 10 minutes | 4 | 0.0259034 | 0.0193678 | 0.0290243 | 0 | 0.097021 | 1 | 0.657969 | 0.705965 | 0.0291362 | 17.1975 | 15.9198 | 19.8979 |
| rico | 5 | 5 | degrees C | 4 | 2.32387 | 1.97957 | 2.54696 | 0 | 68.3208 | 0 | 0.132593 | 0.675592 | 1.19032 | 21.6763 | 13.716 | 27.7123 |
| rico | 15 | 15 | degrees C | 4 | 2.34519 | 1.95815 | 2.49914 | 0 | 72.8083 | 0 | 0.129317 | 0.783295 | 0.538569 | 20.421 | 13.0932 | 30.0634 |
| rico | 30 | 30 | degrees C | 4 | 2.22348 | 1.9506 | 2.49124 | 0 | 74.9226 | 0 | 0.110963 | 0.823432 | -0.456865 | 21.8691 | 12.7816 | 28.7314 |
| rico | 60 | 60 | degrees C | 4 | 1.61473 | 1.22803 | 1.92213 | 0 | 61.251 | 0 | 0.182305 | 0.85964 | -2.27735 | 14.7689 | 13.0042 | 17.0905 |

All seed contributions remain in the paired table. These means/ranges concern training randomness on the same support, not population uncertainty. Consistent width or score differences do not imply adequate coverage, statistical superiority or equivalence. The remaining outer folds and broader interval methods are still required.
