"""Executable C freeze/readiness/run/validate/resume; real execution is manifest gated."""
import os
for _key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_key]='1'
import argparse,copy,gc,json
from pathlib import Path
import numpy as np
import pandas as pd
from .intervals005_common import (ROOT,REPO,Stages,Operations,PhaseMeter,read,atomic,csv,tree,
    signature,digest,source_digest,packages,resources,dump_owner,load_owner,now)
from .context005_spec import VERSION,POLICIES,table,controls,rules,context_positions
from .context005_data import load_real,synthetic
from .context005_features import bounded_frame,inject,causal_features,feature_hash
from .context005_owner import ContextOwner,prediction_cache
from .context005_metrics import conditional_summary,original_contributions,interval_diagnostics,inference
from .intervals005_owners import fit_owner,conformalize_owner
from .operational004_stream import replay,stream_hash
from .operational004_metrics import alert_on_stream
from .operational004_design import STRATA,segments

def load_data(manifest):
    return synthetic(manifest['dataset']) if manifest['synthetic'] else load_real(manifest['dataset'],manifest['outer_fold'])

def validate_manifest(m):
    if m['version']!=VERSION or m['dataset'] not in POLICIES:raise ValueError('unknown C manifest')
    p=POLICIES[m['dataset']]
    if m['horizon']!=p['horizon'] or m['outer_fold'] not in [0,1,2] or m['model_seed'] not in range(42,47):raise ValueError('scope outside declared C endpoint')
    if m['controls']!=controls(m['dataset']) or m['rules']!=rules(m['dataset']):raise ValueError('C controls/rules differ from amendment005')
    if m.get('selection')!='none' or m.get('endpoint')!='C_effective_fault_conditional_context':raise ValueError('C must not perform A selection')
    if m['synthetic'] and m['model_seed']!=42:raise ValueError('synthetic fixture seed fixed')
    if not m['synthetic'] and m.get('tiny_estimator',False):raise ValueError('synthetic estimator cannot enter real scope')

def data_identity(d):
    return dict(features=feature_hash(d['X']),outcomes=signature(d['y'].tolist()),
        role_rows={k:signature(d['meta'].iloc[v].row_id.tolist()) for k,v in d['roles'].items()},
        context_hash=signature(d['contexts'].to_dict('records')),schedule_hash=signature(d['schedules'].to_dict('records')),
        cache_sha256=d['cache_sha256'],columns=list(d['X'].columns),frequency=str(d['frequency']),fcfg=d['fcfg'])

def freeze(manifest_path,design):
    m=read(manifest_path);validate_manifest(m);dest=Path(design)
    if dest.exists():raise ValueError('preserve frozen design')
    with Operations(forbid=True),PhaseMeter() as meter:
        d=load_data(m);ident=data_identity(d);test=d['meta'].iloc[d['roles']['outer_test']].reset_index(drop=True)
        for ctx in d['contexts'].to_dict('records'):
            ix=context_positions(test,ctx);part=test.iloc[ix]
            p=POLICIES[m['dataset']]
            if not pd.to_datetime(part.target_time).diff().dropna().eq(d['frequency']).all():raise ValueError('context gap')
            if int(ctx['onset_offset'])<p['warmup'] or int(ctx['onset_offset'])+p['duration']+p['followup']>len(part):raise ValueError('context warmup/envelope/followup')
            if part.iloc[int(ctx['onset_offset'])].row_id!=ctx['onset_row_id']:raise ValueError('fixed onset moved')
            sch=d['schedules'][d['schedules'].context_id==ctx['context_id']]
            if len(sch)!=42 or set(zip(sch.family,sch.severity,sch.replicate))!={(f,s,r) for f,s in STRATA for r in [42,43]}:raise ValueError('schedule/stratum/slot completeness')
        if m['expected_contexts']!=len(d['contexts']) or m['expected_schedules']!=len(d['schedules']):raise ValueError('execution manifest context/schedule scope mismatch')
        dest.mkdir(parents=True)
        csv(dest/'contexts.csv',d['contexts']);csv(dest/'schedules.csv.gz',d['schedules'])
        csv(dest/'roles.csv.gz',pd.concat([d['meta'].iloc[ix][['row_id','group_id','origin_time','target_time']].assign(role=r) for r,ix in d['roles'].items()],ignore_index=True))
        for r,ix in d['roles'].items():
            if len(ix)<400:raise ValueError('declared support minimum')
        protocol=dict(version=VERSION,manifest=m,manifest_path=str(Path(manifest_path).resolve()),manifest_sha256=digest(manifest_path),source_hash=source_digest(),
            packages=packages(),data_identity=ident,source_inputs=d['source_inputs'],design_hashes=tree(dest),
            rows={k:len(v) for k,v in d['roles'].items()},expected_operations=dict(cqr_wrapper_fit=1,quantile_estimator_fit=3,calibrator_conformalize=2,persistence_radius=1),
            owner_reuse='new C owner required unless exact features/roles/calibration/parameters/source contract proven',
            static_convention='MAPIE1.4.1 native asymmetric tail correction; emitted pair ordered',
            rolling_convention='max-score ceil((n+1)*.95); observe/compare/release before scheduled origin update',
            resource_policy=dict(threads=1,device='cpu',launch_ram_reference_nonblocking=True,launch_ram_reference_bytes=3*2**30,disk_floor_bytes=8*2**30,batch=256),
            frozen_utc=now(),full_study_ready=False,models_fitted=0)
        atomic(dest/'frozen_protocol.json',protocol)
    return dict(frozen=True,rows=protocol['rows'],contexts=len(d['contexts']),schedules=len(d['schedules']),models_fitted=0,resources=meter.result)

