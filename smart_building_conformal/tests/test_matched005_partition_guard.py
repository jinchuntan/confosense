"""The metadata partition exception must not permit learned fitting."""
from types import SimpleNamespace
import pandas as pd
import pytest
from src.datasets.base import GroupPartitioner
from src.matched_models005 import forbid_fitting


def test_metadata_partition_is_allowed_and_unchanged():
    series=[SimpleNamespace(group_id=f'run{i}',start=pd.Timestamp('2023-01-01')+pd.Timedelta(days=i)) for i in range(10)]
    expected=GroupPartitioner().fit(series).assignment
    with forbid_fitting() as calls:
        actual=GroupPartitioner().fit(list(reversed(series))).assignment
    assert actual==expected and not calls
    assert list(actual.values())==['train']*6+['calibration']*2+['test']*2


@pytest.mark.parametrize('module,name', [('src.datasets.base','fit'),('src.pilot_forecasters','fit'),
    ('xgboost.training','train'),('sklearn.ensemble','fit'),('src.matched_models005','run_model')])
def test_same_name_or_learned_route_is_still_blocked(module,name):
    entered=[];scope={'__name__':module,'entered':entered}
    exec(f'def {name}():\n entered.append(True)',scope)
    with pytest.raises(AssertionError,match='fitting forbidden'):
        with forbid_fitting():scope[name]()
    assert not entered
