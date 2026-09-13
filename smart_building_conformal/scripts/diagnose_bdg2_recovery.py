"""No-fit numeric diagnosis of convolution versus frozen binary rolling means."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import independent_bdg2_operational_audit as audit


def main(run,out):
    run=Path(run);out=Path(out)
    if out.exists():raise FileExistsError(out)
    spec=json.loads((run/'checkpoint_manifest.json').read_text())['spec'];fold=spec['outer_fold']
    unit=run/f'units/outer{fold}_model42';before={p.name:audit.sha(p) for p in unit.iterdir()}
    catalogue=audit.read(unit/'outer_catalogues.csv.gz');saved=audit.read(unit/'outer_recovery.csv.gz')
    differences=[];checked=0;records=[]
    for (role,cid),frame in audit.ordered_blocks(unit/'outer_streams.csv.gz',['role','candidate_id']):
        clean=frame[frame.catalogue_seed==-1].reset_index(drop=True)
        for seed in [42,43,44,45,46]:
            stream=frame[frame.catalogue_seed==seed].reset_index(drop=True)
            events=catalogue[catalogue.catalogue_seed==seed]
            for group,part in stream.groupby('group_id',sort=True):
                fs=events[(events.group_id==group)&events.effective]
                if not len(fs):continue
                end=pd.to_datetime(fs.end).max();start=pd.to_datetime(fs.onset).min()
                times=pd.to_datetime(part.target_time);pre=times<start;post=times>end
                assert pre.any() and post.any()
                truth=clean.observed.to_numpy()[part.index]
                cover=(truth>=part.lower)&(truth<=part.upper)
                baseline=float(cover[pre].mean());window=max(1,min(24,int(post.sum())//4))
                tail=cover[post].to_numpy(bool);cumulative=np.r_[0,np.cumsum(tail,dtype=np.int64)]
                integer=(cumulative[window:]-cumulative[:-window])/window
                rolling=pd.Series(tail.astype(float)).rolling(window,min_periods=window).mean().to_numpy()[window-1:]
                np.testing.assert_array_equal(integer,rolling)
                convolution=np.convolve(tail,np.ones(window)/window,mode='valid')
                correct=np.flatnonzero(abs(integer-baseline)<=.05)
                previous=np.flatnonzero(abs(convolution-baseline)<=.05)
                status='observed' if len(correct) else 'right_censored'
                at=(times[post].iloc[correct[0]+window-1]-end).total_seconds()/60 if len(correct) else np.nan
                old=saved[(saved.candidate_id==cid)&(saved.catalogue_seed==seed)&(saved.group_id==group)].iloc[0]
                assert status==old.status
                np.testing.assert_allclose(at,old.recovery_minutes,rtol=0,atol=0,equal_nan=True)
                checked+=1
                changed=np.flatnonzero((abs(integer-baseline)<=.05)!=(abs(convolution-baseline)<=.05))
                if len(changed):
                    i=int(changed[0]);differences.append(dict(candidate_id=cid,catalogue_seed=seed,group_id=group,
                        window=window,baseline=baseline,baseline_hex=baseline.hex(),
                        convolution_mean=float(convolution[i]),integer_mean=float(integer[i]),
                        convolution_distance=float(abs(convolution[i]-baseline)),integer_distance=float(abs(integer[i]-baseline)),
                        frozen_threshold=.05,convolution_status='observed' if len(previous) else 'right_censored',saved_and_integer_status=status,
                        changed_window_decisions=len(changed)))
    after={p.name:audit.sha(p) for p in unit.iterdir()};assert before==after and differences
    result=dict(passed=True,learned_fits=0,source_or_threshold_changed=False,production_results_changed=False,
        diagnosis='Independent audit convolution kernel rounding differs at the frozen floating-point inclusive .05 boundary; integer binary counts divided by window exactly match compensated pandas rolling means and every saved recovery record.',
        outer_recovery_records_checked=checked,unit_files_byte_identical=len(before),differences=differences,
        source_sha256=audit.sha(__file__),unit_hashes=before)
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='unit_hashes'},indent=2))


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
