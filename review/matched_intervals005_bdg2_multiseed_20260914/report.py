"""No-fit five-seed aggregation, validation, figures and reports."""
import argparse,csv,json,math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import *

OLD_BATCH=SMART/'outputs/matched_intervals005/bdg2_pilot_v1_coordinator'
OLD_RUN=SMART/'outputs/matched_intervals005/bdg2_f2_s42_v1'
METHODS=['quantile_uncalibrated','cqr','recentred_enbpi_static','recentred_enbpi_updated','dscp']
LABELS={'quantile_uncalibrated':'Uncalibrated quantiles','cqr':'CQR','recentred_enbpi_static':'EnbPI static','recentred_enbpi_updated':'EnbPI updated','dscp':'DSCP'}

def frame(path):return pd.read_csv(path,float_precision='round_trip',converters={'row_id':str,'group_id':str})
def write_csv(path,value):value.to_csv(path,index=False,float_format='%.15g')

def summary(frame,metrics,groups):
    rows=[]
    for key,part in frame.groupby(groups,sort=True):
        row=dict(zip(groups,key if isinstance(key,tuple) else (key,)),n_seeds=len(part))
        for metric in metrics:
            values=part[metric].astype(float)
            row.update({f'{metric}_mean':values.mean(),f'{metric}_std':values.std(ddof=1),f'{metric}_min':values.min(),f'{metric}_max':values.max()})
        rows.append(row)
    return pd.DataFrame(rows)

