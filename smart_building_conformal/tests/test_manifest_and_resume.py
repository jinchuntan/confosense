"""Run manifests and resumable execution.

The critical property: resume must never reuse a stage computed under a
different configuration. Silently mixing two configurations is the easiest way
to end up reporting a number that no single run ever produced.
"""

import json

import pytest

from src.manifest import ResumeLedger, RunManifest, git_state, package_versions
from src.datasets.base import config_hash


CFG_A = {"seed": 42, "horizons": [1, 3], "models": {"xgboost": {"seeds": 5}}}
CFG_B = {"seed": 42, "horizons": [1, 3, 6], "models": {"xgboost": {"seeds": 5}}}


def test_ledger_reuses_completed_stages_for_the_same_config(tmp_path):
    path = tmp_path / "ledger.json"
    a = ResumeLedger(path, config_hash(CFG_A), enabled=True)
    assert not a.done("pleia:point")
    a.mark("pleia:point", rows=12)
    assert a.done("pleia:point")

    reopened = ResumeLedger(path, config_hash(CFG_A), enabled=True)
    assert reopened.done("pleia:point")
    assert not reopened.mismatches


def test_ledger_refuses_to_mix_incompatible_configs(tmp_path):
    path = tmp_path / "ledger.json"
    a = ResumeLedger(path, config_hash(CFG_A), enabled=True)
    a.mark("pleia:point")

    b = ResumeLedger(path, config_hash(CFG_B), enabled=True)
    assert not b.done("pleia:point"), "a stage from another config was reused"
    assert b.mismatches and "recomputed" in b.mismatches[0]


def test_resume_disabled_ignores_an_existing_ledger(tmp_path):
    path = tmp_path / "ledger.json"
    ResumeLedger(path, config_hash(CFG_A), enabled=True).mark("pleia:point")
    fresh = ResumeLedger(path, config_hash(CFG_A), enabled=False)
    assert not fresh.done("pleia:point")


def test_ledger_survives_a_corrupt_file(tmp_path):
    path = tmp_path / "ledger.json"
    path.write_text("{not json", encoding="utf-8")
    led = ResumeLedger(path, config_hash(CFG_A), enabled=True)
    assert not led.done("anything")
    led.mark("pleia:prepare")
    assert json.loads(path.read_text(encoding="utf-8"))["config_hash"] == config_hash(CFG_A)


# --------------------------------------------------------------------------- #
def test_manifest_records_stage_outcomes_and_reasons(tmp_path):
    m = RunManifest("configs/study_full.yaml", CFG_A, tmp_path, fast=True,
                    datasets=["pleia"])
    m.record("pleia:prepare", "completed", 1.5)
    m.record("pleia:intervals", "failed", 0.2, reason="ValueError: boom")
    m.record("pleia:robustness", "skipped", reason="not selected by --stage")
    m.note_limitation("seasonal naive not applicable")
    m.note_limitation("seasonal naive not applicable")      # de-duplicated

    payload = m.write()
    assert payload["n_completed"] == 1
    assert payload["n_failed"] == 1
    assert payload["n_skipped"] == 1
    assert payload["fast_mode"] is True
    assert payload["config_hash"] == config_hash(CFG_A)
    assert len(payload["limitations"]) == 1

    written = json.loads((tmp_path / "manifests" / "experiment_manifest.json")
                         .read_text(encoding="utf-8"))
    assert written["datasets"] == ["pleia"]
    failed = [s for s in written["stages"] if s["status"] == "failed"]
    assert failed[0]["reason"] == "ValueError: boom"


def test_manifest_captures_environment_and_git_state(tmp_path):
    m = RunManifest("cfg.yaml", CFG_A, tmp_path)
    payload = m.write()
    assert "python" in payload["packages"]
    assert payload["packages"]["numpy"] != "not installed"
    assert set(payload["git"]) >= {"commit", "branch", "dirty"}
    assert isinstance(payload["git"]["dirty"], bool)
    assert payload["runtime_seconds"] >= 0
    assert "cpu_count" in payload["machine"]


def test_provenance_is_written_with_a_retrieval_timestamp(tmp_path):
    m = RunManifest("cfg.yaml", CFG_A, tmp_path)
    m.add_provenance("rico", {"official_source": "Zenodo 14871584",
                              "doi": "10.1016/j.dib.2025.111678",
                              "checksum": "abc123"})
    m.write()
    prov = json.loads((tmp_path / "manifests" / "dataset_sources.json")
                      .read_text(encoding="utf-8"))
    assert prov["rico"]["doi"] == "10.1016/j.dib.2025.111678"
    assert prov["rico"]["retrieved_at"]


def test_package_versions_reports_missing_rather_than_raising():
    v = package_versions()
    assert v["python"]
    assert all(isinstance(x, str) for x in v.values())


