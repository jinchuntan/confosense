# Support-design audit: amendment-005 decision evidence

13 September 2026. **No model fitting.** Entry is `9b5acb49531ce12706285c3f040310c0ab6053dd`; the unchanged production source hash is `203f3babf66c98ac072ad450abec5ea7ce3d60473f02708fa64ac2102ea3f7c9`. The completed BDG2 three-fold benchmark and forecasting pilot are preserved. This audit uses structural information, observed signal changes and measured costs; prediction-performance values did not select the proposed design.

**Decision:** retain amendment 004 as the fixed-incidence operational benchmark. Add a separately named **effective-fault conditional context challenge** for PLEIA temperature, PLEIA energy and RICO. Forecasting and own-model interval/compute evaluation remain supported independently of sparse event incidence. RICO needs separately versioned chronological whole-run batches for useful multi-run evaluation. None of this reverses BDG2's three primary abstentions.

The [evidence index](review/support_design_20260913/EVIDENCE_INDEX.md) gives exact table paths, source archives and commands. [AMENDMENT005_PROPOSAL.md](AMENDMENT005_PROPOSAL.md) defines the recommendation; [REMAINING_STUDY_EXECUTION_PLAN.md](REMAINING_STUDY_EXECUTION_PLAN.md) gives the executable queue and missing entrypoint contract.

## Exposure and original units

| dataset | primary_horizon | frequency_minutes | original_rows | eligible_rows | groups | segments | asset_days | all_eligible_five_catalogue_bound |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 1 | 10 | 50543 | 49535 | 1 | 1 | 343.993 | 860 |
| pleia_energy | 1 | 10 | 50545 | 49537 | 1 | 1 | 344.007 | 860 |
| rico | 5 | 1 | 49680 | 45747 | 207 | 207 | 31.7688 | 80 |
| bdg2 | 1 | 60 | 175440 | 173352 | 10 | 40 | 7223 | 18060 |


PLEIA temperature retains block B, room 11, variable V2; energy retains block B `dif_cons` in kWh per ten-minute interval. Each is one original series, not dozens of independent buildings. RICO retains `B.RTD3`, 207 four-hour runs and 49,680 raw minute observations; 45,747 remain eligible at its primary five-minute horizon (221 per run). The local 287 scheduler candidates include 80 excluded by the source quality flags. BDG2 retains ten buildings and hourly kWh targets. See the [target/group inventory](smart_building_conformal/outputs/amendment005/support_design_v1/original_groups.csv) and [RICO source run audit](smart_building_conformal/outputs/amendment005/support_design_v1/rico_source_run_audit.csv).

All 117 current unsupported-task role hashes match the published preflight. The detailed [role table](smart_building_conformal/outputs/amendment005/support_design_v1/current_roles.csv) includes training/calibration counts, physical frequency/horizon, contiguous segments, eligible onset positions, guarded placement capacity, exact dates and original exposure. The current selection/test roles are:

