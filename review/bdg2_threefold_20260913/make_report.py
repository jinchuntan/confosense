"""Render the completed report directly from audited, frozen-scope CSV evidence."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'smart_building_conformal/outputs/amendment004'
COMBINED=BASE/'bdg2_threefold_combined_v1'
COST=BASE/'bdg2_threefold_costs_v1'


def table(df,columns):
    def cell(v):
        if pd.isna(v):return 'unavailable'
        if isinstance(v,(float,np.floating)):return f'{v:.6g}'
        return str(v).replace('|',' / ').replace('\n',' ')
    return '| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'+''.join(
        '| '+' | '.join(cell(x) for x in row)+' |\n' for row in df[columns].itertuples(index=False,name=None))


def main():
    read=lambda p:pd.read_csv(p,float_precision='round_trip')
    plan=json.loads((BASE/'bdg2_threefold_frozen_v2/execution_analysis_manifest.json').read_text())
    m=read(COMBINED/'per_fold_operational_interval_metrics.csv');dec=read(COMBINED/'fold_decisions.csv')
    primary=dec[dec.selection=='primary'].copy();inverse=dec[dec.selection=='inverse']
    membership=read(BASE/'bdg2_threefold_frozen_v2/memberships.csv');support=read(COMBINED/'event_support.csv')
    outer_support=support[support.role=='outer_test'].groupby('outer_fold').agg(effective_events=('effective','sum'),minimum_distinct_onsets=('distinct_effective_onsets','min')).reset_index()
    first=primary.merge(membership[membership.role=='outer_test'],on='outer_fold').merge(outer_support,on='outer_fold')
    paired=read(COMBINED/'paired_contrasts.csv');pooled=read(COMBINED/'pooled_metrics.csv')
    recall_pair=paired[paired.metric=='macro_event_recall'].iloc[0]
    workload_pair=paired[paired.metric=='background_episodes_per_asset_day'].iloc[0]
    commands=read(COST/'command_measurements.csv');phases=read(COST/'phase_measurements.csv');cpu=read(COST/'process_measurements.csv')
    scope=json.loads((COST/'cost_scope.json').read_text());validation=[];resource=[];gates=[]
    for fold in [2,1,0]:
        root=BASE/Path(plan['units'][str(fold)]['out']).name
        audit=BASE/('bdg2_pilot_independent_validation_v1' if fold==2 else f'bdg2_threefold_f{fold}_audit_v{2 if fold==1 else 1}')
        v=json.loads((audit/'validation.json').read_text())
        resume=json.loads((BASE/'bdg2_pilot_validation_v1/resume_validation.json' if fold==2 else
                          BASE/f'bdg2_threefold_validation_v1/fold{fold}_resume_validation.json').read_text())
        validation.append(dict(outer_fold=fold,exit_status=0,inner_cells=v['candidate_fold_cells'],
            inner_pairs=v['inner_catalogue_pairs'],outer_cells=v['outer_metric_cells'],outer_pairs=v['outer_catalogue_pairs'],
            streams=v['persisted_streams'],contribution_rows=v['contribution_rows'],event_channel_records=v['event_channel_records'],
            resume_new_fits=resume['normal_completed_resume']['new_fit_invocations'],unchanged_unit_files=resume['unit_files_byte_identical']))
        runphase=phases[(phases.outer_fold==fold)&(phases.invocation=='run')]
        cmd=commands[commands.command_label==('pilot_v2' if fold==2 else f'fold{fold}_run')].iloc[0]
        process=cpu[cpu.outer_fold==fold].iloc[0]
        resource.append(dict(outer_fold=fold,command_seconds=cmd.seconds,cpu_seconds=process.total_cpu_seconds,
            peak_RSS_GiB=runphase.lifetime_peak_rss_bytes.max()/2**30,minimum_available_RAM_GiB=runphase.min_available_ram_bytes.min()/2**30))
        surface=read(root/f'units/outer{fold}_model42/surface.csv.gz')
        for cid,part in surface.groupby('candidate_id',sort=False):
            reasons=[]
            for r in part.to_dict('records'):
                if r['bound_status']!='supported': reasons.append(f"inner{r['inner_fold']}:unavailable_bounds")
                if r['recall_lcb']<.6: reasons.append(f"inner{r['inner_fold']}:recall")
                if r['workload_ucb']>1: reasons.append(f"inner{r['inner_fold']}:workload")
            gates.append(dict(outer_fold=fold,candidate_id=cid,failed_gates='; '.join(reasons) or 'none'))
    v=pd.DataFrame(validation);costs=pd.DataFrame(resource)
    channels=read(COMBINED/'pooled_stratum_channels.csv');a='c0012_23099bed3753';b='c0000_f5146f1247fa'
    channel_rows=[]
    for (family,severity),part in channels.groupby(['family','severity'],sort=False):
        def value(cid,ch):return part[(part.candidate_id==cid)&(part.channel==ch)].recall.iloc[0]
        assert value(a,'availability_only')==value(b,'availability_only')
        channel_rows.append(dict(family=family,severity=severity,shared_availability_recall=value(a,'availability_only'),
            uncal_numerical_recall=value(b,'numerical_only'),cqr_numerical_recall=value(a,'numerical_only'),
            uncal_combined_recall=value(b,'combined'),cqr_combined_recall=value(a,'combined')))
    group=read(COMBINED/'group_workload.csv')
    g=group.groupby(['outer_fold','candidate_id']).agg(min_W=('episodes_per_asset_day','min'),max_W=('episodes_per_asset_day','max'),
        buildings_above_1=('above_workload_ceiling','sum')).reset_index()
    chosen=int(primary.operational_feasible.sum())
    text=f'''# Three-fold BDG2 reduced-grid benchmark, model seed 42

**Primary operational feasibility: {chosen} of 3 outer units selected a configuration; {3-chosen} abstained.** These decisions come only from the two inner folds. All three original study commands completed with **exit status 0**. Both new units passed independent saved-stream reconstruction and normal completed-unit resume with **zero new fits**. Full-study readiness remains **false**.

This benchmark combines preserved fold 2 with the explicitly authorized fold-1 then fold-0 runs. It evaluates ten known BDG2 buildings, one-hour forecasts, model seed 42, five synthetic catalogue seeds and the identical nine reduced-grid candidates. It is not the full candidate/method, multi-task or five-model-seed study. The [evidence index](review/bdg2_threefold_20260913/EVIDENCE_INDEX.md) links the complete code, CSVs, source archives, commands and reconstruction instructions.

## Identity, freeze and preservation

Entry/publication ancestor: `d63251b75f5c70c4d51c19456fbec6724e712516`. The repair, compatibility evidence, both-unit manifest and paired-analysis code were committed before either new fit at **`18e5db5f2d81ed641ae90c5e257e512cf7ebbcc7`**. Both new units evaluated source SHA-256 **`{plan['source_hash']}`**. Fold 2 retains historical evaluated commit `ef9a8a9525bafea00a12b5c1327aadec071eab91` and source `8218d9f461811fa9075c2966c394cae2344ae61f073887ff356af82025c8f4e4`. Exact archived bytes avoid line-ending ambiguity.

The [joint manifest](smart_building_conformal/outputs/amendment004/bdg2_threefold_frozen_v2/execution_analysis_manifest.json) froze both new units and the combined estimands before either fit. Configuration hash: `{plan['config_hash']}`. Feature/data hash: `{plan['data_hash']}`. Outcome hash: `{plan['outcomes_hash']}`. All **39 role memberships, 18 boundaries, 45 catalogues and 189 stratum-support cells** were checked against the published preflight without fitting. Every new launch also regenerated and verified its 15 catalogues. The initial no-fit freeze attempt exited at the unchanged 3 GiB RAM guard; after unused applications were closed, the successful freeze passed. No model had been fitted in that failed attempt.

The [memory repair report](CHECKPOINT_MEMORY_REPAIR_REPORT.md) records unchanged fold-2 values, 30 byte-identical unit files, zero fits, 28 required CSV parses and zero parses during completeness checking. The repaired comparable scope peaked at **2.817 GiB RSS**, versus historical resume's **4.422 GiB**; current-machine host availability differs and no universal reduction is promised. Production training resume continues to reject a changed source identity. No old manifest was rewritten, and fold 2 was not refitted. Main, historical results, the forecasting pilot and backups remain preserved; the old [fold-2 report](BDG2_OPERATIONAL_PILOT_REPORT.md) is unchanged.

## Per-fold dates, support and decisions

Fold IDs run backward in time: fold 2 is earliest, fold 0 latest. The ten buildings recur across periods. Asset-days use eligible observed hourly rows, not five times those rows for five catalogues. Event counts pool the five actual catalogues; distinct-onset minima deduplicate building/onset within each of 21 strata.

{table(first,['outer_fold','target_min','target_max','n','groups','asset_days','effective_events','minimum_distinct_onsets','decision','candidate_id'])}

Primary feasibility requires supported bounds, recall LCB >=0.60 and workload UCB <=1.0 in **both** inner folds, using the unchanged 2,000 shared whole-building bootstrap draws, seed 20240601 and minimum 1,900 valid replicates. Utility is equal-fold custom synthetic F1, with the original delay/workload/ID ties. That custom utility allocates unmatched episodes uniformly across 21 strata and is distinct from ordinary matched-event/episode precision. No outer result changes a threshold, grid, catalogue or decision. Every candidate's failed gates follow; exact numerical bounds and rejection strings remain in each saved surface and the [combined rejection CSV](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/rejections.csv).

{table(pd.DataFrame(gates),['outer_fold','candidate_id','failed_gates'])}

The secondary inverse recall-floor selector is separate and removes the workload ceiling only for its own declared objective. Its `operational_feasible` flag does not establish primary feasibility. Independently selected components, shared-fit controlled components and persistence remain separately identified in the [actual comparison ledger](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/outer_comparisons.csv).

{table(inverse,['outer_fold','decision','candidate_id'])}

## Per-fold outer operational and interval results

All frozen candidates use .95 intervals. Candidate `c0000_f5146f1247fa` is static immediate uncalibrated; `c0012_23099bed3753` is static immediate CQR; `c0013_a21278d4e492` is static CQR, 180-minute 3-of-3; `c0024_ba16b82adffd` is immediate CQR rolling every 12 origins with window 200. Other evaluated IDs retain their exact settings in the ledger. Persistence is the fixed .95 split-conformal lag-0 diagnostic, with zero learned fits. The 360-minute 4-of-6 candidate remains in inner selection even where it is not requested for outer evaluation.

The operational predictor is the CQR-owned HistGradientBoosting quantile model. Uncalibrated controls share its fit. It is not the separate Attention-LSTM or point XGBoost comparison. Recall is the equal-weight mean across 21 family/severity strata; workload W is clean-background episodes per original asset-day, not adjudicated real-world false-alarm rate. Coverage is a fraction; MPIW and Winkler95 are in kWh per hourly observation. Clean interval metrics weight observed rows. The full CSV also retains point MAE/RMSE, ordinary matched-event/episode precision, custom synthetic F1, misses and censored-delay accounting.

{table(m,['outer_fold','candidate_id','strategy','rule_id','macro_event_recall','background_episodes_per_asset_day','empirical_coverage','mpiw_kWh','winkler95_kWh'])}

No diagnostic substitutes for an abstained primary pipeline. Outer workload violations remain outcomes. Logged ill-sorted quantile notices are handled by the pre-existing CQR interval-order repair; the independently checked metrics use the actual issued bounds. No new interval sorting or calibration change was introduced. Temporal aggregation's changes in workload and detection are properties of these frozen physical rules and event envelopes; they did not trigger a software fix or retuning.

## Pooled results and frozen paired contrast

All **{int(m.groupby('outer_fold').observed_rows.first().sum()):,} outer rows are disjoint** across the three test periods. Pooled W sums original clean episode counts and divides by original eligible asset-days. Pooled macro recall first sums N and TP separately within each of the 21 strata across folds/catalogues, then averages the 21 recalls equally. These are not unlabelled averages of fold percentages. Only identical candidate settings are pooled; the CSV explicitly flags any candidate not evaluated in all three folds. Interval quality below weights original observed rows; pooled RMSE is the square root of weighted squared RMSE.

{table(pooled,['candidate_id','outer_folds','all_three_folds','asset_days','n_events','macro_event_recall','background_episodes_per_asset_day','empirical_coverage','mpiw_kWh','winkler95_kWh'])}

The main exploratory paired contrast was frozen as **static immediate CQR minus static immediate uncalibrated quantiles**. Recall and workload changes must be interpreted together; a workload decrease is not a same-recall improvement. The [per-fold differences](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/paired_per_fold.csv) accompany the pooled contrast.

{table(paired,['metric','estimate_a','estimate_b','difference_a_minus_b','ci_lower','ci_upper','valid_replicates','interval_status'])}

Static CQR's pooled recall changed by **{100*recall_pair.difference_a_minus_b:.3f} percentage points**, with an approximate interval of **[{100*recall_pair.ci_lower:.3f}, {100*recall_pair.ci_upper:.3f}] points**, while clean workload changed by **{workload_pair.difference_a_minus_b:.3f} episodes/asset-day**, interval **[{workload_pair.ci_lower:.3f}, {workload_pair.ci_upper:.3f}]**. The recall change was negative in fold 2 and positive in folds 1 and 0. The interval spanning zero does not establish equal recall. The static CQR workload remains above 1.0 in every outer fold, and all primary inner-selection decisions remain abstentions.

These optional intervals use 2,000 paired draws of **ten original buildings**, with all each building's fold/catalogue contributions kept together. Seed 42 is the only model seed. The saved [count inputs](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/original_building_contributions.csv), draws and replicate differences permit exact recomputation. Three periods do not create 30 independent buildings, and five catalogues do not create five model seeds. Intervals are approximate, conditional and exploratory; no confirmatory significance, equivalence or population-wide superiority claim is made.

## Channel attribution, misses, recovery and local workload

The table reports every pooled family/severity stratum for the main controlled pair. Availability-only detection is exactly shared by the two immediate baselines; it must not be credited to conformal calibration. Numerical and combined channels are separate. The [full channel CSV](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/stratum_channel_metrics.csv) retains each fold, inner role and every actually evaluated comparison, including temporal and persistence.

{table(pd.DataFrame(channel_rows),list(channel_rows[0]))}

Misses remain in recall and restricted mean detection time; detected-only delay quantiles do not replace them. Episode starts are matched one-to-one at target-observation time, and pre-active episodes get no onset credit. Full scheduled tolerance is required. [Recovery records](smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/recovery.csv.gz) retain right censoring and follow-up; return toward pre-injection coverage is descriptive, not guaranteed restoration of nominal coverage.

Building-specific burden remains visible:

{table(g,['outer_fold','candidate_id','min_W','max_W','buildings_above_1'])}

## Actual verification and cost

{table(v,list(v.columns))}

The two new audits independently reconstruct metrics, bounds and selection from saved streams, events, original-row contributions and actual resampling draws. Outer counts are derived from each actual decision/ledger. The preserved fold-2 independent audit remains unchanged and its newly read values are compatible. Both new normal resumes forbid fitting/computation routes and preserve all 30 unit files. Focused/shared-consumer regression, authorization, paired-count and recovery-arithmetic tests passed **58 distinct checks** (62 executions including four focused repeats); three existing MAPIE warnings remain. None of these engineering checks alone establishes scientific readiness.

The first fold-1 independent audit exited **1** on recovery censoring, and its failed output/log remain preserved. The [no-fit diagnosis](smart_building_conformal/outputs/amendment004/bdg2_threefold_validation_v1/recovery_numerics.json) demonstrated fractional-convolution rounding in the independent checker: an all-covered window became 0.9999999999999999, while the saved compensated rolling mean was exactly 1.0. Against a pre-coverage value of .95, this crosses the literal floating-point `<=.05` comparison. Integer prefix counts divided once by window size exactly reproduce the saved rolling arithmetic and **all 250 outer recovery records**. Six candidate/catalogue/group cases had differing window decisions; four changed the erroneous audit censoring status. The checker was repaired and six focused checks passed, then the audit was rerun into a fresh version-2 directory. Production source, recovery threshold, primary feasibility gates and all 30 completed unit files stayed unchanged. This preserves the frozen floating-point boundary behavior; it does not introduce a favourable tolerance or invalidate the study result. Recovery at an exact mathematical boundary remains sensitive to the declared numerical convention.

{table(costs,list(costs.columns))}

The three nonoverlapping original study commands total **{scope['study_command_seconds']:.3f} s ({scope['study_command_seconds']/60:.2f} minutes)**, including historical fold 2 exactly once. The two newly authorized commands total **{scope['new_execution_seconds']:.3f} s**. Actual process CPU totals **{costs.cpu_seconds.sum():.3f} s**. There are **9 CQR fit objects / 27 quantile sub-estimators** across the three units; shared uncalibrated controls add no fits and persistence adds zero. This task added 6 objects / 18 sub-estimators and did not refit fold 2.

Separate command costs, including preserved failed verification attempts:

{table(commands[commands.scope!='study_execution'],['command_label','historical','seconds','exit_status'])}

Verification commands are separate scopes and may overlap each other; they are not added to the nonoverlapping study total or represented as end-to-end project elapsed time.

The prior 16.46-minute fold-2 measurement informed scheduling; the frozen 20-40-minute per-new-unit range was a planning estimate, not a substitute for these measurements. Numerical thread variables were all 1 in the existing environment, with sequential real fits and launch RAM/disk guards. Complete command/CPU/artifact tables and [nested phase measurements](smart_building_conformal/outputs/amendment004/bdg2_threefold_costs_v1/phase_measurements.csv) separate preparation, windows, identity, checkpoint and validation. Fit, calibration, replay and scoring are measured jointly per inner/outer block; their separate constituent times were not isolated. The checkpoint phase contains those blocks, so it must not be added to them. No memory peaks are added together. Resume, independent audits, compatibility, freezing and regression have separate actual command rows, including the failed no-fit guard attempt.

## Interpretation and remaining research scope

The design was declared after inspection of earlier evidence, and fold 2 was already inspected before this replication. The result assesses repeatability across historical periods for the same ten selected buildings. Later folds legitimately train on earlier historical observations; they are not independent prospective trials or unseen-building tests. Synthetic catalogue uncertainty, one model seed, selected buildings, possible within-site dependence, coarse hourly fault realizations and unadjudicated natural faults limit interpretation. Clean W measures monitoring workload, not established false-alarm truth. No disappointing result caused a change to incidence, thresholds, candidates, model parameters or rules.

The broader work still requires matched point/interval/computational comparisons across all declared tasks and horizons, including the panel's Attention-LSTM versus XGBoost question; the full candidate/method scope; and justified operational handling for PLEIA temperature, PLEIA energy and RICO. Their current six inner banks per task have zero structurally supported banks; BDG2 has six of six. They are not dropped, and incidence is not inflated to manufacture support. This benchmark does not authorize a full-grid, four-task, five-model-seed or 900-cell robustness launch.

The single next justified bounded step is a **no-fitting support-design audit for the three unsupported tasks**, using their existing data to determine whether defensible temporal memberships/exposure can support the unchanged scientific estimands, followed by a written amendment or explicit non-estimability decision before further operational fitting. The broader forecasting comparison remains required regardless of operational support. No next experiment was launched automatically.
'''
    (ROOT/'BDG2_THREEFOLD_BENCHMARK_REPORT.md').write_text(text,encoding='utf-8')
    print('Wrote complete report from audited evidence')


if __name__=='__main__':main()
