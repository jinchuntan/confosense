# What ConfoSense is, and its final configuration

## Definition

**ConfoSense is not a model. It is a framework**: a specified pipeline plus a specified decision procedure for instantiating it on a given building target. Defining it as "XGBoost" or "CQR" would be wrong on this evidence, because neither wins across the four targets studied.

The framework fixes:

1. **Group-safe supervised windowing** with direct horizon-specific models - one model per horizon, no recursive feeding.
2. **A point forecaster** drawn from a declared candidate set (persistence, seasonal naive where a full cycle exists, XGBoost, Attention-LSTM), with naive baselines mandatory rather than optional.
3. **A conformal interval layer** drawn from a declared candidate set (CQR, recentred EnbPI static/updated, DSCP), always reported against an uncalibrated quantile baseline.
4. **Interval-violation alerting** with a k-of-m persistence rule frozen on out-of-conformal-calibration data under a stated false-alert budget.
5. **Delay-aware recalibration** (static / periodic / rolling) whose parameters come from a calibration replay with an h-step embargo, and which never consumes a residual before its ground truth exists.
6. **Closed-loop robustness evaluation** reporting observed-signal and clean-reference metrics separately.

## Universal configuration, or configurable framework?

**Configurable (option B). No universal configuration dominates**, and the evidence for that is direct:

* the best point forecaster differs by target (persistence on PLEIA temperature, XGBoost on both energy targets and RICO);
* the best-calibrated conformal method differs by dataset (`recentred_enbpi_updated` on three, `cqr` on one), and on RICO none reaches nominal;
* the frozen alert rule differs on all four datasets;
* the best recalibration strategy differs (rolling on PLEIA and pleia_energy, periodic on RICO and BDG2).

## Evidence class of each choice

This is the most important table in this document. Some components were selected without ever seeing test data; others are *comparisons* reported on test data. The dissertation must not present the second group as though the framework had chosen them blind.

| component | selected on | evidence class | persisted evidence |
|---|---|---|---|
| XGBoost hyperparameters | training data, 3-fold time-series CV | VALIDATED SELECTION | `<dataset>/models/xgboost_best_params_h*.json` |
| Alert operating rule | later 40% of the calibration partition | VALIDATED SELECTION | `<dataset>/metrics/alert_rule_selection_calibration.csv`, `alert_selection_split.csv` |
| Recalibration update_every / window | calibration replay with h-step embargo | VALIDATED SELECTION | `<dataset>/metrics/recalibration_selection.csv` |
| Target / building selection | documented criteria, no performance column | PRE-SPECIFIED | `<dataset>/data_profiles/target_selection.csv`, `subset_selection.csv`, `run_audit.csv` |
| Point-model family | test partition | REPORTED COMPARISON - NOT A VALIDATED SELECTION | `combined/point_metrics.csv` |
| Conformal method | test partition | REPORTED COMPARISON - NOT A VALIDATED SELECTION | `combined/interval_metrics.csv` |

The consequence: the point-forecaster and conformal-method rows in the per-target table below are **best-observed configurations**, not validated selections. A deployment would need a calibration-side model-selection protocol, which this study did not pre-register. That is a genuine limitation and is recorded as such.

## Per-target configuration

| dataset | point_forecaster | conformal_best_calibrated | conformal_best_winkler | alert_rule | recalibration |
|---|---|---|---|---|---|
| pleia | persistence | cqr | cqr | 4-of-7 | rolling |
| pleia_energy | xgboost | recentred_enbpi_updated | cqr | 2-of-3 | rolling |
| rico | xgboost | recentred_enbpi_updated | recentred_enbpi_updated | 2-of-3 | periodic |
| bdg2 | xgboost | recentred_enbpi_updated | quantile_uncalibrated | 1-of-1 | periodic |

Where the best-calibrated and best-Winkler conformal methods differ, both are shown: coverage deviation and Winkler answer different questions and neither alone is the right criterion.

### Rationale and limitations per target

**pleia (indoor temperature, 10 min).** Persistence is the strongest point forecaster at every horizon; the room is thermally slow and learned models add nothing at these horizons. CQR is best calibrated and best scoring. Rolling recalibration reduces coverage deviation to 0.002. Limitation: one room, one block - no cross-room generalisation is claimed.

**pleia_energy (interval consumption, 10 min).** XGBoost improves 24% in mean MAE over persistence. `recentred_enbpi_updated` is best calibrated, CQR best by Winkler. Limitation: the target contains two meter-stall catch-up artefacts, one in calibration and one in test; RMSE on this target is not interpretable without `pleia_energy_audit.md`.

**rico (HVAC air temperature, 1 min).** XGBoost wins at every horizon, by up to 39% in mean MAE. `recentred_enbpi_updated` and DSCP are the only arms above 0.89 coverage; CQR fails here. Limitation: **no arm reaches nominal coverage**, so this target is not solved, and the alert budget of 1 false alert/day is unreachable by any candidate rule.

**bdg2 (hourly electricity, 10 buildings).** XGBoost wins at 3 h and 6 h, persistence at 1 h. `recentred_enbpi_updated` is best calibrated (deviation 0.0008), CQR much better by Winkler because it is 32% narrower. Limitation: recalibration leaves coverage at 0.859 against 0.95, and no distinct rolling-window result exists.

## Recommended default when no per-target evidence is available

State it as a default, not as a validated optimum: persistence and XGBoost both fitted and the better one retained on calibration data; `recentred_enbpi_updated` as the conformal layer (best calibrated on three of four targets); a 2-of-3 or 3-of-5 rule as the starting point for budget-constrained tuning; periodic recalibration. Every one of these must be re-selected on the target's own calibration data before deployment.

## Sources

* `combined/confosense_configurations.csv`
* `combined/point_metrics.csv`, `combined/interval_metrics.csv`
* `combined/alert_metrics.csv`, `combined/recalibration_metrics.csv`
* `report/alert_selection_audit.md`, `report/pleia_energy_audit.md`, `report/rico_quantile_crossing_audit.md`
