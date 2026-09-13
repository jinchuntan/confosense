"""Regression tests through engine/extension paths, not just helper contracts."""
from dataclasses import asdict
import numpy as np
import pandas as pd
import pytest
from src import corrected_study as E, robustness_extension as R, windowing
from src import split_integrity as S
from src.interval_stream import IntervalEstimator, recalibrated_bounds
from src.datasets.base import PreparedDataset, PreparedSeries, Provenance, ChronologicalPartitioner


def fixture_data(n=800, horizon=5):
    t = pd.date_range("2021", periods=n, freq="min")
    frame = pd.DataFrame({"target": np.sin(np.arange(n) / 19) + np.arange(n) / 80}, index=t)
    series = PreparedSeries("fixture", "target", frame, pd.Timedelta("1min"),
                            group_id="asset", season_steps=None)
    prepared = PreparedDataset("fixture", [series], ChronologicalPartitioner(),
                                Provenance("fixture", "deterministic test fixture"))
    cfg = {"features": {"target_lags": [0, 1, 3], "rolling_windows": [4]},
           "alerts": {"primary_horizon": horizon, "detection_tolerance_steps": 2},
           "horizons": [horizon]}
    fcfg = windowing.feature_config(cfg, [])
    w = windowing.build_dataset_windows(prepared, horizon, fcfg)
    return prepared, cfg, fcfg, w


class DeterministicEstimator:
    """An observable estimator double with distinct method-specific predictions."""
    def __init__(self, method, level, Xtr, ytr, Xca, yca, meta_ca, horizon, seed=42):
        self.method, self.level, self.seed = method, level, seed
        self.horizon, self.meta_ca, self.y_ca = horizon, meta_ca, np.asarray(yca)
        self.estimator_class = "fixtures.DeterministicForecaster"
        self.fallback = None; self.fit_seconds = 0.0
        self.offset = (2 if "enbpi" in method else 0) + seed / 100
        self.point_ca = Xca.iloc[:, 0].to_numpy() + self.offset
        self.resid_ca = self.y_ca - self.point_ca

    @property
    def identity(self):
        return {"estimator_class": self.estimator_class, "model_seed": self.seed,
                "fallback": None}

    def predict(self, Xte, **kw):
        point = Xte.iloc[:, 0].to_numpy() + self.offset
        return point, point - 1, point + 1

    def stream(self, Xte, **kw):
        point, lo, hi = self.predict(Xte, **kw)
        return dict(point=point, lower=lo, upper=hi,
                    calibration_point=self.point_ca, identity=self.identity)


def install_estimators(monkeypatch):
    monkeypatch.setattr(E, "IntervalEstimator", DeterministicEstimator)
    monkeypatch.setattr(R, "UnitModel", DeterministicEstimator)
    monkeypatch.setattr(R.xgboost_model, "tune", lambda *a, **kw: {"estimator": object()})
    monkeypatch.setattr(R.xgboost_model, "predict", lambda m, x: x.iloc[:, 0].to_numpy())


@pytest.mark.parametrize("horizon", [1, 3, 6, 15, 30, 60])
def test_actual_engine_inner_and_refit_boundaries(horizon, monkeypatch):
    _, _, _, w = fixture_data(1200, horizon)
    m = w["meta"]
    for f in E.make_outer_folds(m, "chronological", 3, horizon, pd.Timedelta("1min")):
        pool = np.concatenate([f["train"], f["calibration"]])
        inner = E.inner_split(m, pool, "chronological", horizon, pd.Timedelta("1min"))
        S.assert_boundary(m, inner["inner_train"], inner["inner_calib"])
        S.assert_boundary(m, inner["inner_calib"], inner["inner_select"])
        install_estimators(monkeypatch)
        iv, (ca, _), cp = E._fit_interval_on("cqr", .9, w["X"], w["y"], pool, f["test"], m, horizon, seed=7)
        tr, expected_ca = S.refit_split(m, pool)
        assert np.array_equal(ca, expected_ca)
        S.assert_boundary(m, tr, ca)
        assert iv["identity"]["model_seed"] == 7


