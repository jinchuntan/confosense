# ConfoSense Full Study — Table-Ready Results

_Generated from the persisted CSV outputs._

## Point forecasting

| Dataset | Target | h (steps) | h (min) | Model | MAE | RMSE | MAE sd | MAE impr % | Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | electricity | 1 | 60.000 | persistence | 18.917 | 37.842 | n/a | 0.000 | 1 |
| bdg2 | electricity | 1 | 60.000 | seasonal_naive | 36.535 | 79.070 | n/a | -93.136 | 1 |
| bdg2 | electricity | 1 | 60.000 | xgboost | 21.349 | 39.710 | 0.097 | -12.856 | 5 |
| bdg2 | electricity | 1 | 60.000 | attention_lstm | 19.865 | 35.305 | 0.999 | -5.015 | 3 |
| bdg2 | electricity | 3 | 180.000 | persistence | 35.993 | 70.023 | n/a | 0.000 | 1 |
| bdg2 | electricity | 3 | 180.000 | seasonal_naive | 36.527 | 79.076 | n/a | -1.482 | 1 |
| bdg2 | electricity | 3 | 180.000 | xgboost | 28.142 | 52.650 | 0.123 | 21.814 | 5 |
| bdg2 | electricity | 3 | 180.000 | attention_lstm | 30.278 | 57.164 | 2.636 | 15.878 | 3 |
| bdg2 | electricity | 6 | 360.000 | persistence | 60.911 | 106.777 | n/a | 0.000 | 1 |
| bdg2 | electricity | 6 | 360.000 | seasonal_naive | 36.531 | 79.099 | n/a | 40.026 | 1 |
| bdg2 | electricity | 6 | 360.000 | xgboost | 31.677 | 60.063 | 0.235 | 47.995 | 5 |
| bdg2 | electricity | 6 | 360.000 | attention_lstm | 40.704 | 75.029 | 2.950 | 33.175 | 3 |
| pleia | B-room11-V2 | 1 | 10.000 | persistence | 0.203 | 0.325 | n/a | 0.000 | 1 |
| pleia | B-room11-V2 | 1 | 10.000 | seasonal_naive | 1.477 | 2.197 | n/a | -628.922 | 1 |
| pleia | B-room11-V2 | 1 | 10.000 | xgboost | 0.343 | 0.501 | 0.007 | -69.192 | 5 |
| pleia | B-room11-V2 | 1 | 10.000 | attention_lstm | 0.803 | 1.074 | 0.094 | -296.276 | 3 |
| pleia | B-room11-V2 | 3 | 30.000 | persistence | 0.375 | 0.606 | n/a | 0.000 | 1 |
| pleia | B-room11-V2 | 3 | 30.000 | seasonal_naive | 1.477 | 2.198 | n/a | -293.785 | 1 |
| pleia | B-room11-V2 | 3 | 30.000 | xgboost | 0.532 | 0.728 | 0.000 | -41.745 | 5 |
| pleia | B-room11-V2 | 3 | 30.000 | attention_lstm | 0.813 | 1.075 | 0.025 | -116.651 | 3 |
| pleia | B-room11-V2 | 6 | 60.000 | persistence | 0.546 | 0.872 | n/a | 0.000 | 1 |
| pleia | B-room11-V2 | 6 | 60.000 | seasonal_naive | 1.477 | 2.198 | n/a | -170.731 | 1 |
| pleia | B-room11-V2 | 6 | 60.000 | xgboost | 0.693 | 0.950 | 0.010 | -27.043 | 5 |
| pleia | B-room11-V2 | 6 | 60.000 | attention_lstm | 1.057 | 1.369 | 0.025 | -93.622 | 3 |
| pleia_energy | blockB-dif_cons | 1 | 10.000 | persistence | 0.142 | 3.463 | n/a | 0.000 | 1 |
| pleia_energy | blockB-dif_cons | 1 | 10.000 | seasonal_naive | 0.198 | 3.468 | n/a | -39.848 | 1 |
| pleia_energy | blockB-dif_cons | 1 | 10.000 | xgboost | 0.098 | 2.451 | 0.000 | 31.029 | 5 |
| pleia_energy | blockB-dif_cons | 1 | 10.000 | attention_lstm | 0.102 | 2.451 | 0.003 | 28.035 | 3 |
| pleia_energy | blockB-dif_cons | 3 | 30.000 | persistence | 0.130 | 3.457 | n/a | 0.000 | 1 |
| pleia_energy | blockB-dif_cons | 3 | 30.000 | seasonal_naive | 0.198 | 3.468 | n/a | -52.069 | 1 |
| pleia_energy | blockB-dif_cons | 3 | 30.000 | xgboost | 0.104 | 2.452 | 0.000 | 20.075 | 5 |
| pleia_energy | blockB-dif_cons | 3 | 30.000 | attention_lstm | 0.106 | 2.452 | 0.001 | 18.990 | 3 |
| pleia_energy | blockB-dif_cons | 6 | 60.000 | persistence | 0.142 | 3.457 | n/a | 0.000 | 1 |
| pleia_energy | blockB-dif_cons | 6 | 60.000 | seasonal_naive | 0.198 | 3.469 | n/a | -39.970 | 1 |
| pleia_energy | blockB-dif_cons | 6 | 60.000 | xgboost | 0.112 | 2.452 | 0.000 | 21.117 | 5 |
| pleia_energy | blockB-dif_cons | 6 | 60.000 | attention_lstm | 0.115 | 2.453 | 0.003 | 18.827 | 3 |
| rico | B.RTD3 | 5 | 5.000 | persistence | 0.122 | 0.215 | n/a | 0.000 | 1 |
| rico | B.RTD3 | 5 | 5.000 | seasonal_naive | n/a | n/a | n/a | n/a | 0 |
| rico | B.RTD3 | 5 | 5.000 | xgboost | 0.093 | 0.126 | 0.000 | 23.662 | 5 |
| rico | B.RTD3 | 5 | 5.000 | attention_lstm | 0.444 | 0.547 | 0.020 | -263.654 | 3 |
| rico | B.RTD3 | 15 | 15.000 | persistence | 0.350 | 0.601 | n/a | 0.000 | 1 |
| rico | B.RTD3 | 15 | 15.000 | seasonal_naive | n/a | n/a | n/a | n/a | 0 |
| rico | B.RTD3 | 15 | 15.000 | xgboost | 0.220 | 0.320 | 0.000 | 37.107 | 5 |
| rico | B.RTD3 | 15 | 15.000 | attention_lstm | 0.519 | 0.676 | 0.072 | -48.605 | 3 |
| rico | B.RTD3 | 30 | 30.000 | persistence | 0.658 | 1.103 | n/a | 0.000 | 1 |
| rico | B.RTD3 | 30 | 30.000 | seasonal_naive | n/a | n/a | n/a | n/a | 0 |
| rico | B.RTD3 | 30 | 30.000 | xgboost | 0.353 | 0.515 | 0.015 | 46.320 | 5 |
| rico | B.RTD3 | 30 | 30.000 | attention_lstm | 0.751 | 0.945 | 0.159 | -14.118 | 3 |
| rico | B.RTD3 | 60 | 60.000 | persistence | 1.203 | 1.890 | n/a | 0.000 | 1 |
| rico | B.RTD3 | 60 | 60.000 | seasonal_naive | n/a | n/a | n/a | n/a | 0 |
| rico | B.RTD3 | 60 | 60.000 | xgboost | 0.616 | 0.904 | 0.009 | 48.765 | 5 |
| rico | B.RTD3 | 60 | 60.000 | attention_lstm | 0.924 | 1.165 | 0.154 | 23.199 | 3 |

## Prediction intervals