| dataset | outer_fold | role | target_min | target_max | n | asset_days | groups | segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 0 | outer_test | 2021-10-10 04:50:00 | 2021-12-17 23:50:00 | 9907 | 68.7986 | 1 | 1 |
| pleia | 0 | inner0_selection | 2021-04-21 04:40:00 | 2021-06-11 18:40:00 | 7429 | 51.5903 | 1 | 1 |
| pleia | 0 | inner1_selection | 2021-06-11 19:00:00 | 2021-08-02 09:10:00 | 7430 | 51.5972 | 1 | 1 |
| pleia | 1 | outer_test | 2021-08-02 09:40:00 | 2021-10-10 04:40:00 | 9907 | 68.7986 | 1 | 1 |
| pleia | 1 | inner0_selection | 2021-03-26 09:30:00 | 2021-05-04 01:50:00 | 5571 | 38.6875 | 1 | 1 |
| pleia | 1 | inner1_selection | 2021-05-04 02:10:00 | 2021-06-11 18:50:00 | 5573 | 38.7014 | 1 | 1 |
| pleia | 2 | outer_test | 2021-05-25 14:30:00 | 2021-08-02 09:30:00 | 9907 | 68.7986 | 1 | 1 |
| pleia | 2 | inner0_selection | 2021-02-28 14:20:00 | 2021-03-26 09:00:00 | 3713 | 25.7847 | 1 | 1 |
| pleia | 2 | inner1_selection | 2021-03-26 09:20:00 | 2021-04-21 04:20:00 | 3715 | 25.7986 | 1 | 1 |
| pleia_energy | 0 | outer_test | 2021-10-10 04:40:00 | 2021-12-18 00:00:00 | 9909 | 68.8125 | 1 | 1 |
| pleia_energy | 0 | inner0_selection | 2021-04-21 04:30:00 | 2021-06-11 18:30:00 | 7429 | 51.5903 | 1 | 1 |
| pleia_energy | 0 | inner1_selection | 2021-06-11 18:50:00 | 2021-08-02 09:00:00 | 7430 | 51.5972 | 1 | 1 |
| pleia_energy | 1 | outer_test | 2021-08-02 09:30:00 | 2021-10-10 04:30:00 | 9907 | 68.7986 | 1 | 1 |
| pleia_energy | 1 | inner0_selection | 2021-03-26 09:20:00 | 2021-05-04 01:40:00 | 5571 | 38.6875 | 1 | 1 |
| pleia_energy | 1 | inner1_selection | 2021-05-04 02:00:00 | 2021-06-11 18:40:00 | 5573 | 38.7014 | 1 | 1 |
| pleia_energy | 2 | outer_test | 2021-05-25 14:20:00 | 2021-08-02 09:20:00 | 9907 | 68.7986 | 1 | 1 |
| pleia_energy | 2 | inner0_selection | 2021-02-28 14:10:00 | 2021-03-26 08:50:00 | 3713 | 25.7847 | 1 | 1 |
| pleia_energy | 2 | inner1_selection | 2021-03-26 09:10:00 | 2021-04-21 04:10:00 | 3715 | 25.7986 | 1 | 1 |
| rico | 0 | outer_test | 2024-05-18 03:20:00 | 2024-05-18 07:00:00 | 221 | 0.153472 | 1 | 1 |
| rico | 0 | inner0_selection | 2023-08-11 03:20:00 | 2024-02-03 03:00:00 | 8398 | 5.83194 | 38 | 38 |
| rico | 0 | inner1_selection | 2024-02-03 03:20:00 | 2024-05-09 11:00:00 | 8619 | 5.98542 | 39 | 39 |
| rico | 1 | outer_test | 2024-05-17 23:20:00 | 2024-05-18 03:00:00 | 221 | 0.153472 | 1 | 1 |
| rico | 1 | inner0_selection | 2023-08-10 23:20:00 | 2024-02-02 23:00:00 | 8398 | 5.83194 | 38 | 38 |
| rico | 1 | inner1_selection | 2024-02-02 23:20:00 | 2024-05-09 07:00:00 | 8619 | 5.98542 | 39 | 39 |
| rico | 2 | outer_test | 2024-05-17 19:20:00 | 2024-05-17 23:00:00 | 221 | 0.153472 | 1 | 1 |
| rico | 2 | inner0_selection | 2023-08-10 23:20:00 | 2024-02-02 23:00:00 | 8398 | 5.83194 | 38 | 38 |
| rico | 2 | inner1_selection | 2024-02-02 23:20:00 | 2024-05-09 07:00:00 | 8619 | 5.98542 | 39 | 39 |


## Count, allocation, null, placement and inference mechanisms

The exact request is `floor(0.5 * eligible_asset_days + 0.5)` **per catalogue**. Five catalogues share the same real exposure. At least 105 effective instances are necessary for five distinct onsets in all 21 strata, but duplicates, nulls, distribution and confidence-bound support can still fail. The count-only exposure minimum for five catalogues is **41 eligible asset-days**, since that first produces 21 requests per catalogue. This is a project gate, not a conformal theorem.

