# Final figure index

All files under `outputs/full_study/report/figures/`.

| output file | purpose | dissertation section | main takeaway | exists |
|---|---|---|---|---|
| fig_01_point_forecasting_comparison.png | MAE by model, dataset and horizon | Ch. 5 - point forecasting | No model wins everywhere | True |
| fig_02_coverage_vs_width.png | Coverage against interval width per method | Ch. 5 - intervals | Calibration costs width; uncalibrated sits low-left | True |
| fig_03_coverage_deviation_by_horizon.png | Coverage deviation by horizon | Ch. 5 - intervals | Deviation grows with horizon on RICO | True |
| fig_04_winkler_comparison.png | Winkler score by method and dataset | Ch. 5 - intervals | Winkler and coverage disagree on two datasets | True |
| fig_05_alert_rule_sensitivity.png | k-of-m rule sensitivity | Ch. 5 - alerting | Precision/recall trade monotonically with k | True |
| fig_06_alert_tradeoff.png | Recall against false-alert workload | Ch. 5 - alerting | RICO cannot meet a 1/day budget at any rule | True |
| fig_07_robustness_degradation.png | Coverage under every disturbance, both reference signals | Ch. 5 - robustness | Observed-signal and clean-reference diverge in closed loop | True |
| fig_08_recalibration_recovery.png | Coverage recovery after a disturbance | Ch. 5 - recalibration | Adaptive strategies recover faster than static | True |
| fig_09_cross_dataset_rankings.png | Mean ranks across datasets | Ch. 5 - statistics | XGBoost first, seasonal naive last | True |
| fig_10_rico_interval_timeline.png | RICO interval timeline | Ch. 5 / Appendix | Interval behaviour within one experimental run | True |
| fig_11_bdg2_interval_timeline.png | BDG2 interval timeline | Ch. 5 / Appendix | Daily load cycle and interval width | True |
| fig_12_pleia_interval_timeline.png | PLEIA interval timeline | Ch. 5 / Appendix | Smooth target, narrow intervals | True |
| fig_13_closed_loop_absorption.png | Sensor-bias sweep: both coverage definitions and clean-reference MAE | Ch. 5 - robustness / Ch. 6 | The study's headline robustness result | True |
