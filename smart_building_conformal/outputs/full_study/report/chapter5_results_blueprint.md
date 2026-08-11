# Chapter 5 (Results) — writing blueprint

Built **only** from the final audited outputs. Pre-audit values are obsolete and
must not appear: in particular the PLEIA alert rule is **4-of-7** (not 3-of-5),
the RICO alert rule is **2-of-3** (not 4-of-7), the RICO crossing count is
**3,912 of 66,696 overall** (2,558 is the 0.95-level subtotal), and robustness
coverage must always be qualified as *observed-signal* or *clean-reference*.

Chapter 5 reports. It does not interpret — interpretation belongs in Chapter 6.

---

## 5.1 Dataset Profiles

**Purpose.** Establish what was analysed, at what resolution, over what period,
and how it was partitioned, so every later number has a denominator.

**Table 5.1 — Dataset profiles.** Source: `<dataset>/data_profiles/series_profile.csv`,
`window_summary.csv`, `manifests/dataset_sources.json`.

| Dataset | Target | Units | Series | Observations | Sampling | Span | Horizons | Seasonal naive |
|---|---|---|---|---|---|---|---|---|
| PLEIA temperature | B-room11-V2 | °C | 1 | 50,543 | 10 min | 2021-01-01 – 2021-12-17 | 1, 3, 6 | applicable |
| PLEIA energy | blockB-dif_cons | kWh/interval | 1 | 50,545 | 10 min | 2021-01-01 – 2021-12-18 | 1, 3, 6 | applicable |
| RICO HVAC | B.RTD3 | °C | 207 runs | 49,680 | 1 min | 2023-07-26 – 2024-05-18 | 5, 15, 30, 60 | **not applicable** |
| BDG2 electricity | electricity | kWh | 10 buildings | 175,440 | 1 h | 2016-01-01 – 2017-12-31 | 1, 3, 6 | applicable |

**Table 5.2 — Supervised window counts at the operating horizon.** Source:
`<dataset>/data_profiles/window_summary.csv`.

| Dataset | h | Train | Calibration | Test |
|---|---|---|---|---|
| PLEIA temperature | 1 | 29,318 | 10,109 | 10,108 |
| PLEIA energy | 1 | 29,320 | 10,109 | 10,108 |
| RICO | 5 | 27,404 | 9,061 | 9,282 |
| BDG2 | 1 | 103,527 | 34,987 | 34,838 |

**Observations to state.**

1. Four targets of genuinely different character: a thermally slow indoor
   temperature, a spiky interval-consumption meter, a fast experimentally
   controlled HVAC air temperature, and pooled hourly electricity across ten
   buildings.
2. RICO carries no seasonal-naive baseline; no series contains a full daily
   cycle, so it is reported as *not applicable* rather than approximated.
3. RICO uses 207 of 287 candidate scheduler groups; 80 were excluded on the
   dataset authors' own quality flag (`rico/data_profiles/run_audit.csv`).
4. BDG2 uses 10 of 1,258 eligible buildings across 6 sites and 3 use types
   (`bdg2/data_profiles/subset_selection.csv`).
5. Partitioning is group-safe: RICO partitions whole experimental runs, BDG2
   partitions chronologically within each building
   (`<dataset>/data_profiles/partitioning.json`).

**Caveats.** Window counts differ slightly from raw observation counts because
windows require a complete feature history and a realised target; RICO's counts
differ per horizon because longer horizons consume more of each 4-hour run.

**Must not claim.** That the datasets are representative of building stock —
BDG2 is a 10-building sample and PLEIA is one room.

---

## 5.2 Point Forecasting Results

**Purpose.** Establish forecast accuracy against mandatory naive baselines.

**Table 5.3 — Best point forecaster per dataset and horizon.** Source:
`combined/point_metrics.csv`.