@pytest.mark.parametrize("horizon", [5, 15, 30, 60])
def test_rico_refit_and_tuning_keep_variable_length_runs_whole(horizon):
    parts = []
    for i in range(15):
        t = pd.date_range(pd.Timestamp("2020") + pd.Timedelta(days=i), periods=100 + 7*i, freq="min")
        parts.append(pd.DataFrame({"group_id": f"run{i}", "origin_time": t,
                                   "target_time": t + pd.Timedelta(minutes=horizon)}))
    m = pd.concat(parts, ignore_index=True)
    for f in E.make_outer_folds(m, S.GROUPED, 3, horizon, pd.Timedelta("1min")):
        pool = np.concatenate([f["train"], f["calibration"]])
        inner = E.inner_split(m, pool, S.GROUPED, horizon, pd.Timedelta("1min"))
        tr, ca = S.refit_split(m, pool)
        S.assert_boundary(m, tr, ca, S.GROUPED)
        for a, b in S.tuning_splits(m.iloc[inner["inner_train"]].reset_index(drop=True), 2, S.GROUPED):
            S.assert_boundary(m.iloc[inner["inner_train"]].reset_index(drop=True), a, b, S.GROUPED)


def test_bdg2_boundaries_do_not_split_simultaneous_buildings():
    t = pd.date_range("2020", periods=501, freq="h")
    m = pd.concat([pd.DataFrame({"group_id": g, "origin_time": t,
                                "target_time": t + pd.Timedelta("6h")})
                   for g in ["a", "b", "c"]], ignore_index=True)
    folds = E.make_outer_folds(m, "chronological", 3, 6, pd.Timedelta("1h"))
    for f in folds:
        counts = m.iloc[f["test"]].groupby("origin_time").size()
        assert (counts == 3).all()
    keys = [set(map(tuple, m.iloc[f["test"]][["group_id", "origin_time"]].to_numpy())) for f in folds]
    assert not any(keys[i] & keys[j] for i in range(3) for j in range(i))


@pytest.mark.parametrize("policy", ["static", "periodic", "rolling"])
def test_engine_recalibration_observations_are_delayed_and_group_isolated(policy):
    origins = pd.date_range("2021", periods=80, freq="min").repeat(2)
    groups = np.tile(["a", "b"], 80)
    target = origins + pd.Timedelta("5min")
    observed = np.where(groups == "b", 500.0, 2.0)
    kw = dict(strategy=policy, point=np.zeros(160), y_ca=np.array([-1., 1., -1., 1.]),
        point_ca=np.zeros(4), groups_ev=groups, o_ev=origins, t_ev=target,
        groups_ca=np.array(["a", "a", "b", "b"]),
        t_ca=pd.date_range("2020", periods=4, freq="min"), level=.9, horizon=5,
        update_every=1, window=10, min_samples=1)
    lo, hi = E._recalibrated_stream(**kw, y_observed=observed)
    _, zero_hi = E._recalibrated_stream(**kw, y_observed=np.zeros(160))
    assert np.allclose(hi[:10], zero_hi[:10])
    assert hi[groups == "a"].max() <= 2.0
    if policy == "static":
        assert np.allclose(hi, zero_hi)
    else:
        assert hi[-1] > zero_hi[-1]
    altered = observed.copy(); altered[-2:] = 1e8
    _, altered_hi = E._recalibrated_stream(**kw, y_observed=altered)
    assert np.array_equal(hi, altered_hi)


@pytest.mark.parametrize("policy", ["static", "periodic", "rolling"])
def test_core_outer_and_extension_clean_zero_streams_match(monkeypatch, policy):
    install_estimators(monkeypatch)
    prepared, cfg, fcfg, w = fixture_data()
    m, X, y = w["meta"], w["X"], w["y"]
    f = E.make_outer_folds(m, "chronological", 3, 5, prepared.freq)[0]
    trc = np.concatenate([f["train"], f["calibration"]]); tr, _ = S.refit_split(m, trc)
    scales = S.training_scale(y, m, tr)
    pipe = E.Pipeline("fixture", 5, 7, 0, "DeterministicForecaster", "cqr", .9,
        policy, "single", 1, 1, 0., "fixture", estimator_class="fixtures.DeterministicForecaster", event_seed=99).freeze()
    row, bounds, _, _ = E.evaluate_outer(pipe, m, X, y, trc, f["test"], cfg,
                                       prepared.freq, scales, {"incidence": .5})
    captured = []
    real_score = R.score_cell
    def score(*args, **kw):
        captured.append((args[2].copy(), args[3].copy()))
        return real_score(*args, **kw)
    monkeypatch.setattr(R, "score_cell", score)
    rows, _, _ = R.evaluate_unit("fixture", prepared, m, X, y, 0, f,
        asdict(pipe), cfg, prepared.freq, scales, fcfg, 5, fast=True)
    for lo, hi in captured[:2]:
        assert np.array_equal(lo, bounds["lower"])
        assert np.array_equal(hi, bounds["upper"])
    assert rows[0]["coverage_all"] == row["empirical_coverage"]
    assert rows[0]["model_seed"] == 7 and rows[0]["event_seed"] == 99
    bad = E.Pipeline(**{**asdict(pipe), "point_model": "attention_lstm"}).freeze()
    with pytest.raises(E.FailClosed, match="identity"):
        E.evaluate_outer(bad, m, X, y, trc, f["test"], cfg, prepared.freq, scales, {"incidence": .5})