def check_protocol(design):
    p=read(Path(design)/'frozen_protocol.json');validate_manifest(p['manifest'])
    if p['source_hash']!=source_digest() or p['packages']!=packages():raise ValueError('source/package protocol mismatch')
    if digest(p['manifest_path'])!=p['manifest_sha256']:raise ValueError('execution manifest changed; freeze a new authorized version')
    for f,h in p['source_inputs'].items():
        if digest(REPO/f)!=h:raise ValueError('published input changed: '+f)
    for f,h in p['design_hashes'].items():
        if digest(Path(design)/f)!=h:raise ValueError('frozen design corruption: '+f)
    return p

def readiness(design,receipt):
    p=check_protocol(design)
    with Operations(forbid=True):
        d=load_data(p['manifest'])
        if signature(data_identity(d))!=signature(p['data_identity']):raise ValueError('fresh input/role identity mismatch')
        r=dict(passed=True,implementation_ready=True,execution_authorized=bool(p['manifest']['execution_authorized']),
            protocol_sha256=digest(Path(design)/'frozen_protocol.json'),source_hash=p['source_hash'],models_fitted=0,
            required_new_quantile_estimators=3,required_new_cqr_wrappers=1,required_conformalize_calls=2,
            resource_snapshot=resources(ROOT),scope=p['manifest'],utc=now())
    if Path(receipt).exists():raise ValueError('preserve readiness receipt')
    atomic(receipt,r);return r

def models_from_stage(stages,d,manifest):
    rows=d['roles'];X=d['X'];y=d['y'];seed=manifest['model_seed']
    fit=fit_owner(stages,'owner_fit_cqr','cqr',.95,seed,X.iloc[rows['final_fit']],y[rows['final_fit']],synthetic=manifest['synthetic'])
    calibrated=conformalize_owner(stages,'owner_cal_cqr',fit,X.iloc[rows['final_calibration']],y[rows['final_calibration']],synthetic=manifest['synthetic'])
    def persist(out):
        owner=load_owner(calibrated/'owner.pkl');identity=dict(owner_sha256=digest(calibrated/'owner.pkl'),
            fit_sha256=digest(fit/'owner.pkl'),source_hash=source_digest(),model_seed=seed,dataset=manifest['dataset'],roles=data_identity(d)['role_rows'])
        wrappers={name:ContextOwner(owner,method,X.iloc[rows['final_calibration']],y[rows['final_calibration']],d['meta'].iloc[rows['final_calibration']],identity)
            for name,method in [('cqr','cqr'),('quantile_uncalibrated','quantile_uncalibrated'),('persistence_split','persistence_split')]}
        # Pickle memoization preserves the shared quantile estimator object.
        dump_owner(out/'controls.pkl',wrappers);atomic(out/'identity.json',dict(identity,columns=list(X.columns),persistence_radius=wrappers['persistence_split'].radius,
            quantile_shared=True,new_learned_fits=0,persistence_calibrations=1))
        return dict(owner_sha256=identity['owner_sha256'])
    path=stages.run('controls',persist);result=load_owner(path/'controls.pkl')
    if result['cqr'].owner is not result['quantile_uncalibrated'].owner:raise ValueError('quantile ownership not shared')
    return result

