"""No-fit C first-run manifest and owner compatibility evidence."""
from common import *
import numpy as np,pandas as pd
from src.context005_spec import VERSION,BASE,FINAL,POLICIES,controls,rules,table,role_rows
from src.context005_data import load_real
from src.context005_features import bounded_frame,inject,causal_features
from src.intervals005_common import Operations,csv

def main():
    with Operations(forbid=True):
        d=load_real('pleia_energy',2);meta=d['meta'];rows=d['roles'];contexts=d['contexts'];schedules=d['schedules']
        old=table(SMART/'protocols/matched_intervals005/pleia_energy_f2_s42_v2/native_membership.csv.gz');old=old[old.horizon==1]
        comparison=[]
        for oldrole,newrole in [('fit','final_fit'),('calibration','final_calibration'),('test','outer_test')]:
            a=set(old[old.role==oldrole].row_id);b=set(meta.iloc[rows[newrole]].row_id)
            comparison.append(dict(role=newrole,matched_rows=len(a),context_rows=len(b),common_rows=len(a&b),matched_only=len(a-b),context_only=len(b-a),exact_row_identity=a==b))
        csv(REVIEW/'owner_role_compatibility.csv',pd.DataFrame(comparison))
        maxdiff=0.
        test=meta.iloc[rows['outer_test']].reset_index(drop=True)
        from src.context005_spec import context_positions
        for ctx in contexts.to_dict('records'):
            ix=context_positions(test,ctx);local=test.iloc[ix].reset_index(drop=True)
            f,s=bounded_frame(d['series'],local,d['fcfg'],d['horizon']);ff,t,o,a=inject(f,local)
            X=causal_features(ff,local,d['horizon'],d['frequency'],s,d['fcfg'],d['X'].columns)
            native=d['X'].iloc[rows['outer_test'][ix]].to_numpy(float)
            # Fixed float64 comparison, no prediction or outer-result tuning.
            delta=float(np.max(abs(X.to_numpy(float)-native)));maxdiff=max(maxdiff,delta)
            np.testing.assert_allclose(X,native,atol=1e-10,rtol=1e-10)
        manifest=dict(version=VERSION,dataset='pleia_energy',outer_fold=2,model_seed=42,horizon=1,synthetic=False,tiny_estimator=False,
            controls=controls('pleia_energy'),rules=rules('pleia_energy'),expected_contexts=68,expected_schedules=2856,
            selection='none',endpoint='C_effective_fault_conditional_context',execution_authorized=False,authorization_kind='proposal_only_no_real_fitting_or_replay')
        atomic(REVIEW/'first_real_run_proposal_manifest.json',manifest)
        csv(REVIEW/'first_run_published_contexts.csv',contexts);csv(REVIEW/'first_run_published_schedules.csv.gz',schedules)
        zero=table(FINAL/'challenge_zero_controls.csv');zero=zero[(zero.dataset=='pleia_energy')&(zero.outer_fold==2)&(zero.role=='outer_test')]
        csv(REVIEW/'first_run_zero_controls.csv',zero)
        atomic(REVIEW/'FIRST_RUN_NO_FIT_READINESS.json',dict(passed=True,execution_authorized=False,rows={k:len(v) for k,v in rows.items()},
            contexts=len(contexts),scheduled_fault_slots=len(schedules),expected_event_channel_rows=len(schedules)*4*5*3,
            clean_context_identities=len(zero),clean_fullstream_rows=len(test),clean_asset_days=len(test)/144,
            unused_challenge_tail_rows=len(test)-len(contexts)*144,role_compatibility=comparison,
            fitted_owner_reuse_permitted=all(x['exact_row_identity'] for x in comparison),required_new_histgradientboosting_fits=3,
            required_new_mapie_fit_wrappers=1,public_conformalize_calls=1,nested_conformalize_calls=2,persistence_radius_computations=1,
            calibration_and_feature_reconstruction_max_abs_difference=maxdiff,models_fitted=0,calibrators_fitted=0,
            source_hash=source_digest(),columns=list(d['X'].columns),cache_sha256=d['cache_sha256'],inputs=d['source_inputs']))
        print('FIRST REAL RUN PROPOSAL READY; NO REAL FITTING OR REPLAY',flush=True)

if __name__=='__main__':main()