| Dataset | h | Minutes | Best model | MAE | RMSE | % MAE vs persistence |
|---|---|---|---|---|---|---|
| PLEIA temp | 1 | 10 | persistence | 0.2026 | 0.3253 | — |
| PLEIA temp | 3 | 30 | persistence | 0.3751 | 0.6058 | — |
| PLEIA temp | 6 | 60 | persistence | 0.5457 | 0.8723 | — |
| PLEIA energy | 1 | 10 | xgboost | 0.0977 | 2.4510 | +31.03 |
| PLEIA energy | 3 | 30 | xgboost | 0.1042 | 2.4517 | +20.07 |
| PLEIA energy | 6 | 60 | xgboost | 0.1117 | 2.4524 | +21.12 |
| RICO | 5 | 5 | xgboost | 0.0933 | 0.1259 | +23.66 |
| RICO | 15 | 15 | xgboost | 0.2198 | 0.3200 | +37.11 |
| RICO | 30 | 30 | xgboost | 0.3533 | 0.5145 | +46.32 |
| RICO | 60 | 60 | xgboost | 0.6163 | 0.9040 | +48.77 |
| BDG2 | 1 | 60 | persistence | 18.9167 | 37.8422 | — |
| BDG2 | 3 | 180 | xgboost | 28.1416 | 52.6496 | +21.81 |
| BDG2 | 6 | 360 | xgboost | 31.6766 | 60.0627 | +48.00 |

**Table 5.4 — Mean within-dataset ranks.** Source: `combined/model_rankings.csv`.

**Figure 5.1** — `fig_01_point_forecasting_comparison.png` (MAE by model,
dataset and horizon).

**Observations to state.**

1. XGBoost wins 9 of 13 dataset/horizon cells; persistence wins 4.
2. Persistence wins **every** PLEIA temperature horizon. XGBoost is 69.19 %
   *worse* than persistence there at h=1 (`combined/effect_sizes.csv`).
3. The learned-model advantage grows with horizon: RICO +23.66 % at 5 min to
   +48.77 % at 60 min; BDG2 crosses over from −12.86 % at 1 h to +48.00 % at 6 h.
4. Attention-LSTM never wins a cell outright.
5. Seasonal naive is the weakest arm wherever it applies (mean rank 3.78).

**Caveats.**

- **PLEIA energy RMSE is not interpretable as load volatility.** All four models
  report RMSE ≈ 2.45 because one shared unforecastable observation dominates the
  squared error; excluding it, XGBoost RMSE is 0.1550
  (`combined/pleia_energy_artefact_sensitivity.csv`, `report/pleia_energy_audit.md`).
  Report MAE as the headline for that target, with the artefact explained.
- MAE is not comparable across targets: °C against kWh.

**Must not claim.** That XGBoost is generally superior; that Attention-LSTM
underperformed because of insufficient data (not tested); that RMSE differences
on PLEIA energy reflect model quality.

---

## 5.3 Prediction Interval Results

**Purpose.** Establish whether conformal calibration delivers nominal coverage,
and at what cost in width.

**Table 5.5 — Interval performance at nominal 0.95, averaged over horizons.**
Source: `combined/interval_metrics.csv`.

| Dataset | Method | Coverage | Deviation | Mean width | Winkler |
|---|---|---|---|---|---|
| PLEIA temp | cqr | 0.9417 | 0.0083 | 2.5104 | 3.7967 |
| PLEIA temp | dscp | 0.9527 | 0.0135 | 2.8461 | 4.1529 |
| PLEIA temp | recentred_enbpi_updated | 0.9313 | 0.0187 | 2.7137 | 4.2553 |
| PLEIA temp | recentred_enbpi_static | 0.8902 | 0.0598 | 2.2644 | 4.5361 |
| PLEIA temp | quantile_uncalibrated | 0.8795 | 0.0705 | 1.9717 | 4.2150 |
| PLEIA energy | recentred_enbpi_updated | 0.9511 | 0.0027 | 0.8907 | 2.2778 |
| PLEIA energy | cqr | 0.9664 | 0.0164 | 0.4363 | 1.6582 |
| PLEIA energy | dscp | 0.9840 | 0.0340 | 0.9029 | 2.0311 |
| PLEIA energy | recentred_enbpi_static | 0.9853 | 0.0353 | 1.4036 | 2.5462 |
| PLEIA energy | quantile_uncalibrated | 0.8484 | 0.1016 | 0.2978 | 1.7070 |
| RICO | recentred_enbpi_updated | 0.9036 | 0.0464 | 1.7076 | 3.3217 |
| RICO | dscp | 0.8972 | 0.0528 | 1.7902 | 3.3731 |
| RICO | recentred_enbpi_static | 0.8722 | 0.0778 | 1.4266 | 4.3177 |
| RICO | cqr | 0.7719 | 0.1781 | 2.4983 | 11.2602 |
| RICO | quantile_uncalibrated | 0.6304 | 0.3196 | 1.8094 | 12.6819 |
| BDG2 | recentred_enbpi_updated | 0.9503 | 0.0008 | 203.5668 | 332.9632 |
| BDG2 | cqr | 0.9476 | 0.0033 | 138.8535 | 200.2521 |
| BDG2 | recentred_enbpi_static | 0.9419 | 0.0081 | 187.2787 | 329.7039 |
| BDG2 | dscp | 0.9274 | 0.0226 | 147.0737 | 287.4609 |
| BDG2 | quantile_uncalibrated | 0.8390 | 0.1110 | 127.0172 | 200.2032 |

