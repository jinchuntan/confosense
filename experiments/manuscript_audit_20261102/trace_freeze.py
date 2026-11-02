"""Extract the earliest moved alarm in the first submitted-CQR fault schedule."""

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import replay_models as replay
from src.conformal_cqr import cqr_interval


def trace(source, raw, out):
    pairs = pd.read_csv(Path(__file__).parent / "results/paired_events.csv.gz")
    switches = pairs.query(
        "model=='submitted_cqr95' and channel=='numerical' and support=='common' "
        "and family=='stuck' and fixed=='during' and live=='after'"
    )
    example = switches.sort_values(["catalogue", "onset", "building"]).iloc[0]
    fold, seed = int(example.fold), int(example.catalogue)
    protocol = json.loads((source / "f0/protocol.json").read_text())
    frames, cfg, features, meta = replay.prepare(raw, protocol)
    _, _, fit, test, _ = replay.load_point(
        source / f"f{fold}", fold, features, meta, protocol
    )
    test_meta = meta.iloc[test].reset_index(drop=True)
    y = test_meta.y_true.to_numpy()
    scales = replay.training_scale(meta.y_true.to_numpy(), meta, fit)
    observed, _, events, _ = replay.catalogue(
        y, test_meta, replay.HOUR, scales, "bdg2", "outer_test", fold, seed
    )
    event = events.loc[events.event_id.eq(example.event_id)].squeeze()
    begin, end = int(event.start_index), int(event.end_index)
    idx = np.arange(begin - 1, end + 4)
    common = set(pd.read_csv(source / "cqr/common.csv.gz", usecols=["row_id"]).row_id)
    assert test_meta.iloc[idx].row_id.isin(common).all()
    assert test_meta.iloc[idx].group_id.eq(example.building).all()
    assert test_meta.iloc[idx].target_time.diff().dropna().eq(replay.HOUR).all()
    clean = features.iloc[test].reset_index(drop=True)
    dirty = replay.predict_dirty(frames, cfg, test_meta, observed, features.columns)
    path = source / "cqr/owner.pkl"
    manifest = json.loads((source / "cqr/COMPLETE.json").read_text())
    assert replay.hash_file(path) == manifest["files"]["owner.pkl"]
    with path.open("rb") as handle:
        model = pickle.load(handle)
    view = pd.DataFrame(
        {
            "event_id": example.event_id,
            "building": example.building,
            "reading_time": test_meta.iloc[idx].target_time.to_numpy(),
            "hour_from_slot_start": idx - begin,
            "observed_kwh": observed[idx],
            "altered_by_injection": observed[idx] != y[idx],
        }
    )
    for label, x in [("fixed", clean), ("live", dirty)]:
        band = cqr_interval(model, x.iloc[idx])
        view[label + "_lower"] = band["lower"]
        view[label + "_upper"] = band["upper"]
        alert = replay.flags((band["lower"], band["upper"]), observed[idx], False)
        starts = alert & ~np.r_[False, alert[:-1]]
        starts[0] = (
            False  # The preceding row is context and is outside this event's window.
        )
        view[label + "_new_alarm"] = starts
        assert int(view.loc[starts, "hour_from_slot_start"].iloc[0]) == int(
            example[label + "_hour"]
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    view.to_csv(out, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["source", "raw", "out"]:
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    trace(args.source, args.raw, args.out)
