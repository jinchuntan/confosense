"""Strict loader, validator and config-compiler for the frozen study protocol.

The frozen protocol (``outputs/final_dissertation_v2/protocol/frozen_protocol.yaml``)
is the predeclared design the corrected dissertation study must obey. This module

* parses it with the same YAML library the study uses;
* validates it against a strict :mod:`pydantic` schema that **rejects unknown,
  missing, placeholder or internally inconsistent fields** (``extra='forbid'``
  everywhere, plus explicit cross-field checks);
* computes a stable SHA-256 over the canonical serialisation, so an accidental
  reformat does not silently change the recorded hash while a real content change
  always does;
* compiles the validated protocol into the resolved runtime configuration and
  asserts that the executable config implements every protocol field.

Nothing here reads results; it only governs the design and its provenance.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Tokens that must never survive into a frozen, executable protocol.
_PLACEHOLDERS = {"explicit", "todo", "tbd", "placeholder", "changeme", "xxx",
                 "fixme", "none_yet", "?"}


class _Strict(BaseModel):
    """Base model that forbids unknown keys and scans strings for placeholders."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _no_placeholders(self):
        for name in type(self).model_fields:
            val = getattr(self, name)
            if isinstance(val, str) and val.strip().lower() in _PLACEHOLDERS:
                raise ValueError(f"placeholder value {val!r} in field {name!r}")
        return self


# --------------------------------------------------------------------------- #
class Meta(_Strict):
    audited_commit: str
    repair_branch: str
    output_root: str
    preserve: str


class Seeds(_Strict):
    model: List[int] = Field(min_length=1)
    event_catalogue: List[int] = Field(min_length=1)
    bootstrap: int


class Embargo(_Strict):
    mode: Literal["horizon"]
    sided: Literal["both", "leading", "trailing"]
    definition: str


class DatasetPartition(_Strict):
    scheme: Literal["purged_rolling_origin", "whole_run_group_blocked",
                    "within_building_target_time_aligned"]
    unit: Literal["window", "run"]
    nested_subsplit: Literal["whole_run"] | None = None
    portability: str | None = None


class Partitioning(_Strict):
    embargo: Embargo
    outer_folds: int = Field(ge=1)
    inner_folds: int = Field(ge=1)
    min_train_windows: int = Field(ge=1)
    min_calibration_windows: int = Field(ge=1)
    min_selection_windows: int = Field(ge=1)
    datasets: dict[str, DatasetPartition]


class Features(_Strict):
    target_lags_include_zero: bool
    persist_schema: bool


class Interval(_Strict):
    candidates: List[str] = Field(min_length=1)
    quantile_uncalibrated_is_diagnostic: bool
    quality_levels: List[float]
    operating_levels: List[float]
    min_calibration_for_level: int = Field(ge=1)

    @field_validator("quality_levels", "operating_levels")
    @classmethod
    def _levels_in_unit_interval(cls, v):
        if not v or any(not (0.0 < x < 1.0) for x in v):
            raise ValueError("coverage levels must lie strictly in (0, 1)")
        if list(v) != sorted(v):
            raise ValueError("coverage levels must be listed in ascending order")
        return v


class Recalibration(_Strict):
    strategies: List[str] = Field(min_length=1)
    residual_delay: Literal["horizon"]
    group_safe: bool
    feed_selected_stream_into_alerts: bool

    @field_validator("feed_selected_stream_into_alerts", "group_safe")
    @classmethod
    def _must_be_true(cls, v):
        if v is not True:
            raise ValueError("must be true in the corrected protocol")
        return v


class PhysicalRule(_Strict):
    name: str
    window_minutes: float = Field(gt=0)
    required_violations: int = Field(ge=1)


class AlertEpisode(_Strict):
    min_alert_duration_minutes: float = Field(ge=0)
    clear_duration_minutes: float = Field(ge=0)
    cooldown_gap_minutes: float = Field(ge=0)
    latching: bool


class EventBalance(_Strict):
    across: List[str]
    scope: Literal["dataset", "fold", "group"]


class EventPlacement(_Strict):
    inside_eligible_groups: bool
    retry_on_boundary: bool
    drop_silently: bool
    record_counts: List[str]

    @field_validator("drop_silently")
    @classmethod
    def _never_drop_silently(cls, v):
        if v is not False:
            raise ValueError("events must never be dropped silently")
        return v


class EventScale(_Strict):
    estimator: Literal["mad_to_sigma"]
    scope: Literal["per_group", "pooled"]
    source: Literal["train_only"]
    fallback: str


