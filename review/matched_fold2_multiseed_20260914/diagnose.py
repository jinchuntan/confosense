"""Bounded retrospective diagnosis from preserved seed-42 artifacts; never fits."""
import gc, math, sys
from decimal import Decimal, ROUND_CEILING
from common import *
sys.path.insert(0,str(SMART))
from src import matched_forecasting005 as R
from src.matched_models005 import forbid_fitting, restore
from src import pilot_forecasters as F
from src.unit_checkpoint import source_digest
import numpy as np
import pandas as pd

OUT=BATCH/'diagnosis_v2'
UNITS={'pleia':'degrees C','rico':'degrees C','pleia_energy':'kWh per 10 minutes','bdg2':'kWh per hour'}
MINUTES={'pleia':10,'pleia_energy':10,'rico':1,'bdg2':60}
INPUTS={}
def frame(path):
    path=Path(path);INPUTS[path.relative_to(ROOT).as_posix()]=sha(path)
    return pd.read_csv(path,keep_default_na=False,float_precision='round_trip',dtype={'row_id':str,'group_id':str})
def record(path):
    path=Path(path);INPUTS[path.relative_to(ROOT).as_posix()]=sha(path);return read(path)
def dump(name,rows):pd.DataFrame(rows).to_csv(OUT/name,index=False)
def stats(values):
    a=np.asarray(values,dtype=float)
    return dict(n=len(a),minimum=a.min(),maximum=a.max(),mean=a.mean(),std=a.std(),median=np.median(a),q90=np.quantile(a,.9,method='higher'),q95=np.quantile(a,.95,method='higher'),q99=np.quantile(a,.99,method='higher'))
def errors(f):
    e=f.point.to_numpy()-f.y_true.to_numpy()
    return dict(n=len(f),bias=e.mean(),mae=np.abs(e).mean(),rmse=np.sqrt(np.square(e).mean()),truth_mean=f.y_true.mean(),truth_min=f.y_true.min(),truth_max=f.y_true.max(),prediction_min=f.point.min(),prediction_max=f.point.max())
def tab(f,cols):
    def fmt(v):return f'{v:.6g}' if isinstance(v,(float,np.floating)) else str(v)
    return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+''.join('| '+' | '.join(fmt(r[c]) for c in cols)+' |\n' for _,r in f.iterrows())

