# Final dissertation study — repair plan

**Branch:** `fix/final-dissertation-study`
**Baseline commit (pre-repair):** `06fe967be2be8d7898812c0c2d6e464d4e942351`
**Baseline tests:** 183 passed, 1 skipped, 0 failed (`pytest`, cfs_venv, 72 s).
**Corrected outputs will be written to:** `outputs/final_dissertation_v2/` (the existing
`outputs/full_study/` is preserved untouched as the original diagnostic study).

This plan is grounded in a three-part read-only source audit (partitioning/features;
interval methods/recalibration; alerting/events/selection). Every defect below cites the
file and line where it was confirmed. Nothing here was inferred from the existing test
outputs; the outputs are treated as *diagnostic only* per the task's scientific rules.

Legend for **Validity of old results**:
- **INVALID** — must be withdrawn or re-run before any dissertation claim.
- **DIAGNOSTIC** — usable to understand behaviour, not as a final claim.
- **DEFENSIBLE** — methodologically sound; may stand with corrected framing.

---

## A. Partitioning & validation

### A1. Origin-time splitting with no horizon embargo → target-time leakage
- **Evidence:** `src/windowing.py:90` passes `meta["origin_time"]` to the partitioner;
  `src/datasets/base.py:182-196` (`ChronologicalPartitioner`) cuts the index by position
  and labels by origin only. No embargo/purge of any width.
- **Effect:** last train origins have targets `origin + h·freq` that land inside the
  calibration window; last calibration targets land inside test. Affects **pleia,
  pleia_energy, bdg2**. RICO is immune (`GroupPartitioner`, base.py:204-235 assigns whole
  runs; targets never exist past a run end).
- **Correction:** add a target-time-aware embargo. In `ChronologicalPartitioner.labels`,
  after origin labelling, reassign to a dropped `"embargo"` partition any origin whose
  `origin + horizon·freq` crosses the next boundary (train→calib, calib→test). Persist
  embargoed counts.
- **Regression test:** `test_no_target_time_leakage_across_partitions` — for pleia h=6,
  assert `max(target_time[train]) < min(origin_time[calibration])` and the calib→test
  analogue.
- **Validity of old results:** point/interval/alert metrics for pleia, pleia_energy, bdg2
  are **DIAGNOSTIC** (mild optimism from ≤h leaked boundary rows out of tens of thousands;
  RICO unaffected). Re-run under embargo for final claims.

### A2. RICO nested alert subsplit is not run-aware
- **Evidence:** `src/alert_study.py:117-123` (`chronological_subsplit`) cuts the pooled
  calibration target-time axis; no `group_id` awareness, so the straddling run is split
  between the conformal-fit and rule-scoring blocks.
- **Correction:** for grouped datasets, subsplit at whole-group granularity.
- **Regression test:** `test_rico_alert_subsplit_keeps_runs_whole` — no `group_id` in both
  `conformal_mask` and `rule_mask`.
- **Validity:** RICO alert-rule *selection* is **DIAGNOSTIC**.

### A3. BDG2 is within-building only; no unseen-building portability
- **Evidence:** `src/datasets/bdg2.py:306-338` one series per building; `base.py:182-189`
  splits inside each building on its own fractions; every building appears in train, calib
  and test (`study_runner.py:200-201`). No leave-building-out anywhere.
- **Correction:** none for correctness. **Do not** claim unseen-building generalisation.
  Add an optional leave-building-out variant only if portability is claimed.
- **Regression test:** `test_bdg2_every_building_in_all_partitions`.
- **Validity:** BDG2 results are **DEFENSIBLE** as *within-building temporal* generalisation;
  any portability wording is **INVALID** and must be removed.

## B. Feature pipeline

### B1. `target_lag_0` absent from every config (y_t not a feature)
- **Evidence:** `src/features.py:52-53` supports `target.shift(k)` and `y = target.shift(-h)`
  (features.py:85), but no config lists 0 — `study_full.yaml:38` `[1,2,3,6,12]`, `:222`
  `[1,2,3,5,10]` (rico), `:270` `[1,2,3,6,12,24]` (bdg2). Most recent value a model sees is
  `y_{t-1}`, though `y_t` is known at origin; this handicaps learned models vs persistence.