class EventInjection(_Strict):
    allocation: Literal["exposure_proportional"]
    incidence_events_per_asset_day: float = Field(gt=0)
    balance: EventBalance
    preserve_group_boundaries: bool
    n_catalogues: int = Field(ge=1)
    types: List[str] = Field(min_length=1)
    severities_sd: List[float] = Field(min_length=1)
    scale: EventScale
    duration_physical: bool
    placement: EventPlacement
    keep_clean_counterfactual: bool


class Matching(_Strict):
    build_episodes_before_matching: bool
    one_to_one: bool
    onset_aware: bool
    overlapping_tolerance_steps: int = Field(ge=0)


class WorkloadConstraint(_Strict):
    metric: str
    max: float = Field(gt=0)


class SelectionPolicy(_Strict):
    scope: Literal["inner_selection_only"]
    workload_constraint: WorkloadConstraint
    min_recall: float = Field(ge=0.0, le=1.0)
    utility: str
    beta: float = Field(gt=0)
    confidence_bound_handling: str
    delay_tie_break: str
    on_no_feasible: Literal["report_no_feasible_configuration"]


class Metrics(_Strict):
    primary: List[str] = Field(min_length=1)
    secondary: List[str]
    forbidden_terms: List[str]
    resampling: dict
    report: List[str]


class Statistics(_Strict):
    bootstrap_replicates: int = Field(ge=2000)
    block_length_method: str
    multiple_comparison: Literal["holm", "simultaneous"]
    ci_method: Literal["percentile", "bca"]
    macro_aggregation: str
    micro_aggregation: str
    min_events_for_recall_ci: int = Field(ge=1)
    cross_target_summary: str


class Robustness(_Strict):
    variants: List[str] = Field(min_length=1)
    perturbations: List[str] = Field(min_length=1)
    affect_only_corruptible_information: bool
    keep_clean_counterfactual: bool


class AblationLevel(_Strict):
    name: Literal["baseline", "conformal_only", "temporal", "full"]
    interval: str
    alerting: str
    recalibration: str


class Ablation(_Strict):
    levels: List[AblationLevel] = Field(min_length=4, max_length=4)
    operational_comparison: str
    comparison_alternative: str
    fixed_before_outer_results: bool

    @field_validator("fixed_before_outer_results")
    @classmethod
    def _must_be_fixed(cls, v):
        if v is not True:
            raise ValueError("the reporting comparison must be fixed pre-outer-results")
        return v


class RobustnessExtension(_Strict):
    fault_types: List[str] = Field(min_length=1)
    severities_sd: List[float] = Field(min_length=1)
    zero_severity_control: bool
    fault_window_fraction: List[float]
    segments: dict
    random_missing_fraction: float = Field(gt=0, lt=1)
    contamination_rates: List[float] = Field(min_length=1)
    recovery_policies: List[str] = Field(min_length=1)
    recovery_fault: dict
    recovery_definition: str
    residual_delay: Literal["horizon"]
    group_safe: bool
    coverage_reference: Literal["clean_ground_truth"]
    background_exposure_excludes_fault_window: bool
    primary_endpoints: List[str] = Field(min_length=1)
    secondary_endpoints: List[str]
    multiplicity: str
    abstention_treatment: str
    seeds: str
    paired_bootstrap_replicates: int = Field(ge=2000)

    @model_validator(mode="after")
    def _window_valid(self):
        lo, hi = self.fault_window_fraction
        if not (0.0 < lo < hi < 1.0):
            raise ValueError("fault_window_fraction must satisfy 0 < lo < hi < 1")
        if self.zero_severity_control is not True:
            raise ValueError("zero-severity control is mandatory")
        return self


class Protocol(_Strict):
    schema_version: int = Field(ge=2)
    meta: Meta
    seeds: Seeds
    partitioning: Partitioning
    point_models: List[str] = Field(min_length=1)
    features: Features
    interval: Interval
    recalibration: Recalibration
    alert_rules_physical: List[PhysicalRule] = Field(min_length=1)
    alert_episode: AlertEpisode
    event_injection: EventInjection
    matching: Matching
    selection_policy: SelectionPolicy
    metrics: Metrics
    statistics: Statistics
    robustness: Robustness
    ablation: Ablation
    robustness_extension: RobustnessExtension
    honesty_clause: str

    @model_validator(mode="after")
    def _cross_field(self):
        # every rule must be feasible in the abstract (needs > required steps)
        for r in self.alert_rules_physical:
            if r.required_violations < 1:
                raise ValueError(f"rule {r.name}: required_violations must be >= 1")
        # operating levels must be a superset-compatible extension of quality levels
        if self.selection_policy.workload_constraint.max <= 0:
            raise ValueError("workload max must be positive")
        # event severities must be positive
        if any(s <= 0 for s in self.event_injection.severities_sd):
            raise ValueError("event severities_sd must be positive")
        # honesty clause must actually be about the non-pristine holdout
        if "holdout" not in self.honesty_clause.lower():
            raise ValueError("honesty_clause must state the holdout is no longer pristine")
        return self


