# PLEIA-temperature conditional-context five-seed report

The authorized outer-fold-2/horizon-1 batch completed model seeds 43--46 and reused accepted seed 42 without refitting or replaying it. All units retain 68 original contexts, 2,856 fixed fault slots, four 95% controls, five rules, three channels, and fault-slot replicate seeds 42/43. No tuning, model selection, feature changes, extra datasets, or result-driven protocol changes occurred.

## Combined-channel detection and workload

Point estimates average model seeds within each original context/stratum and then weight the 21 strata equally. Bounds use 2,000 paired chronological seven-context block draws with RNG seed 20240601. Workload, delay, misses and seed dispersion are descriptive; unsupported or degenerate population intervals remain unavailable.

| control_id | rule_id | conditional_context_detection | lower | upper | status_inference | seed_sd_detection | mean_restricted_ttd_minutes | mean_misses | mean_background_episodes_per_asset_day | mean_fraction_time_in_alert |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cqr_rolling | 180min_3of18 | 0.38048 | 0.33452 | 0.438 | supported | 0.0041405 | 80.329 | 1666.6 | 0.95641 | 0.1876 |
| cqr_static | 180min_3of18 | 0.16761 | 0.022965 | 0.30813 | supported | 0.0050387 | 97.691 | 2264.2 | 0.4535 | 0.76962 |
| persistence_static | 180min_3of18 | 0.51271 | 0.43526 | 0.58847 | supported | 0 | 74.295 | 1315 | 0.81397 | 0.062582 |
| quantile_static | 180min_3of18 | 0.089125 | 0.0074041 | 0.14967 | supported | 0.015302 | 103.59 | 2487 | 0.60466 | 0.89634 |
| cqr_rolling | 30min_3of3 | 0.40963 | 0.37397 | 0.45161 | supported | 0.0064677 | 77.934 | 1571.2 | 1.3024 | 0.058484 |
| cqr_static | 30min_3of3 | 0.32487 | 0.23723 | 0.42008 | supported | 0.011119 | 91.159 | 1816 | 1.5407 | 0.65671 |
| persistence_static | 30min_3of3 | 0.18502 | 0.17033 | 0.1928 | supported | 0 | 95.496 | 2211 | 0.11628 | 0.00080751 |
| quantile_static | 30min_3of3 | 0.31833 | 0.19475 | 0.43291 | supported | 0.019452 | 92.067 | 1839.8 | 1.5204 | 0.75185 |
| cqr_rolling | 360min_4of36 | 0.19911 | 0.15861 | 0.2408 | supported | 0.0019027 | 95.962 | 2166.6 | 0.80234 | 0.26991 |
| cqr_static | 360min_4of36 | 0.10799 | 0.00021008 | 0.20741 | supported | 0.010245 | 102.86 | 2426.2 | 0.25291 | 0.80589 |
| persistence_static | 360min_4of36 | 0.37021 | 0.30656 | 0.43317 | supported | 0 | 84.037 | 1703 | 0.69769 | 0.099929 |
| quantile_static | 360min_4of36 | 0.054223 | 0 | 0.093353 | supported | 0.016795 | 106.33 | 2580.6 | 0.33431 | 0.93901 |
| cqr_rolling | 60min_4of6 | 0.30291 | 0.26094 | 0.36124 | supported | 0.0030812 | 88.868 | 1874 | 0.92444 | 0.075825 |
| cqr_static | 60min_4of6 | 0.25372 | 0.17838 | 0.34342 | supported | 0.0061333 | 97.724 | 2014.4 | 1.1308 | 0.6769 |
| persistence_static | 60min_4of6 | 0.1804 | 0.16588 | 0.19334 | supported | 0 | 97.555 | 2223 | 0.10175 | 0.0014131 |
| quantile_static | 60min_4of6 | 0.25321 | 0.15106 | 0.35008 | supported | 0.020274 | 96.907 | 2020.4 | 1.1047 | 0.77287 |
| cqr_rolling | single_sample | 0.68928 | 0.63158 | 0.73507 | supported | 0.004974 | 47.446 | 882.2 | 3.1105 | 0.091814 |
| cqr_static | single_sample | 0.42688 | 0.26104 | 0.5848 | supported | 0.0098364 | 75.655 | 1559.4 | 2.7878 | 0.68866 |
| persistence_static | single_sample | 0.90861 | 0.89671 | 0.91982 | supported | 0 | 24.624 | 261 | 4.2443 | 0.034824 |
| quantile_static | single_sample | 0.41193 | 0.23888 | 0.55772 | supported | 0.026717 | 79.244 | 1595.6 | 4.0321 | 0.79493 |

## Interval behavior

Across five seeds, full-clean rolling-CQR coverage is 0.9082 with mean width 9.1915 °C. Persistence coverage is 0.9652 with mean width 1.6000 °C. These results retain rather than tune away the adverse undercoverage and the rule-dependent detection/workload tradeoffs.

Original-context inference was supported for 56 of 60 control/rule/channel cells; 4 cells remain explicitly unavailable under the prespecified valid-draw and degeneracy gates.

## Validation and computation

All four new seeds passed full explicit-path A-and-B-and-C validation, completed zero-fit resume, owner/native-seed verification, operation-budget reconciliation and artifact-integrity checks. Independent aggregation reproduced all 60 endpoints and all saved draws; maximum point difference was 2.22e-16 and maximum bound difference was 0.

The four new units used 1.939 sequential run wall-hours and 4.623 validation wall-hours (6.869 hours across recorded freeze/readiness/run/validation/resume/verification phases). Maximum measured process-family working set was 847.6 MiB; minimum free disk was 92.73 GiB. Raw evidence was packaged into 40 verified parts totaling 2.046 GiB.

Actual new operations were four CQR wrapper fits containing twelve native quantile-estimator fits, eight recorded nested conformalization calls representing four logical conformalizations, and four persistence-radius computations. Seed-42 refits and additional model-family fits were zero.

## Interpretation limits

The five model seeds are robustness repetitions within the same historical conditional fault challenge; they are not five buildings or 340 independent contexts. The 68 original contexts remain the observational units. This endpoint does not estimate natural fault prevalence, precision, F1, deployment feasibility, or complete the matched-forecasting, interval-method, or seasonal matrices. Full-study readiness remains false.
