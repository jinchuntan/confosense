# ConfoSense Full Study — Limitations

_Tracked automatically from the run manifest and the generated outputs. Inconvenient findings are recorded here rather than omitted._

## Recorded during this run

- Run executed in --fast smoke-test mode: reduced horizons, seeds, search iterations, epochs, bootstrap replicates and disturbance repetitions. Numbers are not the full-study results.
- DSCP is applied to a multi-step vector assembled across ConfoSense's direct per-horizon models rather than a single multi-output model as in Yu et al. (2025); documented deviation.

## Stages that failed or were skipped

- Every stage completed.

## Seed counts actually used

| Dataset | Model | Seeds actually run | Stochastic |
| --- | --- | --- | --- |
| pleia | attention_lstm | 1 | yes |
| pleia | persistence | 1 | no |
| pleia | seasonal_naive | 1 | no |
| pleia | xgboost | 2 | yes |

Persistence and seasonal naive are deterministic, so a single run is the complete result for them; the seed count is only meaningful for the stochastic methods.

Below the five-seed target because of CPU cost: pleia/attention_lstm (1), pleia/xgboost (2). These are the counts actually executed, not the target.

## Methods not applicable

- Every configured point model was applicable.

## Standing methodological caveats

- Anomalies are synthetic. The datasets carry no labelled real fault record, so alert precision and recall are measured against injected events whose catalogue is recorded in `data_profiles/injected_event_catalog.csv`. They quantify sensitivity to controlled disturbances, not field fault-detection performance.
- DSCP is applied to a multi-step vector assembled across ConfoSense's direct per-horizon models rather than a single multi-output model as in Yu et al. (2025). No official author implementation was located, so the code is written from the open-access preprint (arXiv:2503.21251v1) and the paper-to-code mapping is documented in `src/conformal_dscp.py`.
- The EnbPI variants are a documented **recentred** adaptation, reported as `recentred_enbpi_static` / `recentred_enbpi_updated`, never as standard EnbPI.
- Quantile regressors can produce crossing quantiles that MAPIE's conformal step does not always re-sort. Crossed pairs are ordered before any metric is computed, and the number repaired is reported in the `n_crossed_repaired` column of the interval tables. This affects nothing on PLEIAData (no interval crosses) and around 1% of CQR intervals on RICO.
- The seasonal-naive baseline is reported as not applicable wherever no series contains a full seasonal cycle, rather than being approximated with a cross-group lag.
- Cross-dataset comparisons use rankings, percentage improvement and normalised interval width; raw MAE is not compared across targets with different units.

- **This run used `--fast`.** Its numbers are a smoke test of the pipeline, not full-study results.