| dataset | outer_fold | role | requested_per_catalogue | requested | placed | effective_events | null | rejected | minimum_distinct_onsets | supported_strata | faulted_original_groups |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 0 | outer_test | 34 | 170 | 170 | 162 | 8 | 0 | 5 | 21 | 1 |
| pleia | 0 | inner0_selection | 26 | 130 | 130 | 124 | 6 | 0 | 2 | 20 | 1 |
| pleia | 0 | inner1_selection | 26 | 130 | 130 | 123 | 7 | 0 | 3 | 20 | 1 |
| pleia | 1 | outer_test | 34 | 170 | 170 | 163 | 7 | 0 | 2 | 20 | 1 |
| pleia | 1 | inner0_selection | 19 | 95 | 95 | 93 | 2 | 0 | 2 | 15 | 1 |
| pleia | 1 | inner1_selection | 19 | 95 | 95 | 93 | 2 | 0 | 1 | 15 | 1 |
| pleia | 2 | outer_test | 34 | 170 | 170 | 164 | 6 | 0 | 2 | 20 | 1 |
| pleia | 2 | inner0_selection | 13 | 65 | 65 | 64 | 1 | 0 | 0 | 9 | 1 |
| pleia | 2 | inner1_selection | 13 | 65 | 65 | 64 | 1 | 0 | 0 | 9 | 1 |
| pleia_energy | 0 | outer_test | 34 | 170 | 170 | 164 | 6 | 0 | 4 | 19 | 1 |
| pleia_energy | 0 | inner0_selection | 26 | 130 | 130 | 123 | 7 | 0 | 2 | 20 | 1 |
| pleia_energy | 0 | inner1_selection | 26 | 130 | 130 | 125 | 5 | 0 | 2 | 20 | 1 |
| pleia_energy | 1 | outer_test | 34 | 170 | 170 | 159 | 11 | 0 | 3 | 19 | 1 |
| pleia_energy | 1 | inner0_selection | 19 | 95 | 95 | 92 | 3 | 0 | 2 | 14 | 1 |
| pleia_energy | 1 | inner1_selection | 19 | 95 | 95 | 93 | 2 | 0 | 2 | 14 | 1 |
| pleia_energy | 2 | outer_test | 34 | 170 | 170 | 164 | 6 | 0 | 1 | 20 | 1 |
| pleia_energy | 2 | inner0_selection | 13 | 65 | 65 | 64 | 1 | 0 | 0 | 9 | 1 |
| pleia_energy | 2 | inner1_selection | 13 | 65 | 65 | 64 | 1 | 0 | 0 | 9 | 1 |
| rico | 0 | outer_test | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rico | 0 | inner0_selection | 3 | 15 | 15 | 15 | 0 | 0 | 0 | 0 | 3 |
| rico | 0 | inner1_selection | 3 | 15 | 15 | 15 | 0 | 0 | 0 | 0 | 3 |
| rico | 1 | outer_test | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rico | 1 | inner0_selection | 3 | 15 | 15 | 14 | 1 | 0 | 0 | 0 | 3 |
| rico | 1 | inner1_selection | 3 | 15 | 15 | 15 | 0 | 0 | 0 | 0 | 3 |
| rico | 2 | outer_test | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rico | 2 | inner0_selection | 3 | 15 | 15 | 14 | 1 | 0 | 0 | 0 | 3 |
| rico | 2 | inner1_selection | 3 | 15 | 15 | 15 | 0 | 0 | 0 | 0 | 3 |


All current requested events were hostable and placed: **zero placement rejections**. Thus the observed shortfalls are not hidden failures to place requests. Hostable requests, candidate onset capacity and complete family/severity counts are published separately. The [567 current stratum rows](smart_building_conformal/outputs/amendment005/support_design_v1/current_strata.csv) retain requested/placed/effective/null/rejected counts and distinct original onsets.

