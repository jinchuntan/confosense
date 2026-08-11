# UCI Occupancy — auxiliary pipeline-portability check

> **This is not a dissertation benchmark.** It is a check on the software: can
> the generic ConfoSense pipeline ingest an independent public building-sensor
> dataset and run load → preprocess → partition → feature → forecast →
> conformalize → evaluate → report with only a small adapter? The numbers below
> describe that run. They are **not** used to select the ConfoSense
> configuration, are **not** part of the cross-dataset statistical comparison,
> and change no conclusion drawn from PLEIAData, RICO or BDG2.

Every value is read back from a file under `outputs/auxiliary_uci/`.

---

## 1. Dataset verification

| Item | Value |
|---|---|
| Official source | UCI Machine Learning Repository, dataset 357 |
| DOI | 10.24432/C5X01N |
| Download URL | `https://archive.ics.uci.edu/static/public/357/occupancy+detection.zip` |
| Licence | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| Retrieved | 2026-08-11T21:26:01Z |
| Archive sha256 | `4ae3f46aa98eedff564a9f6924d1635173e2fd2c816004342a9be93076d3a81a` (335,713 bytes) |

No mirror was used.

**Citation.** Candanedo, L. M. and Feldheim, V. (2016). Accurate occupancy
detection of an office room from light, temperature, humidity and CO₂
measurements using statistical learning models. *Energy and Buildings*, 112,
28–39. Dataset: Candanedo, L. (2016). *Occupancy Detection* [Dataset]. UCI
Machine Learning Repository. https://doi.org/10.24432/C5X01N

### Files

| File | Bytes | sha256 |
|---|---|---|
| `datatest.txt` | 200,766 | `1b92c7c1b2838963464fa891a610cf3c5db4becb7189189b29b330107a584c7f` |
| `datatraining.txt` | 596,674 | `b2c4d0ce2b9e4e453c476f7125ef31aeec2d1f5c7f5572d0e80de3df6521ab56` |
| `datatest2.txt` | 699,664 | `d026d1bd5aeccd4aff4f3b3710d48e40613bd5fc370db7e61bbdcaa50d985095` |

Raw files are gitignored and downloaded on demand.

### Variables

`date`, `Temperature` (°C), `Humidity` (%), `Light` (lux), `CO2` (ppm),
`HumidityRatio` (kg water-vapour / kg air), `Occupancy` (binary label, **not
used**).

### Verified temporal structure

Sampling was verified from the timestamps rather than assumed. The nominal
interval is **one minute**, recorded with about one second of jitter: the
interval counts split between 59 s, 60 s and 61 s in a symmetric pattern. After
rounding to the minute, each file spans exactly `n_rows − 1` minutes, so every
segment is **gap-free** and no interpolation was needed.

| Segment | Rows | Start | End | Gap to next |
|---|---|---|---|---|
| `datatest.txt` | 2,665 | 2015-02-02 14:19 | 2015-02-04 10:43 | 7 h 08 min |
| `datatraining.txt` | 8,143 | 2015-02-04 17:51 | 2015-02-10 09:33 | 1 d 05 h 15 min |
| `datatest2.txt` | 9,752 | 2015-02-11 14:48 | 2015-02-18 09:19 | — |

Total 20,560 rows, matching UCI's stated instance count. No missing values, no
duplicate timestamps, and the three files are pairwise disjoint in time with
zero shared timestamps.

**Two discontinuities exist and were preserved.** The files were *not*
concatenated into one index: doing so would manufacture continuity across a
seven-hour and a twenty-nine-hour recording break. Each becomes its own series,
so no feature window can reach across a gap.

**The chronological order is not the filename order.** `datatest.txt` is the
*earliest* segment and the file named `datatraining.txt` is the *middle* one.
The dataset's own train/test division therefore trains on data that postdates
part of its test set — acceptable for the original classification study, but not
for forecasting, which is why this run does not reuse it.

### Target

`Temperature` (°C), the documented continuous indoor air-temperature channel.
Chosen because it is continuous and compatible with this framework — **not** on
any forecasting-performance criterion (`data_profiles/dataset_profile.csv`).
`Occupancy` is a binary label and is not used, because ConfoSense is evaluated
here as a continuous-variable forecasting and uncertainty framework, not a
classifier.

