# Research question / objective evidence matrix

One block per research question. `result_table_or_figure` lists every persisted artefact that supports the stated evidence; all paths are relative to `outputs/full_study/`.

## RQ1 / RO1

**Research Problem.** Short-term building forecasts are deployed as point values, giving operators no calibrated statement of uncertainty and no principled threshold for raising an alert.

**Research Question.** How accurately can short-term building sensor and energy values be forecast, and do learned models improve on naive baselines?

**Research Objective.** RO1: implement and evaluate short-term point forecasting across heterogeneous building datasets against mandatory naive baselines.

**Method.** Direct horizon-specific forecasting with group-safe windowing; four arms (persistence, seasonal naive, XGBoost, Attention-LSTM); multi-seed refits; moving-block bootstrap, Diebold-Mariano with HLN correction, Friedman and Holm-corrected post-hoc.

**Final Evidence.** XGBoost wins on both energy targets and RICO (up to +48.8% MAE at RICO h=60); persistence wins on PLEIA temperature at all horizons and BDG2 h=1. Friedman chi2 = 14.07, p = 0.0028; Holm post-hoc finds only seasonal_naive vs xgboost significant (p = 0.0234); xgboost vs persistence p = 1.000.

**Conclusion.** Learned models help where the signal is spiky or the horizon long, and hurt on slow indoor temperature. The advantage is real in magnitude but not statistically separable from persistence across blocks, so the dissertation must claim target-dependent benefit, not general superiority.

**Result tables and figures.**

* `combined/point_metrics.csv`
* `combined/model_rankings.csv`
* `combined/effect_sizes.csv`
* `combined/bootstrap_metrics.csv`
* `combined/ranking_tests.csv`
* `combined/posthoc_comparisons.csv`
* `report/figures/fig_01_point_forecasting_comparison.png`
* `report/figures/fig_09_cross_dataset_rankings.png`

## RQ2 / RO2

**Research Problem.** Uncertainty estimates from quantile models are not calibrated, so intervals used for monitoring do not deliver their nominal coverage.

**Research Question.** Does conformal prediction deliver calibrated intervals for building time series, and which conformal method is preferable?

**Research Objective.** RO2: implement CQR, recentred EnbPI and DSCP under one protocol and compare them against an uncalibrated quantile baseline.

**Method.** Split-conformal calibration on a held-out chronological partition; CQR via MAPIE; recentred EnbPI with block bootstrap, static and online-updated; DSCP reimplemented from Yu et al. (2025) with the paper's smallest-cluster neighbourhood rule; coverage, deviation, width and Winkler at nominal 0.90 and 0.95.

**Final Evidence.** The uncalibrated baseline undercovers on all four datasets (deviation 0.070-0.320). recentred_enbpi_updated is best calibrated on bdg2 (0.9503), pleia_energy (0.9511) and rico (0.9036); cqr is best on pleia (0.9417) and best by Winkler on three datasets. On rico no method reaches nominal and CQR undercovers substantially (0.7719) with 2,558 crossed intervals repaired at the 0.95 level.

**Conclusion.** Conformal calibration is necessary and measurably effective, but no single conformal method transfers across datasets, and on run-structured HVAC data none of them is adequate.

**Result tables and figures.**

* `combined/interval_metrics.csv`
* `combined/rico_quantile_crossings.csv`
* `report/rico_quantile_crossing_audit.md`
* `report/figures/fig_02_coverage_vs_width.png`
* `fig_03_coverage_deviation_by_horizon.png`
* `fig_04_winkler_comparison.png`

## RQ3 / RO3

**Research Problem.** Interval-based alerting is proposed for building monitoring but its operating point, its behaviour under sensor faults, and its need for recalibration are rarely evaluated together.

**Research Question.** Can calibrated intervals support practical alerting, and does that alerting remain trustworthy under realistic data disturbance and drift?

**Research Objective.** RO3: evaluate interval-based alerting, its sensitivity to the aggregation rule, its robustness to disturbance, and the effect of periodic and rolling recalibration.

**Method.** Seven injected event types; k-of-m rules scored on a nested out-of-conformal-calibration block and frozen under a false-alert budget; 15 disturbance scenarios in legacy-fixed-interval and closed-loop modes plus three calibration-contamination levels; delay-aware static/periodic/rolling recalibration.

**Final Evidence.** Frozen rules differ per dataset (4-of-7, 2-of-3, 2-of-3, 1-of-1) with test F1 0.05-0.67. Under 2 sd sensor bias in closed loop, observed-signal coverage remains 0.888 (bdg2) and 0.976 (pleia_energy) while clean-reference coverage falls to 0.053 and 0.180 and clean-reference MAE rises 20.0 -> 472.0 kWh and 0.093 -> 0.622 kWh. 10% calibration contamination inflates PLEIA interval width 1.85 -> 26.82. Adaptive recalibration reduces coverage deviation on all four datasets.

**Conclusion.** Interval alerting works, but its operating point must be tuned per target, and conventional fixed-interval evaluation overstates its fault sensitivity: in closed loop the forecaster absorbs a sustained bias on three of four targets, so the monitor looks calibrated while the forecast diverges from reality. Recalibration mitigates drift but does not rescue BDG2.

**Result tables and figures.**

* `combined/alert_metrics.csv`
* `combined/robustness_metrics.csv`
* `combined/robustness_metric_schema.csv`
* `combined/recalibration_metrics.csv`
* `report/alert_selection_audit.md`
* `report/closed_loop_terminology.md`
* `report/figures/fig_05_alert_rule_sensitivity.png`
* `fig_06_alert_tradeoff.png`
* `fig_07_robustness_degradation.png`
* `fig_08_recalibration_recovery.png`
* `fig_13_closed_loop_absorption.png`

Machine-readable: `outputs/full_study/combined/rq_ro_evidence_matrix.csv`.

