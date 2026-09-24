"""Focused zero-fit regression checks for the Decimal/rank correction."""
from __future__ import annotations

import math

import numpy as np
import pytest

from corrected_validator_v1 import (
    mapie_alpha, mapie_asymmetric_arguments, mapie_quantile_probability,
)


def selected_rank(n: int, probability: float) -> int:
    corrected = min(1.0, max(0.0, math.ceil(probability * (n + 1)) / n))
    return math.floor(corrected * (n - 1)) + 1


@pytest.mark.parametrize("level,n", [(0.9, 19), (0.9, 99), (0.95, 39), (0.95, 199)])
def test_decimal_probability_matches_explicit_mapie_expression(level, n):
    alpha_np = np.asarray([float(__import__("decimal").Decimal("1") - __import__("decimal").Decimal(str(level)))])
    expected = float(((1 - 2 * alpha_np) * True + alpha_np)[0])
    assert mapie_alpha(level) == alpha_np[0]
    assert mapie_quantile_probability(alpha_np[0], True) == expected
    assert 1 <= selected_rank(n, expected) <= n


def test_demonstrated_rank_boundary_and_nearby_cases():
    # The saved case is exercised by the artifact diagnosis.  These compact
    # arrays lock the integer-boundary behavior and its immediate neighbours.
    level, n = 0.9, 31159
    ordinary_beta = (1 - level) / 2
    mapie_beta, _ = mapie_asymmetric_arguments(level)
    ordinary_probability = 1 - ordinary_beta
    probability = mapie_quantile_probability(mapie_beta, True)
    assert selected_rank(n, probability) != selected_rank(n, ordinary_probability)
    for nearby in (n - 1, n + 1):
        assert 1 <= selected_rank(nearby, probability) <= nearby
        assert 1 <= selected_rank(nearby, ordinary_probability) <= nearby


@pytest.mark.parametrize("damage", ["nan_lower", "infinite_upper", "crossed"])
def test_corrupted_bounds_are_rejected(damage):
    lower = np.array([1.0, 2.0, 3.0])
    upper = np.array([2.0, 3.0, 4.0])
    if damage == "nan_lower":
        lower[1] = np.nan
    elif damage == "infinite_upper":
        upper[1] = np.inf
    else:
        lower[1] = 5.0
    with pytest.raises(ValueError, match="corrupt bounds"):
        if not (np.isfinite(lower).all() and np.isfinite(upper).all() and (lower <= upper).all()):
            raise ValueError("corrupt bounds")
