"""No-fit seed-path probes and checks of actual fitted artifact metadata."""
import inspect, sys
from common import *
sys.path.insert(0,str(SMART))
from src import pilot_forecasters as F
from src import matched_models005 as M
from src.attention_lstm import set_determinism
import numpy as np
import torch

def preflight():
    # These assertions bind the exact reviewed dispatch and RNG paths. They are
    # complemented by actual per-fit records and serialized seeds after each unit.
    checks={'model_seed_dispatch':"seed, batch = config['model_seed']" in inspect.getsource(M.run_model),
            'dispatch_passes_seed':'F.fit(name, data, rows, params, seed' in inspect.getsource(M.run_model),
            'xgb_constructor':'random_state=seed,n_jobs=1' in inspect.getsource(F.fit),
            'lstm_dispatch':'LazyLSTM().fit(data,train,params,seed' in inspect.getsource(F.fit),
            'lstm_initialization':'set_determinism(seed)' in inspect.getsource(F.LazyLSTM.fit),
            'shuffle_generator':'torch.Generator().manual_seed(seed)' in inspect.getsource(F.LazyLSTM.fit),
            'shuffle_uses_generator':'torch.randperm(len(train_rows), generator=generator)' in inspect.getsource(F.LazyLSTM.fit)}
    assert all(checks.values()),checks
    rows=[]
    for seed in [42,43,44,45,46]:
        set_determinism(seed)
        actual_np=int(np.random.get_state()[1][0]);actual_torch=int(torch.initial_seed())
        generator=torch.Generator().manual_seed(seed)
        assert actual_np==actual_torch==generator.initial_seed()==seed
        rows.append(dict(requested_seed=seed,numpy_seed=actual_np,torch_seed=actual_torch,shuffle_generator_seed=generator.initial_seed(),numpy_probe=np.random.random(3).tolist(),torch_probe=torch.rand(3).tolist(),shuffle_probe=torch.randperm(10,generator=generator).tolist()))
    return dict(passed=True,models_fitted=0,source_paths=checks,rng_probes=rows,predictions_required_to_differ=False)

def unit(unit):
    key=unit['key'];seed=key[3];run=Path(unit['run']);rows=[]
    journal=[json.loads(line) for line in (run/'fit_calls.jsonl').read_text().splitlines()]
    assert len([r for r in journal if r['event']=='complete'])==10
    assert all(r['seed']==seed and f'_s{seed}_' in r['unit'] for r in journal)
    for model in MODELS:
        directory=run/'units'/f'{key[0]}_h{key[1]}_f{key[2]}_s{seed}_{model}'
        p=read(directory/'payload.json');assert p['model_seed']==seed
        result=dict(zip(KEYCOLS,key),model=model,estimator_class=p['point']['estimator_class'],payload_seed=p['model_seed'],fit_record_seeds=sorted(set(r['seed'] for r in p['fitting_records'])),source_hash=unit['source_hash'],protocol_hash=unit['protocol_hash'],source_run=run.relative_to(ROOT).as_posix(),passed=True)
        if model=='xgboost':
            actual=p['actual_parameters']['random_state'];booster=read(directory/'booster_config.json')['learner']['generic_param']
            assert actual==int(booster['seed'])==int(booster['random_state'])==seed
            result.update(actual_wrapper_random_state=actual,actual_booster_seed=int(booster['seed']),actual_n_jobs=int(booster['n_jobs']))
        elif model=='attention_lstm':
            state=torch.load(directory/'model.pt',map_location='cpu',weights_only=True)
            assert state['seed']==seed and all(r['seed']==seed for r in p['fitting_records'])
            result.update(serialized_training_seed=state['seed'],rng_paths='verified unchanged set_determinism NumPy/Torch and torch.Generator manual_seed path; actual fit and artifact seeds match')
        else:
            assert p['learned_fits']==0 and not p['fitting_records']
            result.update(seed_variability='deterministic baseline alias on identical targets; not an independent replicate')
        rows.append(result)
    return rows
