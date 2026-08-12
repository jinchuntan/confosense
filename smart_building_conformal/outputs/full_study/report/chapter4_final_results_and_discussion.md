# Chapter 4 — Final Results and Discussion

*Dissertation-ready draft. Every numerical value in this chapter was read from a
persisted output under `outputs/full_study/`; the source path is stated beneath
each table. No value was entered by hand, and no result was recomputed for this
chapter.*

---

## 4.1 Experimental Overview

This chapter reports and interprets the final results of the ConfoSense study.
The framework was evaluated across four experimental settings drawn from three
independent public smart-building datasets, under a single controlled protocol
in which the partitions, features, random seeds, forecast horizons and metric
definitions were held identical across every method. Because the experimental
conditions were fixed, differences between methods reported below are
attributable to the methods themselves rather than to the settings under which
they were measured. Results and their interpretation are presented together,
subsection by subsection, and the chapter closes with the findings against each
research question, the final definition of the framework, and the limitations
that qualify those findings.

Two framing points should be established at the outset. First, the study was
executed in full and non-abbreviated form: the complete run recorded
`fast_mode: false` with zero failed stages across all four settings
(`manifests/run_history.jsonl`). Second, a fifth dataset — the UCI Occupancy
Detection recordings — was exercised only as an auxiliary check that the generic
software pipeline could ingest an independent public dataset. That auxiliary
experiment is reported in Appendix J and is deliberately excluded from every
table, statistical test and conclusion in this chapter.

### 4.1.1 Dataset Profiles and Targets

The four settings were chosen to differ in physical quantity, sampling
resolution, structural organisation and horizon regime, so that any finding
holding across all four would not be an artefact of a single measurement
context. PLEIAData contributed two distinct targets: a slow indoor air
temperature and a spiky interval-consumption meter. RICO contributed a fast,
experimentally controlled HVAC air temperature organised as independent
four-hour runs. BDG2 contributed pooled hourly electricity across ten separate
buildings. Table 4.1 summarises the four settings together with their supervised
partition sizes at the operating horizon.

Target selection followed documented, performance-blind rules in every case. The
RICO subset retained 207 of 287 candidate scheduler groups, the 80 exclusions
resting on the dataset authors' own quality flag rather than on any criterion of
this study; the BDG2 subset retained 10 of 1,258 eligible buildings across six
sites and three use types. Neither selection audit contains a forecast-performance
column.

**Table 4.1 — Dataset profiles and supervised partitions**

| Setting | Target | Units | Series | Observations | Sampling | Span | Horizons | Train | Calibration | Test | Seasonal naive |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PLEIA temperature | `B-room11-V2` | °C | 1 | 50,543 | 10 min | 2021-01-01 – 2021-12-17 | 1, 3, 6 | 29,318 | 10,109 | 10,108 | applicable |
| PLEIA energy | `blockB-dif_cons` | kWh per interval | 1 | 50,545 | 10 min | 2021-01-01 – 2021-12-18 | 1, 3, 6 | 29,320 | 10,109 | 10,108 | applicable |
| RICO HVAC | `B.RTD3` | °C | 207 runs | 49,680 | 1 min | 2023-07-26 – 2024-05-18 | 5, 15, 30, 60 | 27,404 | 9,061 | 9,282 | **not applicable** |
| BDG2 electricity | `electricity` | kWh | 10 buildings | 175,440 | 1 h | 2016-01-01 – 2017-12-31 | 1, 3, 6 | 103,527 | 34,987 | 34,838 | applicable |

*Partition counts are supervised windows at the operating horizon (h = 1 for the
PLEIAData and BDG2 settings, h = 5 for RICO). Sources:
`<dataset>/data_profiles/series_profile.csv`,
`<dataset>/data_profiles/window_summary.csv`,
`manifests/dataset_sources.json`.*

The seasonal-naive baseline was reported as *not applicable* for RICO rather
than approximated. No RICO series contains a full daily cycle, since each
experimental run lasts four hours, and fabricating a seasonal lag by reaching
across runs would have spliced unrelated experiments together. Recording the
baseline as inapplicable, with the reason, was preferred to producing a number
that would have been meaningless.

### 4.1.2 Data Partitions and Evaluation Scope

All partitions were chronological and group-safe, following a 60 / 20 / 20
division into training, conformal calibration and test. The two PLEIAData
settings were split chronologically along a single continuous series. RICO was
partitioned at run granularity, so that every timestamp of a four-hour
experimental run was assigned wholly to one partition and no run contributed
rows to two. BDG2 was partitioned chronologically within each building, which
preserves the temporal ordering that matters for each building's own forecasts.

Several controls were applied to prevent information from the future entering a
forecast. Forecasting was performed directly at each horizon, with one model per
horizon and no recursive feeding of predictions back into inputs. Feature
windows were constructed per series, so no lag or rolling statistic could reach
across a run boundary in RICO or a building boundary in BDG2. Residual
availability was enforced throughout the adaptive procedures: a residual became
usable at forecast origin *t* only once its target time had passed, so no
recalibration step consumed an observation that had not yet been made. The alert
operating point was selected on a block of calibration data that the conformal
quantile had never seen, by the nested procedure described in Section 4.4.1, and
the recalibration parameters were chosen by a calibration replay separated by a
horizon-length embargo.

The evaluation scope comprised 13 dataset-and-horizon cells for point
forecasting, five interval methods at two nominal coverage levels, four
candidate alert rules, three recalibration strategies, and fifteen disturbance
scenarios evaluated under two distinct evaluation modes together with three
levels of calibration contamination.

**Takeaway.** The four settings were deliberately heterogeneous in physics,
resolution and structure; the partitioning and leakage controls were designed so
that heterogeneity, rather than experimental artefact, would be the source of any
observed difference.

---

## 4.2 Point Forecasting Results and Discussion

This section reports the accuracy of the four point-forecasting arms —
persistence, seasonal naive, XGBoost and an attention-based LSTM — against the
mandatory naive baselines. Naive baselines were treated as compulsory rather than
optional throughout, because a study reporting only learned models cannot
establish that learning was necessary. Table 4.2 gives the complete results.

**Table 4.2 — Point forecasting results by dataset and horizon**

| Setting | h | Minutes | Model | MAE | RMSE | % MAE vs persistence |
|---|---|---|---|---|---|---|
| PLEIA temp | 1 | 10 | **persistence** | **0.2026** | 0.3253 | — |
| PLEIA temp | 1 | 10 | xgboost | 0.3428 | 0.5014 | −69.19 |
| PLEIA temp | 1 | 10 | attention_lstm | 0.8029 | 1.0739 | −296.28 |
| PLEIA temp | 1 | 10 | seasonal_naive | 1.4768 | 2.1973 | −628.92 |
| PLEIA temp | 3 | 30 | **persistence** | **0.3751** | 0.6058 | — |
| PLEIA temp | 3 | 30 | xgboost | 0.5317 | 0.7283 | −41.75 |
| PLEIA temp | 6 | 60 | **persistence** | **0.5457** | 0.8723 | — |
| PLEIA temp | 6 | 60 | xgboost | 0.6933 | 0.9500 | −27.04 |
| PLEIA energy | 1 | 10 | **xgboost** | **0.0977** | 2.4510 | +31.03 |
| PLEIA energy | 1 | 10 | persistence | 0.1417 | 3.4627 | — |
| PLEIA energy | 3 | 30 | **xgboost** | **0.1042** | 2.4517 | +20.07 |
| PLEIA energy | 6 | 60 | **xgboost** | **0.1117** | 2.4524 | +21.12 |
| RICO | 5 | 5 | **xgboost** | **0.0933** | 0.1259 | +23.66 |
| RICO | 5 | 5 | persistence | 0.1222 | 0.2151 | — |
| RICO | 15 | 15 | **xgboost** | **0.2198** | 0.3200 | +37.11 |
| RICO | 30 | 30 | **xgboost** | **0.3533** | 0.5145 | +46.32 |
| RICO | 60 | 60 | **xgboost** | **0.6163** | 0.9040 | +48.77 |
| BDG2 | 1 | 60 | **persistence** | **18.9167** | 37.8422 | — |
| BDG2 | 1 | 60 | xgboost | 21.3487 | 39.7102 | −12.86 |
| BDG2 | 3 | 180 | **xgboost** | **28.1416** | 52.6496 | +21.81 |
| BDG2 | 6 | 360 | **xgboost** | **31.6766** | 60.0627 | +47.99 |
| BDG2 | 6 | 360 | seasonal_naive | 36.5308 | 79.0989 | +40.03 |

*Best model per cell in bold. The table is abridged for readability; the complete
52-row matrix including all four arms at every horizon appears in Appendix E.
Sources: `combined/point_metrics.csv`, `combined/effect_sizes.csv`.*

### 4.2.1 PLEIAData Results

The two PLEIAData targets produced opposite conclusions from the same building,
the same instrumentation and the same protocol, which is the clearest single
demonstration in this study that model value depends on the target rather than on
the dataset.

On indoor temperature, persistence was the strongest forecaster at all three
horizons. XGBoost was 69.19 % worse than persistence in mean absolute error at
ten minutes, 41.75 % worse at thirty minutes and 27.04 % worse at sixty minutes.
The attention-based LSTM was worse still, and seasonal naive was by a wide margin
the weakest arm. The interpretation is physical rather than algorithmic: the room
is thermally slow, so over ten minutes the best available estimate of the future
temperature is the present temperature, and a learned model can only add
estimation variance to a signal that has almost no exploitable structure at these
horizons. The narrowing of the deficit as the horizon lengthens — from 69 % to
27 % — is consistent with that reading, since the persistence assumption weakens
as the forecast reaches further ahead.

