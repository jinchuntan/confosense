"""Executable SMOKE ONLY acceptance probes used by tests and saved evidence."""
from copy import deepcopy
import numpy as np
import pandas as pd
from . import conformal_cqr, split_integrity as SI
from .operational004_design import DESIGN, FAMILIES, candidates, nested_roles, make_outer_folds
from .operational004_events import catalogue, corruption
from .operational004_fixtures import fixture_data, sufficient_bank, DeterministicOwnedInterval
from .operational004_stream import OwnedInterval, replay, corrupted_features
from .operational004_metrics import (alert_on_stream, confidence_bounds, totals_metrics,
    select_pipeline, resampling_draws, group_recovery)
from .unit_checkpoint import signature


def selection_probes():
    """Actual 2,000-resample bounds feed both-fold selection, including ties."""
    rows=[];frames={};draw_records={}
    for fold,groups in enumerate((20,30)):
        bank,meta,events=sufficient_bank(groups)
        draws=resampling_draws(meta,pd.Timedelta('1h'),'bdg2')
        bounds=confidence_bounds(bank,events,meta,pd.Timedelta('1h'),'bdg2',draws)
        assert bounds['bound_status']=='supported' and bounds['valid_replicates']==2000
        metrics=totals_metrics(bank.select_dtypes(include=np.number).sum())
        rows.append(dict(inner_fold=fold,**bounds,**metrics,detected_delay_median_minutes=10.))
        frames[f'sufficient_fold{fold}_contributions']=bank
        frames[f'sufficient_fold{fold}_events']=pd.concat(events,ignore_index=True)
        draw_records[str(fold)]={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in draws.items()}
    grid=[dict(candidate_id='fixture_a'),dict(candidate_id='fixture_b')]
    surface=pd.DataFrame([dict(r,candidate_id=c['candidate_id']) for c in grid for r in rows])
    result=select_pipeline(surface,grid)
    assert result['pipeline']['candidate_id']=='fixture_a'
    average=(rows[0]['custom_synthetic_f1']+rows[1]['custom_synthetic_f1'])/2
    assert result['rejections'].equal_fold_custom_synthetic_f1.eq(average).all()
    assert not np.isclose(average,(20*rows[0]['custom_synthetic_f1']+30*rows[1]['custom_synthetic_f1'])/50)
    missing=select_pipeline(surface[surface.inner_fold.eq(0)],grid)
    assert missing['pipeline'] is None and missing['decision']=='no_feasible_configuration'
    failed=surface.copy();failed.loc[failed.inner_fold.eq(1),'recall_lcb']=.59
    both=select_pipeline(failed,grid)
    assert both['pipeline'] is None and both['rejections'].reasons.str.contains('fold1:recall_below_floor').all()
    high=surface.copy();high['workload_ucb']=10.;high['background_episodes_per_asset_day']=9.
    no=select_pipeline(high,grid);inverse=select_pipeline(high,grid,objective='inverse_recall_floor')
    assert no['pipeline'] is None and inverse['pipeline'] is not None
    unavailable=surface.copy();unavailable['bound_status']='insufficient_bound_support'
    unavailable['recall_lcb']=np.nan;unavailable['workload_ucb']=np.nan
    assert select_pipeline(unavailable,grid)['pipeline'] is None
    bank,meta,events=sufficient_bank(20,perfect=True)
    degenerate=confidence_bounds(bank,events,meta,pd.Timedelta('1h'),'bdg2')
    assert degenerate['bound_status']=='insufficient_bound_support'
    bank,meta,events=sufficient_bank(20);bank['clean_episodes']=0.
    zero_work=confidence_bounds(bank,events,meta,pd.Timedelta('1h'),'bdg2')
    assert zero_work['bound_status']=='insufficient_bound_support'
    bank,meta,events=sufficient_bank(4)
    small=confidence_bounds(bank,events,meta,pd.Timedelta('1h'),'bdg2')
    assert small['bound_status']=='insufficient_design_support'
    # Exact tie hierarchy: delay, then clean workload, then immutable ID.
    delay=surface.copy();delay.loc[delay.candidate_id.eq('fixture_b'),'detected_delay_median_minutes']=9.
    assert select_pipeline(delay,grid)['pipeline']['candidate_id']=='fixture_b'
    work=surface.copy();work.loc[work.candidate_id.eq('fixture_b'),'background_episodes_per_asset_day']=0.
    assert select_pipeline(work,grid)['pipeline']['candidate_id']=='fixture_b'
    frames.update(sufficient_surface=surface,sufficient_rejections=result['rejections'],all_infeasible_surface=failed,
                  all_infeasible_rejections=both['rejections'],unsupported_surface=unavailable)
    return dict(scope='SMOKE ONLY',feasible_selection=result['pipeline'],equal_fold_utility=average,
        unequal_original_groups=[20,30],both_folds_required=True,no_point_fallback=True,all_infeasible_abstains=True,
        exact_ties_verified=True,degenerate_recall=degenerate,degenerate_workload=zero_work,insufficient_groups=small,
        paired_resampling_draws=draw_records,inverse_comparison_separate=True),frames


