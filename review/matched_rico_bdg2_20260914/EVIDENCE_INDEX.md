# Matched RICO and BDG2 evidence index

Branch: [review/matched-rico-bdg2-20260914](https://github.com/jinchuntan/confosense/tree/review/matched-rico-bdg2-20260914). Evaluated pre-fit commit: `350ef4fd1c92c12a982df2b8366023937515b65b`. Final publication SHA is supplied by the delivery and branch history. Both authorized units completed; no additional batch ran.

- [Combined completed report](../../RICO_BDG2_MATCHED_FIRST_UNITS_REPORT.md), [concrete twelve-unit proposal](../../MATCHED_NEXT_BATCH_PROPOSAL.md)
- [Current authorizing handoff](AUTHORIZING_HANDOFF.md), [authorization](../../smart_building_conformal/configs/matched_forecasting005_rico_bdg2_authorization.json), [pre-fit record](PRE_FIT_EXECUTION.md), [joint identity manifest](joint_pre_fit_manifest.json)
- [Exact evaluated source archive](evaluated_source.zip), [runner](../../smart_building_conformal/src/matched_forecasting005.py), [guard repair](../../smart_building_conformal/src/matched_models005.py), [independent validator](../../smart_building_conformal/src/matched_validation005.py)
- [Fresh roles/dates](fresh_role_support.csv), [original-group history](role_group_history.csv), [sequence boundary verification](sequence_group_verification.csv)
- [Publication manifest](EVIDENCE_MANIFEST.csv), [preservation/publication validation](publication_validation.json), [report-helper archive](review_helpers.zip), [data attribution](DATA_NOTICE.md)
- [Reporting attempts](reporting_attempts.json), [preserved failed analysis status](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v1/ATTEMPT_STATUS.json)

## Summary CSVs

All links below are repository-relative. Use `pandas.read_csv(path, keep_default_na=False, float_precision="round_trip")` to preserve string IDs and numeric round trips. Empty final-epoch fields are inapplicable to persistence/XGBoost, not zero-epoch fits. No CSV upload by the user is needed.

| File | Purpose |
|---|---|
| [rico_comparison.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/rico_comparison.csv) | Three RICO model rows, errors, both interval levels, selection and model-phase cost. |
| [bdg2_comparison.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/bdg2_comparison.csv) | Three BDG2 model rows with the same complete fields. |
| [pooled_comparison.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/pooled_comparison.csv) | Both units pooled over target rows, clearly labelled units/horizons. |
| [group_metrics.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/group_metrics.csv) | Every original RICO run / BDG2 building: point and 90/95 interval metrics, support and negative-output counts. |
| [rico_phase_metrics.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/rico_phase_metrics.csv) | Separate sample-weighted acquisition-phase summaries. |
| [equal_group_diagnostics.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/equal_group_diagnostics.csv) | Explicit equal-run/equal-building diagnostics, separate from pooled results. |
| [model_costs.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/model_costs.csv) | Tuning/final/calibration/inference/serialization, CPU, throughput, memory and actual launch RAM. |
| [run_costs.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/run_costs.csv) | Command wall/CPU, preparation, action/lifetime memory, audit/resume and storage costs. |
| [checkpoint_io.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/checkpoint_io.csv) | Atomic checkpoint writing measurements, separate from model phases. |
| [command_measurements.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/command_measurements.csv) | All successful/failed attempts with exact command, PID, start/end, exit and fit count. |
| [tuning_comparison.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/tuning_comparison.csv) | All sixteen tuning candidate/fold outcomes and best epochs. |
| [target_diagnostics.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/target_diagnostics.csv) | Unfiltered zeros, repeated values and target extrema by task/role. |
| [all_four_settings.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/all_four_settings.csv) | Eighteen model rows across six completed paired units, all four settings. |
| [paired_descriptive_contrasts.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/paired_descriptive_contrasts.csv) | Within-unit LSTM-minus-XGBoost errors/interval scores and cost ratios; no pooled cross-unit ranking. |
| [evidence_reuse_ledger.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/evidence_reuse_ledger.csv) | Original source, protocol and full run-file-tree identities, with zero historical refits. |
| [completion_overlay.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/completion_overlay.csv) | Versioned 6/195 paired-unit completion; original and earlier overlays untouched. |
| [remaining_queue_updated.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/remaining_queue_updated.csv) | 189 remaining units in preserved queue order with same-dataset measured timing scenarios. |
| [measured_task_timing_references.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/measured_task_timing_references.csv) | Actual six paired-unit model-phase measurements used for all four settings. |
| [next_batch_units.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/next_batch_units.csv) | Twelve specifically enumerated proposed keys, counts, order and commands; not launched. |
| [analysis_validation.json](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/analysis_validation.json) | Independent group-to-pooled reconciliation and complete analysis outcomes. |
| [verification_summary.csv](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/verification_summary.csv) | Actual exits, metric/artifact cell counts, maximum reload discrepancies and zero-fit resume outcomes. |

## Per-unit protocols, artifacts and independent checks

### rico: h5/fold2/seed42

- [Frozen protocol](../../smart_building_conformal/protocols/matched_forecasting005/rico_h5_f2_s42_v2/frozen_protocol.json), [all ordered memberships](../../smart_building_conformal/protocols/matched_forecasting005/rico_h5_f2_s42_v2/membership.csv.gz), [readiness](../../smart_building_conformal/protocols/matched_forecasting005/rico_h5_f2_s42_v2/readiness.json)
- [Point metrics](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2/point_summary.csv), [interval metrics](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2/interval_quality.csv), [actual exit](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2.log.json), [process cost](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2.process.json), [fit journal](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2/fit_calls.jsonl), [execution environment](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2/execution_environment.json)
- [Independent validation](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2_audit/validation.json), [recomputed points](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2_audit/recomputed_point_metrics.csv), [recomputed intervals](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2_audit/recomputed_interval_metrics.csv), [saved-model verification](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2_audit/saved_model_verification.csv), [selection](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2_audit/independent_selection.csv), [phase resources](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2_audit/phase_measurements.csv), [nested fit resources](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2_audit/learned_fit_measurements.csv)
- [Zero-fit resume](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_validation_v1/rico_h5_f2_s42_v2_resume.json), [resume command exit](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_validation_v1/rico_h5_f2_s42_v2_resume.log.json)

| Model | Fitted artifact and complete per-row evidence |
|---|---|
| persistence | [artifact](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2/units/rico_h5_f2_s42_persistence/model.json), [all unit files](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2/units/rico_h5_f2_s42_persistence) |
| xgboost | [artifact](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2/units/rico_h5_f2_s42_xgboost/model.ubj), [all unit files](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2/units/rico_h5_f2_s42_xgboost) |
| attention_lstm | [artifact](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2/units/rico_h5_f2_s42_attention_lstm/model.pt), [all unit files](../../smart_building_conformal/outputs/matched_forecasting005/rico_h5_f2_s42_v2/units/rico_h5_f2_s42_attention_lstm) |
### bdg2: h1/fold2/seed42

- [Frozen protocol](../../smart_building_conformal/protocols/matched_forecasting005/bdg2_h1_f2_s42_v2/frozen_protocol.json), [all ordered memberships](../../smart_building_conformal/protocols/matched_forecasting005/bdg2_h1_f2_s42_v2/membership.csv.gz), [readiness](../../smart_building_conformal/protocols/matched_forecasting005/bdg2_h1_f2_s42_v2/readiness.json)
- [Point metrics](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2/point_summary.csv), [interval metrics](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2/interval_quality.csv), [actual exit](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2.log.json), [process cost](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2.process.json), [fit journal](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2/fit_calls.jsonl), [execution environment](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2/execution_environment.json)
- [Independent validation](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2_audit/validation.json), [recomputed points](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2_audit/recomputed_point_metrics.csv), [recomputed intervals](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2_audit/recomputed_interval_metrics.csv), [saved-model verification](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2_audit/saved_model_verification.csv), [selection](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2_audit/independent_selection.csv), [phase resources](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2_audit/phase_measurements.csv), [nested fit resources](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2_audit/learned_fit_measurements.csv)
- [Zero-fit resume](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_validation_v1/bdg2_h1_f2_s42_v2_resume.json), [resume command exit](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_validation_v1/bdg2_h1_f2_s42_v2_resume.log.json)

| Model | Fitted artifact and complete per-row evidence |
|---|---|
| persistence | [artifact](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2/units/bdg2_h1_f2_s42_persistence/model.json), [all unit files](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2/units/bdg2_h1_f2_s42_persistence) |
| xgboost | [artifact](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2/units/bdg2_h1_f2_s42_xgboost/model.ubj), [all unit files](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2/units/bdg2_h1_f2_s42_xgboost) |
| attention_lstm | [artifact](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2/units/bdg2_h1_f2_s42_attention_lstm/model.pt), [all unit files](../../smart_building_conformal/outputs/matched_forecasting005/bdg2_h1_f2_s42_v2/units/bdg2_h1_f2_s42_attention_lstm) |

Each model directory includes `predictions.csv.gz` (both levels), `calibration.csv.gz` (own residuals), `fitting_membership.csv.gz`, `tuning_predictions.csv.gz`, `tuning.csv.gz`, `training_history.csv.gz`, `payload.json` and `COMPLETE.json` hashes. Learned final artifacts include all required model/preprocessing state. XGBoost's actual booster configuration is separate; LSTM reload uses `weights_only=True`. Both levels share the same trained model.

## Reproduction and preserved evidence

From `smart_building_conformal`, with the recorded environment/data and exact evaluated source bytes, use fresh receipt directories:

```powershell
# Replace dataset/horizon/stem together for BDG2: bdg2 / 1 / bdg2_h1_f2_s42_v2.
& C:/cfs_venv/Scripts/python.exe -B -m src.matched_forecasting005 validate --matrix outputs/amendment005/support_design_v1/experiment_matrix.csv --dataset rico --horizon 5 --outer-fold 2 --model-seed 42 --design-dir protocols/matched_forecasting005/rico_h5_f2_s42_v2 --out outputs/matched_forecasting005/rico_h5_f2_s42_v2 --receipt outputs/matched_forecasting005/rico_recheck
& C:/cfs_venv/Scripts/python.exe -B -m src.matched_forecasting005 resume --forbid-fits --matrix outputs/amendment005/support_design_v1/experiment_matrix.csv --dataset rico --horizon 5 --outer-fold 2 --model-seed 42 --design-dir protocols/matched_forecasting005/rico_h5_f2_s42_v2 --out outputs/matched_forecasting005/rico_h5_f2_s42_v2 --receipt outputs/matched_forecasting005/rico_resume_recheck.json
```

Validation/resume never authorize new fitting. Source/config/package/data or checkpoint mismatch must fail. The archive preserves raw evaluated source bytes, including line endings; use an isolated copy if a checkout changes those bytes. Recomputing published group/pooled arithmetic requires only the saved CSVs and analysis helper; recreating features for fitted-model checks additionally requires the original data. The existing local source/data were used for the actual recorded checks.

[Fifteen regression checks](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_validation_v1/regression.log), [successful joint preflight](../../smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_validation_v1/joint_preflight_v2.log.json), [entry preservation hashes](entry_preservation.json) and the exact failed attempts are retained. No historical output or original protocol was rewritten. The historical [energy report](../../PLEIA_ENERGY_MATCHED_H1_REPORT.md), [temperature pilot](../../MODEL_COMPARISON_PILOT_REPORT.md) and [BDG2 operational report](../../BDG2_THREEFOLD_BENCHMARK_REPORT.md) remain available with their original identities and abstentions.

The publication manifest excludes itself and publication_validation.json to avoid recursive hashes; final Git identity binds both. Remote SHA/content checks and the additional backup are recorded externally and confirmed in the delivery. Main and previous review branches remain unchanged.