On interval energy consumption, the ordering reversed. XGBoost improved on
persistence by 31.03 %, 20.07 % and 21.12 % at the three horizons. A spiky
consumption meter carries exploitable structure — occupancy and plant-cycling
patterns that calendar and covariate features can capture — and persistence
performs poorly precisely because consecutive intervals are weakly correlated.

One result on the energy target requires careful reporting. The root mean squared
error was approximately 2.45 for every model, a value roughly twenty-five times
the corresponding mean absolute error. The audit of this target established that
the discrepancy was **not** a property of the load. The source cumulative meter
`cons_total` is monotonically non-decreasing throughout, so no counter reset or
rollover occurred; instead the meter feed stalled twice, reporting an unchanged
cumulative total for 556 and 385 consecutive ten-minute steps — approximately 93
and 64 hours — and then discharged the accumulated consumption into a single
interval. Spreading each catch-up across its own stall yields implied rates of
0.586 and 0.637 kWh per interval, either side of the series mean of 0.443,
confirming that the energy was real but had been consumed over days and booked to
one timestamp. One of these artefacts falls in the test partition. Excluding that
single observation from 10,108 reduces the XGBoost RMSE from 2.4510 to 0.1550, a
factor of approximately sixteen. The observation was **retained**, since removing
it would have redefined the target after seeing the results, but the consequence
for reporting is firm: mean absolute error is the headline metric for this target,
and RMSE must never be quoted without the explanation above. The near-identical
RMSE across all four models on this target reflects one shared unforecastable
observation and is not evidence that the models perform alike.

*Sources: `report/pleia_energy_audit.md`,
`combined/pleia_energy_meter_stalls.csv`,
`combined/pleia_energy_artefact_sensitivity.csv`.*

### 4.2.2 RICO HVAC Results

RICO produced the study's most decisive point-forecasting result. XGBoost won at
every horizon, and its margin over persistence widened monotonically with the
forecast lead: 23.66 % at five minutes, 37.11 % at fifteen, 46.32 % at thirty and
48.77 % at sixty minutes. The attention-based LSTM was substantially worse than
persistence at the two shortest horizons (−263.65 % at five minutes) and only
overtook it at sixty minutes (+23.20 %).

The interpretation follows from the experimental design of the dataset. RICO
recordings are controlled HVAC experiments in which set-point programmes drive
the air temperature through deliberate transients. At one-minute resolution the
signal is smooth enough that persistence is competitive over a single step, but
as the horizon extends the scheduled dynamics dominate, and a model with access
to covariates and recent history can anticipate them where a naive carry-forward
cannot. The monotone widening of the margin is the signature of that mechanism.

### 4.2.3 BDG2 Results

BDG2 exhibited a crossover. At one hour ahead persistence was best, with XGBoost
12.86 % worse. At three hours XGBoost led by 21.81 %, and at six hours by
47.99 %. The physical reading is that hourly electricity in an occupied building
is strongly autocorrelated at one lag, so the previous hour is an excellent
predictor of the next, but by three to six hours the daily occupancy cycle
matters more than the immediate past, and that cycle is learnable.

BDG2 was also the only setting in which the seasonal-naive baseline proved
useful. At six hours ahead it achieved a mean absolute error of 36.53 against
persistence's 60.91, an improvement of 40.03 %, because a same-time-yesterday
prediction captures the daily cycle that persistence loses at that lead. It
remained inferior to XGBoost (31.68), but the result is a reminder that naive
baselines should be selected to match the horizon regime rather than dismissed
collectively.

### 4.2.4 Cross-Dataset Point Forecasting Comparison

Aggregating across the 13 dataset-and-horizon cells, XGBoost achieved the lowest
mean absolute error in nine cells and persistence in four. The attention-based
LSTM did not win a single cell outright, and seasonal naive won none. Within
datasets, XGBoost ranked first on three of the four settings, while persistence
ranked first on PLEIA temperature with a perfect mean rank of 1.00.

Two patterns hold across settings. Learned models gained value as the forecast
horizon lengthened, evidenced on RICO by the monotone progression from +23.66 %
to +48.77 % and on BDG2 by the crossover from −12.86 % to +47.99 %. Conversely,
the smoother and slower the target, the more competitive naive persistence
became, with PLEIA temperature the limiting case in which persistence was never
beaten.

Seed variability was small for XGBoost and larger for the neural arm. XGBoost
mean-absolute-error standard deviations over five seeds ranged from 0.0000 to
0.2349 depending on the setting, whereas the attention-based LSTM reached 2.9504
on BDG2 at six hours over three seeds — an instability that itself argues against
adopting the neural arm in this application.

**Figure 4.1** — *Mean absolute error by point-forecasting model, dataset and
horizon.*
File: `outputs/full_study/report/figures/fig_01_point_forecasting_comparison.png`
Insertion point: immediately after Table 4.2, at the start of Section 4.2.4.

*Interpretation.* The figure makes the central point-forecasting finding visible
at a glance: no arm is uniformly lowest. The PLEIA temperature panel shows
persistence beneath every learned model at all three horizons, while the RICO and
BDG2 panels show the learned models descending below persistence as the horizon
grows. Reading the panels together, the visual signature of the study is a
crossing pattern rather than a consistent ranking, which is the graphical
counterpart of the claim that model value is target- and horizon-dependent. The
figure should be read alongside Section 4.6.2, because the visible separations
are not all statistically supported at the block level.

**Takeaway.** No point-forecasting arm was best everywhere. XGBoost won nine of
thirteen cells and gained with horizon; naive persistence won the remaining four
and was never beaten on slow indoor temperature. The correct conclusion is that
the point forecaster must be selected per target and horizon regime, and that
mandatory naive baselines are what make this visible.

---

## 4.3 Prediction Interval Results and Discussion

This section evaluates whether conformal calibration delivered its nominal
coverage, and at what cost in interval width. Five interval methods were
compared: an uncalibrated quantile band, conformalized quantile regression (CQR),
a recentred adaptation of EnbPI in static and sequentially updated forms, and
dual-splitting conformal prediction (DSCP). The uncalibrated band was retained
throughout as the reference against which the contribution of calibration is
measured rather than assumed. Table 4.3 reports performance at the 95 % nominal
level, averaged across horizons.

**Table 4.3 — Prediction interval results at nominal 95 %**

| Setting | Method | Coverage | Coverage deviation | Mean width | Winkler score |
|---|---|---|---|---|---|
| PLEIA temp | **cqr** | 0.9417 | **0.0083** | 2.5104 | **3.7967** |
| PLEIA temp | dscp | 0.9527 | 0.0135 | 2.8461 | 4.1529 |
| PLEIA temp | recentred_enbpi_updated | 0.9313 | 0.0187 | 2.7137 | 4.2553 |
| PLEIA temp | recentred_enbpi_static | 0.8902 | 0.0598 | 2.2644 | 4.5361 |
| PLEIA temp | quantile_uncalibrated | 0.8795 | 0.0705 | 1.9717 | 4.2150 |
| PLEIA energy | **recentred_enbpi_updated** | 0.9511 | **0.0027** | 0.8907 | 2.2778 |
| PLEIA energy | cqr | 0.9664 | 0.0164 | 0.4363 | **1.6582** |
| PLEIA energy | dscp | 0.9840 | 0.0340 | 0.9029 | 2.0311 |
| PLEIA energy | recentred_enbpi_static | 0.9853 | 0.0353 | 1.4036 | 2.5462 |
| PLEIA energy | quantile_uncalibrated | 0.8484 | 0.1016 | 0.2978 | 1.7070 |
| RICO | **recentred_enbpi_updated** | 0.9036 | **0.0464** | 1.7076 | 3.3217 |
| RICO | dscp | 0.8972 | 0.0528 | 1.7902 | 3.3731 |
| RICO | recentred_enbpi_static | 0.8722 | 0.0778 | 1.4266 | 4.3177 |
| RICO | cqr | 0.7719 | 0.1781 | 2.4983 | 11.2602 |
| RICO | quantile_uncalibrated | 0.6304 | 0.3196 | 1.8094 | 12.6819 |
| BDG2 | **recentred_enbpi_updated** | 0.9503 | **0.0008** | 203.5668 | 332.9632 |
| BDG2 | cqr | 0.9476 | 0.0033 | 138.8535 | 200.2521 |
| BDG2 | recentred_enbpi_static | 0.9419 | 0.0081 | 187.2787 | 329.7039 |
| BDG2 | dscp | 0.9274 | 0.0226 | 147.0737 | 287.4609 |
| BDG2 | quantile_uncalibrated | 0.8390 | 0.1110 | 127.0172 | 200.2032 |

*Coverage and width are averaged over the horizons of each setting. Widths are in
target units and are not comparable across settings. Best coverage deviation per
setting in bold; best Winkler score also in bold where it differs. Source:
`combined/interval_metrics.csv`. Results at the 90 % nominal level appear in
Appendix B.*

### 4.3.1 Effect of Conformal Calibration

The uncalibrated quantile band failed to deliver its nominal coverage in every
one of the four settings, undercovering by 0.0705 on PLEIA temperature, 0.1016 on
PLEIA energy, 0.1110 on BDG2 and 0.3196 on RICO. The same ordering held at the
90 % level, where the deviations were 0.0963, 0.1254, 0.0882 and 0.3357
respectively. Conformal calibration reduced the coverage deviation in every
setting, in the strongest case from 0.3196 to 0.0464 on RICO.

