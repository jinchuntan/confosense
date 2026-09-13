"""Amendment-004 nested selection and paired evaluation, isolated from old runs."""
from __future__ import annotations
from copy import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from . import split_integrity as SI, windowing
from .operational004_design import DESIGN, candidates, nested_roles, resampling_support
from .operational004_events import catalogue, bank_support
from .operational004_stream import OwnedInterval, corrupted_features, replay, stream_hash
from .operational004_metrics import (alert_on_stream, contributions, pool_bank, summarize_bank,
    confidence_bounds, resampling_draws, select_pipeline, family_attribution, group_workload, group_recovery)
from .unit_checkpoint import UnitCheckpoint, signature, source_digest


def _tag(frame,**tags):
    frame=frame.copy()
    for k,v in tags.items():frame[k]=v
    return frame


def _concat(frames):
    return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()


def evaluate_block(dataset,fold,role,model_seed,segmented,w,cfg,train,cal,selection,grid,
                   *,model_factory=OwnedInterval,force_diagnostic=False,save_streams=False):
    """A block receives only its own fitting/calibration/selection memberships.

    force_diagnostic computes unsupported cells for explicitly labeled software
    fixtures or diagnostics; it cannot change their feasibility/support status.
    """
    meta,X,y=w['meta'],w['X'],w['y'];freq=segmented.freq;horizon=w['horizon']
    scheme=meta.attrs.get('split_scheme','chronological')
    SI.assert_boundary(meta,train,cal,scheme);SI.assert_boundary(meta,cal,selection,scheme)
    if len(train)<400 or len(cal)<400 or len(selection)<200:
        raise ValueError('declared train/calibration/selection minimum not met')
    block=meta.iloc[selection].reset_index(drop=True)
    fcfg=windowing.feature_config(cfg,segmented.series[0].covariates)
    scales=SI.training_scale(y,meta,train)
    observations={};available={};catalogues={};allocations=[]
    for seed in DESIGN['catalogue_seeds']:
        obs,flags,cat,allocation=catalogue(y[selection],block,freq,scales,dataset,role,fold,seed)
        observations[seed]=obs;available[seed]=flags;catalogues[seed]=cat
        allocations.append(dict(dataset=dataset,outer_fold=fold,role=role,**allocation))
    structural=bool(bank_support(list(catalogues.values())).support.all() and
                    resampling_support(block,freq,dataset)['enough_original_units'])
    rows=[];streams=[];hashes=[];episodes=[];event_scores=[];pooled=[];updates=[];released=[];fit_records=[];group_rows=[];family_rows=[];recovery=[]
    common=dict(dataset=dataset,outer_fold=fold,role=role,model_seed=model_seed)
    if not structural and not force_diagnostic:
        for c in grid:
            rows.append(dict(**common,**c,bound_status='insufficient_design_support',
                recall_lcb=np.nan,workload_ucb=np.nan,custom_synthetic_f1=np.nan,
                macro_event_recall=np.nan,background_episodes_per_asset_day=np.nan,
                detected_delay_median_minutes=np.nan,performance_measured=False))
        return dict(surface=pd.DataFrame(rows),fits=0,fit_records=[],frames={},
                    allocations=pd.DataFrame(allocations),catalogues=_concat(list(catalogues.values())),
                    structural_support=False,draws=None)
    feature_sets={'clean':X.iloc[selection].reset_index(drop=True)}
    for seed in DESIGN['catalogue_seeds']:
        feature_sets[seed]=corrupted_features(segmented,block,observations[seed],available[seed],horizon,fcfg,list(X.columns))
    fits={};model_count=0
    # Shared immutable draws across all candidates in this block. Unsupported
    # structural fixtures still exercise replay but never become feasible.
    draws=resampling_draws(block,freq,dataset) if structural else None
    policy_groups={}
    for c in grid:
        key=tuple(c[k] for k in ['method','level','strategy','every','window'])
        policy_groups.setdefault(key,[]).append(c)
    for key,rule_candidates in policy_groups.items():
        c=rule_candidates[0];owner='cqr' if c['method']=='quantile_uncalibrated' else c['method']
        model_key=(owner,c['level'])
        if model_key not in fits:
            factory=OwnedInterval if owner=='persistence_split' else model_factory
            model=factory(owner,c['level'],X.iloc[train],y[train],X.iloc[cal],y[cal],
                meta.iloc[cal],horizon,seed=model_seed)
            fits[model_key]=model;model_count+=int(model.fitted_models)
            fit_records.append(dict(**common,method=owner,level=c['level'],fit_identity=model.fit_identity,
                                    identity=model.identity,fit_invocations=int(model.fitted_models)))
        model=fits[model_key]
        if c['method']=='quantile_uncalibrated':
            model=copy(model);model.method='quantile_uncalibrated';model.identity=dict(model.identity,method=model.method)
        raw={}
        for seed,xx in feature_sets.items():
            raw[seed]=dict(values=model.raw(xx),fit_identity=model.fit_identity,
                feature_hash=hashlib.sha256(pd.util.hash_pandas_object(xx,index=False).values.tobytes()).hexdigest())
        clean_replay=replay(model,feature_sets['clean'],block,y[selection],np.ones(len(block),bool),c,freq,raw_prediction=raw['clean'])
        corrupt_replays={seed:replay(model,feature_sets[seed],block,observations[seed],available[seed],c,freq,raw_prediction=raw[seed])
                         for seed in DESIGN['catalogue_seeds']}
        # Release dense policy streams after their rules are scored. Compact
        # event accounting still scales with candidates and is measured per run.
        for candidate in rule_candidates:
            clean=alert_on_stream(clean_replay,candidate,pd.DataFrame(),freq)
            bank_parts=[];per_events=[]
            for seed in DESIGN['catalogue_seeds']:
                corrupt=alert_on_stream(corrupt_replays[seed],candidate,catalogues[seed],freq)
                bank_parts.append(contributions(clean,corrupt,catalogues[seed],freq));per_events.append(corrupt['per_event'])
                tag=dict(**common,candidate_id=candidate['candidate_id'],catalogue_seed=seed)
                hashes.append(dict(**tag,clean_emitted=clean['emitted_hash'],clean_consumed=clean['consumed_hash'],
                    corrupted_emitted=corrupt['emitted_hash'],corrupted_consumed=corrupt['consumed_hash'],
                    catalogue_hash=signature(catalogues[seed].to_dict('records')),
                    feature_hash=corrupt_replays[seed]['causal_features_hash'],fit_identity=model.fit_identity))
                event_scores.append(_tag(corrupt['per_event'],**tag))
                recovered,_=group_recovery(corrupt['stream'],y[selection],catalogues[seed],freq)
                recovery.append(_tag(recovered,**tag))
                if save_streams:
                    streams.append(_tag(corrupt['stream'],stream_role='corrupted',**tag))
                    episodes.append(_tag(corrupt['episodes'],stream_role='corrupted',**tag))
                    updates.append(_tag(corrupt_replays[seed]['updates'],**tag))
                    released.append(_tag(corrupt_replays[seed]['released_scores'],**tag))
            bank=pool_bank(bank_parts)
            summary=summarize_bank(bank,per_events)
            groups,portfolio=group_workload(bank,freq);summary.update(portfolio)
            group_rows.append(_tag(groups,**common,candidate_id=candidate['candidate_id']))
            family_rows.append(_tag(family_attribution(_concat(per_events)),**common,candidate_id=candidate['candidate_id']))
            bounds=confidence_bounds(bank,list(catalogues.values()),block,freq,dataset,draws)
            rows.append(dict(**common,**candidate,**summary,**bounds,performance_measured=True,
                             estimator_class=model.identity['estimator_class'],fit_identity=model.fit_identity))
            if save_streams:
                tag=dict(**common,candidate_id=candidate['candidate_id'],catalogue_seed=-1)
                streams.append(_tag(clean['stream'],stream_role='clean',**tag));episodes.append(_tag(clean['episodes'],stream_role='clean',**tag))
                pooled.append(_tag(bank,**common,candidate_id=candidate['candidate_id']))
    return dict(surface=pd.DataFrame(rows),fits=model_count,fit_records=fit_records,
        frames=dict(streams=_concat(streams),hashes=pd.DataFrame(hashes),episodes=_concat(episodes),
                    event_scores=_concat(event_scores),contributions=_concat(pooled),updates=_concat(updates),released_scores=_concat(released),
                    group_workload=_concat(group_rows),family_attribution=_concat(family_rows),recovery=_concat(recovery)),
        allocations=pd.DataFrame(allocations),catalogues=_concat(list(catalogues.values())),
        structural_support=structural,draws=draws)


