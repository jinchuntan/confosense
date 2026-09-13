"""Build review prose from completed, hash-checked amendment evidence."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
P='smart_building_conformal/outputs/amendment004'
OUT=ROOT/P


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


def main():
    proof=read(f'{P}/smoke_20260913_v2/output_validation.json')
    resume=read(f'{P}/smoke_20260913_v2/resume_validation.json')
    payload=read(f'{P}/smoke_20260913_v2/units/outer0_model42/payload.json')
    source=read(f'{P}/validation/evaluated_source_v3.json')
    preservation=read(f'{P}/validation/preservation.json')
    tests=ET.parse(OUT/'validation/regression_v3.xml').getroot().find('testsuite')
    assert proof['output_valid'] and resume['new_fit_invocations']==0
    assert source['source_hash']==proof['source_hash']==payload['source_hash']
    assert tests.get('failures')=='0' and tests.get('errors')=='0'
    count=int(tests.get('tests'))-int(tests.get('skipped'))
    commands={n:read(f'{P}/validation/{n}.log.json') for n in ['preflight_v1','preflight_validation_v1','regression_v3','smoke_v2','smoke_resume_v2','preservation']}
    assert all(x['exit_status']==0 for x in commands.values())
    resources=payload['compute_resources'];unit=f'{P}/smoke_20260913_v2/units/outer0_model42'
    report=f'''# Amendment 004 implementation report

13 September 2026. The bounded implementation and synthetic smoke are complete on `review/amendment004-20260913`, a descendant of the user's published implementation `3354393290d2afaef4361a9a7a1a43336a14c21d`. Main and the original review branch are unchanged. The [evidence index](review/CURRENT_EVIDENCE.md) links code, configuration, support, execution logs and recomputable smoke arrays. **Full-study/dissertation readiness remains false.** No full experiment, real-data operational fit or repeated LSTM investigation was run.

## 1. Software and verification

The [new operational engine](smart_building_conformal/src/operational004_engine.py) implements two purged inner folds with final calibration reserved, estimator-owned intervals, crossed model/catalogue namespaces, shared seven-family exposure catalogues, physical rules, actual target-time episodes, deterministic one-to-one matching, clean-counterfactual workload, both-fold confidence screening, exact ties and explicit abstention. It records controlled shared-fit comparisons separately from independent operating points, the inverse recall-floor comparison and fixed persistence/CQR diagnostics. It exports ordinary precision/recall and labels the constructed stratum F1 as a **custom synthetic selection utility**.

The [causal replay](smart_building_conformal/src/operational004_stream.py) preserves static CQR's existing bounds, uses stored raw-quantile CQR scores for periodic/rolling updates, releases only matured available outcomes, feeds corruptions into later features and resets at groups/gaps. Native updated EnbPI has one every-origin policy on its static fitted base. Availability-only, numerical-only and combined channels remain visible. [Paired inference](smart_building_conformal/src/operational004_inference.py) aggregates seed contributions within original groups/time before resampling and retains unavailable few-run CIs and Holm multiplicity. Recovery retains physical follow-up and censoring; no real-data recovery or contrast CI is claimed here.

The review correction is precise: `corrected_study.select_on_inner`, `evaluate_outer` and `evaluate_ablation` already preserve static method bounds. Regressions protect those paths. The repaired gaps concern generic signed-residual *online* CQR recalibration and clean-only forecast/recalibration followed by injected alert comparisons. Historical operational results still require newly versioned reruns; the completed fixed split-conformal forecast pilot is unaffected.

The [frozen amendment](smart_building_conformal/protocols/amendment004/AMENDMENT004.md) records clarifications, including unhostable allocation/rejection, scheduled-envelope onset, centred stuck semantics, guard endpoints, mask aliases, unsupported short bootstrap segments, temporal control choice and inverse-selector ties. A demonstrated CSV issue also required explicit string columns in the new checkpoint reader: PLEIA's literal asset ID `None` otherwise becomes missing on reload. Historical checkpoint-reader defaults are unchanged.

- Final [regression log]({P}/validation/regression_v3.log): **{count} passed, {tests.get('skipped')} skipped, three existing MAPIE warnings; exit 0**. The skip is retained, not converted into a pass. The new runner-level test includes real checkpoint serialization, output validation and resume; the actual CQR interface has its own separate test.
- Final-calibration/test sentinels, unequal fold weights, supported/degenerate/insufficient bounds, exact ties, no hidden point fallback, no-fit abstention, target-time causality, groups/gaps, seven-family zero identity, method scores, single native adaptation, shared fits, string IDs, persisted bounds and checkpoint corruption all pass.
- [Preservation]({P}/validation/preservation.json): **{preservation['original_pilot_protocol_config_files_unchanged']} original pilot/config/protocol files** and **{preservation['historical_snapshot_files_byte_identical']} historical data/output files** remain byte-identical. Nineteen previously annotated historical reports remain unchanged from entry commit 3354393. Prior backup bundles are preserved. The pilot's **9/9 point and 18/18 interval cells, completion exit 0**, remain the same evidence; this task did not refit them or reinterpret below-nominal coverage as success.

## 2. Actual-data support, measured without fitting

The no-fit run `preflight_20260913_v1` preceded new fitting. Its [independent validator]({P}/preflight_validation_20260913_v1/validation.json) checked **156 role memberships, 72 boundaries, 180 catalogues, 756 stratum cells and 177,984 calibration-rank cells**. Zero models were fitted and no forecast/alert performance was measured.

| Task | Inner banks structurally supported | Effective events per inner five-catalogue bank | Supported strata out of 21 | Outer support |
|---|---:|---:|---:|---|
| PLEIA temperature | 0/6 | 64–124 | 9–20 | 1/3 banks only |
| PLEIA energy | 0/6 | 64–125 | 9–20 | 0/3 |
| RICO | 0/6 | 14–15 | 0 meeting five-onset requirement | 0 events in each outer bank |
| BDG2 | 6/6 | 1,268–2,548 | 21/21 | 3/3 banks |

See [per-fold event support]({P}/preflight_20260913_v1/event_support.csv), [family/severity counts]({P}/preflight_20260913_v1/stratum_support.csv), [exposure/memberships]({P}/preflight_20260913_v1/memberships_summary.csv), [catalogue accounting]({P}/preflight_20260913_v1/catalogue_summary.csv), [rank support]({P}/preflight_20260913_v1/calibration_rank_support.csv) and [physical applicability]({P}/preflight_20260913_v1/physical_rule_applicability.csv). The supplemental [group exposure]({P}/preflight_validation_20260913_v1/group_exposure.csv), [boundary-excluded origin slots]({P}/preflight_validation_20260913_v1/boundary_excluded_slots.csv) and [relative mask aliases]({P}/preflight_validation_20260913_v1/coarse_mask_aliases.csv) preserve denominators and discretization limits.

BDG2 has ten original buildings. PLEIA has 60–86 original nonoverlapping blocks, but lacks required event-stratum support. RICO has 38–39 inner runs yet too few events; its single-run outer blocks round to zero events at the declared incidence. Counts do **not** establish identifiable bootstrap bounds or a feasible operating point. No incidence, threshold, test duration or support requirement was changed to make a task pass. A future four-task scientific comparison needs an explicit scope/design decision for these unsupported tasks; this task does not make that decision from performance.

The no-fit command took {commands['preflight_v1']['seconds']:.2f} s; the measured preparation/audit region took 84.41 s, with peak sampled RSS **1,215,311,872 bytes**. [Per-task resources]({P}/preflight_20260913_v1/resources.csv) remain separate from the original pilot's timings.

## 3. Completed synthetic smoke and its limits

Canonical run: **`smoke_20260913_v2`, command exit 0**. It uses two 3,600-sample ten-minute groups, two inner folds, model seed 42 crossed with catalogue seeds 42–46, .95 CQR/shared uncalibrated bounds, static/first declared rolling and immediate/first applicable temporal rules.

- [Output validation]({P}/smoke_20260913_v2/output_validation.json): **12/12 expected inner cells**, **60/60 inner catalogue/hash pairs**, **20/20 outer diagnostic pairs**, and **96 persisted streams** rehashed after CSV reload. [Expected]({P}/smoke_20260913_v2/expected_inner_keys.csv) and [observed]({P}/smoke_20260913_v2/actual_inner_keys.csv) keys agree exactly.
- The incidence-generated bank correctly returns **`no_feasible_configuration`**, with no operational pipeline. Final diagnostics and shared-fit controls are explicitly separate. Deterministic **SMOKE ONLY** sufficient-support fixtures with 20/30 original groups exercise the real 2,000-resample CI/selector interface and select `fixture_a` under exact ties. Separate unavailable/all-infeasible cases abstain. These engineered count fixtures are not empirical events generated at the scientific incidence.
- Main replay uses three deterministic fixture fit objects; the zero control uses one. There is **one actual tiny CQR fit object, containing three unchanged quantile estimators**, on 400/400/300 train/calibration/evaluation rows. Static bounds equal the native method; corruptions change only later feature/interval states; unavailable readings never enter numerical scores. The fixed persistence reference has zero learned fits. These accounting units must not be conflated.
- [Resume]({P}/smoke_20260913_v2/resume_validation.json) reuses **one completed unit with zero new fit invocations**. Intentional corruption of a temporary checkpoint copy is rejected. The full-study validator rejects this smoke. Seven family-specific zero controls and five zero-catalogue replays are identity checks, not performance observations.
- Compute-region time: **{resources['seconds']:.2f} s**; command wall time: **{commands['smoke_v2']['seconds']:.2f} s**; sampled peak RSS **{resources['peak_rss_bytes']:,} bytes**. [Resources]({P}/smoke_20260913_v2/resources.csv) and [command log]({P}/validation/smoke_v2.log) give the exact scope and hardware. These timings are not measured BDG2 fitting costs.

The first smoke command (`smoke_20260913_v1`) exited **1** after computing and saving its unit, while assembling the final JSON report. Duplicate `scope` and `scientific_readiness` keywords caused the reporting failure; the added runner regression exposed the second duplicate. The failed run, intermediate failed regression, logs and source archives are retained. The corrected smoke uses a new directory; no completed unit was overwritten or threshold retuned. MAPIE's informational messages about quantile crossing also remain in the logs; the static method's existing crossing repair is protected by exact equality checks.

## 4. Execution identity and review artifacts

| Identity | Value |
|---|---|
| Evaluated implementation commit | `{source['evaluated_commit']}` |
| Evaluated source SHA-256 | `{source['source_hash']}` |
| Frozen configuration SHA-256 | `{source['config_hash']}` |
| Design SHA-256 | `{proof['design_hash']}` |
| Preflight source SHA-256 | `3dea8da16ae2f9520219d58d86b500dbdff7b9115e87f8ce0d4c1fc686282838` |

The [final source archive]({P}/validation/evaluated_source_v3.zip) and [identity]({P}/validation/evaluated_source_v3.json) preserve exact evaluated bytes across Git line-ending conversion. The [preflight archive]({P}/validation/preflight_source.zip) preserves the earlier no-fit implementation. Reporting/publication commits are later descendants, not substituted evaluated source.

The [unit directory]({unit}) contains `surface.csv.gz`, rejection tables, catalogue allocation/events, clean/corrupted `streams.csv.gz`, `hashes.csv.gz`, episode and per-event accounting, group workload, family attribution, recovery, updates and released scores. `outer_*` files contain the separate controlled/fixed/independent comparisons. `actual_cqr_*` files hold the tiny real-interface evidence. `sufficient_*` and unsupported fixtures are explicitly synthetic; `payload.json` retains estimator identity, configuration, memberships and paired draw indices. `COMPLETE.json` hashes every unit file. No raw source dataset, environment or external backup is added to Git.

All commands ran from `smart_building_conformal/` using `C:/cfs_venv/Scripts/python.exe`, `-B`, and numerical thread variables `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` set to `1`. Each [execution record]({P}/validation) saves the exact argv, working directory, UTC endpoints, elapsed seconds and exit status. The source archive and existing environment are required for a source-identical training resume; saved-output validation does not require raw datasets.

## Single next bounded real-data execution proposal

Run **one BDG2 fold-2, model-seed-42 reduced operational pilot**, with all ten retained buildings and the five frozen catalogue seeds. The [frozen proposal](review/amendment004_20260913/next_bounded_proposal.json) has nine .95 candidates: CQR/shared uncalibrated, static plus rolling every 12 origins with 200 scores, and all three applicable rules. It requires **18 inner candidate cells, two inner CQR objects plus one final CQR object (nine quantile estimators total)**; persistence adds no learned fit. Inner selection supports are 13,002/13,030 rows; final fit/calibration/test are 52,025/17,380/34,732 rows. If screening fails, retain abstention and only the predeclared diagnostic outputs.

Allow **1–3 hours as an engineering planning allowance**, not an empirical cost estimate. Use one numerical thread, no parallel real fits, the existing free-RAM launch guard and recorded phase/peak memory. Larger saved streams and real-data fitting costs remain unmeasured. This execution is proposed, **not launched or automatically authorized by completion of this task**:

```powershell
C:/cfs_venv/Scripts/python.exe -B -m src.operational004 --dataset bdg2 --outer-fold 2 --model-seed 42 --config configs/operational_amendment004.json --out outputs/amendment004/bdg2_operational_pilot_f2_s42_v1
```

This is a bounded engineering pilot, not the full candidate-grid, five-model-seed, multi-task experiment. No claim of reliable alerts, successful population coverage, superiority or dissertation readiness follows from the support counts, file validation or smoke.
'''
    (ROOT/'AMENDMENT004_IMPLEMENTATION_REPORT.md').write_text(report,encoding='utf-8')
    print('Wrote report from completed smoke, resume and regression evidence.')


if __name__=='__main__':main()
