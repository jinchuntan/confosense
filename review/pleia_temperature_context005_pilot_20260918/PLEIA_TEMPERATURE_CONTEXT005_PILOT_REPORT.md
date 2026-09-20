# PLEIA temperature conditional-context pilot (fold 2, horizon 1, seed 42)

Unit `pleia_f2_s42_C_v1` | dataset `pleia` (temperature, degC) | outer fold 2 | horizon 1 (10 min) | model seed 42 | 95% intervals | endpoint `C_effective_fault_conditional_context` | selection `none`.

**This is a conditional synthetic-fault challenge on one model seed and one outer fold.** Detection and workload below are conditional on a predeclared fault being present. They are not prevalence, precision, F1 or deployment-feasibility estimates. Temperature units differ from the energy study, so no cross-dataset error is pooled and no energy uncertainty bound is transferred. BDG2 operational feasibility remains a separate endpoint.

<!-- validation-audit-20260919 -->
> **Acceptance status: execution and publication complete; scientific acceptance pending validation.** The frozen `validate` action did not pass and has not been made to pass. A validation audit on branch `review/pleia-temperature-context005-validation-audit-20260919` proves the failure mechanism, shows that no evaluated endpoint differs, and proposes a candidate validator that is NOT adopted here. See `review/pleia_temperature_context005_validation_audit_20260919/VALIDATION_AUDIT_REPORT.md`.

## Execution and scope

| Item | Value |
| --- | --- |
| Original contexts | 68 |
| Scheduled fault slots | 2856 |
| Context replay stages | 2924 (68 x 43: 1 clean identity + 42 slots) |
| Event/control/rule/channel records | 171360 |
| Stratum rows | 1260 |
| Control/rule/channel summary rows | 60 |
| Unique realization hashes | 2151 |
| Alias variants | 773 |
| Null realizations | 197 |
| Effective fault slots | 2727 |
| Recorded run exit status | 0 |

<!-- validation-audit-20260919 -->
**Count identities.** The figures above are two distinct partitions of the same 2,924 context stages, plus a classification of the fault slots:

| identity | arithmetic |
| --- | --- |
| context stages = clean identity replays + scheduled fault slots | 2924 = 68 + 2856 |
| context stages = 68 contexts x 43 ordinals (0..42) | 2924 = 68 x 43 |
| context stages = alias variants + unique canonical realizations (a different partition) | 2924 = 773 + 2151 |
| unique canonical realizations = distinct realization hashes | 2151 = 2151 |
| fault slots = effective fault slots + null fault slots | 2856 = 2727 + 129 |
| null realizations = clean stages (null by definition) + null fault slots | 197 = 68 + 129 |
| effective fault slots = scheduled fault slots - null fault slots | 2727 = 2856 - 129 |
| clean stages are never effective | 0 = 0 |

Clean identity replays are **not** fault slots: each context contributes one clean replay (ordinal 0) plus 42 scheduled fault slots (ordinals 1-42). Aliases arise only among fault slots (773), never among clean stages (0). `null` and `effective` are exact complements on the 2,856 fault slots, and the 68 clean stages are null by definition.

## Fitting budget (authorized and actually spent)

| Operation | Count |
| --- | --- |
| cqr_wrapper_fit | 1 |
| quantile_estimator_fit | 3 |
| nested_calibrator_conformalize | 2 |
| logical_conformalizations | 1 |
| persistence_radius_computations | 1 |
| persistence_learned_fits | 0 |
| xgboost_fits | 0 |
| attention_lstm_fits | 0 |
| enbpi_fits | 0 |
| dscp_fits | 0 |
| tuning_runs | 0 |
| matched_forecast_refits | 0 |

Shared quantile owner `22ede7e8d7e32759...`, native estimator random states `42;42;42`, persistence radius 0.800 degC. Raw, static CQR and rolling CQR share the same fitted estimators.

## Detection versus workload (combined channel)