For both PLEIA tasks, earliest inner blocks have about 25.8 days, 13 requests each and 65 per five-catalogue bank: impossible even before nulls. Middle blocks have about 38.7 days, 19 each and 95 total: also impossible. Latest inner blocks have about 51.6 days, 26 each and 130 total: arithmetically possible, but only 20/21 strata pass. Their limiting low-severity random-missing stratum has only 2–3 distinct effective onsets. Every current PLEIA inner bank therefore fails the full gate. PLEIA temperature outer fold 0 alone has full structural event support; its unsupported inner selection still prevents primary selection. Other PLEIA outer banks support many stratum point estimates but fail the declared five-onset gate in one or two strata; absence and insufficient precision are distinguished in the tables.

The deterministic rule is exactly `STRATA[(event_number + rotation) % 21]`, with rotations 0–4. A 13-request catalogue bank can request only indices 0–16: `level_shift` severity 2 and all three `drift` severities are absent before any realization. With 19 requests all strata occur, but the minimum request count is only three. With 26 requests the request minimum is five. RICO's three-request bank can request only indices 0–6, leaving 14 strata unrequested; a null can increase the number of missing effective strata. These are design limitations consistent with the existing implementation, not a demonstrated mismatch to its five-rotation specification. A complete set of 21 rotations allocates exactly q requests to every stratum for any q.

PLEIA's one-hour envelope has six samples. For random-missing severities 0.5/1/2, null probabilities are `0.9^6=0.531441`, `0.8^6=0.262144`, and `0.6^6=0.046656`. A low-severity positive schedule therefore often changes nothing. Those schedules remain null and never become positives. Stuck/dropout may also be null on an already constant/zero signal; the per-stratum records preserve those cases. RICO's 60-sample envelope has low-severity random-missing null probability `0.9^60=0.00179701`; its fundamental problem is exposure/allocation, not that probability.

RICO's current inner banks span 38–39 runs and 5.83–5.99 eligible days: three requests per catalogue and at most 15 total. Equal per-run exposure and stable largest-remainder ties repeatedly assign the three requests to the same three runs. More catalogues alone would not create new original runs. Each outer role is a single run: 221 minutes = 0.153472 days, zero requests and only one run for inference. Injected-event recall is unavailable there; a descriptive clean workload/forecast error is still measurable for that run.

Even using **all** RICO data as evaluation, with no training or calibration, the eligible exposure is **31.76875 days**, yielding 16 requests per catalogue and only **80** across five. Even the optimistic raw exposure, 34.5 days, yields only **85** requests. Rearranging subsets cannot fix this unchanged five-catalogue count design. At least 59,040 eligible minute rows are needed to reach the count-only 41-day bound: **13,293 more eligible minutes, or at least 61 additional comparable 221-minute eligible runs**, with separate training/calibration data still required. That bound does not guarantee effective events, representativeness or precise bounds.

Initial finite-rank support is not the cause of the current sparse-event failure: all summarized initial rank checks pass (`True`), with at least 400 calibration rows. Online support is method/level/window specific: signed-tail EnbPI with a 200-score window cannot support 99.5% tails, whereas one-sided CQR has a different finite-rank condition. The [rank table](smart_building_conformal/outputs/amendment005/support_final_checks_v1/rank_support_verified.csv) keeps these mechanisms separate. RICO's inner original-unit counts exceed five but its outer count is one; PLEIA's declared time blocks are not independent buildings and do not guarantee a precise CI.

## Three explicit alternatives

| Choice | What it can estimate | Structural evidence and trade-off | Decision |
|---|---|---|---|
| A: unchanged amendment 004 | Forecast/interval quality and original-exposure clean workload; stratum recall where effective events exist; full operational selection only with both supported inner banks | All 18 unsupported-task inner banks fail; RICO outer recall has no events. PLEIA temperature outer 0 support alone is insufficient for nested selection. | Preserve and label limitations; no reinterpretation of old results. |
| B: larger blocks / fixed additional catalogues | Same incidence/stratum estimand if fully supported; additional simulation precision only | Exposure minimum 41 days per evaluated bank is optimistic. Larger PLEIA selection blocks take observations from fitting/calibration; RICO total-data bound remains below 105. | Not the recommended immediate evaluation; count analysis is not demonstrated precision. |
| C: separate balanced challenge | Detection conditional on effective declared fault/context, per-stratum and full named conditional macro; paired clean workload separately | Concrete contexts and finite masks support all 567 role/stratum cells; no prevalence, real precision or deployment-feasibility claim follows. | Recommended supplement, with the versioned memberships below. |