This is the most robust interval finding of the study, and it is the quantitative
justification for the framework's central design decision. A quantile regressor
trained by pinball loss produces bands whose nominal level is a property of the
loss function, not of the realised data; the conformal step replaces that
assumption with a finite-sample guarantee calibrated on held-out residuals. The
measured gap between the two — up to 0.32 in coverage — is the practical size of
that distinction on real building data.

One caution attaches to this section. On BDG2 the uncalibrated band achieved the
*lowest* Winkler score of any method, 200.2032 against CQR's 200.2521. This must
not be read as evidence in its favour. The Winkler score prices both width and
miss penalty, and the uncalibrated band is narrow enough — mean width 127.02
against CQR's 138.85 — that the width saving very nearly offsets its penalty for
missing nominal coverage by 0.111. The two scores differ by 0.02 %, which is
within any reasonable notion of a tie. The lesson is methodological rather than
substantive: coverage deviation and Winkler score answer different questions and
must be reported together, since either alone can rank an undercovering method
first.

### 4.3.2 Comparison of CQR, Recentred EnbPI and DSCP

No conformal method transferred across all four settings. The best-calibrated arm
was CQR on PLEIA temperature (0.9417) and the sequentially updated recentred
EnbPI on PLEIA energy (0.9511), RICO (0.9036) and BDG2 (0.9503). Ranking by
Winkler score gave a different answer again, favouring CQR on PLEIA temperature,
PLEIA energy and BDG2, and the updated EnbPI on RICO.

The most consequential single result concerns CQR on RICO. Averaged over
horizons, CQR attained 0.7719 coverage against a nominal 0.95, and its Winkler
score of 11.2602 was more than three times that of the updated EnbPI. Per horizon
the coverage was 0.7805, 0.8024, 0.7521 and 0.7526, so the shortfall was
consistent rather than confined to a single lead time. The correct statement,
which should be used verbatim in the dissertation, is that **CQR substantially
undercovered on RICO under the evaluated protocol.**

An associated diagnostic was quantified. Across both nominal levels and all four
horizons, 3,912 of 66,696 RICO CQR intervals — 5.87 % — had a lower bound above
their upper bound before repair; the figure of 2,558 that appears elsewhere is the
subtotal at the 95 % level alone. Crossing was roughly twice as frequent at the
95 % level (7.67 %) as at the 90 % level (4.06 %), and it was strongly
concentrated, touching 16 of the 42 test runs, with almost every interval crossing
in the worst-affected runs. Median crossing magnitudes ranged from 0.21 to
1.35 °C, comparable to the interval widths themselves. The repair applied was
order-restoring only, taking the minimum and maximum of the pair; it raised
coverage by between 0.000 and 0.039 per cell and never to nominal, so the
conclusion does not depend on it.

Two explanations may be offered, and both must be labelled as hypotheses that
this experiment did not test. The first is that RICO's calibration and test
partitions comprise disjoint sets of four-hour runs following different set-point
programmes, so calibration and test residuals may not be exchangeable. The second
is that independently fitted conditional quantiles are more prone to crossing
where the conditional distribution shifts sharply between operating regimes; the
concentration of crossings within a minority of runs is consistent with this, but
consistency is not evidence of cause. Establishing the first would require a
designed exchangeability test across run partitions and the second a per-regime
refit. **This study does not claim that RICO's run structure caused CQR to
fail.**

DSCP behaved as its design would suggest. It was the second-best-calibrated arm
on RICO at 0.8972 with a mean width 28 % narrower than CQR's, and its per-horizon
coverage was remarkably stable at 0.9006, 0.8898, 0.8995 and 0.8987 — the only
method whose RICO coverage did not degrade with horizon. On the smoother PLEIA
targets it over-covered, reaching 0.9527 on temperature and 0.9840 on energy,
paying for that conservatism in width and Winkler score. A methodological
qualification applies: the multi-step vector supplied to DSCP was assembled
across direct per-horizon models rather than produced by a single multi-output
model, which is a documented deviation from the published procedure.

*Sources: `combined/interval_metrics.csv`,
`combined/rico_quantile_crossings.csv`,
`combined/rico_quantile_crossings_by_run.csv`,
`report/rico_quantile_crossing_audit.md`, `<dataset>/models/dscp_level95.json`.*

### 4.3.3 Dataset- and Horizon-Specific Interval Behaviour

Coverage deviation varied systematically with horizon in a manner that differed
by method. On RICO, the static recentred EnbPI degraded from 0.9293 coverage at
five minutes to 0.7894 at sixty minutes, whereas its sequentially updated
counterpart degraded far more slowly, from 0.9272 to 0.8719, and DSCP was
essentially flat. The online update is therefore doing measurable work as the
prediction problem becomes harder, which is the behaviour the adaptation was
introduced to obtain.

On PLEIA temperature the interval methods were comparatively stable across
horizons, CQR ranging from 0.9373 to 0.9481 with mean widths growing from 1.65 to
3.31 °C as the horizon lengthened. Interval width grew with horizon in every
setting, which is the expected consequence of a genuinely harder forecasting
problem being reflected honestly in the uncertainty estimate rather than
suppressed.

The single most important negative result of the interval analysis is that **on
RICO no method reached nominal coverage.** The best coverage attained in any
individual method-and-horizon cell was 0.9293, and the best method averaged over
horizons reached 0.9036, both against a nominal 0.95. RICO must therefore be
reported as an unsolved setting for this framework.

**Figure 4.2** — *Empirical coverage against mean interval width, by conformal
method and dataset (dashed line at nominal coverage).*
File: `outputs/full_study/report/figures/fig_02_coverage_vs_width.png`
Insertion point: immediately after Table 4.3, at the start of Section 4.3.1.

*Interpretation.* This figure presents the calibration–width trade-off that
governs the whole interval analysis. The uncalibrated quantile band occupies the
lower-left region in every panel — narrow, and below nominal coverage — while the
conformal methods sit higher and to the right, having purchased coverage with
width. The figure also makes the RICO anomaly visible: that panel's points sit
markedly below the nominal line regardless of width, showing that the shortfall
there is not simply a matter of intervals being too narrow. Readers should be
directed to the fact that a point near the nominal line at small width is the
desirable region, and that no method occupies it on RICO.

**Figure 4.3** — *Coverage deviation by forecast horizon and conformal method.*
File: `outputs/full_study/report/figures/fig_03_coverage_deviation_by_horizon.png`
Insertion point: within Section 4.3.3, after the first paragraph.

*Interpretation.* The figure isolates how calibration quality changes as the
forecast reaches further ahead. On RICO the deviation of the static recentred
EnbPI grows steeply with horizon while the sequentially updated variant and DSCP
remain comparatively flat, which is the visual evidence for the claim that online
updating and the dual-splitting construction confer horizon robustness that a
static split-conformal calibration does not. On the PLEIAData and BDG2 panels the
curves are flatter for all methods, indicating that horizon growth alone does not
degrade calibration where the underlying signal is well behaved.

**Takeaway.** Conformal calibration was necessary on all four settings and was
never sufficient on RICO. No single conformal method transferred, the best arm
differing by setting, and coverage deviation and Winkler score must be reported
jointly because they can disagree.

---

## 4.4 Interval-Based Alert Results and Discussion

This section evaluates whether calibrated intervals can support a practical
alerting scheme. Alerts were raised by a *k*-of-*m* persistence rule over interval
violations, and the operating rule was frozen before any test observation was
examined. Because building datasets of this kind carry no labelled sensor faults,
disturbances were injected from a controlled catalogue of seven event types, and
the resulting precision and recall must be read as sensitivity to controlled
disturbances rather than as real fault-detection performance.

### 4.4.1 Nested Alert-Rule Selection

An earlier formulation of the protocol scored candidate rules using calibration
intervals produced by the model conformalized on that same calibration partition.
This was found to be methodologically unsound: the conformal quantile is fitted to
cover precisely those residuals, so their violation rate is not an out-of-sample
quantity, and any rule chosen against it inherits that optimism.

The procedure was therefore replaced by a nested chronological split *inside* the
original calibration period. The earlier 60 % of the calibration partition
conformalized a separate selection model, and the later 40 % was used to score the
candidate rules. A window entered the later block only when its forecast origin
was strictly later than the last target time of the earlier block, so every
rule-tuning timestamp postdated every conformal-calibration timestamp; windows
straddling the boundary were discarded, giving an exact rather than approximate
embargo. The test partition was untouched throughout, and the final reported test
intervals continued to be produced by the model conformalized on the complete
calibration partition, which is fixed before any test observation is seen.

The consequences were material and are reported in the upper half of Table 4.4.
On PLEIA temperature the pooled procedure had reported a point-level false alarm
rate of 0.0131 for the 3-of-5 rule, whereas the leakage-safe surface reported
0.0508 for the same rule — an understatement of roughly fourfold. Under the
corrected surface, 3-of-5 exceeded the stated budget of one false alert per day
at 1.6384, and 4-of-7 was selected instead at 0.8904. Two of the four frozen
rules changed as a result: PLEIA temperature moved from 3-of-5 to **4-of-7** and
RICO from 4-of-7 to **2-of-3**. PLEIA energy remained at **2-of-3** and BDG2 at
**1-of-1**.

