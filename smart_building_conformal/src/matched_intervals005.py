"""Versioned matched interval-method freeze/readiness/run/validate/resume CLI."""
from __future__ import annotations
import os
for _name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_name]='1'
import argparse
import gc
from pathlib import Path
import numpy as np
import pandas as pd
from .intervals005_common import *
from .intervals005_data import MATRIX,JOINT,JOINT_SUPPORT,LEDGER,historical_references,load_data,role_frame,historical_predictions,joint_join,expected_joint
from .intervals005_owners import method_spec,fit_owner,conformalize_owner,raw_predictions
from .intervals005_stream import emit,save_stream,interval_metrics
from .conformal_dscp import fit_dscp
from .pilot_conformal import calibrate_absolute


def config_scope(auth,matrix):
    c=auth['scope']
    if not auth.get('real_fitting_authorized') or c!={'dataset':'bdg2','outer_fold':2,'model_seed':42,'horizons':[1,3,6],'levels':LEVELS,'methods':METHODS}:raise ValueError('outside bounded authorization')
    f=frame(matrix);f=f[(f.dataset==c['dataset'])&(f.outer_fold==c['outer_fold'])&(f.model_seed==c['model_seed'])&f.horizon.isin(c['horizons'])]
    from .unit_checkpoint import require_cells
    require_cells(f,['horizon','level','method'],[(h,l,m) for h in c['horizons'] for l in LEVELS for m in METHODS])
    return c,f


def freeze(matrix,authorization,design,synthetic_receipt):
    auth=read(authorization);c,cells=config_scope(auth,matrix)
    synthetic=read(synthetic_receipt)
    if not synthetic['passed'] or synthetic['enbpi_base_fits_per_owner']!=11:raise ValueError('synthetic operation contract not verified')
    out=Path(design)
    if out.exists():raise ValueError('preserve existing design; choose an unused version')
    out.mkdir(parents=True)
    with Operations(forbid=True),PhaseMeter() as meter:
        refs=historical_references(c['dataset'],c['outer_fold'],c['model_seed'],c['horizons'])
        roles_all={};support={};prepared=None
        for h in c['horizons']:
            data,roles,prepared=load_data(refs[str(h)],prepared)
            roles_all[h]={r:role_frame(data,roles[r]) for r in ('fit','calibration','test')}
            support[str(h)]=dict(data_hash=data['data_hash'],roles=data['old_protocol']['support']['roles'],features=data['feature_names'],available_by_role={r:int(data['available'][v].sum()) for r,v in roles.items()})
            del data;gc.collect()
        joint={}
        for role in ('fit','calibration','test'):
            pieces=joint_join({h:roles_all[h][role] for h in c['horizons']},c['horizons'],expected=expected_joint(c['dataset'],c['outer_fold'],role))
            joint[role]=len(pieces[c['horizons'][0]])
            csv(out/f'joint_{role}.csv.gz',pd.concat([f.assign(horizon=h,role=role) for h,f in pieces.items()],ignore_index=True))
        if joint!={'fit':51534,'calibration':17270,'test':34590}:raise ValueError('published joint support changed')
        csv(out/'native_membership.csv.gz',pd.concat([f.assign(horizon=h,role=r) for h,rr in roles_all.items() for r,f in rr.items()],ignore_index=True))
    csv(out/'scope.csv',cells)
    inputs=[Path(matrix).resolve(),Path(authorization).resolve(),Path(synthetic_receipt).resolve(),JOINT,JOINT_SUPPORT,LEDGER]
    spec=method_spec(c['model_seed']);atomic(out/'method_specification.json',spec)
    protocol=dict(version='matched_intervals005_bdg2_f2_s42_v1',scope=c,authorization=auth,entry_commit=ENTRY,historical_source_hash=OLD_SOURCE,source_hash=source_digest(),packages=packages(),references=refs,support=support,joint_support=joint,method_specification=spec,inputs={str(p.relative_to(REPO)):digest(p) for p in inputs},design_hashes=tree(out),expected_operations=dict(cqr_wrapper_fit=6,quantile_estimator_fit=18,enbpi_wrapper_fit=3,xgboost_estimator_fit=33,random_forest_estimator_fit=0,dscp_calibrator_fit=1,kmeans_candidate_fit=5,calibrator_conformalize=18),expected_cells=dict(interval_method=30,seasonal_point=3,seasonal_interval=6,alert_streams=30),resource_policy=dict(device='cpu',threads=1,n_jobs=1,batch_size=256,launch_ram_reference_bytes=3*2**30,nonblocking_launch_ram=True,epoch_floor_bytes=256*2**20,disk_floor_bytes=8*2**30),tolerances=dict(prediction_atol=1e-7,prediction_rtol=1e-7,metric_atol=1e-10,metric_rtol=1e-12),frozen_utc=now(),freeze_resources=meter.result,models_fitted=0,full_study_ready=False)
    atomic(out/'frozen_protocol.json',protocol)
    return dict(frozen=True,models_fitted=0,joint_support=joint,source_hash=protocol['source_hash'])


