# Robustness, contamination and recovery extension v1

This directory is the compact, versioned control record for the original Amendment-003 extension. It does not alter the frozen scientific source, protocols, historical results or failed attempts. Operational replay remains paused and is not an input to this extension.

## Frozen scope and readiness

- `CROSSWALK.csv` maps all 60 historical units to the matched-role row/group identities, role-bank hashes, saved point-owner hashes and exact interval-owner hashes. It preserves 15 cells per unit and 900 cells overall.
- RICO uses the revised whole-run identities. Fold 0/1/2 have respectively 123/41/43, 92/31/41 and 61/21/41 fit/calibration/test groups; their ordered row, group and time hashes are frozen per unit.
- 52 units (780 cells) have exact saved interval owners. Eight units (120 cells) remain explicitly `requires_authorized_owner_construction`; none was substituted with a 0.95 owner.
- `PROTOCOL.json` freezes the original five fault types, seven fault cells, [25%,55%) windows, zero control, calibration-only 5%/10% contamination, three recovery policies, resource gates and one authorized pilot.
- `robustness_saved_owner_v1.py` is the checkpointed saved-owner adapter. `validate_saved_owner_v1.py` is a separate scalar/stream validator. Eight focused zero-fit tests include deliberate corruption rejection.

## Operation accounting

The complete 900-cell execution has 480 distinct corrupted-feature rebuilds, 540 saved-owner inference passes and 900 emitted cell streams. Recovery `level_shift@2` reuses the matching fault feature/prediction stream, and contamination reuses the clean test features and point predictions. It therefore does not double-count those nested computations.

Across the frozen crosswalk, group-specific recovery produces 2,415 rows (805 test groups × three policies). The remaining batch has 472 feature rebuilds, 531 inference passes, 885 cell streams, 177 contamination reconstructions (118 nonzero), 177 recovery-policy computations, 2,385 recovery-group rows and 118 saved point-metric rows, plus 59 checkpoint validations and zero-fit resumes.

Completing the eight unsupported owners requires exactly 24 quantile-estimator fits and eight owner conformalizations. No other model fits are required.

## Authorized pilot result

The selected key was `bdg2_h1_f2_s42`. It is scientifically suitable because the historical obligation uses primary horizon 1, CQR at exactly 0.95, periodic recalibration, ten frozen BDG2 test groups and the exact saved owner `f31aaf373787f894f38c07708f3eb63dedadd21f5e6bdbe313d477a06f3eae48`. Its historical policy was a best-effort, operationally abstaining unit; it is valid for the robustness obligation and pipeline pilot but not an operational-feasibility claim.

The pilot completed 15/15 cells and 519,600 stream rows in 61.82 seconds. It performed eight feature rebuilds, nine saved-owner inference passes, three contamination reconstructions and three recovery computations. Fits, conformalizations and new seeds were all zero. Peak RSS was 0.974 GiB, peak process commit was 2.127 GiB, and committed output was 45.53 MiB. Independent validation took approximately 34.6 seconds and passed every cell. Zero-fit resume took 9.9 seconds and left the checkpoint SHA-256 unchanged.

The zero-control stream is exactly equal to clean. Multi-group scalar `fault_detected` and scalar detection delay are intentionally unavailable; group detection rates remain available. The strongest pilot degradation was `level_shift@2`, with during-window coverage 0.0324 versus pre-window 0.9532. Dropout and stuck during-window coverage were 0.3421 and 0.3573. Random missing was milder at 0.9345.

Calibration-only contamination left all test targets/features unchanged. The 5% and 10% cells increased mean width from 138.73 in the contamination reference to 639.21 and 644.47, with coverage 0.9715 and 0.9697. These are pilot diagnostics, not population estimates.

All ten groups recovered under each policy within the common 92,400-minute follow-up; no group was censored. Restricted mean recovery was 1,854 minutes static, 2,070 periodic and 1,560 rolling; medians were 1,500, 1,500 and 1,440 minutes. No recovery metric was unavailable in this pilot. Population intervals remain unavailable from one unit.

The preserved failed attempt predates checkpoint commit and records the nominal-level duplication correction in `PILOT_FAILED_ATTEMPT_001.json`.

## Revised remaining budget

The crosswalk contains 947,710 test rows. Scaling the observed 45.53 MiB pilot by frozen row counts gives 1.22 GB for all live checkpoints; a 25% cross-dataset allowance raises this to 1.52 GiB. A separate 0.25 GiB allowance covers the eight missing owners and their fit/calibration stages.

From the current state, the conservative additional peak is 7.54 GiB: 1.73 GiB remaining live growth including missing owners, 1.77 GiB each for final archive, verified backup and temporary packaging overlap, and 0.50 GiB for compact Git/delivery growth. No archive compression saving is assumed. After the pilot's verified external copy, 53.93 GiB is free and the projected margin above the existing 8 GiB floor is approximately 38.39 GiB.

Row-scaled pilot measurements imply a 44-minute lower bound for full production plus independent validation. Allowing for dataset/owner heterogeneity, missing-owner construction and checkpoint overhead gives 1–4 hours for science and validation. Including archive, backup, verification and Git delivery, the current planning range is 3–8 hours. This range includes the 24 missing-owner estimator fits, eight conformalizations and final delivery; it excludes the already completed pilot.

## Remaining authorization

Completion of all 900 cells now requires one precise authorization: construct the eight exact higher-level CQR/quantile owners listed in `CROSSWALK_SUMMARY.json` within a budget of 24 quantile-estimator fits and eight conformalizations, then execute the remaining 59 frozen units (885 cells), independently validate them, verify zero-fit resume, aggregate, back up and deliver. Authorization must not permit 0.95 substitution, fault-definition changes, operational-policy reselection or resumption of the operational replay.