The direction of the optimism was not uniform. On RICO the pooled surface had been
*pessimistic* rather than optimistic, reporting 20.02 false alerts per day for the
1-of-1 rule against 4.38 under the nested split. The explanation is that the two
calibration blocks cover different time periods with different dynamics, so the
reuse effect is confounded with genuine non-stationarity. This should be reported
as a limitation of the diagnosis rather than smoothed over.

**Table 4.4 — Nested alert selection and final alert performance**

*(a) Nested calibration split*

| Setting | Conformal block | Rule block | Embargoed | Boundary |
|---|---|---|---|---|
| PLEIA temp | 6,065 | 4,043 | 1 | 2021-09-10 17:10 |
| PLEIA energy | 6,065 | 4,043 | 1 | 2021-09-10 17:20 |
| RICO | 5,437 | 3,619 | 5 | 2024-05-08 13:32 |
| BDG2 | 20,999 | 13,978 | 10 | 2017-06-10 12:00 |

*(b) Frozen operating rule, evaluated on the test partition*

| Setting | Frozen rule | Precision | Recall | F1 | FAR | False alerts/day | Median delay (min) |
|---|---|---|---|---|---|---|---|
| PLEIA temp | **4-of-7** | 0.5763 | 0.8095 | 0.6733 | 0.0132 | 0.3562 | 30.0 |
| PLEIA energy | **2-of-3** | 0.4384 | 0.7619 | 0.5565 | 0.0102 | 0.5841 | 10.0 |
| RICO | **2-of-3** | 0.3125 | 0.8750 | 0.4605 | 0.2077 | 11.9457 | 1.0 |
| BDG2 | **1-of-1** | 0.0252 | 0.8810 | 0.0490 | 0.0575 | 0.9858 | 0.0 |

*Sources: `<dataset>/metrics/alert_selection_split.csv`,
`combined/alert_metrics.csv` (`role = post_hoc_sensitivity`),
`report/alert_selection_audit.md`.*

### 4.4.2 Test-Set Alert Reliability

The frozen rules differed on all four settings, and their test performance spanned
more than an order of magnitude in F1, from 0.0490 on BDG2 to 0.6733 on PLEIA
temperature. Recall was comparatively stable across settings, ranging from 0.7619
to 0.8810; precision was what varied, from 0.0252 to 0.5763. Detection delay
tracked the persistence requirement of the chosen rule almost mechanically: the
1-of-1 rule detected immediately, 2-of-3 within one to ten minutes, and 4-of-7
after thirty minutes.

Two findings from this section are uncomfortable and are reported as measured.

First, on RICO no candidate rule met the stated budget of one false alert per day.
The selection procedure therefore fell back to its documented rule of taking the
quietest candidate, and that candidate still produced 11.9457 false alerts per day
on the test partition. The interval violation rate on clean RICO test data is
itself 0.22, which follows directly from the undercoverage reported in
Section 4.3, so the alerting layer inherits a problem created upstream. Alerting
on RICO was not achievable at a practical workload under this configuration.

Second, the leakage-safe procedure did not uniformly improve test performance. On
PLEIA temperature the newly selected 4-of-7 rule was better on test than the
superseded 3-of-5 rule (F1 0.6733 against 0.4892, precision 0.5763 against 0.3505,
false alerts per day 0.3562 against 0.8975, at identical recall). On RICO it was
worse: the newly selected 2-of-3 achieved F1 0.4605 against 0.5344 for the
superseded 4-of-7, with false alerts rising from 8.6878 to 11.9457 per day. This
is the expected behaviour of an honest selection procedure, which optimises the
quantity it may legitimately observe rather than the test score. The contribution
claimed is improved *validity* of selection, not improved performance.

A related observation reinforces the point. On three of the four settings the
frozen rule was not the rule that would have scored best on test. On PLEIA energy
the frozen 2-of-3 rule achieved F1 0.5565 while 3-of-5 and 4-of-7 would have
achieved 0.7126 and 0.7317; on BDG2 the frozen 1-of-1 achieved 0.0490 while 4-of-7
would have achieved 0.4000. The reason is the stated selection criterion, which
maximises event recall subject to a false-alert budget and therefore prefers the
most sensitive rule the budget permits. A precision-weighted criterion would have
selected differently. The criterion was fixed in advance and applied consistently;
that it does not maximise test F1 is a property of honest selection, but it also
indicates that the criterion itself deserves reconsideration in future work.

### 4.4.3 Precision–Recall–False-Alert Trade-offs

Increasing the persistence requirement *k* traded recall for precision
monotonically wherever the budget was attainable. On PLEIA temperature, moving
from 1-of-1 to 4-of-7 raised test precision from 0.0965 to 0.5763 while recall
fell only from 0.9286 to 0.8095, and the false-alert workload fell from 5.1998 to
0.3562 per day. On BDG2 the same progression raised precision from 0.0252 to
0.2683 and reduced the workload from 0.9858 to 0.0620 per day, at a recall cost of
0.0953. The trade is therefore highly favourable on these settings: substantial
precision and workload gains for modest recall loss.

RICO was the exception. Across all four rules the point-level false alarm rate
remained essentially constant at 0.2050 to 0.2077, and the workload fell only from
18.6167 to 8.6878 alerts per day. Because the underlying intervals undercover, a
large fraction of clean observations fall outside them, and no amount of temporal
aggregation can remove a violation signal that is present at nearly every step.

The two false-alarm measures reported throughout were kept distinct and must
remain so in the dissertation. The point-level false alarm rate is a rate per
opportunity, computed over timesteps outside any event window; false alerts per
day counts contiguous alert clusters and expresses an operator workload. They
answer different questions, and conflating them under the name "false alarm rate"
would misreport both.

**Figure 4.4** — *Precision, recall and F1 across candidate k-of-m alert rules,
by dataset.*
File: `outputs/full_study/report/figures/fig_05_alert_rule_sensitivity.png`
Insertion point: at the start of Section 4.4.3.

*Interpretation.* The figure shows the monotone precision–recall exchange that
governs operating-point selection. On the PLEIAData and BDG2 panels precision
rises steeply with *k* while recall declines gently, which is why longer
persistence requirements are attractive where the false-alert budget permits them.
The RICO panel is visibly flatter, and this flatness is the graphical statement of
the section's central negative finding: where the intervals themselves undercover,
temporal aggregation cannot recover a usable operating point.

**Figure 4.5** — *Event recall against false-alert workload per day, with the
stated budget marked.*
File: `outputs/full_study/report/figures/fig_06_alert_tradeoff.png`
Insertion point: immediately following Figure 4.4.

*Interpretation.* This figure presents the selection problem as an operator would
face it, plotting what is gained in detection against what is paid in daily
nuisance alerts. Three settings show candidates lying to the left of the budget
line, so a rule could be chosen within the workload constraint; RICO shows every
candidate far to its right, which is the direct visual evidence that the budget
was unattainable there and that the quietest-candidate fallback was invoked. The
figure should be captioned to note that the selected point on each curve was fixed
using calibration data alone.

**Takeaway.** Interval-based alerting was workable, but its operating point had to
be tuned per setting on data the conformal quantile had not seen, and correcting
the selection procedure for reuse changed two of four rules while improving test
performance on only one of them. On RICO, upstream undercoverage made a practical
alerting workload unattainable.

---

## 4.5 Robustness and Recalibration Results and Discussion

This section examines whether the calibrated intervals and the alerting layer
remained trustworthy under realistic data disturbance and drift. Fifteen
disturbance scenarios were evaluated under two distinct evaluation modes, together
with three levels of calibration contamination and three recalibration strategies.

Before any result is quoted, the terminology must be fixed, because two different
quantities in this study are both called *coverage* and a disturbance experiment
moves them in opposite directions.

| Term | Persisted column | Meaning |
|---|---|---|
| **observed-signal coverage** | `empirical_coverage` | the interval contains the reading the monitor actually received |
| **clean-reference coverage** | `empirical_coverage_vs_clean_truth` | the interval contains the value the sensor should have reported |
| **clean-reference MAE** | `mae_vs_clean_truth` | forecast error measured against physical reality |

*Source: `combined/robustness_metric_schema.csv`,
`report/closed_loop_terminology.md`.*

The two evaluation modes must likewise be distinguished. Under
`legacy_fixed_intervals`, the conventional protocol, the perturbation was applied
to the evaluation signal only; the model never ingested it, so clean-reference
metrics are constant across severities **by construction** and only
observed-signal metrics move. Under `closed_loop`, the perturbation entered the
feature history, so the next forecast was computed from corrupted lags and both
families of metric respond.

### 4.5.1 Missingness and Communication Disturbances

Random missingness, block missingness, dropout and stuck-sensor conditions were
evaluated at severities up to 20 %. These disturbances proved comparatively benign.

Under random missingness in closed loop, PLEIA temperature observed-signal
coverage moved only from 0.9373 undisturbed to 0.9396 at 20 % missingness, and
clean-reference MAE from 0.3142 to 0.3093 °C. PLEIA energy was similarly
insensitive, and RICO's coverage remained at 0.7811 against its undisturbed
0.7805. BDG2 showed the clearest effect under the fixed-interval protocol, where
observed-signal coverage fell from 0.9427 to 0.7811 as missingness rose to 20 %,
yet in closed loop it held at 0.9477 because the imputation used to rebuild the
feature matrix restored a plausible input.