def check_protocol(path,audit_manifest=None):
    path=Path(path);p=read(path)
    if packages()!=p['packages']:raise ValueError('package identity mismatch')
    if audit_manifest is None:
        if source_digest()!=p['source_hash']:raise ValueError('source identity mismatch')
    else:
        # Explicit read-only compatibility for a completed historical pilot.
        # Pin both source trees; never relabel the evaluated source as current.
        import zipfile
        audit=read(audit_manifest)
        if audit['version']!='cqr_native_validation_erratum_v2' or not audit['completed_readonly_only']:raise ValueError('unsupported audit manifest')
        if audit['protocol_sha256']!=digest(path) or audit['evaluated_source_hash']!=p['source_hash'] or audit['validator_source_hash']!=source_digest():raise ValueError('audit source/protocol identity mismatch')
        archive=REPO/audit['evaluated_archive']
        if digest(archive)!=audit['evaluated_archive_sha256']:raise ValueError('evaluated archive changed')
        with zipfile.ZipFile(archive) as z:
            original={name.removeprefix('src/'):hashlib.sha256(z.read(name)).hexdigest() for name in z.namelist() if name.startswith('src/') and name.endswith('.py')}
        original_digest=hashlib.sha256('\n'.join(f'{name}:{original[name]}' for name in sorted(original)).encode()).hexdigest()
        if original_digest!=p['source_hash']:raise ValueError('archived evaluated source mismatch')
        current={file.relative_to(ROOT/'src').as_posix():digest(file) for file in sorted((ROOT/'src').rglob('*.py'))}
        if current!=audit['validator_files'] or set(current)!=set(original):raise ValueError('audit file identity mismatch')
        changed={name for name in current if current[name]!=original[name]}
        if changed!={'matched_intervals005.py','intervals005_validate.py','intervals005_owners.py'}:raise ValueError('unexpected source change for native validation erratum')
    for name,value in p['inputs'].items():
        if digest(REPO/name)!=value:raise ValueError('frozen input changed: '+name)
    for name,value in p['design_hashes'].items():
        if digest(path.parent/name)!=value:raise ValueError('frozen membership/spec changed')
    actual=method_spec(p['scope']['model_seed'])
    if audit_manifest is None:
        if signature(actual)!=signature(p['method_specification']):raise ValueError('factory specification drift')
    else:
        if signature(actual)!=signature(audit['resolved_method_specification']):raise ValueError('resolved audit specification drift')
        import copy
        old=copy.deepcopy(p['method_specification']);new=copy.deepcopy(actual)
        for field in ('score','native_quantile','native_predict_parameters'):
            old['cqr'].pop(field,None);new['cqr'].pop(field,None)
        if signature(old)!=signature(new):raise ValueError('audit changed a frozen factory or policy')
    return p


