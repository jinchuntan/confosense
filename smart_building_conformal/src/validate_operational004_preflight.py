"""Independently check published no-fit membership/catalogue support records."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from . import split_integrity as SI
from .operational004_design import DESIGN,physical_rules,segments,rank_support
from .operational004_events import bank_support
from .unit_checkpoint import digest,signature


def validate(run,out):
    run=Path(run);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    summary=json.loads((run/'summary.json').read_text(encoding='utf-8'))
    assert summary['models_fitted']==0 and not summary['forecast_or_alert_performance_measured']
    assert summary['design_hash']==signature(DESIGN)
    banks=pd.read_csv(run/'event_support.csv');strata=pd.read_csv(run/'stratum_support.csv')
    roles=pd.read_csv(run/'memberships_summary.csv');bounds=pd.read_csv(run/'boundaries.csv')
    allocations=pd.read_csv(run/'catalogue_summary.csv');ranks=pd.read_csv(run/'calibration_rank_support.csv')
    identities={r['dataset']:r for r in summary['datasets']};group_rows=[];purges=[];aliases=[];members={}
    assert len(banks)==36 and len(strata)==36*21 and len(allocations)==180
    for dataset in DESIGN['tasks']:
        m=pd.read_csv(run/f'{dataset}_membership.csv.gz',converters={'group_id':str},parse_dates=['origin_time','target_time'])
        assert not m.duplicated(['outer_fold','row_id']).any()
        freq=pd.Timedelta(identities[dataset]['freq']);scheme=identities[dataset]['scheme']
        for fi in range(3):
            original=m[m.outer_fold.eq(fi)].reset_index(drop=True);decoded={}
            for r in roles[roles.dataset.eq(dataset)&roles.outer_fold.eq(fi)].to_dict('records'):
                mask=original.roles.str.split('|',regex=False).map(lambda x:r['role'] in x)
                idx=np.flatnonzero(mask)
                if r['role']=='final_fit':idx=np.concatenate([decoded[f'B{i}'] for i in range(4)])
                elif r['role']=='inner1_train':idx=np.concatenate([decoded['B0'],decoded['B1']])
                part=original.iloc[idx];decoded[r['role']]=idx
                assert len(part)==r['n'] and part.group_id.nunique()==r['groups']
                assert SI.membership_hash(original,idx)==r['membership_hash'],(dataset,fi,r['role'])
                assert np.isclose(len(part)*freq/pd.Timedelta(days=1),r['asset_days'])
            for row in bounds[bounds.dataset.eq(dataset)&bounds.outer_fold.eq(fi)].to_dict('records'):
                SI.assert_boundary(original,decoded[row['left']],decoded[row['right']],scheme)
                actual=SI.boundary_record(original,decoded[row['left']],decoded[row['right']],scheme)
                for key in ['target_overlap_count','row_overlap_count','run_intersections','n_left','n_right']:
                    assert actual[key]==row[key]
            for role in ['inner0_selection','inner1_selection','outer_test']:
                part=original.iloc[decoded[role]].reset_index(drop=True);members[(dataset,fi,role)]=part
                for group,sub in part.groupby('group_id',sort=True):
                    group_rows.append(dict(dataset=dataset,outer_fold=fi,role=role,group_id=group,
                        monitored_rows=len(sub),asset_days=len(sub)*freq/pd.Timedelta(days=1),
                        first_target=str(sub.target_time.min()),last_target=str(sub.target_time.max()),
                        continuous_segments=len(segments(sub.reset_index(drop=True),freq))))
            # The public ledger keeps every retained role, so the purged holes
            # between adjacent B blocks can be counted on each observed asset.
            # Entire-run purges are represented by run intersections (zero here).
            for left,right in [('B0','B1'),('B1','B2'),('B2','B3'),('final_fit','final_calibration'),('final_calibration','outer_test')]:
                a,b=original.iloc[decoded[left]],original.iloc[decoded[right]]
                shared=sorted(set(a.group_id)&set(b.group_id));count=0
                if scheme!='whole_run_group_blocked':
                    for g in shared:
                        delta=b[b.group_id.eq(g)].origin_time.min()-a[a.group_id.eq(g)].origin_time.max()
                        count+=max(0,int(delta/freq)-1)
                purges.append(dict(dataset=dataset,outer_fold=fi,left=left,right=right,
                    boundary_excluded_origin_slots=count,shared_assets=len(shared),
                    whole_group_boundary=scheme=='whole_run_group_blocked',
                    interpretation='gap in eligible boundary origin slots; acquisition gaps are separately reported'))
    for (dataset,fi,role),part in members.items():
        freq=pd.Timedelta(identities[dataset]['freq']);tables=[]
        row=banks[banks.dataset.eq(dataset)&banks.outer_fold.eq(fi)&banks.role.eq(role)].iloc[0]
        for seed in DESIGN['catalogue_seeds']:
            events=pd.read_csv(run/f'{dataset}_f{fi}_{role}_e{seed}_catalogue.csv.gz',converters={'group_id':str},float_precision='round_trip')
            allocation=allocations[allocations.dataset.eq(dataset)&allocations.outer_fold.eq(fi)&allocations.role.eq(role)&allocations.catalogue_seed.eq(seed)].iloc[0]
            assert len(events)==allocation.requested==math.floor(.5*allocation.asset_days+.5)
            assert int(events.placed.sum())==allocation.placed and int(events.effective.sum())==allocation.effective
            assert int(events.null.sum())==allocation['null'] and int(events.rejected.sum())==allocation.rejected
            assert allocation.placed+allocation.rejected==allocation.requested and allocation.effective+allocation['null']==allocation.placed
            segment_rows={sid:rows for _,sid,rows in segments(part,freq)}
            for event in events[events.placed.astype(bool)].to_dict('records'):
                rows=segment_rows[event['segment_id']];a=int(event['start_index']);b=int(event['end_index'])
                assert a in rows and b in rows and a>rows[0]
                assert str(part.iloc[a].target_time)==event['onset'] and str(part.iloc[b].target_time)==event['end']
                assert pd.Timestamp(event['tolerance_end'])<=part.iloc[rows[-1]].target_time
                assert b-a+1==allocation.duration_steps
                family=event['family'];duration=event['duration_steps'];mask=None
                if family in ('stuck','dropout'):
                    n=math.ceil(duration*{.5:.25,1.:.5,2.:1.}[event['severity']]);start=(duration-n)//2
                    mask=signature([start<=j<start+n for j in range(duration)])
                elif family in ('random_missing','block_missing'):mask=event['mask_hash']
                if mask is not None:aliases.append(dict(dataset=dataset,family=family,severity=event['severity'],
                    duration_steps=duration,mask_hash=mask,scope='relative envelope mask, not independent physical events'))
            for _,sub in events[events.placed.astype(bool)].groupby('segment_id'):
                sub=sub.sort_values('onset');ends=pd.to_datetime(sub.end).tolist();starts=pd.to_datetime(sub.onset).tolist()
                assert all(a+allocation.guard_steps*freq<b for a,b in zip(ends[:-1],starts[1:]))
            tables.append(events)
        recomputed=bank_support(tables)
        expected=strata[strata.dataset.eq(dataset)&strata.outer_fold.eq(fi)&strata.role.eq(role)].reset_index(drop=True)
        pd.testing.assert_frame_equal(recomputed,expected[recomputed.columns],check_dtype=False)
        assert int(recomputed.effective.sum())==row.effective_events and int(recomputed.support.sum())==row.supported_strata
    for r in ranks.to_dict('records'):
        assert r['initial_rank_supported']==rank_support(r['initial_calibration_n'],r['level'],r['method'])['supported']
        assert r['online_rank_supported']==rank_support(r['update_pool_n'],r['level'],r['method'])['supported']
    masks=pd.DataFrame(aliases)
    mask_groups=masks.groupby(['dataset','family','duration_steps','mask_hash'],as_index=False).agg(
        realised_rows=('severity','size'),severity_count=('severity','nunique'),severities=('severity',lambda x:'|'.join(map(str,sorted(set(x))))))
    mask_groups['cross_severity_mask_alias']=mask_groups.severity_count>1
    mask_groups.to_csv(out/'coarse_mask_aliases.csv',index=False)
    pd.DataFrame(group_rows).to_csv(out/'group_exposure.csv',index=False)
    pd.DataFrame(purges).to_csv(out/'boundary_excluded_slots.csv',index=False)
    result=dict(output_valid=True,models_fitted=0,performance_measured=False,membership_roles_checked=len(roles),
        boundaries_checked=len(bounds),catalogues_checked=len(allocations),stratum_cells_checked=len(strata),
        calibration_rank_cells_checked=len(ranks),structurally_supported_banks=int(banks.structural_event_support.sum()),
        source_run=run.name,source_hash=summary['source_hash'],design_hash=summary['design_hash'],
        source_files={p.name:digest(p) for p in sorted(run.iterdir()) if p.is_file()},global_study_ready=False)
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='source_files'},indent=2),flush=True)
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--out',required=True)
    args=ap.parse_args();validate(args.run,args.out)
