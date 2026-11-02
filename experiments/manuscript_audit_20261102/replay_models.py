"""Replay the original BDG2 event schedules with an archived, or verified refit, model."""

import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "smart_building_conformal"))
sys.path.insert(0, str(ROOT / "experiments" / "recovery_replay_20261102"))
from replay import load_runner
from src.features import build_supervised
from src.operational004_events import catalogue
from src.split_integrity import training_scale

HOUR = pd.Timedelta(hours=1)
WEATHER = ["airTemperature", "dewTemperature"]
FIXED_COLUMNS = ["group_id", "origin_time", "target_time", "y_true", "row_id"]


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(frame, config):
    return build_supervised(frame, 1, HOUR, 24, config)


def prepare(raw, protocol):
    reader = load_runner(ROOT / "experiments" / "matched_workload_20261102")
    raw_frames, _ = reader.read_data(raw)
    cfg = dict(protocol["resolved_dataset_config"]["features"], covariates=WEATHER)
    cfg["target_lags"] = [0] + cfg["target_lags"]
    frames, matrices, metadata = {}, [], []
    for name, source in sorted(raw_frames.items()):
        frame = pd.DataFrame(index=source.index)
        for col in ["target", *WEATHER]:
            original = source["y" if col == "target" else col]
            frame[col] = original.ffill(limit=3)
            frame[col + "_was_missing"] = original.isna().astype(int)
        frames[name] = frame
        xy = build(frame, cfg)
        seq_ok = (
            frame[["target", *WEATHER]].notna().all(axis=1).rolling(24).sum().eq(24)
        )
        valid = seq_ok.reindex(xy["X"].index).to_numpy()
        matrices.append(xy["X"].loc[valid, protocol["support"]["feature_names"]])
        m = xy["meta"].loc[valid].assign(group_id=name)
        m["row_id"] = [
            hashlib.sha256(f"1|{name}|{o}|{t}".encode()).hexdigest()
            for o, t in zip(m.origin_time, m.target_time)
        ]
        metadata.append(m[FIXED_COLUMNS])
    return (
        frames,
        cfg,
        pd.concat(matrices, ignore_index=True),
        pd.concat(metadata, ignore_index=True),
    )


def members(meta, membership):
    key = pd.Index(meta.row_id)
    ix = key.get_indexer(membership.row_id)
    if (ix < 0).any() or not membership.row_id.is_unique:
        raise ValueError("Archived row membership cannot be reconstructed")
    return ix


