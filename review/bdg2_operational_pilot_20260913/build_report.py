"""Build the completed pilot report exclusively from verified saved evidence."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'smart_building_conformal/outputs/amendment004'
RUN=BASE/'bdg2_operational_pilot_f2_s42_v2'
EXEC=Path(str(RUN)+'_execution')
VAL=BASE/'bdg2_pilot_validation_v1'
AUDIT=BASE/'bdg2_pilot_independent_validation_v1'

def md(frame):
    def cell(v):
        if isinstance(v,float):return 'NA' if pd.isna(v) else f'{v:.6g}'
        return str(v).replace('|','/')
    return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+ '\n'.join(
        '| '+' | '.join(cell(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None))

def main():
    p=json.loads((RUN/'units/outer2_model42/payload.json').read_text())
    ident=json.loads((EXEC/'prefit_identity.json').read_text())
    verification=json.loads((AUDIT/'validation.json').read_text());assert verification['passed']
    resume=json.loads((VAL/'resume_validation.json').read_text());assert resume['passed']
    exitlog=json.loads((VAL/'pilot_v2.log.json').read_text());assert exitlog['exit_status']==0
    oldlog=json.loads((VAL/'pilot.log.json').read_text());assert oldlog['exit_status']==1
    built=json.loads((EXEC/'run_output_validation.json').read_text());assert built['output_valid']
    metrics=pd.read_csv(AUDIT/'recomputed_metrics.csv');quality=pd.read_csv(AUDIT/'clean_interval_quality.csv')
    inner=metrics[metrics.inner_fold>=0];outer=metrics[metrics.inner_fold<0]
    phases=pd.read_csv(VAL/'phase_measurements.csv');commands=pd.read_csv(VAL/'command_measurements.csv')
    runphases=phases[(phases.run==EXEC.name)&(phases.invocation=='run_phases.jsonl')]
    resumephases=phases[(phases.run==EXEC.name)&(phases.invocation=='resume_phases.jsonl')]
    resumepeak=int(resumephases.lifetime_peak_rss_bytes.max());resumemin=int(resumephases.min_available_ram_bytes.min())
    peak=int(runphases.lifetime_peak_rss_bytes.max());minimum=int(runphases.min_available_ram_bytes.min())
    cost=json.loads((VAL/'cost_scope.json').read_text())
    files=[f for f in RUN.rglob('*') if f.is_file()];size=sum(f.stat().st_size for f in files)
    outertable=outer[['candidate_id','method','rule_id','macro_event_recall','recall_lcb','recall_ucb',
        'background_episodes_per_asset_day','workload_ucb','custom_synthetic_f1','ordinary_matched_event_episode_precision']]
    innertable=inner[['inner_fold','candidate_id','macro_event_recall','recall_lcb',
        'background_episodes_per_asset_day','workload_ucb','custom_synthetic_f1','bound_status']]
    delays=outer[['candidate_id','n_events','n_detected','corrupted_episode_count','unmatched_episode_count',
        'detected_delay_median_minutes','detected_delay_q90_minutes','undetected_fraction','restricted_mean_detection_minutes']]
    q=quality[quality.role=='outer_test'][['candidate_id','observed_rows','empirical_coverage','mpiw_kWh','winkler95_kWh','mae_kWh','rmse_kWh']]
    support=pd.read_csv(AUDIT/'event_support.csv')
    supports=support.groupby('role',sort=False).agg(requested=('requested','sum'),placed=('placed','sum'),
        effective=('effective','sum'),null=('null','sum'),rejected=('rejected','sum'),
        minimum_distinct_effective_onsets=('distinct_effective_onsets','min')).reset_index()
    members=pd.DataFrame(ident['memberships']);members=members[members.role.str.startswith(('inner','final','outer'))][['role','n','groups','asset_days']]
    groups=pd.read_csv(AUDIT/'group_metrics.csv');g=groups[groups.role=='outer_test']
    groupstats=g.groupby('candidate_id').agg(min_group_workload=('episodes_per_asset_day','min'),
        max_group_workload=('episodes_per_asset_day','max'),groups_above_1_per_day=('episodes_per_asset_day',lambda x:int((x>1).sum()))).reset_index()
    bounds=metrics.groupby(['role','bound_status'],sort=False).agg(cells=('candidate_id','size'),
        minimum_valid_replicates=('valid_replicates','min'),maximum_valid_replicates=('valid_replicates','max')).reset_index()
    decision=(f"Selected `{p['pipeline']['candidate_id']}` from the frozen nine candidates." if p['pipeline'] else
        '**Explicit abstention: no feasible configuration.** No operational pipeline was selected from the frozen nine candidates. The fixed CQR .95/static/immediate reference and controlled components are diagnostics, not substitutes for feasibility.')
    violation=', '.join('`'+x+'`' for x in p['outer_budget_violations']) or 'None'
    text=f'''# Completed BDG2 operational pilot report

{decision}

The canonical version-2 command completed with **exit status 0**. Its complete output matrix passed the production validator and independent reconstruction from saved observations, intervals, event schedules, original-row contributions and paired bootstrap draws. Completed-unit resume returned **zero new fits**, with all {resume['unit_files_byte_identical']} unit files byte-identical and fitting/computation functions forbidden. These are engineering and calculation checks; full-study readiness remains **false**.

## Identity and bounded scope

- Entry implementation: `2243c167804690ad1ec9b8aebc369e5596d392aa`; evaluated implementation: `{ident['git_commit']}`. This is a descendant review branch, not the older source beneath the instruction branch.
- Source SHA-256: `{ident['spec']['source_hash']}`. The [exact evaluated ZIP](smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2_execution/evaluated_source.zip) preserves original bytes.
- Frozen configuration SHA-256: `{ident['spec']['config_hash']}`; data/features hash: `{ident['spec']['data_hash']}`; outcome hash: `{ident['spec']['outcomes_hash']}`. Full identity, seed ledger, nine candidates and expected keys are in the [pre-fit record](smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2_execution/prefit_identity.json).
- BDG2 only, outer fold 2, model seed 42, all ten retained buildings, horizon one hour, catalogue seeds 42–46. All nine reduced-grid candidates use .95; CQR/uncalibrated static plus CQR rolling every 12 origins with window 200; immediate, 180-minute 3-of-3 and 360-minute 4-of-6 rules. Candidate IDs, incidence .5 events/asset-day, recall floor .60 and workload ceiling 1 episode/asset-day are unchanged.
- The original proposal remains marked as a historical proposal. This report records its execution. No additional real-data unit or full experiment was launched.

## Membership, exposure and event support

Fresh preparation passed all 13 role-hash comparisons against the published preflight before fitting. The five catalogue repetitions do not multiply exposure or independent building count. Asset-day exposure is eligible hourly observations divided by 24; target observations define the evaluation clock.

{md(members)}

The 15 actual inner/outer catalogue files match the frozen preflight schedules exactly, including null realizations and failed requests. Event totals below pool the five catalogues; distinct support deduplicates building/onset pairs within each of the 21 strata.

{md(supports)}

The four-task preflight limitations still apply: PLEIA temperature, PLEIA energy and RICO lack inner structural support at the unchanged incidence. RICO outer banks have zero events. This BDG2 pilot does not resolve those limitations or supply results for those tasks.

## Inner selection

Every candidate retained both inner folds. Bounds used 2,000 shared whole-building bootstrap draws per fold, with a minimum of 1,900 valid replicates. Feasibility requires both folds' recall LCB ≥.60 and workload UCB ≤1.0; unavailable or degenerate bounds cannot be replaced with point estimates. Selection utility is the equal-fold mean of the custom 21-stratum synthetic F1, followed by the frozen delay/workload/ID tie-breaks.

{md(innertable)}

All rejection reasons, independently selected component decisions and the secondary inverse recall-floor decision are retained in the [checkpoint payload](smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2/units/outer2_model42/payload.json) and [independently recalculated rejections](smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/rejections.csv). The inverse selector also returned `{p['inverse_recall_floor']['decision']}`. No outer outcome selected or revised a pipeline.

The immediate rolling CQR candidate `c0024_ba16b82adffd` passes both recall lower-bound gates and the second fold's workload gate, but its first-fold workload UCB is **{inner[(inner.candidate_id=='c0024_ba16b82adffd')&(inner.inner_fold==0)].workload_ucb.iloc[0]:.12f}**, strictly above 1.0. Rounding that value to 1.000 would conceal its rejection. Its selection under the separate inverse objective removes the workload ceiling only for that declared secondary comparison; it is not primary operational feasibility. This near-boundary result also warrants caution about Monte Carlo and ten-building sampling uncertainty. Neither bootstrap settings nor thresholds were changed to change the decision.

## Outer results

The {len(outer)} distinct outer configurations and {len(outer)*5} catalogue pairs were derived from the actual frozen decision/comparators. Multiple comparison labels can refer to one evaluated configuration; they are not extra fits. Controlled components share the final quantile fit. The fixed persistence split-conformal reference requires zero learned fits.

{md(outertable)}

The recall columns are equal-weight means over all 21 family/severity strata. The custom synthetic F1 allocates unmatched episodes uniformly across those strata and is **not conventional precision**. Ordinary matched-event/episode precision is shown separately. Workload is clean-background episodes per original asset-day, not a proven real-world false-alarm rate: the source has no adjudicated natural-fault labels.

Observed outer point-workload violations of the declared ceiling: **{violation}**. No violation triggered reselection or threshold changes. Per-building workload shows whether an aggregate rate conceals local burden:

{md(groupstats)}

Event matches use one-to-one episode starts at target-observation time. An episode already active before onset receives no credit. Complete scheduled tolerance is required for eligibility. Misses remain in recall and the restricted mean; median and 90th-percentile delays describe detected events only.

{md(delays)}

All three channel attributions (availability-only, numerical-only, combined), 21 strata, buildings, misses, delays and recovery censoring are independently checked and available in the [audit directory](smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1). Recovery is a descriptive return toward each building's pre-injection coverage, not a guaranteed restoration of nominal coverage.

## Clean interval and point quality

The following is independently recomputed from **unmodified-stream** observed targets and issued bounds. Coverage is a fraction; MPIW, Winkler95, MAE and RMSE use the adapter's **kWh per hourly observation**. All {int(q.observed_rows.iloc[0])} outer rows contribute to each configuration; aggregation weights observations, not buildings equally. Winkler95 uses alpha=.05 and a penalty multiplier of 40 beyond either bound. It includes CQR's existing interval-order repair. The .95 uncalibrated quantiles do not acquire conformal guarantees from their label.

{md(q)}

## Uncertainty and applicability limits

{md(bounds)}

These are approximate percentile, whole-building, conditional pilot bounds. Ten selected buildings are ten original resampling units; five synthetic catalogues are not five independent datasets. Only one model seed and one outer fold were run. Selection uncertainty, variation across other model seeds/folds, possible dependence between buildings at the same site and generalization to a broader building population are not established. Paired full-study tests, Holm-adjusted claims, equivalence and superiority claims are not produced by this pilot. Any unavailable bound retains its explicit reason rather than receiving an invented interval.

Synthetic scheduled fault envelopes and coarse hourly duration/missingness realizations limit interpretation. Bias/drift can begin at zero amplitude; null realizations stay null. Results describe the declared injection distribution and frozen horizon, not verified detection of naturally occurring faults. Inspection of this pilot does not authorize retuning.

## Actual computational cost

The successful command took **{exitlog['seconds']:.3f} seconds ({exitlog['seconds']/60:.2f} minutes)** and **{cost['process_cpu']['total_cpu_seconds']:.3f} CPU seconds** in the actual pilot process. Its evaluate-unit region took **{p['compute_resources']['seconds']:.3f} seconds**. Peak Windows process RSS was **{peak:,} bytes ({peak/2**30:.3f} GiB)**; minimum sampled available physical RAM was **{minimum:,} bytes ({minimum/2**30:.3f} GiB)**. Launch required 3 GiB available RAM and passed. Numerical thread variables were all 1; real fits were sequential in the existing Python environment. [Process lifetime CPU measurements](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/process_measurements.csv) come from Windows process accounting and include the interval before the observer attached.

There were **3 CQR fit objects containing 9 quantile sub-estimators**: two inner fits and one final fit. Uncalibrated controls shared those fits; persistence used zero learned fits. The failed version-1 attempt used zero fits and took {oldlog['seconds']:.3f} seconds. The canonical run directory contains **{len(files)} files, {size:,} bytes ({size/2**20:.2f} MiB)**, excluding raw data, environments and external backups.

{md(runphases[['phase','seconds','peak_rss_bytes','lifetime_peak_rss_bytes','min_available_ram_bytes']])}

Phase intervals overlap: do not add nested phase durations or memory peaks. The checkpoint phase includes computation, frame assembly, compression and integrity reload. Full command time includes imports and final output checks. [Command measurements](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/command_measurements.csv), [phase measurements](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/phase_measurements.csv), [fit counts](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/fit_measurements.csv), [artifact sizes](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/artifact_measurements.csv) and [measurement scope](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/cost_scope.json) separately retain actual costs of resume, independent verification and regression. They are not full-study runtime estimates.

Completed-unit resume took **{commands[commands.log=='resume.log'].seconds.iloc[0]:.3f} seconds**, with **{resumepeak:,} bytes ({resumepeak/2**30:.3f} GiB)** process peak RSS and **{resumemin:,} bytes ({resumemin/2**30:.3f} GiB)** minimum sampled available RAM. It performs no fits, but [the completed-unit path](smart_building_conformal/src/operational004_engine.py) calls `load` and then `require_complete`; [the latter calls `load` again](smart_building_conformal/src/unit_checkpoint.py) while the first loaded frames remain live. This confirmed duplicate materialization explains an avoidable allocation component; the exact peak reduction from fixing it has not been measured. It is a new checkpoint-read limitation, not a repeat of the earlier preparation-memory investigation. Independent metric recomputation took **{commands[commands.log=='independent_audit.log'].seconds.iloc[0]:.3f} seconds**, with zero fits.

## Demonstrated defect, verification and preservation

Version 1 exited **1**, before any model fit, because assigning Boolean flags to BDG2's integer `target_was_missing` column coerced it to an object-valued feature matrix and NumPy's finite-value check failed. The focused fix explicitly retains the binary flag as numeric 0/1 before causal injection. It changes representation, not values, memberships, events, models or settings.

Three integer/float/Boolean flag tests passed. A no-fitting real-data reproduction checked 13,002 rows × 22 features across ten buildings: the original TypeError reproduced, corrected values matched the original numeric view exactly, and zero corruption reproduced clean features. The earlier 27 operational/journal regression checks passed; all five final independent-audit/materialization tests passed. The failed logs, source identity and empty unit manifest remain under version 1; version 2 has a new source identity and directory. No previous completed pilot result is invalidated: the forecasting pipeline does not use this operational feature function, and the previous synthetic fixture did not contain this adapter covariate.

Production validation: {built['candidate_fold_cells']}/18 inner cells, {built['stream_hash_pairs']}/90 inner pairs, {built['outer_stream_hash_pairs']}/{len(outer)*5} outer pairs and {built['persisted_streams_recomputed']} persisted streams passed. Independent validation recomputed {verification['contribution_rows']:,} original-row contributions, {verification['event_channel_records']:,} event/channel records and {verification['bootstrap_cells']} confidence-bound cells, checked all declared surface metrics, per-building workloads, channel attribution, recovery, selection and paired draws, and verified all 15 preflight catalogues. Resume completed with fitting routes forbidden and {resume['unit_files_byte_identical']} files unchanged. [Verification record](smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/validation.json), [resume proof](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/resume_validation.json).

All 942 entry evidence/protocol files and the previous publication bundle remain unchanged. The old snapshot's 554 data/result files remain byte-identical; its 19 earlier report annotations remain unchanged since entry. Main and the previous review branch retain their original heads. [Preservation proof](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/preservation.json). The original completed forecasting pilot is preserved.

## Single next justified step

**Remove the duplicate completed-checkpoint table materialization, then verify the same preserved BDG2 unit with zero fits.** Introduce a file/hash-only completeness check for the second verification pass, retain corruption/provenance checks, and measure the resulting resume peak against the observed 4.422 GiB. This is a bounded checkpoint implementation/verification follow-up and requires no additional real-data fitting or changes to the selected/abstained result. A new real-data unit or full study should not launch automatically. The current task leaves the evaluated source and completed checkpoint immutable for review.

The [evidence index](review/bdg2_operational_pilot_20260913/EVIDENCE_INDEX.md) links exact files and purposes, including the two canonical metric CSVs and their independently recomputed counterparts. [BDG2 attribution and derived-data notice](review/bdg2_operational_pilot_20260913/DATA_NOTICE.md).

The 150,246,039-byte inner `streams.csv.gz` exceeds [GitHub's ordinary 100 MiB file limit](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). All of its bytes are published as four ordered binary parts with a [SHA-256 manifest](smart_building_conformal/outputs/amendment004/bdg2_pilot_publication_v1/large_files.json). The index provides the reconstruction command, which preserves the original gzip bytes and completed-checkpoint hash. The original local file is unchanged; no manual CSV upload is needed. Other canonical files are published directly.
'''
    (ROOT/'BDG2_OPERATIONAL_PILOT_REPORT.md').write_text(text,encoding='utf-8')
    print('Completed report written from passing validation and actual exit records.')

if __name__=='__main__':main()
