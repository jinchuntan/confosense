# Between-horizon validation cleanup import

The fourth validator completed all first-horizon checks: owner reloads, native quantiles/bounds, scalar causal replay, releases/updates, emitted/consumed alerts, native/common metrics, building reconciliation and seasonal cells. It then exited **1** at `gc.collect()` because the new validator module lacked `import gc`. The failed attempt is preserved.

The repair adds that import. No scientific calculation, tolerance, output, model, protocol or setting changes. All new scientific modules were checked for unresolved referenced globals. Eleven no-fit regression checks passed on the repaired source, comprising the preceding ten checks plus that scan. There are **49 distinct resolved acceptance checks** and no repeated learned or calibrator fits.

Evaluated scientific source: `026da0df7a10396c455a6a8d28a2736532e9a439a61e38ddea04d830bd142f19`.

Current validator source: `3d07d3cc76dd359da04c1ca741c0ca658cf9e68b6b6478de97c3f8a727f01c87`.

[Revision-5 exact source manifest](VALIDATION_ERRATUM_V5.json), [source archive](corrected_validation_source_v5.zip), and [read-only recovery commands](VALIDATION_RECOVERY_COMMANDS_V5.json) retain the same strict historical identity checks. Validation writes `validation_v5` and `validate_worker_resources_v5.json`; the four previous attempts and their costs remain intact. The preceding [native-point precision record](VALIDATION_ERRATUM_V4.md) links the earlier scientific-reconstruction diagnoses.
