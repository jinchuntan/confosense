# Nested-engine 4-dataset smoke — readiness evidence (not results)

A `--fast` run of the nested end-to-end engine (`src/corrected_study.py`) across
all four datasets, into the git-ignored `runs/engine_smoke/`.

```
python -m src.corrected_study --fast --out outputs/final_dissertation_v2/runs/engine_smoke
```

| Field | Value |
|---|---|
| Exit code | **0** |
| Datasets | pleia, pleia_energy, rico, bdg2 (all 2 outer folds) |
| Ablation levels per dataset | baseline, conformal_only, temporal, full |
| Protocol hash | `07bf304a…` |
| Fail-closed gates | passed (no FailClosed raised: selected-hash == evaluated-hash; alert-consumed bounds == selected recalibrated bounds) |
| Interval candidates exercised | CQR, static + updated recentred EnbPI, uncalibrated quantile; DSCP recorded not-applicable at single-horizon alerting |
| Selection outcomes | 7 folds `no_feasible_configuration` (honest abstention under the strict fast policy), 1 `selected`; best-effort diagnostics drove the ablation on abstaining folds |
| Event allocation | exposure-proportional, group-safe; RICO short-run viability floor applied and realised-vs-requested incidence recorded |
| `outputs/full_study/` after run | unchanged |

`python -m src.validate_final_study --mode readiness` → **all 6 checks PASS**
(protocol parses, hash recorded, full_study unchanged, no audit item pending,
engine smoke covers all four datasets and four ablations).

**Not results:** `--fast` numbers are never quoted. This establishes only that
the corrected nested pipeline runs end-to-end on every dataset with the
integrity gates holding. The full (non-fast) multi-seed run, its ≥2000-replicate
CIs, figures and reports remain to be produced.
