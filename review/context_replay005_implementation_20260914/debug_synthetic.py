import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
from common import *
from src.context005_data import synthetic
from src.context005_features import *
from src.context005_spec import context_positions
from src.intervals005_common import Operations
from src.intervals005_owners import new_cqr,quantile_raw
with Operations(REVIEW/'synthetic_debug_operations.jsonl',stage='predictor_path_diagnosis',synthetic=True):
    d=synthetic('pleia_energy');r=d['roles'];o=new_cqr(.95,42,True);o.fit(d['X'].iloc[r['final_fit']].to_numpy(),d['y'][r['final_fit']]);o.conformalize(d['X'].iloc[r['final_calibration']].to_numpy(),d['y'][r['final_calibration']])
    m=d['meta'].iloc[r['outer_test']].reset_index(drop=True);ctx=d['contexts'].iloc[0].to_dict();m=m.iloc[context_positions(m,ctx)].reset_index(drop=True)
    base,season=bounded_frame(d['series'],m,d['fcfg'],d['horizon']);out=[]
    for e in [None]+d['schedules'][(d['schedules'].context_id==ctx['context_id'])&(d['schedules'].family=='level_shift')&(d['schedules'].severity==2)].to_dict('records'):
        f,t,y,a=inject(base,m,e);X=causal_features(f,m,d['horizon'],d['frequency'],season,d['fcfg'],d['X'].columns)
        pred=quantile_raw(o,X.to_numpy());out.append(dict(event=e,features=X.iloc[38:46].to_dict('list'),point=pred['point'][38:46].tolist(),all_point_min=float(pred['point'].min()),all_point_max=float(pred['point'].max())))
    est=o._mapie_quantile_regressor.estimators_[2]
    nodes=[p[0].nodes.tolist() for p in est._predictors]
    atomic(REVIEW/'SYNTHETIC_PREDICTOR_DIAGNOSTIC.json',dict(variants=out,median_tree_nodes=nodes,feature_columns=d['X'].columns.tolist()))
    print([(x['event']['sign'] if x['event'] else 0,x['point'],x['features']['target_lag_0']) for x in out],flush=True)
    print([(d['X'].columns[int(node[2])],node[3]) for nodeset in nodes for node in nodeset if not node[9]],flush=True)
