# Supported comparative findings for Chapter 4

These findings are bounded to the validated tasks, horizons, supports and
synthetic-event protocols named in `METHODOLOGY_FACTS.md`. They are descriptive
unless an original-context conditional bound is explicitly reported.

## Evidence against the approved objectives

- **RO1:** the experiments provide an empirical comparison of simple,
  tree-based and recurrent forecasting; conformal interval constructions;
  online recalibration; and interval-derived alert rules. The literature review
  and conceptual synthesis remain report-writing work rather than an
  experimental result.
- **RO2:** the complete implemented chain is evidenced: causal features ->
  matched point forecasts -> conformal intervals -> delayed residual updates ->
  k-of-m alert episodes -> clean/fault/recovery metrics -> independent
  validation and preservation.
- **RO3:** direct alert comparisons exist for the PLEIA temperature and energy
  conditional challenges, the BDG2 one-hour operational replay, and the frozen
  robustness/recovery cells. The matched forecasting and 1,950-cell interval
  matrix support accuracy and interval-quality comparisons, but do not by
  themselves support fault precision/recall/F1 claims.

## Point forecasting and simple baselines

Across the 13 matched task-horizon summaries, XGBoost has the lowest MAE in
seven and persistence in six; Attention-LSTM has the lowest MAE in none.
XGBoost leads all three BDG2 horizons and all three PLEIA-energy horizons, plus
RICO at 60 minutes. Persistence leads all three PLEIA-temperature horizons and
RICO at 5, 15 and 30 minutes. This is strong evidence that simple persistence
must remain an explicit benchmark rather than a token baseline.

Seasonal-naive is evaluated only for BDG2 and the two PLEIA tasks. It uses 27
unique deterministic fold computations; seed-labelled views are not extra
runs. Its equal-fold MAE is about 38.88--38.90 kWh for BDG2, 1.046 degrees C
for PLEIA temperature and 0.230 kWh/10 min for PLEIA energy. It does not replace
persistence as the best simple baseline in these matched summaries, and it is
inapplicable to the frozen RICO design.

Use `REPORT_TABLES/POINT_FORECASTING.csv` for all exact values and ranks.

## Interval quality

At the dataset-level common-support medians reported by the completed
interval-method analysis:

- CQR has the lowest median Winkler score among the five methods for BDG2 and
  PLEIA energy at both 90% and 95%.
- DSCP has the lowest median Winkler score for PLEIA temperature and RICO at
  both levels. This is not a pure conformal-only comparison because DSCP uses
  the matched XGBoost owner.
- Relative to its shared uncalibrated-quantile owner, CQR raises median coverage
  by 0.110 (BDG2), 0.222 (PLEIA temperature), 0.119 (PLEIA energy) and 0.184
  (RICO), while its median Winkler difference is lower by 3.287 kWh, 17.943
  degrees C, 0.044 kWh and 1.266 degrees C respectively.
- Updated versus static recentred EnbPI is strongly beneficial for the
  undercovered PLEIA-temperature and RICO settings. For BDG2 it trades a modest
  median coverage reduction for materially narrower intervals and a lower
  Winkler score. The direction and magnitude therefore remain task-specific.

The horizon-preserving values are in
`REPORT_TABLES/INTERVAL_METHODS_COMMON_SUPPORT.csv`; own-model forecasting
intervals are separate in `REPORT_TABLES/INTERVAL_OWN_MODEL.csv`. Do not copy a
dataset-level median into a horizon-specific claim without checking the former.

## Attention-LSTM cost and predictive benefit

Attention-LSTM used 17.85--81.19 times the recorded process CPU of XGBoost
across the 13 equal-fold task-horizon summaries (median ratio 33.65). It did not
beat XGBoost on MAE in any summary. Its 95% own-model interval had a lower
Winkler score in only two of 13 summaries, both PLEIA-temperature horizons (30
and 60 minutes), with improvements of only 0.164 and 0.802 degrees C while
coverage differed by 0.022 and 0.015 and MPIW was wider. At the other 11
task-horizons its Winkler score was higher; the RICO coverage deficit was also
large.

The recorded computational expense is therefore not accompanied by a general
point-accuracy or interval-quality benefit. This conclusion concerns the
frozen architecture, tuning budget, datasets and horizons—not all possible
LSTM designs. The CPU and fit-phase measurements are original matched-model
training/calibration/inference costs. Robustness and operational replay reused
saved owners; they are not additional Attention-LSTM training measurements.

