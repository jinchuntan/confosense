# Verified methodology facts for Chapter 3

This package is a report-writing view of completed evidence. It does not define
a new experiment, recompute a scientific result, or merge protocols that used
different supports or endpoints. `EVIDENCE_MAP.csv` pins every comparison to a
Git commit and source file.

## Authoritative result generations

| Evidence family | Authoritative commit | Status |
|---|---|---|
| Matched forecasting and own-model intervals | `0c57f73618552514d41c6b78c631bd575beeebbc` | 195/195 task-horizon-fold-seed units validated |
| Broader interval methods and seasonal baseline | `7544e6aba3f6a8125711f0c7e38a69ca2369bf63` | 1,950/1,950 method cells and 27/27 unique seasonal computations validated |
| PLEIA energy conditional context | `80df3579dfe68ccf2c0d406c21c0fec967ff2b41` | five-seed, 68-context result validated |
| PLEIA temperature conditional context | `640aa76d0c4ff47d5fea09d160bfacf488b7c5e7` | five-seed, 68-context result validated |
| Robustness, contamination and recovery | `1b94d7dc027fe2a15049c82ba3c9a721df329ece` | 60/60 units and 900/900 cells validated |
| BDG2 one-hour operational replay | scientific `477151c0df4834fa1e26d6fbed260e0155bf5ff6`; final receipt `cb93a32a9e753295e313cae45ace1602e23eacb5` | 825/825 blocks and 2,475/2,475 evaluation rows validated |

These generations replace preliminary pilot tables, generic `run_study`
outputs, and earlier partial-completion statements. Historical results remain
provenance but must not be combined numerically with the tables here unless the
protocol and support are explicitly identified.

## Datasets, targets and forecast horizons

| Study task | Target and retained grouping | Sampling | Forecast horizons | Primary monitoring horizon |
|---|---|---:|---|---:|
| PLEIAData temperature (`pleia`) | Block B, room 11, variable V2 indoor temperature; one original series | 10 min | 1, 3, 6 steps = 10, 30, 60 min | 1 step / 10 min |
| PLEIAData energy (`pleia_energy`) | Block B interval consumption `dif_cons`; one original series | 10 min | 1, 3, 6 steps = 10, 30, 60 min | 1 step / 10 min |
| RICO HVAC (`rico`) | B.RTD3 indoor air temperature; 207 retained quality-screened runs | 1 min | 5, 15, 30, 60 steps = 5, 15, 30, 60 min | 5 steps / 5 min |
| BDG2 electricity (`bdg2`) | Hourly whole-building electricity consumption for ten retained buildings | 60 min | 1, 3, 6 steps = 1, 3, 6 h | 1 step / 1 h |

Temperature errors and interval widths are in degrees Celsius. PLEIA energy is
recorded as kWh per ten-minute interval; BDG2 is recorded as hourly kWh. Those
physical-unit metrics are never pooled across tasks.

## RO2 implementation chain

The implemented uncertainty-aware monitoring method connects these stages:

1. **Causal data preparation and chronological roles.** Dataset adapters create
   fixed fit, calibration and outer-test identities. Features use only values
   available at the forecast origin; tuning is confined to training-side
   roles. RICO run boundaries and BDG2 building groups are retained.
2. **Point forecasting.** Persistence, XGBoost and Attention-LSTM are evaluated
   on identical target rows in 13 task-horizon combinations, three outer folds
   and model seeds 42--46. Persistence performs no learned fit. Seasonal-naive
   is an additional deterministic baseline for PLEIA temperature, PLEIA energy
   and BDG2; RICO seasonal evaluation is inapplicable under the frozen design.
3. **Uncertainty construction.** Each point model has its own absolute-residual
   split-conformal 90% and 95% intervals. The broader matched matrix evaluates
   CQR, uncalibrated quantile intervals, static and sequentially updated
   recentred EnbPI, and DSCP at 90% and 95%.
4. **Online interval control.** Depending on the frozen protocol, interval
   state is static, periodically refreshed, rolling-window refreshed, or uses
   EnbPI's native per-step update. A score becomes available only after its
   target is observed; future residuals cannot enter an earlier interval.
5. **Interval-to-alert conversion.** An observation outside the interval forms
   the numerical alarm stream. Missingness/availability alarms are tracked
   separately and combined only in the declared combined channel. Temporal
   k-of-m rules turn sample alarms into alert episodes.
6. **Evaluation under clean, fault and recovery conditions.** Clean-stream
   workload is separated from event recall, precision, F1 and detection delay.
   Robustness replays propagate corrupt observations causally into later lags
   and rolling features. Calibration contamination changes calibration targets
   only; recovery is assessed by group with right censoring.
7. **Independent validation and preservation.** Saved metrics are independently
   reconstructed, completion resumes are zero-fit, and compact outputs are
   linked to verified raw-evidence backups and commit-pinned delivery receipts.

## Forecasting and interval protocols

### Matched forecasting