Block missingness, dropout and stuck-sensor conditions behaved similarly. The
largest single effect was on BDG2 under a stuck sensor in closed loop, where
clean-reference MAE rose from 20.0111 to 24.3114 kWh — a 21 % degradation — while
observed-signal coverage actually improved to 0.9449, because a frozen reading is
trivially easy to bracket. PLEIA temperature under dropout showed the same
pattern: observed-signal coverage rose to 0.9464 while clean-reference coverage
fell to 0.9042 and clean-reference MAE rose from 0.3142 to 0.4318 °C.

The interpretation is that gap-filling and short communication outages are handled
adequately by the pipeline's missing-data machinery, and that they are the least
threatening of the disturbances studied. The recurring pattern in which
observed-signal coverage *improves* while clean-reference error worsens is the
first appearance of the effect analysed in Section 4.5.3.

### 4.5.2 Sensor Bias, Level Shift and Drift

Sustained magnitude disturbances were far more damaging than missingness, and
their reported severity depends entirely on which evaluation mode is used.

Under the conventional fixed-interval protocol, every sustained disturbance was
loud. At a 2 σ sensor bias, observed-signal coverage collapsed to 0.0000 on PLEIA
temperature and RICO, 0.0013 on BDG2 and 0.0749 on PLEIA energy, with alert rates
between 0.9279 and 0.9999. Gradual drift produced a similar picture, with
observed-signal coverage falling to 0.0961 on PLEIA temperature and 0.1310 on RICO
at 2 σ terminal drift. Level shifts of 1 σ and 2 σ reduced observed-signal
coverage to between 0.4249 and 0.7055 depending on the setting. Throughout these
rows the clean-reference metrics were flat — PLEIA temperature clean-reference
coverage remained at 0.9373 and clean-reference MAE at 0.3142 °C at every severity
— which is a property of the protocol and not evidence of robustness.

Table 4.5 presents the key rows, with the fixed-interval and closed-loop readings
placed side by side.

**Table 4.5 — Key robustness results (2 σ sensor bias and 10 % calibration
contamination)**

*(a) 2 σ sensor bias, both evaluation modes*

| Setting | Mode | Observed-signal coverage | Clean-reference coverage | Clean-reference MAE | Alert rate |
|---|---|---|---|---|---|
| PLEIA temp | legacy_fixed_intervals | 0.0000 | 0.9373 | 0.3142 | 0.9997 |
| PLEIA temp | closed_loop | 0.2580 | 0.0006 | 7.3606 | 0.7315 |
| PLEIA energy | legacy_fixed_intervals | 0.0749 | 0.9731 | 0.0933 | 0.9279 |
| PLEIA energy | closed_loop | 0.9763 | 0.1804 | 0.6216 | 0.0058 |
| RICO | legacy_fixed_intervals | 0.0000 | 0.7805 | 0.1113 | 0.9999 |
| RICO | closed_loop | 0.5025 | 0.0001 | 10.5115 | 0.4972 |
| BDG2 | legacy_fixed_intervals | 0.0013 | 0.9427 | 20.0111 | 0.9987 |
| BDG2 | closed_loop | 0.8876 | 0.0529 | 472.0058 | 0.1124 |

*(b) Calibration contamination, evaluated on clean test data*

| Setting | Contamination | Coverage | Mean interval width |
|---|---|---|---|
| PLEIA temp | 1 % | 0.9449 | 1.8526 |
| PLEIA temp | 5 % | 0.9970 | 14.4692 |
| PLEIA temp | 10 % | 1.0000 | 26.8179 |
| RICO | 10 % | 1.0000 | 34.0274 |
| BDG2 | 10 % | 0.9999 | 1,468.7591 |
| PLEIA energy | 10 % | 0.9968 | 2.0444 |

*Undisturbed reference values: PLEIA temperature clean-reference MAE 0.3142 °C;
PLEIA energy 0.0933 kWh; RICO 0.1113 °C; BDG2 20.0111 kWh. Source:
`combined/robustness_metrics.csv`.*

Calibration contamination proved the most damaging disturbance studied, and its
effect was monotone in every setting. On PLEIA temperature the mean interval width
rose from 1.8526 at 1 % contamination to 14.4692 at 5 % and 26.8179 at 10 %, while
coverage rose to 1.0000. On BDG2 the width reached 1,468.7591 kWh. The essential
point for interpretation is that coverage saturating at unity is a *failure* mode,
not a success: the intervals have become so wide that they are uninformative, and
an operator receiving them learns nothing. Contaminated calibration data therefore
destroys the utility of a conformal monitor while leaving its nominal guarantee
formally intact — an outcome that no coverage-only evaluation would detect.

### 4.5.3 Closed-Loop Fault-Absorption Analysis

The closed-loop analysis produced the study's most consequential result for
practice, and it inverts the reading obtained from the conventional protocol.

When the perturbation entered the feature history, the autoregressive forecaster
began to track the corrupted signal. Because the forecast moved with the fault,
the interval continued to contain the reading the monitor received, and the alert
rate fell. Meanwhile the forecast diverged sharply from physical reality. At a
2 σ bias, observed-signal coverage in closed loop remained at 0.9763 on PLEIA
energy and 0.8876 on BDG2 — at or near their undisturbed values of 0.9731 and
0.9427 — while clean-reference coverage fell to 0.1804 and 0.0529 and
clean-reference MAE rose from 0.0933 to 0.6216 kWh and from 20.0111 to
472.0058 kWh respectively. The alert rate fell on every setting, most sharply on
BDG2 from 0.9987 under the fixed-interval protocol to 0.1124 in closed loop.

The magnitude of the divergence between reality and the monitor's view can be
summarised by the growth in clean-reference MAE at 2 σ bias: a factor of
approximately 6.7 on PLEIA energy, 23.4 on PLEIA temperature, 23.6 on BDG2 and
94.4 on RICO. The same effect appeared under level shift and drift. Under 2 σ
terminal drift in closed loop, BDG2 observed-signal coverage was 0.9483 while
clean-reference coverage was 0.1631, and PLEIA energy showed 0.9793 against 0.4034.

Because the disturbance was experimentally manipulated rather than merely
observed, a causal statement is warranted here, and this is the one place in the
dissertation where causal language is earned: injecting a sustained sensor bias
into the feature history caused the forecast to diverge from the clean reference
while leaving observed-signal coverage high.

That said, **fault absorption did not occur identically on every setting, and must
not be described as though it did.** The effect was near-complete on PLEIA energy
and BDG2, partial on RICO where observed-signal coverage still fell to 0.5025, and
weakest on PLEIA temperature where observed-signal coverage fell to 0.2580 and the
alert rate remained at 0.7315. On that setting a 2 σ bias therefore stayed largely
visible to the monitor even in closed loop. The gradient itself is informative:
absorption was strongest where the target has the least short-term
autocorrelation for the model to contradict.

The practical implication is direct. A monitoring system evaluated only under the
conventional fixed-interval protocol will appear highly sensitive to sensor faults
and will, on three of four settings here, be substantially less sensitive in
deployment. Closed-loop evaluation should be regarded as the default for
autoregressive monitors, and clean-reference metrics should be reported alongside
observed-signal metrics as a matter of routine.

**Figure 4.6** — *Coverage under every disturbance scenario, shown separately for
observed-signal and clean-reference references, in both evaluation modes.*
File: `outputs/full_study/report/figures/fig_07_robustness_degradation.png`
Insertion point: at the start of Section 4.5.2, before Table 4.5.

*Interpretation.* The figure's two columns carry the section's central
methodological message. In the left column, observed-signal coverage collapses
under the fixed-interval protocol and is largely preserved in closed loop; in the
right column, clean-reference coverage does the opposite, remaining flat under the
fixed-interval protocol and collapsing in closed loop. Presented on a single axis
without these labels, the same data would support opposite conclusions, which is
precisely why the two quantities are plotted separately throughout this
dissertation.

**Figure 4.7** — *Sensor-bias sweep: observed-signal and clean-reference coverage
with clean-reference MAE, by dataset and evaluation mode.*
File: `outputs/full_study/report/figures/fig_13_closed_loop_absorption.png`
Insertion point: within Section 4.5.3, immediately after the second paragraph.

*Interpretation.* This is the single most important figure in the chapter. Reading
across the severity axis, the closed-loop observed-signal curve stays high while
the closed-loop clean-reference curve falls toward zero and the clean-reference
error rises steeply, so the divergence between what the monitor sees and what is
physically true is legible in one image. The per-dataset panels also make the
gradient explicit: the gap between the two coverage curves is widest on PLEIA
energy and BDG2 and narrowest on PLEIA temperature, which is the graphical basis
for the qualification that absorption is not uniform.

### 4.5.4 Static, Periodic and Rolling Recalibration

Three recalibration strategies were compared: static calibration, periodic
recalibration at a fixed update interval, and rolling recalibration over a bounded
residual window. Update intervals and window lengths were chosen by a replay
within the calibration partition, separated by a horizon-length embargo, so that
no test observation influenced the configuration.

**Table 4.6 — Recalibration comparison**

