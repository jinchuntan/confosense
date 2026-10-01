# Operational005 causal-replay evidence index

- [Frozen protocol](PROTOCOL.json), [candidate queue](evaluation_queue.csv), [candidate definitions](candidate_definitions.csv), and [owner inventory](owner_inventory.csv)
- [Parallel reverse helper](parallel_reverse_v1.py), [completion validator/delivery](completion_delivery_v1.py), and [guarded delivery supervisor](completion_supervisor_v1.py)
- [Independent completion validation](COMPLETION_VALIDATION.json) and [operational report](OPERATIONAL_REPORT.md)
- [Validated operational metrics](../../smart_building_conformal/outputs/operational005_causal_replay_v2/analysis_v1/operational_metrics.csv), [candidate summary](../../smart_building_conformal/outputs/operational005_causal_replay_v2/analysis_v1/candidate_summary.csv), [explicitly unavailable metrics](../../smart_building_conformal/outputs/operational005_causal_replay_v2/analysis_v1/unavailable_metrics.csv), and [trade-off figure](../../smart_building_conformal/outputs/operational005_causal_replay_v2/analysis_v1/operational_tradeoff.png)
- [Aggregate validation](../../smart_building_conformal/outputs/operational005_causal_replay_v2/analysis_v1/analysis_validation.json) and [aggregate report](../../smart_building_conformal/outputs/operational005_causal_replay_v2/analysis_v1/REPORT.md)
- [Verified external backup](BACKUP_VERIFICATION.json)
- [Commit-pinned HTTPS readback](GITHUB_REMOTE_READBACK.json) and [final delivery receipt](DELIVERY_RECEIPT.json)

The readback receipt verifies the earlier substantive commit, not itself. Raw replay evidence remains outside Git in the D: package recorded by the backup receipt. The separate operational policy execution is complete, but population inference remains unavailable under the recorded dependent design.
