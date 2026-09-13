"""Recalculate proposed corruptions from public rows; verify memberships and counts."""
import argparse, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from support_design005 import ROOT, STRATA, signature, digest, no_fitting, source_digest, seed_for, SI

def independent_fault(values,family,severity,sigma,sign,seed,predecessor):
    result=values.copy();flag=np.ones(len(values),bool);n=len(values)
    length=math.ceil(n*{.5:.25,1.:.5,2.:1.}[severity]);start=(n-length)//2
    if family=='random_missing':flag=np.random.default_rng(seed).random(n)>=.2*severity
    elif family=='block_missing':flag[start:start+length]=False
    elif family=='stuck':result[start:start+length]=predecessor if start==0 else result[start-1]
    elif family=='dropout':result[start:start+length]=0.
    else:
        u=np.linspace(0,1,n)
        shape=np.minimum(np.minimum(4*u,1),4*(1-u)) if family=='bias' else u if family=='drift' else np.ones(n)
        result+=sign*severity*sigma*shape
    result[~flag]=np.nan
    return result,flag

def verify(base,out):
    base=Path(base);spec=json.loads((base/'proposal_spec.json').read_text());contexts=pd.read_csv(base/'challenge_contexts.csv',keep_default_na=False,float_precision='round_trip')
    events=pd.read_csv(base/'challenge_schedules.csv.gz',keep_default_na=False,float_precision='round_trip',dtype={'mask_seed':str})
    support=pd.read_csv(base/'challenge_support.csv');boundaries=[];checked=0
    for ds in ['pleia','pleia_energy','rico']:
        m=pd.read_csv(base/f'{ds}_operational_membership_observations.csv.gz',keep_default_na=False,float_precision='round_trip',dtype={'group_id':str})
        m.origin_time=pd.to_datetime(m.origin_time);m.target_time=pd.to_datetime(m.target_time)
        assert m.row_id.is_unique;position={r:i for i,r in enumerate(m.row_id)};y=m.y.to_numpy()
        scales={}
        for fi in range(3):
            labels=m[f'fold{fi}_roles'].str.split('|');roles={r:np.flatnonzero(labels.apply(lambda x:r in x)) for r in ['inner0_train','inner0_calibration','inner0_selection','inner1_train','inner1_calibration','inner1_selection','final_fit','final_calibration','outer_test']}
            for role,train in [('inner0_selection','inner0_train'),('inner1_selection','inner1_train'),('outer_test','final_fit')]:
                scales[(fi,role)]=SI.training_scale(y,m,roles[train])
            for a,b in [('inner0_train','inner0_calibration'),('inner0_calibration','inner0_selection'),('inner1_train','inner1_calibration'),('inner1_calibration','inner1_selection'),('final_fit','final_calibration'),('final_calibration','outer_test')]:
                left,right=m.iloc[roles[a]],m.iloc[roles[b]]
                assert left.target_time.max()<right.origin_time.min() and not set(left.row_id)&set(right.row_id)
                intersections=len(set(left.group_id)&set(right.group_id)) if ds=='rico' else 0
                assert intersections==0
                boundaries.append(dict(dataset=ds,outer_fold=fi,left=a,right=b,run_intersections=intersections,passed=True))
        for c in contexts[contexts.dataset==ds].to_dict('records'):
            start,end=position[c['context_start_row_id']],position[c['context_end_row_id']]
            rr=np.arange(start,end+1);block=m.iloc[rr]
            assert len(rr)==c['context_rows'] and block.group_id.nunique()==1
            dt=pd.Timedelta('1min' if ds=='rico' else '10min')
            assert block.target_time.diff().dropna().eq(dt).all()
            assert signature(block.row_id.tolist())==c['context_row_hash']
            first=position[c['onset_row_id']];duration=int(c['duration']);pick=np.arange(first,first+duration)
            assert first-start>=c['warmup'] and end-pick[-1]>=c['followup']
            expected_offset=np.random.default_rng(seed_for('amendment005',spec['context_seed'],c['context_id'])).integers(c['warmup'],len(rr)-duration-c['followup']+1)
            assert first-start==expected_offset
            scale=scales[(c['outer_fold'],c['role'])]
            assert c['sigma']==scale.get(c['group_id'],scale['__pooled__'])
            variants=events[events.context_id==c['context_id']]
            assert set(zip(variants.family,variants.severity,variants.replicate))=={(f,s,r) for f,s in STRATA for r in spec['challenge_replicates']}
            for e in events[events.context_id==c['context_id']].to_dict('records'):
                assert e['end_row_id']==m.iloc[pick[-1]].row_id
                result,flag=independent_fault(y[pick],e['family'],e['severity'],e['sigma'],e['sign'],int(e['mask_seed']),y[first-1])
                effective=bool((~flag).any() or np.any(result[flag]!=y[pick][flag]))
                assert effective==e['effective'] and (not effective)==e['null']
                assert signature(flag.tolist())==e['mask_hash']
                assert signature(np.nan_to_num(result,nan=-1.23456789e307).tolist())==e['observed_hash']
                checked+=1
    for keys,part in events.groupby(['dataset','outer_fold','role','family','severity']):
        saved=support
        for k,v in zip(['dataset','outer_fold','role','family','severity'],keys):saved=saved[saved[k]==v]
        saved=saved.iloc[0];eff=part[part.effective]
        distinct=len(eff[['group_id','onset']].drop_duplicates());units=eff.group_id.nunique() if keys[0]=='rico' else eff.context_id.nunique()
        assert len(part)==saved.requested and len(eff)==saved.effective and distinct==saved.distinct_effective_onsets
        assert (distinct>=5 and units>=5)==saved.supported
        assert len(part)==2*part.context_id.nunique()
    forecast_boundaries=0
    for file in base.glob('*_forecast_membership.csv.gz'):
        fm=pd.read_csv(file,keep_default_na=False)
        fm.origin_time=pd.to_datetime(fm.origin_time);fm.target_time=pd.to_datetime(fm.target_time)
        for fi in range(3):
            labels=fm[f'fold{fi}_roles'].str.split('|')
            for a,b in [('fit','calibration'),('calibration','test'),('inner0_train','inner0_validation'),('inner1_train','inner1_validation')]:
                left=fm[labels.apply(lambda x:a in x)];right=fm[labels.apply(lambda x:b in x)]
                assert left.target_time.max()<right.origin_time.min() and not set(left.row_id)&set(right.row_id)
                if file.name.startswith('rico_'):assert not set(left.group_id)&set(right.group_id)
                forecast_boundaries+=1
    fc=pd.read_csv(base/'experiment_matrix.csv');assert not fc.duplicated(['dataset','horizon','outer_fold','model_seed','model','level']).any()
    assert len(fc[['dataset','horizon']].drop_duplicates())==13
    assert len(fc)==13*3*5*4*2 and len(fc[fc.status=='completed_reusable'])==18
    original=json.loads((base/'entry_preservation.json').read_text())
    for r in original['files']:assert digest(ROOT/r['path'])==r['sha256'],r['path']
    assert source_digest()==json.loads((base/'validation.json').read_text())['source_hash']
    result=dict(passed=True,models_fitted=0,schedule_variants_recomputed=checked,contexts_verified=len(contexts),
        role_boundaries_verified=len(boundaries),forecast_boundaries_verified=forecast_boundaries,all_complete_stratum_banks_checked=True,
        forecast_level_cells=len(fc),reusable_pilot_level_cells=18,preserved_files=len(original['files']),
        production_source_unchanged=True,full_study_ready=False,publication_ready=False)
    Path(out).mkdir(parents=True,exist_ok=False);pd.DataFrame(boundaries).to_csv(Path(out)/'boundaries.csv',index=False)
    (Path(out)/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    with no_fitting():verify(a.base,a.out)
