# Checkpoint memory repair and preserved fold-2 verification

The duplicate CSV allocation is repaired. The preserved BDG2 fold-2 result passes read-only compatibility verification with **zero fits**, all **30 original unit files byte-identical**, every payload value equal and all **28 frame value/schema fingerprints equal** to the historical parser. Primary abstention and the separate inverse selection of `c0024_ba16b82adffd` are unchanged. This repair does not invalidate the completed pilot.

## Implementation and correctness

[`UnitCheckpoint.verify`](smart_building_conformal/src/unit_checkpoint.py) checks the completion marker, unit key, specification identity, required payload/frame hash coverage, file existence, every recorded SHA-256 and JSON payload syntax without parsing CSVs. `load` then materializes the required frames once. `require_complete` checks the exact unit matrix and calls `verify`. Thus both the completed-unit path and new-save verification avoid a redundant all-frame allocation. Scientific cell/stream validation remains in the consumers, including the operational validator.

The [focused tests](smart_building_conformal/tests/test_checkpoint_memory.py) demonstrate zero CSV parses for new-save completeness verification, one parse per required frame for completed resume, source-mismatch rejection, damaged payload/frame/marker rejection, provenance/hash-coverage rejection, missing/duplicate unit and scientific-cell rejection, empty frames and literal string identifiers. The existing operational tests cover missing candidate cells, edited bounds, insufficient support, causal recalibration, method identity and zero-refit reuse. Shared-checkpoint forecasting/extension regression checks also passed.

The first regression command passed **47 tests** with the three existing MAPIE warnings; the separate authorization command passed **7 tests**. [Commands and actual exit records](smart_building_conformal/outputs/amendment004/bdg2_threefold_validation_v1) preserve these outcomes. Additional combined-analysis checks are reported with the benchmark.

## Historical evaluation versus current reader

This is explicitly **read-only historical checkpoint compatibility**, not production training resume under a substituted identity. The verifier never rewrites the historical manifest or source hash. A current-source production identity is tested and rejected with `resume code/config/data signature mismatch; use a new run directory`. Computation and fit constructors are forbidden throughout.

- Historical evaluation commit: `ef9a8a9525bafea00a12b5c1327aadec071eab91`; source SHA-256 `8218d9f461811fa9075c2966c394cae2344ae61f073887ff356af82025c8f4e4`.
- New reader source SHA-256: `203f3babf66c98ac072ad450abec5ea7ce3d60473f02708fa64ac2102ea3f7c9`; developed on entry commit `d63251b75f5c70c4d51c19456fbec6724e712516`. The implementation is committed before the new study fits.
- [Historical exact source archive](smart_building_conformal/outputs/amendment004/bdg2_operational_pilot_f2_s42_v2_execution/evaluated_source.zip), [current reader exact source archive](smart_building_conformal/outputs/amendment004/bdg2_checkpoint_compatibility_v1/current_reader_source.zip).
- [Complete compatibility record](smart_building_conformal/outputs/amendment004/bdg2_checkpoint_compatibility_v1/validation.json), [reproducible verifier](smart_building_conformal/scripts/verify_checkpoint_compatibility.py).

Fresh preparation reproduces configuration, features, outcomes, candidate grid and all 13 role hashes. Production output validation again passes **18 inner cells, 90 inner pairs, 25 outer pairs and 138 saved streams**. The new completed read calls `read_csv` **28 times**; its subsequent completeness check calls it **zero times**.

The exhaustive value audit records columns, dtypes, row counts and SHA-256 over ordered pandas row-value/index hashes for every frame. It then releases the loaded frame collection and parses each original CSV with the exact archived parser settings, one frame at a time, comparing those fingerprints. All payload values are compared directly. The full original file hashes, including the completion marker and manifest, match before and after. This avoids recreating the unsafe second all-frame allocation merely to test the repair.

## Measured memory and timing

| Measurement | Historical completed resume | Repaired compatibility scope |
|---|---:|---:|
| Process peak RSS | 4,748,304,384 bytes (4.422 GiB) | 3,024,769,024 bytes (2.817 GiB) |
| Minimum sampled available RAM | 633,327,616 bytes (0.590 GiB) | 2,544,988,160 bytes (2.370 GiB) |
| Comparable preparation/windows/identity/read/validation region | See historical phase records | 50.132 s |
| Full command | 86.231 s | 98.559 s, including the additional exhaustive value audit |

The comparable new region includes fresh preparation, windows, read-only identity checks, one load, completeness and production validation. The historical command also includes imports and journal operations; its individual corresponding phases are preserved in the [historical phase CSV](smart_building_conformal/outputs/amendment004/bdg2_pilot_validation_v1/phase_measurements.csv). The new full command additionally includes the separate all-value comparison and file-preservation audit, so its total is **not** a like-for-like speed claim. [New phase measurements](smart_building_conformal/outputs/amendment004/bdg2_checkpoint_compatibility_v1/phase_measurements.csv), [durable command/exit record](smart_building_conformal/outputs/amendment004/bdg2_threefold_validation_v1/compatibility_v1.log.json).

These are measured outcomes on the current Windows host, with 50 ms memory sampling and the OS lifetime RSS high-water mark. The observed RSS reduction is 1,723,535,360 bytes (1.605 GiB); it is not a promised reduction for larger folds. Available host RAM also changed because unused applications were closed. Numerical thread variables remain 1, and the existing 3 GiB launch guard remains unchanged. A no-fit preflight attempt correctly stopped below that guard; its failed log is preserved. No preparation-memory investigation or LSTM experiment was repeated.

The next two authorized folds have larger inner datasets. They retain the same scientific settings, run sequentially in fresh directories and receive separate resource and output checks. Their completion and actual costs are recorded in the three-fold benchmark report. Full-study readiness remains false.