Exact contrasts are in `REPORT_TABLES/ATTENTION_LSTM_VS_XGBOOST.csv`, and cost
scope is separated in `REPORT_TABLES/COMPUTATIONAL_OVERHEAD.csv`.

## Direct alert findings

### PLEIA conditional contexts

No one control/rule pair dominates both detection and clean workload across the
two PLEIA tasks. In the combined channel, the highest detection control changes
with the temporal rule:

- PLEIA temperature: persistence-static leads single-sample, 180-minute and
  360-minute rules; rolling CQR leads the 30-minute and 60-minute rules.
- PLEIA energy: quantile-static leads single-sample and 60-minute rules;
  persistence-static leads the 30-minute rule; rolling CQR leads the
  180-minute and 360-minute rules.

Higher detection can carry high clean-stream workload. For example, the
PLEIA-energy single-sample quantile control detects 0.893 of the conditional
endpoint but produces 18.646 background episodes per asset-day; the
PLEIA-temperature single-sample persistence control detects 0.909 with 4.244
episodes per asset-day. The temporal rule and workload must therefore accompany
every detection claim. All channels, supported bounds, misses and restricted
times are retained in `REPORT_TABLES/CONDITIONAL_ALERTS_PLEIA.csv`.

### BDG2 one-hour operational replay

Across native-support candidate summaries, mean event recall spans 0.0601 to
0.8067 and mean clean workload spans 0.00319 to 1.501 episodes per asset-day.
Static 95% CQR with a single-sample rule has the highest mean recall (0.8067),
ordinary matched-event episode precision 0.258, custom synthetic F1 0.381 and
mean clean workload 1.118. Among configurations with mean workload at or below
one, the strongest recall values are rolling 95% CQR single-sample controls:
about 0.775--0.780 recall, 0.970--0.986 mean episodes per asset-day, and
restricted mean detection time about 132--134 minutes. Their maximum
fold/seed workload still exceeds one, so this is a descriptive trade-off rather
than a universal deployment selection.

`REPORT_TABLES/OPERATIONAL_ALERTS_BDG2_H1.csv` retains macro recall,
observed-strata recall, micro recall, ordinary precision, the distinct custom
synthetic F1, clean workload, time in alert and delay metrics. Native and common
support rows are two views of the same evaluations.

## Robustness, contamination and recovery

The exact zero control equals the clean stream for all 60 units. Under
`level_shift@2`, mean during-window coverage loss is 0.878 for BDG2, 0.379 for
PLEIA temperature, 0.664 for PLEIA energy and 0.860 for RICO. PLEIA temperature
stuck/dropout faults are slightly more damaging on the same summary (about
0.407 loss). Random missing is mild in BDG2, PLEIA energy and RICO but reduces
PLEIA-temperature coverage by about 0.087.

Calibration-only contamination widens intervals substantially. Mean width from
clean reference to 5%/10% contamination changes from 132.99 to 646.49/650.99
for BDG2; 3.26 to 9.66/10.04 for PLEIA temperature; 0.77 to 1.00/1.07 for PLEIA
energy; and 1.37 to 10.15/10.23 for RICO. The associated coverage increase is
not a free robustness gain because it is obtained through much wider intervals.

All 450 BDG2 group-policy recovery rows are observed. PLEIA temperature has
10/15 static, 13/15 periodic and 15/15 rolling recoveries; PLEIA energy has
12/15, 13/15 and 15/15. RICO has 578/625 static, 523/625 periodic and 312/625
rolling recoveries. The other 474 group-policy rows remain right-censored.
Those outcomes show that recalibration policy effects are dataset-specific;
rolling updates are not universally fastest or most likely to recover.

Use the three `ROBUSTNESS_*.csv` tables; do not replace censored rows with an
invented recovery time or collapse group-specific outcomes into independent
population replicates.

## Limits on conclusions

The evidence supports reliability comparisons within the declared datasets,
horizons, owners, synthetic-fault designs and clean-workload definitions. It
does not establish universal robustness, natural fault prevalence, deployment
performance, or population-level superiority. Cross-target MAE, width and
Winkler values are in different units and must not be numerically pooled.
