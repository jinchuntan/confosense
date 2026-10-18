# Scientific package

This directory contains ConfoSense's implementation, tests, experiment definitions
and saved outputs. Start with the [results index](../RESULTS_INDEX.md) for the
completed studies and the [development guide](../docs/development.md) for a module map.

## Install

The recorded scientific environment used Python 3.11. Exact package versions are
in [requirements-lock.txt](requirements-lock.txt); supported dependency ranges are
in [requirements.txt](requirements.txt).

From the repository root:

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r smart_building_conformal/requirements-lock.txt
python -m pip install -r requirements-dev.txt
```

Activate the environment before running the install commands. Use Python 3.11
when creating the environment for scientific reproduction.

## Check the code

From the repository root:

```sh
python tools/check_repository.py
python tools/check_repository.py --tests
ruff check .
ruff format --check .
```

The first command parses Python and checks links without importing experiment
runners. `--tests` adds a small synthetic suite covering metrics, temporal leakage,
alerts, windowing, statistics, recalibration and figure generation. It does not
need raw data or train models.

Run the wider package suite from this directory after installing the scientific
dependencies:

```sh
python -m pytest
```

Some integration tests require committed protocol files, saved evidence or small
model fits. The smoke suite is the lightweight option for routine maintenance.

## Implementation

| Area | Modules |
| --- | --- |
| Data and temporal splits | [datasets](src/datasets/), [split_integrity](src/split_integrity.py), [windowing](src/windowing.py) |
| Matched forecasts | [matched_forecasting005](src/matched_forecasting005.py), [matched_models005](src/matched_models005.py) |
| Conformal intervals | [conformal_cqr](src/conformal_cqr.py), [conformal_enbpi](src/conformal_enbpi.py), [conformal_dscp](src/conformal_dscp.py), [matched_intervals005](src/matched_intervals005.py) |
| Monitoring | [conditional_context005](src/conditional_context005.py), [alerts_corrected](src/alerts_corrected.py), [residuals](src/residuals.py), [recalibration](src/recalibration.py) |
| Metrics and reporting | [metrics](src/metrics.py), [reporting](src/reporting.py), [statistics](src/statistics.py) |
| Checkpoint integrity | [unit_checkpoint](src/unit_checkpoint.py) |

The dated [review adapters](../review/) supply the exact saved-owner replay,
independent interval-rank correction and completion validation used by particular
published runs. The [reproducibility guide](../docs/reproducibility.md) identifies them.

## Recorded experiments

Saved checkpoints include hashes of the scientific source, configuration and
input identities. Formatting a source file changes that identity, even when its
calculations stay the same. The development formatter therefore covers tests and
tools; it leaves the recorded scientific source and evidence outside its scope.

Use the protocol, source version, dependency environment and output paths recorded
by the study being reproduced. Historical commands such as `src.run_experiment`,
`src.run_study --all` and `src.run_uci_auxiliary` remain available, but do not
regenerate every completed study. Use a separate output directory for fresh runs.