**Table 5.6 — Coverage at nominal 0.90.** Same source; the 0.90 level shows the
same ordering, with RICO's best arm at 0.8289 (dscp).

**Figures.** `fig_02_coverage_vs_width.png`, `fig_03_coverage_deviation_by_horizon.png`,
`fig_04_winkler_comparison.png`.

**Observations to state.**

1. `quantile_uncalibrated` undercovers on **all four** datasets: deviation
   0.0705 (PLEIA temp) to 0.3196 (RICO) at nominal 0.95.
2. The best-calibrated arm differs by dataset: `recentred_enbpi_updated` on
   PLEIA energy, RICO and BDG2; `cqr` on PLEIA temperature.
3. On RICO **no arm reaches nominal**. The best single (method, horizon) cell is
   0.9293 and the best arm averaged over horizons is 0.9036, against 0.95.
4. CQR undercovered substantially on RICO (0.7719) with 2,558 crossed intervals
   order-repaired at the 0.95 level, 3,912 across both levels
   (`combined/rico_quantile_crossings.csv`).
5. DSCP over-covers on PLEIA energy (0.9840) and PLEIA temperature (0.9527) but
   is the second-best-calibrated arm on RICO (0.8972) at 28 % narrower width
   than CQR.
6. Coverage and Winkler disagree. On BDG2 the *uncalibrated* baseline has the
   lowest Winkler (200.2032 versus CQR 200.2521 — a 0.02 % difference) purely
   because it is narrower, while covering 0.8390 against 0.95.

**Caveats.**

- Observation 6 must be stated carefully: Winkler alone can favour an
  undercovering method whose width saving offsets its penalty. Coverage
  deviation and Winkler must be reported together; neither is sufficient alone.
- Widths are in target units and never comparable across datasets.
- The RICO crossing repair is order-restoring only (`min`/`max`); it raises
  coverage by 0.000–0.039 per cell and never to nominal, so the conclusion does
  not depend on it (`report/rico_quantile_crossing_audit.md`).

**Must not claim.** That any method is "well calibrated on RICO"; that CQR's
RICO undercoverage is *caused* by run structure; that the crossing repair
rescued or damaged the result; that DSCP is generally superior or inferior.

---

## 5.4 Alert-Rule Selection and Alert Performance

**Purpose.** Establish the operating point, how it was chosen without test data,
and how it performed.

**Table 5.7 — Nested calibration split.** Source:
`<dataset>/metrics/alert_selection_split.csv`.

| Dataset | Conformal block | Rule block | Embargoed | Boundary |
|---|---|---|---|---|
| PLEIA temp | 6,065 | 4,043 | 1 | 2021-09-10 17:10 |
| PLEIA energy | 6,065 | 4,043 | 1 | 2021-09-10 17:20 |
| RICO | 5,437 | 3,619 | 5 | 2024-05-08 13:32 |
| BDG2 | 20,999 | 13,978 | 10 | 2017-06-10 12:00 |

**Table 5.8 — Frozen operating rule, evaluated on test.** Source:
`combined/alert_metrics.csv` (`role = post_hoc_sensitivity`).

| Dataset | Rule | Precision | Recall | F1 | FAR | False alerts/day | Median delay (min) |
|---|---|---|---|---|---|---|---|
| PLEIA temp | 4-of-7 | 0.5763 | 0.8095 | 0.6733 | 0.0132 | 0.3562 | 30.0 |
| PLEIA energy | 2-of-3 | 0.4384 | 0.7619 | 0.5565 | 0.0102 | 0.5841 | 10.0 |
| RICO | 2-of-3 | 0.3125 | 0.8750 | 0.4605 | 0.2077 | 11.9457 | 1.0 |
| BDG2 | 1-of-1 | 0.0252 | 0.8810 | 0.0490 | 0.0575 | 0.9858 | 0.0 |

**Figures.** `fig_05_alert_rule_sensitivity.png`, `fig_06_alert_tradeoff.png`.