| Dataset | h | Method | Nominal | Empirical | Cov. dev. | Width | Norm. width | Winkler |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | cqr | 0.900 | 0.896 | 0.004 | 85.748 | 0.355 | 127.123 |
| bdg2 | 1 | quantile_uncalibrated | 0.900 | 0.778 | 0.122 | 83.667 | 0.347 | 127.317 |
| bdg2 | 1 | cqr | 0.950 | 0.943 | 0.007 | 110.219 | 0.457 | 160.680 |
| bdg2 | 1 | quantile_uncalibrated | 0.950 | 0.856 | 0.094 | 104.292 | 0.432 | 161.705 |
| bdg2 | 1 | recentred_enbpi_static | 0.900 | 0.891 | 0.009 | 101.351 | 0.420 | 194.240 |
| bdg2 | 1 | recentred_enbpi_static | 0.950 | 0.940 | 0.010 | 146.605 | 0.607 | 259.038 |
| bdg2 | 1 | recentred_enbpi_updated | 0.900 | 0.903 | 0.003 | 110.196 | 0.456 | 195.322 |
| bdg2 | 1 | recentred_enbpi_updated | 0.950 | 0.949 | 0.001 | 160.589 | 0.665 | 260.687 |
| bdg2 | 3 | cqr | 0.900 | 0.899 | 0.001 | 107.664 | 0.446 | 160.617 |
| bdg2 | 3 | quantile_uncalibrated | 0.900 | 0.871 | 0.029 | 104.314 | 0.432 | 160.691 |
| bdg2 | 3 | cqr | 0.950 | 0.949 | 0.001 | 143.006 | 0.592 | 204.246 |
| bdg2 | 3 | quantile_uncalibrated | 0.950 | 0.840 | 0.110 | 130.879 | 0.542 | 203.609 |
| bdg2 | 3 | recentred_enbpi_static | 0.900 | 0.890 | 0.010 | 132.090 | 0.547 | 253.560 |
| bdg2 | 3 | recentred_enbpi_static | 0.950 | 0.941 | 0.009 | 191.202 | 0.792 | 340.044 |
| bdg2 | 3 | recentred_enbpi_updated | 0.900 | 0.903 | 0.003 | 142.961 | 0.592 | 254.581 |
| bdg2 | 3 | recentred_enbpi_updated | 0.950 | 0.950 | 0.000 | 208.530 | 0.864 | 343.681 |
| bdg2 | 6 | cqr | 0.900 | 0.903 | 0.003 | 122.801 | 0.509 | 184.986 |
| bdg2 | 6 | quantile_uncalibrated | 0.900 | 0.785 | 0.115 | 115.994 | 0.480 | 184.762 |
| bdg2 | 6 | cqr | 0.950 | 0.951 | 0.001 | 163.335 | 0.677 | 235.831 |
| bdg2 | 6 | quantile_uncalibrated | 0.950 | 0.821 | 0.129 | 145.881 | 0.604 | 235.296 |
| bdg2 | 6 | recentred_enbpi_static | 0.900 | 0.895 | 0.005 | 156.040 | 0.646 | 290.338 |
| bdg2 | 6 | recentred_enbpi_static | 0.950 | 0.944 | 0.006 | 224.029 | 0.928 | 390.030 |
| bdg2 | 6 | recentred_enbpi_updated | 0.900 | 0.906 | 0.006 | 166.326 | 0.689 | 291.137 |
| bdg2 | 6 | recentred_enbpi_updated | 0.950 | 0.952 | 0.002 | 241.582 | 1.001 | 394.521 |
| bdg2 | 1 | dscp | 0.900 | 0.864 | 0.036 | 83.138 | 0.344 | 172.597 |
| bdg2 | 3 | dscp | 0.900 | 0.866 | 0.034 | 107.401 | 0.445 | 219.694 |
| bdg2 | 6 | dscp | 0.900 | 0.876 | 0.024 | 125.023 | 0.518 | 253.419 |
| bdg2 | 1 | dscp | 0.950 | 0.930 | 0.020 | 119.035 | 0.493 | 227.105 |
| bdg2 | 3 | dscp | 0.950 | 0.922 | 0.028 | 148.781 | 0.616 | 292.654 |
| bdg2 | 6 | dscp | 0.950 | 0.930 | 0.020 | 173.405 | 0.718 | 342.624 |
| pleia | 1 | cqr | 0.900 | 0.890 | 0.010 | 1.330 | 0.538 | 1.988 |
| pleia | 1 | quantile_uncalibrated | 0.900 | 0.826 | 0.074 | 1.154 | 0.467 | 2.075 |
| pleia | 1 | cqr | 0.950 | 0.937 | 0.013 | 1.648 | 0.667 | 2.510 |
| pleia | 1 | quantile_uncalibrated | 0.950 | 0.896 | 0.054 | 1.419 | 0.574 | 2.632 |
| pleia | 1 | recentred_enbpi_static | 0.900 | 0.845 | 0.055 | 1.307 | 0.529 | 2.421 |
| pleia | 1 | recentred_enbpi_static | 0.950 | 0.914 | 0.036 | 1.723 | 0.697 | 3.059 |
| pleia | 1 | recentred_enbpi_updated | 0.900 | 0.883 | 0.017 | 1.499 | 0.607 | 2.368 |
| pleia | 1 | recentred_enbpi_updated | 0.950 | 0.940 | 0.010 | 1.961 | 0.794 | 2.965 |
| pleia | 3 | cqr | 0.900 | 0.888 | 0.012 | 2.007 | 0.812 | 3.114 |
| pleia | 3 | quantile_uncalibrated | 0.900 | 0.805 | 0.095 | 1.627 | 0.659 | 3.317 |
| pleia | 3 | cqr | 0.950 | 0.948 | 0.002 | 2.576 | 1.043 | 3.861 |
| pleia | 3 | quantile_uncalibrated | 0.950 | 0.892 | 0.058 | 2.059 | 0.833 | 4.133 |
| pleia | 3 | recentred_enbpi_static | 0.900 | 0.801 | 0.099 | 1.760 | 0.713 | 3.678 |
| pleia | 3 | recentred_enbpi_static | 0.950 | 0.880 | 0.070 | 2.298 | 0.930 | 4.671 |
| pleia | 3 | recentred_enbpi_updated | 0.900 | 0.871 | 0.029 | 2.139 | 0.866 | 3.491 |
| pleia | 3 | recentred_enbpi_updated | 0.950 | 0.928 | 0.022 | 2.785 | 1.128 | 4.352 |
| pleia | 6 | cqr | 0.900 | 0.901 | 0.001 | 2.714 | 1.099 | 3.987 |
| pleia | 6 | quantile_uncalibrated | 0.900 | 0.780 | 0.120 | 2.020 | 0.818 | 4.335 |
| pleia | 6 | cqr | 0.950 | 0.940 | 0.010 | 3.308 | 1.339 | 5.019 |
| pleia | 6 | quantile_uncalibrated | 0.950 | 0.851 | 0.099 | 2.438 | 0.987 | 5.880 |
| pleia | 6 | recentred_enbpi_static | 0.900 | 0.795 | 0.105 | 2.153 | 0.872 | 4.619 |
| pleia | 6 | recentred_enbpi_static | 0.950 | 0.877 | 0.073 | 2.773 | 1.123 | 5.878 |
| pleia | 6 | recentred_enbpi_updated | 0.900 | 0.866 | 0.034 | 2.666 | 1.079 | 4.371 |
| pleia | 6 | recentred_enbpi_updated | 0.950 | 0.926 | 0.024 | 3.395 | 1.374 | 5.450 |
| pleia | 1 | dscp | 0.900 | 0.927 | 0.027 | 1.649 | 0.667 | 2.282 |
| pleia | 3 | dscp | 0.900 | 0.924 | 0.024 | 2.253 | 0.912 | 3.226 |
| pleia | 6 | dscp | 0.900 | 0.883 | 0.017 | 2.732 | 1.106 | 4.314 |
| pleia | 1 | dscp | 0.950 | 0.964 | 0.014 | 2.171 | 0.878 | 2.900 |
| pleia | 3 | dscp | 0.950 | 0.960 | 0.010 | 2.893 | 1.171 | 4.137 |
| pleia | 6 | dscp | 0.950 | 0.934 | 0.016 | 3.474 | 1.407 | 5.422 |
| pleia_energy | 1 | cqr | 0.900 | 0.938 | 0.038 | 0.307 | 0.124 | 0.955 |
| pleia_energy | 1 | quantile_uncalibrated | 0.900 | 0.796 | 0.104 | 0.214 | 0.087 | 0.970 |
| pleia_energy | 1 | cqr | 0.950 | 0.973 | 0.023 | 0.410 | 0.166 | 1.586 |
| pleia_energy | 1 | quantile_uncalibrated | 0.950 | 0.869 | 0.081 | 0.285 | 0.115 | 1.609 |
| pleia_energy | 1 | recentred_enbpi_static | 0.900 | 0.969 | 0.069 | 0.812 | 0.329 | 1.441 |
| pleia_energy | 1 | recentred_enbpi_static | 0.950 | 0.988 | 0.038 | 1.251 | 0.507 | 2.374 |
| pleia_energy | 1 | recentred_enbpi_updated | 0.900 | 0.905 | 0.005 | 0.556 | 0.225 | 1.381 |
| pleia_energy | 1 | recentred_enbpi_updated | 0.950 | 0.954 | 0.004 | 0.822 | 0.333 | 2.167 |
| pleia_energy | 3 | cqr | 0.900 | 0.940 | 0.040 | 0.317 | 0.128 | 1.017 |
| pleia_energy | 3 | quantile_uncalibrated | 0.900 | 0.770 | 0.130 | 0.221 | 0.090 | 1.042 |
| pleia_energy | 3 | cqr | 0.950 | 0.963 | 0.013 | 0.423 | 0.171 | 1.668 |
| pleia_energy | 3 | quantile_uncalibrated | 0.950 | 0.838 | 0.112 | 0.291 | 0.118 | 1.732 |
| pleia_energy | 3 | recentred_enbpi_static | 0.900 | 0.958 | 0.058 | 0.857 | 0.348 | 1.529 |
| pleia_energy | 3 | recentred_enbpi_static | 0.950 | 0.981 | 0.031 | 1.156 | 0.469 | 2.332 |
| pleia_energy | 3 | recentred_enbpi_updated | 0.900 | 0.904 | 0.004 | 0.601 | 0.244 | 1.492 |
| pleia_energy | 3 | recentred_enbpi_updated | 0.950 | 0.948 | 0.002 | 0.856 | 0.347 | 2.293 |
| pleia_energy | 6 | cqr | 0.900 | 0.924 | 0.024 | 0.358 | 0.145 | 1.071 |
| pleia_energy | 6 | quantile_uncalibrated | 0.900 | 0.758 | 0.142 | 0.242 | 0.098 | 1.101 |
| pleia_energy | 6 | cqr | 0.950 | 0.963 | 0.013 | 0.476 | 0.193 | 1.720 |
| pleia_energy | 6 | quantile_uncalibrated | 0.950 | 0.838 | 0.112 | 0.318 | 0.129 | 1.780 |
| pleia_energy | 6 | recentred_enbpi_static | 0.900 | 0.967 | 0.067 | 0.911 | 0.369 | 1.545 |
| pleia_energy | 6 | recentred_enbpi_static | 0.950 | 0.988 | 0.038 | 1.804 | 0.731 | 2.933 |
| pleia_energy | 6 | recentred_enbpi_updated | 0.900 | 0.907 | 0.007 | 0.633 | 0.257 | 1.483 |
| pleia_energy | 6 | recentred_enbpi_updated | 0.950 | 0.952 | 0.002 | 0.994 | 0.403 | 2.374 |
| pleia_energy | 1 | dscp | 0.900 | 0.970 | 0.070 | 0.704 | 0.285 | 1.305 |
| pleia_energy | 3 | dscp | 0.900 | 0.970 | 0.070 | 0.727 | 0.295 | 1.341 |
| pleia_energy | 6 | dscp | 0.900 | 0.967 | 0.067 | 0.753 | 0.305 | 1.361 |
| pleia_energy | 1 | dscp | 0.950 | 0.984 | 0.034 | 0.868 | 0.352 | 1.993 |
| pleia_energy | 3 | dscp | 0.950 | 0.983 | 0.033 | 0.906 | 0.367 | 2.043 |
| pleia_energy | 6 | dscp | 0.950 | 0.985 | 0.035 | 0.935 | 0.379 | 2.057 |
| rico | 5 | cqr | 0.900 | 0.846 | 0.054 | 1.238 | 0.281 | 2.064 |
| rico | 5 | quantile_uncalibrated | 0.900 | 0.622 | 0.278 | 0.866 | 0.197 | 2.145 |
| rico | 5 | cqr | 0.950 | 0.781 | 0.169 | 1.444 | 0.328 | 4.968 |
| rico | 5 | quantile_uncalibrated | 0.950 | 0.690 | 0.260 | 1.240 | 0.282 | 5.581 |
| rico | 5 | recentred_enbpi_static | 0.900 | 0.857 | 0.043 | 0.390 | 0.089 | 0.679 |
| rico | 5 | recentred_enbpi_static | 0.950 | 0.929 | 0.021 | 0.524 | 0.119 | 0.824 |
| rico | 5 | recentred_enbpi_updated | 0.900 | 0.852 | 0.048 | 0.382 | 0.087 | 0.664 |
| rico | 5 | recentred_enbpi_updated | 0.950 | 0.927 | 0.023 | 0.511 | 0.116 | 0.813 |
| rico | 15 | cqr | 0.900 | 0.855 | 0.045 | 1.388 | 0.314 | 2.286 |
| rico | 15 | quantile_uncalibrated | 0.900 | 0.675 | 0.225 | 0.911 | 0.206 | 2.409 |
| rico | 15 | cqr | 0.950 | 0.802 | 0.148 | 1.834 | 0.415 | 5.969 |
| rico | 15 | quantile_uncalibrated | 0.950 | 0.678 | 0.272 | 1.370 | 0.310 | 7.339 |
| rico | 15 | recentred_enbpi_static | 0.900 | 0.820 | 0.080 | 0.848 | 0.192 | 1.787 |
| rico | 15 | recentred_enbpi_static | 0.950 | 0.906 | 0.044 | 1.189 | 0.269 | 2.099 |
| rico | 15 | recentred_enbpi_updated | 0.900 | 0.821 | 0.079 | 0.875 | 0.198 | 1.676 |
| rico | 15 | recentred_enbpi_updated | 0.950 | 0.912 | 0.038 | 1.166 | 0.264 | 1.994 |
| rico | 30 | cqr | 0.900 | 0.817 | 0.083 | 2.228 | 0.497 | 3.619 |
| rico | 30 | quantile_uncalibrated | 0.900 | 0.490 | 0.410 | 1.085 | 0.242 | 5.630 |
| rico | 30 | cqr | 0.950 | 0.752 | 0.198 | 2.649 | 0.591 | 15.652 |
| rico | 30 | quantile_uncalibrated | 0.950 | 0.548 | 0.402 | 1.754 | 0.391 | 16.940 |
| rico | 30 | recentred_enbpi_static | 0.900 | 0.786 | 0.114 | 1.232 | 0.275 | 3.439 |
| rico | 30 | recentred_enbpi_static | 0.950 | 0.864 | 0.086 | 1.736 | 0.387 | 4.280 |
| rico | 30 | recentred_enbpi_updated | 0.900 | 0.819 | 0.081 | 1.369 | 0.305 | 3.118 |
| rico | 30 | recentred_enbpi_updated | 0.950 | 0.903 | 0.047 | 1.969 | 0.439 | 3.782 |
| rico | 60 | cqr | 0.900 | 0.795 | 0.105 | 3.343 | 0.721 | 7.891 |
| rico | 60 | quantile_uncalibrated | 0.900 | 0.470 | 0.430 | 1.937 | 0.418 | 8.909 |
| rico | 60 | cqr | 0.950 | 0.753 | 0.197 | 4.065 | 0.876 | 18.451 |
| rico | 60 | quantile_uncalibrated | 0.950 | 0.606 | 0.344 | 2.874 | 0.620 | 20.868 |
| rico | 60 | recentred_enbpi_static | 0.900 | 0.703 | 0.197 | 1.602 | 0.345 | 7.020 |
| rico | 60 | recentred_enbpi_static | 0.950 | 0.789 | 0.161 | 2.257 | 0.487 | 10.068 |
| rico | 60 | recentred_enbpi_updated | 0.900 | 0.805 | 0.095 | 2.353 | 0.507 | 5.689 |
| rico | 60 | recentred_enbpi_updated | 0.950 | 0.872 | 0.078 | 3.184 | 0.687 | 6.697 |
| rico | 5 | dscp | 0.900 | 0.839 | 0.061 | 0.441 | 0.105 | 0.820 |
| rico | 15 | dscp | 0.900 | 0.832 | 0.068 | 0.958 | 0.226 | 1.931 |
| rico | 30 | dscp | 0.900 | 0.827 | 0.073 | 1.588 | 0.363 | 3.062 |
| rico | 60 | dscp | 0.900 | 0.817 | 0.083 | 2.661 | 0.574 | 4.924 |
| rico | 5 | dscp | 0.950 | 0.901 | 0.049 | 0.593 | 0.142 | 1.050 |
| rico | 15 | dscp | 0.950 | 0.890 | 0.060 | 1.237 | 0.291 | 2.519 |
| rico | 30 | dscp | 0.950 | 0.899 | 0.051 | 2.011 | 0.460 | 3.783 |
| rico | 60 | dscp | 0.950 | 0.899 | 0.051 | 3.320 | 0.716 | 6.140 |