def output_variant(out,models,X,meta,truth,observed,available,m,variant_id):
    pdmeta=meta.reset_index(drop=True)
    csv(out/'features.csv.gz',pd.concat([pdmeta[['row_id']],X],axis=1))
    csv(out/'observations.csv.gz',pdmeta.assign(truth=truth,observed=observed,available=available))
    diagnostics=[]
    shared_raw=models['cqr'].raw(X)
    for control in m['controls']:
        model=models[control['method']];cid=control['control_id']
        cache=(dict(feature_hash=feature_hash(X),fit_identity=model.fit_identity,variant_identity=variant_id,values=shared_raw)
               if control['method']!='persistence_split' else prediction_cache(model,X,variant_id))
        # Both cache identities are enforced; clean predictions cannot satisfy a changed variant.
        if cache['variant_identity']!=variant_id:raise ValueError('variant prediction cache identity mismatch')
        r=replay(model,X,pdmeta,observed,available,control,POLICIES[m['dataset']]['frequency'],raw_prediction=cache)
        stream=r['stream'];stream['truth']=truth
        csv(out/(cid+'_issued.csv.gz'),stream)
        csv(out/(cid+'_released.csv.gz'),r['released_scores'].reindex(columns=['row_id','group_id','segment_id','target_time','released_at_origin','score','kind','prior_interval_compared']))
        csv(out/(cid+'_updates.csv.gz'),r['updates'].reindex(columns=['group_id','segment_id','origin_time','pool_n','latest_score_target','status','correction_lower','correction_upper']))
        for rule in m['rules']:
            scored=alert_on_stream(r,dict(control,**rule),pd.DataFrame(),POLICIES[m['dataset']]['frequency'])
            cols=['row_id','alert_numerical_only','alert_availability_only','alert_combined']
            csv(out/(cid+'_'+rule['rule_id']+'_alerts.csv.gz'),scored['stream'][cols])
            csv(out/(cid+'_'+rule['rule_id']+'_episodes.csv.gz'),scored['episodes'])
            if scored['consumed_hash']!=r['emitted_hash']:raise ValueError('alert consumption changed issued stream')
        diagnostics.extend(dict(control_id=cid,target=target,**value) for target,value in interval_diagnostics(stream,truth).items())
    csv(out/'interval_diagnostics.csv',pd.DataFrame(diagnostics))
    atomic(out/'identity.json',dict(variant_id=variant_id,feature_hash=feature_hash(X),row_hash=signature(meta.row_id.tolist()),
        observation_hash=signature(np.nan_to_num(observed,nan=-1.23456789e307).tolist()),availability_hash=signature(available.tolist()),
        shared_predictor=models['cqr'].identity['owner_sha256'],source_hash=source_digest()))

def read_event_metrics(path,event,ctx,m,alias):
    rows=[];p=POLICIES[m['dataset']];freq=pd.Timedelta(p['frequency']);onset=pd.Timestamp(event['onset'])
    # Preserve original last-observation end plus tolerance (no edge extension).
    end=onset+(p['duration']-1+p['tolerance'])*freq;tau=float((end-onset)/pd.Timedelta('1min'))
    for control in m['controls']:
        for rule in m['rules']:
            eps=table(path/(control['control_id']+'_'+rule['rule_id']+'_episodes.csv.gz'))
            for channel in ['numerical_only','availability_only','combined']:
                options=eps[(eps.channel==channel)&(eps.group_id==str(ctx['group_id']))]
                options=options[(pd.to_datetime(options.onset)>=onset)&(pd.to_datetime(options.onset)<=end)].sort_values('onset')
                detected=bool(event['effective']) and bool(len(options));delay=float((pd.Timestamp(options.iloc[0].onset)-onset)/pd.Timedelta('1min')) if detected else np.nan
                rows.append(dict(dataset=m['dataset'],outer_fold=m['outer_fold'],model_seed=m['model_seed'],context_id=ctx['context_id'],
                    original_segment_id=ctx['segment_id'],group_id=str(ctx['group_id']),control_id=control['control_id'],rule_id=rule['rule_id'],channel=channel,
                    family=event['family'],severity=event['severity'],replicate=event['replicate'],slot_sign=event['sign'],mask_seed=str(event['mask_seed']),
                    effective=bool(event['effective']),null=bool(event['null']),alias=alias,eligible=end<=pd.Timestamp(ctx['end_time']),
                    detected=detected,delay_minutes=delay,restricted_delay_minutes=delay if detected else tau,censored=not detected,
                    restriction_minutes=tau,endpoint_end=str(end),matched_episode_id=str(options.iloc[0].episode_id) if detected else ''))
    return rows

