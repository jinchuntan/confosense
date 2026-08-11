"""Statistical machinery: Holm, Diebold-Mariano, Friedman and effect sizes."""

import numpy as np
import pandas as pd
import pytest

from src import statistics as S


# --------------------------------------------------------------------------- #
def test_holm_matches_the_textbook_step_down_procedure():
    p = [0.01, 0.02, 0.03, 0.04]
    got = S.holm_adjust(p)
    # 4*0.01=0.04, 3*0.02=0.06, 2*0.03=0.06 (monotone), 1*0.04=0.06 (monotone).
    assert got == pytest.approx([0.04, 0.06, 0.06, 0.06])


def test_holm_is_monotone_clipped_and_order_independent():
    p = np.array([0.5, 0.001, 0.2, 0.9])
    adj = S.holm_adjust(p)
    assert np.all(adj <= 1.0)
    assert np.all(adj >= p)                       # adjustment never lowers a p
    # Applying to a permutation gives the correspondingly permuted answer.
    order = np.array([2, 0, 3, 1])
    assert S.holm_adjust(p[order]) == pytest.approx(adj[order])


def test_holm_handles_nan_without_poisoning_the_family():
    adj = S.holm_adjust([0.01, np.nan, 0.04])
    assert np.isnan(adj[1])
    assert np.isfinite(adj[0]) and np.isfinite(adj[2])
    assert adj[0] == pytest.approx(0.02)          # only two live hypotheses


# --------------------------------------------------------------------------- #
def test_dm_detects_a_clearly_better_model_and_signs_it_correctly():
    rng = np.random.default_rng(0)
    n = 500
    y = rng.normal(size=n)
    good = y + rng.normal(scale=0.1, size=n)
    bad = y + rng.normal(scale=1.0, size=n)

    res = S.diebold_mariano(y, good, bad, horizon=1)
    assert res["p_value"] < 0.01
    assert res["dm_statistic"] < 0                 # negative => A has lower loss
    assert res["better_model"] == "a"
    assert res["mean_loss_a"] < res["mean_loss_b"]

    flipped = S.diebold_mariano(y, bad, good, horizon=1)
    assert flipped["dm_statistic"] > 0
    assert flipped["better_model"] == "b"


def test_dm_does_not_flag_two_equivalent_models():
    rng = np.random.default_rng(1)
    n = 400
    y = rng.normal(size=n)
    a = y + rng.normal(scale=0.5, size=n)
    b = y + rng.normal(scale=0.5, size=n)
    assert S.diebold_mariano(y, a, b, horizon=1)["p_value"] > 0.05


def test_dm_refuses_a_sample_too_small_to_test():
    res = S.diebold_mariano([1, 2, 3], [1, 2, 3], [3, 2, 1], horizon=1)
    assert np.isnan(res["p_value"])
    assert "too few" in res["note"]


def test_dm_ignores_nan_pairs():
    rng = np.random.default_rng(2)
    n = 200
    y = rng.normal(size=n)
    a = y + rng.normal(scale=0.1, size=n)
    b = y + rng.normal(scale=1.0, size=n)
    a[:20] = np.nan                                # e.g. an abstaining baseline
    res = S.diebold_mariano(y, a, b, horizon=1)
    assert res["n"] == n - 20


def test_dm_longer_horizon_widens_the_variance_and_softens_the_verdict():
    rng = np.random.default_rng(3)
    n = 300
    y = np.cumsum(rng.normal(size=n))              # autocorrelated errors
    a = y + rng.normal(scale=0.4, size=n)
    b = y + rng.normal(scale=0.5, size=n)
    h1 = S.diebold_mariano(y, a, b, horizon=1)
    h6 = S.diebold_mariano(y, a, b, horizon=6)
    assert abs(h6["dm_statistic"]) <= abs(h1["dm_statistic"]) * 1.5
    assert np.isfinite(h6["p_value"])


def test_pairwise_dm_table_holm_adjusts_and_skips_unavailable_models():
    rng = np.random.default_rng(4)
    n = 300
    y = rng.normal(size=n)
    preds = {
        "xgboost": y + rng.normal(scale=0.2, size=n),
        "persistence": y + rng.normal(scale=0.8, size=n),
        "seasonal_naive": np.full(n, np.nan),      # not applicable here
    }
    table = S.pairwise_dm_table(
        y, preds, [("xgboost", "persistence"), ("seasonal_naive", "persistence")],
        horizon=1, context={"dataset": "d"})
    assert len(table) == 1                         # the all-NaN model is skipped
    assert "p_value_holm" in table.columns
    assert table["dataset"].iloc[0] == "d"