## Alert rules

| Dataset | Role | Rule | Precision | Recall | F1 | FAR | False/day | Mean delay | Median delay | Selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | calibration_selection | 1-of-1 | 0.065 | 0.929 | 0.121 | 0.063 | 0.967 | 35.385 | 0.000 | yes |
| bdg2 | calibration_selection | 2-of-3 | 0.154 | 0.857 | 0.261 | 0.038 | 0.340 | 95.000 | 60.000 | no |
| bdg2 | calibration_selection | 3-of-5 | 0.265 | 0.857 | 0.404 | 0.023 | 0.172 | 155.000 | 120.000 | no |
| bdg2 | calibration_selection | 4-of-7 | 0.333 | 0.833 | 0.476 | 0.018 | 0.120 | 236.571 | 180.000 | no |
| bdg2 | post_hoc_sensitivity | 1-of-1 | 0.025 | 0.881 | 0.049 | 0.057 | 0.986 | 30.811 | 0.000 | yes |
| bdg2 | post_hoc_sensitivity | 2-of-3 | 0.075 | 0.833 | 0.137 | 0.030 | 0.299 | 96.000 | 60.000 | no |
| bdg2 | post_hoc_sensitivity | 3-of-5 | 0.163 | 0.810 | 0.272 | 0.014 | 0.120 | 176.471 | 120.000 | no |
| bdg2 | post_hoc_sensitivity | 4-of-7 | 0.268 | 0.786 | 0.400 | 0.008 | 0.062 | 216.364 | 180.000 | no |
| bdg2 | clean_test_no_events | 1-of-1 | 0.000 | n/a | n/a | 0.057 | 1.002 | n/a | n/a | yes |
| bdg2 | clean_test_no_events | 2-of-3 | 0.000 | n/a | n/a | 0.030 | 0.304 | n/a | n/a | no |
| bdg2 | clean_test_no_events | 3-of-5 | 0.000 | n/a | n/a | 0.014 | 0.120 | n/a | n/a | no |
| bdg2 | clean_test_no_events | 4-of-7 | 0.000 | n/a | n/a | 0.008 | 0.057 | n/a | n/a | no |
| pleia | calibration_selection | 1-of-1 | 0.161 | 0.952 | 0.276 | 0.110 | 7.408 | 14.750 | 0.000 | no |
| pleia | calibration_selection | 2-of-3 | 0.296 | 0.881 | 0.443 | 0.078 | 3.134 | 17.838 | 10.000 | no |
| pleia | calibration_selection | 3-of-5 | 0.439 | 0.857 | 0.581 | 0.051 | 1.638 | 28.333 | 20.000 | no |
| pleia | calibration_selection | 4-of-7 | 0.583 | 0.833 | 0.686 | 0.035 | 0.890 | 35.714 | 30.000 | yes |
| pleia | post_hoc_sensitivity | 1-of-1 | 0.097 | 0.929 | 0.175 | 0.063 | 5.200 | 12.308 | 0.000 | no |
| pleia | post_hoc_sensitivity | 2-of-3 | 0.205 | 0.857 | 0.330 | 0.041 | 1.994 | 22.778 | 10.000 | no |
| pleia | post_hoc_sensitivity | 3-of-5 | 0.351 | 0.810 | 0.489 | 0.025 | 0.898 | 29.118 | 20.000 | no |
| pleia | post_hoc_sensitivity | 4-of-7 | 0.576 | 0.810 | 0.673 | 0.013 | 0.356 | 38.824 | 30.000 | yes |
| pleia | clean_test_no_events | 1-of-1 | 0.000 | n/a | n/a | 0.063 | 5.613 | n/a | n/a | no |
| pleia | clean_test_no_events | 2-of-3 | 0.000 | n/a | n/a | 0.041 | 2.180 | n/a | n/a | no |
| pleia | clean_test_no_events | 3-of-5 | 0.000 | n/a | n/a | 0.025 | 0.954 | n/a | n/a | no |
| pleia | clean_test_no_events | 4-of-7 | 0.000 | n/a | n/a | 0.014 | 0.413 | n/a | n/a | yes |
| pleia_energy | calibration_selection | 1-of-1 | 0.208 | 0.786 | 0.328 | 0.048 | 4.488 | 35.152 | 0.000 | no |
| pleia_energy | calibration_selection | 2-of-3 | 0.542 | 0.619 | 0.578 | 0.015 | 0.784 | 55.000 | 15.000 | yes |
| pleia_energy | calibration_selection | 3-of-5 | 0.759 | 0.524 | 0.620 | 0.006 | 0.249 | 57.727 | 25.000 | no |
| pleia_energy | calibration_selection | 4-of-7 | 0.917 | 0.524 | 0.667 | 0.002 | 0.071 | 74.091 | 40.000 | no |
| pleia_energy | post_hoc_sensitivity | 1-of-1 | 0.145 | 0.881 | 0.248 | 0.028 | 3.120 | 19.189 | 0.000 | no |
| pleia_energy | post_hoc_sensitivity | 2-of-3 | 0.438 | 0.762 | 0.557 | 0.010 | 0.584 | 32.812 | 10.000 | yes |
| pleia_energy | post_hoc_sensitivity | 3-of-5 | 0.689 | 0.738 | 0.713 | 0.005 | 0.199 | 43.226 | 20.000 | no |
| pleia_energy | post_hoc_sensitivity | 4-of-7 | 0.750 | 0.714 | 0.732 | 0.003 | 0.142 | 57.667 | 30.000 | no |
| pleia_energy | clean_test_no_events | 1-of-1 | 0.000 | n/a | n/a | 0.027 | 3.305 | n/a | n/a | no |
| pleia_energy | clean_test_no_events | 2-of-3 | 0.000 | n/a | n/a | 0.009 | 0.584 | n/a | n/a | yes |
| pleia_energy | clean_test_no_events | 3-of-5 | 0.000 | n/a | n/a | 0.005 | 0.214 | n/a | n/a | no |
| pleia_energy | clean_test_no_events | 4-of-7 | 0.000 | n/a | n/a | 0.003 | 0.157 | n/a | n/a | no |
| rico | calibration_selection | 1-of-1 | 0.732 | 0.857 | 0.789 | 0.017 | 4.377 | 0.933 | 0.000 | no |
| rico | calibration_selection | 2-of-3 | 0.771 | 0.771 | 0.771 | 0.017 | 3.183 | 2.037 | 1.000 | yes |
| rico | calibration_selection | 3-of-5 | 0.771 | 0.771 | 0.771 | 0.017 | 3.183 | 3.074 | 2.000 | no |
| rico | calibration_selection | 4-of-7 | 0.771 | 0.771 | 0.771 | 0.017 | 3.183 | 4.074 | 3.000 | no |
| rico | post_hoc_sensitivity | 1-of-1 | 0.241 | 0.950 | 0.384 | 0.206 | 18.617 | 1.026 | 0.000 | no |
| rico | post_hoc_sensitivity | 2-of-3 | 0.312 | 0.875 | 0.461 | 0.208 | 11.946 | 2.286 | 1.000 | yes |
| rico | post_hoc_sensitivity | 3-of-5 | 0.372 | 0.875 | 0.522 | 0.206 | 9.153 | 3.029 | 2.000 | no |
| rico | post_hoc_sensitivity | 4-of-7 | 0.385 | 0.875 | 0.534 | 0.205 | 8.688 | 3.743 | 3.000 | no |
| rico | clean_test_no_events | 1-of-1 | 0.000 | n/a | n/a | 0.219 | 20.323 | n/a | n/a | no |
| rico | clean_test_no_events | 2-of-3 | 0.000 | n/a | n/a | 0.221 | 12.566 | n/a | n/a | yes |
| rico | clean_test_no_events | 3-of-5 | 0.000 | n/a | n/a | 0.220 | 9.463 | n/a | n/a | no |
| rico | clean_test_no_events | 4-of-7 | 0.000 | n/a | n/a | 0.218 | 8.533 | n/a | n/a | no |

