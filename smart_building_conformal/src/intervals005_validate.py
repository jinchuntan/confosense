"""Independent scalar, metric, native-quantile and serialized-owner checks."""
from __future__ import annotations
import bisect
import gc
import math
import warnings
import numpy as np
import pandas as pd
from .intervals005_common import *
from .intervals005_data import load_data,joint_join,expected_joint,role_frame,historical_predictions
from .operational004_design import segments


def independent_metrics(f,level):
    y=np.asarray(f.observed,float);lower=np.asarray(f.lower,float);upper=np.asarray(f.upper,float)
    if not (np.isfinite(y).all() and np.isfinite(lower).all() and np.isfinite(upper).all() and (lower<=upper).all()):raise ValueError('invalid row; cannot silently exclude')
    covered=(lower<=y)&(y<=upper);width=upper-lower
    winkler=width.copy();low=y<lower;high=y>upper
    winkler[low]+=2*(lower[low]-y[low])/(1-level);winkler[high]+=2*(y[high]-upper[high])/(1-level)
    error=np.asarray(f.point,float)-y;coverage=np.count_nonzero(covered)/len(y)
    return dict(n=len(y),coverage=coverage,signed_coverage_deviation=coverage-level,absolute_coverage_deviation=abs(coverage-level),mpiw=np.sum(width)/len(y),winkler=np.sum(winkler)/len(y),mae=np.sum(np.abs(error))/len(y),rmse=math.sqrt(np.dot(error,error)/len(y)),sum_absolute_error=np.sum(np.abs(error)),sum_squared_error=np.dot(error,error),sum_width=np.sum(width),sum_winkler=np.sum(winkler),covered_count=np.count_nonzero(covered),available_count=int(f.available.sum()),unavailable_count=int((~f.available).sum()))


def quantile_pair(sorted_scores,level,kind):
    n=len(sorted_scores)
    if kind=='cqr':lo=hi=math.ceil((n+1)*level)
    else:lo=math.floor((n+1)*(1-level)/2+1e-12);hi=math.ceil((n+1)*(1-(1-level)/2)-1e-12)
    if not 1<=lo<=hi<=n:return None
    return sorted_scores[lo-1],sorted_scores[hi-1]