For B, a concrete PLEIA 10%/10%/40%/40% division of the existing final fitting pool creates earliest selection blocks of 5,942/5,944 rows (41.264/41.278 days), meeting the count-only bound. Initial training falls to **1,484 rows**, versus about 3,714 in the equal-quarter design; calibration has 1,485 rows. Final reserved calibration stays 4,954 rows. This does not resolve the 53% null probability or prove a good predictor. Middle/later blocks grow to about 61.9/82.6 days. [Exact B boundaries and sizes](smart_building_conformal/outputs/amendment005/study_plan_v1/alternative_B_larger_blocks.csv) document the trade-off without fitting.

A fixed B simulation budget can be derived in advance: under the random-missing-mask model alone, require probability at least .95 of at least five effective masks per stratum. The minimum number of requests is **17** for PLEIA and **5** for RICO. Require complete 21-rotation cycles, `K=21*ceil(n_required/q)`. Current PLEIA earliest banks need 42 catalogues; middle/later/outer banks need 21. Current RICO inner banks need 42; zero-request outer banks admit no finite K. Proposed batched RICO inner banks need 63–105 catalogues under this bound. Rotate largest-remainder ties too if broader run coverage is intended. Freeze K before any generation, stop at K whether successful or not, never redraw nulls or add catalogues until a model passes. The criterion covers only random masks, not other nulls, distinct onsets, independent units or performance-bound precision. No B performance run or expanded catalogue bank was launched.

## Demonstrated support for C and remaining precision limits

| dataset | outer_fold | role | contexts | effective_variants | null_variants | minimum_effective_onsets | supported_strata | complete_original_inference_blocks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pleia | 0 | inner0_selection | 51 | 2045 | 97 | 33 | 21 | 7 |
| pleia | 0 | inner1_selection | 51 | 2040 | 102 | 28 | 21 | 7 |
| pleia | 0 | outer_test | 68 | 2691 | 165 | 51 | 21 | 9 |
| pleia | 1 | inner0_selection | 38 | 1522 | 74 | 23 | 21 | 5 |
| pleia | 1 | inner1_selection | 38 | 1545 | 51 | 30 | 21 | 5 |
| pleia | 1 | outer_test | 68 | 2718 | 138 | 52 | 21 | 9 |
| pleia | 2 | inner0_selection | 25 | 998 | 52 | 19 | 21 | 3 |
| pleia | 2 | inner1_selection | 25 | 1003 | 47 | 19 | 21 | 3 |
| pleia | 2 | outer_test | 68 | 2727 | 129 | 46 | 21 | 9 |
| pleia_energy | 0 | inner0_selection | 51 | 2045 | 97 | 29 | 21 | 7 |
| pleia_energy | 0 | inner1_selection | 51 | 2051 | 91 | 34 | 21 | 7 |
| pleia_energy | 0 | outer_test | 68 | 2722 | 134 | 50 | 21 | 9 |
| pleia_energy | 1 | inner0_selection | 38 | 1521 | 75 | 25 | 21 | 5 |
| pleia_energy | 1 | inner1_selection | 38 | 1533 | 63 | 27 | 21 | 5 |
| pleia_energy | 1 | outer_test | 68 | 2692 | 164 | 42 | 21 | 9 |
| pleia_energy | 2 | inner0_selection | 25 | 1005 | 45 | 18 | 21 | 3 |
| pleia_energy | 2 | inner1_selection | 25 | 1009 | 41 | 20 | 21 | 3 |
| pleia_energy | 2 | outer_test | 68 | 2742 | 114 | 50 | 21 | 9 |
| rico | 0 | inner0_selection | 31 | 1290 | 12 | 26 | 21 | 31 |
| rico | 0 | inner1_selection | 31 | 1288 | 14 | 27 | 21 | 31 |
| rico | 0 | outer_test | 43 | 1796 | 10 | 38 | 21 | 43 |
| rico | 1 | inner0_selection | 23 | 956 | 10 | 21 | 21 | 23 |
| rico | 1 | inner1_selection | 23 | 960 | 6 | 20 | 21 | 23 |
| rico | 1 | outer_test | 41 | 1702 | 20 | 36 | 21 | 41 |
| rico | 2 | inner0_selection | 15 | 612 | 18 | 11 | 21 | 15 |
| rico | 2 | inner1_selection | 16 | 664 | 8 | 13 | 21 | 16 |
| rico | 2 | outer_test | 41 | 1705 | 17 | 36 | 21 | 41 |