---

## 2. Experimental configuration

| Item | Value |
|---|---|
| Partitioning | single chronological cut on the **pooled** timeline, 60 / 20 / 20 by observation |
| Horizons | 5 and 15 steps = **5 and 15 minutes** at the verified one-minute sampling |
| Predictors | target lags 1, 2, 3, 5, 10; rolling mean/std over 10 and 30 steps; cyclical hour and day-of-week; contemporaneous `Humidity`, `Light`, `CO2`, `HumidityRatio` |
| Point models | persistence, XGBoost (3 seeds, single-threaded refits) |
| Interval methods | uncalibrated quantile band, CQR |
| Nominal levels | 0.90 and 0.95 |
| Seasonal features | **omitted** (`season_steps = None`) |
| Seed | 42 |

**Why a pooled cut.** The three segments are disjoint *and* already ordered in
time, so one global cut keeps train < calibration < test in wall-clock order.
The per-series `ChronologicalPartitioner` used for the multi-building BDG2 panel
would instead place segment 1's test period *before* segment 2's training
period, fitting a model on observations recorded after forecasts it is scored
on. Realised partitions (`data_profiles/window_summary.csv`, h = 5):

| Partition | Windows | Origin span | Segments |
|---|---|---|---|
| train | 12,284 | 2015-02-02 14:33 → 2015-02-12 16:15 | all three |
| calibration | 4,112 | 2015-02-12 16:16 → 2015-02-15 12:47 | `datatest2` |
| test | 4,107 | 2015-02-15 12:48 → 2015-02-18 09:14 | `datatest2` |

Row-wise this is exactly 60 / 20 / 20 (12,336 / 4,112 / 4,112) and the three
spans do not overlap.

**Why no seasonal features.** The shortest segment is about 1.85 days, so a
1,440-step daily lag would consume the majority of it. The seasonal-naive
baseline is not part of this check, so the features were omitted rather than
fabricated.

---

## 3. Point-forecast results

Source: `metrics/point_metrics.csv`, `metrics/bootstrap_metrics.csv`.

| Horizon | Model | MAE (°C) | 95 % CI | RMSE (°C) | % MAE vs persistence | % RMSE vs persistence |
|---|---|---|---|---|---|---|
| 5 min | persistence | 0.0316 | [0.0288, 0.0341] | 0.0506 | — | — |
| 5 min | xgboost | 0.0391 | [0.0360, 0.0418] | 0.0540 | **−23.67** | −6.77 |
| 15 min | persistence | 0.0637 | [0.0563, 0.0705] | 0.0957 | — | — |
| 15 min | xgboost | 0.0635 | [0.0575, 0.0682] | 0.0858 | +0.35 | **+10.27** |

XGBoost seed spread is negligible (MAE sd 0.0002 over 3 seeds at both horizons).

**Observations.** Persistence is clearly better at 5 minutes; at 15 minutes the
two are indistinguishable on MAE (confidence intervals overlap heavily) while
XGBoost is better on RMSE. Absolute errors are very small — 0.03–0.06 °C —
because an office air temperature sampled every minute is extremely smooth.

This mirrors the pattern already reported for PLEIAData indoor temperature,
where persistence also won. It is recorded as an observation about pipeline
behaviour, **not** as cross-dataset evidence: this run is excluded from the
Friedman and Diebold–Mariano analyses.

---

## 4. Prediction-interval results

Source: `metrics/interval_metrics.csv`. Normalised width divides mean width by
the training-partition standard deviation.

| Horizon | Method | Nominal | Coverage | Deviation | Mean width | Norm. width | Winkler | Crossings repaired |
|---|---|---|---|---|---|---|---|---|
| 5 min | cqr | 0.90 | 0.9218 | 0.0218 | 0.2484 | 0.2190 | 0.2940 | 1 (0.02 %) |
| 5 min | quantile_uncalibrated | 0.90 | 0.7200 | 0.1800 | 0.1355 | 0.1195 | 0.3231 | 61 (1.49 %) |
| 5 min | cqr | 0.95 | **0.8169** | 0.1331 | 0.3094 | 0.2729 | 0.7696 | 18 (0.44 %) |
| 5 min | quantile_uncalibrated | 0.95 | 0.7022 | 0.2478 | 0.2035 | 0.1795 | 0.7043 | 611 (14.88 %) |
| 15 min | cqr | 0.90 | 0.9368 | 0.0368 | 0.4187 | 0.3702 | 0.4647 | 0 |
| 15 min | quantile_uncalibrated | 0.90 | 0.6890 | 0.2110 | 0.2138 | 0.1890 | 0.5479 | 57 (1.39 %) |
| 15 min | cqr | 0.95 | 0.9834 | 0.0334 | 0.6284 | 0.5556 | 0.6644 | 0 |
| 15 min | quantile_uncalibrated | 0.95 | 0.7681 | 0.1819 | 0.2607 | 0.2305 | 0.7693 | 18 (0.44 %) |