def execute(design,out,ready,*,resume=False):
    p=check_protocol(design);m=p['manifest'];rr=read(ready)
    if rr['protocol_sha256']!=digest(Path(design)/'frozen_protocol.json') or not rr['passed']:raise ValueError('readiness is not bound to design')
    if not m['execution_authorized']:raise PermissionError('real execution proposal is not an execution authorization')
    if not m['synthetic'] and m.get('authorization_kind')!='explicit_real_C_run':raise PermissionError('real C fitting/replay not authorized by implementation package')
    resources(ROOT);stages=Stages(out,dict(protocol_sha256=digest(Path(design)/'frozen_protocol.json')),resume=resume)
    if (Path(out)/'COMPLETE.json').exists():return completed_resume(design,out,ready,None)
    d=load_data(m)
    if signature(data_identity(d))!=signature(p['data_identity']):raise ValueError('execution data changed')
    models=models_from_stage(stages,d,m);rows=d['roles']['outer_test'];meta=d['meta'].iloc[rows].reset_index(drop=True)
    # Full-stream clean trajectories include unused challenge tails and never
    # appear in variant denominators. Source segments are evaluated independently.
    workload=[]
    for number,(group,sid,ix) in enumerate(segments(meta,d['frequency'])):
        local=meta.iloc[ix].reset_index(drop=True);base,season=bounded_frame(d['series'],local,d['fcfg'],d['horizon'])
        frame,truth,obs,avail=inject(base,local);X=causal_features(frame,local,d['horizon'],d['frequency'],season,d['fcfg'],d['X'].columns)
        path=stages.run(f'fullstream_{number}',lambda dest:output_variant(dest,models,X,local,truth,obs,avail,m,'fullstream:'+sid))
        for control in m['controls']:
            for rule in m['rules']:
                prefix=control['control_id']+'_'+rule['rule_id'];eps=table(path/(prefix+'_episodes.csv.gz'));flags=table(path/(prefix+'_alerts.csv.gz'))
                for channel in ['numerical_only','availability_only','combined']:
                    n=len(local);count=int((eps.channel==channel).sum());duration=n*float(d['frequency']/pd.Timedelta('1D'))
                    workload.append(dict(dataset=m['dataset'],outer_fold=m['outer_fold'],model_seed=m['model_seed'],control_id=control['control_id'],rule_id=rule['rule_id'],channel=channel,
                        group_id=group,original_segment_id=sid,eligible_rows=n,asset_days=duration,episodes=count,episodes_per_asset_day=count/duration,
                        alert_rows=int(flags['alert_'+channel].sum()),time_in_alert_days=float(flags['alert_'+channel].sum())*float(d['frequency']/pd.Timedelta('1D'))))
    all_events=[];variants=[]
    for ctx in d['contexts'].to_dict('records'):
        ix=context_positions(meta,ctx);local=meta.iloc[ix].reset_index(drop=True);ctx=dict(ctx,end_time=str(local.target_time.max()))
        base,season=bounded_frame(d['series'],local,d['fcfg'],d['horizon']);sch=d['schedules'][d['schedules'].context_id==ctx['context_id']]
        seen={}
        for ordinal,event in enumerate([None]+sch.to_dict('records')):
            frame,truth,obs,avail=inject(base,local,event);X=causal_features(frame,local,d['horizon'],d['frequency'],season,d['fcfg'],d['X'].columns)
            realhash=signature(dict(features=feature_hash(X),observed=np.nan_to_num(obs,nan=-1.23456789e307).tolist(),available=avail.tolist()))
            key='context_'+ctx['context_id']+'_v'+str(ordinal);alias=realhash in seen
            if alias:
                canonical=seen[realhash]
                aliaspath=stages.run(key,lambda dest:atomic(dest/'alias.json',dict(canonical_stage=canonical,realization_hash=realhash)))
                path=stages.get(canonical)
            else:
                canonical=key;seen[realhash]=canonical
                path=stages.run(key,lambda dest:output_variant(dest,models,X,local,truth,obs,avail,m,realhash))
            variants.append(dict(context_id=ctx['context_id'],ordinal=ordinal,stage=key,canonical_stage=canonical,alias=alias,realization_hash=realhash,
                family=event['family'] if event else 'identity',severity=event['severity'] if event else 0,replicate=event['replicate'] if event else 0,
                effective=bool(event['effective']) if event else False,null=bool(event['null']) if event else True))
            if event:all_events.extend(read_event_metrics(path,event,ctx,m,alias))
        print('C CONTEXT COMPLETE',m['dataset'],ctx['context_id'],len(seen),'unique realizations',flush=True)
    def finish(dest):
        event_frame=pd.DataFrame(all_events);strata,macros=conditional_summary(event_frame);contrib=original_contributions(event_frame)
        csv(dest/'events.csv.gz',event_frame);csv(dest/'variants.csv',pd.DataFrame(variants));csv(dest/'strata.csv',strata);csv(dest/'conditional_macro.csv',macros)
        csv(dest/'original_context_contributions.csv.gz',contrib);csv(dest/'fullstream_workload.csv',pd.DataFrame(workload))
        bounds,draws=inference(contrib,d['contexts'],m['dataset']);csv(dest/'inference.csv',bounds);atomic(dest/'inference.json',draws)
        return dict(contexts=len(d['contexts']),scheduled_fault_slots=len(d['schedules']),zero_controls=len(d['contexts']),semantic_controls=4,rules=5,
            endpoint='C_effective_fault_conditional_context',selection='none',real_study_cells_added=0 if m['synthetic'] else None)
    stages.run('tables',finish)
    atomic(Path(out)/'COMPLETE.json',dict(protocol_sha256=digest(Path(design)/'frozen_protocol.json'),files=tree(Path(out)),actual_exit_status=0,utc=now()))
    return dict(completed=True,synthetic=m['synthetic'],contexts=len(d['contexts']),schedules=len(d['schedules']))

