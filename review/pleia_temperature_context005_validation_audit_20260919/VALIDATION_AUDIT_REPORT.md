# PLEIA-temperature context005 seed-42 pilot: validation audit

Audit branch `review/pleia-temperature-context005-validation-audit-20260919`, a descendant of the delivered pilot branch `review/pleia-temperature-context005-pilot-20260918`.

- Pilot primary results: `31fdacbb29ef70bbb297cfe52d9fbf91fb789038`
- Pilot final delivery: `571408be0b51e81c6987306a292afc7fcae2ff94`
- Recorded main (unchanged): `06fe967be2be8d7898812c0c2d6e464d4e942351`

## 1. Acceptance status

**Execution and publication complete; scientific acceptance pending validation.**

Publication and scientific validation are separate. Publication is verified: 10 published artifacts were downloaded over HTTPS from `raw.githubusercontent.com` pinned to their commit SHAs and compared against the committed git blobs; all were byte-identical (`passed = True`). Scientific validation is NOT established: the frozen `validate` action failed on attempt 1 and has not been made to pass. That original failure is preserved and is not relabelled here.

## 2. The mechanism: proven, not inferred

The engine computes causal features with vectorised pandas operations; the frozen validator reconstructs them scalar-wise. On the stage where attempt 1 aborted (`context_3c2ed441cb78fe67ef35_v0`) the two representations agree to 1.776e-14, inside the unchanged frozen feature tolerance of 1e-10 (`within_frozen_tolerance = True`).

The largest single difference is on `target_rollmean_144` at row 120: engine `25.445833333333336` versus validator `25.44583333333332`, a gap of 1.776e-14, which is **5 ULP** of that value. This is floating-point summation-order noise, not a difference in the causal construction.

### Feature identity, order and dtype

- Columns: 29; order identical in both representations: True.
- Reconstructed dtypes: ['float64']; saved dtypes: ['float64', 'int64']. (The saved frame additionally carries an integer column; the model receives the same float64 matrix in both cases.)

### The routing difference, at node level

At predict time a `HistGradientBoostingRegressor` compares the **raw** feature value against each tree node's `num_threshold`. The audit walks the serialized trees node by node for both representations. The manual walk reproduces `sklearn`'s own `predict` exactly in every case checked, so the routing evidence is trustworthy.

| estimator | row | feature | `num_threshold` | engine value | validator value | boosting stages diverging | prediction delta (degC) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q=0.025 | 100 | `target_rollmean_6` | `23.2` | `23.2` | `23.200000000000003` | 1 of 215 | 4.031e-04 |
| q=0.975 | 84 | `target_rollmean_6` | `23.299999999999997` | `23.3` | `23.299999999999997` | 1 of 216 | 1.310e-03 |
| q=0.975 | 100 | `target_rollmean_6` | `23.2` | `23.2` | `23.200000000000003` | 1 of 216 | 5.913e-03 |

In each case the feature value sits **exactly on** the split threshold for one of the two representations, so `v <= threshold` is decided by the last bit. Exactly one boosted stage diverges, and the prediction delta equals that single leaf-value delta.

### Why this feature, and why this dataset

The mechanism is not a coincidence; it is predictable from the data. The raw PLEIA temperature target is recorded at 0.1 degC resolution (186 distinct values). `target_rollmean_6` averages six such values and therefore lands on a coarse lattice with only 2126 distinct values. Split thresholds are learned from that same lattice, so **170 of 183 (92.9%) of the split thresholds on this feature are exactly equal to an observed feature value**, and 13.21% of feature rows sit exactly on some threshold.

By contrast `target_rollmean_144` has 23858 distinct values (a much finer lattice) and never carries a flip, despite having the LARGER reconstruction difference. `target_lag_0`, which `persistence_static` uses, is a direct lookup with no summation and has zero reconstruction difference. That is why persistence is immune — supporting evidence that now has a mechanism behind it rather than standing alone.

