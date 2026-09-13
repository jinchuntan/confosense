> **Historical document ? status changed 13 September 2026.** This retained account predates the integration repairs. Its performance/achievement statements do not establish current findings. See `INTEGRATION_REPAIR_REPORT.md` at the repository root and `audit/integration_repair_status.json`. Historical metrics and publication markers are preserved, not revalidated.

# Claims disposition after the post-run statistical audit

Tiers: **confirmed** (paired/CI-supported on adequate independent units) ·
**descriptive** (correct arithmetic, insufficient independent units for CI) ·
**exploratory** (post-hoc or endpoint differs from the frozen one) ·
**withdrawn/prohibited**.

| # | Claim | Disposition | Basis |
|---|---|---|---|
| 1 | Conformal calibration reduces background alert workload at comparable recall | **exploratory (paired-effect supported)** | Δworkload −2.51 [−4.74, −0.78]/day, Δrecall ≈ 0 over 12 paired units; frozen matched-budget endpoint not computed |
| 2 | Temporal (k-of-m) aggregation reduces workload at a recall cost | **exploratory (paired-effect supported)** | −0.57 [−1.03, −0.14] workload; −0.073 [−0.137, −0.022] recall |
| 3 | Full pipeline beats temporal level | **unsupported** | Δworkload +1.02 [+0.21, +2.11] with Δrecall ≈ 0 — negative finding, reported |
| 4 | BDG2 within-building coverage 0.891 [0.865, 0.915]; recall 0.375 [0.334, 0.417] | **confirmed (corrected CI, 10 buildings)** | `final_cis_corrected.csv`; against own nominals this is systematic undercoverage |
| 5 | PLEIA temp/energy operational performance under the frozen policy | **descriptive** | 2 feasible folds each (energy: single catalogue seed); NA CIs, 3 periods |
| 6 | "PLEIA-energy workload = 10.44/day" | **withdrawn as headline** | pooling artifact of best-effort diagnostic units; feasible-only 0.32 & 0.00/day |
| 7 | RICO coverage 1.000 = successful calibration | **prohibited** | uninformative over-wide intervals on 3 short runs; zero alerts |
| 8 | Any RICO CI | **withdrawn** | 3 independent runs → NA; descriptive only |
| 9 | Frozen operating policy is broadly satisfiable | **unsupported** | feasible on 12/60 units; RICO/BDG2 0/15 — reported as a first-class feasibility finding |
| 10 | Interval sharpness / point accuracy from this run | **prohibited** | widths, Winkler, outer MAE/RMSE not persisted |
| 11 | Distribution-free coverage guarantee held in practice | **withdrawn** | undercoverage in 44/60 units vs own nominal |
| 12 | Real-world fault precision, unseen-building portability, SDG-11 impact | **prohibited (unchanged)** | design limits |

Every retained number's source: `metrics/final_cis_corrected.csv`,
`metrics/PAIRED_ABLATION_EFFECTS.csv`, `metrics/OUTER_UNIT_LEDGER.csv`, with
numerators/denominators in `metrics/ALERT_ACCOUNTING_AUDIT.csv`.
