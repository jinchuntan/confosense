# Protocol amendment 003 — robustness / contamination / recovery extension

**When:** after the Phase-1 statistical audit of core run `full_20260831_220811`
(verdict: PASS WITH REPORTING CORRECTIONS) and **before any robustness,
contamination or recovery result was produced or viewed**. The core run is
immutable; the extension writes to a new timestamped run directory.

## What is predeclared (see `robustness_extension:` in `frozen_protocol.yaml`)

- **Closed-loop faults** on the observed test stream, corrupting the sensor (not
  reality): `random_missing` (20% of in-window steps, gap-filled last value),
  `dropout` (hold last pre-window value), `stuck` (freeze at window start),
  `level_shift`, `drift`; severities {1.0, 2.0} per-group **train-only**
  robust-sigma; a mandatory **zero-severity control** that must reproduce the
  clean cell exactly. Corrupted readings feed the lagged/rolling inputs of every
  subsequent prediction (features rebuilt from the corrupted series), so faults
  cascade causally.
- **Fault window** = the contiguous [25%, 55%) slice of each group's test span;
  segments pre/during/post fixed at [0, 25) / [25, 55) / [55, 100]%.
- **Calibration contamination** only: {5%, 10%} of calibration targets biased
  by +2σ before conformalization; the evaluated test stream stays clean.
- **Recovery**: `level_shift` @ 2σ under recalibration policies
  {static, periodic, rolling}, delayed corrupted residuals only; recovery =
  rolling coverage back within 0.05 of the pre-fault segment coverage, censored
  if never.
- **Endpoints**: primary = Δcoverage(during−pre), Δbackground/day(post−pre),
  fault detected, time-to-recovery; secondary = width, Winkler, post-fault
  cascade, point MAE vs persistence (closing the Phase-1 evidence gaps: widths
  and point accuracy are now persisted). Coverage is always against **clean
  ground truth**; background exposure **excludes** the fault window.
- **Units and inference**: the same 60 core units, each evaluated with its own
  frozen pipeline from the core run's provenance (deterministic refit — same
  code, seeds and fold construction; models were not serialized). Abstaining
  units keep `operational_feasible=false` and are never pooled into headline
  rows. Seeds aggregate before inference; paired bootstrap 2000 replicates on
  the correct independent units; Holm within each dataset's primary family.

## Hashes

| Stage | SHA-256 | Status |
|---|---|---|
| Amendment 002 | `07bf304aceeafc7411b570f21c26a48a8d33515cdd3badad35c4f1a61a932c7b` | superseded |
| Amendment 003 | `10437ab054199d64c74edb5e62a4011f707fedb96b7d6440d6047f42ea500a8d` | active |

The strict schema (`src/protocol.py::RobustnessExtension`) validates the block
(window ordering, mandatory zero-severity control, ≥2000 replicates,
clean-ground-truth reference).