The 195 units equal 13 task-horizon combinations x three outer folds x five
model seeds. Each unit contains persistence, XGBoost and Attention-LSTM point
cells. Learned-model selection uses inner training roles; calibration and test
targets are common across models. The accepted completion contains 585 point
cells and 1,170 own-model interval cells. Report MAE and RMSE for point
accuracy; for intervals report empirical coverage, signed/absolute deviation
from nominal coverage, mean prediction-interval width (MPIW) and Winkler score.

### Broader interval methods

The 1,950-cell matrix equals all 13 task-horizons x three folds x five seeds x
five methods x two levels. `native` and `common` are reporting views of the same
cell, not extra experiments. Report-writing comparisons should normally use the
common-support table in this package.

- CQR and uncalibrated quantile intervals share the frozen quantile owner.
- Static and updated recentred EnbPI share the frozen EnbPI owner.
- DSCP reuses the matched XGBoost forecasting owner, so a contrast involving
  DSCP changes both the conformal construction and the predictor; it is not a
  pure post-hoc calibration comparison.
- Seasonal-naive uses 27 unique dataset/fold/horizon computations. Five
  seed-labelled views of one deterministic computation are aliases, not
  independent runs.

## Direct alert-evaluation protocols

### PLEIA conditional-context challenge

Temperature and energy are each evaluated at outer fold 2 and the one-step
(10-minute) horizon with model seeds 42--46. Every seed uses the same 68
original contexts and 2,856 fixed fault slots. Results first average model
seeds within original context and stratum, then weight the 21 declared strata
equally. Detection bounds use 2,000 paired chronological seven-context block
draws with RNG seed 20240601. Seeds do not become additional contexts.

The four 95% controls are:

| Control | Interval method | Online strategy |
|---|---|---|
| `quantile_static` | uncalibrated quantile | static |
| `cqr_static` | CQR | static |
| `cqr_rolling` | CQR | rolling; update every 24 steps from the latest 250 released scores |
| `persistence_static` | persistence split-conformal | static |

Rules are single-sample (1-of-1), 3-of-3 over 30 minutes, 4-of-6 over 60
minutes, 3-of-18 over 180 minutes, and 4-of-36 over 360 minutes. Results retain
availability-only, numerical-only and combined channels separately. This
endpoint estimates conditional synthetic-fault detection, misses, restricted
time to detection, background episodes per asset-day and time in alert. It
does not estimate natural fault prevalence or deployment precision/F1.

### BDG2 one-hour causal replay

The completed operational replay evaluates the BDG2 one-hour target over three
outer folds and five model seeds. Each candidate uses fixed operational004
catalogues; catalogue seeds are repetitions inside the evaluation, not
population replicates. The evaluated controls are:

- 95% uncalibrated quantile, static;
- 95% CQR with static, periodic (12/24/48 steps) and rolling (200/500 released
  scores, refreshed every 12/24/48 steps) strategies;
- recentred EnbPI at 95%, 97.5%, 99% and 99.5%, with static, periodic, rolling
  and native per-step updated strategies.

Rules are single-sample, 3-of-3 over 180 minutes and 4-of-6 over 360 minutes.
The fixed operational design contains missingness, stuck/dropout, bias,
level-shift and drift event families at the declared severities. The report
table keeps these distinct metrics:

- macro event recall: equal weight across the 21 type/severity strata;
- observed-strata recall: macro recall over strata actually represented;
- micro event recall: detected events divided by scheduled eligible events;
- ordinary matched-event episode precision: detected event matches divided by
  alert episodes on corrupted streams;
- custom synthetic F1: the frozen equal-stratum utility, not ordinary F1;
- restricted mean detection time: misses retained at the declared follow-up
  restriction;
- clean-stream alert workload: background episodes per asset-day; and
- fraction of monitored time in alert.

## Robustness, contamination and recovery

The frozen extension contains 60 historical units and 15 cells per unit (900
cells). Exact saved owners are used; eight absent high-level owners were built
with the authorized 24 quantile-estimator fits and eight conformalizations.
Scientific replay itself used zero model fits and zero conformalizations.

- **Zero control:** `level_shift@0` passes through the same rebuild/replay path
  and must equal the clean stream exactly.
- **Causal faults:** random missing affects 20% of the fault window; dropout,
  stuck, level shift and drift use the frozen definitions. Shift/drift
  severities are one and two training-only pooled standard deviations. The
  fault window is 25%--55% of the stream, with pre/during/post segments fixed.
- **Calibration contamination:** 0%, 5% and 10% of calibration targets receive
  a +2 training-only pooled-standard-deviation change. Test targets, test
  features and point predictions remain clean and identical.
- **Recovery:** static, periodic and rolling policies are assessed after
  `level_shift@2`. Recovery is computed for each physical group with fixed
  follow-up. Unobserved recovery remains right-censored rather than being
  converted into a recovery time.

## Inference and aggregation restrictions

Matched forecasting, interval methods, seasonal results, robustness and the
BDG2 operational replay are descriptive under the recorded dependence
structure. Overlapping folds, repeated model seeds, catalogue seeds, groups and
stream rows are not independent population replicates. Population confidence
intervals and significance claims are therefore unavailable.

The PLEIA conditional-context detection bounds use original contexts and the
stated chronological block design. They do not convert model seeds into new
observational units, and they do not apply to workload or delay endpoints.
