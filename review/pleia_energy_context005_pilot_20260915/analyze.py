"""Recompute the real PLEIA-energy C pilot report from completed, validated files."""
from __future__ import annotations
import itertools,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'smart_building_conformal'))
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='1'
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.intervals005_common import ROOT,REPO,Operations,atomic,csv,read,tree,digest,source_digest
from src.unit_checkpoint import signature

REVIEW=REPO/'review/pleia_energy_context005_pilot_20260915'
RUN=ROOT/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1'
BATCH=ROOT/'outputs/conditional_context005/first_real_C_v1_coordinator'
DESIGN=ROOT/'protocols/conditional_context005/pleia_energy_f2_s42_C_v1'
OUT=ROOT/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1_analysis'
CONTROLS=['quantile_static','cqr_static','cqr_rolling','persistence_static']
RULES=['single_sample','30min_3of3','60min_4of6','180min_3of18','360min_4of36']
CHANNELS=['numerical_only','availability_only','combined']

def frame(path):
    try:return pd.read_csv(path,float_precision='round_trip',dtype={'row_id':str,'context_id':str,'group_id':str,'original_segment_id':str,'segment_id':str})
    except pd.errors.EmptyDataError:return pd.DataFrame()

def weighted(part):
    n=part.n.sum()
    return pd.Series(dict(n=int(n),unavailable_n=int(part.unavailable_n.sum()),coverage=float((part.coverage*part.n).sum()/n),
        mpiw=float((part.mpiw*part.n).sum()/n),winkler=float((part.winkler*part.n).sum()/n)))

def md(f):
    def value(v):
        if pd.isna(v):return 'unavailable'
        if isinstance(v,(float,np.floating)):return f'{v:.5g}'
        return str(v).replace('|','\\|').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+
        ['| '+' | '.join(value(v) for v in row)+' |' for row in f.itertuples(index=False,name=None)])