def load_point(folder, fold, X, meta, protocol):
    if fold == 0:
        roles = {}
        for role in ["fit", "calibration", "test"]:
            record = protocol["support"]["roles"][role]
            ix = np.flatnonzero(
                meta.origin_time.between(record["origin_min"], record["origin_max"])
            )
            digest = hashlib.sha256(
                "\n".join(meta.iloc[ix].row_id).encode()
            ).hexdigest()
            assert digest == record["row_id_hash"] and len(ix) == record["n"], (
                role,
                len(ix),
            )
            roles[role] = ix
        saved = (
            pd.read_csv(folder / "point_summary.csv").query("model=='xgboost'").iloc[0]
        )
        params = protocol["config"]["candidates"]["xgboost"][
            int(saved.selected_candidate)
        ]
        model = XGBRegressor(
            **params,
            objective="reg:squarederror",
            tree_method="hist",
            random_state=42,
            n_jobs=1,
        )
        model.fit(X.iloc[roles["fit"]], meta.y_true.iloc[roles["fit"]])
        cal, test = roles["calibration"], roles["test"]
        residual = np.abs(meta.y_true.iloc[cal].to_numpy() - model.predict(X.iloc[cal]))
        q = float(np.sort(residual)[int(np.ceil(0.95 * (len(cal) + 1))) - 1])
        error = meta.y_true.iloc[test].to_numpy() - model.predict(X.iloc[test])
        quality = (
            pd.read_csv(folder / "interval_quality.csv")
            .query("model=='xgboost' and nominal_level==.95")
            .iloc[0]
        )
        observed_metrics = [np.abs(error).mean(), np.sqrt(np.mean(error**2)), q]
        archived_metrics = [saved.mae, saved.rmse, quality.q]
        if not np.allclose(observed_metrics, archived_metrics, rtol=0, atol=1e-7):
            return (
                None,
                q,
                roles["fit"],
                test,
                "excluded refit: archived versus refit MAE/RMSE/radius "
                + repr(
                    list(
                        zip(map(float, archived_metrics), map(float, observed_metrics))
                    )
                ),
            )
        status = "refit; all role hashes, MAE, RMSE and 95% calibration radius matched"
        return model, q, roles["fit"], test, status
    manifest = json.loads((folder / "COMPLETE.json").read_text())["hashes"]
    for name in [
        "model.ubj",
        "predictions.csv.gz",
        "fitting_membership.csv.gz",
        "payload.json",
    ]:
        assert hash_file(folder / name) == manifest[name]
    archived = pd.read_csv(
        folder / "predictions.csv.gz", float_precision="round_trip"
    ).query("nominal_level==.95")
    test = members(meta, archived)
    fit = members(meta, pd.read_csv(folder / "fitting_membership.csv.gz"))
    model = XGBRegressor(n_jobs=1)
    model.load_model(folder / "model.ubj")
    point = model.predict(X.iloc[test]).astype(float)
    np.testing.assert_array_equal(point, archived.point)
    np.testing.assert_array_equal(meta.y_true.iloc[test], archived.y_true)
    q = next(
        r["q"]
        for r in json.loads((folder / "payload.json").read_text())["intervals"]
        if r["nominal_level"] == 0.95
    )
    np.testing.assert_allclose(point - q, archived.lower, rtol=0, atol=1e-10)
    np.testing.assert_allclose(point + q, archived.upper, rtol=0, atol=1e-10)
    return (
        model,
        q,
        fit,
        test,
        "archived booster; every clean test point and both 95% bounds matched",
    )


def predict_dirty(frames, cfg, meta, observed, columns):
    matrices = []
    for name, group in meta.groupby("group_id", sort=False):
        frame = frames[name].copy()
        frame.loc[group.target_time, "target"] = observed[group.index]
        frame.loc[group.target_time, "target_was_missing"] = (
            ~np.isfinite(observed[group.index])
        ).astype(int)
        frame["target"] = frame.target.ffill()
        matrices.append(build(frame, cfg)["X"].loc[group.origin_time, columns])
    return pd.concat(matrices, ignore_index=True)


def flags(bounds, values, combined):
    lo, hi = bounds
    return (values < lo) | (values > hi) | (combined & ~np.isfinite(values))


def states(meta, events, alarm, observed, common=None):
    keep = (
        np.ones(len(meta), bool)
        if common is None
        else meta.row_id.isin(common).to_numpy()
    )
    selected = np.flatnonzero(keep)
    previous = np.r_[-2, selected[:-1]]
    time = pd.DatetimeIndex(meta.target_time).asi8
    group = meta.group_id.to_numpy()
    boundary = (
        (previous < 0)
        | (group[selected] != group[previous])
        | (time[selected] - time[previous] != HOUR.value)
    )
    starts = np.zeros(len(meta), bool)
    starts[selected] = alarm[selected] & (boundary | ~alarm[previous])
    y = meta.y_true.to_numpy()
    data = []
    for row in events.itertuples():
        start, end = int(row.start_index), int(row.end_index)
        window = np.arange(start, end + 4)
        if not keep[window].all():
            continue
        changed = np.flatnonzero(observed[start : end + 1] != y[start : end + 1])
        assert len(changed) and (np.diff(time[window]) == HOUR.value).all()
        pos = np.flatnonzero(starts[window])
        first = int(pos[0]) if len(pos) else -1
        state = (
            "miss"
            if first < 0
            else (
                "before"
                if first < changed[0]
                else "during" if first <= changed[-1] else "after"
            )
        )
        data.append(
            (
                row.event_id,
                row.group_id,
                row.family,
                row.severity,
                row.onset,
                int(changed[0]),
                int(changed[-1]),
                end - start,
                state,
                first,
            )
        )
    return pd.DataFrame(
        data,
        columns=[
            "event_id",
            "building",
            "family",
            "severity",
            "onset",
            "first_changed_hour",
            "last_changed_hour",
            "slot_end_hour",
            "state",
            "hour",
        ],
    )


