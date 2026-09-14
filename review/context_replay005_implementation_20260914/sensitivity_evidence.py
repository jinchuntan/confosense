"""Export the proposed interface's synthetic provenance and denominator example."""
from common import *
import numpy as np,pandas as pd
from src.energy_sensitivity005 import parameters,stratify
from src.intervals005_common import Operations,csv
out=SMART/'outputs/conditional_context005/energy_sensitivity_proposal_v1';out.mkdir(parents=True,exist_ok=False)
with Operations(forbid=True):
    train=np.arange(1,501,dtype=float);ids=['synthetic_fit_'+str(i) for i in range(len(train))]
    spec=parameters(train,ids);csv(out/'synthetic_fitting_values.csv',pd.DataFrame(dict(row_id=ids,value=train)))
    f=pd.DataFrame(dict(row_id=['synthetic_test_'+str(i) for i in range(16)],group_id='original',target_time=pd.date_range('2020',periods=16,freq='10min'),observed=[0]*6+[600,2]+[0]*6+[3,2]))
    before=f.copy();mask,denominator=stratify(f,spec);pd.testing.assert_frame_equal(f,before)
    assert mask.sensitivity_mask.sum()==7 and denominator['retained_n']==9 and mask.primary_keep.all()
    csv(out/'synthetic_observations.csv',f);csv(out/'mask_reason_provenance.csv',mask)
    atomic(out/'proposed_parameters.json',spec);atomic(out/'denominators.json',denominator)
    atomic(out/'validation.json',dict(passed=True,models_fitted=0,primary_unchanged=True,real_masks_applied=0,status='proposal_not_adopted'))
print('PROPOSED SYNTHETIC MASK/REASON/DENOMINATOR EVIDENCE PASSED')
