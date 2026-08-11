# RICO CQR quantile-crossing audit

## The repair under audit

MAPIE's conformalized quantile regressor can return a lower bound above
its upper bound: the underlying quantile regressors are fitted
independently and the conformal correction does not restore ordering.
`src/conformal_cqr.py::cqr_interval` applies exactly

```python
lower = np.minimum(raw_lo, raw_hi)
upper = np.maximum(raw_lo, raw_hi)
```

and returns `n_crossed_repaired` so the count reaches the output files.
No other modelling change is applied, here or in the study.

## Reproduction check

These counts were recomputed here from a fresh CQR fit, independently of the study run. They reproduce the `n_crossed_repaired` values the study recorded **exactly** (True), and post-repair coverage agrees to 0.00e+00. The audit and the reported results therefore describe the same fit.

## Extent

Across all horizons and nominal levels, **3912 of 66696 RICO CQR intervals cross before repair (5.87%)**. The headline figure quoted elsewhere, 2,558, is the subtotal at the 0.95 level only.

| horizon | nominal_coverage | n_intervals | n_crossed | pct_crossed | mean_crossing_magnitude | median_crossing_magnitude | max_crossing_magnitude | coverage_before_repair | coverage_after_repair | mean_signed_width_before | mean_width_after | winkler_after |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 0.9000 | 9282 | 463 | 4.9881 | 0.2314 | 0.2128 | 0.7290 | 0.8458 | 0.8460 | 1.2154 | 1.2385 | 2.0635 |
| 5 | 0.9500 | 9282 | 773 | 8.3279 | 0.4488 | 0.3949 | 1.7299 | 0.7769 | 0.7805 | 1.3697 | 1.4445 | 4.9681 |
| 15 | 0.9000 | 8862 | 57 | 0.6432 | 0.2141 | 0.2435 | 0.4735 | 0.8539 | 0.8548 | 1.3853 | 1.3881 | 2.2858 |
| 15 | 0.9500 | 8862 | 580 | 6.5448 | 0.7324 | 0.5928 | 1.9515 | 0.7791 | 0.8024 | 1.7385 | 1.8344 | 5.9688 |
| 30 | 0.9000 | 8232 | 36 | 0.4373 | 0.5212 | 0.6519 | 1.0763 | 0.8166 | 0.8166 | 2.2239 | 2.2285 | 3.6190 |
| 30 | 0.9500 | 8232 | 682 | 8.2847 | 0.6315 | 0.5514 | 3.1618 | 0.7453 | 0.7521 | 2.5445 | 2.6491 | 15.6525 |
| 60 | 0.9000 | 6972 | 798 | 11.4458 | 1.5424 | 1.3510 | 3.8667 | 0.7557 | 0.7946 | 2.9895 | 3.3426 | 7.8912 |
| 60 | 0.9500 | 6972 | 523 | 7.5014 | 0.6017 | 0.5296 | 1.7574 | 0.7526 | 0.7526 | 3.9750 | 4.0653 | 18.4514 |

By nominal level:

| nominal_coverage | n_intervals | n_crossed | pct_crossed |
|---|---|---|---|
| 0.900 | 33348 | 1354 | 4.060 |
| 0.950 | 33348 | 2558 | 7.671 |

By horizon:

| horizon | n_intervals | n_crossed | pct_crossed |
|---|---|---|---|
| 5 | 18564 | 1236 | 6.658 |
| 15 | 17724 | 637 | 3.594 |
| 30 | 16464 | 718 | 4.361 |
| 60 | 13944 | 1321 | 9.474 |

Crossing is roughly twice as frequent at the 0.95 level as at 0.90, which is consistent with the two fitted quantiles lying further into the tails and thus being estimated less stably. It is not monotonic in horizon.

## Where crossings occur

Crossings are strongly concentrated: they touch 16 of the 42 test runs, and in the worst-affected runs almost every interval crosses.

| horizon | nominal_coverage | group_id | n_crossed | n_intervals | pct_of_run |
|---|---|---|---|---|---|
| 60 | 0.90 | P5S50 | 166 | 166 | 100.00 |
| 30 | 0.95 | P5S38 | 196 | 196 | 100.00 |
| 60 | 0.95 | P5S50 | 150 | 166 | 90.36 |
| 5 | 0.95 | P5S43 | 186 | 221 | 84.16 |
| 5 | 0.95 | P5S32 | 170 | 221 | 76.92 |
| 5 | 0.90 | P5S43 | 170 | 221 | 76.92 |
| 60 | 0.90 | P5S32 | 127 | 166 | 76.51 |
| 5 | 0.95 | P5S50 | 164 | 221 | 74.21 |

Full per-run counts are in `combined/rico_quantile_crossings_by_run.csv`.

## Effect of the repair

Coverage before repair is well defined - a crossed pair simply covers nothing - and is tabulated above. Mean width and the Winkler score are **not** meaningful before repair, because a crossed pair has negative width; `mean_signed_width_before` is shown only to expose how small that quantity is and must not be read as an interval width.

The repair raises coverage by between 0.000 and 0.039 depending on the cell, and never brings it to nominal.

## Interpretation

CQR substantially undercovered on RICO under the evaluated protocol. The repair is order-restoring only: it cannot manufacture coverage, and post-repair coverage remains below nominal in every cell. Removing the repair would make the undercoverage worse, not better, so the scientific conclusion - that CQR is the weakest calibrated interval method on this dataset - does not depend on the repair.

The crossings are also not a rounding-scale nuisance: the median crossing magnitude ranges from 0.21 to 1.35 degC, comparable to the interval widths themselves in the affected cells.

Possible explanations, **stated as hypotheses that this experiment does not test**:

1. RICO's calibration and test partitions are disjoint sets of four-hour experimental runs following different set-point programmes, so calibration and test residuals may not be exchangeable.
2. The quantile regressors are fitted on pooled runs, and independent conditional quantile estimates are more likely to cross where the conditional distribution shifts sharply between regimes. The concentration of crossings in a minority of runs is consistent with this, but consistency is not evidence of cause.

Neither hypothesis is established here, and this study does **not** claim that RICO's run structure causes CQR to fail. Testing (1) would require a designed exchangeability test across run partitions; testing (2) would require a per-regime refit. Both are recorded as future work.

## Sources

* `outputs/full_study/combined/rico_quantile_crossings.csv`
* `outputs/full_study/combined/rico_quantile_crossings_by_run.csv`
* `outputs/full_study/rico/metrics/interval_metrics.csv` (`n_crossed_repaired` as recorded by the study run)
