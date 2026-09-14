# Panel 2: training-seed sensitivity of Attention-LSTM versus XGBoost

| dataset | horizon | physical_minutes | target_units | seeds | mae_difference_mean | mae_difference_min | mae_difference_max | lstm_lower_mae_seeds | winkler95_difference_mean | lstm_lower_winkler95_seeds | lstm_coverage95_mean | xgboost_coverage95_mean | mpiw95_difference_mean | cpu_ratio_mean | cpu_ratio_min | cpu_ratio_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | 60 | kWh per hour | 5 | 1.70466 | 1.43653 | 2.24482 | 0 | 7.89683 | 0 | 0.949209 | 0.948839 | 4.99201 | 86.6814 | 66.8132 | 143.863 |
| bdg2 | 3 | 180 | kWh per hour | 5 | 5.24307 | 3.66955 | 6.9661 | 0 | 76.5282 | 0 | 0.950208 | 0.949284 | 30.1274 | 56.5056 | 40.0923 | 76.2373 |
| bdg2 | 6 | 360 | kWh per hour | 5 | 6.83414 | 5.80442 | 8.08193 | 0 | 64.9654 | 0 | 0.95213 | 0.949423 | 34.3412 | 34.2093 | 27.9135 | 43.099 |
| pleia | 1 | 10 | degrees C | 5 | 0.982142 | 0.769482 | 1.37862 | 0 | 8.3671 | 0 | 0.290663 | 0.329 | 1.78655 | 55.6362 | 52.788 | 57.3087 |
| pleia | 3 | 30 | degrees C | 5 | 0.296409 | 0.187038 | 0.528796 | 0 | -0.411313 | 3 | 0.275704 | 0.305118 | 0.677315 | 45.4219 | 42.0287 | 49.6875 |
| pleia | 6 | 60 | degrees C | 5 | 0.16867 | -0.174228 | 0.495218 | 1 | -5.63639 | 4 | 0.271828 | 0.306753 | 0.598746 | 27.254 | 25.6904 | 28.952 |
| pleia_energy | 1 | 10 | kWh per 10 minutes | 5 | -0.000101804 | -0.0224386 | 0.0144587 | 2 | 1.01924 | 0 | 0.604825 | 0.791501 | -0.249825 | 25.8794 | 24.6059 | 27.3256 |
| pleia_energy | 3 | 30 | kWh per 10 minutes | 5 | 0.0268554 | 0.00805599 | 0.0377919 | 0 | 0.411492 | 0 | 0.649823 | 0.739356 | -0.0378058 | 19.5171 | 18.6947 | 20.6376 |
| pleia_energy | 6 | 60 | kWh per 10 minutes | 5 | 0.0256686 | 0.0193678 | 0.0290243 | 0 | 0.0313173 | 2 | 0.662744 | 0.70213 | 0.0363251 | 17.0898 | 15.9198 | 19.8979 |
| rico | 5 | 5 | degrees C | 5 | 2.41115 | 1.97957 | 2.76027 | 0 | 68.6033 | 0 | 0.133985 | 0.679061 | 1.3587 | 21.8496 | 13.716 | 27.7123 |
| rico | 15 | 15 | degrees C | 5 | 2.44387 | 1.95815 | 2.83862 | 0 | 73.8712 | 0 | 0.128109 | 0.801715 | 0.616985 | 20.3479 | 13.0932 | 30.0634 |
| rico | 30 | 30 | degrees C | 5 | 2.35891 | 1.9506 | 2.9006 | 0 | 76.7734 | 0 | 0.108934 | 0.833494 | -0.353878 | 20.281 | 12.7816 | 28.7314 |
| rico | 60 | 60 | degrees C | 5 | 1.80038 | 1.22803 | 2.543 | 0 | 66.3679 | 0 | 0.165574 | 0.856455 | -2.1374 | 14.177 | 11.8091 | 17.0905 |

All seed contributions remain in the paired table. These means/ranges concern training randomness on the same support, not population uncertainty. Consistent width or score differences do not imply adequate coverage, statistical superiority or equivalence. The remaining outer folds and broader interval methods are still required.