**Observations.**

1. The uncalibrated quantile band undercovers in all four cells (0.6890–0.7681),
   by 0.18 to 0.25. Conformal calibration improves coverage in every cell. This
   is the same qualitative contrast the four primary datasets show, which is
   what a portability check should demonstrate.
2. **CQR is not well calibrated here at 0.95.** At 5 minutes it reaches 0.8169
   against nominal 0.95 — material undercoverage — and at 15 minutes it
   over-covers at 0.9834. At 0.90 it is much closer (0.9218, 0.9368). The poor
   cell is reported as measured; portability does not require good accuracy.
3. Quantile crossings occur and are repaired by the existing audited
   order-restoring step. They concentrate in the uncalibrated band at 5 minutes
   and 0.95 (611 of 4,107, 14.88 %), where the two fitted quantiles are closest
   together relative to the noise.

---

## 5. Interval-violation diagnostic

Source: `metrics/interval_violation_diagnostic.csv`.

| Horizon | Test rows | Outside the 95 % CQR interval | Violation rate | Expected |
|---|---|---|---|---|
| 5 min | 4,107 | 752 | 0.1831 | 0.05 |
| 15 min | 4,097 | 68 | 0.0166 | 0.05 |

**This is a descriptive interval-violation diagnostic, not alert reliability.**
It is simply one minus empirical coverage restated in monitoring vocabulary. The
UCI dataset carries no labelled sensor-fault events of the kind the
dissertation's alert protocol scores against, so **no k-of-m rule was tuned, no
synthetic event catalogue was injected, and no precision, recall or F1 is
reported.** UCI is excluded from the dissertation's alert benchmark.

---

## 6. What was deliberately not run

DSCP · recentred EnbPI · Attention-LSTM · seasonal-naive baseline · alert-rule
selection · synthetic event catalogue · the robustness scenario matrix ·
calibration contamination · static/periodic/rolling recalibration ·
Friedman/Diebold–Mariano inclusion.

Each answers a research question this check makes no claim about, and running
them would invite these results to be read as a fifth primary dataset.

---

## 7. Portability conclusion

**The generic pipeline operated on UCI Occupancy without modification.** All six
stages completed with zero failures in 200.7 s
(`manifests/experiment_manifest.json`). Data loading, preprocessing,
chronological partitioning, feature generation, point forecasting, conformal
calibration, interval evaluation, bootstrap inference, provenance recording,
manifesting and reporting all ran through the same modules the four primary
experiments use.

The dataset-specific code is one adapter of about 300 lines, most of it
documentation, plus one 30-line partitioning strategy and a configuration file.
No generic component was altered; the only change outside the adapter was adding
its name to the registry's lazy import list.

---

## 8. Outputs

```
outputs/auxiliary_uci/
    data_profiles/  dataset_profile.csv, partition_summary.csv,
                    window_summary.csv, partitioning.json
    metrics/        point_metrics.csv, interval_metrics.csv,
                    interval_violation_diagnostic.csv, bootstrap_metrics.csv,
                    xgboost_best_params_h{5,15}.json
    predictions/    point_predictions.csv, interval_predictions.csv (gitignored)
    figures/        fig_uci_01_point_mae.png, fig_uci_02_cqr_interval.png
    report/         uci_auxiliary_results.md, uci_auxiliary_limitations.md,
                    dissertation_positioning.md
    manifests/      experiment_manifest.json, dataset_source.json,
                    dataset_sources.json, limitations.json, run_history.jsonl
```

`outputs/full_study/` was not opened, read for input, or written to.
