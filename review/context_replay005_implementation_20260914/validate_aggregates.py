"""Read-only independent diagnostics, aggregate denominators and input/stream hashes."""
import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[name]='1'
from common import *
import numpy as np,pandas as pd
from src.context005_spec import table
from src.intervals005_common import Operations,csv

def main(version):
    out=SMART/'outputs/conditional_context005/aggregate_validation_v2'
    out.mkdir(parents=True,exist_ok=False);checks=[];hashes=[]
    def check(label,actual,expected):
        actual=np.asarray(actual,object);actual[actual=='']=np.nan
        np.testing.assert_allclose(np.asarray(actual,float),expected,atol=1e-10,rtol=1e-10,equal_nan=True)
        checks.append(dict(check=label,passed=True))
    with Operations(forbid=True):
        for ds in ['pleia_energy','rico']:
            root=SMART/f'outputs/conditional_context005/synthetic_{ds}_{version}';before=tree(root)
            v=table(root/'stages/tables/variants.csv');events=table(root/'stages/tables/events.csv.gz');strata=table(root/'stages/tables/strata.csv')
            events['delay_minutes']=pd.to_numeric(events.delay_minutes.replace('',np.nan),errors='raise')
            for stage in sorted(set(v.canonical_stage)|{p.name for p in (root/'stages').glob('fullstream_*')}):
                path=root/'stages'/stage;ident=read(path/'identity.json');obs=table(path/'observations.csv.gz');diag=table(path/'interval_diagnostics.csv')
                assert signature(obs.row_id.tolist())==ident['row_hash']
                assert signature(obs.available.tolist())==ident['availability_hash']
                for cid in ['quantile_static','cqr_static','cqr_rolling','persistence_static']:
                    stream=table(path/(cid+'_issued.csv.gz'))
                    assert stream.row_id.tolist()==obs.row_id.tolist()
                    for target in ['clean_counterfactual','corrupted_observation']:
                        mask=np.ones(len(obs),bool) if target=='clean_counterfactual' else obs.available.to_numpy(bool)
                        y=pd.to_numeric(obs.truth if target=='clean_counterfactual' else obs.observed.replace('',np.nan)).to_numpy()[mask]
                        lo=stream.lower.to_numpy()[mask];hi=stream.upper.to_numpy()[mask];width=hi-lo
                        row=diag[(diag.control_id==cid)&(diag.target==target)].iloc[0]
                        expected=[mask.sum(),(~mask).sum(),((lo<=y)&(y<=hi)).mean(),width.mean(),np.mean(width+40*np.maximum(lo-y,0)+40*np.maximum(y-hi,0))]
                        check(ds+'/'+stage+'/'+cid+'/'+target,row[['n','unavailable_n','coverage','mpiw','winkler']].to_numpy(float),expected)
                    for flags_path in path.glob(cid+'_*_alerts.csv.gz'):
                        consumed=table(flags_path);assert consumed.row_id.tolist()==stream.row_id.tolist()
                        hashes.append(dict(dataset=ds,stage=stage,control_id=cid,rule_flags=flags_path.name,issued_file_sha256=sha(path/(cid+'_issued.csv.gz')),consumed_flags_sha256=sha(flags_path),issued_row_hash=signature(stream.row_id.tolist()),consumed_row_hash=signature(consumed.row_id.tolist()),feature_hash=ident['feature_hash'],observation_hash=ident['observation_hash']))
            for row in strata.to_dict('records'):
                f=events[(events.control_id==row['control_id'])&(events.rule_id==row['rule_id'])&(events.channel==row['channel'])&(events.family==row['family'])&(events.severity==row['severity'])]
                pos=f[f.effective&f.eligible];found=pos[pos.detected]
                cm=pos.groupby('context_id').agg(recall=('detected','mean'),delay=('restricted_delay_minutes','mean'))
                expected=[len(f),f.effective.sum(),f['null'].sum(),f.alias.sum(),len(cm),int(len(cm)>=5),(~pos.detected).sum(),pos.detected.sum(),cm.recall.mean(),cm.delay.mean(),found.delay_minutes.median(),found.delay_minutes.quantile(.9)]
                cols=['scheduled','effective','null','aliases','effective_contexts','supported','misses','detected','recall','restricted_mean_detection_minutes','detected_delay_median','detected_delay_q90']
                check(ds+'/stratum/'+str(len(checks)),[row[c] for c in cols],expected)
            macro=table(root/'stages/tables/conditional_macro.csv')
            for row in macro.to_dict('records'):
                ss=strata[(strata.control_id==row['control_id'])&(strata.rule_id==row['rule_id'])&(strata.channel==row['channel'])]
                supported=len(ss)==21 and ss.supported.all()
                value=row['conditional_context_macro'];value=np.nan if value=='' else value
                check(ds+'/macro',value,ss.recall.mean() if supported else np.nan)
                assert row['status']==('supported_point_estimate' if supported else 'unavailable_missing_distinct_context_support')
            assert tree(root)==before
    csv(out/'independent_checks.csv',pd.DataFrame(checks));csv(out/'issued_consumed_hash_crosswalk.csv.gz',pd.DataFrame(hashes))
    atomic(out/'validation.json',dict(passed=True,checks=len(checks),issued_consumed_pairs=len(hashes),models_fitted=0,calibrators_fitted=0,scientific_artifacts_unchanged=True))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--version',default='v1');main(p.parse_args().version)
