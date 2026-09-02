# Contributions, limitations and future work

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

## Contributions
1. A leakage-audited, group-safe, physical-time conformal alerting pipeline with fail-closed integrity gates and machine-checkable validation.
2. Feasibility-first evaluation: `no_feasible_configuration` as a reported outcome under a frozen operating policy.
3. Paired evidence that conformal calibration reduces background workload at comparable recall (exploratory tier).
4. Closed-loop fault-absorption characterisation with causal residual delay (amendment-003 extension).
## Limitations
- 3 independent periods (PLEIA), 3 evaluated runs (RICO), 10 buildings (BDG2); undercoverage vs nominal; matched-budget endpoint not computed; contamination family uses residual-offset construction; no peak-memory instrumentation; recovery floor-limited.
## Future work
- Confirmatory RICO expansion over the 204 untouched runs; matched-budget operating curves; adaptive conformal methods targeting the observed undercoverage; real fault labels.