**Observations to state.**

1. The frozen rule differs on every dataset: 4-of-7, 2-of-3, 2-of-3, 1-of-1.
2. Test F1 spans 0.0490 (BDG2) to 0.6733 (PLEIA temperature) — an order of
   magnitude.
3. Recall is high and stable across datasets (0.76–0.88); precision is what
   varies (0.025–0.576).
4. On RICO **no candidate rule met the 1 false alert/day budget**; the quietest
   was taken, and it still produces 11.95 false alerts/day on test.
5. Longer persistence windows trade recall for precision monotonically where
   the budget is attainable.
6. Under the pooled procedure that this study replaced, the PLEIA calibration
   FAR for 3-of-5 was 0.0131 against 0.0508 under the leakage-safe split — the
   pooled surface understated it roughly fourfold
   (`report/alert_selection_audit.md`).

**Caveats.**

- Point-level FAR and false alerts per day are different quantities and must
  never be merged: FAR is a rate per opportunity, false alerts/day is a workload.
- All events are **injected**. Precision and recall measure sensitivity to
  controlled disturbances, not real fault-detection performance.
- BDG2's precision is low because 1-of-1 fires on any single violation across
  ten pooled buildings; that is the operating point the budget selected, not a
  failure of the framework.
- The frozen rule was selected against a model conformalized on 60 % of the
  calibration partition, while the reported test intervals use 100 % of it.

**Must not claim.** That the framework detects real building faults; that the
rule changes improved performance (on RICO the leakage-safe rule is *worse* on
test: F1 0.4605 versus 0.5344 for the superseded 4-of-7); that FAR and false
alerts per day measure the same thing.

---

## 5.5 Robustness Results (fixed-interval protocol)

**Purpose.** Report the conventional evaluation, in which the disturbance
affects the evaluated signal but never the model's inputs.

**Table 5.9 — Sensor bias under `legacy_fixed_intervals`.** Source:
`combined/robustness_metrics.csv`.

| Dataset | Bias | Observed-signal coverage | Clean-reference coverage | Alert rate |
|---|---|---|---|---|
| PLEIA temp | 2.0 σ | 0.0000 | 0.9373 | 0.9997 |
| RICO | 2.0 σ | 0.0000 | 0.7805 | 0.9999 |
| BDG2 | 2.0 σ | 0.0013 | 0.9427 | 0.9987 |
| PLEIA energy | 2.0 σ | 0.0749 | 0.9731 | 0.9279 |

**Table 5.10 — Calibration contamination.** Source: same file, `kind =
calibration_contamination`.

| Dataset | Level | Coverage | Mean interval width |
|---|---|---|---|
| PLEIA temp | 1 % | 0.9449 | 1.8526 |
| PLEIA temp | 5 % | 0.9970 | 14.4692 |
| PLEIA temp | 10 % | 1.0000 | 26.8179 |
| RICO | 10 % | 1.0000 | 34.0274 |
| BDG2 | 10 % | 0.9999 | 1,468.7591 |
| PLEIA energy | 10 % | 0.9968 | 2.0444 |

**Figure 5.7** — `fig_07_robustness_degradation.png`.

**Observations to state.**

1. Under the fixed-interval protocol every disturbance is loud: observed-signal
   coverage collapses to ≤ 0.075 at 2 σ and the alert rate approaches 1.
2. Clean-reference metrics are flat across severities **by construction** in
   this mode — the model never ingests the perturbation. State this explicitly
   so a reader does not read flatness as robustness.
3. Calibration contamination degrades monotonically and is the most damaging
   disturbance studied: 10 % contamination inflates PLEIA interval width from
   1.8526 (1 %) to 26.8179 and saturates coverage at 1.0000.
4. Coverage saturating at 1.0 is a failure mode, not a success: the intervals
   have become uninformative.

**Caveats.** Contamination is applied to the calibration partition and evaluated
on clean test data — a different design from the scenario rows, and it must be
labelled as such.

**Must not claim.** That the framework "detects" bias with high reliability —
this mode cannot show what happens when the fault enters the model's inputs.

---

## 5.6 Closed-Loop Disturbance Analysis

**Purpose.** Report what happens when the disturbance enters the feature history
and the forecast is computed from corrupted lags. This is the study's most
consequential result.

**Terminology (define before the table).** Source:
`combined/robustness_metric_schema.csv`, `report/closed_loop_terminology.md`.

