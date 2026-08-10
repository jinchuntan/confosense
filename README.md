# ConfoSense

Uncertainty-aware short-term forecasting for smart-building IoT sensor data,
using conformal prediction for reliable alerts.

Master's dissertation project. The work pairs short-term forecasts of indoor
temperature with conformal prediction intervals, and turns interval violations
into an alerting scheme intended for monitoring and decision support.

The experiment, its code and its outputs live in
[`smart_building_conformal/`](smart_building_conformal/) — see
[`smart_building_conformal/README.md`](smart_building_conformal/README.md) for
setup, the single command that reproduces the run, and a description of every
generated artefact.

## Data

PLEIAData: consumption, HVAC, temperature, weather and motion-sensor data for
smart-building applications.

- Article: <https://www.nature.com/articles/s41597-023-02023-3>
- Zenodo record: <https://zenodo.org/records/7620136> (DOI 10.5281/zenodo.7620136)

The raw archive is not committed; it is downloaded on demand by the pipeline.
