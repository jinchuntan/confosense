"""Versioned, zero-fit correction for the frozen EnbPI rank reconstruction.

The scientific source and its frozen validator remain untouched.  This module
loads the exact frozen validator source, verifies its identity, and replaces
one expression in the independent EnbPI reconstruction so that it follows the
installed MAPIE 1.4.1 confidence-level-to-alpha and reversed-probability path.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import types

import numpy as np

from src import intervals005_validate as frozen_validator
from src.intervals005_common import atomic, digest, read, tree


VERSION = "matched_intervals005_enbpi_decimal_rank_validator_v1"
FROZEN_VALIDATOR_SHA256 = "28313cdc1c48e5c8f74b49c36a1eb47aa4d771657cf33bc7172a441b6329c2fa"
ORIGINAL_QUANTILE_EXPRESSION = "signed=-1 if reverse else 1;ref=1-alpha if reverse else alpha"
CORRECTED_QUANTILE_EXPRESSION = (
    "signed=-1 if reverse else 1;ref=mapie_quantile_probability(alpha,reverse)"
)
ORIGINAL_ASYMMETRIC_EXPRESSION = "else:lower=q((1-l)/2,True);upper=q(1-(1-l)/2)"
CORRECTED_ASYMMETRIC_EXPRESSION = (
    "else:alpha_np=mapie_alpha(l);beta_np=alpha_np/2;"
    "lower=q(beta_np,True);upper=q(1-alpha_np+beta_np)"
)


def mapie_alpha(level: float) -> float:
    """Reproduce MAPIE 1.4.1's Decimal conversion without calling production."""
    return float(Decimal("1") - Decimal(str(level)))


def mapie_symmetric_probability(level: float) -> float:
    """Reproduce MAPIE's reversed quantile probability for symmetric scores."""
    alpha_np = np.asarray([mapie_alpha(level)], dtype=float)
    return float(((1 - 2 * alpha_np) * True + alpha_np)[0])


def mapie_quantile_probability(alpha: float, reversed: bool) -> float:
    """Reproduce MAPIE's affine lower/reversed probability expression."""
    alpha_np = np.asarray([alpha], dtype=float)
    return float(((1 - 2 * alpha_np) * reversed + alpha_np)[0])


def mapie_asymmetric_arguments(level: float) -> tuple[float, float]:
    """Return MAPIE's beta/upper-alpha arguments for an asymmetric score."""
    alpha_np = mapie_alpha(level)
    beta_np = alpha_np / 2
    return beta_np, 1 - alpha_np + beta_np


def frozen_validator_identity() -> dict:
    path = Path(frozen_validator.__file__).resolve()
    actual = digest(path)
    if actual != FROZEN_VALIDATOR_SHA256:
        raise ValueError("frozen validator identity mismatch")
    return {"path": str(path), "sha256": actual}


def corrected_source() -> str:
    identity = frozen_validator_identity()
    source = Path(identity["path"]).read_text(encoding="utf-8")
    replacements = (
        (ORIGINAL_QUANTILE_EXPRESSION, CORRECTED_QUANTILE_EXPRESSION),
        (ORIGINAL_ASYMMETRIC_EXPRESSION, CORRECTED_ASYMMETRIC_EXPRESSION),
    )
    for original, corrected in replacements:
        if source.count(original) != 1:
            raise ValueError("frozen validator correction anchor mismatch")
        source = source.replace(original, corrected)
    return source


def corrected_source_sha256() -> str:
    return hashlib.sha256(corrected_source().encode("utf-8")).hexdigest()


def _corrected_module() -> types.ModuleType:
    module = types.ModuleType("src.intervals005_validate_decimal_rank_v1")
    module.__file__ = str(Path(frozen_validator.__file__).resolve())
    module.__package__ = "src"
    module.__dict__.update(
        mapie_alpha=mapie_alpha,
        mapie_quantile_probability=mapie_quantile_probability,
    )
    exec(compile(corrected_source(), module.__file__, "exec"), module.__dict__)
    return module


def validate(protocol_path, output, receipt, *, failure_provenance=None) -> dict:
    """Run the full independent validator with only the pinned rank correction."""
    dest = Path(receipt)
    result = _corrected_module().validate(protocol_path, output, dest)
    validation = read(dest / "validation.json")
    validation.update(
        correction_version=VERSION,
        correction_module_sha256=digest(Path(__file__)),
        corrected_validator_source_sha256=corrected_source_sha256(),
        frozen_validator=frozen_validator_identity(),
        mapie_probability_contract=(
            "alpha=float(Decimal('1')-Decimal(str(level))); "
            "beta=alpha/2; upper_alpha=1-alpha+beta; "
            "probability=((1-2*quantile_alpha)*reversed+quantile_alpha)"
        ),
        failure_provenance=failure_provenance,
        tolerances_unchanged=True,
        scientific_source_modified=False,
    )
    atomic(dest / "validation.json", validation)
    files = tree(dest)
    files.pop("COMPLETE.json", None)
    atomic(dest / "COMPLETE.json", {"files": files})
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--fold", required=True, type=int)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--failure-log")
    args = parser.parse_args()
    from adapter import bundle_paths
    design, output = bundle_paths(args.dataset, args.fold, args.seed)
    provenance = None
    if args.failure_log:
        path = Path(args.failure_log).resolve()
        provenance = {"path": str(path), "sha256": digest(path)}
    result = validate(
        design / "frozen_protocol.json", output, args.receipt,
        failure_provenance=provenance,
    )
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()

