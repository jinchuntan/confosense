# PLEIAData energy target audit

## Why this audit exists

The full study reports XGBoost MAE 0.0977 and RMSE 2.4510 at h=1 on `blockB-dif_cons` - a ratio of about 25x, where a well-behaved error distribution gives roughly 1.3. Three things had to be established: what the target is, whether the two metrics were computed on the same samples, and whether the extreme errors are real load or a data artefact.

## Target definition

* column: `blockB-dif_cons` - PLEIAData `dif_cons`, block B, 10min grid
* units: kWh per interval
* semantics: `dif_cons` is the **first difference of the cumulative energy meter** `cons_total`, i.e. the energy booked to each interval. It is not an instantaneous power reading and not a cumulative total.
* the source `cons_total` column is monotonically non-decreasing (True), so there is **no counter rollover and no meter reset** anywhere in the series.

## Distribution

| statistic | value |
|---|---|
| target_column | blockB-dif_cons |
| units | kWh per interval |
| target_kind | energy |
| n_observations | 50545 |
| n_valid | 50545 |
| n_missing | 0 |
| min | 0 |
| max | 326.531 |
| mean | 0.443189 |
| median | 0.40625 |
| std | 1.84855 |
| n_negative | 0 |
| n_zero | 1193 |
| skew | 154.994 |
| kurtosis | 25318 |
| p1 | 0 |
| p5 | 0.0859375 |
| p25 | 0.132812 |
| p50 | 0.40625 |
| p75 | 0.597656 |
| p95 | 1.07812 |
| p99 | 1.59375 |
| p99.9 | 2.40625 |

## What the extreme values actually are

The six largest interval increments, with the number of consecutive zero-increment steps immediately preceding each:

| timestamp | dif_cons | preceding_zero_steps | stall_hours | implied_rate_per_step |
|---|---|---|---|---|
| 2021-08-15 23:00:00+00:00 | 326.531 | 556 | 92.700 | 0.586 |
| 2021-12-13 07:30:00+00:00 | 246.008 | 385 | 64.200 | 0.637 |
| 2021-07-20 12:00:00+00:00 | 3.047 | 0 | 0.000 | 3.047 |
| 2021-07-19 15:30:00+00:00 | 2.961 | 0 | 0.000 | 2.961 |
| 2021-07-21 07:00:00+00:00 | 2.930 | 0 | 0.000 | 2.930 |
| 2021-09-30 10:50:00+00:00 | 2.891 | 0 | 0.000 | 2.891 |

This is decisive. The two extreme values are not consumption spikes: the cumulative meter **stalled** - reporting an unchanged total for 556 and 385 consecutive steps (93 h and 64 h) - and then caught up in a single interval. Spreading each catch-up over its own stall gives implied rates of 0.586 and 0.637 kWh per interval, either side of the series mean of 0.443: the *energy* is real, but it was consumed over days and is booked to one 10-minute stamp. Every other observation in the series is at or below 3.047 kWh per interval - a gap of roughly 80x.

These are therefore **data-acquisition discontinuities in the source feed**, evidenced by the `cons_total` column shipped with the dataset. They are not resets, not preprocessing effects introduced by this study, and not legitimate single-interval loads.

## Where they fall

* `2021-12-13 07:30:00+00:00` (246.008 kWh per interval) is in the **test** partition
* `2021-08-15 23:00:00+00:00` (326.531 kWh per interval) is in the **calibration** partition
* partition boundaries at h=1 (forecast origins): train 2021-01-07 23:50:00 -> 2021-07-30 14:20:00; calibration 2021-07-30 14:30:00 -> 2021-10-08 19:10:00; test 2021-10-08 19:20:00 -> 2021-12-17 23:50:00

## Metric-sample equality

MAE and RMSE are computed over the identical 10108 test rows from a single absolute-error vector with no separate filtering, so the gap is not a sample mismatch.

## Sensitivity to the single test-partition artefact

Reported values, and the same values with that one row excluded. The excluded figures are a **diagnostic only** - they are not the study's results and must not be quoted as such:

| point_model | mae | rmse | mae_excl_artefact | rmse_excl_artefact |
|---|---|---|---|---|
| persistence | 0.1417 | 3.4627 | 0.1174 | 2.4503 |
| seasonal_naive | 0.1982 | 3.4680 | 0.1739 | 2.4577 |
| xgboost | 0.0977 | 2.4510 | 0.0734 | 0.1550 |
| attention_lstm | 0.1020 | 2.4511 | 0.0777 | 0.1553 |

One observation out of 10108 inflates the XGBoost RMSE by 16x. Persistence is penalised twice, because it also carries the stale value forward into the following step. That is why every model's RMSE on this target collapses to nearly the same number: they are all being scored on the same unforecastable point.

Interval metrics at the operating point (cqr, h=1, nominal 0.95):

* coverage 0.973091; excluding the artefact 0.973187
* mean width 0.4099; excluding the artefact 0.4099
* Winkler 1.5865; excluding the artefact 0.6138

The artefact is not covered by its interval, so it costs one Winkler penalty and almost nothing in coverage. The **calibration-partition** artefact matters differently: it enlarges the conformal correction, which is a plausible contributor to this target's over-coverage (0.9731 against a nominal 0.95). That link is stated as a mechanism, not a measured decomposition.

## Decision

**The result is retained unchanged.** No observation was removed, no target was re-derived, and nothing was re-run to improve these numbers. The extreme values are diagnosable from the dataset's own cumulative column, but excluding them would mean redefining the target after seeing the results - exactly the move this study is designed not to make.

**Reporting consequences for the dissertation.**

1. MAE is the headline point metric for this target. RMSE must be reported alongside the explanation above, never as a bare number.
2. RMSE must not be compared across targets: the PLEIA temperature and energy RMSEs are not measuring comparable phenomena.
3. The near-identical RMSE across all four point models on this target is an artefact of one shared unforecastable observation, not evidence that the models perform alike.
4. Future work: gate the differenced meter on `cons_total` stalls and redistribute or mask catch-up intervals before modelling.

## Sources

* source meter: `data/interim/Data_Nature/processed_data/consB-10T.csv` (`dif_cons`, `cons_total`)
* errors: `outputs/full_study/pleia_energy/predictions/point_predictions.csv` (h=1)
* intervals: `outputs/full_study/pleia_energy/predictions/interval_predictions.csv`
* headline metrics: `outputs/full_study/combined/point_metrics.csv`, `outputs/full_study/combined/interval_metrics.csv`
* partitions: `outputs/full_study/pleia_energy/data_profiles/window_summary.csv`
* generated tables: `combined/pleia_energy_target_profile.json`, `combined/pleia_energy_meter_stalls.csv`, `combined/pleia_energy_artefact_sensitivity.csv`
