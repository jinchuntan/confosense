"""Independent real-evidence reconstruction of seed pooling and block inference."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from common import *
from src.operational004_design import STRATA
from src.unit_checkpoint import signature

def frame(path):return pd.read_csv(path,float_precision='round_trip',dtype={'context_id':str,'group_id':str,'original_segment_id':str,'segment_id':str})

def main():
    result=read(ANALYSIS/'validation.json');assert result['passed'] and result['model_seeds']==list(ALL_SEEDS)
    saved=frame(ANALYSIS/'original_context_seed_contributions.csv.gz')
    original=pd.concat([frame(run(s)/'stages/tables/original_context_contributions.csv.gz') for s in ALL_SEEDS],ignore_index=True)
    sort=['model_seed','control_id','rule_id','channel','context_id','family','severity']
    pd.testing.assert_frame_equal(saved.sort_values(sort).reset_index(drop=True),original.sort_values(sort).reset_index(drop=True),check_exact=False,rtol=0,atol=0)
    contexts=frame(SEED42_DESIGN/'contexts.csv').drop_duplicates('context_id').reset_index(drop=True)
    rng=np.random.default_rng(20240601);parts=[]
    groups=[p.sort_values('onset').index.to_numpy() for _,p in contexts.groupby(['outer_fold','segment_id'],sort=True)]
    if any(len(g)<7 for g in groups) or sum(len(g)//7 for g in groups)<5:raise ValueError('independent complete-week support unavailable')
    for g in groups:
        starts=rng.integers(len(g)-6,size=(2000,int(np.ceil(len(g)/7))))
        parts.append(g[(starts[:,:,None]+np.arange(7)).reshape(2000,-1)[:,:len(g)]])
    draws=np.concatenate(parts,axis=1);saved_design=read(ANALYSIS/'bootstrap_design.json')
    if draws.tolist()!=saved_design['draws'] or signature(draws.tolist())!=saved_design['draw_hash']:raise ValueError('draw identity mismatch')
    key=['context_id','control_id','rule_id','channel','family','severity']
    pooled=original.groupby(key,as_index=False).recall.mean();lookup={c:i for i,c in enumerate(contexts.context_id)}
    checks=[];drawrows=[]
    for cell,part in pooled.groupby(['control_id','rule_id','channel'],sort=True):
        a=np.full((len(contexts),21),np.nan)
        for row in part.itertuples():a[lookup[row.context_id],STRATA.index((row.family,row.severity))]=row.recall
        sample=a[draws];counts=np.isfinite(sample).sum(axis=1);means=np.divide(np.nansum(sample,axis=1),counts,out=np.full_like(counts,np.nan,dtype=float),where=counts>0)
        vals=means.mean(axis=1);valid=vals[np.isfinite(vals)];good=len(valid)>=1900 and np.ptp(valid)>0
        point=float(np.nanmean(a,axis=0).mean());lower=float(np.quantile(valid,.025)) if good else np.nan;upper=float(np.quantile(valid,.975)) if good else np.nan
        checks.append(dict(control_id=cell[0],rule_id=cell[1],channel=cell[2],point=point,status='supported' if good else 'unavailable_valid_draw_or_degenerate',valid_draws=len(valid),lower=lower,upper=upper))
        drawrows.extend(dict(control_id=cell[0],rule_id=cell[1],channel=cell[2],draw=i,value=float(v)) for i,v in enumerate(vals))
    checks=pd.DataFrame(checks);saved_bounds=frame(ANALYSIS/'inference_bounds.csv');saved_points=frame(ANALYSIS/'five_seed_control_rule_channel.csv')
    merged=checks.merge(saved_bounds,on=['control_id','rule_id','channel'],suffixes=('_independent','_saved'),validate='one_to_one')
    np.testing.assert_allclose(merged.lower_independent,merged.lower_saved,atol=1e-15,rtol=1e-13,equal_nan=True)
    np.testing.assert_allclose(merged.upper_independent,merged.upper_saved,atol=1e-15,rtol=1e-13,equal_nan=True)
    points=checks.merge(saved_points[['control_id','rule_id','channel','conditional_context_detection']],on=['control_id','rule_id','channel'],validate='one_to_one')
    np.testing.assert_allclose(points.point,points.conditional_context_detection,atol=1e-15,rtol=1e-13)
    saved_draws=frame(ANALYSIS/'bootstrap_draw_estimates.csv.gz').sort_values(['control_id','rule_id','channel','draw']).reset_index(drop=True)
    independent_draws=pd.DataFrame(drawrows).sort_values(['control_id','rule_id','channel','draw']).reset_index(drop=True)
    np.testing.assert_allclose(saved_draws.value,independent_draws.value,atol=1e-15,rtol=1e-13)
    for seed in SEEDS:
        v=read(validation(seed)/'validation.json');r=read(resume(seed));assert v['passed'] and v['actual_exit_status']==0
        assert r['passed'] and r['models_fitted']==r['calibrators_fitted']==r['replay_updates']==0 and r['scientific_artifacts_unchanged']
    csv(ANALYSIS/'independent_inference_checks.csv',checks)
    receipt=dict(passed=True,source_hash=source_digest(),contribution_rows=len(original),original_contexts=len(contexts),model_seeds=list(ALL_SEEDS),
        draw_seed=20240601,draws=2000,draw_shape=list(draws.shape),draw_hash=signature(draws.tolist()),cells=len(checks),
        supported_bounds=int((checks.status=='supported').sum()),unavailable_bounds=int((checks.status!='supported').sum()),
        maximum_absolute_point_difference=float(np.max(np.abs(points.point-points.conditional_context_detection))),
        maximum_absolute_bound_difference=float(np.nanmax(np.r_[np.abs(merged.lower_independent-merged.lower_saved),np.abs(merged.upper_independent-merged.upper_saved)])),
        paired_draws_shared_across_all_controls=True,chronological_adjacent_seven_context_blocks=True,completed_resume_zero_fit_all_new_seeds=True)
    atomic(ANALYSIS/'independent_validation.json',receipt);print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
