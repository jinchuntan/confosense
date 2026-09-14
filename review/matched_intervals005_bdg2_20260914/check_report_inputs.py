"""Independent vector checks of exposure/rates, crossings, and journal counts."""
from common import *
from collections import Counter
import numpy as np,pandas as pd
from src.intervals005_common import frame,Operations


def check(out):
    before=tree(RUN);rows=[]
    with Operations(forbid=True):
        counts=read(RUN/'stages/tables/operation_counts.json')
        journal=[json.loads(line) for line in (RUN/'operations.jsonl').read_text().splitlines()]
        started={row['operation_id']:row for row in journal if row['event']=='started'}
        returned={row['operation_id']:row for row in journal if row['event']=='returned'}
        assert len(started)==len(returned) and set(started)==set(returned)
        recount=Counter(row['kind'] for row in returned.values())
        for name,n in counts.items():assert recount[name]==n
        for row in started.values():
            if row['kind'] in ('quantile_estimator_fit','xgboost_estimator_fit','kmeans_candidate_fit'):
                assert row['parameters']['random_state']==42
        native=frame(RUN/'stages/tables/native_support_metrics.csv')
        common=frame(RUN/'stages/tables/common_support_metrics.csv')
        seasonal_points=frame(RUN/'stages/tables/seasonal_point_metrics.csv')
        seasonal_intervals=frame(RUN/'stages/tables/seasonal_interval_metrics.csv')
        assert len(seasonal_points)==3 and len(seasonal_intervals)==6
        for _,point in seasonal_points.iterrows():
            references=seasonal_intervals[seasonal_intervals.horizon==point.horizon]
            assert len(references)==2 and point.learned_fits==0
            for _,reference in references.iterrows():
                for column in ('n','mae','rmse'):np.testing.assert_allclose(point[column],reference[column],atol=1e-10,rtol=1e-12)
        all_work=frame(RUN/'stages/tables/background_workload.csv')
        for _,key in native.iterrows():
            h=int(key.horizon);level=float(key.level);method=key.method
            folder=RUN/f'stages/stream_h{h}_l{int(level*100)}_{method}'
            f=frame(folder/'issued.csv.gz');shared=set(frame(RUN/f'stages/dscp_joint/test_h{h}.csv.gz').row_id)
            crossed=f.raw_lower.to_numpy()>f.raw_upper.to_numpy()
            np.testing.assert_array_equal(f.raw_crossed,crossed)
            assert int(key.raw_crossed)==int(crossed.sum())
            cr=common[(common.horizon==h)&(common.level==level)&(common.method==method)].iloc[0]
            assert int(cr.raw_crossed)==int(crossed[f.row_id.isin(shared)].sum())
            part_work=all_work[(all_work.horizon==h)&(all_work.level==level)&(all_work.method==method)]
            contributions=[]
            for group,part in f.groupby('group_id',sort=True):
                part=part.sort_values('target_time',kind='stable')
                available=part.available.to_numpy(bool)
                numerical=available&((part.observed.to_numpy()<part.lower.to_numpy())|(part.observed.to_numpy()>part.upper.to_numpy()))
                times=pd.to_datetime(part.target_time).astype('int64').to_numpy()
                gap=np.r_[True,np.diff(times)!=pd.Timedelta(hours=1).value]
                for channel,flag in [('numerical_only',numerical),('availability_only',~available),('combined',numerical|~available)]:
                    episodes=int(np.count_nonzero(flag&(gap|~np.r_[False,flag[:-1]])))
                    contributions.append(dict(group_id=str(group),channel=channel,n_rows=len(part),n_available=int(available.sum()),n_unavailable=int((~available).sum()),episodes=episodes,alert_samples=int(flag.sum())))
            for channel in ('numerical_only','availability_only','combined'):
                pieces=[row for row in contributions if row['channel']==channel]
                contributions.append(dict(group_id='__pooled__',channel=channel,**{name:sum(row[name] for row in pieces) for name in ('n_rows','n_available','n_unavailable','episodes','alert_samples')}))
            for expected in contributions:
                saved=part_work[(part_work.group_id==expected['group_id'])&(part_work.channel==expected['channel'])].iloc[0]
                for name in ('n_rows','n_available','n_unavailable','episodes'):assert int(saved[name])==expected[name]
                days=expected['n_rows']/24
                values=dict(exposure_asset_days=days,observed_asset_days=expected['n_available']/24,background_episodes_per_asset_day=expected['episodes']/days,time_in_alert_fraction=expected['alert_samples']/expected['n_rows'])
                delta=max(abs(float(saved[name])-value) for name,value in values.items())
                for name,value in values.items():np.testing.assert_allclose(saved[name],value,atol=1e-10,rtol=1e-12)
                assert saved.event_count==0 and saved.event_recall_status=='not_estimable_empty_event_catalogue'
                rows.append(dict(horizon=h,level=level,method=method,group_id=expected['group_id'],channel=expected['channel'],maximum_arithmetic_difference=delta,passed=True))
        assert len(rows)==990 and tree(RUN)==before
        pd.DataFrame(rows).to_csv(out/'background_and_crossing_checks.csv',index=False)
        result=dict(passed=True,workload_checks=990,native_common_crossing_checks=60,seasonal_point_checks=3,matched_started_returned_operations=len(returned),journal_counts=dict(recount),base_estimator_seed_checked=42,maximum_arithmetic_difference=max(r['maximum_arithmetic_difference'] for r in rows),models_fitted=0,calibrators_fitted=0,scientific_artifacts_unchanged=True)
        atomic(out/'additional_integrity_validation.json',result)
        return result
