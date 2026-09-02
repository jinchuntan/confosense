# RQ / RO achievement (post-audit)

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

- **RQ1 point forecasting**: evidence now exported (`point_accuracy_summary.csv`; fig01) — *descriptive* (3 folds); persistence is competitive at short horizons.
- **RQ2 interval validity**: *achieved as a negative-leaning finding* — systematic undercoverage vs own nominal (44/60 units; BDG2 CI 0.891 [0.865, 0.915] at nominals ≥0.95).
- **RQ3 alerting value**: *exploratory-supported* — paired workload reduction at equal recall; feasibility 12/60 is the honest headline.
- **RO leakage-controlled pipeline**: *achieved* (audited; no defect found; every estimate recomputes).
- **RO robustness/fault absorption**: *achieved via amendment-003 extension* — closed-loop absorption quantified; recovery policies compared under causal residual delay.