| Term | Column | Meaning |
|---|---|---|
| observed-signal coverage | `empirical_coverage` | interval contains the reading the monitor received |
| clean-reference coverage | `empirical_coverage_vs_clean_truth` | interval contains the value the sensor should have reported |
| clean-reference MAE | `mae_vs_clean_truth` | forecast error against physical reality |

**Table 5.11 — 2 σ sensor bias, closed loop.** Source:
`combined/robustness_metrics.csv`.

| Dataset | Observed-signal coverage | Clean-reference coverage | Clean-reference MAE (clean → biased) | Alert rate (legacy → closed loop) |
|---|---|---|---|---|
| PLEIA energy | 0.9763 | 0.1804 | 0.0933 → 0.6216 | 0.9279 → 0.0058 |
| BDG2 | 0.8876 | 0.0529 | 20.0111 → 472.0058 | 0.9987 → 0.1124 |
| RICO | 0.5025 | 0.0001 | 0.1113 → 10.5115 | 0.9999 → 0.4972 |
| PLEIA temp | 0.2580 | 0.0006 | 0.3142 → 7.3606 | 0.9997 → 0.7315 |

**Figure 5.8** — `fig_13_closed_loop_absorption.png` (bias sweep: both coverage
definitions plus clean-reference MAE).

**Observations to state.**

1. The two protocols give opposite readings of the same disturbance.
2. Absorption is strongest on PLEIA energy and BDG2: observed-signal coverage
   remains 0.9763 and 0.8876 — near or above the clean baseline — while
   clean-reference coverage falls to 0.1804 and 0.0529.
3. Clean-reference MAE rises sharply in closed loop on every dataset: ×6.7
   (PLEIA energy), ×23.6 (BDG2), ×94 (RICO), ×23.4 (PLEIA temperature).
4. The alert rate falls in closed loop on every dataset, most sharply on BDG2
   (0.9987 → 0.1124): the monitor becomes quieter precisely as the forecast
   becomes more wrong.
5. **Absorption is a gradient, not a uniform effect.** On PLEIA temperature
   observed-signal coverage still falls to 0.2580 and the alert rate remains
   0.7315, so a 2 σ bias stays partly visible even in closed loop.

**Caveats.**

- The disturbance is experimentally manipulated, so a causal statement about the
  *injected bias* is legitimate here — unlike the interval comparisons.
- Clean-reference flatness in legacy mode is by construction and is not evidence.
- Undisturbed baselines (`kind = none`) must be shown alongside, otherwise the
  reader cannot tell how far each number has moved.

**Must not claim.** That closed-loop absorption occurs identically on every
dataset; that observed-signal coverage near nominal indicates a healthy monitor;
that this generalises to fault types not injected here.

---

## 5.7 Recalibration Results

**Purpose.** Establish whether delay-aware recalibration improves coverage.

**Table 5.12 — Recalibration.** Source: `combined/recalibration_metrics.csv`.

| Dataset | Strategy | Coverage | Deviation | Winkler | Distinct strategy |
|---|---|---|---|---|---|
| PLEIA temp | static | 0.9324 | 0.0176 | 2.8942 | yes |
| PLEIA temp | periodic | 0.9390 | 0.0110 | 2.8773 | yes |
| PLEIA temp | rolling | 0.9480 | **0.0020** | 2.8687 | yes |
| PLEIA energy | static | 0.9810 | 0.0310 | 2.0993 | yes |
| PLEIA energy | periodic | 0.9724 | 0.0224 | 2.0596 | yes |
| PLEIA energy | rolling | 0.9293 | **0.0207** | 1.8660 | yes |
| RICO | static | 0.9051 | 0.0449 | 0.9248 | yes |
| RICO | periodic | 0.9256 | **0.0244** | 0.8547 | yes |
| RICO | rolling | 0.9119 | 0.0381 | 0.8301 | yes |
| BDG2 | static | 0.8432 | 0.1068 | 202.3312 | yes |
| BDG2 | periodic | 0.8592 | **0.0908** | 194.0248 | yes |
| BDG2 | rolling | 0.8592 | 0.0908 | 194.0248 | **no** |

**Figure 5.9** — `fig_08_recalibration_recovery.png`.

**Observations to state.**

1. Adaptive recalibration reduces coverage deviation on all four datasets.
2. The best strategy differs: rolling on both PLEIA targets, periodic on RICO
   and BDG2.
3. The largest gain is PLEIA temperature: deviation 0.0176 → 0.0020 under
   rolling.
