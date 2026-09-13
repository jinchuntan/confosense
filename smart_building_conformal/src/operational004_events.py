"""Shared, exposure-based amendment-004 schedules and causal sensor corruption."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from .operational004_design import DESIGN, FAMILIES, STRATA, physical_rules, seed_for, segments
from .unit_checkpoint import signature


def corruption(values, family, severity, sigma, sign, rng, predecessor):
    values = np.asarray(values, float)
    out = values.copy(); available = np.ones(len(values), bool)
    if severity == 0:
        return out, available
    if family not in FAMILIES or severity not in (.5, 1., 2.):
        raise ValueError('undeclared fault family/severity')
    n = len(values); fraction = {.5:.25, 1.:.5, 2.:1.}[severity]
    length = math.ceil(n*fraction); start = (n-length)//2
    sub = slice(start,start+length)
    if family == 'random_missing':
        available = rng.random(n) >= .2*severity
    elif family == 'block_missing':
        available[sub] = False
    elif family == 'stuck':
        # Last reading before the actual held sub-block, not a future clean value.
        out[sub] = predecessor if start == 0 else out[start-1]
    elif family == 'dropout':
        out[sub] = 0.
    else:
        u = np.linspace(0,1,n)
        shape = np.minimum(np.minimum(4*u,1),4*(1-u)) if family == 'bias' else u if family == 'drift' else np.ones(n)
        out += sign*severity*sigma*shape
    out[~available] = np.nan
    return out, available


def _allocate(budget, weights):
    keys = sorted(weights)
    if not keys or sum(weights.values()) <= 0:
        return {}
    share = {k: budget*weights[k]/sum(weights.values()) for k in keys}
    out = {k: math.floor(share[k]) for k in keys}
    order = sorted(keys,key=lambda k: (-(share[k]-out[k]),k))
    for k in order[:budget-sum(out.values())]: out[k] += 1
    return out


def catalogue(y, meta, freq, scales, dataset, role, fold, catalogue_seed, *, zero=False):
    """No predictor/performance input. Schedules depend only on declared structure.

    Null-realisation status additionally inspects the proposed sensor change;
    it never resamples a null mask or selects a policy from its performance.
    """
    y = np.asarray(y, float); meta = meta.reset_index(drop=True)
    if len(y) != len(meta) or not np.isfinite(y).all():
        raise ValueError('catalogue requires finite common observed support')
    dt = float(pd.Timedelta(freq)/pd.Timedelta(minutes=1))
    duration = max(4, math.ceil(60/dt))
    tol = {'pleia':6,'pleia_energy':6,'rico':10,'bdg2':3}.get(dataset,6)
    guard = max(max(r['m'] for r in physical_rules(freq) if r['applicable']), tol)
    parts = segments(meta,freq)
    exposures = {}; starts = {}; segment_by_row = {}
    for group, sid, rows in parts:
        exposures[group] = exposures.get(group,0.) + len(rows)*dt/1440
        # A predecessor and full envelope+follow-up must lie inside one segment.
        for j in range(1,len(rows)-duration-tol+1):
            starts.setdefault(group,[]).append((int(rows[j]),sid,rows,j))
        for r in rows: segment_by_row[int(r)] = sid
    total = sum(exposures.values()); requested = math.floor(DESIGN['incidence']*total+.5)
    # Preserve unhostable assets' proportional requests as explicit rejections.
    alloc = _allocate(requested,exposures)
    namespace = seed_for('amendment004',dataset,fold,role,catalogue_seed)
    rng = np.random.default_rng(namespace)
    observed = y.copy(); available = np.ones(len(y),bool)
    events = []; occupied = {}; event_number = 0
    rotation = DESIGN['catalogue_seeds'].index(catalogue_seed)
    for group, count in alloc.items():
        for _ in range(count):
            family,severity = STRATA[(event_number+rotation)%len(STRATA)]
            event_id = f'{dataset}_f{fold}_{role}_e{catalogue_seed}_{event_number:05d}'
            sign = 1 if (event_number//len(STRATA)+rotation)%2 == 0 else -1
            record = dict(event_id=event_id, group_id=group, family=family, severity=severity,
                sign=sign, catalogue_seed=catalogue_seed, namespace_seed=namespace,
                requested=True, placed=False, effective=False, null=False, rejected=True,
                reason='unhostable_group', attempts=0, start_index=-1, end_index=-1,
                segment_id='', onset='', end='', tolerance_end='', duration_steps=duration)
            options = starts.get(group,[])
            for attempt in range(DESIGN['max_placement_attempts'] if options else 0):
                record['attempts'] = attempt+1
                pos,sid,rows,j = options[int(rng.integers(len(options)))]
                end = int(rows[j+duration-1])
                onset_time = pd.Timestamp(meta.iloc[pos].target_time)
                end_time = pd.Timestamp(meta.iloc[end].target_time)
                if any(not (end_time+guard*freq < old_start or onset_time > old_end+guard*freq)
                       for old_start,old_end in occupied.get(sid,[])):
                    record['reason'] = 'placement_guard_exhausted'; continue
                occupied.setdefault(sid,[]).append((onset_time,end_time))
                pick = rows[j:j+duration]
                sigma = float(scales.get(group,scales['__pooled__']))
                values,flags = corruption(observed[pick],family,0. if zero else severity,sigma,sign,
                    np.random.default_rng(seed_for(namespace,event_id,'mask')),observed[rows[j-1]])
                effective = bool((~flags).any() or np.any(values[flags] != y[pick][flags]))
                observed[pick],available[pick] = values,flags
                record.update(placed=True,effective=effective,null=not effective,rejected=False,
                    reason='zero_control' if zero else 'effective' if effective else 'null_realisation',
                    start_index=pos,end_index=end,segment_id=sid,onset=str(onset_time),end=str(end_time),
                    tolerance_end=str(end_time+tol*freq),sigma=sigma,
                    changed_values=int(np.sum(flags & (np.nan_to_num(values) != y[pick]))),
                    unavailable_readings=int((~flags).sum()),
                    mask_hash=signature(flags.tolist()))
                break
            events.append(record); event_number += 1
    columns = ['event_id','group_id','family','severity','sign','catalogue_seed','namespace_seed',
        'requested','placed','effective','null','rejected','reason','attempts','start_index','end_index',
        'segment_id','onset','end','tolerance_end','duration_steps','sigma','changed_values',
        'unavailable_readings','mask_hash']
    table = pd.DataFrame(events,columns=columns)
    summary = dict(requested=requested, attempted=requested,
        placed=int(table.placed.sum()), effective=int(table.effective.sum()),
        null=int(table.null.sum()), rejected=int(table.rejected.sum()),
        asset_days=total, hostable_asset_days=sum(exposures[g] for g in starts),
        requested_incidence=DESIGN['incidence'], realised_incidence=float(table.effective.sum())/total if total else 0.,
        requested_schedule_incidence=requested/total if total else 0.,
        duration_steps=duration, guard_steps=guard, tolerance_steps=tol,
        catalogue_seed=catalogue_seed, namespace_seed=namespace,
        catalogue_hash=signature(table.to_dict('records')), zero_control=zero)
    return observed, available, table, summary


def bank_support(tables):
    table = pd.concat(tables,ignore_index=True) if tables else pd.DataFrame()
    rows = []
    for family,severity in STRATA:
        sub = table[(table.family == family)&(table.severity == severity)] if len(table) else table
        effective = sub[sub.effective.astype(bool)] if len(sub) else sub
        distinct = len(effective[['group_id','onset']].drop_duplicates()) if len(effective) else 0
        rows.append(dict(family=family,severity=severity,requested=len(sub),
            placed=int(sub.placed.sum()) if len(sub) else 0,
            effective=len(effective),distinct_onsets=distinct,
            null=int(sub.null.sum()) if len(sub) else 0,
            rejected=int(sub.rejected.sum()) if len(sub) else 0,
            support=distinct >= DESIGN['min_events_per_stratum']))
    return pd.DataFrame(rows)
