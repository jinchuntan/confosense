# Corrected final dissertation study — status and resume

This directory holds the corrected study's **design, provenance and validator**.
It deliberately holds **no corrected performance numbers**: the nested end-to-end
run has not been executed, and no number is written until its source CSV exists.

## What is done (implemented, wired, tested)

| Item | State | Commit | Test |
|---|---|---|---|
| A1 target-time horizon embargo | FIXED, wired | `64901cd` | `test_windowing_integrity` |
| B1 `target_lag_0` (y_t feature) | FIXED, wired | `64901cd` | `test_windowing_integrity` |
| Executable + validated protocol | done | `4c19ad6` | `test_protocol` (12) |
| C1 causal group-safe updated EnbPI | FIXED, wired | `69037dd` | `test_enbpi_causal` (4) |
| B2 feature-schema persistence | FIXED, wired | `e8f445b` | `test_corrections_bde` |
| B3 BDG2 weather loud-fail | FIXED, wired | `e8f445b` | `test_bdg2_weather` (3) |
| A2 whole-run nested subsplit | implemented, tested | `e8f445b` | `test_corrections_bde` |
| D5 per-group train-only scaling | implemented, tested | `e8f445b` | `test_corrections_bde` |
| D2/D3/D6/D7/D8 alert primitives | implemented, tested | `20fbeb8` | `test_alerts_corrected` (14) |
| Final-study validator | done | `3d3b8a7` | `test_validate_final_study` (2) |

Full test suite: **224 passed, 1 skipped**. `outputs/full_study/` is byte-for-byte
unchanged (baseline inventory in `audit/full_study_baseline_checksums.txt`).

## What remains (the nested end-to-end engine and the run)

Still `PENDING` in `audit/leakage_audit.json`:

- **C3 / E** — build the single evaluated pipeline object (point model → interval
  → operating level → recalibration → alert rule → episode/matching) and evaluate
  exactly the inner-selected object on each outer fold, feeding the selected
  recalibrated stream into alerting.
- **D1** — remove the hard-wired CQR@95% operating choice; select the operating
  level/method on inner data.
- **D4** — wire exposure-proportional event allocation (the frozen catalogues)
  into the run.
- Wire the tested primitives (A2, D2, D3, D5, D6, D7, D8) into that engine.

Then: nested multi-seed run → `runs/full_<id>/`, ≥2000-replicate group-appropriate
CIs, the 10 primary figures, the report suite, and finally
`python -m src.validate_final_study` writing `PUBLICATION_READY.json`.

## Resume

```bash
cd smart_building_conformal
git checkout fix/final-dissertation-study            # HEAD after session 2
C:/cfs_venv/Scripts/python -m pytest -o addopts="" -q # expect 224 passed, 1 skipped
# Design-level gate (passes now; run-dependent checks fail until the full run exists):
C:/cfs_venv/Scripts/python -m src.validate_final_study --output-root outputs/final_dissertation_v2
# Corrected smoke (validates the wired corrections integrate end-to-end):
C:/cfs_venv/Scripts/python -m src.run_study \
    --config configs/study_final_dissertation_v2.yaml --dataset pleia --fast \
    --outputs outputs/final_dissertation_v2/runs/smoke_s1
```

The corrected **full** run is gated behind C3/D1/D4/E above; do not run it (or
generate any report/figure) before those land, or the numbers would come from a
pipeline that does not yet implement the frozen protocol end-to-end.
