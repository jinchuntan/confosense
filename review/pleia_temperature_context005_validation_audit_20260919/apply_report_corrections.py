"""Apply the audit's additive corrections to the pilot report, on the audit branch only.

Nothing already in the report is deleted or restated; the audit adds the missing
acceptance-status label, the explicit nominal-coverage interpretation and the
count-identity explanation, and records a before/after digest of the file.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

import audit_common as A
from src.intervals005_common import read

REPORT = A.PILOT_REVIEW / 'PLEIA_TEMPERATURE_CONTEXT005_PILOT_REPORT.md'
MARK = '<!-- validation-audit-20260919 -->'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    before = REPORT.read_bytes()
    text = REPORT.read_text(encoding='utf-8')
    if MARK in text:
        raise SystemExit('corrections already applied')

    counts = read(A.OUT / 'COUNT_RECONCILIATION.json')
    cand = read(A.OUT / 'candidate_v1/CANDIDATE_VALIDATION.json')
    ivl = pd.read_csv(A.BASE / (A.KEY + '_analysis') / 'interval_diagnostics.csv')
    fs = ivl[(ivl.scope == 'fullstream_clean') & (ivl.target == 'clean_counterfactual')]
    summ = pd.read_csv(A.BASE / (A.KEY + '_analysis') / 'control_rule_channel_summary.csv')
    comb = summ[summ.channel == 'combined']
    imm = comb[comb.rule_id == 'single_sample']

    # 1. acceptance status, immediately after the opening caveat paragraph
    anchor = 'BDG2 operational feasibility remains a separate endpoint.'
    status = [
        '', MARK,
        '> **Acceptance status: execution and publication complete; scientific acceptance pending '
        'validation.** The frozen `validate` action did not pass and has not been made to pass. '
        f'A validation audit on branch `{A.AUDIT_BRANCH}` proves the failure mechanism, shows that no '
        'evaluated endpoint differs, and proposes a candidate validator that is NOT adopted here. '
        'See `review/pleia_temperature_context005_validation_audit_20260919/VALIDATION_AUDIT_REPORT.md`.',
    ]
    text = text.replace(anchor, anchor + '\n' + '\n'.join(status), 1)

    # 2. count identities, after the scope table
    anchor2 = '| Recorded run exit status | 0 |'
    ident = ['', MARK, '**Count identities.** The figures above are two distinct partitions of the same '
             '2,924 context stages, plus a classification of the fault slots:', '',
             '| identity | arithmetic |', '| --- | --- |']
    for r in counts['identities']:
        ident.append(f'| {r["identity"]} | {r["arithmetic"]} |')
    ident += ['', 'Clean identity replays are **not** fault slots: each context contributes one clean '
              'replay (ordinal 0) plus 42 scheduled fault slots (ordinals 1-42). Aliases arise only '
              f'among fault slots ({counts["aliases_among_fault"]}), never among clean stages '
              f'({counts["aliases_among_clean"]}). `null` and `effective` are exact complements on the '
              '2,856 fault slots, and the 68 clean stages are null by definition.']
    text = text.replace(anchor2, anchor2 + '\n' + '\n'.join(ident), 1)

    # 3. explicit nominal interpretation, before the ordering section
    anchor3 = '## Quantile-ordering warnings'
    nominal = [MARK,
               '**Reading the coverage column against nominal 0.95.** Only `persistence_static` attains '
               'nominal coverage on the clean stream. The learned quantile controls do not:', '',
               '| control | clean-stream coverage | reaches nominal 0.95 | shortfall | MPIW (degC) |',
               '| --- | --- | --- | --- | --- |']
    for r in fs.sort_values('coverage', ascending=False).itertuples():
        nominal.append(f'| `{r.control_id}` | {r.coverage:.4f} | '
                       f'{"yes" if r.coverage >= 0.95 else "**no**"} | {0.95 - r.coverage:+.4f} | '
                       f'{r.mpiw:.3f} |')
    nominal += ['', '`cqr_rolling` narrows the shortfall relative to the static conformal controls but '
                'remains 0.0419 below nominal, at the widest interval of the four. It does not reach '
                'nominal coverage.', '',
                'Leadership is also rule-dependent rather than uniform. At the immediate rule in the '
                'combined channel `persistence_static` detects most (0.9086) but raises MORE clean-stream '
                f'episodes per asset-day than `cqr_rolling` '
                f'({imm[imm.control_id=="persistence_static"].background_episodes_per_asset_day.iloc[0]:.4f} '
                f'versus {imm[imm.control_id=="cqr_rolling"].background_episodes_per_asset_day.iloc[0]:.4f}), '
                'and `cqr_rolling` leads detection at the 30- and 60-minute rules.', '']
    text = text.replace(anchor3, '\n'.join(nominal) + '\n' + anchor3, 1)

    # 4. audit outcome note in the validation section
    anchor4 = '**Unresolved.**'
    s = cand['sensitivity']
    note = [MARK,
            f'**Audit outcome (2026-09-19).** The failure mechanism is proven at node level: a '
            f'{s["rows_affected"]}-row, {s["stages_where_representations_diverge"]}-stage sensitivity, '
            'every case attributable to a gradient-boosting split threshold that a feature value sits '
            'exactly on. A candidate representation-compatible contract passed across the complete '
            f'pilot ({cand["totals"]["assertions"]} assertions, {cand["totals"]["violations"]} '
            'violations) with scientific artifacts unchanged, and was verified to reject feature, '
            'model, prediction, interval, rolling-update, released-score and alert corruption. The '
            'candidate is proposed, NOT adopted; the frozen gate remains unmet.', '']
    text = text.replace(anchor4, '\n'.join(note) + anchor4, 1)

    REPORT.write_text(text, encoding='utf-8')
    after = REPORT.read_bytes()
    rec = dict(file=str(REPORT.relative_to(A.REPO).as_posix()),
               before_sha256=sha(before), before_bytes=len(before),
               after_sha256=sha(after), after_bytes=len(after),
               additive_only=True, sections_added=4, marker=MARK,
               note='Corrections are additive; no existing sentence, number or table was deleted or '
                    'altered. The pilot branch copy of this report is unchanged.')
    (A.OUT / 'REPORT_PATCH_RECORD.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
    print(json.dumps(rec, indent=2))


if __name__ == '__main__':
    main()
