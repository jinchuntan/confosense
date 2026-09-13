"""Interruption, real tiny fits and evidence-gating regression scenarios."""
from dataclasses import asdict
import json
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from src import corrected_study as E, robustness_extension as R, split_integrity as S
from src import final_reports_v2 as reports, xgboost_model, attention_lstm
from src.unit_checkpoint import UnitCheckpoint, require_cells
from src.evidence_status import extension_matrix
from test_integration_repairs import fixture_data, install_estimators


def fake_selection(dataset, horizon, seed, fold, meta, X, y, inner, cfg, freq, scale, policy):
    p = E.Pipeline(dataset, horizon, seed, fold, "DeterministicForecaster", "cqr", .9,
        "periodic", "single", 1, 1, 0., "fixture",
        estimator_class="fixtures.DeterministicForecaster", event_seed=seed).freeze()
    return dict(decision="selected", pipeline=p, notes={}, event_allocation={},
                surface=pd.DataFrame({"candidate": [1]}))


def test_core_interruption_resume_preserves_bounds_without_refitting_completed_unit(tmp_path, monkeypatch):
    install_estimators(monkeypatch)
    monkeypatch.setattr(E, "select_on_inner", fake_selection)
    prepared, cfg, _, _ = fixture_data(1600)
    calls = []
    evaluate = E.evaluate_outer
    def interrupted(*a, **kw):
        calls.append(a[0].outer_fold)
        if len(calls) == 2:
            raise RuntimeError("simulated interruption")
        return evaluate(*a, **kw)
    monkeypatch.setattr(E, "evaluate_outer", interrupted)
    args = ("fixture", cfg, prepared, tmp_path / "core", [42], 3, prepared.freq, True)
    with pytest.raises(RuntimeError, match="interruption"):
        E.run_dataset(*args)
    unit = tmp_path / "core" / "units" / "h5_f0_s42_e42" / "predictions.csv.gz"
    saved = unit.read_bytes()
    calls.clear()
    def resumed(*a, **kw):
        calls.append(a[0].outer_fold)
        return evaluate(*a, **kw)
    monkeypatch.setattr(E, "evaluate_outer", resumed)
    summary = E.run_dataset(*args, resume=True)
    assert calls == [1, 2] and summary["complete_units"] == 3
    assert unit.read_bytes() == saved
    calls.clear()
    E.run_dataset(*args, resume=True)
    assert calls == []
    with pytest.raises(ValueError, match="signature"):
        E.run_dataset(*args[:4], [43], *args[5:], resume=True)


def test_checkpoint_corruption_duplicates_and_empty_frames_fail_safely(tmp_path):
    store = UnitCheckpoint(tmp_path / "run", {"data": "one"})
    store.save("a", {"score": 1.}, {"empty": pd.DataFrame(), "bounds": pd.DataFrame({"x": [np.pi]})})
    assert store.load("a")[1]["bounds"].x[0] == np.pi
    assert store.load("a")[1]["empty"].empty
    with pytest.raises(ValueError, match="duplicate"):
        store.save("a", {}, {})
    with pytest.raises(ValueError, match="matrix"):
        store.require_complete(["a", "b"])
    (tmp_path / "run" / "units" / "a" / "payload.json").write_text('{}')
    with pytest.raises(ValueError, match="corrupt"):
        store.load("a")
    with pytest.raises(ValueError, match="duplicate"):
        require_cells(pd.DataFrame({"cell": ["a", "a"]}), ["cell"], [("a",)])


