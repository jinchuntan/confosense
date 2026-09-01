# Scientific validity audit — run `full_20260831_220811`

## What is scientifically sound

- **No leakage found.** Nested selection used inner data only; the horizon
  embargo, group-safe alerting/EnbPI state, delayed residuals, one-to-one
  onset-aware matching and exposure-based events are unit-tested and were the
  code that ran (evaluated SHA `9942156`; post-launch diffs touch analysis only).
- **All numbers recompute** from the preserved per-event/per-group artifacts;
  `final_cis.csv` regenerates bit-identically.
- **Abstention was honest**: 48/60 units returned `no_feasible_configuration`
  with a recorded reason and were never converted to favourable zeros.
- **Ablation is genuinely paired**: identical folds, exposures and event
  catalogues across all four levels in all 60 units.

## Validity limits (binding on every downstream claim)

1. **Independent-evidence base is small.** PLEIA temp/energy: 3 chronological
   folds each. RICO: **3 evaluated runs** (out of 207 loaded; 204 untouched).
   BDG2: 10 buildings — the only dataset supporting a defensible CI.
2. **Headline pooling**: published `final_cis.csv` mixed feasible and
   best-effort-diagnostic units and pooled seeds as independent rows. Corrected
   inference is in `final_cis_corrected.csv`; the old table is retained as a
   diagnostic artifact only.
3. **RICO evidence is descriptive at best**: 2–3 `bias`-type events per 3.7 h
   test run, no other strata placeable, overcovering (uninformative) intervals;
   its previously published degenerate CIs are withdrawn.
4. **Interval widths/Winkler and outer point MAE/RMSE were not persisted**, so
   no sharpness or point-accuracy claim may cite this run.
5. **Amendment-002's matched-budget endpoint was not computed** (each ablation
   level ran a single rule); paired comparisons are exploratory.
6. **Background exposure includes event windows** (small conservative bias,
   ~1–3%).
7. **Undercoverage is the norm** on pleia/pleia_energy/bdg2 against each unit's
   own selected nominal level — a substantive finding about conformal validity
   under distribution shift in these buildings, and it must be presented as
   such, not smoothed over.

## Options that involve genuinely untouched data (for any confirmatory follow-up)

- RICO: 204 runs never used as outer test.
- BDG2: further buildings from the source corpus beyond the 10-building subset.
- PLEIA: no untouched temporal period remains within the released span (all
  three folds consumed the 2021 range); confirmatory claims for PLEIA would
  require external data.