There are **1,128 role-specific contexts / 47,376 scheduled variants**, not 47,376 independent observations. Inner roles and historical folds reuse observations; only distinct outer periods/runs contribute to final outer summaries. Each PLEIA task has 204 outer daily contexts across three disjoint periods; RICO has 125 distinct proposed outer runs. All 567 role/stratum cells have at least five distinct effective contexts, with minimums 19 for temperature, 18 for energy and 11 for RICO. Deterministic duplicate realizations across the two sign slots are recorded as aliases; support uses distinct contexts and onsets, not variant row counts.

For PLEIA uncertainty, keep seven adjacent daily contexts together and never join across a gap or fold. Earliest inner banks have only three complete seven-day blocks: a five-block precision screen fails even though conditional point recall is structurally estimable. Middle/later inner banks have five/seven and each outer bank nine. RICO resamples whole runs, stratified by represented acquisition phase, retaining all variants, methods and model seeds together; phase/run dependence remains an assumption. No CI precision was measured. The often-used independent-Bernoulli approximation would need about 97 independent units for a worst-case 95% half-width of 0.10; it is only a planning heuristic and is not a power claim for these dependent contexts.

The smallest precision diagnostic after streams exist is one fixed 2,000-draw paired original-unit analysis per required endpoint, seed 20240601, at least 1,900 valid nondegenerate draws. If a required stratum is absent or only a few independent blocks are defensible, report the CI unavailable. Do not expand draws/contexts in response to favourable or disappointing model results.

## Verification and interpretation

The generator exited 0 with zero fits. Six focused tests passed; independent reconstruction verified all 47,376 masks/changes/null statuses, 1,128 contexts, training-only scales, 54 operational and 156 forecasting boundaries. A further check recalculated all 27 current banks and 567 current strata and verified the 192-unit remaining queue. The initial reporting helper parsed the literal PLEIA group ID `None` as NA, producing zero in its faulted-group-count column. The corrected reader and [canonical verified bank table](smart_building_conformal/outputs/amendment005/plan_check_v1/current_banks_verified.csv) report one; the 18 corrections, original helper archive and correction record are published. The same literal-ID issue affected 864 aggregated rank-table group counts; the canonical rank table corrects them while preserving all rank values. The initial seasonal scope prose also said 45 unique computations; the verified queue and canonical scope ledger correctly give 27 (nine applicable horizons times three folds). No historical catalogue, support decision, observation, threshold or production source changed. One pandas empty-concatenation FutureWarning is retained in the generator log; it did not fail validation.

All 1,267 entry output/configuration/protocol files remain byte-identical. Source assumptions and primary methodological references are in the [register](review/support_design_20260913/SOURCE_ASSUMPTION_REGISTER.md). Structural support is not measured operational performance, nominal coverage, precise inference or dissertation readiness. Full-study and scientific publication readiness remain **false**.

The [supplementary no-fit check](smart_building_conformal/outputs/amendment005/support_final_checks_v1/validation.json) exited 0: 1,224 rank summaries checked, 27 role-specific inference screens, 1,128 explicit zero-control schedules and 36 DSCP joint-origin role sets with 24 valid boundaries. Five conditional CI screens remain unavailable (four earliest PLEIA inner banks and the earliest RICO outer phase mixture). All joint-horizon calibration sets exceed 400 rows; this is structural applicability, not evaluated DSCP performance.