# --------------------------------------------------------------------------- #
def test_friedman_ranks_ascending_so_lower_error_ranks_first():
    matrix = pd.DataFrame({
        "best":  [1.0, 1.1, 0.9, 1.2, 1.0],
        "mid":   [2.0, 2.1, 1.9, 2.2, 2.0],
        "worst": [3.0, 3.1, 2.9, 3.2, 3.0],
    })
    out = S.friedman_test(matrix)
    assert out["p_value"] < 0.05
    ranks = out["mean_ranks"]
    assert ranks["best"] < ranks["mid"] < ranks["worst"]
    assert ranks["best"] == pytest.approx(1.0)


def test_friedman_refuses_an_invalid_design_rather_than_guessing():
    two_methods = pd.DataFrame({"a": [1, 2, 3, 4], "b": [2, 3, 4, 5]})
    out = S.friedman_test(two_methods)
    assert np.isnan(out["p_value"])
    assert "at least 3 methods" in out["note"]

    too_few_blocks = pd.DataFrame({"a": [1, 2], "b": [2, 3], "c": [3, 4]})
    assert np.isnan(S.friedman_test(too_few_blocks)["p_value"])


def test_friedman_drops_incomplete_blocks_and_reports_how_many():
    matrix = pd.DataFrame({
        "a": [1.0, 1.1, 0.9, 1.2, 1.0],
        "b": [2.0, np.nan, 1.9, 2.2, 2.0],
        "c": [3.0, 3.1, 2.9, 3.2, 3.0],
    })
    out = S.friedman_test(matrix)
    assert out["n_blocks"] == 4
    assert out["n_blocks_dropped"] == 1


def test_posthoc_is_holm_adjusted_over_the_whole_family():
    rng = np.random.default_rng(5)
    matrix = pd.DataFrame({
        "a": rng.normal(1.0, 0.05, 20),
        "b": rng.normal(2.0, 0.05, 20),
        "c": rng.normal(3.0, 0.05, 20),
    })
    post = S.nemenyi_style_posthoc(matrix)
    assert len(post) == 3                          # 3 choose 2
    assert (post["p_value_holm"] >= post["p_value"]).all()
    assert post["significant_holm_5pct"].all()


# --------------------------------------------------------------------------- #
def test_effect_sizes_report_direction_and_practical_magnitude():
    rng = np.random.default_rng(6)
    n = 400
    y = rng.normal(size=n)
    a = y + rng.normal(scale=0.2, size=n)          # better
    b = y + rng.normal(scale=0.6, size=n)
    out = S.effect_sizes(y, a, b, n_boot=200, seed=0)
    assert out["pct_mae_improvement"] > 0          # A improves on B
    assert out["mean_abs_error_difference"] < 0    # A's errors are smaller
    assert out["win_rate_a"] > 0.5
    assert out["mean_difference_ci_high"] < 0      # CI excludes zero
    assert out["mae_a"] < out["mae_b"]


def test_bootstrap_covers_every_model_including_simple_baselines():
    rng = np.random.default_rng(7)
    n = 300
    y = rng.normal(size=n)
    preds = {"persistence": y + rng.normal(scale=0.5, size=n),
             "xgboost": y + rng.normal(scale=0.3, size=n),
             "seasonal_naive": np.full(n, np.nan)}
    table = S.bootstrap_all_point_models(y, preds, context={"dataset": "d"},
                                         n_boot=100, seed=0)
    assert set(table["model"]) == {"persistence", "xgboost"}
    assert (table["mae_ci_low"] <= table["mae"]).all()
    assert (table["mae"] <= table["mae_ci_high"]).all()


def test_ranking_matrix_pivots_blocks_against_methods():
    long = pd.DataFrame({
        "dataset": ["d"] * 6, "target": ["t"] * 6,
        "horizon_steps": [1, 1, 3, 3, 6, 6],
        "point_model": ["a", "b"] * 3,
        "mae": [1.0, 2.0, 1.1, 2.1, 1.2, 2.2],
    })
    m = S.ranking_matrix(long, block_cols=["dataset", "target", "horizon_steps"],
                         method_col="point_model", value_col="mae")
    assert m.shape == (3, 2)
    assert list(m.columns) == ["a", "b"]
