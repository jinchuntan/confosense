"""Bounded no-fit regression checks for the review batch and aggregation gates."""
import importlib.util,sys
from pathlib import Path
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[2]
REVIEW=ROOT/'review/pleia_energy_context005_multiseed_20260915'
sys.path.insert(0,str(REVIEW))
spec=importlib.util.spec_from_file_location('multiseed_preflight',REVIEW/'preflight.py')
pre=importlib.util.module_from_spec(spec);spec.loader.exec_module(pre)

def manifest(seed):
    return dict(model_seed=seed,dataset='pleia_energy',outer_fold=2,horizon=1,expected_contexts=68,expected_schedules=2856,
        selection='none',endpoint='C_effective_fault_conditional_context',tiny_estimator=False,execution_authorized=True,authorization_kind='explicit_real_C_run')

def test_exact_seed_scope_and_manifest_guards():
    assert pre.check_manifest_set([manifest(s) for s in range(43,47)])
    bad=[manifest(s) for s in [43,44,44,46]]
    with pytest.raises(ValueError,match='seeds'):pre.check_manifest_set(bad)
    bad=[manifest(s) for s in range(43,47)];bad[0]['endpoint']='changed'
    with pytest.raises(ValueError,match='endpoint'):pre.check_manifest_set(bad)

def test_aggregate_key_gate_rejects_duplicate_missing_and_support_mismatch():
    spec=importlib.util.spec_from_file_location('multiseed_analyze',REVIEW/'analyze.py')
    analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)
    validate_contribution_keys=analysis.validate_contribution_keys
    base=[]
    for seed in range(42,47):
        for context in ['a','b']:
            base.append(dict(dataset='pleia_energy',outer_fold=2,model_seed=seed,control_id='c',rule_id='r',channel='combined',
                context_id=context,original_segment_id='s',group_id='g',family='spike',severity=1,recall=.5,restricted_delay=10,effective_slots=2))
    frame=pd.DataFrame(base);assert validate_contribution_keys(frame,expected_seeds=tuple(range(42,47)))['passed']
    with pytest.raises(ValueError,match='duplicate'):validate_contribution_keys(pd.concat([frame,frame.iloc[:1]]),expected_seeds=tuple(range(42,47)))
    with pytest.raises(ValueError,match='seed completeness'):validate_contribution_keys(frame.iloc[:-1],expected_seeds=tuple(range(42,47)))
    changed=frame.copy();changed.loc[changed.model_seed==46,'effective_slots']=1
    with pytest.raises(ValueError,match='support mismatch'):validate_contribution_keys(changed,expected_seeds=tuple(range(42,47)))

def test_macro_pooling_retains_nullable_group_id():
    spec=importlib.util.spec_from_file_location('multiseed_analyze_nullable_group',REVIEW/'analyze.py')
    analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)
    rows=[]
    for family,severity in [('spike',1),('bias',1)]:
        rows.append(dict(dataset='pleia_energy',outer_fold=2,model_seed=42,control_id='c',rule_id='r',channel='combined',
            context_id='a',original_segment_id='s',group_id=pd.NA,family=family,severity=severity,recall=.5,restricted_delay=10,effective_slots=2))
    _,_,macro=analysis.macro_from_contributions(pd.DataFrame(rows))
    assert list(macro[['control_id','rule_id','channel']].iloc[0])==['c','r','combined']
