# BDG2 retrospective alert-budget pilot

Completed and independently audited: 2 November 2026.

## Finding

This pilot does **not** establish that CQR generally improves building-event
detection over simpler threshold choices. The scaled-quantile comparator has
higher observed recall than separate-tail CQR at all three validation budgets.
The primary separate-tail-CQR versus seasonal-residual comparison has descriptive
site-cluster intervals spanning zero for recall, delay and workload at every
budget. These are inconclusive comparisons, not proof of equivalence.

The candidate methods target the same selection-stream episode budgets, but
their achieved test workloads differ. They must not be presented as exactly
matched-workload comparisons. No test-workload matching or policy retuning was
performed after looking at these outcomes.

## What was evaluated

Ten previously studied BDG2 buildings across six sites; three chronological test
periods; five fitting seeds; five injected-event catalogues per unit. Each unit
uses the same histogram gradient boosting quantile forecasts for every detector.
Fitting, calibration, budget selection and test streams have separate chronological
roles with target-to-origin embargoes. The four detector choices are separate-tail
CQR, symmetric CQR, scaled raw-quantile intervals and a specified seasonal-residual
threshold. All are retained at 0.25, 0.5 and 1 episode/asset-day selection budgets.

This is a new retrospective follow-up, not a reproduction of manuscript Table 6.
It uses HGB, new fitting/selection roles and a new event schedule. Original
manuscript evidence is unchanged. The cohort and historical periods had already
been inspected. They cannot be described as untouched confirmatory data.

The scaled-quantile and seasonal-residual candidate grids include calibration
score quantiles as well as fixed multipliers. They are simple calibration-based
comparators, not purely uncalibrated detectors. This experiment compares interval
geometry and threshold choices; it does not refute all forms of conformal
calibration.

The five fitting seeds produce identical clean prediction streams within each
period (one distinct stream per period), as recorded in `SEED_IDENTITY.json`.
Repeated seeds therefore add no observed fitting variability in this HGB pilot.
They are not independent replications, and they are not the bootstrap unit.

## Numerical alert results

These recall values include the observed effective disturbance families, including
missing-data events; numerical alerts do not directly flag missing observations.
All values below are building-balanced descriptive averages. Delay assigns misses
the full six-hour restriction. Background workload and active-time fraction are
measured on the original uninjected stream.

| Validation budget | Method | Test episodes/asset-day | Time in alert | Macro event recall | Restricted delay, min |
| --- | --- | ---: | ---: | ---: | ---: |
| 0.25 | Separate-tail CQR | 0.2462 | 1.14% | 0.3591 | 261.68 |
| 0.25 | Symmetric CQR | 0.2112 | 0.99% | 0.3382 | 267.59 |
| 0.25 | Scaled quantile | 0.2371 | 1.05% | 0.4101 | 243.90 |
| 0.25 | Seasonal residual | 0.4201 | 3.59% | 0.3971 | 257.82 |
| 0.50 | Separate-tail CQR | 0.4865 | 2.26% | 0.4641 | 235.04 |
| 0.50 | Symmetric CQR | 0.4372 | 2.04% | 0.4407 | 241.00 |
| 0.50 | Scaled quantile | 0.4981 | 2.25% | 0.5085 | 221.76 |
| 0.50 | Seasonal residual | 0.6804 | 5.74% | 0.4981 | 230.61 |
| 1.00 | Separate-tail CQR | 1.0278 | 6.59% | 0.6017 | 203.66 |
| 1.00 | Symmetric CQR | 1.0031 | 4.88% | 0.5958 | 204.03 |
| 1.00 | Scaled quantile | 1.0005 | 8.75% | 0.6163 | 200.49 |
| 1.00 | Seasonal residual | 1.1870 | 10.42% | 0.6285 | 198.02 |

At the 0.5 selection budget, scaled quantiles have 4.44 percentage points higher
observed numerical-channel recall than separate-tail CQR, at similar achieved
workload and active time. This comparison was not the prespecified primary
comparison and is descriptive; no inferential superiority claim is made.

The separate-tail-CQR minus seasonal-residual numerical recall differences are
-0.0381, -0.0340 and -0.0267 at increasing budgets. Their descriptive 95%
site-cluster intervals are [-0.2328, 0.1231], [-0.2076, 0.1130] and
[-0.1168, 0.0639]. Different achieved workloads limit a direct detection-quality
interpretation of these differences.

## Missing-reading and coincidence controls

At the 0.5 selection budget, adding the same missing-reading rule raises observed
combined-channel recall to 0.6878 for separate-tail CQR and 0.7316 for scaled
quantiles. This additional detection is partly attributable to explicit missing
flags, not numerical calibration. Original-stream coincidence recall in the same
event windows is 0.1169 and 0.1195 respectively. This negative control is reported
separately and is not subtracted from recall as a causal adjustment.

All channels, budgets and descriptive raw-95% reference policies are recorded in
`results_v1/summary.csv`. Building, family/severity and primary-comparison tables
are also retained. The seasonal baseline can exceed its validation workload target
substantially at test; a selected budget is not a deployment guarantee.

## Verification and recovery

All 15 units pass independent reconstruction of episode onsets, workload, active
time, exposure and event matching from packed emitted flags. There are 2,065,350
reconstructed checks and 225 exact symmetric-CQR/raw-score flag-equivalence
checks. Eleven constructed-stream unit tests pass. Per-unit hashes, source and
protocol identities and the analysis hash are retained in `VALIDATION.json`,
`ARTIFACT_MANIFEST.json` and completion records.

One recovered unit, `f2_s43`, had an event-file checksum mismatch. It was excluded
and regenerated with the unchanged protocol, source and raw inputs. The original
failed file was preserved separately. Its completion receipt was not edited to
accept the mismatched bytes. See `RECOVERY.json`.

The independent summary uses array searches over emitted onsets. It rejects reused
onsets/overlapping windows and verifies the source/protocol against the execution
manifest. This analysis-only improvement does not change fitted models, detector
rules, budgets or scientific outcomes.

## Implication for the paper

The earlier 25.53% workload reduction remains evidence for its original
fixed-nominal-coverage comparison. It does not show an advantage over a tuned
simple detector. This pilot provides a reason to narrow the claim and test why
calibration, threshold geometry, aggregation and adaptation change the operational
tradeoff. It does not by itself establish a novel method or a publishable result.

Next, complete the closest-work audit, lock one precise remaining research
question, and freeze a design for previously uninspected buildings/sites and
additional monitoring targets. Include the simple comparators and component
ablations. If a proposed improvement fails, retain the failure and change the
scientific claim rather than repeatedly tuning on these test periods.

The sample contains only six sites. Seeds and fault catalogues do not create
additional independent sites. Reported intervals condition on these buildings
and models. Missing family/severity cells are not silently imputed: the minimum
observed stratum count is 18 of 21, with counts recorded for inspection.

Background episodes are not verified false alarms. Sensor injections are not
maintenance-confirmed physical equipment failures. Operator time, cost and alarm
fatigue were not measured, and no noninferiority or population guarantee follows.

## Artifact scope

The committed checkpoint includes source, protocol, dependency pins, unit tests,
aggregate tables, per-unit policies/splits/workloads/completion hashes, an artifact
manifest and this interpretation. Large generated models, packed flags, prediction
streams and event records remain in the local audited run directories. They can
be regenerated with the README commands; a summary-only checkout cannot repeat
the stored-flag audit without regenerating those files. Publishing a complete
portable evidence archive remains item C10 of the journal checklist.