def baseline_selections(surface,grid):
    subsets={
        'baseline':[c for c in grid if c['method']=='quantile_uncalibrated' and c['rule_id']=='single_sample'],
        'conformal_only':[c for c in grid if c['method']=='cqr' and c['strategy']=='static' and c['rule_id']=='single_sample'],
        'temporal':[c for c in grid if c['method']=='cqr' and c['strategy']=='static' and c['rule_id']!='single_sample'],
        'full':grid}
    return {name:select_pipeline(surface[surface.candidate_id.isin([c['candidate_id'] for c in cs])],cs)
            for name,cs in subsets.items() if cs}


def evaluate_unit(dataset,outer_fold,model_seed,segmented,w,cfg,fold,*,smoke=False,
                  model_factory=OwnedInterval,force_diagnostic=False,save_streams=False,evaluate_outer=False,
                  candidate_grid=None):
    grid=candidate_grid if candidate_grid is not None else candidates(cfg,segmented.freq,smoke=smoke)
    roles=nested_roles(w['meta'],fold,w['meta'].attrs.get('split_scheme','chronological'))
    evaluated=[]
    for i in [0,1]:
        r=evaluate_block(dataset,outer_fold,f'inner{i}_selection',model_seed,segmented,w,cfg,
            roles[f'inner{i}_train'],roles[f'inner{i}_calibration'],roles[f'inner{i}_selection'],grid,
            model_factory=model_factory,force_diagnostic=force_diagnostic,save_streams=save_streams)
        r['surface']['inner_fold']=i;evaluated.append(r)
    surface=pd.concat([r['surface'] for r in evaluated],ignore_index=True)
    decision=select_pipeline(surface,grid);comparators=baseline_selections(surface,grid)
    inverse=select_pipeline(surface,grid,objective='inverse_recall_floor')
    payload=dict(dataset=dataset,outer_fold=outer_fold,model_seed=model_seed,evidence_status='SMOKE ONLY' if smoke else 'bounded_operational_pilot',
        decision=decision['decision'],pipeline=decision['pipeline'],operational_feasible=decision['operational_feasible'],
        diagnostic_fallback=decision['diagnostic_fallback'],fits=sum(r['fits'] for r in evaluated),
        fit_records=sum((r['fit_records'] for r in evaluated),[]),
        independent_operating_points={k:{x:v[x] for x in ['decision','pipeline','operational_feasible']} for k,v in comparators.items()},
        inverse_recall_floor={k:inverse[k] for k in ['decision','pipeline','operational_feasible']},
        design_hash=signature(DESIGN),source_hash=source_digest(),data_hash=w['data_hash'],candidate_grid=grid,
        actual_catalogue_seeds=DESIGN['catalogue_seeds'],global_study_ready=False,
        outcomes_hash=hashlib.sha256(np.asarray(w['y'],float).tobytes()).hexdigest(),
        inner_memberships={k:SI.membership_hash(w['meta'],v) for k,v in roles.items()},
        structural_support=[r['structural_support'] for r in evaluated])
    frames={'surface':surface,'rejections':decision['rejections'],'inverse_rejections':inverse['rejections'],
        'allocations':_concat([r['allocations'] for r in evaluated]),
        'catalogues':_concat([_tag(r['catalogues'],inner_fold=i) for i,r in enumerate(evaluated)])}
    for name in ['streams','hashes','episodes','event_scores','contributions','updates','released_scores','group_workload','family_attribution','recovery']:
        frames[name]=_concat([r['frames'].get(name,pd.DataFrame()) for r in evaluated])
    # Save actual paired cluster/block draws separately, including original row
    # ordering for moving blocks. No seed is treated as an independent asset.
    payload['resampling_draws']={str(i):{k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in r['draws'].items()}
        for i,r in enumerate(evaluated) if r['draws'] is not None}
    if evaluate_outer:
        outer,contrasts=selected_outer(dataset,outer_fold,model_seed,segmented,w,cfg,roles,grid,
            decision,dict(comparators,secondary_inverse=inverse),model_factory=model_factory,save_streams=save_streams)
        payload['fits']+=outer['fits'];payload['fit_records']+=outer['fit_records']
        payload['outer_refit_performed']=True
        payload['outer_comparisons']=contrasts
        frames['outer_metrics']=outer['surface'];frames['outer_hashes']=outer['frames']['hashes']
        for name,frame in outer['frames'].items():frames['outer_'+name]=frame
        frames['outer_catalogues']=outer['catalogues'];frames['outer_allocations']=outer['allocations']
        # An outer budget violation is an outcome, never a reason to reselect.
        payload['outer_budget_violations']=outer['surface'].loc[
            outer['surface'].background_episodes_per_asset_day>1.,'candidate_id'].tolist()
    else:payload['outer_refit_performed']=False
    return payload,frames


