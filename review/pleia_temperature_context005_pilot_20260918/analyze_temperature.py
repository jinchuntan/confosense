"""Single-seed PLEIA-temperature conditional-context analysis.

This is NOT the five-seed energy aggregator. The declared five-seed inference is
unavailable for this temperature setting, so population intervals stay
unavailable and no energy bound is recycled. Reporting is descriptive for one
model seed and one outer fold.

Explicit imports only: ``common`` re-exports a ``csv`` writer helper that
shadows the standard-library ``csv`` module, which is the documented packaging
defect this unit must not repeat.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

for _name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    os.environ[_name] = '1'

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import common
from common import REPO, REVIEW, SMART, KEY, SOURCE_HASH, read, digest, source_digest, now

sys.path.insert(0, str(SMART))
from src.intervals005_common import Operations, load_owner
from src.operational004_design import STRATA
from src.conformal_quantile import _sub_estimators

SEED = 42
DATASET = 'pleia'
TARGET = 'temperature'
UNITS = 'degC'
RUN = common.run()
ANALYSIS = common.BASE / (KEY + '_analysis')
TABLES = RUN / 'stages/tables'

CONTROLS = ['quantile_static', 'cqr_static', 'cqr_rolling', 'persistence_static']
RULES = ['single_sample', '30min_3of3', '60min_4of6', '180min_3of18', '360min_4of36']
CHANNELS = ['numerical_only', 'availability_only', 'combined']

EXPECTED = dict(contexts=68, scheduled_slots=2856, context_stages=2924,
                events=171360, strata_rows=1260, macro_rows=60, workload_rows=60)


def frame(path):
    try:
        return pd.read_csv(path, float_precision='round_trip',
                           dtype={'row_id': str, 'context_id': str, 'group_id': str,
                                  'original_segment_id': str, 'segment_id': str, 'mask_seed': str})
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def weighted(part):
    n = part.n.sum()
    return pd.Series(dict(n=int(n), unavailable_n=int(part.unavailable_n.sum()),
                          coverage=float((part.coverage * part.n).sum() / n),
                          mpiw=float((part.mpiw * part.n).sum() / n),
                          winkler=float((part.winkler * part.n).sum() / n)))


def summary_rows(events, strata, macros, work):
    workagg = work.groupby(['control_id', 'rule_id', 'channel'], as_index=False).agg(
        eligible_rows=('eligible_rows', 'sum'), asset_days=('asset_days', 'sum'),
        background_episodes=('episodes', 'sum'), alert_rows=('alert_rows', 'sum'),
        time_in_alert_days=('time_in_alert_days', 'sum'))
    workagg['background_episodes_per_asset_day'] = workagg.background_episodes / workagg.asset_days
    workagg['fraction_time_in_alert'] = workagg.time_in_alert_days / workagg.asset_days
    rows = []
    for m in macros.itertuples():
        ss = strata[(strata.control_id == m.control_id) & (strata.rule_id == m.rule_id) & (strata.channel == m.channel)]
        ev = events[(events.control_id == m.control_id) & (events.rule_id == m.rule_id) & (events.channel == m.channel)]
        pos = ev[ev.effective & ev.eligible]
        found = pos[pos.detected]
        w = workagg[(workagg.control_id == m.control_id) & (workagg.rule_id == m.rule_id)
                    & (workagg.channel == m.channel)].iloc[0]
        rows.append(dict(
            dataset=DATASET, target=TARGET, outer_fold=2, horizon=1, model_seed=SEED,
            control_id=m.control_id, rule_id=m.rule_id, channel=m.channel,
            conditional_context_detection=m.conditional_context_macro,
            macro_status=m.status, inference_status=m.inference_status,
            restricted_ttd_equal_stratum_minutes=float(ss.restricted_mean_detection_minutes.mean()),
            effective_slots=int(pos.shape[0]), detected=int(pos.detected.sum()),
            misses=int((~pos.detected).sum()),
            detected_delay_median_minutes=float(found.delay_minutes.median()) if len(found) else np.nan,
            detected_delay_q90_minutes=float(found.delay_minutes.quantile(.9)) if len(found) else np.nan,
            supported_strata=int(m.supported_strata),
            original_eligible_rows=int(w.eligible_rows), original_asset_days=float(w.asset_days),
            background_episodes=int(w.background_episodes),
            background_episodes_per_asset_day=float(w.background_episodes_per_asset_day),
            alert_rows=int(w.alert_rows), time_in_alert_days=float(w.time_in_alert_days),
            fraction_time_in_alert=float(w.fraction_time_in_alert)))
    return pd.DataFrame(rows), workagg


def interval_rows(variants):
    cache = {}
    rows = []
    for v in variants.itertuples():
        if v.canonical_stage not in cache:
            cache[v.canonical_stage] = frame(RUN / 'stages' / v.canonical_stage / 'interval_diagnostics.csv')
        for r in cache[v.canonical_stage].to_dict('records'):
            rows.append(dict(model_seed=SEED, context_id=v.context_id, ordinal=v.ordinal, family=v.family,
                             severity=v.severity, effective=v.effective, null=v.null, alias=v.alias,
                             canonical_stage=v.canonical_stage, **r))
    detail = pd.DataFrame(rows)
    out = []
    for scope, mask in [('identity', detail.ordinal == 0),
                        ('all_scheduled_fault_slots', detail.ordinal > 0),
                        ('effective_fault_slots', (detail.ordinal > 0) & detail.effective)]:
        for key, g in detail[mask].groupby(['control_id', 'target']):
            out.append(dict(model_seed=SEED, scope=scope, control_id=key[0], target=key[1],
                            streams=g[['context_id', 'ordinal']].drop_duplicates().shape[0], **weighted(g)))
    full = [frame(stage / 'interval_diagnostics.csv') for stage in sorted((RUN / 'stages').glob('fullstream_*'))]
    f = pd.concat(full, ignore_index=True)
    for key, g in f.groupby(['control_id', 'target']):
        out.append(dict(model_seed=SEED, scope='fullstream_clean', control_id=key[0], target=key[1],
                        streams=len(g), **weighted(g)))
    result = pd.DataFrame(out)
    result['mpiw_units'] = UNITS
    result['winkler_units'] = UNITS
    return result, detail


def operation_and_cost():
    ops = [json.loads(line) for line in (RUN / 'operations.jsonl').read_text(encoding='utf-8').splitlines()]
    returned = pd.DataFrame([r for r in ops if r.get('event') == 'returned'])
    counts = returned.groupby('kind').size().to_dict()
    if counts != {'calibrator_conformalize': 2, 'cqr_wrapper_fit': 1, 'quantile_estimator_fit': 3}:
        raise ValueError(f'operation budget mismatch: {counts}')
    owner = load_owner(RUN / 'stages/owner_fit_cqr/owner.pkl')
    estimators, _ = _sub_estimators(owner)
    states = [e.get_params()['random_state'] for e in estimators]
    if states != [SEED, SEED, SEED]:
        raise ValueError(f'native estimator seed mismatch: {states}')
    ident = read(RUN / 'stages/controls/identity.json')
    if not ident['quantile_shared'] or ident['new_learned_fits'] != 0 or ident['persistence_calibrations'] != 1:
        raise ValueError('owner sharing mismatch')
    return dict(dataset=DATASET, target=TARGET, model_seed=SEED, cqr_wrapper_fit=1, quantile_estimator_fit=3,
                nested_calibrator_conformalize=2, logical_conformalizations=1, persistence_radius_computations=1,
                persistence_learned_fits=0, xgboost_fits=0, attention_lstm_fits=0, enbpi_fits=0, dscp_fits=0,
                tuning_runs=0, matched_forecast_refits=0,
                estimator_random_states=';'.join(map(str, states)), owner_sha256=ident['owner_sha256'],
                persistence_radius_degC=ident['persistence_radius'])


def ordering_assessment(variants):
    """Assess the retained MAPIE 'ill-sorted' messages against saved artifacts.

    MAPIE's _check_lower_upper_bounds only logs; it never sorts or clips. It
    fires when lower>upper OR when the median prediction leaves the band. The
    distinction matters, so both are counted on the emitted streams.
    """
    rows = []
    stages = sorted(set(variants.canonical_stage)) + [p.name for p in sorted((RUN / 'stages').glob('fullstream_*'))]
    for name in stages:
        path = RUN / 'stages' / name
        for control in CONTROLS:
            f = path / (control + '_issued.csv.gz')
            if not f.exists():
                continue
            d = pd.read_csv(f, float_precision='round_trip',
                            usecols=['point', 'raw_lower', 'raw_upper', 'lower', 'upper'])
            width = d.upper - d.lower
            rows.append(dict(stage=name, control_id=control, rows=len(d),
                             raw_inversions=int((d.raw_lower > d.raw_upper).sum()),
                             emitted_inversions=int((d.lower > d.upper).sum()),
                             point_below_lower=int((d.point < d.lower).sum()),
                             point_above_upper=int((d.point > d.upper).sum()),
                             min_width=float(width.min())))
    detail = pd.DataFrame(rows)
    agg = detail.groupby('control_id', as_index=False).agg(
        stages=('stage', 'nunique'), rows=('rows', 'sum'),
        raw_inversions=('raw_inversions', 'sum'), emitted_inversions=('emitted_inversions', 'sum'),
        point_below_lower=('point_below_lower', 'sum'), point_above_upper=('point_above_upper', 'sum'),
        minimum_emitted_width=('min_width', 'min'))
    agg['width_units'] = UNITS
    agg['interpretation'] = np.where(
        agg.emitted_inversions > 0, 'INVERTED_EMITTED_INTERVALS_PRESENT',
        'ordered_endpoints_only_median_tail_crossing')
    return agg, detail


def costs():
    journal = [json.loads(l) for l in (RUN / 'stage_journal.jsonl').read_text(encoding='utf-8').splitlines()]
    done = [e for e in journal if e['event'] == 'complete' and 'resources' in e]
    coord = common.BATCH / 'durable_attempts.jsonl'
    attempts = [json.loads(l) for l in coord.read_text(encoding='utf-8').splitlines()] if coord.exists() else []
    phases = [a for a in attempts if a['event'] == 'phase_finished']
    return dict(
        measured_stage_cpu_seconds=round(sum(e['resources']['process_cpu_seconds'] for e in done), 2),
        measured_stage_wall_seconds=round(sum(e['resources']['seconds'] for e in done), 2),
        measured_peak_rss_bytes=max(e['resources']['lifetime_peak_rss_bytes'] for e in done),
        stages_completed=len(done),
        first_stage_started_utc=journal[0]['utc'], last_stage_completed_utc=done[-1]['utc'],
        rename_denials=sum(1 for e in journal if e['event'] == 'atomic_rename_denial'),
        recovered_ready_stages=sum(1 for e in journal if e['event'] == 'recovered_ready_stage'),
        coordinator_phases=[dict(phase=p['phase'], exit_status=p['exit_status'], utc=p['utc'],
                                 worker_peak_rss_bytes=p.get('worker_peak_rss_bytes')) for p in phases],
        measurement_limitations=[
            'The original 2026-09-18 attempt was interrupted without an exit receipt; its wall time is '
            'bounded by journal timestamps only and its terminal exit status is unknown.',
            'Stage-level CPU and RSS are measured inside the worker by the engine PhaseMeter and cover '
            'both the original and the resumed attempt, because completed stage records are preserved.',
            'Peak RSS is the maximum lifetime peak recorded across completed stages, not a continuous '
            'sample of the whole process lifetime.',
            'Coordinator heartbeat worker CPU under-reports: it latched onto the venv redirector stub '
            'for the resumed run phase. The independent liveness probe records the real worker.'])


def figures(summary):
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    combined = summary[summary.channel == 'combined']
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
    markers = dict(zip(CONTROLS, ['o', 's', '^', 'D']))
    for control in CONTROLS:
        part = combined[combined.control_id == control]
        ax[0].scatter(part.background_episodes_per_asset_day, part.conditional_context_detection,
                      label=control, marker=markers[control], s=58, alpha=.85)
        ax[1].scatter(part.background_episodes_per_asset_day, part.restricted_ttd_equal_stratum_minutes,
                      label=control, marker=markers[control], s=58, alpha=.85)
    ax[0].set_xlabel('background episodes per asset-day (clean full stream)')
    ax[0].set_ylabel('conditional-context detection')
    ax[0].set_title(f'PLEIA {TARGET} f2 s{SEED} h1: detection vs workload (combined channel)')
    ax[1].set_xlabel('background episodes per asset-day (clean full stream)')
    ax[1].set_ylabel('restricted time to detection (minutes)')
    ax[1].set_title('Restricted delay vs workload (combined channel)')
    for a in ax:
        a.grid(alpha=.3)
        a.legend(fontsize=8)
    fig.suptitle('Conditional synthetic-fault challenge; not a deployment prevalence estimate', fontsize=9, y=.02)
    fig.tight_layout()
    fig.savefig(ANALYSIS / 'detection_workload_delay.png', dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.2))
    width = .2
    x = np.arange(len(RULES))
    for i, control in enumerate(CONTROLS):
        vals = [combined[(combined.control_id == control) & (combined.rule_id == r)].conditional_context_detection.mean()
                for r in RULES]
        ax.bar(x + i * width - 1.5 * width, vals, width, label=control)
    ax.set_xticks(x)
    ax.set_xticklabels(RULES, rotation=20)
    ax.set_ylabel('conditional-context detection')
    ax.set_title(f'PLEIA {TARGET} f2 s{SEED} h1: detection by persistence rule (combined channel)')
    ax.grid(alpha=.3, axis='y')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(ANALYSIS / 'detection_by_rule.png', dpi=150)
    plt.close(fig)


def main():
    if ANALYSIS.exists() and any(ANALYSIS.iterdir()):
        raise ValueError('preserve completed analysis output')
    complete = read(RUN / 'COMPLETE.json')
    if complete['actual_exit_status'] != 0:
        raise ValueError(f'run did not record a clean exit: {complete["actual_exit_status"]}')
    if source_digest() != SOURCE_HASH:
        raise ValueError('source drift since the frozen design')
    ANALYSIS.mkdir(parents=True, exist_ok=True)

    with Operations(forbid=True):
        events = frame(TABLES / 'events.csv.gz')
        strata = frame(TABLES / 'strata.csv')
        macros = frame(TABLES / 'conditional_macro.csv')
        work = frame(TABLES / 'fullstream_workload.csv')
        variants = frame(TABLES / 'variants.csv')
        contrib = frame(TABLES / 'original_context_contributions.csv.gz')
        inference_csv = frame(TABLES / 'inference.csv')
        inference_json = read(TABLES / 'inference.json')

        actual = dict(contexts=int(variants.context_id.nunique()), scheduled_slots=int((variants.ordinal > 0).sum()),
                      context_stages=len(variants), events=len(events), strata_rows=len(strata),
                      macro_rows=len(macros), workload_rows=len(work))
        if actual != EXPECTED:
            raise ValueError(f'scope accounting mismatch expected={EXPECTED} actual={actual}')

        summary, workagg = summary_rows(events, strata, macros, work)
        intervals, interval_detail = interval_rows(variants)
        ops = operation_and_cost()
        ordering, ordering_detail = ordering_assessment(variants)
        cost = costs()

        summary.to_csv(ANALYSIS / 'control_rule_channel_summary.csv', index=False)
        strata.to_csv(ANALYSIS / 'stratum_support.csv', index=False)
        workagg.to_csv(ANALYSIS / 'fullstream_workload.csv', index=False)
        intervals.to_csv(ANALYSIS / 'interval_diagnostics.csv', index=False)
        ordering.to_csv(ANALYSIS / 'interval_ordering_assessment.csv', index=False)
        ordering_detail.to_csv(ANALYSIS / 'interval_ordering_detail.csv.gz', index=False)
        pd.DataFrame([ops]).to_csv(ANALYSIS / 'operation_counts.csv', index=False)
        contrib.to_csv(ANALYSIS / 'original_context_contributions.csv.gz', index=False)
        pd.DataFrame([{k: v for k, v in cost.items() if not isinstance(v, (list, dict))}]).to_csv(
            ANALYSIS / 'execution_cost.csv', index=False)

        aliases = int(variants.alias.sum())
        nulls = int(variants['null'].sum())
        unique_real = int(variants.realization_hash.nunique())
        effective = int(variants.effective.sum())
        record = dict(
            unit=KEY, dataset=DATASET, target=TARGET, units=UNITS, outer_fold=2, horizon=1, model_seed=SEED,
            level=.95, endpoint='C_effective_fault_conditional_context', selection='none',
            generated_utc=now(), source_hash=SOURCE_HASH,
            complete_json=dict(actual_exit_status=complete['actual_exit_status'],
                               protocol_sha256=complete['protocol_sha256'], utc=complete['utc'],
                               files=len(complete['files'])),
            scope_counts=actual,
            variant_accounting=dict(total_variants=len(variants), identity_variants=int((variants.ordinal == 0).sum()),
                                    scheduled_slots=int((variants.ordinal > 0).sum()), aliases=aliases,
                                    null_realizations=nulls, effective_slots=effective,
                                    unique_realization_hashes=unique_real),
            operation_counts=ops, costs=cost,
            interval_ordering=ordering.to_dict('records'),
            inference=dict(rows=len(inference_csv), status=inference_json.get('status'),
                           note='Single model seed: population intervals are unavailable by design. '
                                'No energy bound is transferred to temperature.'),
            macro_status=macros.status.value_counts().to_dict(),
            limitations=[
                'One model seed (42) and one outer fold (2); descriptive only.',
                'Conditional synthetic-fault challenge: prevalence, precision, F1 and deployment '
                'feasibility are NOT inferable from these counts.',
                'Temperature units (degC) differ from the energy study; no pooled cross-dataset error.',
                'BDG2 operational feasibility remains a separate endpoint.'])
        (ANALYSIS / 'ANALYSIS_RECORD.json').write_text(json.dumps(record, indent=2, default=str), encoding='utf-8')
        figures(summary)
    print(json.dumps(dict(analysis=str(ANALYSIS), scope=actual, operations=ops,
                          ordering=ordering.to_dict('records'), costs=cost), indent=2, default=str))


if __name__ == '__main__':
    main()
