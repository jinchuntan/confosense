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


def test_publication_mode_rejects_historical_evidence_after_integration_defects():
    rep = V.run("outputs/final_dissertation_v2", run_tests=False,
                mode="publication")
    by = {c.name: c for c in rep.checks}
    # Historical files remain present; existence does not validate repaired code.
    assert by["full_nonfast_run_present"].ok
    assert by["run_matrix_complete"].ok
    assert by["estimates_with_cis_present"].ok
    assert not by["repaired_execution_lineage"].ok
    assert not by["declared_methodology_executed"].ok
    assert not by["integration_scientific_decisions_resolved"].ok
    assert not by["integration_evidence_recomputed"].ok
    assert not rep.passed


def test_validator_fails_closed_on_empty_output_root(tmp_path):
    # The fail-closed mechanism itself: an output root with no run/CIs/reports
    # must not be declared publication-ready.
    (tmp_path / "protocol").mkdir()
    rep = V.run(str(tmp_path), run_tests=False, mode="publication")
    assert not rep.passed


def test_no_audit_item_pending_now_passes():
    rep = V.run("outputs/final_dissertation_v2", run_tests=False, mode="readiness")
    by = {c.name: c for c in rep.checks}
    # Every audit item is FIXED / WIRED_IN_ENGINE / OK / DOCUMENT — none PENDING.
    assert by["no_audit_item_pending"].ok


def test_readiness_mode_reports_engine_smoke_coverage():
    rep = V.run("outputs/final_dissertation_v2", run_tests=False, mode="readiness")
    names = {c.name for c in rep.checks}
    assert "engine_smoke_all_datasets" in names
    assert "engine_smoke_four_ablations" in names
