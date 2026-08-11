# Final table index

All paths relative to `outputs/full_study/`.

| output file | purpose | dissertation section | main takeaway |
|---|---|---|---|
| combined/point_metrics.csv | Point-forecast MAE/RMSE per dataset, horizon and model | Ch. 5 Results - point forecasting | Model value is target-dependent; persistence wins PLEIA temperature outright |
| combined/model_rankings.csv | Mean within-dataset ranks per point model | Ch. 5 Results - point forecasting | XGBoost ranks first overall (1.56) |
| combined/bootstrap_metrics.csv | Moving-block bootstrap CIs for point metrics | Ch. 5 / Appendix | Every CI brackets its point estimate |
| combined/effect_sizes.csv | Pairwise effect sizes between point models | Ch. 6 Discussion | XGBoost vs persistence spans -69.2% to +48.8% |
| combined/statistical_tests.csv | Diebold-Mariano tests (HLN corrected) | Ch. 5 / Appendix | 36 of 48 significant after Holm |
| combined/ranking_tests.csv | Friedman test across blocks | Ch. 5 Results - statistical analysis | chi2 = 14.07, p = 0.0028, 9 blocks |
| combined/posthoc_comparisons.csv | Holm-corrected Wilcoxon post-hoc | Ch. 5 Results - statistical analysis | Only seasonal_naive vs xgboost survives correction |
| combined/interval_metrics.csv | Coverage, width and Winkler for all five interval arms | Ch. 5 Results - prediction intervals | Uncalibrated quantiles undercover everywhere; no arm dominates |
| combined/rico_quantile_crossings.csv | CQR quantile crossings on RICO by horizon and level | Ch. 5 / Appendix | 3,912 of 66,696 intervals cross before repair (5.87%) |
| combined/rico_quantile_crossings_by_run.csv | Crossings per RICO experimental run | Appendix | Crossings concentrate in 16 of 42 test runs |
| combined/alert_metrics.csv | Alert rule surfaces: calibration, test, clean-test | Ch. 5 Results - alerting | Frozen rule differs on all four datasets |
| combined/robustness_metrics.csv | Disturbance scenarios in both evaluation modes | Ch. 5 Results - robustness | Closed-loop reveals fault absorption that legacy mode hides |
| combined/robustness_metric_schema.csv | Terminology for the two coverage definitions | Ch. 4 Methodology | observed-signal vs clean-reference must never be merged |
| combined/recalibration_metrics.csv | Static / periodic / rolling recalibration | Ch. 5 Results - recalibration | Adaptive helps on all four; BDG2 rolling is not a distinct strategy |
| combined/confosense_configurations.csv | Per-target framework configuration | Ch. 6 Discussion | No universal configuration dominates |
| combined/literature_benchmark_matrix.csv | Classified literature comparability | Ch. 2 Literature / Ch. 6 | 0 of 12 papers are directly comparable |
| combined/rq_ro_evidence_matrix.csv | RQ/RO to evidence mapping | Ch. 6 Discussion | Each RQ has named persisted evidence |
| combined/pleia_energy_target_profile.json | PLEIA energy target distribution | Ch. 4 Data / Appendix | Skew 155, kurtosis 25,318 |
| combined/pleia_energy_meter_stalls.csv | Meter-stall catch-up artefacts | Ch. 4 Data / Appendix | Two artefacts follow 556 and 385 zero-increment steps |
| combined/pleia_energy_artefact_sensitivity.csv | Point metrics with and without the artefact | Appendix | One row inflates XGBoost RMSE 16x |
| <dataset>/metrics/alert_selection_split.csv | Nested calibration split per dataset | Ch. 4 Methodology | Rule-tuning timestamps strictly postdate conformal ones |
| <dataset>/data_profiles/*.csv | Per-dataset selection and split audits | Ch. 4 Data | Selection criteria contain no performance column |
| manifests/run_history.jsonl | One line per study invocation | Ch. 3 / Appendix | fast_mode false, 0 failed stages in the full execution |
| manifests/stage_provenance.json | Which configuration produced each stage | Ch. 3 / Appendix | Post-audit stages re-executed; the rest verified identical |
| manifests/dataset_sources.json | Provenance with DOIs, licences, checksums | Ch. 4 Data | All four datasets fully attributed |
