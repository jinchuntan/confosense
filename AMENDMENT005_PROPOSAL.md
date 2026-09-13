# Amendment-005 proposal: separate operational frequency, conditional challenge and matched forecasting

**Version:** `amendment005_proposal_v1`, 13 September 2026. **Post-inspection proposal; no fitting authorized or performed.** This document supplements amendment 004. It never modifies the historical 0.60 recall / 1.0 episode-per-asset-day gates, old memberships, incidence, thresholds or BDG2 abstentions. [Quantified audit](SUPPORT_DESIGN_AUDIT.md) and [execution plan](REMAINING_STUDY_EXECUTION_PLAN.md) supply the evidence and implementation sequence.

## Questions and estimands

| Endpoint | Retained task scope | Estimand and available interpretation |
|---|---|---|
| Matched forecasting and own-model intervals | All 13 task/horizon combinations; persistence, XGBoost, Attention-LSTM; seasonal where applicable | Common-target MAE/RMSE; 90/95% own-model split-conformal coverage, MPIW, Winkler and actual phase costs. Separate units per task. |
| Natural-frequency monitoring A | All four tasks, existing primary horizons and incidence 0.5/asset-day | Original-exposure clean workload and supported injected-event strata. Full primary nested operational selection remains unavailable for the three unsupported tasks. |
| Effective-fault conditional context challenge C | PLEIA temperature/energy and RICO at primary horizons | Per-stratum detection conditional on a predetermined context and an effective realization; each original context weighted equally. A separately named 21-stratum conditional macro is available only when all strata meet support. |
| Broader methods/robustness | All declared tasks/methods retained | Separate method-quality, contamination, closed-loop cascade and censored recovery evidence; no substitution of C for their different questions. |

For C, let a context's score within a stratum be the mean detection indicator over its effective replicate slots. Average those context scores equally within that stratum, then average all 21 strata equally. Report scheduled/effective/null counts and effective-context denominators alongside the result. This **conditional-context macro** differs from amendment 004's pooled event-count macro. A context with no effective replicate contributes to null incidence, not the positive denominator. A missing/under-supported stratum makes the full conditional macro unavailable; supported stratum estimates remain visible with their denominators. Do not report an observed-strata-only mean as the full macro.

Clean workload is measured once on the full original held-out stream per model/policy and divided by original eligible asset-days. It is not multiplied by challenge variants, confined to easy challenge windows or labelled an adjudicated false-alarm probability. Challenge precision/F1 does not estimate deployment precision or real fault prevalence. A challenge recall bound never replaces amendment 004's primary feasibility gate. Fixed-incidence and challenge outputs have different endpoint IDs and tables.

## Targets, horizons, memberships and calibration

PLEIA temperature: block B room 11 V2, degrees Celsius, 10-minute sampling, forecasting horizons 10/30/60 minutes; primary alert horizon 10 minutes. PLEIA energy: block B `dif_cons`, kWh per 10-minute interval, the same horizons. RICO: `B.RTD3`, degrees Celsius, one-minute sampling, forecasting horizons 5/15/30/60 minutes; primary alert horizon 5 minutes. BDG2: all ten retained buildings, hourly kWh, horizons 1/3/6 hours; primary alert horizon 1 hour. No additional sensor or easier cohort was selected.

For PLEIA C, retain amendment-004 role boundaries exactly. B0–B3 are four purged quarters of the final fitting pool; inner0 fits B0/calibrates B1/evaluates B2, inner1 fits B0+B1/calibrates B2/evaluates B3. Reserved final calibration and outer periods remain unchanged. For matched forecasting, retain the existing pilot's 24-step sequence/common-flat-feature eligibility, two expanding purged tuning folds and final calibration; the three completed PLEIA horizon hashes matched exactly. Forecasting and operational masks are separately versioned and are not falsely treated as identical.

For RICO C and the new matched-forecasting version, order all 207 retained runs by first origin then ID; split the run list into five chronological blocks using floor(207/5)=41 and a 43-run final remainder. The last three blocks are outer tests. Fold IDs remain backward: **fold 2=41 earliest evaluation runs, fold 1=41 middle, fold 0=43 latest**. Earlier runs supply development; reserve its last quarter of whole runs for final calibration. Keep entire runs at all boundaries. Original source flags and run lengths remain unchanged. Per-horizon sequence eligibility may reduce row counts but never split a run's role.

