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

## Pending (see FINAL_STUDY_REPAIR_PLAN.md for file:line and the test for each)
A2 RICO run-aware alert subsplit; B2 feature-schema persistence; B3 BDG2 weather loud-fail;
C1 horizon-safe + group-safe updated EnbPI; C3/E end-to-end recalibration→alert integration;
D2 group-safe alert state (high priority); D3 physical-time rules; D4 incidence-based events;
D5 per-group robust event scaling; D6 onset-aware one-to-one episode matching;
D7 no_feasible_configuration; D8 macro recall + background-workload terminology;
D10 operational-level selection. Then: nested selection, fast smoke, full multi-seed run,
statistical aggregation, figures, and the report suite.