def main(source, raw, out):
    from src.conformal_cqr import cqr_interval

    protocol = json.loads((source / "f0/protocol.json").read_text())
    for filename, expected in {
        "electricity.csv": "039d909d8981e2d69eaeb366144e6ab7e84fa5e7e216aee42bddd95384a66418",
        "metadata.csv": "992d0b29f24f96ad4332bc4dbb534b7bdd7dd2689aad093f94e93068ecddca02",
        "weather.csv": "a8189f1c6acdf3b9933a9e6354b8e7c1278cd56a7075929623a17565d44f04bd",
    }.items():
        assert hash_file(raw / filename) == expected, filename
    frames, cfg, X, meta = prepare(raw, protocol)
    records = []
    receipts = []
    history = []
    for fold in [1, 2, 0]:
        point, q, fit, test, status = load_point(
            source / f"f{fold}", fold, X, meta, protocol
        )
        testmeta = meta.iloc[test].reset_index(drop=True)
        if point is None:
            receipts.append(
                dict(fold=fold, test_rows=len(test), radius=q, model_check=status)
            )
            print(f"Fold {fold}: {status}", flush=True)
            continue
        orig = testmeta.y_true.to_numpy()
        scales = training_scale(meta.y_true.to_numpy(), meta, fit)

        def point_bounds(x):
            pred = point.predict(x).astype(float)
            return pred - q, pred + q

        methods = {"xgboost_abs95": point_bounds}
        common = None
        if fold == 2:
            manifest = json.loads((source / "cqr/COMPLETE.json").read_text())
            assert hash_file(source / "cqr/owner.pkl") == manifest["files"]["owner.pkl"]
            with (source / "cqr/owner.pkl").open("rb") as f:
                owner = pickle.load(f)

            def cqr_bounds(x):
                band = cqr_interval(owner, x)
                return band["lower"], band["upper"]

            methods["submitted_cqr95"] = cqr_bounds
            common = set(
                pd.read_csv(source / "cqr/common.csv.gz", usecols=["row_id"]).row_id
            )
        clean_X = X.iloc[test].reset_index(drop=True)
        null_history = predict_dirty(frames, cfg, testmeta, orig, X.columns)
        np.testing.assert_array_equal(null_history.to_numpy(), clean_X.to_numpy())
        clean = {key: func(clean_X) for key, func in methods.items()}
        clean_hash = hashlib.sha256(clean_X.to_numpy().tobytes()).hexdigest()
        if fold == 2:
            cqr_rates = []
            for support, ids in [("native", None), ("common", common)]:
                mask = (
                    np.ones(len(testmeta), bool)
                    if ids is None
                    else testmeta.row_id.isin(ids)
                )
                a = flags(clean["submitted_cqr95"], orig, True)[mask]
                episodes = clean_episodes(testmeta.loc[mask], a)
                cqr_rates.append((support, episodes / (sum(mask) / 24)))
        for seed in [42, 43, 44, 45, 46]:
            observed, available, ev, _ = catalogue(
                orig, testmeta, HOUR, scales, "bdg2", "outer_test", fold, seed
            )
            effective = ev[ev.effective].copy()
            dirty = predict_dirty(frames, cfg, testmeta, observed, X.columns)
            history.append(
                dict(
                    fold=fold,
                    catalogue=seed,
                    clean_features_sha256=clean_hash,
                    feedback_features_sha256=hashlib.sha256(
                        dirty.to_numpy().tobytes()
                    ).hexdigest(),
                )
            )
            for key, func in methods.items():
                feedback = func(dirty)
                for channel in ["numerical", "combined"]:
                    fixed = flags(clean[key], observed, channel == "combined")
                    live = flags(feedback, observed, channel == "combined")
                    for support, ids in [("native", None)] + (
                        [("common", common)] if key == "submitted_cqr95" else []
                    ):
                        left = states(testmeta, effective, fixed, observed, ids)
                        right = states(testmeta, effective, live, observed, ids)
                        np.testing.assert_array_equal(left.event_id, right.event_id)
                        pairs = left.rename(
                            columns={"state": "fixed", "hour": "fixed_hour"}
                        ).assign(
                            live=right.state,
                            live_hour=right.hour,
                            model=key,
                            fold=fold,
                            catalogue=seed,
                            channel=channel,
                            support=support,
                        )
                        records.append(pairs)
        receipts.append(
            dict(
                fold=fold,
                test_rows=len(test),
                radius=q,
                model_check=status,
                background_episodes=clean_episodes(
                    testmeta, flags(clean["xgboost_abs95"], orig, False)
                ),
                exposure_meter_days=len(test) / 24,
            )
        )
        print(f"Verified and scored fold {fold} ({status})", flush=True)
    out.mkdir(exist_ok=True, parents=True)
    data = pd.concat(records, ignore_index=True)
    keys = ["model", "fold", "catalogue", "channel", "support", "event_id"]
    assert not data.duplicated(keys).any()
    stuck = data.query('family=="stuck" and channel=="numerical"')
    summary = stuck.assign(
        fixed_credit=stuck.fixed.ne("miss"),
        feedback_credit=stuck.live.ne("miss"),
        fixed_during=stuck.fixed.eq("during"),
        feedback_during=stuck.live.eq("during"),
        retained_during=(stuck.fixed.eq("during") & stuck.live.eq("during")),
        moved_after=(stuck.fixed.eq("during") & stuck.live.eq("after")),
        moved_to_miss=(stuck.fixed.eq("during") & stuck.live.eq("miss")),
    )
    headline = summary.groupby(["model", "fold", "support"]).agg(
        events=("event_id", "size"),
        **{
            c: (c, "sum")
            for c in [
                "fixed_credit",
                "feedback_credit",
                "fixed_during",
                "feedback_during",
                "retained_during",
                "moved_after",
                "moved_to_miss",
            ]
        },
    )
    archive = pd.read_csv(source / "source/op_metrics.csv")
    published = archive.query(
        'outer_fold==2 and model_seed==42 and method=="cqr" and level==.95 and strategy=="static" and rule_id=="single_sample"'
    )
    assert set(published.support) == {"native", "common"} and len(published) == 2
    for row in published.itertuples():
        np.testing.assert_allclose(
            dict(cqr_rates)[row.support],
            row.background_episodes_per_asset_day,
            atol=1e-12,
        )
        actual = data.query(
            'model=="submitted_cqr95" and channel=="combined" and support==@row.support'
        )
        assert (
            len(actual) == row.n_events
            and actual.live.ne("miss").sum() == row.n_detected
        ), (
            row.support,
            len(actual),
            row.n_events,
            actual.live.ne("miss").sum(),
            row.n_detected,
        )
    headline.to_csv(out / "stuck_summary.csv")
    data.to_csv(
        out / "paired_events.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    dims = ["model", "fold", "channel", "support", "family", "fixed", "live"]
    data.groupby(dims).size().rename("events").to_csv(out / "transitions.csv")
    pd.DataFrame(receipts).to_csv(out / "model_checks.csv", index=False)
    pd.DataFrame(history).to_csv(out / "feature_hashes.csv", index=False)


def clean_episodes(meta, alarm):
    hours = pd.DatetimeIndex(meta.target_time).asi8
    group = meta.group_id.to_numpy()
    boundary = np.r_[True, (np.diff(hours) != HOUR.value) | (group[:-1] != group[1:])]
    return int((alarm & (boundary | ~np.r_[False, alarm[:-1]])).sum())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for arg in ["source", "raw", "out"]:
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    main(args.source, args.raw, args.out)
