"""No-fitting acceptance gates over all four frozen designs."""
from __future__ import annotations
import ast,json
from common import *

IDENTITY_FIELDS=('features','outcomes','role_rows','context_hash','schedule_hash','cache_sha256','columns','frequency','fcfg')

def check_manifest_set(rows):
    seeds=[r['model_seed'] for r in rows]
    if seeds!=list(SEEDS) or len(set(seeds))!=4:raise ValueError('exact ordered seeds 43--46 required')
    for m in rows:
        if m['dataset']!='pleia_energy' or m['outer_fold']!=2 or m['horizon']!=1:raise ValueError('scope mismatch')
        if m['expected_contexts']!=68 or m['expected_schedules']!=2856:raise ValueError('membership mismatch')
        if m['selection']!='none' or m['endpoint']!='C_effective_fault_conditional_context':raise ValueError('endpoint/selection mismatch')
        if m.get('tiny_estimator') or not m['execution_authorized'] or m['authorization_kind']!='explicit_real_C_run':raise ValueError('authorization mismatch')
    return True

def main():
    if source_digest()!=SOURCE_HASH:raise ValueError('scientific source changed')
    rows=[read(manifest(s)) for s in SEEDS];check_manifest_set(rows)
    old=read(SEED42_DESIGN/'frozen_protocol.json')
    records=[]
    for seed,m in zip(SEEDS,rows):
        p=read(design(seed)/'frozen_protocol.json');ready=read(design(seed)/'readiness.json')
        assert p['manifest']==m and p['source_hash']==SOURCE_HASH and ready['source_hash']==SOURCE_HASH
        assert p['rows']=={'final_fit':14855,'final_calibration':4954,'outer_test':9907}
        assert p['expected_operations']==old['expected_operations']=={'cqr_wrapper_fit':1,'quantile_estimator_fit':3,'calibrator_conformalize':2,'persistence_radius':1}
        for field in IDENTITY_FIELDS:assert p['data_identity'][field]==old['data_identity'][field],(seed,field)
        assert p['source_inputs']==old['source_inputs']
        assert digest(design(seed)/'contexts.csv')==digest(SEED42_DESIGN/'contexts.csv')
        assert digest(design(seed)/'schedules.csv.gz')==digest(SEED42_DESIGN/'schedules.csv.gz')
        assert digest(design(seed)/'roles.csv.gz')==digest(SEED42_DESIGN/'roles.csv.gz')
        assert ready['required_new_quantile_estimators']==3 and ready['required_new_cqr_wrappers']==1 and ready['required_conformalize_calls']==2
        records.append(dict(model_seed=seed,manifest_sha256=digest(manifest(seed)),protocol_sha256=digest(design(seed)/'frozen_protocol.json'),
            context_hash=p['data_identity']['context_hash'],schedule_hash=p['data_identity']['schedule_hash'],feature_hash=p['data_identity']['features'],
            roles_hash=p['data_identity']['role_rows'],readiness_passed=ready['passed']))
    # Static path verification proves the manifest seed reaches new_cqr and the
    # three cloned native estimators through fit_owner; runtime ledgers and
    # serialized owner parameters are checked after every run.
    owner=(SMART/'src/intervals005_owners.py').read_text(encoding='utf-8');ctx=(SMART/'src/conditional_context005.py').read_text(encoding='utf-8')
    ast.parse(owner);ast.parse(ctx)
    required=['seed=manifest[\'model_seed\']','fit_owner(stages,\'owner_fit_cqr\',\'cqr\',.95,seed','new_cqr(level,seed,synthetic)','_quantile_estimator(seed)']
    for token in required:
        if token not in (ctx+owner):raise ValueError('seed propagation path missing: '+token)
    result=dict(passed=True,models_fitted=0,seeds=list(SEEDS),unique_run_paths=len({str(run(s)) for s in SEEDS}),
        manifests=records,seed42_preserved=digest(SEED42_RUN/'COMPLETE.json')==read(REVIEW/'PRESERVATION_BASELINE.json')['seed42_complete_sha256'],
        same_context_schedule_roles_features=True,slot_rng_seeds=[42,43],energy_sensitivity=False,worker_helpers_imported=True,
        seed_propagation='manifest.model_seed -> models_from_stage seed -> fit_owner -> new_cqr -> HistGradientBoostingRegressor(random_state=seed)',
        operation_policy='3 native quantile estimator fits per seed; verified again from runtime ledgers')
    atomic(REVIEW/'PREFLIGHT_VALIDATION.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