def selected_outer(dataset,fold,seed,segmented,w,cfg,roles,grid,decision,comparators,
                   *,model_factory=OwnedInterval,save_streams=False):
    """Final refit and controlled/independently selected operating comparisons.

    On abstention the fixed .95 CQR static single-sample reference is a diagnostic
    only. Controlled ablations share its nominal level and fitted quantiles.
    """
    chosen=decision['pipeline']
    reference=chosen or next(c for c in grid if c['method']=='cqr' and c['level']==.95
                            and c['strategy']=='static' and c['rule_id']=='single_sample')
    level=reference['level']
    temporal_rule=(reference['rule_id'] if reference['rule_id']!='single_sample' else
                   next(c['rule_id'] for c in grid if c['method']=='cqr' and c['level']==level
                        and c['strategy']=='static' and c['rule_id']!='single_sample'))
    controls={}
    for name,method,rule in [('baseline','quantile_uncalibrated','single_sample'),
        ('conformal_only','cqr','single_sample'),('temporal','cqr',temporal_rule)]:
        controls[name]=next(c for c in grid if c['method']==method and c['level']==level
                           and c['strategy']=='static' and c['rule_id']==rule)
    controls['full' if chosen else 'fixed_diagnostic']=reference
    comparisons=[];requested={c['candidate_id']:c for c in controls.values()}
    for name,c in controls.items():
        comparisons.append(dict(comparison='controlled_component',name=name,candidate_id=c['candidate_id'],
            shared_quantile_level=level,reference_operational_feasible=bool(chosen),
            status='controlled_component_diagnostic_not_independent_feasibility',
            rule_reference='selected temporal rule, or first declared temporal rule when reference is immediate'))
    for name,value in comparators.items():
        c=value['pipeline']
        comparisons.append(dict(comparison='secondary_inverse_recall_floor' if name=='secondary_inverse' else 'independently_inner_selected',name=name,
            candidate_id=c['candidate_id'] if c else None,operational_feasible=value['operational_feasible'],
            decision=value['decision'],workload_ceiling=None if name=='secondary_inverse' else 1.))
        if c:requested[c['candidate_id']]=c
    persistence=dict(reference,method='persistence_split',level=.95,strategy='static',every=0,window=None,
        rule_id='single_sample',k=1,m=1,window_minutes=float(segmented.freq/pd.Timedelta(minutes=1)),
        candidate_id='diagnostic_persistence_split_095_single_sample')
    requested[persistence['candidate_id']]=persistence
    comparisons.append(dict(comparison='fixed_diagnostic',name='persistence_split',candidate_id=persistence['candidate_id'],
                            operational_feasible=False,decision='predeclared_reference_not_selected'))
    result=evaluate_block(dataset,fold,'outer_test',seed,segmented,w,cfg,roles['final_fit'],
        roles['final_calibration'],roles['outer_test'],list(requested.values()),model_factory=model_factory,
        force_diagnostic=True,save_streams=save_streams)
    return result,comparisons


