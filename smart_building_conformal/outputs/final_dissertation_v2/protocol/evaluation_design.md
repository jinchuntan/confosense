# Corrected evaluation design (predeclared)

**Status:** PREDECLARATION. This document fixes the corrected evaluation design
*before* any corrected outer-fold result is inspected. It contains no results.
The corrected study writes to `outputs/final_dissertation_v2/`; the original
`outputs/full_study/` is preserved untouched as the pre-repair diagnostic study.

**Baseline commit audited:** `06fe967be2be8d7898812c0c2d6e464d4e942351`
**Repair branch:** `fix/final-dissertation-study`

## Honesty clause (mandatory in the final report)
> The original test outputs were already inspected and used to diagnose the
> pipeline, so they are no longer a pristine holdout. Corrected performance is
> therefore estimated through fully nested post-audit resampling and is **not**
> presented as validation on an untouched holdout. No untouched holdout remains.

## Partitioning (per dataset)
- **PLEIA temperature, PLEIA energy** — purged rolling-origin folds; embargo = the
  forecast horizon on both sides of every boundary. (Embargo now enforced centrally
  in `windowing.apply_horizon_embargo`, verified by
  `test_no_target_time_leakage_across_partitions_chronological`.)
- **RICO** — whole-run / group-blocked folds; each run lies wholly in one partition.
  Any nested calibration subsplit must also cut at whole-run granularity (see plan
  A2 — pending in `alert_study.chronological_subsplit`).
- **BDG2** — target-time-aligned folds *within* buildings over common chronological
  periods; building identity preserved. This measures **within-building temporal
  generalisation only**. A separate leave-building-out analysis is required before
  any *unseen-building portability* claim and is otherwise not asserted.

## Selection (inner folds only)
The complete pipeline — point model, interval method, nominal alert level,
recalibration strategy, temporal alert rule (physical time), episode/latching and
cooldown, event-scaling policy — is selected using only inner training/calibration
folds under the prospectively declared operational policy in `frozen_protocol.yaml`.
Outer-fold test data never enter any selection function. When no candidate meets the
policy, the outcome is recorded as `no_feasible_configuration` and no rule is frozen.

## Seeds and uncertainty
- Aggregate across **all** predeclared seeds; report mean ± 95% CI; never select the
  best seed.
- Confidence intervals from moving-block (single series), run-level (RICO) or
  building-level (BDG2) resampling — never IID bootstrap on serially dependent data.
- Report point estimate, 95% CI and exposure size (asset-days / building-days) for
  every headline number, with per-group, macro and micro summaries where they answer
  different questions.

## Alert metrics (prevalence-resistant, primary)
Synthetic-event recall macro-averaged across event type × severity; recall by type and
severity; **background alert episodes per asset-day** (BDG2: per building-day and
portfolio per calendar-day); median and upper-quantile detection delay; proportion of
time in alert state. Natural interval violations are reported as *background/unmatched
alert workload*, never as confirmed false positives, because the public datasets carry
no comprehensive real fault labels. Precision/F1 are secondary and only reported at a
single explicitly declared standard event incidence, plus a sensitivity sweep.

## Interval quality (methodological, kept regardless of operating level)
For every candidate {quantile-uncalibrated, CQR, static recentred EnbPI, corrected
updated recentred EnbPI, DSCP} × dataset × horizon × {90%, 95%}: empirical coverage,
coverage deviation, mean/normalised width, Winkler score, quantile-crossing count,
group-level coverage, macro-average and worst-group, with group-appropriate resampling
CIs. Selection never uses coverage deviation alone; a predeclared calibration-side
feasibility+utility criterion governs the operating choice.

## Change control
Candidate grids and the selection policy are frozen (hash in `config_hash.txt`) before
outer evaluation and are not altered afterwards except to repair a verified code defect,
each of which is logged in `report/RESULTS_CHANGELOG.md` with the affected folds re-run.