| Setting | Strategy | Update every | Window | Updates | Coverage | Coverage deviation | Winkler | Distinct strategy |
|---|---|---|---|---|---|---|---|---|
| PLEIA temp | static | 24 | 1000 | 0 | 0.9324 | 0.0176 | 2.8942 | yes |
| PLEIA temp | periodic | 24 | 1000 | 422 | 0.9390 | 0.0110 | 2.8773 | yes |
| PLEIA temp | **rolling** | 24 | 1000 | 422 | 0.9480 | **0.0020** | 2.8687 | yes |
| PLEIA energy | static | 144 | 1000 | 0 | 0.9810 | 0.0310 | 2.0993 | yes |
| PLEIA energy | periodic | 144 | 1000 | 71 | 0.9724 | 0.0224 | 2.0596 | yes |
| PLEIA energy | **rolling** | 144 | 1000 | 71 | 0.9293 | **0.0207** | 1.8660 | yes |
| RICO | static | 15 | 500 | 0 | 0.9051 | 0.0449 | 0.9248 | yes |
| RICO | **periodic** | 15 | 500 | 619 | 0.9256 | **0.0244** | 0.8547 | yes |
| RICO | rolling | 15 | 500 | 619 | 0.9119 | 0.0381 | 0.8301 | yes |
| BDG2 | static | 24 | — | 0 | 0.8432 | 0.1068 | 202.3312 | yes |
| BDG2 | **periodic** | 24 | — | 1460 | 0.8592 | **0.0908** | 194.0248 | yes |
| BDG2 | rolling | 24 | — | 1460 | 0.8592 | 0.0908 | 194.0248 | **no** |

*Residual delay was one step for the PLEIAData and BDG2 settings and five steps
for RICO. Source: `combined/recalibration_metrics.csv`,
`<dataset>/metrics/recalibration_selection.csv`.*

Adaptive recalibration reduced coverage deviation relative to static calibration
in all four settings. The largest improvement was on PLEIA temperature, where
rolling recalibration reduced the deviation from 0.0176 to 0.0020, effectively
achieving nominal coverage. The best strategy differed by setting: rolling on both
PLEIAData targets and periodic on RICO and BDG2. No strategy was universally best.

Two qualifications must accompany this table. First, recalibration did not rescue
BDG2. Coverage improved only from 0.8432 to 0.8592 against a nominal 0.95, leaving
that setting materially undercovered even after adaptation. Second, and
importantly for correct reporting, **BDG2 has no distinct rolling-window result.**
The calibration replay selected an unwindowed configuration for that setting, so
the rolling strategy reduced to the same unbounded update procedure as periodic
and reproduced it exactly. This degeneracy is recorded in the persisted data as
`strategy_is_distinct = False`, and the two rows must not be presented as
independent strategies. No alternative rolling window was manufactured in order to
obtain a different number.

**Figure 4.8** — *Rolling coverage in blocks either side of a disturbance onset,
by recalibration strategy.*
File: `outputs/full_study/report/figures/fig_08_recalibration_recovery.png`
Insertion point: at the end of Section 4.5.4, after Table 4.6.

*Interpretation.* The figure shows how quickly each strategy restores nominal
coverage after a disturbance. The static curve remains depressed for the remainder
of the evaluation window because its conformal quantile is fixed, whereas the
periodic and rolling curves recover as successive updates incorporate the new
residual regime. The figure motivates adaptive recalibration operationally rather
than merely statistically: the relevant quantity for an operator is not only the
average coverage over a period but how long the monitor remains mis-calibrated
after conditions change.

**Takeaway.** Missingness and communication faults were handled adequately;
sustained magnitude faults were not. Under closed-loop evaluation the forecaster
absorbed a sustained bias on three of four settings, and calibration contamination
rendered intervals uninformative. Adaptive recalibration improved coverage
deviation everywhere but did not restore nominal coverage on BDG2.

---

## 4.6 Statistical and Comparative Analysis

This section reports the formal statistical analysis of the point-forecasting
results and then positions the study against internal and published benchmarks.
Its purpose is to establish which of the differences described in Section 4.2 are
supported by inference rather than by point estimates alone.

### 4.6.1 Bootstrap Confidence Intervals and Effect Sizes

Moving-block bootstrap confidence intervals were computed for every point-model
and horizon combination, with the block structure chosen to respect temporal
dependence. All 48 rows produced intervals that bracket their point estimates.

The intervals show that several differences visible in Table 4.2 are comfortably
separated while others are not. On RICO at five minutes, XGBoost achieved a mean
absolute error of 0.0933 with a 95 % interval of [0.0872, 0.0995] against
persistence's 0.1222 with [0.1076, 0.1385]; the intervals do not overlap. On BDG2
at one hour, persistence gave 18.9167 with [17.7854, 20.0762] against XGBoost's
21.3487 with [20.2122, 22.6021], again separated. By contrast, on PLEIA energy at
ten minutes XGBoost gave 0.0977 with [0.0675, 0.1534] against persistence's 0.1417
with [0.0858, 0.2440] — heavily overlapping intervals despite a nominal 31 %
improvement, which the artefact analysis of Section 4.2.1 explains.

Effect sizes spanned a wide range. The XGBoost-versus-persistence mean absolute
error improvement ranged from −69.19 % on PLEIA temperature at ten minutes to
+48.77 % on RICO at sixty minutes, a spread of well over one hundred percentage
points across the study.

### 4.6.2 Diebold–Mariano, Friedman and Holm Tests

Pairwise predictive accuracy was tested using the Diebold–Mariano statistic with
the Harvey–Leybourne–Newbold small-sample correction and a Newey–West variance
estimator, applied within each dataset-and-horizon cell and adjusted across the
family by the Holm step-down procedure. Cross-dataset ranking was tested by the
Friedman test on within-block ranks, followed by Holm-corrected Wilcoxon post-hoc
comparisons.

**Table 4.7 — Statistical-analysis summary**

| Test | Scope | Result |
|---|---|---|
| Friedman | 4 point models, 9 complete blocks (4 dropped: RICO has no seasonal naive) | χ² = 14.0667, p = 0.002816 |
| Mean ranks | across blocks | xgboost 1.5556 · persistence 2.2222 · attention_lstm 2.4444 · seasonal_naive 3.7778 |
| Wilcoxon post-hoc, Holm | seasonal_naive vs xgboost | p = 0.0234 — **significant** |
| Wilcoxon post-hoc, Holm | persistence vs xgboost | p = 1.0000 — not significant |
| Wilcoxon post-hoc, Holm | all other pairs | not significant at 5 % |
| Diebold–Mariano, Holm | 48 tests over 4 model pairs | 36 significant |
| Diebold–Mariano, Holm | xgboost vs persistence, 13 cells | 10 significant: XGBoost better in 6, **persistence better in 4**; 3 not significant |
| Bootstrap | 48 model-horizon rows | every confidence interval brackets its estimate |

*Sources: `combined/ranking_tests.csv`, `combined/posthoc_comparisons.csv`,
`combined/statistical_tests.csv`, `combined/bootstrap_metrics.csv`.*

The Friedman test rejected the hypothesis that the four point models perform
equally across blocks. However, after Holm correction only one pairwise comparison
survived at the block level: seasonal naive against XGBoost. **XGBoost was not
significantly better than persistence across blocks (p = 1.0000)**, despite
achieving the lowest error in nine of thirteen cells.

The per-cell Diebold–Mariano results tell a compatible but more precise story, and
the precision matters. Of the thirteen XGBoost-versus-persistence comparisons, ten
were significant after correction — but the better model was not always XGBoost.
XGBoost was significantly better in six cells (all four RICO horizons and BDG2 at
three and six hours), whereas **persistence was significantly better in four
cells** (all three PLEIA temperature horizons and BDG2 at one hour). The three
PLEIA energy cells were not significant after correction (Holm-adjusted p of
0.2072, 0.5591 and 0.4352), notwithstanding nominal improvements of 20–31 %,
because the loss differential on that target is dominated by the meter-stall
observation identified in Section 4.2.1.

These two analyses are not in conflict and must be presented together. The
block-level test asks whether one model dominates across heterogeneous targets,
and the answer is no. The per-cell test asks whether a model wins on a given
target and horizon, and the answer is frequently yes — but for both models,
depending on the cell. Reporting only the per-cell result would overstate
XGBoost's standing; reporting only the block-level result would understate the
real and substantial per-setting differences. Statistical significance and
practical improvement are therefore reported as separate quantities throughout
this dissertation.

### 4.6.3 Controlled Internal Benchmarking

The primary comparative evidence in this study is the controlled internal
benchmark. Four point forecasters, five prediction-interval methods, four
alert-aggregation rules and three recalibration strategies were implemented within
the same framework and evaluated on identical partitions with identical features,
seeds, horizons and metric definitions. Because the experimental setting was held
constant, differences between arms are attributable to the methods rather than to
the conditions of measurement, and this is the only comparison from which relative
performance conclusions are drawn.

The internal benchmark returned a consistent structural finding across all four
components: the winner was setting-dependent in every case. The best point
forecaster differed by target; the best-calibrated interval method differed by
setting; the frozen alert rule differed on all four settings; and the best
recalibration strategy differed. This convergent pattern is the empirical basis
for the framework definition given in Section 4.7.4.

### 4.6.4 Comparison with Published Literature

Twelve benchmark studies were reviewed and each was classified according to
whether a direct numerical comparison with the present results would be
legitimate. The criterion required simultaneous agreement on dataset, target
variable, forecast horizon, partitioning scheme and metric definition.

**None of the twelve studies satisfied all of these conditions.** Seven were
classified as partially comparable, contributing a method, a protocol convention
or a metric definition, and five as contextual only, contributing motivation,
dataset documentation or design rationale. The classification is recorded in full
in `combined/literature_benchmark_matrix.csv`.

Consequently, **this dissertation makes no claim of numerical superiority over any
published study.** Where prior work is cited alongside a result, it is cited as
the source of a method, as corroboration of a design decision, or as evidence that
a phenomenon has been observed elsewhere — never as a baseline that the present
results outperform. Reporting a lower error than a published figure obtained on
different buildings, at a different horizon and under a different partitioning
scheme would not constitute a finding.

