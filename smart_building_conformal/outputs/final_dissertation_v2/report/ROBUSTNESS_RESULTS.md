# Robustness, contamination and recovery results (amendment 003)

> The original test outputs were inspected and used to diagnose the pipeline, so they are no longer a pristine holdout. Corrected performance is estimated through fully nested post-audit evaluation and is **not** presented as validation on an untouched holdout.

**Tiers:** *confirmed* = paired/CI-supported on adequate independent units · *descriptive* = correct arithmetic, too few independent units for a CI · *exploratory* = post-hoc or endpoint differs from the frozen one · *unsupported/prohibited* = must not be claimed.

Sources: `metrics/robustness_effects.csv`, per-dataset `robustness_cells.csv` in the extension run; paired within unit; clean-ground-truth coverage; Holm within the primary family.
_Extension effects not yet computed — no number is reported._

## Interpretation guardrails
- Closed-loop faults are partially **absorbed**: with `y_t` as a feature, predictions track the corrupted sensor, so coverage against clean truth collapses during sustained faults while the alert stream reacts mainly at fault onset/offset. This is a finding about closed-loop monitoring, not a defect.
- Contamination cells use the residual-offset construction uniformly in-family (documented deviation).
- Recovery times are floor-limited by the rolling-window length and right-censored at test end.