## Robustness

| Dataset | Mode | Scenario | Severity | MAE | Coverage | Cov. dev. | Width | False/day |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | legacy_fixed_intervals | clean | none | 20.011 | 0.943 | 0.007 | 110.219 | 1.002 |
| bdg2 | closed_loop | clean | none | 20.011 | 0.943 | 0.007 | 110.219 | 1.002 |
| bdg2 | legacy_fixed_intervals | random_missing_5pct | 5% | 31.904 | 0.902 | 0.048 | 110.219 | 1.869 |
| bdg2 | closed_loop | random_missing_5pct | 5% | 19.862 | 0.943 | 0.007 | 109.860 | 0.982 |
| bdg2 | legacy_fixed_intervals | random_missing_10pct | 10% | 44.522 | 0.861 | 0.089 | 110.219 | 2.663 |
| bdg2 | closed_loop | random_missing_10pct | 10% | 19.656 | 0.944 | 0.006 | 109.599 | 0.975 |
| bdg2 | legacy_fixed_intervals | random_missing_20pct | 20% | 67.410 | 0.781 | 0.169 | 110.219 | 3.947 |
| bdg2 | closed_loop | random_missing_20pct | 20% | 19.054 | 0.948 | 0.002 | 108.759 | 0.888 |
| bdg2 | legacy_fixed_intervals | block_missing_5pct | 5% | 22.807 | 0.933 | 0.017 | 110.219 | 1.060 |
| bdg2 | closed_loop | block_missing_5pct | 5% | 20.127 | 0.942 | 0.008 | 110.117 | 1.009 |
| bdg2 | legacy_fixed_intervals | block_missing_10pct | 10% | 25.601 | 0.922 | 0.028 | 110.219 | 1.110 |
| bdg2 | closed_loop | block_missing_10pct | 10% | 20.221 | 0.943 | 0.007 | 110.533 | 1.004 |
| bdg2 | legacy_fixed_intervals | bias_0.5sd | 0.5 sigma | 123.404 | 0.135 | 0.815 | 110.219 | 1.253 |
| bdg2 | closed_loop | bias_0.5sd | 0.5 sigma | 27.060 | 0.963 | 0.013 | 172.217 | 0.610 |
| bdg2 | legacy_fixed_intervals | bias_1.0sd | 1.0 sigma | 244.910 | 0.022 | 0.928 | 110.219 | 0.210 |
| bdg2 | closed_loop | bias_1.0sd | 1.0 sigma | 27.790 | 0.939 | 0.011 | 144.468 | 0.825 |
| bdg2 | legacy_fixed_intervals | bias_2.0sd | 2.0 sigma | 489.522 | 0.001 | 0.949 | 110.219 | 0.011 |
| bdg2 | closed_loop | bias_2.0sd | 2.0 sigma | 44.166 | 0.888 | 0.062 | 222.726 | 0.871 |
| bdg2 | legacy_fixed_intervals | level_shift_1.0sd | 1.0 sigma | 136.740 | 0.469 | 0.481 | 110.219 | 0.734 |
| bdg2 | closed_loop | level_shift_1.0sd | 1.0 sigma | 23.539 | 0.947 | 0.003 | 125.428 | 0.869 |
| bdg2 | legacy_fixed_intervals | level_shift_2.0sd | 2.0 sigma | 259.057 | 0.463 | 0.487 | 110.219 | 0.723 |
| bdg2 | closed_loop | level_shift_2.0sd | 2.0 sigma | 29.165 | 0.929 | 0.021 | 165.356 | 0.967 |
| bdg2 | legacy_fixed_intervals | drift_1.0sd | 1.0 sigma terminal | 125.489 | 0.281 | 0.669 | 110.219 | 1.409 |
| bdg2 | closed_loop | drift_1.0sd | 1.0 sigma terminal | 24.277 | 0.966 | 0.016 | 147.617 | 0.587 |
| bdg2 | legacy_fixed_intervals | drift_2.0sd | 2.0 sigma terminal | 246.020 | 0.146 | 0.804 | 110.219 | 0.810 |
| bdg2 | closed_loop | drift_2.0sd | 2.0 sigma terminal | 28.484 | 0.948 | 0.002 | 158.634 | 0.764 |
| bdg2 | legacy_fixed_intervals | stuck_5pct | 5% of region | 30.633 | 0.901 | 0.049 | 110.219 | 0.938 |
| bdg2 | closed_loop | stuck_5pct | 5% of region | 19.888 | 0.945 | 0.005 | 110.939 | 0.943 |
| bdg2 | legacy_fixed_intervals | dropout_5pct | 5% of region | 24.232 | 0.919 | 0.031 | 110.219 | 0.982 |
| bdg2 | closed_loop | dropout_5pct | 5% of region | 19.606 | 0.940 | 0.010 | 109.754 | 0.985 |
| bdg2 | calibration_contamination | calib_contam_1pct | 1% | n/a | 0.954 | 0.004 | 170.526 | n/a |
| bdg2 | calibration_contamination | calib_contam_5pct | 5% | n/a | 0.999 | 0.049 | 951.175 | n/a |
| bdg2 | calibration_contamination | calib_contam_10pct | 10% | n/a | 1.000 | 0.050 | 1468.759 | n/a |
| pleia | legacy_fixed_intervals | clean | none | 0.314 | 0.937 | 0.013 | 1.648 | 0.413 |
| pleia | closed_loop | clean | none | 0.314 | 0.937 | 0.013 | 1.648 | 0.413 |
| pleia | legacy_fixed_intervals | random_missing_5pct | 5% | 0.312 | 0.938 | 0.012 | 1.648 | 0.385 |
| pleia | closed_loop | random_missing_5pct | 5% | 0.311 | 0.937 | 0.013 | 1.642 | 0.370 |
| pleia | legacy_fixed_intervals | random_missing_10pct | 10% | 0.311 | 0.939 | 0.011 | 1.648 | 0.385 |
| pleia | closed_loop | random_missing_10pct | 10% | 0.307 | 0.939 | 0.011 | 1.634 | 0.356 |
| pleia | legacy_fixed_intervals | random_missing_20pct | 20% | 0.305 | 0.941 | 0.009 | 1.648 | 0.413 |
| pleia | closed_loop | random_missing_20pct | 20% | 0.300 | 0.940 | 0.010 | 1.619 | 0.402 |
| pleia | legacy_fixed_intervals | block_missing_5pct | 5% | 0.313 | 0.938 | 0.012 | 1.648 | 0.399 |
| pleia | closed_loop | block_missing_5pct | 5% | 0.314 | 0.938 | 0.012 | 1.648 | 0.436 |
| pleia | legacy_fixed_intervals | block_missing_10pct | 10% | 0.313 | 0.938 | 0.012 | 1.648 | 0.370 |
| pleia | closed_loop | block_missing_10pct | 10% | 0.311 | 0.940 | 0.010 | 1.644 | 0.374 |
| pleia | legacy_fixed_intervals | bias_0.5sd | 0.5 sigma | 2.274 | 0.023 | 0.927 | 1.648 | 0.328 |
| pleia | closed_loop | bias_0.5sd | 0.5 sigma | 0.349 | 0.887 | 0.063 | 1.585 | 1.311 |
| pleia | legacy_fixed_intervals | bias_1.0sd | 1.0 sigma | 4.504 | 0.003 | 0.947 | 1.648 | 0.071 |
| pleia | closed_loop | bias_1.0sd | 1.0 sigma | 0.383 | 0.832 | 0.118 | 1.688 | 2.094 |
| pleia | legacy_fixed_intervals | bias_2.0sd | 2.0 sigma | 8.974 | 0.000 | 0.950 | 1.648 | 0.014 |
| pleia | closed_loop | bias_2.0sd | 2.0 sigma | 1.655 | 0.258 | 0.692 | 2.761 | 2.265 |
| pleia | legacy_fixed_intervals | level_shift_1.0sd | 1.0 sigma | 2.428 | 0.458 | 0.492 | 1.648 | 0.370 |
| pleia | closed_loop | level_shift_1.0sd | 1.0 sigma | 0.354 | 0.876 | 0.074 | 1.631 | 1.282 |
| pleia | legacy_fixed_intervals | level_shift_2.0sd | 2.0 sigma | 4.663 | 0.457 | 0.493 | 1.648 | 0.342 |
| pleia | closed_loop | level_shift_2.0sd | 2.0 sigma | 0.755 | 0.615 | 0.335 | 2.161 | 1.752 |
| pleia | legacy_fixed_intervals | drift_1.0sd | 1.0 sigma terminal | 2.291 | 0.206 | 0.744 | 1.648 | 1.539 |
| pleia | closed_loop | drift_1.0sd | 1.0 sigma terminal | 0.352 | 0.885 | 0.065 | 1.603 | 1.254 |
| pleia | legacy_fixed_intervals | drift_2.0sd | 2.0 sigma terminal | 4.512 | 0.096 | 0.854 | 1.648 | 0.427 |
| pleia | closed_loop | drift_2.0sd | 2.0 sigma terminal | 0.412 | 0.746 | 0.204 | 1.717 | 2.365 |
| pleia | legacy_fixed_intervals | stuck_5pct | 5% of region | 0.363 | 0.898 | 0.052 | 1.648 | 0.456 |
| pleia | closed_loop | stuck_5pct | 5% of region | 0.312 | 0.938 | 0.012 | 1.628 | 0.399 |
| pleia | legacy_fixed_intervals | dropout_5pct | 5% of region | 0.442 | 0.908 | 0.042 | 1.648 | 0.399 |
| pleia | closed_loop | dropout_5pct | 5% of region | 0.297 | 0.946 | 0.004 | 1.613 | 0.342 |
| pleia | calibration_contamination | calib_contam_1pct | 1% | n/a | 0.945 | 0.005 | 1.853 | n/a |
| pleia | calibration_contamination | calib_contam_5pct | 5% | n/a | 0.997 | 0.047 | 14.469 | n/a |
| pleia | calibration_contamination | calib_contam_10pct | 10% | n/a | 1.000 | 0.050 | 26.818 | n/a |
| pleia_energy | legacy_fixed_intervals | clean | none | 0.093 | 0.973 | 0.023 | 0.410 | 0.584 |
| pleia_energy | closed_loop | clean | none | 0.093 | 0.973 | 0.023 | 0.410 | 0.584 |
| pleia_energy | legacy_fixed_intervals | random_missing_5pct | 5% | 0.105 | 0.974 | 0.024 | 0.410 | 0.627 |
| pleia_energy | closed_loop | random_missing_5pct | 5% | 0.105 | 0.973 | 0.023 | 0.407 | 0.670 |
| pleia_energy | legacy_fixed_intervals | random_missing_10pct | 10% | 0.104 | 0.974 | 0.024 | 0.410 | 0.655 |
| pleia_energy | closed_loop | random_missing_10pct | 10% | 0.104 | 0.974 | 0.024 | 0.405 | 0.698 |
| pleia_energy | legacy_fixed_intervals | random_missing_20pct | 20% | 0.103 | 0.976 | 0.026 | 0.410 | 0.641 |
| pleia_energy | closed_loop | random_missing_20pct | 20% | 0.104 | 0.974 | 0.024 | 0.398 | 0.761 |
| pleia_energy | legacy_fixed_intervals | block_missing_5pct | 5% | 0.094 | 0.973 | 0.023 | 0.410 | 0.570 |
| pleia_energy | closed_loop | block_missing_5pct | 5% | 0.098 | 0.972 | 0.022 | 0.413 | 0.637 |
| pleia_energy | legacy_fixed_intervals | block_missing_10pct | 10% | 0.095 | 0.973 | 0.023 | 0.410 | 0.570 |
| pleia_energy | closed_loop | block_missing_10pct | 10% | 0.101 | 0.972 | 0.022 | 0.405 | 0.631 |
| pleia_energy | legacy_fixed_intervals | bias_0.5sd | 0.5 sigma | 0.212 | 0.452 | 0.498 | 0.410 | 3.619 |
| pleia_energy | closed_loop | bias_0.5sd | 0.5 sigma | 0.096 | 0.977 | 0.027 | 0.506 | 0.556 |
| pleia_energy | legacy_fixed_intervals | bias_1.0sd | 1.0 sigma | 0.375 | 0.264 | 0.686 | 0.410 | 3.861 |
| pleia_energy | closed_loop | bias_1.0sd | 1.0 sigma | 0.100 | 0.978 | 0.028 | 0.515 | 0.356 |
| pleia_energy | legacy_fixed_intervals | bias_2.0sd | 2.0 sigma | 0.714 | 0.075 | 0.875 | 0.410 | 2.066 |
| pleia_energy | closed_loop | bias_2.0sd | 2.0 sigma | 0.134 | 0.976 | 0.026 | 0.836 | 0.356 |
| pleia_energy | legacy_fixed_intervals | level_shift_1.0sd | 1.0 sigma | 0.216 | 0.705 | 0.245 | 0.410 | 3.063 |
| pleia_energy | closed_loop | level_shift_1.0sd | 1.0 sigma | 0.099 | 0.976 | 0.026 | 0.496 | 0.342 |
| pleia_energy | legacy_fixed_intervals | level_shift_2.0sd | 2.0 sigma | 0.384 | 0.562 | 0.388 | 0.410 | 1.895 |
| pleia_energy | closed_loop | level_shift_2.0sd | 2.0 sigma | 0.120 | 0.972 | 0.022 | 0.653 | 0.399 |
| pleia_energy | legacy_fixed_intervals | drift_1.0sd | 1.0 sigma terminal | 0.210 | 0.639 | 0.311 | 0.410 | 3.775 |
| pleia_energy | closed_loop | drift_1.0sd | 1.0 sigma terminal | 0.100 | 0.976 | 0.026 | 0.514 | 0.598 |
| pleia_energy | legacy_fixed_intervals | drift_2.0sd | 2.0 sigma terminal | 0.375 | 0.347 | 0.603 | 0.410 | 4.274 |
| pleia_energy | closed_loop | drift_2.0sd | 2.0 sigma terminal | 0.106 | 0.979 | 0.029 | 0.639 | 0.442 |
| pleia_energy | legacy_fixed_intervals | stuck_5pct | 5% of region | 0.093 | 0.972 | 0.022 | 0.410 | 0.598 |
| pleia_energy | closed_loop | stuck_5pct | 5% of region | 0.090 | 0.974 | 0.024 | 0.399 | 0.541 |
| pleia_energy | legacy_fixed_intervals | dropout_5pct | 5% of region | 0.093 | 0.973 | 0.023 | 0.410 | 0.570 |
| pleia_energy | closed_loop | dropout_5pct | 5% of region | 0.092 | 0.973 | 0.023 | 0.408 | 0.570 |
| pleia_energy | calibration_contamination | calib_contam_1pct | 1% | n/a | 0.984 | 0.034 | 1.014 | n/a |
| pleia_energy | calibration_contamination | calib_contam_5pct | 5% | n/a | 0.995 | 0.045 | 1.594 | n/a |
| pleia_energy | calibration_contamination | calib_contam_10pct | 10% | n/a | 0.997 | 0.047 | 2.044 | n/a |
| rico | legacy_fixed_intervals | clean | none | 0.111 | 0.781 | 0.169 | 1.444 | 12.566 |
| rico | closed_loop | clean | none | 0.111 | 0.781 | 0.169 | 1.444 | 12.566 |
| rico | legacy_fixed_intervals | random_missing_5pct | 5% | 0.111 | 0.781 | 0.169 | 1.444 | 12.411 |
| rico | closed_loop | random_missing_5pct | 5% | 0.111 | 0.780 | 0.170 | 1.444 | 12.778 |
| rico | legacy_fixed_intervals | random_missing_10pct | 10% | 0.111 | 0.781 | 0.169 | 1.444 | 12.877 |
| rico | closed_loop | random_missing_10pct | 10% | 0.111 | 0.781 | 0.169 | 1.446 | 12.778 |
| rico | legacy_fixed_intervals | random_missing_20pct | 20% | 0.111 | 0.781 | 0.169 | 1.444 | 12.566 |
| rico | closed_loop | random_missing_20pct | 20% | 0.111 | 0.781 | 0.169 | 1.449 | 13.236 |
| rico | legacy_fixed_intervals | block_missing_5pct | 5% | 0.112 | 0.783 | 0.167 | 1.444 | 13.652 |
| rico | closed_loop | block_missing_5pct | 5% | 0.103 | 0.775 | 0.175 | 1.429 | 11.888 |
| rico | legacy_fixed_intervals | block_missing_10pct | 10% | 0.112 | 0.784 | 0.166 | 1.444 | 15.048 |
| rico | closed_loop | block_missing_10pct | 10% | 0.105 | 0.773 | 0.177 | 1.437 | 12.203 |
| rico | legacy_fixed_intervals | bias_0.5sd | 0.5 sigma | 2.858 | 0.049 | 0.901 | 1.444 | 3.878 |
| rico | closed_loop | bias_0.5sd | 0.5 sigma | 0.120 | 0.799 | 0.151 | 1.486 | 17.065 |
| rico | legacy_fixed_intervals | bias_1.0sd | 1.0 sigma | 5.693 | 0.000 | 0.950 | 1.444 | 0.155 |
| rico | closed_loop | bias_1.0sd | 1.0 sigma | 0.247 | 0.600 | 0.350 | 1.350 | 32.734 |
| rico | legacy_fixed_intervals | bias_2.0sd | 2.0 sigma | 11.364 | 0.000 | 0.950 | 1.444 | 0.155 |
| rico | closed_loop | bias_2.0sd | 2.0 sigma | 0.833 | 0.502 | 0.448 | 2.188 | 19.392 |
| rico | legacy_fixed_intervals | level_shift_1.0sd | 1.0 sigma | 2.896 | 0.425 | 0.525 | 1.444 | 3.878 |
| rico | closed_loop | level_shift_1.0sd | 1.0 sigma | 0.358 | 0.669 | 0.281 | 1.435 | 27.460 |
| rico | legacy_fixed_intervals | level_shift_2.0sd | 2.0 sigma | 5.731 | 0.425 | 0.525 | 1.444 | 3.878 |
| rico | closed_loop | level_shift_2.0sd | 2.0 sigma | 0.889 | 0.624 | 0.326 | 1.977 | 20.168 |
| rico | legacy_fixed_intervals | drift_1.0sd | 1.0 sigma terminal | 2.860 | 0.194 | 0.756 | 1.444 | 2.637 |
| rico | closed_loop | drift_1.0sd | 1.0 sigma terminal | 0.209 | 0.674 | 0.276 | 1.369 | 37.544 |
| rico | legacy_fixed_intervals | drift_2.0sd | 2.0 sigma terminal | 5.694 | 0.131 | 0.819 | 1.444 | 1.707 |
| rico | closed_loop | drift_2.0sd | 2.0 sigma terminal | 0.616 | 0.449 | 0.501 | 1.615 | 36.768 |
| rico | legacy_fixed_intervals | stuck_5pct | 5% of region | 0.226 | 0.738 | 0.212 | 1.444 | 12.721 |
| rico | closed_loop | stuck_5pct | 5% of region | 0.114 | 0.780 | 0.170 | 1.446 | 13.187 |
| rico | legacy_fixed_intervals | dropout_5pct | 5% of region | 0.469 | 0.760 | 0.190 | 1.444 | 11.946 |
| rico | closed_loop | dropout_5pct | 5% of region | 0.119 | 0.779 | 0.171 | 1.446 | 13.497 |
| rico | calibration_contamination | calib_contam_1pct | 1% | n/a | 0.921 | 0.029 | 0.573 | n/a |
| rico | calibration_contamination | calib_contam_5pct | 5% | n/a | 1.000 | 0.050 | 17.493 | n/a |
| rico | calibration_contamination | calib_contam_10pct | 10% | n/a | 1.000 | 0.050 | 34.027 | n/a |