def test_actual_extension_driver_resumes_and_rejects_missing_provenance(tmp_path, monkeypatch):
    from src import run_study, datasets, protocol
    install_estimators(monkeypatch)
    monkeypatch.setattr(E, "select_on_inner", fake_selection)
    prepared, cfg, _, _ = fixture_data(1600)
    core = tmp_path / "core"
    E.run_dataset("fixture", cfg, prepared, core / "fixture", [42], 3, prepared.freq, False)
    (core / "engine_summary.json").write_text(json.dumps({"integration_version": 1, "fast": False}))
    monkeypatch.setattr(run_study, "load_config", lambda _: {"protocol_ref": {"path": "fixture"}})
    monkeypatch.setattr(run_study, "resolve_dataset_config", lambda *_: cfg)
    monkeypatch.setattr(datasets, "get_adapter", lambda _: SimpleNamespace(prepare=lambda _: prepared))
    monkeypatch.setattr(protocol, "load_protocol", lambda _: SimpleNamespace(seeds=SimpleNamespace(model=[42])))
    monkeypatch.setattr(protocol, "protocol_hash", lambda _: "fixture-protocol")
    calls = []
    evaluate = R.evaluate_unit
    def interrupted(*a, **kw):
        calls.append(a[5])
        if len(calls) == 2:
            raise RuntimeError("simulated interruption")
        return evaluate(*a, **kw)
    monkeypatch.setattr(R, "evaluate_unit", interrupted)
    with pytest.raises(RuntimeError, match="interruption"):
        R.run_extension("fixture", ["fixture"], tmp_path / "extension", core_artifacts=core)
    monkeypatch.setattr(R, "evaluate_unit", evaluate)
    result = R.run_extension("fixture", ["fixture"], tmp_path / "extension", core_artifacts=core, resume=True)
    assert result["fixture"]["n_units"] == 3
    assert result["fixture"]["n_cell_rows"] == 3 * len(R.expected_cell_names(False))
    frame = extension_matrix(tmp_path / "extension", ["fixture"], [42], 3)
    frame.iloc[:-1].to_csv(tmp_path / "extension" / "fixture" / "robustness_cells.csv", index=False)
    with pytest.raises(ValueError, match="missing"):
        extension_matrix(tmp_path / "extension", ["fixture"], [42], 3)
    p = core / "fixture" / "provenance.json"
    p.write_text(json.dumps(json.loads(p.read_text())[:-1]))
    with pytest.raises(ValueError, match="missing core"):
        R.run_extension("fixture", ["fixture"], tmp_path / "bad", core_artifacts=core)


def test_real_xgboost_search_uses_purged_group_validation_and_seed(monkeypatch):
    rng = np.random.default_rng(4)
    n = 180
    m = pd.DataFrame({"group_id": np.repeat(np.arange(9), 20),
        "origin_time": pd.date_range("2020", periods=n, freq="h")})
    m["target_time"] = m.origin_time + pd.Timedelta("3h")
    m.attrs["split_scheme"] = S.GROUPED
    X = pd.DataFrame(rng.normal(size=(n, 2))); y = X[0] + .1 * X[1]
    monkeypatch.setattr(xgboost_model, "PARAM_DISTRIBUTIONS", {"n_estimators": [3], "max_depth": [2]})
    actual = xgboost_model.RandomizedSearchCV
    captured = []
    def search(**kw):
        captured.extend(kw["cv"])
        return actual(**kw)
    monkeypatch.setattr(xgboost_model, "RandomizedSearchCV", search)
    result = xgboost_model.tune(X, y, n_iter=1, n_splits=2, seed=17, n_jobs=1, meta_train=m)
    assert result["estimator"].random_state == 17
    for tr, va in captured:
        S.assert_boundary(m, tr, va, S.GROUPED)
    assert np.isfinite(xgboost_model.predict(result["estimator"], X[:4])).all()


def test_real_lstm_normalisation_excludes_purged_validation(monkeypatch):
    rng = np.random.default_rng(4)
    X = rng.normal(size=(80, 4, 2)).astype("float32"); y = X[:, -1, 0]
    m = pd.DataFrame({"group_id": ["a"] * 80,
        "origin_time": pd.date_range("2020", periods=80, freq="h")})
    m["target_time"] = m.origin_time + pd.Timedelta("6h")
    expected, validation = S.ordered_blocks(m, np.arange(80), [.8, .2])
    actual = attention_lstm._standardise
    used = []
    def standardise(a):
        used.append(a.copy()); return actual(a)
    monkeypatch.setattr(attention_lstm, "_standardise", standardise)
    attention_lstm.torch.set_num_threads(1)
    result = attention_lstm.train_predict(X, y, X[:5], dict(hidden_size=2, max_epochs=1,
        batch_size=16, dropout=0.), seed=17, meta_train=m)
    assert np.array_equal(used[0], X[expected])
    assert np.array_equal(result["validation_indices"], validation)
    assert result["model_seed"] == 17 and np.isfinite(result["predictions"]).all()


