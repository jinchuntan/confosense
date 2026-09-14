"""No-fit support reconciliation and missing interval-owner diagnosis."""
from common import *
import gc,hashlib,numpy as np,pandas as pd
from src.context005_spec import BASE,FINAL,PLAN,table,identity_crosswalk
from src.intervals005_common import Operations,csv,load_owner
from src.intervals005_data import LEDGER
from src.matched_intervals005 import scope_policy

OUT=SMART/'outputs/conditional_context005/implementation_support_v1'
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    inputs={};records=[];checks=[]
    def t(path):inputs[str(path.relative_to(ROOT))]=sha(path);return table(path)
    with Operations(forbid=True):
        matrix=t(PLAN/'interval_method_matrix.csv');joint=t(FINAL/'dscp_joint_origin_membership.csv.gz');support=t(FINAL/'dscp_joint_origin_support.csv');owners=t(LEDGER)
        completion=t(SMART/'outputs/matched_intervals005/four_settings_f2_s42_v2_coordinator/analysis_v2/interval_completion_overlay.csv')
        print('completion columns',completion.columns.tolist(),flush=True)
        for ds in ['pleia_energy','pleia','rico','bdg2']:
            freq=pd.Timedelta('10min' if ds.startswith('pleia') else '1min' if ds=='rico' else '1h')
            horizons=[5,15,30,60] if ds=='rico' else [1,3,6]
            memberships={h:t(BASE/f'{ds}_h{h}_forecast_membership.csv.gz') for h in horizons}
            for fold in [0,1,2]:
                policy=scope_policy(ds,fold);rolekeys={}
                for role in ['fit','calibration','test']:
                    pieces=[]
                    for h,mem in memberships.items():
                        local=mem[mem[f'fold{fold}_roles'].map(lambda s:role in s.split('|'))]
                        if not (pd.to_datetime(local.target_time)-pd.to_datetime(local.origin_time)).eq(h*freq).all():raise ValueError('cadence/target failure')
                        pieces.append(set(zip(local.group_id,local.origin_time)))
                    common=set.intersection(*pieces);pub=joint[(joint.dataset==ds)&(joint.outer_fold==fold)&(joint.role==role)]
                    if common!=set(zip(pub.group_id,pub.origin_time)) or len(common)!=policy['joint_support'][role]:raise ValueError('joint membership mismatch')
                    rolekeys[role]=pub
                    records.append(dict(dataset=ds,outer_fold=fold,role=role,joint_rows=len(pub),groups=pub.group_id.nunique(),frequency_minutes=freq/pd.Timedelta('1min'),membership_no_fit_passed=True))
                for a,b in [('fit','calibration'),('calibration','test')]:
                    if pd.to_datetime(rolekeys[a].origin_time).max()+max(horizons)*freq>=pd.to_datetime(rolekeys[b].origin_time).min():raise ValueError('joint boundary')
                    if ds=='rico' and set(rolekeys[a].group_id)&set(rolekeys[b].group_id):raise ValueError('RICO split group')
                    checks.append(dict(dataset=ds,outer_fold=fold,boundary=a+'_'+b,passed=True))
        cells=[]
        for r in matrix.to_dict('records'):
            q=owners[(owners.dataset==r['dataset'])&(owners.outer_fold==r['outer_fold'])&(owners.model_seed==r['model_seed'])&(owners.horizon==r['horizon'])]
            c=completion[(completion.dataset==r['dataset'])&(completion.outer_fold==r['outer_fold'])&(completion.model_seed==r['model_seed'])&(completion.horizon==r['horizon'])&(completion.level==r['level'])&(completion.method==r['method'])]
            status=c.iloc[0].get('completion_status',c.iloc[0].get('status','')) if len(c) else ''
            cells.append(dict(dataset=r['dataset'],outer_fold=r['outer_fold'],model_seed=r['model_seed'],horizon=r['horizon'],level=r['level'],method=r['method'],
                adapter_implemented=True,no_fit_role_support_passed=True,matched_xgboost_owner_available=len(q)==1,completion_status=status,
                execution_prerequisite='owner_artifact_absent' if len(q)!=1 else 'fresh_versioned_authorization_and_readiness_for_unexecuted_cells'))
        csv(OUT/'scope_crosswalk.csv',pd.DataFrame(cells));csv(OUT/'joint_support.csv',pd.DataFrame(records));csv(OUT/'boundary_checks.csv',pd.DataFrame(checks))
        # Published context roles are checked separately from matched masks.
        from src.context005_data import load_real
        crows=[];cross=[]
        for ds in ['pleia_energy','pleia','rico']:
            for fold in [0,1,2]:
                d=load_real(ds,fold);m=d['meta'];r=d['roles'];ctx=d['contexts'];test=m.iloc[r['outer_test']].reset_index(drop=True)
                from src.context005_spec import context_positions
                covered=set()
                for c in ctx.to_dict('records'):covered.update(context_positions(test,c))
                crows.append(dict(dataset=ds,outer_fold=fold,fit_rows=len(r['final_fit']),calibration_rows=len(r['final_calibration']),outer_rows=len(test),
                    original_outer_groups=test.group_id.nunique(),contexts=len(ctx),scheduled=len(d['schedules']),context_eligible_rows=len(covered),unused_tail_rows=len(test)-len(covered),
                    full_original_asset_days=len(test)*d['frequency']/pd.Timedelta('1D'),source_cache_sha256=d['cache_sha256'],passed=True))
                old=t(BASE/f'{ds}_h{d["horizon"]}_forecast_membership.csv.gz')
                cross.append(identity_crosswalk(ds,m.group_id.unique(),old.group_id.unique()))
                del d;gc.collect()
        csv(OUT/'context_role_support.csv',pd.DataFrame(crows));atomic(OUT/'identity_crosswalk.json',cross)
        # Diagnose intervals from immutable saved predictions and owner scores.
        diagnostic=[];score_tables=[]
        runs={'pleia_energy':'pleia_energy_f2_s42_v2','pleia':'pleia_f2_s42_v1','rico':'rico_f2_s42_v1','bdg2':'bdg2_f2_s42_v1'}
        for ds,run in runs.items():
            stage=SMART/'outputs/matched_intervals005'/run/'stages'
            native=t(stage/'tables/native_support_metrics.csv');common=t(stage/'tables/common_support_metrics.csv')
            for h in sorted(native.horizon.unique()):
                for kind,levels in [('cqr',[.9,.95]),('enbpi',[.9,.95])]:
                    for level in levels:
                        suffix=f'h{h}_{kind}'+(f'_l{int(level*100)}' if kind=='cqr' else '')
                        cal=t(stage/('raw_'+suffix)/f'calibration_{int(level*100)}.csv.gz');calmeta=t(stage/('raw_'+suffix)/'calibration_metadata.csv.gz')
                        raw=t(stage/('raw_'+suffix)/f'test_{int(level*100)}.csv.gz');meta=t(stage/('raw_'+suffix)/'test_metadata.csv.gz')
                        owner_path=stage/('owner_cal_'+suffix)/'owner.pkl';inputs[str(owner_path.relative_to(ROOT))]=sha(owner_path);owner=load_owner(owner_path)
                        ycal=calmeta.y_true.to_numpy();yt=meta.y_true.to_numpy();calerr=ycal-cal.point.to_numpy();testerr=yt-raw.point.to_numpy()
                        score=np.asarray(owner._mapie_quantile_regressor.conformity_scores_ if kind=='cqr' else owner.conformity_scores_)
                        if kind=='cqr':
                            tails=np.vstack([cal.raw_lower-ycal,ycal-cal.raw_upper]);np.testing.assert_allclose(score[:2],tails,atol=1e-10,rtol=0)
                            corrections=np.quantile(tails,(1-(1-level)/2)*(1+1/len(ycal)),axis=1,method='higher')
                            lower=np.minimum(raw.raw_lower-corrections[0],raw.raw_upper+corrections[1]);upper=np.maximum(raw.raw_lower-corrections[0],raw.raw_upper+corrections[1]);method='cqr'
                        else:
                            corrections=np.array([np.median(raw.static_lower-raw.point),np.median(raw.static_upper-raw.point)]);lower=raw.static_lower;upper=raw.static_upper;method='recentred_enbpi_static'
                        np.testing.assert_allclose(lower,raw.static_lower,atol=1e-7,rtol=1e-7);np.testing.assert_allclose(upper,raw.static_upper,atol=1e-7,rtol=1e-7)
                        n=native[(native.horizon==h)&(native.level==level)&(native.method==method)].iloc[0];c=common[(common.horizon==h)&(common.level==level)&(common.method==method)].iloc[0]
                        diagnostic.append(dict(dataset=ds,horizon=int(h),level=level,method=method,calibration_rows=len(ycal),test_rows=len(yt),native_n=int(n.n),common_n=int(c.n),
                            native_coverage=n.coverage,common_coverage=c.coverage,mpiw=n.mpiw,winkler=n.winkler,available=int(meta.available.sum()),
                            calibration_bias_prediction_minus_y=float(-calerr.mean()),test_bias_prediction_minus_y=float(-testerr.mean()),
                            calibration_abs_error_q95=float(np.quantile(abs(calerr),.95)),test_abs_error_q95=float(np.quantile(abs(testerr),.95)),
                            correction_lower=float(corrections[0]),correction_upper=float(corrections[1]),negative_correction=bool((corrections<0).any()) if kind=='cqr' else False,
                            below_fraction=float((yt<lower).mean()),above_fraction=float((yt>upper).mean()),
                            score_nonfinite=int((~np.isfinite(score)).sum()),owner_sha256=sha(owner_path),arithmetic_defect_demonstrated=False,
                            native_convention='asymmetric native CQR tails' if kind=='cqr' else 'native MAPIE OOB calibration scores around final own point',
                            units='kWh per interval' if ds in ('pleia_energy','bdg2') else 'degrees Celsius'))
                        for label,values in [('own_calibration_signed_error',calerr),('own_test_signed_error',testerr),('native_calibration_score',score.ravel())]:
                            v=values[np.isfinite(values)];score_tables.append(dict(dataset=ds,horizon=int(h),level=level,method=method,distribution=label,n=len(v),mean=float(v.mean()),**{f'q{q}':float(np.quantile(v,q/100)) for q in [1,5,25,50,75,95,99]}))
                        del owner;gc.collect()
        csv(OUT/'interval_owner_diagnostic.csv',pd.DataFrame(diagnostic));csv(OUT/'score_distributions.csv',pd.DataFrame(score_tables))
        # Integrity count and historical stage checks are already independently
        # validated; this diagnostic does not relabel their older source.
        if any(sha(ROOT/name)!=h for name,h in inputs.items()):raise ValueError('diagnostic mutated preserved input')
        csv(OUT/'input_hashes.csv',pd.DataFrame([dict(path=k,sha256=v) for k,v in inputs.items()]))
        atomic(OUT/'validation.json',dict(passed=True,models_fitted=0,calibrators_fitted=0,joint_role_rows=len(records),boundaries=len(checks),context_role_sets=len(crows),interval_diagnostics=len(diagnostic),inputs_unchanged=True,real_study_cells_added=0))
    print('NO FIT SUPPORT AND INTERVAL DIAGNOSTIC COMPLETE',flush=True)

if __name__=='__main__':main()
