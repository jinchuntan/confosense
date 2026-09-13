"""Compare published frozen support tables directly; no datasets or fitting."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]


def rows(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))


def main(out):
    base=ROOT/'smart_building_conformal/outputs/amendment004'
    fresh=base/'bdg2_threefold_frozen_v2';old=base/'preflight_20260913_v1';counts={}
    for current,previous,keys in [('memberships.csv','memberships_summary.csv',['outer_fold','role']),
        ('boundaries.csv','boundaries.csv',['outer_fold','left','right']),
        ('stratum_support.csv','stratum_support.csv',['outer_fold','role','family','severity'])]:
        prior={tuple(r[k] for k in keys):r for r in rows(old/previous) if r['dataset']=='bdg2'}
        now=rows(fresh/current)
        for r in now:
            p=prior[tuple(r[k] for k in keys)]
            for k,v in r.items():
                if k=='asset_days':assert math.isclose(float(v),float(p[k]),rel_tol=2e-15)
                else:assert v==p[k],(current,k,v,p[k])
        counts[current]=len(now)
    cats=rows(fresh/'catalogues.csv')
    prior={tuple(r[k] for k in ['outer_fold','role','catalogue_seed']):r for r in rows(old/'catalogue_summary.csv') if r['dataset']=='bdg2'}
    for r in cats:
        with (ROOT/'smart_building_conformal'/r['path']).open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
        assert h==r['preflight_file_sha256']
        assert r['catalogue_hash']==prior[tuple(r[k] for k in ['outer_fold','role','catalogue_seed'])]['catalogue_hash']
    counts['catalogue_file_and_value_hashes']=len(cats)
    result=dict(passed=True,learned_fits=0,all_current_support_values_match_published_preflight=True,checks=counts)
    with Path(out).open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))


if __name__=='__main__':main(sys.argv[1])
