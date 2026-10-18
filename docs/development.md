# Development

## Environment

The scientific runs used Python 3.11. From the repository root, create and activate
a virtual environment, then install the recorded environment and development tools:

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r smart_building_conformal/requirements-lock.txt
python -m pip install -r requirements-dev.txt
```

[requirements-lock.txt](../smart_building_conformal/requirements-lock.txt) records
exact scientific versions. [requirements.txt](../smart_building_conformal/requirements.txt)
provides dependency ranges for a development environment; using those ranges does
not establish an exact reproduction of a recorded run.

## Everyday checks

```sh
python tools/check_repository.py
python tools/check_repository.py --tests
ruff check .
ruff format --check .
```

The first check uses only the standard library. It parses Python files without
executing them and checks local links in the maintained guides. It understands
tracked paths in a sparse checkout, so missing local copies of large output
folders do not count as broken links.

The smoke tests need NumPy, pandas, SciPy, Matplotlib and pytest. They use synthetic
data and temporary directories, without dataset downloads or model training.
The full scientific environment is needed for the wider suite.

To run that suite:

```sh
cd smart_building_conformal
python -m pytest
```

Some tests inspect saved artifacts; others make small model fits. Check the test
being selected before treating it as an inspection-only command.

To format the test and maintenance code:

```sh
ruff format .
```

The [formatter configuration](../pyproject.toml) excludes scientific source,
versioned review scripts, protocols, outputs and publication figures. Their exact
bytes are part of the saved experiment identities.

For a maintenance change that should preserve the scientific source, compare
against its starting commit:

```sh
python tools/check_repository.py --source-ref STARTING_COMMIT
```

This verifies every scientific Python file against the given Git revision and
reports additions, changes or missing files.

## Code map

| Area | Start with |
| --- | --- |
| Dataset interface | [datasets/base.py](../smart_building_conformal/src/datasets/base.py) |
| Features and windows | [features.py](../smart_building_conformal/src/features.py), [windowing.py](../smart_building_conformal/src/windowing.py) |
| Chronological and grouped splits | [split_integrity.py](../smart_building_conformal/src/split_integrity.py) |
| Point forecasters | [baselines.py](../smart_building_conformal/src/baselines.py), [xgboost_model.py](../smart_building_conformal/src/xgboost_model.py), [attention_lstm.py](../smart_building_conformal/src/attention_lstm.py) |
| Matched forecasting | [matched_forecasting005.py](../smart_building_conformal/src/matched_forecasting005.py) |
| Interval comparison | [matched_intervals005.py](../smart_building_conformal/src/matched_intervals005.py) |
| Delayed residuals and recalibration | [residuals.py](../smart_building_conformal/src/residuals.py), [recalibration.py](../smart_building_conformal/src/recalibration.py) |
| Conditional-context monitoring | [conditional_context005.py](../smart_building_conformal/src/conditional_context005.py) |
| Operational replay | [operational004_engine.py](../smart_building_conformal/src/operational004_engine.py), [completed replay adapter](../review/operational005_causal_replay_20260925/) |
| Checkpoints | [unit_checkpoint.py](../smart_building_conformal/src/unit_checkpoint.py) |
| Manuscript figures | [JBE plotting package](../report_figures/jbe_operational_20261018/) |

Modules with numbered study names bind a particular experimental design. Renaming
or merging them can change imports, source hashes and reproducibility contracts.
Use the [reproducibility guide](reproducibility.md) before changing those boundaries.

## Working conventions

- Keep features and calibration restricted to information available at the forecast origin.
- Evaluate targets with different units separately.
- Keep unsupported metrics explicit instead of filling them with estimates.
- Put new runs in separate directories; retain the protocol and source identity.
- Keep local environments, credentials, caches and temporary files out of commits.
- Stage specific paths when working near the large evidence folders.