## Recalibration

| Dataset | Strategy | Coverage | Cov. dev. | Width | Winkler | Updates | Every | Window |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | static | 0.843 | 0.107 | 126.210 | 202.331 | 0 | 24 | n/a |
| bdg2 | periodic | 0.859 | 0.091 | 127.375 | 194.025 | 1460 | 24 | n/a |
| bdg2 | rolling | 0.859 | 0.091 | 127.375 | 194.025 | 1460 | 24 | n/a |
| pleia | static | 0.932 | 0.018 | 1.707 | 2.894 | 0 | 24 | 1000.000 |
| pleia | periodic | 0.939 | 0.011 | 1.784 | 2.877 | 422 | 24 | 1000.000 |
| pleia | rolling | 0.948 | 0.002 | 1.891 | 2.869 | 422 | 24 | 1000.000 |
| pleia_energy | static | 0.981 | 0.031 | 0.941 | 2.099 | 0 | 144 | 1000.000 |
| pleia_energy | periodic | 0.972 | 0.022 | 0.847 | 2.060 | 71 | 144 | 1000.000 |
| pleia_energy | rolling | 0.929 | 0.021 | 0.458 | 1.866 | 71 | 144 | 1000.000 |
| rico | static | 0.905 | 0.045 | 0.536 | 0.925 | 0 | 15 | 500.000 |
| rico | periodic | 0.926 | 0.024 | 0.571 | 0.855 | 619 | 15 | 500.000 |
| rico | rolling | 0.912 | 0.038 | 0.529 | 0.830 | 619 | 15 | 500.000 |