- **Correction:** guarantee lag 0 (default it in `windowing.feature_config` and/or prepend 0
  to each config's `target_lags`). Rolling windows already end at `t` (features.py:63-66).
- **Regression test:** `test_target_lag_0_present_and_equals_yt`.
- **Validity:** all learned-model point results are **DIAGNOSTIC** (understate the models);
  re-run needed.

### B2. Ordered feature schema not persisted
- **Evidence:** `feature_names` computed and consistency-checked (windowing.py:84-89) but
  never written to disk.
- **Correction:** dump `data_profiles/feature_schema_h{h}.json` per dataset/horizon.
- **Regression test:** `test_feature_schema_persisted`.
- **Validity:** auditability gap, results unaffected.

### B3. BDG2 weather configured but silently dropped if missing
- **Evidence:** `bdg2_full`/`study_full.yaml:260-261` set `use_weather: true`; `bdg2.py:243`
  only downloads electricity+metadata (not `weather.csv`); `bdg2.py:275` gates on
  `wpath.exists()` and silently yields `covariates=[]`; cross-building intersection
  (bdg2.py:324-327) empties weather if any building lacks it.
- **Correction:** fetch `weather.csv`; if `use_weather` and weather missing/empty, raise or
  `manifest.note_limitation`.
- **Regression test:** `test_bdg2_weather_configured_but_missing_is_loud`.
- **Validity:** BDG2 model inputs are **DIAGNOSTIC** if weather was silently absent — verify
  which was true in the old run and record it.

### B4. PLEIA energy meter stalls / zero runs / catch-up spikes
- **Correction:** keep primary data; add a *predeclared* sensitivity analysis (mask vs keep),
  never silently clean.
- **Validity:** existing pleia_energy is **DEFENSIBLE** as primary; sensitivity is additive.

## C. Interval methods

### C1. Updated recentred EnbPI is horizon-unsafe and cross-group
- **Evidence:** `src/conformal_enbpi.py:128-135` forecasts a block then immediately
  `model.update(Xte[block], yte[block])`; no `target_time` gating, so the last `h-1` rows of
  each block are consumed before their ground truth exists; a single pooled
  `TimeSeriesRegressor` means one group updates another. The correct
  `DelayedResidualPool`/`availability_frontier` (`src/residuals.py:35-125`) is used by
  recalibration but **not** by this path.
- **Correction:** gate updates by `target_time ≤ current_origin` and hold per-group state
  (reset at each `group_id`). Reuse `residuals.availability_frontier`.
- **Regression tests:** `test_enbpi_no_early_residual` (delayed vs current differ pre-fix,
  equal post-fix); `test_enbpi_no_cross_group_update`.
- **Validity:** **updated** recentred-EnbPI results are **INVALID** until re-run. Static
  recentred-EnbPI, CQR, DSCP, quantile-uncalibrated are unaffected.

### C2. CQR crossing handling & DSCP parity
- **Evidence:** `src/conformal_cqr.py:65-73` swaps crossed bounds and reports
  `n_crossed_repaired`; DSCP clamps (`conformal_dscp.py:255`) but does not count.
- **Correction:** sound as-is; optionally count DSCP crossings for parity. Investigate RICO
  crossing concentration as a *predeclared* candidate (group/regime-conditional calibration)
  inside the nested protocol, not a post-hoc swap.
- **Validity:** **DEFENSIBLE**.

### C3. Recalibrated interval stream never reaches alerts
- **Evidence:** stage order `intervals → alerts → recalibration` (`study_runner.py`); alerts
  read only `artifacts["intervals"]` (CQR). Recalibration is itself horizon-delayed and
  group-safe (residual_delay=h, per-group pools) but unconsumed downstream.
- **Correction:** add an explicit end-to-end variant that feeds the *selected* recalibrated
  stream into the alert stage (§E), or document recalibration as diagnostic-only.
- **Validity:** the "recalibration improves alerting" claim is **INVALID** (never evaluated
  end-to-end); recalibration *interval* metrics are **DEFENSIBLE**.

## D. Alerting, events, selection

| # | Defect | Evidence | Correction | Test | Old-result validity |
|---|--------|----------|-----------|------|---------------------|
| D1 | Alerts hard-wired to CQR@95% | study_runner.py:578-591 | make (method,level,rule) selectable in inner folds, or declare CQR@95% a fixed operating point with justification | `test_alert_interval_selected_in_validation` | DIAGNOSTIC |
| D2 | Alert state not group-safe (k-of-m, clustering, tolerance mask leak across groups; also robustness_study.py:229) | alerts.py:41,152,161 | thread `group_ids`; reset k-of-m, clusters, masks at every run/building boundary | `test_no_cross_group_alert_state` | **INVALID** for RICO & BDG2 alert metrics |
| D3 | Step-based rules, not physical time | alert_study.py:42-47 | rules in minutes/hours → steps via each dataset freq | `test_physical_time_rule_conversion` | DIAGNOSTIC (rules not comparable across datasets) |
| D4 | Fixed ~42 events, not per-asset-day incidence | alert_study.py:157-188 | size by `events_per_stream_day × stream_days`; same declared incidence when comparing precision/F1 | `test_event_incidence_matched` | **INVALID** for cross-dataset precision/F1 |
| D5 | Pooled non-robust event scaling | study_runner.py:763-768 | per-group training-only robust scale (MAD→σ) | `test_per_group_event_scale` | **INVALID** for injected-severity semantics |
| D6 | Naive episode matching (not one-to-one/onset-aware, fragments alarms) | alerts.py:168-213 | build episodes → one-to-one → onset-aware (pre-existing alarm ≠ detection) → single workload unit | `test_onset_aware_one_to_one_matching` | **INVALID** for detection/precision |
| D7 | No `no_feasible_configuration` path | alert_study.py:331-366 | abstain + record when no candidate meets policy | `test_no_feasible_configuration` | DIAGNOSTIC |
| D8 | Synthetic-label "precision"/"false positives"; micro recall | alerts.py:190-208 | rename to background/unmatched workload; macro-average recall across type×severity | `test_macro_recall_and_background_terms` | Framing **INVALID**; recompute + relabel |
| D9 | Recall-first selection policy not prospectively justified | alert_study.py:331-366 | prospective operational policy in frozen YAML (§E); Pareto secondary | covered by §E tests | DIAGNOSTIC |
| D10 | Nominal 95% forced as operational alert level | study_full.yaml:35,88 | predeclare {95,97.5,99,99.5} / p-value thresholds; select in inner folds; keep 90/95 for interval-quality | `test_alert_level_selected_in_validation` | DIAGNOSTIC |

## E. End-to-end pipeline (currently never evaluated as one object)
- The claimed final methodology (point + interval + level + recalibration + temporal rule +
  episode/latching + cooldown + event-scaling) is assembled from *separate* stage tables.
- **Correction:** implement one integration path where the **selected recalibrated interval
  stream is the stream the alert stage consumes**, selected entirely on inner folds, then
  scored once on the outer fold. Tests: `test_end_to_end_pipeline_evaluated`,
  `test_selected_config_equals_evaluated_config`.
- **Validity:** any "final methodology" performance number is **INVALID** until this exists.

## F. Corrected evaluation design (frozen before viewing outer results)
- **PLEIA / pleia_energy:** nested purged rolling-origin folds, embargo = horizon.
- **RICO:** nested whole-run / group-blocked folds; nested calibration also whole-run.
- **BDG2:** nested target-time-aligned folds *within* buildings (common periods); optional
  separate leave-building-out portability analysis, clearly labelled.
- **Seeds:** aggregate across all predeclared seeds; report mean ± CI; never pick best seed.
- **Resampling CIs:** moving-block (series) / run-level / building-level bootstrap — never IID.
- **Honesty clause (mandatory in the final report):** *"The original test outputs were used
  for methodological diagnosis. Corrected performance is therefore estimated through fully
  nested post-audit resampling and is not presented as validation on a pristine untouched
  holdout."* No untouched holdout remains.

## G. Execution status & sequencing
Implemented and tested in this session are listed in `report/RESULTS_CHANGELOG.md` as they
land. The full corrected multi-seed study is a **checkpointed** run: it is not presented until
it completes, and no corrected metric is reported before its source CSV exists. The frozen
protocol (`outputs/final_dissertation_v2/protocol/`) is written and hashed **before** any
outer-fold result is inspected, and the candidate grids / selection policy are not altered
afterwards except to repair a verified code defect (each such change is logged and its folds
re-run).

## H. Non-negotiables carried into every step
No configuration/level/seed/rule/dataset is chosen because it scored better on existing
outputs; chronology and RICO-run/BDG2-building boundaries are preserved; difficult
datasets/events/severities/methods are retained; `outputs/full_study/` is never overwritten;
every final number is traceable to a generated CSV + manifest + frozen config hash; synthetic
fault detection is reported as *synthetic-event recall* and *background alert workload*, never
as real-world precision.
