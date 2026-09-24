# Fresh-process import recovery v2

The `bdg2_f1_s42` experiment completed normally, but its first corrected-validation child failed before argument parsing because Python script mode placed the external review directory on `sys.path`. The recorded scientific cwd was correct, but cwd was not itself an import entry and the process inherited an empty `PYTHONPATH`. Therefore the preserved `corrected_validator_v1.py` could not import `smart_building_conformal/src`.

The hash-bound v1 validator remains byte-identical at `c13f4da453b59add612cb37996e45477c3b56a6618a3439116d7e42a790909b5`. The new `corrected_validator_v2.py` is only a fresh-process bootstrap: it resolves the scientific root from its own location before importing v1. The coordinator additionally supplies that root through its process-local child environment; it does not change global `PATH`, frozen `src`, tolerances, outputs, or the scientific contract.

Import-only checks reproduced the v1 failure and passed for v2 from both the production scientific cwd and an external backup cwd. The coordinator and finisher import paths also passed from the external cwd. No experiment was used as an import smoke test.

The already-completed `bdg2_f1_s42` output then passed the full corrected independent validation for all 30 method cells with zero model fits and zero calibrator fits. Its zero-fit resume verified 138 stages. `COMPLETE.json`, `operations.jsonl`, `checkpoint_manifest.json`, and `operation_counts.json` retained their exact pre-validation hashes. The original failed attempt and log remain preserved and hash-pinned in `IMPORT_BOOTSTRAP_RECOVERY_V2.json`.
