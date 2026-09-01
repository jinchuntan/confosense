# Feasibility audit — run `full_20260831_220811`

Source: `metrics/OUTER_UNIT_LEDGER.csv` (all 60 units), `metrics/final_cis_corrected.csv`.

## Counts

- **60 evaluation units** = 12 dataset×fold units × 5 model seeds (seeds are
  replicates, not independent folds).
- Executed 60/60; failed 0; insufficient-observations 0; undefined-metric 0.
- **Feasible 12/60 (20%)** under the frozen policy
  (inner macro recall ≥ 0.60 ∧ inner background ≤ 1.0/asset-day):

| dataset | feasible / units | pattern |
|---|---|---|
| pleia | 10 / 15 | folds 0 and 2 feasible for all 5 seeds; fold 1 (Aug–Oct) infeasible for all |
| pleia_energy | 2 / 15 | only seed 46's event catalogues yield a feasible surface (folds 0, 1) |
| rico | 0 / 15 | intervals wide → near-zero inner recall at acceptable workload |
| bdg2 | 0 / 15 | undercoverage → workload above 1.0/day at the recall floor |

All 48 abstentions carry reason
`no_candidate_met_recall0.60_and_workload1.0_on_inner_selection_block` — the
predeclared `no_feasible_configuration` outcome, which the protocol treats as a
first-class scientific result. None was silently dropped or zero-filled.

## What abstention means here (three-tier reporting)

1. **Applicability/feasibility (all 60 units):** ConfoSense's frozen operating
   policy is satisfiable on 2 of 12 dataset-folds robustly (pleia 0/2) and on 2
   more only under particular event catalogues (pleia_energy, seed 46). On RICO
   and BDG2 the policy is unsatisfiable with the evaluated candidate grid.
2. **Performance conditional on feasibility (12 units):** pleia coverage 0.794,
   recall 0.671, workload 1.24/day (descriptive, 2 folds); pleia_energy coverage
   0.912, recall 0.456, workload **0.16/day** (descriptive, 2 folds, one seed).
3. **All-units diagnostic:** the previously published headline (best-effort
   configurations pooled with feasible ones) — retained only as a diagnostic
   table, never as operational performance.

## Sensitivity of feasibility to the event-catalogue seed

pleia_energy's feasibility flips with the catalogue seed (46 feasible, 42–45
not). With ~34 events per fold the inner recall estimate has wide sampling
error around the 0.60 floor; feasibility decisions near the threshold are
noisy. This is disclosed as a limitation; the thresholds themselves are frozen
and were not relaxed.