def scalar_replay(meta,raw,cal,rawcal,level,kind,strategy='static',*,every=1,window=None,freq=pd.Timedelta(hours=1)):
    """Independent ordered scalar state machine; never calls production replay."""
    y=np.asarray(meta.y_true,float);available=np.asarray(meta.available,bool)
    yc=np.asarray(cal.y_true,float)
    scorecal=np.maximum(rawcal.raw_lower-yc,yc-rawcal.raw_upper).to_numpy() if kind in ('cqr','quantile_uncalibrated') else yc-rawcal.point.to_numpy()
    rankkind='cqr' if kind in ('cqr','quantile_uncalibrated') else kind
    base=quantile_pair(sorted(scorecal),level,rankkind)
    if base is None:raise ValueError('initial unsupported rank')
    times=pd.to_datetime(meta.target_time).astype('int64').to_numpy();origins=pd.to_datetime(meta.origin_time).astype('int64').to_numpy()
    lo=np.full(len(meta),np.nan);hi=lo.copy();release=[];updates=[]
    for group,sid,idx in segments(meta,freq):
        mask=cal.group_id.astype(str).eq(group).to_numpy()
        if not mask.any():mask=np.ones(len(cal),bool)
        # Preserve chronological rolling history separately from order statistics.
        order=np.argsort(pd.to_datetime(cal.target_time).astype('int64').to_numpy()[mask],kind='stable')
        history=list(scorecal[mask][order]);sorted_history=sorted(history);q=base;pointer=0
        for ordinal,i in enumerate(idx):
            while pointer<ordinal and times[idx[pointer]]<=origins[i]:
                old=idx[pointer];pointer+=1
                if available[old]:
                    score=max(float(raw.raw_lower.iloc[old])-y[old],y[old]-float(raw.raw_upper.iloc[old])) if kind in ('cqr','quantile_uncalibrated') else y[old]-float(raw.point.iloc[old])
                    history.append(score);bisect.insort(sorted_history,score)
                    release.append(dict(row_id=str(meta.row_id.iloc[old]),group_id=group,segment_id=sid,score=score,released_at_origin=str(pd.Timestamp(meta.origin_time.iloc[i]))))
            if strategy!='static' and ordinal%every==0:
                values=sorted(history[-window:]) if strategy=='rolling' else sorted_history
                proposed=quantile_pair(values,level,rankkind) if len(values)>=50 else None
                status='updated' if proposed is not None else 'held_insufficient_score_or_rank_support'
                if proposed is not None:q=proposed
                updates.append(dict(group_id=group,segment_id=sid,origin_time=str(pd.Timestamp(meta.origin_time.iloc[i])),pool_n=len(values),correction_lower=q[0],correction_upper=q[1],status=status))
            if kind=='quantile_uncalibrated':lo[i],hi[i]=sorted((float(raw.raw_lower.iloc[i]),float(raw.raw_upper.iloc[i])))
            elif strategy=='static':lo[i]=raw.static_lower.iloc[i];hi[i]=raw.static_upper.iloc[i]
            elif kind=='cqr':lo[i],hi[i]=sorted((float(raw.raw_lower.iloc[i])-q[0],float(raw.raw_upper.iloc[i])+q[1]))
            else:lo[i]=raw.point.iloc[i]+q[0];hi[i]=raw.point.iloc[i]+q[1]
    numerical=available&((y<lo)|(y>hi))
    return dict(lower=lo,upper=hi,numerical=numerical,releases=pd.DataFrame(release),updates=pd.DataFrame(updates))


def independent_alert(f,freq,k=1,m=1):
    # Segment boundaries independently derived without production segments().
    expected={name:np.zeros(len(f),bool) for name in ('numerical_only','availability_only','combined')};episodes=[]
    numerical=f.available.to_numpy(bool)&((f.observed<f.lower)|(f.observed>f.upper)).to_numpy()
    flags=dict(numerical_only=numerical,availability_only=~f.available.to_numpy(bool),combined=numerical|~f.available.to_numpy(bool))
    for group in sorted(f.group_id.astype(str).unique()):
        ix=np.flatnonzero(f.group_id.astype(str).eq(group));ix=ix[np.argsort(pd.to_datetime(f.target_time.iloc[ix]).astype('int64'),kind='stable')]
        gap=np.r_[True,np.diff(pd.to_datetime(f.target_time.iloc[ix]).astype('int64'))!=pd.Timedelta(freq).value];sid=-1;history=[];active={name:None for name in flags}
        for j,i in enumerate(ix):
            if gap[j]:sid+=1;history=[]
            history.append(i)
            for channel,arr in flags.items():
                on=sum(bool(arr[t]) for t in history[-m:])>=k
                expected[channel][i]=on
                if on and (gap[j] or not expected[channel][ix[j-1]]):episodes.append(dict(channel=channel,group_id=group,segment_id=f'{group}:segment:{sid}',start_index=int(i),onset=str(pd.Timestamp(f.target_time.iloc[i]))))
    return expected,pd.DataFrame(episodes,columns=['channel','group_id','segment_id','start_index','onset'])


