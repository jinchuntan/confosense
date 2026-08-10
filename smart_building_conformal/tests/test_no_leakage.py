import numpy as np
import pandas as pd

from src import features


FREQ = pd.Timedelta("10min")
SEASON = 144


def _make_df(n=2000):
    idx = pd.date_range("2021-01-01", periods=n, freq="10min")
    rng = np.random.default_rng(0)
    target = 20 + np.sin(np.arange(n) * 2 * np.pi / SEASON) + rng.normal(scale=0.1, size=n)
    df = pd.DataFrame({
        "target": target,
        "target_was_missing": np.zeros(n, dtype=int),
        "tmed": rng.normal(size=n),
    }, index=idx)
    df.index.name = "timestamp"
    return df


CFG = {"target_lags": [1, 2, 3], "rolling_windows": [6], "include_weekly": False,
       "covariates": ["tmed"]}


def test_targets_and_baselines_are_leak_free():
    df = _make_df()
    sup = features.build_supervised(df, horizon=3, freq=FREQ, season_steps=SEASON, cfg=CFG)
    meta = sup["meta"]
    target = df["target"]

    for _, row in meta.head(50).iterrows():
        ot, tt = row["origin_time"], row["target_time"]
        # target is the value at origin + horizon
        assert abs(row["y_true"] - target.loc[tt]) < 1e-9
        # persistence uses the value observed at the origin
        assert abs(row["persistence_pred"] - target.loc[ot]) < 1e-9
        # seasonal naive uses one daily cycle before the target time
        assert abs(row["seasonal_naive_pred"] - target.loc[tt - SEASON * FREQ]) < 1e-9


def test_features_do_not_depend_on_the_far_future():
    df = _make_df()
    sup1 = features.build_supervised(df, horizon=3, freq=FREQ, season_steps=SEASON, cfg=CFG)

    # Corrupt a value near the very end; early feature rows must be unchanged.
    df2 = df.copy()
    df2.iloc[-1, df2.columns.get_loc("target")] = 1e6
    sup2 = features.build_supervised(df2, horizon=3, freq=FREQ, season_steps=SEASON, cfg=CFG)

    x1 = sup1["X"].iloc[:100].to_numpy()
    x2 = sup2["X"].iloc[:100].to_numpy()
    assert np.allclose(x1, x2)


def test_no_feature_equals_the_future_target():
    df = _make_df()
    sup = features.build_supervised(df, horizon=1, freq=FREQ, season_steps=SEASON, cfg=CFG)
    y = sup["y"].to_numpy()
    # No engineered feature column should be identical to the future target.
    for col in sup["X"].columns:
        assert not np.allclose(sup["X"][col].to_numpy(), y)
