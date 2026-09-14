# PLEIA-energy conditional-context005 pilot report

The exact outer-fold-2/model-seed-42/h1 pilot completed all 68 published contexts, 2,856 scheduled fault slots, 68 clean context identities, four fixed 95% controls and five rules. The final coordinator, all five CLI actions, independent validation and completed resume exited successfully. No setting was selected or changed using these outcomes.

## Every fixed control/rule comparison

The table below shows the combined channel. The machine table `control_rule_channel_summary.csv` contains the same fields for numerical-only, availability-only and combined channels: all 60 comparisons. Detection is the predeclared equal-context/equal-stratum macro; delay is minutes, with misses censored at 110 elapsed minutes for restricted TTD. Background comes from the original held-out clean stream.

| control_id | rule_id | conditional_context_detection | detected | misses | detected_delay_median_minutes | restricted_ttd_equal_stratum_minutes | background_episodes_per_asset_day | fraction_time_in_alert |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cqr_rolling | 180min_3of18 | 0.45321 | 1251 | 1491 | 30 | 74.352 | 1.2646 | 0.10245 |
| cqr_static | 180min_3of18 | 0.46831 | 1297 | 1445 | 20 | 70.867 | 2.5146 | 0.40194 |
| persistence_static | 180min_3of18 | 0.1588 | 441 | 2301 | 40 | 99.568 | 0.55234 | 0.49046 |
| quantile_static | 180min_3of18 | 0.49832 | 1369 | 1373 | 20 | 69.499 | 3.2995 | 0.4408 |
| cqr_rolling | 30min_3of3 | 0.32864 | 925 | 1817 | 30 | 82.984 | 0.17442 | 0.0014131 |
| cqr_static | 30min_3of3 | 0.38342 | 1070 | 1672 | 30 | 80.262 | 1.1483 | 0.022913 |
| persistence_static | 30min_3of3 | 0.44069 | 1221 | 1521 | 40 | 81.889 | 6.2647 | 0.21995 |
| quantile_static | 30min_3of3 | 0.39615 | 1112 | 1630 | 30 | 78.678 | 0.91572 | 0.011507 |
| cqr_rolling | 360min_4of36 | 0.26928 | 745 | 1997 | 30 | 89.961 | 1.0175 | 0.15888 |
| cqr_static | 360min_4of36 | 0.25579 | 704 | 2038 | 30 | 89.88 | 0.74129 | 0.52549 |
| persistence_static | 360min_4of36 | 0.090391 | 253 | 2489 | 50 | 104.9 | 0.43606 | 0.52549 |
| quantile_static | 360min_4of36 | 0.29211 | 800 | 1942 | 20 | 87.084 | 1.6715 | 0.62673 |
| cqr_rolling | 60min_4of6 | 0.26384 | 739 | 2003 | 30 | 90.417 | 0.20349 | 0.00323 |
| cqr_static | 60min_4of6 | 0.30309 | 842 | 1900 | 30 | 88.133 | 1.5553 | 0.042899 |
| persistence_static | 60min_4of6 | 0.26044 | 726 | 2016 | 50 | 95.034 | 2.2093 | 0.36984 |
| quantile_static | 60min_4of6 | 0.37473 | 1045 | 1697 | 30 | 82.836 | 1.8896 | 0.038861 |
| cqr_rolling | single_sample | 0.8096 | 2200 | 542 | 10 | 38.427 | 6.6862 | 0.052084 |
| cqr_static | single_sample | 0.89776 | 2450 | 292 | 10 | 29.952 | 14.026 | 0.14374 |
| persistence_static | single_sample | 0.86354 | 2357 | 385 | 20 | 36.242 | 11.381 | 0.35712 |
| quantile_static | single_sample | 0.89073 | 2430 | 312 | 10 | 32.639 | 17.689 | 0.15888 |

60/60 channel-specific macros met the frozen 21-stratum support rule. Numerical-only conditional detection ranged from 0.052 to 0.800; availability-only ranged from 0.060 to 0.286. These ranges are descriptive and include controls/rules with different clean alert workloads.

The PLEIA event envelope contains six observations (60 physical minutes from first through the boundary after the last sample). Episode matching retains the established last-envelope-observation plus six-sample tolerance convention: `(6-1+6) × 10 = 110` elapsed minutes. Misses receive 110 minutes in restricted TTD; detected-only delay excludes misses.

## Interval and workload definitions

`clean_counterfactual` scores the original meter truth against intervals issued after the variant’s causal observed history; `corrupted_observation` scores available corrupted readings against those intervals and excludes unavailable readings. `fullstream_clean_interval_diagnostics.csv` separately scores the untouched original held-out stream. Aliases retain scheduled incidence but do not add unique realizations or inferential units. Original exposure is 9,907 rows / 68.798611 asset-days for every control/rule/channel, including 115 rows outside challenge tiles.

## Computation and validation

| task | actual_exit_status | wall_seconds |
| --- | --- | --- |
| pleia_energy/freeze | 0 | 6.2178 |
| pleia_energy/readiness | 0 | 5.1926 |
| pleia_energy/run | 0 | 3149.8 |
| pleia_energy/validate | 0 | 5337.2 |
| pleia_energy/resume | 0 | 367.63 |

The operation ledger contains one real CQR wrapper fit, exactly three HistGradientBoosting quantile-estimator fits on 14,855 rows, and two nested profiler records for one logical conformalization on 4,954 rows. Persistence performs one recorded absolute-error radius construction and zero learned fits. Raw quantile, static CQR and rolling CQR share the fitted quantile owner. No XGBoost, Attention-LSTM, EnbPI, DSCP, tuning or matched-forecast fit occurred.

MAPIE logged raw quantile-order warnings during replay. The frozen implementation retains the learned raw tails and orders emitted lower/upper bounds; `stream_bound_integrity.csv` records raw crossings and verifies every emitted interval is ordered. The warnings did not trigger fitting, clipping, retuning or discarded outcomes.

The independent validator completed 61,200 numerical/identity checks, reconstructed 171,360 event/control/rule/channel records, checked 60 clean workload paths and found maximum absolute numerical difference 1.05e-15. Completed resume recorded zero model fits, calibrator fits and replay updates and preserved all scientific files.

## Interpretation limits

This is one model seed on one historically inspected evaluation period. Paired differences are descriptive; five-seed population intervals are unavailable and are stored as unavailable rather than fabricated. C measures detection conditional on declared synthetic faults in fixed contexts. It does not estimate real fault prevalence, deployment precision/F1, or amendment-004 natural-frequency feasibility. It does not add a matched forecasting or interval-quality cell. The energy sensitivity proposal was not adopted or applied; primary meter values and workload denominators remain intact.
