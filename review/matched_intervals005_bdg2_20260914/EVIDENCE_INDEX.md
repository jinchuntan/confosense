# Matched intervals005 / BDG2 pilot evidence index

[User authorization](USER_AUTHORIZATION.txt), [complete pinned handoff](AUTHORIZING_HANDOFF.md), [entry preservation](entry_preservation.json), [method/reference attribution](METHOD_REFERENCES.md), [synthetic acceptance](SYNTHETIC_ACCEPTANCE.json), [retained fixture recovery](SYNTHETIC_RECOVERY.md), and [durable progress/restart](PROGRESS_AND_RESTART.md).

[Exact pre-fit commands and identities](joint_pre_fit_manifest.json). [Evaluated commit](evaluated_commit.json). [Evaluated source archive](evaluated_source.zip).

[Supplemental no-fit DSCP truth-independence acceptance](SUPPLEMENTAL_ACCEPTANCE.md).

[Native CQR validation/specification erratum](VALIDATION_ERRATUM.md), [resolved method specification](method_specification_resolved_v2.json), [exact read-only source manifest](VALIDATION_ERRATUM.json), and [corrected validation source](corrected_validation_source.zip).

**Preceding validation correction:** [EnbPI precision erratum](VALIDATION_ERRATUM_V3.md), [revision-3 source manifest](VALIDATION_ERRATUM_V3.json), [exact recovery commands](VALIDATION_RECOVERY_COMMANDS_V3.json), and [final corrected validation source](corrected_validation_source_v3.zip). Both earlier failed validators are retained.

**Native-point correction:** [native-point roundtrip erratum](VALIDATION_ERRATUM_V4.md), [revision-4 source manifest](VALIDATION_ERRATUM_V4.json), [exact recovery commands](VALIDATION_RECOVERY_COMMANDS_V4.json), and [final validation source](corrected_validation_source_v4.zip). All three earlier failed validators are retained.

**Current accepted validation source:** [cleanup import record](VALIDATION_ERRATUM_V5.md), [revision-5 source manifest](VALIDATION_ERRATUM_V5.json), [exact recovery commands](VALIDATION_RECOVERY_COMMANDS_V5.json), and [current source archive](corrected_validation_source_v5.zip). All four earlier failed validators are retained.

[Implementation report](../../MATCHED_INTERVALS005_IMPLEMENTATION_REPORT.md), [completed numerical report](../../BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md), [panel response](PANEL_RESPONSE.md), and [current evidence](../CURRENT_EVIDENCE.md).

## Protocol and scientific results

- [frozen_protocol.json](../../smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s42_v1/frozen_protocol.json)
- [method_specification.json](../../smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s42_v1/method_specification.json)
- [scope.csv](../../smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s42_v1/scope.csv)
- [native_membership.csv.gz](../../smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s42_v1/native_membership.csv.gz)
- [joint_fit.csv.gz](../../smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s42_v1/joint_fit.csv.gz)
- [joint_calibration.csv.gz](../../smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s42_v1/joint_calibration.csv.gz)
- [joint_test.csv.gz](../../smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s42_v1/joint_test.csv.gz)
- [readiness.json](../../smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s42_v1/readiness.json)

[Scientific checkpoints, serialized owners/calibrators, exact raw and issued/consumed streams](../../smart_building_conformal/outputs/matched_intervals005/bdg2_f2_s42_v1/stages), [actual operation journal](../../smart_building_conformal/outputs/matched_intervals005/bdg2_f2_s42_v1/operations.jsonl), [stage journal](../../smart_building_conformal/outputs/matched_intervals005/bdg2_f2_s42_v1/stage_journal.jsonl).

- [native_support_metrics.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/native_support_metrics.csv): 30 native-support method cells.
- [common_support_metrics.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/common_support_metrics.csv): 30 views on the identical DSCP-supported rows.
- [per_building_metrics.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/per_building_metrics.csv): original-building counts and metrics.
- [shared_owner_contrasts.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/shared_owner_contrasts.csv): CQR minus uncalibrated and updated minus static.
- [background_workload.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/background_workload.csv): numerical/availability/combined hourly immediate episodes and exposure.
- [seasonal_point_metrics.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/seasonal_point_metrics.csv): three deterministic point computations.
- [seasonal_interval_metrics.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/seasonal_interval_metrics.csv): six seasonal own-residual interval cells.
- [worker_costs.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/worker_costs.csv): whole CLI worker wall/CPU/memory.
- [stage_costs.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/stage_costs.csv): nonoverlapping scientific stage wall/CPU/memory.
- [preparation_costs.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/preparation_costs.csv): full preparation costs, excluded from stage no-op bookkeeping.
- [enbpi_calibration_support.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/enbpi_calibration_support.csv): finite and nonfinite out-of-bag calibration score counts.
- [dscp_calibration_summary.json](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/dscp_calibration_summary.json): calibration clusters, neighbours and reused first-64 assignment cost.
- [operations.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/operations.csv): nested wrapper, learned estimator and calibrator calls; not additive runtime.
- [interval_completion_overlay.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/interval_completion_overlay.csv): 30/1950 completed method keys.
- [next_proposed_method_keys.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/next_proposed_method_keys.csv): 120 explicit unlaunched next keys.
- [next_proposed_costs.json](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/next_proposed_costs.json): measured pilot scaling and sharing counts.
- [analysis_validation.json](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/analysis_validation.json): reconciled completion counts.
- [background_and_crossing_checks.csv](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/background_and_crossing_checks.csv): 990 independent background rate/exposure checks.
- [additional_integrity_validation.json](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/additional_integrity_validation.json): crossings, exposures, seed and operation-journal reconciliation.
- native_interval_quality: [PNG](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/figures/native_interval_quality.png), [PDF](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/figures/native_interval_quality.pdf), [source hashes](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/figures/native_interval_quality.sources.json).
- common_interval_quality: [PNG](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/figures/common_interval_quality.png), [PDF](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/figures/common_interval_quality.pdf), [source hashes](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/figures/common_interval_quality.sources.json).
- stage_costs: [PNG](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/figures/stage_costs.png), [PDF](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/figures/stage_costs.pdf), [source hashes](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/analysis_v1/figures/stage_costs.sources.json).

Recompute reports without fitting from the original repository layout, using an unused output directory beneath the repository:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/matched_intervals005_bdg2_20260914/report.py --out smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/recomputed_analysis_v1
```

This creates a new analysis directory and refreshes current report prefixes. It does not modify the scientific run or historical results. Original absolute command paths remain in receipts.

[Independent validation](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/validation_v5/validation.json), [all arithmetic/model/quantile checks](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/validation_v5/reconstruction_checks.csv), [alert checks](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/validation_v5/alert_checks.csv), [zero-fit/calibrator-fit completed resume](../../smart_building_conformal/outputs/matched_intervals005/bdg2_pilot_v1_coordinator/completed_resume_v1.json).

[Final delivery and publication receipts](delivery_v1).

[Report links, figure provenance and visual review](DELIVERY_QA.json).

[Published artifact readbacks and full remote Git-tree verification](REMOTE_VERIFICATION.json). This receipt identifies the verified parent commit; the delivery commit adds the receipt and its index entry.

[Exact byte manifest](EVIDENCE_MANIFEST.csv) covers the bounded task files except itself; the Git commit binds the manifest. All previous review heads/main and the entry backup chain remain preserved.