def main():
    if OUT.exists():raise ValueError('preserve completed analysis; use a new version')
    OUT.mkdir(parents=True)
    with Operations(forbid=True):
        progress=read(BATCH/'progress.json');assert progress['status']=='completed' and progress['active'] is None
        validation=read(BATCH/'validation/validation.json');resume=read(BATCH/'resume.json')
        assert validation['passed'] and validation['actual_exit_status']==0
        assert resume==dict(passed=True,completed=True,models_fitted=0,calibrators_fitted=0,replay_updates=0,scientific_artifacts_unchanged=True,protocol_sha256=resume['protocol_sha256'])
        protocol=read(DESIGN/'frozen_protocol.json');readiness=read(DESIGN/'readiness.json')
        assert protocol['source_hash']==source_digest()==readiness['source_hash']=='a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f'
        assert protocol['manifest']['execution_authorized'] and protocol['manifest']['authorization_kind']=='explicit_real_C_run'
        assert protocol['rows']=={'final_fit':14855,'final_calibration':4954,'outer_test':9907}
        assert protocol['manifest']['expected_contexts']==68 and protocol['manifest']['expected_schedules']==2856
        assert [x['control_id'] for x in protocol['manifest']['controls']]==CONTROLS
        assert [x['rule_id'] for x in protocol['manifest']['rules']]==RULES

        variants=frame(RUN/'stages/tables/variants.csv');events=frame(RUN/'stages/tables/events.csv.gz')
        strata=frame(RUN/'stages/tables/strata.csv');macros=frame(RUN/'stages/tables/conditional_macro.csv')
        contributions=frame(RUN/'stages/tables/original_context_contributions.csv.gz')
        workload=frame(RUN/'stages/tables/fullstream_workload.csv')
        assert len(variants)==68*43 and variants.context_id.nunique()==68
        assert (variants.ordinal==0).sum()==68 and (variants.ordinal>0).sum()==2856
        assert len(events)==171360 and len(strata)==4*5*3*21 and len(macros)==4*5*3
        assert set(events.control_id)==set(CONTROLS) and set(events.rule_id)==set(RULES) and set(events.channel)==set(CHANNELS)
        assert set(events.restriction_minutes)=={110.0}
        assert len(frame(DESIGN/'contexts.csv'))==68 and len(frame(DESIGN/'schedules.csv.gz'))==2856
        inference=read(RUN/'stages/tables/inference.json')
        assert inference['status']=='unavailable_incomplete_model_seeds' and inference['required_seeds']==[42,43,44,45,46]
        assert frame(RUN/'stages/tables/inference.csv').empty

        # Every one of the 60 channel-specific control/rule cells, with fixed
        # equal-stratum detection and original clean exposure.
        workagg=workload.groupby(['control_id','rule_id','channel'],as_index=False).agg(
            eligible_rows=('eligible_rows','sum'),asset_days=('asset_days','sum'),background_episodes=('episodes','sum'),
            alert_rows=('alert_rows','sum'),time_in_alert_days=('time_in_alert_days','sum'))
        workagg['background_episodes_per_asset_day']=workagg.background_episodes/workagg.asset_days
        workagg['fraction_time_in_alert']=workagg.time_in_alert_days/workagg.asset_days
        assert workagg.eligible_rows.eq(9907).all()
        np.testing.assert_allclose(workagg.asset_days,9907/144,atol=1e-12,rtol=1e-12)
        summary=[]
        for macro in macros.itertuples():
            ss=strata[(strata.control_id==macro.control_id)&(strata.rule_id==macro.rule_id)&(strata.channel==macro.channel)]
            ev=events[(events.control_id==macro.control_id)&(events.rule_id==macro.rule_id)&(events.channel==macro.channel)]
            pos=ev[ev.effective&ev.eligible];found=pos[pos.detected]
            w=workagg[(workagg.control_id==macro.control_id)&(workagg.rule_id==macro.rule_id)&(workagg.channel==macro.channel)].iloc[0]
            supported=ss.supported.all() and len(ss)==21
            expected=float(ss.recall.mean()) if supported else np.nan
            np.testing.assert_allclose(macro.conditional_context_macro,expected,atol=1e-12,rtol=1e-12,equal_nan=True)
            summary.append(dict(control_id=macro.control_id,rule_id=macro.rule_id,channel=macro.channel,
                conditional_context_detection=macro.conditional_context_macro,macro_status=macro.status,supported_strata=int(macro.supported_strata),
                min_effective_contexts=int(ss.effective_contexts.min()),max_effective_contexts=int(ss.effective_contexts.max()),
                scheduled=int(len(ev)),effective=int(ev.effective.sum()),null=int(ev['null'].sum()),aliases=int(ev.alias.sum()),
                detected=int(pos.detected.sum()),misses=int((~pos.detected).sum()),
                detected_delay_median_minutes=float(found.delay_minutes.median()) if len(found) else np.nan,
                detected_delay_q90_minutes=float(found.delay_minutes.quantile(.9)) if len(found) else np.nan,
                restricted_ttd_equal_stratum_minutes=float(ss.restricted_mean_detection_minutes.mean()) if supported else np.nan,
                original_eligible_rows=int(w.eligible_rows),original_asset_days=float(w.asset_days),background_episodes=int(w.background_episodes),
                background_episodes_per_asset_day=float(w.background_episodes_per_asset_day),alert_rows=int(w.alert_rows),
                time_in_alert_days=float(w.time_in_alert_days),fraction_time_in_alert=float(w.fraction_time_in_alert)))
        summary=pd.DataFrame(summary).sort_values(['channel','rule_id','control_id'])
        assert len(summary)==60
        csv(OUT/'control_rule_channel_summary.csv',summary)
        csv(OUT/'stratum_metrics.csv',strata)
        csv(OUT/'event_records.csv.gz',events)
        csv(OUT/'original_context_contributions.csv.gz',contributions)
        csv(OUT/'background_workload.csv',workload)
        csv(OUT/'background_workload_summary.csv',workagg)

        schedule_support=events.drop_duplicates(['context_id','family','severity','replicate']).groupby(['family','severity'],as_index=False).agg(
            scheduled=('context_id','size'),effective=('effective','sum'),null=('null','sum'),aliases=('alias','sum'),distinct_contexts=('context_id','nunique'),effective_contexts=('context_id',lambda s:s[events.loc[s.index,'effective']].nunique()))
        assert schedule_support.scheduled.eq(136).all() and schedule_support.distinct_contexts.eq(68).all()
        csv(OUT/'fault_schedule_support.csv',schedule_support)

        identity=[];realizations=[];diagnostic_cache={}
        for vr in variants.itertuples():
            stage=RUN/'stages'/vr.stage;canonical=RUN/'stages'/vr.canonical_stage
            if vr.ordinal==0:
                assert not vr.alias
                ident=read(canonical/'identity.json')
                identity.append(dict(context_id=vr.context_id,stage=vr.stage,feature_hash=ident['feature_hash'],row_hash=ident['row_hash'],
                    observation_hash=ident['observation_hash'],availability_hash=ident['availability_hash'],shared_predictor=ident['shared_predictor'],source_hash=ident['source_hash']))
            if vr.alias:
                alias=read(stage/'alias.json');assert alias['canonical_stage']==vr.canonical_stage and alias['realization_hash']==vr.realization_hash
            key=vr.canonical_stage
            if key not in diagnostic_cache:diagnostic_cache[key]=frame(canonical/'interval_diagnostics.csv')
            for row in diagnostic_cache[key].to_dict('records'):
                realizations.append(dict(context_id=vr.context_id,ordinal=vr.ordinal,family=vr.family,severity=vr.severity,replicate=vr.replicate,
                    effective=vr.effective,null=vr.null,alias=vr.alias,canonical_stage=key,**row))
        identity=pd.DataFrame(identity);diag=pd.DataFrame(realizations)
        assert len(identity)==68 and len(diag)==len(variants)*4*2
        assert identity.source_hash.eq(source_digest()).all() and identity.shared_predictor.nunique()==1
        csv(OUT/'zero_control_identities.csv',identity)
        csv(OUT/'context_interval_diagnostics.csv.gz',diag)

        interval=[]
        selections=[('identity',diag.ordinal==0),('all_scheduled_fault_slots',diag.ordinal>0),('effective_fault_slots',(diag.ordinal>0)&diag.effective)]
        for label,mask in selections:
            part=diag[mask]
            for key,g in part.groupby(['control_id','target']):interval.append(dict(scope=label,control_id=key[0],target=key[1],streams=g[['context_id','ordinal']].drop_duplicates().shape[0],**weighted(g)))
        interval=pd.DataFrame(interval);csv(OUT/'interval_summary.csv',interval)
        interval_strata=diag[(diag.ordinal>0)].groupby(['family','severity','control_id','target'],as_index=False).apply(weighted,include_groups=False).reset_index(drop=True)
        csv(OUT/'interval_by_fault_stratum.csv',interval_strata)

        full=[]
        for stage in sorted((RUN/'stages').glob('fullstream_*')):
            d=frame(stage/'interval_diagnostics.csv');d['segment_stage']=stage.name;full.append(d)
        full=pd.concat(full,ignore_index=True)
        fullsummary=full.groupby(['control_id','target'],as_index=False).apply(weighted,include_groups=False).reset_index(drop=True)
        csv(OUT/'fullstream_clean_interval_diagnostics.csv',fullsummary)

        # Descriptive paired contrasts retain context and stratum pairing. A
        # positive detection contrast favors A; a negative restricted-TTD
        # contrast favors A. There is no significance or selection claim.
        pairs=[]
        keys=['context_id','family','severity','rule_id','channel']
        for a,b in itertools.combinations(CONTROLS,2):
            for metric in ['recall','restricted_delay']:
                p=contributions[contributions.control_id.isin([a,b])].pivot(index=keys,columns='control_id',values=metric).dropna(subset=[a,b]).reset_index()
                p['difference']=p[a]-p[b]
                for (rule,channel),g in p.groupby(['rule_id','channel']):
                    strata_diff=g.groupby(['family','severity']).agg(mean_difference=('difference','mean'),paired_contexts=('context_id','nunique')).reset_index()
                    supported=len(strata_diff)==21 and strata_diff.paired_contexts.min()>=5
                    pairs.append(dict(control_a=a,control_b=b,metric=metric,definition='A minus B',rule_id=rule,channel=channel,
                        paired_strata=len(strata_diff),min_paired_contexts=int(strata_diff.paired_contexts.min()),status='descriptive_complete_pairing' if supported else 'unavailable_pairing_support',
                        equal_stratum_mean_difference=float(strata_diff.mean_difference.mean()) if supported else np.nan))
        paired=pd.DataFrame(pairs);assert len(paired)==6*2*5*3
        csv(OUT/'paired_control_differences.csv',paired)

        # Every rule receives exactly the saved issued row identities. File
        # hashes make the lossless publication independently checkable.
        hashrows=[];integrity=[]
        canonical_stages=sorted(set(variants.canonical_stage))
        canonical_stages+=sorted(p.name for p in (RUN/'stages').glob('fullstream_*'))
        for name in canonical_stages:
            stage=RUN/'stages'/name
            for control in CONTROLS:
                issued=frame(stage/(control+'_issued.csv.gz'));issued_hash=signature(issued.row_id.tolist())
                ordered=(issued.lower<=issued.upper)|issued.lower.isna()|issued.upper.isna()
                assert ordered.all()
                integrity.append(dict(stage=name,control_id=control,rows=len(issued),ordered_issued_bounds=int(ordered.sum()),
                    raw_crossing_rows=int((issued.raw_lower>issued.raw_upper).sum()),finite_issued_bounds=int((issued.lower.notna()&issued.upper.notna()).sum())))
                for rule in RULES:
                    alerts=frame(stage/(control+'_'+rule+'_alerts.csv.gz'));consumed_hash=signature(alerts.row_id.tolist())
                    assert issued_hash==consumed_hash
                    hashrows.append(dict(stage=name,control_id=control,rule_id=rule,rows=len(issued),issued_row_hash=issued_hash,consumed_row_hash=consumed_hash,
                        issued_file_sha256=digest(stage/(control+'_issued.csv.gz')),consumed_alert_file_sha256=digest(stage/(control+'_'+rule+'_alerts.csv.gz'))))
        hashes=pd.DataFrame(hashrows);csv(OUT/'issued_consumed_hashes.csv.gz',hashes)
        integrity=pd.DataFrame(integrity)
        csv(OUT/'stream_bound_integrity.csv',integrity)
        csv(OUT/'stream_bound_integrity_summary.csv',integrity.groupby('control_id',as_index=False).agg(
            unique_streams=('stage','size'),rows=('rows','sum'),ordered_issued_bounds=('ordered_issued_bounds','sum'),raw_crossing_rows=('raw_crossing_rows','sum'),finite_issued_bounds=('finite_issued_bounds','sum')))

        # Exact operation calls. Nested wrapper/conformalize timings are not
        # additive; worker and stage elapsed costs remain separate tables.
        operations=[]
        for line in (RUN/'operations.jsonl').read_text(encoding='utf-8').splitlines():
            row=json.loads(line)
            if row.get('event')=='returned':operations.append(row)
        operations=pd.DataFrame(operations);csv(OUT/'operations.csv',operations)
        opcounts=operations.groupby('kind').size().rename('returned_calls').reset_index();csv(OUT/'operation_counts.csv',opcounts)
        observed=dict(zip(opcounts.kind,opcounts.returned_calls))
        assert observed=={'calibrator_conformalize':2,'cqr_wrapper_fit':1,'quantile_estimator_fit':3}
        assert (~operations.synthetic).all() and set(operations.n_rows)=={14855,4954}
        owner_identity=read(RUN/'stages/controls/identity.json')
        assert owner_identity['quantile_shared'] and owner_identity['new_learned_fits']==0 and owner_identity['persistence_calibrations']==1
        atomic(OUT/'owner_operation_reconciliation.json',dict(passed=True,operation_counts=observed,logical_conformalizations=1,
            nested_instrumented_conformalize_calls=2,persistence_radius_computations=1,persistence_learned_fits=0,
            persistence_radius=owner_identity['persistence_radius'],quantile_shared=True,owner_sha256=owner_identity['owner_sha256'],
            unexpected_fit_calls=0,note='The wrapper contains the three quantile-estimator fits. Nested conformalize instrumentation is one public logical conformalization. Persistence radius construction is recorded in owner identity and has no fit call.'))

        workers=[]
        for task,row in progress['tasks'].items():
            workers.append(dict(task=task,status=row['status'],actual_exit_status=row['exit_code'],wall_seconds=row['seconds'],
                started_utc=row['started_utc'],ended_utc=row['ended_utc'],logger_receipt=row['logger_receipt']))
        workers=pd.DataFrame(workers);assert len(workers)==5 and workers.actual_exit_status.eq(0).all()
        csv(OUT/'worker_costs_and_exits.csv',workers)
        stages=[]
        for path in sorted((RUN/'stages').glob('*/stage.json')):
            row=read(path);r=row['resources'];name=path.parent.name
            category='context_replay' if name.startswith('context_') else 'fullstream_clean' if name.startswith('fullstream_') else 'owner_fit' if name=='owner_fit_cqr' else 'owner_calibration' if name=='owner_cal_cqr' else 'control_serialization' if name=='controls' else 'aggregate_tables'
            stages.append(dict(stage=name,category=category,**r))
        stages=pd.DataFrame(stages);csv(OUT/'stage_costs.csv',stages)
        stage_summary=stages.groupby('category',as_index=False).agg(stages=('stage','size'),summed_wall_seconds=('seconds','sum'),summed_process_cpu_seconds=('process_cpu_seconds','sum'),
            max_peak_rss_bytes=('peak_rss_bytes','max'),max_peak_private_bytes=('peak_private_bytes','max'),min_available_ram_bytes=('min_available_ram_bytes','min'))
        csv(OUT/'stage_cost_summary.csv',stage_summary)

        # Compact descriptive view; no model/rule is selected from it.
        fig,axes=plt.subplots(1,4,figsize=(16,4.8))
        labels=['Immediate','30m 3/3','60m 4/6','180m 3/18','360m 4/36']
        display=['Raw quantile','CQR static','CQR rolling','Persistence']
        for ax,channel in zip(axes[:3],CHANNELS):
            part=summary[summary.channel==channel].pivot(index='control_id',columns='rule_id',values='conditional_context_detection').reindex(index=CONTROLS,columns=RULES)
            im=ax.imshow(part.to_numpy(float),vmin=0,vmax=1,cmap='viridis',aspect='auto')
            for i in range(4):
                for j in range(5):
                    value=part.iloc[i,j];ax.text(j,i,'NA' if pd.isna(value) else f'{value:.2f}',ha='center',va='center',color='white' if pd.notna(value) and value<.65 else 'black',fontsize=8)
            ax.set_title(channel.replace('_',' '));ax.set_xticks(range(5),labels,rotation=40,ha='right');ax.set_yticks(range(4),display)
        part=summary[summary.channel=='combined'].pivot(index='control_id',columns='rule_id',values='background_episodes_per_asset_day').reindex(index=CONTROLS,columns=RULES)
        im2=axes[3].imshow(part.to_numpy(float),cmap='magma',aspect='auto')
        for i in range(4):
            for j in range(5):axes[3].text(j,i,f'{part.iloc[i,j]:.2f}',ha='center',va='center',color='white' if part.iloc[i,j]>.5*part.to_numpy().max() else 'black',fontsize=8)
        axes[3].set_title('clean background episodes/day\ncombined channel');axes[3].set_xticks(range(5),labels,rotation=40,ha='right');axes[3].set_yticks(range(4),display)
        fig.colorbar(im,ax=axes[:3].tolist(),shrink=.75,label='conditional-context detection');fig.colorbar(im2,ax=axes[3],shrink=.75,label='episodes / asset-day')
        fig.suptitle('PLEIA energy C pilot — fold 2, model seed 42, h1 (descriptive)')
        fig.subplots_adjust(left=.08,right=.97,bottom=.25,top=.82,wspace=.38)
        fig.savefig(OUT/'control_rule_comparison.png',dpi=180);fig.savefig(OUT/'control_rule_comparison.pdf');plt.close(fig)
        atomic(OUT/'control_rule_comparison.sources.json',dict(source_csv='control_rule_channel_summary.csv',source_sha256=digest(OUT/'control_rule_channel_summary.csv'),
            panels='three conditional-context detection channels plus combined-channel original clean background episodes per asset-day',nominal_selection=False))

        # Headline tables and evidence-led prose.
        combined=summary[summary.channel=='combined'][['control_id','rule_id','conditional_context_detection','detected','misses','detected_delay_median_minutes','restricted_ttd_equal_stratum_minutes','background_episodes_per_asset_day','fraction_time_in_alert']].sort_values(['rule_id','control_id'])
        numerical=summary[summary.channel=='numerical_only'].conditional_context_detection
        availability=summary[summary.channel=='availability_only'].conditional_context_detection
        macro_supported=int((macros.status=='supported_point_estimate').sum())
        report='# PLEIA-energy conditional-context005 pilot report\n\n'
        report+='The exact outer-fold-2/model-seed-42/h1 pilot completed all 68 published contexts, 2,856 scheduled fault slots, 68 clean context identities, four fixed 95% controls and five rules. The final coordinator, all five CLI actions, independent validation and completed resume exited successfully. No setting was selected or changed using these outcomes.\n\n'
        report+='## Every fixed control/rule comparison\n\nThe table below shows the combined channel. The machine table `control_rule_channel_summary.csv` contains the same fields for numerical-only, availability-only and combined channels: all 60 comparisons. Detection is the predeclared equal-context/equal-stratum macro; delay is minutes, with misses censored at 110 elapsed minutes for restricted TTD. Background comes from the original held-out clean stream.\n\n'+md(combined)+'\n\n'
        report+=f'{macro_supported}/60 channel-specific macros met the frozen 21-stratum support rule. Numerical-only conditional detection ranged from {numerical.min():.3f} to {numerical.max():.3f}; availability-only ranged from {availability.min():.3f} to {availability.max():.3f}. These ranges are descriptive and include controls/rules with different clean alert workloads.\n\n'
        report+='The PLEIA event envelope contains six observations (60 physical minutes from first through the boundary after the last sample). Episode matching retains the established last-envelope-observation plus six-sample tolerance convention: `(6-1+6) × 10 = 110` elapsed minutes. Misses receive 110 minutes in restricted TTD; detected-only delay excludes misses.\n\n'
        report+='## Interval and workload definitions\n\n`clean_counterfactual` scores the original meter truth against intervals issued after the variant’s causal observed history; `corrupted_observation` scores available corrupted readings against those intervals and excludes unavailable readings. `fullstream_clean_interval_diagnostics.csv` separately scores the untouched original held-out stream. Aliases retain scheduled incidence but do not add unique realizations or inferential units. Original exposure is 9,907 rows / 68.798611 asset-days for every control/rule/channel, including 115 rows outside challenge tiles.\n\n'
        report+='## Computation and validation\n\n'+md(workers[['task','actual_exit_status','wall_seconds']])+'\n\n'
        report+='The operation ledger contains one real CQR wrapper fit, exactly three HistGradientBoosting quantile-estimator fits on 14,855 rows, and two nested profiler records for one logical conformalization on 4,954 rows. Persistence performs one recorded absolute-error radius construction and zero learned fits. Raw quantile, static CQR and rolling CQR share the fitted quantile owner. No XGBoost, Attention-LSTM, EnbPI, DSCP, tuning or matched-forecast fit occurred.\n\n'
        report+='MAPIE logged raw quantile-order warnings during replay. The frozen implementation retains the learned raw tails and orders emitted lower/upper bounds; `stream_bound_integrity.csv` records raw crossings and verifies every emitted interval is ordered. The warnings did not trigger fitting, clipping, retuning or discarded outcomes.\n\n'
        report+=f'The independent validator completed {validation["checks"]:,} numerical/identity checks, reconstructed {validation["independently_reconstructed_event_rows"]:,} event/control/rule/channel records, checked {validation["fullstream_workload_checks"]} clean workload paths and found maximum absolute numerical difference {validation["maximum_absolute_difference"]:.3g}. Completed resume recorded zero model fits, calibrator fits and replay updates and preserved all scientific files.\n\n'
        report+='## Interpretation limits\n\nThis is one model seed on one historically inspected evaluation period. Paired differences are descriptive; five-seed population intervals are unavailable and are stored as unavailable rather than fabricated. C measures detection conditional on declared synthetic faults in fixed contexts. It does not estimate real fault prevalence, deployment precision/F1, or amendment-004 natural-frequency feasibility. It does not add a matched forecasting or interval-quality cell. The energy sensitivity proposal was not adopted or applied; primary meter values and workload denominators remain intact.\n'
        atomic(REVIEW/'PLEIA_ENERGY_CONTEXT005_PILOT_REPORT.md',report)
        atomic(OUT/'validation.json',dict(passed=True,source_hash=source_digest(),contexts=68,scheduled_fault_slots=2856,zero_controls=68,event_records=171360,
            control_rule_channel_cells=60,control_rule_pairs=20,independent_checks=validation['checks'],maximum_absolute_difference=validation['maximum_absolute_difference'],
            all_five_cli_actions_exit_zero=True,zero_fit_resume=True,real_learned_estimator_fits=3,cqr_wrapper_fits=1,logical_conformalizations=1,
            persistence_radius_computations=1,persistence_learned_fits=0,energy_sensitivity_applied=False,population_inference_available=False,
            matched_forecasting_complete=70,interval_quality_complete=250,seasonal_unique_complete=9,full_study_ready=False,scientific_run_tree_sha256=signature(tree(RUN))))
    print('REAL C PILOT ANALYSIS RECOMPUTED WITHOUT FITTING',flush=True)

if __name__=='__main__':main()
