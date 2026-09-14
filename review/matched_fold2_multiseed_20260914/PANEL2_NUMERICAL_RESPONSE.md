# Panel 2: training-seed sensitivity of Attention-LSTM versus XGBoost

| dataset | horizon | physical_minutes | target_units | seeds | mae_difference_mean | mae_difference_min | mae_difference_max | lstm_lower_mae_seeds | winkler95_difference_mean | lstm_lower_winkler95_seeds | lstm_coverage95_mean | xgboost_coverage95_mean | mpiw95_difference_mean | cpu_ratio_mean | cpu_ratio_min | cpu_ratio_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | 60 | kWh per hour | 3 | 1.58357 | 1.43653 | 1.86018 | 0 | 7.75343 | 0 | 0.949394 | 0.948653 | 5.59702 | 99.6477 | 75.2636 | 143.863 |
| bdg2 | 3 | 180 | kWh per hour | 3 | 5.19323 | 4.77752 | 5.93024 | 0 | 79.6867 | 0 | 0.949731 | 0.949076 | 32.4204 | 55.3995 | 49.558 | 62.7251 |
| bdg2 | 6 | 360 | kWh per hour | 3 | 6.5955 | 5.80442 | 8.08193 | 0 | 66.0937 | 0 | 0.951357 | 0.949394 | 35.4803 | 33.2074 | 27.9135 | 43.099 |
| pleia | 1 | 10 | degrees C | 3 | 0.894766 | 0.769482 | 1.10247 | 0 | 9.51627 | 0 | 0.284479 | 0.33764 | 1.48647 | 55.8007 | 52.788 | 57.3087 |
| pleia | 3 | 30 | degrees C | 3 | 0.255404 | 0.237183 | 0.273412 | 0 | -0.452344 | 2 | 0.274183 | 0.304869 | 0.580481 | 44.4966 | 42.0287 | 48.0702 |
| pleia | 6 | 60 | degrees C | 3 | 0.268469 | 0.126363 | 0.495218 | 0 | -3.68571 | 2 | 0.264964 | 0.322297 | 0.621395 | 27.2092 | 26.5844 | 27.869 |
| pleia_energy | 1 | 10 | kWh per 10 minutes | 3 | -0.00806256 | -0.0224386 | 0.00155544 | 2 | 0.984181 | 0 | 0.607517 | 0.787087 | -0.263983 | 26.5941 | 25.683 | 27.3256 |
| pleia_energy | 3 | 30 | kWh per 10 minutes | 3 | 0.0230005 | 0.00805599 | 0.0377919 | 0 | 0.510647 | 0 | 0.655395 | 0.752902 | -0.0648872 | 19.9152 | 18.8114 | 20.6376 |
| pleia_energy | 6 | 60 | kWh per 10 minutes | 3 | 0.0248631 | 0.0193678 | 0.028065 | 0 | 0.0265116 | 1 | 0.671949 | 0.706807 | 0.0327604 | 16.2973 | 15.9198 | 16.8268 |
| rico | 5 | 5 | degrees C | 3 | 2.24951 | 1.97957 | 2.46308 | 0 | 66.4582 | 0 | 0.135834 | 0.67054 | 1.12662 | 22.3423 | 13.716 | 27.7123 |
| rico | 15 | 15 | degrees C | 3 | 2.29411 | 1.95815 | 2.49914 | 0 | 73.8599 | 0 | 0.118973 | 0.774048 | 0.400266 | 22.8635 | 15.3419 | 30.0634 |
| rico | 30 | 30 | degrees C | 3 | 2.14796 | 1.9506 | 2.49124 | 0 | 72.2691 | 0 | 0.109604 | 0.812139 | -0.382219 | 24.8982 | 20.8793 | 28.7314 |
| rico | 60 | 60 | degrees C | 3 | 1.53031 | 1.22803 | 1.92213 | 0 | 58.1253 | 0 | 0.196313 | 0.857128 | -2.25537 | 14.6891 | 13.0042 | 17.0905 |

All seed contributions remain in the paired table. These means/ranges concern training randomness on the same support, not population uncertainty. Consistent width or score differences do not imply adequate coverage, statistical superiority or equivalence. The remaining outer folds and broader interval methods are still required.
