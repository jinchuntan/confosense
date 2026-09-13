"""No-fitting reproduction of the observed BDG2 flag-type failure and fix."""
import json
import pickle
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from src.operational004_stream import corrupted_features
from src.operational004_design import make_outer_folds,nested_roles
from src.operational004_events import catalogue
from src import split_integrity as SI

out=Path(sys.argv[1])
if out.exists(): raise FileExistsError(out)
cache=Path('C:/Users/nigel/ConfoSenseBackups/amendment004_20260913/preflight_v1/bdg2_prepared.pkl')
with cache.open('rb') as f: d=pickle.load(f)
s,w,cfg,fc=d['segmented'],d['w'],d['cfg'],d['fcfg']
fold=make_outer_folds(w['meta'],'chronological',3,1,s.freq)[2]
roles=nested_roles(w['meta'],fold,'chronological');ix=roles['inner0_selection'];meta=w['meta'].iloc[ix].reset_index(drop=True)
scales=SI.training_scale(w['y'],w['meta'],roles['inner0_train'])
obs,flags,cat,_=catalogue(w['y'][ix],meta,s.freq,scales,'bdg2','inner0_selection',2,42)
old=subprocess.check_output(['git','show','cdc5362:smart_building_conformal/src/operational004_stream.py'],text=True)
ns={'__package__':'src'};exec(compile(old,'preserved_v1_stream.py','exec'),ns)
try: ns['corrupted_features'](s,meta,obs,flags,1,fc,list(w['X']))
except TypeError as exc: reproduced=str(exc)
else: raise AssertionError('original TypeError did not reproduce')
# Numeric view solely for checking values; this is not used by the pilot.
ns2={'__package__':'src'}
exec(compile(old.replace('np.isfinite(X.to_numpy())','np.isfinite(X.to_numpy(dtype=float))'),'numeric_view_only.py','exec'),ns2)
counterfactual=ns2['corrupted_features'](s,meta,obs,flags,1,fc,list(w['X']))
fixed=corrupted_features(s,meta,obs,flags,1,fc,list(w['X']))
np.testing.assert_array_equal(fixed.to_numpy(),counterfactual.to_numpy(float))
clean=corrupted_features(s,meta,w['y'][ix],np.ones(len(ix),bool),1,fc,list(w['X']))
np.testing.assert_array_equal(clean.to_numpy(),w['X'].iloc[ix].to_numpy(float))
record=dict(passed=True,learned_fits=0,scope='BDG2 inner0 seed42 no-fitting data-type regression',
    rows=len(ix),features=len(fixed.columns),groups=meta.group_id.nunique(),
    original_error=reproduced,old_matrix_dtype=str(counterfactual.to_numpy().dtype),
    fixed_matrix_dtype=str(fixed.to_numpy().dtype),numeric_values_identical=True,
    zero_corruption_feature_identity=True,data_hash=w['data_hash'],
    changed_settings=[],failed_run='bdg2_operational_pilot_f2_s42_v1')
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