## Bootstrap confidence intervals

| Dataset | h | Model | MAE | MAE lo | MAE hi | RMSE | RMSE lo | RMSE hi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | persistence | 18.917 | 17.785 | 20.076 | 37.842 | 35.933 | 39.888 |
| bdg2 | 1 | seasonal_naive | 36.535 | 34.006 | 39.430 | 79.070 | 72.388 | 86.481 |
| bdg2 | 1 | xgboost | 21.349 | 20.212 | 22.602 | 39.710 | 37.342 | 42.324 |
| bdg2 | 1 | attention_lstm | 19.865 | 18.826 | 20.899 | 35.305 | 33.377 | 37.369 |
| bdg2 | 3 | persistence | 35.993 | 33.935 | 38.172 | 70.023 | 66.545 | 73.484 |
| bdg2 | 3 | seasonal_naive | 36.527 | 33.944 | 39.450 | 79.076 | 72.383 | 86.361 |
| bdg2 | 3 | xgboost | 28.142 | 26.552 | 30.008 | 52.650 | 49.169 | 56.518 |
| bdg2 | 3 | attention_lstm | 30.278 | 28.379 | 32.356 | 57.164 | 53.710 | 60.977 |
| bdg2 | 6 | persistence | 60.911 | 57.397 | 64.880 | 106.777 | 101.464 | 112.060 |
| bdg2 | 6 | seasonal_naive | 36.531 | 33.825 | 39.410 | 79.099 | 72.334 | 86.714 |
| bdg2 | 6 | xgboost | 31.677 | 29.667 | 34.007 | 60.063 | 55.527 | 65.080 |
| bdg2 | 6 | attention_lstm | 40.704 | 38.204 | 43.454 | 75.029 | 69.697 | 80.294 |
| pleia | 1 | persistence | 0.203 | 0.192 | 0.215 | 0.325 | 0.306 | 0.348 |
| pleia | 1 | seasonal_naive | 1.477 | 1.349 | 1.601 | 2.197 | 2.013 | 2.374 |
| pleia | 1 | xgboost | 0.343 | 0.326 | 0.362 | 0.501 | 0.471 | 0.535 |
| pleia | 1 | attention_lstm | 0.803 | 0.755 | 0.855 | 1.074 | 1.011 | 1.138 |
| pleia | 3 | persistence | 0.375 | 0.352 | 0.402 | 0.606 | 0.561 | 0.656 |
| pleia | 3 | seasonal_naive | 1.477 | 1.351 | 1.603 | 2.198 | 2.012 | 2.377 |
| pleia | 3 | xgboost | 0.532 | 0.506 | 0.559 | 0.728 | 0.682 | 0.778 |
| pleia | 3 | attention_lstm | 0.813 | 0.764 | 0.864 | 1.075 | 1.011 | 1.141 |
| pleia | 6 | persistence | 0.546 | 0.510 | 0.590 | 0.872 | 0.799 | 0.960 |
| pleia | 6 | seasonal_naive | 1.477 | 1.352 | 1.604 | 2.198 | 2.004 | 2.375 |
| pleia | 6 | xgboost | 0.693 | 0.655 | 0.735 | 0.950 | 0.886 | 1.023 |
| pleia | 6 | attention_lstm | 1.057 | 0.998 | 1.126 | 1.369 | 1.292 | 1.452 |
| pleia_energy | 1 | persistence | 0.142 | 0.086 | 0.244 | 3.463 | 0.188 | 5.991 |
| pleia_energy | 1 | seasonal_naive | 0.198 | 0.142 | 0.279 | 3.468 | 0.277 | 5.473 |
| pleia_energy | 1 | xgboost | 0.098 | 0.067 | 0.153 | 2.451 | 0.143 | 4.240 |
| pleia_energy | 1 | attention_lstm | 0.102 | 0.072 | 0.157 | 2.451 | 0.145 | 4.240 |
| pleia_energy | 3 | persistence | 0.130 | 0.076 | 0.234 | 3.457 | 0.175 | 5.983 |
| pleia_energy | 3 | seasonal_naive | 0.198 | 0.141 | 0.276 | 3.468 | 0.277 | 5.473 |
| pleia_energy | 3 | xgboost | 0.104 | 0.074 | 0.159 | 2.452 | 0.153 | 4.240 |
| pleia_energy | 3 | attention_lstm | 0.106 | 0.075 | 0.161 | 2.452 | 0.151 | 4.241 |
| pleia_energy | 6 | persistence | 0.142 | 0.086 | 0.247 | 3.457 | 0.195 | 5.982 |
| pleia_energy | 6 | seasonal_naive | 0.198 | 0.141 | 0.276 | 3.469 | 0.277 | 5.474 |
| pleia_energy | 6 | xgboost | 0.112 | 0.081 | 0.166 | 2.452 | 0.161 | 4.241 |
| pleia_energy | 6 | attention_lstm | 0.115 | 0.084 | 0.170 | 2.453 | 0.158 | 4.242 |
| rico | 5 | persistence | 0.122 | 0.108 | 0.139 | 0.215 | 0.185 | 0.244 |
| rico | 5 | xgboost | 0.093 | 0.087 | 0.100 | 0.126 | 0.116 | 0.135 |
| rico | 5 | attention_lstm | 0.444 | 0.416 | 0.475 | 0.547 | 0.510 | 0.584 |
| rico | 15 | persistence | 0.350 | 0.308 | 0.392 | 0.601 | 0.518 | 0.684 |
| rico | 15 | xgboost | 0.220 | 0.199 | 0.240 | 0.320 | 0.285 | 0.354 |
| rico | 15 | attention_lstm | 0.519 | 0.478 | 0.562 | 0.676 | 0.627 | 0.724 |
| rico | 30 | persistence | 0.658 | 0.581 | 0.741 | 1.103 | 0.962 | 1.252 |
| rico | 30 | xgboost | 0.353 | 0.319 | 0.388 | 0.515 | 0.457 | 0.568 |
| rico | 30 | attention_lstm | 0.751 | 0.696 | 0.807 | 0.945 | 0.884 | 1.006 |
| rico | 60 | persistence | 1.203 | 1.072 | 1.353 | 1.890 | 1.640 | 2.136 |
| rico | 60 | xgboost | 0.616 | 0.553 | 0.684 | 0.904 | 0.815 | 0.998 |
| rico | 60 | attention_lstm | 0.924 | 0.852 | 0.995 | 1.165 | 1.090 | 1.241 |

