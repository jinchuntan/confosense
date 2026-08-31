"""The frozen protocol parses, validates strictly, and drives the runtime config.

These tests are the executable half of protocol amendment 001: they prove the
predeclared design is not just prose but a machine-checked, hash-pinned object
that the corrected runner must implement.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from src import protocol as P
from src.run_study import load_config

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "outputs" / "final_dissertation_v2" / "protocol" / "frozen_protocol.yaml"
HASH_FILE = ROOT / "outputs" / "final_dissertation_v2" / "protocol" / "config_hash.txt"
EXEC_CFG = ROOT / "configs" / "study_final_dissertation_v2.yaml"


def test_protocol_parses_and_validates():
    p = P.load_protocol(PROTO)
    assert p.schema_version >= 2
    assert p.partitioning.outer_folds >= 3
    assert p.selection_policy.on_no_feasible == "report_no_feasible_configuration"
    assert p.recalibration.feed_selected_stream_into_alerts is True


def test_recorded_hash_matches_file():
    h = P.protocol_hash(PROTO)
    text = HASH_FILE.read_text(encoding="utf-8")
    assert h in text, "config_hash.txt must record the current canonical hash"


def test_unknown_field_is_rejected():
    raw = yaml.safe_load(PROTO.read_text(encoding="utf-8"))
    raw["unexpected_field"] = 1
    with pytest.raises(Exception):
        P.Protocol.model_validate(raw)


def test_placeholder_value_is_rejected():
    raw = yaml.safe_load(PROTO.read_text(encoding="utf-8"))
    raw["meta"]["output_root"] = "explicit"
    with pytest.raises(Exception):
        P.Protocol.model_validate(raw)


def test_silent_event_drop_is_rejected():
    raw = yaml.safe_load(PROTO.read_text(encoding="utf-8"))
    raw["event_injection"]["placement"]["drop_silently"] = True
    with pytest.raises(Exception):
        P.Protocol.model_validate(raw)


def test_end_to_end_flag_must_be_true():
    raw = yaml.safe_load(PROTO.read_text(encoding="utf-8"))
    raw["recalibration"]["feed_selected_stream_into_alerts"] = False
    with pytest.raises(Exception):
        P.Protocol.model_validate(raw)


def test_out_of_range_coverage_level_is_rejected():
    raw = yaml.safe_load(PROTO.read_text(encoding="utf-8"))
    raw["interval"]["operating_levels"] = [0.95, 1.5]
    with pytest.raises(Exception):
        P.Protocol.model_validate(raw)


def test_executable_config_implements_protocol():
    p = P.load_protocol(PROTO)
    base = load_config(str(EXEC_CFG))
    resolved = P.compile_to_config(p, base)
    P.assert_config_implements_protocol(p, resolved)   # raises on any gap
    assert resolved["protocol"]["output_root"] == p.meta.output_root
    assert resolved["paths"]["full_study_dir"].startswith(p.meta.output_root)


def test_executable_config_references_current_protocol_hash():
    raw = yaml.safe_load(EXEC_CFG.read_text(encoding="utf-8"))
    assert raw["protocol_ref"]["hash"] == P.protocol_hash(PROTO)


def test_executable_config_output_root_is_corrected_not_full_study():
    cfg = load_config(str(EXEC_CFG))
    assert "final_dissertation_v2" in cfg["paths"]["full_study_dir"]
    assert cfg["paths"]["full_study_dir"] != "outputs/full_study"


def test_changing_a_protocol_field_changes_the_hash():
    raw = yaml.safe_load(PROTO.read_text(encoding="utf-8"))
    before = P.canonical_bytes(P.Protocol.model_validate(raw))
    raw["selection_policy"]["min_recall"] = 0.61
    after = P.canonical_bytes(P.Protocol.model_validate(raw))
    assert before != after


def test_resolved_config_hash_tracks_operating_levels():
    p = P.load_protocol(PROTO)
    base = load_config(str(EXEC_CFG))
    r1 = P.compile_to_config(p, base)
    p2 = copy.deepcopy(p)
    object.__setattr__(p2.interval, "operating_levels", [0.95, 0.99])
    r2 = P.compile_to_config(p2, base)
    assert P.resolved_config_hash(r1) != P.resolved_config_hash(r2)
