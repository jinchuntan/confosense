# Operational005 high-coverage extension: evidence index

A separately versioned extension of the BDG2 one-hour operational005 causal replay. It completes the
99 candidates that the frozen replay recorded as unavailable: CQR and uncalibrated quantiles at
nominal 0.975, 0.99 and 0.995, over outer folds 0 to 2 and model seeds 42 to 46. That is 1,485
evaluation rows in 495 policy blocks. These results are separate from the candidature report. The
accepted operational005 outputs, the candidature evidence package and the frozen tag
`candidature-evidence-20261002-v1` are unchanged.

## Results

- [Extension report](results/REPORT.md) and [native-support trade-off figure](results/combined_tradeoff_native.png)
- [Extension metrics, 2,970 native and common views of 1,485 rows](results/extension_operational_metrics.csv) and [extension candidate summary](results/extension_candidate_summary.csv)
- Combined with the 165 accepted candidates, which are read from their committed blobs and not rewritten: [264-candidate summary](results/combined_candidate_summary.csv), [3,960-row evaluation inventory](results/combined_evaluation_inventory.csv), [candidate inventory](results/combined_candidate_inventory.csv) and [by-method table](results/combined_by_method_level_strategy.csv)
- [Completion validation](results/COMPLETION_VALIDATION.json) and [independent post-aggregation check](INDEPENDENT_RESULT_CHECK.json)

## Protocol and scope

- [Authorization reference](AUTHORIZATION_REFERENCE.md)
- [Extension protocol, revision 1.3](EXTENSION_PROTOCOL.json). Predecessors: [1.0](EXTENSION_PROTOCOL_V1_0.json), [1.1](EXTENSION_PROTOCOL_V1_1.json) and [1.2](EXTENSION_PROTOCOL_V1_2.json).
  - 1.1 corrected a validator shape check; its failure is recorded in [OWNER_VALIDATION_FAILURE_V1_0.json](OWNER_VALIDATION_FAILURE_V1_0.json).
  - 1.2 changed scheduling only.
  - 1.3 corrected the report's source attribution.
- Queue derived from the frozen definitions: [evaluation queue](extension_evaluation_queue.csv), [metric views](extension_metric_view_queue.csv), [policy blocks](extension_block_queue.csv) and [owner fits](extension_owner_queue.csv).
- Pre-scheduling checks: [later-work check](LATER_WORK_CHECK.json), which found no overlap with accepted or published work, and [saved-owner search](SAVED_OWNER_SEARCH.json), which found no reusable BDG2 owner.
- [Science-root manifest](SCIENCE_ROOT_MANIFEST.json): the pinned input copy. The 2026-10-02 checkout rewrote line endings, so each frozen input is written in the byte variant that matches its pin.

## Execution and validation

- [Pilot gate](PILOT_VALIDATION.json), unit `bdg2_f0_s42`, covering all three levels
- Owner receipts for all 15 units: [manifests, validations and zero-fit resumes](receipts/owners/), plus the [fit ledger](receipts/fit_ledger.jsonl)
  - Totals: 45 CQR wrapper fits, 135 quantile-estimator fits and 90 conformalize operations.
- [Per-block validation summary](receipts/BLOCK_VALIDATION_SUMMARY.csv), 495 blocks. Each block passed:
  - the frozen validator;
  - an extended validator that rebuilds intervals and recomputes metrics independently;
  - a zero-fit resume.
- [Supervisor summary](receipts/SUPERVISOR_SUMMARY.json)
- [Backup verification](BACKUP_VERIFICATION.json)

Bulk owners, streams and logs remain at `D:\ConfoSenseStorage\runs\op005_hicov_v1`, with a
hash-verified archive copy under `D:\ConfoSenseStorage\backups\operational005_high_coverage_extension_20261003\run_v1`.

All results are descriptive. Folds, model seeds, catalogue seeds and the native and common support
views are not population replicates, and no setting was selected from test outcomes.
