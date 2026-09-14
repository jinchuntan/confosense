"""No-fit aggregation, figures, acceptance, and evidence-facing reports."""
import json, math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from common import *

METHODS=['quantile_uncalibrated','cqr','recentred_enbpi_static','recentred_enbpi_updated','dscp']
LABELS={'quantile_uncalibrated':'Raw quantiles','cqr':'CQR','recentred_enbpi_static':'EnbPI static','recentred_enbpi_updated':'EnbPI updated','dscp':'DSCP'}

def frame(path):return pd.read_csv(path,float_precision='round_trip',converters={'row_id':str,'group_id':str})
def write(path,value):value.to_csv(path,index=False,float_format='%.15g')

def figure(common_metrics,out,metric,ylabel):
    fig,axes=plt.subplots(1,3,figsize=(16,4.5),sharey=False)
    for ax,(dataset,part) in zip(axes,common_metrics.groupby('dataset',sort=False)):
        for level,style in ((.9,'-'),(.95,'--')):
            subset=part[part.level==level]
            for method in METHODS:
                m=subset[subset.method==method].sort_values('horizon')
                ax.plot(m.horizon,m[metric],marker='o',linestyle=style,label=f'{LABELS[method]} {int(level*100)}%')
            if metric=='coverage':ax.axhline(level,color='black',lw=.8,linestyle=style)
        ax.set(title=dataset,xlabel='Horizon (dataset sampling steps)',ylabel=ylabel);ax.grid(alpha=.25)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=5,fontsize=8,frameon=False);fig.tight_layout(rect=(0,.17,1,1))
    for suffix in ('png','pdf'):fig.savefig(out/f'remaining_settings_{metric}.{suffix}',dpi=180,bbox_inches='tight')
    plt.close(fig)