| Control | Rule | Detection | Restricted TTD (min) | Detected | Misses | Background episodes/asset-day | Fraction time in alert |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cqr_rolling | 180min_3of18 | 0.3751 | 81.2 | 1050 | 1677 | 0.9448 | 0.1857 |
| cqr_rolling | 30min_3of3 | 0.4174 | 77.4 | 1178 | 1549 | 1.2791 | 0.0589 |
| cqr_rolling | 360min_4of36 | 0.1974 | 96.1 | 555 | 2172 | 0.7704 | 0.2640 |
| cqr_rolling | 60min_4of6 | 0.3040 | 88.7 | 856 | 1871 | 0.8721 | 0.0759 |
| cqr_rolling | single_sample | 0.6967 | 46.5 | 1866 | 861 | 3.0815 | 0.0919 |
| cqr_static | 180min_3of18 | 0.1690 | 97.8 | 467 | 2260 | 0.5233 | 0.7574 |
| cqr_static | 30min_3of3 | 0.3327 | 91.0 | 932 | 1795 | 1.4971 | 0.6442 |
| cqr_static | 360min_4of36 | 0.1024 | 103.5 | 285 | 2442 | 0.2471 | 0.7975 |
| cqr_static | 60min_4of6 | 0.2509 | 97.4 | 706 | 2021 | 1.1192 | 0.6641 |
| cqr_static | single_sample | 0.4409 | 75.0 | 1204 | 1523 | 2.6599 | 0.6754 |
| persistence_static | 180min_3of18 | 0.5127 | 74.3 | 1412 | 1315 | 0.8140 | 0.0626 |
| persistence_static | 30min_3of3 | 0.1850 | 95.5 | 516 | 2211 | 0.1163 | 0.0008 |
| persistence_static | 360min_4of36 | 0.3702 | 84.0 | 1024 | 1703 | 0.6977 | 0.0999 |
| persistence_static | 60min_4of6 | 0.1804 | 97.6 | 504 | 2223 | 0.1017 | 0.0014 |
| persistence_static | single_sample | 0.9086 | 24.6 | 2466 | 261 | 4.2443 | 0.0348 |
| quantile_static | 180min_3of18 | 0.1076 | 102.0 | 290 | 2437 | 0.6541 | 0.8802 |
| quantile_static | 30min_3of3 | 0.3304 | 91.2 | 920 | 1807 | 1.5407 | 0.7323 |
| quantile_static | 360min_4of36 | 0.0687 | 105.3 | 186 | 2541 | 0.3779 | 0.9276 |
| quantile_static | 60min_4of6 | 0.2757 | 95.8 | 769 | 1958 | 1.1628 | 0.7528 |
| quantile_static | single_sample | 0.4274 | 78.0 | 1174 | 1553 | 4.0989 | 0.7760 |

Highest conditional-context detection in the combined channel: `persistence_static` / `single_sample` at 0.9086, with 4.2443 background episodes per asset-day.

Workload denominators use the entire declared clean stream, including the untiled tail rows, at 68.798611 asset-days over 9907 outer rows. Misses remain included in the restricted time-to-detection, which retains the declared restriction.

## Interval quality

| Scope | Control | Target | n | Coverage | MPIW (degC) | Winkler (degC) |
| --- | --- | --- | --- | --- | --- | --- |
| all_scheduled_fault_slots | cqr_rolling | clean_counterfactual | 411264.0 | 0.7440 | 7.708 | 23.797 |
| all_scheduled_fault_slots | cqr_rolling | corrupted_observation | 409194.0 | 0.7395 | 7.705 | 25.876 |
| all_scheduled_fault_slots | cqr_static | clean_counterfactual | 411264.0 | 0.3261 | 3.440 | 54.073 |
| all_scheduled_fault_slots | cqr_static | corrupted_observation | 409194.0 | 0.3277 | 3.441 | 56.236 |
| all_scheduled_fault_slots | persistence_static | clean_counterfactual | 411264.0 | 0.9470 | 1.600 | 7.153 |
| all_scheduled_fault_slots | persistence_static | corrupted_observation | 409194.0 | 0.9553 | 1.600 | 4.614 |
| all_scheduled_fault_slots | quantile_static | clean_counterfactual | 411264.0 | 0.2250 | 2.767 | 72.739 |
| all_scheduled_fault_slots | quantile_static | corrupted_observation | 409194.0 | 0.2270 | 2.767 | 74.738 |
| effective_fault_slots | cqr_rolling | clean_counterfactual | 392688.0 | 0.7437 | 7.713 | 23.831 |
| effective_fault_slots | cqr_rolling | corrupted_observation | 390618.0 | 0.7390 | 7.710 | 26.009 |
| effective_fault_slots | cqr_static | clean_counterfactual | 392688.0 | 0.3262 | 3.444 | 54.126 |
| effective_fault_slots | cqr_static | corrupted_observation | 390618.0 | 0.3278 | 3.445 | 56.392 |
| effective_fault_slots | persistence_static | clean_counterfactual | 392688.0 | 0.9462 | 1.600 | 7.400 |
| effective_fault_slots | persistence_static | corrupted_observation | 390618.0 | 0.9549 | 1.600 | 4.742 |
| effective_fault_slots | quantile_static | clean_counterfactual | 392688.0 | 0.2252 | 2.770 | 72.789 |
| effective_fault_slots | quantile_static | corrupted_observation | 390618.0 | 0.2273 | 2.771 | 74.883 |
| fullstream_clean | cqr_rolling | clean_counterfactual | 9907.0 | 0.9081 | 8.934 | 10.355 |
| fullstream_clean | cqr_rolling | corrupted_observation | 9907.0 | 0.9081 | 8.934 | 10.355 |
| fullstream_clean | cqr_static | clean_counterfactual | 9907.0 | 0.3246 | 3.343 | 53.474 |
| fullstream_clean | cqr_static | corrupted_observation | 9907.0 | 0.3246 | 3.343 | 53.474 |
| fullstream_clean | persistence_static | clean_counterfactual | 9907.0 | 0.9652 | 1.600 | 1.904 |
| fullstream_clean | persistence_static | corrupted_observation | 9907.0 | 0.9652 | 1.600 | 1.904 |
| fullstream_clean | quantile_static | clean_counterfactual | 9907.0 | 0.2240 | 2.669 | 72.177 |
| fullstream_clean | quantile_static | corrupted_observation | 9907.0 | 0.2240 | 2.669 | 72.177 |
| identity | cqr_rolling | clean_counterfactual | 9792.0 | 0.7478 | 7.572 | 22.914 |
| identity | cqr_rolling | corrupted_observation | 9792.0 | 0.7478 | 7.572 | 22.914 |
| identity | cqr_static | clean_counterfactual | 9792.0 | 0.3284 | 3.342 | 53.108 |
| identity | cqr_static | corrupted_observation | 9792.0 | 0.3284 | 3.342 | 53.108 |
| identity | persistence_static | clean_counterfactual | 9792.0 | 0.9648 | 1.600 | 1.908 |
| identity | persistence_static | corrupted_observation | 9792.0 | 0.9648 | 1.600 | 1.908 |
| identity | quantile_static | clean_counterfactual | 9792.0 | 0.2266 | 2.668 | 71.725 |
| identity | quantile_static | corrupted_observation | 9792.0 | 0.2266 | 2.668 | 71.725 |