4. Recalibration does not rescue BDG2: coverage remains 0.8592 against 0.95.
5. **BDG2's rolling row is not a distinct strategy.** The calibration replay
   selected an unwindowed configuration, so rolling reduced to the same
   unbounded update procedure as periodic and reproduces it exactly. This is
   recorded in the data as `strategy_is_distinct = False`.

**Caveats.** Parameters came from a calibration replay with an h-step embargo,
never from test performance (`<dataset>/metrics/recalibration_selection.csv`).
Residual availability is enforced: no residual is consumed before its ground
truth exists.

**Must not claim.** That BDG2 has separate periodic and rolling results; that
rolling recalibration is generally best; that recalibration achieved nominal
coverage on BDG2 or RICO.

---

## 5.8 Statistical Analysis

**Purpose.** Establish which observed differences survive formal testing.

**Table 5.13 — Friedman test.** Source: `combined/ranking_tests.csv`.
χ² = 14.0667, p = 0.002816, 9 complete blocks, 4 methods, 4 blocks dropped
(RICO has no seasonal naive). Mean ranks: xgboost 1.5556, persistence 2.2222,
attention_lstm 2.4444, seasonal_naive 3.7778.

**Table 5.14 — Holm-corrected Wilcoxon post-hoc.** Source:
`combined/posthoc_comparisons.csv`. Only seasonal_naive vs xgboost is
significant (p_holm = 0.0234). xgboost vs persistence: p_holm = 1.0000.

**Table 5.15 — Diebold–Mariano (HLN corrected, Holm adjusted).** Source:
`combined/statistical_tests.csv`. 48 tests, **36 significant**:

| Pair | Tests | Significant |
|---|---|---|
| xgboost vs attention_lstm | 13 | 12 |
| xgboost vs persistence | 13 | 10 |
| attention_lstm vs persistence | 13 | 9 |
| seasonal_naive vs persistence | 9 | 5 |

**Figure 5.10** — `fig_09_cross_dataset_rankings.png`.

**Observations to state.**

1. The Friedman test rejects equality of the four point models across blocks.
2. After Holm correction only one pairwise comparison survives at the block
   level: seasonal_naive vs xgboost.
3. XGBoost is **not** significantly better than persistence across blocks
   (p = 1.0000), despite winning 9 of 13 cells.
4. Per-cell Diebold–Mariano tells a different and compatible story: xgboost beats
   persistence significantly in 10 of 13 individual cells.
5. Bootstrap confidence intervals bracket every point estimate across all 48
   rows (`combined/bootstrap_metrics.csv`).

**Caveats.** Observations 3 and 4 are **not contradictory** and must be
presented together: the block-level test asks whether one model dominates across
heterogeneous targets; the per-cell test asks whether it wins on a given target
and horizon. The answer is no to the first and usually yes to the second. Writing
only one of them would misrepresent the evidence.

**Must not claim.** That statistical significance demonstrates practical
superiority, or that its absence demonstrates equivalence.

---

## 5.9 Cross-Dataset Comparative Results

**Purpose.** Report which findings hold across all four targets and which do not.

**Consistent across all four datasets** (sources as cited above):

1. `quantile_uncalibrated` undercovers everywhere.
2. Adaptive recalibration reduces coverage deviation everywhere.
3. Closed-loop evaluation lowers the alert rate and raises clean-reference MAE
   relative to the fixed-interval protocol everywhere.
4. Calibration contamination is the most damaging disturbance everywhere.
5. Seasonal naive is the weakest point arm wherever it applies.

**Differs by dataset:**

1. Best point forecaster (persistence on PLEIA temperature; XGBoost elsewhere at
   longer horizons).
2. Best-calibrated conformal method.
3. Frozen alert rule (all four differ).
4. Best recalibration strategy.
5. Degree of closed-loop absorption.
6. Whether the false-alert budget is attainable at all (it is not on RICO).

**Table 5.16 — Per-target configuration.** Source:
`combined/confosense_configurations.csv`.

**Must not claim.** That any single configuration is best overall; that the
cross-dataset pattern would extend to datasets not studied.

---

## 5.10 Chapter Summary

Restate, without interpretation: what was measured, on how many cells, and which
results are qualified by an audit (PLEIA energy RMSE, RICO CQR undercoverage and
crossings, BDG2 rolling degeneracy, the two coverage definitions). Point forward
to Chapter 6 for interpretation.