def validate(protocol_path,out,receipt,*,audit_manifest=None):
    from .matched_intervals005 import check_protocol
    p=check_protocol(protocol_path,audit_manifest);root=Path(out);before=tree(root);complete=read(root/'COMPLETE.json')
    frozen=dict(before);frozen.pop('COMPLETE.json')
    if frozen!=complete['files']:raise ValueError('completed scientific artifact hash mismatch')
    dest=Path(receipt)
    if dest.exists():raise ValueError('preserve existing validation; use new receipt directory')
    dest.mkdir(parents=True);stage=root/'stages';checks=[];metric_checks=[];alert_checks=[];maxdiff=0.;prepared=None
    def close(actual,expected,tag,atol=1e-7,rtol=1e-7):
        nonlocal maxdiff
        a=np.asarray(actual,float);b=np.asarray(expected,float)
        delta=float(np.nanmax(np.abs(a-b))) if a.size else 0.;maxdiff=max(maxdiff,delta)
        np.testing.assert_allclose(a,b,atol=atol,rtol=rtol,equal_nan=True,err_msg=tag)
        checks.append(dict(check=tag,n=a.size,maximum_difference=delta,atol=atol,rtol=rtol))
    with Operations(forbid=True),PhaseMeter() as meter:
        for h in p['scope']['horizons']:
            print(f'VALIDATE horizon {h}',flush=True)
            data,roles,prepared=load_data(p['references'][str(h)],prepared)
            histories,_=historical_predictions(p['references'][str(h)],data,roles)
            for role,hist in histories.items():close(frame(stage/f'historical_h{h}'/(role+'.csv.gz')).point,hist.point,f'historical_reload_{h}_{role}')
            calmeta=role_frame(data,roles['calibration']);testmeta=role_frame(data,roles['test'])
            native_ids=set(testmeta.row_id);common=set(frame(stage/'dscp_joint'/f'test_h{h}.csv.gz').row_id)
            for kind,levels in [('cqr',LEVELS),('enbpi',[None])]:
                for level in levels:
                    suffix=f'h{h}_{kind}'+(f'_l{int(level*100)}' if level else '')
                    owner=load_owner(stage/('owner_cal_'+suffix)/'owner.pkl');rawpath=stage/('raw_'+suffix)
                    for role in ('calibration','test'):
                        X=data['X'].iloc[roles[role]].to_numpy();levels_actual=[level] if kind=='cqr' else LEVELS
                        stored={l:frame(rawpath/f'{role}_{int(l*100)}.csv.gz') for l in levels_actual}
                        for start in range(0,len(X),256):
                            block=X[start:start+256];sl=slice(start,start+len(block))
                            if kind=='cqr':
                                sub=owner._mapie_quantile_regressor.estimators_;raw=[e.predict(block) for e in sub]
                                for name,arr in zip(('raw_lower','raw_upper','point'),raw):close(stored[level][name].iloc[sl],arr,f'reload_{h}_{kind}_{level}_{role}_{start}_{name}')
                            else:
                                prediction=owner.estimator_.single_estimator_.predict(block)
                                for l in levels_actual:close(stored[l].point.iloc[sl],prediction,f'reload_{h}_{kind}_{l}_{role}_{start}_point')
                    if kind=='cqr':
                        rawcal=frame(rawpath/f'calibration_{int(level*100)}.csv.gz');scores=np.maximum(rawcal.raw_lower-calmeta.y_true,calmeta.y_true-rawcal.raw_upper).to_numpy()
                        close(owner._mapie_quantile_regressor.conformity_scores_[2],scores,f'cqr_scores_h{h}_{level}')
                        # MAPIE 1.4.1 predict_interval defaults to asymmetric
                        # correction. Online CQR replay still uses max scores.
                        tail_scores=np.vstack([rawcal.raw_lower-calmeta.y_true,calmeta.y_true-rawcal.raw_upper])
                        close(owner._mapie_quantile_regressor.conformity_scores_[:2],tail_scores,f'cqr_tail_scores_h{h}_{level}')
                        correction=np.quantile(tail_scores,(1-(1-level)/2)*(1+1/len(scores)),axis=1,method='higher')
                    else:
                        # MAPIE's out-of-fold matrix is float64 even when the
                        # XGBoost predictions are float32. Match its arithmetic
                        # before averaging, without relaxing frozen tolerances.
                        X=data['X'].iloc[roles['calibration']].to_numpy();preds=np.column_stack([e.predict(X) for e in owner.estimator_.estimators_]).astype(np.float64);mask=owner.estimator_.k_
                        with warnings.catch_warnings():
                            warnings.simplefilter('ignore',RuntimeWarning);oob=np.nanmean(np.where(mask==1,preds,np.nan),axis=1)
                        scores=calmeta.y_true.to_numpy()-oob
                        if owner.conformity_score_function_.sym:scores=np.abs(scores)
                        close(owner.conformity_scores_,scores,f'enbpi_oob_scores_h{h}')
                    for l in ([level] if kind=='cqr' else LEVELS):
                        raw=frame(rawpath/f'test_{int(l*100)}.csv.gz');rawcal=frame(rawpath/f'calibration_{int(l*100)}.csv.gz')
                        if kind=='cqr':
                            a=raw.raw_lower.to_numpy()-correction[0];b=raw.raw_upper.to_numpy()+correction[1]
                            close(raw.static_lower,np.minimum(a,b),f'cqr_native_lo_h{h}_{l}');close(raw.static_upper,np.maximum(a,b),f'cqr_native_hi_h{h}_{l}')
                        else:
                            finite=scores[np.isfinite(scores)];n=len(finite)
                            def q(alpha,reverse=False):
                                signed=-1 if reverse else 1;ref=1-alpha if reverse else alpha
                                corrected=min(1,max(0,math.ceil(ref*(n+1))/n))
                                return signed*np.quantile(signed*finite,corrected,method='lower')
                            if owner.conformity_score_function_.sym:upper=q(l);lower=-upper
                            else:lower=q((1-l)/2,True);upper=q(1-(1-l)/2)
                            native_point=owner.estimator_.single_estimator_.predict(data['X'].iloc[roles['test']].to_numpy()).astype(np.float64)
                            # CSV's shortest float32 decimals recover the exact
                            # owner points at their original dtype. Reading
                            # them as float64 first can spoil near-zero bounds.
                            close(raw.point.to_numpy(np.float32).astype(np.float64),native_point,f'enbpi_point_float32_roundtrip_h{h}_{l}',atol=0,rtol=0)
                            close(raw.static_lower,native_point+lower,f'enbpi_native_lo_h{h}_{l}');close(raw.static_upper,native_point+upper,f'enbpi_native_hi_h{h}_{l}')
                        for method in (['quantile_uncalibrated','cqr'] if kind=='cqr' else ['recentred_enbpi_static','recentred_enbpi_updated']):
                            path=stage/f'stream_h{h}_l{int(l*100)}_{method}';f=frame(path/'issued.csv.gz')
                            scalar=scalar_replay(testmeta,raw,calmeta,rawcal,l,method if kind=='cqr' else 'recentred_enbpi',strategy='native_updated' if method.endswith('_updated') else 'static')
                            close(f.lower,scalar['lower'],f'scalar_lower_{h}_{l}_{method}');close(f.upper,scalar['upper'],f'scalar_upper_{h}_{l}_{method}')
                            if not np.array_equal(f.numerical_violation,scalar['numerical']):raise ValueError('numerical flag mismatch')
                            saved_release=frame(path/'released_scores.csv.gz')
                            if len(saved_release)!=len(scalar['releases']):raise ValueError('release count mismatch')
                            if len(saved_release):
                                if list(saved_release.row_id)!=list(scalar['releases'].row_id):raise ValueError('release row mismatch')
                                close(saved_release.score,scalar['releases'].score,f'released_scores_{h}_{l}_{method}')
                                if not np.array_equal(pd.to_datetime(saved_release.released_at_origin),pd.to_datetime(scalar['releases'].released_at_origin)):raise ValueError('causal release time mismatch')
                            if method.endswith('_updated'):
                                u=frame(path/'updates.csv.gz');v=scalar['updates']
                                close(u[['pool_n','correction_lower','correction_upper']],v[['pool_n','correction_lower','correction_upper']],f'update_state_{h}_{l}')
                                if list(u.status)!=list(v.status):raise ValueError('hold/update status mismatch')
            for l in LEVELS:
                for method in METHODS:
                    path=stage/f'stream_h{h}_l{int(l*100)}_{method}';f=frame(path/'issued.csv.gz');consumed=frame(path/'consumed.csv.gz')
                    if set(f.row_id)!=(common if method=='dscp' else native_ids):raise ValueError('native cohort changed')
                    expected_meta=(frame(stage/'dscp_joint'/f'test_h{h}.csv.gz') if method=='dscp' else testmeta).set_index('row_id').loc[f.row_id]
                    if not np.array_equal(f.available,expected_meta.available):raise ValueError('source availability changed')
                    close(f.observed,expected_meta.y_true,f'outcome_identity_{h}_{l}_{method}',atol=1e-12,rtol=0)
                    for time_column in ('origin_time','target_time'):
                        if not np.array_equal(pd.to_datetime(f[time_column]),pd.to_datetime(expected_meta[time_column])):raise ValueError('timestamp identity mismatch')
                    for col in ('row_id','group_id','origin_time','target_time','lower','upper','available'):
                        if not np.array_equal(f[col],consumed[col]):raise ValueError('consumed stream mismatch: '+col)
                    flags,episodes=independent_alert(f,pd.Timedelta(hours=1));saved=frame(path/'episodes.csv.gz')
                    for name,expected in flags.items():
                        if not np.array_equal(consumed['alert_'+name],expected):raise ValueError('alert flag mismatch')
                    if len(saved)!=len(episodes):raise ValueError('episode count mismatch')
                    for col in ('channel','group_id','segment_id','start_index'):
                        if not np.array_equal(saved[col],episodes[col]):
                            # Production is channel-major; compare keyed episodes.
                            cols=['channel','group_id','segment_id','start_index']
                            if set(map(tuple,saved[cols].to_numpy()))!=set(map(tuple,episodes[cols].to_numpy())):raise ValueError('episode identity mismatch')
                    alert_checks.append(dict(horizon=h,level=l,method=method,n=len(f),episodes=len(saved),passed=True))
                    for support,part in [('native',f),('common',f[f.row_id.isin(common)])]:
                        expected=independent_metrics(part,l);summary=frame(stage/'tables'/f'{support}_support_metrics.csv');row=summary[(summary.horizon==h)&(summary.level==l)&(summary.method==method)].iloc[0]
                        for name,value in expected.items():close(row[name],value,f'metric_{support}_{h}_{l}_{method}_{name}',atol=1e-10,rtol=1e-12)
                        metric_checks.append(dict(horizon=h,level=l,method=method,support=support,**expected))
                        groups=frame(stage/'tables'/'per_building_metrics.csv');groups=groups[(groups.horizon==h)&(groups.level==l)&(groups.method==method)&(groups.support==support)]
                        for group,sub in part.groupby('group_id'):
                            gr=groups[groups.group_id.astype(str)==str(group)].iloc[0]
                            for col,value in independent_metrics(sub,l).items():close(gr[col],value,f'building_{support}_{h}_{l}_{method}_{group}_{col}',atol=1e-7,rtol=1e-12)
                        for col in ('n','covered_count','sum_absolute_error','sum_squared_error','sum_width','sum_winkler'):close(groups[col].sum(),expected[col],f'group_reconcile_{support}_{h}_{l}_{method}_{col}',atol=1e-7,rtol=1e-12)
                sf=frame(stage/f'seasonal_h{h}'/f'interval_{int(l*100)}.csv.gz');ca=frame(stage/f'seasonal_h{h}'/'calibration.csv.gz')
                close(sf.point,data['seasonal'][roles['test']],f'seasonal_point_h{h}_{l}')
                residuals=sorted(np.abs(ca.y_true-ca.point));rank=math.ceil((len(residuals)+1)*l);q=residuals[rank-1]
                close(sf.lower,sf.point-q,f'seasonal_lower_h{h}_{l}');close(sf.upper,sf.point+q,f'seasonal_upper_h{h}_{l}')
                ss=frame(stage/'tables'/'seasonal_interval_metrics.csv');sr=ss[(ss.horizon==h)&(ss.level==l)].iloc[0]
                for name,value in independent_metrics(sf,l).items():close(sr[name],value,f'seasonal_metric_{h}_{l}_{name}',atol=1e-7,rtol=1e-12)
            del data;gc.collect()
        calibrator=load_owner(stage/'dscp_fit'/'calibrator.pkl');hs=p['scope']['horizons']
        cal={h:frame(stage/'dscp_joint'/f'calibration_h{h}.csv.gz') for h in hs};test={h:frame(stage/'dscp_joint'/f'test_h{h}.csv.gz') for h in hs}
        P=np.column_stack([cal[h].point for h in hs]);Y=np.column_stack([cal[h].y_true for h in hs]);T=np.column_stack([test[h].point for h in hs])
        close(calibrator.calib_predictions,P,'dscp_calibration_prediction_identity')
        errors=Y-P
        for cluster in range(calibrator.n_clusters):
            mask=calibrator.cluster_labels==cluster
            for j in range(len(hs)):
                members=[i for i in range(len(hs)) if calibrator.merge_map[cluster][i]==calibrator.merge_map[cluster][j]]
                expected=np.concatenate([errors[mask,i] for i in members])
                close(calibrator.merged_errors[cluster][j],expected,f'dscp_calibration_only_pool_{cluster}_{j}')
        # Native assignments after serialization, full cohort, no calibrator fit.
        assignments=calibrator.assign(T)
        for l in LEVELS:
            for j,h in enumerate(hs):
                f=frame(stage/f'stream_h{h}_l{int(l*100)}_dscp'/'issued.csv.gz')
                if not np.array_equal(f.dscp_cluster,assignments):raise ValueError('serialized DSCP assignment mismatch')
                low=np.empty(len(T));high=low.copy()
                for cluster in range(calibrator.n_clusters):
                    pool=calibrator.merged_errors[cluster][j];values=np.quantile(pool,[(1-l)/2,1-(1-l)/2]);mask=assignments==cluster
                    low[mask]=T[mask,j]+values[0];high[mask]=T[mask,j]+values[1]
                close(f.lower,low,f'dscp_lower_h{h}_{l}');close(f.upper,high,f'dscp_upper_h{h}_{l}')
        counts=read(stage/'tables'/'operation_counts.json')
        for name,n in p['expected_operations'].items():
            if counts.get(name,0)!=n:raise ValueError('actual operations mismatch')
    if tree(root)!=before:raise ValueError('independent validation mutated source artifacts')
    csv(dest/'reconstruction_checks.csv',pd.DataFrame(checks));csv(dest/'independent_metrics.csv',pd.DataFrame(metric_checks));csv(dest/'alert_checks.csv',pd.DataFrame(alert_checks))
    result=dict(passed=True,method_cells=30,native_common_metric_rows=len(metric_checks),seasonal_interval_cells=6,alert_stream_checks=len(alert_checks),maximum_observed_difference=maxdiff,models_fitted=0,calibrators_fitted=0,source_artifacts_unchanged=True,resources=meter.result,source_hash=p['source_hash'],protocol_hash=digest(protocol_path),utc=now())
    if audit_manifest:result.update(validator_source_hash=source_digest(),audit_manifest_sha256=digest(audit_manifest))
    atomic(dest/'validation.json',result);atomic(dest/'COMPLETE.json',dict(files=tree(dest)));return result
