# Protocol amendment 002 — predeclared end-to-end ablation benchmark

**When:** before any corrected outer-fold result was produced or inspected. The
nested engine had been implemented and exercised only on synthetic unit fixtures
and a `--fast` integration smoke whose numbers are explicitly not results. No
corrected outer metric existed, so this amendment cannot have been influenced by
one.

## Why

The corrected study must attribute its operational behaviour to specific design
choices. A four-level ablation, fixed **before** outer results are seen, is the
instrument. Predeclaring it (and the single reporting comparison) prevents
choosing the flattering contrast after the fact.

## What changed

Added an `ablation:` block to `frozen_protocol.yaml` and a strict `Ablation`
schema to `src/protocol.py` (validated: exactly four named levels; the
`fixed_before_outer_results` flag must be true). The four levels, evaluated under
the **same** outer folds and injected-event catalogues:

1. **baseline** — uncalibrated intervals + single-violation alerts + no recalibration
2. **conformal_only** — CQR intervals + single-violation alerts
3. **temporal** — CQR intervals + physical-time k-of-m aggregation
4. **full** — inner-selected interval method + k-of-m aggregation + selected recalibration

The **operational comparison** is fixed as *synthetic-event recall at a matched
background-alert budget*, with *background alerts per asset-day at matched recall*
as the declared alternative. Selection and tuning remain inner-data only.

The engine (`src/corrected_study.py`, commit `ef97905`) already implements these
four levels (`evaluate_ablation`) on the same outer folds and event catalogues,
so the amendment records a design the code already obeys.

## Hashes

| Stage | SHA-256 | Status |
|---|---|---|
| Session-1 raw bytes | `f710c96c1a90ea76ab7dc3fc003769c35eba589ea018b78faeb914b16402f5ac` | superseded (invalid YAML) |
| Amendment 001 (executable) | `1e4506d203c9543a2ccf50dd0c64bf3c2cf09195f9c25f1a232ae5fd2b55d9ea` | superseded |
| Amendment 002 (ablation added) | `07bf304aceeafc7411b570f21c26a48a8d33515cdd3badad35c4f1a61a932c7b` | active |

Recorded in `config_hash.txt` and referenced by
`configs/study_final_dissertation_v2.yaml`.