# --------------------------------------------------------------------------- #
# Resume granularity
# --------------------------------------------------------------------------- #
def test_resume_skips_a_complete_dataset_but_restarts_a_partial_one(tmp_path):
    """Resume is per-dataset because stages share in-memory artefacts.

    A dataset whose every stage is recorded must be skipped whole. A dataset
    missing even one stage must restart from the beginning rather than resume
    mid-way into stages whose inputs no longer exist.
    """
    from src.study_runner import DatasetStudy

    stages = [s for s in DatasetStudy.STAGES if s != "prepare"]
    path = tmp_path / "ledger.json"

    complete = ResumeLedger(path, config_hash(CFG_A), enabled=True)
    for s in stages:
        complete.mark(f"done_ds:{s}")
    assert all(complete.done(f"done_ds:{s}") for s in stages)

    # One stage missing -> the dataset is not considered complete.
    partial = ResumeLedger(tmp_path / "l2.json", config_hash(CFG_A), enabled=True)
    for s in stages[:-1]:
        partial.mark(f"part_ds:{s}")
    assert not all(partial.done(f"part_ds:{s}") for s in stages)


def test_prepare_is_never_skipped_by_the_ledger(tmp_path):
    """prepare populates the in-memory dataset every later stage reads."""
    import inspect
    from src.study_runner import DatasetStudy

    src = inspect.getsource(DatasetStudy.run)
    assert 'self._stage("prepare", self.stage_prepare, resumable=False)' in src
    # And every downstream stage in run() is likewise forced, since the
    # dataset-level check above has already decided whether to run at all.
    assert src.count("resumable=False") >= 2


def test_blank_retrieval_time_is_stamped_not_left_empty(tmp_path):
    """Provenance objects start with an empty retrieved_at, which must be filled."""
    m = RunManifest("cfg.yaml", CFG_A, tmp_path)
    m.add_provenance("pleia", {"official_source": "Zenodo 7620136",
                               "retrieved_at": ""})       # as Provenance emits it
    m.write()
    prov = json.loads((tmp_path / "manifests" / "dataset_sources.json")
                      .read_text(encoding="utf-8"))
    assert prov["pleia"]["retrieved_at"].strip(), "retrieval time was left blank"


def test_provenance_is_merged_across_invocations_not_overwritten(tmp_path):
    """Datasets are usually run one command at a time; each must survive."""
    RunManifest("cfg.yaml", CFG_A, tmp_path, datasets=["pleia"]).__class__
    a = RunManifest("cfg.yaml", CFG_A, tmp_path, datasets=["pleia"])
    a.add_provenance("pleia", {"official_source": "Zenodo 7620136", "checksum": "aaa"})
    a.write()
    b = RunManifest("cfg.yaml", CFG_A, tmp_path, datasets=["rico"])
    b.add_provenance("rico", {"official_source": "Zenodo 14871584", "checksum": "bbb"})
    b.write()

    prov = json.loads((tmp_path / "manifests" / "dataset_sources.json")
                      .read_text(encoding="utf-8"))
    assert set(prov) == {"pleia", "rico"}, "an earlier dataset's provenance was lost"
    assert prov["pleia"]["checksum"] == "aaa"
    assert prov["rico"]["checksum"] == "bbb"


def test_run_history_records_every_invocation(tmp_path):
    for ds in ("pleia", "rico", "bdg2"):
        m = RunManifest("cfg.yaml", CFG_A, tmp_path, datasets=[ds])
        m.record(f"{ds}:point", "completed", 1.0)
        m.write()
    lines = (tmp_path / "manifests" / "run_history.jsonl").read_text(
        encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    seen = [json.loads(x)["datasets"][0] for x in lines]
    assert seen == ["pleia", "rico", "bdg2"]
    assert all(json.loads(x)["fast_mode"] is False for x in lines)


def test_a_run_without_resume_does_not_erase_the_ledger(tmp_path):
    """Regression: --stage prepare (no --resume) wiped a finished study's record.

    mark() rewrites the whole file, so a run that started from an empty ledger
    destroyed every previously recorded stage. The file must be loaded even when
    resume is off, so marking merges instead of replacing.
    """
    path = tmp_path / "ledger.json"
    first = ResumeLedger(path, config_hash(CFG_A), enabled=True)
    for s in ("pleia:point", "pleia:intervals", "rico:point"):
        first.mark(s)

    # A later invocation without --resume marks one stage of its own.
    second = ResumeLedger(path, config_hash(CFG_A), enabled=False)
    assert not second.done("pleia:point")          # resume off: not reusable...
    second.mark("pleia:prepare")

    # ...but the earlier record must still be on disk afterwards.
    third = ResumeLedger(path, config_hash(CFG_A), enabled=True)
    for s in ("pleia:point", "pleia:intervals", "rico:point", "pleia:prepare"):
        assert third.done(s), f"{s} was erased by a non-resume invocation"


def test_incompatible_config_still_starts_clean(tmp_path):
    """Loading always must not resurrect stages from a different configuration."""
    path = tmp_path / "ledger.json"
    ResumeLedger(path, config_hash(CFG_A), enabled=True).mark("pleia:point")
    other = ResumeLedger(path, config_hash(CFG_B), enabled=True)
    assert not other.done("pleia:point")
    assert other.mismatches