def main():
    os.chdir(SMART);R.setup_threads();OUT.mkdir(parents=True,exist_ok=False)
    assert source_digest()=='cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e'
    ledger=frame(OLD_ANALYSIS/'evidence_reuse_ledger.csv');ledger=ledger[ledger.outer_fold==2]
    assert len(ledger)==13 and set(ledger.model_seed)=={42}
    protocols={sha(p):p for p in (SMART/'protocols/matched_forecasting005').glob('*/frozen_protocol.json')}
    history=frame(SMART/'outputs/amendment005/study_plan_v1/rico_run_history.csv').set_index('group_id')
    distributions=[];role_ranges=[];point=[];group_errors=[];equal=[];calibration=[];blocks=[];identity=[];learning=[]
    for row in ledger.to_dict('records'):
        key=tuple(row[k] for k in KEYCOLS);ds,h,fold,seed=key;run=ROOT/row['run_path'];before=tree(run)
        assert hashlib.sha256('\n'.join(f'{p}:{v}' for p,v in before.items()).encode()).hexdigest()==row['run_file_tree_hash']
        protocol_path=protocols[row['protocol_hash']];protocol=record(protocol_path)
        meta={k:row[k] for k in KEYCOLS};meta.update(target_units=UNITS[ds],physical_minutes=h*MINUTES[ds],source_run=row['run_path'],source_hash=row['source_hash'],protocol_hash=row['protocol_hash'])
        data=roles=None
        if ds in ('pleia','rico'):
            data,roles=R.fresh_data(protocol)
            assert data['data_hash']==protocol['support']['data_hash']
            # Existing independent validators already checked alignment, scaling,
            # selection, checkpoint identity and prediction inversion. This bounded
            # diagnosis reuses them; fit predictions are inference on saved objects.
            for role,idx in roles.items():
                base=roles['fit'] if not role.startswith('inner') else roles[role[:6]+'_train']
                timestamps=data['meta'].iloc[idx]
                rolemeta=dict(meta,role=role,**{k:v for k,v in protocol['support']['roles'][role].items() if k!='n'},groups=timestamps.group_id.nunique())
                ys=stats(data['y'][idx]);reference=data['y'][base]
                role_ranges.append(dict(rolemeta,**ys,reference_role='fit' if not role.startswith('inner') else role[:6]+'_train',below_reference_min=float((data['y'][idx]<reference.min()).mean()),above_reference_max=float((data['y'][idx]>reference.max()).mean())))
                for column in data['X'].columns:
                    a=data['X'].iloc[idx][column].to_numpy(float);b=data['X'].iloc[base][column].to_numpy(float)
                    distributions.append(dict(meta,role=role,representation='flat permitted feature at forecast origin; not a hidden activation',feature=column,**stats(a),reference_role='fit' if not role.startswith('inner') else role[:6]+'_train',reference_min=b.min(),reference_max=b.max(),below_reference_min=float((a<b.min()).mean()),above_reference_max=float((a>b.max()).mean())))
        for model in MODELS:
            directory=run/'units'/f'{ds}_h{h}_f{fold}_s{seed}_{model}'
            payload=record(directory/'payload.json');cal=frame(directory/'calibration.csv.gz');pred=frame(directory/'predictions.csv.gz')
            test=pred[pred.nominal_level==.9].copy();cal=cal.copy()
            assert len(test)==payload['point']['n_evaluation'] and len(cal)==payload['point']['n_calibration']
            np.testing.assert_allclose(cal.absolute_error,np.abs(cal.y_true-cal.point),rtol=0,atol=1e-12)
            parts=[('calibration',-1,cal),('test',-1,test)]
            if data is not None:
                fitted=restore(model,directory,data)
                fit= data['meta'].iloc[roles['fit']][['row_id','group_id','origin_time','target_time']].copy()
                fit['y_true']=data['y'][roles['fit']];fit['point']=F.predict(fitted,model,data,roles['fit'],256)
                fit.group_id=fit.group_id.astype(str);fit.to_csv(OUT/f'{ds}_h{h}_{model}_saved_model_fit_predictions.csv.gz',index=False,compression={'method':'gzip','mtime':0})
                parts.append(('fit',payload['selected_candidate'],fit))
                if model=='persistence':
                    for inner in range(2):
                        idx=roles[f'inner{inner}_validation'];f=data['meta'].iloc[idx][['row_id','group_id','origin_time','target_time']].copy()
                        f['y_true']=data['y'][idx];f['point']=F.predict(fitted,model,data,idx,256);f.group_id=f.group_id.astype(str)
                        parts.append((f'inner{inner}_validation',-1,f))
                else:
                    tuning=frame(directory/'tuning_predictions.csv.gz')
                    for (candidate,inner),f in tuning.groupby(['candidate_id','inner_fold']):parts.append((f'inner{inner}_validation',candidate,f))
                    scores=frame(directory/'tuning.csv.gz')
                    for s in scores.to_dict('records'):learning.append(dict(meta,model=model,selected_candidate=payload['selected_candidate'],final_epochs=payload['final_epochs'],**s))
                if model=='attention_lstm':
                    np.testing.assert_allclose([fitted.y_mean,fitted.y_std],[data['y'][roles['fit']].mean(),data['y'][roles['fit']].std() or 1.],atol=1e-12,rtol=1e-12)
                    assert payload['sequence_channels']==data['sequence_channels'] and payload['feature_names']==data['feature_names']
                del fitted
            for role,candidate,f in parts:
                pm=dict(meta,model=model,role=role,candidate_id=candidate,selected_candidate=payload['selected_candidate'],prediction_source='new inference from unchanged saved final model' if role=='fit' else 'saved prediction stream' if model!='persistence' or not role.startswith('inner') else 'deterministic persistence on identical existing inner rows')
                point.append(dict(pm,aggregation='sample weighted',**errors(f)))
                local=[]
                for group,part in f.groupby('group_id',sort=False):
                    g=dict(pm,group_id=str(group),aggregation='within original group',**errors(part))
                    if ds=='rico':g['phase']=history.loc[str(group),'phase']
                    group_errors.append(g);local.append(g)
                for field in ['bias','mae']:
                    np.testing.assert_allclose(np.average([g[field] for g in local],weights=[g['n'] for g in local]),errors(f)[field],atol=1e-12,rtol=1e-12)
                np.testing.assert_allclose(np.sqrt(np.average([g['rmse']**2 for g in local],weights=[g['n'] for g in local])),errors(f)['rmse'],atol=1e-12,rtol=1e-12)
                equal.append(dict(pm,original_groups=len(local),aggregation='equal original-group diagnostic; not pooled',bias=np.mean([g['bias'] for g in local]),mae=np.mean([g['mae'] for g in local]),root_mean_group_mse=np.sqrt(np.mean([g['rmse']**2 for g in local]))))
            ecal=np.abs(cal.y_true-cal.point).to_numpy();etest=np.abs(test.y_true-test.point).to_numpy()
            for saved in payload['intervals']:
                level=saved['nominal_level'];q=saved['q'];rank=int((Decimal(len(ecal)+1)*Decimal(str(level))).to_integral_value(rounding=ROUND_CEILING))
                assert rank==saved['rank'];np.testing.assert_allclose(np.sort(ecal)[rank-1],q,atol=1e-12,rtol=1e-12)
                saved_level=pred[pred.nominal_level==level]
                inside=((saved_level.lower<=saved_level.y_true)&(saved_level.y_true<=saved_level.upper)).to_numpy()
                mismatch=inside!=(etest<=q)
                tolerance=8*np.finfo(float).eps*np.maximum(1,np.maximum(np.abs(test.y_true),np.abs(test.point)))
                assert np.all(np.abs(etest[mismatch]-q)<=tolerance[mismatch]), 'non-boundary interval/error mismatch'
                np.testing.assert_allclose(inside.mean(),saved['coverage'],atol=1e-12,rtol=1e-12)
                calibration.append(dict(meta,model=model,nominal_level=level,frozen_radius=q,finite_sample_rank=rank,calibration_exceedance=float((ecal>q).mean()),test_absolute_error_exceedance=float((etest>q).mean()),test_exceedance=float((~inside).mean()),test_coverage=float(inside.mean()),floating_boundary_ties=int(mismatch.sum()),signed_coverage_deviation=float(inside.mean()-level),absolute_coverage_deviation=abs(float(inside.mean()-level)),**{'calibration_abs_'+k:v for k,v in stats(ecal).items()},**{'test_abs_'+k:v for k,v in stats(etest).items()},test_quantiles_use='retrospective diagnostic only; never used to choose a radius or decision'))
                for role,f in [('calibration',cal),('test',test)]:
                    f=f.copy();f['calendar_month']=f.target_time.astype(str).str[:7]
                    for kind,column in [('calendar month','calendar_month'),('original group','group_id')]:
                        for label,part in f.groupby(column,sort=False):
                            e=np.abs(part.y_true-part.point)
                            inside=(part.point-q<=part.y_true)&(part.y_true<=part.point+q)
                            blocks.append(dict(meta,model=model,role=role,nominal_level=level,block_kind=kind,block=str(label),n=len(part),original_groups=part.group_id.nunique(),frozen_radius=q,coverage=float(inside.mean()),absolute_error_exceedance=float((e>q).mean()),bias=float((part.point-part.y_true).mean()),mae=float(e.mean()),rmse=float(np.sqrt(np.square(e).mean()))))
            identity.append(dict(meta,model=model,estimator_class=payload['point']['estimator_class'],saved_seed=payload['model_seed'],artifact_directory=directory.relative_to(ROOT).as_posix(),fitting_performed=False,existing_full_validation='reused prior independent artifact/selection/support validation',new_identity_or_correctness_defect=False))
        assert tree(run)==before
        del data,roles;gc.collect();print('DIAGNOSED',key,flush=True)
    dump('role_target_ranges.csv',role_ranges);dump('permitted_feature_ranges.csv',distributions);dump('point_bias_by_role.csv',point);dump('point_bias_by_original_group.csv',group_errors);dump('equal_group_bias_diagnostics.csv',equal);dump('frozen_radius_residual_shift.csv',calibration);dump('timeblock_group_coverage.csv',blocks);dump('artifact_identity.csv',identity);dump('preserved_tuning_choices.csv',learning)
    groupframe=pd.DataFrame(group_errors);phase=[]
    rico=groupframe[groupframe.dataset=='rico']
    for key,f in rico.groupby(KEYCOLS+['model','role','candidate_id','phase'],dropna=False):
        r=dict(zip(KEYCOLS+['model','role','candidate_id','phase'],key));base=f.iloc[0]
        r.update({k:base[k] for k in ['source_run','source_hash','protocol_hash','physical_minutes','target_units']})
        phase.append(dict(r,original_runs=len(f),n=int(f.n.sum()),sample_weighted_bias=np.average(f.bias,weights=f.n),sample_weighted_mae=np.average(f.mae,weights=f.n),sample_weighted_rmse=np.sqrt(np.average(f.rmse**2,weights=f.n)),equal_run_bias=f.bias.mean(),equal_run_mae=f.mae.mean(),equal_run_root_mean_mse=np.sqrt(np.mean(f.rmse**2))))
    dump('rico_phase_bias.csv',phase)
    pd.DataFrame([dict(path=p,sha256=s) for p,s in sorted(INPUTS.items())]).to_csv(OUT/'input_manifest.csv',index=False)
    c=pd.DataFrame(calibration);p=pd.DataFrame(point);r=pd.DataFrame(role_ranges)
    rel=OUT.relative_to(ROOT).as_posix()
    text='# Matched failure diagnosis: preserved fold-2 seed-42 evidence\n\nNo new unresolved correctness defect was demonstrated. All thirteen existing task/horizon units were inspected without fitting or repeating historical tuning. Existing exact model-reload, support, normalization, selection and interval-arithmetic checks remain valid. Measured distribution changes and prediction bias warrant reporting; they do not identify their causal mechanism. The authorized seed replication may proceed with unchanged scientific settings.\n\n'
    text+='## Observed bias and distributions\n\nFinal fitting predictions below are new inference using the preserved fitted objects; calibration/test and learned inner-validation predictions are saved streams. Inner training predictions were not saved and are not recreated by refitting. Current role boundaries and target ranges are in [role_target_ranges.csv]('+rel+'/role_target_ranges.csv); every permitted flat-feature range is in [permitted_feature_ranges.csv]('+rel+'/permitted_feature_ranges.csv). These describe available inputs at the origin; flat and sequence representations remain distinct.\n\n'
    for ds in ['pleia','rico']:
        text+='### '+ds+'\n\n'+tab(p[(p.dataset==ds)&p.role.isin(['fit','calibration','test'])],['horizon','model','role','n','truth_mean','bias','mae','rmse'])+'\n'
        text+=tab(r[(r.dataset==ds)&r.role.isin(['fit','calibration','test'])],['horizon','role','origin_min','origin_max','minimum','maximum','mean','above_reference_max','below_reference_min'])+'\n'
    text+='[All candidate inner-validation errors]( '+rel+'/point_bias_by_role.csv) retain the original candidate IDs and selected choices. [RICO phase bias]( '+rel+'/rico_phase_bias.csv) distinguishes count-weighted metrics from equal-run diagnostics. Group RMSE reconciles through counts and squared errors, not an average of RMSE. Repeated runs, horizons and training seeds do not add independent acquisition periods.\n\n'
    text+='## Why the frozen intervals miss\n\nThe radius is the declared finite-sample order statistic of that fitted model\'s calibration absolute errors. Test errors increase relative to this fixed radius. Coverage uses the saved inclusive lower/upper endpoints. Direct absolute-error comparisons can differ at floating-point boundary ties; both counts are exported and every difference is verified within floating-point precision. The first diagnostic attempt rejected these ties, and its failed log is preserved; the diagnostic was corrected without changing any model, interval or historical metric. Empirical test quantiles are retrospective descriptions only and never change a radius, candidate or threshold.\n\n'
    text+=tab(c[c.nominal_level==.95],['dataset','horizon','model','frozen_radius','calibration_abs_q95','test_abs_q95','calibration_exceedance','test_exceedance','test_coverage'])+'\n'
    text+='[Both levels and full error distributions]('+rel+'/frozen_radius_residual_shift.csv) and [calendar-month/original-group coverage]('+rel+'/timeblock_group_coverage.csv) show heterogeneity hidden by pooled summaries. PLEIA energy preserves its zeros, stalls and catch-up values, including persistence failures. BDG2 is a contrasting pooled case on the same ten known buildings; near-nominal pooled coverage is not a conditional or unseen-building guarantee.\n\n'
    text+='## Findings, hypotheses and preserved identity\n\nConfirmed measurements: target/covariate range shifts, model-specific signed prediction bias, and changes between calibration and test absolute-error distributions. No new alignment, current-observation, channel-order, train-only scaling/inversion or saved-model identity defect is established. Existing independent checks resolve those correctness questions; this task additionally verifies raw support identity and saved final target scaling during inference. Architecture saturation, extrapolation behavior, training budget and loss/selection mismatch remain hypotheses, without controlled causal ablations. Neither a correlation nor another training seed establishes a repair.\n\n'
    text+='The [older pilot diagnosis](PILOT_DIAGNOSTICS.md) used different fits and development partitions, and previously required 24 reproduced inner fits because those predictions had not been saved. This task performs zero fits and uses the current saved inner streams. Overlapping calendar dates do not make those old and current models identical. All source runs are byte-identical after diagnosis; [input manifest]('+rel+'/input_manifest.csv) and [artifact identities]('+rel+'/artifact_identity.csv) bind these conclusions. Scientific source SHA-256 remains `'+source_digest()+'`.\n'
    text=text.replace(']('+ ' '+rel,']('+rel)
    atomic(ROOT/'MATCHED_FAILURE_DIAGNOSIS.md',text)
    result=dict(passed=True,models_fitted=0,historical_tuning_repeated=0,source_hash=source_digest(),inspected_paired_units=13,inspected_models=39,interval_diagnostics=78,all_historical_run_files_unchanged=True,unresolved_correctness_defect=False,expansion_may_proceed=True,test_quantiles_used_for_selection=False)
    atomic(OUT/'validation.json',result);atomic(OUT/'COMPLETE.json',dict(files=tree(OUT),models_fitted=0));print(json.dumps(result),flush=True)

if __name__=='__main__':
    with forbid_fitting():main()