def readiness(path,receipt):
    p=check_protocol(path);prepared=None
    with Operations(forbid=True),PhaseMeter() as meter:
        for h,reference in p['references'].items():
            data,roles,prepared=load_data(reference,prepared)
            if data['data_hash']!=p['support'][h]['data_hash']:raise ValueError('fresh support changed')
            if min(len(roles['fit']),len(roles['calibration']))<400:raise ValueError('production support minimum')
            if not np.isfinite(data['seasonal'][np.r_[roles['calibration'],roles['test']]]).all():raise ValueError('seasonal support unavailable')
            del data;gc.collect()
    r=dict(passed=True,ready=True,source_hash=source_digest(),protocol_hash=digest(path),models_fitted=0,calibrators_fitted=0,resources=resources(ROOT),preparation_resources=meter.result,utc=now())
    if Path(receipt).exists():raise ValueError('readiness receipt already exists')
    atomic(receipt,r);return r


def raw_stage(stages,key,owner_path,kind,level,data,roles):
    def work(out):
        owner=load_owner(owner_path/'owner.pkl')
        for role in ('calibration','test'):
            rows=roles[role];pred=raw_predictions(owner,kind,data['X'].iloc[rows].to_numpy(),[level] if kind=='cqr' else LEVELS)
            meta=role_frame(data,rows);csv(out/(role+'_metadata.csv.gz'),meta)
            for l,f in pred.items():csv(out/f'{role}_{int(l*100)}.csv.gz',f)
        return dict(owner_sha256=digest(owner_path/'owner.pkl'),kind=kind,levels=[level] if kind=='cqr' else LEVELS)
    return stages.run(key,work)


def finish_tables(stages,scope):
    def work(out):
        metrics=[];groups=[];workloads=[];seasons=[];season_points=[]
        for h in scope['horizons']:
            joint=frame(stages.get('dscp_joint')/f'test_h{h}.csv.gz');common=set(joint.row_id)
            for l in LEVELS:
                for method in METHODS:
                    path=stages.get(f'stream_h{h}_l{int(l*100)}_{method}');f=frame(path/'issued.csv.gz')
                    tag=dict(dataset=scope['dataset'],outer_fold=scope['outer_fold'],model_seed=scope['model_seed'],horizon=h,level=l,method=method)
                    for support,part in [('native',f),('common',f[f.row_id.isin(common)])]:
                        if support=='common' and len(part)!=len(common):raise ValueError('common support missing rows')
                        metrics.append(dict(tag,support=support,**interval_metrics(part,l)))
                        for group,sub in part.groupby('group_id'):groups.append(dict(tag,support=support,group_id=group,**interval_metrics(sub,l)))
                    workloads.append(frame(path/'background_workload.csv'))
                seasonal=frame(stages.get(f'seasonal_h{h}')/f'interval_{int(l*100)}.csv.gz')
                seasons.append(dict(dataset=scope['dataset'],outer_fold=scope['outer_fold'],model_seed=scope['model_seed'],horizon=h,level=l,method='seasonal_naive',**interval_metrics(seasonal,l)))
            season_points.append(read(stages.get(f'seasonal_h{h}')/'point.json'))
        f=pd.DataFrame(metrics);csv(out/'native_support_metrics.csv',f[f.support=='native']);csv(out/'common_support_metrics.csv',f[f.support=='common'])
        csv(out/'per_building_metrics.csv',pd.DataFrame(groups));csv(out/'background_workload.csv',pd.concat(workloads,ignore_index=True))
        csv(out/'seasonal_interval_metrics.csv',pd.DataFrame(seasons));csv(out/'seasonal_point_metrics.csv',pd.DataFrame(season_points))
        operations=[json.loads(s) for s in (stages.root/'operations.jsonl').read_text().splitlines()]
        csv(out/'operations.csv',pd.DataFrame(operations));counts={k:sum(r.get('kind')==k and r['event']=='returned' for r in operations) for k in set(r.get('kind') for r in operations) if k}
        costs=[dict(stage=p.name,**read(p/'stage.json')['resources']) for p in (stages.root/'stages').iterdir() if (p/'stage.json').exists()]
        csv(out/'stage_costs.csv',pd.DataFrame(costs));atomic(out/'operation_counts.json',counts)
        return dict(method_cells=30,seasonal_point_cells=3,seasonal_interval_cells=6,alert_streams=30,operation_counts=counts)
    return stages.run('tables',work)