## Diebold-Mariano tests

| Dataset | h | A | B | DM | p | Holm p | Significant |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | xgboost | persistence | 16.323 | 0.000 | 0.000 | yes |
| bdg2 | 1 | attention_lstm | persistence | 8.287 | 0.000 | 0.000 | yes |
| bdg2 | 1 | xgboost | attention_lstm | 11.531 | 0.000 | 0.000 | yes |
| bdg2 | 1 | seasonal_naive | persistence | 49.328 | 0.000 | 0.000 | yes |
| bdg2 | 3 | xgboost | persistence | -21.327 | 0.000 | 0.000 | yes |
| bdg2 | 3 | attention_lstm | persistence | -16.290 | 0.000 | 0.000 | yes |
| bdg2 | 3 | xgboost | attention_lstm | -6.825 | 0.000 | 0.000 | yes |
| bdg2 | 3 | seasonal_naive | persistence | 0.906 | 0.365 | 0.365 | no |
| bdg2 | 6 | xgboost | persistence | -37.572 | 0.000 | 0.000 | yes |
| bdg2 | 6 | attention_lstm | persistence | -27.177 | 0.000 | 0.000 | yes |
| bdg2 | 6 | xgboost | attention_lstm | -16.991 | 0.000 | 0.000 | yes |
| bdg2 | 6 | seasonal_naive | persistence | -27.229 | 0.000 | 0.000 | yes |
| pleia | 1 | xgboost | persistence | 46.787 | 0.000 | 0.000 | yes |
| pleia | 1 | attention_lstm | persistence | 84.227 | 0.000 | 0.000 | yes |
| pleia | 1 | xgboost | attention_lstm | -68.856 | 0.000 | 0.000 | yes |
| pleia | 1 | seasonal_naive | persistence | 79.250 | 0.000 | 0.000 | yes |
| pleia | 3 | xgboost | persistence | 28.507 | 0.000 | 0.000 | yes |
| pleia | 3 | attention_lstm | persistence | 39.042 | 0.000 | 0.000 | yes |
| pleia | 3 | xgboost | attention_lstm | -29.265 | 0.000 | 0.000 | yes |
| pleia | 3 | seasonal_naive | persistence | 40.443 | 0.000 | 0.000 | yes |
| pleia | 6 | xgboost | persistence | 13.822 | 0.000 | 0.000 | yes |
| pleia | 6 | attention_lstm | persistence | 26.610 | 0.000 | 0.000 | yes |
| pleia | 6 | xgboost | attention_lstm | -20.909 | 0.000 | 0.000 | yes |
| pleia | 6 | seasonal_naive | persistence | 24.557 | 0.000 | 0.000 | yes |
| pleia_energy | 1 | xgboost | persistence | -1.818 | 0.069 | 0.207 | no |
| pleia_energy | 1 | attention_lstm | persistence | -1.635 | 0.102 | 0.207 | no |
| pleia_energy | 1 | xgboost | attention_lstm | -7.261 | 0.000 | 0.000 | yes |
| pleia_energy | 1 | seasonal_naive | persistence | 1.645 | 0.100 | 0.207 | no |
| pleia_energy | 3 | xgboost | persistence | -1.081 | 0.280 | 0.559 | no |
| pleia_energy | 3 | attention_lstm | persistence | -1.026 | 0.305 | 0.559 | no |
| pleia_energy | 3 | xgboost | attention_lstm | -1.570 | 0.116 | 0.349 | no |
| pleia_energy | 3 | seasonal_naive | persistence | 1.976 | 0.048 | 0.193 | no |
| pleia_energy | 6 | xgboost | persistence | -1.233 | 0.218 | 0.435 | no |
| pleia_energy | 6 | attention_lstm | persistence | -1.109 | 0.268 | 0.435 | no |
| pleia_energy | 6 | xgboost | attention_lstm | -2.683 | 0.007 | 0.029 | yes |
| pleia_energy | 6 | seasonal_naive | persistence | 1.645 | 0.100 | 0.300 | no |
| rico | 5 | xgboost | persistence | -7.385 | 0.000 | 0.000 | yes |
| rico | 5 | attention_lstm | persistence | 39.661 | 0.000 | 0.000 | yes |
| rico | 5 | xgboost | attention_lstm | -46.351 | 0.000 | 0.000 | yes |
| rico | 15 | xgboost | persistence | -7.051 | 0.000 | 0.000 | yes |
| rico | 15 | attention_lstm | persistence | 7.654 | 0.000 | 0.000 | yes |
| rico | 15 | xgboost | attention_lstm | -14.964 | 0.000 | 0.000 | yes |
| rico | 30 | xgboost | persistence | -6.875 | 0.000 | 0.000 | yes |
| rico | 30 | attention_lstm | persistence | 2.448 | 0.014 | 0.014 | yes |
| rico | 30 | xgboost | attention_lstm | -10.654 | 0.000 | 0.000 | yes |
| rico | 60 | xgboost | persistence | -5.985 | 0.000 | 0.000 | yes |
| rico | 60 | attention_lstm | persistence | -1.925 | 0.054 | 0.054 | no |
| rico | 60 | xgboost | attention_lstm | -4.178 | 0.000 | 0.000 | yes |

