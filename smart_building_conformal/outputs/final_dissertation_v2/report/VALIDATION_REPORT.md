> **Historical document ? status changed 13 September 2026.** This retained account predates the integration repairs. Its performance/achievement statements do not establish current findings. See `INTEGRATION_REPAIR_REPORT.md` at the repository root and `audit/integration_repair_status.json`. Historical metrics and publication markers are preserved, not revalidated.

CHECK                                              RESULT
protocol_parses_and_validates                      PASS  schema_version=2
protocol_hash_recorded                             PASS  canonical=07bf304aceeafc74...
full_study_unchanged                               PASS  ok
no_audit_item_pending                              PASS  none pending
full_nonfast_run_present                           PASS  run=full_20260831_220811, fast=False
run_matrix_complete                                PASS  datasets ['bdg2', 'pleia', 'pleia_energy', 'rico']; folds [3]
estimates_with_cis_present                         PASS  final_cis.csv ok
reports_no_placeholders                            PASS  results report clean
figures_trace_to_csv                               PASS  4 figures traced

ALL PUBLICATION CHECKS PASSED -> wrote C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\final_dissertation_v2\PUBLICATION_READY.json
