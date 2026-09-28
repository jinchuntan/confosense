# ConfoSense scientific package

This directory contains the maintained scientific implementation, frozen
protocols, focused tests, and result artifacts for the ConfoSense dissertation.
Start with the repository-level [`RESULTS_INDEX.md`](../RESULTS_INDEX.md) for the
status and evidence links for every completed workstream.

## Scope and interpretation

The current candidature evidence covers four separately evaluated tasks from
three source datasets: PLEIA temperature, PLEIA energy, RICO HVAC, and the
selected Building Data Genome 2 cohort. It includes matched point forecasting,
own-model conformal intervals, broader interval methods, seasonal baselines,
two PLEIA conditional-context challenges, and the frozen robustness,
contamination, and recovery extension.

The results are conditional on the recorded datasets, folds, seeds, protocols,
and fault definitions. They are not proof of universal robustness. The study
does not establish a general computational advantage for Attention-LSTM over
XGBoost. Population inference is unavailable because folds, model-seed aliases,
groups, and stream rows are dependent rather than independent population
replicates. The separate operational causal replay is partial and inactive.

## Environment setup

The delivered runs used Python 3.11 in a dedicated Windows environment. Exact
scientific versions are pinned in `requirements-lock.txt`, including MAPIE
1.4.1, NumPy 2.1.3, pandas 2.2.3, scikit-learn 1.5.2, PyTorch 2.13.0, and XGBoost
3.2.0.

From this directory on Windows PowerShell:

```powershell
py -3.11 -m venv .venv
& .venv/Scripts/python.exe -m pip install --upgrade pip
& .venv/Scripts/python.exe -m pip install -r requirements-lock.txt
```

On Linux or macOS, replace `.venv/Scripts/python.exe` with
`.venv/bin/python`. Raw datasets are not stored in Git; provenance, checksums,
and exact memberships live in the manifests and frozen protocols. Installing an
environment does not authorize a scientific rerun.

## Inspect existing results: lightweight and zero-fit

Inspection does not require a dataset download, model fit, conformalization, or
replay. Open these compact starting points:

- matched forecasting:
  `../review/matched_forecasting005_completion_20260923/EVIDENCE_INDEX.md`;
- interval methods and seasonal benchmark:
  `../review/matched_intervals_seasonal005_completion_20260924/EVIDENCE_INDEX.md`;
- PLEIA energy conditional context:
  `../review/pleia_energy_context005_multiseed_20260915/PLEIA_ENERGY_CONTEXT005_MULTISEED_REPORT.md`;
- PLEIA temperature conditional context:
  `../review/pleia_temperature_context005_multiseed_20260923/PLEIA_TEMPERATURE_CONTEXT005_FIVE_SEED_REPORT.md`;
- robustness, contamination, and recovery:
  `../review/robustness_contamination_recovery_20260928/COMPLETION_REPORT.md`.

For machine-readable completion summaries from the repository root:

```powershell
Get-Content review/matched_forecasting005_completion_20260923/DELIVERY_RECEIPT.json | ConvertFrom-Json
Get-Content review/matched_intervals_seasonal005_completion_20260924/PUBLICATION_RECEIPT.json | ConvertFrom-Json
Get-Content review/pleia_energy_context005_multiseed_20260915/COMPLETION_VERIFICATION.json | ConvertFrom-Json
Get-Content review/pleia_temperature_context005_multiseed_20260923/COMPLETION_VERIFICATION.json | ConvertFrom-Json
Get-Content review/robustness_contamination_recovery_20260928/COMPLETION_RESULT.json | ConvertFrom-Json
```

The compact CSV tables and figures linked by those indexes are committed. Bulk
run trees, checkpoints, and archives may be ignored by Git but remain scientific
evidence governed by their verified external-backup manifests; ignored does not
mean disposable.

## Maintained implementation

| Responsibility | Maintained modules |
|---|---|
| Dataset adapters and temporal identities | `src/datasets/`, `src/matched_data005.py`, `src/split_integrity.py`, `src/timebase.py` |
| Point models and matched forecasting | `src/matched_models005.py`, `src/matched_forecasting005.py`, `src/matched_validation005.py`, `src/unit_checkpoint.py` |
| Conformal methods and interval comparison | `src/conformal_cqr.py`, `src/conformal_enbpi.py`, `src/conformal_dscp.py`, `src/conformal_acp.py`, `src/matched_intervals005.py`, `src/intervals005_common.py`, `src/intervals005_data.py`, `src/intervals005_owners.py`, `src/intervals005_stream.py`, `src/intervals005_validate.py` |
| Conditional-context replay and alerts | `src/conditional_context005.py`, `src/context005_data.py`, `src/context005_features.py`, `src/context005_metrics.py`, `src/context005_owner.py`, `src/context005_spec.py`, `src/context005_validate.py`, `src/alerts_corrected.py`, `src/residuals.py` |
| Study assembly and reporting | `src/corrected_study.py`, `src/reporting.py`, `src/statistics.py`, `src/seasonal.py` |