## Model rankings

| Dataset | Model | Mean MAE rank | Mean RMSE rank | Mean impr % | Blocks |
| --- | --- | --- | --- | --- | --- |
| bdg2 | attention_lstm | 2.333 | 1.667 | 14.679 | 3 |
| bdg2 | persistence | 2.667 | 3.000 | 0.000 | 3 |
| bdg2 | seasonal_naive | 3.333 | 3.667 | -18.197 | 3 |
| bdg2 | xgboost | 1.667 | 1.667 | 18.984 | 3 |
| pleia | attention_lstm | 3.000 | 3.000 | -168.850 | 3 |
| pleia | persistence | 1.000 | 1.000 | 0.000 | 3 |
| pleia | seasonal_naive | 4.000 | 4.000 | -364.479 | 3 |
| pleia | xgboost | 2.000 | 2.000 | -45.994 | 3 |
| pleia_energy | attention_lstm | 2.000 | 2.000 | 21.951 | 3 |
| pleia_energy | persistence | 3.000 | 3.000 | 0.000 | 3 |
| pleia_energy | seasonal_naive | 4.000 | 4.000 | -43.962 | 3 |
| pleia_energy | xgboost | 1.000 | 1.000 | 24.074 | 3 |
| rico | attention_lstm | 2.750 | 2.500 | -75.794 | 4 |
| rico | persistence | 2.250 | 2.500 | 0.000 | 4 |
| rico | xgboost | 1.000 | 1.000 | 38.964 | 4 |

## Post-hoc comparisons (Holm-adjusted)

| A | B | Blocks | Rank A | Rank B | Median diff | p | Holm p | Significant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attention_lstm | persistence | 9 | 2.444 | 2.222 | -0.025 | 1.000 | 1.000 | no |
| attention_lstm | seasonal_naive | 9 | 2.444 | 3.778 | -0.421 | 0.074 | 0.371 | no |
| attention_lstm | xgboost | 9 | 2.444 | 1.556 | 0.281 | 0.074 | 0.371 | no |
| persistence | seasonal_naive | 9 | 2.222 | 3.778 | -0.533 | 0.129 | 0.387 | no |
| persistence | xgboost | 9 | 2.222 | 1.556 | 0.026 | 1.000 | 1.000 | no |
| seasonal_naive | xgboost | 9 | 3.778 | 1.556 | 0.945 | 0.004 | 0.023 | yes |
