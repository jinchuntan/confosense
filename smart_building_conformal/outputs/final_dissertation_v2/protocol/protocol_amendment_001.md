# Protocol amendment 001 — make the frozen protocol executable

**When:** before any corrected outer-fold result was produced or inspected. No
corrected metric exists yet, so this amendment cannot have been influenced by a
result. It repairs the *form* of the predeclaration, not its scientific intent.

## Why an amendment was necessary

The first predeclared `frozen_protocol.yaml` (session 1) was **not parseable**.
The `episode:` mapping was written as a member of the `alert_rules_physical:`
block sequence, mixing a YAML sequence and a mapping at the same indentation:

```
alert_rules_physical:
  - {name: "1min-1of1", ...}
  ...
  episode:            # <-- mapping key inside a sequence: invalid YAML
    ...
```

`yaml.safe_load` raises `ParserError` on it. The SHA-256 recorded in session 1,

```
f710c96c1a90ea76ab7dc3fc003769c35eba589ea018b78faeb914b16402f5ac
```

is therefore the hash of **invalid bytes** — not of a usable study protocol. It
is retained here for history and superseded.

## What changed

1. **Valid structure.** `episode` moved out of the rule sequence into a separate
   top-level mapping `alert_episode`. The file now parses with `yaml.safe_load`.
2. **Placeholders removed.** `matching.overlapping_tolerance: explicit` (a
   non-value) is replaced by `matching.overlapping_tolerance_steps: 0` (exact,
   with units — extra steps beyond the detection tolerance allowed for
   overlap; 0 = none).
3. **Strict validation added.** `src/protocol.py` defines a `pydantic` schema
   with `extra='forbid'` at every level, a placeholder scanner, coverage-level
   range/order checks, "must be true" checks on the end-to-end and group-safety
   flags, a "never drop events silently" check, and cross-field consistency
   checks. Unknown, missing, placeholder or inconsistent fields are rejected.
4. **§4 inconsistencies resolved and made executable** (all predeclared, none
   result-driven):
   - **Folds.** Nested design made explicit: `outer_folds: 3`, `inner_folds: 2`,
     per-dataset schemes (`purged_rolling_origin` for PLEIA temp/energy,
     `whole_run_group_blocked` for RICO, `within_building_target_time_aligned`
     for BDG2), minimum block sizes, and a separate leave-building-out label for
     BDG2 portability that is only asserted if a portability claim is made.
   - **Embargo.** Defined mathematically as "no label/residual from an earlier
     block may have `target_time` reaching a later block", `sided: both`.
   - **RICO chronology.** `unit: run`, `nested_subsplit: whole_run` — a run is
     never split across partitions, verified by adapter tests.
   - **Physical rules.** Declared in wall-clock minutes; converted to steps per
     dataset frequency, with infeasible rules marked `not_applicable` (never
     silently coerced).
   - **Event allocation.** Replaced the impossible "balance all types within
     every short run" with `allocation: exposure_proportional`,
     `balance.scope: dataset`, `n_catalogues: 5` frozen catalogues, explicit
     attempted/placed/rejected accounting, `drop_silently: false`, and three
     distinct seed ledgers (`seeds.model`, `seeds.event_catalogue`,
     `seeds.bootstrap`).
   - **Event definitions.** Frozen type list
     `[random_missing, block_missing, stuck, dropout, bias, level_shift, drift]`,
     severities in per-group **train-only** robust-sigma units, physical
     durations, paired clean counterfactual retained.
   - **Statistics.** `bootstrap_replicates: 2000`, moving-block length rule,
     Holm multiple-comparison, percentile CI, macro/micro aggregation formulas,
     `min_events_for_recall_ci: 5`, skill-relative cross-target summary.

## Hashes

| Stage | SHA-256 | Status |
|---|---|---|
| Session-1 raw bytes | `f710c96c1a90ea76ab7dc3fc003769c35eba589ea018b78faeb914b16402f5ac` | superseded (invalid YAML) |
| Amended, canonical (`src.protocol.protocol_hash`) | `1e4506d203c9543a2ccf50dd0c64bf3c2cf09195f9c25f1a232ae5fd2b55d9ea` | active |

The canonical hash is taken over the validated protocol's order-independent JSON
serialisation, so a cosmetic reformat does not change it while any content change
does. It is recorded in `config_hash.txt` and referenced by
`configs/study_final_dissertation_v2.yaml`.
