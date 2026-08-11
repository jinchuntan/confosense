# ConfoSense

Uncertainty-aware short-term forecasting for smart-building IoT sensor data,
using conformal prediction for reliable alerts.

Master's dissertation project. The work pairs short-term forecasts of
smart-building sensor data with conformal prediction intervals, and turns
interval violations into an alerting scheme intended for monitoring and decision
support.

The code and outputs live in
[`smart_building_conformal/`](smart_building_conformal/) — see
[`smart_building_conformal/README.md`](smart_building_conformal/README.md) for
setup, commands and a description of every generated artefact.

## Two experiments

The repository holds two experiments, kept separate so neither overwrites the
other:

- **Preliminary PLEIAData experiment** — the completed indoor-temperature study
  used in the progress report and Proposal Defence. Reproduced by
  `python -m src.run_experiment --config configs/pleia_preliminary.yaml`;
  outputs live in `outputs/`. Treated as a frozen, reproducible baseline.
- **Full dissertation framework** — a multi-dataset study across PLEIAData
  (temperature and energy), RICO HVAC and a reproducibly selected Building Data
  Genome 2 subset, adding DSCP, an uncalibrated interval baseline, alert-rule
  sensitivity, closed-loop robustness, recalibration strategies and statistical
  comparison. Run with
  `python -m src.run_study --config configs/study_full.yaml --all`;
  outputs live in `outputs/full_study/`.

## Data

None of the raw datasets is committed; each is downloaded on demand from its
official source, and provenance (DOI, URL, checksum, licence, retrieval time) is
recorded in `outputs/full_study/manifests/dataset_sources.json`.

- **PLEIAData** — consumption, HVAC, temperature, weather and motion-sensor data
  for smart buildings.
  Article: <https://www.nature.com/articles/s41597-023-02023-3> ·
  Zenodo: <https://zenodo.org/records/7620136> (DOI 10.5281/zenodo.7620136)
- **RICO** — a multivariate HVAC indoor/outdoor time-series dataset of 4-hour
  controlled experimental runs, published by SINTEF AS Digital.
  Thiry, Ruocco, Nocente & Oksavik (2025), *Data in Brief* 61, 111678
  (DOI 10.1016/j.dib.2025.111678) ·
  Zenodo: <https://zenodo.org/records/14871584> (CC BY 4.0)
- **Building Data Genome Project 2** — hourly whole-building energy meter data.
  Miller et al. (2020), *Scientific Data* 7, 368
  (DOI 10.1038/s41597-020-00712-x) ·
  Repository: <https://github.com/buds-lab/building-data-genome-project-2>
