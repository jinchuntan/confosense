"""Freeze both authorized units and combined estimands before either new fit."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src import operational004 as R, operational004_engine as E, operational004_stream as S
from src import split_integrity as SI
from src.operational004_design import DESIGN, nested_roles, make_outer_folds
from src.operational004_authorization import verify_catalogues
from src.unit_checkpoint import source_digest, signature, digest, json_value
from src.pilot_resources import ResourceMeter, hardware, require_ram


def main(out):
    out=Path(out);out.mkdir(exist_ok=False,parents=True)
    def forbidden(*a,**k): raise AssertionError('freezing must fit nothing')
    R.evaluate_unit=E.evaluate_unit=S.OwnedInterval.__init__=S.conformal_cqr.fit_cqr=forbidden
    config='configs/operational_amendment004.json';frozen=json.loads(Path(config).read_text())
    preflight=Path('outputs/amendment004')/frozen['preflight_run']
    old=pd.read_csv(preflight/'memberships_summary.csv',float_precision='round_trip')
    require_ram(3*2**30)
    with ResourceMeter() as meter:
        cfg=R.resolve_dataset_config(R.load_config('configs/study_final_dissertation_v2.yaml'),'bdg2')
        prepared=R.prepare(cfg);s,w,_=R.build_windows(prepared,cfg,cfg['alerts']['primary_horizon'])
        scheme='chronological' if isinstance(prepared.partitioner,R.ChronologicalPartitioner) else SI.GROUPED
        folds=make_outer_folds(w['meta'],scheme,3,w['horizon'],s.freq);grid=R.pilot_grid(cfg,s.freq)
        prior=json.loads(Path('../review/amendment004_20260913/next_bounded_proposal.json').read_text())
        assert grid==prior['candidate_grid'] and len(grid)==9
        units={};members=[];boundaries=[];catalogues=[];support=[];outer_sets={}
        for fold in [2,1,0]:
            roles=nested_roles(w['meta'],folds[fold],scheme);hashes={}
            for role,ix in roles.items():
                sub=w['meta'].iloc[ix];h=SI.membership_hash(w['meta'],ix)
                saved=old[(old.dataset=='bdg2')&(old.outer_fold==fold)&(old.role==role)].iloc[0]
                assert h==saved.membership_hash and len(ix)==saved.n
                hashes[role]=h
                members.append(dict(outer_fold=fold,role=role,n=len(ix),groups=sub.group_id.nunique(),
                    asset_days=len(ix)/24,origin_min=str(sub.origin_time.min()),origin_max=str(sub.origin_time.max()),
                    target_min=str(sub.target_time.min()),target_max=str(sub.target_time.max()),membership_hash=h))
            for left,right in [('inner0_train','inner0_calibration'),('inner0_calibration','inner0_selection'),
                ('inner1_train','inner1_calibration'),('inner1_calibration','inner1_selection'),
                ('final_fit','final_calibration'),('final_calibration','outer_test')]:
                SI.assert_boundary(w['meta'],roles[left],roles[right],scheme)
                boundaries.append(dict(outer_fold=fold,left=left,right=right,**SI.boundary_record(w['meta'],roles[left],roles[right],scheme)))
            cat,sup=verify_catalogues(w,roles,s.freq,fold,preflight)
            catalogues.extend(cat);support.extend(sup)
            outer_sets[fold]=set(w['meta'].iloc[roles['outer_test']].row_id)
            unitout=f'outputs/amendment004/bdg2_threefold_f{fold}_s42_v1' if fold!=2 else 'outputs/amendment004/bdg2_operational_pilot_f2_s42_v2'
            units[str(fold)]=dict(out=unitout,action='read_only_preserved' if fold==2 else 'authorized_new_fit',
                                 membership_hashes=hashes,catalogues=cat)
            print(f'Frozen fold {fold}: 13 memberships and 15 catalogues, zero fits',flush=True)
        disjoint=[dict(fold_a=a,fold_b=b,overlap=len(outer_sets[a]&outer_sets[b])) for a,b in [(2,1),(2,0),(1,0)]]
        assert all(r['overlap']==0 for r in disjoint)
    plan=dict(status='FROZEN_BEFORE_BOTH_NEW_FITS',frozen_utc=datetime.now(timezone.utc).isoformat(),
        label='three-fold BDG2 reduced-grid benchmark, model seed 42',execution_order=[1,0],dataset='bdg2',
        model_seeds=[42],catalogue_seeds=DESIGN['catalogue_seeds'],horizon=w['horizon'],
        source_hash=source_digest(),source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        config_hash=digest(config),design_hash=signature(DESIGN),data_hash=w['data_hash'],
        outcomes_hash=hashlib.sha256(np.asarray(w['y'],float).tobytes()).hexdigest(),
        candidate_grid=grid,design=DESIGN,resolved_config=cfg,feature_names=list(w['X'].columns),
        original_buildings=sorted(w['meta'].group_id.unique()),units=units,outer_disjointness=disjoint,
        combined_analysis=dict(main_exploratory_paired_contrast='static immediate CQR minus static immediate uncalibrated',
            candidate_a='c0012_23099bed3753',candidate_b='c0000_f5146f1247fa',
            metrics=['macro_event_recall','background_episodes_per_asset_day'],
            workload_pool='sum original clean episodes / sum original asset-days; never multiply exposure by catalogue count',
            recall_pool='sum N and TP within each of 21 strata across folds and all catalogues, then equal-stratum mean',
            per_fold_results_required=True,paired_ci='approximate percentile 95%; resample ten original buildings with all fold/catalogue contributions together',
            bootstrap_seed=20240601,bootstrap_replicates=2000,minimum_valid_replicates=1900,
            model_seeds=[42],independent_buildings=10,inference='exploratory conditional; no significance/equivalence/same-recall superiority claim',
            attribution=['availability','numerical','combined'],preserve=['misses','recovery censoring','per-building workload'],
            outer_comparisons='derive from actual frozen selection, fixed controls, independent subsets, inverse and persistence; no reselection',
            limitations='post-inspection design; fold 2 already inspected; historical period repeatability, not prospective or unseen buildings'),
        resources=dict(minimum_free_ram_bytes=3*2**30,minimum_free_disk_bytes=8*2**30,threads=1,
            historical_smaller_fold2_command_seconds=987.3824542,planning_only_minutes_per_new_unit=[20,40],
            policy='sequential real fits; preserve failure evidence; stop on guard failure; no second-run adaptation to first-run scores'),
        no_fits=True,preflight_resources=meter.result,hardware=hardware(),disk=shutil.disk_usage(Path.cwd())._asdict(),full_study_ready=False)
    for name,rows in [('memberships',members),('boundaries',boundaries),('catalogues',catalogues),('stratum_support',support),('outer_disjointness',disjoint)]:
        pd.DataFrame(rows).to_csv(out/(name+'.csv'),index=False)
    (out/'execution_analysis_manifest.json').write_text(json.dumps(plan,indent=2,default=json_value)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,learned_fits=0,membership_roles=len(members),catalogues=len(catalogues),strata=len(support),source_hash=plan['source_hash'])),flush=True)


if __name__=='__main__':main(sys.argv[1])