def verify_complete(design,out):
    p=check_protocol(design);root=Path(out);c=read(root/'COMPLETE.json');f=tree(root);f.pop('COMPLETE.json')
    if c['protocol_sha256']!=digest(Path(design)/'frozen_protocol.json') or c['files']!=f:raise ValueError('corrupt completed context checkpoint')
    return p

def completed_resume(design,out,ready,receipt):
    before=tree(Path(out))
    with Operations(forbid=True):
        p=verify_complete(design,out);r=read(ready)
        if r['protocol_sha256']!=digest(Path(design)/'frozen_protocol.json'):raise ValueError('resume readiness mismatch')
        if tree(Path(out))!=before:raise ValueError('completed resume mutated science')
        result=dict(passed=True,completed=True,models_fitted=0,calibrators_fitted=0,replay_updates=0,scientific_artifacts_unchanged=True,protocol_sha256=r['protocol_sha256'])
    if receipt:
        if Path(receipt).exists():raise ValueError('preserve resume receipt')
        atomic(receipt,result)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','readiness','run','validate','resume'])
    parser.add_argument('--manifest');parser.add_argument('--design',required=True);parser.add_argument('--out');parser.add_argument('--readiness');parser.add_argument('--receipt');parser.add_argument('--resume-incomplete',action='store_true')
    a=parser.parse_args()
    if a.action=='freeze':result=freeze(a.manifest,a.design)
    elif a.action=='readiness':result=readiness(a.design,a.receipt)
    elif a.action=='run':result=execute(a.design,a.out,a.readiness,resume=a.resume_incomplete)
    elif a.action=='resume':result=completed_resume(a.design,a.out,a.readiness,a.receipt)
    else:
        from .context005_validate import validate
        result=validate(a.design,a.out,a.receipt)
    print(json.dumps(result,default=str,indent=2),flush=True)

if __name__=='__main__':main()