def actual_cqr_probe():
    """One tiny actual CQR object (three standard quantile estimators), no tuning."""
    _,segmented,w,cfg,fcfg=fixture_data(n=1200,groups=1)
    tr=np.arange(400);ca=np.arange(401,801);ev=np.arange(802,1102)
    X,y,meta=w['X'],w['y'],w['meta'];block=meta.iloc[ev].reset_index(drop=True)
    model=OwnedInterval('cqr',.95,X.iloc[tr],y[tr],X.iloc[ca],y[ca],meta.iloc[ca],1,seed=42)
    grid=candidates(cfg,segmented.freq,smoke=True)
    static=next(c for c in grid if c['method']=='cqr' and c['strategy']=='static' and c['k']==1)
    rolling=next(c for c in grid if c['method']=='cqr' and c['strategy']=='rolling' and c['k']==1)
    flags=np.ones(len(ev),bool);obs=y[ev].copy()
    clean=replay(model,X.iloc[ev],block,obs,flags,rolling,segmented.freq)
    fixed=replay(model,X.iloc[ev],block,obs,flags,static,segmented.freq)
    original=conformal_cqr.cqr_interval(model.m,X.iloc[ev])
    assert np.array_equal(fixed['stream'].lower,original['lower']) and np.array_equal(fixed['stream'].upper,original['upper'])
    obs[50:110]+=8.;flags[130:140]=False;obs[~flags]=np.nan
    features=corrupted_features(segmented,block,obs,flags,1,fcfg,list(X.columns))
    corrupted=replay(model,features,block,obs,flags,rolling,segmented.freq)
    future=obs.copy();future[220:]+=100.
    future_X=corrupted_features(segmented,block,future,flags,1,fcfg,list(X.columns))
    later=replay(model,future_X,block,future,flags,rolling,segmented.freq)
    # At target index 50 the injected reading is still in the future at its origin.
    pd.testing.assert_frame_equal(features.iloc[:51],X.iloc[ev].reset_index(drop=True).iloc[:51])
    assert np.array_equal(clean['stream'].lower.iloc[:51],corrupted['stream'].lower.iloc[:51])
    pd.testing.assert_frame_equal(features.iloc[:221],future_X.iloc[:221])
    assert np.array_equal(corrupted['stream'].lower.iloc[:221],later['stream'].lower.iloc[:221])
    assert not np.array_equal(clean['stream'].lower.iloc[100:],corrupted['stream'].lower.iloc[100:])
    release=corrupted['released_scores'];issued=corrupted['stream'].set_index('row_id')
    for row in release.to_dict('records'):
        prior=issued.loc[row['row_id']]
        assert prior.available and row['kind']=='cqr_nonconformity' and row['prior_interval_compared']
        assert row['score']==max(prior.raw_lower-prior.observed,prior.observed-prior.raw_upper)
        assert pd.Timestamp(row['target_time'])<=pd.Timestamp(row['released_at_origin'])
    assert not set(block.loc[~flags,'row_id']) & set(release.row_id)
    assert (pd.to_datetime(corrupted['updates'].latest_score_target)<=pd.to_datetime(corrupted['updates'].origin_time)).all()
    scored=alert_on_stream(corrupted,rolling,pd.DataFrame(),segmented.freq)
    assert scored['consumed_hash']==corrupted['emitted_hash']
    assert scored['stream'].availability_violation.sum()==10
    return dict(scope='SMOKE ONLY',actual_cqr_objects_fitted=1,actual_quantile_sub_estimators_fitted=3,
        identity=model.identity,fit_identity=model.fit_identity,static_native_equality=True,
        future_sentinel_causal=True,corruption_changes_later_issued_bounds=True,missing_scores_excluded=True,
        method_specific_online_scores=True,clean_hash=clean['emitted_hash'],corrupted_hash=corrupted['emitted_hash'],
        consumed_hash=scored['consumed_hash'],training_rows=len(tr),calibration_rows=len(ca),evaluation_rows=len(ev)),dict(
        actual_cqr_clean=clean['stream'],actual_cqr_corrupted=scored['stream'],actual_cqr_static=fixed['stream'],
        actual_cqr_updates=corrupted['updates'],actual_cqr_released_scores=release,actual_cqr_calibration=model.calibration)


def zero_probe(segmented,w,cfg,fold):
    roles=nested_roles(w['meta'],fold,'chronological');meta=w['meta'];X=w['X'];y=w['y']
    tr,ca,ev=[roles[k] for k in ('inner0_train','inner0_calibration','inner0_selection')]
    from .windowing import feature_config
    fcfg=feature_config(cfg,segmented.series[0].covariates);block=meta.iloc[ev].reset_index(drop=True)
    model=DeterministicOwnedInterval('cqr',.95,X.iloc[tr],y[tr],X.iloc[ca],y[ca],meta.iloc[ca],1,42)
    candidate=next(c for c in candidates(cfg,segmented.freq,smoke=True) if c['method']=='cqr' and c['strategy']=='rolling')
    clean=replay(model,X.iloc[ev],block,y[ev],np.ones(len(ev),bool),candidate,segmented.freq)
    scales=SI.training_scale(y,meta,tr);rows=[]
    for seed in DESIGN['catalogue_seeds']:
        obs,flags,events,_=catalogue(y[ev],block,segmented.freq,scales,'synthetic004','inner0_selection',0,seed,zero=True)
        xx=corrupted_features(segmented,block,obs,flags,1,fcfg,list(X.columns))
        zero=replay(model,xx,block,obs,flags,candidate,segmented.freq)
        assert np.array_equal(obs,y[ev]) and flags.all() and not events.effective.any()
        assert zero['emitted_hash']==clean['emitted_hash']
        rows.append(dict(catalogue_seed=seed,zero_emitted_hash=zero['emitted_hash'],clean_emitted_hash=clean['emitted_hash'],identity=True))
    for family in FAMILIES:
        values=np.arange(6.)+10
        obs,flags=corruption(values,family,0.,3.,1,np.random.default_rng(42),9.)
        assert np.array_equal(values,obs) and flags.all()
        rows.append(dict(family=family,zero_severity_identity=True))
    return pd.DataFrame(rows)
