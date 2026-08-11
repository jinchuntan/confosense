# ConfoSense Full Study — Limitations

_Tracked automatically from the run manifest and the generated outputs. Inconvenient findings are recorded here rather than omitted._

## Recorded during this run

- No run-time limitation was recorded.

## Stages that failed or were skipped

| Stage | Status | Reason |
| --- | --- | --- |
| pleia:point | skipped | dataset already complete (--resume) |
| pleia:intervals | skipped | dataset already complete (--resume) |
| pleia:alerts | skipped | dataset already complete (--resume) |
| pleia:recalibration | skipped | dataset already complete (--resume) |
| pleia:robustness | skipped | dataset already complete (--resume) |
| pleia:statistics | skipped | dataset already complete (--resume) |
| pleia_energy:point | skipped | dataset already complete (--resume) |
| pleia_energy:intervals | skipped | dataset already complete (--resume) |
| pleia_energy:alerts | skipped | dataset already complete (--resume) |
| pleia_energy:recalibration | skipped | dataset already complete (--resume) |
| pleia_energy:robustness | skipped | dataset already complete (--resume) |
| pleia_energy:statistics | skipped | dataset already complete (--resume) |
| rico:point | skipped | dataset already complete (--resume) |
| rico:intervals | skipped | dataset already complete (--resume) |
| rico:alerts | skipped | dataset already complete (--resume) |
| rico:recalibration | skipped | dataset already complete (--resume) |
| rico:robustness | skipped | dataset already complete (--resume) |
| rico:statistics | skipped | dataset already complete (--resume) |
| bdg2:point | skipped | dataset already complete (--resume) |
| bdg2:intervals | skipped | dataset already complete (--resume) |
| bdg2:alerts | skipped | dataset already complete (--resume) |
| bdg2:recalibration | skipped | dataset already complete (--resume) |
| bdg2:robustness | skipped | dataset already complete (--resume) |
| bdg2:statistics | skipped | dataset already complete (--resume) |

## Seed counts actually used

| Dataset | Model | Seeds actually run | Stochastic |
| --- | --- | --- | --- |
| bdg2 | attention_lstm | 3 | yes |
| bdg2 | persistence | 1 | no |
| bdg2 | seasonal_naive | 1 | no |
| bdg2 | xgboost | 5 | yes |
| pleia | attention_lstm | 3 | yes |
| pleia | persistence | 1 | no |
| pleia | seasonal_naive | 1 | no |
| pleia | xgboost | 5 | yes |
| pleia_energy | attention_lstm | 3 | yes |
| pleia_energy | persistence | 1 | no |
| pleia_energy | seasonal_naive | 1 | no |
| pleia_energy | xgboost | 5 | yes |
| rico | attention_lstm | 3 | yes |
| rico | persistence | 1 | no |
| rico | xgboost | 5 | yes |

Persistence and seasonal naive are deterministic, so a single run is the complete result for them; the seed count is only meaningful for the stochastic methods.

Below the five-seed target because of CPU cost: bdg2/attention_lstm (3), pleia/attention_lstm (3), pleia_energy/attention_lstm (3), rico/attention_lstm (3). These are the counts actually executed, not the target.

## Methods not applicable

| Dataset | h | Model | Reason |
| --- | --- | --- | --- |
| rico | 5 | seasonal_naive | not applicable: no series contains a full seasonal cycle |
| rico | 15 | seasonal_naive | not applicable: no series contains a full seasonal cycle |
| rico | 30 | seasonal_naive | not applicable: no series contains a full seasonal cycle |
| rico | 60 | seasonal_naive | not applicable: no series contains a full seasonal cycle |

## Standing methodological caveats

- Anomalies are synthetic. The datasets carry no labelled real fault record, so alert precision and recall are measured against injected events whose catalogue is recorded in `data_profiles/injected_event_catalog.csv`. They quantify sensitivity to controlled disturbances, not field fault-detection performance.
- DSCP is applied to a multi-step vector assembled across ConfoSense's direct per-horizon models rather than a single multi-output model as in Yu et al. (2025). No official author implementation was located, so the code is written from the open-access preprint (arXiv:2503.21251v1) and the paper-to-code mapping is documented in `src/conformal_dscp.py`.
- The EnbPI variants are a documented **recentred** adaptation, reported as `recentred_enbpi_static` / `recentred_enbpi_updated`, never as standard EnbPI.
- Quantile regressors can produce crossing quantiles that MAPIE's conformal step does not always re-sort. Crossed pairs are ordered before any metric is computed, and the number repaired is reported in the `n_crossed_repaired` column of the interval tables. This affects nothing on PLEIAData (no interval crosses) and around 1% of CQR intervals on RICO.
- The seasonal-naive baseline is reported as not applicable wherever no series contains a full seasonal cycle, rather than being approximated with a cross-group lag.
- Cross-dataset comparisons use rankings, percentage improvement and normalised interval width; raw MAE is not compared across targets with different units.
