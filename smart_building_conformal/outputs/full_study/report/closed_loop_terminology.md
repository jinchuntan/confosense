# Closed-loop robustness: terminology and verification

## The problem this fixes

Two different quantities in this study are both called *coverage*, and a disturbance experiment moves them in opposite directions. Comparing one against the other, or plotting them on a shared axis without labels, would make a captured forecast look healthy.

## Agreed terminology

| term | column | definition |
|---|---|---|
| observed-signal coverage | empirical_coverage | fraction of test steps where the interval contains the reading the monitor actually received (the perturbed signal). This is what the alert logic reacts to. |
| observed-signal coverage deviation | coverage_deviation | |observed-signal coverage - nominal|. |
| clean-reference coverage | empirical_coverage_vs_clean_truth | fraction of test steps where the interval contains the value the sensor should have reported, i.e. the unperturbed observation. |
| clean-reference coverage deviation | coverage_deviation_vs_clean_truth | |clean-reference coverage - nominal|. |
| observed-signal MAE | mae | mean absolute error of the point forecast against the perturbed signal. |
| clean-reference MAE | mae_vs_clean_truth | mean absolute error of the point forecast against the unperturbed observation: how wrong the forecast is about physical reality. |
| clean-reference RMSE | rmse_vs_clean_truth | as above, squared-error form. |
| alert rate | alert_rate | fraction of test steps at which the frozen k-of-m rule fires. |
| false-alert workload | false_alert_events_per_day | contiguous alert clusters outside any injected event window, per day. |

All schema columns are present in the persisted table.

The same distinction applies to error: **clean-reference MAE** is the only error figure that answers *how wrong is the forecast about reality*; observed-signal MAE falls when the model learns to track a corrupted sensor, which is the opposite of an improvement.

## The two modes

* `legacy_fixed_intervals` — the perturbation is applied to the evaluation signal only. The model never ingests it, so clean-reference metrics are flat **by construction** and only observed-signal metrics move. This is the conventional sensor-fault protocol.
* `closed_loop` — the perturbation enters the feature history, so the next forecast is computed from corrupted lags. Both families move.

A clean-reference metric that is constant across severities in legacy mode is therefore correct behaviour, not a bug.

## Sensor-bias sweep, verified under this terminology

| dataset | mode | severity_label | empirical_coverage | empirical_coverage_vs_clean_truth | mae | mae_vs_clean_truth | alert_rate | false_alert_events_per_day |
|---|---|---|---|---|---|---|---|---|
| bdg2 | closed_loop | 0.5 sigma | 0.9625 | 0.1651 | 27.0601 | 123.4544 | 0.0375 | 0.6104 |
| bdg2 | closed_loop | 1.0 sigma | 0.9386 | 0.0634 | 27.7898 | 241.4438 | 0.0614 | 0.8246 |
| bdg2 | closed_loop | 2.0 sigma | 0.8876 | 0.0529 | 44.1657 | 472.0058 | 0.1124 | 0.8708 |
| bdg2 | legacy_fixed_intervals | 0.5 sigma | 0.1347 | 0.9427 | 123.4044 | 20.0111 | 0.8653 | 1.2531 |
| bdg2 | legacy_fixed_intervals | 1.0 sigma | 0.0216 | 0.9427 | 244.9099 | 20.0111 | 0.9784 | 0.2101 |
| bdg2 | legacy_fixed_intervals | 2.0 sigma | 0.0013 | 0.9427 | 489.5225 | 20.0111 | 0.9987 | 0.0110 |
| pleia | closed_loop | 0.5 sigma | 0.8873 | 0.0238 | 0.3491 | 2.1038 | 0.0529 | 1.3106 |
| pleia | closed_loop | 1.0 sigma | 0.8316 | 0.0029 | 0.3833 | 4.2843 | 0.1116 | 2.0942 |
| pleia | closed_loop | 2.0 sigma | 0.2580 | 0.0006 | 1.6546 | 7.3606 | 0.7315 | 2.2651 |
| pleia | legacy_fixed_intervals | 0.5 sigma | 0.0226 | 0.9373 | 2.2745 | 0.3142 | 0.9873 | 0.3277 |
| pleia | legacy_fixed_intervals | 1.0 sigma | 0.0029 | 0.9373 | 4.5040 | 0.3142 | 0.9974 | 0.0712 |
| pleia | legacy_fixed_intervals | 2.0 sigma | 0.0000 | 0.9373 | 8.9736 | 0.3142 | 0.9997 | 0.0142 |
| pleia_energy | closed_loop | 0.5 sigma | 0.9769 | 0.4565 | 0.0964 | 0.2251 | 0.0119 | 0.5556 |
| pleia_energy | closed_loop | 1.0 sigma | 0.9777 | 0.1854 | 0.1001 | 0.3541 | 0.0049 | 0.3562 |
| pleia_energy | closed_loop | 2.0 sigma | 0.9763 | 0.1804 | 0.1343 | 0.6216 | 0.0058 | 0.3562 |
| pleia_energy | legacy_fixed_intervals | 0.5 sigma | 0.4519 | 0.9731 | 0.2122 | 0.0933 | 0.5275 | 3.6185 |
| pleia_energy | legacy_fixed_intervals | 1.0 sigma | 0.2640 | 0.9731 | 0.3753 | 0.0933 | 0.7067 | 3.8607 |
| pleia_energy | legacy_fixed_intervals | 2.0 sigma | 0.0749 | 0.9731 | 0.7136 | 0.0933 | 0.9279 | 2.0657 |
| rico | closed_loop | 0.5 sigma | 0.7988 | 0.0054 | 0.1199 | 2.7913 | 0.1995 | 17.0653 |
| rico | closed_loop | 1.0 sigma | 0.5997 | 0.0002 | 0.2472 | 5.4404 | 0.3991 | 32.7343 |
| rico | closed_loop | 2.0 sigma | 0.5025 | 0.0001 | 0.8328 | 10.5115 | 0.4972 | 19.3924 |
| rico | legacy_fixed_intervals | 0.5 sigma | 0.0495 | 0.7805 | 2.8576 | 0.1113 | 0.9510 | 3.8785 |
| rico | legacy_fixed_intervals | 1.0 sigma | 0.0000 | 0.7805 | 5.6932 | 0.1113 | 0.9999 | 0.1551 |
| rico | legacy_fixed_intervals | 2.0 sigma | 0.0000 | 0.7805 | 11.3644 | 0.1113 | 0.9999 | 0.1551 |