def main():
    state=read(BATCH/'progress.json')
    if state['status']!='science_complete':raise ValueError('analysis requires all scientific units complete')
    # Preserve v1: it exposed that the per-run workload table has no dataset
    # column.  v2 adds that immutable protocol identity while aggregating.
    out=BATCH/'analysis_v2'
    if out.exists():raise ValueError('preserve existing analysis')
    out.mkdir();figures=out/'figures';figures.mkdir()
    native=[];common=[];groups=[];workloads=[];operations=[];seasons=[];points=[];season_status=[];costs=[];validations=[];supports=[]
    expected_new=set()
    for unit in UNITS:
        root=run(unit);stage=root/'stages';complete=read(root/'COMPLETE.json');files=tree(root);files.pop('COMPLETE.json');assert files==complete['files']
        validation=read(BATCH/f'{unit["name"]}_validation/validation.json');resume=read(BATCH/f'{unit["name"]}_completed_resume.json')
        assert validation['passed'] and validation['method_cells']==unit['cells'] and validation['alert_stream_checks']==unit['cells']
        assert validation['models_fitted']==validation['calibrators_fitted']==0 and validation['source_artifacts_unchanged']
        assert resume['models_fitted']==resume['calibrators_fitted']==0 and resume['all_run_files_unchanged']
        validations.append(dict(dataset=unit['dataset'],**validation,zero_fit_resume=True))
        for collection,name in ((native,'native_support_metrics.csv'),(common,'common_support_metrics.csv'),(groups,'per_building_metrics.csv'),(workloads,'background_workload.csv'),(operations,'operations.csv')):
            value=frame(stage/'tables'/name)
            if name in ('background_workload.csv','operations.csv'):value['dataset']=unit['dataset']
            collection.append(value)
        seasons.append(frame(stage/'tables'/'seasonal_interval_metrics.csv'));points.append(frame(stage/'tables'/'seasonal_point_metrics.csv'));season_status.append(frame(stage/'tables'/'seasonal_applicability.csv'))
        proto=read(design(unit)/'frozen_protocol.json')
        for h,value in proto['support'].items():supports.append(dict(dataset=unit['dataset'],horizon=int(h),joint_fit=proto['joint_support']['fit'],joint_calibration=proto['joint_support']['calibration'],joint_test=proto['joint_support']['test'],frequency=value['frequency'],available_fit=value['available_by_role']['fit'],available_calibration=value['available_by_role']['calibration'],available_test=value['available_by_role']['test'],seasonal_available_test=value['seasonal_available_by_role']['test']))
        for action in ('run','validate','resume'):
            row=read(BATCH/f'{unit["name"]}_{action}_worker_resources.json')
            costs.append(dict(dataset=unit['dataset'],action=action,actual_exit=row['actual_exit'],**row['resources']))
        expected_new|={(unit['dataset'],2,42,h,l,m) for h in unit['horizons'] for l in (.9,.95) for m in METHODS}
    native=pd.concat(native,ignore_index=True);common=pd.concat(common,ignore_index=True);groups=pd.concat(groups,ignore_index=True);workloads=pd.concat(workloads,ignore_index=True);operations=pd.concat(operations,ignore_index=True)
    seasons=pd.concat(seasons,ignore_index=True);points=pd.concat(points,ignore_index=True);season_status=pd.concat(season_status,ignore_index=True);costs=pd.DataFrame(costs);validations=pd.DataFrame(validations);supports=pd.DataFrame(supports)
    keys=['dataset','outer_fold','model_seed','horizon','level','method']
    assert set(common[keys].itertuples(index=False,name=None))==expected_new and len(common)==len(native)==100
    old=SMART/'outputs/matched_intervals005/bdg2_f2_s42_v1/stages/tables'
    old_common=frame(old/'common_support_metrics.csv');all_seed42=pd.concat([old_common,common],ignore_index=True)
    expected_seed42={('bdg2',2,42,h,l,m) for h in (1,3,6) for l in (.9,.95) for m in METHODS}|expected_new
    assert len(all_seed42)==130 and set(all_seed42[keys].itertuples(index=False,name=None))==expected_seed42
    returned=operations[operations.event=='returned'];fits=returned.groupby('kind').size().rename('actual').reset_index()
    expected=dict(cqr_wrapper_fit=20,quantile_estimator_fit=60,enbpi_wrapper_fit=10,xgboost_estimator_fit=110,dscp_calibrator_fit=3,kmeans_candidate_fit=15,calibrator_conformalize=60)
    for kind,count in expected.items():assert int(fits.loc[fits.kind==kind,'actual'].iloc[0])==count,(kind,count)
    assert len(points)==6 and len(seasons)==12 and len(season_status[season_status.applicable==False])==4
    assert (costs.actual_exit==0).all() and len(costs)==9
    for name,value in [('native_support_metrics.csv',native),('common_support_metrics.csv',common),('all_seed42_common_support_metrics.csv',all_seed42),('per_building_metrics.csv',groups),('background_workload.csv',workloads),('operations.csv',operations),('fit_operation_counts.csv',fits),('worker_costs.csv',costs),('validation_summary.csv',validations),('joint_support_and_availability.csv',supports),('seasonal_point_metrics.csv',points),('seasonal_interval_metrics.csv',seasons),('seasonal_applicability.csv',season_status)]:write(out/name,value)
    for metric,label in [('coverage','Coverage'),('mpiw','Mean prediction interval width'),('winkler','Winkler score')]:
        figure(common,figures,metric,label)
        atomic(figures/f'remaining_settings_{metric}.sources.json',dict(figure=metric,generator=str(Path(__file__).relative_to(ROOT)),generator_sha256=sha(Path(__file__)),input_sha256=sha(out/'common_support_metrics.csv'),interpretation='Each panel uses one target scale. Dataset panels are not directly comparable when targets have different units.'))
    matrix=frame(SMART/'outputs/amendment005/study_plan_v1/interval_method_matrix.csv');matrix['status']='remaining';matrix['evidence_run']=''
    completed={('bdg2',2,s,h,l,m) for s in (42,43,44,45,46) for h in (1,3,6) for l in (.9,.95) for m in METHODS}|expected_new
    mask=matrix[keys].apply(tuple,axis=1).isin(completed);matrix.loc[mask,'status']='complete';matrix.loc[mask,'evidence_run']='matched_intervals005'
    assert int(mask.sum())==250
    write(out/'interval_completion_overlay.csv',matrix)
    pooled=workloads[(workloads.group_id.astype(str)=='__pooled__')&(workloads.channel=='combined')]
    report=['# Matched interval methods: remaining fold-2 seed-42 settings','', 'The authorized PLEIA-energy, PLEIA-temperature and RICO interval-method units are complete. The batch adds **100/100** new interval-method cells: 30 for each PLEIA target and 40 for RICO. With the existing BDG2 seed-42 run, the cross-setting seed-42 comparison contains **130 cells**. Every completed unit passed independent reconstruction and a completed forbidden-fit resume.','', 'Each method uses its own frozen native owner and its own 90%/95% stream. CQR retains its asymmetric native construction, EnbPI updated uses causal maturity-based replay, and DSCP uses only the matched historical XGBoost owners. No matched forecasting owner was refitted and no setting was retuned from outer-test outcomes.','', '## Coverage, width and score evidence','', '| dataset | horizons | joint fit / calibration / test origins | frequency | methods × levels |','|---|---|---:|---|---:|']
    for unit in UNITS:
        proto=read(design(unit)/'frozen_protocol.json');j=proto['joint_support'];report.append(f'| {unit["dataset"]} | {"/".join(map(str,unit["horizons"]))} | {j["fit"]:,} / {j["calibration"]:,} / {j["test"]:,} | {proto["support"][str(unit["horizons"][0])]["frequency"]} | {unit["cells"]} |')
    report += ['', 'Exact MAE, RMSE, coverage, MPIW and Winkler rows are in the linked CSVs. The three target panels keep their own scales; they do not support a numerical ranking across temperature and energy targets. Coverage and interval quality describe these fixed test partitions rather than population uncertainty estimates.', '', '![Coverage](smart_building_conformal/outputs/matched_intervals005/four_settings_f2_s42_v2_coordinator/analysis_v2/figures/remaining_settings_coverage.png)', '', '## Seasonal baselines and clean-stream alerts','', 'PLEIA energy and temperature each have daily-lag-144 seasonal-naive point baselines for three horizons and twelve split-conformal interval rows in total. RICO has four explicit not-applicable markers because its run segments do not contain a daily cycle; it was not given an invented daily baseline. All streams use original availability masks. The event catalogues are empty, so workload is reported as background episodes and time in alert only; recall, F1, delay and confirmed false-alarm rates are not estimable.', '', '## Computation and completion','', f'The batch recorded {expected["quantile_estimator_fit"]} quantile-estimator fits and {expected["xgboost_estimator_fit"]} EnbPI XGBoost fits ({expected["quantile_estimator_fit"]+expected["xgboost_estimator_fit"]} learned fits), plus three DSCP calibrators and 15 KMeans candidate fits. The nine run/validation/resume workers all exited 0. Their measured wall time was {costs.seconds.sum():.2f} seconds, CPU time {costs.process_cpu_seconds.sum():.2f} seconds, and peak worker lifetime RSS {costs.lifetime_peak_rss_bytes.max()/2**30:.3f} GiB.', '', 'The interval matrix is now **250/1950** complete, leaving **1700** cells. Matched forecasting remains 70/195. This is a bounded evidence update, not full-study completion.', '', '## Next implementation package','', 'Implement the prespecified broader conformal-method and alerting evaluation: add the remaining declared conformal variants and event-backed alert protocol to the supported matched settings, retaining fixed owners, causal observation delay, group isolation, and the frozen matrix. Do not launch it without a separate authorization.']
    atomic(ROOT/'MATCHED_INTERVAL_METHODS_REMAINING_SETTINGS_REPORT.md','\n'.join(report)+'\n')
    prefix='# Remaining fold-2 interval settings completed\n\nPLEIA energy, PLEIA temperature and RICO now contribute 100 independently validated interval-method cells at seed 42. The combined seed-42 cross-setting table has 130 cells; the full interval matrix is 250/1950.\n\n[Report](../MATCHED_INTERVAL_METHODS_REMAINING_SETTINGS_REPORT.md) and [evidence index](matched_intervals005_four_settings_20260914/EVIDENCE_INDEX.md).\n\n<!-- matched-intervals005-four-settings-20260914: historical content follows -->\n\n'
    for filename in ('CURRENT_EVIDENCE.md',):
        existing=(ROOT/'review'/filename).read_text(encoding='utf-8')
        if not existing.startswith('# Remaining fold-2 interval settings completed'):atomic(ROOT/'review'/filename,prefix+existing)
    for filename in ('PROJECT_RECOVERY_STATUS.md','MATCHED_METHOD_READINESS_MAP.md'):
        existing=(ROOT/filename).read_text(encoding='utf-8')
        if not existing.startswith('# Remaining fold-2 interval settings completed'):atomic(ROOT/filename,prefix.replace('../','')+existing)
    atomic(REVIEW/'PANEL_RESPONSE.md','# Numerical panel response: remaining interval settings\n\nThe response links all 100 new frozen cells, the combined 130-cell seed-42 table, independent validations, zero-fit resumes, background workload, seasonal applicability, and measured worker costs. No ranking is made across targets with different units, and empty-event streams remain limited to background workload.\n')
    result=dict(passed=True,new_method_cells=100,combined_seed42_method_cells=130,interval_methods_complete=250,interval_methods_remaining=1700,matched_forecasting_complete=70,new_learned_estimator_fits=170,new_dscp_calibrators=3,new_kmeans_candidate_fits=15,seasonal_point_cells=6,seasonal_interval_cells=12,rico_seasonal_not_applicable=4,independent_validations=3,zero_fit_completed_resumes=3,worker_exit_zero=9,models_fitted=0,calibrators_fitted=0,source_artifacts_unchanged=True,full_study_ready=False,utc=now())
    atomic(out/'analysis_validation.json',result);atomic(out/'COMPLETE.json',dict(files=tree(out),models_fitted=0,calibrators_fitted=0));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
