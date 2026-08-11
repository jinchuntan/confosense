# Uncertainty-Aware Short-Term Forecasting for Smart-Building IoT Sensor Data

ConfoSense pairs short-term forecasts of smart-building sensor data with
conformal prediction intervals, and turns interval violations into an alerting
scheme for monitoring and decision support.

## Two experiments live here — read this first

The repository contains **two distinct experiments**, deliberately kept apart so
that neither can overwrite the other.

| | Preliminary experiment | Full dissertation framework |
| --- | --- | --- |
| Purpose | Progress report and Proposal Defence | The dissertation study |
| Datasets | PLEIAData indoor temperature | PLEIAData (temperature + energy), RICO HVAC, BDG2 |
| Entry point | `python -m src.run_experiment --config configs/pleia_preliminary.yaml` | `python -m src.run_study --config configs/study_full.yaml --all` |
| Config | `configs/pleia_preliminary.yaml` | `configs/study_full.yaml` (+ per-dataset files) |
| Outputs | `outputs/metrics`, `outputs/predictions`, `outputs/figures`, `outputs/report` | `outputs/full_study/` |
| Status | **Complete and reported.** Reproducible baseline; do not modify | See "Execution status" below |

The preliminary results have already been used in the progress report and the
Proposal Defence slides, so that experiment is treated as a frozen, reproducible
baseline. The full study writes only under `outputs/full_study/` and never
touches the preliminary output folders.

---

# Part 1 — Preliminary experiment (progress report)

Produces short-term indoor-temperature forecasts, conformal prediction intervals
(CQR and a recentred EnbPI adaptation), and an interval-based alerting scheme,
evaluated on the public **PLEIAData** smart-building dataset.

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

---

# Part 2 — Full dissertation experimental framework

The full study generalises the preliminary pipeline to three datasets and adds
the methods, sensitivity analyses and statistical comparisons the dissertation
requires. It shares the forecasting, conformal, metric and alert code with the
preliminary experiment; what changed is that everything now runs against a
common prepared-data representation instead of one PLEIAData frame.

## Datasets

| Dataset | Target | Sampling | Horizons | Structure |
| --- | --- | --- | --- | --- |
| **PLEIAData** | indoor temperature (block B, room 11, `V2`) | 10 min | 1, 3, 6 steps (10/30/60 min) | one long series |
| **PLEIAData** | interval energy consumption (`dif_cons`) | 10 min | 1, 3, 6 steps | one long series |
| **RICO HVAC** | indoor air temperature (`B.RTD3`) | 1 min | 5, 15, 30, 60 steps | 207 independent 4-hour runs |
| **BDG2** | hourly electricity (kWh) | 1 h | 1, 3, 6 steps | ~10 independent buildings |

Sources, DOIs, checksums, licences and preprocessing decisions are recorded in
`outputs/full_study/manifests/dataset_sources.json`. Raw data is never committed.

