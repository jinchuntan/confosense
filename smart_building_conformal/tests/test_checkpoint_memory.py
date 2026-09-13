import json
import pandas as pd
import pytest
from src.unit_checkpoint import UnitCheckpoint, digest, require_cells
from src.operational004_engine import checkpointed_unit


def test_save_verification_zero_parses_and_resume_one_per_frame(tmp_path, monkeypatch):
    real = pd.read_csv
    calls = []
    def read(*args, **kwargs):
        calls.append(str(args[0]))
        return real(*args, **kwargs)
    monkeypatch.setattr(pd, 'read_csv', read)
    spec = dict(outer_fold=1, model_seed=42, source_hash='original')
    frames = dict(a=pd.DataFrame({'row_id':['001', 'None'], 'x':[1.2345678901234567, float('nan')]}),
                  empty=pd.DataFrame())
    checkpointed_unit(tmp_path, spec, lambda: (dict(fits=0), frames))
    assert calls == []
    def forbidden(): pytest.fail('refitting completed unit')
    payload, got, status = checkpointed_unit(tmp_path, spec, forbidden, resume=True)
    assert len(calls) == 2 and len(set(calls)) == 2
    pd.testing.assert_frame_equal(got['a'], frames['a'])
    assert got['empty'].empty and status['new_fit_invocations'] == 0
    with pytest.raises(ValueError, match='signature mismatch'):
        checkpointed_unit(tmp_path, dict(spec, source_hash='new'), forbidden, resume=True)


@pytest.mark.parametrize('damage', ['payload', 'frame', 'marker', 'provenance', 'unhashed'])
def test_integrity_damage_rejected_without_csv(tmp_path, monkeypatch, damage):
    s=UnitCheckpoint(tmp_path, {'source':'one'})
    s.save('a', {'ok':True}, {'data':pd.DataFrame({'cell':[1]})})
    p=tmp_path/'units/a'; marker=p/'COMPLETE.json'
    if damage in ('payload', 'frame'):
        (p/('payload.json' if damage=='payload' else 'data.csv.gz')).write_bytes(b'damaged')
    elif damage=='marker': marker.unlink()
    else:
        r=json.loads(marker.read_text())
        if damage=='provenance': r['key']='wrong'
        else: del r['hashes']['data.csv.gz']
        marker.write_text(json.dumps(r))
    monkeypatch.setattr(pd, 'read_csv', lambda *a,**k: pytest.fail('integrity parsed CSV'))
    with pytest.raises(ValueError): s.require_complete(['a'])


def test_matrix_and_scientific_cells_remain_checked(tmp_path):
    s=UnitCheckpoint(tmp_path, {})
    assert s.load('absent') is None
    s.save('a', {}, {})
    for keys in (['a','a'], ['a','missing'], []):
        with pytest.raises(ValueError): s.require_complete(keys)
    for frame in (pd.DataFrame({'cell':[1,1]}), pd.DataFrame({'cell':[1]})):
        with pytest.raises(ValueError): require_cells(frame, ['cell'], [(1,),(2,)])
