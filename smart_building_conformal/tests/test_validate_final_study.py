"""The final-study validator is a real gate: it passes the design-level checks
that hold now and fails closed on the run-dependent ones until a completed,
non-fast corrected run exists.
"""

from __future__ import annotations

from src import validate_final_study as V


def test_validator_passes_design_checks_now():
    rep = V.run("outputs/final_dissertation_v2", run_tests=False)
    by = {c.name: c for c in rep.checks}
    assert by["protocol_parses_and_validates"].ok
    assert by["protocol_hash_recorded"].ok
    assert by["full_study_unchanged"].ok


def test_validator_fails_closed_without_completed_run():
    rep = V.run("outputs/final_dissertation_v2", run_tests=False)
    by = {c.name: c for c in rep.checks}
    # No corrected full run has completed, so publication-readiness must be false.
    assert not rep.passed
    assert not by["full_nonfast_run_present"].ok
