# PLEIA-temperature seeds 43--46 zero-fit preflight

## Decision

**Technical checks passed; launch readiness did not pass.** The explicit validator interface, four draft designs, data identities, authorization gate, and 12 focused tests passed. Execution remains unauthorized, and the shared working/backup volume has only 4.15 GiB free: below both the frozen 8 GiB floor and the 15.70 GiB pre-launch capacity budget documented here. No experiment coordinator was started.

The exact remaining decision is: first increase free capacity by at least the recorded 11.55 GiB deficit (and remeasure); then obtain explicit authorization for model seeds 43--46. Only after both conditions are met may new final authorized manifests and protocols be created and one worker launched at a time. These draft manifests must never be edited into authorized manifests or executed.

## Actual work and preservation

- Models fitted: **0**. Calibrators fitted: **0**. Experiments started: **0**.
- Full scientific validations: **0**. Five-seed scientific analyses: **0**.
- The accepted seed-42 `COMPLETE.json`, `operations.jsonl`, scientific source digest, and source/protocol files remain unchanged.
- The seed-42 run measures 127,162 files and 554,303,486 bytes. Its packaged raw evidence is 549,321,115 bytes.
- Installed package versions match the frozen protocol exactly. Available RAM was 4,699,762,688 bytes on a 16,890,978,304-byte machine; the nonblocking 3 GiB RAM reference was met. The machine reports 20 logical CPUs, but the future policy remains CPU-only and one thread.

The capacity projection retains four raw runs, four package sets, package-sized external backup objects, one raw-plus-package restore scratch area, one package temporary peak, and the unchanged 8 GiB post-allocation floor. That totals 16,854,663,172 bytes required before launch versus 4,452,564,992 bytes measured free on the shared `C:` working/backup volume. This is a planning bound, not an execution measurement.

## Draft designs and authorization

The four review-local draft manifests use proposed units `pleia_f2_s43_C_v1` through `pleia_f2_s46_C_v1`. Every manifest has `execution_authorized=false` and `authorization_kind=preflight_only_not_authorized`. Draft freeze performed no fits. The deterministic contexts, schedules and role files are byte-identical to seed 42; all feature, outcome, role, context, schedule, cache, column-order, frequency, feature-configuration, source-input, row-count, operation-budget and resource-policy identities match.

The four draft manifests differ from seed 42 only in `model_seed`, `unit_key`, `execution_authorized`, and `authorization_kind`. A disposable readiness-shaped receipt was used only to prove that the engine rejects an unauthorized run before fitting. Native readiness was not invoked because the known shared-volume free space is already below its 8 GiB gate.

See [MANIFEST_COMPARISON.csv](MANIFEST_COMPARISON.csv), [DESIGN_PREFLIGHT.json](DESIGN_PREFLIGHT.json), and [RESOURCE_BUDGET.json](RESOURCE_BUDGET.json).

## Validator and focused tests

`candidate_representation_compatible_v2_explicit_paths` requires explicit design, run, output, dataset, fold, horizon and model seed. Before validation it verifies the frozen protocol and manifest hash, current source/packages/inputs, independently reconstructed data identity, completion or limited-fixture binding, saved wrapper identity, and native quantile-estimator random states. Full mode additionally verifies every file declared by `COMPLETE.json` and fitted/calibrated owner blob hashes. Output paths that could overwrite or mix with design/run evidence are rejected.

The adapter delegates the unchanged accepted v1 A-and-B-and-C implementation only after matching its normalized working source to the audited Git blob SHA-256 `14cab398cf5ec389a1eae0a2f22d832a56ada31add44f93f6a38ea3095d2a091`. Absolute and relative tolerances remain `1e-10`; model application uses the A-verified saved representation; `Operations(forbid=True)` remains active. A limited receipt explicitly cannot satisfy full acceptance.

All 12 focused cases passed: bounded seed-42 v1/v2 numerical/category equivalence; intact acceptance; eight meaningful A/B/C corruption rejections; wrong expected seed; seed-43 design cross-wired to seed-42 run/owners; and an output-overwrite path. No seed-43 artifact was relabelled as a positive test. Future fitted-owner random states and full owner hashes for seeds 43--46 remain pending execution-time checks.

The authoritative results are [focused_tests_v2/FOCUSED_TEST_RECEIPT.json](focused_tests_v2/FOCUSED_TEST_RECEIPT.json) and [PREFLIGHT_READINESS_V2.json](PREFLIGHT_READINESS_V2.json). The earlier successful provisional run is retained and explicitly superseded because it preceded the added audited-source pin.

## Future execution and aggregation plan

After capacity and authorization, create separate final manifests/protocols and process seeds 43, 44, 45 and 46 sequentially. Preserve completed stages, resume only an exact matching unit, and monitor the real worker PID/family, CPU, RSS, stage journal and exit status. Per-seed completion requires its operation ledger, fitted-owner seed checks, full amended validation, zero-fit completed resume, artifact-integrity proof and actual resource receipt.

The published seed-42 full validation took 3.04 wall hours and 2.71 CPU hours. Four-times validation-only planning anchors are 12.16 wall hours and 10.85 CPU hours; there is no reliable end-to-end ETA for execution, packaging, aggregation and publication. Revise estimates only from measured authorized new-unit phases.

Five-seed analysis remains future work. It must average seeds 42--46 within each original context/stratum, preserve equal-stratum weighting and null/alias/censoring semantics, and use 2,000 paired chronological seven-context block draws with RNG seed 20240601 and the existing support/valid-draw/degeneracy gates. Energy results, bounds and authorization are excluded.

The planned per-seed budget is one CQR wrapper fit, three native quantile-estimator fits, two recorded nested conformalize calls (one logical conformalization), and one persistence-radius computation. Across four seeds those become 4, 12, 8 (4 logical), and 4 respectively. XGBoost, LSTM, EnbPI, DSCP, tuning and seed-42 refits remain zero.

## Scientific limits retained

Rolling CQR clean-stream coverage remains 0.9081 versus nominal 0.95; persistence remains 0.9652 but does not dominate every rule-dependent detection/workload tradeoff. Additional model seeds are not additional buildings or independent contexts. Population intervals remain unavailable unless the established five-seed support and degeneracy rules pass. This work adds no matched-forecasting, interval-method, seasonal, prevalence, precision, F1 or deployment-feasibility evidence.