def checkpointed_unit(out,spec,compute,*,resume=False):
    """Validate completed data before computing anything, enabling zero-refit resume."""
    store=UnitCheckpoint(out,spec,resume=resume,string_columns=('group_id','row_id'));key=f"outer{spec['outer_fold']}_model{spec['model_seed']}"
    loaded=store.load(key)
    if loaded is not None:
        store.require_complete([key]);return loaded[0],loaded[1],dict(reused_units=1,new_fit_invocations=0)
    payload,frames=compute();store.save(key,payload,frames);store.require_complete([key])
    return payload,frames,dict(reused_units=0,new_fit_invocations=payload.get('total_fit_invocations',payload['fits']))


def validate_unit(payload,frames,*,expected_scope):
    if expected_scope=='full_study':
        raise ValueError('one bounded unit or SMOKE ONLY cannot establish full-study readiness')
    if expected_scope not in ('SMOKE ONLY','bounded_operational_pilot') or payload['evidence_status']!=expected_scope:
        raise ValueError('synthetic/reduced smoke cannot be a real-data result')
    grid=payload['candidate_grid'];surface=frames['surface']
    expected={(c['candidate_id'],i) for c in grid for i in [0,1]}
    actual=list(surface[['candidate_id','inner_fold']].itertuples(index=False,name=None))
    if set(actual)!=expected or len(actual)!=len(expected):raise ValueError('candidate/two-fold output matrix mismatch')
    recomputed=0
    for section,table in [('',surface),('outer_',frames.get('outer_metrics',pd.DataFrame()))]:
        hashes=frames.get(section+'hashes',pd.DataFrame());streams=frames.get(section+'streams',pd.DataFrame())
        expected_hashes={(r['candidate_id'],r['role'],seed) for r in table.to_dict('records')
            if r.get('performance_measured',False) for seed in DESIGN['catalogue_seeds']}
        keys=list(hashes[['candidate_id','role','catalogue_seed']].itertuples(index=False,name=None)) if len(hashes) else []
        if len(keys)!=len(expected_hashes) or set(keys)!=expected_hashes:raise ValueError('catalogue/hash matrix mismatch')
        for prefix in ['clean','corrupted']:
            if len(hashes) and not hashes[f'{prefix}_emitted'].eq(hashes[f'{prefix}_consumed']).all():
                raise ValueError('emitted/consumed stream mismatch')
        if len(streams):
            observed_keys=set()
            for (cid,role,seed,kind),part in streams.groupby(['candidate_id','role','catalogue_seed','stream_role'],sort=False):
                source=hashes[hashes.candidate_id.eq(cid)&hashes.role.eq(role)]
                if kind=='corrupted':source=source[source.catalogue_seed.eq(seed)]
                elif kind!='clean' or seed!=-1:raise ValueError('unexpected stream role')
                if source.empty or not source[kind+'_emitted'].eq(stream_hash(part)).all():
                    raise ValueError('persisted issued stream hash mismatch')
                observed_keys.add((cid,role,int(seed),kind));recomputed+=1
            want={(cid,role,seed,'corrupted') for cid,role,seed in expected_hashes}
            want|={(cid,role,-1,'clean') for cid,role,seed in expected_hashes}
            if observed_keys!=want:raise ValueError('persisted stream matrix mismatch')
        elif expected_scope=='SMOKE ONLY' and expected_hashes:raise ValueError('smoke must preserve issued streams')
    if payload['decision']=='no_feasible_configuration' and payload['pipeline'] is not None:
        raise ValueError('abstention contains a hidden selected pipeline')
    return dict(output_valid=True,candidate_fold_cells=len(actual),stream_hash_pairs=len(frames['hashes']),
                outer_stream_hash_pairs=len(frames.get('outer_hashes',[])),persisted_streams_recomputed=recomputed,
                scientific_readiness=False,scope=payload['evidence_status'])
