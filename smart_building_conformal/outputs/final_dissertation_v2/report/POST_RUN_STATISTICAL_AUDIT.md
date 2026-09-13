> **Historical document ? status changed 13 September 2026.** This retained account predates the integration repairs. Its performance/achievement statements do not establish current findings. See `INTEGRATION_REPAIR_REPORT.md` at the repository root and `audit/integration_repair_status.json`. Historical metrics and publication markers are preserved, not revalidated.

# Post-run statistical audit — run `full_20260831_220811` (immutable)

Audit performed against the preserved raw artifacts only; **no model was rerun**.
Every table referenced here lives under `metrics/` and every number in this
document was produced by the audit scripts, not typed by hand.

## Verdict

**STATISTICAL AUDIT PASS WITH REPORTING CORRECTIONS**

No leakage, arithmetic, or implementation defect was found in what the run
computed: every reported estimate recomputes exactly from the per-event and
per-group artifacts (`ALERT_ACCOUNTING_AUDIT.csv`), and `final_cis.csv`
regenerates bit-identically from the preserved raw artifacts in an independent
temporary directory (12/12 rows exact). The corrections below are to *reporting
and inference*, not to the evaluated pipeline. No core rerun is required; the
run remains valid as a diagnostic + feasibility study with corrected labels.

## A. Inventory reconciliation (`FULL_RUN_INVENTORY.csv`, `FOLD_MEMBERSHIP.csv`)

| dataset | expected obs | loaded obs | groups | match |
|---|---|---|---|---|
| PLEIA temperature | ~50,543 | **50,543** | 1 series | exact |
| PLEIA energy | ~50,545 | **50,545** | 1 series | exact |
| RICO | ~49,680 / 207 runs | **49,680 / 207 runs** | 207 | exact |
| BDG2 subset | ~175,440 / 10 buildings | **175,440 / 10 buildings** | 10 | exact |

No fast-mode, row or group cap was active (`fast: false` in the run summary).

**The RICO "3 runs" is now precisely resolved:** the fold constructor assigns
exactly **one whole run per outer fold as test** — runs `P5S59` (fold 0),
`P5S58` (fold 1), `P5S57` (fold 2) — 221 windows ≈ 3.7 h ≈ 0.15 asset-days
each. It is a fold-design property, not an accidental cap: 207 runs were loaded,
train/calibration pools used the remainder, and **204 runs were never used as
outer test** (genuinely untouched data, available for a legitimate future
expansion under a predeclared amendment).

## B. Unit accounting (`OUTER_UNIT_LEDGER.csv`)

There are **12 dataset×fold units × 5 model seeds = 60 evaluation units**, not
60 independent folds. All 60 executed; none failed. Feasibility under the frozen
policy (macro recall ≥ 0.60 ∧ background ≤ 1.0/asset-day on the inner selection
block): **12/60 feasible** — pleia 10 (folds 0 and 2, all seeds), pleia_energy 2
(seed 46 only — feasibility there is event-catalogue-seed dependent), rico 0,
bdg2 0. All 48 abstentions carry the single reason code
`no_candidate_met_recall0.60_and_workload1.0_on_inner_selection_block`; none is
an execution failure, insufficient-observation case or undefined metric.

**Material correction:** the published headline pooled all 60 units — the 48
abstaining units were evaluated with a clearly-flagged *best-effort diagnostic*
configuration and those rows entered `final_cis.csv` alongside the 12 feasible
ones. Abstentions were never converted to zero-workload rows, but the pooling
means the headline numbers describe *best-effort diagnostic performance across
all units*, *not* operational performance of feasible configurations. Corrected
reporting (`final_cis_corrected.csv`) separates: (1) feasibility rates, (2)
feasible-only performance, (3) all-units diagnostic performance.

## C. Metric recomputation (`ALERT_ACCOUNTING_AUDIT.csv`)

Macro recall, exposure-weighted coverage and background workload all recompute
exactly for all four datasets. Matching is one-to-one and onset-aware and alerts
are episodes, not samples (unit-tested primitives). Two accounting notes:

- **Background exposure denominator includes event/tolerance windows** (code
  divides by total monitored steps). Bias is small (~1–3% of exposure at 0.5
  events/asset-day with ~1 h events) and conservative for the workload claim,
  but the extension will exclude event windows.
- **PLEIA-energy "10.44 alerts/asset-day" is a pooling artifact, not an
  accounting error.** The 13 best-effort units used single-violation rules on a
  stream whose intervals undercover (0.49–0.89 vs 0.95+ nominal), yielding
  13–20 episodes/day. The **2 feasible units show 0.32 and 0.00/day**. The
  arithmetic is correct; the headline label was wrong.