def execute(path,ready,out,*,resume=False,forbid=False,receipt=None,audit_manifest=None):
    if audit_manifest is not None and not (resume and forbid and (Path(out)/'COMPLETE.json').exists()):raise ValueError('audit manifest permits completed forbidden-fit resume only')
    p=check_protocol(path,audit_manifest);r=read(ready)
    if not r['ready'] or r['protocol_hash']!=digest(path) or r['source_hash']!=p['source_hash']:raise ValueError('fresh readiness mismatch')
    stages=Stages(out,dict(protocol_hash=digest(path),source_hash=p['source_hash']),resume=resume)
    if (stages.root/'COMPLETE.json').exists():
        before=tree(stages.root);marker=read(stages.root/'COMPLETE.json')
        current=dict(before);current.pop('COMPLETE.json')
        if current!=marker['files']:raise ValueError('completed evidence corruption')
        with Operations(forbid=True):
            for key in marker['stage_keys']:stages.get(key)
        if tree(stages.root)!=before:raise ValueError('completed resume changed scientific files')
        result=dict(status='complete',models_fitted=0,calibrators_fitted=0,all_run_files_unchanged=True,stages_verified=len(marker['stage_keys']),utc=now())
        if audit_manifest:result.update(evaluated_source_hash=p['source_hash'],validator_source_hash=source_digest(),audit_manifest_sha256=digest(audit_manifest))
        if receipt:atomic(receipt,result)
        return result
    if forbid:raise ValueError('forbidden-fit resume requires complete scientific output')
    resources(stages.root);scope=p['scope'];prepared=None;historical={}
    for h in scope['horizons']:
        print(f'PREPARE horizon {h}',flush=True)
        with PhaseMeter() as preparation:data,roles,prepared=load_data(p['references'][str(h)],prepared)
        prep_key=f'preparation_h{h}'
        stages.run(prep_key,lambda dest:dict(resources=preparation.result,native_rows={k:len(v) for k,v in roles.items()}))
        def history_work(dest):
            with Operations(forbid=True):records,checks=historical_predictions(p['references'][str(h)],data,roles)
            for role,f in records.items():csv(dest/(role+'.csv.gz'),f)
            csv(dest/'reload_checks.csv',pd.DataFrame(checks))
            return dict(reference=p['references'][str(h)],new_predictor_fits=0)
        history=stages.run(f'historical_h{h}',history_work);historical[h]=history
        def seasonal_work(dest):
            ca=roles['calibration'];te=roles['test'];cal=role_frame(data,ca);cal['point']=data['seasonal'][ca];csv(dest/'calibration.csv.gz',cal)
            f=role_frame(data,te).rename(columns={'y_true':'observed'});f['point']=data['seasonal'][te]
            if not np.isfinite(f.point).all():raise ValueError('seasonal unavailable on frozen support')
            records=[]
            for level in LEVELS:
                q=calibrate_absolute(cal.y_true,cal.point,level)
                if q['status']!='ok':raise ValueError('seasonal calibration rank unsupported')
                z=f.copy();z['lower']=z.point-q['q'];z['upper']=z.point+q['q'];z['raw_crossed']=False
                csv(dest/f'interval_{int(level*100)}.csv.gz',z);records.append(dict(level=level,**q))
            error=f.point-f.observed
            point=dict(dataset=scope['dataset'],outer_fold=scope['outer_fold'],model_seed=scope['model_seed'],horizon=h,model='seasonal_naive',n=len(f),mae=float(np.abs(error).mean()),rmse=float(np.sqrt(np.mean(error**2))),learned_fits=0,deterministic_seed_alias=True)
            atomic(dest/'point.json',point);atomic(dest/'calibration.json',records);return point
        stages.run(f'seasonal_h{h}',seasonal_work)
        tr,ca,te=roles['fit'],roles['calibration'],roles['test']
        for kind,levels in [('cqr',LEVELS),('enbpi',[None])]:
            for l in levels:
                suffix=f'h{h}_{kind}'+(f'_l{int(l*100)}' if l else '')
                print('OWNER '+suffix,flush=True);resources(stages.root)
                fitted=fit_owner(stages,'owner_fit_'+suffix,kind,l,scope['model_seed'],data['X'].iloc[tr],data['y'][tr])
                calibrated=conformalize_owner(stages,'owner_cal_'+suffix,fitted,data['X'].iloc[ca],data['y'][ca])
                rawpath=raw_stage(stages,'raw_'+suffix,calibrated,kind,l,data,roles)
                for level in ([l] if kind=='cqr' else LEVELS):
                    raw=frame(rawpath/f'test_{int(level*100)}.csv.gz');rawcal=frame(rawpath/f'calibration_{int(level*100)}.csv.gz')
                    for method in (['quantile_uncalibrated','cqr'] if kind=='cqr' else ['recentred_enbpi_static','recentred_enbpi_updated']):
                        key=f'stream_h{h}_l{int(level*100)}_{method}'
                        def stream_work(dest,method=method,level=level,raw=raw,rawcal=rawcal):
                            result=emit(method,level,digest(calibrated/'owner.pkl'),data['X'].iloc[te].reset_index(drop=True),role_frame(data,te),raw,role_frame(data,ca),rawcal,data['freq'])
                            return save_stream(dest,result,data['freq'],dict(horizon=h,level=level,method=method))
                        print('STREAM '+key,flush=True);stages.run(key,stream_work)
        del data;gc.collect()
    def join_work(dest):
        for role in ('fit','calibration','test'):
            parts=joint_join({h:frame(historical[h]/(role+'.csv.gz')) for h in scope['horizons']},scope['horizons'],expected=expected_joint(scope['dataset'],scope['outer_fold'],role))
            for h,f in parts.items():csv(dest/f'{role}_h{h}.csv.gz',f)
        return dict(joint_support=p['joint_support'],historical_models_refitted=0)
    joint=stages.run('dscp_joint',join_work)
    calibration={h:frame(joint/f'calibration_h{h}.csv.gz') for h in scope['horizons']};test={h:frame(joint/f'test_h{h}.csv.gz') for h in scope['horizons']}
    P=np.column_stack([calibration[h].point for h in scope['horizons']]);Y=np.column_stack([calibration[h].y_true for h in scope['horizons']]);T=np.column_stack([test[h].point for h in scope['horizons']])
    def dscp_work(dest):
        params={k:p['method_specification']['dscp'][k] for k in ('max_clusters','ks_threshold','neighbours','gamma','seed')}
        with Operations(stages.root/'operations.jsonl',stage='dscp_fit') as ops:calibrator=fit_dscp(P,Y,scope['horizons'],**params)
        dump_owner(dest/'calibrator.pkl',calibrator);atomic(dest/'calibrator_metadata.json',dict(n_clusters=calibrator.n_clusters,neighbours=calibrator.neighbours,silhouette=calibrator.silhouette,metadata=calibrator.metadata,merge_map=calibrator.merge_map));return dict(n_calibration=len(P),parameters=params,operations=ops.rows)
    dscp=stages.run('dscp_fit',dscp_work);calibrator=load_owner(dscp/'calibrator.pkl')
    assignments=[];ranges=[(0,min(64,len(T)))]+[(a,min(a+512,len(T))) for a in range(64,len(T),512)]
    for a,b in ranges:
        key=f'dscp_assignment_{a:06d}_{b:06d}'
        def assign_work(dest,a=a,b=b):
            with Operations(forbid=True):assigned=calibrator.assign(T[a:b])
            np.save(dest/'assignments.npy',assigned);return dict(start=a,end=b,n=b-a,calibrator_sha256=digest(dscp/'calibrator.pkl'),predicted_sequence_hash=hashlib.sha256(T[a:b].tobytes()).hexdigest(),levels_shared=LEVELS,planning_prefix_only=a==0)
        part=stages.run(key,assign_work);assignments.append(np.load(part/'assignments.npy'))
        if a==0 or a%4096==64:print(f'DSCP assigned through {b}/{len(T)}',flush=True)
    assigned=np.concatenate(assignments)
    for l in LEVELS:
        bounds=calibrator.predict_interval(T,l,assignments=assigned)
        for j,h in enumerate(scope['horizons']):
            raw=pd.DataFrame(dict(point=T[:,j],raw_lower=bounds['lower'][:,j],raw_upper=bounds['upper'][:,j],static_lower=bounds['lower'][:,j],static_upper=bounds['upper'][:,j],static_raw_lower=bounds['lower'][:,j],static_raw_upper=bounds['upper'][:,j]))
            calraw=pd.DataFrame(dict(point=P[:,j],raw_lower=P[:,j],raw_upper=P[:,j]))
            def dscp_stream(dest,l=l,h=h,raw=raw,calraw=calraw):
                X=pd.DataFrame(T,columns=[f'matched_xgboost_h{k}' for k in scope['horizons']])
                result=emit('dscp',l,digest(dscp/'calibrator.pkl'),X,test[h],raw,calibration[h],calraw,pd.Timedelta(hours=1))
                result['stream']['dscp_cluster']=assigned
                return save_stream(dest,result,pd.Timedelta(hours=1),dict(horizon=h,level=l,method='dscp'))
            stages.run(f'stream_h{h}_l{int(l*100)}_dscp',dscp_stream)
    tables=finish_tables(stages,scope);counts=read(tables/'operation_counts.json')
    for k,n in p['expected_operations'].items():
        if counts.get(k,0)!=n:raise ValueError(f'actual operation count mismatch {k}: {counts.get(k,0)} != {n}')
    atomic(stages.root/'COMPLETE.json',dict(status='complete',source_hash=p['source_hash'],protocol_hash=digest(path),utc=now(),method_cells=30,seasonal_interval_cells=6,stage_keys=sorted(s.name for s in (stages.root/'stages').iterdir()),files=tree(stages.root)))
    return dict(status='complete',method_cells=30,seasonal_interval_cells=6,operation_counts=counts)


