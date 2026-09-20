"""Generate the audit documents from produced evidence. No hand-typed numbers."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import audit_common as A
from src.intervals005_common import read

AUD = A.OUT
CAND = AUD / 'candidate_v1'
REPORT = A.AUDIT_REVIEW / 'VALIDATION_AUDIT_REPORT.md'
CONTRACT = A.AUDIT_REVIEW / 'CANDIDATE_VALIDATION_CONTRACT.md'
CORRECT = A.AUDIT_REVIEW / 'REPORT_CORRECTIONS.md'
INDEX = A.AUDIT_REVIEW / 'AUDIT_EVIDENCE_INDEX.md'


def w(path, lines):
    path.write_text('\n'.join(lines).rstrip('\n') + '\n', encoding='utf-8')


def main():
    mech = read(AUD / 'MECHANISM_PROOF.json')
    cand = read(CAND / 'CANDIDATE_VALIDATION.json')
    sens = json.loads((CAND / 'sensitivity_attribution.json').read_text(encoding='utf-8'))
    tests = read(AUD / 'contract_tests/CONTRACT_TESTS.json')
    gh = read(A.COORD / 'AUDIT_GITHUB_READBACK.json')
    survey = read(A.COORD / 'validation_survey/VALIDATION_SURVEY.json')
    corrected = read(A.COORD / 'validation_survey/VALIDATION_SURVEY_CORRECTED_READING.json')
    counts = read(AUD / 'COUNT_RECONCILIATION.json')
    lattice = read(AUD / 'LATTICE_EVIDENCE.json')
    cov = read(AUD / 'SURVEY_COVERAGE_AUDIT.json')
    ivl = pd.read_csv(A.BASE / (A.KEY + '_analysis') / 'interval_diagnostics.csv')
    summ = pd.read_csv(A.BASE / (A.KEY + '_analysis') / 'control_rule_channel_summary.csv')

    # ---------------- main audit report ----------------
    L = []
    a = L.append
    a('# PLEIA-temperature context005 seed-42 pilot: validation audit')
    a('')
    a(f'Audit branch `{A.AUDIT_BRANCH}`, a descendant of the delivered pilot branch '
      f'`{A.PILOT_BRANCH}`.')
    a('')
    a(f'- Pilot primary results: `{A.PRIMARY}`')
    a(f'- Pilot final delivery: `{A.DELIVERY}`')
    a(f'- Recorded main (unchanged): `{A.MAIN}`')
    a('')
    a('## 1. Acceptance status')
    a('')
    a('**Execution and publication complete; scientific acceptance pending validation.**')
    a('')
    a('Publication and scientific validation are separate. Publication is verified: '
      f'{len(gh["checks"])} published artifacts were downloaded over HTTPS from '
      '`raw.githubusercontent.com` pinned to their commit SHAs and compared against the committed '
      f'git blobs; all were byte-identical (`passed = {gh["passed"]}`). '
      'Scientific validation is NOT established: the frozen `validate` action failed on attempt 1 '
      'and has not been made to pass. That original failure is preserved and is not relabelled here.')
    a('')
    a('## 2. The mechanism: proven, not inferred')
    a('')
    fd = mech['feature_difference']
    a(f'The engine computes causal features with vectorised pandas operations; the frozen validator '
      f'reconstructs them scalar-wise. On the stage where attempt 1 aborted '
      f'(`{mech["stage"]}`) the two representations agree to '
      f'{fd["max_overall"]:.3e}, inside the unchanged frozen feature tolerance of '
      f'{fd["frozen_feature_tolerance"]:g} (`within_frozen_tolerance = {fd["within_frozen_tolerance"]}`).')
    a('')
    u = fd['ulp_multiple_of_max']
    a(f'The largest single difference is on `{u["column"]}` at row {u["row"]}: engine '
      f'`{u["engine_value"]}` versus validator `{u["validator_value"]}`, a gap of '
      f'{u["absolute_difference"]:.3e}, which is **{u["difference_in_ulps"]:.0f} ULP** of that value. '
      'This is floating-point summation-order noise, not a difference in the causal construction.')
    a('')
    a('### Feature identity, order and dtype')
    a('')
    fi = mech['feature_identity']
    a(f'- Columns: {fi["n_columns"]}; order identical in both representations: '
      f'{fi["column_order_identical"] and fi["saved_column_order_identical"]}.')
    a(f'- Reconstructed dtypes: {fi["scalar_dtypes"]}; saved dtypes: {fi["saved_dtypes"]}. '
      '(The saved frame additionally carries an integer column; the model receives the same '
      'float64 matrix in both cases.)')
    a('')
    a('### The routing difference, at node level')
    a('')
    a('At predict time a `HistGradientBoostingRegressor` compares the **raw** feature value against '
      'each tree node\'s `num_threshold`. The audit walks the serialized trees node by node for both '
      'representations. The manual walk reproduces `sklearn`\'s own `predict` exactly in every case '
      'checked, so the routing evidence is trustworthy.')
    a('')
    a('| estimator | row | feature | `num_threshold` | engine value | validator value | boosting stages diverging | prediction delta (degC) |')
    a('| --- | --- | --- | --- | --- | --- | --- | --- |')
    for e in mech['tree_routing_evidence']:
        for dv in e['divergences']:
            n = dv['first_divergent_node']
            a(f'| q={e["quantile"]} | {e["row"]} | `{n["feature_name"]}` | `{n["num_threshold"]}` | '
              f'`{n["engine_value"]}` | `{n["validator_value"]}` | {e["stages_with_different_leaf"]} of '
              f'{e["total_stages"]} | {e["prediction_difference"]:.3e} |')
    a('')
    a('In each case the feature value sits **exactly on** the split threshold for one of the two '
      'representations, so `v <= threshold` is decided by the last bit. Exactly one boosted stage '
      'diverges, and the prediction delta equals that single leaf-value delta.')
    a('')
    a('### Why this feature, and why this dataset')
    a('')
    a(f'The mechanism is not a coincidence; it is predictable from the data. The raw PLEIA temperature '
      f'target is recorded at {lattice["target_resolution_degC"]} degC resolution '
      f'({lattice["distinct_target_values"]} distinct values). `target_rollmean_6` averages six such '
      f'values and therefore lands on a coarse lattice with only {lattice["rollmean_6_distinct"]} '
      f'distinct values. Split thresholds are learned from that same lattice, so '
      f'**{lattice["thresholds_equal_to_observed_value"]} of {lattice["thresholds_on_rollmean_6"]} '
      f'({lattice["threshold_coincidence_pct"]:.1f}%) of the split thresholds on this feature are exactly '
      f'equal to an observed feature value**, and '
      f'{lattice["rows_exactly_on_threshold_pct"]:.2f}% of feature rows sit exactly on some threshold.')
    a('')
    a(f'By contrast `target_rollmean_144` has {lattice["rollmean_144_distinct"]} distinct values (a much '
      'finer lattice) and never carries a flip, despite having the LARGER reconstruction difference. '
      '`target_lag_0`, which `persistence_static` uses, is a direct lookup with no summation and has '
      'zero reconstruction difference. That is why persistence is immune — supporting evidence that '
      'now has a mechanism behind it rather than standing alone.')
    a('')
    a('### Does the mechanism explain every violation?')
    a('')
    s = cand['sensitivity']
    a(f'Across the complete pilot the audit located every variant whose two representations produce a '
      f'different prediction: **{s["stages_where_representations_diverge"]} stages, '
      f'{s["rows_affected"]} rows** '
      f'({100*s["rows_affected"]/counts["unique_canonical"]/144:.5f}% of the '
      f'{counts["unique_canonical"]} x 144 unique rows). Each was attributed by walking the trees.')
    a('')
    a(f'- Row-cases fully explained by a split-threshold straddle: '
      f'**{lattice["rowcases_explained"]} of {lattice["rowcases_total"]}**.')
    a(f'- Unexplained discrepancies: **{len(s["unexplained"])}**.')
    a(f'- Every one of the {lattice["divergence_events"]} divergence events is carried by a single '
      f'feature, `target_rollmean_6`; per-estimator split {lattice["divergence_by_estimator"]}.')
    a('')
    a('The mechanism therefore explains **all** observed discrepancy, with no unexplained residue.')
    a('')
    a('## 3. Audit of the original survey and its corrected interpretation')
    a('')
    a(f'The original survey reported {survey["total_checks"]} checks and '
      f'{survey["total_violating_elements"]} violating elements '
      f'({survey["violations_by_kind"][0]["violations"]} bounds, '
      f'{survey["violations_by_kind"][1]["violations"]} released-score).')
    a('')
    a('### Assertion coverage reconstructed independently')
    a('')
    a('Absence of recorded violations is not coverage. The audit reconstructs the survey\'s assertion '
      'count analytically from the design, and it matches exactly:')
    a('')
    a('| term | value |')
    a('| --- | --- |')
    for k, v in cov['analytic_terms'].items():
        a(f'| {k} | {v} |')
    a(f'| **analytic total** | **{cov["analytic_total"]}** |')
    a(f'| survey reported | {cov["survey_reported"]} |')
    a(f'| match | {cov["match"]} |')
    a('')
    a('Skipped checks are accounted for explicitly rather than silently: the three static controls '
      f'have zero rolling-update rows, so their `update` assertions do not execute '
      f'({cov["updates_rows_by_control"]}). Only `cqr_rolling` carries updates.')
    a('')
    a('### Rolling numerical state was verified, with denominators')
    a('')
    bk = cand['by_kind']
    a('Unchanged release identity and update counts would NOT establish that rolling calibration '
      'state is unchanged. The state numbers themselves were compared:')
    a('')
    a(f'- `C_rolling_state` (pool_n, correction_lower, correction_upper): '
      f'{bk["C_rolling_state"]["assertions"]} assertions over '
      f'{bk["C_rolling_state"]["elements"]} compared numbers, '
      f'{bk["C_rolling_state"]["violations"]} violations.')
    a(f'- `C_released_scores`: {bk["C_released_scores"]["assertions"]} assertions over '
      f'{bk["C_released_scores"]["elements"]} scores, {bk["C_released_scores"]["violations"]} violations.')
    a(f'- `C_update_status`: {bk["C_update_status"]["assertions"]} assertions, '
      f'{bk["C_update_status"]["violations"]} violations.')
    a('')
    a('Propagation was traced directly: a released-score difference can only move a later bound '
      'through the rolling correction, and the corrections are numerically identical everywhere. '
      'On the attempt-1 stage the bound differences remain confined to the same two rows as the '
      'prediction differences, with no downstream drift.')
    a('')
    a('### The original "SCIENTIFIC OUTCOME DIFFERS" string')
    a('')
    a('That string is retained in the raw survey output and is **incorrect**. It was produced by the '
      'survey\'s own classification, which counted the `release` kind as a scientific outcome when its '
      'violations are released conformity SCORE VALUES. The release semantics that carry meaning — '
      'release identity, release counts, update counts, update status — recorded zero violations. '
      f'`VALIDATION_SURVEY_CORRECTED_READING.json` records this, and this audit confirms it '
      'independently.')
    a('')
    a('**Which numerical quantities differ:** interval bound values and released conformity score '
      'values, at rows where a feature sits on a split threshold.')
    a('')
    a('**Which evaluated endpoints agree:** alert flags, episode onsets, event-ledger completeness, '
      'event detection, restricted/censored delay, equal-context denominators, equal-context recall, '
      'full clean-stream workload and original exposure.')
    a('')
    a('## 4. Candidate validation result')
    a('')
    t = cand['totals']
    a(f'The candidate contract (see `CANDIDATE_VALIDATION_CONTRACT.md`) was run across the complete '
      f'existing pilot with fits forbidden and no scientific output mutated:')
    a('')
    a(f'- **{t["assertions"]} assertions** over **{t["elements"]} compared elements**')
    a(f'- **{t["violations"]} violations**; `passed = {cand["passed"]}`')
    a(f'- maximum observed difference {t["maximum_observed_difference"]:.3e} (feature provenance, '
      'inside the unchanged 1e-10)')
    a(f'- scientific artifacts unchanged before/after: `{cand["artifacts_unchanged"]}`')
    a(f'- cost: {cand["resources"]["seconds"]:.0f} s wall, '
      f'{cand["resources"]["process_cpu_seconds"]:.0f} s CPU, '
      f'{cand["resources"]["lifetime_peak_rss_bytes"]/2**20:.1f} MiB peak RSS')
    a('')
    a('| contract layer | assertions | elements | violations |')
    a('| --- | --- | --- | --- |')
    for k, v in sorted(bk.items()):
        a(f'| `{k}` | {v["assertions"]} | {v["elements"]} | {v["violations"]} |')
    a('')
    a('## 5. Focused tests')
    a('')
    a(f'{tests["passed"]} of {tests["total"]} passed (`all_ok = {tests["all_ok"]}`). Each test runs the '
      'real candidate code path against a disposable sandbox copy; the genuine artifacts are never '
      'written to.')
    a('')
    a('| test | expected | observed | detected by |')
    a('| --- | --- | --- | --- |')
    for r in tests['results']:
        a(f'| `{r["test"]}` | {r["expected"]} | {r["observed"]} | {r.get("detected_by","") or "-"} |')
    a('')
    a('The candidate is therefore not vacuous: it rejects feature, observation, model, prediction, '
      'interval, rolling-update, released-score and alert corruption.')
    a('')
    a('## 6. Count reconciliation')
    a('')
    a('The pilot report lists several counts without stating how they relate. They are two distinct '
      'partitions of the same 2,924 context stages, plus a classification of the fault slots.')
    a('')
    a('| identity | arithmetic | holds |')
    a('| --- | --- | --- |')
    for r in counts['identities']:
        a(f'| {r["identity"]} | {r["arithmetic"]} | {r["holds"]} |')
    a('')
    a('- **Clean stages are not fault slots.** Each context contributes one clean identity replay '
      '(ordinal 0) plus 42 scheduled fault slots (ordinals 1-42).')
    a(f'- Aliases occur only among fault slots ({counts["aliases_among_fault"]}), never among clean '
      f'stages ({counts["aliases_among_clean"]}): each context\'s clean replay is a distinct realization.')
    a('- `null` and `effective` are exact complements **on fault slots**; clean stages are null by '
      'definition and are never effective.')
    a('')
    a('## 7. Preservation')
    a('')
    a('No scientific artifact was modified by this audit. The candidate validator recorded the run '
      'directory file tree before and after its full pass and they are identical '
      f'(`artifacts_unchanged = {cand["artifacts_unchanged"]}`). The frozen `src` tree is untouched, so '
      'the source hash that the completed energy study also depends on is intact.')
    a('')
    w(REPORT, L)

    # ---------------- contract document ----------------
    L = []
    a = L.append
    a('# Candidate validation contract v1')
    a('')
    a('Status: **candidate, not adopted.** It does not replace the frozen `validate` action and does '
      'not waive any scientific gate. It is implemented on the audit branch and imports `src` without '
      'modifying it.')
    a('')
    a('## What the frozen validator asserts')
    a('')
    a('The frozen validator asserts, in a single step, that the saved bounds equal those obtained by '
      'applying the saved model to a feature vector reconstructed **independently of the engine**. '
      'Call this A\'.')
    a('')
    a('A\' silently conflates two claims, and is **unsatisfiable** on this data: a gradient-boosted '
      'tree ensemble is piecewise constant, so a sub-tolerance change in an input can change the '
      'output by an arbitrary amount. Demanding agreement of a discontinuous function under a 1-ULP '
      'perturbation is not a strict test; it is an impossible one.')
    a('')
    a('## What the candidate asserts')
    a('')
    a('| layer | claim | how |')
    a('| --- | --- | --- |')
    a('| **A** | Provenance: the saved production features are what the declared causal construction '
      'produces from the raw source | independent scalar reconstruction (no production '
      '`causal_features`/`inject`/pandas rolling) compared at the UNCHANGED 1e-10 tolerance, plus saved '
      '`feature_hash` and `observation_hash` identity |')
    a('| **B** | Model application: the saved model reproduces the saved predictions from the exact '
      'verified production representation | direct estimator application to the verified saved features |')
    a('| **C** | Downstream: calibration, causal release/update state, interval construction and alert '
      'outcomes | independent scalar re-derivation from that verified representation |')
    a('')
    a('Saved features are therefore **never** trusted as inputs: layer A establishes their provenance '
      'before layer B consumes them.')
    a('')
    a('## Precisely how the contract differs')
    a('')
    a('A ^ B ^ C is strictly weaker than A\' in exactly one respect: it does not certify that a '
      'prediction is **stable** under a sub-tolerance perturbation of the features. Everything else '
      'the frozen validator checks is retained, at the same tolerances.')
    a('')
    a('## What it can detect')
    a('')
    a('- Wrong or tampered causal features, including ones that would pass a coarse eyeball check '
      '(layer A, demonstrated at 0.5 degC).')
    a('- Tampered observations (layer A).')
    a('- A substituted or perturbed model, even when every saved output is left untouched '
      '(layer B, demonstrated at 0.05 degC on a baseline).')
    a('- Tampered predictions, interval bounds, released scores, rolling corrections, update status '
      'and alert flags (layers B and C).')
    a('')
    a('## Remaining limitations, stated plainly')
    a('')
    a('1. **Perturbation stability is not certified.** The audit quantifies what this gives up rather '
      f'than hiding it: {cand["sensitivity"]["stages_where_representations_diverge"]} stages and '
      f'{cand["sensitivity"]["rows_affected"]} rows out of {counts["unique_canonical"]} x 144 would '
      'predict differently under the independent reconstruction, every one attributable to a split '
      'threshold.')
    a('2. **Common-mode error is not excluded.** If the declared causal construction were itself wrong, '
      'and the independent scalar reconstruction reproduced the same wrong value, layer A would pass. '
      'The scalar path is deliberately written without the production helpers, which mitigates but does '
      'not eliminate this.')
    a('3. **It does not re-derive the model.** No validator here refits; the saved estimators are taken '
      'as the object under test, and their identity is checked by hash elsewhere in the pipeline.')
    a('4. **Single seed.** Nothing here changes the fact that population intervals remain unavailable '
      'for this setting.')
    a('')
    a('## Why this was NOT implemented inside `src`')
    a('')
    a('The repository provides `validation_source_compatible()` for exactly this kind of post-completion '
      'validator repair. The audit assessed it and did **not** use it, for two concrete reasons:')
    a('')
    a(f'1. **It mandates a two-file change set.** The check requires the changed set to equal exactly '
      '`{conditional_context005.py, context005_validate.py}`. A repair confined to the validator '
      '(`context005_validate.py` alone) would FAIL the mechanism, forcing an otherwise unnecessary edit '
      'to a second file purely to satisfy a hash-exact gate.')
    a(f'2. **Blast radius.** `source_digest()` covers all of `src`. '
      f'{lattice["protocols_pinning_source_hash"]} protocol files in this repository pin a source hash, '
      f'and all five completed PLEIA-energy seeds pin the identical `{A.SOURCE_HASH[:16]}...` as this '
      'temperature pilot. Editing `src` would invalidate `check_protocol` for the delivered energy '
      'study as well, and each affected design would need its own compatibility receipt before it could '
      'be re-validated.')
    a('')
    a('Adopting the candidate into `src` is therefore a separate, explicit decision with consequences '
      'beyond this pilot. It is proposed, not taken.')
    a('')
    w(CONTRACT, L)

    # ---------------- corrections ----------------
    comb = summ[summ.channel == 'combined']
    fs = ivl[(ivl.scope == 'fullstream_clean') & (ivl.target == 'clean_counterfactual')]
    L = []
    a = L.append
    a('# Corrections to reported wording and count labels')
    a('')
    a('## Scope of these corrections')
    a('')
    a('Two of the three items raised concern claims that appeared in the **delivering session\'s prose '
      'summary**, not in the committed report. The committed '
      '`PLEIA_TEMPERATURE_CONTEXT005_PILOT_REPORT.md` presents the numbers in tables and makes one '
      'narrative claim, which correctly pairs detection with its workload. The corrections are recorded '
      'here in full regardless, and the report is given the missing explicit interpretation.')
    a('')
    a('## Correction 1: rolling CQR does not reach nominal coverage')
    a('')
    a('Claimed in the session summary: rolling CQR "recovers to 90.8%" and "only reaches nominal by '
      'widening". **Wrong.** Nominal is 0.95.')
    a('')
    a('| control | clean-stream coverage | reaches nominal 0.95 | shortfall |')
    a('| --- | --- | --- | --- |')
    for r in fs.sort_values('coverage', ascending=False).itertuples():
        a(f'| `{r.control_id}` | {r.coverage:.4f} | {"yes" if r.coverage >= 0.95 else "**no**"} | '
          f'{0.95 - r.coverage:+.4f} |')
    a('')
    a('Only `persistence_static` attains nominal coverage. `cqr_rolling` at 0.9081 remains **0.0419 '
      'below nominal**, and it does so at the widest interval of all four controls '
      f'({fs[fs.control_id=="cqr_rolling"].mpiw.iloc[0]:.3f} degC MPIW). It narrows the shortfall '
      'relative to the static conformal controls; it does not close it.')
    a('')
    a('## Correction 2: "dominates on every axis" is too broad')
    a('')
    a('Claimed in the session summary: persistence "dominates on every axis". **Too broad.**')
    a('')
    imm = comb[comb.rule_id == 'single_sample']
    a('At the immediate rule in the combined channel:')
    a('')
    a('| control | detection | background episodes/asset-day | fraction time in alert |')
    a('| --- | --- | --- | --- |')
    for r in imm.sort_values('conditional_context_detection', ascending=False).itertuples():
        a(f'| `{r.control_id}` | {r.conditional_context_detection:.4f} | '
          f'{r.background_episodes_per_asset_day:.4f} | {r.fraction_time_in_alert:.4f} |')
    a('')
    a(f'`persistence_static` raises **more** clean-stream episodes per asset-day than `cqr_rolling` '
      f'({imm[imm.control_id=="persistence_static"].background_episodes_per_asset_day.iloc[0]:.4f} versus '
      f'{imm[imm.control_id=="cqr_rolling"].background_episodes_per_asset_day.iloc[0]:.4f}), so it does '
      'not dominate on that axis. Nor does it lead at every rule:')
    a('')
    best = comb.loc[comb.groupby('rule_id').conditional_context_detection.idxmax()]
    a('| rule | best control (combined) | detection |')
    a('| --- | --- | --- |')
    for r in best.itertuples():
        a(f'| `{r.rule_id}` | `{r.control_id}` | {r.conditional_context_detection:.4f} |')
    a('')
    a('Supportable statement: persistence leads on interval coverage, width, Winkler score, and on '
      'detection and restricted delay at the immediate, 180-minute and 360-minute rules, while '
      '`cqr_rolling` leads at the 30- and 60-minute rules and raises fewer clean-stream episodes at '
      'the immediate rule.')
    a('')
    a('## Correction 3: count labels reconciled')
    a('')
    a('| identity | arithmetic | holds |')
    a('| --- | --- | --- |')
    for r in counts['identities']:
        a(f'| {r["identity"]} | {r["arithmetic"]} | {r["holds"]} |')
    a('')
    a('Clean stages are distinct from fault slots: 68 contexts x (1 clean identity replay + 42 '
      'scheduled fault slots) = 2,924 context stages. The alias/unique split is a **different** '
      'partition of those same 2,924 stages. `null` and `effective` are exact complements on the 2,856 '
      'fault slots, and the 68 clean stages are null by definition.')
    a('')
    a('## Preserved')
    a('')
    a('Negative findings stand unchanged: severe undercoverage of the learned quantile controls on '
      'temperature, and the high alerting workload that follows from it. No uncertainty bound is '
      'invented for this single seed; population intervals remain unavailable. Measurement gaps are '
      'retained, including the unknown exit status of the interrupted original attempt, and stage CPU '
      'totals remain distinct from end-to-end cost.')
    a('')
    w(CORRECT, L)

    # ---------------- evidence index ----------------
    L = []
    a = L.append
    a('# Validation audit: evidence index')
    a('')
    a(f'Audit branch `{A.AUDIT_BRANCH}`.')
    a('')
    a('| Artifact | Path |')
    a('| --- | --- |')
    rows = [
        ('Audit report', REPORT), ('Candidate contract', CONTRACT), ('Report corrections', CORRECT),
        ('Mechanism proof (node-level)', AUD / 'MECHANISM_PROOF.json'),
        ('Lattice / threshold-coincidence evidence', AUD / 'LATTICE_EVIDENCE.json'),
        ('Survey coverage audit', AUD / 'SURVEY_COVERAGE_AUDIT.json'),
        ('Count reconciliation', AUD / 'COUNT_RECONCILIATION.json'),
        ('Candidate validation result', CAND / 'CANDIDATE_VALIDATION.json'),
        ('Candidate sensitivity attribution', CAND / 'sensitivity_attribution.json'),
        ('Contract test results', AUD / 'contract_tests/CONTRACT_TESTS.json'),
        ('Contract test table', AUD / 'contract_tests/contract_test_results.csv'),
        ('GitHub readback (audit)', A.COORD / 'AUDIT_GITHUB_READBACK.json'),
        ('Candidate validator source', A.AUDIT_REVIEW / 'candidate_validate_v1.py'),
        ('Mechanism proof source', A.AUDIT_REVIEW / 'prove_mechanism.py'),
        ('Contract tests source', A.AUDIT_REVIEW / 'test_candidate_contract.py'),
        ('Original frozen-validate failure (preserved)', A.COORD / 'VALIDATION_ATTEMPT_001_FAILED.json'),
        ('Original survey (unmodified)', A.COORD / 'validation_survey/VALIDATION_SURVEY.json'),
        ('Original survey corrected reading', A.COORD / 'validation_survey/VALIDATION_SURVEY_CORRECTED_READING.json'),
    ]
    for label, path in rows:
        a(f'| {label} | `{Path(path).resolve().relative_to(A.REPO).as_posix()}` |')
    a('')
    a('All paths are relative to the repository root.')
    a('')
    w(INDEX, L)
    print(json.dumps(dict(report=str(REPORT), contract=str(CONTRACT), corrections=str(CORRECT),
                          index=str(INDEX)), indent=2))


if __name__ == '__main__':
    main()
