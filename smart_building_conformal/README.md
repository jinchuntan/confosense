# Uncertainty-Aware Short-Term Forecasting for Smart-Building IoT Sensor Data

Preliminary experiment for a Master's dissertation progress report. The pipeline
produces short-term indoor-temperature forecasts, conformal prediction
intervals (CQR and EnbPI), and an interval-based alerting scheme, and evaluates
all of them on the public **PLEIAData** smart-building dataset.

## What the pipeline does

1. Downloads and inventories the PLEIAData Zenodo record.
2. Selects one indoor-temperature series with a reproducible, documented rule.
3. Builds a regular 10-minute dataset with weather and HVAC covariates,
   documented outlier and missing-data handling, and leak-free features.
4. Trains point forecasters (persistence, seasonal naive, XGBoost, Attention-LSTM)
   at horizons of 1, 3 and 6 steps (10/30/60 minutes).
5. Produces conformalized prediction intervals with Conformalized Quantile
   Regression and EnbPI (static and sequentially updated) at 90% and 95%.
6. Defines interval-violation alerts, selects an aggregation rule on the
   calibration set, and evaluates it on clean and synthetically perturbed test
   data.
7. Runs a small preliminary robustness probe and reports bootstrap confidence
   intervals and multi-seed variability.
8. Writes report-ready tables, publication-quality figures and a factual results
   summary containing only measured values.

## Dataset

PLEIAData: consumption, HVAC, temperature, weather and motion-sensor data for
smart-building applications.

- Article: <https://www.nature.com/articles/s41597-023-02023-3>
- Zenodo record: <https://zenodo.org/records/7620136> (DOI 10.5281/zenodo.7620136)

The raw archive is **not** committed; it is downloaded on demand into
`data/raw/` and extracted into `data/interim/`.

## Setup

Python 3.11 is required.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Reproduce the experiment

A single command runs the whole preliminary experiment:

```bash
python -m src.run_experiment --config configs/pleia_preliminary.yaml
```

The dataset download and extraction happen automatically on the first run. To
download separately, or to inspect the files first:

```bash
python -m src.download_data --record-id 7620136
python -m src.inspect_pleia
```

A reduced smoke test (single horizon, few seeds) that exercises the entire code
path in a couple of minutes:

```bash
python -m src.run_experiment --config configs/pleia_preliminary.yaml --fast
```

Run the tests:

```bash
pytest -q
```

## Outputs

All artefacts are written under `outputs/`:

| Folder | Contents |
| --- | --- |
| `data_profiles/` | file inventory, target-selection audit, split summary, preprocessing summary, injected-event catalog |
| `metrics/` | point-forecast, CQR, EnbPI, combined interval, alert, robustness and bootstrap metrics |
| `predictions/` | test predictions for the point models and both conformal methods |
| `figures/` | Figures 4–7 and the metric comparison chart (from the run); Figures 2–3 and the graphical-abstract assets (from `scripts/`) |
| `models/` | fitted models, hyperparameters, LSTM training history and config |
| `report/` | `report_ready_results.md`, `result_placeholders_filled.md`, seed log, environment versions, test results |

## Repository layout

```
configs/    experiment configuration (all settings)
data/       raw / interim / processed (git-ignored)
src/        pipeline modules
scripts/    standalone figure generators (schematics only)
tests/      chronology, leakage, metric and alert tests
outputs/    generated results (created by the run)
```

## Standalone figures

`scripts/` holds generators for the figures that are **schematics rather than
results**: they read no data, no fitted model and no file under
`outputs/metrics`, and they never overwrite the experiment's own figures 4–7.

```bash
python scripts/generate_methodology_figures.py           # Figures 2-3
python scripts/generate_graphical_abstract.py            # graphical abstract
python scripts/generate_graphical_abstract_elements.py   # its separate elements
```

## Methodology notes

- Chronological order is preserved everywhere; there is no shuffling. The series
  is split 60/20/20 into train / calibration / test, and the ordering
  `train < calibration < test` is asserted.
- Scalers, imputers, feature transforms and the XGBoost hyperparameter search
  use the **training** partition only.
- The **calibration** partition is used only for conformal calibration and for
  selecting the alert-aggregation rule.
- The **test** partition is used once, for final evaluation.
- Synthetic perturbations are applied only to copies of the held-out test target;
  the original test data is preserved for clean false-alarm evaluation.
- Every automatic decision (target selection, covariate inclusion, thresholds)
  is recorded in `configs/pleia_preliminary.yaml` and in the profile CSVs.

See `outputs/report/report_ready_results.md` (after a run) for the measured
findings and their limitations.