<!-- validation-audit-20260919 -->
**Reading the coverage column against nominal 0.95.** Only `persistence_static` attains nominal coverage on the clean stream. The learned quantile controls do not:

| control | clean-stream coverage | reaches nominal 0.95 | shortfall | MPIW (degC) |
| --- | --- | --- | --- | --- |
| `persistence_static` | 0.9652 | yes | -0.0152 | 1.600 |
| `cqr_rolling` | 0.9081 | **no** | +0.0419 | 8.934 |
| `cqr_static` | 0.3246 | **no** | +0.6254 | 3.343 |
| `quantile_static` | 0.2240 | **no** | +0.7260 | 2.669 |

`cqr_rolling` narrows the shortfall relative to the static conformal controls but remains 0.0419 below nominal, at the widest interval of the four. It does not reach nominal coverage.

Leadership is also rule-dependent rather than uniform. At the immediate rule in the combined channel `persistence_static` detects most (0.9086) but raises MORE clean-stream episodes per asset-day than `cqr_rolling` (4.2443 versus 3.0815), and `cqr_rolling` leads detection at the 30- and 60-minute rules.

## Quantile-ordering warnings

The run log retains MAPIE `The predictions are ill-sorted.` messages. They were assessed against the saved artifacts rather than suppressed. In MAPIE 1.4.1 `_check_lower_upper_bounds` only emits a log record; it never sorts, clips or recalibrates. It fires when the lower bound exceeds the upper bound **or** when the median prediction leaves the band. Counts on the emitted streams:

| Control | Stages | Rows | Raw inversions | Emitted inversions | Median below lower | Median above upper | Min emitted width (degC) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cqr_rolling | 2152 | 319651 | 0 | 0 | 0 | 0 | 0.701355 |
| cqr_static | 2152 | 319651 | 0 | 0 | 611 | 0 | 1.018535 |
| persistence_static | 2152 | 319651 | 0 | 0 | 0 | 0 | 1.600000 |
| quantile_static | 2152 | 319651 | 0 | 0 | 631 | 1 | 0.344941 |

No emitted interval is inverted anywhere in the study, and the minimum emitted width is strictly positive for every control. The messages therefore reflect median/tail quantile crossing in a small minority of rows, which leaves interval endpoints correctly ordered and coverage and MPIW well defined. No sorting, clipping or recalibration was introduced, and the frozen protocol was not changed.

## Independent validation and zero-fit completed resume

- The frozen `validate` action **did not pass**. Attempt 1 aborted at `lower_context_3c2ed441cb78fe67ef35_v0`; the failed attempt and its log are preserved and no tolerance was loosened. See the full-extent survey below.
- Full-extent independent validation survey (frozen tolerance 1e-10 applied unchanged): 253938 checks, 1281 violating elements, maximum observed difference 4.946e-02 degC.