- **PLEIAData** — Zenodo record 7620136 (DOI 10.5281/zenodo.7620136).
- **RICO** — Thiry et al. (2025), *Data in Brief* 61, 111678
  (DOI 10.1016/j.dib.2025.111678); official SINTEF Zenodo deposit
  [record 14871584](https://zenodo.org/records/14871584), CC BY 4.0.
- **BDG2** — Miller et al. (2020), *Scientific Data* 7, 368
  (DOI 10.1038/s41597-020-00712-x); the authors' repository
  `buds-lab/building-data-genome-project-2` (files are Git LFS, so the LFS media
  endpoint is used).

```bash
python -m src.fetch_datasets --all        # RICO + BDG2, resumable
python -m src.download_data --record-id 7620136   # PLEIAData
```

## Methods

**Point forecasting** — persistence, seasonal naive, XGBoost, Attention-LSTM,
all trained as *direct* horizon-specific models. No prediction is ever fed back
in as an input.

**Prediction intervals** — reported under exact, non-interchangeable names:

| Name in outputs | What it is |
| --- | --- |
| `quantile_uncalibrated` | the raw quantile band **before** conformal calibration, taken from the very sub-estimators CQR conformalizes, so the two differ only by the conformal step |
| `cqr` | Conformalized Quantile Regression |
| `recentred_enbpi_static` | the documented recentred EnbPI adaptation, residuals fixed |
| `recentred_enbpi_updated` | the same, with residuals folded in online |
| `dscp` | Dual-Splitting Conformal Prediction (Yu et al. 2025) |

The EnbPI variants are an adaptation and are never labelled as standard EnbPI.

**Alerting** — configurable k-of-m rules (`1-of-1`, `2-of-3`, `3-of-5`,
`4-of-7`). The operating rule is selected on **calibration data only**; all
candidates are then re-scored on test purely for sensitivity reporting, and the
two roles are distinguished by a `role` column, not just in prose. Point-level
False Alarm Rate (`far`) and false alert **events per day** are reported as
separate quantities.

**Robustness** — random and block missingness, constant bias, level shift,
gradual drift, stuck sensor, dropout, and calibration contamination, in two
modes: `legacy_fixed_intervals` (preliminary behaviour, preserved) and
`closed_loop` (primary — the perturbation propagates into lagged features and
the model re-forecasts from the corrupted history).

**Recalibration** — static, periodic and rolling. Adaptive strategies consume a
residual only once its ground truth has been observed: for horizon *h* a
residual becomes usable *h* steps after its forecast origin. This fixes the
online-residual-availability limitation identified in the preliminary report.

**Statistics** — moving-block bootstrap CIs for *every* point model (baselines
included), Diebold-Mariano with the Harvey-Leybourne-Newbold correction,
Friedman across blocks, Holm-adjusted post-hoc comparisons, and effect sizes.

## Commands

```bash
# Smoke tests (minutes) — same code paths, smaller settings
python -m src.run_study --config configs/study_full.yaml --dataset pleia --fast
python -m src.run_study --config configs/study_full.yaml --dataset rico  --fast
python -m src.run_study --config configs/study_full.yaml --dataset bdg2  --fast

# Full runs
python -m src.run_study --config configs/pleia_full.yaml --all
python -m src.run_study --config configs/rico_full.yaml  --all
python -m src.run_study --config configs/bdg2_full.yaml  --all
python -m src.run_study --config configs/study_full.yaml --all          # everything

# Resume an interrupted run (reuses only stages from the same config hash)
python -m src.run_study --config configs/study_full.yaml --all --resume

# Debug a single stage or horizon
python -m src.run_study --config configs/study_full.yaml --dataset rico \
    --stage intervals --horizon 5
```

`--fast` reduces horizons, seeds, search iterations, epochs, bootstrap
replicates, BDG2 building count and disturbance repetitions. It exercises the
same code paths as a full run — it is a smoke test, not a second methodology —
and every run it produces is stamped `fast_mode` in the manifest and report.

## Full-study outputs

```
outputs/full_study/
    pleia/ | pleia_energy/ | rico/ | bdg2/
        data_profiles/   series profile, split summary, selection audits,
                         injected-event catalog
        metrics/         point, interval, alert, robustness, recalibration,
                         bootstrap, Diebold-Mariano, effect sizes
        predictions/     point and interval predictions
        models/          tuned hyperparameters, LSTM history, DSCP state
    combined/            cross-dataset tables and model rankings
    report/              full_study_results.md, table_ready_results.md,
                         full_study_limitations.md, figures/
    manifests/           dataset_sources.json, experiment_manifest.json,
                         resume_ledger.json
```

Key audit files: `bdg2/data_profiles/subset_selection.csv` (every candidate
building with the reason it was kept or dropped), `rico/data_profiles/
run_audit.csv` (every experimental run and its partition), and
`*/metrics/alert_rule_selection_calibration.csv` (the full calibration rule
surface the operating rule was chosen from).

## Execution status

| Component | Status |
| --- | --- |
| Preliminary PLEIAData experiment | **complete and reported**; regression-verified |
| Multi-dataset architecture | implemented, tested |
| PLEIAData full study | implemented; smoke-tested |
| PLEIAData energy target | implemented; smoke-tested |
| RICO adapter and study | implemented; smoke-tested |
| BDG2 subset selection and study | implemented; smoke-tested |
| DSCP | implemented from the open-access preprint; unit-tested |
| Alert-rule sensitivity | implemented; smoke-tested |
| Robustness (both modes) and recalibration | implemented; smoke-tested |
| Statistical analysis | implemented; smoke-tested |
| **Full (non-`--fast`) multi-dataset run** | **not yet executed** — see the commands above |

Where a component is marked *implemented / smoke-tested*, the code runs end to
end under `--fast` and writes real outputs, but the full-scale numbers have not
been produced. No result is claimed for an experiment that has not run; the
generated `full_study_limitations.md` lists anything that failed or was skipped
in a given run.

---

## Repository layout

```
configs/    pleia_preliminary.yaml (frozen) + study_full.yaml and per-dataset configs
data/       raw / interim / processed (git-ignored)
src/        pipeline modules
  datasets/     dataset adapters (base, pleia, rico, bdg2) + registry
  windowing.py  group-safe supervised windowing
  residuals.py  delayed residual availability
  recalibration.py, statistics.py, conformal_dscp.py, conformal_quantile.py
  alert_study.py, robustness_study.py
  study_runner.py, run_study.py, manifest.py
  study_plotting.py, study_reporting.py
scripts/    standalone figure generators (schematics only)
tests/      chronology, leakage, group-integrity, metric, alert, DSCP,
            statistics, manifest/resume and output-schema tests
outputs/    preliminary results (committed) + full_study/ (generated)
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

The full study adds three rules on top of these:

- **Group integrity.** A RICO experimental run is assigned whole to one
  partition, and no feature window may cross a run or a BDG2 building boundary.
  Both hold by construction — features are built one series at a time — and are
  asserted in `tests/test_windowing_integrity.py`.
- **Delayed residuals.** An adaptive method may use a test residual only after
  its ground truth has been observed: at horizon *h*, *h* steps after the
  forecast origin. This also applies to the calibration replay used to choose
  recalibration parameters, which is split with an *h*-step embargo.
- **Rule selection before test.** The alert operating rule is frozen from the
  calibration surface; the test surface is reported as `post_hoc_sensitivity`
  and never feeds back into the choice.

## Reproducibility

- **Seeds.** One global seed (`seed:` in the config) drives every stochastic
  component; per-method seeds are derived from it and the numbers actually used
  are written to the outputs, never assumed.
- **Manifest.** Each full-study run writes
  `outputs/full_study/manifests/experiment_manifest.json`: git commit and dirty
  flag, config path and hash, package versions, machine, seeds, timings, and
  every stage that completed, failed or was skipped with its reason.
- **Provenance.** `manifests/dataset_sources.json` records each dataset's
  official source, DOI, URL, retrieval time, archive name, checksum, licence and
  preprocessing decisions.
- **Resume.** `--resume` reuses only stages recorded under the *same* config
  hash; a changed configuration discards the ledger and says so, so results from
  two different configurations can never be mixed.
- **Regression check.** To confirm the preliminary experiment still reproduces
  after a change, redirect its outputs and diff against the committed CSVs:

  ```bash
  # copy configs/pleia_preliminary.yaml, set paths.outputs_dir to
  # outputs/regression_check, then:
  python -m src.run_experiment --config <redirected-config>.yaml
  ```

  `outputs/regression_check*/` is git-ignored, so the committed preliminary
  results are never overwritten by a verification run.

## Tests

```bash
pytest -q
```

The suite uses small synthetic arrays and never downloads an external dataset.
It covers chronological and group-level split integrity, feature leakage,
direct-horizon targets, delayed residual availability, DSCP mechanics, interval
ordering and metric correctness, k-of-m rules, event matching and detection
delay, FAR against false-alerts-per-day, in-place perturbation safety,
closed-loop causality, reproducible BDG2 subset selection, RICO run
segmentation, manifest/resume behaviour, and the persisted output schemas.

See `outputs/report/report_ready_results.md` (preliminary) and
`outputs/full_study/report/full_study_results.md` (full study) after a run for
the measured findings and their limitations.