| outer_fold | role | n | groups | target_min | target_max | asset_days |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | final_fit | 27183 | 123 | 2023-07-26 15:20:00 | 2024-02-04 11:00:00 | 18.8771 |
| 0 | final_calibration | 9061 | 41 | 2024-02-04 11:20:00 | 2024-05-11 03:00:00 | 6.29236 |
| 0 | outer_test | 9503 | 43 | 2024-05-11 03:20:00 | 2024-05-18 07:00:00 | 6.59931 |
| 1 | final_fit | 20332 | 92 | 2023-07-26 15:20:00 | 2024-01-30 03:00:00 | 14.1194 |
| 1 | final_calibration | 6851 | 31 | 2024-01-30 03:20:00 | 2024-02-04 11:00:00 | 4.75764 |
| 1 | outer_test | 9061 | 41 | 2024-02-04 11:20:00 | 2024-05-11 03:00:00 | 6.29236 |
| 2 | final_fit | 13481 | 61 | 2023-07-26 15:20:00 | 2023-08-07 23:00:00 | 9.36181 |
| 2 | final_calibration | 4641 | 21 | 2023-08-07 23:20:00 | 2023-08-12 03:00:00 | 3.22292 |
| 2 | outer_test | 9061 | 41 | 2023-08-12 07:20:00 | 2024-02-04 11:00:00 | 6.29236 |


The evaluation is conditional on the represented acquisition phases:

| outer_fold | phase | runs | start | end | ever_legacy_final_fit | ever_legacy_final_calibration |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 5 | 43 | 2024-05-11 03:01:00 | 2024-05-18 07:00:00 | 0 | 42 |
| 1 | 4 | 24 | 2024-02-04 11:01:00 | 2024-02-08 11:00:00 | 24 | 0 |
| 1 | 5 | 17 | 2024-05-08 07:01:00 | 2024-05-11 03:00:00 | 7 | 11 |
| 2 | 1 | 1 | 2023-08-12 07:01:00 | 2023-08-12 11:00:00 | 1 | 0 |
| 2 | 3 | 6 | 2024-01-22 13:30:00 | 2024-01-26 01:29:00 | 6 | 0 |
| 2 | 4 | 34 | 2024-01-29 15:01:00 | 2024-02-04 11:00:00 | 34 | 0 |


The [207-run history ledger](smart_building_conformal/outputs/amendment005/study_plan_v1/rico_run_history.csv) shows prior training/calibration/test use under every old fold. These are not globally untouched holdouts. Within each new fold, only earlier runs train/calibrate; the reporting must disclose prior inspection and reuse. No unseen-building or prospective-trial claim follows.

Matched forecasting normalizes only on each permitted training block; tuning uses equal inner-fold MAE, fixed two-candidate grids and deterministic candidate-order ties. LSTM final epochs are the ceiling of the mean selected-candidate best epochs. Final calibration/test outcomes select neither candidates nor epochs. RICO calibration is pooled over earlier whole runs; new evaluation runs have no within-run calibration observations. Report that assumption and phase-specific quality rather than promising conditional coverage. Initial calibration remains at least 400 rows; insufficient finite ranks produce unavailable/infinite bounds with an explicit status.

## Fixed challenge contexts and schedules

The machine specification is [proposal_spec.json](smart_building_conformal/outputs/amendment005/support_design_v1/proposal_spec.json). [Membership/observations and schedule files](review/support_design_20260913/EVIDENCE_INDEX.md) are sufficient to recalculate the no-fit realization evidence; raw source data and exact features are still required for future fitting.

- PLEIA: tile each eligible contiguous role segment into nonoverlapping 144-row (24-hour) contexts, anchored at that segment's first row; leave the shorter final tail unused for the challenge but included in full-stream clean workload.
- RICO: one context per whole eligible run. Never concatenate runs or bridge acquisition gaps.
- Choose one onset per context using a SHA-derived seed from version, task, fold, role and context identity, with master context seed **20260913**. Selection uses structure only. No onset is moved after inspecting signal magnitude, null status or detection.
- Require warm-up of **360 minutes for PLEIA**, **60 minutes for RICO**, the original one-hour fault envelope (6 or 60 samples), and at least **60 minutes follow-up**. The original detection tolerances remain 60 and 10 minutes respectively. The actual predecessor and entire envelope/follow-up lie in the same context. Future features may use only available original pre-context history in that source segment; common feature eligibility already establishes required lag/sequence history.
- Every context receives all seven families x three severities in independent counterfactual replays. Use exactly **two slots**, seeds 42/43, with additive signs -/+ respectively. Random-missing masks have independent event-keyed RNGs. Deterministic block/stuck/dropout slots can be identical: [aliases](smart_building_conformal/outputs/amendment005/study_plan_v1/challenge_aliases.csv) identify them, and they add no original contexts or inferential degrees of freedom.
- The two-slot choice counterbalances additive signs; it is a fixed project design, not a claimed precision optimum. Stop after the fixed slots regardless of nulls or model results. Do not select easy severities, replace nulls or draw until support/performance passes.
- Reset alert, residual-release and recalibration state independently for each context/variant, initialized from that role's permitted historical calibration pool. Use clean observed warm-up and causal corrupted inputs thereafter; corruption enters future lags, rolling features and observable residuals. Targets release residuals only when available; no clean truth repairs the corrupted path. Methods share context/onset/mask identities. The clean counterfactual has its own state.
- Keep one clean/zero identity replay per context, shared across equivalent zero-family slots. It must reproduce clean inputs, issued bounds, alerts and released scores exactly; no zero-control is a positive. The no-fit schedule's clean control is the unchanged context observation sequence; the future runner must enforce stream identity.

