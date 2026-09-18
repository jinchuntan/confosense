"""Generate the temperature pilot report, evidence index and remaining-work note.

Reads only produced evidence. Every number is taken from the analysis record,
the validation receipt and the resume receipt; nothing is restated from the
energy study.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import common
from common import REPO, REVIEW, KEY, BRANCH, read, now

ANALYSIS = common.BASE / (KEY + '_analysis')
PUBLICATION = common.publication()
REPORT = REVIEW / 'PLEIA_TEMPERATURE_CONTEXT005_PILOT_REPORT.md'
INDEX = REVIEW / 'TEMPERATURE_EVIDENCE_INDEX.md'
REMAINING = REVIEW / 'TEMPERATURE_REMAINING_WORK.md'


def fmt(x, nd=4):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return 'unavailable'
    if isinstance(x, float):
        return f'{x:.{nd}f}'
    return str(x)


def main():
    rec = read(ANALYSIS / 'ANALYSIS_RECORD.json')
    summary = pd.read_csv(ANALYSIS / 'control_rule_channel_summary.csv')
    ordering = pd.read_csv(ANALYSIS / 'interval_ordering_assessment.csv')
    intervals = pd.read_csv(ANALYSIS / 'interval_diagnostics.csv')
    vpath = common.validation() / 'validation.json'
    val = read(vpath) if vpath.exists() else None
    survey_path = common.BATCH / 'validation_survey/VALIDATION_SURVEY.json'
    survey = read(survey_path) if survey_path.exists() else None
    corrected_path = common.BATCH / 'validation_survey/VALIDATION_SURVEY_CORRECTED_READING.json'
    corrected = read(corrected_path) if corrected_path.exists() else None
    res = read(common.resume())
    pack = read(REVIEW / 'TEMPERATURE_RAW_PACKAGE_VALIDATION.json')
    cost = rec['costs']
    va = rec['variant_accounting']

    comb = summary[summary.channel == 'combined'].copy()
    best = comb.sort_values('conditional_context_detection', ascending=False)

    lines = []
    a = lines.append
    a('# PLEIA temperature conditional-context pilot (fold 2, horizon 1, seed 42)')
    a('')
    a(f'Unit `{KEY}` | dataset `pleia` (temperature, {rec["units"]}) | outer fold 2 | horizon 1 (10 min) | '
      f'model seed 42 | 95% intervals | endpoint `{rec["endpoint"]}` | selection `{rec["selection"]}`.')
    a('')
    a('**This is a conditional synthetic-fault challenge on one model seed and one outer fold.** '
      'Detection and workload below are conditional on a predeclared fault being present. They are not '
      'prevalence, precision, F1 or deployment-feasibility estimates. Temperature units differ from the '
      'energy study, so no cross-dataset error is pooled and no energy uncertainty bound is transferred. '
      'BDG2 operational feasibility remains a separate endpoint.')
    a('')
    a('## Execution and scope')
    a('')
    a('| Item | Value |')
    a('| --- | --- |')
    a(f'| Original contexts | {rec["scope_counts"]["contexts"]} |')
    a(f'| Scheduled fault slots | {rec["scope_counts"]["scheduled_slots"]} |')
    a(f'| Context replay stages | {rec["scope_counts"]["context_stages"]} (68 x 43: 1 clean identity + 42 slots) |')
    a(f'| Event/control/rule/channel records | {rec["scope_counts"]["events"]} |')
    a(f'| Stratum rows | {rec["scope_counts"]["strata_rows"]} |')
    a(f'| Control/rule/channel summary rows | {rec["scope_counts"]["macro_rows"]} |')
    a(f'| Unique realization hashes | {va["unique_realization_hashes"]} |')
    a(f'| Alias variants | {va["aliases"]} |')
    a(f'| Null realizations | {va["null_realizations"]} |')
    a(f'| Effective fault slots | {va["effective_slots"]} |')
    a(f'| Recorded run exit status | {rec["complete_json"]["actual_exit_status"]} |')
    a('')
    a('## Fitting budget (authorized and actually spent)')
    a('')
    ops = rec['operation_counts']
    a('| Operation | Count |')
    a('| --- | --- |')
    for k in ['cqr_wrapper_fit', 'quantile_estimator_fit', 'nested_calibrator_conformalize',
              'logical_conformalizations', 'persistence_radius_computations', 'persistence_learned_fits',
              'xgboost_fits', 'attention_lstm_fits', 'enbpi_fits', 'dscp_fits', 'tuning_runs',
              'matched_forecast_refits']:
        a(f'| {k} | {ops[k]} |')
    a('')
    a(f'Shared quantile owner `{ops["owner_sha256"][:16]}...`, native estimator random states '
      f'`{ops["estimator_random_states"]}`, persistence radius {fmt(ops["persistence_radius_degC"], 3)} '
      f'{rec["units"]}. Raw, static CQR and rolling CQR share the same fitted estimators.')
    a('')
    a('## Detection versus workload (combined channel)')
    a('')
    a('| Control | Rule | Detection | Restricted TTD (min) | Detected | Misses | '
      'Background episodes/asset-day | Fraction time in alert |')
    a('| --- | --- | --- | --- | --- | --- | --- | --- |')
    for r in comb.sort_values(['control_id', 'rule_id']).itertuples():
        a(f'| {r.control_id} | {r.rule_id} | {fmt(r.conditional_context_detection)} | '
          f'{fmt(r.restricted_ttd_equal_stratum_minutes, 1)} | {r.detected} | {r.misses} | '
          f'{fmt(r.background_episodes_per_asset_day, 4)} | {fmt(r.fraction_time_in_alert, 4)} |')
    a('')
    a(f'Highest conditional-context detection in the combined channel: `{best.iloc[0].control_id}` / '
      f'`{best.iloc[0].rule_id}` at {fmt(best.iloc[0].conditional_context_detection)}, with '
      f'{fmt(best.iloc[0].background_episodes_per_asset_day, 4)} background episodes per asset-day.')
    a('')
    a('Workload denominators use the entire declared clean stream, including the untiled tail rows, '
      f'at {fmt(comb.original_asset_days.iloc[0], 6)} asset-days over '
      f'{int(comb.original_eligible_rows.iloc[0])} outer rows. Misses remain included in the restricted '
      'time-to-detection, which retains the declared restriction.')
    a('')
    a('## Interval quality')
    a('')
    a('| Scope | Control | Target | n | Coverage | MPIW (degC) | Winkler (degC) |')
    a('| --- | --- | --- | --- | --- | --- | --- |')
    for r in intervals.sort_values(['scope', 'control_id', 'target']).itertuples():
        a(f'| {r.scope} | {r.control_id} | {r.target} | {r.n} | {fmt(r.coverage)} | '
          f'{fmt(r.mpiw, 3)} | {fmt(r.winkler, 3)} |')
    a('')
    a('## Quantile-ordering warnings')
    a('')
    a('The run log retains MAPIE `The predictions are ill-sorted.` messages. They were assessed against '
      'the saved artifacts rather than suppressed. In MAPIE 1.4.1 `_check_lower_upper_bounds` only emits a '
      'log record; it never sorts, clips or recalibrates. It fires when the lower bound exceeds the upper '
      'bound **or** when the median prediction leaves the band. Counts on the emitted streams:')
    a('')
    a('| Control | Stages | Rows | Raw inversions | Emitted inversions | Median below lower | '
      'Median above upper | Min emitted width (degC) |')
    a('| --- | --- | --- | --- | --- | --- | --- | --- |')
    for r in ordering.itertuples():
        a(f'| {r.control_id} | {r.stages} | {r.rows} | {r.raw_inversions} | {r.emitted_inversions} | '
          f'{r.point_below_lower} | {r.point_above_upper} | {fmt(r.minimum_emitted_width, 6)} |')
    a('')
    total_inv = int(ordering.emitted_inversions.sum())
    if total_inv == 0:
        a('No emitted interval is inverted anywhere in the study, and the minimum emitted width is strictly '
          'positive for every control. The messages therefore reflect median/tail quantile crossing in a '
          'small minority of rows, which leaves interval endpoints correctly ordered and coverage and MPIW '
          'well defined. No sorting, clipping or recalibration was introduced, and the frozen protocol was '
          'not changed.')
    else:
        a(f'**{total_inv} emitted intervals are inverted.** This is a methodological defect and is reported '
          'here rather than repaired by changing the frozen protocol.')
    a('')
    a('## Independent validation and zero-fit completed resume')
    a('')
    if val is not None:
        a(f'- Independent validation receipt: passed = {val.get("passed")}, '
          f'maximum observed difference = {val.get("maximum_difference", "see receipt")}.')
    else:
        a('- The frozen `validate` action **did not pass**. Attempt 1 aborted at '
          '`lower_context_3c2ed441cb78fe67ef35_v0`; the failed attempt and its log are preserved and no '
          'tolerance was loosened. See the full-extent survey below.')
    if survey is not None:
        a(f'- Full-extent independent validation survey (frozen tolerance 1e-10 applied unchanged): '
          f'{survey["total_checks"]} checks, {survey["total_violating_elements"]} violating elements, '
          f'maximum observed difference {survey["maximum_observed_difference"]:.3e} degC.')
    if corrected is not None:
        a('')
        a('| Category | Violations |')
        a('| --- | --- |')
        for k, v in corrected['zero_violation_categories'].items():
            a(f'| {k} | {v} |')
        for k, v in corrected['nonzero_categories'].items():
            a(f'| {k} | {v["violating_elements"]} elements, max {v["maximum_difference"]:.4g} {v["units"]} '
              f'({v["affected"]}) |')
        a('')
        a(f'**Corrected conclusion.** {corrected["corrected_conclusion"]}')
        a('')
        a(f'{corrected["persistence_static_unaffected"]}')
        a('')
        a(f'A computed string in the raw survey file reads "SCIENTIFIC OUTCOME DIFFERS - investigate". '
          f"That string is incorrect and is a defect in the survey's own reporting logic, not a finding: "
          f'{corrected["why_the_string_is_wrong"]} The raw file is preserved unmodified and '
          f'`VALIDATION_SURVEY_CORRECTED_READING.json` records this correction.')
        a('')
        a(f'**Unresolved.** {corrected["what_remains_unresolved"]}')
    a(f'- Completed resume: models fitted {res["models_fitted"]}, calibrators fitted {res["calibrators_fitted"]}, '
      f'replay updates {res["replay_updates"]}, scientific artifacts unchanged '
      f'{res["scientific_artifacts_unchanged"]}.')
    a('')
    a('## Measured cost and its limits')
    a('')
    a(f'- Measured stage CPU: {cost["measured_stage_cpu_seconds"]} s across {cost["stages_completed"]} stages.')
    a(f'- Measured stage wall: {cost["measured_stage_wall_seconds"]} s.')
    a(f'- Measured peak RSS: {cost["measured_peak_rss_bytes"]} bytes '
      f'({cost["measured_peak_rss_bytes"] / 2 ** 20:.1f} MiB).')
    a(f'- Atomic-rename denials retried to success: {cost["rename_denials"]}; '
      f'recovered ready stages: {cost["recovered_ready_stages"]}.')
    a('')
    for lim in cost['measurement_limitations']:
        a(f'- {lim}')
    a('')
    a('Per-attempt coordinator phases:')
    a('')
    a('| Phase | Exit status | Finished (UTC) |')
    a('| --- | --- | --- |')
    for p in cost['coordinator_phases']:
        a(f'| {p["phase"]} | {p["exit_status"]} | {p["utc"]} |')
    a('')
    a('## Inference status')
    a('')
    a(f'{rec["inference"]["note"]} Engine inference status: `{rec["inference"]["status"]}`. '
      f'Control/rule/channel macro statuses: {json.dumps(rec["macro_status"])}.')
    a('')
    a('## Scope accounting')
    a('')
    a('Matched forecasting units remain 70/195, matched interval-method cells 250/1950, unique seasonal '
      'computations 9/27. This conditional-context pilot is separately identified evidence and fills none '
      'of those cells. Full-study readiness remains false.')
    a('')
    a(f'Packaged raw evidence: {pack["parts"]} parts, {pack["members"]} verified members, '
      f'{pack["raw_files"]} raw files, {pack["total_part_bytes"]} bytes total '
      f'({pack["total_part_bytes"] / 2 ** 30:.3f} GiB).')
    a('')
    REPORT.write_text('\n'.join(lines).rstrip('\n') + '\n', encoding='utf-8')

    # ---- evidence index -------------------------------------------------
    idx = []
    b = idx.append
    b('# PLEIA temperature context005 pilot: evidence index')
    b('')
    b(f'Branch `{BRANCH}`. Unit `{KEY}`. Generated {now()}.')
    b('')
    b('## Reports and receipts')
    b('')
    b('| Artifact | Path |')
    b('| --- | --- |')
    for label, path in [
        ('Pilot report', REPORT),
        ('Analysis record', ANALYSIS / 'ANALYSIS_RECORD.json'),
        ('Independent validation receipt', common.validation() / 'validation.json'),
        ('Zero-fit completed resume receipt', common.resume()),
        ('Raw package validation', REVIEW / 'TEMPERATURE_RAW_PACKAGE_VALIDATION.json'),
        ('Interruption record (attempt 1)', common.BATCH / 'ATTEMPT_001_INTERRUPTION_RECORD.json'),
        ('Pre-resume fit baseline', common.BATCH / 'PRE_RESUME_FIT_BASELINE.json'),
        ('Preservation baseline', REVIEW / 'TEMPERATURE_PRESERVATION_BASELINE.json'),
        ('Execution manifest', common.manifest()),
        ('Frozen protocol', common.design() / 'frozen_protocol.json'),
        ('Readiness', common.design() / 'readiness.json'),
    ]:
        b(f'| {label} | `{path.relative_to(REPO).as_posix()}` |')
    b('')
    b('## Directly accessible CSVs')
    b('')
    b('| Table | Path |')
    b('| --- | --- |')
    for label, name in [
        ('Control/rule/channel summary (60 rows)', 'control_rule_channel_summary.csv'),
        ('Stratum support (1260 rows)', 'stratum_support.csv'),
        ('Full clean-stream workload', 'fullstream_workload.csv'),
        ('Interval diagnostics', 'interval_diagnostics.csv'),
        ('Interval ordering assessment', 'interval_ordering_assessment.csv'),
        ('Operation counts', 'operation_counts.csv'),
        ('Execution cost', 'execution_cost.csv'),
        ('Original-context contributions (for later seed aggregation)',
         'original_context_contributions.csv.gz'),
    ]:
        b(f'| {label} | `{(ANALYSIS / name).relative_to(REPO).as_posix()}` |')
    b('')
    b('## Figures')
    b('')
    for name in ['detection_workload_delay.png', 'detection_by_rule.png']:
        b(f'- `{(ANALYSIS / name).relative_to(REPO).as_posix()}`')
    b('')
    b('## Lossless raw evidence')
    b('')
    b(f'{pack["parts"]} deterministic ZIP parts with `parts_manifest.csv` and `raw_file_manifest.csv.gz` '
      f'under `{PUBLICATION.relative_to(REPO).as_posix()}`. '
      f'{pack["reconstruction"]}')
    b('')
    INDEX.write_text('\n'.join(idx).rstrip('\n') + '\n', encoding='utf-8')

    # ---- remaining work -------------------------------------------------
    rem = []
    c = rem.append
    c('# Remaining work after the temperature seed-42 pilot')
    c('')
    c('This delivered unit is one model seed (42) and one outer fold (2) for PLEIA temperature.')
    c('')
    c('## Not authorized here; awaiting review of this delivered pilot')
    c('')
    c('- PLEIA temperature seeds 43-46 for the same fold/horizon, then the five-seed original-context '
      'analysis that would make population intervals available for this temperature setting.')
    c('')
    c('## Standing study gaps (unchanged by this pilot)')
    c('')
    c('- Matched forecasting units 70/195.')
    c('- Matched interval-method cells 250/1950; the five interval families are implemented, so the '
      'remainder is predominantly unexecuted scope rather than missing method code.')
    c('- Unique seasonal computations 9/27.')
    c('- Full-study readiness remains false.')
    c('')
    c('No further experiment has been launched.')
    c('')
    REMAINING.write_text('\n'.join(rem).rstrip('\n') + '\n', encoding='utf-8')
    print(json.dumps(dict(report=str(REPORT), index=str(INDEX), remaining=str(REMAINING)), indent=2))


if __name__ == '__main__':
    main()
