# ConfoSense

ConfoSense is a master's dissertation codebase for uncertainty-aware,
short-term smart-building forecasting. It compares point forecasters and
conformal interval methods, then evaluates interval-based monitoring under
conditional faults, contamination, and recovery scenarios.

## Reviewer start here

1. [`RESULTS_INDEX.md`](RESULTS_INDEX.md) is the authoritative map of completed
   results, compact artifacts, validation evidence, and limitations.
2. [`smart_building_conformal/README.md`](smart_building_conformal/README.md)
   explains the maintained implementation, environment, lightweight inspection,
   and the guarded reproduction entry points.
3. [`PANEL_RESPONSE_MATRIX.md`](PANEL_RESPONSE_MATRIX.md) separates validated
   evidence from candidature writing and presentation work that is still needed.
4. [`PROJECT_RECOVERY_STATUS.md`](PROJECT_RECOVERY_STATUS.md) is the operational
   recovery record. It is useful when auditing historical recovery decisions,
   but is not the current results index.

The current submission history contains the completed forecasting,
interval-method, seasonal, PLEIA conditional-context, and robustness deliveries.
Their prior review branches are preserved as provenance; the necessary compact
code and result artifacts are also reachable from this submission branch.

## Current scientific status

| Workstream | Status |
|---|---|
| Matched forecasting | Complete: 195/195 units, 585/585 point cells, and 1,170/1,170 own-model interval cells |
| Interval methods and seasonal benchmark | Complete: 1,950/1,950 method cells and 27/27 unique seasonal computations |
| PLEIA conditional-context challenge | Complete for the declared temperature and energy five-seed designs; each has 68 original contexts and 60 aggregate control/rule/channel cells |
| Robustness, contamination, and recovery | Complete for the frozen extension: 60/60 units and 900/900 cells |
| Operational causal replay | Partial and inactive: 72/825 policy blocks were accepted locally before the preserved run stopped; it is not a completed result |

These are bounded results for the declared datasets, folds, seeds, methods, and
fault protocols. They do not prove universal robustness. The matched study did
not establish a general computational benefit for Attention-LSTM over XGBoost.
Population inference is unavailable under the recorded dependence structure;
folds, model-seed aliases, groups, and stream rows are not treated as independent
population replicates.

No experiment should be started from a README command merely to inspect the
submission. The operational replay remains paused, and all scientific execution
is inactive.

## Repository map

- [`smart_building_conformal/src/`](smart_building_conformal/src/) contains the
  maintained reusable scientific implementation.
- [`smart_building_conformal/tests/`](smart_building_conformal/tests/) contains
  focused, zero-fit unit and integration checks.
- [`smart_building_conformal/configs/`](smart_building_conformal/configs/) and
  [`smart_building_conformal/protocols/`](smart_building_conformal/protocols/)
  retain configuration and frozen scientific identities.
- [`review/`](review/) contains versioned adapters, validators, reports, and
  delivery records. Required versioned adapters are listed in the package
  README; dated orchestrators are not interchangeable general entry points.
- [`smart_building_conformal/outputs/`](smart_building_conformal/outputs/)
  contains compact committed result tables and figures as well as locally
  preserved bulk evidence. Ignored output is not disposable output.

## Data

Raw datasets are not committed. Their provenance is recorded in the study
manifests and frozen protocols.

- **PLEIAData** supplies separate temperature and energy tasks. Article:
  <https://www.nature.com/articles/s41597-023-02023-3>; Zenodo:
  <https://zenodo.org/records/7620136> (DOI 10.5281/zenodo.7620136).
- **RICO** supplies controlled multivariate HVAC runs. Thiry, Ruocco, Nocente
  and Oksavik (2025), *Data in Brief* 61, 111678; Zenodo:
  <https://zenodo.org/records/14871584>.
- **Building Data Genome Project 2** supplies hourly whole-building energy data.
  Miller et al. (2020), *Scientific Data* 7, 368; repository:
  <https://github.com/buds-lab/building-data-genome-project-2>.
- **UCI Occupancy Detection** is an auxiliary portability check, not a fourth
  source dataset or fifth core task. DOI 10.24432/C5X01N.

The three source datasets and four core evaluation tasks are evaluated
separately; raw errors in different physical units are not pooled.

## Historical commands

The preliminary `src.run_experiment`, generic `src.run_study --all`, and
`src.run_uci_auxiliary` workflows remain available for historical reproduction.
They are superseded as entry points for the completed candidature results and
must not be used to regenerate or overwrite the frozen deliveries. Use the
family-specific commands and exact protocols identified in the package README
and dated evidence indexes instead.
