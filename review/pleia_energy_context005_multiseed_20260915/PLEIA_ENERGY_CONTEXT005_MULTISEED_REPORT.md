# PLEIA-energy conditional-context005 five-seed report

The authorized outer-fold-2/h1 batch completed model seeds 43–46 and reused the preserved seed-42 unit without rerunning it. All five seeds use the same 68 original contexts, 2,856 fault slots, four fixed 95% controls, five rules, three channels, calibration schedules and 68.798611 asset-day clean workload. Fault-slot seeds remain 42/43 and the energy-sensitivity mask remained inactive. No result-driven selection or retuning occurred.

## Combined-channel comparisons

The point is the frozen equal-seed-within-context, equal-context-within-stratum, equal-21-stratum detection endpoint. Bounds are approximate original-context block-bootstrap uncertainty conditional on this historical setting and protocol. Workload and restricted TTD remain descriptive. The directly accessible CSV contains all 60 control/rule/channel cells.

| control_id | rule_id | conditional_context_detection | lower | upper | status_inference | seed_sd_detection | mean_restricted_ttd_minutes | mean_misses | mean_background_episodes_per_asset_day | mean_fraction_time_in_alert |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cqr_rolling | 180min_3of18 | 0.38549 | 0.30408 | 0.4693 | supported | 0.047206 | 80.059 | 1672.4 | 1.218 | 0.099102 |
| cqr_static | 180min_3of18 | 0.32995 | 0.22872 | 0.44484 | supported | 0.083453 | 83.682 | 1827.2 | 1.6367 | 0.46383 |
| persistence_static | 180min_3of18 | 0.1588 | 0.075572 | 0.24848 | supported | 0 | 99.568 | 2301 | 0.55234 | 0.49046 |
| quantile_static | 180min_3of18 | 0.37762 | 0.2784 | 0.47828 | supported | 0.071873 | 80.03 | 1698.4 | 2.8256 | 0.49325 |
| cqr_rolling | 30min_3of3 | 0.33094 | 0.29579 | 0.3661 | supported | 0.016978 | 82.653 | 1811.2 | 0.13082 | 0.0010498 |
| cqr_static | 30min_3of3 | 0.41028 | 0.37575 | 0.44797 | supported | 0.027505 | 78.586 | 1597.8 | 1.7442 | 0.025336 |
| persistence_static | 30min_3of3 | 0.44069 | 0.25472 | 0.65034 | supported | 0 | 81.889 | 1521 | 6.2647 | 0.21995 |
| quantile_static | 30min_3of3 | 0.41295 | 0.39262 | 0.42339 | supported | 0.034024 | 76.506 | 1588.6 | 1.1047 | 0.012294 |
| cqr_rolling | 360min_4of36 | 0.25829 | 0.16586 | 0.35307 | supported | 0.035808 | 90.368 | 2023.8 | 1.0349 | 0.16354 |
| cqr_static | 360min_4of36 | 0.21671 | 0.11243 | 0.33245 | supported | 0.030681 | 93.753 | 2143.4 | 0.56687 | 0.53225 |
| persistence_static | 360min_4of36 | 0.090391 | 0.04281 | 0.14569 | supported | 0 | 104.9 | 2489 | 0.43606 | 0.52549 |
| quantile_static | 360min_4of36 | 0.24776 | 0.14523 | 0.35034 | supported | 0.052013 | 90.603 | 2058.2 | 1.3896 | 0.64946 |
| cqr_rolling | 60min_4of6 | 0.2826 | 0.25912 | 0.30462 | supported | 0.02883 | 89.277 | 1952.4 | 0.16279 | 0.0027859 |
| cqr_static | 60min_4of6 | 0.36197 | 0.30151 | 0.42545 | supported | 0.041196 | 84.144 | 1740.4 | 2.3314 | 0.058383 |
| persistence_static | 60min_4of6 | 0.26044 | 0.17487 | 0.3621 | supported | 0 | 95.034 | 2016 | 2.2093 | 0.36984 |
| quantile_static | 60min_4of6 | 0.39943 | 0.3683 | 0.42889 | supported | 0.04897 | 81 | 1634.2 | 1.8954 | 0.038882 |
| cqr_rolling | single_sample | 0.81604 | 0.77561 | 0.85837 | supported | 0.027882 | 39.438 | 524.4 | 6.7036 | 0.052044 |
| cqr_static | single_sample | 0.88739 | 0.84593 | 0.93074 | supported | 0.029725 | 30.297 | 321.6 | 16.05 | 0.17063 |
| persistence_static | single_sample | 0.86354 | 0.84879 | 0.89416 | supported | 0 | 36.242 | 385 | 11.381 | 0.35712 |
| quantile_static | single_sample | 0.89319 | 0.85707 | 0.93036 | supported | 0.031505 | 33.822 | 305 | 18.646 | 0.16905 |

## Validation and computation

All four new runs contain 685,440 event records; the combined five-seed evidence contains 856,800 records and 300 seed-specific macro cells. Independent aggregate validation reproduced all 60 endpoints using the saved contributions and the exact 2,000 paired chronological block draws. It found maximum point difference 2.22e-16 and maximum bound difference 0.

The four new seeds performed 4 CQR wrapper fits containing 12 native quantile-estimator fits, four logical conformalizations (eight nested profiler calls), four persistence-radius computations and zero persistence learned fits. Serialized native estimators carried their actual model seeds. Every new completed resume performed zero model fits, zero calibrator fits and zero replay updates.

| action | units | total_wall_seconds | mean_wall_seconds | max_wall_seconds |
| --- | --- | --- | --- | --- |
| freeze | 5 | 30.726 | 6.1452 | 6.3298 |
| readiness | 5 | 25.591 | 5.1182 | 5.4617 |
| resume | 5 | 5727.1 | 1145.4 | 3205.4 |
| run | 5 | 21515 | 4303 | 6190.1 |
| validate | 5 | 38138 | 7627.7 | 9222.2 |

Across all five units, run commands used 5.976 wall-hours, independent validation 10.594 wall-hours, and completed resume verification 1.591 wall-hours. These are summed sequential command durations; nested profiler calls are not added to them. The four new raw trees were packaged into 40 lossless parts (2.094 GiB), with every member read back and hash-verified.

## Interpretation limits

The 68 original contexts remain the independent observational units; the five training seeds are averaged within context and do not become 340 contexts. Repeated deterministic persistence results do not add data replicates. Detection intervals do not apply to workload or delay because those endpoints use different full-stream exposure, including the held-out tails. Degenerate or unsupported bounds remain explicitly unavailable. This conditional synthetic-fault endpoint does not estimate natural fault prevalence, deployment precision/F1, or amendment-004 feasibility, and it does not add cells to the matched forecasting or interval-quality matrices.
