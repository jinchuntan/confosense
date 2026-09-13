"""Episode accounting, custom synthetic utility and paired group/time bounds."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from .operational004_design import DESIGN, STRATA, segments, resampling_support
from .operational004_events import bank_support
from .operational004_stream import stream_hash
from .unit_checkpoint import signature


def alert_on_stream(result, candidate, events, freq):
    frame=result['stream'].copy().reset_index(drop=True)
    consumed=stream_hash(frame)
    if consumed!=result['emitted_hash']:
        raise ValueError('alert-consumed bounds/availability differ from issued stream')
    if not candidate['applicable'] or candidate['k']>candidate['m'] or candidate['m']<1:
        raise ValueError('inapplicable alert rule')
    channels=dict(availability_only=~frame.available.to_numpy(bool),
        numerical_only=frame.available.to_numpy(bool)&((frame.observed<frame.lower)|(frame.observed>frame.upper)).to_numpy())
    channels['combined']=channels['availability_only']|channels['numerical_only']
    parts=segments(frame,freq);eps=[];segment_end={};segment_at={}
    for channel,violations in channels.items():
        flags=np.zeros(len(frame),bool)
        for group,sid,rows in parts:
            segment_end[sid]=pd.Timestamp(frame.iloc[rows[-1]].target_time)
            for row in rows:segment_at[int(row)]=sid
            c=np.r_[0,np.cumsum(violations[rows])]
            count=c[1:]-c[np.maximum(0,np.arange(len(rows))+1-candidate['m'])]
            values=count>=candidate['k'];flags[rows]=values
            starts=np.flatnonzero(values & ~np.r_[False,values[:-1]])
            ends=np.flatnonzero(values & ~np.r_[values[1:],False])
            for start,end in zip(starts,ends):
                a,b=int(rows[start]),int(rows[end])
                eps.append(dict(channel=channel,group_id=group,segment_id=sid,
                    episode_id=f'{channel}:{sid}:{a}',start_index=a,end_index=b,
                    onset=str(frame.iloc[a].target_time),end=str(frame.iloc[b].target_time)))
        frame[f'alert_{channel}']=flags
    episodes=pd.DataFrame(eps,columns=['channel','group_id','segment_id','episode_id','start_index','end_index','onset','end'])
    matches=[]
    for channel in channels:
        ep=episodes[episodes.channel.eq(channel)].sort_values(['group_id','onset','episode_id'],kind='stable')
        used=set()
        eligible=events[events.effective.astype(bool)].sort_values(['group_id','onset','event_id'],kind='stable') if len(events) else events
        for event in eligible.to_dict('records'):
            onset=pd.Timestamp(event['onset']);end=pd.Timestamp(event['tolerance_end'])
            full=event['segment_id'] in segment_end and end<=segment_end[event['segment_id']]
            options=ep[(ep.group_id.astype(str)==str(event['group_id'])) & (ep.segment_id==event['segment_id'])]
            found=None
            if full:
                for e in options.to_dict('records'):
                    t=pd.Timestamp(e['onset'])
                    if e['episode_id'] not in used and onset<=t<=end:
                        found=e;used.add(e['episode_id']);break
            delay=(pd.Timestamp(found['onset'])-onset)/pd.Timedelta(minutes=1) if found else np.nan
            followup=max(0.,(min(end,segment_end.get(event['segment_id'],onset))-onset)/pd.Timedelta(minutes=1))
            matches.append(dict(**event,channel=channel,eligible=full,detected=found is not None,
                episode_id=found['episode_id'] if found else '',delay_minutes=delay,
                followup_minutes=followup,detection_censored=found is None,
                incomplete_followup=not full))
        if len(episodes):
            episodes.loc[episodes.channel.eq(channel),'matched']=episodes.loc[episodes.channel.eq(channel),'episode_id'].isin(used)
    per_event=pd.DataFrame(matches)
    return dict(stream=frame,episodes=episodes,per_event=per_event,
                emitted_hash=result['emitted_hash'],consumed_hash=consumed)


def contributions(clean,corrupt,events,freq):
    """One row per original monitored time; never bootstrap an event-row list."""
    a,b=clean['stream'],corrupt['stream']
    keys=['row_id','group_id','origin_time','target_time']
    pd.testing.assert_frame_equal(a[keys].reset_index(drop=True),b[keys].reset_index(drop=True))
    out=a[keys].copy()
    out['exposure_days']=float(pd.Timedelta(freq)/pd.Timedelta(days=1))
    out['clean_episodes']=0.;out['unmatched_episodes']=0.;out['corrupted_episodes']=0.
    out['time_in_alert_days']=b.alert_combined.to_numpy()*out.exposure_days
    for j in range(len(STRATA)):
        out[f'n{j}']=0.;out[f'tp{j}']=0.
    for scoring,name in [(clean,'clean_episodes'),(corrupt,'corrupted_episodes')]:
        eps=scoring['episodes'];eps=eps[eps.channel.eq('combined')]
        for row in eps.to_dict('records'):
            out.loc[int(row['start_index']),name]+=1
            if name=='corrupted_episodes' and not bool(row.get('matched',False)):
                out.loc[int(row['start_index']),'unmatched_episodes']+=1
    pe=corrupt['per_event']
    if len(pe):
        for event in pe[(pe.channel=='combined')&pe.eligible].to_dict('records'):
            j=STRATA.index((event['family'],float(event['severity'])))
            i=int(event['start_index']);out.loc[i,f'n{j}']+=1
            out.loc[i,f'tp{j}']+=bool(event['detected'])
    return out


def pool_bank(frames):
    if not frames:raise ValueError('empty catalogue bank')
    out=frames[0].copy();keys=['row_id','group_id','origin_time','target_time']
    metric=[c for c in out if c not in keys]
    for frame in frames[1:]:
        pd.testing.assert_frame_equal(frame[keys],out[keys])
        out[metric]+=frame[metric]
    # Catalogue outcomes are pooled for stratum utility, but clean workload and
    # exposure are averaged, retaining the original amount of monitored time.
    for name in ['exposure_days','clean_episodes','time_in_alert_days']:
        out[name]/=len(frames)
    return out


def totals_metrics(totals):
    n=np.array([totals[f'n{j}'] for j in range(21)],float)
    tp=np.array([totals[f'tp{j}'] for j in range(21)],float)
    recalls=np.divide(tp,n,out=np.full(21,np.nan),where=n>0)
    # Algebraic F1 form handles zero detections without undefined precision.
    custom=np.divide(2*tp,n+tp+totals['unmatched_episodes']/21,
                     out=np.full(21,np.nan),where=n>0)
    exposure=float(totals['exposure_days'])
    return dict(macro_event_recall=float(np.mean(recalls)),
        observed_strata_recall=float(np.nanmean(recalls)) if (n>0).any() else np.nan,
        custom_synthetic_f1=float(np.mean(custom)),event_recall_micro=float(tp.sum()/n.sum()) if n.sum() else np.nan,
        ordinary_matched_event_episode_precision=float(tp.sum()/totals['corrupted_episodes']) if totals['corrupted_episodes'] else np.nan,
        background_episodes_per_asset_day=float(totals['clean_episodes']/exposure) if exposure else np.nan,
        exposure_asset_days=exposure,n_events=int(n.sum()),n_detected=int(tp.sum()),
        corrupted_episode_count=int(totals['corrupted_episodes']),unmatched_episode_count=int(totals['unmatched_episodes']),
        time_in_alert_fraction=float(totals['time_in_alert_days']/exposure) if exposure else np.nan,
        observed_strata=int((n>0).sum()))


def summarize_bank(bank,per_events):
    numeric=bank.select_dtypes(include=np.number).sum()
    result=totals_metrics(numeric)
    pe=pd.concat(per_events,ignore_index=True) if per_events else pd.DataFrame()
    detected=np.array([],float)
    if len(pe):
        pe=pe[(pe.channel=='combined')&pe.eligible]
        detected=pe.loc[pe.detected,'delay_minutes'].to_numpy(float)
    result['detected_delay_median_minutes']=float(np.median(detected)) if len(detected) else np.nan
    result['detected_delay_q90_minutes']=float(np.quantile(detected,.9)) if len(detected) else np.nan
    result['undetected_fraction']=1-result['event_recall_micro'] if result['n_events'] else np.nan
    # Complete event windows have their planned follow-up. Restrict to the
    # shortest complete horizon, so misses are retained as right-censored waits.
    tau=float(pe.followup_minutes.min()) if len(pe) else np.nan
    result['delay_restriction_minutes']=tau
    result['restricted_mean_detection_minutes']=float(np.minimum(
        np.where(pe.detected,pe.delay_minutes,pe.followup_minutes),tau).mean()) if len(pe) else np.nan
    return result


def resampling_draws(meta,freq,dataset):
    support=resampling_support(meta,freq,dataset);rng=np.random.default_rng(DESIGN['bootstrap_seed'])
    if dataset in ('rico','bdg2'):
        groups=sorted(meta.group_id.astype(str).unique())
        draws=rng.integers(len(groups),size=(DESIGN['bootstrap_replicates'],len(groups)))
        return dict(kind='whole_group',groups=groups,indices=draws,**support)
    length=support['block_length_steps'];parts=segments(meta,freq)
    if any(len(rows)<length for _,_,rows in parts):
        return dict(kind='unsupported_short_segment',**support)
    # Origins refer to original rows; intervals/events were already scored with
    # their complete surrounding context, so no artificial join creates alarms.
    order=np.concatenate([rows for _,_,rows in parts])
    starts=[];offset=0
    for _,_,rows in parts:
        starts.extend(range(offset,offset+len(rows)-length+1));offset+=len(rows)
    starts=np.asarray(starts,int)
    blocks=math.ceil(len(meta)/length)
    draws=starts[rng.integers(len(starts),size=(DESIGN['bootstrap_replicates'],blocks))]
    lengths=np.full(blocks,length,int);lengths[-1]=len(meta)-length*(blocks-1)
    return dict(kind='moving_block',indices=draws,lengths=lengths,row_order=order,**support)


def confidence_bounds(bank,events,meta,freq,dataset,draws=None):
    support=bank_support(events)
    structural=resampling_support(meta,freq,dataset)
    result=dict(bound_status='insufficient_design_support',valid_replicates=0,
        recall_lcb=np.nan,recall_ucb=np.nan,workload_lcb=np.nan,workload_ucb=np.nan,
        supported_strata=int(support.support.sum()),**structural)
    if not support.support.all() or not structural['enough_original_units']:
        return result
    draws=draws or resampling_draws(meta,freq,dataset)
    if draws['kind']=='unsupported_short_segment':
        return dict(result,bound_status='insufficient_bound_support',bound_reason='segment shorter than declared moving block')
    names=['exposure_days','clean_episodes']+[f'n{j}' for j in range(21)]+[f'tp{j}' for j in range(21)]
    array=bank[names].to_numpy(float)
    if draws['kind']=='whole_group':
        groups=meta.group_id.astype(str).to_numpy()
        clustered=np.stack([array[groups==g].sum(axis=0) for g in draws['groups']])
        totals=clustered[draws['indices']].sum(axis=1)
    else:
        array=array[draws['row_order']]
        cumulative=np.vstack([np.zeros(array.shape[1]),np.cumsum(array,axis=0)])
        batches=[]
        for start in range(0,len(draws['indices']),100):
            idx=draws['indices'][start:start+100]
            batches.append((cumulative[idx+draws['lengths']]-cumulative[idx]).sum(axis=1))
        totals=np.concatenate(batches)
    n=totals[:,2:23];tp=totals[:,23:44]
    valid=(n>0).all(axis=1)&(totals[:,0]>0)&np.isfinite(totals).all(axis=1)
    r=np.mean(tp[valid]/n[valid],axis=1);w=totals[valid,1]/totals[valid,0]
    result['valid_replicates']=int(valid.sum())
    if valid.sum()<DESIGN['minimum_valid_replicates'] or np.ptp(r)==0 or np.ptp(w)==0:
        return dict(result,bound_status='insufficient_bound_support',bound_reason='too few valid or degenerate resamples')
    result.update(bound_status='supported',recall_lcb=float(np.quantile(r,.025)),recall_ucb=float(np.quantile(r,.975)),
        workload_lcb=float(np.quantile(w,.025)),workload_ucb=float(np.quantile(w,.975)),
        resampling_hash=signature({k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in draws.items()}))
    return result


def select_pipeline(surface,expected_candidates,*,objective='primary'):
    """Every candidate retains both folds; unavailable bounds never use points."""
    if objective not in ('primary','inverse_recall_floor'):raise ValueError('unknown selection objective')
    if surface.duplicated(['candidate_id','inner_fold']).any():raise ValueError('duplicate candidate/fold cell')
    expected={c['candidate_id'] for c in expected_candidates}
    if len(expected)!=len(expected_candidates) or not expected:
        raise ValueError('empty/duplicate candidate grid')
    if set(surface.candidate_id)-expected:raise ValueError('unexpected candidate identity')
    decisions=[]
    for candidate in expected_candidates:
        cid=candidate['candidate_id'];sub=surface[surface.candidate_id.eq(cid)]
        reasons=[]
        if sorted(sub.inner_fold.tolist())!=[0,1]:reasons.append('missing_required_inner_fold')
        else:
            for row in sub.to_dict('records'):
                if row['bound_status']!='supported':reasons.append(f"fold{row['inner_fold']}:{row['bound_status']}")
                elif not np.isfinite([row['recall_lcb'],row['workload_ucb'],row['custom_synthetic_f1']]).all():
                    reasons.append(f"fold{row['inner_fold']}:nonfinite_bounds_or_utility")
                else:
                    if row['recall_lcb']<.6:reasons.append(f"fold{row['inner_fold']}:recall_below_floor")
                    if objective=='primary' and row['workload_ucb']>1.:reasons.append(f"fold{row['inner_fold']}:workload_above_ceiling")
        decisions.append(dict(candidate_id=cid,feasible=not reasons,reasons=';'.join(reasons),
            equal_fold_custom_synthetic_f1=float(sub.custom_synthetic_f1.mean()) if len(sub)==2 else np.nan,
            equal_fold_workload=float(sub.background_episodes_per_asset_day.mean()) if len(sub)==2 else np.nan,
            equal_fold_detected_delay=float(sub.detected_delay_median_minutes.mean())
                if len(sub)==2 and np.isfinite(sub.detected_delay_median_minutes).all() else float('inf')))
    table=pd.DataFrame(decisions);feasible=table[table.feasible]
    if feasible.empty:
        return dict(decision='no_feasible_configuration',pipeline=None,rejections=table,
            diagnostic_fallback=DESIGN['diagnostic_fallback'],operational_feasible=False)
    columns=(['equal_fold_custom_synthetic_f1','equal_fold_detected_delay','equal_fold_workload','candidate_id']
             if objective=='primary' else ['equal_fold_workload','equal_fold_custom_synthetic_f1','equal_fold_detected_delay','candidate_id'])
    best=feasible.sort_values(columns,ascending=[False,True,True,True] if objective=='primary' else [True,False,True,True],kind='stable').iloc[0]
    return dict(decision='selected',pipeline=next(c for c in expected_candidates if c['candidate_id']==best.candidate_id),
        rejections=table,diagnostic_fallback=None,operational_feasible=True)


def family_attribution(per_event):
    rows=[]
    for family,severity in STRATA:
        for channel in ['availability_only','numerical_only','combined']:
            sub=per_event[(per_event.family==family)&(per_event.severity==severity)
                          &(per_event.channel==channel)&per_event.eligible] if len(per_event) else per_event
            rows.append(dict(family=family,severity=severity,channel=channel,n_events=len(sub),
                n_detected=int(sub.detected.sum()) if len(sub) else 0,
                recall=float(sub.detected.mean()) if len(sub) else np.nan))
    return pd.DataFrame(rows)


def group_workload(bank,freq):
    groups=[]
    for group,part in bank.groupby('group_id',sort=True):
        exposure=float(part.exposure_days.sum());count=float(part.clean_episodes.sum())
        metrics=totals_metrics(part.select_dtypes(include=np.number).sum())
        groups.append(dict(group_id=group,asset_days=exposure,clean_episodes=count,episodes_per_asset_day=count/exposure,
                          event_recall_micro=metrics['event_recall_micro'],n_events=metrics['n_events'],n_detected=metrics['n_detected']))
    calendar=len(pd.to_datetime(bank.target_time).unique())*freq/pd.Timedelta(days=1)
    rates=pd.DataFrame(groups)
    return rates,dict(equal_group_episode_rate=float(rates.episodes_per_asset_day.mean()),
        equal_group_event_recall=float(rates.event_recall_micro.mean()) if rates.event_recall_micro.notna().any() else np.nan,
        portfolio_calendar_days=float(calendar),portfolio_episodes_per_calendar_day=float(rates.clean_episodes.sum()/calendar))


def group_recovery(stream,truth,faults,freq):
    """Coverage recovery is a diagnostic with explicit right-censored follow-up."""
    rows=[];truth=np.asarray(truth,float)
    for group,part in stream.groupby('group_id',sort=True):
        fs=faults[faults.group_id.astype(str).eq(str(group))&faults.effective.astype(bool)]
        if fs.empty:continue
        onset=pd.to_datetime(fs.onset).min();end=pd.to_datetime(fs.end).max()
        idx=part.index.to_numpy();times=pd.to_datetime(part.target_time)
        pre=(times<onset).to_numpy();post=(times>end).to_numpy()
        cover=(truth[idx]>=part.lower.to_numpy())&(truth[idx]<=part.upper.to_numpy())
        post_rows=np.flatnonzero(post)
        if not pre.any() or not len(post_rows):
            rows.append(dict(group_id=group,status='insufficient_recovery_support',recovery_minutes=np.nan,
                recovery_censored=True,followup_minutes=0.));continue
        baseline=float(cover[pre].mean())
        window=max(1,min(int(pd.Timedelta(days=1)/freq),len(post_rows)//4))
        rolling=pd.Series(cover[post].astype(float)).rolling(window,min_periods=window).mean().to_numpy()
        success=np.flatnonzero(np.abs(rolling-baseline)<=.05)
        at=float((times.iloc[post_rows[success[0]]]-end)/pd.Timedelta(minutes=1)) if len(success) else np.nan
        rows.append(dict(group_id=group,status='observed' if len(success) else 'right_censored',
            pre_coverage=baseline,window_steps=window,recovery_minutes=at,recovery_censored=not len(success),
            followup_minutes=float((times.iloc[post_rows[-1]]-end)/pd.Timedelta(minutes=1))))
    result=pd.DataFrame(rows)
    valid=result[result.status.ne('insufficient_recovery_support')] if len(result) else result
    if not len(valid):return result,dict(status='insufficient_recovery_support')
    tau=float(valid.followup_minutes.min())
    waits=np.where(valid.recovery_censored,np.inf,valid.recovery_minutes)
    median=float(np.sort(waits)[math.ceil(len(waits)/2)-1])
    return result,dict(status='descriptive_group_recovery',groups=len(valid),common_horizon_minutes=tau,
        probability_recovered_by_horizon=float(np.mean(waits<=tau)),
        restricted_mean_recovery_minutes=float(np.minimum(waits,tau).mean()),
        median_recovery_minutes=median if np.isfinite(median) else None,
        censored_groups=int(valid.recovery_censored.sum()))