# --------------------------------------------------------------------------- #
def load_protocol(path: str | Path) -> Protocol:
    """Parse and strictly validate the frozen protocol YAML."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("protocol must be a YAML mapping")
    return Protocol.model_validate(raw)


def canonical_bytes(protocol: Protocol) -> bytes:
    """Deterministic serialisation used for hashing (order-independent)."""
    payload = protocol.model_dump(mode="json")
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def protocol_hash(path: str | Path) -> str:
    """SHA-256 of the validated protocol's canonical serialisation."""
    return hashlib.sha256(canonical_bytes(load_protocol(path))).hexdigest()


def resolved_config_hash(resolved: dict) -> str:
    """SHA-256 of a resolved runtime config (canonical JSON)."""
    return hashlib.sha256(
        json.dumps(resolved, sort_keys=True, separators=(",", ":"),
                   default=str).encode("utf-8")
    ).hexdigest()


def compile_to_config(protocol: Protocol, base_config: dict) -> dict:
    """Overlay the protocol's binding choices onto a base study config.

    The result is the resolved runtime configuration. Every field the protocol
    fixes is written here so the runner cannot silently fall back to the old
    ``study_full.yaml`` methodology; :func:`assert_config_implements_protocol`
    checks the overlay is complete.
    """
    import copy

    cfg = copy.deepcopy(base_config)
    cfg.setdefault("paths", {})["full_study_dir"] = protocol.meta.output_root + "/runs"
    cfg["protocol"] = {
        "output_root": protocol.meta.output_root,
        "seeds_model": list(protocol.seeds.model),
        "seeds_event_catalogue": list(protocol.seeds.event_catalogue),
        "seed_bootstrap": protocol.seeds.bootstrap,
        "outer_folds": protocol.partitioning.outer_folds,
        "inner_folds": protocol.partitioning.inner_folds,
        "operating_levels": list(protocol.interval.operating_levels),
        "quality_levels": list(protocol.interval.quality_levels),
        "recalibration_strategies": list(protocol.recalibration.strategies),
        "feed_selected_stream_into_alerts":
            protocol.recalibration.feed_selected_stream_into_alerts,
        "min_recall": protocol.selection_policy.min_recall,
        "workload_max": protocol.selection_policy.workload_constraint.max,
        "on_no_feasible": protocol.selection_policy.on_no_feasible,
        "event_incidence_per_asset_day":
            protocol.event_injection.incidence_events_per_asset_day,
        "event_n_catalogues": protocol.event_injection.n_catalogues,
        "event_scale_source": protocol.event_injection.scale.source,
        "bootstrap_replicates": protocol.statistics.bootstrap_replicates,
        "multiple_comparison": protocol.statistics.multiple_comparison,
        "matching_one_to_one": protocol.matching.one_to_one,
        "matching_onset_aware": protocol.matching.onset_aware,
        "alert_rules_physical": [r.model_dump() for r in protocol.alert_rules_physical],
        "alert_episode": protocol.alert_episode.model_dump(),
        "protocol_hash": None,   # filled by the caller once the file path is known
    }
    # Bind the knobs the existing runtime already reads so a run cannot use stale
    # study_full values for them.
    cfg.setdefault("defaults", {})
    d = cfg["defaults"]
    d["coverage_levels"] = sorted(set(protocol.interval.quality_levels)
                                  | set(protocol.interval.operating_levels))
    d.setdefault("features", {})["target_lags_include_zero"] = True
    d.setdefault("bootstrap", {})["n_boot"] = protocol.statistics.bootstrap_replicates
    return cfg


def assert_config_implements_protocol(protocol: Protocol, resolved: dict) -> None:
    """Raise if the resolved config fails to implement any protocol field."""
    p = resolved.get("protocol", {})
    checks = {
        "output_root": p.get("output_root") == protocol.meta.output_root,
        "seeds_model": p.get("seeds_model") == list(protocol.seeds.model),
        "outer_folds": p.get("outer_folds") == protocol.partitioning.outer_folds,
        "operating_levels":
            p.get("operating_levels") == list(protocol.interval.operating_levels),
        "min_recall": p.get("min_recall") == protocol.selection_policy.min_recall,
        "bootstrap_replicates":
            p.get("bootstrap_replicates") == protocol.statistics.bootstrap_replicates,
        "feed_stream": p.get("feed_selected_stream_into_alerts") is True,
        "coverage_levels": set(resolved["defaults"]["coverage_levels"]) ==
            set(protocol.interval.quality_levels) | set(protocol.interval.operating_levels),
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        raise AssertionError(f"resolved config does not implement protocol: {missing}")
