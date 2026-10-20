# ConfoSense
<img width="6333" height="3240" alt="Building_Context_and_Data_Sources" src="https://github.com/user-attachments/assets/4ed36412-06d2-4830-b4e1-4fd37f4b588c" />

Uncertainty-aware forecasting and alerting for smart-building sensor data.

ConfoSense compares persistence, XGBoost and Attention-LSTM forecasts, builds
prediction intervals with conformal methods, and studies how interval violations
can become useful monitoring alerts. The experiments cover temperature, energy
and HVAC data, with chronological evaluation and explicit controls for leakage.

## Start here

| What you need | Where to go |
| --- | --- |
| Completed results, tables and limitations | [Results index](RESULTS_INDEX.md) |
| Manuscript evidence and consolidated tables | [Evidence package](review/candidature_evidence_package_20261002_v1/) |
| Current manuscript figures and plotting script | [JBE figure package](report_figures/jbe_operational_20261018/) |
| Installation, code map and tests | [Development guide](docs/development.md) |
| Reproducing a recorded experiment | [Reproducibility guide](docs/reproducibility.md) |
| Earlier reports and implementation decisions | [Historical records](docs/history.md) |

## Code

The implementation lives in [smart_building_conformal](smart_building_conformal/):

- [src](smart_building_conformal/src/) — data adapters, forecasting, conformal
  intervals, monitoring, evaluation and reporting;
- [tests](smart_building_conformal/tests/) — unit and integration checks;
- [configs](smart_building_conformal/configs/) and
  [protocols](smart_building_conformal/protocols/) — experiment settings and
  frozen study definitions;
- [outputs](smart_building_conformal/outputs/) — recorded results and evidence.

[review](review/) contains the versioned adapters and validation records used
by completed studies. Some are required for reproduction; their paths are retained.

For a quick syntax and documentation check, run from the repository root:

```sh
python tools/check_repository.py
```

This command uses the standard library and does not import the research runners,
fit models, download datasets or modify results.

## Study scope

The completed evidence includes matched forecasting, interval-method and seasonal
comparisons, PLEIA conditional-context experiments, robustness and recalibration,
and a bounded BDG2 one-hour operational replay. See the results index for the
exact completed cells and their validation records.

Results describe the recorded datasets and protocols. They do not establish
universal robustness or a general computational advantage for Attention-LSTM.
Repeated seeds, overlapping folds and stream rows are not independent population
replicates.

## Data

Raw datasets are not committed. Source attribution and processing records are
preserved in the protocols and manifests.

- **PLEIAData:** separate temperature and energy tasks;
  [article](https://www.nature.com/articles/s41597-023-02023-3),
  [dataset](https://zenodo.org/records/7620136).
- **RICO:** controlled multivariate HVAC runs;
  [dataset](https://zenodo.org/records/14871584).
- **Building Data Genome 2:** hourly building energy data;
  [repository](https://github.com/buds-lab/building-data-genome-project-2).
- **UCI Occupancy Detection:** an auxiliary portability check;
  [dataset](https://doi.org/10.24432/C5X01N).

The three source datasets supply four core evaluation tasks. Errors measured
in different physical units are evaluated separately.