def test_inner_selection_uses_method_specific_residuals_and_seed(monkeypatch):
    install_estimators(monkeypatch)
    prepared, cfg, _, w = fixture_data(1600)
    m, X, y = w["meta"], w["X"], w["y"]
    f = E.make_outer_folds(m, "chronological", 3, 5, prepared.freq)[0]
    inner = E.inner_split(m, np.concatenate([f["train"], f["calibration"]]), "chronological", 5, prepared.freq)
    seen = []
    real = E._recalibrated_stream
    def capture(*a, **kw):
        seen.append((a[3].copy(), kw["y_observed"].copy()))
        return real(*a, **kw)
    monkeypatch.setattr(E, "_recalibrated_stream", capture)
    policy = dict(operating_levels=[.9], incidence=.5, min_recall=0., workload_max=1e6,
                  model_seeds=[7], event_seeds=[99])
    result = E.select_on_inner("fixture", 5, 7, 0, m, X, y, inner, cfg,
        prepared.freq, S.training_scale(y, m, inner["inner_train"]), policy)
    assert result["pipeline"].point_model == "DeterministicForecaster"
    assert result["pipeline"].seed == 7 and result["pipeline"].event_seed == 99
    assert all(np.array_equal(obs, y[inner["inner_select"]]) for _, obs in seen)
    assert not np.array_equal(seen[0][0], seen[-1][0])


def test_preprocessing_and_event_scale_cannot_use_future_values():
    prepared, _, _, w = fixture_data()
    s = prepared.series[0]
    s.frame["target_was_missing"] = 0
    s.frame.iloc[10:12, s.frame.columns.get_loc("target_was_missing")] = 1
    a = S.causal_prepared(prepared).series[0].frame
    s.frame.iloc[12, s.frame.columns.get_loc("target")] = 1e6
    b = S.causal_prepared(prepared).series[0].frame
    assert np.array_equal(a.target.iloc[:12], b.target.iloc[:12])
    tr = np.arange(100); y = w["y"].copy()
    a = S.training_scale(y, w["meta"], tr); y[100:] = 1e8
    assert a == S.training_scale(y, w["meta"], tr)


def test_real_cqr_identity_and_predictions(monkeypatch):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from src import conformal_cqr
    monkeypatch.setattr(conformal_cqr, "_quantile_estimator", lambda seed:
        HistGradientBoostingRegressor(loss="quantile", max_iter=4, min_samples_leaf=5, random_state=seed))
    rng = np.random.default_rng(4)
    X = pd.DataFrame(rng.normal(size=(260, 2))); y = X[0].to_numpy() + rng.normal(size=260)
    meta = pd.DataFrame({"group_id": ["a"] * 60, "target_time": pd.date_range("2020", periods=60, freq="min")})
    model = IntervalEstimator("cqr", .9, X[:180], y[:180], X[180:240], y[180:240], meta, 1, seed=7)
    t = pd.date_range("2021", periods=20, freq="min")
    r = model.stream(X[240:], y_obs=y[240:], groups=np.array(["a"]*20), o_te=t, t_te=t+pd.Timedelta("1min"))
    expected = conformal_cqr.cqr_interval(model.m, X[240:])
    assert np.array_equal(r["point"], expected["point"])
    assert r["identity"]["estimator_class"].endswith("HistGradientBoostingRegressor")
    assert r["identity"]["model_seed"] == 7
