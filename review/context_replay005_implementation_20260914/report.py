"""Recompute the implementation package's reports from sealed evidence."""
import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[name]='1'
from common import *
import json,numpy as np,pandas as pd
from src.intervals005_common import Operations,csv
from src.context005_spec import table,BASE,PLAN,FINAL

def md(f):
    def value(v):
        if isinstance(v,(float,np.floating)):return f'{v:.6g}' if np.isfinite(v) else 'unavailable'
        return str(v).replace('|','\\|').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(map(str,f.columns))+' |','| '+' | '.join(['---']*len(f.columns))+' |']+['| '+' | '.join(value(v) for v in row)+' |' for row in f.itertuples(index=False,name=None)])

def main(version):
    batch=SMART/f'outputs/conditional_context005/synthetic_{version}_coordinator';out=SMART/f'outputs/conditional_context005/implementation_analysis_{version}'
    out.mkdir(parents=True,exist_ok=False)
    state=read(batch/'progress.json')
    if state['status']!='completed':raise ValueError('synthetic batch incomplete')
    gate=read(REVIEW/'REGRESSION_RECEIPT_repository_v4.json')
    if not gate['passed']:raise ValueError('repository gate failed')
    with Operations(forbid=True):
        validations=[];ops=[];cost=[];zero=[]
        for ds in ['pleia_energy','rico']:
            run=SMART/f'outputs/conditional_context005/synthetic_{ds}_{version}'
            v=read(batch/(ds+'_validation_numeric_columns' if ds=='pleia_energy' and version=='v1' else ds+'_validation')/'validation.json');r=read(batch/(ds+'_resume.json'))
            if not v['passed'] or not r['passed']:raise ValueError('failed CLI acceptance')
            validations.append(dict(dataset=ds,**v));zero.append(dict(dataset=ds,**r))
            for line in (run/'operations.jsonl').read_text().splitlines():
                row=json.loads(line)
                if row.get('event')=='returned':ops.append(dict(dataset=ds,**row))
            for path in (run/'stages').glob('*/stage.json'):
                stage=read(path);cost.append(dict(dataset=ds,stage=path.parent.name,**stage['resources']))
        csv(out/'synthetic_validation_summary.csv',pd.DataFrame(validations));csv(out/'zero_fit_resume_summary.csv',pd.DataFrame(zero))
        csv(out/'synthetic_operations.csv',pd.DataFrame(ops));csv(out/'synthetic_stage_costs.csv',pd.DataFrame(cost))
        counts=pd.DataFrame(ops).groupby(['dataset','kind']).size().rename('executed_calls').reset_index();csv(out/'synthetic_operation_counts.csv',counts)
        attempts=pd.DataFrame([dict(task=k,actual_exit=r['exit_code'],seconds=r['seconds'],receipt=r['logger_receipt']) for k,r in state['tasks'].items()]);csv(out/'cli_all_attempt_costs_and_exits.csv',attempts)
        worker=attempts[~attempts.task.str.contains('failed_original')];csv(out/'cli_costs_and_exits.csv',worker)
        support=SMART/'outputs/conditional_context005/implementation_support_v1';diagnosis=SMART/'outputs/conditional_context005/interval_diagnostic_extension_v1'
        owners=table(support/'interval_owner_diagnostic.csv');allmethods=table(diagnosis/'all_method_diagnostic.csv');roles=table(support/'context_role_support.csv');cross=table(support/'scope_crosswalk.csv')
        if len(cross)!=1950 or sum(cross.completion_status=='complete')!=250:raise ValueError('real completion crosswalk')
        seasonal=[]
        runs={'bdg2':'bdg2_f2_s42_v1','pleia':'pleia_f2_s42_v1','pleia_energy':'pleia_energy_f2_s42_v2'}
        for row in table(PLAN/'seasonal_execution_queue.csv').to_dict('records'):
            root=SMART/'outputs/matched_intervals005'/runs[row['dataset']]/'stages'/f'seasonal_h{row["horizon"]}'
            done=row['outer_fold']==2 and (root/'COMPLETE.json').exists()
            seasonal.append(dict(row,unique_computation_complete=done,evidence_path=str(root.relative_to(ROOT)) if done else '',counts_as_original_training_seed=False))
        csv(out/'seasonal_completion_crosswalk.csv',pd.DataFrame(seasonal))
        if sum(x['unique_computation_complete'] for x in seasonal)!=9:raise ValueError('seasonal count')
        # Exact proposal retains the published schedules and roles. Counts below
        # are deterministic schedules, not model fits or independent cases.
        proposal=read(REVIEW/'FIRST_RUN_NO_FIT_READINESS.json');scheduled=table(REVIEW/'first_run_published_schedules.csv.gz')
        counts_proposal=scheduled.groupby(['family','severity'],as_index=False).agg(scheduled=('context_id','size'),effective=('effective','sum'),null=('null','sum'),original_contexts=('context_id','nunique'))
        csv(out/'first_run_stratum_support.csv',counts_proposal)
        import matplotlib;matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axes=plt.subplots(1,4,figsize=(15,4),sharey=True)
        for ax,ds in zip(axes,['pleia_energy','pleia','rico','bdg2']):
            f=allmethods[(allmethods.dataset==ds)&(allmethods.level==.95)]
            for method,g in f.groupby('method'):ax.plot(g.horizon,g.native_coverage,marker='o',label=method)
            ax.axhline(.95,color='black',linestyle='--',linewidth=1);ax.set_title(ds);ax.set_xlabel('Horizon steps');ax.set_ylim(0,1.02)
        axes[0].set_ylabel('Coverage, nominal 95%');handles,labels=axes[-1].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=8)
        fig.tight_layout(rect=(0,.14,1,1));fig.savefig(out/'interval_undercoverage.png',dpi=160);fig.savefig(out/'interval_undercoverage.pdf');plt.close(fig)
        atomic(out/'interval_undercoverage.sources.json',dict(csv=str((diagnosis/'all_method_diagnostic.csv').relative_to(ROOT)),sha256=sha(diagnosis/'all_method_diagnostic.csv'),filter='level=.95, native support; fixed seed42',no_cross_target_error_pooling=True))
        supporttext='# Support gate status\n\nAll four matched interval adapters are implemented. The five declared families are quantile-uncalibrated, CQR, static EnbPI, updated EnbPI and DSCP. There is no missing sixth family. The 1,700 remaining cells are unexecuted scope.\n\n'
        supporttext+='The recomputed crosswalk covers 1,950 cells and all 36 joint fit/calibration/test role sets, with 24 strict boundaries. Fold-0/1 support now reads the frozen support table rather than fold-2 constants; existing real execution authorization guards remain explicit. Missing future XGBoost artifacts remain prerequisites for the all-method/DSCP bundle. Available artifacts are never inferred from an implemented adapter.\n\n'
        supporttext+=md(roles[['dataset','outer_fold','fit_rows','calibration_rows','outer_rows','original_outer_groups','contexts','unused_tail_rows']])+'\n\n'
        supporttext+='All original RICO runs retain their roles. Frequencies are 10 minutes for PLEIA, 1 minute for RICO and 1 hour for BDG2. PLEIA/BDG2 daily seasonal baselines reconcile to 9/27 unique deterministic computations; RICO daily baselines remain inapplicable. Forecasting is 70/195; interval methods are 250/1950. No synthetic test or support check fills a real-study cell.\n\n'
        supporttext+='PLEIA-energy C first-run owner reuse is disallowed: the matched fit contains three extra rows and its calibration lacks one C calibration row. C needs one new shared .95 quantile owner, three HistGradientBoosting sub-estimators, one public conformalization and one persistence radius. The same source group is preserved as literal `None`; the separately versioned crosswalk maps only that verified single-series identity to the matched empty-field representation.\n\n'
        supporttext+='Genuine remaining choices/dependencies: adoption of the new energy sensitivity proposal; absent fitted owners for future unexecuted matrix units; separately authorized real C execution; all five model seeds for inferential aggregation. RICO earliest outer inference retains a singleton phase and unavailable phase-stratified intervals. Early PLEIA inner contexts retain insufficient complete-week support. These limitations do not prevent the implemented fixed C replay.\n\n'
        supporttext+='[Recomputable scope crosswalk](../../smart_building_conformal/outputs/conditional_context005/implementation_support_v1/scope_crosswalk.csv), [context support](../../smart_building_conformal/outputs/conditional_context005/implementation_support_v1/context_role_support.csv), [support validation](../../smart_building_conformal/outputs/conditional_context005/implementation_support_v1/validation.json).\n'
        atomic(REVIEW/'SUPPORT_GATE_STATUS.md',supporttext)
        diagtext='# Interval failure diagnostic\n\nThe read-only extension covers all 130 preserved seed-42 method cells. The native CQR score/correction calculations reconstruct; no new arithmetic or owner-identity defect was demonstrated. Existing independent saved-owner validation remains authoritative for the native EnbPI OOB convention and dtype. Source artifacts remain byte-identical.\n\n'
        subset=owners[(owners.dataset=='pleia')&(owners.level==.95)]
        diagtext+=md(subset[['horizon','method','native_coverage','calibration_bias_prediction_minus_y','test_bias_prediction_minus_y','calibration_abs_error_q95','test_abs_error_q95','below_fraction','above_fraction']])+'\n\n'
        diagtext+='Static EnbPI uses native OOB calibration scores, while its centre is the preserved full-fit predictor. Those native scores can be far narrower than errors of that fixed predictor on the calibration and later test periods. The frozen MAPIE conformalization includes its declared calibration bootstrap fits; it is not equivalent to fixed-model absolute-error calibration. Nonfinite OOB scores remain counted explicitly. Undercoverage therefore cannot be explained away by swapping to another owner or treating every calibration score as the fixed predictor residual.\n\n'
        neg=owners[(owners.method=='cqr')&owners.negative_correction]
        diagtext+=f'{len(neg)} of {sum(owners.method=="cqr")} CQR level/horizon rows contain a negative native tail correction. Negative valid scores shrink overly wide raw tails under the declared convention. Levels are fitted separately and need not nest. For PLEIA-energy h1, the 95% upper correction is '+str(float(owners[(owners.dataset=='pleia_energy')&(owners.horizon==1)&(owners.level==.95)&(owners.method=='cqr')].iloc[0].correction_upper))+'. It is retained, with its resulting undercoverage.\n\n'
        diagtext+='Observed facts are the own-predictor bias, signed error distribution shifts, miss directions and support differences in the CSVs. Distribution change and the native OOB-versus-fixed-predictor calibration construction explain the numerical discrepancy descriptively. A unique causal attribution to meter faults, architecture, extrapolation or a particular covariate is unproven. No clipping, widening, row removal, level/rank changes or retuning occurred. No completed pilot is invalidated by this package.\n\n'
        diagtext+='[All-method table](../../smart_building_conformal/outputs/conditional_context005/interval_diagnostic_extension_v1/all_method_diagnostic.csv), [owner scores/corrections](../../smart_building_conformal/outputs/conditional_context005/implementation_support_v1/interval_owner_diagnostic.csv), [score distributions](../../smart_building_conformal/outputs/conditional_context005/implementation_support_v1/score_distributions.csv).\n'
        atomic(REVIEW/'INTERVAL_FAILURE_DIAGNOSTIC.md',diagtext)
        operations_summary=counts.pivot(index='dataset',columns='kind',values='executed_calls').reset_index()
        report='# Conditional-context005 implementation and synthetic acceptance\n\n'
        report+='The versioned `src.conditional_context005` CLI implements freeze, readiness, run, independent validate and completed resume. Both cadence fixtures completed every CLI stage. All real-data activity in this package was read-only; real fitting and real C replay remain unexecuted.\n\n'
        report+=md(worker[['task','actual_exit','seconds']])+'\n\n'+md(operations_summary)+'\n\n'
        report+='The public CQR conformalize call has one nested implementation call; two instrumented calls are one logical conformalization. Each fixture adds one persistence radius calculation and no persistence predictor fit. Test/debug fits are separately recorded in the regression/debug operation ledgers and are not real experiment cells.\n\n'
        report+='Corruption enters the sensor frame at observation time before causal lag, seasonal, rolling and missingness features. Each variant uses actual serialized estimators; raw/static/rolling controls share a quantile owner. Context resets, clean context identities, original full-stream trajectories and deterministic aliases have separate identities. Null events remain scheduled and add no positive denominator. Full-stream exposure includes eligible tails once per control/rule/channel.\n\n'
        report+='The independent validator reconstructs fault algebra, scalar features, direct-estimator predictions, native tails, delayed releases, rolling updates, alerts, episode matching, equal-context means and exposure. Completed resumes invoke zero fits and zero replay/calibration updates, preserving every scientific byte. Checkpoint corruption, future-sentinel, missing-score, group reset, hold/rank, alias/null, unavailable-macro and coordinator adoption cases are covered by regression tests.\n\n'
        report+='The first exploratory gate failed: scalar variance accumulation exceeded 1e-12 by approximately 2.4e-13; a negative synthetic shift remained in the same fitted leaf; and a source edit during a legacy smoke correctly triggered its source-identity resume guard. The source was stabilized, direct finite-window variance retained the same statistical definition and strict check, and the independently diagnosed positive fixture slot verifies predictor change. All failed logs are preserved; no real experiment was repeated or altered.\n\n'
        report+='Two complete CLI validation attempts exited 1 on empty numeric CSV observations, first during scalar comparison and then in independent alert reconstruction. Literal identity preservation had also preserved missing numeric cells as empty strings. The final repair decodes known numeric stream columns and comparison arrays; group identities stay untouched. A hash-exact, completed-validation-only compatibility receipt preserves the original fitted/replayed PLEIA artifacts. It does not permit old-source execution. The repaired validator and completed resume add zero fits. The full repository gate passed 446 tests with one skip; 38 focused checks then passed on the final numeric-reader repair, followed by two no-fitting paired-inference checks. The original failures, recovery records and all attempt costs remain published. A proposal-only freeze was initially invoked from the repository root and failed before import; its corrected smart_building_conformal working-directory command passed without fitting.\n\n'
        report+='C retains exactly four .95 controls and five applicable rules, no selection, and no A feasibility claim. Native static CQR uses asymmetric tail corrections; rolling CQR uses symmetric maximum nonconformity ranks. The original event timestamp endpoint is last envelope observation plus tolerance, yielding restricted elapsed horizons of 110 minutes (PLEIA) and 69 minutes (RICO). The physical envelope is still six/60 samples; this explicitly preserves the amendment-004 timestamp convention rather than extending matching by another sample.\n\n'
        report+='Inference interfaces average the five model seeds within original units, retain all 21 strata, use 2,000 fixed paired draws/seed20240601, seven-adjacent-context blocks or phase-stratified RICO runs, and retain unavailable bounds for insufficient/degenerate support. The synthetic and proposed single-seed real runs remain descriptive.\n\n'
        report+='The separate energy sensitivity interface is proposed, retrospective and unapproved. It does not alter online features, primary workload exposure or training. Remaining legacy calibration contamination/cascade/recovery obligations and the full 264-candidate BDG2 wrapper remain outstanding. Full-study readiness is false.\n'
        atomic(REVIEW/'IMPLEMENTATION_REPORT.md',report)
        # Proposal cost extrapolation uses only measured C stream work; real
        # 300-iteration fitting is deliberately not estimated from 3-iteration fits.
        phase=pd.DataFrame(cost);ctxcost=phase[(phase.dataset=='pleia_energy')&phase.stage.str.startswith('context_')]
        timecol='seconds' if 'seconds' in phase else 'wall_seconds'
        executed=sum(~table(SMART/f'outputs/conditional_context005/synthetic_pleia_energy_{version}/stages/tables/variants.csv').alias)
        projection=float(ctxcost[timecol].sum())*2924/max(1,executed)
        text='# First conditional-context real-run proposal\n\nPLEIA energy / outer fold 2 / model seed 42 / h1 (10 minutes), fixed .95, no inner or outer challenge selection. This is a concrete execution proposal and does not authorize a real run.\n\n'
        text+='The exact [68 published outer contexts](first_run_published_contexts.csv), [2,856 fault schedules](first_run_published_schedules.csv.gz) and [68 clean identities](first_run_zero_controls.csv) are included. All 21 strata, both slot seeds42/43 with signs-/+, all four controls and all five rules are retained. Rules consume shared streams; 171,360 event/control/rule/channel rows are expected before any aggregate, with null rows retained. These rows and aliases are not independent observations or model fits.\n\n'
        text+=md(pd.DataFrame(proposal['role_compatibility']))+'\n\n'
        text+='Required computation: one new HistGradientBoosting quantile CQR wrapper containing three native estimators, each with max_iter=300; one public conformalization (two nested calls in the profiler); one fixed persistence absolute-error radius. No tuning, XGBoost, LSTM, EnbPI or DSCP fit belongs to C. Raw/CQR/rolling share this owner; persistence uses its own calibration errors. Exact role/features/source compatibility rules rule out reusing the matched owner.\n\n'
        text+='Full-stream workload uses all 9,907 original eligible readings, 68.798611 asset-days, including 115 readings outside challenge tiles. It is counted once for each control/rule/channel. Contexts reset to the permitted 4,954-row historical calibration pool and their clean causal warm-up. Fitting uses 14,855 rows and 23 features. Primary meter values remain untouched.\n\n'
        text+=f'The synthetic PLEIA context-stage extrapolation is {projection:.1f} seconds for at most 2,924 separately reset replay executions, based on {executed} actually executed synthetic streams. These share original contexts and are not independent statistical observations. This is a scheduling calculation with substantial uncertainty from aliases, I/O and different feature count/model size. It excludes real owner fitting, final validation, preparation and publication; no real C fit cost has been measured. The synthetic cost CSV records actual phase/RSS/CPU values.\n\n'
        text+='Resources: existing `C:/cfs_venv`, CPU, one OMP/OpenBLAS/MKL/NumExpr thread, sequential workers, unchanged nonblocking 3 GiB RAM reference and 8 GiB disk floor. Retain the prepared-cache hash and published context/role/input hashes. A source or dependency change requires a fresh reviewed freeze; do not reuse a changed-source readiness receipt.\n\n'
        text+='After a new user instruction authorizes this exact real run, execute the activation helper and durable coordinator below. The helper refuses activation without its explicit acknowledgment flag; it copies the reviewed proposal to a separate execution manifest and preserves the proposal.\n\n```powershell\n& C:/cfs_venv/Scripts/python.exe -B review/context_replay005_implementation_20260914/first_real_coordinator.py --acknowledge-new-user-authorization\n```\n\n'
        text+='The [machine manifest](first_real_run_proposal_manifest.json), [no-fit readiness](FIRST_RUN_NO_FIT_READINESS.json) and [executable coordinator](first_real_coordinator.py) fix freeze/readiness/run/validate/resume argv and unused output paths. An interrupted coordinator adopts its surviving worker; a known failed worker stops for diagnosis. Completed stages and owners are reused; an incomplete fit stage is never blindly repeated. The energy sensitivity proposal remains a separate choice and does not block this unchanged primary C endpoint.\n'
        text+='\nA fresh [proposal-only freeze](../../smart_building_conformal/protocols/conditional_context005/pleia_energy_first_proposal_v3/frozen_protocol.json) and [readiness receipt](../../smart_building_conformal/protocols/conditional_context005/pleia_energy_first_proposal_v3/readiness.json) passed on the final repaired source with execution disabled. Earlier v1/v2 proposal freezes are preserved as superseded source snapshots. After authorization the coordinator creates distinct `pleia_energy_f2_s42_C_v1` protocol/output paths and `first_real_C_v1_coordinator` logs; it never activates the proposal artifact in place.\n'
        atomic(REVIEW/'FIRST_CONDITIONAL_CONTEXT_RUN_PROPOSAL.md',text)
        atomic(out/'validation.json',dict(passed=True,real_model_fits=0,real_context_replays=0,real_study_cells_added=0,
            matched_forecasting_complete=70,interval_methods_complete=250,seasonal_unique_complete=9,synthetic_cli_exit_zero=int((worker.actual_exit==0).sum()),
            synthetic_quantile_estimator_fits=int(sum(pd.DataFrame(ops).kind=='quantile_estimator_fit')),synthetic_cqr_wrapper_fits=int(sum(pd.DataFrame(ops).kind=='cqr_wrapper_fit')),
            synthetic_nested_conformalize_calls=int(sum(pd.DataFrame(ops).kind=='calibrator_conformalize')),full_study_ready=False))
    print('REPORTS RECOMPUTED FROM COMPLETED CLI EVIDENCE',flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--version',default='v1');main(p.parse_args().version)
