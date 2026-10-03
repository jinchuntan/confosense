"""Guard tests for the high-coverage extension (no fitting, no real replay).

Run from the science-root frozen directory with the scientific interpreter:
    C:\\cfs_venv\\Scripts\\python.exe -B <extension>/test_hc_guards.py
"""
from __future__ import annotations

from hc_common import single_thread_environment

single_thread_environment()

import hashlib  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from hc_common import FROZEN, LEVELS, level_tag  # noqa: E402

sys.path.insert(0, str(FROZEN))
import adapter  # noqa: E402,F401  (frozen; puts the science-root src on sys.path)
import hc_adapter  # noqa: E402
import hc_validate  # noqa: E402
from src.operational004_design import rank_support  # noqa: E402
from src.operational004_stream import replay, score_quantiles  # noqa: E402


def test_level_tags():
    assert [level_tag(level) for level in LEVELS] == ["l0975", "l0990", "l0995"]
    for bad in (0.95, 0.9):
        try:
            level_tag(bad)
        except ValueError:
            continue
        raise AssertionError("0.95 must not receive an extension owner tag")


def test_blocks():
    blocks = hc_adapter.extension_blocks(adapter)
    assert len(blocks) == 33 and sum(map(len, blocks)) == 99
    levels = {}
    for block in blocks:
        assert len({tuple(c[k] for k in hc_adapter.POLICY_FIELDS) for c in block}) == 1
        assert {c["rule_id"] for c in block} == {"single_sample", "180min_3of3", "360min_4of6"}
        levels[float(block[0]["level"])] = levels.get(float(block[0]["level"]), 0) + 1
    assert levels == {0.975: 11, 0.99: 11, 0.995: 11}


def test_rank_rule():
    rng = np.random.default_rng(7)
    for level in LEVELS:
        for n in (40, 50, 51, 198, 199, 200, 201, 499, 500, 34534):
            scores = rng.normal(size=n)
            frozen = score_quantiles(scores, level, "cqr")
            mine = hc_validate.cqr_quantile(list(scores), level)
            assert (frozen is None) == (mine is None) == (not rank_support(n, level, "cqr")["supported"])
            if frozen is not None:
                assert frozen[0] == mine
        assert math.ceil(201 * level) <= 200


def test_fitting_disabled():
    from sklearn.ensemble import HistGradientBoostingRegressor
    original = HistGradientBoostingRegressor.fit
    with hc_adapter.FittingDisabled():
        try:
            HistGradientBoostingRegressor().fit(np.zeros((5, 1)), np.zeros(5))
        except AssertionError:
            pass
        else:
            raise AssertionError("fit was not disabled")
    assert HistGradientBoostingRegressor.fit is original


class _Owner:
    def __init__(self, method, level, calibration):
        self.method, self.level, self.calibration = method, level, calibration
        self.fit_identity = "synthetic"
        self.identity = {"synthetic": True}


def _synthetic(seed=3):
    rng = np.random.default_rng(seed)
    rows = []
    for group, start, lengths in (("a", "2020-01-01", (300, 250)), ("b", "2020-01-02", (420,))):
        t = pd.Timestamp(start)
        for length in lengths:
            for _ in range(length):
                rows.append({"row_id": f"{group}{len(rows)}", "group_id": group, "origin_time": t,
                             "target_time": t + pd.Timedelta("1h")})
                t += pd.Timedelta("1h")
            t += pd.Timedelta("5h")
    meta = pd.DataFrame(rows)
    n = len(meta)
    point = rng.normal(size=n)
    raw = {"point": point, "raw_lower": point - 1 + rng.normal(scale=.1, size=n),
           "raw_upper": point + 1 + rng.normal(scale=.1, size=n)}
    raw["static_lower"], raw["static_upper"] = raw["raw_lower"] - .2, raw["raw_upper"] + .2
    observed = point + rng.normal(scale=1.2, size=n)
    available = rng.random(n) > .1
    observed[~available] = np.nan
    cal = pd.DataFrame({"group_id": rng.choice(["a", "b", "c"], size=600),
                        "target_time": pd.Timestamp("2019-06-01") + pd.to_timedelta(rng.permutation(600), unit="h"),
                        "score": rng.normal(size=600)})
    X = pd.DataFrame({"x": np.arange(n, dtype=float)})
    return meta, raw, observed, available, cal, X


def test_independent_interval_rebuild_matches_frozen_replay():
    meta, raw, observed, available, cal, X = _synthetic()
    feature_hash = hashlib.sha256(pd.util.hash_pandas_object(X, index=False).values.tobytes()).hexdigest()
    for level in LEVELS:
        for method, strategy, every, window in (("cqr", "rolling", 12, 200), ("cqr", "rolling", 24, 500),
                                                ("cqr", "periodic", 48, None), ("quantile_uncalibrated", "static", 0, None)):
            candidate = {"method": method, "level": level, "strategy": strategy, "every": every, "window": window,
                         "min_samples": 50}
            owner = _Owner(method, level, cal)
            out = replay(owner, X, meta, observed, available, candidate, pd.Timedelta("1h"),
                         raw_prediction={"values": raw, "feature_hash": feature_hash, "fit_identity": "synthetic"})
            stream = out["stream"].copy()
            stream["update_status"] = stream.update_status.astype(str)
            rebuilt = hc_validate.rebuild_intervals(stream, cal.assign(target_time=pd.to_datetime(cal.target_time)),
                                                    candidate)
            if method == "cqr":
                assert np.array_equal(rebuilt["lower"], stream.lower.to_numpy())
                assert np.array_equal(rebuilt["upper"], stream.upper.to_numpy())
            assert np.array_equal(rebuilt["updated"], stream.updated.to_numpy(bool))
            assert np.array_equal(rebuilt["pool"], stream.update_pool_n.to_numpy(int))
            assert list(rebuilt["status"]) == list(stream.update_status)
            latest = pd.to_datetime(stream.latest_released_target).to_numpy("datetime64[ns]").astype(np.int64)
            assert np.array_equal(rebuilt["latest"], latest)


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("passed", test.__name__)
    print(f"{len(tests)} guard tests passed")