The published work does, however, support the study methodologically. The EnbPI
arm implements the ensemble batch prediction interval construction of Xu and Xie
(2023) in a documented recentred adaptation; the DSCP arm reimplements the
dual-splitting procedure of Yu et al. (2025); the reporting convention of pairing
Winkler score with empirical coverage follows Sousa et al. (2024); the alerting
design follows the operating-point framing used by Nguyen et al. (2025) and Park
et al. (2025); the recalibration comparison is closest in design to Von
Krannichfeldt et al. (2026); and the dataset documentation of Ibarra et al. (2023)
and Thiry et al. (2025) supplies the provenance and quality flags on which the
target and subset selections depend.

**Takeaway.** The Friedman test rejected equality of the point models, but Holm
correction left only seasonal naive against XGBoost significant at the block
level, and per-cell testing showed persistence significantly better in four cells.
Comparative claims rest on the controlled internal benchmark; no published study
in the reviewed set met the conditions for direct numerical comparison.

---

## 4.7 Overall Findings

This section consolidates the findings against each research question and
objective, and states the final definition of the framework.

### 4.7.1 Findings for RQ1 and RO1

*RQ1 asked how accurately short-term building sensor and energy values can be
forecast, and whether learned models improve on naive baselines. RO1 required the
implementation and evaluation of short-term point forecasting across heterogeneous
building datasets against mandatory naive baselines.*

The objective was met. Four point-forecasting arms were implemented and evaluated
across 13 dataset-and-horizon cells drawn from four heterogeneous settings, with
naive baselines treated as compulsory, and the complete study executed with zero
failed stages.

The answer to the question is conditional rather than affirmative. Learned models
improved on naive baselines where the target carries exploitable structure or the
horizon is long: XGBoost won nine of thirteen cells, improving on persistence by up
to 48.77 % on RICO at sixty minutes and 47.99 % on BDG2 at six hours. They did not
improve where the target is thermally slow: persistence won all three PLEIA
temperature horizons and BDG2 at one hour, with XGBoost 69.19 % worse at the
shortest PLEIA horizon. The advantage was real in magnitude but not statistically
separable from persistence at the block level (Holm-adjusted p = 1.0000), while
per-cell testing showed persistence significantly better in four cells and XGBoost
in six.

The defensible conclusion is that short-term forecast accuracy in smart buildings
is governed more by the physical character of the target and the horizon regime
than by model sophistication, and that naive baselines must be evaluated as
first-class competitors rather than as formalities.

### 4.7.2 Findings for RQ2 and RO2

*RQ2 asked whether conformal prediction delivers calibrated intervals for building
time series and which conformal method is preferable. RO2 required the
implementation of CQR, recentred EnbPI and DSCP under one protocol, compared
against an uncalibrated quantile baseline.*

The objective was met: all four interval constructions plus the uncalibrated
baseline were implemented and evaluated at two nominal levels across all four
settings.

Conformal calibration is **necessary**. The uncalibrated quantile band undercovered
in every setting, by 0.0705 to 0.3196 at the 95 % level, and calibration reduced
that deviation in every case. Conformal calibration is **not sufficient**. On RICO
no method reached nominal coverage, the best individual cell attaining 0.9293 and
the best method averaged over horizons 0.9036 against a nominal 0.95.

No conformal method transferred. The best-calibrated arm was CQR on PLEIA
temperature and the sequentially updated recentred EnbPI on the other three
settings, while ranking by Winkler score produced a different ordering again.
Notably, CQR substantially undercovered on RICO under the evaluated protocol
(0.7719), with 3,912 of 66,696 intervals crossing before order-repair across both
nominal levels. No causal explanation for that failure is claimed.

The defensible conclusion is that conformal calibration should be regarded as a
required component of any interval-based building monitor, that the specific
conformal method must be selected per target, and that coverage deviation and
Winkler score must be reported jointly.

### 4.7.3 Findings for RQ3 and RO3

*RQ3 asked whether calibrated intervals can support practical alerting and whether
that alerting remains trustworthy under realistic disturbance and drift. RO3
required evaluation of interval-based alerting, its rule sensitivity, its
robustness to disturbance, and the effect of periodic and rolling recalibration.*

The objective was met across all four components.

Alerting is workable but must be tuned per setting: the frozen rules differed on
all four settings, with test F1 ranging from 0.0490 to 0.6733. Selecting the
operating point on data the conformal quantile had not seen was shown to matter,
correcting a roughly fourfold understatement of false-alert workload on PLEIA
temperature and changing two of four frozen rules — though it improved test
performance on only one of the two that changed. On RICO the false-alert budget was
unattainable by any candidate rule.

Alerting is **not uniformly trustworthy under disturbance**. Missingness and
communication faults were handled adequately, but under closed-loop evaluation a
sustained 2 σ sensor bias was substantially absorbed by the forecaster on three of
four settings, leaving observed-signal coverage at 0.9763 and 0.8876 on PLEIA
energy and BDG2 while clean-reference coverage fell to 0.1804 and 0.0529 and the
alert rate dropped. Absorption was not uniform: on PLEIA temperature the fault
remained partly visible, with observed-signal coverage 0.2580 and alert rate
0.7315. Calibration contamination at 10 % rendered intervals uninformative in
every setting, with coverage saturating at unity.

Adaptive recalibration reduced coverage deviation in all four settings, most
dramatically on PLEIA temperature (0.0176 to 0.0020), but did not restore nominal
coverage on BDG2 (0.8592 against 0.95), for which no distinct rolling-window result
was identified.

### 4.7.4 Final Definition of ConfoSense

**ConfoSense is a configurable uncertainty-aware monitoring framework for
smart-building sensor and energy data — a specified pipeline together with a
decision procedure for instantiating it on a given target. It is not a newly
invented forecasting algorithm, and it is not one universal model.**

The framework comprises six components: data preparation, with group-safe
supervised windowing, direct horizon-specific models and performance-blind target
selection; point forecasting from a declared candidate set in which naive
baselines are mandatory; conformal calibration from a declared candidate set,
always reported against an uncalibrated baseline; interval-based alerting with a
*k*-of-*m* operating point frozen on out-of-conformal-calibration data under a
stated false-alert budget; robustness evaluation in both fixed-interval and
closed-loop modes with observed-signal and clean-reference metrics reported
separately; and delay-aware recalibration whose parameters derive from an embargoed
calibration replay.

The evidence does not support a single universal configuration. Every configurable
component resolved differently across the four settings, as Table 4.8 records.

**Table 4.8 — Final cross-dataset ConfoSense configurations**

| Setting | Point forecaster | Conformal method (best calibrated) | Conformal method (best Winkler) | Alert rule | Recalibration |
|---|---|---|---|---|---|
| PLEIA temperature | persistence | cqr | cqr | 4-of-7 | rolling |
| PLEIA energy | xgboost | recentred_enbpi_updated | cqr | 2-of-3 | rolling |
| RICO HVAC | xgboost | recentred_enbpi_updated | recentred_enbpi_updated | 2-of-3 | periodic |
| BDG2 electricity | xgboost | recentred_enbpi_updated | quantile_uncalibrated † | 1-of-1 | periodic |

*† The uncalibrated baseline attains the lowest BDG2 Winkler score by a margin of
0.02 % while undercovering by 0.111; see Section 4.3.1. It is shown for
completeness and must not be read as a recommendation. Source:
`combined/confosense_configurations.csv`.*

A distinction essential to the integrity of this claim must be preserved in the
writing. Three components were **validated selections**, made without any sight of
test data: the XGBoost hyperparameters, chosen by time-series cross-validation on
the training partition; the alert operating rule, chosen on the later block of the
calibration partition; and the recalibration parameters, chosen by embargoed
calibration replay. Two components are **post-test comparative observations**: the
point-model family and the conformal method were compared on the test partition
and are reported as such. They are best-observed configurations, not selections the
framework made blind. A deployment would require a calibration-side
model-selection protocol, which this study did not pre-register; this is recorded
as a limitation in Section 4.8.1.

The contribution is likewise threefold and should be separated from the methods
adopted. Split conformal prediction, CQR, EnbPI, DSCP, gradient-boosted trees,
attention-based recurrent forecasting and the statistical apparatus were all
adopted from the existing literature. The contribution of this dissertation is,
first, methodological — a leakage-safe procedure for selecting an alerting
operating point by nested chronological splitting inside the calibration partition
with an exact embargo; second, experimental — a controlled cross-setting
comparison of four point forecasters, five interval methods, four alert rules,
three recalibration strategies and fifteen disturbance scenarios under two
evaluation modes, executed under identical conditions with full provenance; and
third, applied — a dual-mode robustness evaluation demonstrating that conventional
fixed-interval evaluation misstates the fault sensitivity of an interval-based
monitor.

Where no target-specific evidence is yet available, a defensible default is to fit
both persistence and gradient-boosted trees and retain the better on calibration
data, to use the sequentially updated recentred EnbPI as the conformal layer, to
begin operating-point tuning from a 2-of-3 or 3-of-5 rule, and to apply periodic
recalibration. Each is a default to be re-selected on the deployment target's own
calibration data, not a validated optimum.

**Takeaway.** All three objectives were met. The framework is configurable rather
than universal, its contribution lies in the integrated and leakage-controlled
procedure rather than in any single algorithm, and two of its principal findings
are negative.

---

## 4.8 Limitations and Future Work

### 4.8.1 Limitations