def main():
    a=argparse.ArgumentParser();a.add_argument('action',choices=['freeze','readiness','run','validate','resume']);a.add_argument('--matrix',default=str(MATRIX));a.add_argument('--authorization');a.add_argument('--synthetic-receipt');a.add_argument('--design-dir',required=True);a.add_argument('--out');a.add_argument('--readiness');a.add_argument('--receipt');a.add_argument('--forbid-fits',action='store_true');a.add_argument('--audit-manifest');args=a.parse_args()
    if args.audit_manifest and not (args.action=='validate' or (args.action=='resume' and args.forbid_fits)):raise ValueError('audit manifest is read-only; no fitting/readiness/freeze allowed')
    from .matched_forecasting005 import setup_threads
    setup_threads();protocol=Path(args.design_dir)/'frozen_protocol.json'
    if args.action=='freeze':result=freeze(args.matrix,args.authorization,args.design_dir,args.synthetic_receipt)
    elif args.action=='readiness':result=readiness(protocol,args.receipt)
    elif args.action=='validate':
        from .intervals005_validate import validate
        result=validate(protocol,args.out,args.receipt,audit_manifest=args.audit_manifest)
    else:result=execute(protocol,args.readiness,args.out,resume=args.action=='resume',forbid=args.forbid_fits,receipt=args.receipt,audit_manifest=args.audit_manifest)
    print(json.dumps(result,indent=2,default=str),flush=True)


if __name__=='__main__':main()
