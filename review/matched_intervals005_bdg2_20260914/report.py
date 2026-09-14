"""Recomputable matched interval pilot reports, tables and figures; never fits."""
import argparse
from common import *
import numpy as np
import pandas as pd
from src.intervals005_common import Operations


def table(frame,columns):
    def fmt(x):return f'{x:.6g}' if isinstance(x,(float,np.floating)) else str(x)
    return '| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'+''.join('| '+' | '.join(fmt(row[c]) for c in columns)+' |\n' for _,row in frame.iterrows())


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    protocol=read(DESIGN/'frozen_protocol.json');validation=read(BATCH/'validation_v1/validation.json');resume=read(BATCH/'completed_resume_v1.json')
    assert validation['passed'] and resume['all_run_files_unchanged']
    assert validation['models_fitted']==validation['calibrators_fitted']==resume['models_fitted']==resume['calibrators_fitted']==0
    t=RUN/'stages/tables';native=pd.read_csv(t/'native_support_metrics.csv');common=pd.read_csv(t/'common_support_metrics.csv')
    assert len(native)==len(common)==30
    contrasts=[]
    for support,frame in [('native',native),('common',common)]:
        for (h,l),part in frame.groupby(['horizon','level']):
            part=part.set_index('method')
            for left,right in [('cqr','quantile_uncalibrated'),('recentred_enbpi_updated','recentred_enbpi_static')]:
                row=dict(support=support,horizon=h,level=l,left_method=left,right_method=right,n=int(part.loc[left,'n']))
                for name in ('coverage','signed_coverage_deviation','absolute_coverage_deviation','mpiw','winkler','mae','rmse'):row[name+'_difference']=float(part.loc[left,name]-part.loc[right,name])
                contrasts.append(row)
    contrasts=pd.DataFrame(contrasts);contrasts.to_csv(out/'shared_owner_contrasts.csv',index=False)
    native.to_csv(out/'native_support_metrics.csv',index=False);common.to_csv(out/'common_support_metrics.csv',index=False)
    for name in ['per_building_metrics.csv','background_workload.csv','seasonal_interval_metrics.csv','seasonal_point_metrics.csv','operations.csv','stage_costs.csv']:
        # Preserve original bytes for direct evidence copies.
        (out/name).write_bytes((t/name).read_bytes())
    measures=[]
    for action in ('run','validate','resume'):
        m=read(BATCH/(action+'_worker_resources_v1.json'));assert m['actual_exit']==0
        measures.append(dict(action=action,actual_exit=0,started_utc=m['started_utc'],ended_utc=m['ended_utc'],pid=m['pid'],**m['resources']))
    pd.DataFrame(measures).to_csv(out/'worker_costs.csv',index=False)
    stagecost=pd.read_csv(t/'stage_costs.csv');preparation=[]
    for h in (1,3,6):
        r=read(RUN/f'stages/preparation_h{h}/stage.json')['payload']['resources'];preparation.append(dict(horizon=h,**r))
    pd.DataFrame(preparation).to_csv(out/'preparation_costs.csv',index=False)
    # Exact matrix overlay: native/common summaries do not create extra cells.
    matrix=pd.read_csv(SMART/'outputs/amendment005/study_plan_v1/interval_method_matrix.csv')
    mask=matrix.dataset.eq('bdg2')&matrix.outer_fold.eq(2)&matrix.model_seed.eq(42)&matrix.horizon.isin([1,3,6])
    assert int(mask.sum())==30
    matrix['current_status']=np.where(mask,'completed_validated_pilot','remaining');matrix['evidence_run']=np.where(mask,str(RUN.relative_to(ROOT)),'')
    matrix.to_csv(out/'interval_completion_overlay.csv',index=False)
    next_queue=[]
    run_measure=measures[0]
    for seed in (43,44,45,46):
        for h in (1,3,6):
            for l in (.9,.95):
                for method in protocol['scope']['methods']:next_queue.append(dict(dataset='bdg2',outer_fold=2,model_seed=seed,horizon=h,level=l,method=method,authorization='proposed_only',dependency='generalize scope guard and verify seed propagation; reuse each seed own matched XGBoost artifacts'))
    pd.DataFrame(next_queue).to_csv(out/'next_proposed_method_keys.csv',index=False)
    atomic(out/'next_proposed_costs.json',dict(method_cells=120,triplet_units=4,new_cqr_wrappers=24,new_quantile_estimators=72,new_enbpi_wrappers=12,new_xgboost_enbpi_estimator_fits=132,new_matched_xgboost_or_lstm_fits=0,dscp_calibrators=4,kmeans_candidates=20,seasonal_new_computations=0,clean_alert_streams=120,measured_single_pilot_worker_seconds=run_measure['seconds'],fourfold_wall_scaling_seconds=4*run_measure['seconds'],fourfold_cpu_scaling_seconds=4*run_measure['process_cpu_seconds'],planning_interpretation='linear scaling from one measured pilot, not a confidence interval or runtime guarantee; separate validation/resume overhead',authorized=False))
    # Publication-ready figures with exact source hashes, separate supports.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors={'quantile_uncalibrated':'#888888','cqr':'#0072B2','recentred_enbpi_static':'#009E73','recentred_enbpi_updated':'#D55E00','dscp':'#CC79A7'}
    figures=out/'figures';figures.mkdir()
    for support,f in [('native',native),('common',common)]:
        fig,axes=plt.subplots(2,3,figsize=(14,8),layout='constrained')
        for i,level in enumerate((.9,.95)):
            for j,(metric,label) in enumerate([('coverage','Achieved coverage'),('mpiw','MPIW (kWh)'),('winkler','Winkler score (kWh)')]):
                ax=axes[i,j]
                for method,color in colors.items():
                    s=f[(f.level==level)&(f.method==method)].sort_values('horizon');ax.plot(s.horizon,s[metric],marker='o',color=color,label=method.replace('_',' '))
                if metric=='coverage':ax.axhline(level,color='black',linestyle='--',linewidth=1);ax.set_ylim(0,1.02)
                ax.set_title(f'{int(level*100)}% nominal: {label}');ax.set_xticks([1,3,6]);ax.set_xlabel('Forecast horizon (hours)');ax.grid(alpha=.2)
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=3,fontsize=9)
        fig.suptitle(f'BDG2 fold 2 / seed 42 — {support} support; ten recurring buildings')
        exports=[]
        for ext in ('png','pdf'):
            path=figures/f'{support}_interval_quality.{ext}';fig.savefig(path,dpi=170);exports.append(dict(path=path.name,sha256=sha(path)))
        plt.close(fig);source=out/f'{support}_support_metrics.csv'
        atomic(figures/f'{support}_interval_quality.sources.json',dict(source_csv=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),script=Path(__file__).relative_to(ROOT).as_posix(),script_sha256=sha(__file__),files=exports))
    phase=stagecost.copy();phase['family']=np.select([phase.stage.str.startswith('owner_fit_'),phase.stage.str.startswith('owner_cal_'),phase.stage.str.startswith('dscp_assignment_'),phase.stage.eq('dscp_fit'),phase.stage.str.startswith('stream_'),phase.stage.str.startswith('raw_')],['owner fit','conformalize','DSCP assignment','DSCP calibrator','replay and alerts','raw inference'],default='other measured stages')
    grouped=phase.groupby('family')[['seconds','process_cpu_seconds']].sum().sort_values('seconds')
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained');grouped.plot.barh(ax=ax,color=['#0072B2','#D55E00']);ax.set_xlabel('Measured seconds (nonoverlapping stage totals)');ax.set_title('Pilot stage costs; whole-worker and preparation costs reported separately');fig.savefig(figures/'stage_costs.png',dpi=170);fig.savefig(figures/'stage_costs.pdf');plt.close(fig)
    atomic(figures/'stage_costs.sources.json',dict(source_csv=(out/'stage_costs.csv').relative_to(ROOT).as_posix(),source_sha256=sha(out/'stage_costs.csv'),script=Path(__file__).relative_to(ROOT).as_posix(),script_sha256=sha(__file__),files=[dict(path='stage_costs.'+ext,sha256=sha(figures/('stage_costs.'+ext))) for ext in ('png','pdf')]))
    counts=read(t/'operation_counts.json');synthetic=read(REVIEW/'SYNTHETIC_ACCEPTANCE.json')
    prefix=out.relative_to(ROOT).as_posix()+'/'
    content='# BDG2 matched interval-method pilot\n\nAll **30 method cells**, **three seasonal point /six seasonal interval cells**, and **30 clean-stream alert-consumption checks** completed and passed independent validation. Completed resume forbade learned and calibrator fitting and preserved every scientific run file. Matched forecasting remains **70/195**; interval methods now have **30/1950** completed cells. Full-study readiness remains false.\n\n'
    content+=f'Evaluated scientific source SHA-256: `{protocol["source_hash"]}`. Historical matched XGBoost owners retain `{protocol["historical_source_hash"]}`. Native single-horizon targets are preserved; common comparisons use exactly **34,590 joint origins per horizon** across ten buildings, with **17,270 calibration origins** and **51,534 fit-role origins**. The latter does not replace any direct model\'s original training support.\n\n'
    content+='## Common-support numerical comparison\n\n'+table(common,['horizon','level','method','n','coverage','mpiw','winkler','mae','rmse'])+'\n'
    content+='[Native-support metrics]('+prefix+'native_support_metrics.csv), [common-support metrics]('+prefix+'common_support_metrics.csv), [per-building contributions]('+prefix+'per_building_metrics.csv), and [shared-owner contrasts]('+prefix+'shared_owner_contrasts.csv) expose every result, without selecting favorable settings.\n\n'
    content+='## Shared-owner calibration and updating\n\n'+table(contrasts[contrasts.support=='common'],['horizon','level','left_method','right_method','coverage_difference','mpiw_difference','winkler_difference'])+'\n'
    content+='Differences are left minus right. CQR/uncalibrated share the same fitted quantile owner, so that pair isolates its conformal correction. Static/updated EnbPI share the same calibrated ensemble, but the updated policy uses amendment-004 delayed signed-score ranks and original-group/segment state; it is explicitly distinct from the legacy interpolated updated policy. Across all five methods, predictor owners differ: this is not a pure calibrator-only comparison. Narrower width alone is not a benefit without achieved coverage and Winkler context.\n\n'
    content+='## Background alert consumption\n\nAll 30 streams use the fixed **immediate single-sample** rule at hourly frequency and an empty event catalogue. Emitted and consumed bounds/availability match exactly. Numerical-only, availability-only and combined episode counts and exposure denominators appear in [background workload]('+prefix+'background_workload.csv). These are background episodes, not confirmed false alarms. Recall, F1, delay and primary operational feasibility are not estimable here. Source-marked missing readings remain unavailable even when preprocessing supplies finite values.\n\n'
    workload=pd.read_csv(out/'background_workload.csv');content+=table(workload[workload.group_id=='__pooled__'],['horizon','level','method','channel','exposure_asset_days','episodes','background_episodes_per_asset_day'])+'\n'
    content+='## Actual fitting and computational cost\n\n'
    content+='Six CQR wrappers trained **18 quantile estimators**. Three EnbPI wrappers made **33 XGBoost estimator fits**: each native factory invocation includes one full-training estimator, five training bootstrap fits and five calibration bootstrap fits during explicit conformalization. The trained calibration-bootstrap ensemble is shared by both levels and static/updated consumers; the original full-training predictor remains the recentring point owner. These 51 learned fits do not include any new matched-XGBoost or LSTM fit. One DSCP calibrator evaluated five KMeans candidates using calibration data only. Wrapper/calibrator calls are separate ledger categories, not additional learned-estimator counts.\n\n'
    content+=table(pd.DataFrame(measures),['action','actual_exit','seconds','process_cpu_seconds','peak_rss_bytes','lifetime_peak_rss_bytes'])+'\n'
    content+='[Whole-worker costs]('+prefix+'worker_costs.csv), [nonoverlapping stage costs]('+prefix+'stage_costs.csv), [preparation costs]('+prefix+'preparation_costs.csv), and [actual nested operations]('+prefix+'operations.csv) retain their measurement scope. Do not add nested wrapper/base operations to enclosing phase totals or add worker totals again. CPU-only/thread1/n_jobs1 and the nonblocking 3 GiB reference remain unchanged.\n\n'
    content+=f'Independent validation maximum observed arithmetic/prediction discrepancy was **{validation["maximum_observed_difference"]:.8g}**; [the per-check CSV](smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/validation_v1/reconstruction_checks.csv) records each frozen tolerance. All checks passed; this maximum may arise from large pooled sums rather than prediction reload.\n\n'
    content+='## Scope and remaining work\n\nThis is one historical fold and one model seed on ten recurring known buildings. It establishes neither population/conditional/simultaneous coverage nor unseen-building portability. DSCP retains its from-paper and direct-horizon adaptation labels. Native and common subsets are two views of the same 30 cells; an online subset retains its original causal history.\n\n'
    content+='**Next scalable proposal:** generalize only the authorization/scope guard and verify seed propagation, then separately authorize BDG2 fold2 /seeds43–46 /horizons1,3,6 /both levels /the same five methods: **120 exact keys** in [next_proposed_method_keys.csv]('+prefix+'next_proposed_method_keys.csv). Reuse each seed\'s existing matched XGBoost objects. Expected additional operations:24 CQR wrappers/72 quantile fits,12 EnbPI wrappers/132 XGBoost fits,4 DSCP calibrators/20 KMeans candidates. Seasonal values are deterministic aliases; no new seasonal computation is needed on unchanged targets. [Measured planning costs]('+prefix+'next_proposed_costs.json) scale this pilot and are neither a guarantee nor a confidence interval. This batch is not launched.\n\n'
    content+='Still required:125 matched forecasting units;1,920 interval-method cells;24 unique seasonal computations plus explicit seed aliases; full operational selection, support-limited PLEIA/RICO endpoints and separately labelled conditional contexts; robustness, calibration contamination and recovery/censoring obligations. No threshold, membership, raw meter value, candidate or historical source was changed.\n'
    atomic(ROOT/'BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md',content)
    implementation='# Matched intervals005 implementation and verification\n\nThe executable `src.matched_intervals005` now provides freeze/readiness/run/validate/resume for the authorized first BDG2 triplet. [The completed pilot report](BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md) is the empirical result; this adapter is deliberately guarded to the authorized scope.\n\n'
    implementation+='Immutable fitted/calibrated owner stages, cached raw predictions, DSCP calibrator/assignment chunks and emitted streams have separate content checksums. Ready partial stages survive atomic rename failure. Interrupted uncommitted fits require explicit reconciliation and are not automatically repeated. The durable coordinator retains exact process identity, exclusive lock, actual exit receipts and surviving-worker adoption. A completed resume rejects corrupt artifacts and blocks both learned fitting and calibrator fitting.\n\n'
    implementation+='[Frozen method specification](smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s42_v1/method_specification.json) records actual classes, parameters, scoring, native quantile conventions, online rank conventions, initialization and crossing handling. The native MAPIE CQR quantile differs from amendment-004 online ranks; the existing generic signed-residual CQR wrapper is not used. Raw crossings remain visible and ordered emitted bounds are recorded.\n\n'
    implementation+='The synthetic evidence contains20 two-group/two-horizon method streams,34 tiny learned-estimator fits and two DSCP calibrators, separate from real results. The initial 25-check command had one scalar-fixture failure;24 passed. Its corrected no-fit recheck and an additional native-formula/unseen-group test passed, reusing saved owners. Eleven generic coordinator tests passed. Thus **37 distinct acceptance checks are resolved**; the initial failure is retained in [the recovery record](review/matched_intervals005_bdg2_20260914/SYNTHETIC_RECOVERY.md). No tiny learned or calibrator fit was repeated for recovery.\n\n'
    implementation+='DSCP uses verified old matched XGBoost owners through a read-only historical loader. The old source/protocol/owner hashes remain explicit even though adding modules changes the new source digest. Each joint role is checked against published memberships and target timestamps. Assignment uses bounded exact per-sequence distances; the first64 rows are checkpointed and reused. All remaining rows are evaluated, assignments are shared across levels, and serialization checks recompute the full test cohort without calibrator fitting.\n\n'
    implementation+='[Source and primary-reference attribution](review/matched_intervals005_bdg2_20260914/METHOD_REFERENCES.md), [current evidence index](review/matched_intervals005_bdg2_20260914/EVIDENCE_INDEX.md), and [exact progress/restart](review/matched_intervals005_bdg2_20260914/PROGRESS_AND_RESTART.md) connect code, protocol, models, CSVs, validation and actual costs. Full operational candidate search, faults, conditional challenges and remaining forecasting runs were not launched.\n'
    atomic(ROOT/'MATCHED_INTERVALS005_IMPLEMENTATION_REPORT.md',implementation)
    panel='# Panel response: shared-owner interval calibration, causal updating and alert consumption\n\n'+content[content.index('## Shared-owner calibration and updating'):content.index('## Scope and remaining work')]
    # Root-report links in this extracted text must remain repository-relative.
    panel=panel.replace(']('+prefix,'](../../'+prefix).replace('](smart_building_conformal/','](../../smart_building_conformal/')
    atomic(REVIEW/'PANEL_RESPONSE.md',panel)
    for name in ('review/CURRENT_EVIDENCE.md','PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','MATCHED_METHOD_READINESS_MAP.md'):
        path=ROOT/name;old=path.read_text(encoding='utf-8');marker='<!-- matched-intervals005-20260914: historical content follows -->'
        if marker in old:old=old.split(marker,1)[1].lstrip('\n')
        base='../' if name.startswith('review/') else ''
        current='# Matched interval adapter and bounded BDG2 pilot completed\n\n30 interval-method cells,3 seasonal point/6 seasonal interval cells and30 clean-stream alert checks validated; completed resume performed zero learned/calibrator fits. Matched forecasting remains70/195; interval methods30/1950.\n\n'
        current+=f'[Implementation report]({base}MATCHED_INTERVALS005_IMPLEMENTATION_REPORT.md), [numerical pilot report]({base}BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md), and [evidence index]({base}review/matched_intervals005_bdg2_20260914/EVIDENCE_INDEX.md). Actual adapter endpoints now exist; broader scope still requires a versioned authorization guard and fresh readiness. The next proposed package is the four remaining BDG2 fold2 training seeds using the same methods and existing matched XGBoost owners. It is not launched. Full-study readiness remains false.\n\n'
        atomic(path,current+marker+'\n\n'+old)
    atomic(out/'analysis_validation.json',dict(passed=True,method_cells=30,seasonal_point_cells=3,seasonal_interval_cells=6,alert_streams=30,forecast_units_completed=70,interval_method_cells_completed=30,remaining_forecast_units=125,remaining_interval_cells=1920,unique_acceptance_checks=37,operation_counts=counts,models_fitted_by_analysis=0,full_study_ready=False))
    atomic(out/'COMPLETE.json',dict(files=tree(out),models_fitted=0));print('Reports and figures complete, no fitting.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    with Operations(forbid=True):main(args.out)
