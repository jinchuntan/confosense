"""Check the corrected EnbPI reconstruction on the four completed bundles."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from adapter import SMART, bundle_paths
from corrected_validator_v1 import mapie_asymmetric_arguments, mapie_quantile_probability
from src.intervals005_common import Operations, atomic, digest, frame, load_owner, tree


def quantile(scores: np.ndarray, probability: float, reverse: bool) -> float:
    signed = -1 if reverse else 1
    finite = np.asarray(scores)[np.isfinite(scores)]
    corrected = min(1.0, max(0.0, math.ceil(probability * (len(finite) + 1)) / len(finite)))
    return float(signed * np.quantile(signed * finite, corrected, method="lower"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    receipt = Path(args.receipt).resolve()
    if receipt.exists():
        raise ValueError("preserve existing completed-bundle check")
    receipt.mkdir(parents=True)
    rows, identities = [], []
    with Operations(forbid=True):
        for seed in (42, 43, 44, 45):
            _, run = bundle_paths("bdg2", 0, seed)
            before, operations_before = tree(run), digest(run / "operations.jsonl")
            for horizon in (1, 3, 6):
                owner = load_owner(run / f"stages/owner_cal_h{horizon}_enbpi/owner.pkl")
                if owner.conformity_score_function_.sym:
                    raise ValueError("unexpected symmetric EnbPI owner")
                for level in (0.9, 0.95):
                    beta, upper_argument = mapie_asymmetric_arguments(level)
                    lower_probability = mapie_quantile_probability(beta, True)
                    upper_probability = mapie_quantile_probability(upper_argument, False)
                    lower_q = quantile(owner.conformity_scores_, lower_probability, True)
                    upper_q = quantile(owner.conformity_scores_, upper_probability, False)
                    raw = frame(run / f"stages/raw_h{horizon}_enbpi/test_{int(level * 100)}.csv.gz")
                    point = raw.point.to_numpy(np.float32).astype(np.float64)
                    lower_delta = raw.static_lower.to_numpy() - (point + lower_q)
                    upper_delta = raw.static_upper.to_numpy() - (point + upper_q)
                    for bound, delta in (("lower", lower_delta), ("upper", upper_delta)):
                        maximum = float(np.max(np.abs(delta)))
                        np.testing.assert_allclose(delta, 0, atol=1e-7, rtol=1e-7)
                        rows.append(dict(
                            seed=seed, horizon=horizon, level=level, bound=bound,
                            rows=len(delta), maximum_absolute_difference=maximum,
                            differing_rows_at_tolerance=int(np.count_nonzero(np.abs(delta) > 1e-7)),
                            passed=True,
                        ))
            after, operations_after = tree(run), digest(run / "operations.jsonl")
            if before != after or operations_before != operations_after:
                raise ValueError("completed scientific bundle changed")
            identities.append(dict(
                seed=seed,
                complete_sha256=digest(run / "COMPLETE.json"),
                operations_sha256_before=operations_before,
                operations_sha256_after=operations_after,
                tree_unchanged=True,
            ))
    pd.DataFrame(rows).to_csv(receipt / "completed_bundle_bounds.csv", index=False)
    result = dict(
        passed=True,
        bundles_checked=4,
        bound_cells_checked=len(rows),
        rows_checked=sum(row["rows"] for row in rows),
        models_fitted=0,
        calibrators_fitted=0,
        tolerances_unchanged=True,
        scientific_artifacts_unchanged=True,
        identities=identities,
    )
    atomic(receipt / "validation.json", result)
    atomic(receipt / "COMPLETE.json", {"files": tree(receipt)})
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