## D. Interval audit (`NOMINAL_COVERAGE_AUDIT.csv`)

Each unit is judged against **its own selected nominal level** (no 90/95
averaging). Undercoverage rates: bdg2 15/15 units, pleia_energy 15/15, pleia
14/15, rico 0/15 (overcoverage). Mean signed deviation: pleia −0.129,
pleia_energy −0.174, bdg2 −0.059, rico +0.023. **RICO's coverage 1.000 with
zero background episodes is NOT successful calibration**: at 0.95/0.995 nominal
on 221-step runs the intervals never violate — they are uninformative for
alerting; only injected faults (2–3 `bias` events per run; higher-severity
strata absent because the 4 h runs cannot host the full balanced catalogue)
produce any alert. Interval widths/Winkler scores were **not persisted** by the
core run (bounds not saved) — a gap the extension closes; no width claim is
permitted from this run.

## E. Confidence-interval audit (`CI_AUDIT.csv`, corrected `final_cis_corrected.csv`)

The published CIs had two inference flaws: (1) the five **model seeds were
pooled as extra rows** of the resampled frame — seeds are algorithmic
replicates, not independent data; (2) for the single-series datasets the moving
blocks were taken over pooled (fold×seed) rows rather than over independent
time periods. Corrected procedure: aggregate over seeds within each independent
unit first, then resample the correct unit (RICO: run; BDG2: building;
PLEIA temp/energy: chronological outer fold). Result: **only BDG2 supports a
legitimate CI** (10 buildings) — recall 0.375 [0.334, 0.417], coverage 0.891
[0.865, 0.915]. PLEIA temp/energy (3 folds) and RICO (**3 independent evaluated
runs**) are reported as descriptive with `NA — insufficient independent groups`;
the previously published degenerate RICO CIs are withdrawn. No overlapping test
timestamps are double-counted (folds are disjoint; the seed dimension is the
only replication and is now aggregated first).

## F. Paired ablation (`PAIRED_ABLATION_EFFECTS.csv`)

All 60 units have complete common support (4/4 levels; identical fold, exposure
and event catalogue within unit — catalogue seeded by the unit's model seed,
shared across levels). Paired within-unit effects, seed-aggregated to 12
dataset-fold units (pooled CI is cluster-naive across heterogeneous datasets —
labelled **EXPLORATORY**, because Amendment 002's frozen endpoint *recall at
matched background budget* was not computable from the single-rule-per-level
core design):

| contrast | Δ recall [95% CI] | Δ workload/day [95% CI] |
|---|---|---|
| conformal_only − baseline | +0.004 [−0.056, +0.070] | **−2.51 [−4.74, −0.78]** |
| temporal − conformal_only | −0.073 [−0.137, −0.022] | −0.57 [−1.03, −0.14] |
| full − baseline | −0.064 [−0.169, +0.038] | **−2.06 [−3.74, −0.82]** |
| full − temporal | +0.005 [−0.027, +0.034] | **+1.02 [+0.21, +2.11]** |

The claim "conformal calibration reduces background workload at comparable
recall" **is supported by the paired effect and CI** (workload CI excludes 0,
recall CI includes 0) and is retained at *exploratory/paired* strength.
Honest negative finding: the *full* level (best-effort selected methods +
recalibration) **increased** workload over the temporal level with no recall
gain.

## G. Point forecasting and efficiency (`POINT_EFFICIENCY_EVIDENCE_AUDIT.csv`)

The engine used inner-selection MAE to choose the point model (persistence
chosen in 10/12 feasible units; xgboost in 2) but **did not persist per-unit
outer MAE/RMSE, per-stage runtimes or peak memory**. RQ1 point-accuracy and
efficiency evidence therefore cannot be claimed from this run; the extension
exports outer point MAE/RMSE vs persistence and stage wall-times.

## H. Provenance (`provenance/artifact_manifest.json`)

Evaluated code = **`9942156`** (run launched 22:08, one minute after that
commit); `git diff 9942156..93231df` over every evaluated source/config file is
**empty** — all post-launch commits (`2850d2e`, `e54dd3f`, `d1a73df`,
`ca78248`, `93231df`) touched analysis, reports, tests and markers only. The
marker's `code_sha ca78248` is the *analysis* commit; the manifest now records
both. `final_cis.csv` regenerated independently: 12/12 rows exact.