| Category | Violations |
| --- | --- |
| features | 0 (independent scalar reconstruction agrees within the frozen 1e-10) |
| observations | 0 |
| identity | 0 (saved feature_hash and observation_hash both match) |
| alert_outcome | 0 (alert flags and episode onsets reconstruct exactly) |
| event_outcome | 0 (event ledger completeness, event detection and censored delay reconstruct exactly) |
| estimand | 0 (equal-context denominators and equal-context recall reconstruct exactly) |
| workload_outcome | 0 (full clean-stream workload and original exposure reconstruct exactly) |
| update | 0 (pool_n, correction_lower, correction_upper and update status all match) |
| bounds | 1077 elements, max 0.04946 degC (quantile_static, cqr_static, cqr_rolling (lower/upper/raw_lower/raw_upper/point)) |
| release | 204 elements, max 0.01386 degC (released conformity score values only; identity and counts unaffected) |

**Corrected conclusion.** No scientific outcome differs. Every decision-relevant quantity -- alert flags, episode onsets, event detection, restricted delay, equal-context recall and full clean workload -- reconstructs exactly from an independent implementation. Discrepancies are confined to numeric interval bound and released-score values at gradient-boosting bin-boundary rows, with a maximum of 0.0495 degC on a target of roughly 25 degC. The study conclusions are unaffected.

persistence_static never appears among the violations, because it derives its interval from target_lag_0 rather than from the binned gradient-boosting estimators. This is direct confirmation of the bin-boundary mechanism.

A computed string in the raw survey file reads "SCIENTIFIC OUTCOME DIFFERS - investigate". That string is incorrect and is a defect in the survey's own reporting logic, not a finding: The survey counted the "release" kind as a scientific outcome. Its 204 violations are numeric released conformity SCORE values. The release semantics that actually matter -- release identity (row_id and released_at_origin), release counts, update counts and update status -- recorded ZERO violations. The raw file is preserved unmodified and `VALIDATION_SURVEY_CORRECTED_READING.json` records this correction.

<!-- validation-audit-20260919 -->
**Audit outcome (2026-09-19).** The failure mechanism is proven at node level: a 145-row, 98-stage sensitivity, every case attributable to a gradient-boosting split threshold that a feature value sits exactly on. A candidate representation-compatible contract passed across the complete pilot (271920 assertions, 0 violations) with scientific artifacts unchanged, and was verified to reject feature, model, prediction, interval, rolling-update, released-score and alert corruption. The candidate is proposed, NOT adopted; the frozen gate remains unmet.
**Unresolved.** The frozen `validate` action still cannot produce a PASS receipt, because it demands bit-level agreement of a discontinuous model under a 1-2 ULP input perturbation. Whether to repair the validator (compare saved bounds against the saved, independently verified features) via the existing validation_source_compatibility mechanism is a decision for the researcher.
- Completed resume: models fitted 0, calibrators fitted 0, replay updates 0, scientific artifacts unchanged True.

## Measured cost and its limits

- Measured stage CPU: 1502.83 s across 2929 stages.
- Measured stage wall: 1541.49 s.
- Measured peak RSS: 660733952 bytes (630.1 MiB).
- Atomic-rename denials retried to success: 58; recovered ready stages: 0.

- The original 2026-09-18 attempt was interrupted without an exit receipt; its wall time is bounded by journal timestamps only and its terminal exit status is unknown.
- Stage-level CPU and RSS are measured inside the worker by the engine PhaseMeter and cover both the original and the resumed attempt, because completed stage records are preserved.
- Peak RSS is the maximum lifetime peak recorded across completed stages, not a continuous sample of the whole process lifetime.
- Coordinator heartbeat worker CPU under-reports: it latched onto the venv redirector stub for the resumed run phase. The independent liveness probe records the real worker.

Per-attempt coordinator phases:

| Phase | Exit status | Finished (UTC) |
| --- | --- | --- |
| run_resume | 0 | 2026-09-18T17:34:39.607643+00:00 |
| validate | 1 | 2026-09-18T18:02:19.033199+00:00 |
| completed_resume | 0 | 2026-09-18T18:50:50.880694+00:00 |
| analysis | 1 | 2026-09-18T18:53:23.631602+00:00 |

## Inference status

Single model seed: population intervals are unavailable by design. No energy bound is transferred to temperature. Engine inference status: `unavailable_incomplete_model_seeds`. Control/rule/channel macro statuses: {"supported_point_estimate": 60}.

## Scope accounting

Matched forecasting units remain 70/195, matched interval-method cells 250/1950, unique seasonal computations 9/27. This conditional-context pilot is separately identified evidence and fills none of those cells. Full-study readiness remains false.

Packaged raw evidence: 10 parts, 127162 verified members, 127162 raw files, 549321115 bytes total (0.512 GiB).
