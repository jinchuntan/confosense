# Chapter 5 — Discussion (dissertation draft)

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

Key discussion threads, each tied to its evidence tier:
1. **Conformal calibration cuts operator workload at equal recall** (exploratory, paired CI excludes 0) — the practical value proposition.
2. **Empirical coverage misses nominal under temporal drift** (confirmed for BDG2; descriptive elsewhere) — exchangeability limits in buildings; motivates adaptive/recalibrated intervals.
3. **Closed-loop fault absorption** (extension) — `y_t`-conditioned predictions track a faulty sensor, hiding sustained faults from interval alerts; onset/offset detection remains. Implication: pair closed-loop monitoring with reference/redundant signals.
4. **Feasibility is the honest headline**: the frozen recall/workload policy is satisfiable on 2/12 dataset-folds robustly; reporting no_feasible_configuration is a contribution, not a failure.
5. **Small independent-evidence bases** (3 folds; 3 RICO runs) bound what can be claimed; 204 untouched RICO runs are the clean path to confirmatory evidence.
