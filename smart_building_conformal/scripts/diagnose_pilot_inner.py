"""Reproduce only frozen development fits; never tune or fit on pilot outer data."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import pickle
import sys
import time
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import torch
from src import model_comparison_pilot as P, pilot_forecasters as F
from src.pilot_resources import require_ram
from src.unit_checkpoint import source_digest

ap=argparse.ArgumentParser();ap.add_argument('--cache',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
protocol_path=Path('protocols/model_comparison_pilot_v1/frozen_protocol.json')
protocol=json.loads(protocol_path.read_text());config=protocol['config']
run=Path('outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913')
# The data loader may change allocation only; model and sequence code must match
# the exact evaluated bytes before any diagnostic fit is allowed.
with zipfile.ZipFile('outputs/model_comparison_pilot_v1/validation/evaluated_source.zip') as z:
    for name in ['attention_lstm.py','pilot_forecasters.py','pilot_data.py','features.py','windowing.py','split_integrity.py']:
        assert Path('src',name).read_bytes()==z.read('src/'+name),name
torch.set_num_threads(1);torch.set_num_interop_threads(1)
require_ram(768*2**20)
with Path(a.cache).open('rb') as f:prepared=pickle.load(f)
scores=[];ranges=[];normalization=[];checks=[]

def metrics(truth,pred):
    error=pred-truth
    return dict(mae=float(np.mean(np.abs(error))),rmse=float(np.sqrt(np.mean(error**2))),
                prediction_minus_truth_bias=float(error.mean()),
                truth_mean=float(truth.mean()),prediction_mean=float(pred.mean()),
                truth_min=float(truth.min()),truth_max=float(truth.max()),
                prediction_min=float(pred.min()),prediction_max=float(pred.max()))

for h in config['horizons']:
    data=P.build_support(prepared,protocol['resolved_dataset_config'],h,24)
    roles=P.pilot_roles(data['meta'],h,prepared.freq)
    P.verify_support(data,roles,protocol['horizons'][str(h)])
    raw=prepared.series[0].frame
    positions=raw.index.get_indexer(pd.DatetimeIndex(data['meta'].origin_time))
    np.testing.assert_array_equal(data['y'],raw.loc[pd.DatetimeIndex(data['meta'].target_time),'target'].to_numpy())
    assert ((data['meta'].target_time-data['meta'].origin_time)==h*prepared.freq).all()
    assert data['meta'].origin_time.is_monotonic_increasing
    assert data['feature_names']==protocol['horizons'][str(h)]['feature_names']
    for start in range(0,len(positions),256):
        rows=np.arange(start,min(start+256,len(positions)))
        seq=data['lazy'].take(data['sequence_rows'][rows])
        expected=raw.target.to_numpy(np.float32)[positions[rows,None]+np.arange(-23,1)]
        np.testing.assert_array_equal(seq[:,:,0],expected)
        np.testing.assert_array_equal(seq[:,-1,0],data['X'].iloc[rows].target_lag_0.to_numpy(np.float32))
    # Independent weighted raw-channel moments equal all overlapping training
    # windows without materialising one complete sequence tensor.
    def moments(rows):
        channel=data['lazy'].channels[0].astype(float)
        multiplicity=np.zeros(len(channel))
        for offset in range(-23,1):np.add.at(multiplicity,positions[rows]+offset,1)
        used=multiplicity>0;xx=channel[used];w=multiplicity[used]
        mean=np.average(xx,axis=0,weights=w)
        std=np.sqrt(np.average((xx-mean)**2,axis=0,weights=w));std[std<1e-12]=1.
        return mean,std
    final=torch.load(run/'units'/f'h{h}_f0_s42_attention_lstm/model.pt',weights_only=True)
    mean,std=moments(roles['fit'])
    np.testing.assert_allclose(final['x_mean'],mean,atol=1e-8,rtol=1e-8)
    np.testing.assert_allclose(final['x_std'],std,atol=1e-7,rtol=1e-7)
    np.testing.assert_allclose(final['y_mean'],data['y'][roles['fit']].mean(),atol=1e-12)
    np.testing.assert_allclose(final['y_std'],data['y'][roles['fit']].std(),atol=1e-12)
    checks.append(dict(horizon=h,all_rows=len(positions),alignment_valid=True,
                       origin_target_shift_valid=True,current_target_available=True,
                       oldest_to_newest_order_valid=True,final_normalization_fit_only=True))
    for fold in [0,1]:
        tr,va=roles[f'inner{fold}_train'],roles[f'inner{fold}_validation']
        for role,rows in [('train',tr),('validation',va)]:
            yy=data['y'][rows]
            ranges.append(dict(horizon=h,inner_fold=fold,role=role,n=len(rows),
                origin_min=str(data['meta'].iloc[rows].origin_time.min()),origin_max=str(data['meta'].iloc[rows].origin_time.max()),
                target_min=float(yy.min()),target_max=float(yy.max()),target_mean=float(yy.mean()),target_std=float(yy.std()),
                fraction_below_train_range=float(np.mean(yy<data['y'][tr].min())),
                fraction_above_train_range=float(np.mean(yy>data['y'][tr].max()))))
        for name in config['models']:
            old=pd.read_csv(run/'units'/f'h{h}_f0_s42_{name}'/'tuning.csv.gz') if name!='persistence' else None
            for c,params in enumerate(config['candidates'][name]):
                folder=out/f'h{h}_{name}_c{c}_inner{fold}';folder.mkdir()
                print(f'DIAGNOSE h{h} {name} candidate {c} inner {fold}',flush=True)
                start=time.perf_counter()
                model=F.fit(name,data,tr,params,42,validation=va,
                            memory_floor=config['minimum_epoch_available_ram_bytes'],
                            progress=lambda row:print(f"  epoch {row['epoch']} MAE {row.get('validation_mae')}",flush=True))
                frames=[];row=dict(horizon=h,inner_fold=fold,model=name,candidate_id=c,seed=42,n_train=len(tr),n_validation=len(va))
                for role,idx in [('train',tr),('validation',va)]:
                    pred=F.predict(model,name,data,idx,256)
                    stats=metrics(data['y'][idx],pred)
                    row.update({role+'_'+k:v for k,v in stats.items()})
                    frame=data['meta'].iloc[idx][['row_id','group_id','origin_time','target_time']].copy()
                    frame['role']=role;frame['truth']=data['y'][idx];frame['prediction']=pred
                    frames.append(frame)
                row['seconds_diagnostic_only']=time.perf_counter()-start
                row['best_epoch']=getattr(model,'best_epoch',None)
                if old is not None:
                    original=old[(old.candidate_id==c)&(old.inner_fold==fold)].iloc[0]
                    row['saved_validation_mae']=float(original.mae)
                    row['mae_difference_from_saved']=row['validation_mae']-float(original.mae)
                    np.testing.assert_allclose(row['validation_mae'],original.mae,rtol=1e-10,atol=1e-10)
                    if name=='attention_lstm':assert row['best_epoch']==int(original.best_epoch)
                if name=='attention_lstm':
                    mean,std=moments(tr)
                    np.testing.assert_allclose(model.mean,mean,atol=1e-8,rtol=1e-8)
                    np.testing.assert_allclose(model.std,std,atol=1e-7,rtol=1e-7)
                    for j,channel in enumerate(data['sequence_channels']):
                        vals=data['lazy'].channels[0][positions[va],j]
                        z=(vals-model.mean[j])/model.std[j]
                        normalization.append(dict(horizon=h,inner_fold=fold,candidate_id=c,channel=channel,
                            train_window_mean=float(model.mean[j]),train_window_std=float(model.std[j]),
                            validation_origin_z_mean=float(z.mean()),validation_origin_z_min=float(z.min()),
                            validation_origin_z_max=float(z.max()),validation_fraction_abs_z_above_5=float(np.mean(np.abs(z)>5))))
                    pd.DataFrame(model.history).to_csv(folder/'history.csv',index=False)
                pd.concat(frames).to_csv(folder/'development_predictions.csv.gz',index=False,compression='gzip')
                scores.append(row)
                pd.DataFrame(scores).to_csv(out/'matched_inner_metrics.csv',index=False)
                pd.DataFrame(ranges).to_csv(out/'development_ranges.csv',index=False)
                pd.DataFrame(normalization).to_csv(out/'normalization.csv',index=False)
                del model;gc.collect()
    del data;gc.collect()
summary=dict(status='complete',new_learned_inner_fits=24,new_outer_or_final_fits=0,
    persistence_supports=6,matched_rows=len(scores),all_saved_inner_maes_and_epochs_reproduced=True,
    checks=checks,source_hash=source_digest(),original_protocol_hash=hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
    scope='Unchanged original candidates, supports, seed and epochs; development diagnostics only. No outer-test retuning.')
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)
