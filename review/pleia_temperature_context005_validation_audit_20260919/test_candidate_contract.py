"""Focused tests for the candidate validator's contract.

A validator that only accepts is worthless. These tests demonstrate BOTH:
  * acceptance of the documented representation-equivalent case, and
  * rejection of meaningful feature, model, prediction, causal-update and
    alert-output corruption.

Every test runs the REAL candidate_validate_v1 code path against a disposable
sandbox copy of one stage. The genuine scientific artifacts are never written to;
the sandbox is built by copying and is deleted afterwards.
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import audit_common as A

REVIEW = A.AUDIT_REVIEW
CANDIDATE = REVIEW / 'candidate_validate_v1.py'
RESULTS = A.OUT / 'contract_tests'


def build_sandbox(root: Path, n_variants: int = 1):
    """Copy the minimum real artifacts needed for a limited candidate run."""
    variants = pd.read_csv(A.RUN / 'stages/tables/variants.csv', keep_default_na=False,
                           dtype={'context_id': str})
    head = variants.head(n_variants)
    stages = sorted(set(head.canonical_stage) | set(head.stage))
    (root / 'stages/tables').mkdir(parents=True)
    head.to_csv(root / 'stages/tables/variants.csv', index=False)
    shutil.copytree(A.RUN / 'stages/controls', root / 'stages/controls')
    for s in stages:
        shutil.copytree(A.RUN / 'stages' / s, root / 'stages' / s)
    return head


def run_candidate(sandbox: Path, out: Path, limit: int):
    env = dict(os.environ, CANDIDATE_RUN=str(sandbox), CANDIDATE_OUT=str(out),
               CANDIDATE_LIMIT=str(limit))
    proc = subprocess.run([A.PYTHON, '-B', str(REVIEW / 'run_stage.py'), 'candidate_validate_v1.py'],
                          cwd=str(A.SMART), env=env, capture_output=True, text=True)
    report = out / 'CANDIDATE_VALIDATION.json'
    if not report.exists():
        return None, proc
    return json.loads(report.read_text(encoding='utf-8')), proc


def rewrite_gz_csv(path: Path, mutate):
    df = pd.read_csv(path, keep_default_na=False, float_precision='round_trip')
    mutate(df)
    with gzip.GzipFile(filename='', mode='wb', fileobj=path.open('wb'), mtime=0) as f:
        df.to_csv(f, index=False, lineterminator='\n')


def violated_kinds(report):
    return sorted({v['kind'] for v in report['candidate_violations']})


CASES = []


def case(name, description, expect_pass, mutate=None, target=None):
    CASES.append(dict(name=name, description=description, expect_pass=expect_pass,
                      mutate=mutate, target=target))


# --- acceptance -------------------------------------------------------
case('accept_unmodified', 'Unmodified representation-equivalent artifacts must pass', True)


# --- rejection --------------------------------------------------------
def corrupt_feature(sandbox, stage):
    def m(df):
        df.loc[5, 'target_rollmean_6'] = float(df.loc[5, 'target_rollmean_6']) + 0.5
    rewrite_gz_csv(sandbox / 'stages' / stage / 'features.csv.gz', m)


case('reject_feature_corruption',
     'A 0.5 degC change to one saved causal feature must fail provenance (Contract A)',
     False, corrupt_feature)


def corrupt_observation(sandbox, stage):
    def m(df):
        df.loc[7, 'observed'] = float(df.loc[7, 'observed']) + 1.0
    rewrite_gz_csv(sandbox / 'stages' / stage / 'observations.csv.gz', m)


case('reject_observation_corruption',
     'A 1.0 degC change to a saved observation must fail Contract A',
     False, corrupt_observation)


def corrupt_prediction(sandbox, stage):
    def m(df):
        df.loc[9, 'raw_upper'] = float(df.loc[9, 'raw_upper']) + 0.25
    rewrite_gz_csv(sandbox / 'stages' / stage / 'cqr_static_issued.csv.gz', m)


case('reject_prediction_corruption',
     'A 0.25 degC change to a saved model prediction must fail Contract B',
     False, corrupt_prediction)


def corrupt_bound(sandbox, stage):
    def m(df):
        df.loc[11, 'lower'] = float(df.loc[11, 'lower']) - 0.3
    rewrite_gz_csv(sandbox / 'stages' / stage / 'cqr_rolling_issued.csv.gz', m)


case('reject_interval_corruption',
     'A 0.3 degC change to a saved interval bound must fail Contract C',
     False, corrupt_bound)


def corrupt_rolling_update(sandbox, stage):
    def m(df):
        if len(df):
            df.loc[0, 'correction_lower'] = float(df.loc[0, 'correction_lower']) + 0.2
    rewrite_gz_csv(sandbox / 'stages' / stage / 'cqr_rolling_updates.csv.gz', m)


case('reject_causal_update_corruption',
     'A 0.2 degC change to a rolling conformal correction must fail Contract C rolling state',
     False, corrupt_rolling_update)


def corrupt_alert(sandbox, stage):
    def m(df):
        df.loc[3, 'alert_combined'] = not bool(df.loc[3, 'alert_combined'])
    rewrite_gz_csv(sandbox / 'stages' / stage / 'cqr_static_single_sample_alerts.csv.gz', m)


case('reject_alert_flag_corruption',
     'Flipping one saved alert flag must fail Contract C alert outcomes',
     False, corrupt_alert)


def corrupt_released_score(sandbox, stage):
    def m(df):
        if len(df):
            df.loc[2, 'score'] = float(df.loc[2, 'score']) + 0.4
    rewrite_gz_csv(sandbox / 'stages' / stage / 'cqr_static_released.csv.gz', m)


case('reject_released_score_corruption',
     'A 0.4 degC change to a released conformity score must fail Contract C',
     False, corrupt_released_score)


def corrupt_owner(sandbox, stage):
    """Perturb the serialized model itself, leaving every saved output intact."""
    import pickle
    p = sandbox / 'stages/controls/controls.pkl'
    with p.open('rb') as f:
        wrappers = pickle.load(f)
    est = wrappers['cqr'].owner._mapie_quantile_regressor.estimators_[1]
    est._baseline_prediction = est._baseline_prediction + 0.05
    with p.open('wb') as f:
        pickle.dump(wrappers, f, protocol=5)


case('reject_model_corruption',
     'Shifting the saved upper-quantile model baseline by 0.05 degC must fail Contract B',
     False, corrupt_owner)


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    variants = pd.read_csv(A.RUN / 'stages/tables/variants.csv', keep_default_na=False)
    stage0 = variants.iloc[0].canonical_stage
    rows = []
    for c in CASES:
        with tempfile.TemporaryDirectory(prefix='candidate_test_') as tmp:
            sandbox = Path(tmp) / 'run'
            sandbox.mkdir(parents=True)
            build_sandbox(sandbox, 1)
            if c['mutate']:
                c['mutate'](sandbox, stage0)
            out = Path(tmp) / 'out'
            report, proc = run_candidate(sandbox, out, 1)
            if report is None:
                rows.append(dict(test=c['name'], description=c['description'],
                                 expected='pass' if c['expect_pass'] else 'reject',
                                 observed='ERROR', ok=False,
                                 detail=proc.stdout[-400:] + proc.stderr[-800:]))
                continue
            passed = report['passed']
            ok = (passed == c['expect_pass'])
            rows.append(dict(test=c['name'], description=c['description'],
                             expected='pass' if c['expect_pass'] else 'reject',
                             observed='pass' if passed else 'reject', ok=ok,
                             violations=report['totals']['violations'],
                             max_difference=report['totals']['maximum_observed_difference'],
                             detected_by=';'.join(violated_kinds(report)) if not passed else ''))
        print(f"{'OK ' if rows[-1]['ok'] else 'FAIL'} {c['name']:38s} expected="
              f"{rows[-1]['expected']:6s} observed={rows[-1]['observed']:6s} "
              f"detected_by={rows[-1].get('detected_by','')}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / 'contract_test_results.csv', index=False)
    summary = dict(total=len(rows), passed=int(df.ok.sum()), failed=int((~df.ok).sum()),
                   all_ok=bool(df.ok.all()), results=rows)
    (RESULTS / 'CONTRACT_TESTS.json').write_text(json.dumps(summary, indent=2, default=str), encoding='utf-8')
    print()
    print(json.dumps(dict(total=summary['total'], passed=summary['passed'],
                          failed=summary['failed'], all_ok=summary['all_ok']), indent=2))
    if not summary['all_ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