def test_reports_do_not_infer_results_from_orphan_csvs_or_smoke(tmp_path):
    out = tmp_path / "out"; metrics = out / "metrics"; metrics.mkdir(parents=True)
    pd.DataFrame({"dataset": ["bdg2"], "estimate": [123.456]}).to_csv(metrics / "final_cis_corrected.csv", index=False)
    pd.DataFrame({"delta_mean": [999.]}).to_csv(metrics / "robustness_effects.csv", index=False)
    missing = tmp_path / "missing"
    reports.build(out, missing, missing)
    assert "**missing**" in (out / "report" / "ROBUSTNESS_RESULTS.md").read_text(encoding="utf-8")
    texts = "\n".join(p.read_text(encoding="utf-8") for p in (out / "report").glob("*.md"))
    assert "123.456" not in texts and "999.0" not in texts
    smoke = tmp_path / "smoke"; (smoke / "bdg2").mkdir(parents=True)
    (smoke / "extension_summary.json").write_text(json.dumps({"fast": True}))
    pd.DataFrame({"unit_fit_seconds": [12.5]}).to_csv(smoke / "bdg2" / "unit_timing.csv", index=False)
    reports.build(out, missing, smoke)
    text = (out / "report" / "COMPUTATIONAL_EFFICIENCY.md").read_text(encoding="utf-8")
    assert "SMOKE ONLY" in text and "12.5s" in text and "n=1" in text


def test_multigroup_fault_detection_does_not_credit_other_assets_pre_fault_alert():
    n = 40
    groups = np.repeat(["a", "b"], n)
    times = pd.date_range("2020", periods=n, freq="min")
    meta = pd.DataFrame({"group_id": groups, "target_time": np.tile(times, 2)})
    masks = R.segment_masks(meta, np.arange(2*n))
    clean = np.zeros(2*n); observed = clean.copy()
    observed[n + 1] = 10.  # asset b PRE fault; inside a pooled a-to-b fault span
    result = R.score_cell(clean, observed, np.full(2*n, -1.), np.ones(2*n),
                          groups, meta, masks, 1., 1, 1, .9, 0)
    assert result["n_detected_groups"] == 0
    assert result["fault_detection_rate"] == 0.
    assert np.isnan(result["fault_detected"])


def test_declared_physical_rules_and_minimum_support_reach_selection(monkeypatch):
    from src import protocol
    p = protocol.load_protocol("outputs/final_dissertation_v2/protocol/frozen_protocol.yaml")
    cfg = protocol.compile_to_config(p, {})
    policy = E._policy_from_cfg(cfg, False)
    assert any(r.get("window_minutes") == 360 for r in E.physical_rules(policy))
    prepared, _, _, w = fixture_data(800)
    f = E.make_outer_folds(w["meta"], "chronological", 3, 5, prepared.freq)[0]
    inner = E.inner_split(w["meta"], np.concatenate([f["train"], f["calibration"]]), "chronological", 5, prepared.freq)
    with pytest.raises(E.FailClosed, match="minimum"):
        E.select_on_inner("fixture", 5, 42, 0, w["meta"], w["X"], w["y"], inner, cfg,
                          prepared.freq, {}, policy)


def test_real_enbpi_fallback_identity_records_exception_and_seed(monkeypatch):
    from src import conformal_enbpi
    from src.interval_stream import IntervalEstimator
    from sklearn.ensemble import RandomForestRegressor
    def fallback(seed, cfg):
        model = RandomForestRegressor(n_estimators=3, max_depth=2, random_state=seed, n_jobs=1)
        model._confosense_fallback_reason = "ImportError: deterministic test substitution"
        return model, "RandomForestRegressor"
    monkeypatch.setattr(conformal_enbpi, "_build_base", fallback)
    rng = np.random.default_rng(4)
    X = pd.DataFrame(rng.normal(size=(300, 2))); y = X[0].to_numpy()
    meta = pd.DataFrame({"group_id": ["a"]*80,
                         "target_time": pd.date_range("2020", periods=80, freq="min")})
    model = IntervalEstimator("recentred_enbpi_static", .9, X[:200], y[:200],
                              X[200:280], y[200:280], meta, 5, seed=17)
    assert model.identity["estimator_class"].endswith("RandomForestRegressor")
    assert "ImportError" in model.identity["fallback"]["reason"]
    assert model.identity["model_seed"] == 17
    origins = pd.date_range("2021", periods=20, freq="min")
    stream = model.stream(X[280:], y_obs=y[280:], groups=np.array(["a"]*20),
                           o_te=origins, t_te=origins+pd.Timedelta("5min"))
    assert np.array_equal(stream["point"], model.m.predict(X[280:].to_numpy(), ensemble=False))
