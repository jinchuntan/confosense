"""Render decision documents from the no-fit tables and verified current counts."""
import json,sys
from pathlib import Path
import pandas as pd
from document_text import prose
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'smart_building_conformal/outputs/amendment005'
A=BASE/'support_design_v1';P=BASE/'study_plan_v1';V=BASE/'plan_check_v1'

def tab(df,cols):
 def val(x):
  if pd.isna(x):return 'unavailable'
  return (f'{x:.6g}' if isinstance(x,float) else str(x)).replace('|',' / ')
 return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+''.join('| '+' | '.join(val(x) for x in row)+' |\n' for row in df[cols].itertuples(index=False,name=None))
def read(p):return pd.read_csv(p,float_precision='round_trip')

def main():
 banks=read(V/'current_banks_verified.csv');roles=read(A/'current_roles.csv');inventory=read(A/'inventory.csv')
 challenge=read(A/'challenge_support.csv');ctx=read(A/'challenge_contexts.csv');precision=read(P/'challenge_precision_support.csv')
 summary=challenge.groupby(['dataset','outer_fold','role']).agg(effective_variants=('effective','sum'),null_variants=('null','sum'),minimum_effective_onsets=('distinct_effective_onsets','min'),supported_strata=('supported','sum')).reset_index()
 summary=summary.merge(precision,on=['dataset','outer_fold','role']);summary.to_csv(P/'challenge_summary.csv',index=False)
 nextunit=json.loads((P/'next_forecast_unit.json').read_text());queue=read(P/'forecast_execution_queue.csv')
 counts=read(P/'completion_counts.csv');revised=read(A/'proposal_roles.csv');phases=read(P/'rico_phase_distribution.csv')
 rank=read(A/'rank_support.csv');initial=bool(rank.initial_rank_all.all())
 dates=roles[roles.role.isin(['inner0_selection','inner1_selection','outer_test'])]
 audit=f'''# Support-design audit: amendment-005 decision evidence

13 September 2026. **No model fitting.** Entry is `9b5acb49531ce12706285c3f040310c0ab6053dd`; the unchanged production source hash is `203f3babf66c98ac072ad450abec5ea7ce3d60473f02708fa64ac2102ea3f7c9`. The completed BDG2 three-fold benchmark and forecasting pilot are preserved. This audit uses structural information, observed signal changes and measured costs; prediction-performance values did not select the proposed design.

**Decision:** retain amendment 004 as the fixed-incidence operational benchmark. Add a separately named **effective-fault conditional context challenge** for PLEIA temperature, PLEIA energy and RICO. Forecasting and own-model interval/compute evaluation remain supported independently of sparse event incidence. RICO needs separately versioned chronological whole-run batches for useful multi-run evaluation. None of this reverses BDG2's three primary abstentions.

The [evidence index](review/support_design_20260913/EVIDENCE_INDEX.md) gives exact table paths, source archives and commands. [AMENDMENT005_PROPOSAL.md](AMENDMENT005_PROPOSAL.md) defines the recommendation; [REMAINING_STUDY_EXECUTION_PLAN.md](REMAINING_STUDY_EXECUTION_PLAN.md) gives the executable queue and missing entrypoint contract.

## Exposure and original units

{tab(inventory,['dataset','primary_horizon','frequency_minutes','original_rows','eligible_rows','groups','segments','asset_days','all_eligible_five_catalogue_bound'])}

PLEIA temperature retains block B, room 11, variable V2; energy retains block B `dif_cons` in kWh per ten-minute interval. Each is one original series, not dozens of independent buildings. RICO retains `B.RTD3`, 207 four-hour runs and 49,680 raw minute observations; 45,747 remain eligible at its primary five-minute horizon (221 per run). The local 287 scheduler candidates include 80 excluded by the source quality flags. BDG2 retains ten buildings and hourly kWh targets. See the [target/group inventory](smart_building_conformal/outputs/amendment005/support_design_v1/original_groups.csv) and [RICO source run audit](smart_building_conformal/outputs/amendment005/support_design_v1/rico_source_run_audit.csv).

All 117 current unsupported-task role hashes match the published preflight. The detailed [role table](smart_building_conformal/outputs/amendment005/support_design_v1/current_roles.csv) includes training/calibration counts, physical frequency/horizon, contiguous segments, eligible onset positions, guarded placement capacity, exact dates and original exposure. The current selection/test roles are:

{tab(dates,['dataset','outer_fold','role','target_min','target_max','n','asset_days','groups','segments'])}

## Count, allocation, null, placement and inference mechanisms

The exact request is `floor(0.5 * eligible_asset_days + 0.5)` **per catalogue**. Five catalogues share the same real exposure. At least 105 effective instances are necessary for five distinct onsets in all 21 strata, but duplicates, nulls, distribution and confidence-bound support can still fail. The count-only exposure minimum for five catalogues is **41 eligible asset-days**, since that first produces 21 requests per catalogue. This is a project gate, not a conformal theorem.

{tab(banks,['dataset','outer_fold','role','requested_per_catalogue','requested','placed','effective_events','null','rejected','minimum_distinct_onsets','supported_strata','faulted_original_groups'])}

All current requested events were hostable and placed: **zero placement rejections**. Thus the observed shortfalls are not hidden failures to place requests. Hostable requests, candidate onset capacity and complete family/severity counts are published separately. The [567 current stratum rows](smart_building_conformal/outputs/amendment005/support_design_v1/current_strata.csv) retain requested/placed/effective/null/rejected counts and distinct original onsets.

For both PLEIA tasks, earliest inner blocks have about 25.8 days, 13 requests each and 65 per five-catalogue bank: impossible even before nulls. Middle blocks have about 38.7 days, 19 each and 95 total: also impossible. Latest inner blocks have about 51.6 days, 26 each and 130 total: arithmetically possible, but only 20/21 strata pass. Their limiting low-severity random-missing stratum has only 2–3 distinct effective onsets. Every current PLEIA inner bank therefore fails the full gate. PLEIA temperature outer fold 0 alone has full structural event support; its unsupported inner selection still prevents primary selection. Other PLEIA outer banks support many stratum point estimates but fail the declared five-onset gate in one or two strata; absence and insufficient precision are distinguished in the tables.

The deterministic rule is exactly `STRATA[(event_number + rotation) % 21]`, with rotations 0–4. A 13-request catalogue bank can request only indices 0–16: `level_shift` severity 2 and all three `drift` severities are absent before any realization. With 19 requests all strata occur, but the minimum request count is only three. With 26 requests the request minimum is five. RICO's three-request bank can request only indices 0–6, leaving 14 strata unrequested; a null can increase the number of missing effective strata. These are design limitations consistent with the existing implementation, not a demonstrated mismatch to its five-rotation specification. A complete set of 21 rotations allocates exactly q requests to every stratum for any q.

PLEIA's one-hour envelope has six samples. For random-missing severities 0.5/1/2, null probabilities are `0.9^6=0.531441`, `0.8^6=0.262144`, and `0.6^6=0.046656`. A low-severity positive schedule therefore often changes nothing. Those schedules remain null and never become positives. Stuck/dropout may also be null on an already constant/zero signal; the per-stratum records preserve those cases. RICO's 60-sample envelope has low-severity random-missing null probability `0.9^60=0.00179701`; its fundamental problem is exposure/allocation, not that probability.

RICO's current inner banks span 38–39 runs and 5.83–5.99 eligible days: three requests per catalogue and at most 15 total. Equal per-run exposure and stable largest-remainder ties repeatedly assign the three requests to the same three runs. More catalogues alone would not create new original runs. Each outer role is a single run: 221 minutes = 0.153472 days, zero requests and only one run for inference. Injected-event recall is unavailable there; a descriptive clean workload/forecast error is still measurable for that run.

Even using **all** RICO data as evaluation, with no training or calibration, the eligible exposure is **31.76875 days**, yielding 16 requests per catalogue and only **80** across five. Even the optimistic raw exposure, 34.5 days, yields only **85** requests. Rearranging subsets cannot fix this unchanged five-catalogue count design. At least 59,040 eligible minute rows are needed to reach the count-only 41-day bound: **13,293 more eligible minutes, or at least 61 additional comparable 221-minute eligible runs**, with separate training/calibration data still required. That bound does not guarantee effective events, representativeness or precise bounds.

Initial finite-rank support is not the cause of the current sparse-event failure: all summarized initial rank checks pass (`{initial}`), with at least 400 calibration rows. Online support is method/level/window specific: signed-tail EnbPI with a 200-score window cannot support 99.5% tails, whereas one-sided CQR has a different finite-rank condition. The [rank table](smart_building_conformal/outputs/amendment005/support_design_v1/rank_support.csv) keeps these mechanisms separate. RICO's inner original-unit counts exceed five but its outer count is one; PLEIA's declared time blocks are not independent buildings and do not guarantee a precise CI.

## Three explicit alternatives

| Choice | What it can estimate | Structural evidence and trade-off | Decision |
|---|---|---|---|
| A: unchanged amendment 004 | Forecast/interval quality and original-exposure clean workload; stratum recall where effective events exist; full operational selection only with both supported inner banks | All 18 unsupported-task inner banks fail; RICO outer recall has no events. PLEIA temperature outer0 support alone is insufficient for nested selection. | Preserve and label limitations; no reinterpretation of old results. |
| B: larger blocks / fixed additional catalogues | Same incidence/stratum estimand if fully supported; additional simulation precision only | Exposure minimum 41 days per evaluated bank is optimistic. Larger PLEIA selection blocks take observations from fitting/calibration; RICO total-data bound remains below 105. | Not the recommended immediate evaluation; count analysis is not demonstrated precision. |
| C: separate balanced challenge | Detection conditional on effective declared fault/context, per-stratum and full named conditional macro; paired clean workload separately | Concrete contexts and finite masks support all 567 role/stratum cells; no prevalence, real precision or deployment-feasibility claim follows. | Recommended supplement, with the versioned memberships below. |

For B, a concrete PLEIA 10%/10%/40%/40% division of the existing final fitting pool creates earliest selection blocks of 5,942/5,944 rows (41.264/41.278 days), meeting the count-only bound. Initial training falls to **1,484 rows**, versus about 3,714 in the equal-quarter design; calibration has 1,485 rows. Final reserved calibration stays 4,954 rows. This does not resolve the 53% null probability or prove a good predictor. Middle/later blocks grow to about 61.9/82.6 days. [Exact B boundaries and sizes](smart_building_conformal/outputs/amendment005/study_plan_v1/alternative_B_larger_blocks.csv) document the trade-off without fitting.

A fixed B simulation budget can be derived in advance: under the random-missing-mask model alone, require probability at least .95 of at least five effective masks per stratum. The minimum number of requests is **17** for PLEIA and **5** for RICO. Require complete 21-rotation cycles, `K=21*ceil(n_required/q)`. Current PLEIA earliest banks need 42 catalogues; middle/later/outer banks need 21. Current RICO inner banks need 42; zero-request outer banks admit no finite K. Proposed batched RICO inner banks need 63–105 catalogues under this bound. Rotate largest-remainder ties too if broader run coverage is intended. Freeze K before any generation, stop at K whether successful or not, never redraw nulls or add catalogues until a model passes. The criterion covers only random masks, not other nulls, distinct onsets, independent units or performance-bound precision. No B performance run or expanded catalogue bank was launched.

## Demonstrated support for C and remaining precision limits

{tab(summary,['dataset','outer_fold','role','contexts','effective_variants','null_variants','minimum_effective_onsets','supported_strata','complete_original_inference_blocks'])}

There are **1,128 role-specific contexts / 47,376 scheduled variants**, not 47,376 independent observations. Inner roles and historical folds reuse observations; only distinct outer periods/runs contribute to final outer summaries. Each PLEIA task has 204 outer daily contexts across three disjoint periods; RICO has 125 distinct proposed outer runs. All 567 role/stratum cells have at least five distinct effective contexts, with minimums 19 for temperature, 18 for energy and 11 for RICO. Deterministic duplicate realizations across the two sign slots are recorded as aliases; support uses distinct contexts and onsets, not variant row counts.

For PLEIA uncertainty, keep seven adjacent daily contexts together and never join across a gap or fold. Earliest inner banks have only three complete seven-day blocks: a five-block precision screen fails even though conditional point recall is structurally estimable. Middle/later inner banks have five/seven and each outer bank nine. RICO resamples whole runs, stratified by represented acquisition phase, retaining all variants, methods and model seeds together; phase/run dependence remains an assumption. No CI precision was measured. The often-used independent-Bernoulli approximation would need about 97 independent units for a worst-case 95% half-width of 0.10; it is only a planning heuristic and is not a power claim for these dependent contexts.

The smallest precision diagnostic after streams exist is one fixed 2,000-draw paired original-unit analysis per required endpoint, seed 20240601, at least 1,900 valid nondegenerate draws. If a required stratum is absent or only a few independent blocks are defensible, report the CI unavailable. Do not expand draws/contexts in response to favourable or disappointing model results.

## Verification and interpretation

The generator exited 0 with zero fits. Six focused tests passed; independent reconstruction verified all 47,376 masks/changes/null statuses, 1,128 contexts, training-only scales, 54 operational and 156 forecasting boundaries. A further check recalculated all 27 current banks and 567 current strata and verified the 192-unit remaining queue. The initial reporting helper parsed the literal PLEIA group ID `None` as NA, producing zero in its faulted-group-count column. The corrected reader and [canonical verified bank table](smart_building_conformal/outputs/amendment005/plan_check_v1/current_banks_verified.csv) report one; the 18 corrections, original helper archive and correction record are published. No historical catalogue, support decision, observation, threshold or production source changed. One pandas empty-concatenation FutureWarning is retained in the generator log; it did not fail validation.

All 1,267 entry output/configuration/protocol files remain byte-identical. Source assumptions and primary methodological references are in the [register](review/support_design_20260913/SOURCE_ASSUMPTION_REGISTER.md). Structural support is not measured operational performance, nominal coverage, precise inference or dissertation readiness. Full-study and scientific publication readiness remain **false**.
'''
 (ROOT/'SUPPORT_DESIGN_AUDIT.md').write_text(audit,encoding='utf-8')
 proposal=f'''# Amendment-005 proposal: separate operational frequency, conditional challenge and matched forecasting

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

PLEIA temperature: block B room11 V2, degrees Celsius, 10-minute sampling, forecasting horizons 10/30/60 minutes; primary alert horizon 10 minutes. PLEIA energy: block B `dif_cons`, kWh per 10-minute interval, the same horizons. RICO: `B.RTD3`, degrees Celsius, one-minute sampling, forecasting horizons 5/15/30/60 minutes; primary alert horizon 5 minutes. BDG2: all ten retained buildings, hourly kWh, horizons 1/3/6 hours; primary alert horizon 1 hour. No additional sensor or easier cohort was selected.

For PLEIA C, retain amendment-004 role boundaries exactly. B0–B3 are four purged quarters of the final fitting pool; inner0 fits B0/calibrates B1/evaluates B2, inner1 fits B0+B1/calibrates B2/evaluates B3. Reserved final calibration and outer periods remain unchanged. For matched forecasting, retain the existing pilot's 24-step sequence/common-flat-feature eligibility, two expanding purged tuning folds and final calibration; the three completed PLEIA horizon hashes matched exactly. Forecasting and operational masks are separately versioned and are not falsely treated as identical.

For RICO C and the new matched-forecasting version, order all 207 retained runs by first origin then ID; split the run list into five chronological blocks using floor(207/5)=41 and a 43-run final remainder. The last three blocks are outer tests. Fold IDs remain backward: **fold2=41 earliest evaluation runs, fold1=41 middle, fold0=43 latest**. Earlier runs supply development; reserve its last quarter of whole runs for final calibration. Keep entire runs at all boundaries. Original source flags and run lengths remain unchanged. Per-horizon sequence eligibility may reduce row counts but never split a run's role.

{tab(revised[(revised.dataset=='rico')&revised.role.isin(['final_fit','final_calibration','outer_test'])],['outer_fold','role','n','groups','target_min','target_max','asset_days'])}

The evaluation is conditional on the represented acquisition phases:

{tab(phases[phases.role=='outer_test'],['outer_fold','phase','runs','start','end','ever_legacy_final_fit','ever_legacy_final_calibration'])}

The [207-run history ledger](smart_building_conformal/outputs/amendment005/study_plan_v1/rico_run_history.csv) shows prior training/calibration/test use under every old fold. These are not globally untouched holdouts. Within each new fold, only earlier runs train/calibrate; the reporting must disclose prior inspection and reuse. No unseen-building or prospective-trial claim follows.

Matched forecasting normalizes only on each permitted training block; tuning uses equal inner-fold MAE, fixed two-candidate grids and deterministic candidate-order ties. LSTM final epochs are the ceiling of the mean selected-candidate best epochs. Final calibration/test outcomes select neither candidates nor epochs. RICO calibration is pooled over earlier whole runs; new evaluation runs have no within-run calibration observations. Report that assumption and phase-specific quality rather than promising conditional coverage. Initial calibration remains at least 400 rows; insufficient finite ranks produce unavailable/infinite bounds with an explicit status.

## Fixed challenge contexts and schedules

The machine specification is [proposal_spec.json](smart_building_conformal/outputs/amendment005/support_design_v1/proposal_spec.json). [Membership/observations and schedule files](review/support_design_20260913/EVIDENCE_INDEX.md) are sufficient to recalculate the no-fit realization evidence; raw source data and exact features are still required for future fitting.

- PLEIA: tile each eligible contiguous role segment into nonoverlapping 144-row (24-hour) contexts, anchored at that segment's first row; leave the shorter final tail unused for the challenge but included in full-stream clean workload.
- RICO: one context per whole eligible run. Never concatenate runs or bridge acquisition gaps.
- Choose one onset per context using a SHA-derived seed from version, task, fold, role and context identity, with master context seed **20260913**. Selection uses structure only. No onset is moved after inspecting signal magnitude, null status or detection.
- Require warm-up of **360 minutes for PLEIA**, **60 minutes for RICO**, the original one-hour fault envelope (6 or 60 samples), and at least **60 minutes follow-up**. The original detection tolerances remain 60 and 10 minutes respectively. The actual predecessor and entire envelope/follow-up lie in the same context. Future features may use only available original pre-context history in that source segment; common feature eligibility already establishes required lag/sequence history.
- Every context receives all seven families x three severities in independent counterfactual replays. Use exactly **two slots**, seeds42/43, with additive signs -/+ respectively. Random-missing masks have independent event-keyed RNGs. Deterministic block/stuck/dropout slots can be identical: [aliases](smart_building_conformal/outputs/amendment005/study_plan_v1/challenge_aliases.csv) identify them, and they add no original contexts or inferential degrees of freedom.
- The two-slot choice counterbalances additive signs; it is a fixed project design, not a claimed precision optimum. Stop after the fixed slots regardless of nulls or model results. Do not select easy severities, replace nulls or draw until support/performance passes.
- Reset alert, residual-release and recalibration state independently for each context/variant, initialized from that role's permitted historical calibration pool. Use clean observed warm-up and causal corrupted inputs thereafter; corruption enters future lags, rolling features and observable residuals. Targets release residuals only when available; no clean truth repairs the corrupted path. Methods share context/onset/mask identities. The clean counterfactual has its own state.
- Keep one clean/zero identity replay per context, shared across equivalent zero-family slots. It must reproduce clean inputs, issued bounds, alerts and released scores exactly; no zero-control is a positive. The no-fit schedule's clean control is the unchanged context observation sequence; the future runner must enforce stream identity.

Fault realizations use the preserved amendment-004 definitions and training-only robust sigma, including pooled-training fallback for new RICO runs. Missingness is availability loss; dropout is numerical zero; stuck holds the observable predecessor of its sub-block. No-change schedules stay null. At least five **distinct effective contexts/onsets** per stratum and five original context/run units are needed for the full named conditional point estimate. All 567 current proposed role/stratum cells pass that structural screen, while inference has separate requirements below.

## Fixed comparisons and selection restrictions

C is **evaluation-only**, with no challenge-score selection. Use fixed .95 quantile-uncalibrated/static, CQR/static, CQR/first-declared-rolling, and persistence with its own fixed .95 absolute split-conformal interval. Uncalibrated quantiles and CQR share the actual HistGradientBoosting quantile fit; they are not labelled Attention-LSTM or XGBoost. Rolling settings are **every24/window250** for both PLEIA tasks and **every15/window200** for RICO, with minimum online pool50. Keep immediate and each context-supported declared physical temporal rule, with fixed no latching/cooldown. Full remaining interval-method comparisons are in their separate ledger.

PLEIA context-supported rules are immediate, 30-minute3/3, 60-minute4/6, 180-minute3/18 and 360-minute4/36. Five- and fifteen-minute rules fail sampling-frequency k/m applicability. RICO supports immediate, 5-minute2/5, 15-minute3/15, 30-minute3/30 and 60-minute4/60. Its 180/360-minute candidates cannot fit complete warm-up, envelope and follow-up into a four-hour run; they remain explicitly inapplicable for this conditional-context endpoint, not silently removed from historical amendment 004. [Applicability ledger](smart_building_conformal/outputs/amendment005/support_design_v1/challenge_rule_applicability.csv).

Availability-only, numerical-only and combined episode detection remain separate. Missing-data alarms are shared by the baselines. Match actual episode onsets one-to-one at target-observation time; pre-active episodes earn no onset credit. Retain misses, detected-only delays and restricted mean time-to-detection with misses censored at the full envelope-plus-tolerance horizon. Recovery is descriptive return toward pre-context coverage using the existing literal 0.05 numerical convention, with fixed follow-up, censoring and unavailable medians retained. Do not tune floating-point tolerances or thresholds.

## Inference, limitations and implementation gate

For C, aggregate the five declared model seeds within original contexts before inference; do not count seeds or variants as independent data. Outer summaries exclude all inner-role outcomes. For PLEIA, resample blocks of seven adjacent daily contexts within original segments/folds, carrying every method/stratum/replicate together. Use fixed-length moving blocks for the percentile diagnostic and keep edge/tail context contributions with their observed weights; the nonoverlapping complete-week counts in the [support table](smart_building_conformal/outputs/amendment005/study_plan_v1/challenge_precision_support.csv) screen whether at least five original blocks exist. Earliest inner roles fail that precision screen and retain unavailable CIs. They still permit conditional stratum point estimates.

For RICO, resample whole runs within acquisition phase, retaining original phase weights and all paired contributions. Require at least five original runs and at least two runs in every phase for a phase-stratified population interval; otherwise report conditional descriptive values and unavailable bounds. The earliest proposed outer fold contains only one phase-1 run, so its phase-stratified interval is unavailable unless that phase is explicitly treated as fixed descriptive support; do not silently drop it. Use 2,000 fixed draws, bootstrap seed20240601, at least1,900 valid nondegenerate draws. These are approximate conditional diagnostics, not exchangeability guarantees.

This amendment requires a context-replay entrypoint that consumes the published membership/schedule hashes, enforces resets/warm-up/null handling, preserves method ownership and exports original-unit contributions plus zero-control stream identities. It is **not yet implemented as a fitting/replay command**. The structural scripts and independent no-fit checks are implemented and complete. The next implementation priority is the independent matched-forecasting package below, not a full operational launch.

The original fixed-incidence 21-stratum operational selection claim remains non-estimable for the three unsupported tasks under amendment 004. Additional independent exposure or a separately justified incidence/allocation design is needed to answer that original question. C answers a narrower, explicitly different conditional question and does not manufacture deployment feasibility. BDG2's completed results, all historical thresholds and all datasets remain visible. Full-study/publication readiness remains **false**.
'''
 (ROOT/'AMENDMENT005_PROPOSAL.md').write_text(proposal,encoding='utf-8')
 plan=f'''# Remaining study execution plan: matched models, methods and operational endpoints

13 September 2026. **Plan and no-fit inventory complete; no new fitting authorized or executed.** [Amendment-005](AMENDMENT005_PROPOSAL.md) resolves the support design; the matched forecasting comparison proceeds independently of event support. The existing PLEIA pilot and BDG2 benchmark remain preserved rather than rerun for this report.

## Exact completion matrix and prerequisites

The [machine-readable experiment matrix](smart_building_conformal/outputs/amendment005/support_design_v1/experiment_matrix.csv) has **1,560 task/horizon/fold/model-seed/model/level rows**, including explicit seasonal inapplicability. It binds data/role hashes, sample counts, expected fitting calls and evidence paths. [273 role records](smart_building_conformal/outputs/amendment005/support_design_v1/forecast_roles.csv) and thirteen compressed membership tables provide actual dates and row IDs for every horizon and all three folds. All 156 train/calibration/test/tuning boundaries passed no-fit validation. RICO uses the separately versioned 41/41/43-run outer batches, never a row cut through a run. Existing PLEIA pilot hashes match exactly.

| Task | Horizon steps | Physical horizons | Primary matched models | Seasonal applicability |
|---|---|---|---|---|
| PLEIA temperature | 1,3,6 | 10,30,60 min | Persistence, XGBoost, Attention-LSTM | Daily144-step baseline; actual common calibration/test rows all supported |
| PLEIA energy | 1,3,6 | 10,30,60 min | Same | Daily144-step baseline; all common rows supported |
| RICO | 5,15,30,60 | 5,15,30,60 min | Same | Inapplicable: no daily cycle inside an independent four-hour run; never reach across runs |
| BDG2 | 1,3,6 | 1,3,6 hours | Same | Daily24-step baseline; all common rows supported |

All tasks retain outer IDs0/1/2 and model seeds42–46. Forecast levels are90/95%. The primary three-model comparison comprises **195 paired task/horizon/fold/seed units, 585 point cells and 1,170 interval cells**. Three paired units are reusable from the completed PLEIA pilot:9 point /18 interval cells. Required new evidence is **192 paired units /576 point /1,152 interval cells**. Every learned model/unit has four inner candidate-fold fits plus one final fit; the remaining work is **1,536 tuning +384 final =1,920 learned fit invocations**. The two interval levels share each model fit and are not counted twice.

{tab(counts,['dataset','model','status','point_cells','tuning_fits','final_fits'])}

Seasonal adds **135 point /270 interval cells** across nine applicable task/horizons, implemented as **27 unique deterministic horizon/fold computations with five paired seed aliases**, zero learned fits. The matrix explicitly records60 RICO seasonal point /120 level cells as inapplicable. Persistence also has no stochastic fitting; any reuse across seed aliases must retain complete identities and exact paired targets. Do not describe repeated baseline aliases as independent training replicates.

The historical operational CQR quality rows have different owners/masks/protocols and do not fill the matched own-model rows. The broader [five-method interval matrix](smart_building_conformal/outputs/amendment005/study_plan_v1/interval_method_matrix.csv) retains **1,950** level/horizon rows for quantile-uncalibrated, CQR, recentred-EnbPI static/updated and DSCP. This is additional required method evidence, not an assertion that 1,950 independent fits are needed. Share CQR/uncalibrated owners; share static/updated EnbPI where the same trained owner and calibration contract permit. DSCP consumes joint-origin multi-horizon predictions from the declared owner, not a fake single-horizon substitute. Record actual MAPIE bootstrap sub-estimator counts from the executed owner; no GPU or unmeasured fit-count shortcut is assumed.

## Smallest next implementation/run package

**Implement `src.matched_forecasting005`, then request/receive authorization for one PLEIA-energy horizon1/fold0/seed42 matched unit containing persistence, XGBoost and Attention-LSTM.** No fitting authorization is implied by this document. The exact proposed [unit specification](smart_building_conformal/outputs/amendment005/study_plan_v1/next_forecast_unit.json) fixes all candidates and identities. It has **{nextunit['fit_n']:,} fitting, {nextunit['calibration_n']:,} final-calibration and {nextunit['test_n']:,} test rows**, three point cells, six interval cells, eight tuning and two learned final fits. This measures the next task's cost and matched errors without requiring operational event support.

The current `src.model_comparison_pilot` entrypoint exists but explicitly rejects another dataset/fold/seed. `pilot_data.pilot_roles` also hard-codes chronological splitting, so it must not be applied blindly to RICO. The proposed generalized command **does not exist yet**; this was checked rather than assumed. The [dry-run checker](smart_building_conformal/scripts/check_remaining_study005.py) is executable now and never fits models.

Required entrypoint work is concrete:

1. Add `freeze`, `readiness`, `run`, `validate` and `resume` actions to the new module; do not relax the old pilot's guard or modify its files. Consume matrix keys and exact data/role hashes, the frozen two-candidate configuration and the appropriate group-aware role constructor already exercised by the no-fit generator. Refuse absent keys, changed source/config/data, duplicate/missing cells and unsafe boundaries.
2. Generalize the existing measured `model_comparison_pilot.run_unit` logic without hard-coded `pleia/f0/s42` output fields. Use `pilot_data.build_support`, bounded LazyLSTM sequences and matching flat features. Preserve target_lag0 availability, input schemas, training-only normalization, own-model predictions/calibration residuals, inner-only candidate/epoch selection and separate phase resource meters. `pilot_roles` compatibility is required for the completed PLEIA cells; current-source production resume may not impersonate their old source.
3. Use one immutable checkpoint per dataset/horizon/fold/seed/model with serialized fitted artifacts and COMPLETE hashes; reuse the repaired hash-only completeness path. Verify shared-level fitting once. Add a read-only compatibility/reuse ledger for historical pilot units instead of rewriting their identities.
4. Check actual RAM/disk, persist command/source/config/data/PID/timestamps/exit through `scripts/log_pilot_command.py`, and serialize all real fits. Keep existing CPU environment, one numerical/Torch thread, `n_jobs=1`, batch256, 3GiB launch RAM and8GiB disk guard; retain the existing epoch memory guard. Do not reduce cohorts, model size, thresholds or candidates due to performance. Preserve incomplete attempts and support completed-unit resume only, with zero new fits when complete.
5. Before the real unit, pass focused train/cal/test sentinel, run-boundary, candidate-selection/epoch, own-model-radius, common-target, checkpoint corruption and forbidden-fit-resume tests. A tiny integration fixture, if fitting is required, belongs in the next explicitly authorized package. The present task used no learned fits, including tests.

Future command, executable only after that implementation and authorization:

```powershell
& C:/cfs_venv/Scripts/python.exe -B scripts/log_pilot_command.py --log outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1.log -- C:/cfs_venv/Scripts/python.exe -B -m src.matched_forecasting005 run --matrix outputs/amendment005/support_design_v1/experiment_matrix.csv --dataset pleia_energy --horizon 1 --outer-fold 0 --model-seed 42 --out outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1
```

Acceptance: actual exit0; exactly3 point/6 interval cells; all models share fitting/calibration/test target IDs; eight tuning/two final learned fits and zero persistence fits; independently recomputed saved MAE/RMSE, coverage/MPIW/Winkler and phase costs; unchanged historical hashes; completed-unit resume invokes zero fitting routes. Low coverage or disappointing LSTM accuracy is an outcome, not grounds to retune. Publish that bounded unit and measured expansion estimate before continuing the queue.

## Prioritized execution queue and costs

The [192-unit queue](smart_building_conformal/outputs/amendment005/study_plan_v1/forecast_execution_queue.csv) specifies exact dataset/horizon/fold/seed, argv, fresh output path, prerequisite, fit count and labelled planning range. It contains each required core unit exactly once and excludes all three reusable pilot units. Priority1 is the package above; priority2 is RICO h5/f2/s42, priority3 BDG2 h1/f2/s42, then remaining units in the published order. Do not launch the whole queue automatically. Each first-task measurement is a resource gate before authorizing a larger chunk; a failed integrity/resource check stops execution without changing settings.

{tab(queue.head(3),['priority','dataset','horizon','outer_fold','model_seed','learned_fit_invocations','scenario_low_model_seconds','scenario_high_model_seconds'])}

These are scheduling scenarios: the minimum/maximum **measured PLEIA three-model per-horizon phase totals**, scaled by fitting-row count and factors0.5/3. They exclude preparation, I/O, validation, channel-dimension differences and model-dependent epochs; they are not statistical intervals or four-task ETAs. The first energy unit has the same fitting-row count as the PLEIA reference; allow roughly **2–20 minutes** as an initial wall-time planning allowance, then replace it with measurements. RICO and BDG2 learned-model costs remain unmeasured. Historical operational CQR runtimes cannot be substituted for Attention-LSTM/XGBoost costs.

Measured reference: the completed PLEIA pilot has three-horizon phase totals864.317s for LSTM and18.009s for XGBoost; persistence0.030s. The current three-fold operational benchmark's3,491.322s uses CQR-owned HistGradientBoosting and is a different task. The measured preparation-copy repair and lazy batches are already in place; do not repeat those investigations. Record separate tuning, final fitting, calibration and inference seconds, sample throughput, peak/baseline/incremental RSS, process CPU, available RAM and actual command wall time. Nested phases must not be added to their enclosing totals. This environment is CPU-only; no GPU saving is claimed.

After core matched cells, execute the [27-job seasonal queue](smart_building_conformal/outputs/amendment005/study_plan_v1/seasonal_execution_queue.csv) with exact same calibration/test targets and own seasonal residuals; then complete the full-method adapter/quality matrix. For DSCP, intersect `(original group, origin_time)` across all declared horizons separately within calibration/test roles, check strict boundaries, retain direct-horizon adaptation labels, and use only historical calibration predictions/errors for clustering/merging. Its clustering/neighbor costs require a bounded measurement before a full multi-horizon launch; an imported module is not experimental evidence.

Implement the C context replay only after matched-runner correctness is established. Its first bounded fitting/replay proposal must name the dataset/fold/seed and fixed .95 controls, use the published context hashes, and include zero-control, causal-input, released-score, method-identity, alias/null and original-unit contribution validation. Do not run unsupported amendment-004 primary selection and label a C result as a replacement. BDG2 full-grid operational execution remains a separate authorization; preserve its reduced-grid evidence.

## Required evidence and optional scope

{tab(read(V/'scope_ledger_verified.csv'),['scope','obligation','exact_status','rationale'])}

The amended execution crosswalk must retain the legacy robustness/contamination/recovery obligations:900 intended cells across60 legacy core unit keys; fixed zero controls; actual closed-loop features/residuals; calibration-only contamination; group-specific coverage/workload shifts, cascades, restricted recovery time and censoring. Original amendment003 fault definitions and frequency must not be silently equated with C's21 strata. Unsupported primary pipelines retain abstention; any fixed diagnostic recovery is labelled diagnostic. RICO membership changes require new IDs and an explicit row-count crosswalk, not relabelling old cells. No full-method, robustness or full operational result is newly claimed.

Report paired LSTM-minus-XGBoost MAE as the primary forecasting contrast for each of13 task/horizon combinations, with RMSE, interval quality and computational trade-offs alongside it. Average model-seed contributions within original groups/time blocks before paired inference; do not resample five seeds as independent test populations. Keep original folds and phase/building dependence. If formal tests are reported, treat the13 MAE contrasts as the declared Holm family; width, coverage, Winkler and timing contrasts are secondary and must remain jointly contextualized. No equivalence claim follows from a CI spanning zero and no width benefit is claimed without coverage context.

The no-fit plan checker exited0, confirmed all192 queued keys and1,920 required learned fits, and explicitly reported the missing generalized entrypoint. This is a concrete implementation prerequisite, not an unresolved design question. Scientific/full-study readiness stays **false** pending implementation, authorized execution, output verification and correctly scoped inference.
'''
 (ROOT/'REMAINING_STUDY_EXECUTION_PLAN.md').write_text(plan,encoding='utf-8')
 for name in ['SUPPORT_DESIGN_AUDIT.md','AMENDMENT005_PROPOSAL.md','REMAINING_STUDY_EXECUTION_PLAN.md']:
  path=ROOT/name
  text=path.read_text(encoding='utf-8')
  text=text.replace('support_design_v1/rank_support.csv','support_final_checks_v1/rank_support_verified.csv')
  if name=='SUPPORT_DESIGN_AUDIT.md':
   text=text.replace('No historical catalogue, support decision, observation, threshold or production source changed.',
    'The same literal-ID issue affected 864 aggregated rank-table group counts; the canonical rank table corrects them while preserving all rank values. The initial seasonal scope prose also said 45 unique computations; the verified queue and canonical scope ledger correctly give 27 (nine applicable horizons times three folds). No historical catalogue, support decision, observation, threshold or production source changed.')
   text += '\nThe [supplementary no-fit check](smart_building_conformal/outputs/amendment005/support_final_checks_v1/validation.json) exited 0: 1,224 rank summaries checked, 27 role-specific inference screens, 1,128 explicit zero-control schedules and 36 DSCP joint-origin role sets with 24 valid boundaries. Five conditional CI screens remain unavailable (four earliest PLEIA inner banks and the earliest RICO outer phase mixture). All joint-horizon calibration sets exceed 400 rows; this is structural applicability, not evaluated DSCP performance.\n'
  if name=='AMENDMENT005_PROPOSAL.md':
   text += '\nMachine-readable supplements: [27 complete inference screens including phase support](smart_building_conformal/outputs/amendment005/support_final_checks_v1/challenge_inference_support.csv) and [1,128 clean identity schedules](smart_building_conformal/outputs/amendment005/support_final_checks_v1/challenge_zero_controls.csv). Input identity is specified without fitting; issued-bound/alert identity awaits the future replay runner and is not claimed complete.\n'
  if name=='REMAINING_STUDY_EXECUTION_PLAN.md':
   text += '\nThe DSCP intersection is now concretely enumerated: [36 joint-origin role support rows](smart_building_conformal/outputs/amendment005/support_final_checks_v1/dscp_joint_origin_support.csv) and [exact common-origin memberships](smart_building_conformal/outputs/amendment005/support_final_checks_v1/dscp_joint_origin_membership.csv.gz). All 24 fit/calibration/test boundaries and whole-run constraints passed; each of 12 joint calibration sets has at least 400 rows. Fitted predictions, joint calibrators and their measured costs remain required.\n'
  path.write_text(prose(text),encoding='utf-8')
 print('Wrote all three complete decision documents')

if __name__=='__main__':main()
