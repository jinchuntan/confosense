"""Actual-data amendment-004 membership/exposure/catalogue audit, with zero fits."""
import argparse
import gc
import json
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
from . import split_integrity as SI
from .datasets.base import ChronologicalPartitioner
from .model_comparison_pilot import prepare
from .run_study import load_config, resolve_dataset_config
from .pilot_resources import ResourceMeter, hardware, require_ram
from .unit_checkpoint import source_digest, signature
from .operational004_design import (DESIGN, build_windows, make_outer_folds, nested_roles,
    candidates, physical_rules, rank_support, resampling_support)
from .operational004_events import catalogue, bank_support


def preflight(out, cache_dir=None):
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    if cache_dir:
        cache_dir = Path(cache_dir); cache_dir.mkdir(parents=True,exist_ok=True)
    study = load_config('configs/study_final_dissertation_v2.yaml')
    all_roles=[]; banks=[]; strata=[]; allocations=[]; rank_rows=[]; boundary_rows=[]; resources=[]; identities=[]; rule_rows=[]
    with ResourceMeter() as total:
        for dataset in DESIGN['tasks']:
            require_ram(3*2**30)
            cfg = resolve_dataset_config(study,dataset)
            print('PREPARE (NO FIT):',dataset,flush=True)
            with ResourceMeter() as meter:
                prepared = prepare(cfg)
                horizon = cfg['alerts']['primary_horizon']; freq = prepared.freq
                segmented,w,fcfg = build_windows(prepared,cfg,horizon)
                meta,X,y = w['meta'],w['X'],w['y']
                scheme = 'chronological' if isinstance(prepared.partitioner,ChronologicalPartitioner) else SI.GROUPED
                folds = make_outer_folds(meta,scheme,3,horizon,freq)
                cs = candidates(cfg,freq)
                rule_rows += [dict(dataset=dataset,**r) for r in physical_rules(freq)]
                identities.append(dict(dataset=dataset,horizon=horizon,freq=str(freq),scheme=scheme,
                    original_prepared_rows=sum(s.n for s in prepared.series),
                    contiguous_observed_rows=sum(s.n for s in segmented.series),
                    eligible_rows=len(meta),groups=meta.group_id.nunique(),data_hash=w['data_hash'],
                    feature_names=list(X.columns),resolved_dataset_config=cfg,candidates=cs))
                # Local cache contains observations; never stage it or use it as
                # a substitute for public derived support tables.
                if cache_dir:
                    with (cache_dir/f'{dataset}_prepared.pkl').open('xb') as f:
                        pickle.dump(dict(prepared=prepared,segmented=segmented,w=w,cfg=cfg,fcfg=fcfg),f)
                members=[]
                for fi,fold in enumerate(folds):
                    roles=nested_roles(meta,fold,scheme)
                    row_roles={i:[] for i in range(len(meta))}
                    for role,idx in roles.items():
                        sub=meta.iloc[idx]
                        all_roles.append(dict(dataset=dataset,outer_fold=fi,role=role,n=len(idx),
                            groups=sub.group_id.nunique(),origin_min=str(sub.origin_time.min()),
                            origin_max=str(sub.origin_time.max()),target_min=str(sub.target_time.min()),
                            target_max=str(sub.target_time.max()),asset_days=len(idx)*freq/pd.Timedelta(days=1),
                            membership_hash=SI.membership_hash(meta,idx)))
                        for i in idx: row_roles[int(i)].append(role)
                    for left,right in [('inner0_train','inner0_calibration'),('inner0_calibration','inner0_selection'),
                        ('inner1_train','inner1_calibration'),('inner1_calibration','inner1_selection'),
                        ('final_fit','final_calibration'),('final_calibration','outer_test')]:
                        boundary_rows.append(dict(dataset=dataset,outer_fold=fi,left=left,right=right,
                            **SI.boundary_record(meta,roles[left],roles[right],scheme)))
                    m=meta[['row_id','group_id','origin_time','target_time']].copy()
                    m['outer_fold']=fi;m['roles']=['|'.join(row_roles[i]) for i in range(len(meta))]
                    members.append(m[m.roles.ne('')])
                    for role,train,cal in [('inner0_selection','inner0_train','inner0_calibration'),
                        ('inner1_selection','inner1_train','inner1_calibration'),
                        ('outer_test','final_fit','final_calibration')]:
                        idx=roles[role]; block=meta.iloc[idx].reset_index(drop=True)
                        sc=SI.training_scale(y,meta,roles[train]);tables=[]
                        support=resampling_support(block,freq,dataset)
                        for seed in DESIGN['catalogue_seeds']:
                            _,_,events,allocation=catalogue(y[idx],block,freq,sc,dataset,role,fi,seed)
                            events.to_csv(out/f'{dataset}_f{fi}_{role}_e{seed}_catalogue.csv.gz',index=False,compression='gzip')
                            tables.append(events);allocations.append(dict(dataset=dataset,outer_fold=fi,role=role,**allocation))
                        counts=bank_support(tables)
                        strata += [dict(dataset=dataset,outer_fold=fi,role=role,**r) for r in counts.to_dict('records')]
                        sufficient = bool(counts.support.all() and support['enough_original_units'])
                        banks.append(dict(dataset=dataset,outer_fold=fi,role=role,
                            effective_events=int(counts.effective.sum()),minimum_distinct_onsets=int(counts.distinct_onsets.min()),
                            supported_strata=int(counts.support.sum()),missing_strata=int((counts.distinct_onsets==0).sum()),
                            required_strata=21,required_effective_onsets_per_stratum=5,
                            **support,structural_event_support=sufficient,
                            status='structural_support_only' if sufficient else 'insufficient_design_support',
                            bounds_identifiable='not_measured_no_fitting'))
                        cm=meta.iloc[roles[cal]]
                        for group in sorted(block.group_id.unique()):
                            same=cm.group_id.eq(group)
                            n=int(same.sum()) if same.any() else len(cm)
                            for c in cs:
                                initial_n=len(cm) # Existing method's global calibration; online pool is group-local.
                                possible_n=min(n,c['window']) if c['window'] else n
                                rank_rows.append(dict(dataset=dataset,outer_fold=fi,role=role,group_id=group,
                                    candidate_id=c['candidate_id'],method=c['method'],level=c['level'],
                                    strategy=c['strategy'],every=c['every'],window=c['window'],
                                    initial_calibration_n=initial_n,group_online_pool_n=n,
                                    historical_pooled_fallback=not bool(same.any()),
                                    initial_minimum_met=initial_n>=400,
                                    initial_rank_supported=rank_support(initial_n,c['level'],c['method'])['supported'],
                                    update_pool_n=possible_n,online_minimum_met=possible_n>=50,
                                    online_rank_supported=rank_support(possible_n,c['level'],c['method'])['supported']))
                    print(dataset,'outer',fi,'support audited (NO FIT)',flush=True)
                pd.concat(members).to_csv(out/f'{dataset}_membership.csv.gz',index=False,compression='gzip')
                del prepared,segmented,w,meta,X,y,members;gc.collect()
            resources.append(dict(dataset=dataset,**meter.result))
    for name,rows in [('memberships_summary',all_roles),('event_support',banks),('stratum_support',strata),
        ('catalogue_summary',allocations),('calibration_rank_support',rank_rows),('boundaries',boundary_rows),
        ('resources',resources),('physical_rule_applicability',rule_rows)]:
        pd.DataFrame(rows).to_csv(out/f'{name}.csv',index=False)
    result=dict(status='complete',models_fitted=0,forecast_or_alert_performance_measured=False,
        design=DESIGN,design_hash=signature(DESIGN),source_hash=source_digest(),hardware=hardware(),
        total_resources=total.result,datasets=identities,unit_banks=len(banks),
        structurally_supported_banks=sum(r['structural_event_support'] for r in banks),
        global_study_ready=False,clarifications=[
            'Final calibration is reserved once by make_outer_folds, not re-cut after purging.',
            'Feature histories restart across genuine source acquisition gaps; source-marked missing targets do not add observed exposure.',
            'Largest-remainder requests for unhostable assets remain explicit rejections; no incidence redistribution to manufacture support.',
            'Event support is structural; no bootstrap or performance claim follows from counts alone.'])
    (out/'summary.json').write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('datasets','hardware','design')},indent=2),flush=True)
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--cache-dir')
    a=ap.parse_args();preflight(a.out,a.cache_dir)