The package-level modules contain reusable science. Dated scripts under
`../review/` bind frozen protocols, hash identities, validation, recovery, and
delivery for a particular completed execution.

## Required versioned adapters

Some accepted results intentionally depend on versioned adapters outside
`src/`; moving their logic into frozen source would erase provenance.

- `../review/matched_intervals_seasonal005_completion_20260924/corrected_validator_v1.py`
  preserves the independently derived MAPIE 1.4.1 rank-arithmetic correction.
  `corrected_validator_v2.py` adds the fresh-process import bootstrap without
  changing that arithmetic, tolerances, or scientific outputs.
- `../review/robustness_contamination_recovery_20260928/robustness_saved_owner_v1.py`
  replays exact saved owners for the frozen 900-cell extension;
  `validate_saved_owner_v1.py` is its independent validator.
- Conditional-context and completion coordinators in their dated review
  directories bind exact protocols and accepted checkpoint identities. They are
  preserved reproduction dependencies, not a second maintained framework.

The partial operational adapter under
`../review/operational005_causal_replay_20260925/` remains historical work in
progress. Its presence is not evidence that the operational grid completed.

## Entry-point discovery and focused checks

These commands only show the maintained command surfaces:

```powershell
python -m src.matched_forecasting005 --help
python -m src.matched_intervals005 --help
python -m src.conditional_context005 --help
python ../review/robustness_contamination_recovery_20260928/completion_v1.py --help
```

These focused tests use synthetic or saved fixtures and perform no model fit or
scientific replay:

```powershell
python -m pytest -q tests/test_residual_delay.py
python -m pytest -q tests/test_matched_forecasting005.py::test_future_observations_do_not_change_training_inputs tests/test_matched_forecasting005.py::test_tuning_rejects_calibration_test_contamination_and_future_targets tests/test_matched_forecasting005.py::test_forbidden_fit_guard_stops_before_model_body
python -m pytest -q ../review/matched_intervals_seasonal005_completion_20260924/test_corrected_validator_v1.py ../review/robustness_contamination_recovery_20260928/test_saved_owner_v1.py ../review/robustness_contamination_recovery_20260928/test_completion_v1.py
```

## Reproduce experiments: expensive and protocol-bound

Scientific reproduction is deliberately separate from inspection. It requires
the original data, the exact locked environment, sufficient RAM and storage,
the frozen protocol and authorization files, and a new non-overwriting output
path. The exact instantiated argument arrays are recorded in each dated
coordinator's attempt receipts. Those arrays, rather than an edited README
example, are authoritative for a bit-for-bit scope audit.

The family-level execution entry points retained by the delivered workflows
are:

```powershell
# Repository root; completed queues are identity-checked and should be no-ops.
python -B review/matched_forecasting005_completion_20260923/batch.py coordinate
python -B review/matched_intervals_seasonal005_completion_20260924/coordinator.py --run
python -B review/pleia_energy_context005_multiseed_20260915/coordinator.py
python -B review/pleia_temperature_context005_multiseed_20260923/coordinator.py

# One frozen robustness unit; UNIT_KEY must come from CROSSWALK.csv.
python -B review/robustness_contamination_recovery_20260928/completion_v1.py run-unit --unit UNIT_KEY
```

These are expensive/recovery commands, not reviewer inspection commands. The
completed coordinators are closed, the robustness extension requires no further
execution, and the operational supervisor must remain stopped. Any fresh
reproduction should be explicitly authorized and isolated from accepted output
paths.

## Superseded historical commands

The following remain in the repository solely for historical reproduction and
comparison with earlier dissertation stages:

- `python -m src.run_experiment --config configs/pleia_preliminary.yaml` — the
  preliminary PLEIA experiment;
- `python -m src.run_study --config configs/study_full.yaml --all` — the generic
  pre-amendment full-study driver;
- `python -m src.run_uci_auxiliary --config configs/uci_auxiliary.yaml` — the
  auxiliary portability check.

They are not authoritative entry points for the accepted matched, interval,
conditional-context, or robustness results and must not overwrite their frozen
artifacts.

## Repository conventions

- Never treat seed aliases, folds, groups, or stream rows as independent
  population replicates without a justified design.
- Keep unavailable metrics explicit; do not manufacture scalar summaries for
  unsupported multi-group outcomes.
- Use explicit Git staging lists. Bulk output exclusions are narrow preservation
  boundaries, not permission to delete evidence.
- Preserve frozen protocols, failed attempts, saved owners, operation ledgers,
  validation receipts, and backup manifests.
- Main is not the candidature integration branch; use the submission review
  branch named in the root results index and delivery handoff.
