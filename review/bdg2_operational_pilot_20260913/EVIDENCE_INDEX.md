# BDG2 operational pilot evidence index

Canonical run: `bdg2_operational_pilot_f2_s42_v2`, descended from `2243c167804690ad1ec9b8aebc369e5596d392aa`. The complete report states the actual decision, numerical results, uncertainty and exit status. The version-1 pre-fit failure is retained separately. Publication branch: [review/bdg2-operational-pilot-20260913](https://github.com/jinchuntan/confosense/tree/review/bdg2-operational-pilot-20260913); the delivery response supplies its exact publication SHA.

- [Completed report](../../BDG2_OPERATIONAL_PILOT_REPORT.md)
- [Execution scope and lineage](EXECUTION_SCOPE.md), [source/configuration/membership identity before fitting](../../smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2_execution/prefit_identity.json), [exact evaluated source ZIP](../../smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2_execution/evaluated_source.zip)
- [Frozen configuration](../../smart_building_conformal/configs/operational_amendment004.json), [amendment](../../smart_building_conformal/protocols/amendment004/AMENDMENT004.md), [original nine-candidate proposal](../amendment004_20260913/next_bounded_proposal.json)
- [Published file/byte/hash manifest](EVIDENCE_MANIFEST.csv), [publication validation](publication_validation.json), [BDG2 attribution and derived-data notice](DATA_NOTICE.md)

## Numerical tables and exact purposes

All paths below are relative to the repository root; links resolve to the actual files. The uncompressed recomputed tables are convenient to review on GitHub. Canonical checkpoint CSVs remain compressed and retain their original hashes. Oversized stream CSVs are published as [lossless binary parts with an ordered manifest](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_publication_v1/large_files.json); every original byte is retained. The reconstruction command below restores their exact canonical filenames and hashes. This handles [GitHub's 100 MiB ordinary-file limit](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) without changing the completed unit or requiring manual CSV uploads.

| File | Purpose |
| --- | --- |
| [recomputed_metrics.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/recomputed_metrics.csv) | Independently reconstructed inner and outer operational metrics, support, recall/workload bounds, custom utility, ordinary precision, delays and misses. |
| [clean_interval_quality.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/clean_interval_quality.csv) | Clean observed-row coverage, MPIW, Winkler95, and point MAE/RMSE; kWh units and denominators. |
| [surface.csv.gz](../../smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2/units/outer2_model42/surface.csv.gz) | Canonical 18 candidate/two-inner-fold selection cells and all reported selection metrics. |
| [outer_metrics.csv.gz](../../smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2/units/outer2_model42/outer_metrics.csv.gz) | Canonical final held-out metrics for the actual requested diagnostic/selected comparisons. |
| [rejections.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/rejections.csv) | Recomputed primary feasibility and every rejection reason, preserving both inner folds. |
| [inverse_rejections.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/inverse_rejections.csv) | Separate secondary inverse recall-floor selection, without the primary workload ceiling. |
| [group_metrics.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/group_metrics.csv) | Building-level clean exposure/episodes, workload and detection counts. |
| [stratum_channel_metrics.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/stratum_channel_metrics.csv) | All 21 family/severity strata × availability, numerical and combined channels. |
| [event_support.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/event_support.csv) | Actual inner/outer event requests, placements, effective/distinct onsets, nulls and rejections. |
| [bootstrap_replicates.csv.gz](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/bootstrap_replicates.csv.gz) | Independent recall/workload recomputations for the saved paired whole-building draws. |
| [recovery.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/recovery.csv) | Building-specific descriptive coverage recovery, follow-up and censoring. |
| [membership_summary.csv](../../smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2_execution/membership_summary.csv) | Pre-fit row counts, original buildings, asset-day exposure and all 13 role hashes. |
| [command_measurements.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/command_measurements.csv) | Exact command wall times, actual exit statuses, timestamps and process IDs, including failed attempt and resume. |
| [phase_measurements.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/phase_measurements.csv) | Preparation, windowing, identity, inner/outer computation, checkpoint and validation timing/peak memory. Nested phases overlap. |
| [process_measurements.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/process_measurements.csv) | Actual pilot process lifetime user/kernel/total CPU, wall time and OS exit code. |
| [fit_measurements.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/fit_measurements.csv) | Actual CQR object and quantile sub-estimator counts, roles and fit identities; zero-fit persistence. |
| [artifact_measurements.csv](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/artifact_measurements.csv) | Actual evidence file counts, byte totals and largest-file sizes at measurement time. |

## Evidence inputs and validation

- [Unit directory](../../smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2/units/outer2_model42): after restoring oversized files from the linked parts, canonical `streams.csv.gz` and `outer_streams.csv.gz` contain observed values, issued bounds and alert flags; `catalogues.csv.gz` and `outer_catalogues.csv.gz` contain event schedules; `event_scores`, `episodes`, `contributions`, `updates`, `released_scores`, workload, attribution and recovery tables retain detailed accounting. `payload.json` retains decisions, comparisons, estimator identities and actual paired resampling indices; `COMPLETE.json` hashes the files.
- [Independent validation](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_independent_validation_v1/validation.json), [production output validation](../../smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2_execution/run_output_validation.json), [zero-fit resume proof](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/resume_validation.json)
- [Successful command log](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/pilot_v2.log), [actual exit/time record](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/pilot_v2.log.json), [durable start/process record](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/pilot_v2.log.started.json)
- [Preserved failed command](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/pilot.log), [failed attempt identity](../../smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v1_execution/prefit_identity.json), [no-fitting real-data defect verification](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/flag_dtype_real_data.json)
- [Regression/verification command records](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1), [environment versions](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/environment.json), [measurement scope](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/cost_scope.json), [historical preservation audit](../../smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/preservation.json)

## Reproduce the read-only audit

From `smart_building_conformal`, with a compatible existing Python environment and a new output directory:

```powershell
& C:/cfs_venv/Scripts/python.exe -B scripts/verify_bdg2_materialize.py --manifest outputs/amendment004/bdg2_pilot_publication_v1/large_files.json
& C:/cfs_venv/Scripts/python.exe -B scripts/independent_bdg2_operational_audit.py --run outputs/amendment004/bdg2_operational_pilot_f2_s42_v2 --out outputs/amendment004/reviewer_bdg2_audit
```

The first command restores missing oversized files and verifies existing ones without overwriting them; it changes no scientific values. The audit then reads published saved streams, events, contribution tables and bootstrap draws, plus the published preflight catalogues. Neither command requires raw dataset files or fits a model. [Independent audit source](../../smart_building_conformal/scripts/independent_bdg2_operational_audit.py), [audit tests](../../smart_building_conformal/tests/test_independent_bdg2_audit.py), [resume verifier](../../smart_building_conformal/scripts/verify_bdg2_completed_resume.py). A training-entrypoint resume additionally requires the exact evaluated source, environment and local raw data; partial-stage recovery is not claimed.

The original forecasting pilot, previous amendment smoke/support evidence and prior publication history remain available through [CURRENT_EVIDENCE.md](../CURRENT_EVIDENCE.md). This bounded operational pilot does not establish full-study readiness. The completed report states the single proposed next bounded unit; it has not been launched.