### Does the mechanism explain every violation?

Across the complete pilot the audit located every variant whose two representations produce a different prediction: **98 stages, 145 rows** (0.04681% of the 2151 x 144 unique rows). Each was attributed by walking the trees.

- Row-cases fully explained by a split-threshold straddle: **145 of 145**.
- Unexplained discrepancies: **0**.
- Every one of the 219 divergence events is carried by a single feature, `target_rollmean_6`; per-estimator split {'q_index_1': 171, 'q_index_0': 47, 'q_index_2': 1}.

The mechanism therefore explains **all** observed discrepancy, with no unexplained residue.

## 3. Audit of the original survey and its corrected interpretation

The original survey reported 253938 checks and 1281 violating elements (1077 bounds, 204 released-score).

### Assertion coverage reconstructed independently

Absence of recorded violations is not coverage. The audit reconstructs the survey's assertion count analytically from the design, and it matches exactly:

| term | value |
| --- | --- |
| per-variant checks (5 x 2924) | 14620 |
| per-unique-canonical checks (110 x 2151) | 236610 |
|   static control (5 bounds + 2 release + 20 alert) | 27 |
|   rolling control (5 bounds + 2 release + 2 update + 20 alert) | 29 |
| aggregate event (ledger, detection, censored delay) | 3 |
| aggregate strata (1260 rows x 2) | 2520 |
| aggregate fullstream (1 stage x 65) | 65 |
| aggregate exposure (60 groups x 2) | 120 |
| **analytic total** | **253938** |
| survey reported | 253938 |
| match | True |

Skipped checks are accounted for explicitly rather than silently: the three static controls have zero rolling-update rows, so their `update` assertions do not execute ({'quantile_static': 0, 'cqr_static': 0, 'cqr_rolling': 6, 'persistence_static': 0}). Only `cqr_rolling` carries updates.

### Rolling numerical state was verified, with denominators

Unchanged release identity and update counts would NOT establish that rolling calibration state is unchanged. The state numbers themselves were compared:

- `C_rolling_state` (pool_n, correction_lower, correction_upper): 2151 assertions over 38718 compared numbers, 0 violations.
- `C_released_scores`: 8604 assertions over 1225212 scores, 0 violations.
- `C_update_status`: 2151 assertions, 0 violations.

Propagation was traced directly: a released-score difference can only move a later bound through the rolling correction, and the corrections are numerically identical everywhere. On the attempt-1 stage the bound differences remain confined to the same two rows as the prediction differences, with no downstream drift.

### The original "SCIENTIFIC OUTCOME DIFFERS" string

That string is retained in the raw survey output and is **incorrect**. It was produced by the survey's own classification, which counted the `release` kind as a scientific outcome when its violations are released conformity SCORE VALUES. The release semantics that carry meaning — release identity, release counts, update counts, update status — recorded zero violations. `VALIDATION_SURVEY_CORRECTED_READING.json` records this, and this audit confirms it independently.

**Which numerical quantities differ:** interval bound values and released conformity score values, at rows where a feature sits on a split threshold.

**Which evaluated endpoints agree:** alert flags, episode onsets, event-ledger completeness, event detection, restricted/censored delay, equal-context denominators, equal-context recall, full clean-stream workload and original exposure.

## 4. Candidate validation result

The candidate contract (see `CANDIDATE_VALIDATION_CONTRACT.md`) was run across the complete existing pilot with fits forbidden and no scientific output mutated:

- **271920 assertions** over **21012059 compared elements**
- **0 violations**; `passed = True`
- maximum observed difference 3.908e-14 (feature provenance, inside the unchanged 1e-10)
- scientific artifacts unchanged before/after: `True`
- cost: 6308 s wall, 5297 s CPU, 833.8 MiB peak RSS

