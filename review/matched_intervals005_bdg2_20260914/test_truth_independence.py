"""No-fit held-out-truth perturbation through the actual joint-input assembly."""
from common import *
import pickle
import numpy as np
import pandas as pd
from src.intervals005_common import Operations, Stages, load_owner
from src.intervals005_data import joint_join


def test_saved_dscp_joint_assignment_and_bounds_ignore_heldout_truth():
    saved=SMART/'outputs/matched_intervals005/synthetic_v1/run'
    before=tree(saved)
    frames={}
    for h in (1,3):
        f=pd.read_csv(saved/f'stages/stream_h{h}_l90_recentred_enbpi_static/issued.csv.gz').rename(columns={'observed':'y_true'})
        for column in ('origin_time','target_time'):
            f[column]=pd.to_datetime(f[column])
        frames[h]=f[['row_id','group_id','origin_time','target_time','y_true','point']].copy()
    changed={h:f.assign(y_true=-1e9-np.arange(len(f))) for h,f in frames.items()}
    with Operations(forbid=True):
        store=Stages(saved,read(saved/'checkpoint_manifest.json')['spec'],resume=True)
        model=load_owner(store.get('dscp_fit')/'calibrator.pkl')
        state_before=pickle.dumps(model,protocol=5)
        clean=joint_join(frames,[1,3],frequency=pd.Timedelta(minutes=10))
        perturbed=joint_join(changed,[1,3],frequency=pd.Timedelta(minutes=10))
        assert not np.array_equal(clean[1].y_true,perturbed[1].y_true)
        predictors=np.column_stack([clean[h].point for h in (1,3)])
        altered_predictors=np.column_stack([perturbed[h].point for h in (1,3)])
        np.testing.assert_array_equal(predictors,altered_predictors)
        assignment=model.assign(predictors)
        changed_assignment=model.assign(altered_predictors)
        np.testing.assert_array_equal(assignment,changed_assignment)
        for level in (.9,.95):
            original=model.predict_interval(predictors,level,assignments=assignment)
            altered=model.predict_interval(altered_predictors,level,assignments=changed_assignment)
            for name in ('lower','upper','cluster'):
                np.testing.assert_array_equal(original[name],altered[name])
        assert pickle.dumps(model,protocol=5)==state_before
    assert tree(saved)==before
