# Corrections to reported wording and count labels

## Scope of these corrections

Two of the three items raised concern claims that appeared in the **delivering session's prose summary**, not in the committed report. The committed `PLEIA_TEMPERATURE_CONTEXT005_PILOT_REPORT.md` presents the numbers in tables and makes one narrative claim, which correctly pairs detection with its workload. The corrections are recorded here in full regardless, and the report is given the missing explicit interpretation.

## Correction 1: rolling CQR does not reach nominal coverage

Claimed in the session summary: rolling CQR "recovers to 90.8%" and "only reaches nominal by widening". **Wrong.** Nominal is 0.95.

| control | clean-stream coverage | reaches nominal 0.95 | shortfall |
| --- | --- | --- | --- |
| `persistence_static` | 0.9652 | yes | -0.0152 |
| `cqr_rolling` | 0.9081 | **no** | +0.0419 |
| `cqr_static` | 0.3246 | **no** | +0.6254 |
| `quantile_static` | 0.2240 | **no** | +0.7260 |

Only `persistence_static` attains nominal coverage. `cqr_rolling` at 0.9081 remains **0.0419 below nominal**, and it does so at the widest interval of all four controls (8.934 degC MPIW). It narrows the shortfall relative to the static conformal controls; it does not close it.

## Correction 2: "dominates on every axis" is too broad

Claimed in the session summary: persistence "dominates on every axis". **Too broad.**

At the immediate rule in the combined channel:

| control | detection | background episodes/asset-day | fraction time in alert |
| --- | --- | --- | --- |
| `persistence_static` | 0.9086 | 4.2443 | 0.0348 |
| `cqr_rolling` | 0.6967 | 3.0815 | 0.0919 |
| `cqr_static` | 0.4409 | 2.6599 | 0.6754 |
| `quantile_static` | 0.4274 | 4.0989 | 0.7760 |

`persistence_static` raises **more** clean-stream episodes per asset-day than `cqr_rolling` (4.2443 versus 3.0815), so it does not dominate on that axis. Nor does it lead at every rule:

| rule | best control (combined) | detection |
| --- | --- | --- |
| `180min_3of18` | `persistence_static` | 0.5127 |
| `30min_3of3` | `cqr_rolling` | 0.4174 |
| `360min_4of36` | `persistence_static` | 0.3702 |
| `60min_4of6` | `cqr_rolling` | 0.3040 |
| `single_sample` | `persistence_static` | 0.9086 |

Supportable statement: persistence leads on interval coverage, width, Winkler score, and on detection and restricted delay at the immediate, 180-minute and 360-minute rules, while `cqr_rolling` leads at the 30- and 60-minute rules and raises fewer clean-stream episodes at the immediate rule.

## Correction 3: count labels reconciled

| identity | arithmetic | holds |
| --- | --- | --- |
| context stages = clean identity replays + scheduled fault slots | 2924 = 68 + 2856 | True |
| context stages = 68 contexts x 43 ordinals (0..42) | 2924 = 68 x 43 | True |
| context stages = alias variants + unique canonical realizations (a different partition) | 2924 = 773 + 2151 | True |
| unique canonical realizations = distinct realization hashes | 2151 = 2151 | True |
| fault slots = effective fault slots + null fault slots | 2856 = 2727 + 129 | True |
| null realizations = clean stages (null by definition) + null fault slots | 197 = 68 + 129 | True |
| effective fault slots = scheduled fault slots - null fault slots | 2727 = 2856 - 129 | True |
| clean stages are never effective | 0 = 0 | True |

Clean stages are distinct from fault slots: 68 contexts x (1 clean identity replay + 42 scheduled fault slots) = 2,924 context stages. The alias/unique split is a **different** partition of those same 2,924 stages. `null` and `effective` are exact complements on the 2,856 fault slots, and the 68 clean stages are null by definition.

## Preserved

Negative findings stand unchanged: severe undercoverage of the learned quantile controls on temperature, and the high alerting workload that follows from it. No uncertainty bound is invented for this single seed; population intervals remain unavailable. Measurement gaps are retained, including the unknown exit status of the interrupted original attempt, and stage CPU totals remain distinct from end-to-end cost.