**Methodological.** All disturbance events were injected from a controlled
catalogue; no labelled real faults exist for these datasets, so alert precision
and recall measure sensitivity to controlled disturbances rather than real
fault-detection performance. The point-model family and the conformal method were
compared on the test partition, and the study did not pre-register a
calibration-side protocol for selecting them. DSCP assembled its multi-step vector
across direct per-horizon models rather than from a single multi-output model, a
documented deviation from the published procedure, and the EnbPI arm is a
documented recentred adaptation reported under that name throughout. CQR required
order-repair of crossed intervals on RICO. The frozen alert rule was selected
against a model conformalized on 60 % of the calibration partition while the
reported test intervals used the whole of it. The alert selection criterion
maximises recall subject to a workload budget and consequently did not choose the
test-optimal rule on three of four settings.

**Dataset.** PLEIAData contributed a single room in a single block, so no
cross-room generalisation is claimed. The PLEIAData energy target contains two
meter-stall catch-up artefacts, one in the calibration partition and one in the
test partition, and its RMSE is not interpretable without that explanation. Eighty
RICO scheduler points were excluded on the dataset authors' own quality flag. BDG2
comprises 10 of 1,258 eligible buildings, so its results are not population-level.
The auxiliary UCI Occupancy experiment reported in Appendix J is a
pipeline-portability check on a dataset designed for binary occupancy
classification; it is not part of the primary comparison and supports no
conclusion in this chapter.

**Computational.** The BDG2 interval stage required approximately 2.6 hours,
dominated by the online updates of the EnbPI arm. XGBoost refits were performed
single-threaded to remove thread-order non-determinism, at a cost of roughly 1.6×
on the point stage. Reproducibility was verified on the same machine; results from
the neural arm may vary across hardware.

*Full limitation register: `report/full_study_limitations.md`,
`report/dissertation_handoff.md`.*

### 4.8.2 Future Work

Six directions follow directly from the limitations above.

First, a **calibration-side model-selection protocol** should be specified and
pre-registered, so that the point-model family and conformal method become
validated selections rather than post-test comparisons. This is the single change
that would most strengthen the framework's deployability claim.

Second, the **RICO undercoverage** should be investigated by the designed
experiments this study identified but did not perform: a formal exchangeability
test across run partitions, and a per-regime refit of the quantile models to test
whether conditional-distribution shift explains the concentration of quantile
crossings in a minority of runs.

Third, the framework should be evaluated against **labelled real faults** where
such data can be obtained, so that alerting performance can be measured rather
than inferred from injected disturbances.

Fourth, the **alert selection criterion** should be generalised beyond
recall-subject-to-budget, since that criterion demonstrably did not select the
test-optimal rule on three of four settings. A cost-weighted criterion that prices
false alerts against missed events would be a natural extension.

Fifth, **calibration-data screening** should be developed into an explicit
pipeline component. Contamination proved the most damaging disturbance studied,
and the framework currently has no mechanism to detect it before calibration.
A related, narrower fix is to gate a differenced meter on stalls in its cumulative
source, which would have removed the PLEIAData energy artefact before modelling.

Sixth, **closed-loop evaluation** should be extended to further fault types and,
ideally, standardised as a default reporting requirement for autoregressive
monitors, since this study demonstrates that the conventional protocol misstates
fault sensitivity on the majority of settings tested.

**Takeaway.** The framework's principal limitations concern the injected nature of
its disturbance evidence and the absence of a pre-registered calibration-side
selection protocol; both are addressable, and the remaining directions follow from
findings this study established rather than from speculation.

---

## Appendix to Chapter 4 — Reporting Record

### A. Section word counts

Counted on the draft as written, including table rows and figure notes.

| Section | Words |
|---|---|
| 4.1 Experimental Overview | 907 |
| 4.2 Point Forecasting Results and Discussion | 1,616 |
| 4.3 Prediction Interval Results and Discussion | 1,718 |
| 4.4 Interval-Based Alert Results and Discussion | 1,533 |
| 4.5 Robustness and Recalibration Results and Discussion | 2,302 |
| 4.6 Statistical and Comparative Analysis | 1,198 |
| 4.7 Overall Findings | 1,392 |
| 4.8 Limitations and Future Work | 624 |
| **Chapter total (excluding this appendix)** | **11,290** |

Prose-only length, excluding table rows, is approximately 8,900 words.

### B. Tables used

| Table | Title | Primary source |
|---|---|---|
| 4.1 | Dataset profiles and supervised partitions | `<dataset>/data_profiles/series_profile.csv`, `window_summary.csv`, `manifests/dataset_sources.json` |
| 4.2 | Point forecasting results by dataset and horizon | `combined/point_metrics.csv`, `combined/effect_sizes.csv` |
| 4.3 | Prediction interval results at nominal 95 % | `combined/interval_metrics.csv` |
| 4.4 | Nested alert selection and final alert performance | `<dataset>/metrics/alert_selection_split.csv`, `combined/alert_metrics.csv` |
| 4.5 | Key robustness results | `combined/robustness_metrics.csv` |
| 4.6 | Recalibration comparison | `combined/recalibration_metrics.csv` |
| 4.7 | Statistical-analysis summary | `combined/ranking_tests.csv`, `posthoc_comparisons.csv`, `statistical_tests.csv`, `bootstrap_metrics.csv` |
| 4.8 | Final cross-dataset ConfoSense configurations | `combined/confosense_configurations.csv` |

An unnumbered terminology table appears at the head of Section 4.5, sourced from
`combined/robustness_metric_schema.csv`.

### C. Figures used

| Figure | File | Section |
|---|---|---|
| 4.1 | `report/figures/fig_01_point_forecasting_comparison.png` | 4.2.4 |
| 4.2 | `report/figures/fig_02_coverage_vs_width.png` | 4.3.1 |
| 4.3 | `report/figures/fig_03_coverage_deviation_by_horizon.png` | 4.3.3 |
| 4.4 | `report/figures/fig_05_alert_rule_sensitivity.png` | 4.4.3 |
| 4.5 | `report/figures/fig_06_alert_tradeoff.png` | 4.4.3 |
| 4.6 | `report/figures/fig_07_robustness_degradation.png` | 4.5.2 |
| 4.7 | `report/figures/fig_13_closed_loop_absorption.png` | 4.5.3 |
| 4.8 | `report/figures/fig_08_recalibration_recovery.png` | 4.5.4 |

### D. Source files used

`combined/point_metrics.csv` · `combined/model_rankings.csv` ·
`combined/effect_sizes.csv` · `combined/bootstrap_metrics.csv` ·
`combined/statistical_tests.csv` · `combined/ranking_tests.csv` ·
`combined/posthoc_comparisons.csv` · `combined/interval_metrics.csv` ·
`combined/rico_quantile_crossings.csv` ·
`combined/rico_quantile_crossings_by_run.csv` · `combined/alert_metrics.csv` ·
`combined/robustness_metrics.csv` · `combined/robustness_metric_schema.csv` ·
`combined/recalibration_metrics.csv` ·
`combined/confosense_configurations.csv` ·
`combined/literature_benchmark_matrix.csv` ·
`combined/pleia_energy_meter_stalls.csv` ·
`combined/pleia_energy_artefact_sensitivity.csv` ·
`<dataset>/data_profiles/series_profile.csv` ·
`<dataset>/data_profiles/window_summary.csv` ·
`<dataset>/metrics/alert_selection_split.csv` ·
`<dataset>/metrics/recalibration_selection.csv` ·
`<dataset>/models/dscp_level95.json` · `manifests/dataset_sources.json` ·
`manifests/run_history.jsonl` · `report/pleia_energy_audit.md` ·
`report/rico_quantile_crossing_audit.md` · `report/alert_selection_audit.md` ·
`report/closed_loop_terminology.md` · `report/full_study_limitations.md` ·
`report/dissertation_handoff.md`

### E. Results requiring cautious wording

1. **RICO CQR undercoverage.** Stated as "CQR substantially undercovered on RICO
   under the evaluated protocol." Exchangeability and regime-shift explanations are
   labelled hypotheses; no causal attribution to run structure is made.
2. **Closed-loop absorption.** Causal language is used only because the
   disturbance was manipulated, and is confined to the injected bias. The
   non-uniformity across settings (0.2580 to 0.9763 observed-signal coverage) is
   stated explicitly wherever the finding appears.
3. **XGBoost versus persistence.** Reported as significant in ten of thirteen
   cells with the winner named per cell — XGBoost in six, persistence in four —
   never as general superiority. The block-level Holm result (p = 1.0000) is
   reported alongside.
4. **PLEIA energy RMSE.** Always accompanied by the meter-stall explanation; MAE
   is designated the headline metric for that target.
5. **BDG2 Winkler and the uncalibrated baseline.** The 0.02 % margin is stated,
   and the row is footnoted in Table 4.8 as not a recommendation.
6. **BDG2 rolling recalibration.** Reported as not distinct from periodic, with
   the persisted `strategy_is_distinct = False` cited; no alternative window was
   manufactured.
7. **Alert rule changes.** Reported as improving selection *validity*, not test
   performance, since RICO's test F1 fell from 0.5344 to 0.4605.
8. **Frozen rules are not test-optimal on three of four settings.** Stated
   explicitly, with the selection criterion identified as the cause and flagged
   for future work.
9. **Literature comparison.** Stated as 0 of 12 directly comparable, with no claim
   of numerical superiority anywhere in the chapter.
10. **UCI Occupancy.** Referenced once, in Section 4.1, solely to record its
    exclusion from this chapter.