| contract layer | assertions | elements | violations |
| --- | --- | --- | --- |
| `A_alias` | 773 | 773 | 0 |
| `A_availability` | 2924 | 2924 | 0 |
| `A_feature_provenance` | 2925 | 12497927 | 0 |
| `A_identity` | 5848 | 5848 | 0 |
| `A_observations` | 2924 | 421056 | 0 |
| `B_model_application` | 25812 | 3716928 | 0 |
| `C_alert_flags` | 129060 | 129060 | 0 |
| `C_censored_delay` | 1 | 171360 | 0 |
| `C_episode_onsets` | 43020 | 43020 | 0 |
| `C_equal_context_denominator` | 1260 | 1260 | 0 |
| `C_equal_context_recall` | 1260 | 1260 | 0 |
| `C_event_detection` | 1 | 171360 | 0 |
| `C_event_ledger` | 1 | 1 | 0 |
| `C_full_exposure` | 120 | 120 | 0 |
| `C_interval_construction` | 17212 | 2557208 | 0 |
| `C_release_count` | 8604 | 8604 | 0 |
| `C_release_identity` | 8604 | 8604 | 0 |
| `C_released_scores` | 8604 | 1225212 | 0 |
| `C_rolling_state` | 2151 | 38718 | 0 |
| `C_update_count` | 8604 | 8604 | 0 |
| `C_update_status` | 2151 | 2151 | 0 |
| `C_workload` | 60 | 60 | 0 |
| `integrity` | 1 | 1 | 0 |

## 5. Focused tests

9 of 9 passed (`all_ok = True`). Each test runs the real candidate code path against a disposable sandbox copy; the genuine artifacts are never written to.

| test | expected | observed | detected by |
| --- | --- | --- | --- |
| `accept_unmodified` | pass | pass | - |
| `reject_feature_corruption` | reject | reject | A_feature_provenance;A_identity |
| `reject_observation_corruption` | reject | reject | A_observations |
| `reject_prediction_corruption` | reject | reject | B_model_application |
| `reject_interval_corruption` | reject | reject | C_interval_construction |
| `reject_causal_update_corruption` | reject | reject | C_rolling_state |
| `reject_alert_flag_corruption` | reject | reject | C_alert_flags |
| `reject_released_score_corruption` | reject | reject | C_released_scores |
| `reject_model_corruption` | reject | reject | B_model_application;C_interval_construction;C_released_scores |

The candidate is therefore not vacuous: it rejects feature, observation, model, prediction, interval, rolling-update, released-score and alert corruption.

## 6. Count reconciliation

The pilot report lists several counts without stating how they relate. They are two distinct partitions of the same 2,924 context stages, plus a classification of the fault slots.

| identity | arithmetic | holds |
| --- | --- | --- |
| context stages = clean identity replays + scheduled fault slots | 2924 = 68 + 2856 | True |
| context stages = 68 contexts x 43 ordinals (0..42) | 2924 = 68 x 43 | True |
| context stages = alias variants + unique canonical realizations (a different partition) | 2924 = 773 + 2151 | True |
| unique canonical realizations = distinct realization hashes | 2151 = 2151 | True |
| fault slots = effective fault slots + null fault slots | 2856 = 2727 + 129 | True |
| null realizations = clean stages (null by definition) + null fault slots | 197 = 68 + 129 | True |
| effective fault slots = scheduled fault slots - null fault slots | 2727 = 2856 - 129 | True |
| clean stages are never effective | 0 = 0 | True |

- **Clean stages are not fault slots.** Each context contributes one clean identity replay (ordinal 0) plus 42 scheduled fault slots (ordinals 1-42).
- Aliases occur only among fault slots (773), never among clean stages (0): each context's clean replay is a distinct realization.
- `null` and `effective` are exact complements **on fault slots**; clean stages are null by definition and are never effective.

## 7. Preservation

No scientific artifact was modified by this audit. The candidate validator recorded the run directory file tree before and after its full pass and they are identical (`artifacts_unchanged = True`). The frozen `src` tree is untouched, so the source hash that the completed energy study also depends on is intact.
