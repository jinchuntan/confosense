# Current ConfoSense implementation and review evidence

## Amendment 004 — current delivery

13 September 2026. Current publication branch: [review/amendment004-20260913](https://github.com/jinchuntan/confosense/tree/review/amendment004-20260913), descended from **3354393290d2afaef4361a9a7a1a43336a14c21d**. [Current remote commit/history](https://github.com/jinchuntan/confosense/commits/review/amendment004-20260913) identifies the publication head; the exact delivered SHA is also returned in the completion response. Main and `review/current-dissertation-20260913` retain their original heads. The older code beneath the separate instruction/evidence branch was never checked out over the current implementation.

- [Completed implementation report](../AMENDMENT004_IMPLEMENTATION_REPORT.md)
- [Executable amendment and clarifications](../smart_building_conformal/protocols/amendment004/AMENDMENT004.md), [frozen resolved configuration](../smart_building_conformal/configs/operational_amendment004.json)
- [Operational engine](../smart_building_conformal/src/operational004_engine.py), [causal interval replay](../smart_building_conformal/src/operational004_stream.py), [events](../smart_building_conformal/src/operational004_events.py), [metrics/selection](../smart_building_conformal/src/operational004_metrics.py), [paired inference](../smart_building_conformal/src/operational004_inference.py), [acceptance tests](../smart_building_conformal/tests/test_operational004.py)
- [Four-task support summary](amendment004_20260913/support_summary.csv), [per-fold event support](../smart_building_conformal/outputs/amendment004/preflight_20260913_v1/event_support.csv), [stratum support](../smart_building_conformal/outputs/amendment004/preflight_20260913_v1/stratum_support.csv), [membership/exposure](../smart_building_conformal/outputs/amendment004/preflight_20260913_v1/memberships_summary.csv), [physical-rule applicability](../smart_building_conformal/outputs/amendment004/preflight_20260913_v1/physical_rule_applicability.csv), [rank support](../smart_building_conformal/outputs/amendment004/preflight_20260913_v1/calibration_rank_support.csv), [physical policy settings](amendment004_20260913/physical_policy_settings.csv)
- [Independent support validation](../smart_building_conformal/outputs/amendment004/preflight_validation_20260913_v1/validation.json), [group exposure](../smart_building_conformal/outputs/amendment004/preflight_validation_20260913_v1/group_exposure.csv), [boundary exclusions](../smart_building_conformal/outputs/amendment004/preflight_validation_20260913_v1/boundary_excluded_slots.csv), [mask aliases](../smart_building_conformal/outputs/amendment004/preflight_validation_20260913_v1/coarse_mask_aliases.csv)
- [Completed SMOKE ONLY run](../smart_building_conformal/outputs/amendment004/smoke_20260913_v2), [output validation](../smart_building_conformal/outputs/amendment004/smoke_20260913_v2/output_validation.json), [zero-refit resume](../smart_building_conformal/outputs/amendment004/smoke_20260913_v2/resume_validation.json), [actual unit data and hashes](../smart_building_conformal/outputs/amendment004/smoke_20260913_v2/units/outer0_model42)
- [Final regression log](../smart_building_conformal/outputs/amendment004/validation/regression_v3.log), [all exact command/exit records](../smart_building_conformal/outputs/amendment004/validation), [preservation audit](../smart_building_conformal/outputs/amendment004/validation/preservation.json), [publication file manifest](amendment004_20260913/EVIDENCE_MANIFEST.csv), [publication audit](amendment004_20260913/PUBLICATION_AUDIT.md)
- [Single next bounded proposal — not executed](amendment004_20260913/next_bounded_proposal.json)

Evaluated implementation: **917d6eb2d634a457f3fba0fc16133463fe05b9b4**; [source archive/identity](../smart_building_conformal/outputs/amendment004/validation/evaluated_source_v3.json). Source SHA-256 **fd7a6bbb5fda25a7058951f49e1c41ec47f4cffe0a21640036ad8f56a7031bd8**; configuration SHA-256 **b49eb9b3802e715b150c5cf3ed7681f0da85b913425c29c6460b74ef8c19a5fb**; design SHA-256 **5c1d4aedbbdedfb5d6cceedfd56b1dbe331233d0c497ea7b0126cf6095938c75**. Reporting/publication commits are later descendants. Preflight used the separately archived source **3dea8da16ae2f9520219d58d86b500dbdff7b9115e87f8ce0d4c1fc686282838**.

The no-fit audit covers all four tasks and three outer folds. BDG2 has structural support in all six inner banks; PLEIA temperature, PLEIA energy and RICO have none. RICO outer banks contain zero events at the unchanged incidence. Counts alone do not establish identifiable bounds or operational feasibility. The canonical synthetic smoke contains 12 inner cells, 60 inner and 20 outer catalogue/hash pairs, 96 persisted streams, separate feasible count fixtures and explicit insufficient-support abstention. It is never accepted as a full-study result. Final regression: **332 passed, 1 skipped, three existing warnings**. Full-study/dissertation readiness is **false**.

The original pilot remains complete at **9/9 point and 18/18 interval cells, completion exit 0**. Its report and all nine canonical CSV paths remain linked below. The old `review/EVIDENCE_MANIFEST.csv` describes the earlier 3354393 publication; use its historical commit when verifying it. The amendment manifest is separate. The failed first smoke/reporting attempt, intermediate failed regression and all previous source archives are preserved and explained in the implementation report.

## Historical pilot and diagnostic publication at 3354393

13 September 2026. Canonical index for `review/current-dissertation-20260913`, created from the latest local dissertation head **a5b32b81266efc107ad0bfdf74f95139ee99ba77**. This branch retains that history; it does not replace it with the older source underlying the separate evidence-review branch. Main is unchanged. The final published head is the commit containing this index and subsequent review-only updates; use the branch history or the completion response for its exact SHA.

## Lineage

| Identity | Exact value |
|---|---|
| Handoff / independent aggregate review | [b7f9a076c379149cc6c5eaef9a20d0db17508cb6](https://github.com/jinchuntan/confosense/tree/b7f9a076c379149cc6c5eaef9a20d0db17508cb6/review/pilot_v1_20260913) on `review/pilot-evidence-20260913`; its base code is older. |
| Evaluated pilot implementation | [d4bc1bc4af7b20d990618df09064ac310809a8ab](https://github.com/jinchuntan/confosense/commit/d4bc1bc4af7b20d990618df09064ac310809a8ab), frozen before research fitting. |
| Evaluated source SHA-256 | `965ff02d8cb67183210632bfbc3a2251c430a2b027b8b44d87df356fd19e3d71` |
| Frozen pilot protocol SHA-256 | `af29d2340427f043c605f777e54389bc86ccbb44c9630aba57964536d0845ce3` |
| Run ID | `pilot_v1_20260913`: PLEIA temperature; horizons 1/3/6; fold 0; seed 42; three models; levels 90%/95%. |
| Current implementation and diagnostic runner | [70b875a5f9abe73bfe6c9a2fe3f72c2ff4b41ecb](https://github.com/jinchuntan/confosense/commit/70b875a5f9abe73bfe6c9a2fe3f72c2ff4b41ecb): allocation-only preparation fix, focused checks and development diagnostic scripts. Model/sequence code and pilot scientific settings unchanged. |

Reporting, publication manifests and the operational plan are later review artifacts. They are not represented as code evaluated in the original pilot. The exact [evaluated source ZIP](../smart_building_conformal/outputs/model_comparison_pilot_v1/validation/evaluated_source.zip) preserves original source bytes despite Git line-ending differences; its [identity record](../smart_building_conformal/outputs/model_comparison_pilot_v1/validation/evaluated_source.json) gives the archive hash.

## Read first

- [Completed pilot report](../MODEL_COMPARISON_PILOT_REPORT.md)
- [Pilot diagnostics: findings, fixes and result validity](../PILOT_DIAGNOSTICS.md)
- [Operational evaluation implementation plan](../OPERATIONAL_EVALUATION_PLAN.md)
- [Current recovery status](../PROJECT_RECOVERY_STATUS.md), [panel response matrix](../PANEL_RESPONSE_MATRIX.md), [integration repair record](../INTEGRATION_REPAIR_REPORT.md)
- [Publication scope/rights notice](DATA_NOTICE.md), [publication audit](PUBLICATION_AUDIT.md), [file/size/SHA-256 manifest](EVIDENCE_MANIFEST.csv)

## Implementation, configuration and protocol

- [Pilot runner](../smart_building_conformal/src/model_comparison_pilot.py), [forecasters](../smart_building_conformal/src/pilot_forecasters.py), [common support](../smart_building_conformal/src/pilot_data.py), [split integrity](../smart_building_conformal/src/split_integrity.py), [conformal ranks](../smart_building_conformal/src/pilot_conformal.py), [memory sampler](../smart_building_conformal/src/pilot_resources.py)
- [Preparation allocation fix](../smart_building_conformal/src/prepare_data.py) and [PLEIA adapter](../smart_building_conformal/src/datasets/pleia.py)
- [Dependency specification](../smart_building_conformal/requirements.txt), [existing lock file](../smart_building_conformal/requirements-lock.txt), and [actual evaluated package versions](../smart_building_conformal/outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913/checkpoint_manifest.json). No dependencies were changed; do not assume a historical lock file exactly describes the existing pilot environment.
- [Pilot configuration](../smart_building_conformal/configs/model_comparison_pilot_v1.json), [frozen protocol](../smart_building_conformal/protocols/model_comparison_pilot_v1/frozen_protocol.json), [readable protocol](../smart_building_conformal/protocols/model_comparison_pilot_v1/PILOT_PROTOCOL.md), [membership](../smart_building_conformal/protocols/model_comparison_pilot_v1/membership.csv.gz), [boundary records](../smart_building_conformal/protocols/model_comparison_pilot_v1/boundaries.csv)
- [Pilot tests](../smart_building_conformal/tests/test_model_comparison_pilot.py), [diagnostic/allocation tests](../smart_building_conformal/tests/test_pilot_diagnostics.py), [repaired engine tests](../smart_building_conformal/tests/test_integration_repairs.py), [checkpoint/delivery tests](../smart_building_conformal/tests/test_integration_delivery.py)

## All nine canonical pilot CSVs

| File | Purpose |
|---|---|
| [point_summary.csv](../smart_building_conformal/outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913/point_summary.csv) | Nine point metric cells and per-unit computation. |
| [interval_quality.csv](../smart_building_conformal/outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913/interval_quality.csv) | Eighteen coverage/MPIW/Winkler/rank/radius cells. |
| [comparison.csv](../smart_building_conformal/outputs/model_comparison_pilot_v1/tables/comparison.csv) | Convenience join of point, interval and computational results. |
| [resource_measurements.csv](../smart_building_conformal/outputs/model_comparison_pilot_v1/tables/resource_measurements.csv) | 36 phase measurements, including empty persistence tuning-branch overhead. |
| [tuning_results.csv](../smart_building_conformal/outputs/model_comparison_pilot_v1/tables/tuning_results.csv) | 24 original learned candidate/inner-fold outcomes. |
| [pleia_preparation_memory.csv](../smart_building_conformal/outputs/model_comparison_pilot_v1/tables/pleia_preparation_memory.csv) | Nine original preparation measurements. |
| [bdg2_preparation_memory.csv](../smart_building_conformal/outputs/model_comparison_pilot_v1/tables/bdg2_preparation_memory.csv) | Five original preparation-only records; no fitted BDG2 models. |
| [execution_measurements.csv](../smart_building_conformal/outputs/model_comparison_pilot_v1/tables/execution_measurements.csv) | Recorded command timing/exit status; the interrupted original exit remains unknown. |
| [measured_cost_and_expansion_scenario.csv](../smart_building_conformal/outputs/model_comparison_pilot_v1/tables/measured_cost_and_expansion_scenario.csv) | Original per-model totals and cautious equal-cost repetition scenario. |

[Readable comparison PNG](../smart_building_conformal/outputs/model_comparison_pilot_v1/figures/pilot_comparison.png), [SVG](../smart_building_conformal/outputs/model_comparison_pilot_v1/figures/pilot_comparison.svg), [figure source hashes](../smart_building_conformal/outputs/model_comparison_pilot_v1/figures/figure_sources.json).

## Evidence that permits recomputation

The [nine unit directories](../smart_building_conformal/outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913/units) contain `predictions.csv.gz` (truth, point, bounds, row IDs and timestamps), `calibration.csv.gz` (truth, own-model predictions/errors), original tuning/history CSVs, fitted model artifacts, `payload.json` and hash-checked `COMPLETE.json`. These are published derived observations, not hashes standing in for missing metric inputs. The original pilot did not save inner learned predictions; the [development reproduction](../smart_building_conformal/outputs/pilot_diagnostics_v1/inner_reproduction) adds only the unchanged inner fits needed for the diagnosis, explicitly separate from the pilot run.

The [original output validator](../smart_building_conformal/outputs/model_comparison_pilot_v1/validation/output_validation.json) confirms 9 point and 18 interval cells; [resume integrity](../smart_building_conformal/outputs/model_comparison_pilot_v1/validation/resume_integrity.json) records nine units reused with zero refits. [Post-fix revalidation](../smart_building_conformal/outputs/pilot_diagnostics_v1/pilot_revalidation.json) checks the preserved evidence again. Validation of files/calculations is not successful coverage or scientific readiness.

The [matched inner table](../smart_building_conformal/outputs/pilot_diagnostics_v1/inner_reproduction/matched_inner_metrics.csv), [target ranges](../smart_building_conformal/outputs/pilot_diagnostics_v1/inner_reproduction/development_ranges.csv), [normalization diagnostics](../smart_building_conformal/outputs/pilot_diagnostics_v1/inner_reproduction/normalization.csv) and [before/after preparation measurements](../smart_building_conformal/outputs/pilot_diagnostics_v1/memory_comparison.csv) are separate follow-up evidence. [Independent recomputation](../smart_building_conformal/outputs/pilot_diagnostics_v1/diagnostic_validation_extended.json) passed all 30 development summaries and 12 complete learning histories. The [follow-up regression log](../smart_building_conformal/outputs/pilot_diagnostics_v1/full_tests.log) records 308 passed, one skipped and three existing warnings.

From `smart_building_conformal/`, the following recomputes the published pilot summaries from published predictions without raw source data or retraining:

```powershell
& 'C:\cfs_venv\Scripts\python.exe' -B -m src.validate_model_comparison_pilot --run outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913 --protocol protocols/model_comparison_pilot_v1/frozen_protocol.json --out review_validation_local.json
```

Use an appropriate existing Python executable on another machine. Check the actual package-version manifest. A *training resume* from the current allocation-fixed source intentionally fails the original source-identity guard; do not overwrite the original readiness or manifest to bypass it. Reproducing original fits requires the exact evaluated source snapshot and raw source data in a separate checkout, or a newly versioned execution identity after verification of the allocation-only change.

## Local-only inventory and next step

Raw/interim/processed datasets remain under ignored local data directories. The baseline prepared-data cache used for diagnosis is local at `C:/Users/nigel/ConfoSenseBackups/pilot_followup_20260913/prepared_baseline.pkl`; it is not required to recompute the published diagnostics from their saved development predictions. Existing virtual environments, full legacy prediction dumps excluded by Git, external backup snapshots and Git bundles remain local. No new sharing service is used. [DATA_NOTICE.md](DATA_NOTICE.md) records source attribution and changes.

That earlier next step is superseded by the completed amendment-004 implementation and bounded smoke indexed above. The single next proposal is the frozen BDG2 fold-2/seed-42 engineering pilot. Full multi-dataset fitting and robustness execution remain unlaunched, and global study/publication readiness remains false.
