# Results changelog — corrected final dissertation study

Chronological record of every methodology/code change on
`fix/final-dissertation-study`. No corrected performance number is reported here or
anywhere until its source CSV exists; this session lays the audited foundation and a
predeclared protocol, not corrected results.

## Session 1 — audit, plan, first leakage fixes, frozen protocol
- **Audit (grounded, read-only):** three source audits confirmed the defect map in
  `FINAL_STUDY_REPAIR_PLAN.md` and `audit/leakage_audit.json`, each with file:line.
- **A1 target-time leakage — FIXED.** `windowing.apply_horizon_embargo` drops any origin
  whose target crosses the next partition boundary; recorded as an `embargo` partition in
  the split audit. No-op for RICO whole-run groups. Commit `64901cd`.
  - Test: `test_no_target_time_leakage_across_partitions_chronological`,
    `test_horizon_embargo_is_noop_for_group_partitioner`.
- **B1 target_lag_0 — FIXED.** `windowing.feature_config` guarantees lag 0 (`y_t`, available
  at the origin and used by persistence). Commit `64901cd`.
  - Test: `test_feature_config_injects_lag_zero_equal_to_yt`.
- **Frozen protocol predeclared** (`protocol/frozen_protocol.yaml`, hashed in
  `config_hash.txt`) and `protocol/evaluation_design.md` — written before any corrected
  outer-fold result was inspected.
- **Tests:** full suite 186 passed, 1 skipped, 0 failed (was 183 passed pre-repair; +3 new).

## Session 2 — executable protocol, corrected primitives, validator
No corrected performance number is reported: the nested full run has not been
executed, so nothing here is a result. This session made the predeclaration
executable and implemented the corrected code with regression tests.

- **Protocol made executable (amendment 001).** `frozen_protocol.yaml` did not
  parse in session 1 (episode nested in a sequence), so its recorded hash was of
  invalid bytes. Repaired before any corrected result existed: valid YAML,
  `src/protocol.py` strict pydantic validator + compiler, executable
  `configs/study_final_dissertation_v2.yaml`, new canonical hash
  `1e4506d2…`. Commit `4c19ad6`. Tests: `tests/test_protocol.py` (12).
- **C1 causal group-safe updated EnbPI — FIXED and wired.** Online intervals now
  recentre on the base prediction and offset by the residual pool observable
  *within the same group* (reusing `DelayedResidualPool`); the interval stage
  passes group ids and origin/target times. Commit `69037dd`. Tests:
  `tests/test_enbpi_causal.py` (4).
- **D2/D3/D6/D7/D8 corrected alert primitives — implemented and unit-tested**
  (`src/alerts_corrected.py`): physical-time rule conversion with `not_applicable`
  marking; group-safe k-of-m / episodes / cooldown; one-to-one onset-aware
  matching; macro synthetic-event recall + background episodes per monitored
  asset-day; `no_feasible_configuration`. Commit `20fbeb8`. Tests:
  `tests/test_alerts_corrected.py` (14). *Wiring into the orchestrator's alert
  stage is the remaining integration step (still PENDING: C3, D1, D4, E).*
- **B2/B3/A2/D5 — FIXED / implemented.** feature-schema persistence
  (`data_profiles/feature_schema_h{h}.json`, wired into stage_prepare); BDG2
  configured-weather loud-fail; whole-run nested subsplit; per-group train-only
  MAD-to-sigma event scaling. Commit `e8f445b`. Tests:
  `tests/test_corrections_bde.py` (5), `tests/test_bdg2_weather.py` (3).
- **Machine-checkable validator** `src/validate_final_study.py` — writes
  `PUBLICATION_READY.json` only on a clean pass; currently and correctly reports
  NOT ready (no completed non-fast run; C3/D1/D4/E pending). Commit `3d3b8a7`.
- **Tests:** full suite 224 passed, 1 skipped (was 198 after session-1 protocol).

## Still pending (require the nested end-to-end engine)
C3/E end-to-end recalibration→alert integration and single evaluated pipeline
object; D1 remove hard-wired CQR@95% operating choice; D4 exposure-based event
allocation wired into the run; wiring A2/D2/D3/D5/D6/D7/D8 into that engine; then
the nested multi-seed full run, 2000-replicate CIs, 10 figures and the report
suite. `outputs/full_study/` remains byte-for-byte unchanged throughout.