def main(out):
    out=Path(out)
    if out.exists():raise ValueError('preserve existing analysis; choose unused directory')
    out.mkdir(parents=True);figdir=out/'figures';figdir.mkdir()
    native=[];common=[];buildings=[];workloads=[];operations=[];costs=[];oob=[];dscp=[];season_alias=[];validation_rows=[]
    for seed in [42,*SEEDS]:
        if seed==42:
            table=OLD_BATCH/'analysis_v1';root=OLD_RUN
            validation=read(OLD_BATCH/'validation_v5/validation.json');resume=read(OLD_BATCH/'completed_resume_v1.json')
            resources={'run':read(OLD_BATCH/'run_worker_resources_v1.json'),'validate':read(OLD_BATCH/'validate_worker_resources_v5.json'),'completed_resume':read(OLD_BATCH/'resume_worker_resources_v1.json')}
        else:
            root=run(seed);table=root/'stages/tables'
            validation=read(BATCH/f'seed{seed}_validation/validation.json');resume=read(BATCH/f'seed{seed}_completed_resume.json')
            resources={'run':read(BATCH/f'seed{seed}_run_worker_resources.json'),'validate':read(BATCH/f'seed{seed}_validate_worker_resources.json'),'completed_resume':read(BATCH/f'seed{seed}_resume_worker_resources.json')}
            for h in (1,3,6):
                alias=read(root/f'stages/seasonal_h{h}/alias.json');assert alias['requested_model_seed']==seed and alias['source_model_seed']==42 and alias['learned_fits']==0
                season_alias.append(dict(model_seed=seed,horizon=h,**alias))
        complete=read(root/'COMPLETE.json');files=tree(root);files.pop('COMPLETE.json');assert files==complete['files']
        assert validation['passed'] and validation['method_cells']==30 and validation['alert_stream_checks']==30 and validation['source_artifacts_unchanged']
        assert resume['models_fitted']==resume['calibrators_fitted']==0 and resume['all_run_files_unchanged']
        validation_rows.append(dict(model_seed=seed,passed=True,method_cells=30,alert_streams=30,maximum_observed_difference=validation['maximum_observed_difference'],models_fitted=0,calibrators_fitted=0,zero_fit_resume=True))
        for target,name in ((native,'native_support_metrics.csv'),(common,'common_support_metrics.csv'),(buildings,'per_building_metrics.csv'),(workloads,'background_workload.csv'),(operations,'operations.csv')):
            f=frame(table/name);f['model_seed']=seed;target.append(f)
        for action,record in resources.items():costs.append(dict(model_seed=seed,action=action,actual_exit=record['actual_exit'],**record['resources']))
        for h in (1,3,6):
            p=read(root/f'stages/owner_cal_h{h}_enbpi/stage.json')['payload'];oob.append(dict(model_seed=seed,horizon=h,calibration_rows=p['n_calibration'],nonfinite_oob_scores=p['nonfinite_native_scores'],finite_oob_scores=p['n_calibration']-p['nonfinite_native_scores']))
        metadata=read(root/'stages/dscp_fit/calibrator_metadata.json');proto=read((SMART/f'protocols/matched_intervals005/bdg2_f2_s{seed}_v{1 if seed==42 else 2}/frozen_protocol.json'))
        dscp.append(dict(model_seed=seed,n_clusters=metadata['n_clusters'],neighbours=metadata['neighbours'],silhouette=metadata['silhouette'],cluster_sizes=json.dumps(metadata['metadata']['cluster_sizes']),matched_owner_hashes=json.dumps({h:proto['references'][h]['owner_hashes']['model.ubj'] for h in ('1','3','6')},sort_keys=True)))
    native=pd.concat(native,ignore_index=True);common=pd.concat(common,ignore_index=True);buildings=pd.concat(buildings,ignore_index=True);workloads=pd.concat(workloads,ignore_index=True);operations=pd.concat(operations,ignore_index=True)
    keys=['dataset','outer_fold','model_seed','horizon','level','method'];expected={('bdg2',2,s,h,l,m) for s in [42,*SEEDS] for h in (1,3,6) for l in (.9,.95) for m in METHODS}
    assert len(native)==len(common)==150 and set(native[keys].itertuples(index=False,name=None))==expected and set(common[keys].itertuples(index=False,name=None))==expected
    metrics=['coverage','absolute_coverage_deviation','mpiw','winkler','mae','rmse']
    seed_summary=summary(common,metrics,['horizon','level','method'])
    contrasts=[]
    for seed in [42,*SEEDS]:
        part=common[common.model_seed==seed].set_index(['horizon','level','method'])
        for h in (1,3,6):
            for level in (.9,.95):
                for left,right in [('cqr','quantile_uncalibrated'),('recentred_enbpi_updated','recentred_enbpi_static')]:
                    a=part.loc[(h,level,left)];b=part.loc[(h,level,right)]
                    contrasts.append(dict(model_seed=seed,horizon=h,level=level,left_method=left,right_method=right,coverage_difference=a.coverage-b.coverage,absolute_gap_difference=a.absolute_coverage_deviation-b.absolute_coverage_deviation,mpiw_difference=a.mpiw-b.mpiw,winkler_difference=a.winkler-b.winkler))
    contrasts=pd.DataFrame(contrasts);contrast_summary=summary(contrasts,['coverage_difference','absolute_gap_difference','mpiw_difference','winkler_difference'],['horizon','level','left_method','right_method'])
    background_summary=summary(workloads[workloads.group_id=='__pooled__'],['episodes','background_episodes_per_asset_day','time_in_alert_fraction'],['horizon','level','method','channel'])
    pooled_background=workloads[(workloads.group_id=='__pooled__')&(workloads.channel=='combined')]
    cost_frame=pd.DataFrame(costs);new_cost=cost_frame[cost_frame.model_seed.isin(SEEDS)]
    returned=operations[operations.event=='returned'];fit_counts=returned.groupby(['model_seed','kind']).size().unstack(fill_value=0).reset_index()
    expected_counts={'cqr_wrapper_fit':6,'quantile_estimator_fit':18,'enbpi_wrapper_fit':3,'xgboost_estimator_fit':33,'dscp_calibrator_fit':1,'kmeans_candidate_fit':5,'calibrator_conformalize':18}
    for seed in [42,*SEEDS]:
        row=fit_counts[fit_counts.model_seed==seed].iloc[0]
        for name,value in expected_counts.items():assert row[name]==value,(seed,name,row[name])
    assert fit_counts[fit_counts.model_seed.isin(SEEDS)].quantile_estimator_fit.sum()==72
    assert fit_counts[fit_counts.model_seed.isin(SEEDS)].xgboost_estimator_fit.sum()==132
    matrix=frame(SMART/'outputs/amendment005/study_plan_v1/interval_method_matrix.csv');matrix['status']='remaining';matrix['evidence_run']=''
    mask=matrix[keys].apply(tuple,axis=1).isin(expected);matrix.loc[mask,'status']='complete';matrix.loc[mask,'evidence_run']=matrix.loc[mask,'model_seed'].map(lambda s:'bdg2_f2_s42_v1' if s==42 else f'bdg2_f2_s{s}_v2')
    assert mask.sum()==150 and (matrix.status=='complete').sum()==150
    remaining=frame(SMART/'outputs/matched_forecasting005/fold2_multiseed_batch_v1/analysis_v1/remaining_queue_updated.csv')
    proposal=remaining.head(3).copy()
    assert set(proposal[['dataset','horizon','outer_fold','model_seed']].itertuples(index=False,name=None))=={('pleia_energy',h,1,42) for h in (1,3,6)}
    proposal['authorized']=False;proposal['launched']=False
    measured=[]
    for h in (1,3,6):
        prior=read(SMART/f'outputs/matched_forecasting005/pleia_energy_h{h}_f2_s42_v1.process.json')
        measured.append(dict(horizon=h,source_outer_fold=2,source_fit_n={1:14858,3:14855,6:14850}[h],proposed_outer_fold=1,proposed_fit_n=int(proposal[proposal.horizon==h].iloc[0].fit_n),measured_source_run_seconds=prior['action_resources']['seconds'],measured_source_cpu_seconds=prior['process_lifetime_cpu_seconds'],scaled_run_seconds=prior['action_resources']['seconds']*int(proposal[proposal.horizon==h].iloc[0].fit_n)/{1:14858,3:14855,6:14850}[h]))
    measured=pd.DataFrame(measured)
    for name,value in [('native_support_metrics.csv',native),('common_support_metrics.csv',common),('per_building_metrics.csv',buildings),('background_workload.csv',workloads),('operations.csv',operations),('worker_costs.csv',cost_frame),('enbpi_oob_support.csv',pd.DataFrame(oob)),('dscp_summary.csv',pd.DataFrame(dscp)),('seasonal_aliases.csv',pd.DataFrame(season_alias)),('validation_summary.csv',pd.DataFrame(validation_rows)),('five_seed_summary.csv',seed_summary),('shared_owner_contrasts.csv',contrasts),('shared_owner_contrast_summary.csv',contrast_summary),('background_workload_summary.csv',background_summary),('fit_operation_counts.csv',fit_counts),('interval_completion_overlay.csv',matrix),('next_proposed_forecasting_units.csv',proposal),('next_proposed_measured_costs.csv',measured)]:write_csv(out/name,value)
    colors=dict(zip(METHODS,plt.get_cmap('tab10').colors))
    for metric,ylabel in [('coverage','Coverage'),('mpiw','MPIW (kWh)'),('winkler','Winkler score (kWh)')]:
        fig,axes=plt.subplots(1,2,figsize=(12,4.2),sharey=False)
        for ax,level in zip(axes,(.9,.95)):
            for method in METHODS:
                f=seed_summary[(seed_summary.level==level)&(seed_summary.method==method)].sort_values('horizon')
                y=f[f'{metric}_mean'];lo=y-f[f'{metric}_min'];hi=f[f'{metric}_max']-y
                ax.errorbar(f.horizon,y,yerr=np.vstack([lo,hi]),marker='o',capsize=3,label=LABELS[method],color=colors[method])
            if metric=='coverage':ax.axhline(level,color='black',ls='--',lw=1,label='Nominal' if level==.9 else None)
            ax.set(title=f'{int(level*100)}% intervals',xlabel='Forecast horizon (hours)',ylabel=ylabel);ax.grid(alpha=.25);ax.set_xticks([1,3,6])
        handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,frameon=False);fig.tight_layout(rect=(0,.13,1,1))
        for ext in ('png','pdf'):fig.savefig(figdir/f'five_seed_{metric}.{ext}',dpi=180,bbox_inches='tight')
        atomic(figdir/f'five_seed_{metric}.sources.json',dict(figure=f'five_seed_{metric}',generator='review/matched_intervals005_bdg2_multiseed_20260914/report.py',generator_sha256=sha(Path(__file__)),inputs={'common_support_metrics.csv':sha(out/'common_support_metrics.csv'),'five_seed_summary.csv':sha(out/'five_seed_summary.csv')},interpretation='Points are five-seed means; whiskers span the observed minimum and maximum across the same buildings and test periods.'))
        plt.close(fig)
    report=['# BDG2 fold-2 interval methods across five training seeds','',f'All **150/150** authorized cells are complete: 30 per seed for seeds 42–46. The four new seeds contributed **120** cells, **204** learned-estimator fits, four DSCP calibrators, 20 KMeans candidate fits, 120 alert streams, and zero matched-forecasting or seasonal-baseline refits. Independent validation and forbidden-fit resume passed for every seed.','','The same ten buildings and test periods are reused across seeds. Standard deviations and ranges below describe training-seed variability; they are not population uncertainty, confidence intervals or significance tests.','', '| horizon | level | method | coverage mean [range] | MPIW mean [range] | Winkler mean [range] |','|---:|---:|---|---:|---:|---:|']
    for _,r in seed_summary.iterrows():report.append(f'| {int(r.horizon)} | {r.level:.2f} | {LABELS[r.method]} | {r.coverage_mean:.4f} [{r.coverage_min:.4f}, {r.coverage_max:.4f}] | {r.mpiw_mean:.2f} [{r.mpiw_min:.2f}, {r.mpiw_max:.2f}] | {r.winkler_mean:.2f} [{r.winkler_min:.2f}, {r.winkler_max:.2f}] |')
    cqr=contrast_summary[contrast_summary.left_method=='cqr'];upd=contrast_summary[contrast_summary.left_method=='recentred_enbpi_updated']
    report += ['', 'Across the six horizon/level settings, the five-seed mean CQR coverage gain over its shared raw-quantile owner ranged from %.2f to %.2f percentage points. CQR reduced absolute nominal-coverage error in %d/6 settings on average and its mean Winkler difference ranged from %.2f to %.2f kWh.'%(100*cqr.coverage_difference_mean.min(),100*cqr.coverage_difference_mean.max(),int((cqr.absolute_gap_difference_mean<0).sum()),cqr.winkler_difference_mean.min(),cqr.winkler_difference_mean.max()),'', 'Updated EnbPI changed mean coverage by %.2f to %.2f percentage points versus its shared static owner. Its mean interval width difference ranged from %.2f to %.2f kWh and mean Winkler difference from %.2f to %.2f kWh.'%(100*upd.coverage_difference_mean.min(),100*upd.coverage_difference_mean.max(),upd.mpiw_difference_mean.min(),upd.mpiw_difference_mean.max(),upd.winkler_difference_mean.min(),upd.winkler_difference_mean.max()),'', '![Five-seed coverage](smart_building_conformal/outputs/matched_intervals005/bdg2_fold2_multiseed_v2_coordinator/analysis_v1/figures/five_seed_coverage.png)','', 'Across the 150 pooled combined-channel cells, clean-stream background episodes ranged from %d to %d per cell (%.4f to %.4f episodes per asset-day), and time in alert ranged from %.4f to %.4f. All rows were available and availability-only alerts were zero. The event catalogue was empty, so these results cannot estimate recall, F1, detection delay, confirmed false-alarm rates or operational feasibility. Native and common-support views describe the same 150 cells and are not double-counted.'%(pooled_background.episodes.min(),pooled_background.episodes.max(),pooled_background.background_episodes_per_asset_day.min(),pooled_background.background_episodes_per_asset_day.max(),pooled_background.time_in_alert_fraction.min(),pooled_background.time_in_alert_fraction.max()),'', 'The four new runs used %.2f worker-seconds, independent validation %.2f, and completed resumes %.2f; all twelve exits were 0. Total measured worker time was %.2f seconds (%.2f CPU seconds), and peak lifetime RSS was %.3f GiB.'%(new_cost[new_cost.action=='run'].seconds.sum(),new_cost[new_cost.action=='validate'].seconds.sum(),new_cost[new_cost.action=='completed_resume'].seconds.sum(),new_cost.seconds.sum(),new_cost.process_cpu_seconds.sum(),new_cost.lifetime_peak_rss_bytes.max()/2**30),'','## Evidence and remaining work','', '[Five-seed metrics](smart_building_conformal/outputs/matched_intervals005/bdg2_fold2_multiseed_v2_coordinator/analysis_v1/five_seed_summary.csv), [per-seed common metrics](smart_building_conformal/outputs/matched_intervals005/bdg2_fold2_multiseed_v2_coordinator/analysis_v1/common_support_metrics.csv), [background workload](smart_building_conformal/outputs/matched_intervals005/bdg2_fold2_multiseed_v2_coordinator/analysis_v1/background_workload.csv), [worker costs](smart_building_conformal/outputs/matched_intervals005/bdg2_fold2_multiseed_v2_coordinator/analysis_v1/worker_costs.csv), and the [evidence index](review/matched_intervals005_bdg2_multiseed_20260914/EVIDENCE_INDEX.md) are recomputable.','','Matched forecasting remains **70/195**. Interval methods are **150/1950**, leaving **1,800** cells. The three deterministic seasonal computations remain three; the four new seeds add twelve point and 24 interval aliases, not computations. Full-study readiness remains false.','', 'The next bounded execution proposal is PLEIA-energy outer fold 1, seed 42, horizons 1/3/6: three matched-forecasting units, 30 learned-fit invocations, nine point cells and eighteen own-model split-conformal interval cells. The corresponding completed fold-2 workers are the direct measured cost basis; fitting-row-scaled run time totals approximately %.1f seconds. This is a scheduling estimate rather than an authorization or runtime guarantee. The exact commands and costs are saved in `next_proposed_forecasting_units.csv` and `next_proposed_measured_costs.csv`; none were launched.'%measured.scaled_run_seconds.sum()]
    atomic(ROOT/'BDG2_MATCHED_INTERVAL_METHODS_MULTISEED_REPORT.md','\n'.join(report)+'\n')
    prefix='# BDG2 five-seed interval extension completed\n\nThe bounded fold-2 comparison now contains 150/1950 interval-method cells across model seeds 42–46. All four new seeds passed independent validation and zero-fit resume. Matched forecasting remains 70/195; full-study readiness remains false.\n\n[Report](../BDG2_MATCHED_INTERVAL_METHODS_MULTISEED_REPORT.md) and [evidence index](matched_intervals005_bdg2_multiseed_20260914/EVIDENCE_INDEX.md).\n\n<!-- bdg2-interval-multiseed-20260914: historical content follows -->\n\n'
    current=(ROOT/'review/CURRENT_EVIDENCE.md').read_text(encoding='utf-8');atomic(ROOT/'review/CURRENT_EVIDENCE.md',prefix+current)
    recovery=(ROOT/'PROJECT_RECOVERY_STATUS.md').read_text(encoding='utf-8');atomic(ROOT/'PROJECT_RECOVERY_STATUS.md',prefix.replace('[Report](../','[Report](').replace('[evidence index](','[evidence index](review/')+recovery)
    readiness=(ROOT/'MATCHED_METHOD_READINESS_MAP.md').read_text(encoding='utf-8');atomic(ROOT/'MATCHED_METHOD_READINESS_MAP.md',prefix.replace('[Report](../','[Report](').replace('[evidence index](','[evidence index](review/')+readiness)
    panel='# Numerical panel response: five-seed BDG2 interval methods\n\nThe response now reports all five prespecified fold-2 training seeds without choosing a favorable seed. Exact coverage, MPIW, Winkler, background workload, fitted-operation counts and costs are linked from the evidence index. Seed dispersion is labelled descriptive because all seeds share buildings and test periods. Empty-event streams are limited to background workload.\n'
    atomic(REVIEW/'PANEL_RESPONSE.md',panel)
    validation=dict(passed=True,method_cells=150,new_method_cells=120,unique_keys=len(expected),validations_passed=5,zero_fit_resumes=5,new_learned_estimator_fits=204,new_dscp_calibrators=4,new_kmeans_candidates=20,new_alert_streams=120,new_seasonal_computations=0,seasonal_point_aliases=12,seasonal_interval_aliases=24,matched_forecasting_complete=70,interval_methods_complete=150,interval_methods_remaining=1800,models_fitted=0,calibrators_fitted=0,source_artifacts_unchanged=True)
    atomic(out/'analysis_validation.json',validation);atomic(out/'COMPLETE.json',dict(files=tree(out),models_fitted=0));print(json.dumps(validation,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();main(args.out)
