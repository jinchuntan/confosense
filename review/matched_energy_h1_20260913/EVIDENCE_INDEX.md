# Matched PLEIA-energy horizon-1 evidence

Publication branch: [review/matched-energy-h1-20260913](https://github.com/jinchuntan/confosense/tree/review/matched-energy-h1-20260913). The implementation, immutable protocol and successful pre-fit checks were committed **before real fitting** at `697d0e6e8a7de0a2fc55c98b8341117d789390ce`. The final delivery and branch history supply the publication SHA. Parent review: `f1a71a19b4e227a9894a8e2c74686a642dca962a`. Main and all completed historical results remain unchanged.

- [Completed numerical report](../../PLEIA_ENERGY_MATCHED_H1_REPORT.md)
- [Pre-fit execution record](PRE_FIT_EXECUTION.md), [pre-fit manifest](pre_fit_execution_manifest.json), [later scoped authorization](../../smart_building_conformal/configs/matched_forecasting005_energy_h1_authorization.json)
- [Frozen protocol, schemas, parameters, libraries and identities](../../smart_building_conformal/protocols/matched_forecasting005/pleia_energy_h1_f0_s42_v1/frozen_protocol.json), [ordered memberships](../../smart_building_conformal/protocols/matched_forecasting005/pleia_energy_h1_f0_s42_v1/membership.csv.gz), [boundaries](../../smart_building_conformal/protocols/matched_forecasting005/pleia_energy_h1_f0_s42_v1/boundaries.csv), [readiness](../../smart_building_conformal/protocols/matched_forecasting005/pleia_energy_h1_f0_s42_v1/readiness.json)
- [Exact evaluated source bytes](evaluated_source.zip), [runner](../../smart_building_conformal/src/matched_forecasting005.py), [group-aware roles](../../smart_building_conformal/src/matched_data005.py), [measured model units](../../smart_building_conformal/src/matched_models005.py), [independent validator](../../smart_building_conformal/src/matched_validation005.py)
- [File/hash manifest](EVIDENCE_MANIFEST.csv), [publication and preservation validation](publication_validation.json), [review-helper source archive](review_helpers.zip)

The original no-fit proposal and `future_fitting_authorized:false` record remain historical evidence. The subsequent user authorized this implementation, necessary tiny fits and exactly one real unit. The separate later memory instruction is recorded in the new authorization; every actual real launch exceeded the original 3 GiB reference. No remaining queue, conditional challenge or full-grid experiment was launched.

## Readable CSVs and computational measurements

Paths resolve from the repository root. The preferred canonical streams are under [energy_h1_audit_v2/canonical_streams](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_audit_v2/canonical_streams); they explicitly preserve the source Python-None group as the string `None`. The immutable original v1 model streams stored that group as an empty CSV field. Every other column is identical, verified in the [schema mapping](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_audit_v2/identifier_schema_mapping.csv). Use `pandas.read_csv(path, keep_default_na=False, float_precision='round_trip')`; preserve the literal group ID `None`. Empty epoch fields are inapplicable to persistence/XGBoost, not zero epochs. Compressed CSVs can be downloaded through GitHub's raw/download control.

| File | Purpose |
|---|---|
| [matched_model_comparison.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/matched_model_comparison.csv) | Three model rows: MAE/RMSE, both nominal levels' coverage/MPIW/Winkler/rank/radius, selected candidate/epochs and measured model-phase time. |
| [point_summary.csv](../../smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1/point_summary.csv) | Original three point-summary cells, shared support, actual estimator identities, fit counts, throughput and model costs. |
| [interval_quality.csv](../../smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1/interval_quality.csv) | Original six own-model 90%/95% interval cells, exact rank/radius and quality metrics. |
| [recomputed_point_metrics.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_audit_v2/recomputed_point_metrics.csv) | Independent MAE/RMSE and negative-point diagnostics from saved streams. |
| [recomputed_interval_metrics.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_audit_v2/recomputed_interval_metrics.csv) | Independent ordered residual ranks, radii, bounds-derived coverage/width/Winkler and support. |
| [model_computational_summary.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/model_computational_summary.csv) | Separate tuning/final/calibration/inference seconds, CPU, throughput, baseline/peak/incremental memory and launch RAM. |
| [phase_measurements.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_audit_v2/phase_measurements.csv) | Detailed model phase resources and separately measured saved-artifact verification; do not add nested fit timings to parent phases. |
| [learned_fit_measurements.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_audit_v2/learned_fit_measurements.csv) | Exactly eight tuning/two final learned fits, roles, candidates, epochs, CPU and memory; these fit timers are nested within model phases. |
| [checkpoint_io_measurements.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/checkpoint_io_measurements.csv) | Per-model atomic checkpoint writing cost, separate from model fitting and artifact serialization. |
| [command_measurements.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/command_measurements.csv) | Actual full commands, UTC times, wall seconds, exits and real/tiny/no-fit categorization, including the corrected preflight failure. |
| [inner_tuning_comparison.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/inner_tuning_comparison.csv) | All eight real candidate-fold scores and best inner epochs. |
| [independent_selection.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_audit_v2/independent_selection.csv) | Candidate and final-epoch choices independently reconstructed from saved inner predictions/histories. |
| [saved_model_verification.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_audit_v2/saved_model_verification.csv) | Calibration/test prediction reproduction from all three saved models, declared tolerance and actual maximum differences; no fitting. |
| [target_diagnostics.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/target_diagnostics.csv) | Original calibration/test zero, repeated and negative values; no filtering or fault labels inferred from these counts. |
| [negative_prediction_diagnostics.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/negative_prediction_diagnostics.csv) | Unclipped negative points and lower bounds at each nominal level. |
| [role_dates_and_support.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/role_dates_and_support.csv) | Exact dates/counts/hashes for all seven roles. |
| [completion_overlay.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/completion_overlay.csv) | New version of completion status: four paired units / twelve point / twenty-four interval cells complete, preserving the original matrix. |
| [remaining_queue_updated.csv](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/remaining_queue_updated.csv) | 191 remaining core units; original order, next prerequisites and four-measurement row-scaled scheduling scenarios. No queue execution. |

## Fitted artifacts and per-row recalculation inputs

All real checkpoints are under `smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1/units/`:

| Unit directory | Fitted artifact |
|---|---|
| [pleia_energy_h1_f0_s42_persistence](../../smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1/units/pleia_energy_h1_f0_s42_persistence) | `model.json`: exact last-observation column; no learned fit. |
| [pleia_energy_h1_f0_s42_xgboost](../../smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1/units/pleia_energy_h1_f0_s42_xgboost) | `model.ubj`: actual trained XGBoost booster; `booster_config.json`: actual learner/tree parameters. |
| [pleia_energy_h1_f0_s42_attention_lstm](../../smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1/units/pleia_energy_h1_f0_s42_attention_lstm) | `model.pt`: CPU state dictionary, architecture parameters, input/target normalization and seed; loaded with `weights_only=True`. |

Each directory also contains:

- `predictions.csv.gz`: every held-out row ID/group/origin/target time, reference target, own point prediction and both issued interval levels.
- `calibration.csv.gz`: every calibration row ID, true target, corresponding model prediction and absolute error.
- `fitting_membership.csv.gz`: exact final fitting rows, preserving the original identifier and role order.
- `tuning_predictions.csv.gz`: each learned candidate/fold's validation rows, targets and predictions, permitting independent selection-MAE calculation.
- `tuning.csv.gz`: complete candidate/fold score, selected-epoch and estimator records.
- `training_history.csv.gz`: complete learned inner training/validation epoch histories; persistence/XGBoost histories are inapplicable.
- `payload.json`: parameters, roles, feature schemas, independent phase resources and actual fitting records.
- `COMPLETE.json`: atomic checkpoint identity and SHA-256 for every payload, frame and model artifact.

Read the [run environment](../../smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1/execution_environment.json), [process/action measurements](../../smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1.process.json), [fit journal](../../smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1/fit_calls.jsonl), [run summary](../../smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1/run_summary.json) and [actual command exit](../../smart_building_conformal/outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1.log.json). Per-row metrics can be recomputed entirely from these published streams. Reproducing model predictions additionally requires the original publicly sourced data/preparation inputs identified by the protocol; the existing local environment/data were used here, without uploading raw pickle caches.

## Verification and reproduction

- [Final eight-check regression log](../../smart_building_conformal/outputs/matched_forecasting005/validation/regression_smoke_v2.log), [final synthetic smoke summary](../../smart_building_conformal/outputs/matched_forecasting005/synthetic_smoke_v2/smoke_summary.json), [earlier smoke](../../smart_building_conformal/outputs/matched_forecasting005/synthetic_smoke_v1/smoke_summary.json), [exact earlier source archive](synthetic_v1_source.zip). Twenty tiny learned fits total are separate from ten real fits.
- [All 39 published role banks](../../smart_building_conformal/outputs/matched_forecasting005/preflight_v2/published_role_compatibility.csv), [preflight validation](../../smart_building_conformal/outputs/matched_forecasting005/preflight_v2/validation.json), [read-only historical pilot validation](../../smart_building_conformal/outputs/matched_forecasting005/preflight_v2/historical_pilot_validation.json), [three-unit reuse ledger](../../smart_building_conformal/outputs/matched_forecasting005/preflight_v2/historical_pilot_reuse.csv).
- [Independent real audit](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_audit_v2/validation.json), [zero-fit completed resume](../../smart_building_conformal/outputs/matched_forecasting005/validation/energy_h1_resume_v1.json), [resume costs](../../smart_building_conformal/outputs/matched_forecasting005/validation/energy_h1_resume_v1.json.process.json), [resume exit](../../smart_building_conformal/outputs/matched_forecasting005/validation/energy_h1_resume_v1.log.json).
- [Historical preservation baseline](../../smart_building_conformal/outputs/matched_forecasting005/preflight_v2/entry_preservation.json), [updated core completion summary](../../smart_building_conformal/outputs/matched_forecasting005/energy_h1_report_v1/completion_summary.json).

From `smart_building_conformal`, these verification actions fit no model. Use fresh audit/receipt paths and preserve all existing run directories:

```powershell
& C:/cfs_venv/Scripts/python.exe -B scripts/read_matched_energy005.py validate --receipt outputs/matched_forecasting005/energy_h1_audit_recheck
& C:/cfs_venv/Scripts/python.exe -B scripts/read_matched_energy005.py resume --receipt outputs/matched_forecasting005/validation/energy_h1_resume_recheck.json
```

The [read-only compatibility command](../../smart_building_conformal/scripts/read_matched_energy005.py) verifies and extracts the exact evaluated source archive, checks fresh data/config identities and forbids fitting. It applies the declared schema adapter only after confirming the original source group is Python None, and records its own reader hash separately. The newer production export repair requires a fresh source identity for future fits; direct current-source resume against the older frozen protocol intentionally fails. The [successful archive-based resume](../../smart_building_conformal/outputs/matched_forecasting005/validation/energy_h1_archive_resume_v1.json) confirms this public reproduction route also performs zero fits and leaves every run file unchanged. Existing successful checkpoints never authorize rerunning learned models for better scores. The original no-fit absence-of-entrypoint assertion is historical and was not rerun as a current readiness requirement.

## Source attribution and remaining scope

These authorized review artifacts contain derived public PLEIA energy observations, predictions, learned model artifacts and reproducible evaluation metadata. PLEIA source attribution, DOI and CC BY 4.0 license are retained in the [verified metadata](../pleia_rights_metadata.json) and [derived-data notice](../support_design_20260913/DATA_NOTICE.md). Modified derivatives preserve the original block-B energy target and causal preprocessing; no source-author endorsement is implied. Raw archives, private credentials and local prepared pickle caches are not published.

The [temperature pilot](../../MODEL_COMPARISON_PILOT_REPORT.md), [BDG2 three-fold report](../../BDG2_THREEFOLD_BENCHMARK_REPORT.md), [support audit](../../SUPPORT_DESIGN_AUDIT.md), [amendment-005 proposal](../../AMENDMENT005_PROPOSAL.md) and [full remaining-study scope](../../REMAINING_STUDY_EXECUTION_PLAN.md) remain preserved. Core completion counts exclude separate seasonal/method/DSCP and robustness obligations. The next RICO and BDG2 queue units remain unlaunched. Full-study/scientific publication readiness remains false.

The publication manifest excludes itself and `publication_validation.json` to avoid recursive hashes; Git commit identity binds those files. Remote SHA/content verification and an additional backup are recorded externally and confirmed in the final delivery.

The initial group-identity audit failure is preserved in [energy_h1_audit_v1.log](../../smart_building_conformal/outputs/matched_forecasting005/validation/energy_h1_audit_v1.log). The repaired exporter passed [two additional no-fit checks](../../smart_building_conformal/outputs/matched_forecasting005/validation/identifier_export_v1.log). The numerical audit succeeded in v2; no real learned model was refitted. See [current source archive](current_source.zip) and [its source ledger](current_source_manifest.csv), separately from the evaluated source archive.