Fault realizations use the preserved amendment-004 definitions and training-only robust sigma, including pooled-training fallback for new RICO runs. Missingness is availability loss; dropout is numerical zero; stuck holds the observable predecessor of its sub-block. No-change schedules stay null. At least five **distinct effective contexts/onsets** per stratum and five original context/run units are needed for the full named conditional point estimate. All 567 current proposed role/stratum cells pass that structural screen, while inference has separate requirements below.

## Fixed comparisons and selection restrictions

C is **evaluation-only**, with no challenge-score selection. Use fixed .95 quantile-uncalibrated/static, CQR/static, CQR/first-declared-rolling, and persistence with its own fixed .95 absolute split-conformal interval. Uncalibrated quantiles and CQR share the actual HistGradientBoosting quantile fit; they are not labelled Attention-LSTM or XGBoost. Rolling settings are **every 24/window 250** for both PLEIA tasks and **every 15/window 200** for RICO, with minimum online pool50. Keep immediate and each context-supported declared physical temporal rule, with fixed no latching/cooldown. Full remaining interval-method comparisons are in their separate ledger.

PLEIA context-supported rules are immediate, 30-minute3/3, 60-minute4/6, 180-minute3/18 and 360-minute4/36. Five- and fifteen-minute rules fail sampling-frequency k/m applicability. RICO supports immediate, 5-minute2/5, 15-minute3/15, 30-minute3/30 and 60-minute4/60. Its 180/360-minute candidates cannot fit complete warm-up, envelope and follow-up into a four-hour run; they remain explicitly inapplicable for this conditional-context endpoint, not silently removed from historical amendment 004. [Applicability ledger](smart_building_conformal/outputs/amendment005/support_design_v1/challenge_rule_applicability.csv).

Availability-only, numerical-only and combined episode detection remain separate. Missing-data alarms are shared by the baselines. Match actual episode onsets one-to-one at target-observation time; pre-active episodes earn no onset credit. Retain misses, detected-only delays and restricted mean time-to-detection with misses censored at the full envelope-plus-tolerance horizon. Recovery is descriptive return toward pre-context coverage using the existing literal 0.05 numerical convention, with fixed follow-up, censoring and unavailable medians retained. Do not tune floating-point tolerances or thresholds.

## Inference, limitations and implementation gate

For C, aggregate the five declared model seeds within original contexts before inference; do not count seeds or variants as independent data. Outer summaries exclude all inner-role outcomes. For PLEIA, resample blocks of seven adjacent daily contexts within original segments/folds, carrying every method/stratum/replicate together. Use fixed-length moving blocks for the percentile diagnostic and keep edge/tail context contributions with their observed weights; the nonoverlapping complete-week counts in the [support table](smart_building_conformal/outputs/amendment005/study_plan_v1/challenge_precision_support.csv) screen whether at least five original blocks exist. Earliest inner roles fail that precision screen and retain unavailable CIs. They still permit conditional stratum point estimates.

For RICO, resample whole runs within acquisition phase, retaining original phase weights and all paired contributions. Require at least five original runs and at least two runs in every phase for a phase-stratified population interval; otherwise report conditional descriptive values and unavailable bounds. The earliest proposed outer fold contains only one phase-1 run, so its phase-stratified interval is unavailable unless that phase is explicitly treated as fixed descriptive support; do not silently drop it. Use 2,000 fixed draws, bootstrap seed 20240601, at least 1,900 valid nondegenerate draws. These are approximate conditional diagnostics, not exchangeability guarantees.

This amendment requires a context-replay entrypoint that consumes the published membership/schedule hashes, enforces resets/warm-up/null handling, preserves method ownership and exports original-unit contributions plus zero-control stream identities. It is **not yet implemented as a fitting/replay command**. The structural scripts and independent no-fit checks are implemented and complete. The next implementation priority is the independent matched-forecasting package below, not a full operational launch.

The original fixed-incidence 21-stratum operational selection claim remains non-estimable for the three unsupported tasks under amendment 004. Additional independent exposure or a separately justified incidence/allocation design is needed to answer that original question. C answers a narrower, explicitly different conditional question and does not manufacture deployment feasibility. BDG2's completed results, all historical thresholds and all datasets remain visible. Full-study/publication readiness remains **false**.

Machine-readable supplements: [27 complete inference screens including phase support](smart_building_conformal/outputs/amendment005/support_final_checks_v1/challenge_inference_support.csv) and [1,128 clean identity schedules](smart_building_conformal/outputs/amendment005/support_final_checks_v1/challenge_zero_controls.csv). Input identity is specified without fitting; issued-bound/alert identity awaits the future replay runner and is not claimed complete.
