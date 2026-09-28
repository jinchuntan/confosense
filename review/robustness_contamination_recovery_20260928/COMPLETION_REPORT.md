# Robustness, contamination and recovery completion

Status: **passed and delivered scientifically**. All 60 frozen units and 900 intended cells were accepted. The accepted `bdg2_h1_f2_s42` pilot supplied 15 cells without repeated execution; the other 59 units supplied 885 cells. The separate operational grid remained paused and was not used.

## Frozen identities and scope

- Preparation commit: `138c9d6d47b01953669d8d4b88e4e662ac5e2fc4`, verified as an ancestor of the delivered work.
- Crosswalk: 60 units, 900 cells, SHA-256 `3c089f4e044ec2711a197fe24b2971be61af730a3bb3a81184e8f24b3b1b53ae`; its bytes match the preparation commit.
- Protocol canonical commit bytes: SHA-256 `68e1f9fbcee422bc1e8bc07ffa3954aa30ece4fc31102669b00b1508d02462a7`, Git blob `82ab48374946f67b04a626e5ad43da6da5503fb3`.
- Protocol execution working bytes: SHA-256 `e65f52b9c7ee2510e185c7ea83da5068760dd399bee39c6e7e9e13a22ef451a4`. The difference is CRLF checkout conversion only: normalized content and `git hash-object` are identical to the preparation blob.
- Exact owners: all 60 mappings were honored. Eight missing higher-level owners were constructed; no 0.95 substitution, point-model refit, new seed, fault redefinition, or operational-policy reselection occurred.

## Reconciled operation ledger

| Operation | Actual |
| --- | ---: |
| Quantile-estimator fits for eight missing owners | 24 |
| Wrapper conformalizations for those owners | 8 |
| Replay model fits / replay conformalizations / new seeds | 0 / 0 / 0 |
| Distinct corrupted-feature rebuilds | 480 |
| Saved-owner inference passes | 540 |
| Emitted cell streams | 900 |
| Contamination reconstructions (nonzero) | 180 (120) |
| Recovery-policy computations | 180 |
| Group-specific recovery rows | 2,415 |
| Point-metric rows from saved predictions | 120 |
| Independent validations / zero-fit resumes | 60 / 60 |

Recovery `level_shift@2` reuses the matching fault feature/inference stream, and contamination reuses clean test features and point predictions. MAPIE's internal calibrator call is nested inside each of the eight authorized wrapper conformalizations. These nested operations were recorded but not double-counted.

## Validation and integrity

Every unit passed separate validation of exact zero-control stream equivalence, calibration-only contamination, causal feature propagation, delayed residual availability, group-specific physical follow-up, censoring, operation accounting, and checkpoint identity. Every resume was zero-fit and left the unit `COMPLETE.json` SHA-256 unchanged. The final focused suite passed 10/10 tests without fitting, including rejection of deliberately corrupted evidence.

Versioned implementation corrections preserved their failed evidence: raw missing-group identity for PLEIA, canonical missing-group identity in PLEIA recovery, outer-test-only RICO fault application, a full-length v4 checkpoint pin, transient atomic replacement retry, and the frozen aggregation metric schema. None changed a fault definition, owner mapping, output tolerance, or accepted scientific output.

## Descriptive scientific findings

These are descriptive diagnostics over frozen folds and correlated seed aliases, not population estimates.

- Exact zero controls matched clean streams and their derived metrics for all 60 units.
- Mean during-window coverage loss for `level_shift@2` was 0.878 in BDG2, 0.379 in PLEIA, 0.664 in PLEIA Energy, and 0.860 in RICO. In PLEIA, stuck/dropout were slightly more damaging on this summary (loss about 0.407). Random missing was mild in BDG2 (-0.009), PLEIA Energy (-0.011), and RICO (+0.008), but reduced PLEIA coverage by 0.087.
- Calibration-only contamination preserved test targets, features, and point predictions. Mean interval width changed from clean-reference to 5%/10% contamination as follows: BDG2 132.99 to 646.49/650.99; PLEIA 3.26 to 9.66/10.04; PLEIA Energy 0.77 to 1.00/1.07; RICO 1.37 to 10.15/10.23. Coverage generally increased with this widening; it is not a free robustness gain.
- All 450 BDG2 group-policy recovery rows were observed. PLEIA observed 10/15 static, 13/15 periodic, and 15/15 rolling recoveries; PLEIA Energy observed 12/15, 13/15, and 15/15. RICO observed 578/625 static, 523/625 periodic, and 312/625 rolling recoveries. The remaining 474/2,415 rows are retained as right-censored, not converted to recoveries.
- Scalar `fault_detected` is unavailable in 450/900 multi-group cells and scalar detection delay in 482/900 cells; group detection rates remain available for every cell. This preserves unavailable metrics rather than manufacturing scalar summaries.

Population intervals are unavailable in all 13 declared scopes because seed aliases reuse fold observations, while groups and stream rows are not independent population replicates. `INFERENCE_STATUS.csv` is the authoritative status table.

## Runtime and resources

The durable supervised interval from first launch to successful backup was 3 h 47 min 13 s, including safe resource waits, preserved failed attempts, corrections, aggregation, and backup. Accepted replay work used 2,429.42 s; independent validation used 4,241.01 s; zero-fit resume checks used 76.58 s. Dataset replay+validation+resume totals were 3,566.66 s BDG2, 1,452.55 s PLEIA, 607.57 s PLEIA Energy, and 1,120.23 s RICO.

Peak worker RSS was 1,254,297,600 bytes (1.168 GiB) and peak process commit was 2,498,318,336 bytes (2.327 GiB), within the frozen limits. The completion manifest covers 917 files and 1,227,726,258 bytes (1.143 GiB); the previously backed-up pilot adds 47,742,826 bytes. The verified backup reproduces those completion bytes exactly. Both copies share C:, so redundancy must not be mistaken for independent capacity.

## Compact evidence index

- `COMPLETION_RESULT.json`: completion counts, operations, time, memory, and aggregate hashes.
- `AGGREGATE_CELL_METRICS.csv`: all 900 cell-level descriptive metrics.
- `AGGREGATE_SEED_MEANS.csv`: explicitly non-population seed-alias summaries.
- `AGGREGATE_RECOVERY_BY_GROUP.csv`: all 2,415 observed/censored group-policy rows.
- `AGGREGATE_POINT_ACCURACY.csv`: saved-prediction accuracy checks with zero fits.
- `INFERENCE_STATUS.csv`: explicit inference availability and reasons.
- `CONSTRUCTED_OWNERS.json`: exact eight-owner construction identities and operation counts.
- `BACKUP_VERIFICATION.json`: compact link to the full verified raw manifest.
- `SCIENTIFIC_REPLAY_CONTRACT.json`: accepted checkpoint roots and correction provenance.

Bulk streams, owners, checkpoints, validation evidence, ledgers, and failed attempts remain outside Git and are preserved in the verified backup workflow. Git publication is intentionally limited to compact protocol, implementation, aggregate, and delivery evidence.