Undisturbed reference rows:

| dataset | mode | mae_vs_clean_truth | empirical_coverage_vs_clean_truth |
|---|---|---|---|
| bdg2 | legacy_fixed_intervals | 20.0111 | 0.9427 |
| bdg2 | closed_loop | 20.0111 | 0.9427 |
| pleia | legacy_fixed_intervals | 0.3142 | 0.9373 |
| pleia | closed_loop | 0.3142 | 0.9373 |
| pleia_energy | legacy_fixed_intervals | 0.0933 | 0.9731 |
| pleia_energy | closed_loop | 0.0933 | 0.9731 |
| rico | legacy_fixed_intervals | 0.1113 | 0.7805 |
| rico | closed_loop | 0.1113 | 0.7805 |

## What the sweep shows

In `legacy_fixed_intervals` the fault is loud: observed-signal coverage collapses toward zero and the alert rate approaches 1 at every severity, while clean-reference coverage and MAE do not move at all.

In `closed_loop` the picture reverses, and by different amounts per dataset:

* On **bdg2** and **pleia_energy** the fault is largely absorbed. At 2 sd, observed-signal coverage stays at 0.888 and 0.976 while clean-reference coverage falls to 0.053 and 0.180, and clean-reference MAE rises from 20.0 to 472.0 kWh and from 0.093 to 0.622 kWh. The monitor looks calibrated while the forecast is badly wrong about reality, and the alert rate falls from 0.999 to 0.112 (bdg2).
* On **rico** absorption is partial: observed-signal coverage at 2 sd is 0.503 against a clean-reference 0.0001.
* On **pleia** absorption is weakest: observed-signal coverage still falls to 0.258 and the alert rate stays at 0.732, so a 2 sd bias remains partly visible to the monitor even in closed loop.

The headline claim must therefore be stated with that gradient. *Closed-loop evaluation reveals substantial fault absorption on three of four targets, complete enough on bdg2 and pleia_energy that observed coverage stays near nominal while the forecast diverges from reality.* It is **not** true that absorption is total on every dataset.

## Sources

* `outputs/full_study/combined/robustness_metrics.csv`
* `outputs/full_study/combined/robustness_metric_schema.csv`
* `outputs/full_study/report/figures/fig_07_robustness_degradation.png`
* `outputs/full_study/report/figures/fig_13_closed_loop_absorption.png`
