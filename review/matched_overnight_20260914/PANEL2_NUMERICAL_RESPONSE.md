# Panel 2: matched Attention-LSTM versus XGBoost evidence

Fold 2 / seed 42; positive differences mean LSTM is larger. CPU ratio is measured LSTM model-phase CPU divided by XGBoost CPU. Width alone is not interval quality; read achieved coverage and Winkler together.

| dataset | physical_minutes | mae_difference | rmse_difference | coverage_deviation95_difference | mpiw95_difference | winkler95_difference | process_cpu_seconds_ratio | model_phase_seconds_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 60 | 1.45398 | 1.07662 | 0.00178984 | 5.19472 | 4.38547 | 143.863 | 152.393 |
| bdg2 | 180 | 5.93024 | 13.7856 | -0.00034642 | 34.5442 | 91.6227 | 53.9156 | 53.4213 |
| bdg2 | 360 | 5.80442 | 10.9203 | -0.000663972 | 27.5916 | 73.2994 | 43.099 | 42.9851 |
| pleia | 10 | 0.769482 | 0.672312 | -0.0572323 | 1.50356 | 3.25226 | 52.788 | 51.7855 |
| pleia | 30 | 0.237183 | 0.168865 | -0.0301807 | 0.594164 | -1.78634 | 43.3908 | 44.476 |
| pleia | 60 | 0.183827 | 0.0615623 | -0.0359342 | 0.780933 | -8.7868 | 27.869 | 27.5715 |
| pleia_energy | 10 | -0.00330454 | 0.00582371 | -0.199758 | -0.268105 | 1.16578 | 25.683 | 24.7032 |
| pleia_energy | 30 | 0.00805599 | 0.0140901 | -0.0768144 | -0.0742696 | 0.474441 | 20.6376 | 20.8843 |
| pleia_energy | 60 | 0.028065 | 0.0162742 | -0.0398708 | 0.0292595 | 0.0287099 | 15.9198 | 16.0433 |
| rico | 5 | 1.97957 | 2.29081 | -0.546595 | 0.943643 | 58.9511 | 27.7123 | 27.3824 |
| rico | 15 | 1.95815 | 2.24949 | -0.633784 | 0.0245522 | 63.8263 | 23.1853 | 23.0714 |
| rico | 30 | 2.00205 | 2.18886 | -0.713708 | -0.580478 | 67.1742 | 20.8793 | 20.9784 |
| rico | 60 | 1.44077 | 1.3262 | -0.612242 | -1.61691 | 54.25 | 13.0042 | 12.9593 |

Numerical reading by horizon (own-model 95% split-conformal intervals):

- BDG2 electricity, 60 min: LSTM-minus-XGBoost MAE +1.45398, RMSE +1.07662, MPIW +5.19472, Winkler +4.38547 (kWh per hour); coverage 94.96% versus 94.78%. LSTM used 143.86× measured model-phase CPU (152.39× model-phase wall time).
- BDG2 electricity, 180 min: LSTM-minus-XGBoost MAE +5.93024, RMSE +13.7856, MPIW +34.5442, Winkler +91.6227 (kWh per hour); coverage 94.98% versus 95.01%. LSTM used 53.92× measured model-phase CPU (53.42× model-phase wall time).
- BDG2 electricity, 360 min: LSTM-minus-XGBoost MAE +5.80442, RMSE +10.9203, MPIW +27.5916, Winkler +73.2994 (kWh per hour); coverage 94.92% versus 94.98%. LSTM used 43.10× measured model-phase CPU (42.99× model-phase wall time).
- PLEIA temperature, 10 min: LSTM-minus-XGBoost MAE +0.769482, RMSE +0.672312, MPIW +1.50356, Winkler +3.25226 (degrees C); coverage 27.69% versus 33.41%. LSTM used 52.79× measured model-phase CPU (51.79× model-phase wall time).
- PLEIA temperature, 30 min: LSTM-minus-XGBoost MAE +0.237183, RMSE +0.168865, MPIW +0.594164, Winkler -1.78634 (degrees C); coverage 25.28% versus 28.29%. LSTM used 43.39× measured model-phase CPU (44.48× model-phase wall time).
- PLEIA temperature, 60 min: LSTM-minus-XGBoost MAE +0.183827, RMSE +0.0615623, MPIW +0.780933, Winkler -8.7868 (degrees C); coverage 27.49% versus 31.08%. LSTM used 27.87× measured model-phase CPU (27.57× model-phase wall time).
- PLEIA energy, 10 min: LSTM-minus-XGBoost MAE -0.00330454, RMSE +0.00582371, MPIW -0.268105, Winkler +1.16578 (kWh per 10 minutes); coverage 60.31% versus 80.29%. LSTM used 25.68× measured model-phase CPU (24.70× model-phase wall time).
- PLEIA energy, 30 min: LSTM-minus-XGBoost MAE +0.00805599, RMSE +0.0140901, MPIW -0.0742696, Winkler +0.474441 (kWh per 10 minutes); coverage 65.91% versus 73.59%. LSTM used 20.64× measured model-phase CPU (20.88× model-phase wall time).
- PLEIA energy, 60 min: LSTM-minus-XGBoost MAE +0.028065, RMSE +0.0162742, MPIW +0.0292595, Winkler +0.0287099 (kWh per 10 minutes); coverage 64.49% versus 68.48%. LSTM used 15.92× measured model-phase CPU (16.04× model-phase wall time).
- RICO temperature, 5 min: LSTM-minus-XGBoost MAE +1.97957, RMSE +2.29081, MPIW +0.943643, Winkler +58.9511 (degrees C); coverage 18.81% versus 73.47%. LSTM used 27.71× measured model-phase CPU (27.38× model-phase wall time).
- RICO temperature, 15 min: LSTM-minus-XGBoost MAE +1.95815, RMSE +2.24949, MPIW +0.0245522, Winkler +63.8263 (degrees C); coverage 17.80% versus 81.18%. LSTM used 23.19× measured model-phase CPU (23.07× model-phase wall time).
- RICO temperature, 30 min: LSTM-minus-XGBoost MAE +2.00205, RMSE +2.18886, MPIW -0.580478, Winkler +67.1742 (degrees C); coverage 13.58% versus 84.95%. LSTM used 20.88× measured model-phase CPU (20.98× model-phase wall time).
- RICO temperature, 60 min: LSTM-minus-XGBoost MAE +1.44077, RMSE +1.3262, MPIW -1.61691, Winkler +54.25 (degrees C); coverage 20.34% versus 81.56%. LSTM used 13.00× measured model-phase CPU (12.96× model-phase wall time).

These observed trade-offs do not establish statistical superiority or equivalence. More horizons are dependent comparisons, not independent replications. Phase imbalance, temporal drift, known-building scope, historical reuse and incomplete multi-seed/multi-fold evaluation remain limitations. Exact 90% and 95% signed coverage deviations and learned-minus-persistence contrasts are in the paired CSV.
